"""One-way reader for the retained legacy B0/K2 checkpoint.

This adapter intentionally imports only the new domain package.  It does not
make the canonical domain depend on legacy contracts, IDs, or timebases.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    SourceRef,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingDraft


@dataclass(frozen=True)
class LegacyCheckpointObservation:
    source_ref: SourceRef
    scene_id: str
    candidate_draft: BlockingDraft
    record_digest: str
    requires_reassembly: bool = True


def _legacy_text(value: Any, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    raise DomainValidationError(f"legacy checkpoint lacks non-empty {field_name}")


def _legacy_texts(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise DomainValidationError(f"legacy checkpoint lacks {field_name}")
    result = tuple(_legacy_text(item, field_name) for item in value)
    return result


def _legacy_state(value: Any, field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise DomainValidationError(f"legacy checkpoint {field_name} must be an object")
    converted: dict[str, str] = {}
    for key, item in value.items():
        if isinstance(item, list):
            converted[str(key)] = " | ".join(str(part) for part in item)
        elif item is None:
            converted[str(key)] = ""
        else:
            converted[str(key)] = str(item)
    return converted


def _legacy_gaze_relations(
    character_states: list[Any],
) -> tuple[str, ...]:
    relations: list[str] = []
    for state in character_states:
        if not isinstance(state, Mapping):
            continue
        character_id = state.get("character_id")
        gaze_target = state.get("gaze_target")
        if (
            isinstance(character_id, str)
            and character_id.strip()
            and isinstance(gaze_target, str)
            and gaze_target.strip()
        ):
            relations.append(f"{character_id} -> {gaze_target}")
    return tuple(relations)


def read_legacy_b0_k2_checkpoint(path: Path) -> LegacyCheckpointObservation:
    """Read a historical checkpoint into a non-authoritative observation.

    The input is never modified, imported as code, assigned new IDs, wrapped as
    a v3 Artifact, or promoted to a validated commit.
    """

    source_path = Path(path)
    raw = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or not isinstance(raw.get("blocking_commit"), Mapping):
        raise DomainValidationError("legacy checkpoint has no blocking_commit object")
    commit = raw["blocking_commit"]
    scene_id = _legacy_text(commit.get("scene_id"), "blocking_commit.scene_id")
    raw_beats = commit.get("beats")
    if not isinstance(raw_beats, list) or not raw_beats:
        raise DomainValidationError("legacy checkpoint has no blocking beats")

    beats: list[BlockingBeatDraft] = []
    for ordinal, raw_beat in enumerate(raw_beats, start=1):
        if not isinstance(raw_beat, Mapping):
            raise DomainValidationError("legacy blocking beat must be an object")
        character_states = raw_beat.get("character_states", [])
        prop_states = raw_beat.get("prop_states", [])
        if not isinstance(character_states, list) or not isinstance(prop_states, list):
            raise DomainValidationError("legacy blocking state lists are malformed")
        continuity_effect = "; ".join(
            (
                f"entry={_legacy_text(raw_beat.get('entry_state_id'), 'beat.entry_state_id')}",
                f"exit={_legacy_text(raw_beat.get('exit_state_id'), 'beat.exit_state_id')}",
                f"space={_legacy_text(raw_beat.get('space_control'), 'beat.space_control')}",
                f"consequence={_legacy_text(raw_beat.get('dramatic_reason'), 'beat.dramatic_reason')}",
            )
        )
        beats.append(
            BlockingBeatDraft(
                ordinal=ordinal,
                dramatic_action=_legacy_text(raw_beat.get("dramatic_function"), "beat.dramatic_function"),
                character_states=tuple(_legacy_state(item, "character_states") for item in character_states),
                prop_states=tuple(_legacy_state(item, "prop_states") for item in prop_states),
                gaze_relations=_legacy_gaze_relations(character_states),
                action_paths=_legacy_texts(raw_beat.get("action_paths"), "beat.action_paths"),
                continuity_effect=continuity_effect,
            )
        )

    draft = BlockingDraft(beats=tuple(beats))
    input_digest = canonical_sha256(raw)
    source_ref = SourceRef(
        source_id=f"legacy-checkpoint:{source_path.name}",
        digest=input_digest,
        locator=str(source_path),
    )
    return LegacyCheckpointObservation(
        source_ref=source_ref,
        scene_id=scene_id,
        candidate_draft=draft,
        record_digest=input_digest,
    )
