"""Canonical K1/K2 knowledge schemas; retrieval behavior belongs to A3."""

from __future__ import annotations

import enum
from dataclasses import dataclass
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


@dataclass(frozen=True)
class KnowledgeCapsuleV2:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.KNOWLEDGE_CAPSULE

    capsule_id: str
    category: str
    claims: tuple[str, ...]
    source_refs: tuple[SourceRef, ...]
    confidence: str

    def __post_init__(self) -> None:
        _require_text(self.capsule_id, "capsule_id")
        _require_text(self.category, "category")
        object.__setattr__(
            self,
            "claims",
            _text_tuple(self.claims, "claims", require_items=True),
        )
        refs = tuple(self.source_refs)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError(
                "source_refs must contain SourceRef values"
            )
        if self.confidence not in {"high", "medium", "low"}:
            raise DomainValidationError(
                "confidence must be high, medium, or low"
            )
        object.__setattr__(self, "source_refs", refs)


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
        exclusions = freeze_mapping(self.exclusions, "exclusions")
        if not all(isinstance(value, str) and value.strip() for value in exclusions.values()):
            raise DomainValidationError(
                "exclusions must map capsule IDs to non-empty reasons"
            )
        conflicts = tuple(
            freeze_mapping(item, "conflict") for item in self.conflicts
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
        object.__setattr__(self, "selected_capsule_ids", selected)
        object.__setattr__(self, "exclusions", exclusions)
        object.__setattr__(self, "conflicts", conflicts)
        object.__setattr__(self, "security_event_digests", security)
