"""A2 acceptance tests for the frozen MODE:P v3.1 runtime ledger."""

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
from mode_p_vnext.domain.facts import NormalizedSource, SourcePartition, normalized_text_sha256
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.pipeline.graph import (
    V31_CANONICAL_NODE_ORDER,
    NodeSpec,
    StateGraph,
    canonical_v31_state_graph,
)
from mode_p_vnext.pipeline.invalidation import FieldInvalidator
from mode_p_vnext.pipeline.state import (
    SUPERSEDED_LIFECYCLE_STATUS,
    ArtifactRef,
    PersistentGraphState,
    StateInvariantError,
)
from mode_p_vnext.runtime.cache import NodeCacheKey
from mode_p_vnext.runtime.session import RunSession, RunSessionError
from mode_p_vnext.runtime.transaction import NodeTransaction, NodeTransactionError, PendingNodeWrite


def _digest(character: str) -> str:
    return character * 64


def _source_ref(label: str) -> SourceRef:
    text = f"source for {label}"
    return SourceRef(source_id=f"source:{label}", digest=normalized_text_sha256(text))


def _artifact(kind: ArtifactKind, label: str, *, parents: tuple[str, ...] = ()) -> ArtifactEnvelope[object]:
    source = _source_ref(label)
    text = f"source for {label}"
    if kind is ArtifactKind.NORMALIZED_SOURCE:
        payload: object = NormalizedSource(
            source_ref=source,
            normalized_text=text,
            encoding="utf-8",
            character_count=len(text),
            line_start_offsets=(0,),
            partitions=(SourcePartition("episode-1", "scene-1", 0, len(text)),),
        )
    elif kind is ArtifactKind.EPISODE_DIRECTION_DRAFT:
        payload = EpisodeDirectionDraft(
            dramatic_promise="A visible choice changes the relationship.",
            audience_contract="Every visual change remains traceable.",
            tension_curve=("arrival", "choice"),
            visual_principles=("hold the decisive object in view",),
            continuity_priorities=("preserve the entry state",),
            unresolved_questions=(),
        )
    elif kind is ArtifactKind.SCENE_INTENT_DRAFT:
        payload = SceneIntentDraft(
            scene_purpose="Make the choice legible.",
            state_change="Responsibility changes hands.",
            audience_information=("The transfer is visible.",),
            character_knowledge=("The lead knows the cost.",),
            performance_questions=("Does the pause read as resolve?",),
            director_problems=("Keep the object on the decision line.",),
            continuity_effects=("The object remains in frame.",),
            unresolved_questions=(),
        )
    else:  # The test graph deliberately uses only A1-frozen payload authorities.
        raise AssertionError(f"unsupported test artifact type: {kind}")
    artifact_id = IdFactory("a2-test-v3").create(
        artifact_kind=kind,
        episode_id="episode-1",
        scene_id="scene-1",
        stage="A2_TEST",
        input_digest=source.digest,
        ordinal=ord(label[0]),
    )
    return ArtifactEnvelope.create(
        artifact_id=artifact_id,
        artifact_type=kind,
        payload=payload,
        producer_stage="A2_TEST",
        parent_artifact_ids=parents,
        source_provenance=(source,),
        knowledge_snapshot_digest=None,
        created_at_utc="2026-08-01T00:00:00Z",
    )


def _ref(kind: ArtifactKind, label: str) -> ArtifactRef:
    """Build a repository-independent reference for graph-shape tests only."""

    identity = canonical_sha256({"a2_ref": label, "kind": kind.value})
    return ArtifactRef(
        artifact_id=f"id:{identity}",
        artifact_type=kind,
        schema_version="3.0",
        canonical_payload_sha256=canonical_sha256({"payload": label}),
        artifact_digest=canonical_sha256({"artifact": label, "kind": kind.value}),
    )


KNOWLEDGE_A = _digest("a")
KNOWLEDGE_B = _digest("b")
CAPABILITY_A = _digest("c")
CAPABILITY_B = _digest("d")


def _graph() -> StateGraph:
    return StateGraph(
        (
            NodeSpec("I0", "a2-v3.1", {"source": ArtifactKind.NORMALIZED_SOURCE}, ("raw_source",)),
            NodeSpec(
                "E0",
                "a2-v3.1",
                {"direction": ArtifactKind.EPISODE_DIRECTION_DRAFT},
                ("source",),
                uses_knowledge_snapshot=True,
            ),
            NodeSpec(
                "B1",
                "a2-v3.1",
                {"execution": ArtifactKind.SCENE_INTENT_DRAFT},
                ("direction",),
                uses_capability_profile=True,
            ),
            NodeSpec(
                "STORYBOARD",
                "a2-v3.1",
                {"storyboard_delivery": ArtifactKind.SCENE_INTENT_DRAFT},
                ("execution", "storyboard_adapter"),
            ),
            NodeSpec(
                "VIDEO",
                "a2-v3.1",
                {"video_delivery": ArtifactKind.SCENE_INTENT_DRAFT},
                ("execution", "video_adapter"),
            ),
        )
    )


