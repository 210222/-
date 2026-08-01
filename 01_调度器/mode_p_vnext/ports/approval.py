"""Owner approval port — the explicit human gate for visual acceptance.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.4 / §14 A7 /
v2.1 ADR-018.

The approval record is the A1-frozen canonical
``domain.evidence.OwnerApprovalRecord`` bound to the exact visual
verification artifact (re-exported here).  A local controller cannot prove
the operator's real identity, so this port remains a human-machine boundary:
the construction agent must never call it on behalf of the user.  A10
implements the concrete gate; A7 freezes the port boundary.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mode_p_vnext.domain.evidence import (
    OwnerApprovalDecision,
    OwnerApprovalRecord,
)

__all__ = ["OwnerApprovalDecision", "OwnerApprovalRecord"]


@runtime_checkable
class ApprovalPort(Protocol):
    """Request an explicit owner approval for a visual verification."""

    def request_approval(self, verification_id: str) -> OwnerApprovalRecord:
        """Return an approval record only after the human explicitly approves."""
        ...
