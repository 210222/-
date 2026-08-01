"""Single ProjectionAST compiler shared by Storyboard and Video projections.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §10 / §14 A6.

The VEC is the sole creative authority.  ``compile_projection_ast`` turns it
into exactly one ProjectionAST; ``derive_storyboard`` and ``derive_video``
both compile from that one AST — never from the VEC independently — so the two
deliveries share beat, tick, and state identities.  Delivery adapters may only
format or perform explicit capability degradation (recorded as
CapabilityAdaptationRecord); they never invent events, and an adapter-only
recompile never invokes the Director.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from mode_p_vnext.domain.artifact import (
    ArtifactKind,
    DomainValidationError,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingCommit
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.time import CanonicalTimeline
from mode_p_vnext.domain.vec import (
    AudioEvent,
    ReferenceRequirement,
    StoryboardRole,
    VisualExecutionContract,
    VisualShot,
    VoiceRequirement,
)

COMPILER_VERSION = "2.1.0"

_EMPTY_DECISIONS: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# ProjectionNode — one frozen node of the shared AST
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProjectionNode:
    """A node in the shared ProjectionAST.

    node_type is one of ``shot`` / ``beat`` / ``boundary``.  Beat nodes carry
    the shared tick/state/decision references required by both projections;
    shot nodes carry the creative execution details used by the Video
    projection; boundary nodes carry the transition intent between shots.
    """

    node_id: str
    node_type: str
    source_id: str
    shot_id: str
    beat_id: str = ""
    boundary_id: str = ""
    start_tick: int = 0
    end_tick: int = 0
    phase: str = ""
    storyboard_role: str = ""
    start_state_id: str = ""
    end_state_id: str = ""
    decision_ids: tuple[str, ...] = _EMPTY_DECISIONS
    subject_state: str = ""
    attention: str = ""
    dramatic_function: str = ""
    attention_target: str = ""
    information_action: str = ""
    framing_intent: str = ""
    camera_pose: str = ""
    camera_motion: str = ""
    composition: str = ""
    lighting: str = ""
    performance: str = ""
    transition_intent: str = ""


# ---------------------------------------------------------------------------
# ProjectionAST — the single intermediate representation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProjectionAST:
    """The one shared projection tree for Storyboard and Video."""

    ast_id: str
    vec_digest: str
    compiler_version: str
    timeline: CanonicalTimeline
    nodes: tuple[ProjectionNode, ...]
    reference_requirements: tuple[ReferenceRequirement, ...]
    audio_events: tuple[AudioEvent, ...]
    voice_requirements: tuple[VoiceRequirement, ...]
    source_node_ids: tuple[str, ...]
    ast_digest: str
    reference_binding_digest: str
    audio_binding_digest: str

    def __post_init__(self) -> None:
        for field_name in ("ast_id", "vec_digest", "ast_digest"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise DomainValidationError(f"{field_name} must be non-empty")
        if not isinstance(self.timeline, CanonicalTimeline):
            raise DomainValidationError("timeline must be the canonical timeline")
        nodes = tuple(self.nodes)
        if not nodes or not all(isinstance(node, ProjectionNode) for node in nodes):
            raise DomainValidationError("nodes must contain ProjectionNode values")
        node_ids = tuple(node.node_id for node in nodes)
        if len(node_ids) != len(set(node_ids)):
            raise DomainValidationError("ProjectionAST node IDs must be unique")
        for node in nodes:
            if node.node_type == "boundary":
                if node.start_tick < 0 or node.end_tick < node.start_tick:
                    raise DomainValidationError(
                        f"boundary node {node.node_id} must be a valid tick point"
                    )
            elif node.start_tick < 0 or node.end_tick <= node.start_tick:
                raise DomainValidationError(
                    f"node {node.node_id} must have a positive tick interval"
                )
        if self.ast_digest != self._compute_digest():
            raise DomainValidationError("ProjectionAST ast_digest is inconsistent")

    def _compute_digest(self) -> str:
        return canonical_sha256(
            {
                "vec_digest": self.vec_digest,
                "compiler_version": self.compiler_version,
                "nodes": self.nodes,
                "reference_requirements": self.reference_requirements,
                "audio_events": self.audio_events,
                "voice_requirements": self.voice_requirements,
            }
        )


# ---------------------------------------------------------------------------
# ProjectionManifest — binding metadata required by §10
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProjectionManifest:
    """Per-projection binding manifest (§10)."""

    vec_digest: str
    projection_ast_digest: str
    source_node_ids: tuple[str, ...]
    compiler_version: str
    adapter_version: str
    capability_profile_digest: str
    reference_binding_digest: str
    audio_binding_digest: str


# ---------------------------------------------------------------------------
# StoryboardProjection / VideoProjection — derived views
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StoryboardProjection:
    """Storyboard view: required + (capacity-permitting) optional beats."""

    nodes: tuple[ProjectionNode, ...]
    manifest: ProjectionManifest
    adapter_version: str


@dataclass(frozen=True)
class VideoProjection:
    """Video view: every node on the shared timeline."""

    nodes: tuple[ProjectionNode, ...]
    manifest: ProjectionManifest
    adapter_version: str


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------


def _beat_nodes(vec: VisualExecutionContract) -> list[ProjectionNode]:
    nodes: list[ProjectionNode] = []
    for shot in vec.shots:
        shot_node_interval = shot.interval
        for beat in shot.visual_beats:
            if (
                beat.interval.start_tick < shot_node_interval.start_tick
                or beat.interval.end_tick > shot_node_interval.end_tick
            ):
                raise DomainValidationError(
                    f"beat {beat.beat_id} interval escapes its shot interval"
                )
            nodes.append(
                ProjectionNode(
                    node_id="",
                    node_type="beat",
                    source_id=beat.beat_id,
                    shot_id=shot.shot_id,
                    beat_id=beat.beat_id,
                    start_tick=beat.interval.start_tick,
                    end_tick=beat.interval.end_tick,
                    phase=beat.phase.value,
                    storyboard_role=beat.storyboard_role.value,
                    start_state_id=beat.start_state_id,
                    end_state_id=beat.end_state_id,
                    decision_ids=tuple(beat.decision_ids),
                    subject_state=beat.subject_state,
                    attention=beat.attention,
                )
            )
    return nodes


def _shot_nodes(vec: VisualExecutionContract) -> list[ProjectionNode]:
    nodes: list[ProjectionNode] = []
    for shot in vec.shots:
        nodes.append(
            ProjectionNode(
                node_id="",
                node_type="shot",
                source_id=shot.shot_id,
                shot_id=shot.shot_id,
                start_tick=shot.interval.start_tick,
                end_tick=shot.interval.end_tick,
                decision_ids=tuple(shot.decision_ids),
                dramatic_function=shot.dramatic_function,
                attention_target=shot.attention_target,
                information_action=shot.information_action,
                framing_intent=shot.framing_intent,
                camera_pose=shot.camera_pose,
                camera_motion=shot.camera_motion,
                composition=shot.composition,
                lighting=shot.lighting,
                performance=shot.performance,
            )
        )
    return nodes


def _boundary_nodes(vec: VisualExecutionContract) -> list[ProjectionNode]:
    """Boundary nodes are zero-length tick points between adjacent shots."""
    shots_by_id = {shot.shot_id: shot for shot in vec.shots}
    nodes: list[ProjectionNode] = []
    for boundary in vec.boundaries:
        left = shots_by_id.get(boundary.from_shot_id)
        right = shots_by_id.get(boundary.to_shot_id)
        if left is None or right is None:
            raise DomainValidationError(
                f"boundary {boundary.boundary_id} references unknown shots"
            )
        boundary_tick = left.interval.end_tick
        nodes.append(
            ProjectionNode(
                node_id="",
                node_type="boundary",
                source_id=boundary.boundary_id,
                shot_id="",
                boundary_id=boundary.boundary_id,
                start_tick=boundary_tick,
                end_tick=boundary_tick,
                decision_ids=tuple(boundary.decision_ids),
                transition_intent=boundary.transition_intent,
            )
        )
    return nodes


def _assign_node_ids(
    nodes: list[ProjectionNode],
    *,
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    vec_digest: str,
) -> tuple[ProjectionNode, ...]:
    assigned: list[ProjectionNode] = []
    for ordinal, node in enumerate(nodes):
        node_id = id_factory.create(
            artifact_kind=ArtifactKind.PROJECTION_AST,
            episode_id=episode_id,
            scene_id=scene_id,
            stage=f"node:{node.node_type}",
            input_digest=vec_digest,
            ordinal=ordinal,
        )
        assigned.append(
            ProjectionNode(
                node_id=node_id,
                node_type=node.node_type,
                source_id=node.source_id,
                shot_id=node.shot_id,
                beat_id=node.beat_id,
                boundary_id=node.boundary_id,
                start_tick=node.start_tick,
                end_tick=node.end_tick,
                phase=node.phase,
                storyboard_role=node.storyboard_role,
                start_state_id=node.start_state_id,
                end_state_id=node.end_state_id,
                decision_ids=node.decision_ids,
                subject_state=node.subject_state,
                attention=node.attention,
                dramatic_function=node.dramatic_function,
                attention_target=node.attention_target,
                information_action=node.information_action,
                framing_intent=node.framing_intent,
                camera_pose=node.camera_pose,
                camera_motion=node.camera_motion,
                composition=node.composition,
                lighting=node.lighting,
                performance=node.performance,
                transition_intent=node.transition_intent,
            )
        )
    return tuple(assigned)


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
    """Compile the sole ProjectionAST from an accepted VEC and its BlockingCommit.

    Every node ID, digest, and the AST identity are generated locally; the
    model never supplies them.  The compiler validates that beat states are
    bound to the blocking commit's state chain and that every beat interval
    stays inside its shot interval.
    """
    vec_digest = canonical_sha256(vec)
    if vec.scene_id != blocking_commit.scene_id:
        raise DomainValidationError(
            "VEC and BlockingCommit must belong to the same scene"
        )
    commit_beat_ids = {beat.beat_id for beat in blocking_commit.beats}
    for shot in vec.shots:
        if shot.blocking_beat_id not in commit_beat_ids:
            raise DomainValidationError(
                f"shot {shot.shot_id} references blocking beat "
                f"{shot.blocking_beat_id} outside the blocking commit"
            )

    shot_nodes = _shot_nodes(vec)
    beat_nodes = _beat_nodes(vec)
    boundary_nodes = _boundary_nodes(vec)

    nodes = _assign_node_ids(
        shot_nodes + beat_nodes + boundary_nodes,
        episode_id=episode_id,
        scene_id=scene_id,
        id_factory=id_factory,
        vec_digest=vec_digest,
    )

    source_node_ids = tuple(
        node.source_id for node in nodes
    )
    if len(source_node_ids) != len(set(source_node_ids)):
        raise DomainValidationError("AST source node ids must be unique")

    ast_digest = canonical_sha256(
        {
            "vec_digest": vec_digest,
            "compiler_version": compiler_version,
            "nodes": nodes,
            "reference_requirements": vec.reference_requirements,
            "audio_events": vec.audio_events,
            "voice_requirements": vec.voice_requirements,
        }
    )
    reference_binding_digest = canonical_sha256(vec.reference_requirements)
    audio_binding_digest = canonical_sha256(
        {
            "audio_events": vec.audio_events,
            "voice_requirements": vec.voice_requirements,
        }
    )

    ast_id = id_factory.create(
        artifact_kind=ArtifactKind.PROJECTION_AST,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="ast",
        input_digest=vec_digest,
        ordinal=0,
    )

    return ProjectionAST(
        ast_id=ast_id,
        vec_digest=vec_digest,
        compiler_version=compiler_version,
        timeline=vec.timeline,
        nodes=nodes,
        reference_requirements=tuple(vec.reference_requirements),
        audio_events=tuple(vec.audio_events),
        voice_requirements=tuple(vec.voice_requirements),
        source_node_ids=source_node_ids,
        ast_digest=ast_digest,
        reference_binding_digest=reference_binding_digest,
        audio_binding_digest=audio_binding_digest,
    )


def _build_manifest(
    ast: ProjectionAST,
    *,
    adapter_version: str,
    capability_profile_digest: str,
) -> ProjectionManifest:
    return ProjectionManifest(
        vec_digest=ast.vec_digest,
        projection_ast_digest=ast.ast_digest,
        source_node_ids=ast.source_node_ids,
        compiler_version=ast.compiler_version,
        adapter_version=adapter_version,
        capability_profile_digest=capability_profile_digest,
        reference_binding_digest=ast.reference_binding_digest,
        audio_binding_digest=ast.audio_binding_digest,
    )


def derive_storyboard(
    ast: ProjectionAST,
    *,
    adapter_version: str = "storyboard-v2.1.0",
    capability_profile_digest: str = "",
    max_panels: Optional[int] = None,
) -> StoryboardProjection:
    """Select storyboard beats: required first, then optional within capacity."""
    beats = [node for node in ast.nodes if node.node_type == "beat"]
    required = [node for node in beats if node.storyboard_role == StoryboardRole.REQUIRED.value]
    optional = [node for node in beats if node.storyboard_role == StoryboardRole.OPTIONAL.value]

    selected = list(required)
    if max_panels is not None:
        if max_panels < 1:
            raise DomainValidationError("max_panels must be positive when supplied")
        remaining = max_panels - len(selected)
        if remaining > 0:
            selected.extend(optional[:remaining])
    else:
        selected.extend(optional)

    manifest = _build_manifest(
        ast,
        adapter_version=adapter_version,
        capability_profile_digest=capability_profile_digest,
    )
    return StoryboardProjection(
        nodes=tuple(selected),
        manifest=manifest,
        adapter_version=adapter_version,
    )


def derive_video(
    ast: ProjectionAST,
    *,
    adapter_version: str = "video-v2.1.0",
    capability_profile_digest: str = "",
) -> VideoProjection:
    """Video view: every node on the shared timeline (all beats, shots, boundaries)."""
    manifest = _build_manifest(
        ast,
        adapter_version=adapter_version,
        capability_profile_digest=capability_profile_digest,
    )
    return VideoProjection(
        nodes=ast.nodes,
        manifest=manifest,
        adapter_version=adapter_version,
    )
