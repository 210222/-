"""A7 verification pipeline logic — canonical types come from A1's domain.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9 / §14 A7.

All evidence types (ReviewPacket, DeterministicGateResult, MediaRunRecord,
FrameEvidencePlan, FrameEvidence, MediaEvidence, OutcomeAttribution,
VisualVerificationResult, OwnerApprovalRecord, RevisionRequest) are the
A1-frozen canonical types in ``mode_p_vnext.domain.evidence``.  This module
only re-exports them and provides the pipeline *logic*:

- the strict status ladder TEXT_VALIDATED -> VISUAL_EVIDENCED ->
  OWNER_APPROVED (text can never claim visual acceptance);
- builders for the DP ReviewPacket, MediaEvidence, and
  VisualVerificationResult;
- layer parsing for media-failure attribution.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    SourceRef,
    canonical_sha256,
)
from mode_p_vnext.domain.evidence import (
    DPReviewVerdict,
    DeterministicGateResult,
    FrameEvidence,
    FrameEvidencePlan,
    IndependentDPReviewResult,
    MediaEvidence,
    MediaRunRecord,
    OutcomeAttribution,
    OwnerApprovalDecision,
    OwnerApprovalRecord,
    ReviewPacket,
    RevisionFailureType,
    RevisionRequest,
    VisualVerificationResult,
)
from mode_p_vnext.domain.facts import FactRegistry
from mode_p_vnext.domain.vec import VisualExecutionContract
from mode_p_vnext.services.projection_compiler import (
    StoryboardProjection,
    VideoProjection,
)

if TYPE_CHECKING:
    from mode_p_vnext.services.deterministic_gates import Gate0Result

TEXT_VALIDATED = "TEXT_VALIDATED"
VISUAL_EVIDENCED = "VISUAL_EVIDENCED"
OWNER_APPROVED = "OWNER_APPROVED"


class VerificationStatus(str, enum.Enum):
    TEXT_VALIDATED = TEXT_VALIDATED
    VISUAL_EVIDENCED = VISUAL_EVIDENCED
    OWNER_APPROVED = OWNER_APPROVED


class AttributionLayer(str, enum.Enum):
    ASSEMBLY = "ASSEMBLY"
    GATE0 = "GATE0"
    PROJECTION = "PROJECTION"
    DP = "DP"
    MEDIA_RENDER = "MEDIA_RENDER"
    MEDIA_VERIFY = "MEDIA_VERIFY"
    DIRECTOR = "DIRECTOR"


# Re-export the canonical domain types so pipeline consumers import them from
# one place without redefining them.
__all__ = [
    "DPReviewVerdict",
    "DeterministicGateResult",
    "FrameEvidence",
    "FrameEvidencePlan",
    "IndependentDPReviewResult",
    "MediaEvidence",
    "MediaRunRecord",
    "OutcomeAttribution",
    "OwnerApprovalDecision",
    "OwnerApprovalRecord",
    "ReviewPacket",
    "RevisionFailureType",
    "RevisionRequest",
    "VisualVerificationResult",
]


# ---------------------------------------------------------------------------
# Attribution helpers (layer is encoded in OutcomeAttribution.cause)
# ---------------------------------------------------------------------------


def _attribution(
    *,
    layer: AttributionLayer,
    reason: str,
    supporting_evidence: tuple[str, ...],
    confidence: str = "high",
) -> OutcomeAttribution:
    return OutcomeAttribution(
        result_id=f"attr:{layer.value.lower()}:{canonical_sha256((reason, supporting_evidence))[:16]}",
        cause=f"{layer.value}|{reason}",
        confidence=confidence,
        supporting_evidence=supporting_evidence,
    )


def gate0_attribution(*, scene_id: str, reason: str) -> OutcomeAttribution:
    return _attribution(
        layer=AttributionLayer.GATE0,
        reason=reason,
        supporting_evidence=(scene_id,),
    )


def media_render_attribution(
    *, scene_id: str, renderer_version: str, reason: str
) -> OutcomeAttribution:
    return _attribution(
        layer=AttributionLayer.MEDIA_RENDER,
        reason=reason,
        supporting_evidence=(scene_id, renderer_version),
    )


def media_verify_attribution(
    *, scene_id: str, verifier_version: str, reason: str
) -> OutcomeAttribution:
    return _attribution(
        layer=AttributionLayer.MEDIA_VERIFY,
        reason=reason,
        supporting_evidence=(scene_id, verifier_version),
    )


def layer_of(attribution: OutcomeAttribution) -> AttributionLayer | None:
    """Parse the attribution layer from the canonical cause prefix."""
    head = attribution.cause.split("|", 1)[0].strip().upper()
    for layer in AttributionLayer:
        if layer.value == head:
            return layer
    return None


# ---------------------------------------------------------------------------
# Status ladder — text can never claim visual acceptance (§9.4)
# ---------------------------------------------------------------------------


def ladder_status(
    *,
    text_ceiling: str,
    verification: VisualVerificationResult | None,
    approval: OwnerApprovalRecord | None,
) -> VerificationStatus:
    """Compute the verification status from the strict ladder.

    - ``text_ceiling`` must be TEXT_VALIDATED; any visual claim from a text
      pipeline is rejected.
    - Without a passed visual verification: TEXT_VALIDATED.
    - With a passed visual verification: VISUAL_EVIDENCED.
    - With an explicit owner approval bound to that verification:
      OWNER_APPROVED.
    """
    if text_ceiling != TEXT_VALIDATED:
        raise ValueError(
            f"text pipeline claim ceiling must be {TEXT_VALIDATED}, got {text_ceiling}"
        )
    if verification is None:
        return VerificationStatus.TEXT_VALIDATED
    if not verification.passed:
        raise ValueError("a failed visual verification cannot claim VISUAL_EVIDENCED")
    if approval is None:
        return VerificationStatus.VISUAL_EVIDENCED
    if approval.decision != OwnerApprovalDecision.APPROVED:
        raise ValueError("owner approval must be an explicit APPROVED decision")
    if approval.visual_verification_artifact_id != verification.verification_id:
        raise ValueError(
            "owner approval must bind the exact visual verification artifact"
        )
    return VerificationStatus.OWNER_APPROVED


def build_media_evidence(
    *,
    plan: FrameEvidencePlan,
    media_run: MediaRunRecord,
    frames: tuple[FrameEvidence, ...],
    evidence_id: str,
    frame_evidence_plan_artifact_id: str,
    media_run_artifact_id: str,
) -> MediaEvidence:
    """Assemble canonical MediaEvidence; domain enforces non-empty run-bound frames."""
    return MediaEvidence(
        evidence_id=evidence_id,
        frame_evidence_plan_artifact_id=frame_evidence_plan_artifact_id,
        media_run_artifact_id=media_run_artifact_id,
        media_run_id=media_run.run_id,
        frame_evidence=frames,
    )


def build_visual_verification(
    *,
    verification_id: str,
    vec: VisualExecutionContract,
    media_run: MediaRunRecord,
    frames: tuple[FrameEvidence, ...],
    attributions: tuple[OutcomeAttribution, ...] = (),
) -> VisualVerificationResult:
    """Build the canonical visual verification; domain requires frame evidence."""
    return VisualVerificationResult(
        verification_id=verification_id,
        vec_artifact_id=vec.contract_id,
        media_run_id=media_run.run_id,
        passed=True,
        frame_evidence=frames,
        attributions=attributions,
    )


# ---------------------------------------------------------------------------
# DP ReviewPacket — scoped, approved-content-only view (§9.3)
# ---------------------------------------------------------------------------


def build_dp_review_packet(
    *,
    scene_id: str,
    facts: FactRegistry,
    vec: VisualExecutionContract,
    storyboard: StoryboardProjection,
    video: VideoProjection,
    gate0: "Gate0Result",
    capability_summary: str,
    episode_direction_artifact_id: str,
    scene_intent_artifact_id: str,
) -> ReviewPacket:
    """Assemble the canonical scoped DP packet from approved content only.

    Facts are approved when they are exactly the VEC's bound source facts;
    any fact outside the VEC set is rejected as an unapproved leak.  The
    packet carries no Director prompt, private reasoning, repair
    conversation, or historical pass label (the canonical type has no such
    fields by construction).  E0/S1 artifact ids are explicit inputs — A8's
    real shadow supplies them; callers must not fabricate them here.
    """
    approved_fact_ids = set(vec.source_fact_ids)
    supplied_fact_ids = {fact.fact_id for fact in facts.facts}
    if not supplied_fact_ids.issubset(approved_fact_ids):
        leaked = sorted(supplied_fact_ids - approved_fact_ids)
        raise ValueError("unapproved fact leak: " + ",".join(leaked))
    if not approved_fact_ids.issubset(supplied_fact_ids):
        missing = sorted(approved_fact_ids - supplied_fact_ids)
        raise ValueError("approved facts missing from packet: " + ",".join(missing))

    packet_id = f"review_packet:{canonical_sha256((scene_id, vec.contract_id))[:32]}"
    return ReviewPacket(
        packet_id=packet_id,
        fact_refs=tuple(sorted(approved_fact_ids)),
        episode_direction_artifact_id=episode_direction_artifact_id,
        scene_intent_artifact_id=scene_intent_artifact_id,
        vec_artifact_id=vec.contract_id,
        projection_artifact_ids=(
            canonical_sha256(storyboard.manifest),
            canonical_sha256(video.manifest),
        ),
        gate_result_refs=(gate0.result_id,),
        capability_profile_digest=canonical_sha256(capability_summary),
    )
