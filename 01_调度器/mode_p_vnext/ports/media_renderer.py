"""A7 media renderer port; no external renderer is activated in this package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    SourceRef,
    freeze_mapping,
    require_sha256,
)


@dataclass(frozen=True)
class MediaRenderRequest:
    """Canonical-input request DTO bound to the sole ProjectionAST."""

    scene_id: str
    projection_artifact_id: str
    projection_ast_digest: str
    projection_manifest_digest: str
    capability_profile_digest: str
    settings: Mapping[str, str]

    def __post_init__(self) -> None:
        for field_name in ("scene_id", "projection_artifact_id"):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name).strip():
                raise DomainValidationError(f"{field_name} must be non-empty")
        for field_name in (
            "projection_ast_digest",
            "projection_manifest_digest",
            "capability_profile_digest",
        ):
            require_sha256(getattr(self, field_name), field_name)
        settings = freeze_mapping(self.settings, "settings")
        if any(not isinstance(value, str) for value in settings.values()):
            raise DomainValidationError("render settings must contain text values")
        object.__setattr__(self, "settings", settings)


@dataclass(frozen=True)
class MediaRenderOutput:
    """External Draft only; local code later creates the MediaRunRecord ID."""

    provider: str
    output_refs: tuple[SourceRef, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise DomainValidationError("provider must be non-empty")
        refs = tuple(self.output_refs)
        if not refs or not all(isinstance(item, SourceRef) for item in refs):
            raise DomainValidationError("output_refs must contain SourceRef values")
        object.__setattr__(self, "output_refs", refs)


class MediaRendererUnavailableError(RuntimeError):
    """No renderer exists; callers must remain at TEXT_VALIDATED."""


@runtime_checkable
class MediaRendererPort(Protocol):
    def render(self, request: MediaRenderRequest) -> MediaRenderOutput:
        """Return a provider Draft, never a provider-owned canonical artifact."""
        ...


__all__ = [
    "MediaRenderOutput",
    "MediaRenderRequest",
    "MediaRendererPort",
    "MediaRendererUnavailableError",
]
