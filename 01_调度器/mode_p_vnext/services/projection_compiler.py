"""Compile both delivery views from the sole canonical v3 ProjectionAST.

Architecture authority: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0 §10,
§15 A6, and §16.  This module deliberately imports (and re-exports) the
projection domain types; it must never define competing ProjectionAST,
ProjectionNode, or ProjectionManifest classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import (
    ArtifactKind,
    DomainValidationError,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingCommit
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.projection import (
    ProjectionAST,
    ProjectionManifest,
    ProjectionNode,
)
from mode_p_vnext.domain.time import TickRange
from mode_p_vnext.domain.vec import StoryboardRole, VisualExecutionContract


COMPILER_VERSION = "3.0.0"
STORYBOARD_ADAPTER_VERSION = "storyboard-adapter-v3.0.0"
VIDEO_ADAPTER_VERSION = "video-adapter-v3.0.0"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")
    return value


def _reference_payload(requirement: Any) -> Mapping[str, Any]:
    return {
        "requirement_id": requirement.requirement_id,
        "responsibility": requirement.responsibility.value,
        "source_fact_id": requirement.source_fact_id,
        "source_fact_handle": requirement.source_fact_handle,
        "shot_id": requirement.shot_id,
        "visual_beat_id": requirement.visual_beat_id,
    }


def _audio_payload(event: Any) -> Mapping[str, Any]:
    return {
        "event_id": event.event_id,
        "source_fact_id": event.source_fact_id,
        "source_fact_handle": event.source_fact_handle,
        "shot_id": event.shot_id,
        "visual_beat_id": event.visual_beat_id,
        "marker_tick": event.marker.tick,
        "placement_phase": event.placement_phase.value,
        "character_label": event.character_label,
        "text": event.text,
        "media_duration_ticks": event.media_duration_ticks,
    }


def _voice_payload(requirement: Any) -> Mapping[str, Any]:
    return {
        "requirement_id": requirement.requirement_id,
        "audio_event_id": requirement.audio_event_id,
        "character_label": requirement.character_label,
        "shot_id": requirement.shot_id,
        "visual_beat_id": requirement.visual_beat_id,
    }


def _boundary_payload(boundary: Any) -> Mapping[str, Any]:
    return {
        "boundary_id": boundary.boundary_id,
        "boundary_ordinal": boundary.boundary_ordinal,
        "scene_tick": boundary.scene_tick,
        "from_shot_id": boundary.from_shot_id,
        "to_shot_id": boundary.to_shot_id,
        "before_state_id": boundary.before_state_id,
        "after_state_id": boundary.after_state_id,
        "transition_intent": boundary.transition_intent,
        "decision_ids": boundary.decision_ids,
    }


def _walk(node: ProjectionNode) -> tuple[ProjectionNode, ...]:
    values = [node]
    for child in node.children:
        values.extend(_walk(child))
    return tuple(values)


def projection_nodes(ast: ProjectionAST) -> tuple[ProjectionNode, ...]:
    """Return every canonical node in deterministic source order."""

    if type(ast) is not ProjectionAST:
        raise DomainValidationError(
            "ast must use the exact mode_p_vnext.domain.projection.ProjectionAST type"
        )
    return tuple(node for root in ast.nodes for node in _walk(root))


def node_attribute(node: ProjectionNode, name: str, expected_type: type) -> Any:
    """Read a compiler-owned node attribute with fail-closed type validation."""

    if type(node) is not ProjectionNode:
        raise DomainValidationError("delivery nodes must use the canonical ProjectionNode")
    try:
        value = node.attributes[name]
    except KeyError as exc:
        raise DomainValidationError(
            f"ProjectionNode {node.node_id} is missing required attribute {name}"
        ) from exc
    if not isinstance(value, expected_type):
        raise DomainValidationError(
            f"ProjectionNode {node.node_id} attribute {name} must be "
            f"{expected_type.__name__}"
        )
    return value


@dataclass(frozen=True)
class StoryboardProjection:
    """Ordered sparse view whose nodes remain owned by one canonical AST."""

    ast: ProjectionAST
    nodes: tuple[ProjectionNode, ...]
    manifest: ProjectionManifest

    def __post_init__(self) -> None:
        _validate_projection_view(self.ast, self.nodes, self.manifest)

    @property
    def adapter_version(self) -> str:
        return self.manifest.adapter_version


@dataclass(frozen=True)
class VideoProjection:
    """Full VisualBeat view whose nodes remain owned by one canonical AST."""

    ast: ProjectionAST
    nodes: tuple[ProjectionNode, ...]
    manifest: ProjectionManifest

    def __post_init__(self) -> None:
        _validate_projection_view(self.ast, self.nodes, self.manifest)

    @property
    def adapter_version(self) -> str:
        return self.manifest.adapter_version


def _validate_projection_view(
    ast: ProjectionAST,
    nodes: tuple[ProjectionNode, ...],
    manifest: ProjectionManifest,
) -> None:
    if type(ast) is not ProjectionAST or type(manifest) is not ProjectionManifest:
        raise DomainValidationError("projection views require exact canonical domain types")
    values = tuple(nodes)
    if not values or not all(type(node) is ProjectionNode for node in values):
        raise DomainValidationError("projection view nodes must be canonical ProjectionNode values")
    ast_nodes = projection_nodes(ast)
    ast_by_id = {node.node_id: node for node in ast_nodes}
    if any(ast_by_id.get(node.node_id) is not node for node in values):
        raise DomainValidationError("projection views must retain the exact AST node objects")
    if len(values) != len({node.node_id for node in values}):
        raise DomainValidationError("projection view nodes must not contain duplicates")
    if manifest.projection_ast_digest != canonical_sha256(ast):
        raise DomainValidationError("projection manifest does not bind its canonical AST")
    if manifest.source_node_ids != tuple(node.node_id for node in ast_nodes):
        raise DomainValidationError("projection manifest source_node_ids do not cover the AST")


def _compile_node_attributes(
    *,
    vec: VisualExecutionContract,
    shot: Any,
    beat: Any,
    entering_boundary: Any,
    exiting_boundary: Any,
    scene_interval: TickRange,
    vec_digest: str,
    compiler_version: str,
    capability_profile_digest: str,
    reference_binding_digest: str,
    audio_binding_digest: str,
) -> Mapping[str, Any]:
    references = {
        item.requirement_id: item for item in vec.reference_requirements
    }
    audio_events = {item.event_id: item for item in vec.audio_events}
    voice_by_event = {
        item.audio_event_id: item for item in vec.voice_requirements
    }
    shot_references = tuple(
        _reference_payload(references[item_id])
        for item_id in shot.reference_requirement_ids
    )
    shot_audio = tuple(
        _audio_payload(audio_events[item_id]) for item_id in shot.audio_event_ids
    )
    shot_voices = tuple(
        _voice_payload(voice_by_event[item_id]) for item_id in shot.audio_event_ids
    )
    return {
        "node_kind": "visual_beat",
        "compiler_version": compiler_version,
        "vec_digest": vec_digest,
        "capability_profile_digest": capability_profile_digest,
        "reference_binding_digest": reference_binding_digest,
        "audio_binding_digest": audio_binding_digest,
        "source_shot_ordinal": shot.source_shot_ordinal,
        "source_visual_beat_ordinal": beat.source_visual_beat_ordinal,
        "generation_unit_id": shot.generation_unit_id,
        "generation_mode": shot.generation_mode.value,
        "local_start_tick": beat.interval.start_tick,
        "local_end_tick": beat.interval.end_tick,
        "scene_start_tick": scene_interval.start_tick,
        "scene_end_tick": scene_interval.end_tick,
        "phase": beat.phase.value,
        "storyboard_role": beat.storyboard_role.value,
        "subject_state": beat.subject_state,
        "attention": beat.attention,
        "composition": shot.composition,
        "camera": shot.camera,
        "lighting": shot.lighting,
        "performance": shot.performance,
        "creative_notes": shot.creative_notes,
        "mirror_flip_forbidden": shot.mirror_flip_forbidden,
        "shot_decision_ids": shot.decision_ids,
        "shot_reference_requirement_ids": shot.reference_requirement_ids,
        "beat_reference_requirement_ids": beat.reference_requirement_ids,
        "shot_audio_event_ids": shot.audio_event_ids,
        "beat_audio_event_ids": beat.audio_event_ids,
        "reference_bindings": shot_references,
        "audio_bindings": shot_audio,
        "voice_bindings": shot_voices,
        "entering_boundary": _boundary_payload(entering_boundary),
        "exiting_boundary": _boundary_payload(exiting_boundary),
    }


def compile_projection_ast(
    *,
    vec: VisualExecutionContract,
    blocking_commit: BlockingCommit,
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    program_version: str,
    compiler_version: str = COMPILER_VERSION,
) -> ProjectionAST:
    """Compile one canonical, beat-addressed ProjectionAST from a validated VEC."""

    if type(vec) is not VisualExecutionContract:
        raise DomainValidationError("vec must be the canonical VisualExecutionContract")
    if type(blocking_commit) is not BlockingCommit:
        raise DomainValidationError("blocking_commit must be the canonical BlockingCommit")
    if not isinstance(id_factory, IdFactory):
        raise DomainValidationError("id_factory must be an IdFactory")
    _require_text(episode_id, "episode_id")
    _require_text(scene_id, "scene_id")
    _require_text(program_version, "program_version")
    _require_text(compiler_version, "compiler_version")
    if id_factory.program_version != program_version:
        raise DomainValidationError("IdFactory program_version must match program_version")
    if vec.episode_id != episode_id or vec.scene_id != scene_id:
        raise DomainValidationError("VEC identity must match the compilation context")
    if blocking_commit.scene_id != scene_id:
        raise DomainValidationError("BlockingCommit identity must match the compilation context")
    if vec.blocking_commit_artifact_id != blocking_commit.commit_id:
        raise DomainValidationError("VEC must bind the supplied BlockingCommit exactly")

    commit_beat_ids = {item.beat_id for item in blocking_commit.beats}
    if any(shot.blocking_beat_id not in commit_beat_ids for shot in vec.shots):
        raise DomainValidationError("VEC references a BlockingBeat outside its commit")

    unit_by_shot = {item.shot_id: item for item in vec.generation_units}
    entering_by_shot = {
        item.to_shot_id: item for item in vec.boundaries if item.to_shot_id is not None
    }
    exiting_by_shot = {
        item.from_shot_id: item
        for item in vec.boundaries
        if item.from_shot_id is not None
    }
    if set(unit_by_shot) != {item.shot_id for item in vec.shots}:
        raise DomainValidationError("every VEC Shot requires exactly one GenerationUnit")
    if set(entering_by_shot) != set(unit_by_shot) or set(exiting_by_shot) != set(unit_by_shot):
        raise DomainValidationError("every VEC Shot requires entering and exiting Boundaries")

    vec_digest = canonical_sha256(vec)
    capability_profile_digest = canonical_sha256(vec.capability_profile)
    reference_binding_digest = canonical_sha256(vec.reference_requirements)
    audio_binding_digest = canonical_sha256(
        {
            "audio_events": vec.audio_events,
            "voice_requirements": vec.voice_requirements,
        }
    )

    nodes: list[ProjectionNode] = []
    ordinal = 0
    for shot in vec.shots:
        placement = unit_by_shot[shot.shot_id].scene_placement.interval
        for beat in shot.visual_beats:
            scene_interval = TickRange(
                start_tick=placement.start_tick + beat.interval.start_tick,
                end_tick=placement.start_tick + beat.interval.end_tick,
            )
            if scene_interval.end_tick > placement.end_tick:
                raise DomainValidationError("VisualBeat scene interval escapes its Shot placement")
            node_id = id_factory.create(
                artifact_kind=ArtifactKind.PROJECTION_AST,
                episode_id=episode_id,
                scene_id=scene_id,
                stage="projection:visual-beat",
                input_digest=vec_digest,
                ordinal=ordinal,
            )
            nodes.append(
                ProjectionNode(
                    node_id=node_id,
                    source_beat_id=beat.beat_id,
                    source_shot_id=shot.shot_id,
                    interval=scene_interval,
                    start_state_id=beat.start_state_id,
                    end_state_id=beat.end_state_id,
                    decision_ids=beat.decision_ids,
                    attributes=_compile_node_attributes(
                        vec=vec,
                        shot=shot,
                        beat=beat,
                        entering_boundary=entering_by_shot[shot.shot_id],
                        exiting_boundary=exiting_by_shot[shot.shot_id],
                        scene_interval=scene_interval,
                        vec_digest=vec_digest,
                        compiler_version=compiler_version,
                        capability_profile_digest=capability_profile_digest,
                        reference_binding_digest=reference_binding_digest,
                        audio_binding_digest=audio_binding_digest,
                    ),
                )
            )
            ordinal += 1

    projection_id = id_factory.create(
        artifact_kind=ArtifactKind.PROJECTION_AST,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="projection:ast",
        input_digest=vec_digest,
        ordinal=0,
    )
    return ProjectionAST(
        projection_id=projection_id,
        source_vec_artifact_id=vec.contract_id,
        nodes=tuple(nodes),
    )


def _consistent_digest_attribute(ast: ProjectionAST, name: str) -> str:
    values = {
        node_attribute(node, name, str) for node in projection_nodes(ast)
    }
    if len(values) != 1:
        raise DomainValidationError(f"ProjectionAST nodes disagree on {name}")
    return values.pop()


def _build_manifest(
    ast: ProjectionAST,
    *,
    adapter_version: str,
    capability_profile_digest: str | None,
) -> ProjectionManifest:
    _require_text(adapter_version, "adapter_version")
    nodes = projection_nodes(ast)
    compiler_versions = {
        node_attribute(node, "compiler_version", str) for node in nodes
    }
    if len(compiler_versions) != 1:
        raise DomainValidationError("ProjectionAST nodes disagree on compiler_version")
    compiled_capability_digest = _consistent_digest_attribute(
        ast, "capability_profile_digest"
    )
    selected_capability_digest = (
        compiled_capability_digest
        if capability_profile_digest is None
        else capability_profile_digest
    )
    return ProjectionManifest(
        vec_digest=_consistent_digest_attribute(ast, "vec_digest"),
        projection_ast_digest=canonical_sha256(ast),
        source_node_ids=tuple(node.node_id for node in nodes),
        compiler_version=compiler_versions.pop(),
        adapter_version=adapter_version,
        capability_profile_digest=selected_capability_digest,
        reference_binding_digest=_consistent_digest_attribute(
            ast, "reference_binding_digest"
        ),
        audio_binding_digest=_consistent_digest_attribute(ast, "audio_binding_digest"),
    )


def derive_storyboard(
    ast: ProjectionAST,
    *,
    adapter_version: str = STORYBOARD_ADAPTER_VERSION,
    capability_profile_digest: str | None = None,
    max_panels: int | None = None,
) -> StoryboardProjection:
    """Select required beats plus capacity-permitting optional beats in AST order."""

    nodes = projection_nodes(ast)
    required = tuple(
        node
        for node in nodes
        if node_attribute(node, "storyboard_role", str)
        == StoryboardRole.REQUIRED.value
    )
    optional = tuple(
        node
        for node in nodes
        if node_attribute(node, "storyboard_role", str)
        == StoryboardRole.OPTIONAL.value
    )
    roles = {
        node_attribute(node, "storyboard_role", str) for node in nodes
    }
    if not roles.issubset({item.value for item in StoryboardRole}):
        raise DomainValidationError("ProjectionAST contains an unknown storyboard role")

    if max_panels is not None:
        if isinstance(max_panels, bool) or not isinstance(max_panels, int) or max_panels < 1:
            raise DomainValidationError("max_panels must be a positive integer")
        if max_panels < len(required):
            raise DomainValidationError(
                "max_panels cannot exclude a required storyboard VisualBeat"
            )
        optional = optional[: max_panels - len(required)]
    selected_ids = {node.node_id for node in (*required, *optional)}
    selected = tuple(node for node in nodes if node.node_id in selected_ids)
    if not selected:
        raise DomainValidationError("storyboard projection cannot be empty")
    manifest = _build_manifest(
        ast,
        adapter_version=adapter_version,
        capability_profile_digest=capability_profile_digest,
    )
    return StoryboardProjection(ast=ast, nodes=selected, manifest=manifest)


def derive_video(
    ast: ProjectionAST,
    *,
    adapter_version: str = VIDEO_ADAPTER_VERSION,
    capability_profile_digest: str | None = None,
) -> VideoProjection:
    """Return the complete ordered VisualBeat projection from the same AST."""

    nodes = projection_nodes(ast)
    manifest = _build_manifest(
        ast,
        adapter_version=adapter_version,
        capability_profile_digest=capability_profile_digest,
    )
    return VideoProjection(ast=ast, nodes=nodes, manifest=manifest)


__all__ = [
    "COMPILER_VERSION",
    "ProjectionAST",
    "ProjectionManifest",
    "ProjectionNode",
    "StoryboardProjection",
    "VideoProjection",
    "compile_projection_ast",
    "derive_storyboard",
    "derive_video",
    "node_attribute",
    "projection_nodes",
]
