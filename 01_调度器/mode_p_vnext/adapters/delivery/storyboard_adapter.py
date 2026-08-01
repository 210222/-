"""Storyboard delivery adapter — formats the storyboard projection only.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §10 / §14 A6.

The adapter re-emits the projection's selected beat nodes as ordered panels.
It never invents events: every panel is a direct projection of one AST beat
node with its shared beat/shot/tick/state/decision references.  If a
capability profile is supplied and the reference budget is exceeded, an
explicit CapabilityAdaptationRecord is emitted instead of silently dropping
content.
"""

from __future__ import annotations

from dataclasses import dataclass

from mode_p_vnext.adapters.delivery.capability import (
    CapabilityAdaptationRecord,
    CapabilityProfile,
)
from mode_p_vnext.services.projection_compiler import (
    ProjectionNode,
    StoryboardProjection,
)

storyboard_adapter_version = "storyboard-adapter-v2.1.0"


@dataclass(frozen=True)
class StoryboardPanel:
    """One storyboard panel — a direct view of one AST beat node."""

    panel_id: str
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


@dataclass(frozen=True)
class StoryboardDelivery:
    """Formatted storyboard output plus explicit adaptation records."""

    panels: tuple[StoryboardPanel, ...]
    adapter_version: str
    adaptation_records: tuple[CapabilityAdaptationRecord, ...] = ()


def render_storyboard(
    projection: StoryboardProjection,
    *,
    adapter_version: str = storyboard_adapter_version,
    profile: CapabilityProfile | None = None,
    reference_requirement_count: int = 0,
) -> StoryboardDelivery:
    """Format the storyboard projection into panels.

    Pure function: identical inputs produce identical output; no Director
    invocation, no side effects.  Adapter-only changes never alter the
    projection nodes themselves.  ``reference_requirement_count`` is the
    number of AST reference requirements this storyboard depends on (the
    caller supplies the AST count; the adapter never derives new content).
    """
    panels = tuple(
        StoryboardPanel(
            panel_id=node.node_id,
            beat_id=node.beat_id,
            shot_id=node.shot_id,
            phase=node.phase,
            start_tick=node.start_tick,
            end_tick=node.end_tick,
            start_state_id=node.start_state_id,
            end_state_id=node.end_state_id,
            subject_state=node.subject_state,
            attention=node.attention,
            decision_ids=node.decision_ids,
        )
        for node in projection.nodes
    )

    records: list[CapabilityAdaptationRecord] = []
    if profile is not None and reference_requirement_count > profile.reference_slots:
        records.append(
            CapabilityAdaptationRecord(
                node_id="",
                capability="reference_slots",
                action="flag_reference_budget_exceeded",
                reason=(
                    f"storyboard references {reference_requirement_count} requirements "
                    f"but the platform supports {profile.reference_slots}"
                ),
                adapter_version=adapter_version,
            )
        )

    return StoryboardDelivery(
        panels=panels,
        adapter_version=adapter_version,
        adaptation_records=tuple(records),
    )
