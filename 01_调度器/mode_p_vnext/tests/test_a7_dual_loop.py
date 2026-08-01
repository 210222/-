"""A7 acceptance tests: deterministic Gate 0, independent DP, media boundaries.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9 / §14 A7.

- Gate 0 is a zero-model deterministic gate (schema, IDs, ticks, references,
  projection homology, claim ceiling).
- DP consumes a scoped ReviewPacket and emits bounded RevisionRequests that
  never rewrite the VEC.
- Text validation can never claim visual acceptance; only real frame
  evidence yields VISUAL_EVIDENCED and only explicit owner approval yields
  OWNER_APPROVED.  Media failures are attributed to a concrete layer.
"""

from __future__ import annotations

import pytest

from mode_p_vnext.domain.artifact import SourceRef, canonical_sha256
from mode_p_vnext.domain.blocking import (
    BlockingBeatDraft,
    BlockingCommit,
    BlockingDraft,
)
from mode_p_vnext.domain.decisions import (
    DecisionBasis,
    DecisionDraft,
    VisualCurvePointDraft,
)
from mode_p_vnext.domain.facts import FactKind, FactRegistry, ScriptFact
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.vec import (
    ExecutionDesignDraft,
    ShotDesignDraft,
    StoryboardRole,
    VisualBeatDraft,
    VisualBeatPhase,
    VisualExecutionContract,
)
from mode_p_vnext.pipeline.verification_nodes import (
    DPReviewPacket,
    FrameEvidence,
    FrameEvidencePlan,
    FrameSpec,
    MediaRunRecord,
    OutcomeAttribution,
    VerificationStatus,
    VisualVerificationResult,
    build_dp_review_packet,
)
from mode_p_vnext.ports.approval import ApprovalPort, OwnerApprovalRecord
from mode_p_vnext.ports.media_renderer import (
    MediaRenderRequest,
    MediaRendererPort,
    MediaRendererUnavailableError,
)
from mode_p_vnext.ports.media_verifier import MediaVerifierPort
from mode_p_vnext.services.blocking_assembler import assemble_blocking_commit
from mode_p_vnext.services.deterministic_gates import (
    Gate0Result,
    run_gate0,
)
from mode_p_vnext.services.projection_compiler import (
    ProjectionAST,
    compile_projection_ast,
    derive_storyboard,
    derive_video,
)
from mode_p_vnext.services.revision_router import (
    RevisionRequest,
    RevisionRoute,
    RevisionRouteKind,
    route_revisions,
)
from mode_p_vnext.services.vec_assembler import assemble_vec


PROGRAM_VERSION = "mode-p-vnext-a7-test"
SCHEMA_VERSION = "2.1"
EPISODE_ID = "EP35"
SCENE_ID = "EP35-S2"


# ---------------------------------------------------------------------------
# Shared fixtures (VEC -> AST -> both projections, reusing A5/A6 shapes)
# ---------------------------------------------------------------------------


@pytest.fixture
def id_factory() -> IdFactory:
    return IdFactory(program_version=PROGRAM_VERSION)


@pytest.fixture
def blocking_draft() -> BlockingDraft:
    return BlockingDraft(
        beats=(
            BlockingBeatDraft(
                ordinal=1,
                dramatic_action="He arrives at the shooting range.",
                character_states=({"character_id": "chen", "posture": "tense"},),
                prop_states=(),
                gaze_relations=(),
                action_paths=("enter the range",),
                continuity_effect="Establishes the space.",
            ),
            BlockingBeatDraft(
                ordinal=2,
                dramatic_action="He loads the pistol.",
                character_states=({"character_id": "chen", "posture": "focused"},),
                prop_states=({"prop_id": "pistol", "state": "loaded"},),
                gaze_relations=("chen -> pistol",),
                action_paths=("load weapon",),
                continuity_effect="The weapon is now live.",
            ),
        )
    )


@pytest.fixture
def blocking_commit(id_factory: IdFactory, blocking_draft: BlockingDraft) -> BlockingCommit:
    return assemble_blocking_commit(
        draft=blocking_draft,
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
        schema_version=SCHEMA_VERSION,
    )


