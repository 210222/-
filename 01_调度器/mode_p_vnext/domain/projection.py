"""The single ProjectionAST shared by storyboard and video adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from .artifact import (
    ArtifactKind,
    DomainValidationError,
    freeze_mapping,
    require_sha256,
)
from .time import TickRange


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = (
    "CapabilityAdaptationRecord",
    "ProjectionAST",
    "ProjectionManifest",
    "ProjectionNode",
)


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")


def _text_tuple(
    value: tuple[str, ...], field_name: str, *, require_items: bool
) -> tuple[str, ...]:
    values = tuple(value)
    if (require_items and not values) or any(
        not isinstance(item, str) or not item.strip() for item in values
    ):
        raise DomainValidationError(
            f"{field_name} must contain only non-empty text"
        )
    if len(values) != len(set(values)):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    return values


@dataclass(frozen=True)
class ProjectionNode:
    node_id: str
    source_beat_id: str
    source_shot_id: str
    interval: TickRange
    start_state_id: str
    end_state_id: str
    decision_ids: tuple[str, ...]
    attributes: Mapping[str, Any]
    children: tuple["ProjectionNode", ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "node_id",
            "source_beat_id",
            "source_shot_id",
            "start_state_id",
            "end_state_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        if (
            not isinstance(self.interval, TickRange)
            or self.interval.duration_ticks <= 0
        ):
            raise DomainValidationError(
                "ProjectionNode interval must be a positive TickRange"
            )
        object.__setattr__(
            self,
            "decision_ids",
            _text_tuple(
                self.decision_ids, "decision_ids", require_items=False
            ),
        )
        object.__setattr__(
            self, "attributes", freeze_mapping(self.attributes, "attributes")
        )
        children = tuple(self.children)
        if not all(isinstance(child, ProjectionNode) for child in children):
            raise DomainValidationError(
                "children must contain ProjectionNode values"
            )
        object.__setattr__(self, "children", children)


@dataclass(frozen=True)
class ProjectionAST:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.PROJECTION_AST

    projection_id: str
    source_vec_artifact_id: str
    nodes: tuple[ProjectionNode, ...]

    def __post_init__(self) -> None:
        _require_text(self.projection_id, "projection_id")
        _require_text(self.source_vec_artifact_id, "source_vec_artifact_id")
        nodes = tuple(self.nodes)
        if not nodes or not all(isinstance(node, ProjectionNode) for node in nodes):
            raise DomainValidationError(
                "nodes must contain ProjectionNode values"
            )
        identifiers = tuple(
            node.node_id for root in nodes for node in _walk(root)
        )
        if len(identifiers) != len(set(identifiers)):
            raise DomainValidationError("ProjectionNode IDs must be unique")
        object.__setattr__(self, "nodes", nodes)


def _walk(node: ProjectionNode) -> tuple[ProjectionNode, ...]:
    descendants: list[ProjectionNode] = [node]
    for child in node.children:
        descendants.extend(_walk(child))
    return tuple(descendants)


@dataclass(frozen=True)
class ProjectionManifest:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.PROJECTION_MANIFEST

    vec_digest: str
    projection_ast_digest: str
    source_node_ids: tuple[str, ...]
    compiler_version: str
    adapter_version: str
    capability_profile_digest: str
    reference_binding_digest: str
    audio_binding_digest: str

    def __post_init__(self) -> None:
        for field_name in (
            "vec_digest",
            "projection_ast_digest",
            "capability_profile_digest",
            "reference_binding_digest",
            "audio_binding_digest",
        ):
            require_sha256(getattr(self, field_name), field_name)
        _require_text(self.compiler_version, "compiler_version")
        _require_text(self.adapter_version, "adapter_version")
        object.__setattr__(
            self,
            "source_node_ids",
            _text_tuple(
                self.source_node_ids, "source_node_ids", require_items=True
            ),
        )


@dataclass(frozen=True)
class CapabilityAdaptationRecord:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = (
        ArtifactKind.CAPABILITY_ADAPTATION
    )

    adapter_version: str
    capability_profile_digest: str
    adaptation_code: str
    source_node_ids: tuple[str, ...]
    semantic_loss: bool

    def __post_init__(self) -> None:
        _require_text(self.adapter_version, "adapter_version")
        _require_text(self.adaptation_code, "adaptation_code")
        require_sha256(
            self.capability_profile_digest, "capability_profile_digest"
        )
        object.__setattr__(
            self,
            "source_node_ids",
            _text_tuple(
                self.source_node_ids, "source_node_ids", require_items=True
            ),
        )
        if not isinstance(self.semantic_loss, bool):
            raise DomainValidationError("semantic_loss must be boolean")
