"""Minimal, deterministic retrieval filtering and budget accounting.

Legacy callers can continue to pass plain ``DecisionCard`` objects.  vNext
callers may attach a metadata index keyed by ``card_id``; hard constraints are
then applied before quality ranking.  An empty result is a valid no-match, not
a license to inject a generic camera or dialogue template.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from mode_p_vnext.schema.decision_card import DecisionCard


_QUALITY_RANK = {
    "golden_evidence": 5,
    "render_evidence": 4,
    "cross_project": 3,
    "user_opinion": 2,
    "textbook": 1,
    "legacy_pipeline": 0,
}


@dataclass(frozen=True)
class RuntimeFilterConstraints:
    """Explicit, non-text-inferred constraints for metadata-based retrieval."""

    project_id: str = ""
    model_id: str = ""
    mode: str = ""
    aspect_ratio: str = ""
    reference_mode: str = ""
    as_of: str = ""
    required_tags: Tuple[str, ...] = ()
    blocked_card_ids: Tuple[str, ...] = ()

    @property
    def date_value(self) -> date:
        return date.fromisoformat(self.as_of) if self.as_of else date.today()


def _as_values(value: object) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    try:
        return tuple(str(item) for item in value)  # type: ignore[arg-type]
    except TypeError:
        return (str(value),)


def _matches(values: Iterable[str], actual: str) -> bool:
    values_tuple = tuple(values)
    return not values_tuple or "*" in values_tuple or (bool(actual) and actual in values_tuple)


def _metadata_reason(
    card: DecisionCard,
    metadata: Mapping[str, object],
    constraints: RuntimeFilterConstraints,
) -> str | None:
    if card.card_id in constraints.blocked_card_ids:
        return "blocked_card"
    status = str(metadata.get("status", "active"))
    if status != "active" or metadata.get("human_reviewed", True) is not True:
        return "not_human_reviewed_active"
    if not _matches(_as_values(metadata.get("project_scope")), constraints.project_id):
        return "project_scope_mismatch"
    if not _matches(_as_values(metadata.get("target_models")), constraints.model_id):
        return "model_mismatch"
    if not _matches(_as_values(metadata.get("target_modes")), constraints.mode):
        return "mode_mismatch"
    if not _matches(_as_values(metadata.get("aspect_ratios")), constraints.aspect_ratio):
        return "aspect_mismatch"
    if not _matches(_as_values(metadata.get("reference_modes")), constraints.reference_mode):
        return "reference_mode_mismatch"
    valid_until = str(metadata.get("valid_until", ""))
    if valid_until:
        try:
            if date.fromisoformat(valid_until) < constraints.date_value:
                return "expired"
        except ValueError:
            return "invalid_expiry"
    required = {item.lower() for item in constraints.required_tags}
    tags = {item.lower() for item in _as_values(metadata.get("query_tags"))}
    if required and not (required & tags):
        return "question_mismatch"
    non_applicable = {item.lower() for item in _as_values(metadata.get("non_applicability"))}
    context_values = {
        constraints.project_id.lower(), constraints.model_id.lower(), constraints.mode.lower(),
        constraints.aspect_ratio.lower(), constraints.reference_mode.lower(),
    }
    if non_applicable & context_values:
        return "non_applicability_matched"
    return None


def hard_filter(
    cards: Sequence[DecisionCard],
    require_approved: bool = False,
    min_quality: str = "textbook",
    project_id: str = "",
    *,
    constraints: RuntimeFilterConstraints | None = None,
    metadata: Mapping[str, Mapping[str, object]] | None = None,
    exclusion_reasons: Dict[str, str] | None = None,
) -> List[DecisionCard]:
    """Apply hard constraints before deterministic evidence ranking.

    ``metadata`` is an already-built index; this function never opens a source
    file.  Old callers without metadata retain the historical quality behavior.
    """
    if min_quality not in _QUALITY_RANK:
        raise ValueError(f"unknown min_quality: {min_quality}")
    active_constraints = constraints or RuntimeFilterConstraints(project_id=project_id)
    if constraints and project_id and project_id != constraints.project_id:
        raise ValueError("project_id conflicts with RuntimeFilterConstraints")
    min_rank = _QUALITY_RANK[min_quality]
    result: List[DecisionCard] = []
    index = metadata or {}
    reasons = exclusion_reasons if exclusion_reasons is not None else {}

    for card in cards:
        if card.source_quality == "legacy_pipeline":
            reasons.setdefault(card.card_id, "legacy_pipeline_forbidden")
            continue
        if require_approved and not card.user_approved:
            reasons.setdefault(card.card_id, "not_user_approved")
            continue
        if _QUALITY_RANK.get(card.source_quality, 0) < min_rank:
            reasons.setdefault(card.card_id, "below_quality_threshold")
            continue
        if card.card_id in index:
            reason = _metadata_reason(card, index[card.card_id], active_constraints)
            if reason:
                reasons.setdefault(card.card_id, reason)
                continue
        result.append(card)

    result.sort(key=lambda card: (
        -_QUALITY_RANK.get(card.source_quality, 0),
        -card.cross_scene_repeat,
        card.card_id,
    ))
    return result


@dataclass
class RetrievalBudget:
    """Tracks card capacity and rejects underflow/overflow accounting bugs."""

    max_cards: int
    _consumed: int = 0

    def __post_init__(self) -> None:
        if self.max_cards < 0:
            raise ValueError("max_cards cannot be negative")
        if self._consumed < 0 or self._consumed > self.max_cards:
            raise ValueError("initial consumed budget is invalid")

    @property
    def remaining(self) -> int:
        return self.max_cards - self._consumed

    @property
    def exhausted(self) -> bool:
        return self.remaining <= 0

    def consume(self, n: int = 1) -> None:
        if n < 0:
            raise ValueError("cannot consume a negative retrieval budget")
        if n > self.remaining:
            raise ValueError("retrieval budget exceeded")
        self._consumed += n


def select_by_budget(
    cards: Sequence[DecisionCard],
    max_cards: int,
    *,
    constraints: RuntimeFilterConstraints | None = None,
    metadata: Mapping[str, Mapping[str, object]] | None = None,
    exclusion_reasons: Dict[str, str] | None = None,
) -> List[DecisionCard]:
    """Select up to ``max_cards`` filtered cards; no match remains empty."""
    if max_cards < 0:
        raise ValueError("max_cards cannot be negative")
    if not cards or max_cards == 0:
        return []
    filtered = hard_filter(
        cards,
        constraints=constraints,
        metadata=metadata,
        exclusion_reasons=exclusion_reasons,
    )
    return filtered[:max_cards]


def select_with_budget(
    cards: Sequence[DecisionCard],
    budget: RetrievalBudget,
    *,
    constraints: RuntimeFilterConstraints | None = None,
    metadata: Mapping[str, Mapping[str, object]] | None = None,
    exclusion_reasons: Dict[str, str] | None = None,
) -> List[DecisionCard]:
    """Select cards only while a validated budget remains."""
    if budget.exhausted:
        return []
    filtered = hard_filter(
        cards,
        constraints=constraints,
        metadata=metadata,
        exclusion_reasons=exclusion_reasons,
    )
    selected = filtered[:budget.remaining]
    budget.consume(len(selected))
    return selected
