"""Canonical K1/K2 knowledge schemas; retrieval behavior belongs to A3."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar, Mapping

from .artifact import (
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    freeze_mapping,
    require_sha256,
)


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = (
    "KnowledgeCapsuleV2",
    "KnowledgeCandidateRecord",
    "KnowledgeCapabilityScope",
    "KnowledgeDecisionEntry",
    "KnowledgeDecisionView",
    "KnowledgeSnapshot",
    "KnowledgeStage",
)


class KnowledgeStage(str, enum.Enum):
    K1 = "K1"
    K2 = "K2"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")


def _text_tuple(
    value: tuple[str, ...], field_name: str, *, require_items: bool
) -> tuple[str, ...]:
    values = tuple(value)
    if (require_items and not values) or any(
        not isinstance(item, str) or not item.strip() for item in values
    ):
        raise DomainValidationError(
            f"{field_name} must contain only non-empty text"
        )
    if len(values) != len(set(values)):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    return values


def _source_ref_tuple(
    value: tuple[SourceRef, ...], field_name: str
) -> tuple[SourceRef, ...]:
    refs = tuple(value)
    if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
        raise DomainValidationError(
            f"{field_name} must contain SourceRef values"
        )
    if len(refs) != len(set(refs)):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    return refs


def _freeze_field_provenance(
    value: Mapping[str, tuple[SourceRef, ...]],
    field_name: str,
    *,
    source_refs: tuple[SourceRef, ...],
    required_fields: frozenset[str] = frozenset(),
) -> Mapping[str, tuple[SourceRef, ...]]:
    """Freeze the per-field source chain without retaining caller aliases."""

    provenance = freeze_mapping(value, field_name)
    if not provenance:
        raise DomainValidationError(f"{field_name} must not be empty")
    if not required_fields.issubset(provenance):
        missing = ", ".join(sorted(required_fields - set(provenance)))
        raise DomainValidationError(
            f"{field_name} is missing required fields: {missing}"
        )
    source_set = set(source_refs)
    for path, refs in provenance.items():
        _require_text(path, f"{field_name} key")
        if not isinstance(refs, tuple) or not refs:
            raise DomainValidationError(
                f"{field_name}[{path}] must contain SourceRef values"
            )
        if not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError(
                f"{field_name}[{path}] must contain SourceRef values"
            )
        if len(refs) != len(set(refs)):
            raise DomainValidationError(
                f"{field_name}[{path}] must not contain duplicates"
            )
        if not set(refs).issubset(source_set):
            raise DomainValidationError(
                f"{field_name}[{path}] must reference source_refs"
            )
    return provenance


def _freeze_text_mapping(
    value: Mapping[str, str], field_name: str, *, require_items: bool
) -> Mapping[str, str]:
    frozen = freeze_mapping(value, field_name)
    if require_items and not frozen:
        raise DomainValidationError(f"{field_name} must not be empty")
    if not all(
        isinstance(item, str) and item.strip() for item in frozen.values()
    ):
        raise DomainValidationError(
            f"{field_name} must map text keys to non-empty text"
        )
    return frozen


@dataclass(frozen=True)
class KnowledgeCapabilityScope:
    """Validity window for a platform capability, never a runtime prompt view."""

    valid_from: str
    valid_until: str
    target_models: tuple[str, ...]
    target_modes: tuple[str, ...]
    aspect_ratios: tuple[str, ...]
    source_digest: str

    def __post_init__(self) -> None:
        _require_text(self.valid_from, "valid_from")
        _require_text(self.valid_until, "valid_until")
        try:
            valid_from = date.fromisoformat(self.valid_from)
            valid_until = date.fromisoformat(self.valid_until)
        except ValueError as exc:
            raise DomainValidationError(
                "valid_from and valid_until must be ISO-8601 dates"
            ) from exc
        if valid_until < valid_from:
            raise DomainValidationError(
                "valid_until must be on or after valid_from"
            )
        for field_name in (
            "target_models",
            "target_modes",
            "aspect_ratios",
        ):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(
                    getattr(self, field_name),
                    field_name,
                    require_items=True,
                ),
            )
        require_sha256(self.source_digest, "source_digest")


@dataclass(frozen=True)
class KnowledgeCandidateRecord:
    """A replay-safe member of the retrieval candidate set.

    The record stores identifiers, immutable content evidence, exact source
    locators, and field provenance; raw source text remains outside the model
    view and is recoverable through the referenced source records.
    """

    candidate_id: str
    content_sha256: str
    source_refs: tuple[SourceRef, ...]
    field_provenance: Mapping[str, tuple[SourceRef, ...]]

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, "candidate_id")
        require_sha256(self.content_sha256, "content_sha256")
        refs = _source_ref_tuple(self.source_refs, "source_refs")
        provenance = _freeze_field_provenance(
            self.field_provenance,
            "field_provenance",
            source_refs=refs,
        )
        object.__setattr__(self, "source_refs", refs)
        object.__setattr__(self, "field_provenance", provenance)


@dataclass(frozen=True)
class KnowledgeCapsuleV2:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.KNOWLEDGE_CAPSULE

    capsule_id: str
    category: str
    claims: tuple[str, ...]
    source_summary: str
    source_refs: tuple[SourceRef, ...]
    field_provenance: Mapping[str, tuple[SourceRef, ...]]
    capability_scope: KnowledgeCapabilityScope | None
    confidence: str

    def __post_init__(self) -> None:
        _require_text(self.capsule_id, "capsule_id")
        _require_text(self.category, "category")
        object.__setattr__(
            self,
            "claims",
            _text_tuple(self.claims, "claims", require_items=True),
        )
        _require_text(self.source_summary, "source_summary")
        refs = _source_ref_tuple(self.source_refs, "source_refs")
        if (
            self.capability_scope is not None
            and not isinstance(self.capability_scope, KnowledgeCapabilityScope)
        ):
            raise DomainValidationError(
                "capability_scope must be a KnowledgeCapabilityScope or None"
            )
        if self.category == "platform_capability" and self.capability_scope is None:
            raise DomainValidationError(
                "platform_capability requires a capability_scope"
            )
        if (
            self.capability_scope is not None
            and self.capability_scope.source_digest
            not in {ref.digest for ref in refs}
        ):
            raise DomainValidationError(
                "capability_scope source_digest must reference source_refs"
            )
        required_provenance = frozenset({"claims", "source_summary"})
        if self.capability_scope is not None:
            required_provenance = required_provenance | frozenset(
                {"capability_scope"}
            )
        provenance = _freeze_field_provenance(
            self.field_provenance,
            "field_provenance",
            source_refs=refs,
            required_fields=required_provenance,
        )
        if self.confidence not in {"high", "medium", "low"}:
            raise DomainValidationError(
                "confidence must be high, medium, or low"
        )
        object.__setattr__(self, "source_refs", refs)
        object.__setattr__(self, "field_provenance", provenance)


@dataclass(frozen=True)
class KnowledgeDecisionEntry:
    """The compact, prompt-safe capsule view declared by architecture §7.2."""

    capsule_id: str
    director_question: str
    applies_because: tuple[str, ...]
    execution_constraints: tuple[str, ...]
    expected_effect: str
    tradeoff: tuple[str, ...]
    anti_pattern: bool
    source_digest: str

    def __post_init__(self) -> None:
        _require_text(self.capsule_id, "capsule_id")
        _require_text(self.director_question, "director_question")
        _require_text(self.expected_effect, "expected_effect")
        for field_name in (
            "applies_because",
            "execution_constraints",
            "tradeoff",
        ):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(
                    getattr(self, field_name),
                    field_name,
                    require_items=False,
                ),
            )
        if not isinstance(self.anti_pattern, bool):
            raise DomainValidationError("anti_pattern must be boolean")
        require_sha256(self.source_digest, "source_digest")


@dataclass(frozen=True)
class KnowledgeDecisionView:
    scene_id: str
    stage: KnowledgeStage
    entries: tuple[KnowledgeDecisionEntry, ...]

    def __post_init__(self) -> None:
        _require_text(self.scene_id, "scene_id")
        if not isinstance(self.stage, KnowledgeStage):
            raise DomainValidationError("stage must be K1 or K2")
        entries = tuple(self.entries)
        if not all(
            isinstance(entry, KnowledgeDecisionEntry) for entry in entries
        ):
            raise DomainValidationError(
                "entries must contain KnowledgeDecisionEntry values"
            )
        identifiers = tuple(entry.capsule_id for entry in entries)
        if len(identifiers) != len(set(identifiers)):
            raise DomainValidationError(
                "KnowledgeDecisionView capsule IDs must be unique"
            )
        object.__setattr__(self, "entries", entries)

    @property
    def capsule_ids(self) -> tuple[str, ...]:
        return tuple(entry.capsule_id for entry in self.entries)


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """A sealed replay record; ArtifactEnvelope supplies its content hash."""

    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.KNOWLEDGE_SNAPSHOT

    snapshot_id: str
    scene_id: str
    stage: KnowledgeStage
    decision_view: KnowledgeDecisionView
    selected_capsule_ids: tuple[str, ...]
    exclusions: Mapping[str, str]
    conflicts: tuple[Mapping[str, Any], ...]
    catalog_index_sha256: str
    retrieval_input_digest: str
    blocking_commit_digest: str | None
    security_event_digests: tuple[str, ...]
    candidate_records: tuple[KnowledgeCandidateRecord, ...]
    selection_reasons: Mapping[str, str]
    catalog_index_abstract: Mapping[str, str]

    def __post_init__(self) -> None:
        _require_text(self.snapshot_id, "snapshot_id")
        _require_text(self.scene_id, "scene_id")
        if not isinstance(self.stage, KnowledgeStage):
            raise DomainValidationError("stage must be K1 or K2")
        if not isinstance(self.decision_view, KnowledgeDecisionView):
            raise DomainValidationError(
                "decision_view must be a KnowledgeDecisionView"
            )
        if (
            self.decision_view.scene_id != self.scene_id
            or self.decision_view.stage is not self.stage
        ):
            raise DomainValidationError(
                "snapshot and decision view must share scene and stage"
            )
        selected = _text_tuple(
            self.selected_capsule_ids,
            "selected_capsule_ids",
            require_items=False,
        )
        if selected != self.decision_view.capsule_ids:
            raise DomainValidationError(
                "selected_capsule_ids must match the decision view"
            )
        exclusions = _freeze_text_mapping(
            self.exclusions, "exclusions", require_items=False
        )
        conflicts = tuple(
            freeze_mapping(item, "conflict") for item in self.conflicts
        )
        candidates = tuple(self.candidate_records)
        if not all(
            isinstance(record, KnowledgeCandidateRecord) for record in candidates
        ):
            raise DomainValidationError(
                "candidate_records must contain KnowledgeCandidateRecord values"
            )
        candidate_ids = tuple(record.candidate_id for record in candidates)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise DomainValidationError(
                "candidate_records candidate IDs must be unique"
            )
        selected_set = set(selected)
        excluded_set = set(exclusions)
        if selected_set & excluded_set:
            raise DomainValidationError(
                "selected capsule IDs cannot also be excluded"
            )
        if set(candidate_ids) != selected_set | excluded_set:
            raise DomainValidationError(
                "candidate_records must account for every selected or excluded candidate"
            )
        selection_reasons = _freeze_text_mapping(
            self.selection_reasons,
            "selection_reasons",
            require_items=False,
        )
        if set(selection_reasons) != selected_set:
            raise DomainValidationError(
                "selection_reasons must cover exactly the selected capsule IDs"
            )
        records_by_id = {record.candidate_id: record for record in candidates}
        for entry in self.decision_view.entries:
            if entry.source_digest != records_by_id[entry.capsule_id].content_sha256:
                raise DomainValidationError(
                    "decision view source_digest must match its candidate record"
                )
        index_abstract = _freeze_text_mapping(
            self.catalog_index_abstract,
            "catalog_index_abstract",
            require_items=True,
        )
        require_sha256(self.catalog_index_sha256, "catalog_index_sha256")
        require_sha256(self.retrieval_input_digest, "retrieval_input_digest")
        if self.blocking_commit_digest is not None:
            require_sha256(
                self.blocking_commit_digest, "blocking_commit_digest"
            )
        if self.stage is KnowledgeStage.K1 and self.blocking_commit_digest is not None:
            raise DomainValidationError(
                "K1 cannot depend on a BlockingCommit"
            )
        if self.stage is KnowledgeStage.K2 and self.blocking_commit_digest is None:
            raise DomainValidationError(
                "K2 requires a verified BlockingCommit digest"
            )
        security = tuple(self.security_event_digests)
        for digest in security:
            require_sha256(digest, "security_event_digest")
        if len(security) != len(set(security)):
            raise DomainValidationError(
                "security_event_digests must not contain duplicates"
            )
        object.__setattr__(self, "selected_capsule_ids", selected)
        object.__setattr__(self, "exclusions", exclusions)
        object.__setattr__(self, "conflicts", conflicts)
        object.__setattr__(self, "security_event_digests", security)
        object.__setattr__(self, "candidate_records", candidates)
        object.__setattr__(self, "selection_reasons", selection_reasons)
        object.__setattr__(self, "catalog_index_abstract", index_abstract)
