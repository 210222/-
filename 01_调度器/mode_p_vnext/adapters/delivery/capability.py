"""Capability profile and explicit adaptation records for delivery adapters.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §10 / §14 A6.

A CapabilityProfile is a verified platform snapshot.  The digest is bound into
every ProjectionManifest.  Adapters may degrade output to match the profile,
but every degradation must be recorded as a CapabilityAdaptationRecord — the
record is the audit trail that makes "adapter-only changes" distinguishable
from Director-level creative changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from mode_p_vnext.domain.artifact import DomainValidationError, canonical_sha256


@dataclass(frozen=True)
class CapabilityProfile:
    """Verified platform capability snapshot (frozen, hashable)."""

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
        if isinstance(self.max_prompt_chars, bool) or not isinstance(
            self.max_prompt_chars, int
        ) or self.max_prompt_chars < 1:
            raise DomainValidationError("max_prompt_chars must be a positive integer")
        if isinstance(self.reference_slots, bool) or not isinstance(
            self.reference_slots, int
        ) or self.reference_slots < 0:
            raise DomainValidationError("reference_slots must be a non-negative integer")
        if not isinstance(self.internal_cuts_supported, bool):
            raise DomainValidationError("internal_cuts_supported must be a bool")


@dataclass(frozen=True)
class CapabilityAdaptationRecord:
    """One explicit capability degradation applied by an adapter.

    node_id names the projection node the degradation applies to ("" when the
    record covers the whole delivery).  ``capability`` names the profile
    dimension, ``action`` describes what the adapter did (e.g. segment_per_shot,
    chunked, flag_reference_budget_exceeded), and ``reason`` states why.
    """

    node_id: str
    capability: str
    action: str
    reason: str
    adapter_version: str


def capability_profile_digest(profile: CapabilityProfile) -> str:
    """Deterministic digest of a capability profile for manifest binding."""
    return canonical_sha256(profile)
