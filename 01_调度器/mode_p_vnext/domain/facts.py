"""Canonical v3.0 source, extraction-draft, and assembled fact contracts."""

from __future__ import annotations

import enum
import hashlib
import unicodedata
from dataclasses import dataclass
from typing import ClassVar

from .artifact import (
    DOMAIN_SCHEMA_VERSION,
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    require_sha256,
)


CANONICAL_DOMAIN_TYPES = (
    "FactConfidence",
    "FactExtractionDraft",
    "FactKind",
    "FactQualifiers",
    "FactRegistry",
    "FactSemantic",
    "NormalizedSource",
    "ScriptFact",
    "SourcePartition",
    "SourceSpan",
)
OPAQUE_HANDLE_PREFIX = "fh:"
OPAQUE_ID_PREFIX = "id:"


class FactKind(str, enum.Enum):
    SCRIPT = "script"
    CONTINUITY = "continuity"
    ASSET = "asset"
    USER_APPROVED = "user_approved"


class FactSemantic(str, enum.Enum):
    """Meaning of a fact, independent of its source authority."""

    NARRATIVE = "narrative"
    CHARACTER = "character"
    WARDROBE = "wardrobe"
    PROP = "prop"
    SETTING = "setting"
    DIALOGUE = "dialogue"
    CONTINUITY = "continuity"
    ASSET = "asset"


class FactConfidence(str, enum.Enum):
    EXPLICIT = "explicit"
    SUPPORTED = "supported"
    UNCERTAIN = "uncertain"


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


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")


def normalized_text_sha256(value: str) -> str:
    if not isinstance(value, str):
        raise DomainValidationError("normalized source must be text")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_opaque_handle(value: str, field_name: str = "fact_handle") -> None:
    if not isinstance(value, str) or not value.startswith(OPAQUE_HANDLE_PREFIX):
        raise DomainValidationError(f"{field_name} must be an opaque local handle")
    require_sha256(value[len(OPAQUE_HANDLE_PREFIX) :], f"{field_name} digest")


def require_opaque_id(value: str, field_name: str = "fact_id") -> None:
    if not isinstance(value, str) or not value.startswith(OPAQUE_ID_PREFIX):
        raise DomainValidationError(f"{field_name} must be an opaque local ID")
    require_sha256(value[len(OPAQUE_ID_PREFIX) :], f"{field_name} digest")


@dataclass(frozen=True)
class SourcePartition:
    episode_id: str
    scene_id: str
    source_start: int
    source_end: int

    def __post_init__(self) -> None:
        _require_text(self.episode_id, "episode_id")
        _require_text(self.scene_id, "scene_id")
        if (
            isinstance(self.source_start, bool)
            or not isinstance(self.source_start, int)
            or self.source_start < 0
        ):
            raise DomainValidationError("source_start must be a non-negative character index")
        if (
            isinstance(self.source_end, bool)
            or not isinstance(self.source_end, int)
            or self.source_end <= self.source_start
        ):
            raise DomainValidationError("source partition must be a non-empty half-open range")

    def contains(self, start: int, end: int) -> bool:
        return self.source_start <= start < end <= self.source_end


