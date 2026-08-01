"""Durable v3.0 graph sessions with fail-closed recovery and concurrency."""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

from mode_p_vnext.concurrency_lock import LockError, SessionLock
from mode_p_vnext.domain.artifact import ArtifactEnvelope, canonical_json_bytes, canonical_sha256, require_sha256
from mode_p_vnext.pipeline.graph import StateGraph
from mode_p_vnext.pipeline.invalidation import FieldInvalidator, InvalidationRecord, InvalidationResult
from mode_p_vnext.pipeline.state import PERSISTENCE_SCHEMA_VERSION, ArtifactRef, PersistentGraphState, StateInvariantError

from .artifacts import ArtifactRepository
from .cache import PersistentNodeCache
from .transaction import MANIFEST_FILENAME, NodeTransaction, NodeTransactionError, PendingNodeWrite


RUN_FILENAME = "RUN.json"
CURRENT_FILENAME = "CURRENT.json"
CHECKPOINTS_DIRNAME = "checkpoints"
RUN_SCHEMA_NAME = "mode_p_vnext_runtime_run"
POINTER_SCHEMA_NAME = "mode_p_vnext_runtime_current_pointer"
CHECKPOINT_SCHEMA_NAME = "mode_p_vnext_runtime_checkpoint"


class RunSessionError(RuntimeError):
    """Raised when a v3.0 run cannot be safely read, resumed, or advanced."""


def _safe_component(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value in {".", ".."}
        or any(character in value for character in ("/", "\\", ":", "\x00"))
        or value.endswith((".", " "))
        or any(ord(character) < 32 for character in value)
    ):
        raise RunSessionError(f"{field_name} must be a safe non-empty path component")
    return value


