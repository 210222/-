"""CPL-1 verifies real source snapshots and explicit knowledge adjudication."""

from __future__ import annotations

from pathlib import Path

import pytest

from mode_p_vnext.director_vnext1.capsules import (
    RetrievalContext,
    attach_conflict_decision,
    retrieve_k1,
)
from mode_p_vnext.director_vnext1.contracts import (
    CapsuleFieldProvenance,
    ConflictDecisionRecord,
    DirectorContractError,
    DirectorProblem,
    DirectorProblemSet,
    KnowledgeCapsule,
)
from mode_p_vnext.director_vnext1.knowledge_catalog import (
    ACTUAL_SOURCES,
    load_actual_catalog,
    verify_actual_source_snapshot,
)


HASH = "a" * 64


def _capsule(
    capsule_id: str,
    *,
    conflicts=(),
    support_level: str = "direct",
    allowed_uses=("scene_intent",),
) -> KnowledgeCapsule:
    return KnowledgeCapsule(
        capsule_id=capsule_id,
        source_locator="03_知识库/test.md:1-2",
        source_sha256=HASH,
        primary_type="dramatic",
        tags=("power",),
        secondary_tags=("attention",),
        decision_level="scene",
        director_problem="How does power change?",
        dramatic_function="make the power change legible",
        triggers=("power",),
        contraindications=("flashback",),
        required_context=(),
        execution_rules=("preserve the approved relation",),
        expected_effect="readable change",
        tradeoffs=("less decorative coverage",),
        alternatives=("hold the relation",),
        confidence_level="high",
        review_status="approved",
        allowed_uses=allowed_uses,
        conflicting_capsule_ids=conflicts,
        field_provenance=(
            CapsuleFieldProvenance(
                "dramatic_function",
                "03_知识库/test.md:1",
                support_level,
            ),
        ),
    )


def _problems() -> DirectorProblemSet:
    return DirectorProblemSet(
        scene_id="UNKNOWN-SCENE",
        problems=(
            DirectorProblem(
                problem_id="P-POWER",
                domain="power",
                question="What changes in the relationship?",
                tags=("power",),
            ),
        ),
    )


def test_actual_catalog_has_field_provenance_and_runtime_does_not_load_books(
    monkeypatch,
):
    project_root = Path(__file__).resolve().parents[3]
    snapshot = verify_actual_source_snapshot(project_root)
    assert snapshot["runtime_full_sources_loaded"] is False
    assert len(snapshot["sources"]) == len(ACTUAL_SOURCES)
    assert len(snapshot["snapshot_sha256"]) == 64

    def _forbid_runtime_source_read(*_args, **_kwargs):
        raise AssertionError("runtime attempted to load a full knowledge source")

    monkeypatch.setattr(Path, "read_bytes", _forbid_runtime_source_read)
    catalog = load_actual_catalog()
    assert catalog
    for capsule in catalog:
        assert capsule.source_authorization == "project_internal_approved"
        assert capsule.field_provenance
        assert all(
            item.support_level in {"direct", "inferred", "unknown"}
            for item in capsule.field_provenance
        )


def test_unknown_field_forces_advisory_or_review_only_use():
    with pytest.raises(
        DirectorContractError,
        match="unknown source fields downgrade",
    ):
        _capsule(
            "K-UNKNOWN-BAD",
            support_level="unknown",
            allowed_uses=("camera_motion",),
        )
    downgraded = _capsule(
        "K-UNKNOWN-REVIEW",
        support_level="unknown",
        allowed_uses=("review_only",),
    )
    assert downgraded.allowed_uses == ("review_only",)


def test_retrieval_exposes_conflict_and_director_records_the_adjudication():
    first = _capsule("K-CONFLICT-A", conflicts=("K-CONFLICT-B",))
    second = _capsule("K-CONFLICT-B", conflicts=("K-CONFLICT-A",))
    packet = retrieve_k1(
        "K1-CONFLICT",
        _problems(),
        (second, first),
        RetrievalContext(scene_tags=("power",), approved_context=()),
    )
    assert [item.capsule_id for item in packet.primary_capsules] == [
        "K-CONFLICT-A"
    ]
    assert packet.conflict_capsule.capsule_id == "K-CONFLICT-B"
    assert packet.conflict_decision is None

    adjudication = ConflictDecisionRecord(
        record_id="CDR-1",
        scene_id="UNKNOWN-SCENE",
        stage="K1",
        conflict_capsule_ids=("K-CONFLICT-A", "K-CONFLICT-B"),
        selected_capsule_ids=("K-CONFLICT-A",),
        excluded_capsule_ids=("K-CONFLICT-B",),
        priority_source="episode_or_scene_intent",
        director_id="director-vnext1",
        selection_reason="The approved scene intent requires a visible power turn.",
        exclusion_reason="The alternative would flatten the approved relationship change.",
    )
    resolved = attach_conflict_decision(packet, adjudication)
    assert resolved.conflict_decision == adjudication
    assert resolved.fingerprint != packet.fingerprint


def test_conflict_record_must_account_for_all_candidates():
    with pytest.raises(DirectorContractError, match="account for every"):
        ConflictDecisionRecord(
            record_id="CDR-BAD",
            scene_id="UNKNOWN-SCENE",
            stage="K1",
            conflict_capsule_ids=("K-A", "K-B", "K-C"),
            selected_capsule_ids=("K-A",),
            excluded_capsule_ids=("K-B",),
            priority_source="knowledge_confidence",
            director_id="director-vnext1",
            selection_reason="one",
            exclusion_reason="two",
        )
