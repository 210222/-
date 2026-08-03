"""Fail-closed A7 verifier adapter; no external media is inspected.

Architecture authority: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.1 §3.4, §7.2,
§9, and §11 A7.
"""

from __future__ import annotations

from mode_p_vnext.domain.evidence import FrameEvidencePlan, MediaRunRecord
from mode_p_vnext.ports.media_verifier import (
    MediaVerificationOutput,
    MediaVerificationUnavailableError,
    MediaVerifierPort,
)


class NoopMediaVerifier:
    """Never fabricates a media verification Draft."""

    def verify(
        self, plan: FrameEvidencePlan, media_run: MediaRunRecord
    ) -> MediaVerificationOutput:
        raise MediaVerificationUnavailableError(
            "no real media verifier is configured; frame evidence is unavailable"
        )


assert issubclass(NoopMediaVerifier, MediaVerifierPort)
