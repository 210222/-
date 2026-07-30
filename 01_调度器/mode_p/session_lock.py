"""Exclusive session writes and crash-safe directory commits for MODE:P.

Writers create a unique ``staging/<transaction_id>`` tree and verify it before
one directory-level switch. Working trees retain an internal manifest. Delivery
manifests are archived beside the target so user-facing delivery contains only
the promised prompt documents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


LOCK_SCHEMA_VERSION = "1.0"
COMMIT_SCHEMA_VERSION = "2.0"
_TRANSACTION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_LOCK_GRACE_SECONDS = 2.0
_MANIFEST_FIELDS = {
    "schema_version", "session_id", "transaction_id", "target", "stage",
    "batch_index", "committed_at", "master_generation", "master_sha256",
    "state_sha256", "implementation_fingerprints", "entries",
    "manifest_sha256",
}
_IMPLEMENTATION_FILES = {
    "master_compiler": "master_compiler.py",
    "view_deriver": "view_deriver.py",
    "master_sync_check": "master_sync_check.py",
    "boundary_check": "boundary_check.py",
    "reference_plan_check": "reference_plan_check.py",
    "sd2_preflight": "sd2_preflight.py",
    "final_master_sync": "master_sync_check.py",
}


class LockError(RuntimeError):
    """Raised when a lock, staged transaction, or commit is invalid."""


@dataclass(frozen=True)
class CommitEntry:
    path: str
    sha256: str
    size: int


@dataclass
class CommitManifest:
    schema_version: str
    session_id: str
    transaction_id: str
    target: str
    stage: str
    batch_index: int
    committed_at: str
    master_generation: int
    master_sha256: str
    state_sha256: str
    implementation_fingerprints: dict[str, str] = field(default_factory=dict)
    entries: list[CommitEntry] = field(default_factory=list)
    manifest_sha256: str = ""

    @property
    def total_files(self) -> int:
        return len(self.entries)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(data: dict[str, Any], excluded: str) -> str:
    payload = {key: value for key, value in data.items() if key != excluded}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _safe_name(value: str, label: str) -> str:
    if not isinstance(value, str) or not _TRANSACTION_RE.fullmatch(value):
        raise LockError(f"invalid {label}: {value!r}")
    return value


def _safe_relative(value: str, label: str = "path") -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise LockError(f"{label} must be a portable relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise LockError(f"{label} escapes its transaction: {value!r}")
    return pure


def _inside(root: Path, path: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise LockError(f"{label} escapes session: {path}") from exc
    return resolved


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _read_lock(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    expected = {"schema_version", "pid", "token", "created_at"}
    if not isinstance(raw, dict) or set(raw) != expected:
        return None
    if raw["schema_version"] != LOCK_SCHEMA_VERSION:
        return None
    if isinstance(raw["pid"], bool) or not isinstance(raw["pid"], int):
        return None
    if not isinstance(raw["token"], str) or not raw["token"]:
        return None
    return raw


def _remove_stale_lock(path: Path) -> bool:
    record = _read_lock(path)
    if record is not None and _pid_alive(record["pid"]):
        return False
    try:
        age = time.time() - path.stat().st_mtime
    except FileNotFoundError:
        return True
    if record is None and age < _LOCK_GRACE_SECONDS:
        return False
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return True


@contextmanager
def session_lock(session_dir: Path, timeout: float = 0.0) -> Iterator[None]:
    """Acquire the only writer lock for a session.

    Dead-owner locks are recovered.  A live owner fails immediately by default;
    a caller may provide a short timeout for explicit waiting.
    """
    if timeout < 0:
        raise LockError("lock timeout cannot be negative")
    session_dir.mkdir(parents=True, exist_ok=True)
    lock_path = session_dir / "SESSION.lock"
    deadline = time.monotonic() + timeout
    token = uuid.uuid4().hex
    record = {
        "schema_version": LOCK_SCHEMA_VERSION,
        "pid": os.getpid(),
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    while True:
        try:
            descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
                os.write(descriptor, payload)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            break
        except FileExistsError:
            if _remove_stale_lock(lock_path):
                continue
            if time.monotonic() >= deadline:
                owner = _read_lock(lock_path)
                owner_pid = owner.get("pid") if owner else "unknown"
                raise LockError(f"session is already locked by PID {owner_pid}: {session_dir}")
            time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
    try:
        yield
    finally:
        current = _read_lock(lock_path)
        if current is not None and current.get("token") == token:
            lock_path.unlink(missing_ok=True)


def staging_dir(session_dir: Path, transaction_id: str | None = None) -> Path:
    root = session_dir / "staging"
    if transaction_id is None:
        return root
    return root / _safe_name(transaction_id, "transaction_id")


def prepare_staging(
    session_dir: Path,
    files: dict[str, Path],
    transaction_id: str | None = None,
) -> Path:
    """Copy a complete candidate file set into a new isolated transaction."""
    if not isinstance(files, dict) or not files:
        raise LockError("a transaction must stage at least one file")
    transaction_id = transaction_id or uuid.uuid4().hex
    _safe_name(transaction_id, "transaction_id")
    normalized: list[tuple[PurePosixPath, Path]] = []
    seen: set[str] = set()
    for raw_path, source in files.items():
        relative = _safe_relative(raw_path, "staged path")
        folded = relative.as_posix().casefold()
        if folded in seen:
            raise LockError(f"duplicate staged path: {raw_path}")
        seen.add(folded)
        source = Path(source)
        if not source.is_file():
            raise LockError(f"staged source is not a file: {source}")
        normalized.append((relative, source))

    with session_lock(session_dir):
        _recover_unlocked(session_dir)
        transaction = staging_dir(session_dir, transaction_id)
        if transaction.exists():
            raise LockError(f"staging transaction already exists: {transaction_id}")
        transaction.mkdir(parents=True)
        try:
            for relative, source in normalized:
                destination = transaction.joinpath(*relative.parts)
                _inside(transaction, destination, "staged path")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        except Exception:
            shutil.rmtree(transaction, ignore_errors=True)
            raise
        return transaction


def _implementation_fingerprints(state: dict[str, Any]) -> dict[str, str]:
    # A commit must remain attributable even when the state machine has just
    # cleared per-stage check records.  Fingerprint the complete deterministic
    # publication toolchain; dependency invalidation still decides which check
    # needs to rerun.
    names = sorted(_IMPLEMENTATION_FILES)
    base = Path(__file__).parent
    fingerprints: dict[str, str] = {}
    for name in names:
        filename = _IMPLEMENTATION_FILES.get(name)
        if filename and (base / filename).is_file():
            fingerprints[name] = _sha256(base / filename)
    return fingerprints


def _state_metadata(session_dir: Path) -> tuple[dict[str, Any], int, str, str]:
    path = session_dir / "RUN_STATE.json"
    if not path.is_file():
        return {}, 0, "", ""
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LockError(f"RUN_STATE cannot authorize a commit: {exc}") from exc
    if not isinstance(state, dict):
        raise LockError("RUN_STATE cannot authorize a commit: root is not an object")
    generation = state.get("artifact_generation", 0)
    master_hash = state.get("master_sha256", "")
    state_hash = state.get("state_sha256", "")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise LockError("RUN_STATE has invalid artifact_generation")
    for label, value in (("master_sha256", master_hash), ("state_sha256", state_hash)):
        if value and (not isinstance(value, str) or not _HASH_RE.fullmatch(value)):
            raise LockError(f"RUN_STATE has invalid {label}")
    return state, generation, master_hash, state_hash


def _transaction_files(transaction: Path) -> list[CommitEntry]:
    entries: list[CommitEntry] = []
    for path in sorted(transaction.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if path.is_symlink():
            raise LockError(f"symlinks are not allowed in staging: {path}")
        if not path.is_file() or path.name == "COMMIT_MANIFEST.json":
            continue
        relative = path.relative_to(transaction).as_posix()
        _safe_relative(relative, "manifest entry")
        entries.append(CommitEntry(relative, _sha256(path), path.stat().st_size))
    if not entries:
        raise LockError("staging transaction contains no files")
    return entries


def _manifest_data(manifest: CommitManifest) -> dict[str, Any]:
    data = asdict(manifest)
    data["manifest_sha256"] = _canonical_hash(data, "manifest_sha256")
    manifest.manifest_sha256 = data["manifest_sha256"]
    return data


def _validate_manifest_data(data: Any, expected_session: str | None = None) -> None:
    if not isinstance(data, dict) or set(data) != _MANIFEST_FIELDS:
        raise LockError("commit manifest fields do not match schema")
    if data["schema_version"] != COMMIT_SCHEMA_VERSION:
        raise LockError("unsupported commit manifest schema_version")
    if expected_session is not None and data["session_id"] != expected_session:
        raise LockError("commit manifest session_id mismatch")
    _safe_name(data["transaction_id"], "transaction_id")
    if data["target"] not in {"working", "delivery"}:
        raise LockError("commit manifest target is invalid")
    if not isinstance(data["stage"], str) or not data["stage"]:
        raise LockError("commit manifest stage is invalid")
    if isinstance(data["batch_index"], bool) or not isinstance(data["batch_index"], int) or data["batch_index"] < 1:
        raise LockError("commit manifest batch_index is invalid")
    if isinstance(data["master_generation"], bool) or not isinstance(data["master_generation"], int) or data["master_generation"] < 0:
        raise LockError("commit manifest master_generation is invalid")
    for key in ("master_sha256", "state_sha256"):
        value = data[key]
        if value and (not isinstance(value, str) or not _HASH_RE.fullmatch(value)):
            raise LockError(f"commit manifest {key} is invalid")
    try:
        datetime.fromisoformat(data["committed_at"])
    except (TypeError, ValueError) as exc:
        raise LockError("commit manifest committed_at is invalid") from exc
    fingerprints = data["implementation_fingerprints"]
    if not isinstance(fingerprints, dict) or any(
        not isinstance(key, str) or not _HASH_RE.fullmatch(value)
        for key, value in fingerprints.items()
    ):
        raise LockError("commit manifest implementation fingerprints are invalid")
    entries = data["entries"]
    if not isinstance(entries, list) or not entries:
        raise LockError("commit manifest entries are empty")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size"}:
            raise LockError("commit manifest entry fields are invalid")
        relative = _safe_relative(entry["path"], "manifest entry").as_posix()
        if relative.casefold() in seen:
            raise LockError("commit manifest contains duplicate paths")
        seen.add(relative.casefold())
        if not isinstance(entry["sha256"], str) or not _HASH_RE.fullmatch(entry["sha256"]):
            raise LockError("commit manifest entry hash is invalid")
        if isinstance(entry["size"], bool) or not isinstance(entry["size"], int) or entry["size"] < 0:
            raise LockError("commit manifest entry size is invalid")
    if data["manifest_sha256"] != _canonical_hash(data, "manifest_sha256"):
        raise LockError("commit manifest integrity hash mismatch")


def _read_manifest(path: Path, expected_session: str | None = None) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LockError(f"cannot read commit manifest: {exc}") from exc
    _validate_manifest_data(data, expected_session)
    return data


def _archive_path(session_dir: Path, data: dict[str, Any]) -> Path:
    return session_dir / "commits" / f"{data['target']}-{data['transaction_id']}.json"


def _archive_manifest(session_dir: Path, data: dict[str, Any]) -> Path:
    path = _archive_path(session_dir, data)
    _atomic_json(path, data)
    return path


def _verify_target(
    session_dir: Path,
    target: Path,
    logical_target: str | None = None,
    manifest_data: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if manifest_data is None:
        manifest_path = target / "COMMIT_MANIFEST.json"
        try:
            data = _read_manifest(manifest_path, session_dir.name)
        except LockError as exc:
            return False, [str(exc)]
    else:
        try:
            _validate_manifest_data(manifest_data, session_dir.name)
        except LockError as exc:
            return False, [str(exc)]
        data = manifest_data
    if data["target"] != (logical_target or target.name):
        issues.append("TARGET MISMATCH")
    expected = {entry["path"]: entry for entry in data["entries"]}
    actual: set[str] = set()
    if target.is_dir():
        for path in target.rglob("*"):
            if path.is_symlink():
                issues.append(f"SYMLINK: {path.relative_to(target).as_posix()}")
            elif path.is_file() and path.name != "COMMIT_MANIFEST.json":
                actual.add(path.relative_to(target).as_posix())
    for relative, entry in expected.items():
        file_path = target.joinpath(*PurePosixPath(relative).parts)
        if not file_path.is_file():
            issues.append(f"MISSING: {relative}")
            continue
        if file_path.stat().st_size != entry["size"]:
            issues.append(f"SIZE MISMATCH: {relative}")
        if _sha256(file_path) != entry["sha256"]:
            issues.append(f"HASH MISMATCH: {relative}")
    for relative in sorted(actual - set(expected)):
        issues.append(f"UNTRACKED: {relative}")
    return not issues, issues


def _pending_path(session_dir: Path) -> Path:
    return session_dir / ".COMMIT_PENDING.json"


def _recover_unlocked(session_dir: Path) -> None:
    pending_path = _pending_path(session_dir)
    if not pending_path.exists():
        return
    try:
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LockError(f"cannot recover malformed pending commit: {exc}") from exc
    legacy_fields = {"schema_version", "transaction_id", "target", "backup"}
    current_fields = legacy_fields | {"previous_manifest"}
    if (
        not isinstance(pending, dict)
        or set(pending) not in (legacy_fields, current_fields)
        or pending.get("schema_version") not in {"1.0", "1.1"}
    ):
        raise LockError("cannot recover malformed pending commit")
    transaction_id = _safe_name(pending["transaction_id"], "transaction_id")
    if pending["target"] not in {"working", "delivery"}:
        raise LockError("pending commit target is invalid")
    target = session_dir / pending["target"]
    expected_backup = f".{pending['target']}.backup-{transaction_id}"
    if pending["backup"] != expected_backup:
        raise LockError("pending commit backup name is invalid")
    backup = session_dir / expected_backup

    # Prefer a fully published new transaction. Delivery may already have had
    # its internal manifest removed, in which case the root pointer is enough.
    new_data: dict[str, Any] | None = None
    internal_path = target / "COMMIT_MANIFEST.json"
    if internal_path.is_file():
        candidate = _read_manifest(internal_path, session_dir.name)
        if candidate["transaction_id"] == transaction_id:
            new_data = candidate
    elif target.is_dir() and (session_dir / "COMMIT_MANIFEST.json").is_file():
        candidate = _read_manifest(
            session_dir / "COMMIT_MANIFEST.json", session_dir.name
        )
        if candidate["transaction_id"] == transaction_id:
            new_data = candidate
    target_ok, _ = (
        _verify_target(session_dir, target, manifest_data=new_data)
        if target.is_dir() and new_data is not None else (False, [])
    )
    if target_ok and new_data is not None:
        _atomic_json(session_dir / "COMMIT_MANIFEST.json", new_data)
        _archive_manifest(session_dir, new_data)
        if new_data["target"] == "delivery":
            internal_path.unlink(missing_ok=True)
        if backup.exists():
            shutil.rmtree(backup)
        pending_path.unlink(missing_ok=True)
        return

    # Schema 1.1 preserves the exact previous manifest, so a delivery without
    # internal metadata can still be restored after a crash.
    previous = pending.get("previous_manifest")
    if previous is not None:
        _validate_manifest_data(previous, session_dir.name)
        for candidate_path in (backup, target):
            if not candidate_path.is_dir():
                continue
            previous_ok, _ = _verify_target(
                session_dir, candidate_path, pending["target"], previous
            )
            if not previous_ok:
                continue
            if candidate_path == backup:
                if target.exists():
                    shutil.rmtree(target)
                backup.replace(target)
            _atomic_json(session_dir / "COMMIT_MANIFEST.json", previous)
            _archive_manifest(session_dir, previous)
            if previous["target"] == "delivery":
                (target / "COMMIT_MANIFEST.json").unlink(missing_ok=True)
            pending_path.unlink(missing_ok=True)
            return

    # Backward-compatible recovery for old working commits.
    if backup.is_dir():
        backup_ok, backup_issues = _verify_target(
            session_dir, backup, pending["target"]
        )
        if not backup_ok:
            raise LockError(f"both commit target and backup are invalid: {backup_issues}")
        if target.exists():
            shutil.rmtree(target)
        backup.replace(target)
        restored = _read_manifest(target / "COMMIT_MANIFEST.json", session_dir.name)
        _atomic_json(session_dir / "COMMIT_MANIFEST.json", restored)
        _archive_manifest(session_dir, restored)
        pending_path.unlink(missing_ok=True)
        return
    raise LockError("pending commit has neither a valid target nor a valid backup")


def recover(session_dir: Path) -> None:
    """Recover an interrupted directory switch, if one exists."""
    with session_lock(session_dir):
        _recover_unlocked(session_dir)


def _select_transaction(session_dir: Path, transaction_id: str | None) -> tuple[str, Path]:
    if transaction_id is not None:
        transaction_id = _safe_name(transaction_id, "transaction_id")
        transaction = staging_dir(session_dir, transaction_id)
        if not transaction.is_dir():
            raise LockError(f"staging transaction not found: {transaction_id}")
        return transaction_id, transaction
    root = staging_dir(session_dir)
    candidates = sorted(path for path in root.iterdir() if path.is_dir()) if root.is_dir() else []
    if len(candidates) != 1:
        raise LockError("transaction_id is required unless exactly one staged transaction exists")
    return _safe_name(candidates[0].name, "transaction_id"), candidates[0]


def commit(
    session_dir: Path,
    stage_name: str,
    batch_index: int,
    transaction_id: str | None = None,
    *,
    target: str = "working",
) -> CommitManifest:
    """Verify and atomically publish one staged transaction directory."""
    if not isinstance(stage_name, str) or not stage_name.strip():
        raise LockError("stage_name cannot be empty")
    if isinstance(batch_index, bool) or not isinstance(batch_index, int) or batch_index < 1:
        raise LockError("batch_index must be a positive integer")
    if target not in {"working", "delivery"}:
        raise LockError("target must be working or delivery")

    with session_lock(session_dir):
        _recover_unlocked(session_dir)
        transaction_id, transaction = _select_transaction(session_dir, transaction_id)
        state, generation, master_hash, state_hash = _state_metadata(session_dir)
        entries = _transaction_files(transaction)
        manifest = CommitManifest(
            schema_version=COMMIT_SCHEMA_VERSION,
            session_id=session_dir.name,
            transaction_id=transaction_id,
            target=target,
            stage=stage_name.strip(),
            batch_index=batch_index,
            committed_at=datetime.now(timezone.utc).isoformat(),
            master_generation=generation,
            master_sha256=master_hash,
            state_sha256=state_hash,
            implementation_fingerprints=_implementation_fingerprints(state),
            entries=entries,
        )
        data = _manifest_data(manifest)
        _validate_manifest_data(data, session_dir.name)
        _atomic_json(transaction / "COMMIT_MANIFEST.json", data)

        destination = session_dir / target
        backup_name = f".{target}.backup-{transaction_id}"
        backup = session_dir / backup_name
        if backup.exists():
            raise LockError(f"commit backup already exists: {backup}")
        previous_manifest: dict[str, Any] | None = None
        root_manifest = session_dir / "COMMIT_MANIFEST.json"
        if destination.is_dir() and root_manifest.is_file():
            candidate = _read_manifest(root_manifest, session_dir.name)
            if candidate["target"] == target:
                previous_ok, previous_issues = _verify_target(
                    session_dir, destination, target, candidate
                )
                if not previous_ok:
                    raise LockError(
                        f"existing target is not a valid commit: {previous_issues}"
                    )
                previous_manifest = candidate
        pending = {
            "schema_version": "1.1",
            "transaction_id": transaction_id,
            "target": target,
            "backup": backup_name,
            "previous_manifest": previous_manifest,
        }
        _atomic_json(_pending_path(session_dir), pending)
        try:
            if destination.exists():
                destination.replace(backup)
            transaction.replace(destination)
            ok, issues = _verify_target(session_dir, destination)
            if not ok:
                raise LockError(f"published commit failed verification: {issues}")
            _atomic_json(session_dir / "COMMIT_MANIFEST.json", data)
            _archive_manifest(session_dir, data)
            if target == "delivery":
                (destination / "COMMIT_MANIFEST.json").unlink(missing_ok=True)
                ok, issues = _verify_target(
                    session_dir, destination, manifest_data=data
                )
                if not ok:
                    raise LockError(
                        f"manifest-free delivery failed verification: {issues}"
                    )
        except Exception:
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            if backup.exists():
                backup.replace(destination)
            if previous_manifest is not None:
                _atomic_json(
                    session_dir / "COMMIT_MANIFEST.json", previous_manifest
                )
                _archive_manifest(session_dir, previous_manifest)
                if previous_manifest["target"] == "delivery":
                    (destination / "COMMIT_MANIFEST.json").unlink(missing_ok=True)
            else:
                (session_dir / "COMMIT_MANIFEST.json").unlink(missing_ok=True)
            _pending_path(session_dir).unlink(missing_ok=True)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        _pending_path(session_dir).unlink(missing_ok=True)
        root = staging_dir(session_dir)
        if root.is_dir() and not any(root.iterdir()):
            root.rmdir()
        return manifest


def verify_commit(session_dir: Path, target: str | None = None) -> tuple[bool, list[str]]:
    """Verify the selected committed directory and its root manifest pointer."""
    try:
        root_data = _read_manifest(session_dir / "COMMIT_MANIFEST.json", session_dir.name)
    except LockError as exc:
        return False, [str(exc)]
    selected = target or root_data["target"]
    if selected not in {"working", "delivery"}:
        return False, ["invalid target"]
    if root_data["target"] != selected:
        return False, ["root manifest target mismatch"]
    destination = session_dir / selected
    ok, issues = _verify_target(
        session_dir, destination, manifest_data=root_data
    )
    if not ok:
        return False, issues
    if selected == "working":
        try:
            internal = _read_manifest(
                destination / "COMMIT_MANIFEST.json", session_dir.name
            )
        except LockError as exc:
            return False, [str(exc)]
        if internal != root_data:
            return False, ["root and committed manifests differ"]
    else:
        if (destination / "COMMIT_MANIFEST.json").exists():
            return False, ["delivery exposes internal commit metadata"]
        try:
            archived = _read_manifest(
                _archive_path(session_dir, root_data), session_dir.name
            )
        except LockError as exc:
            return False, [str(exc)]
        if archived != root_data:
            return False, ["root and archived delivery manifests differ"]
    return True, []


def rollback(session_dir: Path) -> None:
    """Recover any interrupted switch and discard uncommitted transactions."""
    with session_lock(session_dir):
        _recover_unlocked(session_dir)
        root = staging_dir(session_dir)
        if root.exists():
            shutil.rmtree(root)


def main() -> int:
    parser = argparse.ArgumentParser(description="MODE:P crash-safe session commits.")
    sub = parser.add_subparsers(dest="command", required=True)
    lock_parser = sub.add_parser("lock")
    lock_parser.add_argument("session", type=Path)
    stage_parser = sub.add_parser("stage")
    stage_parser.add_argument("session", type=Path)
    stage_parser.add_argument("files", nargs="+", help="source=relative_destination")
    stage_parser.add_argument("--transaction")
    commit_parser = sub.add_parser("commit")
    commit_parser.add_argument("session", type=Path)
    commit_parser.add_argument("--stage-name", default="director_batch")
    commit_parser.add_argument("--batch", type=int, default=1)
    commit_parser.add_argument("--transaction")
    commit_parser.add_argument("--target", choices=("working", "delivery"), default="working")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("session", type=Path)
    verify_parser.add_argument("--target", choices=("working", "delivery"))
    recover_parser = sub.add_parser("recover")
    recover_parser.add_argument("session", type=Path)
    rollback_parser = sub.add_parser("rollback")
    rollback_parser.add_argument("session", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "lock":
            with session_lock(args.session):
                print("Lock acquired.")
        elif args.command == "stage":
            files: dict[str, Path] = {}
            for pair in args.files:
                source, destination = pair.split("=", 1)
                files[destination] = Path(source)
            path = prepare_staging(args.session, files, args.transaction)
            print(path.name)
        elif args.command == "commit":
            manifest = commit(
                args.session, args.stage_name, args.batch, args.transaction,
                target=args.target,
            )
            print(f"Committed {manifest.total_files} file(s) to {manifest.target}.")
        elif args.command == "verify":
            ok, issues = verify_commit(args.session, args.target)
            if not ok:
                print("\n".join(issues), file=sys.stderr)
                return 1
            print("Commit verified.")
        elif args.command == "recover":
            recover(args.session)
            print("Recovery complete.")
        else:
            rollback(args.session)
            print("Rollback complete.")
    except (LockError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
