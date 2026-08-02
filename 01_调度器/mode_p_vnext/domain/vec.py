"""v3.0 B1 creative Drafts and the locally assembled VEC contract."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import ClassVar

from .artifact import (
    DOMAIN_SCHEMA_VERSION,
    ArtifactKind,
    DomainValidationError,
    require_sha256,
)
from .decisions import (
    DecisionDraft,
    DirectorDecision,
    VisualCurvePoint,
    VisualCurvePointDraft,
)
from .facts import require_opaque_handle, require_opaque_id
from .time import (
    CanonicalTimeline,
    DurationIntent,
    GenerationCapabilityProfile,
    GenerationUnitTimeline,
    SceneTimeline,
    TickMarker,
    TickRange,
    TimelinePlacement,
)


CANONICAL_DOMAIN_TYPES = (
    "AudioEvent",
    "DialogueBindingIntent",
    "ExecutionDesignDraft",
    "GenerationMode",
    "GenerationUnit",
    "PlacementPhase",
    "ReferenceBindingIntent",
    "ReferenceRequirement",
    "ReferenceResponsibility",
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


class PlacementPhase(str, enum.Enum):
    OPENING = "opening"
    EARLY = "early"
    MIDDLE = "middle"
    LATE = "late"
    CLOSING = "closing"


class GenerationMode(str, enum.Enum):
    TEXT_ONLY = "text_only"
    FIRST_LAST_FRAME = "first_last_frame"
    OMNI_REFERENCE = "omni_reference"


class ReferenceResponsibility(str, enum.Enum):
    CHARACTER_IDENTITY = "character_identity"
    WARDROBE_CONTINUITY = "wardrobe_continuity"
    PROP_IDENTITY = "prop_identity"
    SETTING_CONTINUITY = "setting_continuity"
    FIRST_FRAME = "first_frame"
    LAST_FRAME = "last_frame"


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
        raise DomainValidationError(f"{field_name} must contain only non-empty text")
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
    visual_beat_ordinal: int
    phase: VisualBeatPhase
    subject_state: str
    attention: str
    storyboard_role: StoryboardRole

    def __post_init__(self) -> None:
        _require_positive_integer(self.visual_beat_ordinal, "visual_beat_ordinal")
        if not isinstance(self.phase, VisualBeatPhase):
            raise DomainValidationError("phase must be a VisualBeatPhase")
        if not isinstance(self.storyboard_role, StoryboardRole):
            raise DomainValidationError("storyboard_role must be a StoryboardRole")
        _require_text(self.subject_state, "subject_state")
        _require_text(self.attention, "attention")


@dataclass(frozen=True)
class ReferenceBindingIntent:
    shot_ordinal: int
    visual_beat_ordinal: int | None
    fact_handle: str
    responsibility: ReferenceResponsibility

    def __post_init__(self) -> None:
        _require_positive_integer(self.shot_ordinal, "shot_ordinal")
        if self.visual_beat_ordinal is not None:
            _require_positive_integer(self.visual_beat_ordinal, "visual_beat_ordinal")
        require_opaque_handle(self.fact_handle)
        if not isinstance(self.responsibility, ReferenceResponsibility):
            raise DomainValidationError("responsibility must be a ReferenceResponsibility")


@dataclass(frozen=True)
class DialogueBindingIntent:
    shot_ordinal: int
    visual_beat_ordinal: int
    fact_handle: str
    placement_phase: PlacementPhase

    def __post_init__(self) -> None:
        _require_positive_integer(self.shot_ordinal, "shot_ordinal")
        _require_positive_integer(self.visual_beat_ordinal, "visual_beat_ordinal")
        require_opaque_handle(self.fact_handle)
        if not isinstance(self.placement_phase, PlacementPhase):
            raise DomainValidationError("placement_phase must be a PlacementPhase")


@dataclass(frozen=True)
class ShotDesignDraft:
    """Director choice surface: creative intent and typed bindings, never raw ticks."""

    shot_ordinal: int
    blocking_beat_ordinal: int
    duration_intent: DurationIntent
    generation_mode: GenerationMode
    composition: str
    camera: str
    lighting: str
    performance: str
    visual_beats: tuple[VisualBeatDraft, ...]
    reference_binding_intents: tuple[ReferenceBindingIntent, ...]
    dialogue_binding_intents: tuple[DialogueBindingIntent, ...]
    creative_notes: str

    def __post_init__(self) -> None:
        _require_positive_integer(self.shot_ordinal, "shot_ordinal")
        _require_positive_integer(self.blocking_beat_ordinal, "blocking_beat_ordinal")
        if not isinstance(self.duration_intent, DurationIntent):
            raise DomainValidationError("duration_intent must be a DurationIntent")
        if not isinstance(self.generation_mode, GenerationMode):
            raise DomainValidationError("generation_mode must be a GenerationMode")
        for field_name in ("composition", "camera", "lighting", "performance", "creative_notes"):
            _require_text(getattr(self, field_name), field_name)
        beats = _typed_tuple(
            self.visual_beats, VisualBeatDraft, "visual_beats", require_items=True
        )
        if tuple(item.visual_beat_ordinal for item in beats) != tuple(
            range(1, len(beats) + 1)
        ):
            raise DomainValidationError("visual beat ordinals must be sequential from one")
        references = _typed_tuple(
            self.reference_binding_intents,
            ReferenceBindingIntent,
            "reference_binding_intents",
            require_items=False,
        )
        dialogues = _typed_tuple(
            self.dialogue_binding_intents,
            DialogueBindingIntent,
            "dialogue_binding_intents",
            require_items=False,
        )
        beat_ordinals = {item.visual_beat_ordinal for item in beats}
        for intent in (*references, *dialogues):
            if intent.shot_ordinal != self.shot_ordinal:
                raise DomainValidationError("typed binding shot_ordinal must match its ShotDesignDraft")
            beat_ordinal = intent.visual_beat_ordinal
            if beat_ordinal is not None and beat_ordinal not in beat_ordinals:
                raise DomainValidationError("typed binding references an unknown VisualBeatDraft")
        reference_keys = tuple(
            (item.visual_beat_ordinal, item.fact_handle, item.responsibility)
            for item in references
        )
        dialogue_keys = tuple(
            (item.visual_beat_ordinal, item.fact_handle, item.placement_phase)
            for item in dialogues
        )
        if len(reference_keys) != len(set(reference_keys)):
            raise DomainValidationError("duplicate reference binding intents are forbidden")
        if len(dialogue_keys) != len(set(dialogue_keys)):
            raise DomainValidationError("duplicate dialogue binding intents are forbidden")
        object.__setattr__(self, "visual_beats", beats)
        object.__setattr__(self, "reference_binding_intents", references)
        object.__setattr__(self, "dialogue_binding_intents", dialogues)


@dataclass(frozen=True)
class ExecutionDesignDraft:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.EXECUTION_DESIGN_DRAFT

    curve_points: tuple[VisualCurvePointDraft, ...]
    decisions: tuple[DecisionDraft, ...]
    shots: tuple[ShotDesignDraft, ...]
    transition_intents: tuple[str, ...]
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
            _typed_tuple(self.decisions, DecisionDraft, "decisions", require_items=True),
        )
        shots = _typed_tuple(self.shots, ShotDesignDraft, "shots", require_items=True)
        if tuple(item.shot_ordinal for item in shots) != tuple(range(1, len(shots) + 1)):
            raise DomainValidationError("shot ordinals must be sequential from one")
        object.__setattr__(self, "shots", shots)
        object.__setattr__(
            self,
            "transition_intents",
            _text_tuple(self.transition_intents, "transition_intents", require_items=False),
        )
        _require_text(self.handoff_intent, "handoff_intent")


@dataclass(frozen=True)
class GenerationUnit:
    unit_id: str
    shot_id: str
    generation_mode: GenerationMode
    timeline: GenerationUnitTimeline
    scene_placement: TimelinePlacement

    def __post_init__(self) -> None:
        _require_text(self.unit_id, "unit_id")
        _require_text(self.shot_id, "shot_id")
        if not isinstance(self.generation_mode, GenerationMode):
            raise DomainValidationError("generation_mode must be a GenerationMode")
        if not isinstance(self.timeline, GenerationUnitTimeline):
            raise DomainValidationError("timeline must be a GenerationUnitTimeline")
        if not isinstance(self.scene_placement, TimelinePlacement):
            raise DomainValidationError("scene_placement must be a TimelinePlacement")
        if self.scene_placement.scope_id != self.unit_id:
            raise DomainValidationError("scene placement must target its GenerationUnit")
        if self.scene_placement.interval.duration_ticks != self.timeline.duration_ticks:
            raise DomainValidationError("local and scene placement durations must match")


@dataclass(frozen=True)
class VisualBeat:
    beat_id: str
    shot_id: str
    source_visual_beat_ordinal: int
    phase: VisualBeatPhase
    interval: TickRange
    subject_state: str
    attention: str
    storyboard_role: StoryboardRole
    start_state_id: str
    end_state_id: str
    decision_ids: tuple[str, ...]
    reference_requirement_ids: tuple[str, ...]
    audio_event_ids: tuple[str, ...]

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
        _require_positive_integer(
            self.source_visual_beat_ordinal, "source_visual_beat_ordinal"
        )
        if not isinstance(self.phase, VisualBeatPhase):
            raise DomainValidationError("phase must be a VisualBeatPhase")
        if not isinstance(self.storyboard_role, StoryboardRole):
            raise DomainValidationError("storyboard_role must be a StoryboardRole")
        if not isinstance(self.interval, TickRange):
            raise DomainValidationError("interval must be a positive TickRange")
        for field_name in (
            "decision_ids",
            "reference_requirement_ids",
            "audio_event_ids",
        ):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(getattr(self, field_name), field_name, require_items=False),
            )


@dataclass(frozen=True)
class VisualShot:
    shot_id: str
    generation_unit_id: str
    source_shot_ordinal: int
    blocking_beat_id: str
    generation_mode: GenerationMode
    interval: TickRange
    composition: str
    camera: str
    lighting: str
    performance: str
    creative_notes: str
    visual_beats: tuple[VisualBeat, ...]
    decision_ids: tuple[str, ...]
    reference_requirement_ids: tuple[str, ...]
    audio_event_ids: tuple[str, ...]
    mirror_flip_forbidden: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "shot_id",
            "generation_unit_id",
            "blocking_beat_id",
            "composition",
            "camera",
            "lighting",
            "performance",
            "creative_notes",
        ):
            _require_text(getattr(self, field_name), field_name)
        _require_positive_integer(self.source_shot_ordinal, "source_shot_ordinal")
        if not isinstance(self.generation_mode, GenerationMode):
            raise DomainValidationError("generation_mode must be a GenerationMode")
        if not isinstance(self.interval, TickRange) or self.interval.start_tick != 0:
            raise DomainValidationError("VisualShot must use generation-unit local time from zero")
        beats = _typed_tuple(self.visual_beats, VisualBeat, "visual_beats", require_items=True)
        if tuple(item.source_visual_beat_ordinal for item in beats) != tuple(
            range(1, len(beats) + 1)
        ):
            raise DomainValidationError("VisualBeat ordinals must be sequential from one")
        if any(item.shot_id != self.shot_id for item in beats):
            raise DomainValidationError("VisualBeat shot_id must match its VisualShot")
        if beats[0].interval.start_tick != 0 or beats[-1].interval.end_tick != self.interval.end_tick:
            raise DomainValidationError("VisualBeat intervals must cover their complete shot")
        for left, right in zip(beats, beats[1:]):
            if left.interval.end_tick != right.interval.start_tick:
                raise DomainValidationError("VisualBeat intervals must be adjacent")
            if left.end_state_id != right.start_state_id:
                raise DomainValidationError("VisualBeat states must form an adjacent chain")
        if self.mirror_flip_forbidden is not True:
            raise DomainValidationError("mirror_flip_forbidden is a local safety constant")
        object.__setattr__(self, "visual_beats", beats)
        for field_name in (
            "decision_ids",
            "reference_requirement_ids",
            "audio_event_ids",
        ):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(getattr(self, field_name), field_name, require_items=False),
            )


@dataclass(frozen=True)
class ShotBoundary:
    boundary_id: str
    boundary_ordinal: int
    scene_tick: int
    from_shot_id: str | None
    to_shot_id: str | None
    before_state_id: str
    after_state_id: str
    transition_intent: str
    decision_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.boundary_id, "boundary_id")
        if isinstance(self.boundary_ordinal, bool) or not isinstance(self.boundary_ordinal, int) or self.boundary_ordinal < 0:
            raise DomainValidationError("boundary_ordinal must be non-negative")
        if isinstance(self.scene_tick, bool) or not isinstance(self.scene_tick, int) or self.scene_tick < 0:
            raise DomainValidationError("scene_tick must be a non-negative integer tick")
        if self.from_shot_id is None and self.to_shot_id is None:
            raise DomainValidationError("a boundary must connect the scene edge or two shots")
        for field_name in ("from_shot_id", "to_shot_id"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        if self.from_shot_id is not None and self.from_shot_id == self.to_shot_id:
            raise DomainValidationError("a boundary cannot connect a shot to itself")
        for field_name in ("before_state_id", "after_state_id", "transition_intent"):
            _require_text(getattr(self, field_name), field_name)
        object.__setattr__(
            self,
            "decision_ids",
            _text_tuple(self.decision_ids, "decision_ids", require_items=False),
        )


@dataclass(frozen=True)
class AudioEvent:
    event_id: str
    source_fact_id: str
    source_fact_handle: str
    shot_id: str
    visual_beat_id: str
    marker: TickMarker
    placement_phase: PlacementPhase
    character_label: str
    text: str
    media_duration_ticks: int | None = None

    def __post_init__(self) -> None:
        for field_name in ("event_id", "shot_id", "visual_beat_id", "character_label", "text"):
            _require_text(getattr(self, field_name), field_name)
        require_opaque_id(self.source_fact_id, "source_fact_id")
        require_opaque_handle(self.source_fact_handle, "source_fact_handle")
        if not isinstance(self.marker, TickMarker):
            raise DomainValidationError("marker must be a TickMarker")
        if not isinstance(self.placement_phase, PlacementPhase):
            raise DomainValidationError("placement_phase must be a PlacementPhase")
        if self.media_duration_ticks is not None and (
            isinstance(self.media_duration_ticks, bool)
            or not isinstance(self.media_duration_ticks, int)
            or self.media_duration_ticks < 1
        ):
            raise DomainValidationError("media_duration_ticks must be positive when real metadata exists")


@dataclass(frozen=True)
class VoiceRequirement:
    requirement_id: str
    audio_event_id: str
    character_label: str
    shot_id: str
    visual_beat_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "requirement_id",
            "audio_event_id",
            "character_label",
            "shot_id",
            "visual_beat_id",
        ):
            _require_text(getattr(self, field_name), field_name)


@dataclass(frozen=True)
class ReferenceRequirement:
    requirement_id: str
    responsibility: ReferenceResponsibility
    source_fact_id: str
    source_fact_handle: str
    shot_id: str
    visual_beat_id: str | None

    def __post_init__(self) -> None:
        _require_text(self.requirement_id, "requirement_id")
        _require_text(self.shot_id, "shot_id")
        if self.visual_beat_id is not None:
            _require_text(self.visual_beat_id, "visual_beat_id")
        if not isinstance(self.responsibility, ReferenceResponsibility):
            raise DomainValidationError("responsibility must be a ReferenceResponsibility")
        require_opaque_id(self.source_fact_id, "source_fact_id")
        require_opaque_handle(self.source_fact_handle, "source_fact_handle")


@dataclass(frozen=True)
class VisualExecutionContract:
    """The sole local VEC authority with an exact approved-fact mapping.

    ``source_fact_ids`` and ``approved_fact_handles`` are parallel immutable
    tuples.  Their shared ordinal is part of the canonical contract: index
    ``n`` describes one approved ``(fact_id, fact_handle)`` pair, rather than
    two independently approved sets.  The director sees handles only; local
    assembly preserves the corresponding opaque IDs for auditability.
    """

    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.VISUAL_EXECUTION_CONTRACT

    contract_id: str
    episode_id: str
    scene_id: str
    execution_design_artifact_id: str
    blocking_commit_artifact_id: str
    source_fact_ids: tuple[str, ...]
    approved_fact_handles: tuple[str, ...]
    timeline: CanonicalTimeline
    scene_timeline: SceneTimeline
    capability_profile: GenerationCapabilityProfile
    curve_points: tuple[VisualCurvePoint, ...]
    decisions: tuple[DirectorDecision, ...]
    generation_units: tuple[GenerationUnit, ...]
    shots: tuple[VisualShot, ...]
    boundaries: tuple[ShotBoundary, ...]
    audio_events: tuple[AudioEvent, ...]
    voice_requirements: tuple[VoiceRequirement, ...]
    reference_requirements: tuple[ReferenceRequirement, ...]
    handoff_intent: str
    canonical_input_sha256: str
    canonical_output_sha256: str

    @property
    def approved_fact_pairs(self) -> tuple[tuple[str, str], ...]:
        """Return the canonical, ordered ID-to-handle approval mapping.

        This is deliberately a derived read-only view, not another persistent
        representation.  It lets every local verifier consume the exact pair
        without guessing from IDs, handles, text, prefixes, or source spans.
        """

        return tuple(zip(self.source_fact_ids, self.approved_fact_handles))

    def __post_init__(self) -> None:
        for field_name in (
            "contract_id",
            "episode_id",
            "scene_id",
            "execution_design_artifact_id",
            "blocking_commit_artifact_id",
            "handoff_intent",
        ):
            _require_text(getattr(self, field_name), field_name)
        require_sha256(self.canonical_input_sha256, "canonical_input_sha256")
        require_sha256(self.canonical_output_sha256, "canonical_output_sha256")
        if not isinstance(self.timeline, CanonicalTimeline):
            raise DomainValidationError("timeline must use the canonical 24000-tick timebase")
        if not isinstance(self.scene_timeline, SceneTimeline) or self.scene_timeline.scene_id != self.scene_id:
            raise DomainValidationError("scene_timeline must match scene_id")
        if not isinstance(self.capability_profile, GenerationCapabilityProfile):
            raise DomainValidationError("capability_profile must be canonical")
        source_fact_ids = _text_tuple(
            self.source_fact_ids, "source_fact_ids", require_items=True
        )
        approved_fact_handles = _text_tuple(
            self.approved_fact_handles,
            "approved_fact_handles",
            require_items=True,
        )
        for value in source_fact_ids:
            require_opaque_id(value, "source_fact_id")
        for value in approved_fact_handles:
            require_opaque_handle(value, "approved_fact_handle")
        if len(source_fact_ids) != len(approved_fact_handles):
            raise DomainValidationError(
                "source_fact_ids and approved_fact_handles must have the same ordered length"
            )
        object.__setattr__(self, "source_fact_ids", source_fact_ids)
        object.__setattr__(self, "approved_fact_handles", approved_fact_handles)
        for field_name, item_type, required in (
            ("curve_points", VisualCurvePoint, True),
            ("decisions", DirectorDecision, True),
            ("generation_units", GenerationUnit, True),
            ("shots", VisualShot, True),
            ("boundaries", ShotBoundary, True),
            ("audio_events", AudioEvent, False),
            ("voice_requirements", VoiceRequirement, False),
            ("reference_requirements", ReferenceRequirement, False),
        ):
            object.__setattr__(
                self,
                field_name,
                _typed_tuple(getattr(self, field_name), item_type, field_name, require_items=required),
            )
        self._validate_graph()

    def _validate_graph(self) -> None:
        collections = (
            ("curve point", tuple(item.point_id for item in self.curve_points)),
            ("decision", tuple(item.decision_id for item in self.decisions)),
            ("generation unit", tuple(item.unit_id for item in self.generation_units)),
            ("shot", tuple(item.shot_id for item in self.shots)),
            ("boundary", tuple(item.boundary_id for item in self.boundaries)),
            ("audio event", tuple(item.event_id for item in self.audio_events)),
            ("voice requirement", tuple(item.requirement_id for item in self.voice_requirements)),
            ("reference requirement", tuple(item.requirement_id for item in self.reference_requirements)),
        )
        all_ids: list[str] = [self.contract_id]
        for label, identifiers in collections:
            if len(identifiers) != len(set(identifiers)):
                raise DomainValidationError(f"{label} IDs must be unique")
            all_ids.extend(identifiers)
        beat_ids = tuple(beat.beat_id for shot in self.shots for beat in shot.visual_beats)
        if len(beat_ids) != len(set(beat_ids)):
            raise DomainValidationError("VisualBeat IDs must be unique")
        all_ids.extend(beat_ids)
        if len(all_ids) != len(set(all_ids)):
            raise DomainValidationError("all local VEC IDs must be globally unique")

        decisions = {item.decision_id for item in self.decisions}
        shots = {item.shot_id: item for item in self.shots}
        units = {item.unit_id: item for item in self.generation_units}
        beats = {item.beat_id: item for shot in self.shots for item in shot.visual_beats}
        if tuple(item.source_shot_ordinal for item in self.shots) != tuple(
            range(1, len(self.shots) + 1)
        ):
            raise DomainValidationError("source shot ordinals must be sequential from one")
        if len(units) != len(shots) or {item.shot_id for item in self.generation_units} != set(shots):
            raise DomainValidationError("each CinematicShot requires exactly one GenerationUnit")
        placements = {item.scope_id: item for item in self.scene_timeline.generation_unit_placements}
        if set(placements) != set(units):
            raise DomainValidationError("SceneTimeline must place every GenerationUnit exactly once")

        for shot in self.shots:
            if shot.generation_unit_id not in units:
                raise DomainValidationError("VisualShot generation_unit_id must resolve")
            unit = units[shot.generation_unit_id]
            if unit.shot_id != shot.shot_id:
                raise DomainValidationError("a GenerationUnit must contain exactly its one VisualShot")
            if unit.generation_mode is not shot.generation_mode:
                raise DomainValidationError("generation mode must agree across Shot and GenerationUnit")
            if unit.timeline.interval != shot.interval:
                raise DomainValidationError("VisualShot must fill its GenerationUnit local timeline")
            if unit.scene_placement != placements[unit.unit_id]:
                raise DomainValidationError("GenerationUnit placement must equal SceneTimeline placement")
            if (
                unit.timeline.capability_profile_id != self.capability_profile.profile_id
                or unit.timeline.capability_profile_version != self.capability_profile.profile_version
                or unit.timeline.max_generation_ticks != self.capability_profile.max_generation_ticks
            ):
                raise DomainValidationError("GenerationUnit capability must match the VEC profile")
            if not set(shot.decision_ids).issubset(decisions):
                raise DomainValidationError("VisualShot decision references must resolve")
            if any(not set(beat.decision_ids).issubset(decisions) for beat in shot.visual_beats):
                raise DomainValidationError("VisualBeat decision references must resolve")

        self._validate_boundaries(decisions)
        self._validate_bindings(shots, beats)

    def _validate_boundaries(self, decisions: set[str]) -> None:
        if len(self.boundaries) != len(self.shots) + 1:
            raise DomainValidationError("a Scene with N shots requires exactly N+1 Boundaries")
        if tuple(item.boundary_ordinal for item in self.boundaries) != tuple(
            range(0, len(self.shots) + 1)
        ):
            raise DomainValidationError("boundary ordinals must be sequential from zero")
        units = {item.unit_id: item for item in self.generation_units}
        placements = tuple(units[shot.generation_unit_id].scene_placement for shot in self.shots)
        for index, boundary in enumerate(self.boundaries):
            expected_from = None if index == 0 else self.shots[index - 1].shot_id
            expected_to = None if index == len(self.shots) else self.shots[index].shot_id
            expected_tick = (
                placements[0].interval.start_tick
                if index == 0
                else placements[-1].interval.end_tick
                if index == len(self.shots)
                else placements[index - 1].interval.end_tick
            )
            if boundary.from_shot_id != expected_from or boundary.to_shot_id != expected_to:
                raise DomainValidationError("Boundaries must encode scene entrance, every cut, and scene exit")
            if boundary.scene_tick != expected_tick:
                raise DomainValidationError("Boundary scene_tick must equal the shared cut point")
            if index not in (0, len(self.shots)) and placements[index].interval.start_tick != expected_tick:
                raise DomainValidationError("adjacent shots must share the same Boundary tick")
            expected_before = (
                self.shots[index - 1].visual_beats[-1].end_state_id
                if index > 0
                else boundary.before_state_id
            )
            expected_after = (
                self.shots[index].visual_beats[0].start_state_id
                if index < len(self.shots)
                else boundary.after_state_id
            )
            if boundary.before_state_id != expected_before or boundary.after_state_id != expected_after:
                raise DomainValidationError("Boundary states must match adjacent Shot states")
            if not set(boundary.decision_ids).issubset(decisions):
                raise DomainValidationError("ShotBoundary decision references must resolve")

    def _validate_bindings(
        self, shots: dict[str, VisualShot], beats: dict[str, VisualBeat]
    ) -> None:
        approved_fact_pairs = frozenset(self.approved_fact_pairs)
        references = {item.requirement_id: item for item in self.reference_requirements}
        audio = {item.event_id: item for item in self.audio_events}

        for requirement in self.reference_requirements:
            if (
                requirement.source_fact_id,
                requirement.source_fact_handle,
            ) not in approved_fact_pairs:
                raise DomainValidationError(
                    "ReferenceRequirement must use an exact approved fact ID/handle pair"
                )
            if requirement.shot_id not in shots:
                raise DomainValidationError("ReferenceRequirement shot target must resolve")
            shot = shots[requirement.shot_id]
            if requirement.requirement_id not in shot.reference_requirement_ids:
                raise DomainValidationError("ReferenceRequirement must be back-referenced by its Shot")
            if requirement.visual_beat_id is not None:
                if requirement.visual_beat_id not in beats or beats[requirement.visual_beat_id].shot_id != shot.shot_id:
                    raise DomainValidationError("ReferenceRequirement VisualBeat target must resolve inside its Shot")
                if requirement.requirement_id not in beats[requirement.visual_beat_id].reference_requirement_ids:
                    raise DomainValidationError("ReferenceRequirement must be back-referenced by its VisualBeat")

        for event in self.audio_events:
            if (event.source_fact_id, event.source_fact_handle) not in approved_fact_pairs:
                raise DomainValidationError(
                    "AudioEvent must use an exact approved fact ID/handle pair"
                )
            if event.shot_id not in shots or event.visual_beat_id not in beats:
                raise DomainValidationError("AudioEvent typed target must resolve")
            shot = shots[event.shot_id]
            beat = beats[event.visual_beat_id]
            if beat.shot_id != shot.shot_id:
                raise DomainValidationError("AudioEvent VisualBeat must belong to its Shot")
            if event.event_id not in shot.audio_event_ids or event.event_id not in beat.audio_event_ids:
                raise DomainValidationError("AudioEvent must be back-referenced by its Shot and VisualBeat")
            if not beat.interval.contains(event.marker.tick):
                raise DomainValidationError("AudioEvent marker must fall inside its target VisualBeat")

        for shot in self.shots:
            for requirement_id in shot.reference_requirement_ids:
                if requirement_id not in references or references[requirement_id].shot_id != shot.shot_id:
                    raise DomainValidationError("VisualShot reference back-reference must resolve exactly")
            for event_id in shot.audio_event_ids:
                if event_id not in audio or audio[event_id].shot_id != shot.shot_id:
                    raise DomainValidationError("VisualShot audio back-reference must resolve exactly")
            for beat in shot.visual_beats:
                for requirement_id in beat.reference_requirement_ids:
                    requirement = references.get(requirement_id)
                    if requirement is None or requirement.visual_beat_id != beat.beat_id:
                        raise DomainValidationError("VisualBeat reference back-reference must resolve exactly")
                for event_id in beat.audio_event_ids:
                    event = audio.get(event_id)
                    if event is None or event.visual_beat_id != beat.beat_id:
                        raise DomainValidationError("VisualBeat audio back-reference must resolve exactly")

        voice_events = tuple(item.audio_event_id for item in self.voice_requirements)
        if set(voice_events) != set(audio) or len(voice_events) != len(set(voice_events)):
            raise DomainValidationError("each AudioEvent requires exactly one VoiceRequirement")
        for requirement in self.voice_requirements:
            event = audio[requirement.audio_event_id]
            if (
                requirement.character_label != event.character_label
                or requirement.shot_id != event.shot_id
                or requirement.visual_beat_id != event.visual_beat_id
            ):
                raise DomainValidationError("VoiceRequirement must preserve the AudioEvent typed target")
