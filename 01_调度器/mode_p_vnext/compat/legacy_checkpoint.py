"""One-way reader for the retained legacy B0/K2 checkpoint.

This adapter intentionally imports only the new domain package.  It does not
make the canonical domain depend on legacy contracts, IDs, or timebases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    ArtifactKind,
    DOMAIN_SCHEMA_VERSION,
    DomainValidationError,
    SourceRef,
    ValidationStatus,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingDraft
from mode_p_vnext.domain.ids import IdFactory


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


def read_legacy_b0_k2_checkpoint(path: Path) -> ArtifactEnvelope[BlockingDraft]:
    """Read a historical checkpoint and return a canonical *draft* envelope.

    The input is never modified, never imported as code, and never promoted to
    a validated commit.  Its original provenance remains part of the envelope.
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
        beats.append(
            BlockingBeatDraft(
                ordinal=ordinal,
                dramatic_action=_legacy_text(raw_beat.get("dramatic_function"), "beat.dramatic_function"),
                dramatic_reason=_legacy_text(raw_beat.get("dramatic_reason"), "beat.dramatic_reason"),
                character_states=tuple(_legacy_state(item, "character_states") for item in character_states),
                prop_states=tuple(_legacy_state(item, "prop_states") for item in prop_states),
                action_paths=_legacy_texts(raw_beat.get("action_paths"), "beat.action_paths"),
                constraint_refs=_legacy_texts(raw_beat.get("constraint_refs"), "beat.constraint_refs"),
                entry_state=_legacy_text(raw_beat.get("entry_state_id"), "beat.entry_state_id"),
                exit_state=_legacy_text(raw_beat.get("exit_state_id"), "beat.exit_state_id"),
                space_control=_legacy_text(raw_beat.get("space_control"), "beat.space_control"),
            )
        )

    draft = BlockingDraft(
        scene_id=scene_id,
        beats=tuple(beats),
        constraint_refs=_legacy_texts(commit.get("constraint_refs"), "blocking_commit.constraint_refs"),
        dramatic_reason=_legacy_text(beats[-1].dramatic_reason, "final beat dramatic_reason"),
    )
    input_digest = canonical_sha256(raw)
    source_ref = SourceRef(
        source_id=f"legacy-checkpoint:{source_path.name}",
        digest=input_digest,
        locator=str(source_path),
    )
    artifact_id = IdFactory(program_version="legacy-read-adapter-v2.1").create(
        artifact_kind=ArtifactKind.BLOCKING_DRAFT,
        episode_id="legacy",
        scene_id=scene_id,
        stage="legacy-b0-k2-import",
        input_digest=input_digest,
        ordinal=1,
    )
    return ArtifactEnvelope.create(
        artifact_id=artifact_id,
        artifact_kind=ArtifactKind.BLOCKING_DRAFT,
        schema_version=DOMAIN_SCHEMA_VERSION,
        program_version="legacy-read-adapter-v2.1",
        payload=draft,
        source_refs=(source_ref,),
        dependency_digests={"legacy_checkpoint": input_digest},
        created_at="1970-01-01T00:00:00Z",
        validation_status=ValidationStatus.DRAFT,
    )
