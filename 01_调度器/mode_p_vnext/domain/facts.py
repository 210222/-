"""Fact records with source-level provenance."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import ClassVar

from .artifact import ArtifactKind, DomainValidationError, SourceRef, require_sha256


DOMAIN_SCHEMA_VERSION = "2.2"
CANONICAL_DOMAIN_TYPES = (
    "FactRegistry",
    "FactKind",
    "FactSemantic",
    "ScriptFact",
)


class FactKind(str, enum.Enum):
    SCRIPT = "script"
    CONTINUITY = "continuity"
    ASSET = "asset"
    USER_APPROVED = "user_approved"


class FactSemantic(str, enum.Enum):
    """What a fact means, independent of where its authority came from."""

    NARRATIVE = "narrative"
    CHARACTER = "character"
    WARDROBE = "wardrobe"
    PROP = "prop"
    SETTING = "setting"
    DIALOGUE = "dialogue"
    CONTINUITY = "continuity"
    ASSET = "asset"


_SUBJECT_REQUIRED_SEMANTICS = frozenset(
    {
        FactSemantic.CHARACTER,
        FactSemantic.WARDROBE,
        FactSemantic.PROP,
        FactSemantic.SETTING,
        FactSemantic.DIALOGUE,
        FactSemantic.ASSET,
    }
)


@dataclass(frozen=True)
class ScriptFact:
    fact_id: str
    scene_id: str
    kind: FactKind
    semantic: FactSemantic
    statement: str
    source_ref: SourceRef
    source_start: int
    source_end: int
    ordinal: int
    subject_id: str | None = None
    spoken_text: str | None = None

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.fact_id, self.scene_id, self.statement)
        ):
            raise DomainValidationError("fact_id, scene_id, and statement must be non-empty")
        if not isinstance(self.kind, FactKind):
            raise DomainValidationError("ScriptFact requires a FactKind")
        if not isinstance(self.semantic, FactSemantic):
            raise DomainValidationError("ScriptFact requires a FactSemantic")
        if not isinstance(self.source_ref, SourceRef):
            raise DomainValidationError("ScriptFact requires a SourceRef")
        if (
            isinstance(self.source_start, bool)
            or not isinstance(self.source_start, int)
            or self.source_start < 0
        ):
            raise DomainValidationError("source_start must be a non-negative integer")
        if (
            isinstance(self.source_end, bool)
            or not isinstance(self.source_end, int)
            or self.source_end <= self.source_start
        ):
            raise DomainValidationError("source span must be a non-empty half-open range")
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 0:
            raise DomainValidationError("ordinal must be a non-negative integer")
        identity_parts = self.fact_id.split(":")
        if (
            len(identity_parts) != 3
            or identity_parts[0] != ArtifactKind.SCRIPT_FACT.value
            or identity_parts[1] != f"{self.ordinal:04d}"
        ):
            raise DomainValidationError(
                "fact_id must be an opaque local ScriptFact identity matching ordinal"
            )
        try:
            require_sha256(identity_parts[2], "fact_id digest")
        except DomainValidationError as exc:
            raise DomainValidationError(
                "fact_id must be an opaque local ScriptFact identity"
            ) from exc

        if self.subject_id is not None and (
            not isinstance(self.subject_id, str) or not self.subject_id.strip()
        ):
            raise DomainValidationError("subject_id must be non-empty when supplied")
        if self.spoken_text is not None and (
            not isinstance(self.spoken_text, str) or not self.spoken_text.strip()
        ):
            raise DomainValidationError("spoken_text must be non-empty when supplied")
        if self.semantic in _SUBJECT_REQUIRED_SEMANTICS and self.subject_id is None:
            raise DomainValidationError(
                f"subject_id is required for {self.semantic.value} facts"
            )
        if self.semantic is FactSemantic.DIALOGUE:
            if self.spoken_text is None:
                raise DomainValidationError("spoken_text is required for dialogue facts")
        elif self.spoken_text is not None:
            raise DomainValidationError("spoken_text is only valid for dialogue facts")

    def validate_against_normalized_source(self, normalized_source: str) -> str:
        """Fail closed unless the declared span directly supports this fact.

        The normalized source is supplied by the local ingest/compatibility
        assembler.  It is intentionally not persisted inside every fact.
        """

        if not isinstance(normalized_source, str):
            raise DomainValidationError("normalized_source must be text")
        if normalized_source.startswith("\ufeff") or "\r" in normalized_source:
            raise DomainValidationError(
                "normalized_source must have BOM removed and LF line endings"
            )
        if self.source_end > len(normalized_source):
            raise DomainValidationError("source_end exceeds normalized_source length")
        supporting_text = normalized_source[self.source_start : self.source_end]
        if not supporting_text.strip():
            raise DomainValidationError("source span must contain non-whitespace text")
        if self.statement.strip() not in supporting_text:
            raise DomainValidationError("statement is not directly supported by source span")
        if self.semantic is FactSemantic.DIALOGUE and self.spoken_text not in supporting_text:
            raise DomainValidationError("spoken_text is not present in source span")
        return supporting_text


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
        last_ordinal_by_source: dict[tuple[str, str], int] = {}
        for fact in facts:
            source_key = (fact.source_ref.source_id, fact.source_ref.digest)
            previous = last_ordinal_by_source.get(source_key)
            if previous is not None and fact.ordinal <= previous:
                raise DomainValidationError(
                    "fact ordinal must be strictly increasing and unique per source document"
                )
            last_ordinal_by_source[source_key] = fact.ordinal
        object.__setattr__(self, "facts", facts)

    def by_id(self, fact_id: str) -> ScriptFact:
        for fact in self.facts:
            if fact.fact_id == fact_id:
                return fact
        raise DomainValidationError(f"unknown fact_id: {fact_id}")

    def by_semantic(self, semantic: FactSemantic) -> tuple[ScriptFact, ...]:
        if not isinstance(semantic, FactSemantic):
            raise DomainValidationError("semantic must be a FactSemantic")
        return tuple(fact for fact in self.facts if fact.semantic is semantic)
