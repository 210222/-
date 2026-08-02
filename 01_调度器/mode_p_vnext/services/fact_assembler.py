"""Local deterministic owner of FactExtractionDraft compilation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    ArtifactKind,
    DomainValidationError,
    canonical_sha256,
)
from mode_p_vnext.domain.facts import (
    FactConfidence,
    FactExtractionDraft,
    FactKind,
    FactRegistry,
    NormalizedSource,
    ScriptFact,
    SourceSpan,
)
from mode_p_vnext.domain.ids import IdFactory


_CONFIDENCE_ORDER = {
    FactConfidence.UNCERTAIN: 0,
    FactConfidence.SUPPORTED: 1,
    FactConfidence.EXPLICIT: 2,
}


def _canonical_statement(value: str) -> str:
    return " ".join(value.split()).casefold()


class FactAssembler:
    """Validate, deduplicate and identify model-produced fact drafts locally."""

    def __init__(self, *, program_version: str = "mode-p-vnext-fact-assembler-3.0") -> None:
        self._ids = IdFactory(program_version=program_version)

    def assemble(
        self,
        *,
        normalized_source: NormalizedSource,
        normalized_source_artifact_id: str,
        drafts: Sequence[FactExtractionDraft],
        source_kind: FactKind,
        producer_stage: str,
        created_at_utc: str,
    ) -> ArtifactEnvelope[FactRegistry]:
        if not isinstance(normalized_source, NormalizedSource):
            raise DomainValidationError("normalized_source must be a NormalizedSource")
        if not isinstance(normalized_source_artifact_id, str) or not normalized_source_artifact_id.strip():
            raise DomainValidationError("normalized_source_artifact_id must be non-empty")
        if not isinstance(source_kind, FactKind):
            raise DomainValidationError("source_kind must be a FactKind")
        values = tuple(drafts)
        if not values or not all(isinstance(item, FactExtractionDraft) for item in values):
            raise DomainValidationError("drafts must contain FactExtractionDraft values")

        validated: list[tuple[FactExtractionDraft, SourceSpan]] = []
        for draft in values:
            partition = normalized_source.partition_for(
                draft.qualifiers.episode_id, draft.qualifiers.scene_id
            )
            if not partition.contains(draft.source_start, draft.source_end):
                raise DomainValidationError("fact draft source span crosses its scene partition")
            supporting_text = normalized_source.text_for(draft.source_start, draft.source_end)
            if supporting_text != draft.statement:
                raise DomainValidationError(
                    "fact source span must match the complete canonical statement"
                )
            if (
                draft.qualifiers.spoken_text is not None
                and draft.qualifiers.spoken_text not in supporting_text
            ):
                raise DomainValidationError("dialogue spoken_text is not present in its source span")
            validated.append(
                (
                    draft,
                    SourceSpan(
                        source_ref=normalized_source.source_ref,
                        episode_id=draft.qualifiers.episode_id,
                        scene_id=draft.qualifiers.scene_id,
                        source_start=draft.source_start,
                        source_end=draft.source_end,
                    ),
                )
            )

        # Canonical order is source order, not provider response order.
        validated.sort(
            key=lambda item: (
                item[1].source_start,
                item[1].source_end,
                item[0].semantic.value,
                _canonical_statement(item[0].statement),
            )
        )
        grouped: dict[tuple[object, ...], list[tuple[FactExtractionDraft, SourceSpan]]] = {}
        for item in validated:
            draft = item[0]
            key = (
                draft.semantic,
                _canonical_statement(draft.statement),
                draft.qualifiers.episode_id,
                draft.qualifiers.scene_id,
                (draft.qualifiers.subject_label or "").casefold(),
                draft.qualifiers.spoken_text,
            )
            grouped.setdefault(key, []).append(item)

        facts: list[ScriptFact] = []
        for ordinal, group in enumerate(grouped.values(), start=1):
            representative = group[0][0]
            spans = tuple(dict.fromkeys(item[1] for item in group))
            confidence = min(
                (item[0].confidence for item in group),
                key=lambda item: _CONFIDENCE_ORDER[item],
            )
            identity_input = canonical_sha256(
                {
                    "source_digest": normalized_source.source_ref.digest,
                    "semantic": representative.semantic,
                    "statement": _canonical_statement(representative.statement),
                    "qualifiers": representative.qualifiers,
                    "provenance": spans,
                }
            )
            fact_id = self._ids.create(
                artifact_kind=ArtifactKind.SCRIPT_FACT,
                episode_id=representative.qualifiers.episode_id,
                scene_id=representative.qualifiers.scene_id,
                stage="fact_assembly",
                input_digest=identity_input,
                ordinal=ordinal,
            )
            fact = ScriptFact(
                fact_id=fact_id,
                fact_handle=f"fh:{canonical_sha256({'identity_input': identity_input, 'purpose': 'model-selection'})}",
                kind=source_kind,
                semantic=representative.semantic,
                statement=representative.statement.strip(),
                confidence=confidence,
                qualifiers=representative.qualifiers,
                provenance=spans,
                ordinal=ordinal,
            )
            fact.validate_against_normalized_source(normalized_source)
            facts.append(fact)

        registry = FactRegistry(source_ref=normalized_source.source_ref, facts=tuple(facts))
        registry_input_digest = canonical_sha256(
            {
                "normalized_source": normalized_source,
                "fact_registry": registry,
                "source_kind": source_kind,
            }
        )
        artifact_id = self._ids.create(
            artifact_kind=ArtifactKind.FACT_REGISTRY,
            episode_id=registry.facts[0].qualifiers.episode_id,
            scene_id=None,
            stage=producer_stage,
            input_digest=registry_input_digest,
            ordinal=1,
        )
        return ArtifactEnvelope.create(
            artifact_id=artifact_id,
            artifact_type=ArtifactKind.FACT_REGISTRY,
            payload=registry,
            producer_stage=producer_stage,
            parent_artifact_ids=(normalized_source_artifact_id,),
            source_provenance=(normalized_source.source_ref,),
            knowledge_snapshot_digest=None,
            created_at_utc=created_at_utc,
        )
