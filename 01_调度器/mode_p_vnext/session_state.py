"""MODE:P vNext session state, persistence, recovery, and audit events.

The small ``SessionStateMachine`` at the end of this module is intentionally
kept for the already published V6.1/V9.2 callers.  New engineering entry
points must use :class:`PersistentSession`: its JSON state file is the single
business-state authority and every explicit transition appends an immutable
event before the new snapshot is atomically published.

This module deliberately contains no Director, DP, model-provider, or v4
imports.  It is infrastructure for LOOP §9, §20, and §27 only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Mapping, Optional, Tuple

from .canonical_serialization import canonical_json_dumps
from .concurrency_lock import LockError, SessionLock
from .contamination_scanner import ContaminationError, check_vnext_write_safe


class InvalidStateTransition(Exception):
    """Raised when a caller requests a transition not in the declared graph."""


class SessionStateError(Exception):
    """Raised for invalid, corrupt, unsafe, or unrecoverable persistent state."""


SESSION_STATE_FILENAME = "SESSION_STATE.json"
SESSION_EVENTS_FILENAME = "STATE_EVENTS.jsonl"
SESSION_SCHEMA_NAME = "mode_p_vnext_session_state"
SESSION_SCHEMA_VERSION = "1.0.0"
EVENT_SCHEMA_NAME = "mode_p_vnext_state_transition"
EVENT_SCHEMA_VERSION = "1.0.0"


# LOOP §20.2 and §20.3.  These are intentionally separate from the older
# in-memory compatibility list below: changing that old public API silently
# would be a migration bug, not a repair.
EPISODE_STATES: FrozenSet[str] = frozenset(
    {
        "INITIALIZED",
        "FACTS_READY",
        "VISUAL_BASELINE_READY",
        "SCENES_IN_PROGRESS",
        "EPISODE_REVIEW_REQUIRED",
        "EPISODE_REVISION_REQUIRED",
        "READY_FOR_DELIVERY",
        "DELIVERED",
        "BLOCKED",
        "FAILED",
    }
)

SCENE_STATES: FrozenSet[str] = frozenset(
    {
        "NEW",
        "FACTS_BOUND",
        "DIAGNOSIS_REQUIRED",
        "DIAGNOSIS_READY",
        "KNOWLEDGE_REQUIRED",
        "KNOWLEDGE_READY",
        "MASTER_REQUIRED",
        "MASTER_DRAFTED",
        "PRECHECK_REQUIRED",
        "PRECHECK_FAILED",
        "DP_REQUIRED",
        "DP_IN_REVIEW",
        "DIRECTOR_REVISION_REQUIRED",
        "STORYBOARD_READY",
        "AWAITING_STORYBOARD_APPROVAL",
        "STORYBOARD_REVISION_REQUIRED",
        "STORYBOARD_APPROVED",
        "VIDEO_CORRECTION_REQUIRED",
        "VIDEO_PROMPT_READY",
        "RENDER_PAYLOAD_REQUIRED",
        "RENDER_PAYLOAD_READY",
        "READY_FOR_EPISODE_REVIEW",
        "COMMITTED",
        "BLOCKED",
        "FAILED",
    }
)

_EPISODE_PATH: Tuple[str, ...] = (
    "INITIALIZED",
    "FACTS_READY",
    "VISUAL_BASELINE_READY",
    "SCENES_IN_PROGRESS",
    "EPISODE_REVIEW_REQUIRED",
    "READY_FOR_DELIVERY",
    "DELIVERED",
)
_SCENE_PATH: Tuple[str, ...] = (
    "NEW",
    "FACTS_BOUND",
    "DIAGNOSIS_REQUIRED",
    "DIAGNOSIS_READY",
    "KNOWLEDGE_REQUIRED",
    "KNOWLEDGE_READY",
    "MASTER_REQUIRED",
    "MASTER_DRAFTED",
    "PRECHECK_REQUIRED",
    "DP_REQUIRED",
    "DP_IN_REVIEW",
    "STORYBOARD_READY",
    "AWAITING_STORYBOARD_APPROVAL",
    "STORYBOARD_APPROVED",
    "VIDEO_PROMPT_READY",
    "RENDER_PAYLOAD_REQUIRED",
    "RENDER_PAYLOAD_READY",
    "READY_FOR_EPISODE_REVIEW",
    "COMMITTED",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _require_identifier(value: str, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise SessionStateError(f"{label} must be a string")
    value = value.strip()
    if not value and not allow_empty:
        raise SessionStateError(f"{label} is required")
    if any(token in value for token in ("\x00", "/", "\\")):
        raise SessionStateError(f"{label} must not contain a path separator")
    if value in {".", ".."}:
        raise SessionStateError(f"{label} is not a valid identifier")
    return value


def _normalise_scope(scope: Optional[str], scene_id: str) -> str:
    if scope is None:
        return "scene" if scene_id else "episode"
    if scope not in {"episode", "scene"}:
        raise SessionStateError("scope must be either 'episode' or 'scene'")
    if scope == "scene" and not scene_id:
        raise SessionStateError("scene_id is required for a scene session")
    if scope == "episode" and scene_id:
        raise SessionStateError("episode sessions must not declare a scene_id")
    return scope


def _states_for_scope(scope: str) -> FrozenSet[str]:
    return EPISODE_STATES if scope == "episode" else SCENE_STATES


def _initial_state(scope: str) -> str:
    return "INITIALIZED" if scope == "episode" else "NEW"


def _linear_edges(path: Iterable[str]) -> Dict[str, FrozenSet[str]]:
    values = tuple(path)
    return {
        values[index]: frozenset({values[index + 1]})
        for index in range(len(values) - 1)
    }


_EPISODE_EDGES: Dict[str, FrozenSet[str]] = _linear_edges(_EPISODE_PATH)
_EPISODE_EDGES.update(
    {
        "EPISODE_REVIEW_REQUIRED": frozenset(
            {"READY_FOR_DELIVERY", "EPISODE_REVISION_REQUIRED"}
        ),
        "EPISODE_REVISION_REQUIRED": frozenset({"SCENES_IN_PROGRESS"}),
    }
)

_SCENE_EDGES: Dict[str, FrozenSet[str]] = _linear_edges(_SCENE_PATH)
_SCENE_EDGES.update(
    {
        "PRECHECK_REQUIRED": frozenset({"DP_REQUIRED", "PRECHECK_FAILED"}),
        "PRECHECK_FAILED": frozenset({"MASTER_REQUIRED"}),
        "DP_IN_REVIEW": frozenset(
            {"STORYBOARD_READY", "DIRECTOR_REVISION_REQUIRED"}
        ),
        "DIRECTOR_REVISION_REQUIRED": frozenset({"MASTER_DRAFTED"}),
        "AWAITING_STORYBOARD_APPROVAL": frozenset(
            {"STORYBOARD_APPROVED", "STORYBOARD_REVISION_REQUIRED"}
        ),
        "STORYBOARD_REVISION_REQUIRED": frozenset({"MASTER_REQUIRED"}),
        "STORYBOARD_APPROVED": frozenset(
            {
                "VIDEO_PROMPT_READY",
                "VIDEO_CORRECTION_REQUIRED",
                "RENDER_PAYLOAD_REQUIRED",
                "STORYBOARD_REVISION_REQUIRED",
                "MASTER_REQUIRED",
            }
        ),
        "VIDEO_CORRECTION_REQUIRED": frozenset({"MASTER_DRAFTED"}),
    }
)


def _is_transition_allowed(scope: str, current: str, target: str) -> bool:
    if current == target:
        return False
    valid_states = _states_for_scope(scope)
    if target not in valid_states:
        return False
    if target == "FAILED" and current not in {"DELIVERED", "COMMITTED", "FAILED"}:
        return True
    if target == "BLOCKED" and current not in {"DELIVERED", "COMMITTED", "FAILED"}:
        return True
    if current == "BLOCKED":
        # Resuming is an explicit caller action.  The audit event's reason
        # must identify the user or external change that resolved the block.
        return target not in {"BLOCKED", "FAILED"}
    edges = _EPISODE_EDGES if scope == "episode" else _SCENE_EDGES
    return target in edges.get(current, frozenset())


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with open(temporary, "xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write_bytes(path, canonical_json_dumps(dict(value)).encode("utf-8"))


def _append_event(path: Path, event: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json_dumps(dict(event)) + "\n").encode("utf-8")
    with open(path, "ab") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SessionStateError(f"cannot parse session state '{path}': {exc}") from exc
    if not isinstance(parsed, dict):
        raise SessionStateError("session state must be a JSON object")
    return parsed


def _read_events(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    if not path.is_file() or path.is_symlink():
        raise SessionStateError("state event log is not a regular file")
    events: List[Dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise SessionStateError(f"cannot read state event log: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise SessionStateError(f"blank event log line at {line_number}")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SessionStateError(
                f"invalid event JSON at line {line_number}: {exc}"
            ) from exc
        if not isinstance(event, dict):
            raise SessionStateError(f"event at line {line_number} is not an object")
        events.append(event)
    return events


def _validate_hashes(value: Mapping[str, str]) -> Dict[str, str]:
    if not isinstance(value, Mapping):
        raise SessionStateError("artifact_hashes must be an object")
    validated: Dict[str, str] = {}
    for key, digest in value.items():
        key = _require_identifier(str(key), "artifact hash key")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise SessionStateError(f"artifact hash for '{key}' must be a SHA-256 hex digest")
        validated[key] = digest
    return validated


def _validate_event(event: Mapping[str, Any], *, scope: str) -> Dict[str, Any]:
    required = {
        "schema_name",
        "schema_version",
        "event_id",
        "timestamp_utc",
        "episode_id",
        "scene_id",
        "from_state",
        "to_state",
        "actor",
        "reason_code",
        "input_commit_id",
        "output_commit_id",
        "correlation_id",
        "scope",
        "artifact_hashes",
    }
    missing = sorted(required.difference(event))
    if missing:
        raise SessionStateError(f"state event is missing required fields: {', '.join(missing)}")
    if event["schema_name"] != EVENT_SCHEMA_NAME or event["schema_version"] != EVENT_SCHEMA_VERSION:
        raise SessionStateError("unsupported state event schema")
    if event["scope"] != scope:
        raise SessionStateError("state event scope does not match session scope")
    for field_name in (
        "event_id",
        "episode_id",
        "actor",
        "reason_code",
        "input_commit_id",
        "output_commit_id",
        "correlation_id",
    ):
        _require_identifier(str(event[field_name]), field_name, allow_empty=field_name in {"input_commit_id", "output_commit_id"})
    _require_identifier(str(event["scene_id"]), "scene_id", allow_empty=scope == "episode")
    if event["from_state"] and event["from_state"] not in _states_for_scope(scope):
        raise SessionStateError("event from_state is unknown")
    if event["to_state"] not in _states_for_scope(scope):
        raise SessionStateError("event to_state is unknown")
    _validate_hashes(event["artifact_hashes"])
    return dict(event)


def _validate_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    required = {
        "schema_name",
        "schema_version",
        "scope",
        "episode_id",
        "scene_id",
        "state",
        "artifact_hashes",
        "current_commit_id",
        "created_at_utc",
        "updated_at_utc",
        "event_count",
    }
    missing = sorted(required.difference(record))
    if missing:
        raise SessionStateError(f"session state is missing required fields: {', '.join(missing)}")
    if record["schema_name"] != SESSION_SCHEMA_NAME or record["schema_version"] != SESSION_SCHEMA_VERSION:
        raise SessionStateError("unsupported session state schema")
    scope = _normalise_scope(str(record["scope"]), str(record["scene_id"]))
    _require_identifier(str(record["episode_id"]), "episode_id")
    _require_identifier(str(record["scene_id"]), "scene_id", allow_empty=scope == "episode")
    if record["state"] not in _states_for_scope(scope):
        raise SessionStateError("session contains an unknown state")
    if not isinstance(record["event_count"], int) or record["event_count"] < 0:
        raise SessionStateError("event_count must be a non-negative integer")
    _require_identifier(str(record["current_commit_id"]), "current_commit_id", allow_empty=True)
    _validate_hashes(record["artifact_hashes"])
    return dict(record)


@dataclass(frozen=True)
class SessionSnapshot:
    """Immutable read model returned by the persistent session API."""

    session_root: Path
    scope: str
    episode_id: str
    scene_id: str
    state: str
    artifact_hashes: Mapping[str, str]
    current_commit_id: str
    event_count: int
    created_at_utc: str
    updated_at_utc: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_name": SESSION_SCHEMA_NAME,
            "schema_version": SESSION_SCHEMA_VERSION,
            "session_root": str(self.session_root),
            "scope": self.scope,
            "episode_id": self.episode_id,
            "scene_id": self.scene_id,
            "state": self.state,
            "artifact_hashes": dict(self.artifact_hashes),
            "current_commit_id": self.current_commit_id,
            "event_count": self.event_count,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }


class PersistentSession:
    """Filesystem-backed, explicit vNext episode or scene state machine.

    A caller owns the session directory it passes in.  The class rejects v4
    protected paths, symlinks, and malformed state rather than trying to infer
    a safe business state from arbitrary files.
    """

    def __init__(self, session_root: Path):
        self.session_root = self._validate_root(session_root)

    @staticmethod
    def _validate_root(session_root: Path | str) -> Path:
        root = Path(session_root).expanduser().resolve()
        if root == root.anchor or root.name in {"", ".", ".."}:
            raise SessionStateError("session_root must be a dedicated directory")
        try:
            check_vnext_write_safe(root)
        except ContaminationError as exc:
            raise SessionStateError(str(exc)) from exc
        if root.exists() and root.is_symlink():
            raise SessionStateError("session_root must not be a symlink")
        project_root = Path(__file__).resolve().parents[2]
        source_roots = (project_root, project_root / "01_调度器", Path(__file__).resolve().parent)
        for source_root in source_roots:
            if root == source_root.resolve():
                raise SessionStateError("session_root must not be a project or source directory")
        package_root = Path(__file__).resolve().parent
        try:
            root.relative_to(package_root)
        except ValueError:
            pass
        else:
            raise SessionStateError("session_root must not be inside the vNext source package")
        return root

    @property
    def state_path(self) -> Path:
        return self.session_root / SESSION_STATE_FILENAME

    @property
    def event_path(self) -> Path:
        return self.session_root / SESSION_EVENTS_FILENAME

    def _lock(self, *, operation: str, correlation_id: str) -> SessionLock:
        digest = hashlib.sha256(str(self.session_root).encode("utf-8")).hexdigest()
        return SessionLock(
            f"vnext-session-{digest}",
            lock_root=self.session_root / "locks",
            operation=operation,
            correlation_id=correlation_id,
        )

    def _acquire(self, *, owner: str, operation: str, correlation_id: str) -> SessionLock:
        owner = _require_identifier(owner, "owner")
        lock = self._lock(operation=operation, correlation_id=correlation_id)
        try:
            acquired = lock.acquire(owner)
        except LockError as exc:
            raise SessionStateError(f"cannot acquire session lock: {exc}") from exc
        if not acquired:
            raise SessionStateError("session is currently locked by another writer")
        return lock

    @staticmethod
    def _release(lock: SessionLock, owner: str) -> None:
        try:
            lock.release(owner)
        except LockError as exc:
            raise SessionStateError(f"cannot release session lock: {exc}") from exc

    @classmethod
    def create(
        cls,
        session_root: Path | str,
        episode_id: str,
        scene_id: str = "",
        *,
        scope: Optional[str] = None,
        owner: str = "system",
        initial_state: Optional[str] = None,
        correlation_id: str = "session-init",
        artifact_hashes: Optional[Mapping[str, str]] = None,
    ) -> "PersistentSession":
        episode_id = _require_identifier(episode_id, "episode_id")
        scene_id = _require_identifier(scene_id, "scene_id", allow_empty=True)
        scope = _normalise_scope(scope, scene_id)
        state = initial_state or _initial_state(scope)
        if state != _initial_state(scope):
            raise SessionStateError(
                "a session must start at its declared scope's initial state; "
                "use an explicit audited transition instead"
            )
        hashes = _validate_hashes(artifact_hashes or {})
        instance = cls(session_root)
        instance.session_root.mkdir(parents=True, exist_ok=True)
        if instance.session_root.is_symlink():
            raise SessionStateError("session_root must not become a symlink")
        lock = instance._acquire(
            owner=owner, operation="session_init", correlation_id=correlation_id
        )
        try:
            if instance.state_path.exists():
                record = instance._recover_and_read_locked()
                if (
                    record["episode_id"] != episode_id
                    or record["scene_id"] != scene_id
                    or record["scope"] != scope
                ):
                    raise SessionStateError("existing session identity does not match init request")
                return instance

            now = _utc_now()
            record: Dict[str, Any] = {
                "schema_name": SESSION_SCHEMA_NAME,
                "schema_version": SESSION_SCHEMA_VERSION,
                "scope": scope,
                "episode_id": episode_id,
                "scene_id": scene_id,
                "state": state,
                "artifact_hashes": hashes,
                "current_commit_id": "",
                "created_at_utc": now,
                "updated_at_utc": now,
                "event_count": 0,
            }
            _atomic_write_json(instance.state_path, record)
            event = instance._event(
                record,
                from_state="",
                to_state=state,
                actor=owner,
                reason_code="SESSION_INITIALIZED",
                input_commit_id="",
                output_commit_id="",
                correlation_id=correlation_id,
                artifact_hashes=hashes,
            )
            _append_event(instance.event_path, event)
            record["event_count"] = 1
            record["updated_at_utc"] = event["timestamp_utc"]
            _atomic_write_json(instance.state_path, record)
            return instance
        finally:
            instance._release(lock, owner)

    @classmethod
    def open(cls, session_root: Path | str, *, owner: str = "reader") -> "PersistentSession":
        instance = cls(session_root)
        if not instance.state_path.is_file() or instance.state_path.is_symlink():
            raise SessionStateError("session state file does not exist")
        correlation_id = f"session-open-{uuid.uuid4().hex}"
        lock = instance._acquire(
            owner=owner, operation="session_recover", correlation_id=correlation_id
        )
        try:
            instance._recover_and_read_locked()
        finally:
            instance._release(lock, owner)
        return instance

    def _event(
        self,
        record: Mapping[str, Any],
        *,
        from_state: str,
        to_state: str,
        actor: str,
        reason_code: str,
        input_commit_id: str,
        output_commit_id: str,
        correlation_id: str,
        artifact_hashes: Mapping[str, str],
    ) -> Dict[str, Any]:
        return {
            "schema_name": EVENT_SCHEMA_NAME,
            "schema_version": EVENT_SCHEMA_VERSION,
            "event_id": uuid.uuid4().hex,
            "timestamp_utc": _utc_now(),
            "episode_id": record["episode_id"],
            "scene_id": record["scene_id"],
            "from_state": from_state,
            "to_state": to_state,
            "actor": _require_identifier(actor, "actor"),
            "reason_code": _require_identifier(reason_code, "reason_code"),
            "input_commit_id": _require_identifier(
                input_commit_id, "input_commit_id", allow_empty=True
            ),
            "output_commit_id": _require_identifier(
                output_commit_id, "output_commit_id", allow_empty=True
            ),
            "correlation_id": _require_identifier(correlation_id, "correlation_id"),
            "scope": record["scope"],
            "artifact_hashes": _validate_hashes(artifact_hashes),
        }

    def _recover_and_read_locked(self) -> Dict[str, Any]:
        record = _validate_record(_read_json(self.state_path))
        events = [_validate_event(event, scope=record["scope"]) for event in _read_events(self.event_path)]
        if record["event_count"] > len(events):
            raise SessionStateError("state snapshot references missing immutable events")
        if record["event_count"] == len(events):
            self._validate_event_alignment(record, events)
            return record

        # A process may have durable-event-appended just before a crash and
        # failed before atomically publishing its snapshot.  Replay only the
        # exact, validated tail; anything ambiguous is fail-closed.
        current = dict(record)
        for event in events[current["event_count"] :]:
            if event["episode_id"] != current["episode_id"] or event["scene_id"] != current["scene_id"]:
                raise SessionStateError("event identity does not match session state")
            if event["from_state"] == "":
                if current["event_count"] != 0 or event["to_state"] != current["state"]:
                    raise SessionStateError("invalid initialization recovery event")
            elif event["from_state"] != current["state"] or not _is_transition_allowed(
                current["scope"], current["state"], event["to_state"]
            ):
                raise SessionStateError("event tail cannot be safely replayed")
            current["state"] = event["to_state"]
            current["artifact_hashes"] = _validate_hashes(event["artifact_hashes"])
            current["current_commit_id"] = event["output_commit_id"] or current["current_commit_id"]
            current["updated_at_utc"] = event["timestamp_utc"]
            current["event_count"] += 1
        _atomic_write_json(self.state_path, current)
        self._validate_event_alignment(current, events)
        return current

    @staticmethod
    def _validate_event_alignment(record: Mapping[str, Any], events: List[Mapping[str, Any]]) -> None:
        if record["event_count"] != len(events):
            raise SessionStateError("event count does not match immutable event log")
        if not events:
            raise SessionStateError("initialized session must contain its creation event")
        expected_state = _initial_state(str(record["scope"]))
        previous_state = ""
        for index, event in enumerate(events):
            if event["episode_id"] != record["episode_id"] or event["scene_id"] != record["scene_id"]:
                raise SessionStateError("event identity does not match session state")
            if index == 0:
                if event["from_state"] != "" or event["to_state"] != expected_state:
                    raise SessionStateError("first event is not a valid session initialization")
            elif event["from_state"] != previous_state or not _is_transition_allowed(
                str(record["scope"]), previous_state, event["to_state"]
            ):
                raise SessionStateError("event history contains an illegal transition")
            previous_state = str(event["to_state"])
        event = events[-1]
        if event["to_state"] != record["state"]:
            raise SessionStateError("state snapshot disagrees with last transition event")
        if _validate_hashes(record["artifact_hashes"]) != _validate_hashes(event["artifact_hashes"]):
            raise SessionStateError("state snapshot artifact hashes disagree with last event")
        if event["output_commit_id"] and event["output_commit_id"] != record["current_commit_id"]:
            raise SessionStateError("state snapshot commit id disagrees with last event")

    def _snapshot_from_record(self, record: Mapping[str, Any]) -> SessionSnapshot:
        return SessionSnapshot(
            session_root=self.session_root,
            scope=str(record["scope"]),
            episode_id=str(record["episode_id"]),
            scene_id=str(record["scene_id"]),
            state=str(record["state"]),
            artifact_hashes=dict(record["artifact_hashes"]),
            current_commit_id=str(record["current_commit_id"]),
            event_count=int(record["event_count"]),
            created_at_utc=str(record["created_at_utc"]),
            updated_at_utc=str(record["updated_at_utc"]),
        )

    def status(self, *, owner: str = "reader") -> SessionSnapshot:
        correlation_id = f"session-status-{uuid.uuid4().hex}"
        lock = self._acquire(owner=owner, operation="session_status", correlation_id=correlation_id)
        try:
            return self._snapshot_from_record(self._recover_and_read_locked())
        finally:
            self._release(lock, owner)

    @property
    def current_state(self) -> str:
        return self.status().state

    def events(self, *, owner: str = "reader") -> Tuple[Dict[str, Any], ...]:
        correlation_id = f"session-events-{uuid.uuid4().hex}"
        lock = self._acquire(owner=owner, operation="session_read_events", correlation_id=correlation_id)
        try:
            record = self._recover_and_read_locked()
            return tuple(
                _validate_event(event, scope=record["scope"])
                for event in _read_events(self.event_path)
            )
        finally:
            self._release(lock, owner)

    def transition(
        self,
        target: str,
        *,
        actor: str,
        reason_code: str,
        input_commit_id: str = "",
        output_commit_id: str = "",
        correlation_id: Optional[str] = None,
        artifact_hashes: Optional[Mapping[str, str]] = None,
    ) -> SessionSnapshot:
        target = _require_identifier(target, "target")
        correlation_id = correlation_id or f"transition-{uuid.uuid4().hex}"
        correlation_id = _require_identifier(correlation_id, "correlation_id")
        lock = self._acquire(owner=actor, operation="session_transition", correlation_id=correlation_id)
        try:
            record = self._recover_and_read_locked()
            if not _is_transition_allowed(record["scope"], record["state"], target):
                raise InvalidStateTransition(
                    f"illegal {record['scope']} transition: {record['state']} -> {target}"
                )
            next_hashes = _validate_hashes(
                artifact_hashes if artifact_hashes is not None else record["artifact_hashes"]
            )
            event = self._event(
                record,
                from_state=record["state"],
                to_state=target,
                actor=actor,
                reason_code=reason_code,
                input_commit_id=input_commit_id,
                output_commit_id=output_commit_id,
                correlation_id=correlation_id,
                artifact_hashes=next_hashes,
            )
            _append_event(self.event_path, event)
            updated = dict(record)
            updated["state"] = target
            updated["artifact_hashes"] = next_hashes
            if output_commit_id:
                updated["current_commit_id"] = output_commit_id
            updated["updated_at_utc"] = event["timestamp_utc"]
            updated["event_count"] = int(record["event_count"]) + 1
            _atomic_write_json(self.state_path, updated)
            return self._snapshot_from_record(updated)
        finally:
            self._release(lock, actor)


class SessionStateStore:
    """Small discoverable facade for callers that prefer a store object."""

    def __init__(self, session_root: Path | str):
        self.session_root = Path(session_root)

    def create(self, episode_id: str, scene_id: str = "", **kwargs: Any) -> PersistentSession:
        return PersistentSession.create(self.session_root, episode_id, scene_id, **kwargs)

    def open(self, **kwargs: Any) -> PersistentSession:
        return PersistentSession.open(self.session_root, **kwargs)


# ---------------------------------------------------------------------------
# V6.1 compatibility state machine.  It remains intentionally in-memory.
# ---------------------------------------------------------------------------

_LEGACY_STATES = [
    "SCRIPT_PARSED",
    "DIAGNOSIS_COMPLETE",
    "KNOWLEDGE_SELECTED",
    "MASTER_DRAFT",
    "STORYBOARD_READY",
    "STORYBOARD_APPROVAL_REQUIRED",
    "DP_REVIEW_COMPLETE",
    "MASTER_REVISED",
    "RENDER_PAYLOAD_READY",
    "DELIVERY_COMPLETE",
]

_STATE_INDEX: Dict[str, int] = {state: index for index, state in enumerate(_LEGACY_STATES)}
_APPROVAL_STATES: FrozenSet[str] = frozenset({"STORYBOARD_APPROVAL_REQUIRED"})


class SessionStateMachine:
    """Legacy in-memory API retained for V6.1/V9.2 compatibility only."""

    def __init__(self, episode_id: str):
        self.episode_id = episode_id
        self._state = "SCRIPT_PARSED"
        self._history: List[str] = ["SCRIPT_PARSED"]

    @property
    def current_state(self) -> str:
        return self._state

    @property
    def is_approval_required(self) -> bool:
        return self._state in _APPROVAL_STATES

    def transition(self, target: str) -> None:
        if target not in _STATE_INDEX:
            raise InvalidStateTransition(f"Unknown state: {target}")
        curr_idx = _STATE_INDEX[self._state]
        target_idx = _STATE_INDEX[target]
        if target_idx <= curr_idx:
            raise InvalidStateTransition(
                f"Cannot transition backwards: {self._state} -> {target}. "
                "Use rollback_to() instead."
            )
        self._state = target
        self._history.append(target)

    def rollback_to(self, target: str) -> None:
        if target not in _STATE_INDEX:
            raise InvalidStateTransition(f"Unknown state: {target}")
        target_idx = _STATE_INDEX[target]
        curr_idx = _STATE_INDEX[self._state]
        if target_idx > curr_idx:
            raise InvalidStateTransition(
                f"Cannot rollback forward: {self._state} -> {target}"
            )
        if target_idx == curr_idx:
            return
        self._state = target
        self._history.append(f"ROLLBACK:{target}")
