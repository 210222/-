"""Immutable canonical state for the vNext persistent node graph."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import ArtifactKind, DomainValidationError, require_sha256


class StateInvariantError(ValueError):
    """Raised when a node violates canonical graph-state ownership."""


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StateInvariantError(f"{field_name} must be a non-empty string")
    return value


def _freeze_digests(value: Mapping[str, str], field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise StateInvariantError(f"{field_name} must be a mapping")
    frozen: dict[str, str] = {}
    for key, digest in value.items():
        _text(str(key), f"{field_name} key")
        try:
            require_sha256(digest, f"{field_name}[{key}]")
        except DomainValidationError as exc:
            raise StateInvariantError(str(exc)) from exc
        frozen[str(key)] = digest
    return MappingProxyType(frozen)


@dataclass(frozen=True)
class ArtifactRef:
    """A persisted ArtifactEnvelope reference, never an in-process payload."""

    artifact_id: str
    artifact_kind: ArtifactKind
    content_sha256: str
    schema_version: str

    def __post_init__(self) -> None:
        _text(self.artifact_id, "artifact_id")
        if not isinstance(self.artifact_kind, ArtifactKind):
            raise StateInvariantError("artifact_kind must be an ArtifactKind")
        try:
            require_sha256(self.content_sha256, "content_sha256")
        except DomainValidationError as exc:
            raise StateInvariantError(str(exc)) from exc
        _text(self.schema_version, "schema_version")

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_kind": self.artifact_kind.value,
            "content_sha256": self.content_sha256,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ArtifactRef":
        if not isinstance(value, Mapping):
            raise StateInvariantError("ArtifactRef must be an object")
        try:
            return cls(
                artifact_id=str(value["artifact_id"]),
                artifact_kind=ArtifactKind(str(value["artifact_kind"])),
                content_sha256=str(value["content_sha256"]),
                schema_version=str(value["schema_version"]),
            )
        except (KeyError, ValueError) as exc:
            raise StateInvariantError("invalid ArtifactRef") from exc


@dataclass(frozen=True)
class NodeAcceptance:
    """The accepted output and input-digest edge set of one graph node."""

    node_id: str
    node_version: str
    output_digests: Mapping[str, str]
    dependency_digests: Mapping[str, str]
    commit_id: str = ""
    cache_key: str = ""

    def __post_init__(self) -> None:
        _text(self.node_id, "node_id")
        _text(self.node_version, "node_version")
        object.__setattr__(self, "output_digests", _freeze_digests(self.output_digests, "output_digests"))
        object.__setattr__(
            self,
            "dependency_digests",
            _freeze_digests(self.dependency_digests, "dependency_digests"),
        )
        if self.commit_id:
            _text(self.commit_id, "commit_id")
        if self.cache_key:
            try:
                require_sha256(self.cache_key, "cache_key")
            except DomainValidationError as exc:
                raise StateInvariantError(str(exc)) from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_version": self.node_version,
            "output_digests": dict(self.output_digests),
            "dependency_digests": dict(self.dependency_digests),
            "commit_id": self.commit_id,
            "cache_key": self.cache_key,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "NodeAcceptance":
        if not isinstance(value, Mapping):
            raise StateInvariantError("NodeAcceptance must be an object")
        try:
            return cls(
                node_id=str(value["node_id"]),
                node_version=str(value["node_version"]),
                output_digests=value["output_digests"],
                dependency_digests=value["dependency_digests"],
                commit_id=str(value.get("commit_id", "")),
                cache_key=str(value.get("cache_key", "")),
            )
        except KeyError as exc:
            raise StateInvariantError("invalid NodeAcceptance") from exc


@dataclass(frozen=True)
class PersistentGraphState:
    """The only mutable business-state snapshot for a run."""

    run_id: str
    outputs: Mapping[str, ArtifactRef]
    accepted: Mapping[str, NodeAcceptance]
    event_sequence: int = 0
    current_commit_id: str = ""

    def __post_init__(self) -> None:
        _text(self.run_id, "run_id")
        if isinstance(self.event_sequence, bool) or not isinstance(self.event_sequence, int) or self.event_sequence < 0:
            raise StateInvariantError("event_sequence must be a non-negative integer")
        if self.current_commit_id:
            _text(self.current_commit_id, "current_commit_id")
        if not isinstance(self.outputs, Mapping) or not isinstance(self.accepted, Mapping):
            raise StateInvariantError("outputs and accepted must be mappings")
        outputs: dict[str, ArtifactRef] = {}
        for field_name, ref in self.outputs.items():
            _text(str(field_name), "output field")
            if not isinstance(ref, ArtifactRef):
                raise StateInvariantError("outputs must contain ArtifactRef values")
            outputs[str(field_name)] = ref
        accepted: dict[str, NodeAcceptance] = {}
        for node_id, result in self.accepted.items():
            _text(str(node_id), "accepted node")
            if not isinstance(result, NodeAcceptance) or result.node_id != node_id:
                raise StateInvariantError("accepted entries must match their NodeAcceptance node_id")
            accepted[str(node_id)] = result
        object.__setattr__(self, "outputs", MappingProxyType(outputs))
        object.__setattr__(self, "accepted", MappingProxyType(accepted))

    @classmethod
    def empty(cls, run_id: str) -> "PersistentGraphState":
        return cls(run_id=run_id, outputs={}, accepted={})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "mode_p_vnext_persistent_graph_state",
            "schema_version": "2.1",
            "run_id": self.run_id,
            "outputs": {field_name: ref.to_dict() for field_name, ref in self.outputs.items()},
            "accepted": {node_id: item.to_dict() for node_id, item in self.accepted.items()},
            "event_sequence": self.event_sequence,
            "current_commit_id": self.current_commit_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PersistentGraphState":
        if not isinstance(value, Mapping):
            raise StateInvariantError("persistent state must be an object")
        if value.get("schema_name") != "mode_p_vnext_persistent_graph_state" or value.get("schema_version") != "2.1":
            raise StateInvariantError("unsupported persistent graph state schema")
        raw_outputs = value.get("outputs")
        raw_accepted = value.get("accepted")
        if not isinstance(raw_outputs, Mapping) or not isinstance(raw_accepted, Mapping):
            raise StateInvariantError("persistent state outputs and accepted must be objects")
        return cls(
            run_id=str(value.get("run_id", "")),
            outputs={str(key): ArtifactRef.from_dict(item) for key, item in raw_outputs.items()},
            accepted={str(key): NodeAcceptance.from_dict(item) for key, item in raw_accepted.items()},
            event_sequence=int(value.get("event_sequence", 0)),
            current_commit_id=str(value.get("current_commit_id", "")),
        )
