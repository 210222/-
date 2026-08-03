"""Fail-closed A7 renderer adapter; no external media is started.

Architecture authority: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.1 §3.4, §7.2,
§9, and §11 A7.
"""

from __future__ import annotations

from mode_p_vnext.ports.media_renderer import (
    MediaRenderOutput,
    MediaRenderRequest,
    MediaRendererPort,
    MediaRendererUnavailableError,
)


class NoopMediaRenderer:
    """Never fabricates even a provider output Draft."""

    def render(self, request: MediaRenderRequest) -> MediaRenderOutput:
        raise MediaRendererUnavailableError(
            "no real media renderer is configured; "
            "visual evidence is unavailable and nothing may claim it"
        )


assert issubclass(NoopMediaRenderer, MediaRendererPort)