def _atomic_bundle_graph() -> StateGraph:
    """Small stored-artifact analogue of the canonical Projection bundle."""

    return StateGraph(
        (
            NodeSpec(
                "Projection",
                "v3.1",
                {
                    "ast": ArtifactKind.NORMALIZED_SOURCE,
                    "storyboard": ArtifactKind.EPISODE_DIRECTION_DRAFT,
                    "video": ArtifactKind.SCENE_INTENT_DRAFT,
                },
                ("base", "storyboard_adapter", "video_adapter"),
                output_input_dependencies={
                    "ast": ("base",),
                    "storyboard": ("base", "storyboard_adapter"),
                    "video": ("base", "video_adapter"),
                },
            ),
        )
    )


def _execute(
    session: RunSession,
    node_id: str,
    artifact: ArtifactEnvelope[object],
    input_digests: dict[str, str],
    *,
    knowledge_snapshot_digest: str | None = None,
    capability_profile_digest: str | None = None,
) -> PersistentGraphState:
    snapshot = session.capture_execution_snapshot()
    field = {
        "I0": "source",
        "E0": "direction",
        "B1": "execution",
        "STORYBOARD": "storyboard_delivery",
        "VIDEO": "video_delivery",
    }[node_id]
    return session.runner(owner=f"worker-{node_id}").execute(
        node_id,
        artifacts={field: artifact},
        input_digests=input_digests,
        base_state_sha256=snapshot.base_state_sha256,
        knowledge_snapshot_digest=knowledge_snapshot_digest,
        capability_profile_digest=capability_profile_digest,
        candidate_revision=snapshot.candidate_revision,
        candidate_digest=snapshot.candidate_digest,
    )


def _complete(session: RunSession) -> PersistentGraphState:
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "source")
    state = _execute(session, "I0", source, {"raw_source": source.source_provenance[0].digest})
    direction = _artifact(ArtifactKind.EPISODE_DIRECTION_DRAFT, "direction", parents=(source.artifact_id,))
    state = _execute(
        session,
        "E0",
        direction,
        {"source": state.outputs["source"].artifact_digest},
        knowledge_snapshot_digest=KNOWLEDGE_A,
    )
    execution = _artifact(ArtifactKind.SCENE_INTENT_DRAFT, "execution", parents=(direction.artifact_id,))
    state = _execute(
        session,
        "B1",
        execution,
        {"direction": state.outputs["direction"].artifact_digest},
        capability_profile_digest=CAPABILITY_A,
    )
    storyboard = _artifact(ArtifactKind.SCENE_INTENT_DRAFT, "storyboard", parents=(execution.artifact_id,))
    state = _execute(
        session,
        "STORYBOARD",
        storyboard,
        {
            "execution": state.outputs["execution"].artifact_digest,
            "storyboard_adapter": _digest("e"),
        },
    )
    video = _artifact(ArtifactKind.SCENE_INTENT_DRAFT, "video", parents=(execution.artifact_id,))
    return _execute(
        session,
        "VIDEO",
        video,
        {
            "execution": state.outputs["execution"].artifact_digest,
            "video_adapter": _digest("f"),
        },
    )


def _complete_canonical_v31_graph() -> tuple[StateGraph, PersistentGraphState]:
    """Build a typed-ref-only canonical graph for runtime invalidation tests."""

    graph = canonical_v31_state_graph()
    state = PersistentGraphState.empty("canonical-adapter-run", graph_digest=graph.digest)
    for node in graph.nodes:
        outputs = {
            field_name: _ref(artifact_kind, f"canonical-{node.node_id}-{field_name}")
            for field_name, artifact_kind in node.output_types.items()
        }
        input_digests = {
            field_name: (
                state.outputs[field_name].artifact_digest
                if field_name in state.outputs
                else _digest("a")
            )
            for field_name in node.input_fields
        }
        state = graph.apply(
            state,
            node_id=node.node_id,
            outputs=outputs,
            input_digests=input_digests,
            knowledge_snapshot_digest=(KNOWLEDGE_A if node.uses_knowledge_snapshot else None),
            capability_profile_digest=(CAPABILITY_A if node.uses_capability_profile else None),
            commit_id=f"canonical-{node.node_id.lower()}-commit",
            candidate_validation_status=(
                ValidationStatus.TEXT_VALIDATED if node.node_id == "DP" else None
            ),
        )
    return graph, state


