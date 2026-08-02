"""A9 v3.0 frozen holdout evaluation tests.

All candidates below contain synthetic hash references only.  They exercise
the non-production evaluator and explicitly do not stand in for media runs,
frame evidence, visual acceptance, or an owner approval.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib

import pytest

from mode_p_vnext.evaluation.prompt_lab import (
    ARCHITECTURE_DOCUMENT_PATH,
    ARCHITECTURE_SHA256,
    EXPECTED_TEXT_SHADOW_NODES,
    TEXT_CLAIM_CEILING,
    TEXTUAL_QUALITY_RUBRIC_SHA256,
    EvaluationError,
    EvaluationMetrics,
    FrozenEvaluator,
    FrozenEvaluatorError,
    GoldenCase,
    HoldoutCase,
    HoldoutCandidate,
    RuntimeInvariantSnapshot,
    TraceLineage,
    assert_no_text_only_media_claim,
    candidate_from_text_shadow_result,
    evaluate_holdout_candidates,
    evaluator_runtime_write_sites,
    freeze_evaluator,
    pareto_dominates,
)
from mode_p_vnext.domain.artifact import canonical_sha256


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _record(body: dict[str, object]) -> dict[str, object]:
    return {**body, "record_sha256": canonical_sha256(body)}


def _golden(case_id: str = "golden-calibration-a") -> GoldenCase:
    return GoldenCase(case_id=case_id, normalized_source_sha256=_sha(f"source:{case_id}"))


def _holdout(case_id: str = "holdout-unknown-script-a") -> HoldoutCase:
    return HoldoutCase(case_id=case_id, normalized_source_sha256=_sha(f"source:{case_id}"))


def _evaluator() -> FrozenEvaluator:
    return freeze_evaluator(
        evaluator_id="a9-evaluator",
        golden_cases=(_golden(),),
        holdout_cases=(_holdout(),),
    )


def _candidate(
    candidate_id: str,
    *,
    case_id: str = "holdout-unknown-script-a",
    source_digest: str | None = None,
    quality: int = 800,
    cost: int = 10,
    latency: int = 100,
    complexity: int = 3,
    authority_path: str = ARCHITECTURE_DOCUMENT_PATH,
    authority_sha256: str = ARCHITECTURE_SHA256,
    accepted_nodes: tuple[str, ...] = EXPECTED_TEXT_SHADOW_NODES,
    claim_ceiling: str = TEXT_CLAIM_CEILING,
    external_media_started: bool = False,
    v4_write: bool = False,
    production_switch_authorized: bool = False,
    visual_acceptance_claimed: bool = False,
    owner_preview_approval_claimed: bool = False,
) -> HoldoutCandidate:
    return HoldoutCandidate(
        candidate_id=candidate_id,
        holdout_case_id=case_id,
        lineage=TraceLineage(
            normalized_source_sha256=source_digest or _sha(f"source:{case_id}"),
            fact_registry_sha256=_sha(f"fact:{candidate_id}"),
            draft_sha256=_sha(f"draft:{candidate_id}"),
            decision_sha256=_sha(f"decision:{candidate_id}"),
            vec_sha256=_sha(f"vec:{candidate_id}"),
            projection_sha256=_sha(f"projection:{candidate_id}"),
            output_sha256=_sha(f"output:{candidate_id}"),
            run_record_sha256=_sha(f"run:{candidate_id}"),
        ),
        invariants=RuntimeInvariantSnapshot(
            authority_path=authority_path,
            authority_sha256=authority_sha256,
            accepted_nodes=accepted_nodes,
            claim_ceiling=claim_ceiling,
            external_media_started=external_media_started,
            v4_write=v4_write,
            production_switch_authorized=production_switch_authorized,
            visual_acceptance_claimed=visual_acceptance_claimed,
            owner_preview_approval_claimed=owner_preview_approval_claimed,
        ),
        metrics=EvaluationMetrics.bind(
            quality_scope="TEXTUAL_CONTRACT",
            quality_score_milli=quality,
            quality_rubric_sha256=TEXTUAL_QUALITY_RUBRIC_SHA256,
            quality_evidence_sha256=_sha(f"quality:{candidate_id}"),
            cost_units=cost,
            latency_ms=latency,
            complexity_units=complexity,
        ),
    )


def test_frozen_evaluator_seals_golden_identities_without_script_text() -> None:
    evaluator = _evaluator()

    policy = evaluator.policy.to_dict()
    assert evaluator.policy.frozen is True
    assert evaluator.policy.runtime_mutation_policy == "FORBID"
    assert policy["architecture_path"] == ARCHITECTURE_DOCUMENT_PATH
    assert policy["architecture_sha256"] == ARCHITECTURE_SHA256
    assert policy["quality_rubric_sha256"] == TEXTUAL_QUALITY_RUBRIC_SHA256
    assert policy["golden_cases"] == [_golden().to_dict()]
    assert policy["holdout_cases"] == [_holdout().to_dict()]
    assert "script" not in policy
    assert "prompt" not in policy
    assert "vec" not in policy


def test_golden_case_or_source_overlap_is_discarded_fail_closed() -> None:
    golden = _golden()
    evaluator = freeze_evaluator(
        evaluator_id="a9-evaluator",
        golden_cases=(golden,),
        holdout_cases=(_holdout(),),
    )

    by_case_id = _candidate("candidate-overlap-id", case_id=golden.case_id)
    by_source = _candidate(
        "candidate-overlap-source",
        source_digest=golden.normalized_source_sha256,
    )
    report = evaluate_holdout_candidates(evaluator, (by_case_id, by_source))

    assert report.status == "FAIL_CLOSED"
    decisions = {item.candidate_id: item for item in report.candidate_evaluations}
    assert decisions["candidate-overlap-id"].disposition == "DISCARD"
    assert decisions["candidate-overlap-id"].reasons == (
        "GOLDEN_CASE_ID_OVERLAP",
        "GOLDEN_SOURCE_DIGEST_OVERLAP",
    )
    assert decisions["candidate-overlap-source"].reasons == (
        "HOLDOUT_SOURCE_DIGEST_MISMATCH",
        "GOLDEN_SOURCE_DIGEST_OVERLAP",
    )


@pytest.mark.parametrize(
    "holdout",
    [
        lambda golden: HoldoutCase("golden-calibration-a", _sha("separate-source")),
        lambda golden: HoldoutCase("holdout-distinct", golden.normalized_source_sha256),
    ],
)
def test_freeze_rejects_any_golden_holdout_registry_overlap(holdout) -> None:  # type: ignore[no-untyped-def]
    golden = _golden()

    with pytest.raises(EvaluationError, match="Golden and holdout"):
        freeze_evaluator(
            evaluator_id="a9-evaluator",
            golden_cases=(golden,),
            holdout_cases=(holdout(golden),),
        )


def test_candidate_must_match_a_presealed_holdout_identity_and_source() -> None:
    evaluator = _evaluator()
    unregistered = _candidate("candidate-unregistered", case_id="holdout-not-sealed")
    wrong_source = _candidate("candidate-wrong-source", source_digest=_sha("other-holdout-source"))

    report = evaluate_holdout_candidates(evaluator, (unregistered, wrong_source))
    decisions = {item.candidate_id: item for item in report.candidate_evaluations}

    assert report.status == "FAIL_CLOSED"
    assert decisions["candidate-unregistered"].reasons == ("UNREGISTERED_HOLDOUT_CASE",)
    assert decisions["candidate-wrong-source"].reasons == ("HOLDOUT_SOURCE_DIGEST_MISMATCH",)


def test_candidate_keep_discard_uses_quality_cost_latency_complexity_pareto() -> None:
    evaluator = _evaluator()
    efficient = _candidate("candidate-efficient", quality=800, cost=10, latency=100, complexity=3)
    premium = _candidate("candidate-premium", quality=900, cost=20, latency=150, complexity=4)
    dominated = _candidate("candidate-dominated", quality=700, cost=20, latency=150, complexity=4)

    report = evaluate_holdout_candidates(evaluator, (dominated, premium, efficient))
    decisions = {item.candidate_id: item for item in report.candidate_evaluations}

    assert report.status == "TEXT_HOLDOUT_EVALUATED"
    assert report.kept_candidate_ids == ("candidate-efficient", "candidate-premium")
    assert decisions["candidate-efficient"].disposition == "KEEP"
    assert decisions["candidate-premium"].disposition == "KEEP"
    assert decisions["candidate-dominated"].disposition == "DISCARD"
    assert decisions["candidate-dominated"].pareto_dominated_by == ("candidate-efficient", "candidate-premium")
    assert pareto_dominates(efficient.metrics, dominated.metrics)
    assert not pareto_dominates(efficient.metrics, premium.metrics)


def test_candidate_adapter_binds_a8_terminal_result_to_digest_lineage() -> None:
    evaluator = _evaluator()
    template = _candidate("candidate-from-a8")
    a8_result = {
        "status": "TEXT_VALIDATED",
        "claim_ceiling": "TEXT_VALIDATED",
        "accepted_nodes": list(EXPECTED_TEXT_SHADOW_NODES),
        "run_record_sha256": template.lineage.run_record_sha256,
        "external_media_started": False,
        "v4_write": False,
        "production_switch_authorized": False,
    }
    run_record = _record(
        {
            "schema_name": "mode_p_vnext_a8_text_shadow_run",
            "schema_version": "3.0",
            "run_id": "run-a8-holdout",
            "write_scope": "shadow",
            "episode_id": "holdout-episode",
            "scene_id": "holdout-scene",
            "source_id": "holdout-source",
            "source_digest": template.lineage.normalized_source_sha256,
            "program_version": "a8-v3.0",
            "provider_id": "native-provider",
            "dp_reviewer_id": "fresh-dp",
            "claim_ceiling": "TEXT_VALIDATED",
            "graph_digest": _sha("a8-state-graph"),
            "external_media_started": False,
            "v4_write": False,
            "created_at_utc": "2026-08-02T00:00:00+00:00",
        }
    )
    lineage = replace(template.lineage, run_record_sha256=run_record["record_sha256"])
    a8_result["run_record_sha256"] = lineage.run_record_sha256
    result_record = _record(
        {
            "schema_name": "mode_p_vnext_a8_text_shadow_result",
            "schema_version": "3.0",
            "run_id": "run-a8-holdout",
            "result": dict(a8_result),
        }
    )
    lineage = replace(lineage, output_sha256=result_record["record_sha256"])
    a8_result["result_record_sha256"] = lineage.output_sha256

    candidate = candidate_from_text_shadow_result(
        evaluator=evaluator,
        candidate_id=template.candidate_id,
        holdout_case_id=template.holdout_case_id,
        text_shadow_result=a8_result,
        text_shadow_run_record=run_record,
        text_shadow_result_record=result_record,
        lineage=lineage,
        metrics=template.metrics,
    )
    report = evaluate_holdout_candidates(evaluator, (candidate,))

    assert report.status == "TEXT_HOLDOUT_EVALUATED"
    assert report.kept_candidate_ids == ("candidate-from-a8",)
    with pytest.raises(EvaluationError, match="not bound to the candidate output lineage"):
        candidate_from_text_shadow_result(
            evaluator=evaluator,
            candidate_id=template.candidate_id,
            holdout_case_id=template.holdout_case_id,
            text_shadow_result={**a8_result, "result_record_sha256": _sha("tampered-result")},
            text_shadow_run_record=run_record,
            text_shadow_result_record=result_record,
            lineage=lineage,
            metrics=template.metrics,
        )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("external_media_started", True, "EXTERNAL_MEDIA_STARTED"),
        ("v4_write", True, "V4_WRITE_DETECTED"),
        ("production_switch_authorized", True, "PRODUCTION_SWITCH_DETECTED"),
        ("visual_acceptance_claimed", True, "TEXT_ONLY_MEDIA_CLAIM"),
        ("owner_preview_approval_claimed", True, "OWNER_PREVIEW_APPROVAL_CLAIM"),
    ],
)
def test_text_only_evaluation_rejects_media_or_production_claims(
    field: str,
    value: bool,
    reason: str,
) -> None:
    evaluator = _evaluator()
    candidate = _candidate("candidate-boundary", **{field: value})

    report = evaluate_holdout_candidates(evaluator, (candidate,))

    assert report.status == "FAIL_CLOSED"
    assert report.claim_ceiling == "TEXT_VALIDATED"
    assert report.external_media_started is False
    assert report.media_visual_acceptance is False
    assert report.owner_preview_approval is False
    assert report.production_switch_authorized is False
    assert report.candidate_evaluations[0].reasons == (reason,)
    assert_no_text_only_media_claim(report)


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"authority_path": "other/authority.md"}, "AUTHORITY_PATH_MISMATCH"),
        ({"authority_sha256": _sha("wrong-authority")}, "AUTHORITY_SHA256_MISMATCH"),
        ({"accepted_nodes": ("I0", "Projection")}, "TEXT_SHADOW_STATE_GRAPH_MISMATCH"),
        ({"claim_ceiling": "VISUAL_VALIDATED"}, "TEXT_CLAIM_CEILING_VIOLATION"),
    ],
)
def test_architecture_invariant_regression_is_discarded(kwargs: dict[str, object], reason: str) -> None:
    evaluator = _evaluator()
    report = evaluate_holdout_candidates(evaluator, (_candidate("candidate-drift", **kwargs),))

    assert report.status == "FAIL_CLOSED"
    assert report.candidate_evaluations[0].reasons == (reason,)


def test_ranking_measurement_is_hash_bound_and_uses_the_frozen_quality_rubric() -> None:
    evaluator = _evaluator()
    candidate = _candidate("candidate-metric")

    with pytest.raises(EvaluationError, match="not bound"):
        replace(candidate.metrics, measurement_evidence_sha256="0" * 64)

    wrong_rubric = EvaluationMetrics.bind(
        quality_scope="TEXTUAL_CONTRACT",
        quality_score_milli=candidate.metrics.quality_score_milli,
        quality_rubric_sha256=_sha("other-textual-rubric"),
        quality_evidence_sha256=candidate.metrics.quality_evidence_sha256,
        cost_units=candidate.metrics.cost_units,
        latency_ms=candidate.metrics.latency_ms,
        complexity_units=candidate.metrics.complexity_units,
    )
    report = evaluate_holdout_candidates(evaluator, (replace(candidate, metrics=wrong_rubric),))

    assert report.status == "FAIL_CLOSED"
    assert report.candidate_evaluations[0].reasons == ("TEXTUAL_QUALITY_RUBRIC_MISMATCH",)


def test_evaluator_integrity_detects_implementation_drift_before_ranking() -> None:
    evaluator = _evaluator()
    drifted_policy = replace(evaluator.policy, implementation_sha256="0" * 64)
    drifted = FrozenEvaluator(policy=drifted_policy)

    with pytest.raises(FrozenEvaluatorError, match="implementation_sha256_drift"):
        evaluate_holdout_candidates(drifted, (_candidate("candidate-safe"),))


def test_evaluator_has_no_runtime_write_sites_and_does_not_change_its_fingerprint() -> None:
    evaluator = _evaluator()
    before = evaluator.fingerprint

    report = evaluate_holdout_candidates(evaluator, (_candidate("candidate-safe"),))

    assert evaluator_runtime_write_sites() == ()
    assert evaluator.fingerprint == before
    assert report.evaluator_integrity.runtime_write_sites == ()
    assert report.digest == report.digest


def test_ambiguous_duplicate_candidate_identity_fails_before_comparison() -> None:
    evaluator = _evaluator()
    first = _candidate("same-candidate")
    second = _candidate("same-candidate", quality=900)

    with pytest.raises(EvaluationError, match="duplicate candidate IDs"):
        evaluate_holdout_candidates(evaluator, (first, second))
