"""MODE:P vNext — Fidelity Contract (V4.3).

Defines LOCKED/ELASTIC/OPTIMIZABLE/FORBIDDEN levels for facts, constraints,
and design elements. Critical facts and user-approved items must never be
downgraded.

Spec references: LOOP §7.11.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

FIDELITY_LEVELS: FrozenSet[str] = frozenset({
    "LOCKED", "ELASTIC", "OPTIMIZABLE", "FORBIDDEN",
})

# Rank for downgrade detection (higher = stricter)
_FIDELITY_RANK = {"LOCKED": 4, "FORBIDDEN": 3, "ELASTIC": 2, "OPTIMIZABLE": 1}


@dataclass
class FidelityBinding:
    item_type: str       # fact_id, user_constraint, composition, timing, etc.
    item_id: str
    level: str
    justification: str = ""


@dataclass
class FidelityContract:
    """Tracks fidelity levels for all bound items in a segment/shot."""

    contract_id: str
    bindings: List[FidelityBinding] = field(default_factory=list)
    _index: Dict[str, FidelityBinding] = field(default_factory=dict)

    def bind(self, item_type: str, item_id: str, level: str,
             justification: str = "") -> None:
        if level not in FIDELITY_LEVELS:
            raise ValueError(f"Invalid fidelity level '{level}'")
        key = f"{item_type}:{item_id}"
        if key in self._index:
            existing = self._index[key]
            if _FIDELITY_RANK[level] < _FIDELITY_RANK[existing.level]:
                raise ValueError(
                    f"Cannot downgrade '{key}' from {existing.level} to {level}"
                )
        binding = FidelityBinding(item_type, item_id, level, justification)
        self.bindings.append(binding)
        self._index[key] = binding

    def get_level(self, item_id: str) -> Optional[str]:
        for key, b in self._index.items():
            if key.endswith(f":{item_id}"):
                return b.level
        return None


def check_user_approved_downgrades(contract: FidelityContract) -> List[str]:
    """Verify no LOCKED user_constraint items are downgraded."""
    violations: List[str] = []
    for b in contract.bindings:
        if b.item_type == "user_constraint" and b.level != "LOCKED":
            violations.append(
                f"User constraint '{b.item_id}' is {b.level} — "
                f"user-approved items must be LOCKED"
            )
    return violations
