"""Bridge the vNext graph state protocol to the established atomic committer."""

from __future__ import annotations

import json
import os
import uuid
from hashlib import sha256
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from mode_p_vnext.atomic_commit import Transaction, TransactionError, recover_scene
from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    canonical_json_bytes,
    canonical_sha256,
    require_sha256,
)
from mode_p_vnext.pipeline.state import (
    PERSISTENCE_SCHEMA_VERSION,
    ArtifactRef,
    PersistentGraphState,
    StateInvariantError,
)


PENDING_FILENAME = "pending.commit"
STATE_FILENAME = "node_state.json"
VNEXT_MANIFEST_FILENAME = "MANIFEST.json"
LEGACY_MANIFEST_FILENAME = "COMMIT_MANIFEST.json"


class NodeTransactionError(ValueError):
    """Raised when a prepared node write cannot be safely promoted."""


def _freeze_refs(values: Mapping[str, ArtifactRef]) -> Mapping[str, ArtifactRef]:
    if not isinstance(values, Mapping):
        raise NodeTransactionError("outputs must be a mapping")
    frozen: dict[str, ArtifactRef] = {}
    for field_name, ref in values.items():
        if not isinstance(field_name, str) or not field_name.strip():
            raise NodeTransactionError("output field names must be non-empty strings")
        if not isinstance(ref, ArtifactRef):
            raise NodeTransactionError("outputs must contain ArtifactRef values")
        frozen[field_name] = ref
    return MappingProxyType(frozen)