@dataclass(frozen=True)
class NormalizedSource:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.NORMALIZED_SOURCE

    source_ref: SourceRef
    normalized_text: str
    encoding: str
    character_count: int
    line_start_offsets: tuple[int, ...]
    partitions: tuple[SourcePartition, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, SourceRef):
            raise DomainValidationError("source_ref must be a SourceRef")
        _require_text(self.normalized_text, "normalized_text")
        _require_text(self.encoding, "encoding")
        if self.normalized_text.startswith("\ufeff") or "\r" in self.normalized_text:
            raise DomainValidationError("normalized_text must remove BOM and use LF line endings")
        if "\x00" in self.normalized_text or any(
            0xD800 <= ord(char) <= 0xDFFF for char in self.normalized_text
        ):
            raise DomainValidationError("normalized_text contains forbidden code points")
        if unicodedata.normalize("NFC", self.normalized_text) != self.normalized_text:
            raise DomainValidationError("normalized_text must use Unicode NFC")
        if self.character_count != len(self.normalized_text):
            raise DomainValidationError("character_count must match normalized_text")
        if self.source_ref.digest != normalized_text_sha256(self.normalized_text):
            raise DomainValidationError("source digest must hash normalized UTF-8 text")
        expected_lines = (0,) + tuple(
            index + 1
            for index, character in enumerate(self.normalized_text)
            if character == "\n"
        )
        if tuple(self.line_start_offsets) != expected_lines:
            raise DomainValidationError("line_start_offsets must exactly index normalized_text")
        partitions = tuple(self.partitions)
        if not partitions or not all(isinstance(item, SourcePartition) for item in partitions):
            raise DomainValidationError("partitions must contain SourcePartition values")
        if partitions[0].source_start != 0 or partitions[-1].source_end != self.character_count:
            raise DomainValidationError("partitions must cover the complete normalized source")
        for left, right in zip(partitions, partitions[1:]):
            if left.source_end != right.source_start:
                raise DomainValidationError("source partitions must be ordered, adjacent, and gap-free")
        keys = tuple((item.episode_id, item.scene_id) for item in partitions)
        if len(keys) != len(set(keys)):
            raise DomainValidationError("episode/scene source partitions must be unique")
        object.__setattr__(self, "line_start_offsets", tuple(self.line_start_offsets))
        object.__setattr__(self, "partitions", partitions)

    def partition_for(self, episode_id: str, scene_id: str) -> SourcePartition:
        matches = tuple(
            item
            for item in self.partitions
            if item.episode_id == episode_id and item.scene_id == scene_id
        )
        if len(matches) != 1:
            raise DomainValidationError("fact qualifiers do not resolve to one source partition")
        return matches[0]

    def text_for(self, start: int, end: int) -> str:
        if (
            isinstance(start, bool)
            or not isinstance(start, int)
            or isinstance(end, bool)
            or not isinstance(end, int)
            or not 0 <= start < end <= self.character_count
        ):
            raise DomainValidationError("source span is outside normalized_text")
        return self.normalized_text[start:end]


@dataclass(frozen=True)
class FactQualifiers:
    episode_id: str
    scene_id: str
    subject_label: str | None = None
    spoken_text: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.episode_id, "episode_id")
        _require_text(self.scene_id, "scene_id")
        for field_name in ("subject_label", "spoken_text"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)


@dataclass(frozen=True)
class FactExtractionDraft:
    """I0 model output. It intentionally has no ID, handle, ordinal, hash, or tick."""

    semantic: FactSemantic
    statement: str
    source_start: int
    source_end: int
    confidence: FactConfidence
    qualifiers: FactQualifiers

    def __post_init__(self) -> None:
        if not isinstance(self.semantic, FactSemantic):
            raise DomainValidationError("semantic must be a FactSemantic")
        if not isinstance(self.confidence, FactConfidence):
            raise DomainValidationError("confidence must be a FactConfidence")
        if not isinstance(self.qualifiers, FactQualifiers):
            raise DomainValidationError("qualifiers must be FactQualifiers")
        _require_text(self.statement, "statement")
        if (
            isinstance(self.source_start, bool)
            or not isinstance(self.source_start, int)
            or self.source_start < 0
        ):
            raise DomainValidationError("source_start must be a non-negative character index")
        if (
            isinstance(self.source_end, bool)
            or not isinstance(self.source_end, int)
            or self.source_end <= self.source_start
        ):
            raise DomainValidationError("source span must be a non-empty half-open range")
        if self.semantic in _SUBJECT_REQUIRED_SEMANTICS and self.qualifiers.subject_label is None:
            raise DomainValidationError(
                f"subject_label is required for {self.semantic.value} facts"
            )
        if self.semantic is FactSemantic.DIALOGUE:
            if self.qualifiers.spoken_text is None:
                raise DomainValidationError("spoken_text is required for dialogue facts")
        elif self.qualifiers.spoken_text is not None:
            raise DomainValidationError("spoken_text is only valid for dialogue facts")


@dataclass(frozen=True)
class SourceSpan:
    source_ref: SourceRef
    episode_id: str
    scene_id: str
    source_start: int
    source_end: int

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, SourceRef):
            raise DomainValidationError("source_ref must be a SourceRef")
        SourcePartition(
            episode_id=self.episode_id,
            scene_id=self.scene_id,
            source_start=self.source_start,
            source_end=self.source_end,
        )


