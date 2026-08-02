"""A7 real-media verifier port; absent implementations fail closed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from mode_p_vnext.domain.artifact import DomainValidationError
from mode_p_vnext.domain.evidence import (
    FrameEvidence,
    FrameEvidencePlan,
    MediaRunRecord,
    OutcomeAttribution,
)


@dataclass(frozen=True)
class MediaVerificationOutput:
    """Verifier Draft; local code binds it to canonical evidence and IDs."""

    passed: bool
    frames: tuple[FrameEvidence, ...]
    attributions: tuple[OutcomeAttribution, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.passed, bool):
            raise DomainValidationError("passed must be boolean")
        frames = tuple(self.frames)
        attributions = tuple(self.attributions)
        if not frames or not all(isinstance(item, FrameEvidence) for item in frames):
            raise DomainValidationError("frames must contain FrameEvidence")
        if not all(isinstance(item, OutcomeAttribution) for item in attributions):
            raise DomainValidationError("attributions must contain OutcomeAttribution")
        if not self.passed and not attributions:
            raise DomainValidationError("failed verification requires outcome attribution")
        object.__setattr__(self, "frames", frames)
        object.__setattr__(self, "attributions", attributions)


class MediaVerificationUnavailableError(RuntimeError):
    """No verifier exists; frame evidence cannot be produced."""


@runtime_checkable
class MediaVerifierPort(Protocol):
    def verify(
        self, plan: FrameEvidencePlan, media_run: MediaRunRecord
    ) -> MediaVerificationOutput:
        ...


__all__ = [
    "MediaVerificationOutput",
    "MediaVerificationUnavailableError",
    "MediaVerifierPort",
]
