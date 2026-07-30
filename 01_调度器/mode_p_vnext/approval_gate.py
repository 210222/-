"""MODE:P vNext — User Storyboard Approval Gate (V6.4).

Saves approved/clarification/revise states, asset bindings, user corrections,
and final impact confirmation. Payload generation is gated behind approval.

Spec references: LOOP §9 Step 10-13.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ApprovalGate:
    episode_id: str
    status: str = "pending"   # pending | approved | clarification_requested | revision_requested
    user_note: str = ""
    asset_bindings: List[str] = field(default_factory=list)
    corrections: List[str] = field(default_factory=list)
    impact_confirmed: bool = False

    @property
    def can_generate_payload(self) -> bool:
        return self.status == "approved"

    def approve(self, user_note: str = "",
                asset_bindings: List[str] | None = None) -> None:
        self.status = "approved"
        self.user_note = user_note
        if asset_bindings:
            self.asset_bindings = list(asset_bindings)

    def request_clarification(self, question: str) -> None:
        self.status = "clarification_requested"
        self.user_note = question

    def request_revision(self, revision_note: str) -> None:
        self.status = "revision_requested"
        self.corrections.append(revision_note)
        self.user_note = revision_note
