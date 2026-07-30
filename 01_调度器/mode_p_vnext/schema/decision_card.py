"""MODE:P vNext — Atomic Claim / Decision Card Schema (V3.2).

Splits knowledge claims into individually auditable cards with source quality,
render evidence, cross-scene repetition, user approval, applicability
conditions, and counter-examples.

Spec references: LOOP §5.4-§5.8; Omission P1-10.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List


SOURCE_QUALITY_LEVELS: FrozenSet[str] = frozenset({
    "golden_evidence",       # backed by Golden Set paired data
    "render_evidence",       # backed by external render observation
    "cross_project",         # observed across multiple episodes
    "user_opinion",          # user-stated but not yet render-verified
    "textbook",              # from film theory, not project-verified
    "legacy_pipeline",       # inherited from old MODE:P pipeline
})


@dataclass
class DecisionCard:
    """One atomic claim or design decision with evidence tracking.

    Each card answers a single director question. Cards are the atomic
    unit of knowledge selection — the retriever picks cards, not capsules.
    """

    card_id: str
    claim: str
    source_quality: str
    render_evidence: List[str] = field(default_factory=list)
    cross_scene_repeat: int = 1
    user_approved: bool = False
    user_approval_note: str = ""
    applicability_conditions: List[str] = field(default_factory=list)
    counter_examples: List[str] = field(default_factory=list)
    source_file: str = ""
    source_hash: str = ""

    def __post_init__(self) -> None:
        if self.source_quality not in SOURCE_QUALITY_LEVELS:
            raise ValueError(
                f"Invalid source_quality '{self.source_quality}'. "
                f"Must be one of: {sorted(SOURCE_QUALITY_LEVELS)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "card_id": self.card_id,
            "claim": self.claim,
            "source_quality": self.source_quality,
            "cross_scene_repeat": self.cross_scene_repeat,
            "user_approved": self.user_approved,
        }
        if self.render_evidence:
            d["render_evidence"] = list(self.render_evidence)
        if self.applicability_conditions:
            d["applicability_conditions"] = list(self.applicability_conditions)
        if self.counter_examples:
            d["counter_examples"] = list(self.counter_examples)
        if self.user_approval_note:
            d["user_approval_note"] = self.user_approval_note
        if self.source_file:
            d["source_file"] = self.source_file
        if self.source_hash:
            d["source_hash"] = self.source_hash
        return d


def validate_decision_card(card: DecisionCard) -> List[str]:
    """Return warnings for a decision card."""
    warnings: List[str] = []

    if card.source_quality in ("user_opinion", "textbook", "legacy_pipeline"):
        if not card.counter_examples:
            warnings.append(
                f"Card '{card.card_id}': source_quality='{card.source_quality}' "
                f"but no counter_examples provided — lower-quality sources "
                f"should document known limitations"
            )

    if card.source_quality == "golden_evidence" and not card.render_evidence:
        warnings.append(
            f"Card '{card.card_id}': claims golden_evidence but has no "
            f"render_evidence entries"
        )

    return warnings
