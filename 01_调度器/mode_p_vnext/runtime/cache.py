"""Persistent cache keys bound to v3.0 graph context and ArtifactRefs only."""

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


def _digests(value: Mapping[str, str], field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise StateInvariantError(f"{field_name} must be a mapping")
    frozen: dict[str, str] = {}
    for field, digest in value.items():
        if not isinstance(field, str) or not field.strip():
            raise StateInvariantError(f"{field_name} keys must be non-empty")
        try:
            require_sha256(digest, f"{field_name}[{field}]")
        except DomainValidationError as exc:
            raise StateInvariantError(str(exc)) from exc
        frozen[field] = digest
    return MappingProxyType(frozen)


def _optional_digest(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    try:
        require_sha256(value, field_name)
    except DomainValidationError as exc:
        raise StateInvariantError(str(exc)) from exc
    return value


def _write_immutable(path: Path, payload: bytes) -> None:
    """Publish a cache value once; a matching key may never be overwritten.

    A cache key is a deterministic statement about the stage and all of its
    inputs.  Replacing an existing value for that key would make a
    nondeterministic producer appear reproducible, so a competing value must
    fail closed instead of winning by write order.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        if path.is_file() and not path.is_symlink() and path.read_bytes() == payload:
            return
        raise StateInvariantError("cache key already names different or unsafe canonical bytes")
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if not path.is_file() or path.is_symlink() or path.read_bytes() != payload:
                raise StateInvariantError("cache key already names different or unsafe canonical bytes")
        except OSError:
            try:
                with path.open("xb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
            except FileExistsError:
                if not path.is_file() or path.is_symlink() or path.read_bytes() != payload:
                    raise StateInvariantError("cache key already names different or unsafe canonical bytes")
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class NodeCacheKey:
    """Cache identity cannot omit a selected snapshot or capability profile."""

    node_id: str
    stage_signature: str
    input_digests: Mapping[str, str]
    knowledge_snapshot_digest: str | None
    capability_profile_digest: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise StateInvariantError("node_id must be non-empty")
        for field_name in ("stage_signature",):
            try:
                require_sha256(getattr(self, field_name), field_name)
            except DomainValidationError as exc:
                raise StateInvariantError(str(exc)) from exc
        object.__setattr__(self, "input_digests", _digests(self.input_digests, "input_digests"))
        _optional_digest(self.knowledge_snapshot_digest, "knowledge_snapshot_digest")
        _optional_digest(self.capability_profile_digest, "capability_profile_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "stage_signature": self.stage_signature,
            "input_digests": dict(self.input_digests),
            "knowledge_snapshot_digest": self.knowledge_snapshot_digest,
            "capability_profile_digest": self.capability_profile_digest,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


class PersistentNodeCache:
    """A restart-safe cache; process payloads cannot enter this store."""

    def __init__(self, run_dir: Path):
        self.root = Path(run_dir).resolve() / "cache"

    def _path(self, key: NodeCacheKey) -> Path:
        return self.root / f"{key.digest}.json"

    def put(self, key: NodeCacheKey, ref: ArtifactRef) -> None:
        if not isinstance(key, NodeCacheKey) or not isinstance(ref, ArtifactRef):
            raise StateInvariantError("cache requires NodeCacheKey and ArtifactRef")
        _write_immutable(
            self._path(key),
            canonical_json_bytes({"key": key.to_dict(), "artifact_ref": ref.to_dict()}),
        )

    def get(self, key: NodeCacheKey) -> ArtifactRef | None:
        if not isinstance(key, NodeCacheKey):
            raise StateInvariantError("cache key must be a NodeCacheKey")
        path = self._path(key)
        if path.is_symlink():
            raise StateInvariantError("cache record is not a regular file")
        if not path.exists():
            return None
        if not path.is_file():
            raise StateInvariantError("cache record is not a regular file")
        try:
            raw = path.read_bytes()
            value = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateInvariantError("cache record is invalid JSON") from exc
        if (
            not isinstance(value, Mapping)
            or set(value) != {"key", "artifact_ref"}
            or value["key"] != key.to_dict()
            or canonical_json_bytes(value) != raw
        ):
            raise StateInvariantError("cache record is not bound to its cache key")
        return ArtifactRef.from_dict(value["artifact_ref"])