def test_v31_canonical_graph_owns_the_full_projection_bundle_and_dp_variant() -> None:
    graph = canonical_v31_state_graph()

    assert tuple(node.node_id for node in graph.nodes) == V31_CANONICAL_NODE_ORDER
    projection = graph.node("Projection")
    assert projection.required_output_fields == (
        "projection_ast",
        "storyboard_manifest",
        "video_manifest",
        "storyboard_adaptation",
        "video_adaptation",
    )
    assert projection.input_fields == (
        "vec",
        "storyboard_adapter_signature",
        "video_adapter_signature",
    )
    assert graph.node("G0").input_fields == (
        "vec",
        "projection_ast",
        "storyboard_manifest",
        "video_manifest",
        "storyboard_adaptation",
        "video_adaptation",
        "gate_policy_signature",
    )
    dp = graph.node("DP")
    assert dp.required_output_fields == ("review_packet", "dp_conclusion")
    assert dict(dp.optional_output_types) == {
        "revision_request": ArtifactKind.REVISION_REQUEST,
    }
    assert graph.invalidation_closure(("storyboard_adapter_signature",)) == (
        "Projection",
        "G0",
        "DP",
    )
    assert graph.invalidation_closure(("video_adapter_signature",)) == (
        "Projection",
        "G0",
        "DP",
    )
    assert graph.invalidation_closure(("gate_policy_signature",)) == ("G0", "DP")
    assert graph.invalidation_closure(("dp_rule_signature",)) == ("DP",)
    assert graph.invalidation_closure(("dp_prompt_signature",)) == ("DP",)
    root = PersistentGraphState.empty("canonical-run", graph_digest=graph.digest)
    assert graph.runnable_node_ids(root) == ("I0",)


def test_canonical_adapter_change_retains_unaffected_bundle_fields_for_atomic_rebuild() -> None:
    graph, accepted = _complete_canonical_v31_graph()
    original = dict(accepted.outputs)
    result = FieldInvalidator(graph).invalidate(
        accepted,
        changed_field_digests={"storyboard_adapter_signature": _digest("9")},
        reason="storyboard adapter profile changed",
        commit_id="adapter-only-invalidation",
    )
    replacement = result.state

    assert result.invalidated_node_ids == ("Projection", "G0", "DP")
    assert replacement.candidate_revision == accepted.candidate_revision + 1
    assert replacement.candidate_validation_status is ValidationStatus.DRAFT
    assert set(replacement.retained_outputs) == {
        "projection_ast",
        "video_manifest",
        "video_adaptation",
    }
    assert {
        retained.artifact_ref.artifact_digest
        for retained in replacement.retained_outputs.values()
    } == {
        original["projection_ast"].artifact_digest,
        original["video_manifest"].artifact_digest,
        original["video_adaptation"].artifact_digest,
    }
    assert {
        original["projection_ast"].artifact_digest,
        original["video_manifest"].artifact_digest,
        original["video_adaptation"].artifact_digest,
    }.isdisjoint(result.record.invalidated_artifact_digests)
    assert set(result.record.retained_artifact_digests) == {
        original["projection_ast"].artifact_digest,
        original["video_manifest"].artifact_digest,
        original["video_adaptation"].artifact_digest,
    }
    assert "storyboard_manifest" not in replacement.outputs
    assert "storyboard_adaptation" not in replacement.outputs
    assert graph.runnable_node_ids(replacement) == ("Projection",)

    projection = graph.node("Projection")
    rebuilt_outputs = {
        field_name: (
            replacement.retained_outputs[field_name].artifact_ref
            if field_name in replacement.retained_outputs
            else _ref(artifact_kind, f"replacement-{field_name}")
        )
        for field_name, artifact_kind in projection.output_types.items()
    }
    projection_inputs = {
        "vec": replacement.outputs["vec"].artifact_digest,
        "storyboard_adapter_signature": _digest("9"),
        "video_adapter_signature": _digest("a"),
    }
    bad_rebuild = dict(rebuilt_outputs)
    bad_rebuild["projection_ast"] = _ref(ArtifactKind.PROJECTION_AST, "rewritten-ast")
    with pytest.raises(StateInvariantError, match="cannot rewrite retained output"):
        graph.apply(
            replacement,
            node_id="Projection",
            outputs=bad_rebuild,
            input_digests=projection_inputs,
            knowledge_snapshot_digest=None,
            capability_profile_digest=CAPABILITY_A,
            commit_id="bad-adapter-rebuild",
        )
    rebuilt = graph.apply(
        replacement,
        node_id="Projection",
        outputs=rebuilt_outputs,
        input_digests=projection_inputs,
        knowledge_snapshot_digest=None,
        capability_profile_digest=CAPABILITY_A,
        commit_id="adapter-rebuild",
    )
    assert not rebuilt.retained_outputs
    assert rebuilt.outputs["projection_ast"] == original["projection_ast"]
    assert rebuilt.outputs["video_manifest"] == original["video_manifest"]
    assert rebuilt.outputs["video_adaptation"] == original["video_adaptation"]
    assert rebuilt.outputs["storyboard_manifest"] != original["storyboard_manifest"]
    assert rebuilt.outputs["storyboard_adaptation"] != original["storyboard_adaptation"]


