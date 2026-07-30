"""Release-gate data only; mutation remains in release_control."""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .artifact import DomainValidationError, SourceRef


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("ReleaseGateRecord", "ReleasePhase")


class ReleasePhase(str, enum.Enum):
    ARCHITECTURE_MIGRATION_REQUIRED = "ARCHITECTURE_MIGRATION_REQUIRED"
    SHADOW_READY = "SHADOW_READY"
    MEDIA_EVIDENCE_REQUIRED = "MEDIA_EVIDENCE_REQUIRED"
    OWNER_APPROVAL_REQUIRED = "OWNER_APPROVAL_REQUIRED"
    PRODUCTION_SWITCH_PROPOSED = "PRODUCTION_SWITCH_PROPOSED"


@dataclass(frozen=True)
class ReleaseGateRecord:
    gate_name: str
    phase: ReleasePhase
    evidence_ref: SourceRef
    accepted: bool

    def __post_init__(self) -> None:
        if not self.gate_name.strip() or not isinstance(self.phase, ReleasePhase):
            raise DomainValidationError("ReleaseGateRecord requires gate_name and ReleasePhase")
        if not isinstance(self.evidence_ref, SourceRef):
            raise DomainValidationError("evidence_ref must be a SourceRef")
