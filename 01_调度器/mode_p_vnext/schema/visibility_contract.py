"""MODE:P vNext — Visibility Contract Schema (V2.1).

Defines what is visible, occluded, narrative-only, audio-only, and forbidden
for a shot. Prevents invisible narrative information and wrong surfaces from
leaking into visual output.

Spec references: LOOP §6, §7.10; Audit P0-06.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List


NEGATIVE_ROUTES: FrozenSet[str] = frozenset({
    "inline",              # 内联在正向提示词中
    "separate_channel",    # 平台的独立负向通道
    "human_qa_only",       # 只供人类QA审核，不进入模型提示词
    "token_leakage_risk",  # 有token泄漏风险，需特殊处理
})


@dataclass
class VisibilityContract:
    """What the camera can and cannot see in the current shot.

    All list fields default to empty — the Director fills them explicitly.
    An empty ``visible_whitelist`` is a design smell (implicit "everything
    is visible" has caused production failures).
    """

    visible_whitelist: List[str] = field(default_factory=list)
    occluded_state: List[str] = field(default_factory=list)
    narrative_only: List[str] = field(default_factory=list)
    audio_only: List[str] = field(default_factory=list)
    positive_closure: List[str] = field(default_factory=list)
    forbidden_qa: List[str] = field(default_factory=list)
    leakage_risks: List[str] = field(default_factory=list)
    negative_route: str = "separate_channel"

    def __post_init__(self) -> None:
        if self.negative_route not in NEGATIVE_ROUTES:
            raise ValueError(
                f"Invalid negative_route '{self.negative_route}'. "
                f"Must be one of: {sorted(NEGATIVE_ROUTES)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "visible_whitelist": list(self.visible_whitelist),
            "occluded_state": list(self.occluded_state),
            "narrative_only": list(self.narrative_only),
            "audio_only": list(self.audio_only),
            "positive_closure": list(self.positive_closure),
            "forbidden_qa": list(self.forbidden_qa),
            "negative_route": self.negative_route,
        }
        if self.leakage_risks:
            d["leakage_risks"] = list(self.leakage_risks)
        return d


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_visibility_contract(contract: VisibilityContract) -> List[str]:
    """Return structural violations in the visibility contract.

    Checks:
    - visible_whitelist must not be empty
    - No item in both visible_whitelist and occluded_state
    - No item in both visible_whitelist and narrative_only
    - No item in both visible_whitelist and audio_only
    """
    violations: List[str] = []

    v_set = set(contract.visible_whitelist)
    o_set = set(contract.occluded_state)
    n_set = set(contract.narrative_only)
    a_set = set(contract.audio_only)

    if not v_set:
        violations.append(
            "visible_whitelist is empty — implicit 'everything visible' "
            "is a known production risk"
        )

    overlap_vo = v_set & o_set
    if overlap_vo:
        violations.append(
            f"Items in both visible_whitelist and occluded_state: {sorted(overlap_vo)}"
        )

    overlap_vn = v_set & n_set
    if overlap_vn:
        violations.append(
            f"Items in both visible_whitelist and narrative_only: "
            f"{sorted(overlap_vn)} — narrative_only content must not leak into "
            f"visual output"
        )

    overlap_va = v_set & a_set
    if overlap_va:
        violations.append(
            f"Items in both visible_whitelist and audio_only: "
            f"{sorted(overlap_va)} — audio-only content must not be drawn"
        )

    return violations
