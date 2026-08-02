"""A8 I0 ingest composition: raw bytes -> FactRegistry, with no final-model IDs.

This module deliberately keeps model output in the Draft layer.  It is the
local code below that normalizes source, validates global source spans, creates
opaque fact handles/IDs, and seals canonical artifact envelopes.
"""

from __future__ import annotations

import codecs
import unicodedata
from dataclasses import dataclass, fields
from typing import Any, Mapping, Sequence

from mode_p_vnext.adapters.storage.shadow_run import TextShadowStorage
from mode_p_vnext.domain.artifact import ArtifactEnvelope, ArtifactKind, DomainValidationError, canonical_sha256
from mode_p_vnext.domain.facts import (
    FactConfidence,
    FactExtractionDraft,
    FactKind,
    FactQualifiers,
    FactSemantic,
    NormalizedSource,
)
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.ports.structured_text import GenerationPolicy, ModelDraft, StructuredGenerationPort, TextCallEvidence
from mode_p_vnext.prompts.compiler import CompiledPrompt, PromptCompiler
from mode_p_vnext.prompts.signatures import Stage, stage_signatures
from mode_p_vnext.services.fact_assembler import FactAssembler
from mode_p_vnext.services.source_normalizer import SourceNormalizer


class IngestNodeError(RuntimeError):
    """Raised for malformed or unauditable I0 source-to-fact transitions."""


@dataclass(frozen=True)
class IngestArtifacts:
    """Canonical I0 outputs plus the exact preflighted prompt inputs."""

    normalized_source: NormalizedSource
    normalized_source_artifact: ArtifactEnvelope[NormalizedSource]
    fact_registry_artifact: ArtifactEnvelope[Any]
    i0_inputs: tuple[Mapping[str, Any], ...]
    i0_audits: tuple[Mapping[str, Any], ...]


def validate_text_call_audit(
    audit: Mapping[str, Any], *, compiled: CompiledPrompt
) -> dict[str, Any]:
    """Bind stored provider evidence to the exact preflighted prompt input."""

    if not isinstance(audit, Mapping):
        raise IngestNodeError("structured text audit must be an object")
    expected = {
        "stage": compiled.signature.stage.value,
        "signature_version": compiled.signature.version,
        "schema_digest": compiled.schema_digest,
        "approved_input_digest": compiled.approved_input_digest,
        "claim_ceiling": "TEXT_VALIDATED",
        "accepted": True,
    }
    for field_name, expected_value in expected.items():
        if audit.get(field_name) != expected_value:
            raise IngestNodeError(
                f"structured text audit {field_name} is not bound to the approved {compiled.signature.stage.value} call"
            )
    return dict(audit)


def text_call_audit(
    evidence: TextCallEvidence, *, compiled: CompiledPrompt
) -> dict[str, Any]:
    """Persist only structured, non-secret text-call audit metadata."""

    if not isinstance(evidence, TextCallEvidence):
        raise IngestNodeError("structured provider did not return TextCallEvidence")
    if evidence.claim_ceiling != "TEXT_VALIDATED" or not evidence.accepted:
        raise IngestNodeError("text-stage evidence must remain accepted TEXT_VALIDATED")
    result: dict[str, Any] = {}
    for item in fields(evidence):
        value = getattr(evidence, item.name)
        result[item.name] = value.value if hasattr(value, "value") else value
    return validate_text_call_audit(result, compiled=compiled)


