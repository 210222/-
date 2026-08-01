"""Delivery adapters for MODE:P vNext projections.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §10 / §14 A6.

Adapters may only format a projection or perform explicit capability
degradation.  Every degradation is recorded as a CapabilityAdaptationRecord;
adapters never invent events, and adapter-only recompiles never invoke the
Director (the render functions are pure).
"""

from mode_p_vnext.adapters.delivery.capability import (
    CapabilityAdaptationRecord,
    CapabilityProfile,
    capability_profile_digest,
)
from mode_p_vnext.adapters.delivery.storyboard_adapter import (
    StoryboardDelivery,
    StoryboardPanel,
    render_storyboard,
    storyboard_adapter_version,
)
from mode_p_vnext.adapters.delivery.video_adapter import (
    VideoDelivery,
    render_video,
    video_adapter_version,
)

__all__ = [
    "CapabilityAdaptationRecord",
    "CapabilityProfile",
    "StoryboardDelivery",
    "StoryboardPanel",
    "VideoDelivery",
    "capability_profile_digest",
    "render_storyboard",
    "render_video",
    "storyboard_adapter_version",
    "video_adapter_version",
]