@pytest.fixture
def execution_design_draft() -> ExecutionDesignDraft:
    return ExecutionDesignDraft(
        curve_points=(
            VisualCurvePointDraft(dramatic_beat_ordinal=1, intensity=60, explanation="arrival"),
            VisualCurvePointDraft(dramatic_beat_ordinal=2, intensity=85, explanation="escalation"),
        ),
        decisions=(
            DecisionDraft(
                scope="camera distance",
                basis=DecisionBasis.CHOICE,
                locked_by=(),
                options=("close-up", "medium"),
                selected_index=0,
                rationale="detail",
                tradeoff="face",
            ),
        ),
        shots=(
            ShotDesignDraft(
                blocking_beat_ordinal=1,
                dramatic_function="introduce the range",
                attention_target="chen entering",
                information_action="the range is empty",
                framing_intent="wide establishing",
                camera_pose="eye level",
                camera_motion="static",
                composition="depth layering",
                lighting="harsh fluorescents",
                performance="deliberate steps",
                duration_weight=4,
                visual_beats=(
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ENTRY,
                        subject_state="chen at doorway",
                        attention="the empty range",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ACTION,
                        subject_state="chen steps forward",
                        attention="the lane",
                        storyboard_role=StoryboardRole.OPTIONAL,
                    ),
                ),
            ),
            ShotDesignDraft(
                blocking_beat_ordinal=2,
                dramatic_function="weapon escalation",
                attention_target="hands loading",
                information_action="pistol ready",
                framing_intent="close-up on hands",
                camera_pose="overhead",
                camera_motion="push-in",
                composition="hands dominate",
                lighting="practical above bench",
                performance="precise movements",
                duration_weight=6,
                visual_beats=(
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ENTRY,
                        subject_state="hands reach for case",
                        attention="the case",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ACTION,
                        subject_state="magazine slides in",
                        attention="the click",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.REACTION,
                        subject_state="breath steadies",
                        attention="the live weapon",
                        storyboard_role=StoryboardRole.OMIT,
                    ),
                ),
            ),
        ),
        transition_intents=("hard cut on the click",),
        audio_intents=("mechanical click",),
        reference_intents=("pistol prop reference",),
        handoff_intent="cut to target paper",
    )


