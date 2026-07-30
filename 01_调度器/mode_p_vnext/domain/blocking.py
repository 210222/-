"""Blocking drafts and local blocking commit schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .artifact import DomainValidationError, freeze_mapping


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("BlockingBeatDraft", "BlockingDraft", "BlockingCommit")


def _text_tuple(value: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    values = tuple(value)
    if not values or any(not isinstance(item, str) or not item.strip() for item in values):
        raise DomainValidationError(f"{field_name} must contain non-empty text")
    return values


def _frozen_states(value: tuple[Mapping[str, Any], ...], field_name: str) -> tuple[Mapping[str, Any], ...]:
    states = tuple(value)
    if not all(isinstance(item, Mapping) for item in states):
        raise DomainValidationError(f"{field_name} must contain mappings")
    return tuple(freeze_mapping(item, field_name) for item in states)


@dataclass(frozen=True)
class BlockingBeatDraft:
    ordinal: int
    dramatic_action: str
    dramatic_reason: str
    character_states: tuple[Mapping[str, Any], ...]
    prop_states: tuple[Mapping[str, Any], ...]
    action_paths: tuple[str, ...]
    constraint_refs: tuple[str, ...]
    entry_state: str
    exit_state: str
    space_control: str

    def __post_init__(self) -> None:
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 1:
            raise DomainValidationError("ordinal must be a positive integer")
        for field_name in ("dramatic_action", "dramatic_reason", "entry_state", "exit_state", "space_control"):
            if not getattr(self, field_name).strip():
                raise DomainValidationError(f"{field_name} must be non-empty")
        object.__setattr__(self, "character_states", _frozen_states(self.character_states, "character_states"))
        object.__setattr__(self, "prop_states", _frozen_states(self.prop_states, "prop_states"))
        object.__setattr__(self, "action_paths", _text_tuple(self.action_paths, "action_paths"))
        object.__setattr__(self, "constraint_refs", _text_tuple(self.constraint_refs, "constraint_refs"))


@dataclass(frozen=True)
class BlockingDraft:
    scene_id: str
    beats: tuple[BlockingBeatDraft, ...]
    constraint_refs: tuple[str, ...]
    dramatic_reason: str

    def __post_init__(self) -> None:
        if not self.scene_id.strip() or not self.dramatic_reason.strip():
            raise DomainValidationError("scene_id and dramatic_reason must be non-empty")
        beats = tuple(self.beats)
        if not beats or not all(isinstance(beat, BlockingBeatDraft) for beat in beats):
            raise DomainValidationError("beats must contain BlockingBeatDraft values")
        ordinals = tuple(beat.ordinal for beat in beats)
        if ordinals != tuple(range(1, len(beats) + 1)):
            raise DomainValidationError("blocking beat ordinals must be sequential from one")
        object.__setattr__(self, "beats", beats)
        object.__setattr__(self, "constraint_refs", _text_tuple(self.constraint_refs, "constraint_refs"))


@dataclass(frozen=True)
class BlockingCommit:
    commit_id: str
    scene_id: str
    blocking_draft_artifact_id: str
    entry_state: str
    exit_state: str
    accepted_beat_ordinals: tuple[int, ...]

    def __post_init__(self) -> None:
        if any(not getattr(self, field_name).strip() for field_name in ("commit_id", "scene_id", "blocking_draft_artifact_id", "entry_state", "exit_state")):
            raise DomainValidationError("BlockingCommit text fields must be non-empty")
        ordinals = tuple(self.accepted_beat_ordinals)
        if not ordinals or any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in ordinals):
            raise DomainValidationError("accepted_beat_ordinals must be positive integers")
        object.__setattr__(self, "accepted_beat_ordinals", ordinals)
