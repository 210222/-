"""DDO-1 knowledge capsules are bounded, provenance-bearing, and staged."""

from __future__ import annotations

import pytest

from mode_p_vnext.director_vnext1.capsules import RetrievalContext, retrieve_k1, retrieve_k2
from mode_p_vnext.director_vnext1.contracts import (
    CapsuleApplicabilityRecord,
    DirectorContractError,
    DirectorProblem,
    DirectorProblemSet,
    KnowledgeCapsule,
)


HASH = "a" * 64


def _capsule(capsule_id: str, primary_type: str, *, confidence: str = "high", conflicts=()):
    return KnowledgeCapsule(
        capsule_id=capsule_id,
        source_locator="book/chapter-1",
        source_sha256=HASH,
        primary_type=primary_type,
        tags=("power", "departure"),
        director_problem="How does the departure change attention?",
        dramatic_function="show a power shift",
        triggers=("power",),
        contraindications=("flashback",),
        required_context=(),
        execution_rules=("preserve the approved relationship",),
        expected_effect="the shift is readable",
        tradeoffs=("less coverage",),
        alternatives=("hold the relation",),
        confidence_level=confidence,
        review_status="approved",
        allowed_uses=("attention",),
        conflicting_capsule_ids=conflicts,
    )


def _problems() -> DirectorProblemSet:
    return DirectorProblemSet(
        scene_id="SCENE-1",
        problems=(
            DirectorProblem("P-1", "power", "What changes in the relation?", ("power",)),
            DirectorProblem("P-2", "blocking", "Who is left in control?", ("departure",)),
        ),
    )


def test_capsule_requires_source_provenance_trigger_and_approved_use():
    with pytest.raises(DirectorContractError):
        _capsule("K-bad", "dramatic", confidence="impossible")
    with pytest.raises(DirectorContractError):
        KnowledgeCapsule(
            capsule_id="K-no-source", source_locator="", source_sha256=HASH,
            primary_type="dramatic", tags=(), director_problem="p", dramatic_function="f",
            triggers=("power",), contraindications=(), required_context=(), execution_rules=("r",),
            expected_effect="e", tradeoffs=(), alternatives=(), confidence_level="high",
            review_status="approved", allowed_uses=("attention",),
        )


def test_k1_never_returns_camera_or_edit_answer_and_records_application():
    packet = retrieve_k1(
        "K1-1",
        _problems(),
        (_capsule("K-dramatic", "dramatic"), _capsule("K-camera", "camera_shot")),
        RetrievalContext(scene_tags=("power",), approved_context=()),
    )
    assert packet.stage == "K1"
    assert [capsule.capsule_id for capsule in packet.primary_capsules] == ["K-dramatic"]
    assert packet.application_records[0].stage == "K1"
    assert packet.application_records[0].influenced_fields == ("director_problem",)
    assert not packet.blocking_commit_id


def test_k2_requires_blocking_commit_and_allows_execution_knowledge_only_afterward():
    with pytest.raises(DirectorContractError):
        retrieve_k2("K2-0", _problems(), (_capsule("K-camera", "camera_shot"),), RetrievalContext(("power",), ()), blocking_commit_id="")
    packet = retrieve_k2(
        "K2-1", _problems(), (_capsule("K-camera", "camera_shot"),),
        RetrievalContext(("power",), ()), blocking_commit_id="BLOCK-1",
    )
    assert packet.stage == "K2"
    assert packet.blocking_commit_id == "BLOCK-1"
    assert packet.application_records[0].influenced_fields == ("execution_constraint",)


def test_conflict_and_anti_pattern_are_exposed_but_not_silently_decided():
    catalog = (
        _capsule("K-1", "dramatic"),
        _capsule("K-2", "dramatic"),
        _capsule("K-3", "dramatic"),
        _capsule("K-4", "dramatic", conflicts=("K-1",)),
        _capsule("K-anti", "anti_pattern"),
    )
    packet = retrieve_k1("K1-2", _problems(), catalog, RetrievalContext(("power",), ()))
    assert [item.capsule_id for item in packet.primary_capsules] == ["K-1", "K-2", "K-3"]
    assert packet.conflict_capsule is not None and packet.conflict_capsule.capsule_id == "K-4"
    assert packet.anti_pattern_capsule is not None and packet.anti_pattern_capsule.capsule_id == "K-anti"


def test_no_match_does_not_fall_back_to_a_generic_shot_template():
    packet = retrieve_k1(
        "K1-none", _problems(), (_capsule("K-other", "dramatic"),),
        RetrievalContext(scene_tags=("flashback",), approved_context=()),
    )
    assert packet.no_match is True
    assert packet.primary_capsules == ()
    assert packet.application_records == ()


def test_low_confidence_cannot_independently_drive_high_impact_selection():
    packet = retrieve_k1(
        "K1-risk", _problems(), (_capsule("K-low", "dramatic", confidence="low"),),
        RetrievalContext(scene_tags=("power",), approved_context=(), impact_level="high"),
    )
    assert packet.no_match is True
