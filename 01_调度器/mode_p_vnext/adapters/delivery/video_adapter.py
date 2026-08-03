"""Pure video formatter over the complete canonical ProjectionAST view."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from mode_p_vnext.adapters.delivery.capability import (
    CapabilityAdaptationRecord,
    CapabilityProfile,
    adaptation_record,
    capability_profile_digest,
)
from mode_p_vnext.domain.artifact import DomainValidationError
from mode_p_vnext.domain.projection import ProjectionManifest, ProjectionNode
from mode_p_vnext.services.projection_compiler import (
    VideoProjection,
    node_attribute,
)


video_adapter_version = "video-adapter-v3.1.0"


@dataclass(frozen=True)
class VideoPromptChunk:
    """Node-aligned delivery text with explicit AST provenance."""

    text: str
    source_node_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text:
            raise DomainValidationError("VideoPromptChunk text must be non-empty")
        if not self.source_node_ids or len(self.source_node_ids) != len(
            set(self.source_node_ids)
        ):
            raise DomainValidationError(
                "VideoPromptChunk source_node_ids must be non-empty and unique"
            )


@dataclass(frozen=True)
class VideoDelivery:
    nodes: tuple[ProjectionNode, ...]
    source_projection_id: str
    manifest: ProjectionManifest
    adapter_version: str
    adaptation_records: tuple[CapabilityAdaptationRecord, ...]
    prompt_chunks: tuple[VideoPromptChunk, ...]


def _boundary(node: ProjectionNode, attribute_name: str) -> Mapping[str, object]:
    return node_attribute(node, attribute_name, Mapping)


def _format_node(node: ProjectionNode) -> str:
    """Serialize only fields already present on the canonical AST node."""

    entering = _boundary(node, "entering_boundary")
    exiting = _boundary(node, "exiting_boundary")
    return (
        f"[node {node.node_id} beat {node.source_beat_id} shot {node.source_shot_id} "
        f"ticks {node.interval.start_tick}-{node.interval.end_tick} "
        f"state {node.start_state_id}->{node.end_state_id}] "
        f"phase={node_attribute(node, 'phase', str)}; "
        f"subject={node_attribute(node, 'subject_state', str)}; "
        f"attention={node_attribute(node, 'attention', str)}; "
        f"composition={node_attribute(node, 'composition', str)}; "
        f"camera={node_attribute(node, 'camera', str)}; "
        f"lighting={node_attribute(node, 'lighting', str)}; "
        f"performance={node_attribute(node, 'performance', str)}; "
        f"references={node_attribute(node, 'node_reference_requirement_ids', tuple)}; "
        f"audio={node_attribute(node, 'node_audio_event_ids', tuple)}; "
        f"boundaries={entering['boundary_id']}->{exiting['boundary_id']}"
    )


def _pack_node_lines(
    values: tuple[tuple[ProjectionNode, str], ...],
    *,
    max_prompt_chars: int,
) -> tuple[VideoPromptChunk, ...]:
    chunks: list[VideoPromptChunk] = []
    current_lines: list[str] = []
    current_ids: list[str] = []
    current_length = 0
    for node, line in values:
        if len(line) > max_prompt_chars:
            raise DomainValidationError(
                f"formatted node {node.node_id} exceeds max_prompt_chars; "
                "the adapter refuses character-slicing semantic content"
            )
        separator = 1 if current_lines else 0
        if current_lines and current_length + separator + len(line) > max_prompt_chars:
            chunks.append(
                VideoPromptChunk(
                    text="\n".join(current_lines),
                    source_node_ids=tuple(current_ids),
                )
            )
            current_lines = []
            current_ids = []
            current_length = 0
            separator = 0
        current_lines.append(line)
        current_ids.append(node.node_id)
        current_length += separator + len(line)
    if current_lines:
        chunks.append(
            VideoPromptChunk(
                text="\n".join(current_lines),
                source_node_ids=tuple(current_ids),
            )
        )
    return tuple(chunks)


def render_video(
    projection: VideoProjection,
    *,
    adapter_version: str = video_adapter_version,
    profile: CapabilityProfile,
) -> VideoDelivery:
    """Format all AST nodes and record every capability-driven format change."""

    if type(projection) is not VideoProjection:
        raise DomainValidationError("projection must be a VideoProjection")
    if type(profile) is not CapabilityProfile:
        raise DomainValidationError("profile must be a CapabilityProfile")
    if adapter_version != projection.manifest.adapter_version:
        raise DomainValidationError(
            "adapter_version must match the ProjectionManifest; re-derive the adapter view"
        )
    if projection.manifest.capability_profile_digest != capability_profile_digest(profile):
        raise DomainValidationError(
            "delivery CapabilityProfile digest must match the ProjectionManifest"
        )

    formatted = tuple((node, _format_node(node)) for node in projection.nodes)
    by_shot: list[tuple[tuple[ProjectionNode, str], ...]] = []
    for node, line in formatted:
        if not by_shot or by_shot[-1][0][0].source_shot_id != node.source_shot_id:
            by_shot.append(((node, line),))
        else:
            by_shot[-1] = (*by_shot[-1], (node, line))

    records: list[CapabilityAdaptationRecord] = []
    if not profile.internal_cuts_supported and len(by_shot) > 1:
        groups = tuple(by_shot)
        records.extend(
            adaptation_record(
                profile=profile,
                adapter_version=adapter_version,
                adaptation_code="INTERNAL_CUT_SEGMENT_PER_SHOT",
                source_node_ids=tuple(node.node_id for node, _ in group),
                semantic_loss=False,
            )
            for group in groups
        )
    else:
        groups = (formatted,)

    chunks = tuple(
        chunk
        for group in groups
        for chunk in _pack_node_lines(
            group, max_prompt_chars=profile.max_prompt_chars
        )
    )
    minimum_group_count = len(groups)
    if len(chunks) > minimum_group_count:
        records.append(
            adaptation_record(
                profile=profile,
                adapter_version=adapter_version,
                adaptation_code="PROMPT_NODE_ALIGNED_CHUNKING",
                source_node_ids=tuple(node.node_id for node in projection.nodes),
                semantic_loss=False,
            )
        )

    if tuple(
        node_id for chunk in chunks for node_id in chunk.source_node_ids
    ) != tuple(node.node_id for node in projection.nodes):
        raise DomainValidationError("delivery chunks must preserve every AST node exactly once")

    return VideoDelivery(
        nodes=projection.nodes,
        source_projection_id=projection.ast.projection_id,
        manifest=projection.manifest,
        adapter_version=adapter_version,
        adaptation_records=tuple(records),
        prompt_chunks=chunks,
    )


__all__ = [
    "VideoDelivery",
    "VideoPromptChunk",
    "render_video",
    "video_adapter_version",
]
