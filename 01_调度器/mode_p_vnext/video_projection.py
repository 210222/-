"""MODE:P vNext — Video Prompt Projection (V5.3 R1.3+).

Uses the shared ContractBuilder to derive timeline nodes from every segment.
Both direct `project_video_prompt(segment)` and builder-supplied paths
produce the same shot-bound timeline.

Spec references: LOOP §11.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from mode_p_vnext.schema.generation_segment import GenerationSegment
from mode_p_vnext.storyboard_projection import (
    ContractBuilder,
    DualOutputContract,
    build_contract_from_segment,
    _format_time_display,
)


# ============================================================================
# VideoPromptView
# ============================================================================

@dataclass
class VideoPromptView:
    """Video-prompt view with legacy fields and the immutable contract."""
    segment_id: str
    reference_images: List[str] = field(default_factory=list)
    shot_descriptions: List[Dict[str, Any]] = field(default_factory=list)
    audio_track: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)
    narrative_summary: str = ""
    contract: DualOutputContract = field(default_factory=DualOutputContract)


# ============================================================================
# Projection
# ============================================================================

def project_video_prompt(
    segment: GenerationSegment,
    storyboard_refs: List[str] | None = None,
    audio_refs: List[str] | None = None,
    forbidden_items: List[str] | None = None,
    ticks_per_second: int = 24000,
    builder: ContractBuilder | None = None,
) -> VideoPromptView:
    """Project a segment into a video prompt view.

    Always populates contract.nodes from the segment via the shared builder.
    Both direct and builder-supplied paths produce the same timeline.
    """
    if builder is None:
        builder = build_contract_from_segment(segment, ticks_per_second)

    # Merge external args into builder
    if storyboard_refs:
        existing = set(builder._ref_images) if hasattr(builder, '_ref_images') else set()
        for r in storyboard_refs:
            if r not in existing:
                builder.add_reference_image(r)
    if audio_refs:
        for a in audio_refs:
            builder.add_audio(a)
    if forbidden_items:
        for f in forbidden_items:
            builder.add_prohibition(f)

    contract = builder.build()

    # Legacy flat shot_descriptions (backward-compatible)
    shots: List[Dict[str, Any]] = []
    for shot in segment.shots:
        shots.append({
            "shot_id": shot.shot_id,
            "start_tick": shot.time_range.start_tick,
            "end_tick": shot.time_range.end_tick,
            "start_s": round(shot.time_range.start_tick / ticks_per_second, 3),
            "end_s": round(shot.time_range.end_tick / ticks_per_second, 3),
            "duration_s": round(shot.time_range.duration_ticks / ticks_per_second, 3),
            "shot_size": shot.shot_size,
            "camera_motion": shot.camera_motion,
            "composition": shot.composition,
            "lighting": shot.lighting,
            "performance": shot.performance,
        })

    transitions: List[str] = []
    if contract.transition_description:
        transitions.append(contract.transition_description)
    if contract.handoff:
        transitions.append(contract.handoff)

    return VideoPromptView(
        segment_id=segment.segment_id,
        reference_images=list(contract.reference_images),
        shot_descriptions=shots,
        audio_track=list(contract.audio_track),
        forbidden=list(contract.prohibitions),
        transitions=transitions,
        narrative_summary=segment.narrative_summary,
        contract=contract,
    )
