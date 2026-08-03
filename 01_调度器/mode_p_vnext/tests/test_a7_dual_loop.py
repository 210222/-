"""A7 acceptance tests for the frozen v3.1 dual-loop boundary."""

from __future__ import annotations

from dataclasses import fields, replace
import inspect
import json

import pytest

from mode_p_vnext.adapters.media.renderer import NoopMediaRenderer
from mode_p_vnext.adapters.media.verifier import NoopMediaVerifier
from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    SourceRef,
    canonical_sha256,
)
from mode_p_vnext.domain.evidence import (
    DPReviewVerdict,
    DeterministicGateResult,
    FrameEvidence,
    FrameEvidencePlan,
    MediaRunRecord,
    OutcomeAttribution,
    RevisionFailureType,
)
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.vec import VisualExecutionContract
from mode_p_vnext.pipeline.verification_nodes import (
    AttributionLayer,
    DPInputBlockedError,
    DPReviewDraft,
    FreshDPContext,
    RevisionRequestDraft,
    VerificationStatus,
    assemble_fresh_dp_review,
    build_dp_review_packet,
    build_frame_evidence_plan,
    build_media_evidence,
    build_visual_verification,
    gate0_attribution,
    gate_result_source_ref,
    ladder_status,
    layer_of,
    media_render_attribution,
    media_verify_attribution,
    start_fresh_dp_context,
)
from mode_p_vnext.ports.approval import ApprovalDecisionDraft, ApprovalPort
from mode_p_vnext.ports.media_renderer import (
    MediaRenderRequest,
    MediaRendererPort,
    MediaRendererUnavailableError,
)
from mode_p_vnext.ports.media_verifier import (
    MediaVerificationOutput,
    MediaVerificationUnavailableError,
    MediaVerifierPort,
)
from mode_p_vnext.prompts.compiler import PromptCompiler
from mode_p_vnext.prompts.signatures import Stage, stage_signatures
from mode_p_vnext.services.blocking_assembler import assemble_blocking_commit
from mode_p_vnext.services.deterministic_gates import (
    CLAIM_CEILING,
    DIGEST_INTEGRITY,
    GATE0_CHECK_IDS,
    ID_INTEGRITY,
    PROMPT_BUDGET,
    PROJECTION_IDENTITY,
    SCHEMA_INTEGRITY,
    SAFETY_BOUNDARY,
    run_gate0,
)
from mode_p_vnext.services.projection_compiler import (
    compile_projection_ast,
    derive_storyboard,
    derive_video,
)
from mode_p_vnext.services.revision_router import (
    RevisionRouteKind,
    RevisionScope,
    route_revisions,
)
from mode_p_vnext.services.vec_assembler import assemble_vec
from mode_p_vnext.tests.test_a6_projection_compiler import (
    EPISODE_ID,
    SCENE_ID,
    make_blocking_draft,
    make_execution_draft,
    make_facts,
)


PROGRAM_VERSION = "mode-p-vnext-a7-v3-test"


@pytest.fixture
def id_factory() -> IdFactory:
    return IdFactory(program_version=PROGRAM_VERSION)


@pytest.fixture
def facts():
    return make_facts()


