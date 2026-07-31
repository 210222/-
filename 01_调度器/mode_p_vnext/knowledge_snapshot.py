"""Compatibility-only archive records for pre-vNext knowledge callers.

The sole runtime knowledge snapshot is
``mode_p_vnext.domain.knowledge.KnowledgeSnapshot`` sealed in an
``ArtifactEnvelope`` by ``services.knowledge_retriever``.  This module keeps
the historical list-oriented API readable for archived callers; its records
are deliberately not accepted as a vNext retrieval, sealing, or replay
authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256
from mode_p_vnext.schema.decision_card import DecisionCard


def _hash(value: object) -> str:
    return stable_hash_sha256(canonical_json_dumps(value).encode("utf-8"))


def _record_card(card: object) -> Dict[str, Any]:
    """Produce an opaque card record without retaining untrusted source text."""
    snapshot_record = getattr(card, "snapshot_record", None)
    if callable(snapshot_record):
        record = dict(snapshot_record())
        if "content_sha256" not in record:
            record["content_sha256"] = _hash(record)
        return record
    if isinstance(card, DecisionCard):
        content = card.to_dict()
        return {
            "card_id": card.card_id,
            "version": "1",
            "content_sha256": _hash(content),
            "source_file": card.source_file,
            "source_hash": card.source_hash,
        }
    if isinstance(card, Mapping):
        record = dict(card)
        if "card_id" not in record:
            raise ValueError("card record requires card_id")
        record.setdefault("version", "1")
        record.setdefault("content_sha256", _hash(record))
        return record
    card_id = getattr(card, "card_id", None)
    if not card_id:
        raise TypeError("selected card must provide card_id or snapshot_record")
    return {"card_id": str(card_id), "version": "1", "content_sha256": _hash({"card_id": card_id})}


@dataclass
class LegacyKnowledgeSelectionArchive:
    """Historical selection record, not a vNext ``KnowledgeSnapshot``."""

    snapshot_id: str
    selected_card_ids: List[str] = field(default_factory=list)
    conflict_ids: List[str] = field(default_factory=list)
    not_selected: Dict[str, str] = field(default_factory=dict)
    budget_used: int = 0
    budget_total: int = 0
    content_sha256: str = ""
    # v2: enough information to prove/replay selection without invoking search
    query: Dict[str, Any] = field(default_factory=dict)
    query_sha256: str = ""
    retriever_version: str = ""
    ranking_version: str = ""
    index_sha256: str = ""
    candidate_set_id: str = ""
    candidate_card_ids: List[str] = field(default_factory=list)
    selected_card_records: List[Dict[str, Any]] = field(default_factory=list)
    selection_reasons: Dict[str, str] = field(default_factory=dict)
    exclusion_reasons: Dict[str, str] = field(default_factory=dict)
    deduplicated_card_ids: List[str] = field(default_factory=list)
    conflict_records: List[Dict[str, Any]] = field(default_factory=list)
    stage_budgets: Dict[str, int] = field(default_factory=dict)
    security_events: List[Dict[str, Any]] = field(default_factory=list)

    def _integrity_payload(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "selected_card_ids": list(self.selected_card_ids),
            "conflict_ids": list(self.conflict_ids),
            "not_selected": dict(sorted(self.not_selected.items())),
            "budget_used": self.budget_used,
            "budget_total": self.budget_total,
            "query": self.query,
            "query_sha256": self.query_sha256,
            "retriever_version": self.retriever_version,
            "ranking_version": self.ranking_version,
            "index_sha256": self.index_sha256,
            "candidate_set_id": self.candidate_set_id,
            "candidate_card_ids": list(self.candidate_card_ids),
            "selected_card_records": list(self.selected_card_records),
            "selection_reasons": dict(sorted(self.selection_reasons.items())),
            "exclusion_reasons": dict(sorted(self.exclusion_reasons.items())),
            "deduplicated_card_ids": list(self.deduplicated_card_ids),
            "conflict_records": list(self.conflict_records),
            "stage_budgets": dict(sorted(self.stage_budgets.items())),
            "security_events": list(self.security_events),
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self._integrity_payload()
        if self.content_sha256:
            d["content_sha256"] = self.content_sha256
        return d

    def verify_integrity(self) -> bool:
        """Detect post-seal mutation of any selection or provenance field."""
        return bool(self.content_sha256) and self.content_sha256 == _hash(self._integrity_payload())


@dataclass(frozen=True)
class KnowledgeReplay:
    """Frozen replay input; creating it never performs a second retrieval."""

    snapshot_id: str
    query: Mapping[str, Any]
    selected_card_records: tuple[Mapping[str, Any], ...]
    conflict_records: tuple[Mapping[str, Any], ...]
    index_sha256: str


def _seal(snapshot: LegacyKnowledgeSelectionArchive) -> LegacyKnowledgeSelectionArchive:
    snapshot.content_sha256 = _hash(snapshot._integrity_payload())
    return snapshot


def create_snapshot(
    snapshot_id: str,
    selected_cards: Sequence[DecisionCard],
    not_selected: Dict[str, str],
    budget_total: int,
    conflict_ids: Optional[List[str]] = None,
) -> LegacyKnowledgeSelectionArchive:
    """Create a sealed historical archive record for a legacy caller."""
    if budget_total < 0:
        raise ValueError("budget_total cannot be negative")
    records = [_record_card(card) for card in selected_cards]
    snapshot = LegacyKnowledgeSelectionArchive(
        snapshot_id=snapshot_id,
        selected_card_ids=[record["card_id"] for record in records],
        conflict_ids=list(conflict_ids or []),
        not_selected=dict(not_selected),
        budget_used=len(records),
        budget_total=budget_total,
        selected_card_records=records,
        exclusion_reasons=dict(not_selected),
    )
    return _seal(snapshot)


def create_retrieval_snapshot(
    *,
    snapshot_id: str,
    query: Mapping[str, Any],
    selected_cards: Sequence[object],
    candidate_cards: Sequence[object],
    exclusions: Mapping[str, str],
    conflicts: Sequence[Mapping[str, Any]],
    index_sha256: str,
    retriever_version: str,
    ranking_version: str,
    stage_budgets: Mapping[str, int],
    security_events: Sequence[Mapping[str, Any]] = (),
    selection_reasons: Mapping[str, str] | None = None,
) -> LegacyKnowledgeSelectionArchive:
    """Seal a historical archive record; never use it in vNext runtime."""
    candidate_records = [_record_card(card) for card in candidate_cards]
    selected_records = [_record_card(card) for card in selected_cards]
    selected_ids = [record["card_id"] for record in selected_records]
    conflict_records = [dict(record) for record in conflicts]
    conflict_ids = [str(record.get("conflict_id", _hash(record)[:16])) for record in conflict_records]
    deduplicated = [
        card_id for card_id, reason in exclusions.items() if str(reason).startswith("duplicate_of:")
    ]
    if any(value < 0 for value in stage_budgets.values()):
        raise ValueError("stage budgets cannot be negative")
    snapshot = LegacyKnowledgeSelectionArchive(
        snapshot_id=snapshot_id,
        selected_card_ids=selected_ids,
        conflict_ids=conflict_ids,
        not_selected=dict(exclusions),
        budget_used=len(selected_ids),
        budget_total=int(stage_budgets.get("primary_limit", 0)) + int(stage_budgets.get("anti_pattern_limit", 0)),
        query=dict(query),
        query_sha256=_hash(dict(query)),
        retriever_version=retriever_version,
        ranking_version=ranking_version,
        index_sha256=index_sha256,
        candidate_set_id="KCS-" + _hash(candidate_records)[:16],
        candidate_card_ids=[record["card_id"] for record in candidate_records],
        selected_card_records=selected_records,
        selection_reasons=dict(selection_reasons or {}),
        exclusion_reasons=dict(exclusions),
        deduplicated_card_ids=deduplicated,
        conflict_records=conflict_records,
        stage_budgets={key: int(value) for key, value in stage_budgets.items()},
        security_events=[dict(event) for event in security_events],
    )
    return _seal(snapshot)


def replay_snapshot(snapshot: LegacyKnowledgeSelectionArchive | object) -> KnowledgeReplay:
    """Read a sealed historical archive without invoking retrieval."""
    if not snapshot.verify_integrity():
        raise ValueError("knowledge snapshot integrity check failed")
    return KnowledgeReplay(
        snapshot_id=snapshot.snapshot_id,
        query=dict(snapshot.query),
        selected_card_records=tuple(dict(record) for record in snapshot.selected_card_records),
        conflict_records=tuple(dict(record) for record in snapshot.conflict_records),
        index_sha256=snapshot.index_sha256,
    )


def __getattr__(name: str) -> object:
    """Resolve the retired v3 constructor only for historical import sites.

    New vNext code must import the canonical type from
    ``mode_p_vnext.domain.knowledge``.  Keeping this dynamic compatibility
    lookup avoids re-declaring a second runtime class with that authority.
    """

    if name == "KnowledgeSnapshot":
        return LegacyKnowledgeSelectionArchive
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