def test_adapter_only_retention_survives_atomic_commit_replay_and_rebuild(tmp_path: Path) -> None:
    graph = _atomic_bundle_graph()
    session = RunSession.create(tmp_path / "runs", run_id="atomic-adapter", graph=graph)
    base_inputs = {
        "base": _digest("a"),
        "storyboard_adapter": _digest("b"),
        "video_adapter": _digest("c"),
    }
    initial_snapshot = session.capture_execution_snapshot()
    initial = session.runner(owner="projection-worker").execute(
        "Projection",
        artifacts={
            "ast": _artifact(ArtifactKind.NORMALIZED_SOURCE, "bundle-ast"),
            "storyboard": _artifact(ArtifactKind.EPISODE_DIRECTION_DRAFT, "bundle-story"),
            "video": _artifact(ArtifactKind.SCENE_INTENT_DRAFT, "bundle-video"),
        },
        input_digests=base_inputs,
        base_state_sha256=initial_snapshot.base_state_sha256,
        candidate_revision=initial_snapshot.candidate_revision,
        candidate_digest=initial_snapshot.candidate_digest,
    )
    original = dict(initial.outputs)
    invalidation = session.invalidate(
        changed_field_digests={"storyboard_adapter": _digest("9")},
        reason="only the storyboard adapter changed",
    )
    partial = session.state()
    assert invalidation.record.invalidated_artifact_digests == (
        original["storyboard"].artifact_digest,
    )
    assert set(partial.retained_outputs) == {"ast", "video"}
    assert partial.outputs["ast"] == original["ast"]
    assert partial.outputs["video"] == original["video"]

    reopened = RunSession.open(session.run_dir, graph=graph)
    assert reopened.state().to_dict() == partial.to_dict()
    snapshot = reopened.capture_execution_snapshot()
    rebuilt = reopened.runner(owner="projection-rebuild").execute(
        "Projection",
        artifacts={
            "ast": partial.retained_outputs["ast"].artifact_ref,
            "storyboard": _artifact(
                ArtifactKind.EPISODE_DIRECTION_DRAFT,
                "bundle-story-rebuilt",
            ),
            "video": partial.retained_outputs["video"].artifact_ref,
        },
        input_digests={
            **base_inputs,
            "storyboard_adapter": _digest("9"),
        },
        base_state_sha256=snapshot.base_state_sha256,
        candidate_revision=snapshot.candidate_revision,
        candidate_digest=snapshot.candidate_digest,
    )
    assert not rebuilt.retained_outputs
    assert rebuilt.outputs["ast"] == original["ast"]
    assert rebuilt.outputs["video"] == original["video"]
    assert rebuilt.outputs["storyboard"] != original["storyboard"]


def test_conditional_dp_revision_request_is_a_graph_owned_persistent_output() -> None:
    graph = StateGraph(
        (
            NodeSpec(
                "DP",
                "a2-v3.1",
                {
                    "review_packet": ArtifactKind.REVIEW_PACKET,
                    "dp_conclusion": ArtifactKind.DP_REVIEW_RESULT,
                },
                ("raw_packet",),
                optional_output_types={"revision_request": ArtifactKind.REVISION_REQUEST},
            ),
        )
    )
    raw_packet = _digest("a")
    ready = graph.apply(
        PersistentGraphState.empty("ready-run", graph_digest=graph.digest),
        node_id="DP",
        outputs={
            "review_packet": _ref(ArtifactKind.REVIEW_PACKET, "ready-packet"),
            "dp_conclusion": _ref(ArtifactKind.DP_REVIEW_RESULT, "ready-conclusion"),
        },
        input_digests={"raw_packet": raw_packet},
        knowledge_snapshot_digest=None,
        capability_profile_digest=None,
        commit_id="ready-commit",
        candidate_validation_status=ValidationStatus.TEXT_VALIDATED,
    )
    assert set(ready.outputs) == {"review_packet", "dp_conclusion"}
    assert ready.candidate_validation_status is ValidationStatus.TEXT_VALIDATED
    replacement, invalidated, _ = graph.invalidate(
        ready,
        changed_fields=("raw_packet",),
        commit_id="ready-superseded",
    )
    assert invalidated == ("DP",)
    assert replacement.candidate_validation_status is ValidationStatus.DRAFT

    revision = graph.apply(
        PersistentGraphState.empty("revision-run", graph_digest=graph.digest),
        node_id="DP",
        outputs={
            "review_packet": _ref(ArtifactKind.REVIEW_PACKET, "revision-packet"),
            "dp_conclusion": _ref(ArtifactKind.DP_REVIEW_RESULT, "revision-conclusion"),
            "revision_request": _ref(ArtifactKind.REVISION_REQUEST, "revision-request"),
        },
        input_digests={"raw_packet": raw_packet},
        knowledge_snapshot_digest=None,
        capability_profile_digest=None,
        commit_id="revision-commit",
    )
    assert set(revision.outputs) == {
        "review_packet", "dp_conclusion", "revision_request",
    }
    assert revision.accepted["DP"].output_artifacts["revision_request"].artifact_type is ArtifactKind.REVISION_REQUEST
    with pytest.raises(StateInvariantError, match="revision request cannot advance"):
        graph.apply(
            PersistentGraphState.empty("invalid-ready", graph_digest=graph.digest),
            node_id="DP",
            outputs={
                "review_packet": _ref(ArtifactKind.REVIEW_PACKET, "invalid-packet"),
                "dp_conclusion": _ref(ArtifactKind.DP_REVIEW_RESULT, "invalid-conclusion"),
                "revision_request": _ref(ArtifactKind.REVISION_REQUEST, "invalid-request"),
            },
            input_digests={"raw_packet": raw_packet},
            knowledge_snapshot_digest=None,
            capability_profile_digest=None,
            commit_id="invalid-ready-commit",
            candidate_validation_status=ValidationStatus.TEXT_VALIDATED,
        )


