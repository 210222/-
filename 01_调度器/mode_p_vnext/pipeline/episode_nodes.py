"""A8 E0/S1 composition nodes for canonical dramatic direction Drafts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeVar

from mode_p_vnext.adapters.storage.shadow_run import TextShadowStorage
from mode_p_vnext.domain.artifact import ArtifactEnvelope, ArtifactKind, DomainValidationError, canonical_sha256
from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
from mode_p_vnext.domain.facts import FactRegistry, FactSemantic
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.ports.structured_text import GenerationPolicy, ModelDraft, StructuredGenerationPort
from mode_p_vnext.prompts.compiler import CompiledPrompt, PromptCompiler
from mode_p_vnext.prompts.signatures import Stage, stage_signatures

from .ingest_nodes import text_call_audit, validate_text_call_audit


class EpisodeNodeError(RuntimeError):
    """Raised for a malformed E0/S1 Draft or an unsafe resume record."""


@dataclass(frozen=True)
class EpisodeDirectionArtifacts:
    artifact: ArtifactEnvelope[EpisodeDirectionDraft]
    approved_input: Mapping[str, Any]
    compiled_prompt: CompiledPrompt
    audit: Mapping[str, Any]


@dataclass(frozen=True)
class SceneIntentArtifacts:
    artifact: ArtifactEnvelope[SceneIntentDraft]
    approved_input: Mapping[str, Any]
    compiled_prompt: CompiledPrompt
    audit: Mapping[str, Any]


T = TypeVar("T", EpisodeDirectionDraft, SceneIntentDraft)


def _as_tuple_text(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise EpisodeNodeError(f"{field_name} must be a JSON string array")
    return tuple(value)


def _decode_episode_direction(payload: Mapping[str, Any]) -> EpisodeDirectionDraft:
    expected = {
        "dramatic_promise", "audience_contract", "tension_curve",
        "visual_principles", "continuity_priorities", "unresolved_questions",
    }
    if set(payload) != expected:
        raise EpisodeNodeError("E0 Draft fields diverge from the frozen schema")
    try:
        return EpisodeDirectionDraft(
            dramatic_promise=payload["dramatic_promise"],
            audience_contract=payload["audience_contract"],
            tension_curve=_as_tuple_text(payload["tension_curve"], "tension_curve"),
            visual_principles=_as_tuple_text(payload["visual_principles"], "visual_principles"),
            continuity_priorities=_as_tuple_text(payload["continuity_priorities"], "continuity_priorities"),
            unresolved_questions=_as_tuple_text(payload["unresolved_questions"], "unresolved_questions"),
        )
    except (KeyError, DomainValidationError) as exc:
        raise EpisodeNodeError("E0 Draft cannot decode to canonical EpisodeDirectionDraft") from exc


def _decode_scene_intent(payload: Mapping[str, Any]) -> SceneIntentDraft:
    expected = {
        "scene_purpose", "state_change", "audience_information",
        "character_knowledge", "performance_questions", "director_problems",
        "continuity_effects", "unresolved_questions",
    }
    if set(payload) != expected:
        raise EpisodeNodeError("S1 Draft fields diverge from the frozen schema")
    try:
        return SceneIntentDraft(
            scene_purpose=payload["scene_purpose"],
            state_change=payload["state_change"],
            audience_information=_as_tuple_text(payload["audience_information"], "audience_information"),
            character_knowledge=_as_tuple_text(payload["character_knowledge"], "character_knowledge"),
            performance_questions=_as_tuple_text(payload["performance_questions"], "performance_questions"),
            director_problems=_as_tuple_text(payload["director_problems"], "director_problems"),
            continuity_effects=_as_tuple_text(payload["continuity_effects"], "continuity_effects"),
            unresolved_questions=_as_tuple_text(payload["unresolved_questions"], "unresolved_questions"),
        )
    except (KeyError, DomainValidationError) as exc:
        raise EpisodeNodeError("S1 Draft cannot decode to canonical SceneIntentDraft") from exc


def _transport_facts(facts: FactRegistry, *, scene_id: str | None = None) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for fact in facts.facts:
        if scene_id is not None and fact.qualifiers.scene_id != scene_id:
            continue
        item = {
            "fact_handle": fact.fact_handle,
            "semantic": fact.semantic.value,
            "statement": fact.statement,
            "episode_id": fact.qualifiers.episode_id,
            "scene_id": fact.qualifiers.scene_id,
        }
        if fact.qualifiers.subject_label is not None:
            item["subject_label"] = fact.qualifiers.subject_label
        if fact.qualifiers.spoken_text is not None:
            item["spoken_text"] = fact.qualifiers.spoken_text
        values.append(item)
    if not values:
        raise EpisodeNodeError("approved transport fact view is empty")
    return values


def direction_transport(direction: EpisodeDirectionDraft) -> dict[str, Any]:
    if not isinstance(direction, EpisodeDirectionDraft):
        raise EpisodeNodeError("episode direction must be canonical")
    return {
        "dramatic_promise": direction.dramatic_promise,
        "audience_contract": direction.audience_contract,
        "tension_curve": list(direction.tension_curve),
        "visual_principles": list(direction.visual_principles),
        "continuity_priorities": list(direction.continuity_priorities),
        "unresolved_questions": list(direction.unresolved_questions),
    }


def scene_intent_transport(intent: SceneIntentDraft) -> dict[str, Any]:
    if not isinstance(intent, SceneIntentDraft):
        raise EpisodeNodeError("scene intent must be canonical")
    return {
        "scene_purpose": intent.scene_purpose,
        "state_change": intent.state_change,
        "audience_information": list(intent.audience_information),
        "character_knowledge": list(intent.character_knowledge),
        "performance_questions": list(intent.performance_questions),
        "director_problems": list(intent.director_problems),
        "continuity_effects": list(intent.continuity_effects),
        "unresolved_questions": list(intent.unresolved_questions),
    }


def call_or_rehydrate(
    *,
    stage: Stage,
    stage_id: str,
    approved_input: Mapping[str, Any],
    provider: StructuredGenerationPort,
    policy: GenerationPolicy,
    storage: TextShadowStorage,
    compiler: PromptCompiler,
) -> tuple[Mapping[str, Any], Mapping[str, Any], CompiledPrompt]:
    signature = stage_signatures()[stage]
    compiled = compiler.compile(signature, approved_input)
    input_digest = canonical_sha256(
        {
            "stage": stage.value,
            "approved_input": approved_input,
            "program_version": storage.run_record["program_version"],
        }
    )
    record = storage.load_stage(stage_id, input_sha256=input_digest)
    if record is None:
        if not callable(getattr(provider, "generate", None)):
            raise EpisodeNodeError("structured provider has no generate method")
        draft, evidence = provider.generate(signature, approved_input, policy)
        if not isinstance(draft, ModelDraft) or draft.stage is not stage or draft.contract_name != signature.contract_name:
            raise EpisodeNodeError(f"provider did not return the required {stage.value} Draft")
        if not isinstance(draft.payload, Mapping):
            raise EpisodeNodeError(f"{stage.value} Draft payload must be an object")
        audit = text_call_audit(evidence, compiled=compiled)
        record = storage.store_stage(
            stage_id,
            input_sha256=input_digest,
            payload=dict(draft.payload),
            audit={"kind": "structured_text", "text_call": audit},
        )
    payload = record.get("payload")
    audit = record.get("audit")
    if not isinstance(payload, Mapping) or not isinstance(audit, Mapping):
        raise EpisodeNodeError(f"{stage.value} stage record is malformed")
    text_audit = audit.get("text_call")
    try:
        validated_audit = validate_text_call_audit(text_audit, compiled=compiled)
    except IngestNodeError as exc:
        raise EpisodeNodeError(f"{stage.value} audit is not bound to its provider stage") from exc
    return dict(payload), validated_audit, compiled


def run_episode_direction(
    *,
    facts: FactRegistry,
    fact_registry_artifact_id: str,
    episode_id: str,
    provider: StructuredGenerationPort,
    policy: GenerationPolicy,
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
    storage: TextShadowStorage,
    compiler: PromptCompiler | None = None,
) -> EpisodeDirectionArtifacts:
    """Run/replay E0 and locally seal its canonical Draft artifact."""

    if not isinstance(facts, FactRegistry) or not isinstance(id_factory, IdFactory):
        raise EpisodeNodeError("E0 needs canonical facts and an IdFactory")
    if id_factory.program_version != program_version:
        raise EpisodeNodeError("E0 IdFactory program version mismatch")
    approved_input: Mapping[str, Any] = {
        "episode_id": episode_id,
        "episode_facts": _transport_facts(facts),
        "episode_constraints": {
            "claim_ceiling": "TEXT_VALIDATED",
            "forbidden_outputs": ["persistent_ids", "hashes", "absolute_ticks", "final_vec"],
        },
        "continuity_state": {"status": "new_text_shadow"},
    }
    payload, audit, compiled = call_or_rehydrate(
        stage=Stage.E0,
        stage_id="E0",
        approved_input=approved_input,
        provider=provider,
        policy=policy,
        storage=storage,
        compiler=compiler or PromptCompiler(),
    )
    direction = _decode_episode_direction(payload)
    input_digest = canonical_sha256(
        {"facts": facts, "approved_input": approved_input, "direction": direction, "program_version": program_version}
    )
    artifact_id = id_factory.create(
        artifact_kind=ArtifactKind.EPISODE_DIRECTION_DRAFT,
        episode_id=episode_id,
        scene_id=None,
        stage="E0",
        input_digest=input_digest,
        ordinal=0,
    )
    artifact = ArtifactEnvelope.create(
        artifact_id=artifact_id,
        artifact_type=ArtifactKind.EPISODE_DIRECTION_DRAFT,
        payload=direction,
        producer_stage="E0:director-draft",
        parent_artifact_ids=(fact_registry_artifact_id,),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )
    return EpisodeDirectionArtifacts(artifact, approved_input, compiled, audit)


def run_scene_intent(
    *,
    facts: FactRegistry,
    fact_registry_artifact_id: str,
    episode_direction: ArtifactEnvelope[EpisodeDirectionDraft],
    scene_id: str,
    provider: StructuredGenerationPort,
    policy: GenerationPolicy,
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
    storage: TextShadowStorage,
    compiler: PromptCompiler | None = None,
) -> SceneIntentArtifacts:
    """Run/replay S1 with E0 and facts as its only creative antecedents."""

    if not isinstance(facts, FactRegistry) or type(episode_direction) is not ArtifactEnvelope:
        raise EpisodeNodeError("S1 needs canonical facts and an E0 envelope")
    if type(episode_direction.payload) is not EpisodeDirectionDraft:
        raise EpisodeNodeError("S1 E0 envelope has the wrong canonical payload")
    episode_id = episode_direction.payload and facts.facts[0].qualifiers.episode_id
    if not isinstance(episode_id, str) or not episode_id:
        raise EpisodeNodeError("S1 cannot infer the episode identity")
    approved_input: Mapping[str, Any] = {
        "scene_id": scene_id,
        "scene_facts": _transport_facts(facts, scene_id=scene_id),
        "episode_direction": direction_transport(episode_direction.payload),
        "continuity_state": {"previous_scene_state": "not_supplied_in_a8"},
        "knowledge_view": [],
    }
    payload, audit, compiled = call_or_rehydrate(
        stage=Stage.S1,
        stage_id="S1",
        approved_input=approved_input,
        provider=provider,
        policy=policy,
        storage=storage,
        compiler=compiler or PromptCompiler(),
    )
    intent = _decode_scene_intent(payload)
    input_digest = canonical_sha256(
        {
            "facts": facts,
            "episode_direction": episode_direction.payload,
            "approved_input": approved_input,
            "scene_intent": intent,
            "program_version": program_version,
        }
    )
    artifact_id = id_factory.create(
        artifact_kind=ArtifactKind.SCENE_INTENT_DRAFT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="S1",
        input_digest=input_digest,
        ordinal=0,
    )
    artifact = ArtifactEnvelope.create(
        artifact_id=artifact_id,
        artifact_type=ArtifactKind.SCENE_INTENT_DRAFT,
        payload=intent,
        producer_stage="S1:director-draft",
        parent_artifact_ids=(fact_registry_artifact_id, episode_direction.artifact_id),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )
    return SceneIntentArtifacts(artifact, approved_input, compiled, audit)


__all__ = [
    "EpisodeDirectionArtifacts",
    "EpisodeNodeError",
    "SceneIntentArtifacts",
    "call_or_rehydrate",
    "direction_transport",
    "run_episode_direction",
    "run_scene_intent",
    "scene_intent_transport",
]
