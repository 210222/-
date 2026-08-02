"""Deterministic local assembly of BlockingCommit from model-authored BlockingDraft.

Architecture ref: frozen MODE:P vNext v3.0 authority, B0 local assembly.

The model outputs only creative beat fields (ordinal, dramatic_action,
character_states, props, gaze, action_paths, continuity_effect).  This assembler
generates every machine ID, state ID, and the commit identity — none of which
the model is allowed to produce.
"""

from __future__ import annotations

from mode_p_vnext.domain.artifact import (
    DOMAIN_SCHEMA_VERSION,
    ArtifactKind,
    DomainValidationError,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingBeat, BlockingCommit, BlockingDraft
from mode_p_vnext.domain.ids import IdFactory


def assemble_blocking_commit(
    *,
    draft: BlockingDraft,
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    program_version: str,
    schema_version: str = DOMAIN_SCHEMA_VERSION,
) -> BlockingCommit:
    """Produce the sole local B0 authority from a validated BlockingDraft."""

    if not isinstance(draft, BlockingDraft):
        raise DomainValidationError("draft must be a BlockingDraft")
    if not isinstance(id_factory, IdFactory):
        raise DomainValidationError("id_factory must be an IdFactory")
    for value, field_name in (
        (episode_id, "episode_id"),
        (scene_id, "scene_id"),
        (program_version, "program_version"),
        (schema_version, "schema_version"),
    ):
        if not isinstance(value, str) or not value.strip():
            raise DomainValidationError(f"{field_name} must be non-empty")
    if schema_version != DOMAIN_SCHEMA_VERSION:
        raise DomainValidationError(
            f"schema_version must match canonical domain schema {DOMAIN_SCHEMA_VERSION}"
        )
    if id_factory.program_version != program_version:
        raise DomainValidationError(
            "id_factory program_version must match the approved Blocking program_version"
        )

    # -- 1.  generate a stable input digest so rebuilds are deterministic ------
    input_digest = canonical_sha256(
        {
            "draft_payload": draft,
            "episode_id": episode_id,
            "scene_id": scene_id,
            "program_version": program_version,
            "schema_version": schema_version,
        }
    )

    # -- 2.  generate the commit identity -------------------------------------
    commit_id = id_factory.create(
        artifact_kind=ArtifactKind.BLOCKING_COMMIT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="B0",
        input_digest=input_digest,
        ordinal=0,
    )

    # -- 3.  assemble validated beats with local IDs --------------------------
    beats: list[BlockingBeat] = []

    for index, draft_beat in enumerate(draft.beats):
        beat_ordinal = draft_beat.ordinal

        beat_id = id_factory.create(
            artifact_kind=ArtifactKind.BLOCKING_COMMIT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B0:beat",
            input_digest=input_digest,
            ordinal=beat_ordinal,
        )

        entry_state_id = id_factory.create(
            artifact_kind=ArtifactKind.BLOCKING_COMMIT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B0:state",
            input_digest=input_digest,
            ordinal=beat_ordinal * 2 - 1,  # odd numbers for entry states
        )

        exit_state_id = id_factory.create(
            artifact_kind=ArtifactKind.BLOCKING_COMMIT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B0:state",
            input_digest=input_digest,
            ordinal=beat_ordinal * 2,  # even numbers for exit states
        )

        beats.append(
            BlockingBeat(
                beat_id=beat_id,
                source_ordinal=beat_ordinal,
                dramatic_action=draft_beat.dramatic_action,
                character_states=draft_beat.character_states,
                prop_states=draft_beat.prop_states,
                gaze_relations=draft_beat.gaze_relations,
                action_paths=draft_beat.action_paths,
                continuity_effect=draft_beat.continuity_effect,
                entry_state_id=entry_state_id,
                exit_state_id=exit_state_id,
            )
        )

    # -- 4.  chain adjacent state IDs so the domain invariant holds -----------
    # Beat[i].exit_state_id must equal Beat[i+1].entry_state_id.
    # Rebuild the beats so the chain is contiguous.
    chained: list[BlockingBeat] = []
    for i, beat in enumerate(beats):
        if i == 0:
            # First beat keeps its entry; later beats adopt the previous exit
            chained.append(beat)
        else:
            prev_exit = chained[i - 1].exit_state_id
            chained.append(
                BlockingBeat(
                    beat_id=beat.beat_id,
                    source_ordinal=beat.source_ordinal,
                    dramatic_action=beat.dramatic_action,
                    character_states=beat.character_states,
                    prop_states=beat.prop_states,
                    gaze_relations=beat.gaze_relations,
                    action_paths=beat.action_paths,
                    continuity_effect=beat.continuity_effect,
                    entry_state_id=prev_exit,
                    exit_state_id=beat.exit_state_id,
                )
            )

    # -- 5.  blocking draft artifact identity (deterministic reference) ------
    blocking_draft_artifact_id = id_factory.create(
        artifact_kind=ArtifactKind.BLOCKING_DRAFT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="B0",
        input_digest=input_digest,
        ordinal=0,
    )

    # -- 6.  return the sole local B0 authority -------------------------------
    return BlockingCommit(
        commit_id=commit_id,
        scene_id=scene_id,
        blocking_draft_artifact_id=blocking_draft_artifact_id,
        beats=tuple(chained),
        entry_state_id=chained[0].entry_state_id,
        exit_state_id=chained[-1].exit_state_id,
    )
