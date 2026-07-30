"""Deterministic local artifact identities."""

from __future__ import annotations

from dataclasses import dataclass

from .artifact import ArtifactKind, DomainValidationError, require_sha256


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("IdFactory",)


@dataclass(frozen=True)
class IdFactory:
    program_version: str

    def __post_init__(self) -> None:
        if not self.program_version.strip():
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
        if not episode_id.strip() or not stage.strip():
            raise DomainValidationError("episode_id and stage must be non-empty")
        if scene_id is not None and not scene_id.strip():
            raise DomainValidationError("scene_id must be non-empty when supplied")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
            raise DomainValidationError("ordinal must be a non-negative integer")
        require_sha256(input_digest, "input_digest")
        scope = scene_id or "episode"
        return ":".join((artifact_kind.value, episode_id, scope, stage, f"{ordinal:04d}", input_digest[:20]))
