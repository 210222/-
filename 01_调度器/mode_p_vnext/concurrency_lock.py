"""MODE:P vNext — cross-process leases and persistent idempotency.

Filesystem-backed locks use exclusive file creation for the uncontended path
and a second exclusive takeover guard for stale recovery.  A lease may be
replaced only when it is expired, its recorded process is no longer alive, and
no active-commit marker is present.

When ``lock_root`` is omitted, :class:`SessionLock` preserves the legacy
in-memory behaviour used by early callers and tests.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Set


class LockError(Exception):
    """Lock ownership or persistence is invalid."""


def _canonical_json_bytes(value: Dict[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _atomic_replace_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        with temp.open("xb") as handle:
            handle.write(_canonical_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _create_exclusive_json(path: Path, value: Dict[str, Any]) -> bool:
    """Publish a complete record only when the destination is absent.

    A fully fsynced same-directory temporary file is hard-linked into place.
    Hard-link creation has create-if-absent semantics, so another process never
    observes the half-written record that a direct ``O_EXCL`` write could leave
    after a crash.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.candidate"
    try:
        descriptor = os.open(
            temp,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
            0o600,
        )
        try:
            payload = _canonical_json_bytes(value)
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.link(temp, path)
        except FileExistsError:
            return False
        return True
    finally:
        if temp.exists():
            temp.unlink()


def _read_record(path: Path) -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LockError(f"invalid lock record: {path}") from exc
    if not isinstance(value, dict):
        raise LockError(f"lock record must be an object: {path}")
    return value


def _pid_alive(process_id: int) -> bool:
    if process_id <= 0:
        return False
    if process_id == os.getpid():
        return True
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _append_audit(lock_root: Path, event: Dict[str, Any]) -> None:
    audit_path = lock_root / "lock_audit.jsonl"
    payload = _canonical_json_bytes(event)
    with audit_path.open("ab") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


