"""Media verifier port — turns a media run into frame-level evidence.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.4 / §14 A7.

A verifier consumes a canonical MediaRunRecord and FrameEvidencePlan and
returns FrameEvidence entries bound to media output refs.  Without a verifier
the pipeline fails closed: no frame evidence, no VISUAL_EVIDENCED.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mode_p_vnext.domain.evidence import (
    FrameEvidence,
    FrameEvidencePlan,
    MediaRunRecord,
)


class MediaVerificationUnavailableError(RuntimeError):
    """No media verifier is configured; frame evidence is unavailable."""


@runtime_checkable
class MediaVerifierPort(Protocol):
    """Verify captured media against a frame plan."""

    def verify(
        self, plan: FrameEvidencePlan, media_run: MediaRunRecord
    ) -> tuple[FrameEvidence, ...]:
        """Return verified frame evidence; raise when verification is impossible."""
        ...
