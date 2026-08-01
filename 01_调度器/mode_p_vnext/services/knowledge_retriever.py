"""Canonical K1/K2 knowledge boundary for MODE:P vNext.

The legacy retrieval module is intentionally used only as a metadata search
adapter.  This service is the sole K1/K2 boundary: it converts candidates into
the v2.2 domain types, seals the complete selection in an ArtifactEnvelope,
and never lets raw source text or retriever-side conflict resolution enter the
Director view.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from mode_p_vnext.domain.artifact import (
    DOMAIN_SCHEMA_VERSION,
    ArtifactEnvelope,
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    ValidationStatus,
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
from mode_p_vnext.knowledge_flow import (
    KnowledgeCandidate,
    KnowledgeCatalog,
    RetrievalContext,
    RetrievalPolicy,
    retrieve_for_diagnosis,
)
from mode_p_vnext.schema.scene_diagnosis import SceneDiagnosis


_SCHEMA_VERSION = DOMAIN_SCHEMA_VERSION
_PROGRAM_VERSION = f"mode-p-vnext-{_SCHEMA_VERSION}"


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
        if evidence and not chain.issubset(evidence):
            raise DomainValidationError(
                "evidence_digests must bind every structured experience link"
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
    if snapshot.artifact_kind is not ArtifactKind.KNOWLEDGE_SNAPSHOT:
        return False
    if (
        snapshot.schema_version != _SCHEMA_VERSION
        or snapshot.program_version != _PROGRAM_VERSION
    ):
        return False
    if type(snapshot.payload) is not KnowledgeSnapshot:
        return False
    try:
        expected = ArtifactEnvelope.content_digest_for(
            artifact_kind=snapshot.artifact_kind,
            schema_version=snapshot.schema_version,
            program_version=snapshot.program_version,
            payload=snapshot.payload,
            source_refs=snapshot.source_refs,
            dependency_digests=snapshot.dependency_digests,
        )
    except DomainValidationError:
        return False
    return snapshot.content_sha256 == expected


class KnowledgeRetriever:
    """The single canonical K1/K2 knowledge service.

    Searching remains a metadata-only adapter.  The adapter cannot become a
    second knowledge authority: all Director-visible values and replayable
    state are instantiated from the v2.2 domain module below.
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
            blocking: Mapping[str, Any] | None = None
        else:
            if not isinstance(blocking_commit, VerifiedBlockingCommit):
                raise ValueError("K2 requires a verified BlockingCommit binding")
            if blocking_commit.scene_id != diagnosis.scene_id:
                raise ValueError("verified BlockingCommit scene_id must match diagnosis")
            if k1_principles:
                raise ValueError("K2 does not accept K1 principles")
            blocking = {
                "approved": True,
                "artifact_id": blocking_commit.artifact_id,
                "content_sha256": blocking_commit.content_sha256,
                "verification_digest": blocking_commit.verification_digest,
            }

        preflight_exclusions: dict[str, str] = {}
        eligible_catalog = catalog
        if stage is KnowledgeStage.K1:
            eligible = tuple(
                candidate
                for candidate in catalog.candidates
                if _is_k1_compatible(candidate)
            )
            eligible_ids = {candidate.card_id for candidate in eligible}
            preflight_exclusions = {
                candidate.card_id: "k1_execution_knowledge_forbidden"
                for candidate in catalog.candidates
                if candidate.card_id not in eligible_ids
            }
            eligible_catalog = KnowledgeCatalog(
                eligible, catalog_version=catalog.catalog_version
            )

        legacy = retrieve_for_diagnosis(
            diagnosis=diagnosis,
            catalog=eligible_catalog,
            context=context,
            policy=self._policy,
            blocking=blocking,
            k1_principles=tuple(k1_principles)
            if stage is KnowledgeStage.K1
            else (),
        )
        expected_phase = "problem" if stage is KnowledgeStage.K1 else "execution"
        if legacy.packet.phase != expected_phase:
            raise RuntimeError("knowledge stage boundary violation")

        records = tuple(_candidate_record(candidate) for candidate in catalog.candidates)
        records_by_id = {record.candidate_id: record for record in records}
        candidates_by_id = {candidate.card_id: candidate for candidate in catalog.candidates}
        conflicts = tuple(item.to_dict() for item in legacy.packet.conflict_exposures)
        conflict_option_ids = {
            option_id
            for conflict in conflicts
            for option_id in conflict["option_card_ids"]
        }
        exclusions: dict[str, str] = {
            **preflight_exclusions,
            **dict(legacy.exclusions),
        }

        selected_candidates: list[KnowledgeCandidate] = []
        selection_reasons: dict[str, str] = {}
        for relation, candidates in (
            ("legacy_primary", legacy.packet.primary_cards),
            ("legacy_anti_pattern", legacy.packet.anti_pattern_cards),
        ):
            for candidate in candidates:
                candidate_id = candidate.card_id
                if candidate_id in selection_reasons:
                    continue
                if candidate_id in conflict_option_ids:
                    exclusions[candidate_id] = "conflict_requires_director_decision"
                    continue
                if candidate.raw_evidence is not None:
                    exclusions[candidate_id] = "security_quarantined"
                    continue
                try:
                    _candidate_to_capsule(candidate)
                except ValueError as exc:
                    exclusions[candidate_id] = str(exc)
                    continue
                selected_candidates.append(candidate)
                selection_reasons[candidate_id] = relation

        selected_ids = {candidate.card_id for candidate in selected_candidates}
        for candidate in catalog.candidates:
            if candidate.card_id in selected_ids:
                exclusions.pop(candidate.card_id, None)
            else:
                exclusions.setdefault(candidate.card_id, "not_selected")

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
            tuple(_security_event_digest(event) for event in legacy.security_events)
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
            exclusions=exclusions,
            conflicts=conflicts,
            catalog_index_sha256=catalog.index_sha256,
            retrieval_input_digest=retrieval_input_digest,
            blocking_commit_digest=blocking_digest,
            security_event_digests=security_event_digests,
            candidate_records=records,
            selection_reasons=selection_reasons,
            catalog_index_abstract={
                "catalog_index": catalog.index_sha256,
                "candidate_count": str(len(catalog.candidates)),
                "catalog_version_digest": canonical_sha256(catalog.catalog_version),
            },
        )
        dependencies = {
            "catalog_index": catalog.index_sha256,
            "retrieval_input": retrieval_input_digest,
            "selection_receipt": legacy.selection_receipt.content_sha256,
        }
        if blocking_digest is not None:
            dependencies["blocking_commit"] = blocking_digest
            dependencies["blocking_commit_binding"] = blocking_binding_digest
        snapshot = ArtifactEnvelope.create(
            artifact_id=f"artifact:{snapshot_id}",
            artifact_kind=ArtifactKind.KNOWLEDGE_SNAPSHOT,
            schema_version=_SCHEMA_VERSION,
            program_version=_PROGRAM_VERSION,
            payload=snapshot_payload,
            source_refs=_envelope_source_refs(catalog, records),
            dependency_digests=dependencies,
            created_at=(f"{context.as_of}T00:00:00Z" if context.as_of else "1970-01-01T00:00:00Z"),
            validation_status=ValidationStatus.DRAFT,
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
