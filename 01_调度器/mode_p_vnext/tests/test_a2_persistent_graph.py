"""A2 acceptance tests for the frozen MODE:P v3.0 runtime ledger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mode_p_vnext.domain.artifact import ArtifactEnvelope, ArtifactKind, SourceRef, canonical_sha256
from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
from mode_p_vnext.domain.facts import NormalizedSource, SourcePartition, normalized_text_sha256
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.pipeline.graph import NodeSpec, StateGraph
from mode_p_vnext.pipeline.state import ArtifactRef, PersistentGraphState, StateInvariantError
from mode_p_vnext.runtime.cache import NodeCacheKey
from mode_p_vnext.runtime.session import RunSession, RunSessionError
from mode_p_vnext.runtime.transaction import NodeTransaction


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


KNOWLEDGE_A = _digest("a")
KNOWLEDGE_B = _digest("b")
CAPABILITY_A = _digest("c")
CAPABILITY_B = _digest("d")


def _graph() -> StateGraph:
    return StateGraph(
        (
            NodeSpec("I0", "3.0", {"source": ArtifactKind.NORMALIZED_SOURCE}, ("raw_source",)),
            NodeSpec(
                "E0",
                "3.0",
                {"direction": ArtifactKind.EPISODE_DIRECTION_DRAFT},
                ("source",),
                uses_knowledge_snapshot=True,
            ),
            NodeSpec(
                "B1",
                "3.0",
                {"execution": ArtifactKind.SCENE_INTENT_DRAFT},
                ("direction",),
                uses_capability_profile=True,
            ),
            NodeSpec(
                "STORYBOARD",
                "3.0",
                {"storyboard_delivery": ArtifactKind.SCENE_INTENT_DRAFT},
                ("execution", "storyboard_adapter"),
            ),
            NodeSpec(
                "VIDEO",
                "3.0",
                {"video_delivery": ArtifactKind.SCENE_INTENT_DRAFT},
                ("execution", "video_adapter"),
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


def test_persistent_state_graph_records_only_canonical_refs_and_full_context(tmp_path: Path) -> None:
    session = RunSession.create(tmp_path / "runs", run_id="run-1", graph=_graph(), write_scope="episode-1:scene-1")
    state = _complete(session)
    direction = state.accepted["E0"]
    assert direction.stage_signature == _graph().node("E0").stage_signature
    assert direction.input_artifacts["source"].artifact_id == state.outputs["source"].artifact_id
    assert direction.input_digests["source"] == state.outputs["source"].artifact_digest
    assert direction.knowledge_snapshot_digest == KNOWLEDGE_A
    assert state.accepted["B1"].capability_profile_digest == CAPABILITY_A
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
            PersistentGraphState.empty("run-type"),
            node_id="I0",
            outputs={"source": wrong},
            input_digests={"raw_source": _digest("4")},
            knowledge_snapshot_digest=None,
            capability_profile_digest=None,
            commit_id="commit-type",
        )
    state = PersistentGraphState.empty("run-type").to_dict()
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
        knowledge_snapshot_digest=None,
        capability_profile_digest=None,
    )
    session.cache.put(key, first)
    with pytest.raises(StateInvariantError, match="already names different"):
        session.cache.put(key, competing)
    assert session.cache.get(key) == first


def test_v30_runtime_does_not_reintroduce_legacy_state_authorities() -> None:
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
    crash_boundary_state = PersistentGraphState.empty("run-11")
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
            },
        )
        NodeTransaction.promote(ambiguous.run_dir, pending)
    with pytest.raises(RunSessionError, match="multiple committed children"):
        RunSession.open(ambiguous.run_dir, graph=_graph()).state()
    with pytest.raises(RunSessionError, match="multiple committed children"):
        RunSession.open(ambiguous.run_dir, graph=_graph()).recover_pending(owner="recovery")
