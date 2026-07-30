"""MODE:P vNext — Canonical Timeline Schema (V1.1).

Foundational timeline data model using rational timebase and integer ticks.
All time values are integers (ticks); floating-point seconds are derived
deterministically by the compiler — never stored as machine facts.

Spec references: LOOP §7.2a, §10.2; Omission P0-08.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional


# ---------------------------------------------------------------------------
# Primitive: Tick is always an int
# ---------------------------------------------------------------------------
Tick = int  # Type alias for clarity — ticks are always integers


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class FramerateUnknownError(Exception):
    """Raised when frame-number operations are attempted but output fps is unverified."""
    pass


# ---------------------------------------------------------------------------
# TimeInterval — [start, end) half-open
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimeInterval:
    """A half-open duration interval ``[start_tick, end_tick)``.

    - ``start_tick`` is inclusive (the first tick of the interval).
    - ``end_tick`` is exclusive (the first tick AFTER the interval).
    - ``end_tick`` must be strictly greater than ``start_tick``.
    - Adjacent intervals (``a.end_tick == b.start_tick``) have no gap and no overlap.
    """

    start_tick: Tick
    end_tick: Tick

    def __post_init__(self) -> None:
        if self.end_tick <= self.start_tick:
            raise ValueError(
                f"TimeInterval end ({self.end_tick}) must be > start ({self.start_tick})"
            )

    @property
    def duration_ticks(self) -> Tick:
        """The number of ticks spanned: end_tick - start_tick."""
        return self.end_tick - self.start_tick

    def contains_tick(self, tick: Tick) -> bool:
        """Return True if *tick* is in [start, end)."""
        return self.start_tick <= tick < self.end_tick

    def display_seconds(self, ticks_per_second: int) -> float:
        """Duration in seconds (derived, not stored as machine fact)."""
        return self.duration_ticks / ticks_per_second

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "interval",
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "duration_ticks": self.duration_ticks,
        }


# ---------------------------------------------------------------------------
# Instant — a point in time
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Instant:
    """An instantaneous point in time at ``at_tick``.

    An Instant has NO duration and MUST NOT be used where a TimeInterval
    is expected. Use it for events like cut points, sync points, or
    trigger moments.
    """

    at_tick: Tick

    @property
    def duration_ticks(self) -> None:
        """An instant has no duration."""
        return None

    def display_seconds(self, ticks_per_second: int) -> float:
        """The time of this instant in seconds (derived)."""
        return self.at_tick / ticks_per_second

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "instant",
            "at_tick": self.at_tick,
        }


# ---------------------------------------------------------------------------
# CanonicalTimeline — overall timeline container
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CanonicalTimeline:
    """The master timeline for a scene or episode.

    Parameters
    ----------
    ticks_per_second:
        Rational timebase. Common values: 24000 (high precision), 24 (frame-aligned).
    duration_ticks:
        Total number of ticks from start to end. Must be > 0.
    display_precision:
        Number of decimal places for human-readable seconds.
    boundary_ownership:
        Who owns the boundary tick. Always ``"incoming"`` — the tick belongs to
        the shot that starts at that tick.
    output_fps_status:
        ``"verified"`` if the output framerate has been confirmed by capability
        data, ``"unknown"`` otherwise.  Frame-number claims are banned when unknown.
    output_fps:
        The verified output framerate (only meaningful when status is verified).
    rounding_policy:
        How ticks round when converting to display values.
    """

    ticks_per_second: int
    duration_ticks: Tick
    display_precision: int = 3
    boundary_ownership: Literal["incoming"] = "incoming"
    output_fps_status: Literal["verified", "unknown"] = "unknown"
    output_fps: Optional[float] = None
    rounding_policy: str = "nearest"

    _VALID_FPS_STATUS = frozenset({"verified", "unknown"})

    def __post_init__(self) -> None:
        if self.ticks_per_second <= 0:
            raise ValueError("ticks_per_second must be > 0")
        if self.duration_ticks <= 0:
            raise ValueError("duration_ticks must be > 0")
        if self.boundary_ownership != "incoming":
            raise ValueError("boundary_ownership must be 'incoming'")
        if self.output_fps_status not in self._VALID_FPS_STATUS:
            raise ValueError(
                f"output_fps_status must be one of {sorted(self._VALID_FPS_STATUS)}, "
                f"got '{self.output_fps_status}'"
            )
        if self.output_fps_status == "verified" and self.output_fps is None:
            raise ValueError("output_fps must be set when output_fps_status is 'verified'")

    @property
    def duration_seconds(self) -> float:
        """Total duration in seconds (derived)."""
        return self.duration_ticks / self.ticks_per_second

    def frame_number(self, tick: Tick) -> int:
        """Return the frame number for a tick (only when fps is verified)."""
        if self.output_fps_status != "verified" or self.output_fps is None:
            raise FramerateUnknownError(
                f"Cannot compute frame number: output_fps_status is "
                f"'{self.output_fps_status}'. Verify capability fps first."
            )
        seconds = tick / self.ticks_per_second
        return round(seconds * self.output_fps)

    def format_frame_claim(self, tick: Tick) -> str:
        """Return a human-readable frame claim (only when fps is verified)."""
        fn = self.frame_number(tick)  # raises FramerateUnknownError if unknown
        return f"Frame {fn}"

    def time_tolerance_at_tick(self, tick: Tick, tolerance_ticks: int) -> float:
        """Return a time tolerance in seconds around *tick*.

        This works regardless of fps status — use it to express uncertainty
        around cut points or event timing without faking frame precision.
        """
        return tolerance_ticks / self.ticks_per_second

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "schema": "canonical_timeline",
            "version": "1.1",
            "ticks_per_second": self.ticks_per_second,
            "duration_ticks": self.duration_ticks,
            "duration_seconds": self.duration_seconds,
            "display_precision": self.display_precision,
            "boundary_ownership": self.boundary_ownership,
            "output_fps_status": self.output_fps_status,
            "rounding_policy": self.rounding_policy,
        }
        if self.output_fps is not None:
            d["output_fps"] = self.output_fps
        return d


# ---------------------------------------------------------------------------
# Free functions — display seconds derivation
# ---------------------------------------------------------------------------

def display_seconds(ticks: Tick, ticks_per_second: int) -> float:
    """Return the floating-point seconds for *ticks*.

    Raises ValueError if ticks is negative.
    """
    if ticks < 0:
        raise ValueError(f"ticks must be >= 0, got {ticks}")
    return ticks / ticks_per_second


def format_display_seconds(
    ticks: Tick, ticks_per_second: int, precision: int = 2, suffix: str = "s"
) -> str:
    """Return a formatted human-readable time string, e.g. ``"1.50s"``."""
    secs = display_seconds(ticks, ticks_per_second)
    return f"{secs:.{precision}f}{suffix}"


def tick_from_seconds(seconds: float, ticks_per_second: int) -> Tick:
    """Convert floating-point seconds to the nearest integer tick."""
    return round(seconds * ticks_per_second)
