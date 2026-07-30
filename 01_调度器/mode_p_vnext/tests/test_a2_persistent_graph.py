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
    canonical_sha256,
)
from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
from mode_p_vnext.pipeline.graph import NodeSpec, StateGraph
from mode_p_vnext.pipeline.invalidation import FieldInvalidator
from mode_p_vnext.pipeline.state import ArtifactRef, PersistentGraphState, StateInvariantError
from mode_p_vnext.runtime.cache import NodeCacheKey
from mode_p_vnext.runtime.session import RunSession


def _direction_artifact() -> ArtifactEnvelope[EpisodeDirectionDraft]:
    source = SourceRef("script:episode-1", "a" * 64)
    payload = EpisodeDirectionDraft(
        dramatic_promise="A choice reshapes the relationship.",
        audience_contract="The cause of every change remains legible.",
        tension_curve=("arrival", "choice"),
        visual_principles=("preserve the decision line",),
        continuity_priorities=("the key remains visible",),
        unresolved_questions=(),
    )
    return ArtifactEnvelope.create(
        artifact_id="episode_direction:episode-1:episode:A1:0001:aaaaaaaaaaaaaaaaaaaa",
        artifact_kind=ArtifactKind.EPISODE_DIRECTION,
        schema_version="2.1",
        program_version="test-vnext-2.1",
        payload=payload,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
        created_at="2026-07-30T00:00:00Z",
        validation_status=ValidationStatus.DRAFT,
    )


def _scene_intent_artifact() -> ArtifactEnvelope[SceneIntentDraft]:
    source = SourceRef("script:scene-1", "b" * 64)
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
        artifact_id="scene_intent:episode-1:scene-1:S1:0001:bbbbbbbbbbbbbbbbbbbb",
        artifact_kind=ArtifactKind.SCENE_INTENT,
        schema_version="2.1",
        program_version="test-vnext-2.1",
        payload=payload,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
        created_at="2026-07-30T00:00:00Z",
        validation_status=ValidationStatus.DRAFT,
    )


def _graph() -> StateGraph:
    return StateGraph(
        (
            NodeSpec(
                node_id="E0",
                node_version="1",
                owns_fields=("episode_direction",),
                input_fields=("episode_facts",),
            ),
            NodeSpec(
                node_id="S1",
                node_version="1",
                owns_fields=("scene_intent",),
                input_fields=("episode_direction", "scene_facts"),
            ),
            NodeSpec(
                node_id="B0",
                node_version="1",
                owns_fields=("blocking_draft",),
                input_fields=("scene_intent",),
            ),
            NodeSpec(
                node_id="DP",
                node_version="1",
                owns_fields=("dp_review",),
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
                owns_fields=("episode_direction",),
                input_fields=("episode_facts",),
            ),
            NodeSpec(
                node_id="S1",
                node_version="1",
                owns_fields=("scene_intent",),
                input_fields=("episode_direction", "scene_facts"),
            ),
            NodeSpec(
                node_id="B0",
                node_version="1",
                owns_fields=("blocking_draft",),
                input_fields=("scene_intent",),
            ),
            NodeSpec(
                node_id="B1",
                node_version="1",
                owns_fields=("blocking_commit",),
                input_fields=("blocking_draft",),
            ),
        )
    )


def _ref(field_name: str, digest_char: str) -> ArtifactRef:
    return ArtifactRef(
        artifact_id=f"{field_name}:{digest_char}",
        artifact_kind=ArtifactKind.SCRIPT_FACT,
        content_sha256=digest_char * 64,
        schema_version="2.1",
    )


def _generic_artifact(field_name: str, digest_char: str) -> ArtifactEnvelope[dict[str, str]]:
    source = SourceRef(f"test:{field_name}", digest_char * 64)
    return ArtifactEnvelope.create(
        artifact_id=f"{field_name}:episode-1:scene-1:{digest_char * 20}",
        artifact_kind=ArtifactKind.SCRIPT_FACT,
        schema_version="2.1",
        program_version="test-vnext-2.1",
        payload={"field": field_name, "marker": digest_char},
        source_refs=(source,),
        dependency_digests={"source": source.digest},
        created_at="2026-07-30T00:00:00Z",
        validation_status=ValidationStatus.DRAFT,
    )


def test_typed_state_graph_allows_only_owned_partial_state_and_preserves_upstream() -> None:
    graph = _graph()
    state = PersistentGraphState.empty("run-graph")
    state = graph.apply(
        state,
        node_id="E0",
        outputs={"episode_direction": _ref("episode_direction", "a")},
        dependency_digests={"episode_facts": "1" * 64},
    )
    assert state.outputs["episode_direction"].content_sha256 == "a" * 64
    assert state.accepted["E0"].dependency_digests["episode_facts"] == "1" * 64

    with pytest.raises(StateInvariantError, match="owns"):
        graph.apply(
            state,
            node_id="S1",
            outputs={"episode_direction": _ref("episode_direction", "b")},
            dependency_digests={"scene_facts": "2" * 64},
        )
    with pytest.raises(StateInvariantError, match="accepted"):
        graph.apply(
            state,
            node_id="E0",
            outputs={"episode_direction": _ref("episode_direction", "b")},
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
        ("B1", "blocking_commit", "d"),
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
        else:
            dependency_digests = {
                "blocking_draft": state.outputs["blocking_draft"].content_sha256,
            }
        artifact = _generic_artifact(field_name, digest_char)
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
        outputs={"episode_direction": _ref("episode_direction", "a")},
        dependency_digests={"episode_facts": "1" * 64},
    )
    state = graph.apply(
        state,
        node_id="S1",
        outputs={"scene_intent": _ref("scene_intent", "b")},
        dependency_digests={"episode_direction": "a" * 64, "scene_facts": "2" * 64},
    )
    state = graph.apply(
        state,
        node_id="B0",
        outputs={"blocking_draft": _ref("blocking_draft", "c")},
        dependency_digests={"scene_intent": "b" * 64},
    )
    state = graph.apply(
        state,
        node_id="DP",
        outputs={"dp_review": _ref("dp_review", "d")},
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
