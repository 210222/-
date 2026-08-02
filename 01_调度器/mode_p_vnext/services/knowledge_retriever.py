"""Canonical K1/K2 knowledge boundary for MODE:P vNext.

The legacy retrieval module is intentionally used only as a metadata search
adapter.  This service is the sole K1/K2 boundary: it converts candidates into
the frozen v3.0 domain types, seals the complete selection in an ArtifactEnvelope,
and never lets raw source text or retriever-side conflict resolution enter the
Director view.
"""

from __future__ import annotations

from datetime import date
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from mode_p_vnext.domain.artifact import (
    DOMAIN_SCHEMA_VERSION,
    ArtifactEnvelope,
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    canonical_sha256,
    require_sha256,
)
from mode_p_vnext.domain.knowledge import (
    KnowledgeCandidateRecord,
    KnowledgeCapsuleV2,
    KnowledgeDecisionEntry,
    KnowledgeDecisionView,
    KnowledgeSnapshot,
    KnowledgeStage,
)
from mode_p_vnext.conflict_graph import build_conflict_graph
from mode_p_vnext.diagnosis_artifact import (
    DiagnosisArtifact,
    validate_diagnosis_artifact,
)
from mode_p_vnext.knowledge_flow import (
    KnowledgeCandidate,
    KnowledgeCatalog,
    RetrievalContext,
    RetrievalPolicy,
)
from mode_p_vnext.knowledge_security import (
    KnowledgeSecurityEvent,
    envelope_untrusted_text,
    inspect_untrusted_text,
)
from mode_p_vnext.retrieval_budget import RetrievalBudget
from mode_p_vnext.schema.scene_diagnosis import (
    KnowledgeQuery,
    SceneDiagnosis,
    generate_knowledge_query,
)


_SCHEMA_VERSION = DOMAIN_SCHEMA_VERSION


class KnowledgePromotionError(ValueError):
    """A candidate has not cleared the evidence-and-human promotion gate."""


def _non_empty_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be a non-empty string")


def _unique_text(values: Sequence[str]) -> tuple[str, ...]:
    """Return compact, stable text without inheriting duplicate metadata."""

    return tuple(dict.fromkeys(value for value in values if value.strip()))


def _digest_tuple(
    value: Sequence[str], field_name: str, *, require_items: bool
) -> tuple[str, ...]:
    values = tuple(value)
    if require_items and not values:
        raise DomainValidationError(f"{field_name} must not be empty")
    if len(values) != len(set(values)):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    for digest in values:
        require_sha256(digest, f"{field_name} entry")
    return values


@dataclass(frozen=True)
class VerifiedBlockingCommit:
    """Cryptographically bound evidence that permits the K2 transition."""

    scene_id: str
    artifact_id: str
    content_sha256: str
    verification_digest: str

    def __post_init__(self) -> None:
        _non_empty_text(self.scene_id, "scene_id")
        _non_empty_text(self.artifact_id, "artifact_id")
        require_sha256(self.content_sha256, "content_sha256")
        require_sha256(self.verification_digest, "verification_digest")

    @property
    def binding_digest(self) -> str:
        """Hash every identity field that proves the K2 transition boundary.

        ``content_sha256`` alone is insufficient: two accepted artifacts can
        have identical payload bytes while differing in artifact identity or
        verification evidence.  The K2 snapshot must bind all three values.
        """

        return canonical_sha256(
            {
                "scene_id": self.scene_id,
                "artifact_id": self.artifact_id,
                "content_sha256": self.content_sha256,
                "verification_digest": self.verification_digest,
            }
        )


@dataclass(frozen=True)
class EvidenceVerifiedPromotion:
    """A proposal from experience or media evidence, still outside K1/K2."""

    proposal_id: str
    capsule: KnowledgeCapsuleV2
    evidence_digests: tuple[str, ...]
    verifier_id: str
    human_reviewer_id: str
    human_approved: bool
    media_observation_digests: tuple[str, ...] = ()
    outcome_attribution_digest: str = ""
    pattern_candidate_digest: str = ""
    corroborating_case_digests: tuple[str, ...] = ()
    counterexample_digests: tuple[str, ...] = ()
    applicability_scope_digest: str = ""

    def __post_init__(self) -> None:
        _non_empty_text(self.proposal_id, "proposal_id")
        if type(self.capsule) is not KnowledgeCapsuleV2:
            raise DomainValidationError("capsule must be a KnowledgeCapsuleV2")
        if (
            not self.media_observation_digests
            or not self.outcome_attribution_digest
            or not self.pattern_candidate_digest
            or not self.corroborating_case_digests
            or not self.counterexample_digests
            or not self.applicability_scope_digest
        ):
            raise DomainValidationError(
                "structured experience promotion chain is required"
            )
        evidence = _digest_tuple(
            self.evidence_digests, "evidence_digests", require_items=False
        )
        observations = _digest_tuple(
            self.media_observation_digests,
            "media_observation_digests",
            require_items=True,
        )
        corroborating = _digest_tuple(
            self.corroborating_case_digests,
            "corroborating_case_digests",
            require_items=True,
        )
        counterexamples = _digest_tuple(
            self.counterexample_digests,
            "counterexample_digests",
            require_items=True,
        )
        for field_name in (
            "outcome_attribution_digest",
            "pattern_candidate_digest",
            "applicability_scope_digest",
        ):
            require_sha256(getattr(self, field_name), field_name)
        chain = {
            *observations,
            self.outcome_attribution_digest,
            self.pattern_candidate_digest,
            *corroborating,
            *counterexamples,
            self.applicability_scope_digest,
        }
        chain_entries = (
            *observations,
            self.outcome_attribution_digest,
            self.pattern_candidate_digest,
            *corroborating,
            *counterexamples,
            self.applicability_scope_digest,
        )
        if len(chain_entries) != len(chain):
            raise DomainValidationError(
                "structured experience promotion links must be distinct"
            )
        if evidence and set(evidence) != chain:
            raise DomainValidationError(
                "evidence_digests must bind exactly the structured experience links"
            )
        object.__setattr__(self, "evidence_digests", evidence)
        object.__setattr__(self, "media_observation_digests", observations)
        object.__setattr__(self, "corroborating_case_digests", corroborating)
        object.__setattr__(self, "counterexample_digests", counterexamples)


