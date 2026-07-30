"""Deterministic, dual projection of one VisualExecutionContract.

The compilers never infer a new event from a storyboard panel.  Every panel
and every video clause is a deliberately reduced representation of the same
VEC nodes, with reference/audio bindings supplied as typed operational input.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence, Tuple

from .cache import ContentAddressedCache, content_address
from .contracts import (
    DirectorContractError,
    DialogueEvent,
    REFERENCE_BINDING_ROLES,
    REFERENCE_BINDING_SCOPES,
    VisualExecutionContract,
    VisualShot,
)


def _require(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise DirectorContractError(f"{field_name} is required")


@dataclass(frozen=True)
class ReferenceBinding:
    """An asset is authoritative because of its role, never its upload index."""

    binding_id: str
    asset_id: str
    role: str
    scope_kind: str
    scope_id: str
    priority: int

    def __post_init__(self) -> None:
        for field_name, value in (
            ("binding_id", self.binding_id), ("asset_id", self.asset_id),
            ("scope_id", self.scope_id),
        ):
            _require(value, field_name)
        if self.role not in REFERENCE_BINDING_ROLES:
            raise DirectorContractError("reference binding role is invalid")
        if self.scope_kind not in REFERENCE_BINDING_SCOPES:
            raise DirectorContractError("reference binding scope is invalid")
        if not isinstance(self.priority, int) or self.priority < 1:
            raise DirectorContractError("reference binding priority must be a positive integer")
        if "@图片" in self.asset_id or "storyboard_whole" in self.role:
            raise DirectorContractError("platform image order or whole-board authority is forbidden")


@dataclass(frozen=True)
class VoiceBinding:
    event_id: str
    character_id: str
    voice_asset_id: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("event_id", self.event_id), ("character_id", self.character_id),
            ("voice_asset_id", self.voice_asset_id),
        ):
            _require(value, field_name)


@dataclass(frozen=True)
class ProjectionBindings:
    references: Tuple[ReferenceBinding, ...]
    voices: Tuple[VoiceBinding, ...]

    @property
    def reference_fingerprint(self) -> str:
        return content_address("director-vnext1/reference-bindings", {"references": self.references})

    @property
    def audio_fingerprint(self) -> str:
        return content_address("director-vnext1/audio-bindings", {"voices": self.voices})

    def validate_for(self, vec: VisualExecutionContract) -> None:
        binding_ids = [binding.binding_id for binding in self.references]
        voice_event_ids = [binding.event_id for binding in self.voices]
        if len(binding_ids) != len(set(binding_ids)) or len(voice_event_ids) != len(set(voice_event_ids)):
            raise DirectorContractError("reference and voice binding IDs must be unique")
        actual_priority = {
            (binding.role, binding.scope_kind, binding.scope_id): max(
                binding.priority,
                *(
                    other.priority
                    for other in self.references
                    if (other.role, other.scope_kind, other.scope_id)
                    == (binding.role, binding.scope_kind, binding.scope_id)
                ),
            )
            for binding in self.references
        }
        for requirement in vec.reference_binding_requirements:
            key = (requirement.role, requirement.scope_kind, requirement.scope_id)
            if actual_priority.get(key, 0) < requirement.minimum_priority:
                raise DirectorContractError("projection bindings do not satisfy a VEC reference requirement")
        voice_map = {binding.event_id: binding for binding in self.voices}
        for event in vec.dialogue_events:
            binding = voice_map.get(event.event_id)
            if binding is None:
                raise DirectorContractError("every dialogue event needs a voice binding")
            if binding.character_id != event.character_id or binding.voice_asset_id != event.voice_asset_id:
                raise DirectorContractError("voice binding must exactly match VEC dialogue character and asset")


@dataclass(frozen=True)
class ProjectionManifest:
    projection_kind: str
    contract_fingerprint: str
    blocking_commit_hashes: Tuple[str, ...]
    decision_ids: Tuple[str, ...]
    source_node_ids: Tuple[str, ...]
    compiler_version: str
    adapter_version: str
    reference_binding_fingerprint: str
    audio_binding_fingerprint: str


@dataclass(frozen=True)
class ProjectedShotNode:
    """Shared AST node used in both projections for field-level homology."""

    shot_id: str
    segment_id: str
    start_tick: int
    end_tick: int
    dramatic_function: str
    attention_target: str
    information_action: str
    blocking_beat_id: str
    axis_id: str
    camera_side: str
    screen_order: Tuple[str, ...]
    shot_size: str
    focal_intent: str
    camera_pose: str
    camera_motion: str
    composition: str
    lighting: str
    performance: str
    gaze_targets: Tuple[str, ...]
    prop_state_ids: Tuple[str, ...]
    dialogue_event_ids: Tuple[str, ...]
    start_state_id: str
    end_state_id: str
    cut_in_reason: str
    cut_out_reason: str
    selected_capsule_ids: Tuple[str, ...]
    freedom_corridor: Tuple[str, ...]
    decision_id: str
    mirror_flip_forbidden: bool


@dataclass(frozen=True)
class StoryboardPanel:
    panel_id: str
    source_node_ids: Tuple[str, ...]
    phase: str
    shot_node: ProjectedShotNode


@dataclass(frozen=True)
class StoryboardProjection:
    manifest: ProjectionManifest
    panels: Tuple[StoryboardPanel, ...]
    shot_nodes: Tuple[ProjectedShotNode, ...]
    prompt_text: str


@dataclass(frozen=True)
class VideoProjection:
    manifest: ProjectionManifest
    shot_nodes: Tuple[ProjectedShotNode, ...]
    boundary_nodes: Tuple[Tuple[str, str, str, str], ...]
    dialogue_events: Tuple[DialogueEvent, ...]
    prompt_text: str


class ProjectionCompiler:
    """Pure compiler; adapter changes only affect the video projection cache key."""

    COMPILER_VERSION = "director-vnext1-projection-1"

    def __init__(self, cache: ContentAddressedCache | None = None) -> None:
        self.cache = cache or ContentAddressedCache()

    def compile_storyboard(
        self, vec: VisualExecutionContract, bindings: ProjectionBindings
    ) -> StoryboardProjection:
        bindings.validate_for(vec)
        key = content_address(
            "director-vnext1/storyboard-projection",
            {"vec": vec, "references": bindings.references, "voices": bindings.voices, "compiler": self.COMPILER_VERSION},
        )
        cached = self.cache.get(key)
        if cached is not None:
            if not isinstance(cached, StoryboardProjection):
                raise DirectorContractError("storyboard cache entry type is corrupted")
            return cached
        nodes = tuple(_shot_node(shot) for shot in vec.shots)
        panels = _panels_for(nodes, vec)
        manifest = _manifest("storyboard", vec, bindings, self.COMPILER_VERSION, "none")
        prompt = _storyboard_prompt(nodes, panels, bindings)
        return self.cache.put(key, StoryboardProjection(manifest, panels, nodes, prompt))

    def compile_video(
        self, vec: VisualExecutionContract, bindings: ProjectionBindings, *, adapter_version: str
    ) -> VideoProjection:
        bindings.validate_for(vec)
        _require(adapter_version, "adapter_version")
        key = content_address(
            "director-vnext1/video-projection",
            {
                "vec": vec, "references": bindings.references, "voices": bindings.voices,
                "compiler": self.COMPILER_VERSION, "adapter": adapter_version,
            },
        )
        cached = self.cache.get(key)
        if cached is not None:
            if not isinstance(cached, VideoProjection):
                raise DirectorContractError("video cache entry type is corrupted")
            return cached
        nodes = tuple(_shot_node(shot) for shot in vec.shots)
        boundary_nodes = tuple(
            (item.from_shot_id, item.to_shot_id, item.mode, item.reason) for item in vec.boundaries
        )
        manifest = _manifest("video", vec, bindings, self.COMPILER_VERSION, adapter_version)
        prompt = _video_prompt(nodes, vec.dialogue_events, boundary_nodes, bindings)
        return self.cache.put(key, VideoProjection(manifest, nodes, boundary_nodes, vec.dialogue_events, prompt))


def _shot_node(shot: VisualShot) -> ProjectedShotNode:
    return ProjectedShotNode(
        shot_id=shot.shot_id, segment_id=shot.segment_id, start_tick=shot.start_tick, end_tick=shot.end_tick,
        dramatic_function=shot.dramatic_function, attention_target=shot.attention_target,
        information_action=shot.information_action, blocking_beat_id=shot.blocking_beat_id,
        axis_id=shot.axis_id, camera_side=shot.camera_side, screen_order=shot.screen_order,
        shot_size=shot.shot_size, focal_intent=shot.focal_intent, camera_pose=shot.camera_pose,
        camera_motion=shot.camera_motion, composition=shot.composition, lighting=shot.lighting,
        performance=shot.performance, gaze_targets=shot.gaze_targets, prop_state_ids=shot.prop_state_ids,
        dialogue_event_ids=shot.dialogue_event_ids, start_state_id=shot.start_state_id,
        end_state_id=shot.end_state_id, cut_in_reason=shot.cut_in_reason,
        cut_out_reason=shot.cut_out_reason, selected_capsule_ids=shot.selected_capsule_ids,
        freedom_corridor=shot.freedom_corridor, decision_id=shot.decision_id,
        mirror_flip_forbidden=shot.mirror_flip_forbidden,
    )


def _manifest(
    kind: str, vec: VisualExecutionContract, bindings: ProjectionBindings, compiler_version: str, adapter_version: str
) -> ProjectionManifest:
    sources = [f"contract:{vec.contract_id}", f"blocking:{vec.blocking_commit.commit_id}"]
    sources.extend(f"decision:{item.decision_id}" for item in vec.decisions)
    sources.extend(f"beat:{item.beat_id}" for item in vec.blocking_commit.beats)
    sources.extend(f"shot:{item.shot_id}" for item in vec.shots)
    sources.extend(f"boundary:{item.boundary_id}" for item in vec.boundaries)
    sources.extend(f"dialogue:{item.event_id}" for item in vec.dialogue_events)
    sources.extend(f"reference_requirement:{item.requirement_id}" for item in vec.reference_binding_requirements)
    return ProjectionManifest(
        projection_kind=kind, contract_fingerprint=vec.fingerprint,
        blocking_commit_hashes=(vec.blocking_commit.fingerprint,),
        decision_ids=tuple(item.decision_id for item in vec.decisions), source_node_ids=tuple(sources),
        compiler_version=compiler_version, adapter_version=adapter_version,
        reference_binding_fingerprint=bindings.reference_fingerprint,
        audio_binding_fingerprint=bindings.audio_fingerprint,
    )


def _panels_for(nodes: Tuple[ProjectedShotNode, ...], vec: VisualExecutionContract) -> Tuple[StoryboardPanel, ...]:
    panels: list[StoryboardPanel] = []
    for index, node in enumerate(nodes):
        panels.append(StoryboardPanel(f"panel-{node.shot_id}-in", (f"shot:{node.shot_id}", f"beat:{node.blocking_beat_id}"), "incoming", node))
        if index == len(nodes) - 1:
            panels.append(StoryboardPanel(f"panel-{node.shot_id}-out", (f"shot:{node.shot_id}",), "outgoing", node))
    for boundary in vec.boundaries:
        for node in nodes:
            if node.shot_id == boundary.from_shot_id:
                panels.append(StoryboardPanel(f"panel-{boundary.boundary_id}-before", (f"boundary:{boundary.boundary_id}", f"shot:{node.shot_id}"), "boundary_before", node))
            if node.shot_id == boundary.to_shot_id:
                panels.append(StoryboardPanel(f"panel-{boundary.boundary_id}-after", (f"boundary:{boundary.boundary_id}", f"shot:{node.shot_id}"), "boundary_after", node))
    return tuple(panels)


def _storyboard_prompt(nodes: Tuple[ProjectedShotNode, ...], panels: Tuple[StoryboardPanel, ...], bindings: ProjectionBindings) -> str:
    clauses = ["Create only the selected visual-beat panels from the approved scene plan."]
    clauses.append("Use the bound identity, wardrobe, layout, and prop-role references for their assigned responsibilities.")
    for panel in panels:
        node = panel.shot_node
        clauses.append(
            f"{panel.phase}: {node.shot_size}; {node.composition}; {node.screen_order}; "
            f"gaze {node.gaze_targets}; performance {node.performance}; lighting {node.lighting}."
        )
    return "\n".join(clauses)


def _video_prompt(
    nodes: Tuple[ProjectedShotNode, ...], events: Tuple[DialogueEvent, ...], boundaries: Tuple[Tuple[str, str, str, str], ...], bindings: ProjectionBindings
) -> str:
    event_map = {event.event_id: event for event in events}
    clauses = ["Create one local-time video segment from the approved scene plan."]
    clauses.append("Use the bound identity, wardrobe, blocking-layout, prop-geometry, scene-layout, and voice references only for their declared roles.")
    for node in nodes:
        start, end = node.start_tick / 10, node.end_tick / 10
        dialogue = [event_map[event_id] for event_id in node.dialogue_event_ids]
        spoken = " ".join(f"{event.character_id} says: {event.text}" for event in dialogue)
        clauses.append(
            f"From {start:.1f}s to {end:.1f}s, {node.composition}; {node.camera_pose}; {node.camera_motion}; "
            f"screen order {node.screen_order}; gaze {node.gaze_targets}; {node.performance}; {spoken}".strip()
        )
    for _, _, mode, reason in boundaries:
        clauses.append(f"Transition mode {mode} because {reason}.")
    return "\n".join(clauses)
