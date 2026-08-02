"""A6 acceptance tests for the frozen v3.0 single-projection invariant."""

from __future__ import annotations

from dataclasses import replace
import inspect
import json

import pytest

from mode_p_vnext.adapters.delivery import capability as delivery_capability
from mode_p_vnext.adapters.delivery.capability import (
    CapabilityProfile,
    capability_profile_digest,
)
from mode_p_vnext.adapters.delivery.storyboard_adapter import (
    render_storyboard,
    storyboard_adapter_version,
)
from mode_p_vnext.adapters.delivery.video_adapter import (
    render_video,
    video_adapter_version,
)
from mode_p_vnext.domain import projection as canonical_projection
from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    canonical_json_bytes,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingCommit, BlockingDraft
from mode_p_vnext.domain.decisions import (
    DecisionBasis,
    DecisionDraft,
    VisualCurvePointDraft,
)
from mode_p_vnext.domain.facts import (
    FactConfidence,
    FactKind,
    FactQualifiers,
    FactRegistry,
    FactSemantic,
    ScriptFact,
    SourceSpan,
)
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.projection import (
    CapabilityAdaptationRecord,
    ProjectionAST,
    ProjectionManifest,
    ProjectionNode,
)
from mode_p_vnext.domain.time import DurationIntent
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
from mode_p_vnext.services import projection_compiler
from mode_p_vnext.services.blocking_assembler import assemble_blocking_commit
from mode_p_vnext.services.projection_compiler import (
    compile_projection_ast,
    derive_storyboard,
    derive_video,
    node_attribute,
)
from mode_p_vnext.services.vec_assembler import assemble_vec


PROGRAM_VERSION = "mode-p-vnext-a6-v3-test"
EPISODE_ID = "EP35"
SCENE_ID = "EP35-S2"
SOURCE_REF = SourceRef(source_id="a6-fixture", digest="f" * 64)


def _opaque_id(character: str) -> str:
    return f"id:{character * 64}"


def _opaque_handle(character: str) -> str:
    return f"fh:{character * 64}"


def _fact(
    *,
    ordinal: int,
    character: str,
    semantic: FactSemantic,
    span_start: int,
    subject_label: str | None = None,
    spoken_text: str | None = None,
) -> ScriptFact:
    return ScriptFact(
        fact_id=_opaque_id(character),
        fact_handle=_opaque_handle(character),
        kind=FactKind.SCRIPT,
        semantic=semantic,
        statement=f"fixture-{semantic.value}-{ordinal}",
        confidence=FactConfidence.EXPLICIT,
        qualifiers=FactQualifiers(
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            subject_label=subject_label,
            spoken_text=spoken_text,
        ),
        provenance=(
            SourceSpan(
                source_ref=SOURCE_REF,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                source_start=span_start,
                source_end=span_start + 1,
            ),
        ),
        ordinal=ordinal,
    )


def make_facts() -> FactRegistry:
    return FactRegistry(
        source_ref=SOURCE_REF,
        facts=(
            _fact(
                ordinal=1,
                character="a",
                semantic=FactSemantic.CHARACTER,
                span_start=10,
                subject_label="Mira",
            ),
            _fact(
                ordinal=2,
                character="b",
                semantic=FactSemantic.PROP,
                span_start=20,
                subject_label="service pistol",
            ),
            _fact(
                ordinal=3,
                character="c",
                semantic=FactSemantic.DIALOGUE,
                span_start=30,
                subject_label="Mira",
                spoken_text="Don't move.",
            ),
            _fact(
                ordinal=4,
                character="d",
                semantic=FactSemantic.SETTING,
                span_start=40,
                subject_label="range",
            ),
        ),
    )