@dataclass(frozen=True)
class ApprovedKnowledgeCapsule:
    """An auditable result of the candidate -> verified -> human gate."""

    capsule: KnowledgeCapsuleV2
    promotion_digest: str


@dataclass(frozen=True)
class KnowledgeRetrieval:
    """The sole K1/K2 retrieval result, bound to canonical artifacts."""

    stage: KnowledgeStage
    selected_capsules: tuple[KnowledgeCapsuleV2, ...]
    decision_view: KnowledgeDecisionView
    snapshot: ArtifactEnvelope[KnowledgeSnapshot]
    conflicts: tuple[Mapping[str, Any], ...]
    exclusions: Mapping[str, str]
    blocking_commit_digest: str | None


@dataclass(frozen=True)
class KnowledgeReplay:
    """A replay reads a sealed canonical snapshot without catalog retrieval."""

    snapshot_id: str
    decision_view: KnowledgeDecisionView
    selected_card_ids: tuple[str, ...]


def _candidate_source_ref(candidate: KnowledgeCandidate) -> SourceRef:
    """Retain trusted locators in the snapshot but never expose raw identities."""

    source_digest = candidate.card.source_hash
    try:
        require_sha256(source_digest, "candidate source_hash")
    except DomainValidationError:
        source_digest = candidate.content_sha256

    if candidate.raw_evidence is not None:
        synthetic_id = canonical_sha256(
            {
                "candidate_id": candidate.card_id,
                "candidate_digest": candidate.content_sha256,
                "source_digest": source_digest,
            }
        )[:24]
        return SourceRef(
            source_id=f"quarantined:{synthetic_id}",
            digest=source_digest,
        )

    locator = candidate.card.source_file or None
    return SourceRef(
        source_id=locator or f"knowledge-candidate:{candidate.card_id}",
        digest=source_digest,
        locator=locator,
    )


def _candidate_record(candidate: KnowledgeCandidate) -> KnowledgeCandidateRecord:
    """Seal every candidate, including excluded candidates, for replay."""

    source_ref = _candidate_source_ref(candidate)
    return KnowledgeCandidateRecord(
        candidate_id=candidate.card_id,
        content_sha256=candidate.content_sha256,
        source_refs=(source_ref,),
        field_provenance={
            "candidate_metadata": (source_ref,),
            "selection_metadata": (source_ref,),
        },
    )


def _candidate_to_capsule(candidate: KnowledgeCandidate) -> KnowledgeCapsuleV2:
    """Convert reviewed metadata into the unique canonical capsule type.

    The legacy catalog lacks a provenance-complete valid-from capability
    record.  A claimed ``platform_capability`` is therefore not upgraded by
    guesswork; it remains excluded until a canonical capability capsule is
    supplied through the proper promotion route.
    """

    if candidate.decision_domain == "platform_capability":
        raise ValueError("capability_scope_required")
    source_ref = _candidate_source_ref(candidate)
    return KnowledgeCapsuleV2(
        capsule_id=candidate.card_id,
        category=candidate.decision_domain,
        claims=(candidate.card.claim,),
        source_summary=(
            f"Reviewed catalog metadata for {candidate.card_id}; full source "
            "provenance is retained in the sealed snapshot."
        ),
        source_refs=(source_ref,),
        field_provenance={
            "claims": (source_ref,),
            "source_summary": (source_ref,),
        },
        capability_scope=None,
        confidence={
            "golden_evidence": "high",
            "render_evidence": "high",
            "cross_project": "medium",
            "user_opinion": "low",
        }.get(candidate.card.source_quality, "low"),
    )


