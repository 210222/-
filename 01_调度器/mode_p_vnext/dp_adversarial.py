"""Deterministic adversarial DP checks for textual visibility evidence.

This is a safety screen for the DP role, not a visual-model evaluator and not
a replacement Director. It converts observable text-contract violations into
bounded questions attached to the affected review object. A clean result means
only ``TEXT_VALIDATED``; actual storyboard/video inspection remains external.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from mode_p_vnext.dp_response_contract import DPIssue, DPResponse
from mode_p_vnext.dp_view_compiler import validate_dp_view


class DPAdversarialViolation(ValueError):
    """The DP review input is not a valid least-privilege review projection."""


def _normalise(value: str) -> str:
    return " ".join(value.lower().split())


def _mentioned(term: str, text: str) -> bool:
    return bool(term.strip()) and _normalise(term) in _normalise(text)


@dataclass(frozen=True)
class VisibilityReviewCase:
    """Textual representation of one Shot/Beat visibility contract for DP."""

    case_id: str
    segment_id: str
    shot_id: str
    positive_visual_text: str
    visible_whitelist: tuple[str, ...] = field(default_factory=tuple)
    positive_closure: tuple[str, ...] = field(default_factory=tuple)
    narrative_only: tuple[str, ...] = field(default_factory=tuple)
    audio_only: tuple[str, ...] = field(default_factory=tuple)
    occluded_only: tuple[str, ...] = field(default_factory=tuple)
    future_only: tuple[str, ...] = field(default_factory=tuple)
    undeclared_reflection_terms: tuple[str, ...] = field(default_factory=tuple)
    rear_surface_only: tuple[str, ...] = field(default_factory=tuple)
    human_qa_only: tuple[str, ...] = field(default_factory=tuple)
    leakage_risks: tuple[str, ...] = field(default_factory=tuple)
    forward_payload_field_ids: tuple[str, ...] = field(default_factory=tuple)
    allowed_forward_field_ids: tuple[str, ...] = field(default_factory=tuple)
    human_qa_only_field_ids: tuple[str, ...] = field(default_factory=tuple)
    beat_id: str = ""
    panel: int = 0
    fidelity_class: str = "LOCKED"

    def __post_init__(self) -> None:
        if not self.case_id or not self.segment_id or not self.shot_id:
            raise ValueError("visibility review case requires case, segment and shot IDs")


@dataclass(frozen=True)
class DPAdversarialReview:
    response: DPResponse
    validation_level: str = "TEXT_VALIDATED"


def _issue(
    case: VisibilityReviewCase,
    ordinal: int,
    code: str,
    evidence: str,
    correction_domain: str = "visibility_contract",
) -> DPIssue:
    return DPIssue(
        issue_id=f"DP-{case.case_id}-{ordinal:02d}",
        issue_code=code,
        question=(
            f"Can the Director resolve {code} for the current visible state "
            "while preserving the approved facts and local topology?"
        ),
        observed_evidence=evidence,
        required_correction_domain=correction_domain,
        bound_to_segment=case.segment_id,
        bound_to_shot=case.shot_id,
        bound_to_beat=case.beat_id,
        bound_to_panel=case.panel,
        fidelity_class=case.fidelity_class,
    )


def inspect_visibility_case(case: VisibilityReviewCase) -> list[DPIssue]:
    """Return local, non-directive issues for textual leakage/closure risks."""
    issues: list[DPIssue] = []
    positive = case.positive_visual_text
    checks = (
        ("VISIBLE_SURFACE_LEAK", case.narrative_only, "narrative-only detail appears in positive visual text"),
        ("AUDIO_ONLY_VISUAL_LEAK", case.audio_only, "audio-only detail appears in positive visual text"),
        ("OCCLUDED_STATE_LEAK", case.occluded_only, "occluded detail appears in positive visual text"),
        ("VISIBILITY_STATE_TIME_VIOLATION", case.future_only, "future-state detail appears too early"),
        ("REFLECTION_PATH_LEAK", case.undeclared_reflection_terms, "undeclared reflection/glass detail appears"),
        ("UNDECLARED_UI_OR_REAR_SURFACE_LEAK", case.rear_surface_only, "rear/hidden-surface detail appears"),
        ("HUMAN_QA_ONLY_LEAK", case.human_qa_only, "human-QA-only detail appears in forward text"),
    )
    for code, terms, description in checks:
        for term in terms:
            if _mentioned(term, positive):
                issues.append(_issue(case, len(issues) + 1, code, f"{description}: {term}"))
    if case.leakage_risks and not case.positive_closure:
        issues.append(_issue(
            case,
            len(issues) + 1,
            "MISSING_POSITIVE_CLOSURE",
            "leakage risk is declared without an observable positive closure",
        ))
    if case.forward_payload_field_ids and case.allowed_forward_field_ids:
        forbidden_ids = sorted(set(case.forward_payload_field_ids) - set(case.allowed_forward_field_ids))
        for field_id in forbidden_ids:
            issues.append(_issue(
                case,
                len(issues) + 1,
                "FORWARD_FIELD_ROUTE_LEAK",
                f"non-whitelisted field ID reached the forward payload: {field_id}",
                "payload_routing",
            ))
    for field_id in sorted(set(case.forward_payload_field_ids) & set(case.human_qa_only_field_ids)):
        issues.append(_issue(
            case,
            len(issues) + 1,
            "HUMAN_QA_ONLY_FIELD_LEAK",
            f"human-QA-only field ID reached the forward payload: {field_id}",
            "payload_routing",
        ))
    return issues


def review_dp_adversarial(
    dp_view: Mapping[str, object],
    cases: Sequence[VisibilityReviewCase],
    *,
    response_id: str,
    context_id: str = "",
    manifest_sha256: str = "",
) -> DPAdversarialReview:
    """Run deterministic textual DP safety checks and return a bounded response."""
    violations = validate_dp_view(dp_view)
    if violations:
        raise DPAdversarialViolation("invalid DP view: " + "; ".join(violations))
    issues: list[DPIssue] = []
    for case in cases:
        issues.extend(inspect_visibility_case(case))
    response = DPResponse(
        response_id=response_id,
        verdict="DIRECTED_QUESTION" if issues else "READY",
        issues=issues,
        context_id=context_id,
        manifest_sha256=manifest_sha256,
    )
    return DPAdversarialReview(response=response)
