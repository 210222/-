"""Release-gate data only; mutation remains in release_control."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import ClassVar

from .artifact import ArtifactKind, DomainValidationError, SourceRef


DOMAIN_SCHEMA_VERSION = "2.2"
CANONICAL_DOMAIN_TYPES = ("ReleaseGateRecord", "ReleasePhase")


class ReleasePhase(str, enum.Enum):
    BASELINE_REPAIR_REQUIRED = "BASELINE_REPAIR_REQUIRED"
    ARCHITECTURE_MIGRATION_REQUIRED = "ARCHITECTURE_MIGRATION_REQUIRED"
    TEXT_SHADOW_REQUIRED = "TEXT_SHADOW_REQUIRED"
    HOLDOUT_EVALUATION_REQUIRED = "HOLDOUT_EVALUATION_REQUIRED"
    MEDIA_EVIDENCE_REQUIRED = "MEDIA_EVIDENCE_REQUIRED"
    OWNER_APPROVAL_REQUIRED = "OWNER_APPROVAL_REQUIRED"
    PRODUCTION_SWITCH_PROPOSAL_ELIGIBLE = (
        "PRODUCTION_SWITCH_PROPOSAL_ELIGIBLE"
    )


@dataclass(frozen=True)
class ReleaseGateRecord:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.RELEASE_DECISION

    gate_name: str
    phase: ReleasePhase
    evidence_ref: SourceRef
    accepted: bool

    def __post_init__(self) -> None:
        if (
            not isinstance(self.gate_name, str)
            or not self.gate_name.strip()
            or not isinstance(self.phase, ReleasePhase)
        ):
            raise DomainValidationError("ReleaseGateRecord requires gate_name and ReleasePhase")
        if not isinstance(self.evidence_ref, SourceRef):
            raise DomainValidationError("evidence_ref must be a SourceRef")
        if not isinstance(self.accepted, bool):
            raise DomainValidationError("accepted must be boolean")