def _entry_for_candidate(
    candidate: KnowledgeCandidate, record: KnowledgeCandidateRecord
) -> KnowledgeDecisionEntry:
    return KnowledgeDecisionEntry(
        capsule_id=candidate.card_id,
        director_question=candidate.director_question,
        applies_because=_unique_text(
            candidate.query_tags or (candidate.decision_domain,)
        ),
        execution_constraints=_unique_text(
            candidate.positive_closure_requirements
            + candidate.negative_routing_constraints
            or candidate.must_not_decide
        ),
        expected_effect=candidate.card.claim,
        tradeoff=_unique_text(
            tuple(candidate.card.counter_examples) + candidate.non_applicability
        ),
        anti_pattern=candidate.decision_relation == "anti_pattern",
        source_digest=record.content_sha256,
    )


def _security_event_digest(event: object) -> str:
    """Keep a verifiable event trace without exposing an untrusted source ID."""

    event_dict = event.to_dict()
    return canonical_sha256(
        {
            "event_id": event_dict["event_id"],
            "category": event_dict["category"],
            "content_sha256": event_dict["content_sha256"],
            "reason_codes": tuple(event_dict["reason_codes"]),
            "disposition": event_dict["disposition"],
        }
    )


_K1_EXECUTION_TERMS = (
    "camera",
    "shot",
    "lens",
    "framing",
    "composition",
    "editing",
    "edit",
    "timeline",
    "摄影",
    "镜头",
    "机位",
    "构图",
    "剪辑",
    "时间线",
)


def _is_k1_compatible(candidate: KnowledgeCandidate) -> bool:
    """Keep execution knowledge out of K1 even if metadata is mislabelled."""

    text = " ".join(
        (
            candidate.decision_domain,
            candidate.director_question,
            candidate.card.claim,
            *candidate.query_tags,
        )
    ).casefold()
    return not any(term in text for term in _K1_EXECUTION_TERMS)


_QUALITY_RANK = {
    "golden_evidence": 5,
    "render_evidence": 4,
    "cross_project": 3,
    "user_opinion": 2,
    "textbook": 1,
    "legacy_pipeline": 0,
}


@dataclass(frozen=True)
class _MetadataSelection:
    """Private deterministic K1/K2 selection before canonical sealing.

    This is deliberately local to this service.  It is the one implementation
    that may decide candidate eligibility, ordering, budget use, conflict
    exposure, or prompt-safety quarantine for both stages.
    """

    query: KnowledgeQuery
    phase: str
    selected_candidates: tuple[KnowledgeCandidate, ...]
    primary_candidates: tuple[KnowledgeCandidate, ...]
    anti_pattern_candidates: tuple[KnowledgeCandidate, ...]
    conflicts: tuple[Mapping[str, Any], ...]
    exclusions: Mapping[str, str]
    security_events: tuple[KnowledgeSecurityEvent, ...]
    selection_reasons: Mapping[str, str]
    stage_budgets: Mapping[str, int]


def _normalise_knowledge_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _query_terms(
    query: KnowledgeQuery,
    diagnosis_artifact: DiagnosisArtifact | None,
) -> tuple[str, ...]:
    terms: list[str] = list(query.dimension_questions.keys())
    for values in query.dimension_questions.values():
        terms.extend(values)
    terms.extend(query.model_risk_queries)
    terms.extend(query.user_constraint_queries)
    if diagnosis_artifact is not None and diagnosis_artifact.problem_set:
        terms.extend(diagnosis_artifact.problem_set.knowledge_questions)
        terms.extend(diagnosis_artifact.problem_set.decision_domains)
    return tuple(_normalise_knowledge_text(term) for term in terms if term)


def _candidate_matches_query(
    candidate: KnowledgeCandidate, terms: Sequence[str]
) -> bool:
    tags = {_normalise_knowledge_text(item) for item in candidate.query_tags}
    domain = _normalise_knowledge_text(candidate.decision_domain)
    question = _normalise_knowledge_text(candidate.director_question)
    if not terms:
        return False
    for term in terms:
        if term in tags or domain == term or term == domain:
            return True
        if any(tag and (tag in term or term in tag) for tag in tags):
            return True
        if domain and (domain in term or term in domain):
            return True
        if question and (question in term or term in question):
            return True
    return False


def _scope_matches(expected: Sequence[str], actual: str) -> bool:
    return not expected or "*" in expected or (bool(actual) and actual in expected)