def _scope(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value or any(ord(character) < 32 for character in value):
        raise RunSessionError("write_scope must be a non-empty safe identifier")
    return value


def _read_json(path: Path, label: str) -> Mapping[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RunSessionError(f"{label} is not a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RunSessionError(f"{label} is invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise RunSessionError(f"{label} must contain an object")
    return value


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class ResumePlan:
    """A read-only restart view; mismatch must be invalidated explicitly."""

    checkpoint_sequence: int
    accepted_node_ids: tuple[str, ...]
    runnable_node_ids: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionSnapshot:
    """The digest a producer must bind before it starts an external computation."""

    run_id: str
    graph_digest: str
    base_state_sha256: str


class RunSession:
    """One persistent graph run bound to one episode/scene write scope."""

    def __init__(self, run_dir: Path, graph: StateGraph) -> None:
        candidate = Path(run_dir)
        if candidate.is_symlink() or not candidate.is_dir():
            raise RunSessionError("run directory must be a regular directory")
        self.run_dir = candidate.resolve()
        self.graph = graph
        self._validate_run_record()
        self.artifacts = ArtifactRepository(self.run_dir)
        self.cache = PersistentNodeCache(self.run_dir)

    @classmethod
    def create(
        cls,
        runs_root: Path,
        *,
        run_id: str,
        graph: StateGraph,
        write_scope: str | None = None,
    ) -> "RunSession":
        safe_run_id = _safe_component(run_id, "run_id")
        root = Path(runs_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink():
            raise RunSessionError("runs root must not be a symbolic link")
        run_dir = (root / safe_run_id).resolve()
        if run_dir.parent != root:
            raise RunSessionError("run_id must stay within the runs root")
        try:
            run_dir.mkdir()
        except FileExistsError as exc:
            raise RunSessionError(f"run already exists: {safe_run_id}") from exc
        for name in ("artifacts", "cache", "commits", "staging", "quarantine", CHECKPOINTS_DIRNAME):
            (run_dir / name).mkdir()
        body = {
            "schema_name": RUN_SCHEMA_NAME,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "run_id": safe_run_id,
            "write_scope": _scope(write_scope if write_scope is not None else safe_run_id),
            "graph": graph.descriptor(),
            "graph_digest": graph.digest,
        }
        _atomic_write(run_dir / RUN_FILENAME, {**body, "record_sha256": canonical_sha256(body)})
        return cls(run_dir, graph)

    @classmethod
    def open(cls, run_dir: Path, *, graph: StateGraph) -> "RunSession":
        return cls(run_dir, graph)

    @property
    def current_pointer_path(self) -> Path:
        return self.run_dir / CURRENT_FILENAME

    @property
    def run_id(self) -> str:
        return self._run_record()["run_id"]  # type: ignore[return-value]

    @property
    def write_scope(self) -> str:
        return self._run_record()["write_scope"]  # type: ignore[return-value]

    def capture_execution_snapshot(self) -> ExecutionSnapshot:
        return ExecutionSnapshot(
            run_id=self.run_id,
            graph_digest=self.graph.digest,
            base_state_sha256=canonical_sha256(self.state().to_dict()),
        )

    def runner(self, *, owner: str) -> "NodeRunner":
        return NodeRunner(self, owner)

    def _run_record(self) -> Mapping[str, Any]:
        return _read_json(self.run_dir / RUN_FILENAME, "RUN.json")

    def _validate_run_record(self) -> None:
        record = self._run_record()
        expected = {
            "schema_name", "schema_version", "run_id", "write_scope", "graph",
            "graph_digest", "record_sha256",
        }
        if set(record) != expected or record.get("schema_name") != RUN_SCHEMA_NAME or record.get("schema_version") != PERSISTENCE_SCHEMA_VERSION:
            raise RunSessionError("RUN record fields do not match the v3.0 schema")
        body = {key: value for key, value in record.items() if key != "record_sha256"}
        if canonical_sha256(body) != record.get("record_sha256"):
            raise RunSessionError("RUN record digest is invalid")
        if _safe_component(record.get("run_id"), "run_id") != self.run_dir.name:
            raise RunSessionError("RUN record identity does not match its directory")
        _scope(record.get("write_scope"))
        if canonical_sha256(record.get("graph")) != self.graph.digest or record.get("graph_digest") != self.graph.digest:
            raise RunSessionError("requested graph does not match the persisted run graph")

    def _read_pointer(self) -> Mapping[str, Any] | None:
        path = self.current_pointer_path
        if not path.exists():
            return None
        pointer = _read_json(path, "CURRENT.json")
        expected = {
            "schema_name", "schema_version", "commit_id", "state_sha256",
            "manifest_sha256", "pointer_sha256",
        }
        if set(pointer) != expected or pointer.get("schema_name") != POINTER_SCHEMA_NAME or pointer.get("schema_version") != PERSISTENCE_SCHEMA_VERSION:
            raise RunSessionError("current pointer fields do not match the v3.0 schema")
        body = {key: value for key, value in pointer.items() if key != "pointer_sha256"}
        if canonical_sha256(body) != pointer.get("pointer_sha256"):
            raise RunSessionError("current pointer digest is invalid")
        for name in ("state_sha256", "manifest_sha256"):
            try:
                require_sha256(pointer[name], name)
            except Exception as exc:
                raise RunSessionError(f"current pointer {name} is invalid") from exc
        _safe_component(pointer.get("commit_id"), "commit_id")
        return pointer

    def _write_pointer(self, pending: PendingNodeWrite) -> None:
        commit_dir = self.run_dir / "commits" / pending.commit_id
        manifest_sha256 = NodeTransaction.manifest_sha256(commit_dir)
        body = {
            "schema_name": POINTER_SCHEMA_NAME,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "commit_id": pending.commit_id,
            "state_sha256": pending.state_sha256,
            "manifest_sha256": manifest_sha256,
        }
        _atomic_write(self.current_pointer_path, {**body, "pointer_sha256": canonical_sha256(body)})

    def _transition_state(self, state: PersistentGraphState, pending: PendingNodeWrite) -> PersistentGraphState:
        if pending.parent_commit_id != state.current_commit_id:
            raise RunSessionError("commit parent does not match the active state")
        if pending.base_state_sha256 != canonical_sha256(state.to_dict()):
            raise RunSessionError("commit base state does not match the active state")
        transition = pending.transition
        if pending.transaction_kind == "node":
            expected = {
                "kind", "node_id", "graph_digest", "outputs", "input_digests",
                "knowledge_snapshot_digest", "capability_profile_digest",
            }
            if set(transition) != expected or transition.get("kind") != "node" or transition.get("graph_digest") != self.graph.digest:
                raise RunSessionError("node transition fields are invalid or bound to another graph")
            raw_outputs = transition.get("outputs")
            if not isinstance(raw_outputs, Mapping):
                raise RunSessionError("node transition outputs must be an object")
            try:
                return self.graph.apply(
                    state,
                    node_id=transition["node_id"],
                    outputs={field: ArtifactRef.from_dict(ref) for field, ref in raw_outputs.items()},
                    input_digests=transition["input_digests"],
                    knowledge_snapshot_digest=transition["knowledge_snapshot_digest"],
                    capability_profile_digest=transition["capability_profile_digest"],
                    commit_id=pending.commit_id,
                )
            except (KeyError, TypeError, StateInvariantError) as exc:
                raise RunSessionError("node transition cannot be reproduced") from exc
        expected = {"kind", "record"}
        if set(transition) != expected or transition.get("kind") != "invalidation" or not isinstance(transition.get("record"), Mapping):
            raise RunSessionError("invalidation transition fields are invalid")
        try:
            record = InvalidationRecord.from_dict(transition["record"])
            invalidator = FieldInvalidator(self.graph)
            if record.invalidation_kind == "capability_profile":
                return invalidator.invalidate_capability_profile(
                    state,
                    capability_profile_digest=record.changed_field_digests["capability_profile"],
                    reason=record.reason,
                    commit_id=pending.commit_id,
                ).state
            if record.invalidation_kind == "knowledge_snapshot":
                return invalidator.invalidate_knowledge_snapshot(
                    state,
                    knowledge_snapshot_digest=record.changed_field_digests["knowledge_snapshot"],
                    reason=record.reason,
                    commit_id=pending.commit_id,
                ).state
            return invalidator.invalidate(
                state,
                changed_field_digests=record.changed_field_digests,
                reason=record.reason,
                commit_id=pending.commit_id,
                invalidation_kind="field",
            ).state
        except (StateInvariantError, KeyError, TypeError) as exc:
            raise RunSessionError("invalidation transition cannot be reproduced") from exc

    def _replay(self, current_commit_id: str) -> PersistentGraphState:
        chain: list[PendingNodeWrite] = []
        seen: set[str] = set()
        commit_id = current_commit_id
        while commit_id:
            if commit_id in seen:
                raise RunSessionError("commit chain contains a cycle")
            seen.add(commit_id)
            pending = NodeTransaction.read_committed(self.run_dir / "commits" / commit_id)
            if pending.commit_id != commit_id:
                raise RunSessionError("commit directory identity does not match its record")
            chain.append(pending)
            commit_id = pending.parent_commit_id
        state = PersistentGraphState.empty(self.run_id)
        for pending in reversed(chain):
            expected = self._transition_state(state, pending)
            if canonical_sha256(expected.to_dict()) != pending.state_sha256 or expected.to_dict() != pending.next_state.to_dict():
                raise RunSessionError("committed transition does not reproduce its state")
            state = expected
        self.graph.validate_state(state)
        for field_name, ref in state.outputs.items():
            if not self.artifacts.contains(ref):
                raise RunSessionError(f"persisted ArtifactRef for '{field_name}' no longer verifies")
        return state

    def state(self) -> PersistentGraphState:
        pointer = self._read_pointer()
        if pointer is None:
            return PersistentGraphState.empty(self.run_id)
        pending = NodeTransaction.read_committed(self.run_dir / "commits" / pointer["commit_id"])
        if NodeTransaction.manifest_sha256(self.run_dir / "commits" / pending.commit_id) != pointer["manifest_sha256"]:
            raise RunSessionError("current pointer is not bound to the committed manifest")
        state = self._replay(pending.commit_id)
        if canonical_sha256(state.to_dict()) != pointer["state_sha256"]:
            raise RunSessionError("current pointer is not bound to the replayed state")
        return state

    def checkpoint(self) -> Path:
        state = self.state()
        body = {
            "schema_name": CHECKPOINT_SCHEMA_NAME,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "run_id": self.run_id,
            "commit_id": state.current_commit_id,
            "event_sequence": state.event_sequence,
            "state": state.to_dict(),
            "state_sha256": canonical_sha256(state.to_dict()),
        }
        path = self.run_dir / CHECKPOINTS_DIRNAME / f"{state.event_sequence:08d}-{state.current_commit_id or 'root'}.json"
        _atomic_write(path, {**body, "checkpoint_sha256": canonical_sha256(body)})
        return path

    def _matching_checkpoint_sequence(self, state: PersistentGraphState) -> int:
        root = self.run_dir / CHECKPOINTS_DIRNAME
        if not root.is_dir() or root.is_symlink():
            return 0
        for path in sorted(root.glob("*.json"), reverse=True):
            try:
                value = _read_json(path, "checkpoint")
                body = {key: item for key, item in value.items() if key != "checkpoint_sha256"}
                if (
                    canonical_sha256(body) == value.get("checkpoint_sha256")
                    and value.get("run_id") == self.run_id
                    and value.get("commit_id") == state.current_commit_id
                    and value.get("state_sha256") == canonical_sha256(state.to_dict())
                    and value.get("state") == state.to_dict()
                ):
                    return state.event_sequence
            except RunSessionError:
                continue
        return 0

    def resume_plan(self, supplied_input_digests: Mapping[str, str]) -> ResumePlan:
        state = self.state()
        if not isinstance(supplied_input_digests, Mapping):
            raise RunSessionError("supplied_input_digests must be a mapping")
        for acceptance in state.accepted.values():
            for field, expected in acceptance.input_digests.items():
                if field in supplied_input_digests and supplied_input_digests[field] != expected:
                    raise RunSessionError("input digest changed; an explicit invalidation transaction is required")
        return ResumePlan(
            checkpoint_sequence=self._matching_checkpoint_sequence(state),
            accepted_node_ids=tuple(state.accepted),
            runnable_node_ids=self.graph.runnable_node_ids(state),
        )

    def _staging_dirs(self) -> tuple[Path, ...]:
        root = self.run_dir / "staging"
        if not root.is_dir() or root.is_symlink():
            raise RunSessionError("staging root is unsafe")
        entries = tuple(sorted(root.iterdir(), key=lambda path: path.name))
        if any(not path.is_dir() or path.is_symlink() for path in entries):
            raise RunSessionError("staging contains an unsafe entry")
        return entries

    def recover_pending(self, *, owner: str) -> tuple[str, ...]:
        """Discard uncommitted candidates; recover exactly one committed child only."""
        with self._lock(owner):
            for staging_dir in self._staging_dirs():
                try:
                    NodeTransaction.abandon_staging(
                        self.run_dir,
                        staging_dir.name,
                        reason="process interrupted before atomic commit; pending state is not recoverable",
                    )
                except NodeTransactionError as exc:
                    raise RunSessionError(str(exc)) from exc
            base = self.state()
            base_hash = canonical_sha256(base.to_dict())
            candidates: list[PendingNodeWrite] = []
            commits_root = self.run_dir / "commits"
            for commit_dir in sorted(commits_root.iterdir(), key=lambda path: path.name):
                if not commit_dir.is_dir() or commit_dir.is_symlink():
                    raise RunSessionError("commits contains an unsafe entry")
                pending = NodeTransaction.read_committed(commit_dir)
                if pending.commit_id == base.current_commit_id:
                    continue
                if pending.parent_commit_id == base.current_commit_id and pending.base_state_sha256 == base_hash:
                    candidates.append(pending)
            if not candidates:
                return ()
            if len(candidates) != 1:
                raise RunSessionError("multiple committed children make recovery ambiguous")
            pending = candidates[0]
            expected = self._transition_state(base, pending)
            if expected.to_dict() != pending.next_state.to_dict():
                raise RunSessionError("committed recovery candidate does not reproduce its state")
            self._write_pointer(pending)
            self.checkpoint()
            return (pending.node_id or pending.transaction_kind,)

    def _commit_invalidation(self, result: InvalidationResult, *, owner: str) -> InvalidationResult:
        if not result.invalidated_node_ids:
            return result
        base = self.state()
        commit_id, generation_id = NodeTransaction.new_identity("invalidate")
        # Recompute with the actual local commit ID; the caller's result is a plan.
        record = result.record
        invalidator = FieldInvalidator(self.graph)
        if record.invalidation_kind == "capability_profile":
            actual = invalidator.invalidate_capability_profile(
                base,
                capability_profile_digest=record.changed_field_digests["capability_profile"],
                reason=record.reason,
                commit_id=commit_id,
            )
        elif record.invalidation_kind == "knowledge_snapshot":
            actual = invalidator.invalidate_knowledge_snapshot(
                base,
                knowledge_snapshot_digest=record.changed_field_digests["knowledge_snapshot"],
                reason=record.reason,
                commit_id=commit_id,
            )
        else:
            actual = invalidator.invalidate(
                base,
                changed_field_digests=record.changed_field_digests,
                reason=record.reason,
                commit_id=commit_id,
            )
        if actual.record.invalidated_node_ids != record.invalidated_node_ids:
            raise RunSessionError("invalidation scope changed while acquiring the write lock")
        pending = NodeTransaction.prepare(
            self.run_dir,
            transaction_kind="invalidation",
            base_state=base,
            next_state=actual.state,
            parent_commit_id=base.current_commit_id,
            commit_id=commit_id,
            generation_id=generation_id,
            transition={"kind": "invalidation", "record": actual.record.to_dict()},
        )
        try:
            NodeTransaction.promote(self.run_dir, pending)
        except NodeTransactionError as exc:
            raise RunSessionError(str(exc)) from exc
        self._write_pointer(pending)
        self.checkpoint()
        return actual

    def invalidate(self, *, changed_field_digests: Mapping[str, str], reason: str) -> InvalidationResult:
        with self._lock("invalidation"):
            if self._staging_dirs():
                raise RunSessionError("an unresolved pending write prevents invalidation")
            base = self.state()
            planning_commit, _ = NodeTransaction.new_identity("invalidate-plan")
            planned = FieldInvalidator(self.graph).invalidate(
                base,
                changed_field_digests=changed_field_digests,
                reason=reason,
                commit_id=planning_commit,
            )
            return self._commit_invalidation(planned, owner="invalidation")

    def invalidate_capability_profile(self, *, capability_profile_digest: str, reason: str) -> InvalidationResult:
        with self._lock("capability-invalidation"):
            if self._staging_dirs():
                raise RunSessionError("an unresolved pending write prevents invalidation")
            base = self.state()
            planning_commit, _ = NodeTransaction.new_identity("capability-plan")
            planned = FieldInvalidator(self.graph).invalidate_capability_profile(
                base,
                capability_profile_digest=capability_profile_digest,
                reason=reason,
                commit_id=planning_commit,
            )
            return self._commit_invalidation(planned, owner="capability-invalidation")

    @contextmanager
    def _lock(self, owner: str) -> Iterator[None]:
        if not isinstance(owner, str) or not owner.strip():
            raise RunSessionError("writer owner must be non-empty")
        lock = SessionLock(
            self.write_scope,
            lock_root=self.run_dir.parent / ".mode_p_vnext_locks",
            operation="vnext_runtime_graph_write",
        )
        acquired = False
        try:
            if not lock.acquire(owner):
                raise RunSessionError(f"write lock is already held for scope '{self.write_scope}'")
            acquired = True
            yield
        except LockError as exc:
            raise RunSessionError(str(exc)) from exc
        finally:
            if acquired:
                lock.release(owner)


class NodeRunner:
    """Accepts only outputs bound to a locally captured pre-execution state."""

    def __init__(self, session: RunSession, owner: str) -> None:
        self.session = session
        self.owner = owner

    def _refs(self, artifacts: Mapping[str, ArtifactEnvelope | ArtifactRef]) -> dict[str, ArtifactRef]:
        if not isinstance(artifacts, Mapping):
            raise StateInvariantError("artifacts must be a mapping")
        refs: dict[str, ArtifactRef] = {}
        for field_name, artifact in artifacts.items():
            if isinstance(artifact, ArtifactEnvelope):
                refs[field_name] = self.session.artifacts.put(artifact)
            elif isinstance(artifact, ArtifactRef):
                if not self.session.artifacts.contains(artifact):
                    raise StateInvariantError(f"ArtifactRef for '{field_name}' is not a stored canonical Artifact")
                refs[field_name] = artifact
            else:
                raise StateInvariantError(f"unsupported artifact for '{field_name}'")
        return refs

    def prepare(
        self,
        node_id: str,
        *,
        artifacts: Mapping[str, ArtifactEnvelope | ArtifactRef],
        input_digests: Mapping[str, str],
        base_state_sha256: str,
        knowledge_snapshot_digest: str | None = None,
        capability_profile_digest: str | None = None,
    ) -> PendingNodeWrite:
        try:
            require_sha256(base_state_sha256, "base_state_sha256")
        except Exception as exc:
            raise StateInvariantError("base_state_sha256 must be a SHA-256 digest") from exc
        with self.session._lock(self.owner):
            if self.session._staging_dirs():
                raise RunSessionError("an unresolved pending write prevents another prepare")
            state = self.session.state()
            if canonical_sha256(state.to_dict()) != base_state_sha256:
                raise StateInvariantError("stale concurrent result: captured base state no longer matches")
            refs = self._refs(artifacts)
            commit_id, generation_id = NodeTransaction.new_identity(node_id)
            next_state = self.session.graph.apply(
                state,
                node_id=node_id,
                outputs=refs,
                input_digests=input_digests,
                knowledge_snapshot_digest=knowledge_snapshot_digest,
                capability_profile_digest=capability_profile_digest,
                commit_id=commit_id,
            )
            return NodeTransaction.prepare(
                self.session.run_dir,
                transaction_kind="node",
                base_state=state,
                next_state=next_state,
                parent_commit_id=state.current_commit_id,
                commit_id=commit_id,
                generation_id=generation_id,
                transition={
                    "kind": "node",
                    "node_id": node_id,
                    "graph_digest": self.session.graph.digest,
                    "outputs": {field: ref.to_dict() for field, ref in refs.items()},
                    "input_digests": dict(input_digests),
                    "knowledge_snapshot_digest": knowledge_snapshot_digest,
                    "capability_profile_digest": capability_profile_digest,
                },
            )

    def accept(self, pending: PendingNodeWrite) -> PersistentGraphState:
        if not isinstance(pending, PendingNodeWrite) or pending.transaction_kind != "node":
            raise StateInvariantError("accept requires a prepared node write")
        with self.session._lock(self.owner):
            state = self.session.state()
            expected = self.session._transition_state(state, pending)
            if expected.to_dict() != pending.next_state.to_dict():
                raise StateInvariantError("prepared node write is stale or cannot reproduce the current transition")
            try:
                NodeTransaction.promote(self.session.run_dir, pending)
            except NodeTransactionError as exc:
                raise RunSessionError(str(exc)) from exc
            self.session._write_pointer(pending)
            self.session.checkpoint()
            return self.session.state()

    def execute(
        self,
        node_id: str,
        *,
        artifacts: Mapping[str, ArtifactEnvelope | ArtifactRef],
        input_digests: Mapping[str, str],
        base_state_sha256: str,
        knowledge_snapshot_digest: str | None = None,
        capability_profile_digest: str | None = None,
    ) -> PersistentGraphState:
        return self.accept(
            self.prepare(
                node_id,
                artifacts=artifacts,
                input_digests=input_digests,
                base_state_sha256=base_state_sha256,
                knowledge_snapshot_digest=knowledge_snapshot_digest,
                capability_profile_digest=capability_profile_digest,
            )
        )