def _normalised_text_for_partition(raw_source: bytes, encoding: str) -> str:
    """Mirror only the partition preflight; SourceNormalizer remains authority."""

    try:
        canonical_encoding = codecs.lookup(encoding).name
        text = raw_source.decode(canonical_encoding, errors="strict")
    except (LookupError, UnicodeDecodeError) as exc:
        raise IngestNodeError("raw source is not decodable using the requested encoding") from exc
    if text.startswith("\ufeff"):
        text = text[1:]
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def normalize_raw_source(
    *,
    raw_source: bytes,
    source_id: str,
    episode_id: str,
    scene_id: str,
    encoding: str,
) -> NormalizedSource:
    """Create the sole canonical source object with one explicit A8 partition."""

    if not isinstance(raw_source, bytes) or not raw_source:
        raise IngestNodeError("raw source must be non-empty bytes")
    normalized_text = _normalised_text_for_partition(raw_source, encoding)
    if not normalized_text.strip():
        raise IngestNodeError("raw source normalizes to empty text")
    try:
        return SourceNormalizer.normalize(
            raw_source,
            source_id=source_id,
            normalized_partitions=((episode_id, scene_id, 0, len(normalized_text)),),
            encoding=encoding,
            locator=None,
        )
    except DomainValidationError as exc:
        raise IngestNodeError(str(exc)) from exc


