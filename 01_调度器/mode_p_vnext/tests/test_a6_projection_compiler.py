"""A6 acceptance tests: one ProjectionAST compiles both projections.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §10 / §14 A6.

The VEC is the sole creative authority; `compile_projection_ast` produces the
single ProjectionAST; `derive_storyboard` / `derive_video` both compile from
that one AST (never from the VEC independently).  Adapters only format or
degrade capability, they never invent events.  Every projection manifest
carries the binding digests required by §10.
"""

from __future__ import annotations

import hashlib

import pytest

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
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
from mode_p_vnext.domain.facts import FactKind, FactRegistry, ScriptFact
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.time import TICKS_PER_SECOND
from mode_p_vnext.domain.vec import (
    ExecutionDesignDraft,
    ShotDesignDraft,
    StoryboardRole,
    VisualBeatDraft,
    VisualBeatPhase,
    VisualExecutionContract,
)
from mode_p_vnext.services.blocking_assembler import assemble_blocking_commit
from mode_p_vnext.services.projection_compiler import (
    ProjectionAST,
    ProjectionManifest,
    ProjectionNode,
    compile_projection_ast,
    derive_storyboard,
    derive_video,
)
from mode_p_vnext.services.vec_assembler import assemble_vec


PROGRAM_VERSION = "mode-p-vnext-a6-test"
COMPILER_VERSION = "2.1.0"
SCHEMA_VERSION = "2.1"
EPISODE_ID = "EP35"
SCENE_ID = "EP35-S2"