def _freeze_digests(values: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(values, Mapping):
        raise NodeTransactionError("dependency_digests must be a mapping")
    frozen: dict[str, str] = {}
    for field_name, digest in values.items():
        if not isinstance(field_name, str) or not field_name.strip():
            raise NodeTransactionError("dependency field names must be non-empty strings")
        if not isinstance(digest, str) or len(digest) != 64:
            raise NodeTransactionError("dependency digests must be sha256 strings")
        frozen[field_name] = digest
    return MappingProxyType(frozen)


@dataclass(frozen=True)
class PendingNodeWrite:
    """Prepared, durable node result that has not yet become graph authority."""

    node_id: str
    commit_id: str
    generation_id: str
    base_state_sha256: str
    next_state: PersistentGraphState
    state_sha256: str
    outputs: Mapping[str, ArtifactRef]
    dependency_digests: Mapping[str, str]
    _transaction: Transaction | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.commit_id.strip() or not self.generation_id.strip():
            raise NodeTransactionError("pending node identity fields must be non-empty")
        try:
            require_sha256(self.base_state_sha256, "base_state_sha256")
            require_sha256(self.state_sha256, "state_sha256")
        except DomainValidationError as exc:
            raise NodeTransactionError(str(exc)) from exc
        if self.state_sha256 != canonical_sha256(self.next_state.to_dict()):
            raise NodeTransactionError("pending state hash does not match the state payload")
        object.__setattr__(self, "outputs", _freeze_refs(self.outputs))
        object.__setattr__(self, "dependency_digests", _freeze_digests(self.dependency_digests))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "mode_p_vnext_pending_node_write",
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "node_id": self.node_id,
            "commit_id": self.commit_id,
            "generation_id": self.generation_id,
            "base_state_sha256": self.base_state_sha256,
            "state": self.next_state.to_dict(),
            "state_sha256": self.state_sha256,
            "outputs": {name: ref.to_dict() for name, ref in self.outputs.items()},
            "dependency_digests": dict(self.dependency_digests),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PendingNodeWrite":
        try:
            if (
                value["schema_name"] != "mode_p_vnext_pending_node_write"
                or value["schema_version"] != PERSISTENCE_SCHEMA_VERSION
            ):
                raise NodeTransactionError("unsupported pending node write schema")
            raw_outputs = value["outputs"]
            if not isinstance(raw_outputs, Mapping):
                raise NodeTransactionError("pending outputs must be an object")
            return cls(
                node_id=str(value["node_id"]),
                commit_id=str(value["commit_id"]),
                generation_id=str(value["generation_id"]),
                base_state_sha256=str(value["base_state_sha256"]),
                next_state=PersistentGraphState.from_dict(value["state"]),
                state_sha256=str(value["state_sha256"]),
                outputs={
                    str(name): ArtifactRef.from_dict(ref)
                    for name, ref in raw_outputs.items()
                },
                dependency_digests=value["dependency_digests"],
            )
        except (KeyError, TypeError, StateInvariantError) as exc:
            if isinstance(exc, NodeTransactionError):
                raise
            raise NodeTransactionError("invalid pending node write") from exc


class NodeTransaction:
    """Prepare/promote one graph transition using the existing atomic filesystem commit."""

    @staticmethod
    def new_identity(node_id: str) -> tuple[str, str]:
        if not node_id or not node_id.strip():
            raise NodeTransactionError("node_id must be non-empty")
        return (
            f"{node_id.lower()}-{uuid.uuid4().hex}",
            f"generation-{uuid.uuid4().hex}",
        )

    @staticmethod
    def prepare(
        run_dir: Path,
        *,
        node_id: str,
        base_state: PersistentGraphState,
        next_state: PersistentGraphState,
        outputs: Mapping[str, ArtifactRef],
        dependency_digests: Mapping[str, str],
        graph_digest: str,
        commit_id: str,
        generation_id: str,
    ) -> PendingNodeWrite:
        root = Path(run_dir).resolve()
        transaction = Transaction(
            commit_id,
            node_id,
            scene_root=root,
            generation_id=generation_id,
            parent_commit_id=base_state.current_commit_id,
        )
        pending = PendingNodeWrite(
            node_id=node_id,
            commit_id=commit_id,
            generation_id=generation_id,
            base_state_sha256=canonical_sha256(base_state.to_dict()),
            next_state=next_state,
            state_sha256=canonical_sha256(next_state.to_dict()),
            outputs=outputs,
            dependency_digests=dependency_digests,
            _transaction=transaction,
        )
        payload = json.dumps(
            pending.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        try:
            transaction.stage(PENDING_FILENAME, payload)
            transaction.stage(STATE_FILENAME, payload)
            transaction.prepare(
                {
                    "node_id": node_id,
                    "graph_digest": graph_digest,
                    "base_state_sha256": pending.base_state_sha256,
                    "state_sha256": pending.state_sha256,
                }
            )
        except TransactionError as exc:
            raise NodeTransactionError(str(exc)) from exc
        staging_dir = transaction.staging_dir
        if staging_dir is None:
            raise NodeTransactionError("prepared transaction has no staging directory")
        NodeTransaction._write_vnext_manifest(staging_dir, pending)
        NodeTransaction._validate_vnext_manifest(staging_dir, pending)
        return pending

    @staticmethod
    def read_prepared(staging_dir: Path) -> PendingNodeWrite:
        path = Path(staging_dir) / PENDING_FILENAME
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise NodeTransactionError(f"cannot read prepared node write: {path}") from exc
        pending = PendingNodeWrite.from_dict(raw)
        if pending.generation_id != Path(staging_dir).name:
            raise NodeTransactionError("pending generation does not match its staging directory")
        return pending

    @staticmethod
    def promote(run_dir: Path, pending: PendingNodeWrite) -> None:
        """Atomically move prepared content into commits and update the legacy pointer."""
        try:
            if pending._transaction is not None:
                pending._transaction.commit()
            else:
                report = recover_scene(Path(run_dir).resolve())
                if report.errors:
                    raise NodeTransactionError("; ".join(report.errors))
                if report.current_commit_id != pending.commit_id:
                    raise NodeTransactionError(
                        "recovery did not promote the expected prepared node write"
                    )
        except TransactionError as exc:
            raise NodeTransactionError(str(exc)) from exc
        NodeTransaction._validate_vnext_manifest(
            Path(run_dir).resolve() / "commits" / pending.commit_id,
            pending,
        )

    @staticmethod
    def _vnext_manifest_payload(
        directory: Path, pending: PendingNodeWrite
    ) -> dict[str, str]:
        root = Path(directory)
        legacy_manifest = root / LEGACY_MANIFEST_FILENAME
        if not legacy_manifest.is_file() or legacy_manifest.is_symlink():
            raise NodeTransactionError("atomic commit has no regular COMMIT_MANIFEST.json")
        try:
            legacy = json.loads(legacy_manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise NodeTransactionError("atomic commit manifest is invalid") from exc
        if legacy.get("commit_id") != pending.commit_id:
            raise NodeTransactionError("atomic commit manifest has a different commit_id")
        metadata = legacy.get("metadata")
        if not isinstance(metadata, Mapping) or (
            metadata.get("node_id") != pending.node_id
            or metadata.get("base_state_sha256") != pending.base_state_sha256
            or metadata.get("state_sha256") != pending.state_sha256
        ):
            raise NodeTransactionError(
                "atomic commit manifest does not bind the pending state transition"
            )
        return {
            "schema_name": "mode_p_vnext_commit_manifest",
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "commit_id": pending.commit_id,
            "generation_id": pending.generation_id,
            "node_id": pending.node_id,
            "base_state_sha256": pending.base_state_sha256,
            "state_sha256": pending.state_sha256,
            # The established committer records a floating-point wall-clock
            # timestamp. It is not a vNext canonical artifact, so retain its
            # file-integrity digest instead of attempting canonical JSON.
            "legacy_manifest_sha256": sha256(legacy_manifest.read_bytes()).hexdigest(),
        }

    @staticmethod
    def _write_vnext_manifest(directory: Path, pending: PendingNodeWrite) -> None:
        """Stage the state-binding manifest before same-volume promotion."""

        root = Path(directory)
        payload = NodeTransaction._vnext_manifest_payload(root, pending)
        target = root / VNEXT_MANIFEST_FILENAME
        if target.exists() and (not target.is_file() or target.is_symlink()):
            raise NodeTransactionError("vNext manifest path is not a regular file")
        temporary = root / f".{VNEXT_MANIFEST_FILENAME}.{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as handle:
                handle.write(canonical_json_bytes(payload))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()

    @staticmethod
    def _validate_vnext_manifest(
        directory: Path, pending: PendingNodeWrite
    ) -> None:
        """Verify the companion manifest before or after atomic promotion."""

        root = Path(directory)
        target = root / VNEXT_MANIFEST_FILENAME
        if not target.is_file() or target.is_symlink():
            raise NodeTransactionError("atomic commit has no regular vNext manifest")
        try:
            actual = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise NodeTransactionError("vNext commit manifest is invalid") from exc
        expected = NodeTransaction._vnext_manifest_payload(root, pending)
        if actual != expected:
            raise NodeTransactionError(
                "vNext commit manifest does not match the pending state transition"
            )
