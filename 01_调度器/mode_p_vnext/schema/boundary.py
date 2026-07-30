"""MODE:P vNext — Boundary Ownership & HOLD Schema (V1.3).

Defines InternalBoundary (between shots in a segment), HOLD (controlled
non-zero pause), and deterministic validation rules.

Spec references: LOOP §7.4, §10.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, List, Literal, Sequence

from mode_p_vnext.schema.canonical_timeline import (
    CanonicalTimeline,
    TimeInterval,
    Tick,
)


# ---------------------------------------------------------------------------
# Boundary types (from LOOP §7.4)
# ---------------------------------------------------------------------------

BOUNDARY_TYPES: FrozenSet[str] = frozenset({
    "hard_cut",
    "match_cut",
    "motivated_cut",
    "continuous_reframe",
    "camera_transition",
    "focus_transition",
    "occlusion_transition",
})


# ---------------------------------------------------------------------------
# InternalBoundary
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InternalBoundary:
    """A boundary between adjacent Cinematic Shots within a Generation Segment.

    The cut tick belongs to the incoming shot (``boundary_ownership = "incoming"``).
    """

    at_tick: Tick
    boundary_type: str
    preferred_execution: str
    fidelity_class: Literal["LOCKED", "ELASTIC", "OPTIMIZABLE", "FORBIDDEN"]
    outgoing_anchor: str
    incoming_anchor: str
    outgoing_state_id: str
    incoming_state_id: str

    # Always incoming — the tick belongs to the shot that starts at this tick
    boundary_ownership: Literal["incoming"] = "incoming"

    def __post_init__(self) -> None:
        if self.boundary_type not in BOUNDARY_TYPES:
            raise ValueError(
                f"Invalid boundary_type '{self.boundary_type}'. "
                f"Must be one of: {sorted(BOUNDARY_TYPES)}"
            )
        if self.boundary_ownership != "incoming":
            raise ValueError("boundary_ownership must be 'incoming'")


# ---------------------------------------------------------------------------
# HOLD
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Hold:
    """An explicit controlled hold with non-zero duration.

    HOLD is NOT a boundary — it's a deliberate pause within a shot,
    e.g., holding on a landing frame or waiting for a character to enter.
    """

    interval: TimeInterval
    held_object: str   # what is being held (e.g., "枪管金属内壁")
    hold_reason: str     # why (e.g., "关键落幅注视", "等待入画")

    def __post_init__(self) -> None:
        if self.interval.duration_ticks <= 0:
            raise ValueError(
                f"HOLD must have non-zero duration, got "
                f"{self.interval.duration_ticks} ticks"
            )
        if not self.held_object.strip():
            raise ValueError("held_object must not be empty")

    def display_seconds(self, ticks_per_second: int) -> float:
        return self.interval.display_seconds(ticks_per_second)


# ---------------------------------------------------------------------------
# Validation: N Shot = N+1 Boundary
# ---------------------------------------------------------------------------

def check_boundary_shot_count(
    shots: Sequence[TimeInterval],
    boundaries: Sequence[InternalBoundary],
) -> List[str]:
    """Return violations when the boundary count doesn't equal shot count + 1.

    For N shots there must be exactly N+1 boundaries: one entry boundary,
    one internal boundary between each adjacent pair, and one exit boundary.
    """
    violations: List[str] = []
    expected = len(shots) + 1
    actual = len(boundaries)
    if actual != expected:
        violations.append(
            f"Boundary count mismatch: {len(shots)} shots require "
            f"{expected} boundaries (entry + internal + exit), got {actual}"
        )
    return violations


# ---------------------------------------------------------------------------
# Validation: boundary ownership
# ---------------------------------------------------------------------------

def check_boundary_ownership(
    shots: Sequence[TimeInterval],
    boundaries: Sequence[InternalBoundary],
) -> List[str]:
    """Return violations where a boundary tick is not inside any shot.

    Every boundary tick must be contained in at least one shot interval,
    OR be the terminal exit boundary at the last shot's end_tick.
    Per ``boundary_ownership = "incoming"``, the cut tick should be in
    the shot that starts at that tick.  The exit boundary at the timeline
    end is owned by the timeline, not by an incoming shot.
    """
    violations: List[str] = []
    last_shot_end = shots[-1].end_tick if shots else None
    for i, b in enumerate(boundaries):
        in_any_shot = any(shot.contains_tick(b.at_tick) for shot in shots)
        # Exit boundary at the timeline end is permitted
        is_exit = (last_shot_end is not None and b.at_tick == last_shot_end)
        if not in_any_shot and not is_exit:
            violations.append(
                f"Boundary {i} at tick {b.at_tick}: orphan — not in any shot "
                f"(and not the terminal exit boundary)"
            )
    return violations


# ---------------------------------------------------------------------------
# Validation: boundary in timeline bounds
# ---------------------------------------------------------------------------

def check_boundary_in_bounds(
    timeline: CanonicalTimeline,
    boundaries: Sequence[InternalBoundary],
) -> List[str]:
    """Return violations where a boundary tick is outside the timeline."""
    violations: List[str] = []
    for i, b in enumerate(boundaries):
        if b.at_tick < 0:
            violations.append(
                f"Boundary {i}: negative tick ({b.at_tick})"
            )
        if b.at_tick > timeline.duration_ticks:
            violations.append(
                f"Boundary {i}: tick ({b.at_tick}) exceeds "
                f"timeline duration ({timeline.duration_ticks})"
            )
    return violations