def make_blocking_draft() -> BlockingDraft:
    return BlockingDraft(
        beats=(
            BlockingBeatDraft(
                ordinal=1,
                dramatic_action="Mira enters the quiet range.",
                character_states=({"character": "Mira", "posture": "guarded"},),
                prop_states=(),
                gaze_relations=(),
                action_paths=("enter",),
                continuity_effect="The range is established.",
            ),
            BlockingBeatDraft(
                ordinal=2,
                dramatic_action="Mira confronts the pistol.",
                character_states=({"character": "Mira", "posture": "ready"},),
                prop_states=({"prop": "pistol", "state": "visible"},),
                gaze_relations=("Mira -> pistol",),
                action_paths=("raise focus",),
                continuity_effect="The threat escalates.",
            ),
        )
    )


def make_execution_draft() -> ExecutionDesignDraft:
    return ExecutionDesignDraft(
        curve_points=(
            VisualCurvePointDraft(1, 60, "arrival tension"),
            VisualCurvePointDraft(2, 85, "threat escalation"),
        ),
        decisions=(
            DecisionDraft(
                scope="coverage",
                basis=DecisionBasis.CHOICE,
                locked_by=(),
                options=("wide", "close"),
                selected_index=1,
                rationale="preserve the reveal",
                tradeoff="less environment detail",
            ),
        ),
        shots=(
            ShotDesignDraft(
                shot_ordinal=1,
                blocking_beat_ordinal=1,
                duration_intent=DurationIntent.STANDARD,
                generation_mode=GenerationMode.TEXT_ONLY,
                composition="wide entrance",
                camera="slow push",
                lighting="cold practicals",
                performance="guarded scan",
                visual_beats=(
                    VisualBeatDraft(
                        1,
                        VisualBeatPhase.ENTRY,
                        "at door",
                        "room",
                        StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        2,
                        VisualBeatPhase.ACTION,
                        "steps in",
                        "Mira",
                        StoryboardRole.OPTIONAL,
                    ),
                ),
                reference_binding_intents=(
                    ReferenceBindingIntent(
                        shot_ordinal=1,
                        visual_beat_ordinal=None,
                        fact_handle=_opaque_handle("a"),
                        responsibility=ReferenceResponsibility.CHARACTER_IDENTITY,
                    ),
                ),
                dialogue_binding_intents=(),
                creative_notes="hold the silence",
            ),
            ShotDesignDraft(
                shot_ordinal=2,
                blocking_beat_ordinal=2,
                duration_intent=DurationIntent.EXTENDED,
                generation_mode=GenerationMode.OMNI_REFERENCE,
                composition="waist-up confrontation",
                camera="controlled settle",
                lighting="hard side key",
                performance="breath held",
                visual_beats=(
                    VisualBeatDraft(
                        1,
                        VisualBeatPhase.ENTRY,
                        "pistol revealed",
                        "pistol",
                        StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        2,
                        VisualBeatPhase.ACTION,
                        "eyes lock",
                        "Mira",
                        StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        3,
                        VisualBeatPhase.REACTION,
                        "breath steadies",
                        "live weapon",
                        StoryboardRole.OMIT,
                    ),
                ),
                reference_binding_intents=(
                    ReferenceBindingIntent(
                        shot_ordinal=2,
                        visual_beat_ordinal=1,
                        fact_handle=_opaque_handle("b"),
                        responsibility=ReferenceResponsibility.PROP_IDENTITY,
                    ),
                ),
                dialogue_binding_intents=(
                    DialogueBindingIntent(
                        shot_ordinal=2,
                        visual_beat_ordinal=2,
                        fact_handle=_opaque_handle("c"),
                        placement_phase=PlacementPhase.MIDDLE,
                    ),
                ),
                creative_notes="do not rush the line",
            ),
        ),
        transition_intents=("hard cut",),
        handoff_intent="leave on the confrontation",
    )


@pytest.fixture
def id_factory() -> IdFactory:
    return IdFactory(program_version=PROGRAM_VERSION)


