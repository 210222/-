"""Read-only adapters from retained legacy artifacts into canonical vNext data."""

from .legacy_checkpoint import LegacyCheckpointObservation, read_legacy_b0_k2_checkpoint
from .legacy_facts import LegacyFactObservation, read_legacy_script_fact
from .retired_authority import (
    LegacyAuthorityObservation,
    RetiredAuthorityError,
    observe_legacy_payload,
    reject_legacy_construction,
)

__all__ = (
    "LegacyCheckpointObservation",
    "LegacyFactObservation",
    "LegacyAuthorityObservation",
    "RetiredAuthorityError",
    "observe_legacy_payload",
    "read_legacy_b0_k2_checkpoint",
    "read_legacy_script_fact",
    "reject_legacy_construction",
)
