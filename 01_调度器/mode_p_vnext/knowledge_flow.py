"""Problem-driven, metadata-only knowledge retrieval for MODE:P vNext.

This is deliberately a Phase-A/Phase-B boundary, not a shot planner.  Phase A
can retrieve *problem* decision capsules from a pre-built metadata catalog;
execution capsules require an explicit blocking decision and are never used to
silently select a camera, edit, or storyboard answer.  Raw K0 passages are
not read by this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256
from mode_p_vnext.diagnosis_artifact import DiagnosisArtifact
from mode_p_vnext.knowledge_security import (
    KnowledgeSecurityEvent,
    UntrustedTextEnvelope,
)
from mode_p_vnext.retrieval_budget import RetrievalBudget
from mode_p_vnext.schema.decision_card import DecisionCard
from mode_p_vnext.schema.scene_diagnosis import KnowledgeQuery, SceneDiagnosis


_VALID_STAGES = frozenset({"problem", "execution"})
_VALID_RELATIONS = frozenset({"primary", "conflict", "anti_pattern"})
_VALID_EVIDENCE_TIERS = frozenset({"E0", "E1", "E2", "E3", "E4", "E5"})


def _hash(value: object) -> str:
    return stable_hash_sha256(canonical_json_dumps(value).encode("utf-8"))


def _normalise(value: str) -> str:
    return " ".join(value.lower().split())


def _contains_forbidden_shot_answer(value: str) -> bool:
    """Reject only concrete shot prescriptions, not ordinary film vocabulary."""
    lowered = _normalise(value)
    disallowed = (
        "50mm", "35mm", "85mm", "three shots", "3 shots", "full timeline",
        "完整时间轴", "三镜头", "固定机位", "camera at ", "shot 1",
    )
    return any(token in lowered for token in disallowed)


@dataclass(frozen=True)
class KnowledgeCandidate:
    """Audited metadata around a legacy :class:`DecisionCard`.

    The wrapper avoids changing the frozen V3.2 schema while adding the
    runtime filters and audit fields required by vNext.  ``raw_evidence`` is
    optional and always remains opaque/untrusted; it never enters a packet.
    """

    card: DecisionCard
    decision_domain: str
    director_question: str
    stage: str = "problem"
    query_tags: Tuple[str, ...] = field(default_factory=tuple)
    project_scope: Tuple[str, ...] = field(default_factory=lambda: ("*",))
    target_models: Tuple[str, ...] = field(default_factory=tuple)
    target_modes: Tuple[str, ...] = field(default_factory=tuple)
    aspect_ratios: Tuple[str, ...] = field(default_factory=tuple)
    reference_modes: Tuple[str, ...] = field(default_factory=tuple)
    valid_until: str = ""
    evidence_tier: str = "E1"
    version: str = "1"
    human_reviewed: bool = True
    status: str = "active"
    non_applicability: Tuple[str, ...] = field(default_factory=tuple)
    director_variables: Tuple[str, ...] = field(default_factory=tuple)
    observable_failures: Tuple[str, ...] = field(default_factory=tuple)
    must_not_decide: Tuple[str, ...] = field(default_factory=lambda: ("final_shot_design",))
    decision_relation: str = "primary"
    contradicts: Tuple[str, ...] = field(default_factory=tuple)
    linked_domains: Tuple[str, ...] = field(default_factory=tuple)
    model_adaptation: Tuple[str, ...] = field(default_factory=tuple)
    visibility_risk_class: str = ""
    positive_closure_requirements: Tuple[str, ...] = field(default_factory=tuple)
    negative_routing_constraints: Tuple[str, ...] = field(default_factory=tuple)
    raw_evidence: Optional[UntrustedTextEnvelope] = None

    def __post_init__(self) -> None:
        if self.stage not in _VALID_STAGES:
            raise ValueError(f"unknown knowledge stage: {self.stage}")
        if self.decision_relation not in _VALID_RELATIONS:
            raise ValueError(f"unknown decision relation: {self.decision_relation}")
        if self.evidence_tier not in _VALID_EVIDENCE_TIERS:
            raise ValueError(f"unknown evidence tier: {self.evidence_tier}")
        if not self.decision_domain or not self.director_question:
            raise ValueError("decision_domain and director_question are required")
        if _contains_forbidden_shot_answer(self.director_question):
            raise ValueError("knowledge capsule must not prescribe a fixed shot answer")
        if not self.must_not_decide:
            raise ValueError("knowledge capsule must state what the Director still decides")

    @property
    def card_id(self) -> str:
        return self.card.card_id

    @property
    def content_sha256(self) -> str:
        return _hash({
            "card": self.card.to_dict(),
            "decision_domain": self.decision_domain,
            "director_question": self.director_question,
            "stage": self.stage,
            "query_tags": self.query_tags,
            "project_scope": self.project_scope,
            "target_models": self.target_models,
            "target_modes": self.target_modes,
            "aspect_ratios": self.aspect_ratios,
            "reference_modes": self.reference_modes,
            "valid_until": self.valid_until,
            "evidence_tier": self.evidence_tier,
            "version": self.version,
            "human_reviewed": self.human_reviewed,
            "status": self.status,
            "non_applicability": self.non_applicability,
            "director_variables": self.director_variables,
            "observable_failures": self.observable_failures,
            "must_not_decide": self.must_not_decide,
            "decision_relation": self.decision_relation,
            "contradicts": self.contradicts,
            "linked_domains": self.linked_domains,
            "model_adaptation": self.model_adaptation,
            "visibility_risk_class": self.visibility_risk_class,
            "positive_closure_requirements": self.positive_closure_requirements,
            "negative_routing_constraints": self.negative_routing_constraints,
            "raw_evidence": self.raw_evidence.to_runtime_metadata() if self.raw_evidence else None,
        })

    def snapshot_record(self) -> Dict[str, Any]:
        """Auditable record with no raw source passage."""
        return {
            "card_id": self.card_id,
            "version": self.version,
            "content_sha256": self.content_sha256,
            "source_file": self.card.source_file,
            "source_hash": self.card.source_hash,
            "decision_domain": self.decision_domain,
            "stage": self.stage,
            "decision_relation": self.decision_relation,
            "evidence_tier": self.evidence_tier,
        }

    def director_payload(self) -> Dict[str, Any]:
        """Return a legacy prompt view without raw or local provenance data.

        This is an archival compatibility shape only.  It must not expose a
        filesystem locator, raw evidence, or caller-supplied provenance to a
        model.  The canonical v3.1 path uses ``KnowledgeDecisionView``.
        """
        return {
            "card_id": self.card_id,
            "title": self.card_id,
            "decision_domain": self.decision_domain,
            "director_question": self.director_question,
            "claim": self.card.claim,
            "applies_when": list(self.card.applicability_conditions),
            "non_applicability": list(self.non_applicability),
            "decision_relation": self.decision_relation,
            "linked_domains": list(self.linked_domains),
            "director_variables": list(self.director_variables),
            "observable_failures": list(self.observable_failures),
            "model_adaptation": list(self.model_adaptation),
            "visibility_risk_class": self.visibility_risk_class,
            "positive_closure_requirements": list(self.positive_closure_requirements),
            "negative_routing_constraints": list(self.negative_routing_constraints),
            # A locally derived digest keeps compatibility provenance useful
            # without reintroducing the source path into a model payload.
            "source_digest": self.content_sha256,
            "evidence_tier": self.evidence_tier,
            "counterexamples": list(self.card.counter_examples),
            "must_not_decide": list(self.must_not_decide),
            "version": self.version,
        }


@dataclass(frozen=True)
class KnowledgeCatalog:
    """A prebuilt metadata index; runtime retrieval never opens K0 sources."""

    candidates: Tuple[KnowledgeCandidate, ...]
    catalog_version: str = "vnext-k2-metadata-1"

    def __post_init__(self) -> None:
        ids = [candidate.card_id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("knowledge catalog contains duplicate card_id values")

    @property
    def index_sha256(self) -> str:
        return _hash({
            "catalog_version": self.catalog_version,
            "candidates": [candidate.snapshot_record() for candidate in self.candidates],
        })


@dataclass(frozen=True)
class RetrievalContext:
    """Hard runtime constraints supplied by the project, never inferred from text."""

    project_id: str
    model_id: str = ""
    mode: str = ""
    aspect_ratio: str = ""
    reference_mode: str = ""
    as_of: str = ""
    blocked_card_ids: Tuple[str, ...] = field(default_factory=tuple)
    fact_override_card_ids: Tuple[str, ...] = field(default_factory=tuple)
    user_override_card_ids: Tuple[str, ...] = field(default_factory=tuple)
    continuity_override_card_ids: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def all_overrides(self) -> Tuple[str, ...]:
        return tuple(sorted(set(
            self.blocked_card_ids
            + self.fact_override_card_ids
            + self.user_override_card_ids
            + self.continuity_override_card_ids
        )))

    @property
    def current_date(self) -> date:
        return date.fromisoformat(self.as_of) if self.as_of else date.today()


@dataclass(frozen=True)
class RetrievalPolicy:
    """Frozen-plan normal budget; these limits are intentionally stricter than legacy K2."""

    primary_card_limit: int = 3
    conflict_record_limit: int = 1
    anti_pattern_limit: int = 1
    retriever_version: str = "knowledge-flow-1"
    ranking_version: str = "evidence-quality-then-repeat-1"

    def __post_init__(self) -> None:
        if self.primary_card_limit < 0 or self.conflict_record_limit < 0 or self.anti_pattern_limit < 0:
            raise ValueError("retrieval policy limits cannot be negative")


@dataclass(frozen=True)
class ConflictExposure:
    """A maximum-two-option conflict that requires a Director decision."""

    conflict_id: str
    option_card_ids: Tuple[str, ...]
    director_question: str

    def __post_init__(self) -> None:
        if not 2 <= len(self.option_card_ids) <= 2:
            raise ValueError("a conflict exposure must contain exactly two options")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "option_card_ids": list(self.option_card_ids),
            "director_question": self.director_question,
            "requires_director_decision": True,
        }


@dataclass(frozen=True)
class KnowledgePacket:
    """The small, reviewed packet Phase B may consider; it is not a shot answer."""

    phase: str
    query: KnowledgeQuery
    k1_principles: Tuple[str, ...]
    primary_cards: Tuple[KnowledgeCandidate, ...]
    anti_pattern_cards: Tuple[KnowledgeCandidate, ...]
    conflict_exposures: Tuple[ConflictExposure, ...]
    no_match: bool

    def to_director_payload(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "primary_cards": [card.director_payload() for card in self.primary_cards],
            "anti_pattern_cards": [card.director_payload() for card in self.anti_pattern_cards],
            "conflict_exposures": [item.to_dict() for item in self.conflict_exposures],
            "no_match": self.no_match,
            # ``k1_principles`` is retained on the archival packet for old
            # readers, but it is caller-supplied text and never prompt input.
            "director_must_decide": "blocking, camera, composition, edit and final execution are not auto-selected",
        }


@dataclass(frozen=True)
class KnowledgeSelectionReceipt:
    """Non-authoritative metadata receipt emitted by the legacy adapter.

    It preserves enough bounded metadata for old callers to inspect a prior
    selection without becoming a second vNext ``KnowledgeSnapshot``.  Only
    ``KnowledgeRetriever`` may create the canonical snapshot sealed in an
    ``ArtifactEnvelope``.
    """

    snapshot_id: str
    query: Mapping[str, Any]
    selected_card_records: Tuple[Mapping[str, Any], ...]
    conflict_records: Tuple[Mapping[str, Any], ...]
    index_sha256: str
    exclusions: Mapping[str, str]
    selection_reasons: Mapping[str, str]
    stage_budgets: Mapping[str, int]
    security_events: Tuple[Mapping[str, Any], ...]
    content_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.content_sha256:
            object.__setattr__(self, "content_sha256", _hash(self._integrity_payload()))

    @property
    def selected_card_ids(self) -> Tuple[str, ...]:
        return tuple(str(record["card_id"]) for record in self.selected_card_records)

    @property
    def conflict_ids(self) -> Tuple[str, ...]:
        return tuple(
            str(record.get("conflict_id", _hash(record)[:16]))
            for record in self.conflict_records
        )

    @property
    def query_sha256(self) -> str:
        return _hash(dict(self.query))

    def _integrity_payload(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.snapshot_id,
            "query": dict(self.query),
            "selected_card_records": [dict(record) for record in self.selected_card_records],
            "conflict_records": [dict(record) for record in self.conflict_records],
            "index_sha256": self.index_sha256,
            "exclusions": dict(sorted(self.exclusions.items())),
            "selection_reasons": dict(sorted(self.selection_reasons.items())),
            "stage_budgets": dict(sorted(self.stage_budgets.items())),
            "security_events": [dict(event) for event in self.security_events],
        }

    def to_dict(self) -> Dict[str, Any]:
        payload = self._integrity_payload()
        payload.update({
            "snapshot_id": self.snapshot_id,
            "selected_card_ids": list(self.selected_card_ids),
            "conflict_ids": list(self.conflict_ids),
            "query_sha256": self.query_sha256,
            "content_sha256": self.content_sha256,
        })
        return payload

    def verify_integrity(self) -> bool:
        return self.content_sha256 == _hash(self._integrity_payload())


@dataclass(frozen=True)
class KnowledgeRetrievalResult:
    """Selection, audit evidence and security events for one no-model retrieval."""

    query: KnowledgeQuery
    packet: KnowledgePacket
    selection_receipt: KnowledgeSelectionReceipt
    exclusions: Mapping[str, str]
    security_events: Tuple[KnowledgeSecurityEvent, ...]

    @property
    def snapshot(self) -> KnowledgeSelectionReceipt:
        """Deprecated compatibility name for historical callers only."""

        return self.selection_receipt


def retrieve_for_diagnosis(
    diagnosis: DiagnosisArtifact | SceneDiagnosis,
    catalog: KnowledgeCatalog,
    context: RetrievalContext,
    *,
    policy: RetrievalPolicy = RetrievalPolicy(),
    budget: RetrievalBudget | None = None,
    blocking: Mapping[str, Any] | None = None,
    k1_principles: Sequence[str] = (),
) -> KnowledgeRetrievalResult:
    """Read the service-owned selection through the historical packet shape.

    This function owns no eligibility, ranking, budget, conflict, security or
    promotion logic.  It is an archive adapter only; the sole K1/K2
    implementation lives in ``services.knowledge_retriever``.
    """
    from mode_p_vnext.services.knowledge_retriever import (
        retrieve_legacy_compatibility,
    )

    return retrieve_legacy_compatibility(
        diagnosis=diagnosis,
        catalog=catalog,
        context=context,
        policy=policy,
        budget=budget,
        blocking=blocking,
        k1_principles=k1_principles,
    )