def _candidate_security_events(
    candidate: KnowledgeCandidate, context: RetrievalContext
) -> tuple[KnowledgeSecurityEvent, ...]:
    events: list[KnowledgeSecurityEvent] = []
    if candidate.raw_evidence is not None:
        if candidate.raw_evidence.project_id != context.project_id:
            events.append(
                KnowledgeSecurityEvent(
                    event_id="SEC-"
                    + canonical_sha256(
                        {
                            "cross_project": candidate.card_id,
                            "project": context.project_id,
                        }
                    )[:16],
                    category="CROSS_PROJECT_SOURCE",
                    source_id=candidate.raw_evidence.source_id,
                    project_id=context.project_id,
                    content_sha256=candidate.raw_evidence.content_sha256,
                    reason_codes=("source_project_mismatch",),
                )
            )
        event = inspect_untrusted_text(candidate.raw_evidence)
        if event is not None:
            events.append(event)
    claim_event = inspect_untrusted_text(
        envelope_untrusted_text(
            source_id=f"card:{candidate.card_id}",
            source_kind="knowledge_card_claim",
            project_id=context.project_id,
            content=candidate.card.claim,
        )
    )
    if claim_event is not None:
        events.append(claim_event)
    # The decision view deliberately contains only a narrow metadata subset,
    # but every value in that subset is still data at this boundary.  Scanning
    # only ``raw_evidence`` or the card claim would leave an instruction-shaped
    # director question, tag, constraint, or tradeoff able to reach a model.
    director_visible_metadata = {
        "decision_domain": (candidate.decision_domain,),
        "director_question": (candidate.director_question,),
        "query_tags": candidate.query_tags,
        "positive_closure_requirements": candidate.positive_closure_requirements,
        "negative_routing_constraints": candidate.negative_routing_constraints,
        "must_not_decide": candidate.must_not_decide,
        "counter_examples": candidate.card.counter_examples,
        "non_applicability": candidate.non_applicability,
    }
    for field_name, values in director_visible_metadata.items():
        for ordinal, value in enumerate(values):
            event = inspect_untrusted_text(
                envelope_untrusted_text(
                    source_id=f"card:{candidate.card_id}:{field_name}:{ordinal}",
                    source_kind="knowledge_card_metadata",
                    project_id=context.project_id,
                    content=value,
                )
            )
            if event is not None:
                events.append(event)
    return tuple(events)


def _hard_exclusion_reason(
    candidate: KnowledgeCandidate,
    context: RetrievalContext,
    phase: str,
    terms: Sequence[str],
) -> str | None:
    if candidate.status != "active" or not candidate.human_reviewed:
        return "not_human_reviewed_active"
    if candidate.stage != phase:
        return "stage_not_available"
    if candidate.card.source_quality == "legacy_pipeline":
        return "legacy_pipeline_forbidden"
    if candidate.card_id in context.all_overrides:
        return "overridden_by_fact_user_or_continuity"
    if not _scope_matches(candidate.project_scope, context.project_id):
        return "project_scope_mismatch"
    if not _scope_matches(candidate.target_models, context.model_id):
        return "model_mismatch"
    if not _scope_matches(candidate.target_modes, context.mode):
        return "mode_mismatch"
    if not _scope_matches(candidate.aspect_ratios, context.aspect_ratio):
        return "aspect_mismatch"
    if not _scope_matches(candidate.reference_modes, context.reference_mode):
        return "reference_mode_mismatch"
    if candidate.valid_until:
        try:
            expired = date.fromisoformat(candidate.valid_until) < context.current_date
        except ValueError as exc:
            raise ValueError(
                f"invalid valid_until for {candidate.card_id}: {candidate.valid_until}"
            ) from exc
        if expired:
            return "expired"
    context_values = {
        _normalise_knowledge_text(context.project_id),
        _normalise_knowledge_text(context.model_id),
        _normalise_knowledge_text(context.mode),
        _normalise_knowledge_text(context.aspect_ratio),
        _normalise_knowledge_text(context.reference_mode),
    }
    if any(
        _normalise_knowledge_text(condition) in context_values
        for condition in candidate.non_applicability
    ):
        return "non_applicability_matched"
    if not _candidate_matches_query(candidate, terms):
        return "question_mismatch"
    return None


def _rank_key(candidate: KnowledgeCandidate) -> tuple[int, int, str]:
    return (
        -_QUALITY_RANK.get(candidate.card.source_quality, 0),
        -candidate.card.cross_scene_repeat,
        candidate.card_id,
    )


def _deduplicate(
    candidates: Sequence[KnowledgeCandidate],
) -> tuple[list[KnowledgeCandidate], dict[str, str]]:
    selected: list[KnowledgeCandidate] = []
    exclusions: dict[str, str] = {}
    seen: dict[tuple[str, str, str], str] = {}
    for candidate in sorted(candidates, key=_rank_key):
        source = candidate.card.source_hash or candidate.card.source_file or candidate.card_id
        key = (source, candidate.version, candidate.decision_domain)
        if key in seen:
            exclusions[candidate.card_id] = f"duplicate_of:{seen[key]}"
            continue
        seen[key] = candidate.card_id
        selected.append(candidate)
    return selected, exclusions


def _conflict_records(
    candidates: Sequence[KnowledgeCandidate], policy: RetrievalPolicy
) -> tuple[Mapping[str, Any], ...]:
    by_id = {candidate.card_id: candidate for candidate in candidates}
    pairs: set[tuple[str, str]] = set()
    for candidate in candidates:
        for other_id in candidate.contradicts:
            if other_id in by_id:
                pairs.add(tuple(sorted((candidate.card_id, other_id))))
    for conflict in build_conflict_graph(
        [candidate.card for candidate in candidates]
    ).conflicts:
        identifiers = tuple(sorted(conflict.get("card_ids", [])))
        if len(identifiers) == 2:
            pairs.add(identifiers)
    records: list[Mapping[str, Any]] = []
    for left, right in sorted(pairs):
        if len(records) >= policy.conflict_record_limit:
            break
        records.append(
            {
                "conflict_id": "KCON-"
                + canonical_sha256({"left": left, "right": right})[:12],
                "option_card_ids": (left, right),
                "director_question": (
                    f"Resolve the conflict between {left} and {right}; do not "
                    "select a creative winner automatically."
                ),
                "requires_director_decision": True,
            }
        )
    return tuple(records)


