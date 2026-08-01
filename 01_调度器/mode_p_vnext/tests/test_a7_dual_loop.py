"""A7 acceptance tests: deterministic Gate 0, independent DP, media boundaries.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9 / §14 A7.

All evidence types are the A1-frozen canonical ``domain.evidence`` types;
A7 adds only the logic: Gate 0, scoped DP packet building, bounded revision
routing, the TEXT_VALIDATED -> VISUAL_EVIDENCED -> OWNER_APPROVED ladder,
and layer attribution for media failures.  Text can never claim visual
acceptance; media failures are attributed to a concrete layer.
"""

from __future__ import annotations

import pytest

from mode_p_vnext.domain.artifact import (
    SourceRef,
    canonical_sha256,
)
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
from mode_p_vnext.domain.evidence import (
    FrameEvidence,
    FrameEvidencePlan,
    MediaRunRecord,
    OutcomeAttribution,
    OwnerApprovalDecision,
    OwnerApprovalRecord,
    RevisionFailureType,
    RevisionRequest,
    VisualVerificationResult,
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
    AttributionLayer,
    ReviewPacket,
    VerificationStatus,
    build_dp_review_packet,
    build_media_evidence,
    build_visual_verification,
    gate0_attribution,
    ladder_status,
    layer_of,
    media_render_attribution,
    media_verify_attribution,
)
from mode_p_vnext.ports.approval import ApprovalPort, OwnerApprovalRecord as _Approval
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


def _media_run() -> MediaRunRecord:
    return MediaRunRecord(
        run_id="run:1",
        provider="sd2",
        request_digest="a" * 64,
        output_refs=(SourceRef(source_id="media/frame_001.png", digest="f" * 64),),
    )


def _frame_evidence(run: MediaRunRecord) -> FrameEvidence:
    return FrameEvidence(
        media_run_id=run.run_id,
        frame_index=0,
        observations=("composition", "subject_state"),
        attributes={"tick": "0", "state": "state:a", "shot": "shot:1"},
    )


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
            episode_direction_artifact_id="episode_direction:0000:" + "a" * 64,
            scene_intent_artifact_id="scene_intent:0000:" + "b" * 64,
        )
        assert isinstance(packet, ReviewPacket)
        assert packet.vec_artifact_id == vec.contract_id
        assert packet.gate_result_refs == (gate0.result_id,)
        assert set(packet.fact_refs) == set(vec.source_fact_ids)
        assert len(packet.projection_artifact_ids) == 2
        assert packet.capability_profile_digest == canonical_sha256("sd2 profile v1")

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
            episode_direction_artifact_id="episode_direction:0000:" + "a" * 64,
            scene_intent_artifact_id="scene_intent:0000:" + "b" * 64,
        )
        # The canonical packet type has no field for private reasoning,
        # prompts, repair conversations, or historical pass labels.
        for forbidden in (
            "director_prompt",
            "private_reasoning",
            "repair_conversation",
            "historical_pass",
            "scene_id",
        ):
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
                episode_direction_artifact_id="episode_direction:0000:" + "a" * 64,
                scene_intent_artifact_id="scene_intent:0000:" + "b" * 64,
            )


# ===================================================================
# required_check: bounded_revision_router
# ===================================================================

class TestBoundedRevisionRouter:
    def _request(self, index: int, failure_type: RevisionFailureType) -> RevisionRequest:
        return RevisionRequest(
            request_id=f"rev:{index}",
            target_artifact_id=f"vec:{index}",
            failure_type=failure_type,
            fact_refs=("char_chen",),
            field_paths=(f"field-{index}",),
            observed_issue=f"issue {index}",
            requested_change="adjust the referenced field",
            evidence_refs=(
                SourceRef(source_id="gate0", digest=f"{index:064x}"),
            ),
        )

    def test_local_derivation_routes_first(self) -> None:
        request = self._request(0, RevisionFailureType.PROJECTION_DIVERGENCE)
        routes = route_revisions((request,), patch_budget=1)
        assert routes[0].kind == RevisionRouteKind.LOCAL_DERIVATION

    def test_scoped_patch_respects_budget(self) -> None:
        # Two creative requests need model patches, but the budget allows one:
        # the first is patched, the second is rejected (fail-closed).
        requests = tuple(
            self._request(i, RevisionFailureType.VISUAL_LOGIC) for i in range(2)
        )
        routes = route_revisions(requests, patch_budget=1)
        kinds = [r.kind for r in routes]
        assert kinds.count(RevisionRouteKind.SCOPED_PATCH) == 1
        assert kinds.count(RevisionRouteKind.REJECT) == 1

    def test_zero_budget_never_patches(self) -> None:
        requests = tuple(
            self._request(i, RevisionFailureType.VISUAL_LOGIC) for i in range(2)
        )
        routes = route_revisions(requests, patch_budget=0)
        assert all(r.kind != RevisionRouteKind.SCOPED_PATCH for r in routes)

    def test_router_never_rewrites_vec(self) -> None:
        # Routing returns requests only; no mutation API exists on the router.
        requests = tuple(
            self._request(i, RevisionFailureType.CONTINUITY) for i in range(2)
        )
        routes = route_revisions(requests, patch_budget=5)
        assert all(isinstance(r, RevisionRoute) for r in routes)
        assert all(r.request.target_artifact_id for r in routes)


