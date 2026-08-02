"""Pure v3 delivery adapters over one canonical ProjectionAST authority."""

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
    VideoPromptChunk,
    render_video,
    video_adapter_version,
)

__all__ = [
    "CapabilityAdaptationRecord",
    "CapabilityProfile",
    "StoryboardDelivery",
    "StoryboardPanel",
    "VideoDelivery",
    "VideoPromptChunk",
    "capability_profile_digest",
    "render_storyboard",
    "render_video",
    "storyboard_adapter_version",
    "video_adapter_version",
]
