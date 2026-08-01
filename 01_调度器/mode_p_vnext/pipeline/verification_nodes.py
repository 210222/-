"""Verification pipeline nodes: DP packet, media runs, frame evidence, attribution.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.3–§9.4 / §14 A7.

The status ladder is strictly ordered:

    TEXT_VALIDATED  ->  VISUAL_EVIDENCED  ->  OWNER_APPROVED

- Text validation alone can only ever produce TEXT_VALIDATED.
- VISUAL_EVIDENCED requires a MediaRunRecord plus captured FrameEvidence.
- OWNER_APPROVED requires an explicit OwnerApprovalRecord bound to the exact
  media evidence digest.

Media failures always carry an OutcomeAttribution naming the failing layer
(ASSEMBLY / GATE0 / PROJECTION / DP / MEDIA_RENDER / MEDIA_VERIFY /
DIRECTOR), so a media failure can be attributed to a concrete layer.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    canonical_sha256,
)
from mode_p_vnext.domain.facts import FactRegistry
from mode_p_vnext.domain.vec import VisualExecutionContract
from mode_p_vnext.ports.approval import OwnerApprovalRecord
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


@dataclass(frozen=True)
class MediaRunRecord:
    """One real media render run (image/video), never a text substitute."""

    run_id: str
    scene_id: str
    renderer_version: str
    media_kind: str
    media_paths: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        for field_name in ("run_id", "scene_id", "renderer_version", "media_kind"):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name):
                raise DomainValidationError(f"{field_name} must be non-empty")
        if not isinstance(self.media_paths, tuple) or not self.media_paths:
            raise DomainValidationError("media_paths must be a non-empty tuple")
        if not isinstance(self.created_at, str) or not self.created_at:
            raise DomainValidationError("created_at must be non-empty")


@dataclass(frozen=True)
class FrameSpec:
    """One planned frame capture inside a FrameEvidencePlan."""

    frame_id: str
    tick: int
    state_id: str
    shot_id: str
    checks: tuple[str, ...] = ()


@dataclass(frozen=True)
class FrameEvidencePlan:
    """The planned frame-level evidence for a media run."""

    plan_id: str
    scene_id: str
    frames: tuple[FrameSpec, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.plan_id, str) or not self.plan_id:
            raise DomainValidationError("plan_id must be non-empty")
        if not isinstance(self.frames, tuple) or not self.frames:
            raise DomainValidationError("frames must be a non-empty tuple")


@dataclass(frozen=True)
class FrameEvidence:
    """Verified frame evidence bound to a media hash."""

    frame_id: str
    media_hash: str
    tick: int
    state_id: str
    shot_id: str
    checks: tuple[str, ...] = ()
    captured_at: str = ""


@dataclass(frozen=True)
class OutcomeAttribution:
    """Which layer failed and why — media failures must name a layer."""

    attribution_id: str
    layer: AttributionLayer
    failure_kind: str
    node_refs: tuple[str, ...]
    reason: str

    @classmethod
    def gate0_failure(cls, *, scene_id: str, reason: str) -> "OutcomeAttribution":
        return cls(
            attribution_id=f"attr:gate0:{_stable_suffix(scene_id, reason)}",
            layer=AttributionLayer.GATE0,
            failure_kind="deterministic_gate_rejection",
            node_refs=(),
            reason=reason,
        )

    @classmethod
    def media_render_failure(
        cls, *, scene_id: str, renderer_version: str, reason: str
    ) -> "OutcomeAttribution":
        return cls(
            attribution_id=f"attr:render:{_stable_suffix(scene_id, reason)}",
            layer=AttributionLayer.MEDIA_RENDER,
            failure_kind="media_render_failed",
            node_refs=(scene_id, renderer_version),
            reason=reason,
        )

    @classmethod
    def media_verify_failure(
        cls, *, scene_id: str, verifier_version: str, reason: str
    ) -> "OutcomeAttribution":
        return cls(
            attribution_id=f"attr:verify:{_stable_suffix(scene_id, reason)}",
            layer=AttributionLayer.MEDIA_VERIFY,
            failure_kind="media_verify_failed",
            node_refs=(scene_id, verifier_version),
            reason=reason,
        )


def _stable_suffix(*parts: str) -> str:
    return canonical_sha256(tuple(parts))[:16]


@dataclass(frozen=True)
class VisualVerificationResult:
    """The single verification outcome with a strict status ladder."""

    result_id: str
    scene_id: str
    status: VerificationStatus
    media_run: MediaRunRecord | None = None
    frame_evidence: tuple[FrameEvidence, ...] = ()
    attribution: OutcomeAttribution | None = None
    approval_id: str | None = None
    media_evidence_digest: str = ""
    failed: bool = False

    @classmethod
    def from_text_validation(
        cls,
        *,
        scene_id: str,
        status: VerificationStatus | str = VerificationStatus.TEXT_VALIDATED,
    ) -> "VisualVerificationResult":
        """Text validation can never claim visual acceptance."""
        resolved = VerificationStatus(status)
        if resolved != VerificationStatus.TEXT_VALIDATED:
            raise ValueError(
                "text validation may only claim TEXT_VALIDATED; "
                "visual acceptance requires media evidence"
            )
        return cls(
            result_id=f"text:{_stable_suffix(scene_id)}",
            scene_id=scene_id,
            status=resolved,
        )

    @classmethod
    def with_media_evidence(
        cls,
        *,
        scene_id: str,
        media_run: MediaRunRecord,
        frame_evidence: tuple[FrameEvidence, ...] = (),
    ) -> "VisualVerificationResult":
        """Real media run plus optional frame evidence => VISUAL_EVIDENCED."""
        if not isinstance(media_run, MediaRunRecord):
            raise ValueError("media_run must be a MediaRunRecord")
        if not isinstance(frame_evidence, tuple):
            raise ValueError("frame_evidence must be a tuple")
        evidence_digest = canonical_sha256(
            {"media_run": media_run, "frame_evidence": frame_evidence}
        )
        return cls(
            result_id=f"visual:{_stable_suffix(scene_id, evidence_digest)}",
            scene_id=scene_id,
            status=VerificationStatus.VISUAL_EVIDENCED,
            media_run=media_run,
            frame_evidence=frame_evidence,
            media_evidence_digest=evidence_digest,
        )

    @classmethod
    def with_owner_approval(
        cls,
        evidenced: "VisualVerificationResult",
        *,
        approval: OwnerApprovalRecord,
    ) -> "VisualVerificationResult":
        """Explicit owner approval bound to the exact evidence digest."""
        if evidenced.status != VerificationStatus.VISUAL_EVIDENCED:
            raise ValueError("owner approval requires VISUAL_EVIDENCED first")
        if approval.media_evidence_digest != evidenced.media_evidence_digest:
            raise ValueError(
                "owner approval digest must match the media evidence digest"
            )
        return cls(
            result_id=evidenced.result_id,
            scene_id=evidenced.scene_id,
            status=VerificationStatus.OWNER_APPROVED,
            media_run=evidenced.media_run,
            frame_evidence=evidenced.frame_evidence,
            attribution=evidenced.attribution,
            approval_id=approval.approval_id,
            media_evidence_digest=evidenced.media_evidence_digest,
            failed=evidenced.failed,
        )

    def with_failure(self, attribution: OutcomeAttribution) -> "VisualVerificationResult":
        return VisualVerificationResult(
            result_id=self.result_id,
            scene_id=self.scene_id,
            status=self.status,
            media_run=self.media_run,
            frame_evidence=self.frame_evidence,
            attribution=attribution,
            approval_id=self.approval_id,
            media_evidence_digest=self.media_evidence_digest,
            failed=True,
        )


# ---------------------------------------------------------------------------
# DP ReviewPacket — scoped, approved-content-only view (§9.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DPReviewPacket:
    """The only content a fresh DP session may read.

    Contains approved facts, VEC review view, both projections, and the Gate 0
    result.  It deliberately has no field for Director prompts, private
    reasoning, repair conversations, or historical pass labels.
    """

    scene_id: str
    gate0_passed: bool
    vec_digest: str
    fact_ids: tuple[str, ...]
    storyboard_source_node_ids: tuple[str, ...]
    video_source_node_ids: tuple[str, ...]
    capability_summary: str

    def __post_init__(self) -> None:
        if not isinstance(self.scene_id, str) or not self.scene_id:
            raise DomainValidationError("scene_id must be non-empty")
        if not isinstance(self.capability_summary, str) or not self.capability_summary:
            raise DomainValidationError("capability_summary must be non-empty")
        if not isinstance(self.fact_ids, tuple) or not self.fact_ids:
            raise DomainValidationError("fact_ids must be non-empty")


def build_dp_review_packet(
    *,
    scene_id: str,
    facts: FactRegistry,
    vec: VisualExecutionContract,
    storyboard: StoryboardProjection,
    video: VideoProjection,
    gate0: "Gate0Result",
    capability_summary: str,
) -> DPReviewPacket:
    """Assemble the scoped DP packet from approved content only.

    Facts are approved when they are exactly the VEC's bound source facts;
    any fact outside the VEC set is rejected as an unapproved leak.
    """
    approved_fact_ids = set(vec.source_fact_ids)
    supplied_fact_ids = {fact.fact_id for fact in facts.facts}
    if not supplied_fact_ids.issubset(approved_fact_ids):
        leaked = sorted(supplied_fact_ids - approved_fact_ids)
        raise ValueError(
            "unapproved fact leak: " + ",".join(leaked)
        )
    if not approved_fact_ids.issubset(supplied_fact_ids):
        missing = sorted(approved_fact_ids - supplied_fact_ids)
        raise ValueError("approved facts missing from packet: " + ",".join(missing))

    return DPReviewPacket(
        scene_id=scene_id,
        gate0_passed=gate0.passed,
        vec_digest=canonical_sha256(vec),
        fact_ids=tuple(sorted(approved_fact_ids)),
        storyboard_source_node_ids=tuple(
            node.source_id for node in storyboard.nodes
        ),
        video_source_node_ids=tuple(
            node.source_id for node in video.nodes
        ),
        capability_summary=capability_summary,
    )
