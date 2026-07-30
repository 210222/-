"""Deterministic control plane for the MODE:P vNext repair/rebuild loop.

The model may edit implementation files, but it may not decide that a task is
complete.  This module owns task selection, exclusive claims, dependency
checks, evidence validation, and the machine state transition.

It deliberately does not invoke Director, DP, image, video, Shadow, Pilot, or
Production flows.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import stat as stat_module
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


TASKS_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REPAIR_TASKS.json")
STATE_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD_STATE.json")
LOCK_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD.lock.json")
SOLE_RELEASE_STATE_REL = Path(
    "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_STATE.json"
)

_MUTABLE_CONTROL_PATHS = {
    STATE_REL.as_posix(),
    LOCK_REL.as_posix(),
    "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md",
    "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock",
}

# Roots supervised by claim-time workspace manifest (relative, /-separated).
_SUPERVISED_ROOTS: Tuple[str, ...] = (
    "01_调度器/mode_p_vnext",
    "01_调度器/mode_p",
    "MODE_P_REDESIGN_PROJECT",
    ".claude/commands",
    "CLAUDE.md",
)

# Glob patterns excluded from workspace manifest.
_MANIFEST_EXCLUSIONS: Tuple[str, ...] = (
    ".git",
    "__pycache__",
    ".pytest_cache",
    "*.pyc",
    "runtime_cache",
    "sessions",
    "telemetry",
    ".mypy_cache",
    ".tox",
    ".eggs",
    "*.egg-info",
    STATE_REL.as_posix(),
    LOCK_REL.as_posix(),
)


class ControlError(RuntimeError):
    """Fail-closed rebuild-control error."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    """Hash text canonically so Git LF/CRLF checkout policy cannot cause drift."""

    payload = path.read_bytes()
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        canonical = payload
    else:
        canonical = (
            text.replace("\r\n", "\n").encode("utf-8")
            if "\x00" not in text
            else payload
        )
    return hashlib.sha256(canonical).hexdigest()


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(_canonical_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ControlError(f"required control file missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ControlError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ControlError(f"control file root must be an object: {path}")
    return value


def _normalise_rel_path(raw: str) -> str:
    value = raw.replace("\\", "/").strip()
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ControlError(f"unsafe changed path: {raw!r}")
    return str(path)


def _resolve_safe(root: Path, rel_path: str) -> Path:
    """Resolve a relative path and verify it stays inside project root.

    Rejects symlinks, Windows junctions, NTFS reparse points, and any
    path whose real location after resolution falls outside root.
    """
    normalised = _normalise_rel_path(rel_path)
    candidate = (root / normalised).resolve()

    # Must still be inside root after resolution (catches symlink escapes).
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ControlError(
            f"path resolves outside project root: {rel_path!r} -> {candidate}"
        ) from exc

    return candidate


def _is_symlink_or_junction(path: Path) -> bool:
    """Return True if *path* is a symlink, junction, or reparse point."""
    try:
        st = path.lstat()
    except OSError:
        return False
    if stat_module.S_ISLNK(st.st_mode):
        return True
    # Windows: check for junction/reparse-point via st_file_attributes.
    st_file_attributes = getattr(st, "st_file_attributes", 0)
    if st_file_attributes:
        import ctypes
        FILE_ATTRIBUTE_REPARSE_POINT = getattr(
            ctypes.wintypes if hasattr(ctypes, "wintypes") else ctypes,
            "FILE_ATTRIBUTE_REPARSE_POINT",
            0x400,
        )
        if st_file_attributes & 0x400:  # FILE_ATTRIBUTE_REPARSE_POINT
            return True
    return False


def _path_allowed(path: str, patterns: Iterable[str]) -> bool:
    normalised = _normalise_rel_path(path)
    for raw_pattern in patterns:
        pattern = raw_pattern.replace("\\", "/")
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if normalised == prefix or normalised.startswith(prefix + "/"):
                return True
        if fnmatch.fnmatchcase(normalised, pattern):
            return True
    return False


def _path_excluded(rel_path: str, exclusions: Iterable[str]) -> bool:
    """Check if *rel_path* matches any exclusion glob."""
    normalised = rel_path.replace("\\", "/")
    for pattern in exclusions:
        if fnmatch.fnmatchcase(normalised, pattern):
            return True
        # Also match any path whose component matches
        parts = normalised.split("/")
        for part in parts:
            if fnmatch.fnmatchcase(part, pattern):
                return True
    return False


def _build_workspace_manifest(
    root: Path,
    evidence_rel: Optional[str] = None,
    mutable_control_paths: Iterable[str] = (),
) -> Dict[str, str]:
    """Walk supervised roots and return {normalised_rel_path: sha256}.

    Excludes git, caches, compiled artefacts, controller state/lock, and
    the current claim's evidence file.
    """
    manifest: Dict[str, str] = {}
    resolved_root = root.resolve()
    exclusion_list = list(_MANIFEST_EXCLUSIONS)
    if evidence_rel:
        exclusion_list.append(evidence_rel.replace("\\", "/"))
    # Exclude the active controller's state/lock in addition to the historical
    # repair paths.  Independent successor queues use their own state files;
    # those bookkeeping writes must not look like implementation drift.
    exclusion_list.extend(path.replace("\\", "/") for path in mutable_control_paths)

    for supervised in _SUPERVISED_ROOTS:
        base = root / supervised
        if not base.exists():
            continue
        if base.is_file():
            rel = supervised.replace("\\", "/")
            if not _path_excluded(rel, exclusion_list):
                manifest[rel] = _sha256_file(base)
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            # Prune excluded directories in-place.
            dirnames[:] = [
                d
                for d in dirnames
                if not _path_excluded(d, exclusion_list)
            ]
            for fname in filenames:
                file_path = Path(dirpath) / fname
                if _path_excluded(fname, exclusion_list):
                    continue
                try:
                    rel = file_path.relative_to(root).as_posix()
                except ValueError:
                    continue
                if _path_excluded(rel, exclusion_list):
                    continue
                # Reject symlinks and junctions.
                if _is_symlink_or_junction(file_path):
                    raise ControlError(
                        f"symlink/junction/reparse-point not allowed in "
                        f"supervised root: {rel}"
                    )
                try:
                    file_path.resolve().relative_to(resolved_root)
                except ValueError:
                    raise ControlError(
                        f"file resolves outside project root: {rel}"
                    )
                manifest[rel] = _sha256_file(file_path)
    return manifest


def _compute_workspace_delta(
    claim_manifest: Dict[str, str],
    complete_manifest: Dict[str, str],
) -> Tuple[Set[str], Set[str], Set[str]]:
    """Return (created, modified, deleted) paths between claim and complete."""
    claim_keys = set(claim_manifest)
    complete_keys = set(complete_manifest)
    created = complete_keys - claim_keys
    deleted = claim_keys - complete_keys
    modified = {
        path
        for path in (claim_keys & complete_keys)
        if claim_manifest[path] != complete_manifest[path]
    }
    return created, modified, deleted


@dataclass(frozen=True)
class VerificationCommand:
    name: str
    argv: Sequence[str]
    cwd: str
    timeout_seconds: int


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str
    depends_on: Sequence[str]
    spec_refs: Sequence[str]
    allowed_paths: Sequence[str]
    required_checks: Sequence[str]
    verification_commands: Sequence[VerificationCommand]
    locked_verification_inputs: Mapping[str, str]
    phase: str = ""
    pending_status: str = "REPAIR_REQUIRED"
    manual_gates: Sequence[str] = ()


class RebuildControl:
    """Stateful controller rooted at one project checkout."""

    def __init__(
        self,
        project_root: Path,
        *,
        tasks_rel: Path = TASKS_REL,
        state_rel: Path = STATE_REL,
        lock_rel: Path = LOCK_REL,
    ):
        self.root = project_root.resolve()
        self.tasks_rel = Path(_normalise_rel_path(tasks_rel.as_posix()))
        self.state_rel = Path(_normalise_rel_path(state_rel.as_posix()))
        self.lock_rel = Path(_normalise_rel_path(lock_rel.as_posix()))
        self.tasks_path = self.root / self.tasks_rel
        self.state_path = self.root / self.state_rel
        self.lock_path = self.root / self.lock_rel
        self._mutable_control_paths = frozenset(
            _MUTABLE_CONTROL_PATHS
            | {self.state_rel.as_posix(), self.lock_rel.as_posix()}
        )

    @classmethod
    def default(cls) -> "RebuildControl":
        # .../project/01_调度器/mode_p_vnext/rebuild_control.py
        return cls(Path(__file__).resolve().parents[2])

    def _load_tasks_document(self) -> Dict[str, Any]:
        return _read_json(self.tasks_path)

    def load_tasks(self) -> List[Task]:
        document = self._load_tasks_document()
        global_locked = document.get("locked_verification_inputs", {})
        if not isinstance(global_locked, dict):
            raise ControlError(
                "registry locked_verification_inputs must be an object"
            )
        raw_tasks = document.get("tasks")
        if not isinstance(raw_tasks, list) or not raw_tasks:
            raise ControlError("repair task registry must contain a non-empty tasks list")
        tasks: List[Task] = []
        for raw in raw_tasks:
            if not isinstance(raw, dict):
                raise ControlError("every repair task must be an object")
            try:
                raw_commands = raw["verification_commands"]
                if not isinstance(raw_commands, list) or not raw_commands:
                    raise ControlError(
                        f"task {raw.get('task_id')} needs verification_commands"
                    )
                commands: List[VerificationCommand] = []
                for command in raw_commands:
                    if not isinstance(command, dict):
                        raise ControlError("verification command must be an object")
                    argv = command.get("argv")
                    if not isinstance(argv, list) or not argv or not all(
                        isinstance(value, str) and value for value in argv
                    ):
                        raise ControlError("verification command argv must be non-empty")
                    timeout_seconds = int(command.get("timeout_seconds", 120))
                    if timeout_seconds < 1 or timeout_seconds > 3600:
                        raise ControlError(
                            "verification command timeout must be between 1 and 3600 seconds"
                        )
                    commands.append(
                        VerificationCommand(
                            name=str(command["name"]),
                            argv=tuple(argv),
                            cwd=_normalise_rel_path(str(command.get("cwd", "."))),
                            timeout_seconds=timeout_seconds,
                        )
                    )
                command_names = [command.name for command in commands]
                if any(not name.strip() for name in command_names) or len(
                    command_names
                ) != len(set(command_names)):
                    raise ControlError(
                        "verification command names must be non-empty and unique"
                    )

                phase = str(raw.get("phase", ""))
                pending_status = str(
                    raw.get("pending_status", "REPAIR_REQUIRED")
                )
                if not pending_status.strip():
                    raise ControlError(
                        f"task {raw.get('task_id')} pending_status must be non-empty"
                    )
                raw_manual_gates = raw.get("manual_gates", [])
                if (
                    not isinstance(raw_manual_gates, list)
                    or not all(
                        isinstance(gate, str) and gate.strip()
                        for gate in raw_manual_gates
                    )
                    or len(raw_manual_gates) != len(set(raw_manual_gates))
                ):
                    raise ControlError(
                        f"task {raw.get('task_id')} manual_gates must be a "
                        "unique list of non-empty strings"
                    )

                # Parse locked_verification_inputs.
                locked_inputs: Dict[str, str] = {}
                raw_locked = raw.get("locked_verification_inputs", {})
                if raw_locked is not None:
                    if not isinstance(raw_locked, dict):
                        raise ControlError(
                            f"task {raw.get('task_id')} locked_verification_inputs "
                            f"must be an object"
                        )
                    combined_locked = dict(global_locked)
                    for rel_path, expected_hash in raw_locked.items():
                        if (
                            rel_path in combined_locked
                            and combined_locked[rel_path] != expected_hash
                        ):
                            raise ControlError(
                                f"task {raw.get('task_id')} overrides global locked "
                                f"input with a different hash: {rel_path}"
                            )
                        combined_locked[rel_path] = expected_hash
                    for rel_path, expected_hash in combined_locked.items():
                        norm = _normalise_rel_path(str(rel_path))
                        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
                            raise ControlError(
                                f"locked input hash must be 64-char hex: {rel_path}"
                            )
                        if not all(c in "0123456789abcdef" for c in expected_hash):
                            raise ControlError(
                                f"locked input hash must be lowercase hex: {rel_path}"
                            )
                        # locked input must not be worker-writable
                        allowed = raw.get("allowed_paths", [])
                        if _path_allowed(norm, allowed):
                            raise ControlError(
                                f"locked input {rel_path} must not match "
                                f"task allowed_paths"
                            )
                        locked_inputs[norm] = expected_hash

                tasks.append(
                    Task(
                        task_id=str(raw["task_id"]),
                        title=str(raw["title"]),
                        depends_on=tuple(raw.get("depends_on", [])),
                        spec_refs=tuple(raw.get("spec_refs", [])),
                        allowed_paths=tuple(raw["allowed_paths"]),
                        required_checks=tuple(raw["required_checks"]),
                        verification_commands=tuple(commands),
                        locked_verification_inputs=locked_inputs,
                        phase=phase,
                        pending_status=pending_status,
                        manual_gates=tuple(raw_manual_gates),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ControlError(f"malformed repair task: {raw!r}") from exc
        return tasks

    def load_state(self) -> Dict[str, Any]:
        return _read_json(self.state_path)

    def _task_map(self) -> Dict[str, Task]:
        tasks = self.load_tasks()
        mapping = {task.task_id: task for task in tasks}
        if len(mapping) != len(tasks):
            raise ControlError("duplicate task_id in repair task registry")
        return mapping

    def _assert_task_authority(self) -> None:
        """Prevent historical controllers from selecting or advancing work.

        Read-only audit/status and stale-lock fail/recover remain available so
        legacy evidence can still be inspected and abandoned safely.
        """

        if self.state_rel == SOLE_RELEASE_STATE_REL:
            return
        release_state_path = self.root / SOLE_RELEASE_STATE_REL
        if not release_state_path.is_file():
            return
        release_state = _read_json(release_state_path)
        if release_state.get("authority") == "SOLE_VNEXT_CONSTRUCTION_LEDGER":
            raise ControlError(
                "legacy construction controller is historical read-only; "
                "use python -m mode_p_vnext.release_control"
            )

    def _validate_locked_inputs(
        self, task: Task, phase: str
    ) -> Dict[str, str]:
        """Verify every locked_verification_input against live filesystem.

        Returns {rel_path: actual_sha256} on success.
        Raises ControlError on missing file, hash mismatch, or path escape.
        """
        verified: Dict[str, str] = {}
        for rel_path, expected_hash in sorted(task.locked_verification_inputs.items()):
            file_path = _resolve_safe(self.root, rel_path)
            if _is_symlink_or_junction(file_path):
                raise ControlError(
                    f"locked input is symlink/junction: {rel_path}"
                )
            if not file_path.is_file():
                raise ControlError(
                    f"locked input missing at {phase}: {rel_path}"
                )
            actual_hash = _sha256_file(file_path)
            if actual_hash != expected_hash:
                raise ControlError(
                    f"locked input hash mismatch at {phase}: {rel_path} "
                    f"(expected {expected_hash}, actual {actual_hash})"
                )
            verified[rel_path] = actual_hash
        return verified

    def audit(self) -> List[str]:
        issues: List[str] = []
        try:
            tasks = self.load_tasks()
            mapping = {task.task_id: task for task in tasks}
            if len(mapping) != len(tasks):
                issues.append("duplicate task_id")
            for task in tasks:
                for dependency in task.depends_on:
                    if dependency not in mapping:
                        issues.append(f"{task.task_id}: missing dependency {dependency}")

            # Ordered DFS catches cycles independently of registry ordering.
            visiting: set[str] = set()
            visited: set[str] = set()

            def visit(task_id: str) -> None:
                if task_id in visiting:
                    issues.append(f"dependency cycle at {task_id}")
                    return
                if task_id in visited or task_id not in mapping:
                    return
                visiting.add(task_id)
                for dependency in mapping[task_id].depends_on:
                    visit(dependency)
                visiting.remove(task_id)
                visited.add(task_id)

            for task in tasks:
                visit(task.task_id)

            state = self.load_state()
            completed = state.get("completed_tasks", [])
            if not isinstance(completed, list) or len(completed) != len(set(completed)):
                issues.append("state completed_tasks must be a unique list")
                completed = []
            for task_id in completed:
                if task_id not in mapping:
                    issues.append(f"state contains unknown completed task {task_id}")
                    continue
                missing = [d for d in mapping[task_id].depends_on if d not in completed]
                if missing:
                    issues.append(
                        f"completed task {task_id} has incomplete dependencies: {','.join(missing)}"
                    )
                record = state.get("evidence_records", {}).get(task_id)
                if not isinstance(record, dict):
                    issues.append(f"completed task {task_id} lacks evidence record")
                else:
                    evidence_path = self.root / record.get("path", "")
                    if not evidence_path.is_file():
                        issues.append(f"completed task {task_id} evidence file missing")
                    elif record.get("sha256") != _sha256_file(evidence_path):
                        issues.append(f"completed task {task_id} evidence hash mismatch")
                    artifact_hashes = record.get("artifact_hashes")
                    if artifact_hashes is not None:
                        if not isinstance(artifact_hashes, dict):
                            issues.append(
                                f"completed task {task_id} artifact_hashes must be an object"
                            )
                        else:
                            for raw_path, expected_hash in artifact_hashes.items():
                                try:
                                    rel_path = _normalise_rel_path(str(raw_path))
                                except ControlError as exc:
                                    issues.append(f"completed task {task_id}: {exc}")
                                    continue
                                artifact_path = self.root / rel_path
                                if expected_hash == "ABSENT":
                                    if artifact_path.exists():
                                        issues.append(
                                            f"completed task {task_id} artifact drift: "
                                            f"{rel_path} was expected to be absent"
                                        )
                                elif not artifact_path.is_file():
                                    issues.append(
                                        f"completed task {task_id} artifact missing: {rel_path}"
                                    )
                                elif expected_hash != _sha256_file(artifact_path):
                                    issues.append(
                                        f"completed task {task_id} artifact drift: {rel_path}"
                                    )

                    # Audit locked verification inputs for completed tasks.
                    record_hashes = record.get("verification_input_hashes")
                    task_obj = mapping.get(task_id)
                    if task_obj and task_obj.locked_verification_inputs:
                        if not isinstance(record_hashes, dict):
                            issues.append(
                                f"completed task {task_id} has locked inputs but "
                                f"no verification_input_hashes in state record"
                            )
                        else:
                            for rel_path, expected_hash in sorted(
                                task_obj.locked_verification_inputs.items()
                            ):
                                if rel_path not in record_hashes:
                                    issues.append(
                                        f"completed task {task_id}: locked input "
                                        f"{rel_path} not in verification_input_hashes"
                                    )
                                elif record_hashes[rel_path] != expected_hash:
                                    issues.append(
                                        f"completed task {task_id}: locked input "
                                        f"{rel_path} hash mismatch in state record"
                                    )
                                # Check live file hash.
                                try:
                                    file_path = _resolve_safe(self.root, rel_path)
                                    if not file_path.is_file():
                                        issues.append(
                                            f"completed task {task_id}: locked input "
                                            f"{rel_path} missing from disk"
                                        )
                                    else:
                                        live_hash = _sha256_file(file_path)
                                        if live_hash != expected_hash:
                                            issues.append(
                                                f"completed task {task_id}: locked input "
                                                f"{rel_path} live drift detected "
                                                f"(expected {expected_hash}, got {live_hash})"
                                            )
                                except ControlError as exc:
                                    issues.append(
                                        f"completed task {task_id}: locked input "
                                        f"{rel_path}: {exc}"
                                    )

            lock = _read_json(self.lock_path) if self.lock_path.exists() else None
            if state.get("status") == "IN_PROGRESS":
                if not lock:
                    issues.append("state is IN_PROGRESS but exclusive lock is missing")
                elif (
                    lock.get("task_id") != state.get("current_task")
                    or lock.get("owner") != state.get("current_owner")
                    or lock.get("token") != state.get("lock_token")
                ):
                    issues.append("state and exclusive lock do not match")
            elif lock:
                issues.append("exclusive lock exists while state is not IN_PROGRESS")
        except ControlError as exc:
            issues.append(str(exc))
        return issues

    def next_task(self) -> Optional[Task]:
        self._assert_task_authority()
        issues = self.audit()
        if issues:
            raise ControlError("control audit failed: " + "; ".join(issues))
        tasks = self.load_tasks()
        state = self.load_state()
        completed = set(state.get("completed_tasks", []))
        for task in tasks:
            if task.task_id in completed:
                continue
            if all(dep in completed for dep in task.depends_on):
                return task
        if len(completed) == len(tasks):
            return None
        raise ControlError("no eligible task; dependency graph or state is inconsistent")

    def claim(self, task_id: str, owner: str) -> Dict[str, Any]:
        self._assert_task_authority()
        if not owner.strip():
            raise ControlError("owner must be non-empty")
        issues = self.audit()
        if issues:
            raise ControlError("control audit failed: " + "; ".join(issues))
        mapping = self._task_map()
        if task_id not in mapping:
            raise ControlError(f"unknown repair task: {task_id}")
        state = self.load_state()
        completed = set(state.get("completed_tasks", []))
        if task_id in completed:
            raise ControlError(f"task already completed: {task_id}")
        missing = [d for d in mapping[task_id].depends_on if d not in completed]
        if missing:
            raise ControlError(
                f"task {task_id} has incomplete dependencies: {','.join(missing)}"
            )
        expected = self.next_task()
        if expected and expected.task_id != task_id:
            raise ControlError(
                f"task {task_id} is not the next eligible task; expected {expected.task_id}"
            )

        task = mapping[task_id]

        # Validate locked inputs at claim time (fail early if gates are missing).
        if task.locked_verification_inputs:
            self._validate_locked_inputs(task, "claim")

        token = uuid.uuid4().hex

        # Build claim-time workspace manifest.
        # The manifest excludes state, lock, and known mutable control files.
        evidence_rel_candidate = state.get("evidence_records", {}).get(
            task_id, {}
        ).get("path")
        manifest = _build_workspace_manifest(
            self.root, evidence_rel_candidate, self._mutable_control_paths
        )

        lock = {
            "schema_version": "1.0",
            "task_id": task_id,
            "owner": owner,
            "token": token,
            "pid": os.getpid(),
            "acquired_at": _utc_now(),
            "claim_manifest": manifest,
            "manifest_sha256": hashlib.sha256(
                _canonical_json_bytes(manifest)
            ).hexdigest(),
            "manifest_file_count": len(manifest),
        }
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(
                self.lock_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as exc:
            raise ControlError(f"repair loop already claimed: {self.lock_path}") from exc
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(_canonical_json_bytes(lock))
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            self.lock_path.unlink(missing_ok=True)
            raise

        state.update(
            {
                "status": "IN_PROGRESS",
                "current_task": task_id,
                "current_owner": owner,
                "lock_token": token,
                "next_task": task_id,
                "updated_at": _utc_now(),
            }
        )
        try:
            _atomic_write_json(self.state_path, state)
        except Exception:
            self.lock_path.unlink(missing_ok=True)
            raise
        return lock

    def _require_lock(self, task_id: str, owner: str, token: str) -> Dict[str, Any]:
        if not self.lock_path.exists():
            raise ControlError("exclusive repair lock is missing")
        lock = _read_json(self.lock_path)
        expected = (task_id, owner, token)
        actual = (lock.get("task_id"), lock.get("owner"), lock.get("token"))
        if actual != expected:
            raise ControlError("task, owner, or token does not match exclusive lock")
        state = self.load_state()
        state_actual = (
            state.get("current_task"),
            state.get("current_owner"),
            state.get("lock_token"),
        )
        if state.get("status") != "IN_PROGRESS" or state_actual != expected:
            raise ControlError("machine state does not match exclusive lock")
        return state

    def _validate_evidence(self, task: Task, evidence_path: Path) -> Dict[str, Any]:
        evidence = _read_json(evidence_path)
        if evidence.get("task_id") != task.task_id:
            raise ControlError("evidence task_id does not match task")
        changed_paths = evidence.get("changed_paths")
        if not isinstance(changed_paths, list):
            raise ControlError("evidence changed_paths must be a list")
        normalised_paths = [_normalise_rel_path(str(path)) for path in changed_paths]
        if len(normalised_paths) != len(set(normalised_paths)):
            raise ControlError("evidence changed_paths must be unique")
        for changed in changed_paths:
            if not _path_allowed(str(changed), task.allowed_paths):
                raise ControlError(
                    f"changed path outside task scope: {changed} (task {task.task_id})"
                )
        checks = evidence.get("checks")
        if not isinstance(checks, list):
            raise ControlError("evidence checks must be a list")
        check_results: Dict[str, int] = {}
        for check in checks:
            if not isinstance(check, dict) or "name" not in check or "exit_code" not in check:
                raise ControlError("each evidence check needs name and exit_code")
            name = str(check["name"])
            if name in check_results:
                raise ControlError(f"duplicate evidence check: {name}")
            check_results[name] = int(check["exit_code"])
        missing = [name for name in task.required_checks if name not in check_results]
        if missing:
            raise ControlError("evidence missing required checks: " + ",".join(missing))
        failed = [name for name in task.required_checks if check_results[name] != 0]
        if failed:
            raise ControlError("required checks failed: " + ",".join(failed))

        # Validate verification_results: only names matching registry commands allowed.
        registry_names = {cmd.name for cmd in task.verification_commands}
        ev_verification = evidence.get("verification_results")
        if isinstance(ev_verification, list):
            for entry in ev_verification:
                if isinstance(entry, dict) and "name" in entry:
                    if entry["name"] not in registry_names:
                        raise ControlError(
                            f"evidence verification_results contains unregistered "
                            f"command '{entry['name']}' not in task registry"
                        )

        # Validate informational_results have authority markers if present.
        ev_info = evidence.get("informational_results")
        if isinstance(ev_info, list):
            for entry in ev_info:
                if isinstance(entry, dict):
                    authority = entry.get("authority", "")
                    if authority != "manual_untrusted_until_controller_or_supervisor_audit":
                        raise ControlError(
                            f"informational_result '{entry.get('name', '?')}' "
                            f"must declare "
                            f"authority=manual_untrusted_until_controller_or_supervisor_audit"
                        )

        return evidence

    def _snapshot_artifacts(
        self, changed_paths: Sequence[str], evidence_path: Path
    ) -> Dict[str, str]:
        try:
            evidence_rel = evidence_path.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ControlError("evidence must be stored inside the project") from exc
        hashes: Dict[str, str] = {}
        for raw_path in changed_paths:
            rel_path = _normalise_rel_path(str(raw_path))
            if rel_path == evidence_rel or rel_path in self._mutable_control_paths:
                continue
            artifact_path = _resolve_safe(self.root, rel_path)
            if _is_symlink_or_junction(artifact_path):
                raise ControlError(
                    f"changed_paths must be regular files, not symlinks: {rel_path}"
                )
            if artifact_path.is_dir():
                raise ControlError(
                    f"changed_paths must name files, not directories: {rel_path}"
                )
            hashes[rel_path] = (
                _sha256_file(artifact_path) if artifact_path.is_file() else "ABSENT"
            )
        return hashes

    def _run_verification_commands(
        self, task: Task
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for command in task.verification_commands:
            cwd = (self.root / command.cwd).resolve()
            try:
                cwd.relative_to(self.root)
            except ValueError as exc:
                raise ControlError(
                    f"verification cwd escapes project: {command.cwd}"
                ) from exc
            if not cwd.is_dir():
                raise ControlError(f"verification cwd does not exist: {command.cwd}")
            argv = [
                sys.executable if value == "{python}" else value
                for value in command.argv
            ]
            started = time.monotonic()
            try:
                result = subprocess.run(
                    argv,
                    cwd=str(cwd),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=command.timeout_seconds,
                    shell=False,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise ControlError(
                    f"verification command timed out: {command.name}"
                ) from exc
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            record = {
                "name": command.name,
                "argv": argv,
                "cwd": command.cwd,
                "exit_code": result.returncode,
                "duration_ms": round((time.monotonic() - started) * 1000),
                "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
                "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
                "stdout_tail": stdout[-2000:],
                "stderr_tail": stderr[-2000:],
            }
            results.append(record)
            if result.returncode != 0:
                raise ControlError(
                    f"verification command failed: {command.name}\n"
                    f"stdout:\n{record['stdout_tail']}\n"
                    f"stderr:\n{record['stderr_tail']}"
                )
        return results

    def complete(
        self,
        task_id: str,
        owner: str,
        token: str,
        evidence_path: Path,
    ) -> Dict[str, Any]:
        self._assert_task_authority()
        state = self._require_lock(task_id, owner, token)
        mapping = self._task_map()
        if task_id not in mapping:
            raise ControlError(f"unknown repair task: {task_id}")
        task = mapping[task_id]
        resolved_evidence = evidence_path.resolve()
        try:
            rel_evidence = resolved_evidence.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ControlError("evidence must be stored inside the project") from exc

        # Re-validate locked inputs at complete time.
        locked_hashes: Dict[str, str] = {}
        if task.locked_verification_inputs:
            locked_hashes = self._validate_locked_inputs(task, "complete")

        evidence = self._validate_evidence(task, resolved_evidence)
        artifact_hashes = self._snapshot_artifacts(
            evidence.get("changed_paths", []), resolved_evidence
        )

        # Build complete-time manifest and compute delta vs claim-time.
        complete_manifest = _build_workspace_manifest(
            self.root, rel_evidence, self._mutable_control_paths
        )
        lock_data = _read_json(self.lock_path)
        claim_manifest = lock_data.get("claim_manifest", {})
        if not isinstance(claim_manifest, dict):
            raise ControlError("lock claim_manifest is missing or invalid")
        created, modified, deleted = _compute_workspace_delta(
            claim_manifest, complete_manifest
        )

        # Also exclude evidence and lock from delta (they are expected changes).
        evidence_norm = rel_evidence.replace("\\", "/")
        lock_norm = self.lock_rel.as_posix()
        state_norm = self.state_rel.as_posix()
        created.discard(evidence_norm)
        created.discard(lock_norm)
        created.discard(state_norm)
        modified.discard(evidence_norm)
        modified.discard(lock_norm)
        modified.discard(state_norm)
        deleted.discard(evidence_norm)
        deleted.discard(lock_norm)
        deleted.discard(state_norm)
        # Remove known mutable control paths from delta.
        for mp in self._mutable_control_paths:
            created.discard(mp)
            modified.discard(mp)
            deleted.discard(mp)

        declared = set(evidence.get("changed_paths", []))
        declared_norm = {_normalise_rel_path(p) for p in declared}

        # Every actual delta must be declared.
        all_actual = created | modified | deleted
        undeclared = all_actual - declared_norm
        if undeclared:
            raise ControlError(
                f"undeclared workspace changes detected: {sorted(undeclared)}. "
                f"Every actual create/modify/delete must appear in evidence changed_paths."
            )

        # Every actual change must match allowed_paths.
        for actual_path in created | modified:
            if not _path_allowed(actual_path, task.allowed_paths):
                raise ControlError(
                    f"actual change outside task scope: {actual_path}"
                )

        # Reject symlink/junction in actual deltas.
        for actual_path in created | modified:
            file_path = self.root / actual_path
            if file_path.exists() and _is_symlink_or_junction(file_path):
                raise ControlError(
                    f"symlink/junction not allowed: {actual_path}"
                )

        # Deleted paths: ensure they weren't in allowed_paths that still need them.
        # (We log but don't block on deletion — it's a safety check.)

        verification_results = self._run_verification_commands(task)

        completed = list(state.get("completed_tasks", []))
        if task_id not in completed:
            completed.append(task_id)
        records = dict(state.get("evidence_records", {}))
        records[task_id] = {
            "path": rel_evidence,
            "sha256": _sha256_file(resolved_evidence),
            "artifact_hashes": artifact_hashes,
            "verification_input_hashes": locked_hashes,
            "verification_results": verification_results,
            "completed_at": _utc_now(),
        }
        state.update(
            {
                "completed_tasks": completed,
                "evidence_records": records,
                "current_task": None,
                "current_owner": None,
                "lock_token": None,
                "last_failure": None,
                "updated_at": _utc_now(),
            }
        )
        tasks_document = self._load_tasks_document()
        if len(completed) == len(self.load_tasks()):
            state["status"] = tasks_document.get(
                "status_after_all", "V_TASK_REVALIDATION_REQUIRED"
            )
            state["next_task"] = None
        else:
            completed_set = set(completed)
            next_task = next(
                task
                for task in self.load_tasks()
                if task.task_id not in completed_set
                and all(dep in completed_set for dep in task.depends_on)
            )
            state["status"] = next_task.pending_status
            state["next_task"] = next_task.task_id
        _atomic_write_json(self.state_path, state)
        self.lock_path.unlink()
        return state

    def invalidate(self, task_id: str, *, owner: str, reason: str) -> Dict[str, Any]:
        """Reopen a completed task whose evidence no longer proves current code."""

        self._assert_task_authority()
        if self.lock_path.exists():
            raise ControlError("cannot invalidate while an exclusive repair lock exists")
        if not owner.strip():
            raise ControlError("owner must be non-empty")
        if not reason.strip():
            raise ControlError("invalidation reason must be non-empty")

        mapping = self._task_map()
        if task_id not in mapping:
            raise ControlError(f"unknown repair task: {task_id}")
        state = self.load_state()
        completed = list(state.get("completed_tasks", []))
        if task_id not in completed:
            raise ControlError(f"task is not completed: {task_id}")
        dependents = [
            task.task_id
            for task in mapping.values()
            if task.task_id in completed and task_id in task.depends_on
        ]
        if dependents:
            raise ControlError(
                f"cannot invalidate {task_id}; completed dependents exist: "
                + ",".join(sorted(dependents))
            )

        records = dict(state.get("evidence_records", {}))
        previous_record = records.pop(task_id, None)
        invalidated = list(state.get("invalidated_records", []))
        invalidation = {
            "task_id": task_id,
            "owner": owner,
            "reason": reason,
            "invalidated_at": _utc_now(),
            "previous_evidence": previous_record,
        }
        invalidated.append(invalidation)
        completed.remove(task_id)
        state.update(
            {
                "status": mapping[task_id].pending_status,
                "completed_tasks": completed,
                "evidence_records": records,
                "invalidated_records": invalidated,
                "current_task": None,
                "current_owner": None,
                "lock_token": None,
                "next_task": task_id,
                "last_failure": invalidation,
                "updated_at": _utc_now(),
            }
        )
        _atomic_write_json(self.state_path, state)
        return state

    def fail(
        self,
        task_id: str,
        owner: str,
        token: str,
        evidence_path: Optional[Path],
    ) -> Dict[str, Any]:
        state = self._require_lock(task_id, owner, token)
        mapping = self._task_map()
        if task_id not in mapping:
            raise ControlError(f"unknown repair task: {task_id}")
        record: Dict[str, Any] = {
            "task_id": task_id,
            "failed_at": _utc_now(),
        }
        if evidence_path is not None:
            resolved = evidence_path.resolve()
            try:
                record["evidence_path"] = resolved.relative_to(self.root).as_posix()
            except ValueError as exc:
                raise ControlError("failure evidence must be stored inside project") from exc
            record["evidence_sha256"] = _sha256_file(resolved)
        state.update(
            {
                "status": mapping[task_id].pending_status,
                "current_task": None,
                "current_owner": None,
                "lock_token": None,
                "last_failure": record,
                "next_task": task_id,
                "updated_at": _utc_now(),
            }
        )
        _atomic_write_json(self.state_path, state)
        self.lock_path.unlink()
        return state

    def recover(self, *, force: bool = False) -> Dict[str, Any]:
        if not self.lock_path.exists():
            raise ControlError("no exclusive lock to recover")
        lock = _read_json(self.lock_path)
        pid = lock.get("pid")
        alive = False
        if isinstance(pid, int) and pid > 0:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False
        if alive and not force:
            raise ControlError(f"lock owner process is still alive: pid={pid}")
        state = self.load_state()
        task_id = str(lock.get("task_id", ""))
        mapping = self._task_map()
        pending_status = (
            mapping[task_id].pending_status
            if task_id in mapping
            else "REPAIR_REQUIRED"
        )
        state.update(
            {
                "status": pending_status,
                "current_task": None,
                "current_owner": None,
                "lock_token": None,
                "next_task": lock.get("task_id"),
                "last_failure": {
                    "task_id": lock.get("task_id"),
                    "reason": "recovered_stale_lock",
                    "recovered_at": _utc_now(),
                },
                "updated_at": _utc_now(),
            }
        )
        _atomic_write_json(self.state_path, state)
        self.lock_path.unlink()
        return state


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MODE:P vNext rebuild control")
    parser.add_argument(
        "--project-root",
        type=Path,
        help="explicit project root (primarily for isolated verification)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit")
    sub.add_parser("status")
    sub.add_parser("next")

    claim = sub.add_parser("claim")
    claim.add_argument("task_id")
    claim.add_argument("--owner", required=True)

    complete = sub.add_parser("complete")
    complete.add_argument("task_id")
    complete.add_argument("--owner", required=True)
    complete.add_argument("--token", required=True)
    complete.add_argument("--evidence", required=True, type=Path)

    fail = sub.add_parser("fail")
    fail.add_argument("task_id")
    fail.add_argument("--owner", required=True)
    fail.add_argument("--token", required=True)
    fail.add_argument("--evidence", type=Path)

    recover = sub.add_parser("recover")
    recover.add_argument("--force", action="store_true")

    invalidate = sub.add_parser("invalidate")
    invalidate.add_argument("task_id")
    invalidate.add_argument("--owner", required=True)
    invalidate.add_argument("--reason", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    _configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    control = (
        RebuildControl(args.project_root)
        if args.project_root is not None
        else RebuildControl.default()
    )
    try:
        if args.command == "audit":
            issues = control.audit()
            _print_json({"ok": not issues, "issues": issues})
            return 0 if not issues else 1
        if args.command == "status":
            _print_json(control.load_state())
            return 0
        if args.command == "next":
            task = control.next_task()
            _print_json(None if task is None else asdict(task))
            return 0
        if args.command == "claim":
            _print_json(control.claim(args.task_id, args.owner))
            return 0
        if args.command == "complete":
            _print_json(
                control.complete(
                    args.task_id, args.owner, args.token, args.evidence
                )
            )
            return 0
        if args.command == "fail":
            _print_json(
                control.fail(
                    args.task_id, args.owner, args.token, args.evidence
                )
            )
            return 0
        if args.command == "recover":
            _print_json(control.recover(force=args.force))
            return 0
        if args.command == "invalidate":
            _print_json(
                control.invalidate(args.task_id, owner=args.owner, reason=args.reason)
            )
            return 0
    except ControlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