def _select_metadata(
    *,
    diagnosis: SceneDiagnosis,
    catalog: KnowledgeCatalog,
    context: RetrievalContext,
    stage: KnowledgeStage,
    policy: RetrievalPolicy,
    k1_principles: Sequence[str] = (),
    budget: RetrievalBudget | None = None,
    diagnosis_artifact: DiagnosisArtifact | None = None,
) -> _MetadataSelection:
    """Perform the sole deterministic candidate selection for K1 or K2."""

    phase = "problem" if stage is KnowledgeStage.K1 else "execution"
    query = generate_knowledge_query(diagnosis)
    terms = _query_terms(query, diagnosis_artifact)
    exclusions: dict[str, str] = {}
    security_events: list[KnowledgeSecurityEvent] = []
    eligible: list[KnowledgeCandidate] = []

    for candidate in catalog.candidates:
        if stage is KnowledgeStage.K1 and not _is_k1_compatible(candidate):
            exclusions[candidate.card_id] = "k1_execution_knowledge_forbidden"
            continue
        candidate_events = _candidate_security_events(candidate, context)
        if candidate_events:
            security_events.extend(candidate_events)
            exclusions[candidate.card_id] = "security_quarantined"
            continue
        reason = _hard_exclusion_reason(candidate, context, phase, terms)
        if reason is not None:
            exclusions[candidate.card_id] = reason
            continue
        eligible.append(candidate)

    deduplicated, duplicate_exclusions = _deduplicate(eligible)
    exclusions.update(duplicate_exclusions)
    conflicts = _conflict_records(deduplicated, policy)
    conflict_option_ids = {
        option_id
        for conflict in conflicts
        for option_id in conflict["option_card_ids"]
    }
    primary_pool = [
        candidate
        for candidate in deduplicated
        if candidate.decision_relation == "primary"
    ]
    anti_pattern_pool = [
        candidate
        for candidate in deduplicated
        if candidate.decision_relation == "anti_pattern"
    ]
    for candidate in deduplicated:
        if candidate.decision_relation == "conflict":
            exclusions.setdefault(
                candidate.card_id, "conflict_requires_director_decision"
            )

    active_budget = budget or RetrievalBudget(max_cards=policy.primary_card_limit)
    primary_limit = min(policy.primary_card_limit, active_budget.remaining)
    primary_candidates = tuple(
        sorted(primary_pool, key=_rank_key)[:primary_limit]
    )
    active_budget.consume(len(primary_candidates))
    anti_pattern_candidates = tuple(
        sorted(anti_pattern_pool, key=_rank_key)[:policy.anti_pattern_limit]
    )
    for candidate in primary_pool[primary_limit:]:
        exclusions.setdefault(candidate.card_id, "primary_budget_exhausted")
    for candidate in anti_pattern_pool[policy.anti_pattern_limit:]:
        exclusions.setdefault(candidate.card_id, "anti_pattern_budget_exhausted")

    selected: list[KnowledgeCandidate] = []
    selection_reasons: dict[str, str] = {}
    for reason, candidates in (
        ("canonical_primary", primary_candidates),
        ("canonical_anti_pattern", anti_pattern_candidates),
    ):
        for candidate in candidates:
            if candidate.card_id in conflict_option_ids:
                exclusions[candidate.card_id] = "conflict_requires_director_decision"
                continue
            try:
                _candidate_to_capsule(candidate)
            except ValueError as exc:
                exclusions[candidate.card_id] = str(exc)
                continue
            selected.append(candidate)
            selection_reasons[candidate.card_id] = reason

    selected_ids = {candidate.card_id for candidate in selected}
    for candidate in catalog.candidates:
        if candidate.card_id in selected_ids:
            exclusions.pop(candidate.card_id, None)
        else:
            exclusions.setdefault(candidate.card_id, "not_selected")

    return _MetadataSelection(
        query=query,
        phase=phase,
        selected_candidates=tuple(selected),
        primary_candidates=tuple(
            candidate
            for candidate in selected
            if selection_reasons[candidate.card_id] == "canonical_primary"
        ),
        anti_pattern_candidates=tuple(
            candidate
            for candidate in selected
            if selection_reasons[candidate.card_id] == "canonical_anti_pattern"
        ),
        conflicts=conflicts,
        exclusions=MappingProxyType(dict(exclusions)),
        security_events=tuple(security_events),
        selection_reasons=MappingProxyType(dict(selection_reasons)),
        stage_budgets=MappingProxyType(
            {
                "primary_limit": policy.primary_card_limit,
                "primary_used": len(primary_candidates),
                "anti_pattern_limit": policy.anti_pattern_limit,
                "anti_pattern_used": len(anti_pattern_candidates),
                "conflict_record_limit": policy.conflict_record_limit,
                "conflict_record_used": len(conflicts),
            }
        ),
    )


