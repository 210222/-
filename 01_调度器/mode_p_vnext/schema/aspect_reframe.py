"""MODE:P vNext — Aspect Reframe Contract (V2.5).

Defines how a landscape (16:9) storyboard may be reframed into a portrait
(9:16) video without breaking protected spatial relationships.

Spec references: LOOP §7.8; Omission P1-08.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class AspectReframeContract:
    """Rules for reframing from source to target aspect ratio.

    Protected relationships (e.g. character left/right, gaze direction)
    MUST survive reframing. Mirroring is forbidden unless explicitly
    listed in ``allowed_reframe``.
    """

    source_aspect: str                       # e.g. "16:9"
    target_aspect: str                       # e.g. "9:16"
    protected_relationships: List[str] = field(default_factory=list)
    allowed_reframe: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=lambda: [
        "水平镜像",
        "180°旋转",
        "人物左右互换",
        "视线方向反转",
        "屏幕运动方向反转",
    ])

    @property
    def is_identity(self) -> bool:
        return self.source_aspect == self.target_aspect


def validate_reframe(contract: AspectReframeContract) -> List[str]:
    """Validate the reframe contract — returns violations."""
    violations: List[str] = []

    if contract.is_identity:
        return violations

    if not contract.protected_relationships:
        violations.append(
            "protected_relationships is empty — spatial invariants "
            "must be declared when reframing aspect ratios"
        )

    # Mirroring is banned unless explicitly allowed
    mirror_terms = {"镜像", "mirror", "反转"}
    has_mirror_allowed = any(
        any(term in a.lower() for term in mirror_terms)
        for a in contract.allowed_reframe
    )
    if not has_mirror_allowed:
        violations.append(
            "镜像/反转未在 allowed_reframe 中声明 — "
            "横版到竖版重构中默认禁止镜像以防止银幕方向反转"
        )

    return violations