def _preferred_window_end(text: str, start: int, provisional_end: int) -> int:
    """Prefer a source boundary, but never omit text merely to find one."""

    if provisional_end >= len(text):
        return len(text)
    lower = start + max(1, (provisional_end - start) // 2)
    candidates = (
        text.rfind("\n", lower, provisional_end),
        text.rfind("。", lower, provisional_end),
        text.rfind(".", lower, provisional_end),
        text.rfind("!", lower, provisional_end),
        text.rfind("？", lower, provisional_end),
        text.rfind("?", lower, provisional_end),
        text.rfind(" ", lower, provisional_end),
    )
    boundary = max(candidates)
    return boundary + 1 if boundary >= lower else provisional_end


def plan_i0_inputs(
    normalized_source: NormalizedSource,
    *,
    compiler: PromptCompiler | None = None,
    maximum_window_characters: int = 3_000,
) -> tuple[Mapping[str, Any], ...]:
    """Split source windows before the I0 prompt budget can cause truncation."""

    if not isinstance(normalized_source, NormalizedSource):
        raise IngestNodeError("normalized_source must be canonical")
    if isinstance(maximum_window_characters, bool) or maximum_window_characters < 128:
        raise IngestNodeError("maximum_window_characters must be at least 128")
    prompt_compiler = compiler or PromptCompiler()
    signature = stage_signatures()[Stage.I0]
    partition = normalized_source.partitions[0]
    inputs: list[Mapping[str, Any]] = []
    start = partition.source_start
    while start < partition.source_end:
        candidate_end = min(partition.source_end, start + maximum_window_characters)
        end = _preferred_window_end(normalized_source.normalized_text, start, candidate_end)
        while True:
            candidate: Mapping[str, Any] = {
                "normalized_source": normalized_source.normalized_text[start:end],
                "source_digest": normalized_source.source_ref.digest,
                "source_start": start,
                "source_end": end,
            }
            try:
                prompt_compiler.compile(signature, candidate)
            except Exception as exc:
                if end - start <= 128:
                    raise IngestNodeError("I0 prompt budget cannot represent a source window") from exc
                end = start + max(128, (end - start) // 2)
                continue
            inputs.append(candidate)
            start = end
            break
    if not inputs:
        raise IngestNodeError("I0 did not receive a source window")
    if "".join(item["normalized_source"] for item in inputs) != normalized_source.normalized_text:
        raise IngestNodeError("I0 window plan does not cover normalized source exactly")
    return tuple(inputs)


def _assert_model_draft(draft: ModelDraft, stage: Stage, contract_name: str) -> Mapping[str, Any]:
    if not isinstance(draft, ModelDraft):
        raise IngestNodeError("provider did not return a ModelDraft")
    if draft.stage is not stage or draft.contract_name != contract_name:
        raise IngestNodeError("provider draft stage or contract does not match I0")
    if not isinstance(draft.payload, Mapping):
        raise IngestNodeError("provider draft payload must be an object")
    return dict(draft.payload)


def _decode_i0_payload(
    payload: Mapping[str, Any],
    *,
    normalized_source: NormalizedSource,
    episode_id: str,
    scene_id: str,
    window_start: int,
    window_end: int,
) -> tuple[FactExtractionDraft, ...]:
    raw_facts = payload.get("facts")
    if not isinstance(raw_facts, list) or not raw_facts:
        raise IngestNodeError("I0 Draft must contain a non-empty facts array")
    values: list[FactExtractionDraft] = []
    for raw in raw_facts:
        if not isinstance(raw, Mapping):
            raise IngestNodeError("I0 fact Draft entries must be objects")
        allowed = {
            "source_start", "source_end", "semantic_type", "statement",
            "subject_id", "spoken_text", "scene_hint",
        }
        if set(raw) - allowed:
            raise IngestNodeError("I0 Draft contains fields outside the frozen schema")
        try:
            semantic = FactSemantic(str(raw["semantic_type"]))
            start = raw["source_start"]
            end = raw["source_end"]
            statement = raw["statement"]
        except (KeyError, ValueError) as exc:
            raise IngestNodeError("I0 Draft has an invalid required fact field") from exc
        if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int):
            raise IngestNodeError("I0 source spans must be integer character offsets")
        if not window_start <= start < end <= window_end:
            raise IngestNodeError("I0 fact span escapes its approved source window")
        hint = raw.get("scene_hint")
        if hint is not None and hint != scene_id:
            raise IngestNodeError("I0 scene_hint may only name the current explicit partition")
        subject = raw.get("subject_id")
        spoken = raw.get("spoken_text")
        try:
            draft = FactExtractionDraft(
                semantic=semantic,
                statement=statement,
                source_start=start,
                source_end=end,
                confidence=FactConfidence.EXPLICIT,
                qualifiers=FactQualifiers(
                    episode_id=episode_id,
                    scene_id=scene_id,
                    subject_label=subject,
                    spoken_text=spoken,
                ),
            )
            # This makes the direct textual support check visible before the
            # FactAssembler repeats it as the authoritative final validation.
            if draft.statement.strip() not in normalized_source.text_for(start, end):
                raise IngestNodeError("I0 fact statement is not supported by its exact source span")
        except DomainValidationError as exc:
            raise IngestNodeError(str(exc)) from exc
        values.append(draft)
    return tuple(values)


def run_i0_ingest(
    *,
    raw_source: bytes,
    source_id: str,
    episode_id: str,
    scene_id: str,
    encoding: str,
    provider: StructuredGenerationPort,
    policy: GenerationPolicy,
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
    storage: TextShadowStorage,
    compiler: PromptCompiler | None = None,
) -> IngestArtifacts:
    """Execute or rehydrate I0 without ever accepting a model-owned final fact."""

    # Runtime-checkable protocols are intentionally avoided; duck typing is
    # checked here to keep independently implemented structured ports usable.
    if not callable(getattr(provider, "generate", None)):
        raise IngestNodeError("provider must implement structured generate")
    if not isinstance(id_factory, IdFactory) or id_factory.program_version != program_version:
        raise IngestNodeError("IdFactory must match the A8 program version")
    normalized = normalize_raw_source(
        raw_source=raw_source,
        source_id=source_id,
        episode_id=episode_id,
        scene_id=scene_id,
        encoding=encoding,
    )
    source_input_digest = canonical_sha256(
        {
            "normalized_source": normalized,
            "episode_id": episode_id,
            "scene_id": scene_id,
            "program_version": program_version,
        }
    )
    normalized_id = id_factory.create(
        artifact_kind=ArtifactKind.NORMALIZED_SOURCE,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="I0:normalize",
        input_digest=source_input_digest,
        ordinal=0,
    )
    normalized_artifact = ArtifactEnvelope.create(
        artifact_id=normalized_id,
        artifact_type=ArtifactKind.NORMALIZED_SOURCE,
        payload=normalized,
        producer_stage="I0:source-normalizer",
        parent_artifact_ids=(),
        source_provenance=(normalized.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )

    prompt_compiler = compiler or PromptCompiler()
    inputs = plan_i0_inputs(normalized, compiler=prompt_compiler)
    stage_input_digest = canonical_sha256(
        {
            "normalized_source": normalized,
            "windows": tuple(inputs),
            "program_version": program_version,
        }
    )
    existing = storage.load_stage("I0", input_sha256=stage_input_digest)
    records: list[Mapping[str, Any]] = []
    if existing is None:
        signature = stage_signatures()[Stage.I0]
        for ordinal, approved_input in enumerate(inputs):
            compiled = prompt_compiler.compile(signature, approved_input)
            draft, evidence = provider.generate(signature, approved_input, policy)
            payload = _assert_model_draft(draft, Stage.I0, signature.contract_name)
            records.append(
                {
                    "ordinal": ordinal,
                    "window_start": approved_input["source_start"],
                    "window_end": approved_input["source_end"],
                    "payload": payload,
                    "text_call": text_call_audit(evidence, compiled=compiled),
                }
            )
        storage.store_stage(
            "I0",
            input_sha256=stage_input_digest,
            payload={"windows": records},
            audit={"kind": "structured_text", "call_count": len(records)},
        )
    else:
        raw_records = existing["payload"].get("windows") if isinstance(existing["payload"], Mapping) else None
        if not isinstance(raw_records, list) or len(raw_records) != len(inputs):
            raise IngestNodeError("rehydrated I0 record does not match the planned source windows")
        records = [dict(item) for item in raw_records if isinstance(item, Mapping)]
        if len(records) != len(inputs):
            raise IngestNodeError("rehydrated I0 window record is malformed")

    decoded: list[FactExtractionDraft] = []
    audits: list[Mapping[str, Any]] = []
    for ordinal, (approved_input, record) in enumerate(zip(inputs, records)):
        if (
            record.get("ordinal") != ordinal
            or record.get("window_start") != approved_input["source_start"]
            or record.get("window_end") != approved_input["source_end"]
            or not isinstance(record.get("payload"), Mapping)
            or not isinstance(record.get("text_call"), Mapping)
        ):
            raise IngestNodeError("I0 record is not bound to the current source-window plan")
        decoded.extend(
            _decode_i0_payload(
                record["payload"],
                normalized_source=normalized,
                episode_id=episode_id,
                scene_id=scene_id,
                window_start=approved_input["source_start"],
                window_end=approved_input["source_end"],
            )
        )
        audits.append(
            validate_text_call_audit(
                record["text_call"],
                compiled=prompt_compiler.compile(stage_signatures()[Stage.I0], approved_input),
            )
        )

    try:
        fact_artifact = FactAssembler(program_version=program_version).assemble(
            normalized_source=normalized,
            normalized_source_artifact_id=normalized_artifact.artifact_id,
            drafts=tuple(decoded),
            source_kind=FactKind.SCRIPT,
            producer_stage="I0:fact-assembler",
            created_at_utc=created_at_utc,
        )
    except DomainValidationError as exc:
        raise IngestNodeError(str(exc)) from exc
    return IngestArtifacts(
        normalized_source=normalized,
        normalized_source_artifact=normalized_artifact,
        fact_registry_artifact=fact_artifact,
        i0_inputs=inputs,
        i0_audits=tuple(audits),
    )


def compile_i0_prompts(
    inputs: Sequence[Mapping[str, Any]], *, compiler: PromptCompiler | None = None
) -> tuple[CompiledPrompt, ...]:
    """Reconstruct preflighted prompt evidence without recalling a provider."""

    prompt_compiler = compiler or PromptCompiler()
    signature = stage_signatures()[Stage.I0]
    return tuple(prompt_compiler.compile(signature, item) for item in inputs)


__all__ = [
    "IngestArtifacts",
    "IngestNodeError",
    "compile_i0_prompts",
    "normalize_raw_source",
    "plan_i0_inputs",
    "run_i0_ingest",
    "text_call_audit",
    "validate_text_call_audit",
]
