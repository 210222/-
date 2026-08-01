"""Immutable content-addressed storage for canonical v3.0 envelopes."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping, TypeVar

from mode_p_vnext.domain.artifact import ArtifactEnvelope, canonical_json_bytes, canonical_sha256
from mode_p_vnext.pipeline.state import ArtifactRef


T = TypeVar("T")


class ArtifactStoreError(ValueError):
    """Raised when an immutable canonical artifact cannot be verified."""


def _atomic_write_if_absent(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if not path.is_file() or path.is_symlink() or path.read_bytes() != payload:
            raise ArtifactStoreError("content-addressed artifact path conflicts with canonical bytes")
        return
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise ArtifactStoreError("concurrent artifact write has different canonical bytes")
        except OSError:
            if path.exists():
                if path.read_bytes() != payload:
                    raise ArtifactStoreError("concurrent artifact write has different canonical bytes")
            else:
                os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class ArtifactRepository:
    """Stores full immutable envelopes and exposes only reference metadata."""

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir).resolve()

    def path_for(self, artifact: ArtifactEnvelope[T]) -> Path:
        digest = canonical_sha256(artifact)
        return self.run_dir / "artifacts" / artifact.artifact_type.value / f"{digest}.json"

    def put(self, artifact: ArtifactEnvelope[T]) -> ArtifactRef:
        if not isinstance(artifact, ArtifactEnvelope):
            raise ArtifactStoreError("ArtifactRepository accepts only canonical ArtifactEnvelope values")
        payload = canonical_json_bytes(artifact)
        artifact_digest = canonical_sha256(artifact)
        _atomic_write_if_absent(self.path_for(artifact), payload)
        ref = ArtifactRef(
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            schema_version=artifact.schema_version,
            canonical_payload_sha256=artifact.canonical_payload_sha256,
            artifact_digest=artifact_digest,
        )
        if not self.contains(ref):
            raise ArtifactStoreError("stored ArtifactEnvelope does not verify against its reference")
        return ref

    def _path_for_ref(self, ref: ArtifactRef) -> Path:
        return self.run_dir / "artifacts" / ref.artifact_type.value / f"{ref.artifact_digest}.json"

    def contains(self, ref: ArtifactRef) -> bool:
        if not isinstance(ref, ArtifactRef):
            raise ArtifactStoreError("contains requires an ArtifactRef")
        path = self._path_for_ref(ref)
        if not path.is_file() or path.is_symlink():
            return False
        try:
            raw = path.read_bytes()
            if canonical_sha256(json.loads(raw.decode("utf-8"))) != ref.artifact_digest:
                return False
            stored: Any = json.loads(raw.decode("utf-8"))
            if not isinstance(stored, Mapping):
                return False
            expected_fields = {
                "artifact_id", "artifact_type", "schema_version", "payload",
                "canonical_payload_sha256", "producer_stage", "parent_artifact_ids",
                "source_provenance", "knowledge_snapshot_digest", "created_at_utc",
            }
            return (
                set(stored) == expected_fields
                and stored.get("artifact_id") == ref.artifact_id
                and stored.get("artifact_type") == ref.artifact_type.value
                and stored.get("schema_version") == ref.schema_version
                and stored.get("canonical_payload_sha256") == ref.canonical_payload_sha256
                and canonical_sha256(stored.get("payload")) == ref.canonical_payload_sha256
            )
        except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
            return False