def test_persistent_state_graph_records_only_canonical_refs_and_full_context(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-1", graph=_graph(), write_scope="episode-1:scene-1")
    state = _complete(session)
    direction = state.accepted["E0"]
    assert direction.stage_signature == _graph().node("E0").stage_signature
    assert direction.input_artifacts["source"].artifact_id == state.outputs["source"].artifact_id
    assert direction.input_digests["source"] == state.outputs["source"].artifact_digest
    assert direction.knowledge_snapshot_digest == KNOWLEDGE_A
    assert state.accepted["B1"].capability_profile_digest == CAPABILITY_A
    assert direction.candidate_revision == state.candidate_revision
    assert direction.input_candidate_digest != state.candidate_digest
    assert state.graph_digest == _graph().digest
    assert all(not hasattr(ref, "payload") for ref in state.outputs.values())
    assert session.artifacts.contains(state.outputs["execution"])
    reopened = RunSession.open(session.run_dir, graph=_graph())
    assert reopened.state().to_dict() == state.to_dict()


def test_checkpoint_resume_uses_committed_chain_not_a_path_guess(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-2", graph=_graph())
    state = _complete(session)
    checkpoint = session.checkpoint()
    assert checkpoint.is_file()
    reopened = RunSession.open(session.run_dir, graph=_graph())
    plan = reopened.resume_plan({})
    assert plan.checkpoint_sequence == state.event_sequence
    assert plan.accepted_node_ids == ("I0", "E0", "B1", "STORYBOARD", "VIDEO")
    assert plan.runnable_node_ids == ()
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["candidate_revision"] == state.candidate_revision
    assert payload["candidate_digest"] == state.candidate_digest
    assert payload["candidate_validation_status"] == state.candidate_validation_status.value
    payload["state"]["run_id"] = "forged"
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")
    assert reopened.state().run_id == "run-2"
    assert reopened.resume_plan({}).checkpoint_sequence == 0


def test_pending_write_is_never_recovered_but_committed_crash_boundary_is(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-3", graph=_graph())
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "pending")
    snapshot = session.capture_execution_snapshot()
    pending = session.runner(owner="writer").prepare(
        "I0",
        artifacts={"source": source},
        input_digests={"raw_source": source.source_provenance[0].digest},
        base_state_sha256=snapshot.base_state_sha256,
    )
    assert pending.base_candidate_revision == snapshot.candidate_revision
    assert pending.base_candidate_digest == snapshot.candidate_digest
    assert pending.transition["candidate_revision"] == snapshot.candidate_revision
    assert pending.transition["candidate_digest"] == snapshot.candidate_digest
    tampered_pending = pending.to_dict()
    tampered_pending["transition"]["candidate_validation_status"] = "text_validated"
    with pytest.raises(NodeTransactionError, match="resulting validation status"):
        PendingNodeWrite.from_dict(tampered_pending)
    assert not session.state().accepted
    resumed = RunSession.open(session.run_dir, graph=_graph())
    assert resumed.recover_pending(owner="recovery") == ()
    assert not resumed.state().accepted
    assert (resumed.run_dir / "quarantine" / pending.generation_id).is_dir()

    committed = RunSession.create(tmp_path / "runs", run_id="run-4", graph=_graph())
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "committed")
    pending = committed.runner(owner="writer").prepare(
        "I0",
        artifacts={"source": source},
        input_digests={"raw_source": source.source_provenance[0].digest},
        base_state_sha256=committed.capture_execution_snapshot().base_state_sha256,
    )
    NodeTransaction.promote(committed.run_dir, pending)  # crash after atomic rename, before pointer publication
    resumed = RunSession.open(committed.run_dir, graph=_graph())
    assert resumed.recover_pending(owner="recovery") == ("I0",)
    assert tuple(resumed.state().accepted) == ("I0",)


def test_unrecovered_committed_child_blocks_stale_state_use_until_explicit_recovery(
    tmp_path: Path,
) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-4a", graph=_graph())
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "committed-gap")
    pending = session.runner(owner="writer").prepare(
        "I0",
        artifacts={"source": source},
        input_digests={"raw_source": source.source_provenance[0].digest},
        base_state_sha256=session.capture_execution_snapshot().base_state_sha256,
    )
    NodeTransaction.promote(session.run_dir, pending)

    resumed = RunSession.open(session.run_dir, graph=_graph())
    with pytest.raises(RunSessionError, match="unresolved committed recovery candidate"):
        resumed.state()
    with pytest.raises(RunSessionError, match="unresolved committed recovery candidate"):
        resumed.capture_execution_snapshot()

    assert resumed.recover_pending(owner="recovery") == ("I0",)
    assert tuple(resumed.state().accepted) == ("I0",)


