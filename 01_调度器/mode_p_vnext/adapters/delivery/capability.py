"""Delivery capability profiles and canonical adaptation records.

CapabilityAdaptationRecord is owned exclusively by
``mode_p_vnext.domain.projection``.  Delivery adapters construct that exact
type so every downgrade is hashable and traceable to canonical AST nodes.
"""

from __future__ import annotations

from dataclasses import dataclass

from mode_p_vnext.domain.artifact import DomainValidationError, canonical_sha256
from mode_p_vnext.domain.projection import CapabilityAdaptationRecord


@dataclass(frozen=True)
class CapabilityProfile:
    """Verified delivery-platform snapshot used only by pure adapters."""

    platform: str
    version: str
    max_prompt_chars: int
    reference_slots: int
    internal_cuts_supported: bool

    def __post_init__(self) -> None:
        if not isinstance(self.platform, str) or not self.platform.strip():
            raise DomainValidationError("platform must be non-empty")
        if not isinstance(self.version, str) or not self.version.strip():
            raise DomainValidationError("version must be non-empty")
        if (
            isinstance(self.max_prompt_chars, bool)
            or not isinstance(self.max_prompt_chars, int)
            or self.max_prompt_chars < 1
        ):
            raise DomainValidationError("max_prompt_chars must be a positive integer")
        if (
            isinstance(self.reference_slots, bool)
            or not isinstance(self.reference_slots, int)
            or self.reference_slots < 0
        ):
            raise DomainValidationError("reference_slots must be non-negative")
        if not isinstance(self.internal_cuts_supported, bool):
            raise DomainValidationError("internal_cuts_supported must be boolean")


def capability_profile_digest(profile: CapabilityProfile) -> str:
    if type(profile) is not CapabilityProfile:
        raise DomainValidationError("profile must be a CapabilityProfile")
    return canonical_sha256(profile)


def adaptation_record(
    *,
    profile: CapabilityProfile,
    adapter_version: str,
    adaptation_code: str,
    source_node_ids: tuple[str, ...],
    semantic_loss: bool,
) -> CapabilityAdaptationRecord:
    """Construct the one canonical adaptation artifact payload type."""

    return CapabilityAdaptationRecord(
        adapter_version=adapter_version,
        capability_profile_digest=capability_profile_digest(profile),
        adaptation_code=adaptation_code,
        source_node_ids=source_node_ids,
        semantic_loss=semantic_loss,
    )


__all__ = [
    "CapabilityAdaptationRecord",
    "CapabilityProfile",
    "adaptation_record",
    "capability_profile_digest",
]