# ===================================================================
# required_check: text_cannot_claim_visual_acceptance
# ===================================================================

class TestTextCannotClaimVisualAcceptance:
    def test_text_validation_stays_text_validated(self) -> None:
        status = ladder_status(
            text_ceiling="TEXT_VALIDATED", verification=None, approval=None
        )
        assert status == VerificationStatus.TEXT_VALIDATED

    def test_text_ceiling_cannot_claim_visual(self) -> None:
        with pytest.raises(ValueError, match="claim ceiling"):
            ladder_status(
                text_ceiling="VISUAL_EVIDENCED", verification=None, approval=None
            )

    def test_visual_evidenced_requires_passed_verification_with_frames(
        self, vec: VisualExecutionContract
    ) -> None:
        run = _media_run()
        frames = (_frame_evidence(run),)
        verification = build_visual_verification(
            verification_id="verification:1",
            vec=vec,
            media_run=run,
            frames=frames,
        )
        status = ladder_status(
            text_ceiling="TEXT_VALIDATED", verification=verification, approval=None
        )
        assert status == VerificationStatus.VISUAL_EVIDENCED

    def test_visual_verification_requires_frame_evidence(self, vec: VisualExecutionContract) -> None:
        # Canonical domain type enforces non-empty frame evidence.
        run = _media_run()
        with pytest.raises(ValueError, match="frame_evidence"):
            build_visual_verification(
                verification_id="verification:2",
                vec=vec,
                media_run=run,
                frames=(),
            )

    def test_owner_approved_requires_explicit_approval_record(
        self, vec: VisualExecutionContract
    ) -> None:
        run = _media_run()
        verification = build_visual_verification(
            verification_id="verification:3",
            vec=vec,
            media_run=run,
            frames=(_frame_evidence(run),),
        )
        approval = OwnerApprovalRecord(
            approval_id="approval:1",
            visual_verification_artifact_id=verification.verification_id,
            decision=OwnerApprovalDecision.APPROVED,
            approved_by="OWNER",
            evidence_ref=SourceRef(
                source_id="approval/session.json", digest="a" * 64
            ),
        )
        status = ladder_status(
            text_ceiling="TEXT_VALIDATED", verification=verification, approval=approval
        )
        assert status == VerificationStatus.OWNER_APPROVED

    def test_owner_approval_must_bind_exact_verification(
        self, vec: VisualExecutionContract
    ) -> None:
        run = _media_run()
        verification = build_visual_verification(
            verification_id="verification:4",
            vec=vec,
            media_run=run,
            frames=(_frame_evidence(run),),
        )
        dangling = OwnerApprovalRecord(
            approval_id="approval:2",
            visual_verification_artifact_id="verification:other",
            decision=OwnerApprovalDecision.APPROVED,
            approved_by="OWNER",
            evidence_ref=SourceRef(
                source_id="approval/session.json", digest="b" * 64
            ),
        )
        with pytest.raises(ValueError, match="bind"):
            ladder_status(
                text_ceiling="TEXT_VALIDATED",
                verification=verification,
                approval=dangling,
            )

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
        assert layer_of(attribution) == AttributionLayer.GATE0

    def test_media_render_failure_attributes_to_media_layer(self) -> None:
        attribution = media_render_attribution(
            scene_id=SCENE_ID,
            renderer_version="sd2-1.0",
            reason="renderer timeout",
        )
        assert layer_of(attribution) == AttributionLayer.MEDIA_RENDER
        assert attribution.supporting_evidence
        assert "renderer timeout" in attribution.cause

    def test_media_verify_failure_attributes_to_verifier_layer(self) -> None:
        attribution = media_verify_attribution(
            scene_id=SCENE_ID,
            verifier_version="frame-check-1.0",
            reason="frame hash mismatch",
        )
        assert layer_of(attribution) == AttributionLayer.MEDIA_VERIFY

    def test_frame_evidence_plan_tracks_checks_and_indices(self) -> None:
        plan = FrameEvidencePlan(
            plan_id="plan:1",
            vec_artifact_id="vec:1",
            checks=("composition", "subject_state"),
            frame_indices=(0, 12, 24),
        )
        assert plan.frame_indices == (0, 12, 24)
        assert "composition" in plan.checks

    def test_attribution_is_required_for_failed_verification(self) -> None:
        # A media verification failure carries a layer attribution; the
        # canonical VisualVerificationResult binds attributions to the result.
        attribution = media_verify_attribution(
            scene_id=SCENE_ID,
            verifier_version="frame-check-1.0",
            reason="no frames captured",
        )
        assert layer_of(attribution) == AttributionLayer.MEDIA_VERIFY
        assert attribution.result_id
        assert attribution.confidence == "high"
