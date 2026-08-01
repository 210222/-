"""No-op media verifier — fails closed without a real verifier.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.4 / §14 A7.

Verification is impossible without a real media stack, so the no-op verifier
raises instead of returning fabricated frame evidence.
"""

from __future__ import annotations

from mode_p_vnext.domain.evidence import (
    FrameEvidence,
    FrameEvidencePlan,
    MediaRunRecord,
)
from mode_p_vnext.ports.media_verifier import (
    MediaVerificationUnavailableError,
    MediaVerifierPort,
)


class NoopMediaVerifier:
    """Fail-closed verifier: never fabricates FrameEvidence."""

    def verify(
        self, plan: FrameEvidencePlan, media_run: MediaRunRecord
    ) -> tuple[FrameEvidence, ...]:
        raise MediaVerificationUnavailableError(
            "no real media verifier is configured; frame evidence is unavailable"
        )


assert issubclass(NoopMediaVerifier, MediaVerifierPort)