@pytest.fixture
def blocking_commit(id_factory: IdFactory) -> BlockingCommit:
    return assemble_blocking_commit(
        draft=make_blocking_draft(),
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


@pytest.fixture
def vec(id_factory: IdFactory, blocking_commit: BlockingCommit) -> VisualExecutionContract:
    return assemble_vec(
        draft=make_execution_draft(),
        blocking_commit=blocking_commit,
        facts=make_facts(),
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


@pytest.fixture
def ast(
    id_factory: IdFactory,
    blocking_commit: BlockingCommit,
    vec: VisualExecutionContract,
) -> ProjectionAST:
    return compile_projection_ast(
        vec=vec,
        blocking_commit=blocking_commit,
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


def _vec_beats(vec: VisualExecutionContract):
    return tuple(beat for shot in vec.shots for beat in shot.visual_beats)


# required_check: single_projection_ast
class TestSingleProjectionAST:
    def test_compile_is_deterministic_and_canonical(
        self,
        id_factory: IdFactory,
        blocking_commit: BlockingCommit,
        vec: VisualExecutionContract,
    ) -> None:
        first = compile_projection_ast(
            vec=vec,
            blocking_commit=blocking_commit,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        second = compile_projection_ast(
            vec=vec,
            blocking_commit=blocking_commit,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        assert first == second
        assert type(first) is ProjectionAST
        assert all(type(node) is ProjectionNode for node in first.nodes)

    def test_projection_identity_binds_the_frozen_compiler_version(
        self,
        ast: ProjectionAST,
        id_factory: IdFactory,
        vec: VisualExecutionContract,
    ) -> None:
        projection_input_digest = canonical_sha256(
            {
                "vec_digest": canonical_sha256(vec),
                "compiler_version": projection_compiler.COMPILER_VERSION,
            }
        )
        assert ast.projection_id == id_factory.create(
            artifact_kind=ArtifactKind.PROJECTION_AST,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            stage="projection:ast",
            input_digest=projection_input_digest,
            ordinal=0,
        )

    def test_ast_binds_vec_and_every_visualbeat_once(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        beats = _vec_beats(vec)
        assert ast.source_vec_artifact_id == vec.contract_id
        assert {node.source_beat_id for node in ast.nodes} == {
            beat.beat_id for beat in beats
        }
        assert len(ast.nodes) == len(beats)
        assert {node.source_shot_id for node in ast.nodes} == {
            shot.shot_id for shot in vec.shots
        }
        assert {
            node_attribute(node, "vec_digest", str) for node in ast.nodes
        } == {canonical_sha256(vec)}

    def test_ast_preserves_scene_ticks_states_and_n_plus_one_boundaries(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        unit_by_shot = {unit.shot_id: unit for unit in vec.generation_units}
        beat_by_id = {beat.beat_id: beat for beat in _vec_beats(vec)}
        boundary_ids: set[str] = set()
        for node in ast.nodes:
            beat = beat_by_id[node.source_beat_id]
            placement = unit_by_shot[node.source_shot_id].scene_placement.interval
            assert node.interval.start_tick == placement.start_tick + beat.interval.start_tick
            assert node.interval.end_tick == placement.start_tick + beat.interval.end_tick
            assert (node.start_state_id, node.end_state_id) == (
                beat.start_state_id,
                beat.end_state_id,
            )
            boundary_ids.add(node.attributes["entering_boundary"]["boundary_id"])
            boundary_ids.add(node.attributes["exiting_boundary"]["boundary_id"])
        assert boundary_ids == {item.boundary_id for item in vec.boundaries}

    def test_compile_rejects_wrong_commit_or_program_authority(
        self,
        vec: VisualExecutionContract,
        blocking_commit: BlockingCommit,
        id_factory: IdFactory,
    ) -> None:
        foreign_factory = IdFactory(program_version="foreign")
        foreign_commit = assemble_blocking_commit(
            draft=make_blocking_draft(),
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=foreign_factory,
            program_version="foreign",
        )
        with pytest.raises(DomainValidationError):
            compile_projection_ast(
                vec=vec,
                blocking_commit=foreign_commit,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
            )
        with pytest.raises(DomainValidationError):
            compile_projection_ast(
                vec=vec,
                blocking_commit=blocking_commit,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                id_factory=id_factory,
                program_version="foreign",
            )

    def test_compile_rejects_stale_canonical_vec_output_digest(
        self,
        vec: VisualExecutionContract,
        blocking_commit: BlockingCommit,
        id_factory: IdFactory,
    ) -> None:
        stale_digest_vec = replace(vec, canonical_output_sha256="0" * 64)

        with pytest.raises(DomainValidationError, match="canonical_output_sha256"):
            compile_projection_ast(
                vec=stale_digest_vec,
                blocking_commit=blocking_commit,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
            )

    def test_compile_rejects_unfrozen_projection_compiler_version(
        self,
        vec: VisualExecutionContract,
        blocking_commit: BlockingCommit,
        id_factory: IdFactory,
    ) -> None:
        with pytest.raises(DomainValidationError, match="compiler_version must match"):
            compile_projection_ast(
                vec=vec,
                blocking_commit=blocking_commit,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
                compiler_version="foreign-projection-compiler",
            )


# required_check: storyboard_visualbeat_selection
class TestStoryboardVisualBeatSelection:
    def test_storyboard_includes_required_and_excludes_omit(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        storyboard = derive_storyboard(ast)
        selected = {node.source_beat_id for node in storyboard.nodes}
        required = {
            beat.beat_id
            for beat in _vec_beats(vec)
            if beat.storyboard_role is StoryboardRole.REQUIRED
        }
        omitted = {
            beat.beat_id
            for beat in _vec_beats(vec)
            if beat.storyboard_role is StoryboardRole.OMIT
        }
        assert required <= selected
        assert selected.isdisjoint(omitted)

    def test_capacity_keeps_ast_order_and_only_drops_optional(
        self, ast: ProjectionAST
    ) -> None:
        required_count = sum(
            node_attribute(node, "storyboard_role", str)
            == StoryboardRole.REQUIRED.value
            for node in ast.nodes
        )
        storyboard = derive_storyboard(ast, max_panels=required_count)
        assert len(storyboard.nodes) == required_count
        assert [node.node_id for node in storyboard.nodes] == [
            node.node_id
            for node in ast.nodes
            if node_attribute(node, "storyboard_role", str)
            == StoryboardRole.REQUIRED.value
        ]

    def test_capacity_cannot_drop_required_beats(self, ast: ProjectionAST) -> None:
        with pytest.raises(DomainValidationError):
            derive_storyboard(ast, max_panels=1)

    def test_sparse_view_reuses_exact_ast_nodes(self, ast: ProjectionAST) -> None:
        storyboard = derive_storyboard(ast)
        ast_by_id = {node.node_id: node for node in ast.nodes}
        assert all(ast_by_id[node.node_id] is node for node in storyboard.nodes)

    def test_storyboard_view_rejects_omit_or_reordered_node_injection(
        self, ast: ProjectionAST
    ) -> None:
        storyboard = derive_storyboard(ast)
        omitted = next(
            node
            for node in ast.nodes
            if node_attribute(node, "storyboard_role", str)
            == StoryboardRole.OMIT.value
        )
        with pytest.raises(DomainValidationError, match="StoryboardProjection"):
            projection_compiler.StoryboardProjection(
                ast=ast,
                nodes=(*storyboard.nodes, omitted),
                manifest=storyboard.manifest,
            )
        with pytest.raises(DomainValidationError, match="StoryboardProjection"):
            projection_compiler.StoryboardProjection(
                ast=ast,
                nodes=tuple(reversed(storyboard.nodes)),
                manifest=storyboard.manifest,
            )
        missing_required = tuple(
            node
            for node in storyboard.nodes
            if node_attribute(node, "storyboard_role", str)
            != StoryboardRole.REQUIRED.value
        )
        with pytest.raises(DomainValidationError, match="required VisualBeat"):
            projection_compiler.StoryboardProjection(
                ast=ast,
                nodes=missing_required,
                manifest=storyboard.manifest,
            )


# required_check: video_full_node_projection
class TestVideoFullNodeProjection:
    def test_video_is_the_complete_ordered_visualbeat_projection(
        self, ast: ProjectionAST
    ) -> None:
        video = derive_video(ast)
        assert video.nodes == ast.nodes
        assert all(left is right for left, right in zip(video.nodes, ast.nodes))

    def test_video_keeps_omit_beats_and_execution_fields(self, ast: ProjectionAST) -> None:
        video = derive_video(ast)
        assert StoryboardRole.OMIT.value in {
            node_attribute(node, "storyboard_role", str) for node in video.nodes
        }
        for node in video.nodes:
            for field_name in (
                "composition",
                "camera",
                "lighting",
                "performance",
                "entering_boundary",
                "exiting_boundary",
            ):
                assert node.attributes[field_name]

    def test_video_carries_typed_reference_and_audio_bindings(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        reference_ids = {
            item["requirement_id"]
            for node in derive_video(ast).nodes
            for item in node.attributes["reference_bindings"]
        }
        audio_ids = {
            item["event_id"]
            for node in derive_video(ast).nodes
            for item in node.attributes["audio_bindings"]
        }
        assert reference_ids == {
            item.requirement_id for item in vec.reference_requirements
        }
        assert audio_ids == {item.event_id for item in vec.audio_events}

    def test_video_view_rejects_missing_or_reordered_ast_node_injection(
        self, ast: ProjectionAST
    ) -> None:
        video = derive_video(ast)
        with pytest.raises(DomainValidationError, match="VideoProjection"):
            projection_compiler.VideoProjection(
                ast=ast,
                nodes=video.nodes[:-1],
                manifest=video.manifest,
            )
        with pytest.raises(DomainValidationError, match="VideoProjection"):
            projection_compiler.VideoProjection(
                ast=ast,
                nodes=tuple(reversed(video.nodes)),
                manifest=video.manifest,
            )
        with pytest.raises(DomainValidationError, match="immutable tuple"):
            projection_compiler.VideoProjection(
                ast=ast,
                nodes=list(video.nodes),
                manifest=video.manifest,
            )


# required_check: shared_tick_state_and_bindings
class TestSharedTickStateAndBindings:
    def test_common_storyboard_and_video_nodes_are_identical(
        self, ast: ProjectionAST
    ) -> None:
        storyboard = derive_storyboard(ast)
        video = derive_video(ast)
        video_by_id = {node.node_id: node for node in video.nodes}
        for node in storyboard.nodes:
            assert video_by_id[node.node_id] is node
            assert node.interval == video_by_id[node.node_id].interval
            assert node.decision_ids == video_by_id[node.node_id].decision_ids

    def test_manifest_is_canonical_and_binds_ast_and_all_nodes(
        self, ast: ProjectionAST
    ) -> None:
        manifest = derive_storyboard(ast).manifest
        assert type(manifest) is ProjectionManifest
        assert manifest.projection_ast_digest == canonical_sha256(ast)
        assert manifest.source_node_ids == tuple(node.node_id for node in ast.nodes)
        assert manifest.vec_digest == node_attribute(ast.nodes[0], "vec_digest", str)

    def test_binding_digests_match_vec_inputs(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        manifest = derive_video(ast).manifest
        assert manifest.reference_binding_digest == canonical_sha256(
            vec.reference_requirements
        )
        assert manifest.audio_binding_digest == canonical_sha256(
            {
                "audio_events": vec.audio_events,
                "voice_requirements": vec.voice_requirements,
            }
        )

    def test_beat_bound_reference_and_audio_do_not_escape_their_target_beat(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        shot = vec.shots[1]
        prop_beat, dialogue_beat, _omitted_beat = shot.visual_beats
        prop_requirement = vec.reference_requirements[1]
        dialogue_event = vec.audio_events[0]
        nodes_by_beat = {node.source_beat_id: node for node in ast.nodes}
        prop_node = nodes_by_beat[prop_beat.beat_id]
        dialogue_node = nodes_by_beat[dialogue_beat.beat_id]

        assert tuple(
            item["requirement_id"]
            for item in node_attribute(prop_node, "reference_bindings", tuple)
        ) == (prop_requirement.requirement_id,)
        assert node_attribute(dialogue_node, "reference_bindings", tuple) == ()
        assert node_attribute(prop_node, "audio_bindings", tuple) == ()
        assert tuple(
            item["event_id"]
            for item in node_attribute(dialogue_node, "audio_bindings", tuple)
        ) == (dialogue_event.event_id,)

        storyboard = derive_storyboard(
            ast, adapter_version=storyboard_adapter_version
        )
        storyboard_delivery = render_storyboard(storyboard)
        panels_by_beat = {
            panel.beat_id: panel for panel in storyboard_delivery.panels
        }
        assert panels_by_beat[prop_beat.beat_id].audio_event_ids == ()
        assert panels_by_beat[dialogue_beat.beat_id].reference_requirement_ids == ()

        profile = CapabilityProfile("scope-test", "1", 10_000, 10, True)
        video = derive_video(
            ast,
            adapter_version=video_adapter_version,
            capability_profile_digest=capability_profile_digest(profile),
        )
        video_delivery = render_video(video, profile=profile)
        lines_by_node = {
            node.node_id: line
            for chunk in video_delivery.prompt_chunks
            for line in chunk.text.splitlines()
            for node in video.nodes
            if line.startswith(f"[node {node.node_id} ")
        }
        assert "audio=()" in lines_by_node[prop_node.node_id]
        assert "references=()" in lines_by_node[dialogue_node.node_id]


# required_check: adapter_only_recompile
class TestAdapterOnlyRecompile:
    def test_adapter_version_change_only_changes_manifest(self, ast: ProjectionAST) -> None:
        first = derive_video(ast, adapter_version="video-adapter-v3.0.0")
        second = derive_video(ast, adapter_version="video-adapter-v3.1.0")
        assert all(left is right for left, right in zip(first.nodes, second.nodes))
        assert first.ast is second.ast is ast
        assert first.manifest.projection_ast_digest == second.manifest.projection_ast_digest
        assert first.adapter_version != second.adapter_version

    def test_adapters_are_pure_and_never_invent_node_ids(self, ast: ProjectionAST) -> None:
        storyboard = derive_storyboard(
            ast, adapter_version=storyboard_adapter_version
        )
        first = render_storyboard(storyboard)
        second = render_storyboard(storyboard)
        assert first == second
        assert tuple(panel.source_node_id for panel in first.panels) == tuple(
            node.node_id for node in storyboard.nodes
        )
        assert first.source_projection_id == ast.projection_id

    def test_profile_must_be_bound_before_render(self, ast: ProjectionAST) -> None:
        profile = CapabilityProfile("test", "1", 100_000, 10, True)
        unbound = derive_video(ast, adapter_version=video_adapter_version)
        with pytest.raises(DomainValidationError):
            render_video(unbound, profile=profile)

    def test_video_chunking_preserves_each_node_exactly_once(
        self, ast: ProjectionAST
    ) -> None:
        profile = CapabilityProfile("test", "1", 5_000, 10, True)
        projection = derive_video(
            ast,
            adapter_version=video_adapter_version,
            capability_profile_digest=capability_profile_digest(profile),
        )
        delivery = render_video(projection, profile=profile)
        assert delivery.nodes == projection.nodes
        assert tuple(
            node_id
            for chunk in delivery.prompt_chunks
            for node_id in chunk.source_node_ids
        ) == tuple(node.node_id for node in ast.nodes)
        assert all(len(chunk.text) <= profile.max_prompt_chars for chunk in delivery.prompt_chunks)


# required_check: canonical_projection_type_identity
# required_check: no_duplicate_projection_authority
class TestCanonicalProjectionAuthority:
    def test_service_exports_exact_domain_types(self) -> None:
        assert projection_compiler.ProjectionAST is canonical_projection.ProjectionAST
        assert projection_compiler.ProjectionNode is canonical_projection.ProjectionNode
        assert projection_compiler.ProjectionManifest is canonical_projection.ProjectionManifest
        assert (
            delivery_capability.CapabilityAdaptationRecord
            is canonical_projection.CapabilityAdaptationRecord
        )

    def test_service_and_adapter_define_no_duplicate_authority_classes(self) -> None:
        compiler_source = inspect.getsource(projection_compiler)
        capability_source = inspect.getsource(delivery_capability)
        assert "class ProjectionAST" not in compiler_source
        assert "class ProjectionNode" not in compiler_source
        assert "class ProjectionManifest" not in compiler_source
        assert "class CapabilityAdaptationRecord" not in capability_source


# required_check: projection_envelope_roundtrip
class TestProjectionEnvelopeRoundtrip:
    def test_canonical_ast_is_accepted_by_projection_envelope(
        self, ast: ProjectionAST, vec: VisualExecutionContract
    ) -> None:
        envelope = ArtifactEnvelope.create(
            artifact_id=ast.projection_id,
            artifact_type=ArtifactKind.PROJECTION_AST,
            payload=ast,
            producer_stage="A6:projection",
            parent_artifact_ids=(vec.contract_id,),
            source_provenance=(SOURCE_REF,),
            knowledge_snapshot_digest=None,
            created_at_utc="2026-08-02T00:00:00+00:00",
        )
        assert envelope.payload is ast
        assert envelope.canonical_payload_sha256 == canonical_sha256(ast)

        wire = canonical_json_bytes(envelope)
        decoded = json.loads(wire.decode("utf-8"))
        encoded = json.dumps(
            decoded,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        assert encoded == wire
        assert decoded["payload"]["projection_id"] == ast.projection_id

    def test_envelope_rejects_noncanonical_projection_payload(self, ast: ProjectionAST) -> None:
        with pytest.raises(DomainValidationError):
            ArtifactEnvelope.create(
                artifact_id=ast.projection_id,
                artifact_type=ArtifactKind.PROJECTION_AST,
                payload=replace(ast, nodes=()),
                producer_stage="A6:projection",
                parent_artifact_ids=(ast.source_vec_artifact_id,),
                source_provenance=(SOURCE_REF,),
                knowledge_snapshot_digest=None,
                created_at_utc="2026-08-02T00:00:00+00:00",
            )


# required_check: capability_adaptation_recorded
class TestCapabilityAdaptationRecorded:
    def test_every_video_degradation_uses_canonical_traceable_record(
        self, ast: ProjectionAST
    ) -> None:
        profile = CapabilityProfile("test-sd2", "1", 100_000, 10, False)
        projection = derive_video(
            ast,
            adapter_version=video_adapter_version,
            capability_profile_digest=capability_profile_digest(profile),
        )
        delivery = render_video(projection, profile=profile)
        assert delivery.adaptation_records
        ast_node_ids = {node.node_id for node in ast.nodes}
        for record in delivery.adaptation_records:
            assert type(record) is CapabilityAdaptationRecord
            assert set(record.source_node_ids) <= ast_node_ids
            assert record.capability_profile_digest == capability_profile_digest(profile)
            assert record.adapter_version == video_adapter_version

    def test_storyboard_reference_budget_loss_is_explicit(
        self, ast: ProjectionAST
    ) -> None:
        profile = CapabilityProfile("board", "1", 100_000, 1, True)
        projection = derive_storyboard(
            ast,
            adapter_version=storyboard_adapter_version,
            capability_profile_digest=capability_profile_digest(profile),
        )
        delivery = render_storyboard(projection, profile=profile)
        assert len(delivery.adaptation_records) == 1
        record = delivery.adaptation_records[0]
        assert type(record) is CapabilityAdaptationRecord
        assert record.adaptation_code == "REFERENCE_SLOT_BUDGET_EXCEEDED"
        assert record.semantic_loss is True
        assert record.source_node_ids
