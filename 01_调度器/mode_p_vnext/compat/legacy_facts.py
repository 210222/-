"""Explicit read adapter for pre-v2.2 ScriptFact records.

Legacy identifiers and legacy ``kind`` fields are never interpreted as new
fact semantics.  Records without an explicit v2.2 semantic contract are
imported as narrative-only and carry a deterministic re-ingest warning.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from mode_p_vnext.domain.artifact import (
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    canonical_sha256,
)
from mode_p_vnext.domain.facts import FactKind, FactSemantic, ScriptFact
from mode_p_vnext.domain.ids import IdFactory


_REFERENCE_OR_DIALOGUE_SEMANTICS = (
    FactSemantic.CHARACTER,
    FactSemantic.WARDROBE,
    FactSemantic.PROP,
    FactSemantic.SETTING,
    FactSemantic.DIALOGUE,
    FactSemantic.ASSET,
)


@dataclass(frozen=True)
class LegacyFactImportResult:
    fact: ScriptFact
    requires_reingest_for: tuple[FactSemantic, ...]


def read_legacy_script_fact(
    record: Mapping[str, object],
    *,
    episode_id: str,
    scene_id: str,
    source_ref: SourceRef,
    source_start: int,
    source_end: int,
    ordinal: int,
    source_kind: FactKind,
    normalized_source: str,
) -> LegacyFactImportResult:
    """Import one legacy fact without granting it inferred v2.2 semantics."""

    if not isinstance(record, Mapping):
        raise DomainValidationError("legacy fact record must be a mapping")
    statement_value = record.get("statement", record.get("summary"))
    if not isinstance(statement_value, str) or not statement_value.strip():
        raise DomainValidationError("legacy fact requires a non-empty statement or summary")
    if not isinstance(source_ref, SourceRef):
        raise DomainValidationError("source_ref must be a SourceRef")
    if not isinstance(source_kind, FactKind):
        raise DomainValidationError("source_kind must be a FactKind")

    input_digest = canonical_sha256(
        {
            "legacy_fact_id": str(record.get("fact_id", "")),
            "legacy_statement": statement_value,
            "source_id": source_ref.source_id,
            "source_digest": source_ref.digest,
            "source_start": source_start,
            "source_end": source_end,
        }
    )
    fact_id = IdFactory(program_version="vnext-2.2-legacy-compat").create(
        artifact_kind=ArtifactKind.SCRIPT_FACT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="legacy_fact_import",
        input_digest=input_digest,
        ordinal=ordinal,
    )
    fact = ScriptFact(
        fact_id=fact_id,
        scene_id=scene_id,
        kind=source_kind,
        semantic=FactSemantic.NARRATIVE,
        statement=statement_value,
        source_ref=source_ref,
        source_start=source_start,
        source_end=source_end,
        ordinal=ordinal,
    )
    fact.validate_against_normalized_source(normalized_source)
    return LegacyFactImportResult(
        fact=fact,
        requires_reingest_for=_REFERENCE_OR_DIALOGUE_SEMANTICS,
    )
