"""Immutable content-addressed ArtifactEnvelope repository."""

from __future__ import annotations

import os
import json
import uuid
from pathlib import Path
from typing import TypeVar

from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    canonical_json_bytes,
    canonical_sha256,
)
from mode_p_vnext.pipeline.state import ArtifactRef


T = TypeVar("T")


class ArtifactStoreError(ValueError):
    """Raised when an immutable artifact cannot be safely persisted."""


def _atomic_write_if_absent(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if not path.is_file() or path.is_symlink():
            raise ArtifactStoreError(f"artifact path is not a regular file: {path}")
        return
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with open(temporary, "xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            pass
        except OSError:
            if not path.exists():
                os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class ArtifactRepository:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir).resolve()

    def path_for(self, artifact: ArtifactEnvelope[T]) -> Path:
        return self.run_dir / "artifacts" / artifact.artifact_kind.value / f"{artifact.content_sha256}.json"

    def put(self, artifact: ArtifactEnvelope[T]) -> ArtifactRef:
        _atomic_write_if_absent(self.path_for(artifact), canonical_json_bytes(artifact))
        ref = ArtifactRef(
            artifact_id=artifact.artifact_id,
            artifact_kind=artifact.artifact_kind,
            content_sha256=artifact.content_sha256,
            schema_version=artifact.schema_version,
        )
        if not self.contains(ref):
            raise ArtifactStoreError(
                "content-addressed artifact path does not verify its canonical digest"
            )
        return ref

    def contains(self, ref: ArtifactRef) -> bool:
        """Check that an ArtifactRef resolves to its immutable stored envelope."""
        if not isinstance(ref, ArtifactRef):
            raise ArtifactStoreError("contains requires an ArtifactRef")
        path = (
            self.run_dir
            / "artifacts"
            / ref.artifact_kind.value
            / f"{ref.content_sha256}.json"
        )
        if not path.is_file() or path.is_symlink():
            return False
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(stored, dict):
                return False
            if not (
                stored.get("artifact_id") == ref.artifact_id
                and stored.get("artifact_kind") == ref.artifact_kind.value
                and stored.get("schema_version") == ref.schema_version
                and stored.get("content_sha256") == ref.content_sha256
            ):
                return False
            canonical_content = {
                "artifact_kind": stored["artifact_kind"],
                "schema_version": stored["schema_version"],
                "program_version": stored["program_version"],
                "payload": stored["payload"],
                "source_refs": stored["source_refs"],
                "dependency_digests": stored["dependency_digests"],
            }
            return canonical_sha256(canonical_content) == ref.content_sha256
        except (
            KeyError,
            OSError,
            UnicodeError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
            AttributeError,
        ):
            return False
