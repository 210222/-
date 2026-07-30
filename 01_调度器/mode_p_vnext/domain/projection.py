"""A single projection AST for storyboard and video-prompt renderers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .artifact import DomainValidationError, freeze_mapping


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("ProjectionAST", "ProjectionNode")


@dataclass(frozen=True)
class ProjectionNode:
    node_kind: str
    source_shot_id: str
    attributes: Mapping[str, Any]
    children: tuple["ProjectionNode", ...] = ()

    def __post_init__(self) -> None:
        if not self.node_kind.strip() or not self.source_shot_id.strip():
            raise DomainValidationError("node_kind and source_shot_id must be non-empty")
        object.__setattr__(self, "attributes", freeze_mapping(self.attributes, "attributes"))
        children = tuple(self.children)
        if not all(isinstance(child, ProjectionNode) for child in children):
            raise DomainValidationError("children must contain ProjectionNode values")
        object.__setattr__(self, "children", children)


@dataclass(frozen=True)
class ProjectionAST:
    projection_id: str
    source_vec_artifact_id: str
    nodes: tuple[ProjectionNode, ...]

    def __post_init__(self) -> None:
        if not self.projection_id.strip() or not self.source_vec_artifact_id.strip():
            raise DomainValidationError("projection_id and source_vec_artifact_id must be non-empty")
        nodes = tuple(self.nodes)
        if not nodes or not all(isinstance(node, ProjectionNode) for node in nodes):
            raise DomainValidationError("nodes must contain ProjectionNode values")
        object.__setattr__(self, "nodes", nodes)
