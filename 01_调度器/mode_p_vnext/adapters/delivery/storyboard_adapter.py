"""Pure storyboard formatter over a sparse canonical ProjectionAST view."""

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
from mode_p_vnext.domain.projection import ProjectionManifest
from mode_p_vnext.services.projection_compiler import (
    StoryboardProjection,
    node_attribute,
)


storyboard_adapter_version = "storyboard-adapter-v3.1.0"


@dataclass(frozen=True)
class StoryboardPanel:
    """A lossless formatting view of one selected canonical VisualBeat node."""

    panel_id: str
    source_node_id: str
    beat_id: str
    shot_id: str
    phase: str
    start_tick: int
    end_tick: int
    start_state_id: str
    end_state_id: str
    subject_state: str
    attention: str
    decision_ids: tuple[str, ...]
    reference_requirement_ids: tuple[str, ...]
    audio_event_ids: tuple[str, ...]
    entering_boundary_id: str
    exiting_boundary_id: str


@dataclass(frozen=True)
class StoryboardDelivery:
    panels: tuple[StoryboardPanel, ...]
    source_projection_id: str
    manifest: ProjectionManifest
    adapter_version: str
    adaptation_records: tuple[CapabilityAdaptationRecord, ...] = ()


def _boundary_id(node: object, attribute_name: str) -> str:
    boundary = node_attribute(node, attribute_name, Mapping)
    value = boundary.get("boundary_id")
    if not isinstance(value, str) or not value:
        raise DomainValidationError(f"{attribute_name} must preserve boundary_id")
    return value


def render_storyboard(
    projection: StoryboardProjection,
    *,
    adapter_version: str = storyboard_adapter_version,
    profile: CapabilityProfile | None = None,
) -> StoryboardDelivery:
    """Format selected nodes without inventing IDs, events, time, or bindings."""

    if type(projection) is not StoryboardProjection:
        raise DomainValidationError("projection must be a StoryboardProjection")
    if adapter_version != projection.manifest.adapter_version:
        raise DomainValidationError(
            "adapter_version must match the ProjectionManifest; re-derive the adapter view"
        )
    if profile is not None and (
        projection.manifest.capability_profile_digest
        != capability_profile_digest(profile)
    ):
        raise DomainValidationError(
            "delivery CapabilityProfile digest must match the ProjectionManifest"
        )

    panels = tuple(
        StoryboardPanel(
            panel_id=node.node_id,
            source_node_id=node.node_id,
            beat_id=node.source_beat_id,
            shot_id=node.source_shot_id,
            phase=node_attribute(node, "phase", str),
            start_tick=node.interval.start_tick,
            end_tick=node.interval.end_tick,
            start_state_id=node.start_state_id,
            end_state_id=node.end_state_id,
            subject_state=node_attribute(node, "subject_state", str),
            attention=node_attribute(node, "attention", str),
            decision_ids=node.decision_ids,
            reference_requirement_ids=node_attribute(
                node, "node_reference_requirement_ids", tuple
            ),
            audio_event_ids=node_attribute(node, "node_audio_event_ids", tuple),
            entering_boundary_id=_boundary_id(node, "entering_boundary"),
            exiting_boundary_id=_boundary_id(node, "exiting_boundary"),
        )
        for node in projection.nodes
    )

    records: tuple[CapabilityAdaptationRecord, ...] = ()
    if profile is not None:
        reference_ids = {
            item_id
            for node in projection.nodes
            for item_id in node_attribute(
                node, "node_reference_requirement_ids", tuple
            )
        }
        if len(reference_ids) > profile.reference_slots:
            affected = tuple(
                node.node_id
                for node in projection.nodes
                if node_attribute(node, "node_reference_requirement_ids", tuple)
            )
            records = (
                adaptation_record(
                    profile=profile,
                    adapter_version=adapter_version,
                    adaptation_code="REFERENCE_SLOT_BUDGET_EXCEEDED",
                    source_node_ids=affected,
                    semantic_loss=True,
                ),
            )

    return StoryboardDelivery(
        panels=panels,
        source_projection_id=projection.ast.projection_id,
        manifest=projection.manifest,
        adapter_version=adapter_version,
        adaptation_records=records,
    )


__all__ = [
    "StoryboardDelivery",
    "StoryboardPanel",
    "render_storyboard",
    "storyboard_adapter_version",
]