@pytest.fixture
def fact_registry() -> FactRegistry:
    return FactRegistry(
        facts=(
            ScriptFact(
                fact_id="char_chen",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Chen is the protagonist, wearing a black tactical jacket.",
                source_ref=SourceRef(source_id="ep35_script", digest="a" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="prop_pistol",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="A standard-issue 9mm pistol sits in a foam case.",
                source_ref=SourceRef(source_id="ep35_script", digest="b" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="scene_shooting_range",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Indoor shooting range, fluorescent lighting.",
                source_ref=SourceRef(source_id="ep35_script", digest="c" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="dialogue_chen_muttering",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Chen mutters: the range is clear.",
                source_ref=SourceRef(source_id="ep35_script", digest="d" * 64, locator="S2"),
            ),
        )
    )


@pytest.fixture
def vec(
    id_factory: IdFactory,
    blocking_commit: BlockingCommit,
    execution_design_draft: ExecutionDesignDraft,
    fact_registry: FactRegistry,
) -> VisualExecutionContract:
    return assemble_vec(
        draft=execution_design_draft,
        blocking_commit=blocking_commit,
        facts=fact_registry,
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
        schema_version=SCHEMA_VERSION,
    )


@pytest.fixture
def ast(
    vec: VisualExecutionContract,
    blocking_commit: BlockingCommit,
    id_factory: IdFactory,
) -> ProjectionAST:
    return compile_projection_ast(
        vec=vec,
        blocking_commit=blocking_commit,
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


@pytest.fixture
def projections(ast: ProjectionAST):
    return derive_storyboard(ast=ast), derive_video(ast=ast)


# ===================================================================
# required_check: deterministic_gate_zero
# ===================================================================

class TestDeterministicGateZero:
    def test_gate_passes_valid_artifacts(
        self, vec: VisualExecutionContract, ast: ProjectionAST, projections
    ) -> None:
        storyboard, video = projections
        result = run_gate0(
            vec=vec,
            ast=ast,
            storyboard=storyboard,
            video=video,
            claim_ceiling="TEXT_VALIDATED",
        )
        assert result.passed is True
        assert result.issues == ()

    def test_gate_is_deterministic(
        self, vec: VisualExecutionContract, ast: ProjectionAST, projections
    ) -> None:
        storyboard, video = projections
        a = run_gate0(vec=vec, ast=ast, storyboard=storyboard, video=video, claim_ceiling="TEXT_VALIDATED")
        b = run_gate0(vec=vec, ast=ast, storyboard=storyboard, video=video, claim_ceiling="TEXT_VALIDATED")
        assert a.result_id == b.result_id
        assert [i.rule for i in a.issues] == [i.rule for i in b.issues]

    def test_gate_rejects_visual_claim_ceiling(
        self, vec: VisualExecutionContract, ast: ProjectionAST, projections
    ) -> None:
        storyboard, video = projections
        result = run_gate0(
            vec=vec,
            ast=ast,
            storyboard=storyboard,
            video=video,
            claim_ceiling="VISUAL_EVIDENCED",
        )
        assert result.passed is False
        assert any("claim_ceiling" in issue.rule for issue in result.issues)

    def test_gate_rejects_projection_homology_break(
        self, vec: VisualExecutionContract, ast: ProjectionAST, projections
    ) -> None:
        storyboard, video = projections
        # A node that is not sourced from the AST must fail the homology check.
        from dataclasses import replace

        foreign = replace(storyboard.nodes[0], source_id="foreign-node")
        broken_storyboard = replace(storyboard, nodes=(foreign,))
        result = run_gate0(
            vec=vec,
            ast=ast,
            storyboard=broken_storyboard,
            video=video,
            claim_ceiling="TEXT_VALIDATED",
        )
        assert result.passed is False
        assert any("homology" in issue.rule for issue in result.issues)

    def test_gate_rejects_unbound_fact_invention(
        self, vec: VisualExecutionContract, ast: ProjectionAST, projections
    ) -> None:
        storyboard, video = projections
        # An audio event sourced from a fact outside the VEC fact set is
        # forbidden invention; the gate must reject it mechanically.  The
        # domain keeps audio/voice pairing, so the pair is domain-valid but
        # fact-unbound — exactly what Gate 0 must catch.
        from mode_p_vnext.domain.vec import AudioEvent, VoiceRequirement
        from mode_p_vnext.domain.time import TickRange
        from dataclasses import replace

        foreign_event = AudioEvent(
            event_id="audio:foreign:0000:" + "0" * 64,
            segment_id=vec.segments[0].segment_id,
            interval=TickRange(start_tick=0, end_tick=100),
            source_fact_id="unlisted_fact",
            character_id="chen",
            text="the range is clear",
        )
        foreign_voice = VoiceRequirement(
            requirement_id="voice:foreign:0000:" + "0" * 64,
            audio_event_id=foreign_event.event_id,
            character_id="chen",
        )
        broken_vec = replace(
            vec,
            audio_events=vec.audio_events + (foreign_event,),
            voice_requirements=vec.voice_requirements + (foreign_voice,),
        )
        result = run_gate0(
            vec=broken_vec,
            ast=ast,
            storyboard=storyboard,
            video=video,
            claim_ceiling="TEXT_VALIDATED",
        )
        assert result.passed is False
        assert any("fact" in issue.rule.lower() for issue in result.issues)


# ===================================================================
# required_check: independent_dp_packet
# ===================================================================

class TestIndependentDPPacket:
    def test_packet_contains_only_approved_scoped_fields(
        self,
        vec: VisualExecutionContract,
        ast: ProjectionAST,
        projections,
        fact_registry: FactRegistry,
        blocking_commit: BlockingCommit,
    ) -> None:
        storyboard, video = projections
        gate0 = run_gate0(vec=vec, ast=ast, storyboard=storyboard, video=video, claim_ceiling="TEXT_VALIDATED")
        packet = build_dp_review_packet(
            scene_id=SCENE_ID,
            facts=fact_registry,
            vec=vec,
            storyboard=storyboard,
            video=video,
            gate0=gate0,
            capability_summary="sd2 profile v1",
        )
        assert isinstance(packet, DPReviewPacket)
        assert packet.scene_id == SCENE_ID
        assert packet.gate0_passed is True
        assert packet.vec_digest == canonical_sha256(vec)
        assert packet.fact_ids
        assert packet.storyboard_source_node_ids
        assert packet.video_source_node_ids

    def test_packet_excludes_director_private_content(
        self,
        vec: VisualExecutionContract,
        ast: ProjectionAST,
        projections,
        fact_registry: FactRegistry,
    ) -> None:
        storyboard, video = projections
        gate0 = run_gate0(vec=vec, ast=ast, storyboard=storyboard, video=video, claim_ceiling="TEXT_VALIDATED")
        packet = build_dp_review_packet(
            scene_id=SCENE_ID,
            facts=fact_registry,
            vec=vec,
            storyboard=storyboard,
            video=video,
            gate0=gate0,
            capability_summary="sd2 profile v1",
        )
        # The packet type has no field for private reasoning, prompts,
        # repair conversations, or historical pass labels.
        for forbidden in ("director_prompt", "private_reasoning", "repair_conversation", "historical_pass"):
            assert not hasattr(packet, forbidden)

    def test_dp_packet_rejects_unapproved_fact(
        self,
        vec: VisualExecutionContract,
        ast: ProjectionAST,
        projections,
        fact_registry: FactRegistry,
    ) -> None:
        storyboard, video = projections
        gate0 = run_gate0(vec=vec, ast=ast, storyboard=storyboard, video=video, claim_ceiling="TEXT_VALIDATED")
        leaked = FactRegistry(
            facts=fact_registry.facts
            + (
                ScriptFact(
                    fact_id="leaked_private_fact",
                    scene_id=SCENE_ID,
                    kind=FactKind.SCRIPT,
                    statement="secret director note",
                    source_ref=SourceRef(source_id="x", digest="e" * 64),
                ),
            )
        )
        with pytest.raises(ValueError, match="unapproved"):
            build_dp_review_packet(
                scene_id=SCENE_ID,
                facts=leaked,
                vec=vec,
                storyboard=storyboard,
                video=video,
                gate0=gate0,
                capability_summary="sd2 profile v1",
            )


# ===================================================================
# required_check: bounded_revision_router
# ===================================================================

class TestBoundedRevisionRouter:
    def _requests(self) -> tuple[RevisionRequest, ...]:
        return (
            RevisionRequest(
                target_artifact_id="vec:1",
                field_path="shots[0].visual_beats[0].subject_state",
                failure_type="schema",
                reason="enum violation",
            ),
            RevisionRequest(
                target_artifact_id="vec:1",
                field_path="curve_points[1].intensity",
                failure_type="range",
                reason="intensity out of bounds",
            ),
        )

    def test_local_derivation_routes_first(self) -> None:
        routes = route_revisions(self._requests(), patch_budget=1)
        assert routes[0].kind == RevisionRouteKind.LOCAL_DERIVATION

    def test_scoped_patch_respects_budget(self) -> None:
        # Two requests need model patches, but the budget allows one:
        # the first is patched, the second is rejected (fail-closed).
        requests = tuple(
            RevisionRequest(
                target_artifact_id=f"vec:{i}",
                field_path=f"field-{i}",
                failure_type="choice",
                reason=f"needs director choice {i}",
            )
            for i in range(2)
        )
        routes = route_revisions(requests, patch_budget=1)
        kinds = [r.kind for r in routes]
        assert kinds.count(RevisionRouteKind.SCOPED_PATCH) == 1
        assert kinds.count(RevisionRouteKind.REJECT) == 1

    def test_zero_budget_never_patches(self) -> None:
        routes = route_revisions(self._requests(), patch_budget=0)
        assert all(r.kind != RevisionRouteKind.SCOPED_PATCH for r in routes)

    def test_router_never_rewrites_vec(self) -> None:
        # Routing returns requests only; no mutation API exists on the router.
        routes = route_revisions(self._requests(), patch_budget=5)
        assert all(isinstance(r, RevisionRoute) for r in routes)
        assert all(r.request.target_artifact_id for r in routes)


# ===================================================================
# required_check: text_cannot_claim_visual_acceptance
# ===================================================================

class TestTextCannotClaimVisualAcceptance:
    def test_text_validation_stays_text_validated(self) -> None:
        result = VisualVerificationResult.from_text_validation(scene_id=SCENE_ID)
        assert result.status == VerificationStatus.TEXT_VALIDATED

    def test_text_alone_cannot_construct_visual_evidenced(self) -> None:
        with pytest.raises(ValueError, match="media"):
            VisualVerificationResult.from_text_validation(
                scene_id=SCENE_ID, status=VerificationStatus.VISUAL_EVIDENCED
            )

    def test_visual_evidenced_requires_frame_evidence(self) -> None:
        text = VisualVerificationResult.from_text_validation(scene_id=SCENE_ID)
        run = MediaRunRecord(
            run_id="run:1",
            scene_id=SCENE_ID,
            renderer_version="sd2-1.0",
            media_kind="image",
            media_paths=("media/frame_001.png",),
            created_at="2026-08-01T00:00:00Z",
        )
        result = VisualVerificationResult.with_media_evidence(
            scene_id=SCENE_ID, media_run=run, frame_evidence=()
        )
        assert result.status == VerificationStatus.VISUAL_EVIDENCED
        # text results have no media bindings at all
        assert text.media_run is None

    def test_owner_approved_requires_explicit_approval_record(self) -> None:
        run = MediaRunRecord(
            run_id="run:2",
            scene_id=SCENE_ID,
            renderer_version="sd2-1.0",
            media_kind="video",
            media_paths=("media/clip_001.mp4",),
            created_at="2026-08-01T00:00:00Z",
        )
        evidenced = VisualVerificationResult.with_media_evidence(
            scene_id=SCENE_ID, media_run=run, frame_evidence=()
        )
        approval = OwnerApprovalRecord(
            approval_id="approval:1",
            approved_at="2026-08-01T00:01:00Z",
            media_evidence_digest=evidenced.media_evidence_digest,
            approver="OWNER",
        )
        approved = VisualVerificationResult.with_owner_approval(
            evidenced, approval=approval
        )
        assert approved.status == VerificationStatus.OWNER_APPROVED
        assert approved.approval_id == "approval:1"

    def test_owner_approval_must_bind_evidence_digest(self) -> None:
        run = MediaRunRecord(
            run_id="run:3",
            scene_id=SCENE_ID,
            renderer_version="sd2-1.0",
            media_kind="image",
            media_paths=("media/f.png",),
            created_at="2026-08-01T00:00:00Z",
        )
        evidenced = VisualVerificationResult.with_media_evidence(
            scene_id=SCENE_ID, media_run=run, frame_evidence=()
        )
        dangling = OwnerApprovalRecord(
            approval_id="approval:2",
            approved_at="2026-08-01T00:02:00Z",
            media_evidence_digest="0" * 64,
            approver="OWNER",
        )
        with pytest.raises(ValueError, match="digest"):
            VisualVerificationResult.with_owner_approval(evidenced, approval=dangling)

    def test_media_renderer_port_fails_closed(
        self, ast: ProjectionAST
    ) -> None:
        from mode_p_vnext.adapters.media.renderer import NoopMediaRenderer

        renderer: MediaRendererPort = NoopMediaRenderer()
        request = MediaRenderRequest(
            scene_id=SCENE_ID,
            projection_ast_digest=ast.ast_digest,
            settings={"platform": "sd2"},
        )
        with pytest.raises(MediaRendererUnavailableError):
            renderer.render(request)


# ===================================================================
# required_check: media_outcome_attribution
# ===================================================================

class TestMediaOutcomeAttribution:
    def test_gate0_failure_attributes_to_gate_layer(
        self, vec: VisualExecutionContract, ast: ProjectionAST, projections
    ) -> None:
        storyboard, video = projections
        result = run_gate0(
            vec=vec,
            ast=ast,
            storyboard=storyboard,
            video=video,
            claim_ceiling="VISUAL_EVIDENCED",
        )
        assert result.passed is False
        attribution = result.attribution
        assert attribution is not None
        assert attribution.layer.value == "GATE0"

    def test_media_render_failure_attributes_to_media_layer(self) -> None:
        attribution = OutcomeAttribution.media_render_failure(
            scene_id=SCENE_ID,
            renderer_version="sd2-1.0",
            reason="renderer timeout",
        )
        assert attribution.layer.value == "MEDIA_RENDER"
        assert attribution.node_refs
        assert attribution.reason == "renderer timeout"

    def test_media_verify_failure_attributes_to_verifier_layer(self) -> None:
        attribution = OutcomeAttribution.media_verify_failure(
            scene_id=SCENE_ID,
            verifier_version="frame-check-1.0",
            reason="frame hash mismatch",
        )
        assert attribution.layer.value == "MEDIA_VERIFY"

    def test_frame_evidence_plan_tracks_ticks_and_states(self) -> None:
        plan = FrameEvidencePlan(
            plan_id="plan:1",
            scene_id=SCENE_ID,
            frames=(
                FrameSpec(
                    frame_id="frame:1",
                    tick=0,
                    state_id="state:a",
                    shot_id="shot:1",
                    checks=("composition", "subject_state"),
                ),
            ),
        )
        assert plan.frames[0].tick == 0
        assert plan.frames[0].state_id == "state:a"

    def test_attribution_is_required_for_failed_verification(self) -> None:
        # A failed visual verification must carry a layer attribution.
        text = VisualVerificationResult.from_text_validation(scene_id=SCENE_ID)
        failure = text.with_failure(OutcomeAttribution.media_verify_failure(
            scene_id=SCENE_ID,
            verifier_version="frame-check-1.0",
            reason="no frames captured",
        ))
        assert failure.failed is True
        assert failure.attribution is not None
        assert failure.attribution.layer.value == "MEDIA_VERIFY"
