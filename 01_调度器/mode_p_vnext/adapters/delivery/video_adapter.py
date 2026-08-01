"""Video delivery adapter — formats the video projection and records degradation.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §10 / §14 A6.

The adapter re-emits every node of the video projection (all beats, shots, and
boundaries on the shared timeline).  When the target platform lacks a
capability, the adapter degrades the *delivery format* — e.g. one prompt
segment per shot when internal cuts are unsupported, or chunked delivery when
the formatted prompt would exceed the platform character budget — and records
each degradation as an explicit CapabilityAdaptationRecord.  Degradation
never invents or drops nodes: ``delivery.nodes`` always equals the projection
nodes.
"""

from __future__ import annotations

from dataclasses import dataclass

from mode_p_vnext.adapters.delivery.capability import (
    CapabilityAdaptationRecord,
    CapabilityProfile,
)
from mode_p_vnext.services.projection_compiler import (
    ProjectionNode,
    VideoProjection,
)

video_adapter_version = "video-adapter-v2.1.0"


@dataclass(frozen=True)
class VideoDelivery:
    """Formatted video output plus explicit adaptation records."""

    nodes: tuple[ProjectionNode, ...]
    adapter_version: str
    adaptation_records: tuple[CapabilityAdaptationRecord, ...] = ()
    prompt_chunks: tuple[str, ...] = ()


def _format_shot_node(node: ProjectionNode) -> str:
    return (
        f"[shot {node.source_id} {node.start_tick}-{node.end_tick}] "
        f"{node.camera_pose} | {node.camera_motion} | {node.composition} | "
        f"{node.lighting} | {node.performance} | {node.framing_intent}"
    )


def _format_beat_node(node: ProjectionNode) -> str:
    return (
        f"[beat {node.source_id} {node.start_tick}-{node.end_tick} "
        f"state {node.start_state_id}->{node.end_state_id} role {node.storyboard_role}] "
        f"{node.subject_state} | {node.attention}"
    )


def _format_boundary_node(node: ProjectionNode) -> str:
    return (
        f"[boundary {node.source_id} @{node.start_tick}] {node.transition_intent}"
    )


def _format_node(node: ProjectionNode) -> str:
    if node.node_type == "shot":
        return _format_shot_node(node)
    if node.node_type == "boundary":
        return _format_boundary_node(node)
    return _format_beat_node(node)


def render_video(
    projection: VideoProjection,
    *,
    adapter_version: str = video_adapter_version,
    profile: CapabilityProfile,
) -> VideoDelivery:
    """Format the video projection against a capability profile.

    Pure function: identical inputs produce identical output; no Director
    invocation, no side effects.  The projection nodes are never altered —
    degradation only changes the delivery format and adds records.
    """
    shot_count = sum(1 for node in projection.nodes if node.node_type == "shot")
    records: list[CapabilityAdaptationRecord] = []

    if not profile.internal_cuts_supported and shot_count > 1:
        for node in projection.nodes:
            if node.node_type == "shot":
                records.append(
                    CapabilityAdaptationRecord(
                        node_id=node.node_id,
                        capability="internal_cuts",
                        action="segment_per_shot",
                        reason=(
                            f"platform {profile.platform} does not support "
                            f"internal cuts; delivery segments per shot"
                        ),
                        adapter_version=adapter_version,
                    )
                )

    lines = [_format_node(node) for node in projection.nodes]
    full_prompt = "\n".join(lines)
    chunks: tuple[str, ...] = ()
    if len(full_prompt) > profile.max_prompt_chars:
        chunks = tuple(
            full_prompt[i : i + profile.max_prompt_chars]
            for i in range(0, len(full_prompt), profile.max_prompt_chars)
        )
        records.append(
            CapabilityAdaptationRecord(
                node_id="",
                capability="prompt_length",
                action="chunked",
                reason=(
                    f"formatted prompt {len(full_prompt)} chars exceeds "
                    f"platform budget {profile.max_prompt_chars}"
                ),
                adapter_version=adapter_version,
            )
        )

    return VideoDelivery(
        nodes=projection.nodes,
        adapter_version=adapter_version,
        adaptation_records=tuple(records),
        prompt_chunks=chunks or (full_prompt,),
    )
