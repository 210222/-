"""The sole v3.0 timebase and versioned generation-capability contracts."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from fractions import Fraction

from .artifact import DOMAIN_SCHEMA_VERSION, DomainValidationError


CANONICAL_DOMAIN_TYPES = (
    "CanonicalTimeline",
    "DurationIntent",
    "DurationOption",
    "EpisodeTimeline",
    "GenerationCapabilityProfile",
    "GenerationUnitTimeline",
    "SceneTimeline",
    "TickMarker",
    "TickRange",
    "TimelinePlacement",
)
TICKS_PER_SECOND = 24_000
TIMEBASE_VERSION = "v3-24000-ticks-per-second"
SD20_MAX_GENERATION_TICKS = 360_000


def _require_tick(value: int, field_name: str, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < (1 if positive else 0):
        qualifier = "positive" if positive else "non-negative"
        raise DomainValidationError(f"{field_name} must be a {qualifier} integer tick")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")


class DurationIntent(str, enum.Enum):
    BRIEF = "brief"
    STANDARD = "standard"
    EXTENDED = "extended"


@dataclass(frozen=True)
class TickRange:
    """A persistent half-open interval. Zero-length intervals are forbidden."""

    start_tick: int
    end_tick: int

    def __post_init__(self) -> None:
        _require_tick(self.start_tick, "start_tick")
        _require_tick(self.end_tick, "end_tick")
        if self.end_tick <= self.start_tick:
            raise DomainValidationError("TickRange requires start_tick < end_tick")

    @property
    def duration_ticks(self) -> int:
        return self.end_tick - self.start_tick

    def contains(self, tick: int) -> bool:
        _require_tick(tick, "tick")
        return self.start_tick <= tick < self.end_tick

    def seconds(self) -> Fraction:
        return Fraction(self.duration_ticks, TICKS_PER_SECOND)


@dataclass(frozen=True)
class TickMarker:
    """An event position; it intentionally makes no duration claim."""

    tick: int

    def __post_init__(self) -> None:
        _require_tick(self.tick, "tick")


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
            raise DomainValidationError("timebase changes require a versioned architecture change")

    def seconds_for(self, ticks: int) -> Fraction:
        _require_tick(ticks, "ticks")
        return Fraction(ticks, TICKS_PER_SECOND)


@dataclass(frozen=True)
class TimelinePlacement:
    scope_id: str
    parent_scope_id: str
    interval: TickRange

    def __post_init__(self) -> None:
        _require_text(self.scope_id, "scope_id")
        _require_text(self.parent_scope_id, "parent_scope_id")
        if self.scope_id == self.parent_scope_id:
            raise DomainValidationError("a timeline scope cannot be its own parent")
        if not isinstance(self.interval, TickRange):
            raise DomainValidationError("interval must be a TickRange")


def _validate_adjacent_placements(
    placements: tuple[TimelinePlacement, ...],
    *,
    parent_scope_id: str,
    interval: TickRange,
) -> tuple[TimelinePlacement, ...]:
    values = tuple(placements)
    if not values or not all(isinstance(item, TimelinePlacement) for item in values):
        raise DomainValidationError("timeline placements must contain TimelinePlacement values")
    if any(item.parent_scope_id != parent_scope_id for item in values):
        raise DomainValidationError("timeline placement parent does not match its timeline")
    if len({item.scope_id for item in values}) != len(values):
        raise DomainValidationError("timeline placement scope IDs must be unique")
    if values[0].interval.start_tick != interval.start_tick:
        raise DomainValidationError("timeline placements must start at the parent start")
    if values[-1].interval.end_tick != interval.end_tick:
        raise DomainValidationError("timeline placements must end at the parent end")
    if any(
        left.interval.end_tick != right.interval.start_tick
        for left, right in zip(values, values[1:])
    ):
        raise DomainValidationError("timeline placements must be ordered and adjacent")
    return values


@dataclass(frozen=True)
class SceneTimeline:
    scene_id: str
    interval: TickRange
    generation_unit_placements: tuple[TimelinePlacement, ...]

    def __post_init__(self) -> None:
        _require_text(self.scene_id, "scene_id")
        if not isinstance(self.interval, TickRange) or self.interval.start_tick != 0:
            raise DomainValidationError("SceneTimeline must use scene-local time starting at zero")
        object.__setattr__(
            self,
            "generation_unit_placements",
            _validate_adjacent_placements(
                self.generation_unit_placements,
                parent_scope_id=self.scene_id,
                interval=self.interval,
            ),
        )


@dataclass(frozen=True)
class EpisodeTimeline:
    episode_id: str
    interval: TickRange
    scene_placements: tuple[TimelinePlacement, ...]

    def __post_init__(self) -> None:
        _require_text(self.episode_id, "episode_id")
        if not isinstance(self.interval, TickRange) or self.interval.start_tick != 0:
            raise DomainValidationError("EpisodeTimeline must use episode-local time starting at zero")
        object.__setattr__(
            self,
            "scene_placements",
            _validate_adjacent_placements(
                self.scene_placements,
                parent_scope_id=self.episode_id,
                interval=self.interval,
            ),
        )


@dataclass(frozen=True)
class DurationOption:
    intent: DurationIntent
    min_ticks: int
    target_ticks: int
    max_ticks: int

    def __post_init__(self) -> None:
        if not isinstance(self.intent, DurationIntent):
            raise DomainValidationError("intent must be a DurationIntent")
        for name in ("min_ticks", "target_ticks", "max_ticks"):
            _require_tick(getattr(self, name), name, positive=True)
        if not self.min_ticks <= self.target_ticks <= self.max_ticks:
            raise DomainValidationError("duration option requires min <= target <= max")


@dataclass(frozen=True)
class GenerationCapabilityProfile:
    profile_id: str
    profile_version: str
    max_generation_ticks: int
    duration_options: tuple[DurationOption, ...]

    def __post_init__(self) -> None:
        _require_text(self.profile_id, "profile_id")
        _require_text(self.profile_version, "profile_version")
        _require_tick(self.max_generation_ticks, "max_generation_ticks", positive=True)
        options = tuple(self.duration_options)
        if not options or not all(isinstance(item, DurationOption) for item in options):
            raise DomainValidationError("duration_options must contain DurationOption values")
        intents = tuple(item.intent for item in options)
        if set(intents) != set(DurationIntent) or len(intents) != len(set(intents)):
            raise DomainValidationError("capability must map every DurationIntent exactly once")
        if any(item.max_ticks > self.max_generation_ticks for item in options):
            raise DomainValidationError("duration option exceeds capability max_generation_ticks")
        object.__setattr__(self, "duration_options", options)

    def option_for(self, intent: DurationIntent) -> DurationOption:
        if not isinstance(intent, DurationIntent):
            raise DomainValidationError("models may select only a DurationIntent enum")
        return next(item for item in self.duration_options if item.intent is intent)

    @classmethod
    def sd20_default(cls) -> "GenerationCapabilityProfile":
        return cls(
            profile_id="sd2.0",
            profile_version="3.0.0",
            max_generation_ticks=SD20_MAX_GENERATION_TICKS,
            duration_options=(
                DurationOption(DurationIntent.BRIEF, 48_000, 96_000, 144_000),
                DurationOption(DurationIntent.STANDARD, 120_000, 192_000, 264_000),
                DurationOption(DurationIntent.EXTENDED, 240_000, 312_000, 360_000),
            ),
        )


@dataclass(frozen=True)
class GenerationUnitTimeline:
    duration_ticks: int
    capability_profile_id: str
    capability_profile_version: str
    max_generation_ticks: int
    start_tick: int = 0

    def __post_init__(self) -> None:
        _require_tick(self.duration_ticks, "duration_ticks", positive=True)
        _require_text(self.capability_profile_id, "capability_profile_id")
        _require_text(self.capability_profile_version, "capability_profile_version")
        _require_tick(self.max_generation_ticks, "max_generation_ticks", positive=True)
        if self.start_tick != 0:
            raise DomainValidationError("generation-unit local time must start at tick zero")
        if self.duration_ticks > self.max_generation_ticks:
            raise DomainValidationError("generation-unit duration exceeds capability")

    @property
    def interval(self) -> TickRange:
        return TickRange(0, self.duration_ticks)
