"""A2 acceptance tests for the canonical persistent node-runner boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    ArtifactKind,
    SourceRef,
    ValidationStatus,
    canonical_json_bytes,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import (
    BlockingBeat,
    BlockingBeatDraft,
    BlockingCommit,
    BlockingDraft,
)
from mode_p_vnext.domain.decisions import (
    DecisionBasis,
    DecisionDraft,
    VisualCurvePointDraft,
)
from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
from mode_p_vnext.domain.vec import (
    ExecutionDesignDraft,
    ShotDesignDraft,
    StoryboardRole,
    VisualBeatDraft,
    VisualBeatPhase,
)
from mode_p_vnext.pipeline.graph import NodeSpec, StateGraph
from mode_p_vnext.pipeline.invalidation import FieldInvalidator
from mode_p_vnext.pipeline.state import ArtifactRef, PersistentGraphState, StateInvariantError
from mode_p_vnext.runtime.cache import NodeCacheKey
from mode_p_vnext.runtime.session import RunSession, RunSessionError


def _direction_artifact(digest_char: str = "a") -> ArtifactEnvelope[EpisodeDirectionDraft]:
    source = SourceRef("script:episode-1", digest_char * 64)
    payload = EpisodeDirectionDraft(
        dramatic_promise="A choice reshapes the relationship.",
        audience_contract="The cause of every change remains legible.",
        tension_curve=("arrival", "choice"),
        visual_principles=("preserve the decision line",),
        continuity_priorities=("the key remains visible",),
        unresolved_questions=(),
    )
    return ArtifactEnvelope.create(
        artifact_id=f"episode_direction:episode-1:episode:E0:0001:{digest_char * 20}",
        artifact_kind=ArtifactKind.EPISODE_DIRECTION,
        schema_version="2.1",
        program_version="test-vnext-2.1",
        payload=payload,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
        created_at="2026-07-30T00:00:00Z",
        validation_status=ValidationStatus.DRAFT,
    )


def _scene_intent_artifact(digest_char: str = "b") -> ArtifactEnvelope[SceneIntentDraft]:
    source = SourceRef("script:scene-1", digest_char * 64)
    payload = SceneIntentDraft(
        scene_purpose="Transfer visible responsibility.",
        state_change="The subordinate must decide alone.",
        audience_information=("The key is now between them.",),
        character_knowledge=("Only the director knows the wider consequence.",),
        performance_questions=("Does the pause read as acceptance?",),
        director_problems=("Keep the key as the only consequential object.",),
        continuity_effects=("The key stays on the table.",),
        unresolved_questions=(),
    )
    return ArtifactEnvelope.create(
        artifact_id=f"scene_intent:episode-1:scene-1:S1:0001:{digest_char * 20}",
        artifact_kind=ArtifactKind.SCENE_INTENT,
        schema_version="2.1",
        program_version="test-vnext-2.1",
        payload=payload,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
        created_at="2026-07-30T00:00:00Z",
        validation_status=ValidationStatus.DRAFT,
    )


def _blocking_draft_artifact(digest_char: str = "c") -> ArtifactEnvelope[BlockingDraft]:
    source = SourceRef("script:scene-1", digest_char * 64)
    payload = BlockingDraft(
        beats=(
            BlockingBeatDraft(
                ordinal=1,
                dramatic_action="The lead retains the key while the decision lands.",
                character_states=({"character_id": "lead", "state": "still"},),
                prop_states=({"prop_id": "key", "state": "on_table"},),
                gaze_relations=("lead watches the key",),
                action_paths=("lead holds position",),
                continuity_effect="The key remains visible at the scene boundary.",
            ),
        )
    )
    return ArtifactEnvelope.create(
        artifact_id=f"blocking_draft:episode-1:scene-1:B0:0001:{digest_char * 20}",
        artifact_kind=ArtifactKind.BLOCKING_DRAFT,
        schema_version="2.1",
        program_version="test-vnext-2.1",
        payload=payload,
        source_refs=(source,),
        dependency_digests={"source": source.digest},
        created_at="2026-07-30T00:00:00Z",
        validation_status=ValidationStatus.DRAFT,
    )


def _blocking_commit_artifact(digest_char: str = "d") -> ArtifactEnvelope[BlockingCommit]:
    source = SourceRef("script:scene-1", digest_char * 64)
    payload = BlockingCommit(
        commit_id=f"blocking-commit-{digest_char}",
        scene_id="scene-1",
        blocking_draft_artifact_id="blocking_draft:episode-1:scene-1:B0:0001",
        beats=(
            BlockingBeat(
                beat_id=f"blocking-beat-{digest_char}",
                source_ordinal=1,
                dramatic_action="The lead retains the key while the decision lands.",
                character_states=({"character_id": "lead", "state": "still"},),
                prop_states=({"prop_id": "key", "state": "on_table"},),
                gaze_relations=("lead watches the key",),
                action_paths=("lead holds position",),
                continuity_effect="The key remains visible at the scene boundary.",
                entry_state_id="state-entry",
                exit_state_id="state-exit",
            ),
        ),
        entry_state_id="state-entry",
        exit_state_id="state-exit",
    )
    return ArtifactEnvelope.create(
        artifact_id=f"blocking_commit:episode-1:scene-1:ASSEMBLE_B0:0001:{digest_char * 20}",
        artifact_kind=ArtifactKind.BLOCKING_COMMIT,
        schema_version="2.1",
        program_version="test-vnext-2.1",
        payload=payload,
        source_refs=(source,),
        dependency_digests={"source": source.digest},
        created_at="2026-07-30T00:00:00Z",
        validation_status=ValidationStatus.TEXT_VALIDATED,
    )


def _execution_design_artifact(
    digest_char: str = "e",
) -> ArtifactEnvelope[ExecutionDesignDraft]:
    source = SourceRef("script:scene-1", digest_char * 64)
    payload = ExecutionDesignDraft(
        curve_points=(
            VisualCurvePointDraft(
                dramatic_beat_ordinal=1,
                intensity=55,
                explanation="Keep the handoff tension legible.",
            ),
        ),
        decisions=(
            DecisionDraft(
                scope="camera framing",
                basis=DecisionBasis.LOCKED,
                locked_by=("blocking_commit",),
                options=("Retain the key in the composition.",),
                selected_index=0,
                rationale="The object carries the scene state.",
                tradeoff="The frame remains deliberately restrained.",
            ),
        ),
        shots=(
            ShotDesignDraft(
                blocking_beat_ordinal=1,
                dramatic_function="Reveal the handoff decision.",
                attention_target="the key",
                information_action="keep the transfer state visible",
                framing_intent="medium two-shot",
                camera_pose="eye level",
                camera_motion="locked-off",
                composition="lead and key on the decision line",
                lighting="consistent soft key",
                performance="contained hesitation",
                duration_weight=1,
                visual_beats=(
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ACTION,
                        subject_state="lead holds the key",
                        attention="the key remains central",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                ),
            ),
        ),
        transition_intents=("cut after the resolved handoff",),
        audio_intents=(),
        reference_intents=(),
        handoff_intent="Preserve the key state into the following segment.",
    )
    return ArtifactEnvelope.create(
        artifact_id=f"execution_design:episode-1:scene-1:B1:0001:{digest_char * 20}",
        artifact_kind=ArtifactKind.EXECUTION_DESIGN_DRAFT,
        schema_version="2.1",
        program_version="test-vnext-2.1",
        payload=payload,
        source_refs=(source,),
        dependency_digests={"source": source.digest},
        created_at="2026-07-30T00:00:00Z",
        validation_status=ValidationStatus.DRAFT,
    )


def _graph() -> StateGraph:
    return StateGraph(
        (
            NodeSpec(
                node_id="E0",
                node_version="1",
                output_kinds={"episode_direction": ArtifactKind.EPISODE_DIRECTION},
                input_fields=("episode_facts",),
            ),
            NodeSpec(
                node_id="S1",
                node_version="1",
                output_kinds={"scene_intent": ArtifactKind.SCENE_INTENT},
                input_fields=("episode_direction", "scene_facts"),
            ),
            NodeSpec(
                node_id="B0",
                node_version="1",
                output_kinds={"blocking_draft": ArtifactKind.BLOCKING_DRAFT},
                input_fields=("scene_intent",),
            ),
            NodeSpec(
                node_id="DP",
                node_version="1",
                output_kinds={"dp_review": ArtifactKind.DP_REVIEW_RESULT},
                input_fields=("dp_rules",),
            ),
        )
    )


def _recovery_graph() -> StateGraph:
    return StateGraph(
        (
            NodeSpec(
                node_id="E0",
                node_version="1",
                output_kinds={"episode_direction": ArtifactKind.EPISODE_DIRECTION},
                input_fields=("episode_facts",),
            ),
            NodeSpec(
                node_id="S1",
                node_version="1",
                output_kinds={"scene_intent": ArtifactKind.SCENE_INTENT},
                input_fields=("episode_direction", "scene_facts"),
            ),
            NodeSpec(
                node_id="B0",
                node_version="1",
                output_kinds={"blocking_draft": ArtifactKind.BLOCKING_DRAFT},
                input_fields=("scene_intent",),
            ),
            NodeSpec(
                node_id="ASSEMBLE_B0",
                node_version="1",
                output_kinds={"blocking_commit": ArtifactKind.BLOCKING_COMMIT},
                input_fields=("blocking_draft",),
            ),
            NodeSpec(
                node_id="B1",
                node_version="1",
                output_kinds={
                    "execution_design": ArtifactKind.EXECUTION_DESIGN_DRAFT,
                },
                input_fields=("blocking_commit",),
            ),
        )
    )


def _ref(field_name: str, artifact_kind: ArtifactKind, digest_char: str) -> ArtifactRef:
    return ArtifactRef(
        artifact_id=f"{field_name}:{digest_char}",
        artifact_kind=artifact_kind,
        content_sha256=digest_char * 64,
        schema_version="2.1",
    )


def _artifact_for(field_name: str, digest_char: str) -> ArtifactEnvelope[object]:
    factories = {
        "episode_direction": _direction_artifact,
        "scene_intent": _scene_intent_artifact,
        "blocking_draft": _blocking_draft_artifact,
        "blocking_commit": _blocking_commit_artifact,
        "execution_design": _execution_design_artifact,
    }
    return factories[field_name](digest_char)  # type: ignore[return-value]


def test_typed_state_graph_allows_only_owned_partial_state_and_preserves_upstream() -> None:
    graph = _graph()
    state = PersistentGraphState.empty("run-graph")
    state = graph.apply(
        state,
        node_id="E0",
        outputs={
            "episode_direction": _ref(
                "episode_direction", ArtifactKind.EPISODE_DIRECTION, "a"
            )
        },
        dependency_digests={"episode_facts": "1" * 64},
    )
    assert state.outputs["episode_direction"].content_sha256 == "a" * 64
    assert state.accepted["E0"].dependency_digests["episode_facts"] == "1" * 64

    with pytest.raises(StateInvariantError, match="owns"):
        graph.apply(
            state,
            node_id="S1",
            outputs={
                "episode_direction": _ref(
                    "episode_direction", ArtifactKind.EPISODE_DIRECTION, "b"
                )
            },
            dependency_digests={"scene_facts": "2" * 64},
        )
    with pytest.raises(StateInvariantError, match="accepted"):
        graph.apply(
            state,
            node_id="E0",
            outputs={
                "episode_direction": _ref(
                    "episode_direction", ArtifactKind.EPISODE_DIRECTION, "b"
                )
            },
            dependency_digests={"episode_facts": "1" * 64},
        )


def test_pending_transaction_recovers_without_reexecuting_an_accepted_node(tmp_path: Path) -> None:
    graph = _graph()
    session = RunSession.create(tmp_path / "runs", run_id="run-recover", graph=graph)
    runner = session.runner(owner="test-worker")
    artifact = _direction_artifact()

    pending = runner.prepare(
        node_id="E0",
        artifacts={"episode_direction": artifact},
        dependency_digests={"episode_facts": "1" * 64},
    )
    assert pending.node_id == "E0"
    assert not session.state().accepted
    assert not session.current_pointer_path.exists()
    assert (session.run_dir / "staging" / pending.generation_id).is_dir()

    resumed = RunSession.open(session.run_dir, graph=graph)
    assert resumed.recover_pending(owner="recovery-worker") == ("E0",)
    recovered_state = resumed.state()
    assert tuple(recovered_state.accepted) == ("E0",)
    assert recovered_state.accepted["E0"].commit_id == pending.commit_id
    assert recovered_state.outputs["episode_direction"].content_sha256 == artifact.content_sha256
    assert resumed.resume_plan({"episode_facts": "1" * 64}).accepted_node_ids == ("E0",)
    assert resumed.resume_plan({"episode_facts": "1" * 64}).runnable_node_ids == ("S1", "DP")
    assert resumed.resume_plan({"episode_facts": "9" * 64}).accepted_node_ids == ()
    assert resumed.current_pointer_path.is_file()
    assert (resumed.run_dir / "commits" / pending.commit_id / "MANIFEST.json").is_file()

    with pytest.raises(StateInvariantError, match="accepted"):
        resumed.runner(owner="test-worker").prepare(
            node_id="E0",
            artifacts={"episode_direction": artifact},
            dependency_digests={"episode_facts": "1" * 64},
        )


@pytest.mark.parametrize("recovery_node", ("E0", "S1", "B0", "B1"))
def test_recovery_accepts_each_required_kill_point_without_rerun(
    tmp_path: Path, recovery_node: str
) -> None:
    graph = _recovery_graph()
    session = RunSession.create(
        tmp_path / "runs",
        run_id=f"run-kill-{recovery_node.lower()}",
        graph=graph,
    )
    workflow = (
        ("E0", "episode_direction", "a"),
        ("S1", "scene_intent", "b"),
        ("B0", "blocking_draft", "c"),
        ("ASSEMBLE_B0", "blocking_commit", "d"),
        ("B1", "execution_design", "e"),
    )
    for node_id, field_name, digest_char in workflow:
        state = session.state()
        dependency_digests: dict[str, str]
        if node_id == "E0":
            dependency_digests = {"episode_facts": "1" * 64}
        elif node_id == "S1":
            dependency_digests = {
                "episode_direction": state.outputs["episode_direction"].content_sha256,
                "scene_facts": "2" * 64,
            }
        elif node_id == "B0":
            dependency_digests = {
                "scene_intent": state.outputs["scene_intent"].content_sha256,
            }
        elif node_id == "ASSEMBLE_B0":
            dependency_digests = {
                "blocking_draft": state.outputs["blocking_draft"].content_sha256,
            }
        else:
            dependency_digests = {
                "blocking_commit": state.outputs["blocking_commit"].content_sha256,
            }
        artifact = _artifact_for(field_name, digest_char)
        runner = session.runner(owner=f"worker-{node_id}")
        if node_id != recovery_node:
            runner.accept(
                node_id=node_id,
                artifacts={field_name: artifact},
                dependency_digests=dependency_digests,
            )
            continue
        pending = runner.prepare(
            node_id=node_id,
            artifacts={field_name: artifact},
            dependency_digests=dependency_digests,
        )
        assert node_id not in session.state().accepted
        resumed = RunSession.open(session.run_dir, graph=graph)
        assert resumed.recover_pending(owner=f"recovery-{node_id}") == (node_id,)
        restored = resumed.state()
        assert node_id in restored.accepted
        assert restored.accepted[node_id].commit_id == pending.commit_id
        with pytest.raises(StateInvariantError, match="accepted"):
            resumed.runner(owner=f"retry-{node_id}").prepare(
                node_id=node_id,
                artifacts={field_name: artifact},
                dependency_digests=dependency_digests,
            )
        break


def test_content_addressed_artifacts_and_persistent_cache_store_refs_not_process_objects(tmp_path: Path) -> None:
    graph = _graph()
    session = RunSession.create(tmp_path / "runs", run_id="run-cache", graph=graph)
    artifact = _direction_artifact()
    session.runner(owner="test-worker").accept(
        node_id="E0",
        artifacts={"episode_direction": artifact},
        dependency_digests={"episode_facts": "1" * 64},
    )
    ref = session.state().outputs["episode_direction"]
    artifact_path = session.run_dir / "artifacts" / artifact.artifact_kind.value / f"{artifact.content_sha256}.json"
    assert artifact_path.is_file()
    stored = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert stored["content_sha256"] == artifact.content_sha256
    assert ref.content_sha256 == artifact.content_sha256

    key = NodeCacheKey(
        node_kind="E0",
        node_version="1",
        signature_version="1",
        schema_digest="2" * 64,
        approved_input_digests={"episode_facts": "1" * 64},
        knowledge_snapshot_digest="3" * 64,
        requested_model="draft-model",
        resolved_provider_config="provider-config-v1",
        generation_policy="deterministic",
    )
    session.cache.put(key, ref)
    reopened = RunSession.open(session.run_dir, graph=graph)
    assert reopened.cache.get(key) == ref
    assert not hasattr(reopened.cache.get(key), "payload")
    assert (reopened.run_dir / "cache" / f"{key.digest}.json").is_file()


def test_field_level_invalidation_is_digest_edge_scoped_and_keeps_unrelated_nodes() -> None:
    graph = _graph()
    state = PersistentGraphState.empty("run-invalidation")
    state = graph.apply(
        state,
        node_id="E0",
        outputs={
            "episode_direction": _ref(
                "episode_direction", ArtifactKind.EPISODE_DIRECTION, "a"
            )
        },
        dependency_digests={"episode_facts": "1" * 64},
    )
    state = graph.apply(
        state,
        node_id="S1",
        outputs={"scene_intent": _ref("scene_intent", ArtifactKind.SCENE_INTENT, "b")},
        dependency_digests={"episode_direction": "a" * 64, "scene_facts": "2" * 64},
    )
    state = graph.apply(
        state,
        node_id="B0",
        outputs={
            "blocking_draft": _ref(
                "blocking_draft", ArtifactKind.BLOCKING_DRAFT, "c"
            )
        },
        dependency_digests={"scene_intent": "b" * 64},
    )
    state = graph.apply(
        state,
        node_id="DP",
        outputs={
            "dp_review": _ref("dp_review", ArtifactKind.DP_REVIEW_RESULT, "d")
        },
        dependency_digests={"dp_rules": "3" * 64},
    )

    invalidated = FieldInvalidator(graph).invalidate(
        state,
        changed_field_digests={"scene_facts": "9" * 64},
        reason="scene fact drift",
    )
    assert invalidated.invalidated_node_ids == ("S1", "B0")
    assert set(invalidated.state.accepted) == {"E0", "DP"}
    assert set(invalidated.state.outputs) == {"episode_direction", "dp_review"}
    assert invalidated.record.changed_field_digests["scene_facts"] == "9" * 64
    assert invalidated.record.invalidated_artifact_digests == ("b" * 64, "c" * 64)


def test_checkpoint_is_bound_to_dependency_digests_not_a_file_path_guess(tmp_path: Path) -> None:
    graph = _graph()
    session = RunSession.create(tmp_path / "runs", run_id="run-checkpoint", graph=graph)
    session.runner(owner="test-worker").accept(
        node_id="E0",
        artifacts={"episode_direction": _direction_artifact()},
        dependency_digests={"episode_facts": "1" * 64},
    )
    checkpoint = next((session.run_dir / "checkpoints").glob("*.json"))
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["accepted"]["E0"]["dependency_digests"] == {"episode_facts": "1" * 64}
    assert "path" not in json.dumps(payload["accepted"]["E0"], sort_keys=True)
    assert session.resume_plan({"episode_facts": "1" * 64}).checkpoint_sequence == 1
    assert session.resume_plan({"episode_facts": "f" * 64}).checkpoint_sequence == 0
    assert canonical_sha256(payload["state"]) == payload["state_sha256"]


def test_each_output_field_rejects_an_artifact_kind_from_another_stage() -> None:
    graph = _graph()
    with pytest.raises(StateInvariantError, match="artifact kind"):
        graph.apply(
            PersistentGraphState.empty("run-kind"),
            node_id="E0",
            outputs={
                "episode_direction": _ref(
                    "episode_direction", ArtifactKind.SCENE_INTENT, "a"
                )
            },
            dependency_digests={"episode_facts": "1" * 64},
        )


def test_session_rejects_a_persisted_state_with_a_wrong_field_kind(tmp_path: Path) -> None:
    graph = _graph()
    session = RunSession.create(tmp_path / "runs", run_id="run-tampered-state", graph=graph)
    accepted = session.runner(owner="worker").accept(
        node_id="E0",
        artifacts={"episode_direction": _direction_artifact()},
        dependency_digests={"episode_facts": "1" * 64},
    )
    forged = PersistentGraphState(
        run_id=accepted.run_id,
        outputs={
            "episode_direction": _ref(
                "episode_direction", ArtifactKind.SCENE_INTENT, "a"
            )
        },
        accepted=accepted.accepted,
        event_sequence=accepted.event_sequence + 1,
        current_commit_id=accepted.current_commit_id,
    )
    event = {
        "state": forged.to_dict(),
        "state_sha256": canonical_sha256(forged.to_dict()),
        "commit_id": None,
        "node_id": None,
    }
    with (session.run_dir / "STATE_EVENTS.jsonl").open("ab") as handle:
        handle.write(canonical_json_bytes(event))
        handle.write(b"\n")

    with pytest.raises(RunSessionError, match="artifact kind"):
        RunSession.open(session.run_dir, graph=graph).state()


def test_content_addressed_repository_rejects_a_mutated_payload(tmp_path: Path) -> None:
    graph = _graph()
    session = RunSession.create(tmp_path / "runs", run_id="run-tampered-artifact", graph=graph)
    artifact = _direction_artifact()
    ref = session.artifacts.put(artifact)
    path = (
        session.run_dir
        / "artifacts"
        / artifact.artifact_kind.value
        / f"{artifact.content_sha256}.json"
    )
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["payload"]["dramatic_promise"] = "Forged post-hash payload."
    path.write_text(json.dumps(stored), encoding="utf-8")

    assert not session.artifacts.contains(ref)
    with pytest.raises(StateInvariantError, match="not a persisted artifact"):
        session.runner(owner="worker").prepare(
            node_id="E0",
            artifacts={"episode_direction": ref},
            dependency_digests={"episode_facts": "1" * 64},
        )
