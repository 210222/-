"""Explicit human approval boundary, frozen for A10 and inactive in A7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from mode_p_vnext.domain.artifact import DomainValidationError, SourceRef
from mode_p_vnext.domain.evidence import OwnerApprovalDecision


@dataclass(frozen=True)
class ApprovalDecisionDraft:
    """Human decision input without a provider/user-owned canonical ID."""

    decision: OwnerApprovalDecision
    approved_by: str
    evidence_ref: SourceRef

    def __post_init__(self) -> None:
        if not isinstance(self.decision, OwnerApprovalDecision):
            raise DomainValidationError("decision must be an OwnerApprovalDecision")
        if not isinstance(self.approved_by, str) or not self.approved_by.strip():
            raise DomainValidationError("approved_by must be non-empty")
        if not isinstance(self.evidence_ref, SourceRef):
            raise DomainValidationError("evidence_ref must be a SourceRef")


@runtime_checkable
class ApprovalPort(Protocol):
    def request_approval(self, verification_id: str) -> ApprovalDecisionDraft:
        """A10 only: return the owner's explicit decision Draft."""
        ...


__all__ = ["ApprovalDecisionDraft", "ApprovalPort", "OwnerApprovalDecision"]
