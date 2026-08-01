"""Media renderer port — the boundary between text and visual evidence.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.4 / §14 A7.

Only a real media renderer can produce a MediaRunRecord.  Text-only pipelines
sit behind this port and can never fabricate visual evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

from mode_p_vnext.domain.artifact import DomainValidationError
from mode_p_vnext.pipeline.verification_nodes import MediaRunRecord


@dataclass(frozen=True)
class MediaRenderRequest:
    """Render one scene's projection into real media."""

    scene_id: str
    projection_ast_digest: str
    settings: Mapping[str, str]

    def __post_init__(self) -> None:
        if not isinstance(self.scene_id, str) or not self.scene_id:
            raise DomainValidationError("scene_id must be non-empty")
        if not isinstance(self.projection_ast_digest, str) or len(self.projection_ast_digest) != 64:
            raise DomainValidationError("projection_ast_digest must be a sha256")


class MediaRendererUnavailableError(RuntimeError):
    """No real media renderer is configured; visual evidence is unavailable."""


@runtime_checkable
class MediaRendererPort(Protocol):
    """Render a MediaRunRecord from a projection; fails closed when absent."""

    def render(self, request: MediaRenderRequest) -> MediaRunRecord:
        """Render real media for the request.

        Raises MediaRendererUnavailableError when no real renderer exists —
        callers must treat that as "no visual evidence", never as a pass.
        """
        ...
