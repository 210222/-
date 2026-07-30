"""Persistent cache keys and ArtifactRef-only cache values."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import DomainValidationError, canonical_json_bytes, canonical_sha256, require_sha256
from mode_p_vnext.pipeline.state import ArtifactRef, StateInvariantError


def _freeze_digest_mapping(value: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise StateInvariantError("approved_input_digests must be a mapping")
    result: dict[str, str] = {}
    for name, digest in value.items():
        if not isinstance(name, str) or not name.strip():
            raise StateInvariantError("cache input names must be non-empty")
        try:
            require_sha256(digest, f"approved_input_digests[{name}]")
        except DomainValidationError as exc:
            raise StateInvariantError(str(exc)) from exc
        result[name] = digest
    return MappingProxyType(result)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with open(temporary, "xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class NodeCacheKey:
    node_kind: str
    node_version: str
    signature_version: str
    schema_digest: str
    approved_input_digests: Mapping[str, str]
    knowledge_snapshot_digest: str
    requested_model: str
    resolved_provider_config: str
    generation_policy: str

    def __post_init__(self) -> None:
        for field_name in (
            "node_kind",
            "node_version",
            "signature_version",
            "requested_model",
            "resolved_provider_config",
            "generation_policy",
        ):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name).strip():
                raise StateInvariantError(f"{field_name} must be non-empty")
        for field_name in ("schema_digest", "knowledge_snapshot_digest"):
            try:
                require_sha256(getattr(self, field_name), field_name)
            except DomainValidationError as exc:
                raise StateInvariantError(str(exc)) from exc
        object.__setattr__(self, "approved_input_digests", _freeze_digest_mapping(self.approved_input_digests))

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_kind": self.node_kind,
            "node_version": self.node_version,
            "signature_version": self.signature_version,
            "schema_digest": self.schema_digest,
            "approved_input_digests": dict(self.approved_input_digests),
            "knowledge_snapshot_digest": self.knowledge_snapshot_digest,
            "requested_model": self.requested_model,
            "resolved_provider_config": self.resolved_provider_config,
            "generation_policy": self.generation_policy,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


class PersistentNodeCache:
    """A restart-safe cache whose values are only persisted ArtifactRef data."""

    def __init__(self, run_dir: Path):
        self.root = Path(run_dir).resolve() / "cache"

    def _path(self, key: NodeCacheKey) -> Path:
        return self.root / f"{key.digest}.json"

    def put(self, key: NodeCacheKey, ref: ArtifactRef) -> None:
        if not isinstance(key, NodeCacheKey) or not isinstance(ref, ArtifactRef):
            raise StateInvariantError("cache requires NodeCacheKey and ArtifactRef")
        _atomic_write(
            self._path(key),
            canonical_json_bytes({"key": key.to_dict(), "artifact_ref": ref.to_dict()}),
        )

    def get(self, key: NodeCacheKey) -> ArtifactRef | None:
        if not isinstance(key, NodeCacheKey):
            raise StateInvariantError("cache key must be a NodeCacheKey")
        path = self._path(key)
        if not path.exists():
            return None
        if not path.is_file() or path.is_symlink():
            raise StateInvariantError("cache record is not a regular file")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateInvariantError("cache record is invalid JSON") from exc
        if not isinstance(value, Mapping) or value.get("key") != key.to_dict():
            raise StateInvariantError("cache key does not match persisted record")
        return ArtifactRef.from_dict(value.get("artifact_ref", {}))
