"""Durable run sessions, checkpoint recovery, and graph-node execution."""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterator, Mapping

from mode_p_vnext.concurrency_lock import LockError, SessionLock
from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    canonical_json_bytes,
    canonical_sha256,
)
from mode_p_vnext.pipeline.graph import StateGraph
from mode_p_vnext.pipeline.invalidation import FieldInvalidator, InvalidationResult
from mode_p_vnext.pipeline.state import (
    ArtifactRef,
    PersistentGraphState,
    StateInvariantError,
)

from .artifacts import ArtifactRepository
from .cache import PersistentNodeCache
from .transaction import NodeTransaction, NodeTransactionError, PendingNodeWrite


RUN_FILENAME = "RUN.json"
EVENTS_FILENAME = "STATE_EVENTS.jsonl"
CHECKPOINTS_DIRNAME = "checkpoints"
CURRENT_FILENAME = "current.json"


class RunSessionError(RuntimeError):
    """Raised where a run cannot be read or advanced safely."""


@dataclass(frozen=True)
class ResumePlan:
    """Validated restart boundary, expressed only with content digests."""

    checkpoint_sequence: int
    accepted_node_ids: tuple[str, ...]
    runnable_node_ids: tuple[str, ...]


class RunSession:
    """Filesystem-backed source of truth for one vNext graph run."""

    def __init__(self, run_dir: Path, graph: StateGraph) -> None:
        self.run_dir = Path(run_dir)
        self.graph = graph
        self._validate_run_record()
        self.artifacts = ArtifactRepository(self.run_dir)
        self.cache = PersistentNodeCache(self.run_dir)

    @classmethod
    def create(
        cls, runs_root: Path, *, run_id: str, graph: StateGraph
    ) -> "RunSession":
        if not run_id or any(char in run_id for char in ("/", "\\", "\0")):
            raise RunSessionError("run_id must be a safe, non-empty path component")
        run_dir = Path(runs_root) / run_id
        if run_dir.exists():
            raise RunSessionError(f"run already exists: {run_id}")
        for name in (
            "artifacts",
            "commits",
            CHECKPOINTS_DIRNAME,
            "projections",
            "evidence",
        ):
            (run_dir / name).mkdir(parents=True, exist_ok=True)
        record = {
            "run_id": run_id,
            "format_version": 1,
            "graph": graph.descriptor(),
            "graph_digest": canonical_sha256(graph.descriptor()),
        }
        cls._atomic_write_json(run_dir / RUN_FILENAME, record)
        (run_dir / EVENTS_FILENAME).touch()
        return cls(run_dir, graph)

    @classmethod
    def open(cls, run_dir: Path, *, graph: StateGraph) -> "RunSession":
        return cls(Path(run_dir), graph)

    @property
    def run_id(self) -> str:
        return str(self._run_record()["run_id"])

    @property
    def current_pointer_path(self) -> Path:
        return self.run_dir / CURRENT_FILENAME

    def runner(self, *, owner: str) -> "NodeRunner":
        return NodeRunner(self, owner)

    def state(self) -> PersistentGraphState:
        """Replay only state events whose referenced commit was atomically promoted."""
        state, checkpoint_sequence = self._latest_valid_checkpoint()
        for event in self._events():
            if int(event["state"]["event_sequence"]) <= checkpoint_sequence:
                continue
            commit_id = str(event.get("commit_id") or "")
            if commit_id and not self._is_promoted_commit(commit_id, event["state_sha256"]):
                # This is a durable prepared event.  It becomes visible only
                # after its same-volume commit promotion succeeds.
                continue
            candidate = PersistentGraphState.from_dict(event["state"])
            if candidate.event_sequence <= state.event_sequence:
                continue
            if candidate.event_sequence != state.event_sequence + 1:
                raise RunSessionError("accepted state events have a sequence gap")
            state = candidate
        return state

    def checkpoint(self) -> Path:
        state = self.state()
        state_payload = state.to_dict()
        payload = dict(state_payload)
        payload["state"] = state_payload
        payload["state_sha256"] = canonical_sha256(state_payload)
        path = self.run_dir / CHECKPOINTS_DIRNAME / f"{state.event_sequence}.json"
        self._atomic_write_json(path, payload)
        return path

    def recover_pending(self, *, owner: str) -> tuple[str, ...]:
        """Promote exactly one valid prepared write at a time, without rerunning it."""
        accepted: list[str] = []
        staging_root = self.run_dir / "staging"
        with self._lock(owner):
            if not staging_root.is_dir():
                return ()
            candidates = [
                path
                for path in sorted(staging_root.iterdir(), key=lambda item: item.name)
                if path.is_dir() and path.name != "abandoned"
            ]
            for staging_dir in candidates:
                pending = NodeTransaction.read_prepared(staging_dir)
                state = self.state()
                if pending.node_id in state.accepted:
                    continue
                if canonical_sha256(state.to_dict()) != pending.base_state_sha256:
                    raise RunSessionError(
                        "prepared write base state no longer matches the last accepted state"
                    )
                try:
                    NodeTransaction.promote(self.run_dir, pending)
                except NodeTransactionError as exc:
                    raise RunSessionError(str(exc)) from exc
                restored = self.state()
                if pending.node_id not in restored.accepted:
                    raise RunSessionError("promoted commit has no visible accepted state event")
                self._write_current_pointer(restored, pending)
                self.checkpoint()
                accepted.append(pending.node_id)
        return tuple(accepted)

    def resume_plan(self, supplied_input_digests: Mapping[str, str]) -> ResumePlan:
        """Return the accepted restart prefix after validating digest edges."""
        state = self.state()
        changed: dict[str, str] = {}
        for node_id, acceptance in state.accepted.items():
            node = self.graph.node(node_id)
            for field_name, expected in acceptance.dependency_digests.items():
                if field_name in node.input_fields and field_name in supplied_input_digests:
                    actual = supplied_input_digests[field_name]
                    if actual != expected:
                        changed[field_name] = actual
        checkpoint_sequence = state.event_sequence
        if changed:
            result = FieldInvalidator(self.graph).invalidate(
                state,
                changed_field_digests=changed,
                reason="resume dependency digest mismatch",
            )
            state = result.state
            checkpoint_sequence = 0
        return ResumePlan(
            checkpoint_sequence=checkpoint_sequence,
            accepted_node_ids=tuple(state.accepted),
            runnable_node_ids=self.graph.runnable_node_ids(state),
        )

    def invalidate(
        self, *, changed_field_digests: Mapping[str, str], reason: str
    ) -> InvalidationResult:
        with self._lock("invalidation"):
            result = FieldInvalidator(self.graph).invalidate(
                self.state(),
                changed_field_digests=changed_field_digests,
                reason=reason,
            )
            if result.invalidated_node_ids:
                self._append_state_event(result.state, pending=None)
                self._write_current_pointer(result.state, pending=None)
                self.checkpoint()
            return result

    def _validate_run_record(self) -> None:
        record = self._run_record()
        stored_graph = record.get("graph")
        if canonical_sha256(stored_graph) != record.get("graph_digest"):
            raise RunSessionError("RUN graph descriptor digest is invalid")
        if canonical_sha256(self.graph.descriptor()) != record.get("graph_digest"):
            raise RunSessionError("requested graph does not match the run graph")

    def _run_record(self) -> Mapping[str, Any]:
        try:
            return json.loads((self.run_dir / RUN_FILENAME).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RunSessionError("invalid RUN.json") from exc

    def _events(self) -> Iterator[Mapping[str, Any]]:
        path = self.run_dir / EVENTS_FILENAME
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise RunSessionError("cannot read state event log") from exc
        for line in lines:
            try:
                event = json.loads(line)
                if canonical_sha256(event["state"]) != event["state_sha256"]:
                    raise RunSessionError("state event digest is invalid")
                yield event
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise RunSessionError("invalid state event") from exc

    def _latest_valid_checkpoint(self) -> tuple[PersistentGraphState, int]:
        baseline = PersistentGraphState.empty(self.run_id)
        checkpoint_dir = self.run_dir / CHECKPOINTS_DIRNAME
        candidates: list[tuple[int, Path]] = []
        for path in checkpoint_dir.glob("*.json"):
            try:
                candidates.append((int(path.stem), path))
            except ValueError:
                continue
        for sequence, path in sorted(candidates, reverse=True):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                state_data = payload.get("state", payload)
                if canonical_sha256(state_data) != payload["state_sha256"]:
                    continue
                state = PersistentGraphState.from_dict(state_data)
                if state.event_sequence == sequence:
                    return state, sequence
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return baseline, 0

    def _is_promoted_commit(self, commit_id: str, state_sha256: str) -> bool:
        commit_dir = self.run_dir / "commits" / commit_id
        manifest_path = commit_dir / "COMMIT_MANIFEST.json"
        # Transaction.commit validates every manifest entry before its
        # same-volume rename. Presence of the final manifest is therefore the
        # visibility boundary; the event state hash is checked by _events.
        return manifest_path.is_file()

    def _append_state_event(
        self, state: PersistentGraphState, pending: PendingNodeWrite | None
    ) -> None:
        event = {
            "state": state.to_dict(),
            "state_sha256": canonical_sha256(state.to_dict()),
            "commit_id": pending.commit_id if pending else None,
            "node_id": pending.node_id if pending else None,
        }
        with (self.run_dir / EVENTS_FILENAME).open("ab") as handle:
            handle.write(canonical_json_bytes(event))
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _write_current_pointer(
        self, state: PersistentGraphState, pending: PendingNodeWrite | None
    ) -> None:
        commit_id = pending.commit_id if pending else state.current_commit_id
        if not commit_id:
            raise RunSessionError("cannot publish a current pointer without a commit id")
        manifest_path = self.run_dir / "commits" / commit_id / "COMMIT_MANIFEST.json"
        if not manifest_path.is_file():
            raise RunSessionError("cannot publish a pointer for a missing commit manifest")
        self._atomic_write_json(
            self.current_pointer_path,
            {
                "sequence": state.event_sequence,
                "state_sha256": canonical_sha256(state.to_dict()),
                "commit_id": commit_id,
                # Required by the reused atomic committer for all subsequent
                # parent-commit validation. This is a raw-file digest because
                # the legacy manifest contains a floating-point timestamp.
                "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
                "node_id": pending.node_id if pending else None,
            },
        )

    @staticmethod
    def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        with temporary.open("wb") as handle:
            handle.write(canonical_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    @contextmanager
    def _lock(self, owner: str) -> Iterator[None]:
        lock = SessionLock(
            self.run_id,
            lock_root=self.run_dir / "locks",
            operation="vnext_graph_transition",
        )
        acquired = False
        try:
            if not lock.acquire(owner):
                raise RunSessionError(f"run lock is already held for {self.run_id}")
            acquired = True
            yield
        except LockError as exc:
            raise RunSessionError(str(exc)) from exc
        finally:
            if acquired:
                lock.release(owner)


class NodeRunner:
    """Prepare or accept an owned PartialState without mutating upstream fields."""

    def __init__(self, session: RunSession, owner: str) -> None:
        self.session = session
        self.owner = owner

    def prepare(
        self,
        node_id: str,
        *,
        artifacts: Mapping[str, ArtifactEnvelope | ArtifactRef],
        dependency_digests: Mapping[str, str],
    ) -> PendingNodeWrite:
        with self.session._lock(self.owner):
            state = self.session.state()
            if node_id in state.accepted:
                raise StateInvariantError(f"node {node_id} is already accepted")
            refs: dict[str, ArtifactRef] = {}
            for field_name, artifact in artifacts.items():
                if isinstance(artifact, ArtifactEnvelope):
                    refs[field_name] = self.session.artifacts.put(artifact)
                elif isinstance(artifact, ArtifactRef):
                    if not self.session.artifacts.contains(artifact):
                        raise StateInvariantError(
                            f"ArtifactRef for {field_name} is not a persisted artifact"
                        )
                    refs[field_name] = artifact
                else:
                    raise StateInvariantError(f"unsupported artifact for {field_name}")
            commit_id, generation_id = NodeTransaction.new_identity(node_id)
            next_state = self.session.graph.apply(
                state,
                node_id=node_id,
                outputs=refs,
                dependency_digests=dependency_digests,
                commit_id=commit_id,
            )
            pending = NodeTransaction.prepare(
                self.session.run_dir,
                node_id=node_id,
                base_state=state,
                next_state=next_state,
                outputs=refs,
                dependency_digests=dependency_digests,
                graph_digest=canonical_sha256(self.session.graph.descriptor()),
                commit_id=commit_id,
                generation_id=generation_id,
            )
            # This event is intentionally invisible until the matching commit
            # directory exists.  Its pre-promotion durability makes restart
            # recovery able to accept a prepared node without rerunning it.
            self.session._append_state_event(next_state, pending)
            return pending

    def accept(
        self,
        pending: PendingNodeWrite | None = None,
        *,
        node_id: str | None = None,
        artifacts: Mapping[str, ArtifactEnvelope | ArtifactRef] | None = None,
        dependency_digests: Mapping[str, str] | None = None,
    ) -> PersistentGraphState:
        if pending is None:
            if node_id is None or artifacts is None or dependency_digests is None:
                raise StateInvariantError("accept requires a pending write or node inputs")
            pending = self.prepare(
                node_id,
                artifacts=artifacts,
                dependency_digests=dependency_digests,
            )
        with self.session._lock(self.owner):
            state = self.session.state()
            if pending.node_id in state.accepted:
                raise StateInvariantError(f"node {pending.node_id} is already accepted")
            if canonical_sha256(state.to_dict()) != pending.base_state_sha256:
                raise StateInvariantError("prepared write does not match current accepted state")
            try:
                NodeTransaction.promote(self.session.run_dir, pending)
            except NodeTransactionError as exc:
                raise RunSessionError(str(exc)) from exc
            accepted = self.session.state()
            if pending.node_id not in accepted.accepted:
                raise RunSessionError("promoted commit did not publish its state event")
            self.session._write_current_pointer(accepted, pending)
            self.session.checkpoint()
            return accepted

    def execute(
        self,
        node_id: str,
        *,
        artifacts: Mapping[str, ArtifactEnvelope | ArtifactRef],
        dependency_digests: Mapping[str, str],
    ) -> PersistentGraphState:
        return self.accept(
            node_id=node_id,
            artifacts=artifacts,
            dependency_digests=dependency_digests,
        )