@dataclass
class SessionLock:
    """A lease for one episode/scene resource."""

    episode_id: str
    owner: Optional[str] = None
    acquired_at: float = 0.0
    lease_seconds: float = 300.0
    lock_root: Optional[Path] = None
    operation: str = "scene_write"
    correlation_id: str = ""
    active_commit_marker: Optional[Path] = None
    lock_id: str = ""
    process_id: int = 0

    def __post_init__(self) -> None:
        if not self.episode_id:
            raise LockError("episode_id is required")
        if self.lease_seconds < 0:
            raise LockError("lease_seconds cannot be negative")
        if self.lock_root is not None:
            self.lock_root = Path(self.lock_root).resolve()
            self.lock_root.mkdir(parents=True, exist_ok=True)
        if self.active_commit_marker is not None:
            self.active_commit_marker = Path(
                self.active_commit_marker
            ).resolve()

    @property
    def lock_path(self) -> Optional[Path]:
        if self.lock_root is None:
            return None
        digest = hashlib.sha256(self.episode_id.encode("utf-8")).hexdigest()
        return self.lock_root / f"{digest}.lock.json"

    @property
    def takeover_guard_path(self) -> Optional[Path]:
        path = self.lock_path
        if path is None:
            return None
        return path.with_suffix(path.suffix + ".takeover")

    def _new_record(self, owner: str) -> Dict[str, Any]:
        now = time.time()
        lock_id = uuid.uuid4().hex
        return {
            "schema_name": "mode_p_session_lock",
            "schema_version": "1.0.0",
            "lock_id": lock_id,
            "resource_id": self.episode_id,
            "owner_id": owner,
            "process_id": os.getpid(),
            "acquired_at_epoch": now,
            "lease_expires_at_epoch": now + self.lease_seconds,
            "operation": self.operation,
            "correlation_id": self.correlation_id,
        }

    def _adopt(self, record: Dict[str, Any]) -> None:
        self.owner = str(record["owner_id"])
        self.lock_id = str(record["lock_id"])
        self.process_id = int(record["process_id"])
        self.acquired_at = float(record["acquired_at_epoch"])

    def read_record(self) -> Optional[Dict[str, Any]]:
        path = self.lock_path
        if path is None:
            if self.owner is None:
                return None
            return {
                "lock_id": self.lock_id,
                "resource_id": self.episode_id,
                "owner_id": self.owner,
                "process_id": self.process_id or os.getpid(),
                "acquired_at_epoch": self.acquired_at,
                "lease_expires_at_epoch": self.acquired_at
                + self.lease_seconds,
                "operation": self.operation,
                "correlation_id": self.correlation_id,
            }
        return _read_record(path)

    def acquire(self, owner: str) -> bool:
        if not owner:
            raise LockError("owner is required")
        if self.lock_root is None:
            if self.owner is not None and not self.is_stale:
                return False
            self.owner = owner
            self.acquired_at = time.monotonic()
            self.lock_id = uuid.uuid4().hex
            self.process_id = os.getpid()
            return True

        path = self.lock_path
        guard = self.takeover_guard_path
        assert path is not None and guard is not None
        record = self._new_record(owner)
        if _create_exclusive_json(path, record):
            self._adopt(record)
            return True

        existing = _read_record(path)
        if existing is None:
            return _create_exclusive_json(path, record)
        now = time.time()
        expires = float(existing.get("lease_expires_at_epoch", 0.0))
        if now < expires:
            return False
        if _pid_alive(int(existing.get("process_id", 0))):
            return False
        if (
            self.active_commit_marker is not None
            and self.active_commit_marker.exists()
        ):
            return False

        guard_record = {
            "owner_id": owner,
            "process_id": os.getpid(),
            "created_at_epoch": now,
        }
        if not _create_exclusive_json(guard, guard_record):
            return False
        try:
            existing = _read_record(path)
            if existing is None:
                acquired = _create_exclusive_json(path, record)
                if acquired:
                    self._adopt(record)
                return acquired
            now = time.time()
            if now < float(existing.get("lease_expires_at_epoch", 0.0)):
                return False
            if _pid_alive(int(existing.get("process_id", 0))):
                return False
            if (
                self.active_commit_marker is not None
                and self.active_commit_marker.exists()
            ):
                return False
            previous = dict(existing)
            _atomic_replace_json(path, record)
            self._adopt(record)
            _append_audit(
                self.lock_root,
                {
                    "event": "LOCK_TAKEOVER",
                    "resource_id": self.episode_id,
                    "previous_lock_id": previous.get("lock_id", ""),
                    "previous_owner_id": previous.get("owner_id", ""),
                    "new_lock_id": record["lock_id"],
                    "new_owner_id": owner,
                    "at_epoch": time.time(),
                },
            )
            return True
        finally:
            if guard.exists():
                guard.unlink()

    def refresh(self, owner: str) -> None:
        if self.lock_root is None:
            if self.owner != owner:
                raise LockError(
                    f"Lock held by '{self.owner}', cannot refresh as '{owner}'"
                )
            self.acquired_at = time.monotonic()
            return
        path = self.lock_path
        guard = self.takeover_guard_path
        assert path is not None and guard is not None
        guard_record = {
            "owner_id": owner,
            "process_id": os.getpid(),
            "created_at_epoch": time.time(),
        }
        if not _create_exclusive_json(guard, guard_record):
            raise LockError("lock is being recovered by another process")
        try:
            record = _read_record(path)
            if (
                record is None
                or record.get("owner_id") != owner
                or record.get("lock_id") != self.lock_id
            ):
                raise LockError("cannot refresh a lock no longer owned")
            now = time.time()
            record["lease_expires_at_epoch"] = now + self.lease_seconds
            _atomic_replace_json(path, record)
            self.acquired_at = now
        finally:
            if guard.exists():
                guard.unlink()

    def release(self, owner: str) -> None:
        if self.lock_root is None:
            if self.owner != owner:
                raise LockError(
                    f"Lock held by '{self.owner}', cannot release as '{owner}'"
                )
            self.owner = None
            self.acquired_at = 0.0
            self.lock_id = ""
            self.process_id = 0
            return
        path = self.lock_path
        guard = self.takeover_guard_path
        assert path is not None and guard is not None
        guard_record = {
            "owner_id": owner,
            "process_id": os.getpid(),
            "created_at_epoch": time.time(),
        }
        if not _create_exclusive_json(guard, guard_record):
            raise LockError("lock is being recovered by another process")
        try:
            record = _read_record(path)
            if (
                record is None
                or record.get("owner_id") != owner
                or record.get("lock_id") != self.lock_id
            ):
                actual = None if record is None else record.get("owner_id")
                raise LockError(
                    f"Lock held by '{actual}', cannot release as '{owner}'"
                )
            path.unlink()
            self.owner = None
            self.acquired_at = 0.0
            self.lock_id = ""
            self.process_id = 0
        finally:
            if guard.exists():
                guard.unlink()

    @property
    def is_stale(self) -> bool:
        if self.lock_root is None:
            if self.owner is None:
                return False
            return (
                time.monotonic() - self.acquired_at
            ) >= self.lease_seconds
        record = self.read_record()
        if record is None:
            return False
        return time.time() >= float(
            record.get("lease_expires_at_epoch", 0.0)
        )

    @property
    def is_held(self) -> bool:
        if self.lock_root is None:
            return self.owner is not None and not self.is_stale
        return self.read_record() is not None and not self.is_stale


class IdempotencyTracker:
    """In-memory or persistent duplicate-submission guard."""

    def __init__(self, storage_root: Optional[Path] = None):
        self._seen: Set[str] = set()
        self.storage_root = (
            None if storage_root is None else Path(storage_root).resolve()
        )
        if self.storage_root is not None:
            self.storage_root.mkdir(parents=True, exist_ok=True)

    def check_and_record(self, tx_id: str) -> bool:
        """Return True only for the process that records a new key first."""
        if not tx_id:
            raise LockError("tx_id is required")
        if self.storage_root is None:
            if tx_id in self._seen:
                return False
            self._seen.add(tx_id)
            return True
        digest = hashlib.sha256(tx_id.encode("utf-8")).hexdigest()
        record_path = self.storage_root / f"{digest}.json"
        return _create_exclusive_json(
            record_path,
            {
                "tx_id_sha256": digest,
                "recorded_at_epoch": time.time(),
                "process_id": os.getpid(),
            },
        )
