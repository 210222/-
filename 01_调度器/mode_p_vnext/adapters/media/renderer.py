"""No-op media renderer — fails closed when no real renderer is configured.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.4 / §14 A7.

Raising MediaRendererUnavailableError is the only honest behavior without a
real media stack: callers must treat it as "no visual evidence available".
"""

from __future__ import annotations

from mode_p_vnext.domain.evidence import MediaRunRecord
from mode_p_vnext.ports.media_renderer import (
    MediaRenderRequest,
    MediaRendererPort,
    MediaRendererUnavailableError,
)


class NoopMediaRenderer:
    """Fail-closed renderer: never fabricates a MediaRunRecord."""

    def render(self, request: MediaRenderRequest) -> MediaRunRecord:
        raise MediaRendererUnavailableError(
            "no real media renderer is configured; "
            "visual evidence is unavailable and nothing may claim it"
        )


assert issubclass(NoopMediaRenderer, MediaRendererPort)
