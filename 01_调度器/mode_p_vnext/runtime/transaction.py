"""Pending-to-atomic-commit protocol for the v3.1 runtime state graph.

The staging directory is intentionally *not* recoverable state.  A process
may resume only a directory that has already been atomically renamed into
``commits``.  This is the fail-closed boundary between a computed candidate
and a committed graph transition.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import DomainValidationError, canonical_json_bytes, canonical_sha256, require_sha256
from mode_p_vnext.pipeline.state import PERSISTENCE_SCHEMA_VERSION, ArtifactRef, PersistentGraphState, StateInvariantError


PENDING_FILENAME = "PENDING.json"
MANIFEST_FILENAME = "MANIFEST.json"
ABANDONED_FILENAME = "ABANDONED.json"
PENDING_SCHEMA_NAME = "mode_p_vnext_pending_runtime_write"
MANIFEST_SCHEMA_NAME = "mode_p_vnext_runtime_commit_manifest"


class NodeTransactionError(ValueError):
    """Raised when a state transition is malformed, stale, or non-atomic."""


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value in {".", ".."} or "/" in value or "\\" in value:
        raise NodeTransactionError(f"{field_name} must be a safe non-empty path component")
    return value


def _digest(value: object, field_name: str) -> str:
    try:
        require_sha256(value, field_name)  # type: ignore[arg-type]
    except DomainValidationError as exc:
        raise NodeTransactionError(str(exc)) from exc
    return value  # type: ignore[return-value]


def _non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise NodeTransactionError(f"{field_name} must be a non-negative integer")
    return value


def _refs(value: Mapping[str, ArtifactRef], field_name: str) -> Mapping[str, ArtifactRef]:
    if not isinstance(value, Mapping):
        raise NodeTransactionError(f"{field_name} must be a mapping")
    frozen: dict[str, ArtifactRef] = {}
    for key, ref in value.items():
        _text(key, f"{field_name} key")
        if not isinstance(ref, ArtifactRef):
            raise NodeTransactionError(f"{field_name} must contain ArtifactRef values")
        frozen[key] = ref
    return MappingProxyType(frozen)


def _digests(value: Mapping[str, str], field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise NodeTransactionError(f"{field_name} must be a mapping")
    frozen: dict[str, str] = {}
    for key, digest in value.items():
        _text(key, f"{field_name} key")
        frozen[key] = _digest(digest, f"{field_name}[{key}]")
    return MappingProxyType(frozen)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json(path: Path, label: str) -> Mapping[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise NodeTransactionError(f"{label} is not a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NodeTransactionError(f"{label} is invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise NodeTransactionError(f"{label} must contain an object")
    return value


@dataclass(frozen=True)
class PendingNodeWrite:
    """A durable candidate transition; it is not accepted state until commit."""

    transaction_kind: str
    commit_id: str
    generation_id: str
    parent_commit_id: str
    base_state_sha256: str
    base_candidate_revision: int
    base_candidate_digest: str
    next_state: PersistentGraphState
    state_sha256: str
    transition: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.transaction_kind not in {"node", "invalidation"}:
            raise NodeTransactionError("transaction_kind must be node or invalidation")
        _text(self.commit_id, "commit_id")
        _text(self.generation_id, "generation_id")
        if self.parent_commit_id:
            _text(self.parent_commit_id, "parent_commit_id")
        _digest(self.base_state_sha256, "base_state_sha256")
        _non_negative_int(self.base_candidate_revision, "base_candidate_revision")
        _digest(self.base_candidate_digest, "base_candidate_digest")
        _digest(self.state_sha256, "state_sha256")
        if self.state_sha256 != canonical_sha256(self.next_state.to_dict()):
            raise NodeTransactionError("state_sha256 does not match next_state")
        if not isinstance(self.transition, Mapping):
            raise NodeTransactionError("transition must be a mapping")
        frozen = MappingProxyType(dict(self.transition))
        if frozen.get("kind") != self.transaction_kind:
            raise NodeTransactionError("transition kind does not match transaction_kind")
        if self.transaction_kind == "node":
            if frozen.get("candidate_revision") != self.base_candidate_revision:
                raise NodeTransactionError("node transition is not bound to its base candidate revision")
            if frozen.get("candidate_digest") != self.base_candidate_digest:
                raise NodeTransactionError("node transition is not bound to its base candidate digest")
            if (
                frozen.get("candidate_validation_status")
                != self.next_state.candidate_validation_status.value
            ):
                raise NodeTransactionError(
                    "node transition is not bound to its resulting validation status"
                )
        object.__setattr__(self, "transition", frozen)

    @property
    def node_id(self) -> str | None:
        value = self.transition.get("node_id")
        return value if isinstance(value, str) and value else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": PENDING_SCHEMA_NAME,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "transaction_kind": self.transaction_kind,
            "commit_id": self.commit_id,
            "generation_id": self.generation_id,
            "parent_commit_id": self.parent_commit_id,
            "base_state_sha256": self.base_state_sha256,
            "base_candidate_revision": self.base_candidate_revision,
            "base_candidate_digest": self.base_candidate_digest,
            "next_state": self.next_state.to_dict(),
            "state_sha256": self.state_sha256,
            "transition": dict(self.transition),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PendingNodeWrite":
        expected = {
            "schema_name", "schema_version", "transaction_kind", "commit_id",
            "generation_id", "parent_commit_id", "base_state_sha256",
            "base_candidate_revision", "base_candidate_digest", "next_state",
            "state_sha256", "transition",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise NodeTransactionError("pending write fields do not match the v3.1 schema")
        if value.get("schema_name") != PENDING_SCHEMA_NAME or value.get("schema_version") != PERSISTENCE_SCHEMA_VERSION:
            raise NodeTransactionError("unsupported pending write schema")
        try:
            return cls(
                transaction_kind=value["transaction_kind"],
                commit_id=value["commit_id"],
                generation_id=value["generation_id"],
                parent_commit_id=value["parent_commit_id"],
                base_state_sha256=value["base_state_sha256"],
                base_candidate_revision=value["base_candidate_revision"],
                base_candidate_digest=value["base_candidate_digest"],
                next_state=PersistentGraphState.from_dict(value["next_state"]),
                state_sha256=value["state_sha256"],
                transition=value["transition"],
            )
        except (KeyError, TypeError, StateInvariantError) as exc:
            if isinstance(exc, NodeTransactionError):
                raise
            raise NodeTransactionError("invalid pending write") from exc


class NodeTransaction:
    """Creates candidates in staging and promotes them by one atomic rename."""

    @staticmethod
    def new_identity(label: str) -> tuple[str, str]:
        _text(label, "transaction label")
        nonce = uuid.uuid4().hex
        return f"{label.lower()}-{nonce}", f"generation-{nonce}"

    @staticmethod
    def prepare(
        run_dir: Path,
        *,
        transaction_kind: str,
        base_state: PersistentGraphState,
        next_state: PersistentGraphState,
        parent_commit_id: str,
        commit_id: str,
        generation_id: str,
        transition: Mapping[str, Any],
    ) -> PendingNodeWrite:
        root = Path(run_dir).resolve()
        if not isinstance(base_state, PersistentGraphState) or not isinstance(next_state, PersistentGraphState):
            raise NodeTransactionError("transactions require persistent graph states")
        if base_state.run_id != next_state.run_id or base_state.graph_digest != next_state.graph_digest:
            raise NodeTransactionError("transaction states must retain run and graph identity")
        if parent_commit_id != base_state.current_commit_id:
            raise NodeTransactionError("transaction parent must match the base state commit")
        if next_state.event_sequence != base_state.event_sequence + 1:
            raise NodeTransactionError("transaction must advance the event sequence exactly once")
        if next_state.current_commit_id != commit_id:
            raise NodeTransactionError("transaction next state must name its commit")
        if transaction_kind == "node" and next_state.candidate_revision != base_state.candidate_revision:
            raise NodeTransactionError("a node transaction cannot advance candidate_revision")
        if transaction_kind == "invalidation" and next_state.candidate_revision != base_state.candidate_revision + 1:
            raise NodeTransactionError("an invalidation transaction must advance candidate_revision once")
        pending = PendingNodeWrite(
            transaction_kind=transaction_kind,
            commit_id=commit_id,
            generation_id=generation_id,
            parent_commit_id=parent_commit_id,
            base_state_sha256=canonical_sha256(base_state.to_dict()),
            base_candidate_revision=base_state.candidate_revision,
            base_candidate_digest=base_state.candidate_digest,
            next_state=next_state,
            state_sha256=canonical_sha256(next_state.to_dict()),
            transition=transition,
        )
        NodeTransaction._stage(root, pending)
        NodeTransaction.validate_staged(root / "staging" / pending.generation_id, pending)
        return pending

    @staticmethod
    def _manifest(pending: PendingNodeWrite) -> dict[str, Any]:
        body = {
            "schema_name": MANIFEST_SCHEMA_NAME,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "transaction_kind": pending.transaction_kind,
            "commit_id": pending.commit_id,
            "generation_id": pending.generation_id,
            "parent_commit_id": pending.parent_commit_id,
            "base_state_sha256": pending.base_state_sha256,
            "base_candidate_revision": pending.base_candidate_revision,
            "base_candidate_digest": pending.base_candidate_digest,
            "next_candidate_revision": pending.next_state.candidate_revision,
            "next_candidate_digest": pending.next_state.candidate_digest,
            "next_candidate_validation_status": pending.next_state.candidate_validation_status.value,
            "state_sha256": pending.state_sha256,
            "transition_sha256": canonical_sha256(pending.transition),
            "pending_sha256": canonical_sha256(pending.to_dict()),
        }
        return {**body, "manifest_sha256": canonical_sha256(body)}

    @staticmethod
    def _stage(root: Path, pending: PendingNodeWrite) -> None:
        staging_root = root / "staging"
        staging_root.mkdir(parents=True, exist_ok=True)
        target = staging_root / pending.generation_id
        if target.exists():
            raise NodeTransactionError("prepared generation already exists")
        temporary = staging_root / f".{pending.generation_id}.{uuid.uuid4().hex}.tmp"
        try:
            temporary.mkdir()
            _atomic_write(temporary / PENDING_FILENAME, canonical_json_bytes(pending.to_dict()))
            _atomic_write(temporary / MANIFEST_FILENAME, canonical_json_bytes(NodeTransaction._manifest(pending)))
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)

    @staticmethod
    def _read(directory: Path, *, committed: bool) -> PendingNodeWrite:
        root = Path(directory)
        pending = PendingNodeWrite.from_dict(_read_json(root / PENDING_FILENAME, "pending write"))
        manifest = _read_json(root / MANIFEST_FILENAME, "commit manifest")
        expected_manifest = NodeTransaction._manifest(pending)
        if manifest != expected_manifest:
            raise NodeTransactionError("commit manifest does not bind its pending state transition")
        expected_name = pending.commit_id if committed else pending.generation_id
        if root.name != expected_name:
            raise NodeTransactionError("transaction directory name does not match its identity")
        return pending

    @staticmethod
    def read_prepared(staging_dir: Path) -> PendingNodeWrite:
        return NodeTransaction._read(staging_dir, committed=False)

    @staticmethod
    def read_committed(commit_dir: Path) -> PendingNodeWrite:
        return NodeTransaction._read(commit_dir, committed=True)

    @staticmethod
    def validate_staged(staging_dir: Path, pending: PendingNodeWrite) -> None:
        if canonical_sha256(NodeTransaction.read_prepared(staging_dir).to_dict()) != canonical_sha256(pending.to_dict()):
            raise NodeTransactionError("staged pending write differs from the prepared transition")

    @staticmethod
    def promote(run_dir: Path, pending: PendingNodeWrite) -> Path:
        root = Path(run_dir).resolve()
        staging = root / "staging" / pending.generation_id
        commits = root / "commits"
        commits.mkdir(parents=True, exist_ok=True)
        target = commits / pending.commit_id
        if target.exists():
            raise NodeTransactionError("commit identity already exists")
        NodeTransaction.validate_staged(staging, pending)
        os.replace(staging, target)
        if canonical_sha256(NodeTransaction.read_committed(target).to_dict()) != canonical_sha256(pending.to_dict()):
            raise NodeTransactionError("atomic promotion produced a mismatched commit")
        return target

    @staticmethod
    def manifest_sha256(commit_dir: Path) -> str:
        manifest = _read_json(Path(commit_dir) / MANIFEST_FILENAME, "commit manifest")
        value = manifest.get("manifest_sha256")
        return _digest(value, "manifest_sha256")

    @staticmethod
    def abandon_staging(run_dir: Path, generation_id: str, *, reason: str) -> Path:
        root = Path(run_dir).resolve()
        generation = _text(generation_id, "generation_id")
        if not isinstance(reason, str) or not reason.strip():
            raise NodeTransactionError("abandon reason must be non-empty")
        source = root / "staging" / generation
        if not source.is_dir() or source.is_symlink():
            raise NodeTransactionError("uncommitted staging candidate is missing or unsafe")
        pending = NodeTransaction.read_prepared(source)
        quarantine = root / "quarantine"
        quarantine.mkdir(parents=True, exist_ok=True)
        target = quarantine / generation
        if target.exists():
            raise NodeTransactionError("quarantine generation already exists")
        _atomic_write(
            source / ABANDONED_FILENAME,
            canonical_json_bytes(
                {
                    "schema_name": "mode_p_vnext_abandoned_pending_write",
                    "schema_version": PERSISTENCE_SCHEMA_VERSION,
                    "generation_id": pending.generation_id,
                    "commit_id": pending.commit_id,
                    "reason": reason,
                    "pending_sha256": canonical_sha256(pending.to_dict()),
                }
            ),
        )
        os.replace(source, target)
        return target