def retrieve_legacy_compatibility(
    diagnosis: DiagnosisArtifact | SceneDiagnosis,
    catalog: KnowledgeCatalog,
    context: RetrievalContext,
    *,
    policy: RetrievalPolicy,
    budget: RetrievalBudget | None,
    blocking: Mapping[str, Any] | None,
    k1_principles: Sequence[str],
) -> object:
    """Translate the sole selection result to a historical read-only receipt.

    This function deliberately creates no canonical ``KnowledgeSnapshot`` or
    ``ArtifactEnvelope``.  It exists only so archived callers can read their
    list-shaped result while all eligibility, ordering, budget, conflict and
    quarantine decisions remain in ``_select_metadata`` above.
    """

    from mode_p_vnext.knowledge_flow import (
        ConflictExposure,
        KnowledgePacket,
        KnowledgeRetrievalResult,
        KnowledgeSelectionReceipt,
    )

    if isinstance(diagnosis, DiagnosisArtifact):
        violations = validate_diagnosis_artifact(diagnosis)
        if violations:
            raise ValueError("invalid Phase-A diagnosis: " + "; ".join(violations))
        scene_diagnosis = diagnosis.diagnosis
        diagnosis_artifact: DiagnosisArtifact | None = diagnosis
    elif isinstance(diagnosis, SceneDiagnosis):
        if not diagnosis.scene_id:
            raise ValueError("scene_id is required for knowledge retrieval")
        scene_diagnosis = diagnosis
        diagnosis_artifact = None
    else:
        raise TypeError("diagnosis must be DiagnosisArtifact or SceneDiagnosis")

    stage = (
        KnowledgeStage.K2
        if blocking is not None and blocking.get("approved") is True
        else KnowledgeStage.K1
    )
    selection = _select_metadata(
        diagnosis=scene_diagnosis,
        catalog=catalog,
        context=context,
        stage=stage,
        policy=policy,
        k1_principles=(k1_principles if stage is KnowledgeStage.K1 else ()),
        budget=budget,
        diagnosis_artifact=diagnosis_artifact,
    )
    conflicts = tuple(
        ConflictExposure(
            conflict_id=str(record["conflict_id"]),
            option_card_ids=tuple(record["option_card_ids"]),
            director_question=str(record["director_question"]),
        )
        for record in selection.conflicts
    )
    packet = KnowledgePacket(
        phase=selection.phase,
        query=selection.query,
        k1_principles=(
            tuple(k1_principles) if stage is KnowledgeStage.K1 else ()
        ),
        primary_cards=selection.primary_candidates,
        anti_pattern_cards=selection.anti_pattern_candidates,
        conflict_exposures=conflicts,
        no_match=(
            not selection.primary_candidates
            and not selection.anti_pattern_candidates
            and not conflicts
        ),
    )
    receipt = KnowledgeSelectionReceipt(
        snapshot_id=f"legacy-selection:{scene_diagnosis.scene_id}:{selection.phase}",
        query={
            "scene_id": selection.query.scene_id,
            "dimension_questions": selection.query.dimension_questions,
            "model_risk_queries": selection.query.model_risk_queries,
            "user_constraint_queries": selection.query.user_constraint_queries,
        },
        selected_card_records=tuple(
            candidate.snapshot_record() for candidate in selection.selected_candidates
        ),
        conflict_records=tuple(conflict.to_dict() for conflict in conflicts),
        index_sha256=catalog.index_sha256,
        exclusions=dict(selection.exclusions),
        selection_reasons=dict(selection.selection_reasons),
        stage_budgets=dict(selection.stage_budgets),
        security_events=tuple(
            {
                "event_digest": _security_event_digest(event),
                "category": event.category,
                "reason_codes": tuple(event.reason_codes),
                "disposition": event.disposition,
            }
            for event in selection.security_events
        ),
    )
    return KnowledgeRetrievalResult(
        query=selection.query,
        packet=packet,
        selection_receipt=receipt,
        exclusions=dict(selection.exclusions),
        security_events=selection.security_events,
    )


def _retrieval_input_digest(
    *,
    diagnosis: SceneDiagnosis,
    context: RetrievalContext,
    stage: KnowledgeStage,
    catalog: KnowledgeCatalog,
    policy: RetrievalPolicy,
    blocking_commit_digest: str | None,
    blocking_commit_binding_digest: str | None,
    k1_principles: Sequence[str],
) -> str:
    return canonical_sha256(
        {
            "scene_id": diagnosis.scene_id,
            "diagnosis_sha256": canonical_sha256(diagnosis),
            "stage": stage.value,
            "catalog_index_sha256": catalog.index_sha256,
            "context": {
                "project_id": context.project_id,
                "model_id": context.model_id,
                "mode": context.mode,
                "aspect_ratio": context.aspect_ratio,
                "reference_mode": context.reference_mode,
                "as_of": context.as_of,
                "all_overrides": context.all_overrides,
            },
            "policy": {
                "primary_card_limit": policy.primary_card_limit,
                "conflict_record_limit": policy.conflict_record_limit,
                "anti_pattern_limit": policy.anti_pattern_limit,
                "retriever_version": policy.retriever_version,
                "ranking_version": policy.ranking_version,
            },
            "blocking_commit_digest": blocking_commit_digest,
            "blocking_commit_binding_digest": blocking_commit_binding_digest,
            "k1_principles": tuple(k1_principles),
        }
    )