def test_content_addressed_artifacts_and_cache_reject_mutation(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-5", graph=_graph())
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "content")
    state = _execute(session, "I0", source, {"raw_source": source.source_provenance[0].digest})
    ref = state.outputs["source"]
    assert session.artifacts.path_for(source).name == f"{ref.artifact_digest}.json"
    key = NodeCacheKey(
        node_id="I0",
        stage_signature=_graph().node("I0").stage_signature,
        input_digests={"raw_source": source.source_provenance[0].digest},
        candidate_revision=state.accepted["I0"].candidate_revision,
        candidate_digest=state.accepted["I0"].input_candidate_digest,
        knowledge_snapshot_digest=None,
        capability_profile_digest=None,
    )
    session.cache.put(key, ref)
    assert session.cache.get(key) == ref
    assert not hasattr(session.cache.get(key), "payload")
    artifact_path = session.artifacts.path_for(source)
    forged = json.loads(artifact_path.read_text(encoding="utf-8"))
    forged["producer_stage"] = "forged"
    artifact_path.write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(RunSessionError, match="no longer verifies"):
        RunSession.open(session.run_dir, graph=_graph()).state()


def test_field_invalidation_is_minimal_and_adapter_scoped(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-6", graph=_graph())
    _complete(session)
    result = session.invalidate(
        changed_field_digests={"storyboard_adapter": _digest("9")},
        reason="storyboard adapter changed",
    )
    assert result.invalidated_node_ids == ("STORYBOARD",)
    assert result.record.retired_lifecycle_status == SUPERSEDED_LIFECYCLE_STATUS
    assert result.record.next_candidate_revision == result.record.source_candidate_revision + 1
    assert set(session.state().accepted) == {"I0", "E0", "B1", "VIDEO"}
    assert "video_delivery" in session.state().outputs
    assert "storyboard_delivery" not in session.state().outputs

    result = session.invalidate(
        changed_field_digests={"raw_source": _digest("8")},
        reason="normalized source changed",
    )
    assert result.invalidated_node_ids == ("I0", "E0", "B1", "VIDEO")
    assert not session.state().accepted


def test_undeclared_field_invalidation_fails_closed_without_mutating_state(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-6a", graph=_graph())
    _complete(session)
    before = session.state().to_dict()

    with pytest.raises(StateInvariantError, match="not declared in StateGraph"):
        session.invalidate(
            changed_field_digests={"unknown_adapter_or_fact_route": _digest("7")},
            reason="an unmodeled input changed",
        )

    assert session.state().to_dict() == before


def test_capability_profile_invalidation_keeps_director_and_knowledge_selection(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-7", graph=_graph())
    _complete(session)
    before = session.state().to_dict()
    no_change = session.invalidate_capability_profile(
        capability_profile_digest=CAPABILITY_A,
        reason="same capability profile",
    )
    assert no_change.invalidated_node_ids == ()
    assert session.state().to_dict() == before
    result = session.invalidate_capability_profile(
        capability_profile_digest=CAPABILITY_B,
        reason="generation capability profile changed",
    )
    assert result.invalidated_node_ids == ("B1", "STORYBOARD", "VIDEO")
    state = session.state()
    assert set(state.accepted) == {"I0", "E0"}
    assert state.accepted["E0"].knowledge_snapshot_digest == KNOWLEDGE_A


def test_selected_knowledge_snapshot_controls_invalidation_not_candidate_churn(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-8", graph=_graph())
    _complete(session)
    from mode_p_vnext.pipeline.invalidation import FieldInvalidator

    no_change = FieldInvalidator(_graph()).invalidate_knowledge_snapshot(
        session.state(),
        knowledge_snapshot_digest=KNOWLEDGE_A,
        reason="candidate set changed but selected snapshot did not",
        commit_id="plan-knowledge",
    )
    assert no_change.invalidated_node_ids == ()
    changed = FieldInvalidator(_graph()).invalidate_knowledge_snapshot(
        session.state(),
        knowledge_snapshot_digest=KNOWLEDGE_B,
        reason="selected snapshot changed",
        commit_id="plan-knowledge-2",
    )
    assert changed.invalidated_node_ids == ("E0", "B1", "STORYBOARD", "VIDEO")


def test_stale_concurrent_result_and_same_scope_writer_are_rejected(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    first = RunSession.create(runs, run_id="run-9a", graph=_graph(), write_scope="episode-1:scene-1")
    second = RunSession.create(runs, run_id="run-9b", graph=_graph(), write_scope="episode-1:scene-1")
    stale = first.capture_execution_snapshot().base_state_sha256
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "stale-source")
    _execute(first, "I0", source, {"raw_source": source.source_provenance[0].digest})
    direction = _artifact(ArtifactKind.EPISODE_DIRECTION_DRAFT, "stale-direction")
    with pytest.raises(StateInvariantError, match="stale concurrent result"):
        first.runner(owner="late-worker").prepare(
            "E0",
            artifacts={"direction": direction},
            input_digests={"source": first.state().outputs["source"].artifact_digest},
            base_state_sha256=stale,
            knowledge_snapshot_digest=KNOWLEDGE_A,
        )
    other = _artifact(ArtifactKind.NORMALIZED_SOURCE, "other")
    with first._lock("lock-holder"):
        with pytest.raises(RunSessionError, match="write lock is already held"):
            second.runner(owner="other-worker").prepare(
                "I0",
                artifacts={"source": other},
                input_digests={"raw_source": other.source_provenance[0].digest},
                base_state_sha256=second.capture_execution_snapshot().base_state_sha256,
            )


def test_explicit_candidate_tuple_rejects_stale_or_malformed_producer_claims(
    tmp_path: Path,
) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-candidate", graph=_graph())
    snapshot = session.capture_execution_snapshot()
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "candidate-source")

    with pytest.raises(StateInvariantError, match="stale candidate revision"):
        session.runner(owner="revision-mismatch").prepare(
            "I0",
            artifacts={"source": source},
            input_digests={"raw_source": source.source_provenance[0].digest},
            base_state_sha256=snapshot.base_state_sha256,
            candidate_revision=snapshot.candidate_revision + 1,
            candidate_digest=snapshot.candidate_digest,
        )
    with pytest.raises(StateInvariantError, match="stale candidate digest"):
        session.runner(owner="digest-mismatch").prepare(
            "I0",
            artifacts={"source": source},
            input_digests={"raw_source": source.source_provenance[0].digest},
            base_state_sha256=snapshot.base_state_sha256,
            candidate_revision=snapshot.candidate_revision,
            candidate_digest=_digest("f"),
        )
    with pytest.raises(StateInvariantError, match="candidate_revision must be"):
        session.runner(owner="revision-type").prepare(
            "I0",
            artifacts={"source": source},
            input_digests={"raw_source": source.source_provenance[0].digest},
            base_state_sha256=snapshot.base_state_sha256,
            candidate_revision=True,
            candidate_digest=snapshot.candidate_digest,
        )
    assert not session.state().accepted


@pytest.mark.parametrize("node_id", ("Projection", "G0", "DP"))
def test_v31_projection_gate_and_dp_require_an_explicit_captured_candidate_tuple(
    tmp_path: Path,
    node_id: str,
) -> None:
    """The concurrent visual/review boundary cannot fill its tuple inside the lock.

    A generic historical graph may use the legacy convenience default, but the
    v3.1 Projection/G0/DP nodes must prove that the worker captured the exact
    candidate revision and digest before it attempted a write.
    """

    graph = StateGraph(
        (
            NodeSpec(
                node_id,
                "v3.1",
                {"result": ArtifactKind.PROJECTION_AST},
                ("external_input",),
            ),
        )
    )
    session = RunSession.create(
        tmp_path / "runs",
        run_id=f"strict-{node_id.lower()}",
        graph=graph,
    )
    snapshot = session.capture_execution_snapshot()
    kwargs = {
        "artifacts": {},
        "input_digests": {"external_input": _digest("a")},
        "base_state_sha256": snapshot.base_state_sha256,
    }
    with pytest.raises(StateInvariantError, match="requires an explicit captured candidate tuple"):
        session.runner(owner="strict-worker").prepare(node_id, **kwargs)
    with pytest.raises(StateInvariantError, match="must be supplied together"):
        session.runner(owner="strict-worker").prepare(
            node_id,
            **kwargs,
            candidate_revision=snapshot.candidate_revision,
        )
    with pytest.raises(StateInvariantError, match=r"requires \('result',\)"):
        session.runner(owner="strict-worker").prepare(
            node_id,
            **kwargs,
            candidate_revision=snapshot.candidate_revision,
            candidate_digest=snapshot.candidate_digest,
        )


def test_candidate_digest_partitions_cache_and_invalidation_lifecycle(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-candidate-cache", graph=_graph())
    root = session.capture_execution_snapshot()
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "cache-candidate")
    state = _execute(session, "I0", source, {"raw_source": source.source_provenance[0].digest})
    accepted = state.accepted["I0"]
    before = NodeCacheKey(
        node_id="I0",
        stage_signature=_graph().node("I0").stage_signature,
        input_digests={"raw_source": source.source_provenance[0].digest},
        candidate_revision=root.candidate_revision,
        candidate_digest=root.candidate_digest,
        knowledge_snapshot_digest=None,
        capability_profile_digest=None,
    )
    after = NodeCacheKey(
        node_id="I0",
        stage_signature=_graph().node("I0").stage_signature,
        input_digests={"raw_source": source.source_provenance[0].digest},
        candidate_revision=accepted.candidate_revision,
        candidate_digest=state.candidate_digest,
        knowledge_snapshot_digest=None,
        capability_profile_digest=None,
    )
    assert before.digest != after.digest

    result = session.invalidate(
        changed_field_digests={"raw_source": _digest("9")},
        reason="source candidate replaced",
    )
    invalidated = session.state()
    assert result.record.source_candidate_revision == root.candidate_revision
    assert result.record.next_candidate_revision == root.candidate_revision + 1
    assert result.record.source_candidate_digest == state.candidate_digest
    assert result.record.next_candidate_digest == invalidated.candidate_digest
    assert result.record.retired_lifecycle_status == SUPERSEDED_LIFECYCLE_STATUS


def test_graph_rejects_wrong_artifact_type_and_noncanonical_state_schema() -> None:
    graph = _graph()
    wrong = ArtifactRef(
        artifact_id="id:" + _digest("1"),
        artifact_type=ArtifactKind.EPISODE_DIRECTION_DRAFT,
        schema_version="3.0",
        canonical_payload_sha256=_digest("2"),
        artifact_digest=_digest("3"),
    )
    with pytest.raises(StateInvariantError, match="artifact type"):
        graph.apply(
            PersistentGraphState.empty("run-type", graph_digest=graph.digest),
            node_id="I0",
            outputs={"source": wrong},
            input_digests={"raw_source": _digest("4")},
            knowledge_snapshot_digest=None,
            capability_profile_digest=None,
            commit_id="commit-type",
        )
    state = PersistentGraphState.empty("run-type", graph_digest=graph.digest).to_dict()
    state["schema_version"] = "2.2"
    with pytest.raises(StateInvariantError, match="unsupported"):
        PersistentGraphState.from_dict(state)


def test_graph_rejects_dependency_cycles_before_a_run_is_persisted() -> None:
    with pytest.raises(StateInvariantError, match="dependency cycle"):
        StateGraph(
            (
                NodeSpec(
                    "A",
                    "3.0",
                    {"a": ArtifactKind.NORMALIZED_SOURCE},
                    ("b",),
                ),
                NodeSpec(
                    "B",
                    "3.0",
                    {"b": ArtifactKind.EPISODE_DIRECTION_DRAFT},
                    ("a",),
                ),
            )
        )


def test_content_addressed_cache_refuses_competing_value_for_same_key(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-cache", graph=_graph())
    first = session.artifacts.put(_artifact(ArtifactKind.NORMALIZED_SOURCE, "cache-first"))
    competing = session.artifacts.put(_artifact(ArtifactKind.NORMALIZED_SOURCE, "cache-second"))
    key = NodeCacheKey(
        node_id="I0",
        stage_signature=_graph().node("I0").stage_signature,
        input_digests={"raw_source": _digest("7")},
        candidate_revision=session.capture_execution_snapshot().candidate_revision,
        candidate_digest=session.capture_execution_snapshot().candidate_digest,
        knowledge_snapshot_digest=None,
        capability_profile_digest=None,
    )
    session.cache.put(key, first)
    with pytest.raises(StateInvariantError, match="already names different"):
        session.cache.put(key, competing)
    assert session.cache.get(key) == first


def test_v31_runtime_does_not_reintroduce_legacy_state_authorities() -> None:
    package_root = Path(__file__).resolve().parents[1]
    runtime_sources = tuple((package_root / "runtime").glob("*.py"))
    assert runtime_sources
    for source in runtime_sources:
        text = source.read_text(encoding="utf-8")
        assert "mode_p_vnext.session_state" not in text
        assert "mode_p_vnext.atomic_commit" not in text
        assert "mode_p_vnext.dependency_invalidation" not in text


def test_pointer_tampering_and_ambiguous_committed_recovery_fail_closed(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-10", graph=_graph())
    source = _artifact(ArtifactKind.NORMALIZED_SOURCE, "pointer")
    _execute(session, "I0", source, {"raw_source": source.source_provenance[0].digest})
    pointer = json.loads(session.current_pointer_path.read_text(encoding="utf-8"))
    pointer["state_sha256"] = _digest("9")
    session.current_pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
    with pytest.raises(RunSessionError, match="pointer digest"):
        RunSession.open(session.run_dir, graph=_graph()).state()

    ambiguous = RunSession.create(tmp_path / "runs", run_id="run-11", graph=_graph())
    crash_boundary_state = PersistentGraphState.empty("run-11", graph_digest=_graph().digest)
    for label in ("ambiguous-a", "ambiguous-b"):
        artifact = _artifact(ArtifactKind.NORMALIZED_SOURCE, label)
        artifact_ref = ambiguous.artifacts.put(artifact)
        commit_id, generation_id = NodeTransaction.new_identity("I0")
        next_state = _graph().apply(
            crash_boundary_state,
            node_id="I0",
            outputs={"source": artifact_ref},
            input_digests={"raw_source": artifact.source_provenance[0].digest},
            knowledge_snapshot_digest=None,
            capability_profile_digest=None,
            commit_id=commit_id,
        )
        pending = NodeTransaction.prepare(
            ambiguous.run_dir,
            transaction_kind="node",
            base_state=crash_boundary_state,
            next_state=next_state,
            parent_commit_id="",
            commit_id=commit_id,
            generation_id=generation_id,
            transition={
                "kind": "node",
                "node_id": "I0",
                "graph_digest": _graph().digest,
                "outputs": {"source": artifact_ref.to_dict()},
                "input_digests": {"raw_source": artifact.source_provenance[0].digest},
                "knowledge_snapshot_digest": None,
                "capability_profile_digest": None,
                "candidate_revision": crash_boundary_state.candidate_revision,
                "candidate_digest": crash_boundary_state.candidate_digest,
                "candidate_validation_status": next_state.candidate_validation_status.value,
            },
        )
        NodeTransaction.promote(ambiguous.run_dir, pending)
    with pytest.raises(RunSessionError, match="multiple committed children"):
        RunSession.open(ambiguous.run_dir, graph=_graph()).state()
    with pytest.raises(RunSessionError, match="multiple committed children"):
        RunSession.open(ambiguous.run_dir, graph=_graph()).recover_pending(owner="recovery")