@dataclass(frozen=True)
class ScriptFact:
    fact_id: str
    fact_handle: str
    kind: FactKind
    semantic: FactSemantic
    statement: str
    confidence: FactConfidence
    qualifiers: FactQualifiers
    provenance: tuple[SourceSpan, ...]
    ordinal: int

    def __post_init__(self) -> None:
        require_opaque_id(self.fact_id)
        require_opaque_handle(self.fact_handle)
        if not isinstance(self.kind, FactKind):
            raise DomainValidationError("kind must be a FactKind")
        if not isinstance(self.semantic, FactSemantic):
            raise DomainValidationError("semantic must be a FactSemantic")
        if not isinstance(self.confidence, FactConfidence):
            raise DomainValidationError("confidence must be a FactConfidence")
        if not isinstance(self.qualifiers, FactQualifiers):
            raise DomainValidationError("qualifiers must be FactQualifiers")
        _require_text(self.statement, "statement")
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 1:
            raise DomainValidationError("ordinal must be a positive local integer")
        provenance = tuple(self.provenance)
        if not provenance or not all(isinstance(item, SourceSpan) for item in provenance):
            raise DomainValidationError("provenance must contain SourceSpan values")
        if any(
            item.episode_id != self.qualifiers.episode_id
            or item.scene_id != self.qualifiers.scene_id
            for item in provenance
        ):
            raise DomainValidationError("fact provenance must match typed qualifiers")
        if len(provenance) != len(set(provenance)):
            raise DomainValidationError("fact provenance must not contain duplicates")
        object.__setattr__(self, "provenance", provenance)

    def validate_against_normalized_source(self, source: NormalizedSource) -> tuple[str, ...]:
        if not isinstance(source, NormalizedSource):
            raise DomainValidationError("source must be a NormalizedSource")
        supporting: list[str] = []
        for span in self.provenance:
            if span.source_ref != source.source_ref:
                raise DomainValidationError("fact provenance references a different source")
            partition = source.partition_for(span.episode_id, span.scene_id)
            if not partition.contains(span.source_start, span.source_end):
                raise DomainValidationError("fact provenance crosses a source partition")
            text = source.text_for(span.source_start, span.source_end)
            if text != self.statement:
                raise DomainValidationError(
                    "fact source span must match the complete canonical statement"
                )
            if self.semantic is FactSemantic.DIALOGUE:
                assert self.qualifiers.spoken_text is not None
                if self.qualifiers.spoken_text not in text:
                    raise DomainValidationError("spoken_text is not present in its source span")
            supporting.append(text)
        return tuple(supporting)


@dataclass(frozen=True)
class FactRegistry:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.FACT_REGISTRY

    source_ref: SourceRef
    facts: tuple[ScriptFact, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, SourceRef):
            raise DomainValidationError("source_ref must be a SourceRef")
        facts = tuple(self.facts)
        if not facts or not all(isinstance(fact, ScriptFact) for fact in facts):
            raise DomainValidationError("facts must contain at least one ScriptFact")
        if tuple(fact.ordinal for fact in facts) != tuple(range(1, len(facts) + 1)):
            raise DomainValidationError("fact ordinals must be sequential from one")
        for field_name, identifiers in (
            ("fact_id", tuple(fact.fact_id for fact in facts)),
            ("fact_handle", tuple(fact.fact_handle for fact in facts)),
        ):
            if len(identifiers) != len(set(identifiers)):
                raise DomainValidationError(f"{field_name} must be unique in a FactRegistry")
        if any(
            span.source_ref != self.source_ref
            for fact in facts
            for span in fact.provenance
        ):
            raise DomainValidationError("all fact provenance must match the registry source")
        object.__setattr__(self, "facts", facts)

    @property
    def approved_handles(self) -> frozenset[str]:
        return frozenset(fact.fact_handle for fact in self.facts)

    def by_id(self, fact_id: str) -> ScriptFact:
        matches = tuple(fact for fact in self.facts if fact.fact_id == fact_id)
        if len(matches) != 1:
            raise DomainValidationError("fact_id is not an exact registry member")
        return matches[0]

    def by_handle(self, fact_handle: str) -> ScriptFact:
        require_opaque_handle(fact_handle)
        matches = tuple(fact for fact in self.facts if fact.fact_handle == fact_handle)
        if len(matches) != 1:
            raise DomainValidationError("fact_handle is not an exact registry member")
        return matches[0]

    def by_semantic(self, semantic: FactSemantic) -> tuple[ScriptFact, ...]:
        if not isinstance(semantic, FactSemantic):
            raise DomainValidationError("semantic must be a FactSemantic")
        return tuple(fact for fact in self.facts if fact.semantic is semantic)