def _envelope_source_refs(
    catalog: KnowledgeCatalog, records: Sequence[KnowledgeCandidateRecord]
) -> tuple[SourceRef, ...]:
    refs = {
        SourceRef(
            source_id=f"knowledge-catalog:{catalog.index_sha256[:24]}",
            digest=catalog.index_sha256,
        )
    }
    for record in records:
        refs.update(record.source_refs)
    return tuple(sorted(refs, key=lambda ref: (ref.source_id, ref.digest, ref.locator or "")))


def _verify_snapshot_envelope(snapshot: ArtifactEnvelope[KnowledgeSnapshot]) -> bool:
    if type(snapshot) is not ArtifactEnvelope:
        return False
    if snapshot.artifact_type is not ArtifactKind.KNOWLEDGE_SNAPSHOT:
        return False
    if snapshot.schema_version != _SCHEMA_VERSION:
        return False
    if type(snapshot.payload) is not KnowledgeSnapshot:
        return False
    try:
        ArtifactEnvelope(
            artifact_id=snapshot.artifact_id,
            artifact_type=snapshot.artifact_type,
            schema_version=snapshot.schema_version,
            payload=snapshot.payload,
            canonical_payload_sha256=snapshot.canonical_payload_sha256,
            producer_stage=snapshot.producer_stage,
            parent_artifact_ids=snapshot.parent_artifact_ids,
            source_provenance=snapshot.source_provenance,
            knowledge_snapshot_digest=snapshot.knowledge_snapshot_digest,
            created_at_utc=snapshot.created_at_utc,
        )
    except DomainValidationError:
        return False
    return (
        snapshot.producer_stage in {"knowledge_retriever:K1", "knowledge_retriever:K2"}
        and snapshot.knowledge_snapshot_digest is None
    )


