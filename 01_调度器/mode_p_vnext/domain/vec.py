"""Visual Execution Contract schemas; local assembly is introduced in A5."""

from __future__ import annotations

from dataclasses import dataclass

from .artifact import DomainValidationError
from .decisions import DecisionDraft, VisualCurvePointDraft
from .time import CanonicalTimeline, TickRange


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = (
    "ExecutionDesignDraft",
    "ShotDesignDraft",
    "VisualBeatDraft",
    "VisualExecutionContract",
    "VisualShot",
)


def _text_tuple(value: tuple[str, ...], field_name: str, *, require_items: bool = True) -> tuple[str, ...]:
    values = tuple(value)
    if (require_items and not values) or any(not isinstance(item, str) or not item.strip() for item in values):
        raise DomainValidationError(f"{field_name} must contain only non-empty text")
    return values


@dataclass(frozen=True)
class VisualBeatDraft:
    blocking_beat_ordinal: int
    visual_intent: str
    performance_focus: str
    continuity_constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.blocking_beat_ordinal, bool) or self.blocking_beat_ordinal < 1:
            raise DomainValidationError("blocking_beat_ordinal must be positive")
        if not self.visual_intent.strip() or not self.performance_focus.strip():
            raise DomainValidationError("visual_intent and performance_focus must be non-empty")
        object.__setattr__(self, "continuity_constraints", _text_tuple(self.continuity_constraints, "continuity_constraints"))


@dataclass(frozen=True)
class ShotDesignDraft:
    visual_beat_ordinal: int
    framing_intent: str
    camera_motion_intent: str
    focus_intent: str
    transition_intent: str

    def __post_init__(self) -> None:
        if isinstance(self.visual_beat_ordinal, bool) or self.visual_beat_ordinal < 1:
            raise DomainValidationError("visual_beat_ordinal must be positive")
        for field_name in ("framing_intent", "camera_motion_intent", "focus_intent", "transition_intent"):
            if not getattr(self, field_name).strip():
                raise DomainValidationError(f"{field_name} must be non-empty")


@dataclass(frozen=True)
class ExecutionDesignDraft:
    visual_beats: tuple[VisualBeatDraft, ...]
    shots: tuple[ShotDesignDraft, ...]
    curve_points: tuple[VisualCurvePointDraft, ...]
    decisions: tuple[DecisionDraft, ...]
    unresolved_questions: tuple[str, ...]

    def __post_init__(self) -> None:
        visual_beats = tuple(self.visual_beats)
        shots = tuple(self.shots)
        curves = tuple(self.curve_points)
        decisions = tuple(self.decisions)
        if not visual_beats or not all(isinstance(item, VisualBeatDraft) for item in visual_beats):
            raise DomainValidationError("visual_beats must contain VisualBeatDraft values")
        if not shots or not all(isinstance(item, ShotDesignDraft) for item in shots):
            raise DomainValidationError("shots must contain ShotDesignDraft values")
        if not curves or not all(isinstance(item, VisualCurvePointDraft) for item in curves):
            raise DomainValidationError("curve_points must contain VisualCurvePointDraft values")
        if not decisions or not all(isinstance(item, DecisionDraft) for item in decisions):
            raise DomainValidationError("decisions must contain DecisionDraft values")
        object.__setattr__(self, "visual_beats", visual_beats)
        object.__setattr__(self, "shots", shots)
        object.__setattr__(self, "curve_points", curves)
        object.__setattr__(self, "decisions", decisions)
        object.__setattr__(
            self,
            "unresolved_questions",
            _text_tuple(self.unresolved_questions, "unresolved_questions", require_items=False),
        )


@dataclass(frozen=True)
class VisualShot:
    shot_id: str
    source_shot_ordinal: int
    interval: TickRange
    framing: str
    camera_motion: str
    focus_target: str
    continuity_constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.shot_id.strip() or not self.framing.strip() or not self.camera_motion.strip() or not self.focus_target.strip():
            raise DomainValidationError("VisualShot textual fields must be non-empty")
        if isinstance(self.source_shot_ordinal, bool) or self.source_shot_ordinal < 1:
            raise DomainValidationError("source_shot_ordinal must be positive")
        if not isinstance(self.interval, TickRange):
            raise DomainValidationError("interval must be a TickRange")
        object.__setattr__(self, "continuity_constraints", _text_tuple(self.continuity_constraints, "continuity_constraints"))


@dataclass(frozen=True)
class VisualExecutionContract:
    contract_id: str
    scene_id: str
    execution_design_artifact_id: str
    timeline: CanonicalTimeline
    shots: tuple[VisualShot, ...]

    def __post_init__(self) -> None:
        if any(not getattr(self, field_name).strip() for field_name in ("contract_id", "scene_id", "execution_design_artifact_id")):
            raise DomainValidationError("VisualExecutionContract textual fields must be non-empty")
        if not isinstance(self.timeline, CanonicalTimeline):
            raise DomainValidationError("timeline must be a CanonicalTimeline")
        shots = tuple(self.shots)
        if not shots or not all(isinstance(item, VisualShot) for item in shots):
            raise DomainValidationError("shots must contain VisualShot values")
        object.__setattr__(self, "shots", shots)
