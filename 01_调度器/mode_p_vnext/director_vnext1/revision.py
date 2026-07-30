"""Bounded, attribution-led revision requests for Director vNext.1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from .contracts import DirectorContractError
from .editorial import EditorialIssue, EditorialReviewRecord


ATTRIBUTION_LAYERS = frozenset(
    {
        "fact", "episode_intent", "scene_intent", "blocking", "decision",
        "VEC_field", "reference", "adapter", "generation_variance",
    }
)
MAX_AUTOMATIC_REVISION_ATTEMPTS = 2


class RevisionLimitReached(DirectorContractError):
    """Raised instead of silently entering an unbounded automatic revision loop."""


@dataclass(frozen=True)
class OutcomeAttribution:
    attribution_id: str
    layer: str
    contract_refs: Tuple[str, ...]
    evidence_summary: str

    def __post_init__(self) -> None:
        if not self.attribution_id.strip() or not self.evidence_summary.strip():
            raise DirectorContractError("outcome attribution needs an ID and evidence summary")
        if self.layer not in ATTRIBUTION_LAYERS:
            raise DirectorContractError("outcome attribution layer is invalid")
        if not self.contract_refs:
            raise DirectorContractError("outcome attribution must identify contract refs")


@dataclass(frozen=True)
class RevisionRequest:
    request_id: str
    contract_fingerprint: str
    issue_ids: Tuple[str, ...]
    attribution: OutcomeAttribution
    affected_node_ids: Tuple[str, ...]
    frozen_node_ids: Tuple[str, ...]
    attempt_number: int
    requires_director_redecision: bool = True

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.contract_fingerprint.strip():
            raise DirectorContractError("revision request needs an ID and contract fingerprint")
        if not self.issue_ids or not self.affected_node_ids:
            raise DirectorContractError("revision request needs issues and a non-empty affected scope")
        if self.attempt_number < 1 or self.attempt_number > MAX_AUTOMATIC_REVISION_ATTEMPTS:
            raise RevisionLimitReached("automatic revision is limited to two attempts")
        if set(self.affected_node_ids) & set(self.frozen_node_ids):
            raise DirectorContractError("revision cannot rewrite a frozen, unaffected node")


def propose_revision(
    review: EditorialReviewRecord,
    issue_ids: Sequence[str],
    attribution: OutcomeAttribution,
    *,
    frozen_node_ids: Sequence[str] = (),
    prior_automatic_attempts: int = 0,
) -> RevisionRequest:
    """Return only a scoped request; it never mutates VEC or generates media."""

    if prior_automatic_attempts >= MAX_AUTOMATIC_REVISION_ATTEMPTS:
        raise RevisionLimitReached("two automatic revision attempts already exist for this scope")
    requested = tuple(issue_ids)
    issue_map = {issue.issue_id: issue for issue in review.issues}
    if not requested or any(issue_id not in issue_map for issue_id in requested):
        raise DirectorContractError("revision can only target observed editorial issues")
    affected = tuple(
        node_id
        for issue_id in requested
        for node_id in issue_map[issue_id].affected_node_ids
    )
    if len(affected) != len(set(affected)):
        affected = tuple(dict.fromkeys(affected))
    if not set(attribution.contract_refs).intersection(
        {ref for issue_id in requested for ref in issue_map[issue_id].contract_refs}
    ):
        raise DirectorContractError("attribution must cite an observed issue reference")
    return RevisionRequest(
        request_id=f"REV-{review.review_id}-{prior_automatic_attempts + 1}",
        contract_fingerprint=review.contract_fingerprint,
        issue_ids=requested,
        attribution=attribution,
        affected_node_ids=affected,
        frozen_node_ids=tuple(frozen_node_ids),
        attempt_number=prior_automatic_attempts + 1,
    )
