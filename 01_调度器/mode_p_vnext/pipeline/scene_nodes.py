"""A8 scene-to-Projection composition and independent DP boundary.

All durable values below are imported from the canonical domain.  Creative
stages return Draft payloads through the structured provider; local code alone
creates artifact IDs, hashes, VEC timing/bindings, ProjectionAST, Gate 0 and
the final DP result.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from mode_p_vnext.adapters.model.claude_deepseek import resolve_windows_claude_binary
from mode_p_vnext.adapters.storage.shadow_run import TextShadowStorage
from mode_p_vnext.domain.artifact import ArtifactEnvelope, ArtifactKind, DomainValidationError, SourceRef, canonical_sha256
from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingCommit, BlockingDraft
from mode_p_vnext.domain.decisions import DecisionBasis, DecisionDraft, VisualCurvePointDraft
from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
from mode_p_vnext.domain.evidence import DPReviewVerdict, DeterministicGateResult, IndependentDPReviewResult, ReviewPacket, RevisionFailureType
from mode_p_vnext.domain.facts import FactRegistry, FactSemantic
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.knowledge import KnowledgeSnapshot, KnowledgeStage
from mode_p_vnext.domain.projection import ProjectionAST, ProjectionManifest
from mode_p_vnext.domain.time import DurationIntent, GenerationCapabilityProfile
from mode_p_vnext.domain.vec import (
    DialogueBindingIntent,
    ExecutionDesignDraft,
    GenerationMode,
    PlacementPhase,
    ReferenceBindingIntent,
    ReferenceResponsibility,
    ShotDesignDraft,
    StoryboardRole,
    VisualBeatDraft,
    VisualBeatPhase,
    VisualExecutionContract,
)
from mode_p_vnext.knowledge_flow import KnowledgeCatalog, RetrievalContext
from mode_p_vnext.ports.structured_text import GenerationPolicy, StructuredGenerationPort
from mode_p_vnext.prompts.compiler import CompiledPrompt, PromptCompiler
from mode_p_vnext.prompts.signatures import Stage
from mode_p_vnext.schema.scene_diagnosis import SceneDiagnosis
from mode_p_vnext.services.blocking_assembler import assemble_blocking_commit
from mode_p_vnext.services.deterministic_gates import TEXT_VALIDATED, run_gate0
from mode_p_vnext.services.knowledge_retriever import KnowledgeRetriever, VerifiedBlockingCommit
from mode_p_vnext.services.projection_compiler import (
    StoryboardProjection,
    VideoProjection,
    compile_projection_ast,
    derive_storyboard,
    derive_video,
)
from mode_p_vnext.services.vec_assembler import assemble_vec

from .episode_nodes import call_or_rehydrate, scene_intent_transport
from .ingest_nodes import text_call_audit
from .verification_nodes import (
    DPReviewDraft,
    FreshDPContext,
    RevisionRequestDraft,
    assemble_fresh_dp_review,
    build_dp_review_packet,
    gate_result_source_ref,
    start_fresh_dp_context,
)


class SceneNodeError(RuntimeError):
    """Raised when an A8 scene node cannot prove its v3.1 boundary."""


@dataclass(frozen=True)
class KnowledgeArtifacts:
    snapshot_artifact: ArtifactEnvelope[KnowledgeSnapshot]


@dataclass(frozen=True)
class BlockingArtifacts:
    draft_artifact: ArtifactEnvelope[BlockingDraft]
    commit_artifact: ArtifactEnvelope[BlockingCommit]
    approved_input: Mapping[str, Any]
    compiled_prompt: CompiledPrompt
    audit: Mapping[str, Any]


@dataclass(frozen=True)
class ExecutionArtifacts:
    draft_artifact: ArtifactEnvelope[ExecutionDesignDraft]
    vec: VisualExecutionContract
    approved_input: Mapping[str, Any]
    compiled_prompt: CompiledPrompt
    audit: Mapping[str, Any]


@dataclass(frozen=True)
class VecArtifacts:
    artifact: ArtifactEnvelope[VisualExecutionContract]


@dataclass(frozen=True)
class ProjectionArtifacts:
    ast_artifact: ArtifactEnvelope[ProjectionAST]
    manifest_artifact: ArtifactEnvelope[ProjectionManifest]
    storyboard: StoryboardProjection
    video: VideoProjection


@dataclass(frozen=True)
class GateArtifacts:
    artifact: ArtifactEnvelope[DeterministicGateResult]


@dataclass(frozen=True)
class DPArtifacts:
    packet_artifact: ArtifactEnvelope[ReviewPacket]
    result_artifact: ArtifactEnvelope[IndependentDPReviewResult]
    context: FreshDPContext
    audit: Mapping[str, Any]


class FreshDPReviewer(Protocol):
    """A fresh-session-only DP port used after local Gate 0 has passed."""

    @property
    def reviewer_id(self) -> str: ...

    def review(
        self, packet: ReviewPacket, context: FreshDPContext
    ) -> tuple[DPReviewDraft, Mapping[str, Any]]: ...


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise SceneNodeError(f"{label} must be an array")
    return value


def _text_tuple(value: object, label: str) -> tuple[str, ...]:
    values = _list(value, label)
    if any(not isinstance(item, str) for item in values):
        raise SceneNodeError(f"{label} must contain strings")
    return tuple(values)


def _mapping_tuple(value: object, label: str) -> tuple[Mapping[str, Any], ...]:
    values = _list(value, label)
    if any(not isinstance(item, Mapping) for item in values):
        raise SceneNodeError(f"{label} must contain objects")
    return tuple(dict(item) for item in values)


def _decode_blocking(payload: Mapping[str, Any]) -> BlockingDraft:
    if set(payload) != {"beats"}:
        raise SceneNodeError("B0 Draft fields diverge from the frozen schema")
    beats: list[BlockingBeatDraft] = []
    expected = {
        "ordinal", "dramatic_action", "character_states", "prop_states",
        "gaze_relations", "action_paths", "continuity_effect",
    }
    for raw in _list(payload["beats"], "B0 beats"):
        if not isinstance(raw, Mapping) or set(raw) != expected:
            raise SceneNodeError("B0 beat fields diverge from the frozen schema")
        try:
            beats.append(
                BlockingBeatDraft(
                    ordinal=raw["ordinal"],
                    dramatic_action=raw["dramatic_action"],
                    character_states=_mapping_tuple(raw["character_states"], "character_states"),
                    prop_states=_mapping_tuple(raw["prop_states"], "prop_states"),
                    gaze_relations=_text_tuple(raw["gaze_relations"], "gaze_relations"),
                    action_paths=_text_tuple(raw["action_paths"], "action_paths"),
                    continuity_effect=raw["continuity_effect"],
                )
            )
        except (KeyError, DomainValidationError) as exc:
            raise SceneNodeError("B0 beat cannot decode to canonical BlockingBeatDraft") from exc
    try:
        return BlockingDraft(beats=tuple(beats))
    except DomainValidationError as exc:
        raise SceneNodeError("B0 Draft cannot decode to canonical BlockingDraft") from exc


def _decode_execution(payload: Mapping[str, Any]) -> ExecutionDesignDraft:
    expected = {"curve_points", "decisions", "shots", "transition_intents", "handoff_intent"}
    if set(payload) != expected:
        raise SceneNodeError("B1 Draft fields diverge from the frozen schema")
    curve: list[VisualCurvePointDraft] = []
    for raw in _list(payload["curve_points"], "curve_points"):
        if not isinstance(raw, Mapping) or set(raw) != {"dramatic_beat_ordinal", "intensity", "explanation"}:
            raise SceneNodeError("B1 curve point fields diverge from the frozen schema")
        try:
            curve.append(VisualCurvePointDraft(raw["dramatic_beat_ordinal"], raw["intensity"], raw["explanation"]))
        except (KeyError, DomainValidationError) as exc:
            raise SceneNodeError("B1 curve point is invalid") from exc

    decisions: list[DecisionDraft] = []
    decision_keys = {"scope", "basis", "locked_by", "options", "selected_index", "rationale", "tradeoff"}
    for raw in _list(payload["decisions"], "decisions"):
        if not isinstance(raw, Mapping) or set(raw) != decision_keys:
            raise SceneNodeError("B1 decision fields diverge from the frozen schema")
        try:
            decisions.append(
                DecisionDraft(
                    scope=raw["scope"],
                    basis=DecisionBasis(raw["basis"]),
                    locked_by=_text_tuple(raw["locked_by"], "locked_by"),
                    options=_text_tuple(raw["options"], "options"),
                    selected_index=raw["selected_index"],
                    rationale=raw["rationale"],
                    tradeoff=raw["tradeoff"],
                )
            )
        except (KeyError, ValueError, DomainValidationError) as exc:
            raise SceneNodeError("B1 decision is invalid") from exc

    shots: list[ShotDesignDraft] = []
    shot_keys = {
        "shot_ordinal", "blocking_beat_ordinal", "duration_intent", "generation_mode",
        "composition", "camera", "lighting", "performance", "visual_beats",
        "reference_binding_intents", "dialogue_binding_intents", "creative_notes",
    }
    beat_keys = {"visual_beat_ordinal", "phase", "subject_state", "attention", "storyboard_role"}
    reference_keys = {"shot_ordinal", "visual_beat_ordinal", "fact_handle", "responsibility"}
    dialogue_keys = {"shot_ordinal", "visual_beat_ordinal", "fact_handle", "placement_phase"}
    for raw in _list(payload["shots"], "shots"):
        if not isinstance(raw, Mapping) or set(raw) != shot_keys:
            raise SceneNodeError("B1 shot fields diverge from the frozen schema")
        visual_beats: list[VisualBeatDraft] = []
        for beat in _list(raw["visual_beats"], "visual_beats"):
            if not isinstance(beat, Mapping) or set(beat) != beat_keys:
                raise SceneNodeError("B1 visual beat fields diverge from the frozen schema")
            try:
                visual_beats.append(
                    VisualBeatDraft(
                        visual_beat_ordinal=beat["visual_beat_ordinal"],
                        phase=VisualBeatPhase(beat["phase"]),
                        subject_state=beat["subject_state"],
                        attention=beat["attention"],
                        storyboard_role=StoryboardRole(beat["storyboard_role"]),
                    )
                )
            except (KeyError, ValueError, DomainValidationError) as exc:
                raise SceneNodeError("B1 visual beat is invalid") from exc
        references: list[ReferenceBindingIntent] = []
        for item in _list(raw["reference_binding_intents"], "reference_binding_intents"):
            if not isinstance(item, Mapping) or set(item) != reference_keys:
                raise SceneNodeError("B1 reference binding fields diverge from the frozen schema")
            try:
                references.append(
                    ReferenceBindingIntent(
                        shot_ordinal=item["shot_ordinal"],
                        visual_beat_ordinal=item["visual_beat_ordinal"],
                        fact_handle=item["fact_handle"],
                        responsibility=ReferenceResponsibility(item["responsibility"]),
                    )
                )
            except (KeyError, ValueError, DomainValidationError) as exc:
                raise SceneNodeError("B1 reference binding is invalid") from exc
        dialogue: list[DialogueBindingIntent] = []
        for item in _list(raw["dialogue_binding_intents"], "dialogue_binding_intents"):
            if not isinstance(item, Mapping) or set(item) != dialogue_keys:
                raise SceneNodeError("B1 dialogue binding fields diverge from the frozen schema")
            try:
                dialogue.append(
                    DialogueBindingIntent(
                        shot_ordinal=item["shot_ordinal"],
                        visual_beat_ordinal=item["visual_beat_ordinal"],
                        fact_handle=item["fact_handle"],
                        placement_phase=PlacementPhase(item["placement_phase"]),
                    )
                )
            except (KeyError, ValueError, DomainValidationError) as exc:
                raise SceneNodeError("B1 dialogue binding is invalid") from exc
        try:
            shots.append(
                ShotDesignDraft(
                    shot_ordinal=raw["shot_ordinal"],
                    blocking_beat_ordinal=raw["blocking_beat_ordinal"],
                    duration_intent=DurationIntent(raw["duration_intent"]),
                    generation_mode=GenerationMode(raw["generation_mode"]),
                    composition=raw["composition"],
                    camera=raw["camera"],
                    lighting=raw["lighting"],
                    performance=raw["performance"],
                    visual_beats=tuple(visual_beats),
                    reference_binding_intents=tuple(references),
                    dialogue_binding_intents=tuple(dialogue),
                    creative_notes=raw["creative_notes"],
                )
            )
        except (KeyError, ValueError, DomainValidationError) as exc:
            raise SceneNodeError("B1 shot cannot decode to canonical ShotDesignDraft") from exc
    try:
        return ExecutionDesignDraft(
            curve_points=tuple(curve),
            decisions=tuple(decisions),
            shots=tuple(shots),
            transition_intents=_text_tuple(payload["transition_intents"], "transition_intents"),
            handoff_intent=payload["handoff_intent"],
        )
    except (KeyError, DomainValidationError) as exc:
        raise SceneNodeError("B1 Draft cannot decode to canonical ExecutionDesignDraft") from exc


def _knowledge_view_transport(snapshot: ArtifactEnvelope[KnowledgeSnapshot]) -> list[dict[str, Any]]:
    if type(snapshot) is not ArtifactEnvelope or type(snapshot.payload) is not KnowledgeSnapshot:
        raise SceneNodeError("knowledge snapshot must be an exact canonical envelope")
    return [
        {
            "capsule_id": item.capsule_id,
            "director_question": item.director_question,
            "applies_because": list(item.applies_because),
            "execution_constraints": list(item.execution_constraints),
            "expected_effect": item.expected_effect,
            "tradeoff": list(item.tradeoff),
            "anti_pattern": item.anti_pattern,
            "source_digest": item.source_digest,
        }
        for item in snapshot.payload.decision_view.entries
    ]


def _capability_transport(profile: GenerationCapabilityProfile) -> dict[str, Any]:
    return {
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "max_generation_ticks": profile.max_generation_ticks,
        "duration_options": [
            {
                "intent": option.intent.value,
                "min_ticks": option.min_ticks,
                "target_ticks": option.target_ticks,
                "max_ticks": option.max_ticks,
            }
            for option in profile.duration_options
        ],
    }


def _fact_binding_transport(facts: FactRegistry) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    references: list[dict[str, Any]] = []
    dialogue: list[dict[str, Any]] = []
    for fact in facts.facts:
        entry: dict[str, Any] = {
            "fact_handle": fact.fact_handle,
            "semantic": fact.semantic.value,
            "subject_label": fact.qualifiers.subject_label,
        }
        if fact.semantic is FactSemantic.DIALOGUE:
            entry["spoken_text"] = fact.qualifiers.spoken_text
            dialogue.append(entry)
        elif fact.semantic in {
            FactSemantic.CHARACTER, FactSemantic.WARDROBE, FactSemantic.PROP,
            FactSemantic.SETTING, FactSemantic.ASSET,
        }:
            references.append(entry)
    return references, dialogue


def run_k1_snapshot(
    *,
    episode_direction: ArtifactEnvelope[EpisodeDirectionDraft],
    scene_intent: ArtifactEnvelope[SceneIntentDraft],
    episode_id: str,
    scene_id: str,
    created_at_utc: str,
) -> KnowledgeArtifacts:
    """Use the single A3 retrieval implementation with an explicit empty catalog."""

    if type(episode_direction.payload) is not EpisodeDirectionDraft or type(scene_intent.payload) is not SceneIntentDraft:
        raise SceneNodeError("K1 requires exact E0/S1 canonical payloads")
    if not isinstance(scene_id, str) or not scene_id.strip():
        raise SceneNodeError("K1 scene_id must be explicit local run scope")
    result = KnowledgeRetriever().retrieve(
        diagnosis=SceneDiagnosis(
            scene_id=scene_id,
            attention_path=scene_intent.payload.scene_purpose,
            performance_issues=list(scene_intent.payload.performance_questions),
            transition_issues=list(scene_intent.payload.director_problems),
        ),
        catalog=KnowledgeCatalog(candidates=()),
        context=RetrievalContext(
            project_id=episode_id,
            mode="text_shadow",
            as_of=created_at_utc[:10],
        ),
        stage=KnowledgeStage.K1,
        k1_principles=episode_direction.payload.visual_principles,
    )
    return KnowledgeArtifacts(snapshot_artifact=result.snapshot)


def run_blocking(
    *,
    facts: FactRegistry,
    scene_intent: ArtifactEnvelope[SceneIntentDraft],
    k1_snapshot: ArtifactEnvelope[KnowledgeSnapshot],
    episode_id: str,
    scene_id: str,
    provider: StructuredGenerationPort,
    policy: GenerationPolicy,
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
    storage: TextShadowStorage,
    compiler: PromptCompiler | None = None,
) -> BlockingArtifacts:
    """Run/replay B0, then locally compile the sole BlockingCommit."""

    if type(scene_intent.payload) is not SceneIntentDraft or type(k1_snapshot.payload) is not KnowledgeSnapshot:
        raise SceneNodeError("B0 needs canonical S1 and K1 artifacts")
    if id_factory.program_version != program_version:
        raise SceneNodeError("B0 IdFactory program version mismatch")
    approved_input: Mapping[str, Any] = {
        "scene_id": scene_id,
        "scene_intent": scene_intent_transport(scene_intent.payload),
        "knowledge_view": _knowledge_view_transport(k1_snapshot),
        "continuity_state": {"status": "new_text_shadow"},
        "blocking_constraints": {
            "must_preserve_fact_handles": sorted(facts.approved_handles),
            "must_not_emit": ["persistent_ids", "ticks", "shots", "final_vec"],
        },
    }
    payload, audit, compiled = call_or_rehydrate(
        stage=Stage.B0,
        stage_id="B0",
        approved_input=approved_input,
        provider=provider,
        policy=policy,
        storage=storage,
        compiler=compiler or PromptCompiler(),
    )
    draft = _decode_blocking(payload)
    try:
        commit = assemble_blocking_commit(
            draft=draft,
            episode_id=episode_id,
            scene_id=scene_id,
            id_factory=id_factory,
            program_version=program_version,
        )
    except DomainValidationError as exc:
        raise SceneNodeError(f"local B0 compiler rejected Draft: {exc}") from exc
    draft_artifact = ArtifactEnvelope.create(
        artifact_id=commit.blocking_draft_artifact_id,
        artifact_type=ArtifactKind.BLOCKING_DRAFT,
        payload=draft,
        producer_stage="B0:director-draft",
        parent_artifact_ids=(scene_intent.artifact_id, k1_snapshot.artifact_id),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=k1_snapshot.canonical_payload_sha256,
        created_at_utc=created_at_utc,
    )
    commit_artifact = ArtifactEnvelope.create(
        artifact_id=commit.commit_id,
        artifact_type=ArtifactKind.BLOCKING_COMMIT,
        payload=commit,
        producer_stage="B0:blocking-compiler",
        parent_artifact_ids=(draft_artifact.artifact_id,),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=k1_snapshot.canonical_payload_sha256,
        created_at_utc=created_at_utc,
    )
    return BlockingArtifacts(draft_artifact, commit_artifact, approved_input, compiled, audit)


def run_k2_snapshot(
    *,
    scene_intent: ArtifactEnvelope[SceneIntentDraft],
    blocking_commit: ArtifactEnvelope[BlockingCommit],
    episode_id: str,
    scene_id: str,
    created_at_utc: str,
) -> KnowledgeArtifacts:
    """Bind K2 to a locally verified canonical BlockingCommit."""

    if type(scene_intent.payload) is not SceneIntentDraft or type(blocking_commit.payload) is not BlockingCommit:
        raise SceneNodeError("K2 requires canonical S1 and BlockingCommit artifacts")
    commit = blocking_commit.payload
    if commit.scene_id != scene_id:
        raise SceneNodeError("K2 BlockingCommit scene does not match explicit local scope")
    verification_digest = canonical_sha256(
        {
            "verification": "A8-local-blocking-commit-validation",
            "artifact_id": blocking_commit.artifact_id,
            "payload_digest": blocking_commit.canonical_payload_sha256,
        }
    )
    verified = VerifiedBlockingCommit(
        scene_id=scene_id,
        artifact_id=blocking_commit.artifact_id,
        content_sha256=blocking_commit.canonical_payload_sha256,
        verification_digest=verification_digest,
    )
    result = KnowledgeRetriever().retrieve(
        diagnosis=SceneDiagnosis(
            scene_id=scene_id,
            attention_path=scene_intent.payload.scene_purpose,
            performance_issues=list(scene_intent.payload.performance_questions),
            transition_issues=list(scene_intent.payload.director_problems),
        ),
        catalog=KnowledgeCatalog(candidates=()),
        context=RetrievalContext(
            project_id=episode_id,
            mode="text_shadow",
            as_of=created_at_utc[:10],
        ),
        stage=KnowledgeStage.K2,
        blocking_commit=verified,
    )
    return KnowledgeArtifacts(snapshot_artifact=result.snapshot)


def run_execution_design(
    *,
    facts: FactRegistry,
    scene_intent: ArtifactEnvelope[SceneIntentDraft],
    blocking_commit: ArtifactEnvelope[BlockingCommit],
    k2_snapshot: ArtifactEnvelope[KnowledgeSnapshot],
    episode_id: str,
    scene_id: str,
    provider: StructuredGenerationPort,
    policy: GenerationPolicy,
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
    storage: TextShadowStorage,
    capability_profile: GenerationCapabilityProfile | None = None,
    compiler: PromptCompiler | None = None,
) -> ExecutionArtifacts:
    """Run/replay B1; local code then derives, rather than accepts, a VEC."""

    if type(scene_intent.payload) is not SceneIntentDraft or type(blocking_commit.payload) is not BlockingCommit or type(k2_snapshot.payload) is not KnowledgeSnapshot:
        raise SceneNodeError("B1 requires canonical S1, B0, and K2 artifacts")
    profile = capability_profile or GenerationCapabilityProfile.sd20_default()
    if not isinstance(profile, GenerationCapabilityProfile):
        raise SceneNodeError("B1 capability profile must be canonical")
    references, dialogue = _fact_binding_transport(facts)
    commit = blocking_commit.payload
    approved_input: Mapping[str, Any] = {
        "scene_id": scene_id,
        "scene_intent": scene_intent_transport(scene_intent.payload),
        "blocking_summary": [
            {"ordinal": item.source_ordinal, "dramatic_action": item.dramatic_action}
            for item in commit.beats
        ],
        "blocking_commit": {"commit_id": commit.commit_id, "beat_count": len(commit.beats)},
        "knowledge_view": _knowledge_view_transport(k2_snapshot),
        "capability_profile": _capability_transport(profile),
        "approved_fact_handles": sorted(facts.approved_handles),
        "reference_requirements": references,
        "dialogue": dialogue,
        "audio_facts": dialogue,
        "continuity_state": {"entry_state_id": commit.entry_state_id, "exit_state_id": commit.exit_state_id},
        "knowledge_conflicts": [],
    }
    payload, audit, compiled = call_or_rehydrate(
        stage=Stage.B1,
        stage_id="B1",
        approved_input=approved_input,
        provider=provider,
        policy=policy,
        storage=storage,
        compiler=compiler or PromptCompiler(),
    )
    draft = _decode_execution(payload)
    try:
        vec = assemble_vec(
            draft=draft,
            blocking_commit=commit,
            facts=facts,
            episode_id=episode_id,
            scene_id=scene_id,
            id_factory=id_factory,
            program_version=program_version,
            capability_profile=profile,
        )
    except DomainValidationError as exc:
        raise SceneNodeError(f"local VEC compiler rejected B1 Draft: {exc}") from exc
    draft_artifact = ArtifactEnvelope.create(
        artifact_id=vec.execution_design_artifact_id,
        artifact_type=ArtifactKind.EXECUTION_DESIGN_DRAFT,
        payload=draft,
        producer_stage="B1:director-draft",
        parent_artifact_ids=(scene_intent.artifact_id, blocking_commit.artifact_id, k2_snapshot.artifact_id),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=k2_snapshot.canonical_payload_sha256,
        created_at_utc=created_at_utc,
    )
    return ExecutionArtifacts(draft_artifact, vec, approved_input, compiled, audit)


def run_vec_assembly(
    *,
    facts: FactRegistry,
    execution: ExecutionArtifacts,
    blocking_commit: ArtifactEnvelope[BlockingCommit],
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
) -> VecArtifacts:
    """Independently rebuild VEC to reject any caller-side/golden injection."""

    if type(execution.draft_artifact.payload) is not ExecutionDesignDraft or type(blocking_commit.payload) is not BlockingCommit:
        raise SceneNodeError("VEC requires exact canonical B1 and B0 payloads")
    try:
        rebuilt = assemble_vec(
            draft=execution.draft_artifact.payload,
            blocking_commit=blocking_commit.payload,
            facts=facts,
            episode_id=episode_id,
            scene_id=scene_id,
            id_factory=id_factory,
            program_version=program_version,
            capability_profile=execution.vec.capability_profile,
        )
    except DomainValidationError as exc:
        raise SceneNodeError(f"VEC rebuild failed: {exc}") from exc
    if rebuilt != execution.vec:
        raise SceneNodeError("VEC rebuild diverged; injected or non-deterministic VEC is forbidden")
    artifact = ArtifactEnvelope.create(
        artifact_id=rebuilt.contract_id,
        artifact_type=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
        payload=rebuilt,
        producer_stage="VEC:local-assembler",
        parent_artifact_ids=(execution.draft_artifact.artifact_id, blocking_commit.artifact_id),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )
    return VecArtifacts(artifact)


def run_projection(
    *,
    facts: FactRegistry,
    vec_artifact: ArtifactEnvelope[VisualExecutionContract],
    blocking_commit: ArtifactEnvelope[BlockingCommit],
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
) -> ProjectionArtifacts:
    """Compile one AST and derive both delivery views from that exact object."""

    if type(vec_artifact.payload) is not VisualExecutionContract or type(blocking_commit.payload) is not BlockingCommit:
        raise SceneNodeError("Projection requires canonical VEC and BlockingCommit")
    try:
        ast = compile_projection_ast(
            vec=vec_artifact.payload,
            blocking_commit=blocking_commit.payload,
            episode_id=episode_id,
            scene_id=scene_id,
            id_factory=id_factory,
            program_version=program_version,
        )
        storyboard = derive_storyboard(ast)
        video = derive_video(ast)
    except DomainValidationError as exc:
        raise SceneNodeError(f"Projection compiler rejected canonical VEC: {exc}") from exc
    ast_artifact = ArtifactEnvelope.create(
        artifact_id=ast.projection_id,
        artifact_type=ArtifactKind.PROJECTION_AST,
        payload=ast,
        producer_stage="Projection:canonical-ast",
        parent_artifact_ids=(vec_artifact.artifact_id,),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )
    manifest_input = canonical_sha256({"ast": ast, "video_manifest": video.manifest, "program_version": program_version})
    manifest_artifact = ArtifactEnvelope.create(
        artifact_id=id_factory.create(
            artifact_kind=ArtifactKind.PROJECTION_MANIFEST,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="Projection:video-manifest",
            input_digest=manifest_input,
            ordinal=0,
        ),
        artifact_type=ArtifactKind.PROJECTION_MANIFEST,
        payload=video.manifest,
        producer_stage="Projection:manifest",
        parent_artifact_ids=(ast_artifact.artifact_id,),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )
    return ProjectionArtifacts(ast_artifact, manifest_artifact, storyboard, video)


def run_gate0_artifact(
    *,
    facts: FactRegistry,
    vec_artifact: ArtifactEnvelope[VisualExecutionContract],
    projections: ProjectionArtifacts,
    compiled_prompts: Sequence[CompiledPrompt],
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
) -> GateArtifacts:
    """Persist only a passed deterministic Gate 0 under TEXT_VALIDATED."""

    try:
        result = run_gate0(
            vec=vec_artifact.payload,
            ast=projections.ast_artifact.payload,
            storyboard=projections.storyboard,
            video=projections.video,
            compiled_prompts=tuple(compiled_prompts),
            claim_ceiling=TEXT_VALIDATED,
            id_factory=id_factory,
            program_version=program_version,
        )
    except DomainValidationError as exc:
        raise SceneNodeError(f"Gate 0 rejected the text shadow: {exc}") from exc
    if not result.passed:
        raise SceneNodeError("Gate 0 failed: " + ",".join(result.failed_check_ids))
    artifact = ArtifactEnvelope.create(
        artifact_id=result.result_id,
        artifact_type=ArtifactKind.GATE0_RESULT,
        payload=result,
        producer_stage="G0:deterministic",
        parent_artifact_ids=(vec_artifact.artifact_id, projections.ast_artifact.artifact_id, projections.manifest_artifact.artifact_id),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )
    return GateArtifacts(artifact)


_DP_SCHEMA: Mapping[str, Any] = {
    "type": "object",
    "title": "DPReviewDraft",
    "additionalProperties": False,
    "required": ["verdict", "finding_codes", "revision_requests"],
    "properties": {
        "verdict": {"enum": ["approved", "revision_required"]},
        "finding_codes": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 160}},
        "revision_requests": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["target_artifact_id", "failure_type", "fact_refs", "field_paths", "observed_issue", "requested_change", "evidence_ref_ids"],
                "properties": {
                    "target_artifact_id": {"type": "string", "minLength": 1},
                    "failure_type": {"enum": [item.value for item in RevisionFailureType]},
                    "fact_refs": {"type": "array", "items": {"type": "string", "minLength": 1}},
                    "field_paths": {"type": "array", "items": {"type": "string", "minLength": 1}},
                    "observed_issue": {"type": "string", "minLength": 1, "maxLength": 500},
                    "requested_change": {"type": "string", "minLength": 1, "maxLength": 500},
                    "evidence_ref_ids": {"type": "array", "items": {"type": "string", "minLength": 1}},
                },
            },
        },
    },
}


def _packet_transport(packet: ReviewPacket) -> dict[str, Any]:
    return {
        "packet_id": packet.packet_id,
        "fact_refs": list(packet.fact_refs),
        "episode_direction_artifact_id": packet.episode_direction_artifact_id,
        "scene_intent_artifact_id": packet.scene_intent_artifact_id,
        "vec_artifact_id": packet.vec_artifact_id,
        "projection_artifact_ids": list(packet.projection_artifact_ids),
        "gate_result_refs": list(packet.gate_result_refs),
        "capability_profile_digest": packet.capability_profile_digest,
    }


def _decode_dp_payload(payload: Mapping[str, Any]) -> DPReviewDraft:
    if set(payload) != {"verdict", "finding_codes", "revision_requests"}:
        raise SceneNodeError("DP Draft fields diverge from the restricted review schema")
    try:
        verdict = DPReviewVerdict(payload["verdict"])
        findings = _text_tuple(payload["finding_codes"], "DP finding_codes")
        requests: list[RevisionRequestDraft] = []
        expected = {"target_artifact_id", "failure_type", "fact_refs", "field_paths", "observed_issue", "requested_change", "evidence_ref_ids"}
        for raw in _list(payload["revision_requests"], "DP revision_requests"):
            if not isinstance(raw, Mapping) or set(raw) != expected:
                raise SceneNodeError("DP RevisionRequestDraft fields are invalid")
            requests.append(
                RevisionRequestDraft(
                    target_artifact_id=raw["target_artifact_id"],
                    failure_type=RevisionFailureType(raw["failure_type"]),
                    fact_refs=_text_tuple(raw["fact_refs"], "DP fact_refs"),
                    field_paths=_text_tuple(raw["field_paths"], "DP field_paths"),
                    observed_issue=raw["observed_issue"],
                    requested_change=raw["requested_change"],
                    evidence_ref_ids=_text_tuple(raw["evidence_ref_ids"], "DP evidence_ref_ids"),
                )
            )
        return DPReviewDraft(verdict=verdict, finding_codes=findings, revision_requests=tuple(requests))
    except (KeyError, ValueError, DomainValidationError) as exc:
        raise SceneNodeError("DP Draft cannot decode to the bounded canonical DTO") from exc


def _dp_payload(draft: DPReviewDraft) -> dict[str, Any]:
    return {
        "verdict": draft.verdict.value,
        "finding_codes": list(draft.finding_codes),
        "revision_requests": [
            {
                "target_artifact_id": item.target_artifact_id,
                "failure_type": item.failure_type.value,
                "fact_refs": list(item.fact_refs),
                "field_paths": list(item.field_paths),
                "observed_issue": item.observed_issue,
                "requested_change": item.requested_change,
                "evidence_ref_ids": list(item.evidence_ref_ids),
            }
            for item in draft.revision_requests
        ],
    }


class NativeFreshDPReviewer:
    """One no-history native Claude process per ReviewPacket.

    It intentionally receives only the compact canonical ReviewPacket.  A
    process failure is fail-closed; there is no text fallback and no access to
    v4, cache, source bodies, media, or Director private reasoning.
    """

    def __init__(self, *, executable: str, model: str, timeout_seconds: int = 600) -> None:
        if not isinstance(model, str) or not model.strip():
            raise SceneNodeError("DP model must be non-empty")
        if isinstance(timeout_seconds, bool) or not 1 <= timeout_seconds <= 1_800:
            raise SceneNodeError("DP timeout must be within 1..1800 seconds")
        self._executable = resolve_windows_claude_binary((executable,))
        self._model = model
        self._timeout_seconds = timeout_seconds

    @property
    def reviewer_id(self) -> str:
        return f"native_fresh_dp:{self._model}"

    def review(self, packet: ReviewPacket, context: FreshDPContext) -> tuple[DPReviewDraft, Mapping[str, Any]]:
        if type(packet) is not ReviewPacket or type(context) is not FreshDPContext:
            raise SceneNodeError("native DP requires exact packet and fresh-context types")
        if context.prior_history_refs or context.forbidden_input_refs or context.review_packet_digest != canonical_sha256(packet):
            raise SceneNodeError("DP_INPUT_BLOCKED: native DP context is not packet-only and fresh")
        request_value = {
            "review_packet": _packet_transport(packet),
            "session_id": context.session_id,
            "instruction": "Return only approved or a bounded RevisionRequestDraft; never create IDs, hashes, VEC, shots, media claims, or new facts.",
        }
        request_text = json.dumps(request_value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        request_digest = hashlib.sha256(request_text.encode("utf-8")).hexdigest()
        argv = [
            self._executable, "-p", "--model", self._model, "--effort", "max",
            "--permission-mode", "bypassPermissions", "--tools", "",
            "--disable-slash-commands", "--safe-mode", "--no-session-persistence",
            "--no-chrome", "--output-format", "json", "--json-schema",
            json.dumps(_DP_SCHEMA, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "--system-prompt",
            "You are an independent DP reviewer. Read only the supplied review packet and produce the separately supplied JSON schema. Do not use prior history or tools.",
        ]
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                input=request_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SceneNodeError(f"fresh native DP transport failed: {type(exc).__name__}") from exc
        latency_ms = round((time.monotonic() - started) * 1000)
        if completed.returncode != 0:
            raise SceneNodeError(
                "fresh native DP returned non-zero; "
                f"exit_code={completed.returncode}; "
                f"stdout_sha256={hashlib.sha256((completed.stdout or '').encode('utf-8')).hexdigest()}; "
                f"stderr_sha256={hashlib.sha256((completed.stderr or '').encode('utf-8')).hexdigest()}"
            )
        try:
            envelope = json.loads(completed.stdout or "")
            raw = envelope.get("result", envelope) if isinstance(envelope, Mapping) else envelope
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            raise SceneNodeError("fresh native DP did not return a JSON Draft") from exc
        if not isinstance(payload, Mapping):
            raise SceneNodeError("fresh native DP output is not an object")
        draft = _decode_dp_payload(payload)
        response_text = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return draft, {
            "kind": "native_fresh_dp",
            "reviewer_id": self.reviewer_id,
            "fresh_session_id": context.session_id,
            "review_packet_digest": context.review_packet_digest,
            "prior_history_refs": [],
            "forbidden_input_refs": [],
            "request_digest": request_digest,
            "response_digest": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
            "latency_ms": latency_ms,
            "claim_ceiling": "TEXT_VALIDATED",
        }


def run_dp_review(
    *,
    facts: FactRegistry,
    episode_direction: ArtifactEnvelope[EpisodeDirectionDraft],
    scene_intent: ArtifactEnvelope[SceneIntentDraft],
    vec_artifact: ArtifactEnvelope[VisualExecutionContract],
    projections: ProjectionArtifacts,
    gate_artifact: ArtifactEnvelope[DeterministicGateResult],
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    program_version: str,
    created_at_utc: str,
    storage: TextShadowStorage,
    reviewer: FreshDPReviewer,
) -> DPArtifacts:
    """Create the minimal packet, demand one fresh review, and stop on revision."""

    if type(episode_direction.payload) is not EpisodeDirectionDraft or type(scene_intent.payload) is not SceneIntentDraft:
        raise SceneNodeError("DP requires canonical E0/S1 artifacts")
    if type(vec_artifact.payload) is not VisualExecutionContract or type(gate_artifact.payload) is not DeterministicGateResult:
        raise SceneNodeError("DP requires canonical VEC and Gate 0 artifacts")
    packet = build_dp_review_packet(
        facts=facts,
        vec=vec_artifact.payload,
        ast=projections.ast_artifact.payload,
        storyboard=projections.storyboard,
        video=projections.video,
        gate0=gate_artifact.payload,
        episode_direction_artifact_id=episode_direction.artifact_id,
        scene_intent_artifact_id=scene_intent.artifact_id,
        id_factory=id_factory,
        program_version=program_version,
    )
    packet_artifact = ArtifactEnvelope.create(
        artifact_id=packet.packet_id,
        artifact_type=ArtifactKind.REVIEW_PACKET,
        payload=packet,
        producer_stage="DP:review-packet",
        parent_artifact_ids=(episode_direction.artifact_id, scene_intent.artifact_id, vec_artifact.artifact_id, projections.ast_artifact.artifact_id, gate_artifact.artifact_id),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )
    context = start_fresh_dp_context(
        packet,
        id_factory=id_factory,
        episode_id=episode_id,
        scene_id=scene_id,
        program_version=program_version,
        attempt_ordinal=0,
    )
    input_digest = canonical_sha256({"packet": packet, "context": context, "reviewer_id": reviewer.reviewer_id})
    record = storage.load_stage("DP", input_sha256=input_digest)
    if record is None:
        draft, audit = reviewer.review(packet, context)
        if type(draft) is not DPReviewDraft or not isinstance(audit, Mapping):
            raise SceneNodeError("fresh DP port returned an invalid review DTO or audit")
        record = storage.store_stage(
            "DP",
            input_sha256=input_digest,
            payload=_dp_payload(draft),
            audit={"kind": "fresh_independent_dp", **dict(audit)},
        )
    payload = record.get("payload")
    audit = record.get("audit")
    if not isinstance(payload, Mapping) or not isinstance(audit, Mapping):
        raise SceneNodeError("DP stage record is malformed")
    if (
        audit.get("kind") != "fresh_independent_dp"
        or audit.get("fresh_session_id") != context.session_id
        or audit.get("review_packet_digest") != context.review_packet_digest
        or audit.get("prior_history_refs") != []
        or audit.get("forbidden_input_refs") != []
        or audit.get("claim_ceiling") != "TEXT_VALIDATED"
    ):
        raise SceneNodeError("DP_INPUT_BLOCKED: stored DP audit is not a fresh packet-only review")
    draft = _decode_dp_payload(payload)
    if draft.verdict is not DPReviewVerdict.APPROVED:
        raise SceneNodeError("DP requested a bounded revision; A8 records it and stops before any unbounded repair")
    try:
        bundle = assemble_fresh_dp_review(
            packet=packet,
            context=context,
            draft=draft,
            scopes=(),
            allowed_evidence_refs=(gate_result_source_ref(gate_artifact.payload),),
            id_factory=id_factory,
            episode_id=episode_id,
            scene_id=scene_id,
            program_version=program_version,
        )
    except DomainValidationError as exc:
        raise SceneNodeError(f"DP canonical assembly rejected the review: {exc}") from exc
    result = bundle.result
    result_artifact = ArtifactEnvelope.create(
        artifact_id=result.result_id,
        artifact_type=ArtifactKind.DP_REVIEW_RESULT,
        payload=result,
        producer_stage="DP:fresh-independent-review",
        parent_artifact_ids=(packet_artifact.artifact_id,),
        source_provenance=(facts.source_ref,),
        knowledge_snapshot_digest=None,
        created_at_utc=created_at_utc,
    )
    return DPArtifacts(packet_artifact, result_artifact, context, dict(audit))


__all__ = [
    "BlockingArtifacts",
    "DPArtifacts",
    "FreshDPReviewer",
    "GateArtifacts",
    "KnowledgeArtifacts",
    "NativeFreshDPReviewer",
    "ProjectionArtifacts",
    "SceneNodeError",
    "VecArtifacts",
    "ExecutionArtifacts",
    "run_blocking",
    "run_dp_review",
    "run_execution_design",
    "run_gate0_artifact",
    "run_k1_snapshot",
    "run_k2_snapshot",
    "run_projection",
    "run_vec_assembly",
]
