"""Independent DP review and real-media evidence schemas."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import ClassVar, Mapping

from .artifact import (
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    freeze_mapping,
    require_sha256,
)


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = (
    "DPReviewVerdict",
    "DeterministicGateResult",
    "FrameEvidence",
    "FrameEvidencePlan",
    "IndependentDPReviewResult",
    "MediaEvidence",
    "MediaRunRecord",
    "OwnerApprovalDecision",
    "OwnerApprovalRecord",
    "OutcomeAttribution",
    "ReviewPacket",
    "RevisionFailureType",
    "RevisionRequest",
    "VisualVerificationResult",
)


class RevisionFailureType(str, enum.Enum):
    FACT_CONTRADICTION = "fact_contradiction"
    CONTINUITY = "continuity"
    VISUAL_LOGIC = "visual_logic"
    PROJECTION_DIVERGENCE = "projection_divergence"
    CAPABILITY = "capability"
    MEDIA_OUTCOME = "media_outcome"


class DPReviewVerdict(str, enum.Enum):
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"


class OwnerApprovalDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")


def _text_tuple(
    value: tuple[str, ...], field_name: str, *, require_items: bool
) -> tuple[str, ...]:
    values = tuple(value)
    if (require_items and not values) or any(
        not isinstance(item, str) or not item.strip() for item in values
    ):
        raise DomainValidationError(
            f"{field_name} must contain only non-empty text"
        )
    if len(values) != len(set(values)):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    return values


@dataclass(frozen=True)
class ReviewPacket:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.REVIEW_PACKET

    packet_id: str
    fact_refs: tuple[str, ...]
    episode_direction_artifact_id: str
    scene_intent_artifact_id: str
    vec_artifact_id: str
    projection_artifact_ids: tuple[str, ...]
    gate_result_refs: tuple[str, ...]
    capability_profile_digest: str

    def __post_init__(self) -> None:
        for field_name in (
            "packet_id",
            "episode_direction_artifact_id",
            "scene_intent_artifact_id",
            "vec_artifact_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        for field_name in (
            "fact_refs",
            "projection_artifact_ids",
            "gate_result_refs",
        ):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(
                    getattr(self, field_name),
                    field_name,
                    require_items=True,
                ),
            )
        require_sha256(
            self.capability_profile_digest, "capability_profile_digest"
        )


@dataclass(frozen=True)
class DeterministicGateResult:
    """Persisted output of the zero-model deterministic Gate 0 node."""

    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.GATE0_RESULT

    result_id: str
    target_artifact_ids: tuple[str, ...]
    check_ids: tuple[str, ...]
    failed_check_ids: tuple[str, ...]
    evidence_refs: tuple[SourceRef, ...]
    passed: bool

    def __post_init__(self) -> None:
        _require_text(self.result_id, "result_id")
        targets = _text_tuple(
            self.target_artifact_ids,
            "target_artifact_ids",
            require_items=True,
        )
        checks = _text_tuple(self.check_ids, "check_ids", require_items=True)
        failed = _text_tuple(
            self.failed_check_ids,
            "failed_check_ids",
            require_items=False,
        )
        if not set(failed).issubset(checks):
            raise DomainValidationError(
                "failed_check_ids must be a subset of check_ids"
            )
        if not isinstance(self.passed, bool):
            raise DomainValidationError("passed must be boolean")
        if self.passed == bool(failed):
            raise DomainValidationError(
                "passed must be true exactly when failed_check_ids is empty"
            )
        refs = tuple(self.evidence_refs)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError(
                "evidence_refs must contain SourceRef values"
            )
        object.__setattr__(self, "target_artifact_ids", targets)
        object.__setattr__(self, "check_ids", checks)
        object.__setattr__(self, "failed_check_ids", failed)
        object.__setattr__(self, "evidence_refs", refs)


@dataclass(frozen=True)
class IndependentDPReviewResult:
    """Auditable result of an independent DP session.

    Revision content remains in separate RevisionRequest artifacts.
    """

    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.DP_REVIEW_RESULT

    result_id: str
    review_packet_artifact_id: str
    verdict: DPReviewVerdict
    finding_codes: tuple[str, ...]
    revision_request_artifact_ids: tuple[str, ...]
    independent_context_digest: str

    def __post_init__(self) -> None:
        _require_text(self.result_id, "result_id")
        _require_text(
            self.review_packet_artifact_id,
            "review_packet_artifact_id",
        )
        if not isinstance(self.verdict, DPReviewVerdict):
            raise DomainValidationError("verdict must be a DPReviewVerdict")
        findings = _text_tuple(
            self.finding_codes,
            "finding_codes",
            require_items=self.verdict is DPReviewVerdict.REVISION_REQUIRED,
        )
        revisions = _text_tuple(
            self.revision_request_artifact_ids,
            "revision_request_artifact_ids",
            require_items=self.verdict is DPReviewVerdict.REVISION_REQUIRED,
        )
        if self.verdict is DPReviewVerdict.APPROVED and (findings or revisions):
            raise DomainValidationError(
                "approved DP results cannot carry findings or revision requests"
            )
        require_sha256(
            self.independent_context_digest,
            "independent_context_digest",
        )
        object.__setattr__(self, "finding_codes", findings)
        object.__setattr__(
            self,
            "revision_request_artifact_ids",
            revisions,
        )


@dataclass(frozen=True)
class RevisionRequest:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.REVISION_REQUEST

    """DP may request a scoped revision but never rewrite the VEC."""

    request_id: str
    target_artifact_id: str
    failure_type: RevisionFailureType
    fact_refs: tuple[str, ...]
    field_paths: tuple[str, ...]
    observed_issue: str
    requested_change: str
    evidence_refs: tuple[SourceRef, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "target_artifact_id",
            "observed_issue",
            "requested_change",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.failure_type, RevisionFailureType):
            raise DomainValidationError(
                "failure_type must be a RevisionFailureType"
            )
        for field_name in ("fact_refs", "field_paths"):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(
                    getattr(self, field_name),
                    field_name,
                    require_items=True,
                ),
            )
        refs = tuple(self.evidence_refs)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError(
                "evidence_refs must contain SourceRef values"
            )
        object.__setattr__(self, "evidence_refs", refs)


@dataclass(frozen=True)
class MediaRunRecord:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.MEDIA_RUN_RECORD

    run_id: str
    provider: str
    request_digest: str
    output_refs: tuple[SourceRef, ...]

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_text(self.provider, "provider")
        require_sha256(self.request_digest, "request_digest")
        refs = tuple(self.output_refs)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError(
                "output_refs must contain SourceRef values"
            )
        object.__setattr__(self, "output_refs", refs)


@dataclass(frozen=True)
class FrameEvidencePlan:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.FRAME_EVIDENCE_PLAN

    plan_id: str
    vec_artifact_id: str
    checks: tuple[str, ...]
    frame_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        _require_text(self.plan_id, "plan_id")
        _require_text(self.vec_artifact_id, "vec_artifact_id")
        object.__setattr__(
            self,
            "checks",
            _text_tuple(self.checks, "checks", require_items=True),
        )
        indices = tuple(self.frame_indices)
        if (
            not indices
            or any(
                isinstance(item, bool)
                or not isinstance(item, int)
                or item < 0
                for item in indices
            )
            or len(indices) != len(set(indices))
        ):
            raise DomainValidationError(
                "frame_indices must contain unique non-negative integers"
            )
        object.__setattr__(self, "frame_indices", indices)


@dataclass(frozen=True)
class FrameEvidence:
    media_run_id: str
    frame_index: int
    observations: tuple[str, ...]
    attributes: Mapping[str, str]

    def __post_init__(self) -> None:
        _require_text(self.media_run_id, "media_run_id")
        if (
            isinstance(self.frame_index, bool)
            or not isinstance(self.frame_index, int)
            or self.frame_index < 0
        ):
            raise DomainValidationError(
                "frame_index must be a non-negative integer"
            )
        object.__setattr__(
            self,
            "observations",
            _text_tuple(
                self.observations, "observations", require_items=True
            ),
        )
        attributes = freeze_mapping(self.attributes, "attributes")
        if not all(isinstance(value, str) for value in attributes.values()):
            raise DomainValidationError(
                "FrameEvidence attributes must contain text values"
            )
        object.__setattr__(self, "attributes", attributes)


@dataclass(frozen=True)
class MediaEvidence:
    """Canonical aggregate proving that frame evidence came from a media run."""

    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.MEDIA_EVIDENCE

    evidence_id: str
    frame_evidence_plan_artifact_id: str
    media_run_artifact_id: str
    media_run_id: str
    frame_evidence: tuple[FrameEvidence, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "evidence_id",
            "frame_evidence_plan_artifact_id",
            "media_run_artifact_id",
            "media_run_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        frames = tuple(self.frame_evidence)
        if not frames or not all(
            isinstance(item, FrameEvidence) for item in frames
        ):
            raise DomainValidationError(
                "frame_evidence must contain FrameEvidence values"
            )
        if any(
            frame.media_run_id != self.media_run_id
            for frame in frames
        ):
            raise DomainValidationError(
                "all FrameEvidence must belong to media_run_id"
            )
        object.__setattr__(self, "frame_evidence", frames)


@dataclass(frozen=True)
class OutcomeAttribution:
    result_id: str
    cause: str
    confidence: str
    supporting_evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.result_id, "result_id")
        _require_text(self.cause, "cause")
        if self.confidence not in {"high", "medium", "low"}:
            raise DomainValidationError(
                "confidence must be high, medium, or low"
            )
        object.__setattr__(
            self,
            "supporting_evidence",
            _text_tuple(
                self.supporting_evidence,
                "supporting_evidence",
                require_items=True,
            ),
        )


@dataclass(frozen=True)
class VisualVerificationResult:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = (
        ArtifactKind.VISUAL_VERIFICATION_RESULT
    )

    verification_id: str
    vec_artifact_id: str
    media_run_id: str
    passed: bool
    frame_evidence: tuple[FrameEvidence, ...]
    attributions: tuple[OutcomeAttribution, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "verification_id",
            "vec_artifact_id",
            "media_run_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.passed, bool):
            raise DomainValidationError("passed must be boolean")
        frames = tuple(self.frame_evidence)
        attributions = tuple(self.attributions)
        if not frames or not all(
            isinstance(item, FrameEvidence) for item in frames
        ):
            raise DomainValidationError(
                "frame_evidence must contain FrameEvidence values"
            )
        if not all(
            isinstance(item, OutcomeAttribution) for item in attributions
        ):
            raise DomainValidationError(
                "attributions must contain OutcomeAttribution values"
            )
        if any(frame.media_run_id != self.media_run_id for frame in frames):
            raise DomainValidationError(
                "all FrameEvidence must belong to the verified media run"
            )
        object.__setattr__(self, "frame_evidence", frames)
        object.__setattr__(self, "attributions", attributions)


@dataclass(frozen=True)
class OwnerApprovalRecord:
    """Explicit owner decision; it never authorizes a production switch."""

    ARTIFACT_KIND: ClassVar[ArtifactKind] = (
        ArtifactKind.OWNER_APPROVAL_RECORD
    )

    approval_id: str
    visual_verification_artifact_id: str
    decision: OwnerApprovalDecision
    approved_by: str
    evidence_ref: SourceRef

    def __post_init__(self) -> None:
        for field_name in (
            "approval_id",
            "visual_verification_artifact_id",
            "approved_by",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.decision, OwnerApprovalDecision):
            raise DomainValidationError(
                "decision must be an OwnerApprovalDecision"
            )
        if not isinstance(self.evidence_ref, SourceRef):
            raise DomainValidationError("evidence_ref must be a SourceRef")
