"""Owner approval port — the explicit human gate for visual acceptance.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.4 / §14 A7 /
v2.1 ADR-018.

The approval record is bound to the exact media evidence digest.  A local
controller cannot prove the operator's real identity, so this port remains a
human-machine boundary: the construction agent must never call it on behalf
of the user.  A10 implements the concrete gate; A7 freezes the port boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from mode_p_vnext.domain.artifact import DomainValidationError


@dataclass(frozen=True)
class OwnerApprovalRecord:
    """An explicit owner approval bound to one media evidence digest."""

    approval_id: str
    approved_at: str
    media_evidence_digest: str
    approver: str

    def __post_init__(self) -> None:
        for field_name in ("approval_id", "approved_at", "media_evidence_digest", "approver"):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name):
                raise DomainValidationError(f"{field_name} must be non-empty")
        if len(self.media_evidence_digest) != 64:
            raise DomainValidationError("media_evidence_digest must be a sha256")
        if self.approver != "OWNER":
            raise DomainValidationError("approver must be the explicit OWNER marker")


@runtime_checkable
class ApprovalPort(Protocol):
    """Request an explicit owner approval for media evidence."""

    def request_approval(self, evidence_digest: str) -> OwnerApprovalRecord:
        """Return an approval record only after the human explicitly approves."""
        ...
