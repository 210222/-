"""Mechanical acceptance tests for A1's canonical vNext domain boundary.

These tests deliberately describe the public schema that downstream A2--A10
must consume.  Legacy schemas remain outside this authority boundary.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path

import pytest

from mode_p_vnext.compat.legacy_checkpoint import read_legacy_b0_k2_checkpoint
from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    ValidationStatus,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingDraft
from mode_p_vnext.domain.decisions import DecisionDraft, VisualCurvePointDraft
from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.time import (
    TICKS_PER_SECOND,
    CanonicalTimeline,
    GenerationSegmentTimeline,
    TickRange,
    TimelinePlacement,
)
from mode_p_vnext.domain.vec import (
    ExecutionDesignDraft,
    ShotDesignDraft,
    VisualBeatDraft,
    VisualExecutionContract,
)


DOMAIN_ROOT = Path(__file__).resolve().parents[1] / "domain"


def _episode_direction() -> EpisodeDirectionDraft:
    return EpisodeDirectionDraft(
        dramatic_promise="The quiet decision changes the relationship.",
        audience_contract="The audience can follow cause and effect.",
        tension_curve=("arrival", "choice", "aftermath"),
        visual_principles=("hold on the decision",),
        continuity_priorities=("the letter remains in the left hand",),
        unresolved_questions=("Does the other character see the letter?",),
    )


def _field_names(domain_type: type) -> tuple[str, ...]:
    return tuple(field.name for field in dataclasses.fields(domain_type))


def test_stage_draft_schemas_match_architecture_section_5_3_exactly() -> None:
    assert _field_names(EpisodeDirectionDraft) == (
        "dramatic_promise",
        "audience_contract",
        "tension_curve",
        "visual_principles",
        "continuity_priorities",
        "unresolved_questions",
    )
    assert _field_names(SceneIntentDraft) == (
        "scene_purpose",
        "state_change",
        "audience_information",
        "character_knowledge",
        "performance_questions",
        "director_problems",
        "continuity_effects",
        "unresolved_questions",
    )
    assert _field_names(BlockingBeatDraft) == (
        "ordinal",
        "dramatic_action",
        "character_states",
        "prop_states",
        "gaze_relations",
        "action_paths",
        "continuity_effect",
    )
    assert _field_names(BlockingDraft) == ("beats",)
    assert _field_names(DecisionDraft) == (
        "scope",
        "basis",
        "locked_by",
        "options",
        "selected_index",
        "rationale",
        "tradeoff",
    )
    assert _field_names(VisualBeatDraft) == (
        "phase",
        "subject_state",
        "attention",
        "storyboard_role",
    )
    assert _field_names(ShotDesignDraft) == (
        "blocking_beat_ordinal",
        "dramatic_function",
        "attention_target",
        "information_action",
        "framing_intent",
        "camera_pose",
        "camera_motion",
        "composition",
        "lighting",
        "performance",
        "duration_weight",
        "visual_beats",
    )
    assert _field_names(ExecutionDesignDraft) == (
        "curve_points",
        "decisions",
        "shots",
        "transition_intents",
        "audio_intents",
        "reference_intents",
        "handoff_intent",
    )


def test_b1_decision_modes_and_visual_beat_roles_are_bounded() -> None:
    from mode_p_vnext.domain.decisions import DecisionBasis
    from mode_p_vnext.domain.vec import StoryboardRole, VisualBeatPhase

    choice = DecisionDraft(
        scope="shot:1",
        basis=DecisionBasis.CHOICE,
        locked_by=(),
        options=("hold the frame", "move with the subject"),
        selected_index=0,
        rationale="The held frame makes the decision legible.",
        tradeoff="Less kinetic energy.",
    )
    locked = DecisionDraft(
        scope="continuity:axis",
        basis=DecisionBasis.LOCKED,
        locked_by=("fact:axis-established",),
        options=("preserve screen direction",),
        selected_index=0,
        rationale="The established axis is a locked fact.",
        tradeoff="Camera placement remains inside the safe corridor.",
    )
    beat = VisualBeatDraft(
        phase=VisualBeatPhase.REACTION,
        subject_state="Lin Lan absorbs the transfer of authority.",
        attention="Her gaze remains on the key.",
        storyboard_role=StoryboardRole.REQUIRED,
    )
    shot = ShotDesignDraft(
        blocking_beat_ordinal=1,
        dramatic_function="Make the transfer of authority legible.",
        attention_target="the key",
        information_action="The audience sees that Lin Lan does not reach.",
        framing_intent="hold both the hand and key in frame",
        camera_pose="eye-level across the table",
        camera_motion="locked",
        composition="the key divides the frame",
        lighting="soft side light preserves the key silhouette",
        performance="Lin Lan stays still after the hand withdraws",
        duration_weight=3,
        visual_beats=(beat,),
    )
    draft = ExecutionDesignDraft(
        curve_points=(
            VisualCurvePointDraft(
                dramatic_beat_ordinal=1,
                intensity=70,
                explanation="The physical handoff concentrates the scene.",
            ),
        ),
        decisions=(choice, locked),
        shots=(shot,),
        transition_intents=(),
        audio_intents=("Preserve the key line without adding dialogue.",),
        reference_intents=("Maintain character and key identity.",),
        handoff_intent="End on Lin Lan alone with the unresolved choice.",
    )

    assert choice.options[choice.selected_index] == "hold the frame"
    assert locked.locked_by == ("fact:axis-established",)
    assert beat.storyboard_role is StoryboardRole.REQUIRED
    assert draft.shots[0].duration_weight == 3
    with pytest.raises(DomainValidationError, match="exactly two"):
        DecisionDraft(
            scope="shot:1",
            basis=DecisionBasis.CHOICE,
            locked_by=(),
            options=("hold",),
            selected_index=0,
            rationale="reason",
            tradeoff="tradeoff",
        )
    with pytest.raises(DomainValidationError, match="locked_by"):
        DecisionDraft(
            scope="continuity:axis",
            basis=DecisionBasis.LOCKED,
            locked_by=(),
            options=("preserve",),
            selected_index=0,
            rationale="reason",
            tradeoff="tradeoff",
        )


def test_canonical_vec_schema_carries_all_locally_assembled_authority() -> None:
    from mode_p_vnext.domain.blocking import BlockingBeat, BlockingCommit
    from mode_p_vnext.domain.decisions import DirectorDecision, VisualCurvePoint
    from mode_p_vnext.domain.vec import (
        AudioEvent,
        GenerationSegment,
        ReferenceRequirement,
        ShotBoundary,
        VisualBeat,
        VoiceRequirement,
    )

    assert _field_names(VisualExecutionContract) == (
        "contract_id",
        "scene_id",
        "execution_design_artifact_id",
        "blocking_commit_artifact_id",
        "source_fact_ids",
        "timeline",
        "curve_points",
        "decisions",
        "segments",
        "shots",
        "boundaries",
        "audio_events",
        "voice_requirements",
        "reference_requirements",
        "handoff_intent",
    )
    required_types = {
        BlockingBeat,
        BlockingCommit,
        DirectorDecision,
        VisualCurvePoint,
        GenerationSegment,
        VisualBeat,
        ShotBoundary,
        AudioEvent,
        VoiceRequirement,
        ReferenceRequirement,
    }
    assert all(dataclasses.is_dataclass(item) for item in required_types)
    assert all(item.__dataclass_params__.frozen for item in required_types)


def test_minimal_vec_is_closed_over_ids_ticks_states_and_requirements() -> None:
    from mode_p_vnext.domain.decisions import (
        DecisionBasis,
        DirectorDecision,
        VisualCurvePoint,
    )
    from mode_p_vnext.domain.vec import (
        GenerationSegment,
        ReferenceRequirement,
        StoryboardRole,
        VisualBeat,
        VisualBeatPhase,
        VisualShot,
    )

    decision = DirectorDecision(
        decision_id="decision:1",
        source_decision_ordinal=1,
        scope="shot:1",
        basis=DecisionBasis.CHOICE,
        locked_by=(),
        options=("hold", "move"),
        selected_index=0,
        rationale="A hold preserves the decision.",
        tradeoff="Less motion.",
    )
    visual_beat = VisualBeat(
        beat_id="visual-beat:1",
        shot_id="shot:1",
        phase=VisualBeatPhase.REACTION,
        interval=TickRange(0, 2_400),
        subject_state="Lin Lan remains still.",
        attention="the key",
        storyboard_role=StoryboardRole.REQUIRED,
        start_state_id="state:entry",
        end_state_id="state:exit",
        decision_ids=(decision.decision_id,),
    )
    requirement = ReferenceRequirement(
        requirement_id="reference:1",
        role="character_identity",
        scope_kind="character",
        scope_id="character:lin-lan",
        source_fact_ids=("fact:lin-lan",),
    )
    shot = VisualShot(
        shot_id="shot:1",
        segment_id="segment:1",
        source_shot_ordinal=1,
        blocking_beat_id="blocking-beat:1",
        interval=TickRange(0, 2_400),
        dramatic_function="Hold the decision.",
        attention_target="the key",
        information_action="Lin Lan does not reach.",
        framing_intent="two-shot across the table",
        camera_pose="eye-level",
        camera_motion="locked",
        composition="key at the center divide",
        lighting="soft side light",
        performance="stillness after the handoff",
        visual_beats=(visual_beat,),
        decision_ids=(decision.decision_id,),
        reference_requirement_ids=(requirement.requirement_id,),
        audio_event_ids=(),
    )
    vec = VisualExecutionContract(
        contract_id="vec:1",
        scene_id="scene:1",
        execution_design_artifact_id="execution-design:1",
        blocking_commit_artifact_id="blocking-commit:1",
        source_fact_ids=("fact:lin-lan",),
        timeline=CanonicalTimeline(),
        curve_points=(
            VisualCurvePoint(
                point_id="curve:1",
                source_curve_ordinal=1,
                blocking_beat_id="blocking-beat:1",
                intensity=70,
                explanation="The transfer peaks here.",
            ),
        ),
        decisions=(decision,),
        segments=(
            GenerationSegment(
                segment_id="segment:1",
                timeline=GenerationSegmentTimeline(duration_ticks=2_400),
                shot_ids=(shot.shot_id,),
            ),
        ),
        shots=(shot,),
        boundaries=(),
        audio_events=(),
        voice_requirements=(),
        reference_requirements=(requirement,),
        handoff_intent="End on Lin Lan and the key.",
    )

    assert vec.shots[0].visual_beats[0].interval == TickRange(0, 2_400)
    assert vec.shots[0].mirror_flip_forbidden is True
    with pytest.raises(DomainValidationError, match="local safety constant"):
        dataclasses.replace(shot, mirror_flip_forbidden=False)


def test_knowledge_projection_and_review_schemas_match_architecture_views() -> None:
    from mode_p_vnext.domain.evidence import RevisionRequest
    from mode_p_vnext.domain.knowledge import (
        KnowledgeCandidateRecord,
        KnowledgeCapabilityScope,
        KnowledgeDecisionEntry,
        KnowledgeDecisionView,
        KnowledgeSnapshot,
    )
    from mode_p_vnext.domain.projection import ProjectionManifest, ProjectionNode

    assert _field_names(KnowledgeDecisionEntry) == (
        "capsule_id",
        "director_question",
        "applies_because",
        "execution_constraints",
        "expected_effect",
        "tradeoff",
        "anti_pattern",
        "source_digest",
    )
    assert _field_names(KnowledgeDecisionView) == ("scene_id", "stage", "entries")
    assert {
        "snapshot_id",
        "scene_id",
        "stage",
        "decision_view",
        "selected_capsule_ids",
        "exclusions",
        "conflicts",
        "catalog_index_sha256",
        "retrieval_input_digest",
        "blocking_commit_digest",
        "security_event_digests",
        "candidate_records",
        "selection_reasons",
        "catalog_index_abstract",
    } == set(_field_names(KnowledgeSnapshot))
    assert _field_names(KnowledgeCapabilityScope) == (
        "valid_from",
        "valid_until",
        "target_models",
        "target_modes",
        "aspect_ratios",
        "source_digest",
    )
    assert _field_names(KnowledgeCandidateRecord) == (
        "candidate_id",
        "content_sha256",
        "source_refs",
        "field_provenance",
    )
    assert _field_names(RevisionRequest) == (
        "request_id",
        "target_artifact_id",
        "failure_type",
        "fact_refs",
        "field_paths",
        "observed_issue",
        "requested_change",
        "evidence_refs",
    )
    assert {
        "node_id",
        "source_beat_id",
        "source_shot_id",
        "interval",
        "start_state_id",
        "end_state_id",
        "decision_ids",
        "attributes",
        "children",
    } == set(_field_names(ProjectionNode))
    assert _field_names(ProjectionManifest) == (
        "vec_digest",
        "projection_ast_digest",
        "source_node_ids",
        "compiler_version",
        "adapter_version",
        "capability_profile_digest",
        "reference_binding_digest",
        "audio_binding_digest",
    )


def test_release_phase_schema_cannot_claim_a_production_switch() -> None:
    from mode_p_vnext.domain.release import ReleasePhase

    assert {phase.value for phase in ReleasePhase} == {
        "BASELINE_REPAIR_REQUIRED",
        "ARCHITECTURE_MIGRATION_REQUIRED",
        "TEXT_SHADOW_REQUIRED",
        "HOLDOUT_EVALUATION_REQUIRED",
        "MEDIA_EVIDENCE_REQUIRED",
        "OWNER_APPROVAL_REQUIRED",
        "PRODUCTION_SWITCH_PROPOSAL_ELIGIBLE",
    }
    assert all("AUTHORIZED" not in phase.value for phase in ReleasePhase)
    assert all("SWITCHED" not in phase.value for phase in ReleasePhase)


def test_nested_domain_data_is_deeply_frozen_before_hashing() -> None:
    visible_parts = ["head", "torso"]
    character_state = {
        "character_id": "character:lin-lan",
        "visible_body_parts": visible_parts,
    }
    beat = BlockingBeatDraft(
        ordinal=1,
        dramatic_action="Lin Lan watches the key.",
        character_states=(character_state,),
        prop_states=({"prop_id": "prop:key", "holder": "table"},),
        gaze_relations=("Lin Lan -> key",),
        action_paths=("stillness -> decision",),
        continuity_effect="The key remains on the table.",
    )
    draft = BlockingDraft(beats=(beat,))
    source = SourceRef(source_id="script:scene-1", digest="a" * 64)
    envelope = ArtifactEnvelope.create(
        artifact_id="blocking_draft:scene-1:0001",
        artifact_kind=ArtifactKind.BLOCKING_DRAFT,
        schema_version="2.1",
        program_version="vnext-2.1",
        payload=draft,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
        created_at="2026-07-30T00:00:00Z",
    )
    digest = envelope.content_sha256

    visible_parts.append("hand")
    character_state["new_field"] = "must not leak"
    assert beat.character_states[0]["visible_body_parts"] == ("head", "torso")
    assert "new_field" not in beat.character_states[0]
    assert envelope.content_sha256 == digest
    assert canonical_sha256(envelope.payload) == canonical_sha256(draft)
    with pytest.raises(TypeError):
        beat.character_states[0]["character_id"] = "mutated"


def test_canonical_artifact_envelope_is_hash_bound_and_machine_assembled() -> None:
    direction = _episode_direction()
    source = SourceRef(source_id="script:episode-1", digest="a" * 64)
    artifact_id = IdFactory(program_version="vnext-2.1").create(
        artifact_kind=ArtifactKind.EPISODE_DIRECTION,
        episode_id="episode-1",
        scene_id=None,
        stage="A1",
        input_digest=canonical_sha256({"script": "episode-1"}),
        ordinal=1,
    )
    envelope = ArtifactEnvelope.create(
        artifact_id=artifact_id,
        artifact_kind=ArtifactKind.EPISODE_DIRECTION,
        schema_version="2.1",
        program_version="vnext-2.1",
        payload=direction,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
        validation_status=ValidationStatus.DRAFT,
        created_at="2026-07-30T00:00:00Z",
    )

    assert envelope.content_sha256 == ArtifactEnvelope.content_digest_for(
        artifact_kind=ArtifactKind.EPISODE_DIRECTION,
        schema_version="2.1",
        program_version="vnext-2.1",
        payload=direction,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
    )
    assert envelope.artifact_id == artifact_id
    assert envelope.validation_status is ValidationStatus.DRAFT
    assert dataclasses.is_dataclass(envelope)
    assert envelope.__dataclass_params__.frozen
    with pytest.raises(TypeError):
        envelope.dependency_digests["script"] = "b" * 64

    with pytest.raises(DomainValidationError, match="content_sha256"):
        ArtifactEnvelope(
            artifact_id=artifact_id,
            artifact_kind=ArtifactKind.EPISODE_DIRECTION,
            schema_version="2.1",
            program_version="vnext-2.1",
            payload=direction,
            source_refs=(source,),
            dependency_digests={"script": source.digest},
            content_sha256="0" * 64,
            created_at="2026-07-30T00:00:00Z",
            validation_status=ValidationStatus.DRAFT,
        )
    with pytest.raises(DomainValidationError, match="artifact_kind"):
        ArtifactEnvelope.create(
            artifact_id=artifact_id,
            artifact_kind=ArtifactKind.SCENE_INTENT,
            schema_version="2.1",
            program_version="vnext-2.1",
            payload=direction,
            source_refs=(source,),
            dependency_digests={"script": source.digest},
            created_at="2026-07-30T00:00:00Z",
        )


def test_persistent_domain_payloads_declare_their_canonical_artifact_kind() -> None:
    from mode_p_vnext.domain.blocking import BlockingCommit
    from mode_p_vnext.domain.evidence import (
        DeterministicGateResult,
        FrameEvidencePlan,
        IndependentDPReviewResult,
        MediaEvidence,
        MediaRunRecord,
        OwnerApprovalRecord,
        ReviewPacket,
        RevisionRequest,
        VisualVerificationResult,
    )
    from mode_p_vnext.domain.facts import FactRegistry
    from mode_p_vnext.domain.knowledge import (
        KnowledgeCapsuleV2,
        KnowledgeSnapshot,
    )
    from mode_p_vnext.domain.projection import (
        CapabilityAdaptationRecord,
        ProjectionAST,
        ProjectionManifest,
    )
    from mode_p_vnext.domain.release import ReleaseGateRecord

    expected_kinds = {
        EpisodeDirectionDraft: ArtifactKind.EPISODE_DIRECTION,
        SceneIntentDraft: ArtifactKind.SCENE_INTENT,
        FactRegistry: ArtifactKind.SCRIPT_FACT,
        KnowledgeCapsuleV2: ArtifactKind.KNOWLEDGE_CAPSULE,
        KnowledgeSnapshot: ArtifactKind.KNOWLEDGE_SNAPSHOT,
        BlockingDraft: ArtifactKind.BLOCKING_DRAFT,
        BlockingCommit: ArtifactKind.BLOCKING_COMMIT,
        DecisionDraft: ArtifactKind.DECISION_DRAFT,
        ExecutionDesignDraft: ArtifactKind.EXECUTION_DESIGN_DRAFT,
        VisualExecutionContract: ArtifactKind.VISUAL_EXECUTION_CONTRACT,
        ProjectionAST: ArtifactKind.PROJECTION_AST,
        ProjectionManifest: ArtifactKind.PROJECTION_MANIFEST,
        CapabilityAdaptationRecord: ArtifactKind.CAPABILITY_ADAPTATION,
        DeterministicGateResult: ArtifactKind.GATE0_RESULT,
        ReviewPacket: ArtifactKind.REVIEW_PACKET,
        IndependentDPReviewResult: ArtifactKind.DP_REVIEW_RESULT,
        RevisionRequest: ArtifactKind.REVISION_REQUEST,
        MediaRunRecord: ArtifactKind.MEDIA_RUN_RECORD,
        FrameEvidencePlan: ArtifactKind.FRAME_EVIDENCE_PLAN,
        MediaEvidence: ArtifactKind.MEDIA_EVIDENCE,
        VisualVerificationResult: ArtifactKind.VISUAL_VERIFICATION_RESULT,
        OwnerApprovalRecord: ArtifactKind.OWNER_APPROVAL_RECORD,
        ReleaseGateRecord: ArtifactKind.RELEASE_DECISION,
    }

    assert {
        payload_type: payload_type.ARTIFACT_KIND
        for payload_type in expected_kinds
    } == expected_kinds
    assert set(expected_kinds.values()) == set(ArtifactKind)
    assert len(expected_kinds) == len(set(expected_kinds.values()))


def test_artifact_envelope_rejects_generic_and_forged_payload_authority() -> None:
    source = SourceRef(source_id="script:scene-1", digest="a" * 64)
    common = {
        "artifact_id": "script_fact:scene-1:0001",
        "artifact_kind": ArtifactKind.SCRIPT_FACT,
        "schema_version": "2.1",
        "program_version": "vnext-2.1",
        "source_refs": (source,),
        "dependency_digests": {"script": source.digest},
        "created_at": "2026-07-30T00:00:00Z",
    }
    with pytest.raises(DomainValidationError, match="payload type"):
        ArtifactEnvelope.create(payload={"facts": ()}, **common)

    @dataclasses.dataclass(frozen=True)
    class ForgedFactPayload:
        ARTIFACT_KIND = ArtifactKind.SCRIPT_FACT
        facts: tuple[str, ...] = ()

    with pytest.raises(DomainValidationError, match="payload type"):
        ArtifactEnvelope.create(payload=ForgedFactPayload(), **common)


def test_gate_dp_media_and_owner_results_are_separate_auditable_authorities() -> None:
    from mode_p_vnext.domain.evidence import (
        DPReviewVerdict,
        DeterministicGateResult,
        FrameEvidence,
        IndependentDPReviewResult,
        MediaEvidence,
        OwnerApprovalDecision,
        OwnerApprovalRecord,
    )

    evidence_ref = SourceRef(source_id="gate-log:1", digest="c" * 64)
    gate = DeterministicGateResult(
        result_id="gate0:scene-1",
        target_artifact_ids=("vec:scene-1",),
        check_ids=("schema", "tick_contiguity"),
        failed_check_ids=(),
        evidence_refs=(evidence_ref,),
        passed=True,
    )
    dp = IndependentDPReviewResult(
        result_id="dp:scene-1",
        review_packet_artifact_id="review-packet:scene-1",
        verdict=DPReviewVerdict.APPROVED,
        finding_codes=(),
        revision_request_artifact_ids=(),
        independent_context_digest="d" * 64,
    )
    frame = FrameEvidence(
        media_run_id="media-run:1",
        frame_index=24,
        observations=("screen direction remains stable",),
        attributes={"character": "Lin Lan"},
    )
    media = MediaEvidence(
        evidence_id="media-evidence:1",
        frame_evidence_plan_artifact_id="frame-plan:1",
        media_run_artifact_id="artifact:media-run:1",
        media_run_id="media-run:1",
        frame_evidence=(frame,),
    )
    approval = OwnerApprovalRecord(
        approval_id="owner-approval:1",
        visual_verification_artifact_id="visual-verification:1",
        decision=OwnerApprovalDecision.APPROVED,
        approved_by="owner:JT",
        evidence_ref=SourceRef(
            source_id="owner-action:1",
            digest="e" * 64,
        ),
    )

    assert gate.ARTIFACT_KIND is ArtifactKind.GATE0_RESULT
    assert dp.ARTIFACT_KIND is ArtifactKind.DP_REVIEW_RESULT
    assert media.ARTIFACT_KIND is ArtifactKind.MEDIA_EVIDENCE
    assert approval.ARTIFACT_KIND is ArtifactKind.OWNER_APPROVAL_RECORD
    assert "production_switch_authorized" not in _field_names(
        OwnerApprovalRecord
    )

    with pytest.raises(DomainValidationError, match="passed"):
        DeterministicGateResult(
            result_id="gate0:scene-1",
            target_artifact_ids=("vec:scene-1",),
            check_ids=("schema",),
            failed_check_ids=("schema",),
            evidence_refs=(evidence_ref,),
            passed=True,
        )
    with pytest.raises(DomainValidationError, match="finding_codes"):
        IndependentDPReviewResult(
            result_id="dp:scene-1",
            review_packet_artifact_id="review-packet:scene-1",
            verdict=DPReviewVerdict.REVISION_REQUIRED,
            finding_codes=(),
            revision_request_artifact_ids=(),
            independent_context_digest="d" * 64,
        )


def test_knowledge_capsule_requires_field_provenance_and_scoped_capability_validity() -> None:
    from mode_p_vnext.domain.knowledge import (
        KnowledgeCapabilityScope,
        KnowledgeCapsuleV2,
    )

    source = SourceRef(
        source_id="capability-note:video-model-x",
        digest="a" * 64,
        locator="knowledge/capabilities/video-model-x-2026-07-30.md",
    )
    scope = KnowledgeCapabilityScope(
        valid_from="2026-07-01",
        valid_until="2026-08-01",
        target_models=("video-model-x",),
        target_modes=("image-to-video",),
        aspect_ratios=("16:9",),
        source_digest=source.digest,
    )
    capsule = KnowledgeCapsuleV2(
        capsule_id="capsule:capability:video-model-x",
        category="platform_capability",
        claims=("The model accepts one character-position reference image.",),
        source_summary="Verified platform capability note for the tested release window.",
        source_refs=(source,),
        field_provenance={
            "claims": (source,),
            "source_summary": (source,),
            "capability_scope": (source,),
        },
        capability_scope=scope,
        confidence="high",
    )

    assert capsule.capability_scope == scope
    assert capsule.field_provenance["claims"] == (source,)
    with pytest.raises(DomainValidationError, match="valid_until"):
        KnowledgeCapabilityScope(
            valid_from="2026-08-02",
            valid_until="2026-08-01",
            target_models=("video-model-x",),
            target_modes=("image-to-video",),
            aspect_ratios=("16:9",),
            source_digest=source.digest,
        )
    with pytest.raises(DomainValidationError, match="field_provenance"):
        KnowledgeCapsuleV2(
            capsule_id="capsule:missing-provenance",
            category="principle",
            claims=("A claim without a field chain is not canonical.",),
            source_summary="A source summary.",
            source_refs=(source,),
            field_provenance={"claims": (source,)},
            capability_scope=None,
            confidence="medium",
        )
    with pytest.raises(DomainValidationError, match="source_digest"):
        KnowledgeCapsuleV2(
            capsule_id="capsule:unregistered-capability-source",
            category="platform_capability",
            claims=("A capability scope cannot cite an unregistered source.",),
            source_summary="A source summary.",
            source_refs=(source,),
            field_provenance={
                "claims": (source,),
                "source_summary": (source,),
                "capability_scope": (source,),
            },
            capability_scope=dataclasses.replace(
                scope,
                source_digest="b" * 64,
            ),
            confidence="medium",
        )


def test_knowledge_snapshot_seals_full_candidate_accounting_and_selection_reasons() -> None:
    from mode_p_vnext.domain.knowledge import (
        KnowledgeCandidateRecord,
        KnowledgeDecisionEntry,
        KnowledgeDecisionView,
        KnowledgeSnapshot,
        KnowledgeStage,
    )

    source = SourceRef(
        source_id="knowledge-source:shot-design",
        digest="b" * 64,
        locator="knowledge/shot-design.md#reaction",
    )
    selected = KnowledgeCandidateRecord(
        candidate_id="capsule:selected",
        content_sha256="c" * 64,
        source_refs=(source,),
        field_provenance={"claims": (source,)},
    )
    excluded = KnowledgeCandidateRecord(
        candidate_id="capsule:excluded",
        content_sha256="d" * 64,
        source_refs=(source,),
        field_provenance={"claims": (source,)},
    )
    view = KnowledgeDecisionView(
        scene_id="scene:1",
        stage=KnowledgeStage.K1,
        entries=(
            KnowledgeDecisionEntry(
                capsule_id=selected.candidate_id,
                director_question="How should the reaction be framed?",
                applies_because=("The scene turns on withheld reaction.",),
                execution_constraints=("Do not add unobserved props.",),
                expected_effect="The audience reads the withheld response.",
                tradeoff=("The pace briefly slows.",),
                anti_pattern=False,
                source_digest=selected.content_sha256,
            ),
        ),
    )
    snapshot = KnowledgeSnapshot(
        snapshot_id="knowledge-snapshot:scene:1:k1",
        scene_id="scene:1",
        stage=KnowledgeStage.K1,
        decision_view=view,
        selected_capsule_ids=(selected.candidate_id,),
        exclusions={excluded.candidate_id: "Lower-ranked for this director question."},
        conflicts=(),
        catalog_index_sha256="e" * 64,
        retrieval_input_digest="f" * 64,
        blocking_commit_digest=None,
        security_event_digests=(),
        candidate_records=(selected, excluded),
        selection_reasons={selected.candidate_id: "Best fit for the question and scene state."},
        catalog_index_abstract={
            "catalog_version": "knowledge-catalog:2026-07-30",
            "retriever_version": "vnext-a3",
        },
    )

    assert tuple(record.candidate_id for record in snapshot.candidate_records) == (
        selected.candidate_id,
        excluded.candidate_id,
    )
    with pytest.raises(DomainValidationError, match="account"):
        KnowledgeSnapshot(
            snapshot_id="knowledge-snapshot:scene:1:incomplete",
            scene_id="scene:1",
            stage=KnowledgeStage.K1,
            decision_view=view,
            selected_capsule_ids=(selected.candidate_id,),
            exclusions={},
            conflicts=(),
            catalog_index_sha256="e" * 64,
            retrieval_input_digest="f" * 64,
            blocking_commit_digest=None,
            security_event_digests=(),
            candidate_records=(selected, excluded),
            selection_reasons={selected.candidate_id: "Best fit."},
            catalog_index_abstract={"catalog_version": "knowledge-catalog:2026-07-30"},
        )

def test_id_factory_is_stable_and_drafts_cannot_carry_machine_authority() -> None:
    factory = IdFactory(program_version="vnext-2.1")
    kwargs = {
        "artifact_kind": ArtifactKind.SCENE_INTENT,
        "episode_id": "episode-1",
        "scene_id": "scene-2",
        "stage": "B0",
        "input_digest": "b" * 64,
        "ordinal": 3,
    }
    assert factory.create(**kwargs) == factory.create(**kwargs)
    assert factory.create(**kwargs) != factory.create(**{**kwargs, "ordinal": 4})
    assert factory.create(**{**kwargs, "episode_id": "episode:a", "scene_id": "scene"}) != factory.create(
        **{**kwargs, "episode_id": "episode", "scene_id": "a:scene"}
    )

    draft_fields = {
        field.name
        for draft_type in (
            EpisodeDirectionDraft,
            SceneIntentDraft,
            BlockingBeatDraft,
            BlockingDraft,
            ExecutionDesignDraft,
        )
        for field in dataclasses.fields(draft_type)
    }
    forbidden_model_authority = {
        "artifact_id",
        "content_sha256",
        "dependency_digests",
        "start_tick",
        "end_tick",
        "timeline",
        "vec_id",
        "contract_id",
        "segment_id",
        "shot_id",
        "boundary_id",
        "event_id",
        "requirement_id",
    }
    assert not (draft_fields & forbidden_model_authority)


def test_only_24000_tick_canonical_timebase_and_half_open_ranges_exist() -> None:
    assert TICKS_PER_SECOND == 24_000
    timeline = CanonicalTimeline()
    assert timeline.ticks_per_second == 24_000
    assert TickRange(10, 20).contains(10)
    assert not TickRange(10, 20).contains(20)
    assert TickRange(10, 20).duration_ticks == 10
    assert TimelinePlacement(scope_id="scene-1", interval=TickRange(100, 300)).interval.start_tick == 100
    assert GenerationSegmentTimeline(duration_ticks=120).interval == TickRange(0, 120)
    with pytest.raises(DomainValidationError):
        CanonicalTimeline(ticks_per_second=24)
    with pytest.raises(DomainValidationError):
        GenerationSegmentTimeline(start_tick=1, duration_ticks=120)


def test_domain_schema_is_frozen_and_has_one_declared_authority_per_type() -> None:
    module_names = (
        "artifact",
        "ids",
        "time",
        "facts",
        "direction",
        "knowledge",
        "blocking",
        "decisions",
        "vec",
        "projection",
        "evidence",
        "release",
    )
    declared_types: list[str] = []
    for module_name in module_names:
        module = importlib.import_module(f"mode_p_vnext.domain.{module_name}")
        assert module.DOMAIN_SCHEMA_VERSION == "2.1"
        authority = module.CANONICAL_DOMAIN_TYPES
        assert authority, module_name
        assert len(authority) == len(set(authority)), module_name
        declared_types.extend(authority)
    assert len(declared_types) == len(set(declared_types))

    for draft_type in (
        EpisodeDirectionDraft,
        SceneIntentDraft,
        BlockingBeatDraft,
        BlockingDraft,
        ExecutionDesignDraft,
    ):
        assert draft_type.__dataclass_params__.frozen
    for type_name in declared_types:
        for module_name in module_names:
            module = importlib.import_module(f"mode_p_vnext.domain.{module_name}")
            candidate = getattr(module, type_name, None)
            if candidate is not None and dataclasses.is_dataclass(candidate):
                assert candidate.__dataclass_params__.frozen, type_name


def test_domain_has_no_legacy_or_runtime_imports() -> None:
    allowed_stdlib_roots = {
        "__future__",
        "dataclasses",
        "datetime",
        "enum",
        "fractions",
        "hashlib",
        "json",
        "types",
        "typing",
    }
    violations: list[str] = []
    for source_path in DOMAIN_ROOT.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for imported in node.names:
                    root = imported.name.split(".", 1)[0]
                    if root not in allowed_stdlib_roots:
                        violations.append(f"{source_path.name}: import {imported.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                if node.module is None:
                    continue
                root = node.module.split(".", 1)[0]
                if root == "mode_p_vnext" and not node.module.startswith("mode_p_vnext.domain"):
                    violations.append(f"{source_path.name}: from {node.module}")
                elif root not in allowed_stdlib_roots and root != "mode_p_vnext":
                    violations.append(f"{source_path.name}: from {node.module}")
    assert not violations, "\n".join(violations)


def test_compat_is_one_way_and_never_imports_legacy_runtime_code() -> None:
    compat_root = Path(__file__).resolve().parents[1] / "compat"
    violations: list[str] = []
    for source_path in compat_root.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("mode_p_vnext."):
                if not node.module.startswith("mode_p_vnext.domain"):
                    violations.append(f"{source_path.name}: from {node.module}")
    assert not violations, "\n".join(violations)


def test_legacy_checkpoint_adapter_is_read_only_and_returns_canonical_blocking_draft(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "CHECKPOINT_B0_K2.json"
    checkpoint.write_text(
        """
{
  "blocking_commit": {
    "scene_id": "scene-legacy-1",
    "beats": [
      {
        "entry_state_id": "state-entry",
        "exit_state_id": "state-exit",
        "space_control": "established screen direction",
        "dramatic_reason": "the decision becomes visible",
        "dramatic_function": "hold the decision",
        "character_states": [
          {"character_id": "character:lin", "gaze_target": "prop:key"}
        ],
        "prop_states": [
          {"prop_id": "prop:key", "holder": "table"}
        ],
        "action_paths": ["stillness -> decision"]
      }
    ]
  }
}
""".strip(),
        encoding="utf-8",
    )
    original_bytes = checkpoint.read_bytes()
    envelope = read_legacy_b0_k2_checkpoint(checkpoint)

    assert isinstance(envelope, ArtifactEnvelope)
    assert envelope.artifact_kind is ArtifactKind.BLOCKING_DRAFT
    assert isinstance(envelope.payload, BlockingDraft)
    assert envelope.payload.beats
    assert envelope.validation_status is ValidationStatus.DRAFT
    assert all(ref.source_id.startswith("legacy-checkpoint:") for ref in envelope.source_refs)
    assert checkpoint.read_bytes() == original_bytes
    assert envelope.content_sha256 == ArtifactEnvelope.content_digest_for(
        artifact_kind=envelope.artifact_kind,
        schema_version=envelope.schema_version,
        program_version=envelope.program_version,
        payload=envelope.payload,
        source_refs=envelope.source_refs,
        dependency_digests=envelope.dependency_digests,
    )
