"""Canonical K1/K2 knowledge boundary for MODE:P vNext.

The pre-existing retrieval implementation remains the metadata-only search
engine.  This module is the only service boundary that turns that search into
Director-visible knowledge: it separates K1 from K2, binds K2 to a verified
blocking commit, seals a replay packet, and refuses to promote raw results or
feedback without independent evidence and a human decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    SourceRef,
    canonical_sha256,
    require_sha256,
)
from mode_p_vnext.domain.knowledge import KnowledgeCapsuleV2
from mode_p_vnext.knowledge_flow import (
    KnowledgeCandidate,
    KnowledgeCatalog,
    RetrievalContext,
    RetrievalPolicy,
    retrieve_for_diagnosis,
)
from mode_p_vnext.schema.scene_diagnosis import SceneDiagnosis


class KnowledgeStage(str, Enum):
    """The two permitted Director knowledge stages."""

    K1 = "K1"
    K2 = "K2"


class KnowledgePromotionError(ValueError):
    """A candidate has not cleared the evidence-and-human promotion gate."""


def _frozen_mapping(value: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DomainValidationError(f"{field_name} must be a mapping")
    return MappingProxyType(dict(value))


def _non_empty_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True)
class VerifiedBlockingCommit:
    """Cryptographically bound evidence that permits the K2 transition.

    This deliberately is not the old ``{approved: true}`` convention.  The
    caller must supply a sealed blocking artifact digest and an independent
    verification digest; both are carried into the retrieval snapshot.
    """

    scene_id: str
    artifact_id: str
    content_sha256: str
    verification_digest: str

    def __post_init__(self) -> None:
        _non_empty_text(self.scene_id, "scene_id")
        _non_empty_text(self.artifact_id, "artifact_id")
        require_sha256(self.content_sha256, "content_sha256")
        require_sha256(self.verification_digest, "verification_digest")


@dataclass(frozen=True)
class EvidenceVerifiedPromotion:
    """A proposal from experience or media evidence, still outside K1/K2."""

    proposal_id: str
    capsule: KnowledgeCapsuleV2
    evidence_digests: tuple[str, ...]
    verifier_id: str
    human_reviewer_id: str
    human_approved: bool

    def __post_init__(self) -> None:
        _non_empty_text(self.proposal_id, "proposal_id")
        if not isinstance(self.capsule, KnowledgeCapsuleV2):
            raise DomainValidationError("capsule must be a KnowledgeCapsuleV2")
        digests = tuple(self.evidence_digests)
        if any(not isinstance(digest, str) for digest in digests):
            raise DomainValidationError("evidence_digests must contain SHA-256 strings")
        for digest in digests:
            require_sha256(digest, "evidence_digests entry")
        object.__setattr__(self, "evidence_digests", digests)


@dataclass(frozen=True)
class ApprovedKnowledgeCapsule:
    """An auditable result of the candidate -> verified -> human gate."""

    capsule: KnowledgeCapsuleV2
    promotion_digest: str


@dataclass(frozen=True)
class KnowledgeDecisionView:
    """The compact decision view; it contains neither raw source nor locator."""

    scene_id: str
    stage: KnowledgeStage
    capsule_ids: tuple[str, ...]
    claims_by_capsule: Mapping[str, tuple[str, ...]]
    source_digests: Mapping[str, tuple[str, ...]]
    entries_by_capsule: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _non_empty_text(self.scene_id, "scene_id")
        if not isinstance(self.stage, KnowledgeStage):
            raise DomainValidationError("stage must be a KnowledgeStage")
        ids = tuple(self.capsule_ids)
        if any(not isinstance(capsule_id, str) or not capsule_id.strip() for capsule_id in ids):
            raise DomainValidationError("capsule_ids must contain non-empty text")
        if len(ids) != len(set(ids)):
            raise DomainValidationError("capsule_ids must be unique")
        claims = {
            capsule_id: tuple(values)
            for capsule_id, values in self.claims_by_capsule.items()
        }
        digests = {
            capsule_id: tuple(values)
            for capsule_id, values in self.source_digests.items()
        }
        if set(claims) != set(ids) or set(digests) != set(ids):
            raise DomainValidationError("view mappings must exactly cover capsule_ids")
        entries = {capsule_id: dict(value) for capsule_id, value in self.entries_by_capsule.items()}
        if set(entries) != set(ids):
            raise DomainValidationError("view entries must exactly cover capsule_ids")
        for capsule_id in ids:
            if not claims[capsule_id] or any(not value.strip() for value in claims[capsule_id]):
                raise DomainValidationError("capsule claims must be non-empty")
            if not digests[capsule_id]:
                raise DomainValidationError("capsule source digests are required")
            for digest in digests[capsule_id]:
                require_sha256(digest, "source digest")
            entry = entries[capsule_id]
            required = {
                "capsule_id", "director_question", "applies_because",
                "execution_constraints", "expected_effect", "tradeoff",
                "anti_pattern", "source_digest",
            }
            if set(entry) != required or entry["capsule_id"] != capsule_id:
                raise DomainValidationError("knowledge decision entry has an invalid shape")
            if not isinstance(entry["director_question"], str) or not entry["director_question"].strip():
                raise DomainValidationError("knowledge decision entry requires a director_question")
            if not isinstance(entry["expected_effect"], str) or not entry["expected_effect"].strip():
                raise DomainValidationError("knowledge decision entry requires an expected_effect")
            for field_name in ("applies_because", "execution_constraints", "tradeoff"):
                if not isinstance(entry[field_name], tuple) or any(
                    not isinstance(value, str) or not value.strip() for value in entry[field_name]
                ):
                    raise DomainValidationError(f"knowledge decision entry {field_name} must be text")
            if not isinstance(entry["anti_pattern"], bool):
                raise DomainValidationError("knowledge decision entry anti_pattern must be boolean")
            require_sha256(entry["source_digest"], "knowledge decision entry source_digest")
        object.__setattr__(self, "capsule_ids", ids)
        object.__setattr__(self, "claims_by_capsule", _frozen_mapping(claims, "claims_by_capsule"))
        object.__setattr__(self, "source_digests", _frozen_mapping(digests, "source_digests"))
        object.__setattr__(
            self,
            "entries_by_capsule",
            _frozen_mapping(
                {capsule_id: MappingProxyType(entry) for capsule_id, entry in entries.items()},
                "entries_by_capsule",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return only prompt-safe, hash-addressed decision content."""
        return {
            "scene_id": self.scene_id,
            "stage": self.stage.value,
            "capsule_ids": list(self.capsule_ids),
            "claims_by_capsule": {
                capsule_id: list(self.claims_by_capsule[capsule_id])
                for capsule_id in self.capsule_ids
            },
            "source_digests": {
                capsule_id: list(self.source_digests[capsule_id])
                for capsule_id in self.capsule_ids
            },
            "capsules": [
                {
                    "capsule_id": capsule_id,
                    "director_question": self.entries_by_capsule[capsule_id]["director_question"],
                    "applies_because": list(self.entries_by_capsule[capsule_id]["applies_because"]),
                    "execution_constraints": list(
                        self.entries_by_capsule[capsule_id]["execution_constraints"]
                    ),
                    "expected_effect": self.entries_by_capsule[capsule_id]["expected_effect"],
                    "tradeoff": list(self.entries_by_capsule[capsule_id]["tradeoff"]),
                    "anti_pattern": self.entries_by_capsule[capsule_id]["anti_pattern"],
                    "source_digest": self.entries_by_capsule[capsule_id]["source_digest"],
                }
                for capsule_id in self.capsule_ids
            ],
        }


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """Sealed snapshot sufficient for replay without another catalog search."""

    snapshot_id: str
    scene_id: str
    stage: KnowledgeStage
    decision_view: KnowledgeDecisionView
    selected_card_ids: tuple[str, ...]
    exclusions: Mapping[str, str]
    conflicts: tuple[Mapping[str, Any], ...]
    catalog_index_sha256: str
    legacy_selection_digest: str
    blocking_commit_digest: str | None
    security_event_digests: tuple[str, ...]
    content_sha256: str = field(repr=False)

    def __post_init__(self) -> None:
        _non_empty_text(self.snapshot_id, "snapshot_id")
        _non_empty_text(self.scene_id, "scene_id")
        if not isinstance(self.stage, KnowledgeStage):
            raise DomainValidationError("stage must be a KnowledgeStage")
        if not isinstance(self.decision_view, KnowledgeDecisionView):
            raise DomainValidationError("decision_view must be a KnowledgeDecisionView")
        if self.decision_view.scene_id != self.scene_id or self.decision_view.stage is not self.stage:
            raise DomainValidationError("snapshot and decision view must have the same scene and stage")
        ids = tuple(self.selected_card_ids)
        if ids != self.decision_view.capsule_ids:
            raise DomainValidationError("selected_card_ids must match the decision view")
        if len(ids) != len(set(ids)):
            raise DomainValidationError("selected_card_ids must be unique")
        require_sha256(self.catalog_index_sha256, "catalog_index_sha256")
        require_sha256(self.legacy_selection_digest, "legacy_selection_digest")
        if self.blocking_commit_digest is not None:
            require_sha256(self.blocking_commit_digest, "blocking_commit_digest")
        event_digests = tuple(self.security_event_digests)
        for digest in event_digests:
            require_sha256(digest, "security_event_digest")
        object.__setattr__(self, "selected_card_ids", ids)
        object.__setattr__(self, "exclusions", _frozen_mapping(self.exclusions, "exclusions"))
        object.__setattr__(self, "conflicts", tuple(MappingProxyType(dict(item)) for item in self.conflicts))
        object.__setattr__(self, "security_event_digests", event_digests)
        require_sha256(self.content_sha256, "content_sha256")
        if self.content_sha256 != canonical_sha256(self._integrity_payload()):
            raise DomainValidationError("knowledge snapshot content_sha256 does not match its content")

    def _integrity_payload(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "scene_id": self.scene_id,
            "stage": self.stage.value,
            "decision_view": self.decision_view.to_dict(),
            "selected_card_ids": self.selected_card_ids,
            "exclusions": dict(sorted(self.exclusions.items())),
            "conflicts": [dict(item) for item in self.conflicts],
            "catalog_index_sha256": self.catalog_index_sha256,
            "legacy_selection_digest": self.legacy_selection_digest,
            "blocking_commit_digest": self.blocking_commit_digest,
            "security_event_digests": self.security_event_digests,
        }

    def verify_integrity(self) -> bool:
        return self.content_sha256 == canonical_sha256(self._integrity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self._integrity_payload()
        payload["content_sha256"] = self.content_sha256
        return payload


@dataclass(frozen=True)
class KnowledgeRetrieval:
    """The canonical result from the only K1/K2 entry point."""

    stage: KnowledgeStage
    decision_view: KnowledgeDecisionView
    snapshot: KnowledgeSnapshot
    conflicts: tuple[Mapping[str, Any], ...]
    exclusions: Mapping[str, str]
    blocking_commit_digest: str | None


@dataclass(frozen=True)
class KnowledgeReplay:
    """A replay reads a sealed snapshot and never invokes catalog retrieval."""

    snapshot_id: str
    decision_view: KnowledgeDecisionView
    selected_card_ids: tuple[str, ...]


def _candidate_to_capsule(candidate: KnowledgeCandidate) -> KnowledgeCapsuleV2:
    source_digest = candidate.card.source_hash
    try:
        require_sha256(source_digest, "candidate source_hash")
    except DomainValidationError:
        source_digest = canonical_sha256(candidate.snapshot_record())
    source_id = candidate.card.source_file or candidate.card_id
    return KnowledgeCapsuleV2(
        capsule_id=candidate.card_id,
        category=candidate.decision_domain,
        claims=(candidate.card.claim,),
        source_refs=(SourceRef(source_id=source_id, digest=source_digest),),
        confidence={
            "golden_evidence": "high",
            "render_evidence": "high",
            "cross_project": "medium",
            "user_opinion": "low",
        }.get(candidate.card.source_quality, "low"),
    )


def _view(scene_id: str, stage: KnowledgeStage, selected: Sequence[KnowledgeCandidate]) -> KnowledgeDecisionView:
    capsules = tuple(_candidate_to_capsule(candidate) for candidate in selected)
    candidates_by_id = {candidate.card_id: candidate for candidate in selected}
    return KnowledgeDecisionView(
        scene_id=scene_id,
        stage=stage,
        capsule_ids=tuple(capsule.capsule_id for capsule in capsules),
        claims_by_capsule={capsule.capsule_id: capsule.claims for capsule in capsules},
        source_digests={
            capsule.capsule_id: tuple(reference.digest for reference in capsule.source_refs)
            for capsule in capsules
        },
        entries_by_capsule={
            capsule.capsule_id: {
                "capsule_id": capsule.capsule_id,
                "director_question": candidates_by_id[capsule.capsule_id].director_question,
                "applies_because": tuple(
                    candidates_by_id[capsule.capsule_id].query_tags
                    or (candidates_by_id[capsule.capsule_id].decision_domain,)
                ),
                "execution_constraints": tuple(
                    candidates_by_id[capsule.capsule_id].positive_closure_requirements
                    + candidates_by_id[capsule.capsule_id].negative_routing_constraints
                    or candidates_by_id[capsule.capsule_id].must_not_decide
                ),
                "expected_effect": capsule.claims[0],
                "tradeoff": tuple(
                    tuple(candidates_by_id[capsule.capsule_id].card.counter_examples)
                    + tuple(candidates_by_id[capsule.capsule_id].non_applicability)
                ),
                "anti_pattern": candidates_by_id[capsule.capsule_id].decision_relation == "anti_pattern",
                "source_digest": capsule.source_refs[0].digest,
            }
            for capsule in capsules
        },
    )


def _security_event_digest(event: object) -> str:
    """Keep a verifiable event trace without exposing untrusted source IDs."""
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
    "camera", "shot", "lens", "framing", "composition", "editing", "edit", "timeline",
    "摄影", "镜头", "镜头", "机位", "构图", "剪辑", "时间线",
)


