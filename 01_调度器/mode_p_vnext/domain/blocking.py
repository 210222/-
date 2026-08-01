"""B0 creative drafts and the locally assembled blocking authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from .artifact import DOMAIN_SCHEMA_VERSION, ArtifactKind, DomainValidationError, freeze_mapping
CANONICAL_DOMAIN_TYPES = (
    "BlockingBeat",
    "BlockingBeatDraft",
    "BlockingCommit",
    "BlockingDraft",
)


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
    return values


def _frozen_states(
    value: tuple[Mapping[str, Any], ...],
    field_name: str,
    *,
    require_items: bool,
) -> tuple[Mapping[str, Any], ...]:
    states = tuple(value)
    if (require_items and not states) or not all(
        isinstance(item, Mapping) for item in states
    ):
        raise DomainValidationError(f"{field_name} must contain mappings")
    return tuple(freeze_mapping(item, field_name) for item in states)


def _require_positive_ordinal(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DomainValidationError(f"{field_name} must be a positive integer")


@dataclass(frozen=True)
class BlockingBeatDraft:
    """Exactly the creative B0 beat fields declared by architecture §5.3."""

    ordinal: int
    dramatic_action: str
    character_states: tuple[Mapping[str, Any], ...]
    prop_states: tuple[Mapping[str, Any], ...]
    gaze_relations: tuple[str, ...]
    action_paths: tuple[str, ...]
    continuity_effect: str

    def __post_init__(self) -> None:
        _require_positive_ordinal(self.ordinal, "ordinal")
        _require_text(self.dramatic_action, "dramatic_action")
        _require_text(self.continuity_effect, "continuity_effect")
        object.__setattr__(
            self,
            "character_states",
            _frozen_states(
                self.character_states, "character_states", require_items=True
            ),
        )
        object.__setattr__(
            self,
            "prop_states",
            _frozen_states(self.prop_states, "prop_states", require_items=False),
        )
        object.__setattr__(
            self,
            "gaze_relations",
            _text_tuple(
                self.gaze_relations, "gaze_relations", require_items=False
            ),
        )
        object.__setattr__(
            self,
            "action_paths",
            _text_tuple(self.action_paths, "action_paths", require_items=True),
        )


@dataclass(frozen=True)
class BlockingDraft:
    """The model-authored B0 payload; scene identity remains approved input."""

    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.BLOCKING_DRAFT

    beats: tuple[BlockingBeatDraft, ...]

    def __post_init__(self) -> None:
        beats = tuple(self.beats)
        if not beats or not all(
            isinstance(beat, BlockingBeatDraft) for beat in beats
        ):
            raise DomainValidationError(
                "beats must contain BlockingBeatDraft values"
            )
        ordinals = tuple(beat.ordinal for beat in beats)
        if ordinals != tuple(range(1, len(beats) + 1)):
            raise DomainValidationError(
                "blocking beat ordinals must be sequential from one"
            )
        object.__setattr__(self, "beats", beats)


@dataclass(frozen=True)
class BlockingBeat:
    """A validated beat with local IDs and state-boundary authority."""

    beat_id: str
    source_ordinal: int
    dramatic_action: str
    character_states: tuple[Mapping[str, Any], ...]
    prop_states: tuple[Mapping[str, Any], ...]
    gaze_relations: tuple[str, ...]
    action_paths: tuple[str, ...]
    continuity_effect: str
    entry_state_id: str
    exit_state_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "beat_id",
            "dramatic_action",
            "continuity_effect",
            "entry_state_id",
            "exit_state_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        _require_positive_ordinal(self.source_ordinal, "source_ordinal")
        object.__setattr__(
            self,
            "character_states",
            _frozen_states(
                self.character_states, "character_states", require_items=True
            ),
        )
        object.__setattr__(
            self,
            "prop_states",
            _frozen_states(self.prop_states, "prop_states", require_items=False),
        )
        object.__setattr__(
            self,
            "gaze_relations",
            _text_tuple(
                self.gaze_relations, "gaze_relations", require_items=False
            ),
        )
        object.__setattr__(
            self,
            "action_paths",
            _text_tuple(self.action_paths, "action_paths", require_items=True),
        )


@dataclass(frozen=True)
class BlockingCommit:
    """The sole local B0 authority consumed by K2, B1, and VEC assembly."""

    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.BLOCKING_COMMIT

    commit_id: str
    scene_id: str
    blocking_draft_artifact_id: str
    beats: tuple[BlockingBeat, ...]
    entry_state_id: str
    exit_state_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "commit_id",
            "scene_id",
            "blocking_draft_artifact_id",
            "entry_state_id",
            "exit_state_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        beats = tuple(self.beats)
        if not beats or not all(isinstance(beat, BlockingBeat) for beat in beats):
            raise DomainValidationError(
                "beats must contain validated BlockingBeat values"
            )
        if tuple(beat.source_ordinal for beat in beats) != tuple(
            range(1, len(beats) + 1)
        ):
            raise DomainValidationError(
                "validated beat ordinals must be sequential from one"
            )
        beat_ids = tuple(beat.beat_id for beat in beats)
        if len(beat_ids) != len(set(beat_ids)):
            raise DomainValidationError("BlockingCommit beat IDs must be unique")
        if beats[0].entry_state_id != self.entry_state_id:
            raise DomainValidationError(
                "BlockingCommit entry state must match its first beat"
            )
        if beats[-1].exit_state_id != self.exit_state_id:
            raise DomainValidationError(
                "BlockingCommit exit state must match its final beat"
            )
        for left, right in zip(beats, beats[1:]):
            if left.exit_state_id != right.entry_state_id:
                raise DomainValidationError(
                    "BlockingCommit beat state boundaries must be adjacent"
                )
        object.__setattr__(self, "beats", beats)
