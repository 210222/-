"""Read-only observation adapter for pre-schema-3.0 fact records.

The adapter never mints a v3 ScriptFact, handle, ID, registry, or Artifact.
Only the A1 FactAssembler may do that after a new typed extraction pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from mode_p_vnext.domain.artifact import DomainValidationError, SourceRef, canonical_sha256
from mode_p_vnext.domain.facts import FactSemantic, NormalizedSource


@dataclass(frozen=True)
class LegacyFactObservation:
    legacy_fact_id: str | None
    statement: str
    source_ref: SourceRef
    source_start: int
    source_end: int
    raw_semantic: str | None
    record_digest: str
    requires_reingest: bool = True


def read_legacy_script_fact(
    record: Mapping[str, object],
    *,
    normalized_source: NormalizedSource,
    source_start: int,
    source_end: int,
) -> LegacyFactObservation:
    """Observe a legacy record without granting it any v3 semantic authority."""

    if not isinstance(record, Mapping):
        raise DomainValidationError("legacy fact record must be a mapping")
    if not isinstance(normalized_source, NormalizedSource):
        raise DomainValidationError("normalized_source must be a NormalizedSource")
    statement = record.get("statement", record.get("summary"))
    if not isinstance(statement, str) or not statement.strip():
        raise DomainValidationError("legacy fact requires a non-empty statement or summary")
    supporting_text = normalized_source.text_for(source_start, source_end)
    if statement.strip() not in supporting_text:
        raise DomainValidationError("legacy fact statement is not supported by the declared span")
    if not any(
        partition.contains(source_start, source_end)
        for partition in normalized_source.partitions
    ):
        raise DomainValidationError("legacy fact span crosses a normalized source partition")
    legacy_id = record.get("fact_id")
    raw_semantic = record.get("semantic", record.get("kind"))
    return LegacyFactObservation(
        legacy_fact_id=legacy_id if isinstance(legacy_id, str) and legacy_id.strip() else None,
        statement=statement.strip(),
        source_ref=normalized_source.source_ref,
        source_start=source_start,
        source_end=source_end,
        raw_semantic=raw_semantic if isinstance(raw_semantic, str) and raw_semantic.strip() else None,
        record_digest=canonical_sha256(dict(record)),
    )
