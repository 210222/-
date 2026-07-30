"""Evidence and independent DP revision schemas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .artifact import DomainValidationError, SourceRef, freeze_mapping


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = (
    "FrameEvidence",
    "MediaRunRecord",
    "OutcomeAttribution",
    "RevisionRequest",
    "VisualVerificationResult",
)


def _texts(value: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    values = tuple(value)
    if not values or any(not isinstance(item, str) or not item.strip() for item in values):
        raise DomainValidationError(f"{field_name} must contain non-empty text")
    return values


@dataclass(frozen=True)
class RevisionRequest:
    request_id: str
    vec_artifact_id: str
    observed_issue: str
    requested_change: str
    evidence_refs: tuple[SourceRef, ...]

    def __post_init__(self) -> None:
        if any(not getattr(self, field_name).strip() for field_name in ("request_id", "vec_artifact_id", "observed_issue", "requested_change")):
            raise DomainValidationError("RevisionRequest text fields must be non-empty")
        refs = tuple(self.evidence_refs)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError("evidence_refs must contain SourceRef values")
        object.__setattr__(self, "evidence_refs", refs)


@dataclass(frozen=True)
class MediaRunRecord:
    run_id: str
    provider: str
    request_digest: str
    output_refs: tuple[SourceRef, ...]

    def __post_init__(self) -> None:
        if any(not getattr(self, field_name).strip() for field_name in ("run_id", "provider", "request_digest")):
            raise DomainValidationError("MediaRunRecord text fields must be non-empty")
        refs = tuple(self.output_refs)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError("output_refs must contain SourceRef values")
        object.__setattr__(self, "output_refs", refs)


@dataclass(frozen=True)
class FrameEvidence:
    media_run_id: str
    frame_index: int
    observations: tuple[str, ...]
    attributes: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.media_run_id.strip() or isinstance(self.frame_index, bool) or self.frame_index < 0:
            raise DomainValidationError("FrameEvidence requires a run id and non-negative frame index")
        object.__setattr__(self, "observations", _texts(self.observations, "observations"))
        object.__setattr__(self, "attributes", freeze_mapping(self.attributes, "attributes"))


@dataclass(frozen=True)
class OutcomeAttribution:
    result_id: str
    cause: str
    confidence: str
    supporting_evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.result_id.strip() or not self.cause.strip() or self.confidence not in {"high", "medium", "low"}:
            raise DomainValidationError("OutcomeAttribution requires id, cause, and bounded confidence")
        object.__setattr__(self, "supporting_evidence", _texts(self.supporting_evidence, "supporting_evidence"))


@dataclass(frozen=True)
class VisualVerificationResult:
    verification_id: str
    vec_artifact_id: str
    passed: bool
    frame_evidence: tuple[FrameEvidence, ...]
    attributions: tuple[OutcomeAttribution, ...]

    def __post_init__(self) -> None:
        if not self.verification_id.strip() or not self.vec_artifact_id.strip():
            raise DomainValidationError("verification_id and vec_artifact_id must be non-empty")
        frames = tuple(self.frame_evidence)
        attributions = tuple(self.attributions)
        if not frames or not all(isinstance(item, FrameEvidence) for item in frames):
            raise DomainValidationError("frame_evidence must contain FrameEvidence values")
        if not all(isinstance(item, OutcomeAttribution) for item in attributions):
            raise DomainValidationError("attributions must contain OutcomeAttribution values")
        object.__setattr__(self, "frame_evidence", frames)
        object.__setattr__(self, "attributions", attributions)
