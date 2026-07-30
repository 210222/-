"""Deterministic local artifact identities."""

from __future__ import annotations

from dataclasses import dataclass

from .artifact import ArtifactKind, DomainValidationError, canonical_sha256, require_sha256


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("IdFactory",)


@dataclass(frozen=True)
class IdFactory:
    program_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.program_version, str) or not self.program_version.strip():
            raise DomainValidationError("program_version must be non-empty")

    def create(
        self,
        *,
        artifact_kind: ArtifactKind,
        episode_id: str,
        scene_id: str | None,
        stage: str,
        input_digest: str,
        ordinal: int,
    ) -> str:
        if not isinstance(artifact_kind, ArtifactKind):
            raise DomainValidationError("artifact_kind must be an ArtifactKind")
        if (
            not isinstance(episode_id, str)
            or not episode_id.strip()
            or not isinstance(stage, str)
            or not stage.strip()
        ):
            raise DomainValidationError("episode_id and stage must be non-empty")
        if scene_id is not None and (
            not isinstance(scene_id, str) or not scene_id.strip()
        ):
            raise DomainValidationError("scene_id must be non-empty when supplied")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
            raise DomainValidationError("ordinal must be a non-negative integer")
        require_sha256(input_digest, "input_digest")
        identity_digest = canonical_sha256(
            {
                "artifact_kind": artifact_kind,
                "program_version": self.program_version,
                "episode_id": episode_id,
                "scene_id": scene_id,
                "stage": stage,
                "input_digest": input_digest,
                "ordinal": ordinal,
            }
        )
        return f"{artifact_kind.value}:{ordinal:04d}:{identity_digest}"
