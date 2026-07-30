"""B1 creative Drafts and the locally assembled Visual Execution Contract."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import ClassVar

from .artifact import ArtifactKind, DomainValidationError
from .decisions import (
    DecisionDraft,
    DirectorDecision,
    VisualCurvePoint,
    VisualCurvePointDraft,
)
from .time import CanonicalTimeline, GenerationSegmentTimeline, TickRange


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = (
    "AudioEvent",
    "ExecutionDesignDraft",
    "GenerationSegment",
    "ReferenceRequirement",
    "ShotBoundary",
    "ShotDesignDraft",
    "StoryboardRole",
    "VisualBeat",
    "VisualBeatDraft",
    "VisualBeatPhase",
    "VisualExecutionContract",
    "VisualShot",
    "VoiceRequirement",
)


class VisualBeatPhase(str, enum.Enum):
    ENTRY = "entry"
    ACTION = "action"
    REACTION = "reaction"
    HANDOFF = "handoff"


class StoryboardRole(str, enum.Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    OMIT = "omit"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")


def _text_tuple(
    value: tuple[str, ...], field_name: str, *, require_items: bool
) -> tuple[str, ...]:
    values = tuple(value)
    if (require_items and not values) or any(
        not isinstance(item, str) or not item.strip() for item in values
    ):
        raise DomainValidationError(
            f"{field_name} must contain only non-empty text"
        )
    if len(values) != len(set(values)):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    return values


def _typed_tuple(
    value: tuple[object, ...],
    expected_type: type,
    field_name: str,
    *,
    require_items: bool,
) -> tuple:
    values = tuple(value)
    if (require_items and not values) or not all(
        isinstance(item, expected_type) for item in values
    ):
        raise DomainValidationError(
            f"{field_name} must contain {expected_type.__name__} values"
        )
    return values


def _require_positive_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DomainValidationError(f"{field_name} must be a positive integer")


@dataclass(frozen=True)
class VisualBeatDraft:
    phase: VisualBeatPhase
    subject_state: str
    attention: str
    storyboard_role: StoryboardRole

    def __post_init__(self) -> None:
        if not isinstance(self.phase, VisualBeatPhase):
            raise DomainValidationError(
                "phase must be entry, action, reaction, or handoff"
            )
        if not isinstance(self.storyboard_role, StoryboardRole):
            raise DomainValidationError(
                "storyboard_role must be required, optional, or omit"
            )
        _require_text(self.subject_state, "subject_state")
        _require_text(self.attention, "attention")


@dataclass(frozen=True)
class ShotDesignDraft:
    blocking_beat_ordinal: int
    dramatic_function: str
    attention_target: str
    information_action: str
    framing_intent: str
    camera_pose: str
    camera_motion: str
    composition: str
    lighting: str
    performance: str
    duration_weight: int
    visual_beats: tuple[VisualBeatDraft, ...]

    def __post_init__(self) -> None:
        _require_positive_integer(
            self.blocking_beat_ordinal, "blocking_beat_ordinal"
        )
        _require_positive_integer(self.duration_weight, "duration_weight")
        for field_name in (
            "dramatic_function",
            "attention_target",
            "information_action",
            "framing_intent",
            "camera_pose",
            "camera_motion",
            "composition",
            "lighting",
            "performance",
        ):
            _require_text(getattr(self, field_name), field_name)
        object.__setattr__(
            self,
            "visual_beats",
            _typed_tuple(
                self.visual_beats,
                VisualBeatDraft,
                "visual_beats",
                require_items=True,
            ),
        )


@dataclass(frozen=True)
class ExecutionDesignDraft:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = (
        ArtifactKind.EXECUTION_DESIGN_DRAFT
    )

    """Exactly the B1 creative output declared by architecture §5.3."""

    curve_points: tuple[VisualCurvePointDraft, ...]
    decisions: tuple[DecisionDraft, ...]
    shots: tuple[ShotDesignDraft, ...]
    transition_intents: tuple[str, ...]
    audio_intents: tuple[str, ...]
    reference_intents: tuple[str, ...]
    handoff_intent: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "curve_points",
            _typed_tuple(
                self.curve_points,
                VisualCurvePointDraft,
                "curve_points",
                require_items=True,
            ),
        )
        object.__setattr__(
            self,
            "decisions",
            _typed_tuple(
                self.decisions, DecisionDraft, "decisions", require_items=True
            ),
        )
        object.__setattr__(
            self,
            "shots",
            _typed_tuple(
                self.shots, ShotDesignDraft, "shots", require_items=True
            ),
        )
        for field_name in (
            "transition_intents",
            "audio_intents",
            "reference_intents",
        ):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(
                    getattr(self, field_name),
                    field_name,
                    require_items=False,
                ),
            )
        _require_text(self.handoff_intent, "handoff_intent")


@dataclass(frozen=True)
class GenerationSegment:
    segment_id: str
    timeline: GenerationSegmentTimeline
    shot_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.segment_id, "segment_id")
        if not isinstance(self.timeline, GenerationSegmentTimeline):
            raise DomainValidationError(
                "timeline must be a GenerationSegmentTimeline"
            )
        object.__setattr__(
            self,
            "shot_ids",
            _text_tuple(self.shot_ids, "shot_ids", require_items=True),
        )


@dataclass(frozen=True)
class VisualBeat:
    beat_id: str
    shot_id: str
    phase: VisualBeatPhase
    interval: TickRange
    subject_state: str
    attention: str
    storyboard_role: StoryboardRole
    start_state_id: str
    end_state_id: str
    decision_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "beat_id",
            "shot_id",
            "subject_state",
            "attention",
            "start_state_id",
            "end_state_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.phase, VisualBeatPhase):
            raise DomainValidationError("phase must be a VisualBeatPhase")
        if not isinstance(self.storyboard_role, StoryboardRole):
            raise DomainValidationError(
                "storyboard_role must be a StoryboardRole"
            )
        if (
            not isinstance(self.interval, TickRange)
            or self.interval.duration_ticks <= 0
        ):
            raise DomainValidationError(
                "VisualBeat interval must be a positive TickRange"
            )
        object.__setattr__(
            self,
            "decision_ids",
            _text_tuple(
                self.decision_ids, "decision_ids", require_items=False
            ),
        )


@dataclass(frozen=True)
class VisualShot:
    shot_id: str
    segment_id: str
    source_shot_ordinal: int
    blocking_beat_id: str
    interval: TickRange
    dramatic_function: str
    attention_target: str
    information_action: str
    framing_intent: str
    camera_pose: str
    camera_motion: str
    composition: str
    lighting: str
    performance: str
    visual_beats: tuple[VisualBeat, ...]
    decision_ids: tuple[str, ...]
    reference_requirement_ids: tuple[str, ...]
    audio_event_ids: tuple[str, ...]
    mirror_flip_forbidden: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "shot_id",
            "segment_id",
            "blocking_beat_id",
            "dramatic_function",
            "attention_target",
            "information_action",
            "framing_intent",
            "camera_pose",
            "camera_motion",
            "composition",
            "lighting",
            "performance",
        ):
            _require_text(getattr(self, field_name), field_name)
        _require_positive_integer(
            self.source_shot_ordinal, "source_shot_ordinal"
        )
        if (
            not isinstance(self.interval, TickRange)
            or self.interval.duration_ticks <= 0
        ):
            raise DomainValidationError(
                "VisualShot interval must be a positive TickRange"
            )
        beats = _typed_tuple(
            self.visual_beats,
            VisualBeat,
            "visual_beats",
            require_items=True,
        )
        if any(beat.shot_id != self.shot_id for beat in beats):
            raise DomainValidationError(
                "VisualBeat shot_id must match its VisualShot"
            )
        if beats[0].interval.start_tick != self.interval.start_tick:
            raise DomainValidationError(
                "VisualBeat coverage must start with its VisualShot"
            )
        if beats[-1].interval.end_tick != self.interval.end_tick:
            raise DomainValidationError(
                "VisualBeat coverage must end with its VisualShot"
            )
        for left, right in zip(beats, beats[1:]):
            if left.interval.end_tick != right.interval.start_tick:
                raise DomainValidationError(
                    "VisualBeat intervals must be adjacent"
                )
            if left.end_state_id != right.start_state_id:
                raise DomainValidationError(
                    "VisualBeat states must form an adjacent chain"
                )
        if self.mirror_flip_forbidden is not True:
            raise DomainValidationError(
                "mirror_flip_forbidden is a local safety constant"
            )
        object.__setattr__(self, "visual_beats", beats)
        for field_name, require_items in (
            ("decision_ids", True),
            ("reference_requirement_ids", False),
            ("audio_event_ids", False),
        ):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(
                    getattr(self, field_name),
                    field_name,
                    require_items=require_items,
                ),
            )


@dataclass(frozen=True)
class ShotBoundary:
    boundary_id: str
    segment_id: str
    from_shot_id: str
    to_shot_id: str
    transition_intent: str
    decision_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "boundary_id",
            "segment_id",
            "from_shot_id",
            "to_shot_id",
            "transition_intent",
        ):
            _require_text(getattr(self, field_name), field_name)
        if self.from_shot_id == self.to_shot_id:
            raise DomainValidationError(
                "a ShotBoundary must connect two different shots"
            )
        object.__setattr__(
            self,
            "decision_ids",
            _text_tuple(
                self.decision_ids, "decision_ids", require_items=False
            ),
        )


@dataclass(frozen=True)
class AudioEvent:
    event_id: str
    segment_id: str
    interval: TickRange
    source_fact_id: str
    character_id: str
    text: str

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "segment_id",
            "source_fact_id",
            "character_id",
            "text",
        ):
            _require_text(getattr(self, field_name), field_name)
        if (
            not isinstance(self.interval, TickRange)
            or self.interval.duration_ticks <= 0
        ):
            raise DomainValidationError(
                "AudioEvent interval must be a positive TickRange"
            )


@dataclass(frozen=True)
class VoiceRequirement:
    requirement_id: str
    audio_event_id: str
    character_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "requirement_id",
            "audio_event_id",
            "character_id",
        ):
            _require_text(getattr(self, field_name), field_name)


@dataclass(frozen=True)
class ReferenceRequirement:
    requirement_id: str
    role: str
    scope_kind: str
    scope_id: str
    source_fact_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "requirement_id",
            "role",
            "scope_kind",
            "scope_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        object.__setattr__(
            self,
            "source_fact_ids",
            _text_tuple(
                self.source_fact_ids, "source_fact_ids", require_items=True
            ),
        )


@dataclass(frozen=True)
class VisualExecutionContract:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = (
        ArtifactKind.VISUAL_EXECUTION_CONTRACT
    )

    """The sole machine-readable creative authority for both projections."""

    contract_id: str
    scene_id: str
    execution_design_artifact_id: str
    blocking_commit_artifact_id: str
    source_fact_ids: tuple[str, ...]
    timeline: CanonicalTimeline
    curve_points: tuple[VisualCurvePoint, ...]
    decisions: tuple[DirectorDecision, ...]
    segments: tuple[GenerationSegment, ...]
    shots: tuple[VisualShot, ...]
    boundaries: tuple[ShotBoundary, ...]
    audio_events: tuple[AudioEvent, ...]
    voice_requirements: tuple[VoiceRequirement, ...]
    reference_requirements: tuple[ReferenceRequirement, ...]
    handoff_intent: str

    def __post_init__(self) -> None:
        for field_name in (
            "contract_id",
            "scene_id",
            "execution_design_artifact_id",
            "blocking_commit_artifact_id",
            "handoff_intent",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.timeline, CanonicalTimeline):
            raise DomainValidationError(
                "timeline must be the canonical 24000-tick timeline"
            )
        object.__setattr__(
            self,
            "source_fact_ids",
            _text_tuple(
                self.source_fact_ids, "source_fact_ids", require_items=True
            ),
        )
        typed_fields = (
            ("curve_points", VisualCurvePoint, True),
            ("decisions", DirectorDecision, True),
            ("segments", GenerationSegment, True),
            ("shots", VisualShot, True),
            ("boundaries", ShotBoundary, False),
            ("audio_events", AudioEvent, False),
            ("voice_requirements", VoiceRequirement, False),
            ("reference_requirements", ReferenceRequirement, True),
        )
        for field_name, item_type, required in typed_fields:
            object.__setattr__(
                self,
                field_name,
                _typed_tuple(
                    getattr(self, field_name),
                    item_type,
                    field_name,
                    require_items=required,
                ),
            )
        self._validate_graph()

    def _validate_graph(self) -> None:
        collections = (
            ("curve point", tuple(item.point_id for item in self.curve_points)),
            ("decision", tuple(item.decision_id for item in self.decisions)),
            ("segment", tuple(item.segment_id for item in self.segments)),
            ("shot", tuple(item.shot_id for item in self.shots)),
            ("boundary", tuple(item.boundary_id for item in self.boundaries)),
            ("audio event", tuple(item.event_id for item in self.audio_events)),
            (
                "voice requirement",
                tuple(item.requirement_id for item in self.voice_requirements),
            ),
            (
                "reference requirement",
                tuple(item.requirement_id for item in self.reference_requirements),
            ),
        )
        all_ids: list[str] = [self.contract_id]
        for label, identifiers in collections:
            if len(identifiers) != len(set(identifiers)):
                raise DomainValidationError(f"{label} IDs must be unique")
            all_ids.extend(identifiers)
        beat_ids = tuple(
            beat.beat_id for shot in self.shots for beat in shot.visual_beats
        )
        if len(beat_ids) != len(set(beat_ids)):
            raise DomainValidationError("VisualBeat IDs must be unique")
        all_ids.extend(beat_ids)
        if len(all_ids) != len(set(all_ids)):
            raise DomainValidationError(
                "all machine-generated VEC IDs must be globally unique"
            )

        decisions = {item.decision_id for item in self.decisions}
        references = {
            item.requirement_id for item in self.reference_requirements
        }
        audio = {item.event_id for item in self.audio_events}
        shots = {item.shot_id: item for item in self.shots}
        segments = {item.segment_id: item for item in self.segments}

        if tuple(shot.source_shot_ordinal for shot in self.shots) != tuple(
            range(1, len(self.shots) + 1)
        ):
            raise DomainValidationError(
                "source shot ordinals must be sequential from one"
            )
        for shot in self.shots:
            if shot.segment_id not in segments:
                raise DomainValidationError(
                    "each VisualShot must belong to a declared segment"
                )
            segment = segments[shot.segment_id]
            if not (
                0
                <= shot.interval.start_tick
                < shot.interval.end_tick
                <= segment.timeline.duration_ticks
            ):
                raise DomainValidationError(
                    "VisualShot intervals must stay inside local segment time"
                )
            if not set(shot.decision_ids).issubset(decisions):
                raise DomainValidationError(
                    "VisualShot decision references must resolve"
                )
            if not set(shot.reference_requirement_ids).issubset(references):
                raise DomainValidationError(
                    "VisualShot reference requirements must resolve"
                )
            if not set(shot.audio_event_ids).issubset(audio):
                raise DomainValidationError(
                    "VisualShot audio event references must resolve"
                )
            for beat in shot.visual_beats:
                if not set(beat.decision_ids).issubset(decisions):
                    raise DomainValidationError(
                        "VisualBeat decision references must resolve"
                    )

        covered_shots = tuple(
            shot_id for segment in self.segments for shot_id in segment.shot_ids
        )
        if len(covered_shots) != len(set(covered_shots)):
            raise DomainValidationError(
                "a VisualShot cannot belong to multiple segments"
            )
        if set(covered_shots) != set(shots):
            raise DomainValidationError(
                "segments must cover every VisualShot exactly once"
            )

        boundary_pairs: dict[str, set[tuple[str, str]]] = {
            segment_id: set() for segment_id in segments
        }
        for boundary in self.boundaries:
            if boundary.segment_id not in segments:
                raise DomainValidationError(
                    "ShotBoundary must belong to a declared segment"
                )
            if (
                boundary.from_shot_id not in shots
                or boundary.to_shot_id not in shots
            ):
                raise DomainValidationError(
                    "ShotBoundary endpoints must resolve"
                )
            left = shots[boundary.from_shot_id]
            right = shots[boundary.to_shot_id]
            if (
                left.segment_id != boundary.segment_id
                or right.segment_id != boundary.segment_id
            ):
                raise DomainValidationError(
                    "ShotBoundary cannot cross generation segments"
                )
            if left.interval.end_tick != right.interval.start_tick:
                raise DomainValidationError(
                    "ShotBoundary endpoints must be tick-adjacent"
                )
            if not set(boundary.decision_ids).issubset(decisions):
                raise DomainValidationError(
                    "ShotBoundary decision references must resolve"
                )
            pair = (boundary.from_shot_id, boundary.to_shot_id)
            if pair in boundary_pairs[boundary.segment_id]:
                raise DomainValidationError(
                    "duplicate ShotBoundary endpoints are forbidden"
                )
            boundary_pairs[boundary.segment_id].add(pair)

        for segment in self.segments:
            ordered = tuple(shots[shot_id] for shot_id in segment.shot_ids)
            if ordered[0].interval.start_tick != 0:
                raise DomainValidationError(
                    "each segment's first shot must start at local tick zero"
                )
            if (
                ordered[-1].interval.end_tick
                != segment.timeline.duration_ticks
            ):
                raise DomainValidationError(
                    "each segment's final shot must end at segment duration"
                )
            expected_pairs = {
                (left.shot_id, right.shot_id)
                for left, right in zip(ordered, ordered[1:])
            }
            if boundary_pairs[segment.segment_id] != expected_pairs:
                raise DomainValidationError(
                    "ShotBoundaries must cover every adjacent shot pair"
                )

        event_ids = {item.event_id for item in self.audio_events}
        voice_event_ids = tuple(
            item.audio_event_id for item in self.voice_requirements
        )
        if set(voice_event_ids) != event_ids or len(voice_event_ids) != len(
            set(voice_event_ids)
        ):
            raise DomainValidationError(
                "each AudioEvent requires exactly one VoiceRequirement"
            )
        for event in self.audio_events:
            if event.segment_id not in segments:
                raise DomainValidationError(
                    "AudioEvent must belong to a declared segment"
                )
            segment = segments[event.segment_id]
            if not (
                0
                <= event.interval.start_tick
                < event.interval.end_tick
                <= segment.timeline.duration_ticks
            ):
                raise DomainValidationError(
                    "AudioEvent intervals must stay inside local segment time"
                )