class KnowledgeRetriever:
    """The single canonical K1/K2 knowledge service.

    Searching remains a metadata-only adapter.  The adapter cannot become a
    second knowledge authority: all Director-visible values and replayable
    state are instantiated from the frozen v3.0 domain module below.
    """

    def __init__(self, *, policy: RetrievalPolicy | None = None) -> None:
        self._policy = policy or RetrievalPolicy()

    def retrieve(
        self,
        *,
        diagnosis: SceneDiagnosis,
        catalog: KnowledgeCatalog,
        context: RetrievalContext,
        stage: KnowledgeStage,
        blocking_commit: VerifiedBlockingCommit | None = None,
        k1_principles: Sequence[str] = (),
    ) -> KnowledgeRetrieval:
        if not isinstance(stage, KnowledgeStage):
            raise TypeError("stage must be a KnowledgeStage")
        if stage is KnowledgeStage.K1:
            if blocking_commit is not None:
                raise ValueError("K1 cannot accept a BlockingCommit binding")
        else:
            if not isinstance(blocking_commit, VerifiedBlockingCommit):
                raise ValueError("K2 requires a verified BlockingCommit binding")
            if blocking_commit.scene_id != diagnosis.scene_id:
                raise ValueError("verified BlockingCommit scene_id must match diagnosis")
            if k1_principles:
                raise ValueError("K2 does not accept K1 principles")
        selection = _select_metadata(
            diagnosis=diagnosis,
            catalog=catalog,
            context=context,
            stage=stage,
            policy=self._policy,
            k1_principles=(k1_principles if stage is KnowledgeStage.K1 else ()),
        )

        records = tuple(_candidate_record(candidate) for candidate in catalog.candidates)
        records_by_id = {record.candidate_id: record for record in records}
        selected_candidates = selection.selected_candidates
        selected_capsules = tuple(
            _candidate_to_capsule(candidate) for candidate in selected_candidates
        )
        decision_view = KnowledgeDecisionView(
            scene_id=diagnosis.scene_id,
            stage=stage,
            entries=tuple(
                _entry_for_candidate(candidate, records_by_id[candidate.card_id])
                for candidate in selected_candidates
            ),
        )
        blocking_digest = blocking_commit.content_sha256 if blocking_commit else None
        blocking_binding_digest = (
            blocking_commit.binding_digest if blocking_commit else None
        )
        retrieval_input_digest = _retrieval_input_digest(
            diagnosis=diagnosis,
            context=context,
            stage=stage,
            catalog=catalog,
            policy=self._policy,
            blocking_commit_digest=blocking_digest,
            blocking_commit_binding_digest=blocking_binding_digest,
            k1_principles=k1_principles,
        )
        security_event_digests = _unique_text(
            tuple(
                _security_event_digest(event) for event in selection.security_events
            )
        )
        snapshot_id = "knowledge-snapshot:{}:{}:{}".format(
            diagnosis.scene_id,
            stage.value.lower(),
            retrieval_input_digest[:16],
        )
        snapshot_payload = KnowledgeSnapshot(
            snapshot_id=snapshot_id,
            scene_id=diagnosis.scene_id,
            stage=stage,
            decision_view=decision_view,
            selected_capsule_ids=decision_view.capsule_ids,
            exclusions=selection.exclusions,
            conflicts=selection.conflicts,
            catalog_index_sha256=catalog.index_sha256,
            retrieval_input_digest=retrieval_input_digest,
            blocking_commit_digest=blocking_digest,
            security_event_digests=security_event_digests,
            candidate_records=records,
            selection_reasons=selection.selection_reasons,
            catalog_index_abstract={
                "catalog_index": catalog.index_sha256,
                "candidate_count": str(len(catalog.candidates)),
                "catalog_version_digest": canonical_sha256(catalog.catalog_version),
            },
        )
        snapshot = ArtifactEnvelope.create(
            artifact_id=f"artifact:{snapshot_id}",
            artifact_type=ArtifactKind.KNOWLEDGE_SNAPSHOT,
            payload=snapshot_payload,
            producer_stage=f"knowledge_retriever:{stage.value}",
            parent_artifact_ids=(
                (blocking_commit.artifact_id,) if blocking_commit is not None else ()
            ),
            source_provenance=_envelope_source_refs(catalog, records),
            knowledge_snapshot_digest=None,
            created_at_utc=(
                f"{context.as_of}T00:00:00Z"
                if context.as_of
                else "1970-01-01T00:00:00Z"
            ),
            schema_version=_SCHEMA_VERSION,
        )
        return KnowledgeRetrieval(
            stage=stage,
            selected_capsules=selected_capsules,
            decision_view=decision_view,
            snapshot=snapshot,
            conflicts=snapshot_payload.conflicts,
            exclusions=MappingProxyType(dict(snapshot_payload.exclusions)),
            blocking_commit_digest=blocking_digest,
        )

    def replay(self, snapshot: ArtifactEnvelope[KnowledgeSnapshot]) -> KnowledgeReplay:
        if not _verify_snapshot_envelope(snapshot):
            raise ValueError("knowledge snapshot integrity check failed")
        payload = snapshot.payload
        return KnowledgeReplay(
            snapshot_id=payload.snapshot_id,
            decision_view=payload.decision_view,
            selected_card_ids=payload.selected_capsule_ids,
        )

    def promote(self, proposal: EvidenceVerifiedPromotion) -> ApprovedKnowledgeCapsule:
        """Promote only independently evidenced, human-approved knowledge."""

        if not isinstance(proposal, EvidenceVerifiedPromotion):
            raise TypeError("proposal must be an EvidenceVerifiedPromotion")
        try:
            EvidenceVerifiedPromotion(
                proposal_id=proposal.proposal_id,
                capsule=proposal.capsule,
                evidence_digests=proposal.evidence_digests,
                verifier_id=proposal.verifier_id,
                human_reviewer_id=proposal.human_reviewer_id,
                human_approved=proposal.human_approved,
                media_observation_digests=proposal.media_observation_digests,
                outcome_attribution_digest=proposal.outcome_attribution_digest,
                pattern_candidate_digest=proposal.pattern_candidate_digest,
                corroborating_case_digests=proposal.corroborating_case_digests,
                counterexample_digests=proposal.counterexample_digests,
                applicability_scope_digest=proposal.applicability_scope_digest,
            )
        except DomainValidationError as exc:
            raise KnowledgePromotionError(
                "structured experience promotion chain is invalid"
            ) from exc
        if not proposal.evidence_digests or not proposal.verifier_id.strip():
            raise KnowledgePromotionError("evidence verification is required before promotion")
        if not proposal.human_approved or not proposal.human_reviewer_id.strip():
            raise KnowledgePromotionError("human approval is required before promotion")
        return ApprovedKnowledgeCapsule(
            capsule=proposal.capsule,
            promotion_digest=canonical_sha256(
                {
                    "proposal_id": proposal.proposal_id,
                    "capsule_id": proposal.capsule.capsule_id,
                    "capsule_digest": canonical_sha256(proposal.capsule),
                    "evidence_digests": proposal.evidence_digests,
                    "verifier_id": proposal.verifier_id,
                    "human_reviewer_id": proposal.human_reviewer_id,
                    "human_approved": proposal.human_approved,
                    "media_observation_digests": proposal.media_observation_digests,
                    "outcome_attribution_digest": proposal.outcome_attribution_digest,
                    "pattern_candidate_digest": proposal.pattern_candidate_digest,
                    "corroborating_case_digests": proposal.corroborating_case_digests,
                    "counterexample_digests": proposal.counterexample_digests,
                    "applicability_scope_digest": proposal.applicability_scope_digest,
                }
            ),
        )
