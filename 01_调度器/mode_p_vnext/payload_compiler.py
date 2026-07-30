"""MODE:P vNext — Render Payload Compiler (V5.6).

Compiles the actual forward payload from allowed fields. Excludes:
- narrative_only (story-layer only, not visible)
- audio_only (belongs in audio track, not visual payload)
- human_qa_only (human QA checklist, never sent to model)
- token_leakage_risk content (unsafe for model prompt)

Spec references: LOOP §9 Step 13, §11.7.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from mode_p_vnext.schema.visibility_contract import VisibilityContract
from mode_p_vnext.video_projection import VideoPromptView


_EXCLUDED_VISIBILITY = frozenset({
    "narrative_only",
    "audio_only",
    "human_qa_only",
    "token_leakage_risk",
})


@dataclass
class RenderPayload:
    """The actual payload submitted to the target model.

    Contains only fields that are safe and relevant for model generation.
    """
    segment_id: str
    fields: Dict[str, Any] = field(default_factory=dict)
    excluded_fields: List[str] = field(default_factory=list)


def compile_render_payload(
    view: VideoPromptView,
    contract: VisibilityContract,
) -> RenderPayload:
    """Compile a render payload from a video prompt view and visibility contract.

    Excludes narrative_only, audio_only, human_qa_only, and token_leakage_risk
    content from the forward payload.
    """
    payload = RenderPayload(segment_id=view.segment_id)

    # Whitelist: visible items go into the payload
    payload.fields["visible_whitelist"] = list(contract.visible_whitelist)

    # Positive closure (safe physical descriptions)
    if contract.positive_closure:
        payload.fields["positive_closure"] = list(contract.positive_closure)

    # Shot descriptions
    payload.fields["shots"] = view.shot_descriptions

    # Reference images
    if view.reference_images:
        payload.fields["reference_images"] = list(view.reference_images)

    # Forbidden + negative_route handling
    if contract.negative_route == "separate_channel" and contract.forbidden_qa:
        payload.fields["negative_prompt"] = list(contract.forbidden_qa)
    elif contract.negative_route == "inline":
        # forbidden_qa was added as negative_prompt in the adapter
        pass   # handled by adapter, not payload

    # Audio — belongs in separate track, not visual payload
    if view.audio_track:
        # audio goes to audio channel, not visual payload
        payload.excluded_fields.append("audio_track (routed to audio channel)")

    # Mark what was excluded
    if contract.narrative_only:
        payload.excluded_fields.append(
            f"narrative_only: {contract.narrative_only}"
        )
    if contract.audio_only:
        payload.excluded_fields.append(
            f"audio_only: {contract.audio_only}"
        )

    return payload
