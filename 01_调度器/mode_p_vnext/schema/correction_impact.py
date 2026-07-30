"""MODE:P vNext — Correction Impact Schema (V4.4).

Classifies how a user correction affects the design and whether prior
approvals are invalidated.

Spec references: LOOP §9 Step 11-12; Omission P0-11.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, List

IMPACT_LEVELS: FrozenSet[str] = frozenset({
    "clarification_only",         # only explains existing frame
    "render_constraint_only",     # changes execution, not visible composition
    "storyboard_visible_change",  # approval invalidated, re-generate storyboard
    "topology_or_fact_change",    # back to Master + DP
})


@dataclass
class CorrectionImpact:
    """Records the impact of a user correction on the design chain."""

    correction_id: str
    impact_level: str
    affected_items: List[str] = field(default_factory=list)
    invalidates_approval: bool = False
    director_proposed_level: str = ""
    dp_confirmed_level: str = ""
    user_confirmed: bool = False

    def __post_init__(self) -> None:
        if self.impact_level not in IMPACT_LEVELS:
            raise ValueError(
                f"Invalid impact_level '{self.impact_level}'. "
                f"Must be one of: {sorted(IMPACT_LEVELS)}"
            )


def validate_correction_impact(c: CorrectionImpact) -> List[str]:
    """Validate a correction impact record."""
    violations: List[str] = []

    if c.impact_level == "topology_or_fact_change" and not c.invalidates_approval:
        violations.append(
            f"Correction '{c.correction_id}': topology_or_fact_change "
            f"MUST invalidate approval"
        )

    if c.impact_level in ("storyboard_visible_change", "topology_or_fact_change"):
        if not c.invalidates_approval:
            violations.append(
                f"Correction '{c.correction_id}': {c.impact_level} "
                f"must invalidate prior storyboard approval"
            )

    return violations