# ---------------------------------------------------------------------------
# Shared fixtures (VEC with required / optional / omit beats in two shots)
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
            VisualCurvePointDraft(
                dramatic_beat_ordinal=1,
                intensity=60,
                explanation="arrival tension",
            ),
            VisualCurvePointDraft(
                dramatic_beat_ordinal=2,
                intensity=85,
                explanation="weapon escalation",
            ),
        ),
        decisions=(
            DecisionDraft(
                scope="camera distance for the loading shot",
                basis=DecisionBasis.CHOICE,
                locked_by=(),
                options=("extreme close-up on hands", "medium shot with face"),
                selected_index=0,
                rationale="weapon detail sells the threat",
                tradeoff="sacrifice facial reaction in this beat",
            ),
        ),
        shots=(
            ShotDesignDraft(
                blocking_beat_ordinal=1,
                dramatic_function="introduce the range and the protagonist's state",
                attention_target="chen entering the space",
                information_action="the range is empty, chen is alone",
                framing_intent="wide establishing",
                camera_pose="eye level",
                camera_motion="static",
                composition="depth layering with targets in background",
                lighting="harsh overhead fluorescents",
                performance="controlled breathing, deliberate steps",
                duration_weight=4,
                visual_beats=(
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ENTRY,
                        subject_state="chen at doorway, surveying",
                        attention="the empty range",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ACTION,
                        subject_state="chen steps forward",
                        attention="the shooting lane",
                        storyboard_role=StoryboardRole.OPTIONAL,
                    ),
                ),
            ),
            ShotDesignDraft(
                blocking_beat_ordinal=2,
                dramatic_function="weapon preparation as threat escalation",
                attention_target="hands loading the pistol",
                information_action="the pistol is ready to fire",
                framing_intent="extreme close-up on hands and weapon",
                camera_pose="overhead angle",
                camera_motion="slow push-in",
                composition="hands dominate frame, face out of focus",
                lighting="single practical above the bench",
                performance="precise, ritualistic movements",
                duration_weight=6,
                visual_beats=(
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ENTRY,
                        subject_state="hands reach for the case",
                        attention="the pistol case",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ACTION,
                        subject_state="magazine slides in",
                        attention="the click of the magazine seating",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.REACTION,
                        subject_state="chen's breath steadies",
                        attention="the now-live weapon",
                        storyboard_role=StoryboardRole.OMIT,
                    ),
                ),
            ),
        ),
        transition_intents=("hard cut on the magazine click",),
        audio_intents=("mechanical click of magazine",),
        reference_intents=("pistol prop reference",),
        handoff_intent="cut to the target paper, hold 12 frames",
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
                fact_id="costume_tactical_jacket",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Black tactical jacket with worn leather patches on the elbows.",
                source_ref=SourceRef(source_id="ep35_script", digest="c" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="scene_shooting_range",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Indoor shooting range, fluorescent lighting, sound-dampening panels.",
                source_ref=SourceRef(source_id="ep35_script", digest="d" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="dialogue_chen_muttering",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Chen mutters: the range is clear.",
                source_ref=SourceRef(source_id="ep35_script", digest="e" * 64, locator="S2"),
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
        compiler_version=COMPILER_VERSION,
    )


def _all_beats(vec: VisualExecutionContract):
    return [beat for shot in vec.shots for beat in shot.visual_beats]


# ===================================================================
# required_check: single_projection_ast
# ===================================================================

class TestSingleProjectionAST:
    def test_compile_is_deterministic(
        self,
        vec: VisualExecutionContract,
        blocking_commit: BlockingCommit,
        id_factory: IdFactory,
    ) -> None:
        a = compile_projection_ast(
            vec=vec,
            blocking_commit=blocking_commit,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
            compiler_version=COMPILER_VERSION,
        )
        b = compile_projection_ast(
            vec=vec,
            blocking_commit=blocking_commit,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
            compiler_version=COMPILER_VERSION,
        )
        assert a.ast_id == b.ast_id
        assert a.ast_digest == b.ast_digest

    def test_ast_binds_vec_digest(self, ast: ProjectionAST, vec: VisualExecutionContract) -> None:
        assert ast.vec_digest == canonical_sha256(vec)
        assert ast.ast_digest == canonical_sha256(
            {
                "vec_digest": ast.vec_digest,
                "compiler_version": ast.compiler_version,
                "nodes": ast.nodes,
                "reference_requirements": ast.reference_requirements,
                "audio_events": ast.audio_events,
                "voice_requirements": ast.voice_requirements,
            }
        )

    def test_ast_covers_all_vec_nodes(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        beat_ids = {beat.beat_id for beat in _all_beats(vec)}
        shot_ids = {shot.shot_id for shot in vec.shots}
        boundary_ids = {b.boundary_id for b in vec.boundaries}
        source_ids = {n.source_id for n in ast.nodes}
        # every VEC node maps to exactly one AST node (via source_id)
        assert beat_ids <= source_ids
        assert shot_ids <= source_ids
        assert boundary_ids <= source_ids
        assert len(ast.nodes) == len(beat_ids) + len(shot_ids) + len(boundary_ids)
        assert len(ast.nodes) == len(source_ids)
        # AST node ids are locally generated and distinct from VEC source ids
        node_ids = {n.node_id for n in ast.nodes}
        assert node_ids.isdisjoint(source_ids)
        for node in ast.nodes:
            assert node.source_id in source_ids

    def test_ast_source_node_ids_match_vec(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        vec_node_ids = (
            {beat.beat_id for beat in _all_beats(vec)}
            | {shot.shot_id for shot in vec.shots}
            | {b.boundary_id for b in vec.boundaries}
        )
        assert set(ast.source_node_ids) == vec_node_ids

    def test_ast_rejects_unbound_state(
        self,
        vec: VisualExecutionContract,
        blocking_draft: BlockingDraft,
    ) -> None:
        # A VEC's beat states derive from one commit input digest; a commit
        # assembled under a different program version has a disjoint state set
        # and must be rejected by the compiler.
        foreign_factory = IdFactory(program_version="foreign-version")
        foreign_commit = assemble_blocking_commit(
            draft=blocking_draft,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=foreign_factory,
            program_version="foreign-version",
            schema_version=SCHEMA_VERSION,
        )
        with pytest.raises(DomainValidationError):
            compile_projection_ast(
                vec=vec,
                blocking_commit=foreign_commit,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
                compiler_version=COMPILER_VERSION,
            )


# ===================================================================
# required_check: storyboard_visualbeat_selection
# ===================================================================

class TestStoryboardVisualBeatSelection:
    def test_storyboard_excludes_omit_beats(self, ast: ProjectionAST) -> None:
        storyboard = derive_storyboard(ast=ast)
        roles = {n.storyboard_role for n in storyboard.nodes}
        assert StoryboardRole.OMIT not in roles
        for node in storyboard.nodes:
            assert node.node_type == "beat"
            assert node.storyboard_role in (StoryboardRole.REQUIRED, StoryboardRole.OPTIONAL)

    def test_storyboard_covers_all_required_beats(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        storyboard = derive_storyboard(ast=ast)
        required = {
            beat.beat_id
            for beat in _all_beats(vec)
            if beat.storyboard_role == StoryboardRole.REQUIRED
        }
        projected = {n.source_id for n in storyboard.nodes}
        assert required <= projected

    def test_storyboard_capacity_keeps_required_first(
        self, ast: ProjectionAST
    ) -> None:
        storyboard = derive_storyboard(ast=ast, max_panels=3)
        required = [n for n in storyboard.nodes if n.storyboard_role == StoryboardRole.REQUIRED]
        optional = [n for n in storyboard.nodes if n.storyboard_role == StoryboardRole.OPTIONAL]
        assert len(required) >= 1
        assert len(optional) <= max(0, 3 - len(required))
        assert len(storyboard.nodes) <= 3

    def test_storyboard_keeps_beat_shot_tick_state_decision_references(
        self, ast: ProjectionAST
    ) -> None:
        storyboard = derive_storyboard(ast=ast)
        for node in storyboard.nodes:
            assert node.beat_id
            assert node.shot_id
            assert node.start_tick < node.end_tick
            assert node.start_state_id
            assert node.end_state_id
            assert isinstance(node.decision_ids, tuple)


# ===================================================================
# required_check: video_full_node_projection
# ===================================================================

class TestVideoFullNodeProjection:
    def test_video_includes_every_beat_including_omit(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        video = derive_video(ast=ast)
        all_beats = {beat.beat_id for beat in _all_beats(vec)}
        video_beat_ids = {n.source_id for n in video.nodes if n.node_type == "beat"}
        assert video_beat_ids == all_beats

    def test_video_includes_shots_boundaries_and_execution_details(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        video = derive_video(ast=ast)
        types = {n.node_type for n in video.nodes}
        assert "shot" in types
        assert "boundary" in types
        shot_nodes = [n for n in video.nodes if n.node_type == "shot"]
        assert shot_nodes
        for node in shot_nodes:
            assert node.camera_pose
            assert node.camera_motion
            assert node.composition
            assert node.lighting
            assert node.performance

    def test_video_does_not_omit_for_storyboard_reasons(
        self, ast: ProjectionAST
    ) -> None:
        video = derive_video(ast=ast)
        roles = {n.storyboard_role for n in video.nodes}
        assert StoryboardRole.OMIT in roles  # omit beats still present in video


# ===================================================================
# required_check: shared_tick_state_and_bindings
# ===================================================================

class TestSharedTickStateAndBindings:
    def test_same_beat_id_same_tick_state_in_both_projections(
        self, ast: ProjectionAST
    ) -> None:
        storyboard = derive_storyboard(ast=ast)
        video = derive_video(ast=ast)
        sb_by_id = {n.source_id: n for n in storyboard.nodes}
        for node in video.nodes:
            if node.node_type != "beat":
                continue
            sb = sb_by_id.get(node.source_id)
            if sb is None:
                continue  # omit beats are storyboard-absent by design
            assert sb.start_tick == node.start_tick
            assert sb.end_tick == node.end_tick
            assert sb.start_state_id == node.start_state_id
            assert sb.end_state_id == node.end_state_id
            assert sb.decision_ids == node.decision_ids
            assert sb.beat_id == node.beat_id
            assert sb.shot_id == node.shot_id

    def test_manifest_carries_required_binding_fields(
        self, ast: ProjectionAST
    ) -> None:
        manifest = ProjectionManifest(
            vec_digest=ast.vec_digest,
            projection_ast_digest=ast.ast_digest,
            source_node_ids=ast.source_node_ids,
            compiler_version=ast.compiler_version,
            adapter_version="storyboard-v2.1.0",
            capability_profile_digest="",
            reference_binding_digest=ast.reference_binding_digest,
            audio_binding_digest=ast.audio_binding_digest,
        )
        assert manifest.vec_digest == ast.vec_digest
        assert manifest.projection_ast_digest == ast.ast_digest
        assert manifest.source_node_ids == ast.source_node_ids
        assert len(manifest.reference_binding_digest) == 64
        assert len(manifest.audio_binding_digest) == 64

    def test_binding_digests_track_ast_inputs(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        expected_ref = canonical_sha256(ast.reference_requirements)
        expected_audio = canonical_sha256(
            {"audio_events": ast.audio_events, "voice_requirements": ast.voice_requirements}
        )
        assert ast.reference_binding_digest == expected_ref
        assert ast.audio_binding_digest == expected_audio

    def test_ast_ids_are_locally_generated_and_stable(
        self, ast: ProjectionAST
    ) -> None:
        # AST ids must be machine-generated and deterministic, never from the model.
        assert ast.ast_id.startswith("projection_ast:")
        assert len(ast.ast_id.split(":")) == 3


# ===================================================================
# required_check: adapter_only_recompile
# ===================================================================

class TestAdapterOnlyRecompile:
    def test_adapter_version_change_keeps_nodes_unchanged(
        self, ast: ProjectionAST
    ) -> None:
        a = derive_video(ast=ast, adapter_version="video-v2.1.0")
        b = derive_video(ast=ast, adapter_version="video-v2.2.0")
        assert [n.node_id for n in a.nodes] == [n.node_id for n in b.nodes]
        assert a.manifest.vec_digest == b.manifest.vec_digest
        assert a.manifest.projection_ast_digest == b.manifest.projection_ast_digest
        assert a.adapter_version != b.adapter_version

    def test_capability_degradation_produces_adaptation_record(
        self, ast: ProjectionAST
    ) -> None:
        from mode_p_vnext.adapters.delivery.capability import (
            CapabilityAdaptationRecord,
            CapabilityProfile,
            capability_profile_digest,
        )
        from mode_p_vnext.adapters.delivery.video_adapter import render_video

        profile = CapabilityProfile(
            platform="test-sd2",
            version="1.0",
            max_prompt_chars=10_000,
            reference_slots=2,
            internal_cuts_supported=False,
        )
        video = derive_video(
            ast=ast,
            adapter_version="video-v2.1.0",
            capability_profile_digest=capability_profile_digest(profile),
        )
        delivery = render_video(video, profile=profile, adapter_version="video-adapter-1")
        assert delivery.adaptation_records, "multi-shot video on a no-internal-cut platform must degrade"
        for record in delivery.adaptation_records:
            assert isinstance(record, CapabilityAdaptationRecord)
            assert record.adapter_version == "video-adapter-1"
        # degradation never invents nodes: node count preserved
        assert len(delivery.nodes) == len(video.nodes)

    def test_render_is_pure_function(self, ast: ProjectionAST) -> None:
        from mode_p_vnext.adapters.delivery.storyboard_adapter import render_storyboard

        storyboard = derive_storyboard(ast=ast)
        a = render_storyboard(storyboard, adapter_version="sb-adapter-1")
        b = render_storyboard(storyboard, adapter_version="sb-adapter-1")
        assert a.panels == b.panels
        assert a.adapter_version == b.adapter_version == "sb-adapter-1"

    def test_storyboard_adapter_formats_without_inventing_events(
        self, ast: ProjectionAST
    ) -> None:
        from mode_p_vnext.adapters.delivery.storyboard_adapter import render_storyboard

        storyboard = derive_storyboard(ast=ast)
        delivery = render_storyboard(storyboard, adapter_version="sb-adapter-1")
        assert delivery.panels
        for panel in delivery.panels:
            # adapter only re-emits nodes from the AST, with no new content
            assert panel.beat_id
            assert panel.shot_id
            assert panel.subject_state
