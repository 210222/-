"""Fact records with source-level provenance."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import ClassVar

from .artifact import ArtifactKind, DomainValidationError, SourceRef


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("FactRegistry", "FactKind", "ScriptFact")


class FactKind(str, enum.Enum):
    SCRIPT = "script"
    CONTINUITY = "continuity"
    ASSET = "asset"
    USER_APPROVED = "user_approved"


@dataclass(frozen=True)
class ScriptFact:
    fact_id: str
    scene_id: str
    kind: FactKind
    statement: str
    source_ref: SourceRef

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.fact_id, self.scene_id, self.statement)
        ):
            raise DomainValidationError("fact_id, scene_id, and statement must be non-empty")
        if not isinstance(self.kind, FactKind) or not isinstance(self.source_ref, SourceRef):
            raise DomainValidationError("ScriptFact requires a FactKind and SourceRef")


@dataclass(frozen=True)
class FactRegistry:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.SCRIPT_FACT

    facts: tuple[ScriptFact, ...]

    def __post_init__(self) -> None:
        facts = tuple(self.facts)
        if not facts or not all(isinstance(fact, ScriptFact) for fact in facts):
            raise DomainValidationError("facts must contain at least one ScriptFact")
        identifiers = tuple(fact.fact_id for fact in facts)
        if len(identifiers) != len(set(identifiers)):
            raise DomainValidationError("fact_id must be unique in a FactRegistry")
        object.__setattr__(self, "facts", facts)

    def by_id(self, fact_id: str) -> ScriptFact:
        for fact in self.facts:
            if fact.fact_id == fact_id:
                return fact
        raise DomainValidationError(f"unknown fact_id: {fact_id}")