@pytest.fixture
def blocking_commit(id_factory: IdFactory):
    return assemble_blocking_commit(
        draft=make_blocking_draft(),
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


@pytest.fixture
def vec(id_factory: IdFactory, blocking_commit, facts) -> VisualExecutionContract:
    return assemble_vec(
        draft=make_execution_draft(),
        blocking_commit=blocking_commit,
        facts=facts,
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


@pytest.fixture
def projections(id_factory: IdFactory, blocking_commit, vec):
    ast = compile_projection_ast(
        vec=vec,
        blocking_commit=blocking_commit,
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )
    return ast, derive_storyboard(ast), derive_video(ast)


@pytest.fixture
def compiled_prompt():
    return PromptCompiler().compile(
        stage_signatures()[Stage.B1],
        {"scene_id": SCENE_ID},
    )


def gate(id_factory, vec, projections, compiled_prompt, **overrides):
    ast, storyboard, video = projections
    values = {
        "vec": vec,
        "ast": ast,
        "storyboard": storyboard,
        "video": video,
        "compiled_prompts": (compiled_prompt,),
        "claim_ceiling": "TEXT_VALIDATED",
        "id_factory": id_factory,
        "program_version": PROGRAM_VERSION,
    }
    values.update(overrides)
    return run_gate0(**values)


@pytest.fixture
def gate0(id_factory, vec, projections, compiled_prompt):
    return gate(id_factory, vec, projections, compiled_prompt)


@pytest.fixture
def packet(id_factory, facts, vec, projections, gate0):
    ast, storyboard, video = projections
    return build_dp_review_packet(
        facts=facts,
        vec=vec,
        ast=ast,
        storyboard=storyboard,
        video=video,
        gate0=gate0,
        episode_direction_artifact_id="id:" + "e" * 64,
        scene_intent_artifact_id="id:" + "d" * 64,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


def director_scope(vec: VisualExecutionContract) -> RevisionScope:
    return RevisionScope(
        target_artifact_id=vec.contract_id,
        route_kind=RevisionRouteKind.DIRECTOR_DRAFT_REVISION,
        allowed_field_paths=("shots.0.camera", "shots.1.performance"),
    )


def fresh_context(packet, id_factory: IdFactory, attempt_ordinal: int):
    return start_fresh_dp_context(
        packet,
        id_factory=id_factory,
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        program_version=PROGRAM_VERSION,
        attempt_ordinal=attempt_ordinal,
    )


def revision_draft(packet, vec, evidence_ref: SourceRef, *, path="shots.0.camera"):
    return DPReviewDraft(
        verdict=DPReviewVerdict.REVISION_REQUIRED,
        finding_codes=("VISUAL_LOGIC_CAMERA",),
        revision_requests=(
            RevisionRequestDraft(
                target_artifact_id=vec.contract_id,
                failure_type=RevisionFailureType.VISUAL_LOGIC,
                fact_refs=(packet.fact_refs[0],),
                field_paths=(path,),
                observed_issue="camera intent obscures the approved subject",
                requested_change="revise only the bounded camera intent",
                evidence_ref_ids=(evidence_ref.source_id,),
            ),
        ),
    )


# required_check: deterministic_gate_zero
class TestDeterministicGateZero:
    def test_valid_v3_artifacts_return_only_canonical_result(self, gate0):
        assert type(gate0) is DeterministicGateResult
        assert gate0.passed
        assert gate0.check_ids == GATE0_CHECK_IDS
        assert gate0.failed_check_ids == ()

    def test_identical_inputs_are_deterministic(
        self, id_factory, vec, projections, compiled_prompt, gate0
    ):
        assert gate(id_factory, vec, projections, compiled_prompt) == gate0

    def test_corrupt_vec_digest_and_cross_authority_id_fail(self, id_factory, vec, projections, compiled_prompt):
        bad_vec = replace(vec, canonical_output_sha256="0" * 64)
        digest_result = gate(id_factory, bad_vec, projections, compiled_prompt)
        assert not digest_result.passed
        assert "digest_integrity" in digest_result.failed_check_ids

        ast, storyboard, video = projections
        collided_ast = replace(ast, projection_id=vec.contract_id)
        collided_views = (
            collided_ast,
            derive_storyboard(collided_ast),
            derive_video(collided_ast),
        )
        id_result = gate(
            id_factory,
            vec,
            collided_views,
            compiled_prompt,
            ast=collided_ast,
            storyboard=collided_views[1],
            video=collided_views[2],
        )
        assert "id_integrity" in id_result.failed_check_ids

    def test_projection_ids_must_be_rederived_from_vec_and_frozen_compiler(
        self, id_factory, vec, projections, compiled_prompt
    ):
        """A machine-shaped foreign AST ID cannot satisfy Gate 0 identity."""

        ast, _, _ = projections
        forged_ast = replace(ast, projection_id="id:" + "f" * 64)
        result = gate(
            id_factory,
            vec,
            (forged_ast, derive_storyboard(forged_ast), derive_video(forged_ast)),
            compiled_prompt,
        )
        assert not result.passed
        assert ID_INTEGRITY in result.failed_check_ids

    def test_projection_capability_divergence_fails(self, id_factory, vec, projections, compiled_prompt):
        ast, storyboard, video = projections
        bad_manifest = replace(
            storyboard.manifest,
            capability_profile_digest="0" * 64,
        )
        bad_storyboard = replace(storyboard, manifest=bad_manifest)
        result = gate(
            id_factory,
            vec,
            (ast, bad_storyboard, video),
            compiled_prompt,
            storyboard=bad_storyboard,
        )
        assert not result.passed
        assert PROJECTION_IDENTITY in result.failed_check_ids

    def test_adapter_only_recompile_remains_a_valid_projection_view(
        self, id_factory, vec, projections, compiled_prompt
    ):
        """A6 allows adapter change without replacing the canonical AST."""

        ast, storyboard, _ = projections
        adapted_video = derive_video(ast, adapter_version="video-adapter-v3.1.0")
        result = gate(
            id_factory,
            vec,
            (ast, storyboard, adapted_video),
            compiled_prompt,
        )
        assert result.passed

    def test_prompt_budget_and_safety_are_revalidated(self, id_factory, vec, projections, compiled_prompt):
        bad_report = replace(
            compiled_prompt.budget_report,
            character_count=compiled_prompt.character_count + 1,
        )
        budget_result = gate(
            id_factory,
            vec,
            projections,
            compiled_prompt,
            compiled_prompts=(replace(compiled_prompt, budget_report=bad_report),),
        )
        assert PROMPT_BUDGET in budget_result.failed_check_ids

        unsafe = replace(
            compiled_prompt,
            user_message=compiled_prompt.user_message[:-1] + ',"dp_history":[]}',
        )
        safety_result = gate(
            id_factory,
            vec,
            projections,
            compiled_prompt,
            compiled_prompts=(unsafe,),
        )
        assert SAFETY_BOUNDARY in safety_result.failed_check_ids

    def test_compiled_prompt_input_digest_is_rederived(self, id_factory, vec, projections, compiled_prompt):
        """A same-length prompt substitution cannot retain a stale digest."""

        payload = json.loads(compiled_prompt.user_message)
        original_scene_id = payload["approved_input"]["scene_id"]
        payload["approved_input"]["scene_id"] = "x" * len(original_scene_id)
        tampered = replace(
            compiled_prompt,
            user_message=json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
        assert len(tampered.prompt_text) == len(compiled_prompt.prompt_text)
        result = gate(
            id_factory,
            vec,
            projections,
            compiled_prompt,
            compiled_prompts=(tampered,),
        )
        assert not result.passed
        assert DIGEST_INTEGRITY in result.failed_check_ids

    def test_malformed_compiled_prompt_fails_as_a_gate_result(
        self, id_factory, vec, projections, compiled_prompt
    ):
        malformed = replace(compiled_prompt, signature=object())
        result = gate(
            id_factory,
            vec,
            projections,
            compiled_prompt,
            compiled_prompts=(malformed,),
        )
        assert not result.passed
        assert SCHEMA_INTEGRITY in result.failed_check_ids

    def test_text_cannot_raise_its_claim_ceiling(self, id_factory, vec, projections, compiled_prompt):
        result = gate(
            id_factory,
            vec,
            projections,
            compiled_prompt,
            claim_ceiling="VISUAL_EVIDENCED",
        )
        assert CLAIM_CEILING in result.failed_check_ids


# required_check: fresh_independent_dp_packet
class TestFreshIndependentDPPacket:
    def test_packet_contains_refs_not_fact_text_or_private_state(self, packet, vec, projections, gate0):
        ast, _, _ = projections
        assert packet.fact_refs == tuple(sorted(vec.approved_fact_handles))
        assert packet.projection_artifact_ids == (ast.projection_id,)
        assert packet.gate_result_refs == (gate0.result_id,)
        assert packet.capability_profile_digest == canonical_sha256(vec.capability_profile)
        packet_fields = {item.name for item in fields(packet)}
        assert packet_fields.isdisjoint(
            {"facts", "statements", "private_reasoning", "dp_history", "runtime_code", "telemetry", "cache"}
        )

    def test_packet_rejects_unapproved_fact_scope(self, id_factory, facts, vec, projections, gate0):
        ast, storyboard, video = projections
        smaller_vec = replace(
            vec,
            source_fact_ids=vec.source_fact_ids[:-1],
            approved_fact_handles=vec.approved_fact_handles[:-1],
        )
        with pytest.raises(DomainValidationError):
            build_dp_review_packet(
                facts=facts,
                vec=smaller_vec,
                ast=ast,
                storyboard=storyboard,
                video=video,
                gate0=gate0,
                episode_direction_artifact_id="id:" + "e" * 64,
                scene_intent_artifact_id="id:" + "d" * 64,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
            )

    def test_packet_rejects_a_passed_gate_result_without_local_identity(
        self, id_factory, facts, vec, projections, gate0
    ):
        ast, storyboard, video = projections
        forged_gate = replace(gate0, result_id="id:" + "f" * 64)
        with pytest.raises(DomainValidationError, match="Gate 0 result"):
            build_dp_review_packet(
                facts=facts,
                vec=vec,
                ast=ast,
                storyboard=storyboard,
                video=video,
                gate0=forged_gate,
                episode_direction_artifact_id="id:" + "e" * 64,
                scene_intent_artifact_id="id:" + "d" * 64,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
            )

    def test_tampered_receipt_digest_or_session_identity_is_dp_input_blocked(
        self, packet, id_factory, gate0
    ):
        """The fresh context must bind the exact receipt digest and session."""

        for tampered in (
            replace(fresh_context(packet, id_factory, 2), review_packet_digest="0" * 64),
            replace(fresh_context(packet, id_factory, 2), session_id="id:" + "0" * 64),
        ):
            with pytest.raises(DPInputBlockedError, match="DP_INPUT_BLOCKED"):
                assemble_fresh_dp_review(
                    packet=packet,
                    context=tampered,
                    draft=DPReviewDraft(DPReviewVerdict.APPROVED, (), ()),
                    scopes=(),
                    allowed_evidence_refs=(gate_result_source_ref(gate0),),
                    id_factory=id_factory,
                    episode_id=EPISODE_ID,
                    scene_id=SCENE_ID,
                    program_version=PROGRAM_VERSION,
                )

    def test_dp_cannot_cite_evidence_outside_its_packet(
        self, packet, id_factory, gate0
    ):
        """DP inputs must be refs the ReviewPacket already exposes."""

        foreign = SourceRef(source_id="id:" + "f" * 64, digest="0" * 64)
        with pytest.raises(DomainValidationError, match="already visible"):
            assemble_fresh_dp_review(
                packet=packet,
                context=fresh_context(packet, id_factory, 3),
                draft=DPReviewDraft(DPReviewVerdict.APPROVED, (), ()),
                scopes=(),
                allowed_evidence_refs=(foreign,),
                id_factory=id_factory,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                program_version=PROGRAM_VERSION,
            )

    def test_prior_history_or_forbidden_input_emits_dp_input_blocked(
        self, packet, id_factory, vec, gate0
    ):
        gate_ref = gate_result_source_ref(gate0)
        context = replace(
            fresh_context(packet, id_factory, 1),
            prior_history_refs=("old-dp-result",),
        )
        with pytest.raises(DPInputBlockedError, match="DP_INPUT_BLOCKED"):
            assemble_fresh_dp_review(
                packet=packet,
                context=context,
                draft=DPReviewDraft(DPReviewVerdict.APPROVED, (), ()),
                scopes=(director_scope(vec),),
                allowed_evidence_refs=(gate_ref,),
                id_factory=id_factory,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                program_version=PROGRAM_VERSION,
            )


# required_check: dp_outcome_exactly_ready_or_bounded_revision_request
class TestDPOnlyEmitsBoundedRevisionRequest:
    def test_ready_conclusion_is_deterministic_and_bound_to_the_receipt(
        self, packet, id_factory, gate0
    ):
        gate_ref = gate_result_source_ref(gate0)
        ready = assemble_fresh_dp_review(
            packet=packet,
            context=fresh_context(packet, id_factory, 1),
            draft=DPReviewDraft(DPReviewVerdict.APPROVED, (), ()),
            scopes=(),
            allowed_evidence_refs=(gate_ref,),
            id_factory=id_factory,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            program_version=PROGRAM_VERSION,
        )
        assert ready.result.verdict is DPReviewVerdict.APPROVED
        assert ready.revision_requests == ()
        assert ready.result.review_packet_artifact_id == packet.packet_id
        assert ready.result.revision_request_artifact_ids == ()
        again = assemble_fresh_dp_review(
            packet=packet,
            context=fresh_context(packet, id_factory, 1),
            draft=DPReviewDraft(DPReviewVerdict.APPROVED, (), ()),
            scopes=(),
            allowed_evidence_refs=(gate_ref,),
            id_factory=id_factory,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            program_version=PROGRAM_VERSION,
        )
        assert again.result.result_id == ready.result.result_id

    def test_verdict_enum_has_no_third_outcome(self):
        """A text verdict is a local failure, never a third DP outcome."""

        with pytest.raises(DomainValidationError, match="verdict must be a DPReviewVerdict"):
            DPReviewDraft(verdict="READY", finding_codes=(), revision_requests=())

    def test_local_code_creates_request_and_result_ids(self, packet, id_factory, vec, gate0):
        gate_ref = gate_result_source_ref(gate0)
        context = fresh_context(packet, id_factory, 2)
        bundle = assemble_fresh_dp_review(
            packet=packet,
            context=context,
            draft=revision_draft(packet, vec, gate_ref),
            scopes=(director_scope(vec),),
            allowed_evidence_refs=(gate_ref,),
            id_factory=id_factory,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            program_version=PROGRAM_VERSION,
        )
        assert bundle.result.result_id.startswith("id:")
        assert bundle.revision_requests[0].request_id.startswith("id:")
        assert bundle.result.revision_request_artifact_ids == (
            bundle.revision_requests[0].request_id,
        )
        draft_fields = {item.name for item in fields(RevisionRequestDraft)}
        assert draft_fields.isdisjoint({"request_id", "vec", "replacement_vec", "projection"})

    def test_out_of_scope_field_is_rejected(self, packet, id_factory, vec, gate0):
        gate_ref = gate_result_source_ref(gate0)
        with pytest.raises(DomainValidationError, match="bounded scope"):
            assemble_fresh_dp_review(
                packet=packet,
                context=fresh_context(packet, id_factory, 3),
                draft=revision_draft(
                    packet,
                    vec,
                    gate_ref,
                    path="shots.0.camera_and_everything_after",
                ),
                scopes=(director_scope(vec),),
                allowed_evidence_refs=(gate_ref,),
                id_factory=id_factory,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                program_version=PROGRAM_VERSION,
            )

    def test_scope_cannot_authorize_an_artifact_outside_the_review_packet(
        self, packet, id_factory, gate0
    ):
        """A local scope must not smuggle an unseen target into DP output."""

        unseen_target = "id:" + "a" * 64
        scope = RevisionScope(
            target_artifact_id=unseen_target,
            route_kind=RevisionRouteKind.DIRECTOR_DRAFT_REVISION,
            allowed_field_paths=("shots.0.camera",),
        )
        draft = DPReviewDraft(
            verdict=DPReviewVerdict.REVISION_REQUIRED,
            finding_codes=("UNSEEN_TARGET",),
            revision_requests=(
                RevisionRequestDraft(
                    target_artifact_id=unseen_target,
                    failure_type=RevisionFailureType.VISUAL_LOGIC,
                    fact_refs=(packet.fact_refs[0],),
                    field_paths=("shots.0.camera",),
                    observed_issue="the target was never exposed to the reviewer",
                    requested_change="reject the unauthorized target",
                    evidence_ref_ids=(gate_result_source_ref(gate0).source_id,),
                ),
            ),
        )
        with pytest.raises(DomainValidationError, match="ReviewPacket"):
            assemble_fresh_dp_review(
                packet=packet,
                context=fresh_context(packet, id_factory, 31),
                draft=draft,
                scopes=(scope,),
                allowed_evidence_refs=(gate_result_source_ref(gate0),),
                id_factory=id_factory,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                program_version=PROGRAM_VERSION,
            )


# required_check: bounded_revision_router
class TestBoundedRevisionRouter:
    def test_revision_scope_requires_an_opaque_local_artifact_id(self):
        with pytest.raises(DomainValidationError, match="opaque"):
            RevisionScope(
                target_artifact_id="rewrite-every-shot",
                route_kind=RevisionRouteKind.DIRECTOR_DRAFT_REVISION,
                allowed_field_paths=("shots.0.camera",),
            )

    def test_creative_request_spends_budget_and_returns_to_director_draft(
        self, packet, id_factory, vec, gate0
    ):
        gate_ref = gate_result_source_ref(gate0)
        bundle = assemble_fresh_dp_review(
            packet=packet,
            context=fresh_context(packet, id_factory, 4),
            draft=revision_draft(packet, vec, gate_ref),
            scopes=(director_scope(vec),),
            allowed_evidence_refs=(gate_ref,),
            id_factory=id_factory,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            program_version=PROGRAM_VERSION,
        )
        routes = route_revisions(
            bundle.revision_requests,
            scopes=(director_scope(vec),),
            allowed_fact_refs=packet.fact_refs,
            patch_budget=1,
        )
        assert routes[0].kind is RevisionRouteKind.DIRECTOR_DRAFT_REVISION
        assert routes[0].patch_budget_remaining == 0
        exhausted = route_revisions(
            bundle.revision_requests,
            scopes=(director_scope(vec),),
            allowed_fact_refs=packet.fact_refs,
            patch_budget=0,
        )
        assert exhausted[0].kind is RevisionRouteKind.REJECT

    def test_projection_recompile_never_spends_director_budget(
        self, packet, id_factory, vec, projections, gate0
    ):
        ast, _, _ = projections
        gate_ref = gate_result_source_ref(gate0)
        scope = RevisionScope(
            target_artifact_id=ast.projection_id,
            route_kind=RevisionRouteKind.PROJECTION_RECOMPILE,
            allowed_field_paths=("nodes",),
        )
        draft = DPReviewDraft(
            DPReviewVerdict.REVISION_REQUIRED,
            ("PROJECTION_DIVERGENCE",),
            (
                RevisionRequestDraft(
                    ast.projection_id,
                    RevisionFailureType.PROJECTION_DIVERGENCE,
                    (packet.fact_refs[0],),
                    ("nodes",),
                    "derived view diverged",
                    "recompile from the unchanged canonical projection",
                    (gate_ref.source_id,),
                ),
            ),
        )
        bundle = assemble_fresh_dp_review(
            packet=packet,
            context=fresh_context(packet, id_factory, 5),
            draft=draft,
            scopes=(scope,),
            allowed_evidence_refs=(gate_ref,),
            id_factory=id_factory,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            program_version=PROGRAM_VERSION,
        )
        route = route_revisions(
            bundle.revision_requests,
            scopes=(scope,),
            allowed_fact_refs=packet.fact_refs,
            patch_budget=0,
        )[0]
        assert route.kind is RevisionRouteKind.PROJECTION_RECOMPILE
        assert route.patch_budget_remaining == 0


# required_check: text_cannot_claim_visual_acceptance
class TestTextCannotClaimVisualAcceptance:
    def test_text_only_status_stops_at_text_validated(self):
        assert ladder_status(
            text_ceiling="TEXT_VALIDATED", verification=None, approval=None
        ) is VerificationStatus.TEXT_VALIDATED
        with pytest.raises(DomainValidationError):
            ladder_status(
                text_ceiling="VISUAL_EVIDENCED", verification=None, approval=None
            )

    def test_visual_builder_has_no_default_or_text_pass_parameter(self):
        from mode_p_vnext.pipeline.verification_nodes import build_visual_verification

        parameters = inspect.signature(build_visual_verification).parameters
        assert "passed" not in parameters
        assert "verifier_output" in parameters
        assert "media_evidence" in parameters

    def test_approval_port_returns_draft_not_canonical_record(self):
        annotation = inspect.signature(ApprovalPort.request_approval).return_annotation
        assert annotation in {ApprovalDecisionDraft, "ApprovalDecisionDraft"}

    def test_passing_media_verifier_output_requires_outcome_attribution(self):
        frame = FrameEvidence(
            media_run_id="id:" + "r" * 64,
            frame_index=0,
            observations=("fixture frame",),
            attributes={"fixture": "only"},
        )
        with pytest.raises(DomainValidationError, match="outcome attribution"):
            MediaVerificationOutput(passed=True, frames=(frame,), attributions=())


# required_check: media_outcome_attribution
class TestMediaOutcomeAttribution:
    def test_failed_gate_and_media_layers_are_machine_attributable(
        self, id_factory, vec, projections, compiled_prompt
    ):
        failed = gate(
            id_factory,
            vec,
            projections,
            compiled_prompt,
            claim_ceiling="VISUAL_EVIDENCED",
        )
        assert layer_of(gate0_attribution(failed)) is AttributionLayer.GATE0
        assert layer_of(
            media_render_attribution(
                scene_id=SCENE_ID, renderer_version="none", reason="unavailable"
            )
        ) is AttributionLayer.MEDIA_RENDER
        assert layer_of(
            media_verify_attribution(
                scene_id=SCENE_ID, verifier_version="none", reason="unavailable"
            )
        ) is AttributionLayer.MEDIA_VERIFY

    def test_visual_verification_rejects_evidence_from_a_different_frame_plan(
        self, id_factory, vec
    ):
        plan = build_frame_evidence_plan(
            vec=vec,
            checks=("composition",),
            frame_indices=(0,),
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        media_run = MediaRunRecord(
            run_id="id:" + "r" * 64,
            provider="fixture-only",
            request_digest="0" * 64,
            output_refs=(SourceRef("fixture-output", "1" * 64),),
        )
        frames = (
            FrameEvidence(
                media_run_id=media_run.run_id,
                frame_index=0,
                observations=("fixture frame",),
                attributes={"fixture": "only"},
            ),
        )
        evidence = build_media_evidence(
            plan=plan,
            media_run=media_run,
            frames=frames,
            id_factory=id_factory,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            program_version=PROGRAM_VERSION,
        )
        verifier_output = MediaVerificationOutput(
            passed=True,
            frames=frames,
            attributions=(
                OutcomeAttribution(
                    result_id="attr:" + "a" * 64,
                    cause="MEDIA_VERIFY|fixture-only",
                    confidence="high",
                    supporting_evidence=(media_run.run_id,),
                ),
            ),
        )
        foreign_plan = replace(plan, plan_id="id:" + "b" * 64)
        with pytest.raises(DomainValidationError, match="frame plan"):
            build_visual_verification(
                vec=vec,
                plan=foreign_plan,
                media_run=media_run,
                media_evidence=evidence,
                verifier_output=verifier_output,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
            )

    def test_media_evidence_identity_uses_the_local_frame_plan_order(
        self, id_factory, vec
    ):
        plan = build_frame_evidence_plan(
            vec=vec,
            checks=("composition", "continuity"),
            frame_indices=(0, 3),
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        media_run = MediaRunRecord(
            run_id="id:" + "r" * 64,
            provider="fixture-only",
            request_digest="0" * 64,
            output_refs=(SourceRef("fixture-output", "1" * 64),),
        )
        first = FrameEvidence(
            media_run_id=media_run.run_id,
            frame_index=0,
            observations=("first",),
            attributes={"fixture": "only"},
        )
        second = FrameEvidence(
            media_run_id=media_run.run_id,
            frame_index=3,
            observations=("second",),
            attributes={"fixture": "only"},
        )
        reversed_evidence = build_media_evidence(
            plan=plan,
            media_run=media_run,
            frames=(second, first),
            id_factory=id_factory,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            program_version=PROGRAM_VERSION,
        )
        ordered_evidence = build_media_evidence(
            plan=plan,
            media_run=media_run,
            frames=(first, second),
            id_factory=id_factory,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            program_version=PROGRAM_VERSION,
        )
        assert reversed_evidence == ordered_evidence
        assert tuple(item.frame_index for item in reversed_evidence.frame_evidence) == (
            0,
            3,
        )


# required_check: projection_bundle_precedes_gate_zero
class TestProjectionBundlePrecedesGateZero:
    def test_gate_zero_fails_closed_without_the_complete_bundle(
        self, id_factory, vec, projections, compiled_prompt
    ):
        """No bundle, no Gate 0: a missing view can never be gate-passed."""

        with pytest.raises(DomainValidationError, match="exact v3 delivery views"):
            gate(id_factory, vec, projections, compiled_prompt, storyboard=None)
        with pytest.raises(DomainValidationError, match="exact v3 delivery views"):
            gate(id_factory, vec, projections, compiled_prompt, video=object())

    def test_gate_zero_rejects_a_manifest_not_bound_to_this_ast(
        self, id_factory, vec, projections, compiled_prompt
    ):
        """A view whose manifest claims a different node set cannot pass."""

        ast, storyboard, _ = projections
        forged_manifest = replace(
            storyboard.manifest,
            source_node_ids=(storyboard.manifest.source_node_ids[0],),
        )
        with pytest.raises(DomainValidationError):
            # The view constructor already refuses a manifest that claims a
            # different node set; Gate 0 must never see such a view at all.
            replace(storyboard, manifest=forged_manifest)
        with pytest.raises(DomainValidationError):
            # Nor can the view be re-bound to a foreign AST object.
            replace(storyboard, ast=replace(ast, projection_id="id:" + "f" * 64))


# required_check: gate_zero_failure_blocks_dp
class TestGateZeroFailureBlocksDP:
    def test_failed_gate_zero_never_creates_a_review_packet(
        self, id_factory, facts, vec, projections, gate0, compiled_prompt
    ):
        """A gate failure must block the packet, not just the DP call."""

        failed = gate(
            id_factory,
            vec,
            projections,
            compiled_prompt,
            claim_ceiling="VISUAL_EVIDENCED",
        )
        assert not failed.passed
        assert failed.failed_check_ids == (CLAIM_CEILING,)
        ast, storyboard, video = projections
        with pytest.raises(DomainValidationError, match="passed canonical Gate 0"):
            build_dp_review_packet(
                facts=facts,
                vec=vec,
                ast=ast,
                storyboard=storyboard,
                video=video,
                gate0=failed,
                episode_direction_artifact_id="id:" + "e" * 64,
                scene_intent_artifact_id="id:" + "d" * 64,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
            )


# required_check: canonical_projection_and_evidence_consumption
class TestCanonicalProjectionAndEvidenceConsumption:
    def test_gate_and_packet_bind_one_projection_and_canonical_evidence(
        self, projections, gate0, packet
    ):
        ast, storyboard, video = projections
        assert storyboard.ast is ast and video.ast is ast
        assert gate0.target_artifact_ids[1] == ast.projection_id
        assert packet.projection_artifact_ids == (ast.projection_id,)
        assert all(isinstance(item, SourceRef) for item in gate0.evidence_refs)


# required_check: external_media_not_started
class TestExternalMediaNotStarted:
    def test_only_fail_closed_noop_ports_are_active(self, projections, vec):
        ast, storyboard, _ = projections
        renderer: MediaRendererPort = NoopMediaRenderer()
        request = MediaRenderRequest(
            scene_id=SCENE_ID,
            projection_artifact_id=ast.projection_id,
            projection_ast_digest=canonical_sha256(ast),
            projection_manifest_digest=canonical_sha256(storyboard.manifest),
            capability_profile_digest=canonical_sha256(vec.capability_profile),
            settings={"profile": "not-started"},
        )
        with pytest.raises(MediaRendererUnavailableError):
            renderer.render(request)

        verifier: MediaVerifierPort = NoopMediaVerifier()
        plan = FrameEvidencePlan(
            plan_id="id:" + "p" * 64,
            vec_artifact_id=vec.contract_id,
            checks=("composition",),
            frame_indices=(0,),
        )
        run = MediaRunRecord(
            run_id="id:" + "r" * 64,
            provider="not-started-fixture",
            request_digest="0" * 64,
            output_refs=(SourceRef("fixture-output", "1" * 64),),
        )
        with pytest.raises(MediaVerificationUnavailableError):
            verifier.verify(plan, run)

    def test_no_approval_or_real_media_adapter_exists(self):
        import mode_p_vnext.adapters.media as adapters

        assert set(adapters.__all__) == {"NoopMediaRenderer", "NoopMediaVerifier"}
        assert not hasattr(adapters, "ApprovalAdapter")
