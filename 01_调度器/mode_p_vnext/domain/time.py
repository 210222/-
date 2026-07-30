"""The sole vNext timebase: 24,000 integer ticks per second."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .artifact import DomainValidationError


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("CanonicalTimeline", "GenerationSegmentTimeline", "TickRange", "TimelinePlacement")
TICKS_PER_SECOND = 24_000
TIMEBASE_VERSION = "v1-24000-ticks-per-second"


def _require_tick(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DomainValidationError(f"{field_name} must be a non-negative integer tick")


@dataclass(frozen=True)
class TickRange:
    start_tick: int
    end_tick: int

    def __post_init__(self) -> None:
        _require_tick(self.start_tick, "start_tick")
        _require_tick(self.end_tick, "end_tick")
        if self.end_tick < self.start_tick:
            raise DomainValidationError("end_tick must be greater than or equal to start_tick")

    @property
    def duration_ticks(self) -> int:
        return self.end_tick - self.start_tick

    def contains(self, tick: int) -> bool:
        _require_tick(tick, "tick")
        return self.start_tick <= tick < self.end_tick

    def seconds(self) -> Fraction:
        return Fraction(self.duration_ticks, TICKS_PER_SECOND)


@dataclass(frozen=True)
class CanonicalTimeline:
    ticks_per_second: int = TICKS_PER_SECOND
    timebase_version: str = TIMEBASE_VERSION

    def __post_init__(self) -> None:
        if (
            isinstance(self.ticks_per_second, bool)
            or not isinstance(self.ticks_per_second, int)
            or self.ticks_per_second != TICKS_PER_SECOND
        ):
            raise DomainValidationError("vNext canonical timebase is exactly 24000 ticks per second")
        if self.timebase_version != TIMEBASE_VERSION:
            raise DomainValidationError("timebase changes require a future versioned architecture capability")

    def seconds_for(self, ticks: int) -> Fraction:
        _require_tick(ticks, "ticks")
        return Fraction(ticks, TICKS_PER_SECOND)


@dataclass(frozen=True)
class TimelinePlacement:
    scope_id: str
    interval: TickRange

    def __post_init__(self) -> None:
        if not isinstance(self.scope_id, str) or not self.scope_id.strip():
            raise DomainValidationError("scope_id must be non-empty")
        if not isinstance(self.interval, TickRange):
            raise DomainValidationError("interval must be a TickRange")


@dataclass(frozen=True)
class GenerationSegmentTimeline:
    duration_ticks: int
    start_tick: int = 0

    def __post_init__(self) -> None:
        _require_tick(self.duration_ticks, "duration_ticks")
        if self.duration_ticks == 0:
            raise DomainValidationError("duration_ticks must be positive")
        if self.start_tick != 0:
            raise DomainValidationError("generation segment local time must start at tick 0")

    @property
    def interval(self) -> TickRange:
        return TickRange(0, self.duration_ticks)