def _is_k1_compatible(candidate: KnowledgeCandidate) -> bool:
    """Keep execution knowledge out of K1 even when legacy metadata is mislabelled."""
    text = " ".join(
        (
            candidate.decision_domain,
            candidate.director_question,
            candidate.card.claim,
            *candidate.query_tags,
        )
    ).casefold()
    return not any(term in text for term in _K1_EXECUTION_TERMS)


class KnowledgeRetriever:
    """The single canonical K1/K2 knowledge service.

    It deliberately delegates searching to the existing metadata-only engine,
    then narrows the result into the v2.1 contract.  No conflict is resolved,
    no raw text is returned, and K2 cannot start from an unverified boolean.
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
            eligible = tuple(candidate for candidate in catalog.candidates if _is_k1_compatible(candidate))
            eligible_ids = {candidate.card_id for candidate in eligible}
            preflight_exclusions = {
                candidate.card_id: "k1_execution_knowledge_forbidden"
                for candidate in catalog.candidates
                if candidate.card_id not in eligible_ids
            }
            eligible_catalog = KnowledgeCatalog(eligible, catalog_version=catalog.catalog_version)

        legacy = retrieve_for_diagnosis(
            diagnosis=diagnosis,
            catalog=eligible_catalog,
            context=context,
            policy=self._policy,
            blocking=blocking,
            k1_principles=tuple(k1_principles) if stage is KnowledgeStage.K1 else (),
        )
        expected_phase = "problem" if stage is KnowledgeStage.K1 else "execution"
        if legacy.packet.phase != expected_phase:
            raise RuntimeError("knowledge stage boundary violation")
        selected = tuple(legacy.packet.primary_cards) + tuple(legacy.packet.anti_pattern_cards)
        decision_view = _view(diagnosis.scene_id, stage, selected)
        conflicts = tuple(item.to_dict() for item in legacy.packet.conflict_exposures)
        blocking_digest = blocking_commit.content_sha256 if blocking_commit else None
        exclusions = {**preflight_exclusions, **legacy.exclusions}
        snapshot_id = "KS2-{}-{}-{}".format(
            diagnosis.scene_id,
            stage.value.lower(),
            legacy.snapshot.content_sha256[:16],
        )
        snapshot_fields = {
            "snapshot_id": snapshot_id,
            "scene_id": diagnosis.scene_id,
            "stage": stage,
            "decision_view": decision_view,
            "selected_card_ids": decision_view.capsule_ids,
            "exclusions": exclusions,
            "conflicts": conflicts,
            "catalog_index_sha256": catalog.index_sha256,
            "legacy_selection_digest": legacy.snapshot.content_sha256,
            "blocking_commit_digest": blocking_digest,
            "security_event_digests": tuple(_security_event_digest(event) for event in legacy.security_events),
        }
        snapshot = KnowledgeSnapshot(
            **snapshot_fields,
            content_sha256=canonical_sha256(
                {
                    "snapshot_id": snapshot_id,
                    "scene_id": diagnosis.scene_id,
                    "stage": stage.value,
                    "decision_view": decision_view.to_dict(),
                    "selected_card_ids": decision_view.capsule_ids,
                    "exclusions": dict(sorted(exclusions.items())),
                    "conflicts": [dict(item) for item in conflicts],
                    "catalog_index_sha256": catalog.index_sha256,
                    "legacy_selection_digest": legacy.snapshot.content_sha256,
                    "blocking_commit_digest": blocking_digest,
                    "security_event_digests": tuple(
                        _security_event_digest(event) for event in legacy.security_events
                    ),
                }
            ),
        )
        return KnowledgeRetrieval(
            stage=stage,
            decision_view=decision_view,
            snapshot=snapshot,
            conflicts=conflicts,
            exclusions=MappingProxyType(exclusions),
            blocking_commit_digest=blocking_digest,
        )

    def replay(self, snapshot: KnowledgeSnapshot) -> KnowledgeReplay:
        if not isinstance(snapshot, KnowledgeSnapshot):
            raise TypeError("snapshot must be a KnowledgeSnapshot")
        if not snapshot.verify_integrity():
            raise ValueError("knowledge snapshot integrity check failed")
        return KnowledgeReplay(
            snapshot_id=snapshot.snapshot_id,
            decision_view=snapshot.decision_view,
            selected_card_ids=snapshot.selected_card_ids,
        )

    def promote(self, proposal: EvidenceVerifiedPromotion) -> ApprovedKnowledgeCapsule:
        """Promote only independently evidenced, human-approved knowledge."""
        if not isinstance(proposal, EvidenceVerifiedPromotion):
            raise TypeError("proposal must be an EvidenceVerifiedPromotion")
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
                    "evidence_digests": proposal.evidence_digests,
                    "verifier_id": proposal.verifier_id,
                    "human_reviewer_id": proposal.human_reviewer_id,
                }
            ),
        )
