"""Provenanced knowledge schemas; retrieval behavior belongs to A3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .artifact import DomainValidationError, SourceRef, freeze_mapping


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("KnowledgeCapsuleV2", "KnowledgeDecisionView", "KnowledgeSnapshot")


def _text_tuple(value: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    values = tuple(value)
    if not values or any(not isinstance(item, str) or not item.strip() for item in values):
        raise DomainValidationError(f"{field_name} must contain non-empty text")
    return values


@dataclass(frozen=True)
class KnowledgeCapsuleV2:
    capsule_id: str
    category: str
    claims: tuple[str, ...]
    source_refs: tuple[SourceRef, ...]
    confidence: str

    def __post_init__(self) -> None:
        if not self.capsule_id.strip() or not self.category.strip():
            raise DomainValidationError("capsule_id and category must be non-empty")
        object.__setattr__(self, "claims", _text_tuple(self.claims, "claims"))
        refs = tuple(self.source_refs)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError("source_refs must contain SourceRef values")
        if self.confidence not in {"high", "medium", "low"}:
            raise DomainValidationError("confidence must be high, medium, or low")
        object.__setattr__(self, "source_refs", refs)


@dataclass(frozen=True)
class KnowledgeDecisionView:
    scene_id: str
    capsule_ids: tuple[str, ...]
    claims_by_capsule: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if not self.scene_id.strip():
            raise DomainValidationError("scene_id must be non-empty")
        object.__setattr__(self, "capsule_ids", _text_tuple(self.capsule_ids, "capsule_ids"))
        object.__setattr__(self, "claims_by_capsule", freeze_mapping(self.claims_by_capsule, "claims_by_capsule"))


@dataclass(frozen=True)
class KnowledgeSnapshot:
    snapshot_id: str
    scene_id: str
    capsule_digests: Mapping[str, str]
    decision_view: KnowledgeDecisionView

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip() or not self.scene_id.strip():
            raise DomainValidationError("snapshot_id and scene_id must be non-empty")
        if not isinstance(self.decision_view, KnowledgeDecisionView):
            raise DomainValidationError("decision_view must be a KnowledgeDecisionView")
        object.__setattr__(self, "capsule_digests", freeze_mapping(self.capsule_digests, "capsule_digests"))
