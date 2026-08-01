"""Durable run sessions, checkpoint recovery, and graph-node execution."""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterator, Mapping

from mode_p_vnext.concurrency_lock import LockError, SessionLock
from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    canonical_json_bytes,
    canonical_sha256,
)
from mode_p_vnext.pipeline.graph import StateGraph
from mode_p_vnext.pipeline.invalidation import (
    FieldInvalidator,
    InvalidationRecord,
    InvalidationResult,
)
from mode_p_vnext.pipeline.state import (
    PERSISTENCE_SCHEMA_VERSION,
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
RUN_SCHEMA_NAME = "mode_p_vnext_run"
RUN_RECORD_DIGEST_FIELD = "record_sha256"


class RunSessionError(RuntimeError):
    """Raised where a run cannot be read or advanced safely."""


def _safe_run_id(value: str) -> str:
    """Return one unambiguous filesystem component or fail closed."""

    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or ":" in value
        or value.endswith((" ", "."))
        or any(ord(character) < 32 for character in value)
    ):
        raise RunSessionError("run_id must be a safe, non-empty path component")
    return value


@dataclass(frozen=True)
class ResumePlan:
    """Validated restart boundary, expressed only with content digests."""

    checkpoint_sequence: int
    accepted_node_ids: tuple[str, ...]
    runnable_node_ids: tuple[str, ...]


class RunSession:
    """Filesystem-backed source of truth for one vNext graph run."""

    def __init__(self, run_dir: Path, graph: StateGraph) -> None:
        candidate = Path(run_dir)
        if candidate.is_symlink():
            raise RunSessionError("run directory must not be a symbolic link")
        self.run_dir = candidate.resolve()
        self.graph = graph
        self._validate_run_record()
        self.artifacts = ArtifactRepository(self.run_dir)
        self.cache = PersistentNodeCache(self.run_dir)

    @classmethod
    def create(
        cls, runs_root: Path, *, run_id: str, graph: StateGraph
    ) -> "RunSession":
        safe_run_id = _safe_run_id(run_id)
        root = Path(runs_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        run_dir = (root / safe_run_id).resolve()
        if run_dir.parent != root:
            raise RunSessionError("run_id must stay within the runs root")
        try:
            run_dir.mkdir()
        except FileExistsError as exc:
            raise RunSessionError(f"run already exists: {safe_run_id}") from exc
        for name in (
            "artifacts",
            "commits",
            CHECKPOINTS_DIRNAME,
            "projections",
            "evidence",
        ):
            (run_dir / name).mkdir()
        record_body = {
            "schema_name": RUN_SCHEMA_NAME,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "run_id": safe_run_id,
            "format_version": 1,
            "graph": graph.descriptor(),
            "graph_digest": canonical_sha256(graph.descriptor()),
        }
        record = {
            **record_body,
            RUN_RECORD_DIGEST_FIELD: canonical_sha256(record_body),
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

    def _unresolved_staging_dirs(self) -> tuple[Path, ...]:
        staging_root = self.run_dir / "staging"
        if not staging_root.exists():
            return ()
        if not staging_root.is_dir() or staging_root.is_symlink():
            raise RunSessionError("staging root must be a regular directory")
        candidates: list[Path] = []
        for path in sorted(staging_root.iterdir(), key=lambda item: item.name):
            if path.name == "abandoned":
                continue
            if not path.is_dir() or path.is_symlink():
                raise RunSessionError("staging contains an unsafe prepared-write entry")
            candidates.append(path)
        return tuple(candidates)

    def runner(self, *, owner: str) -> "NodeRunner":
        return NodeRunner(self, owner)

    def state(self) -> PersistentGraphState:
        """Replay only state transitions bound to trusted commit/event evidence."""
        state, _ = self._replay_event_chain()
        self._validate_current_pointer(state)
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
        with self._lock(owner):
            candidates = self._unresolved_staging_dirs()
            if not candidates:
                return ()
            if len(candidates) != 1:
                raise RunSessionError(
                    "multiple unresolved prepared writes make recovery ambiguous"
                )
            for staging_dir in candidates:
                pending = NodeTransaction.read_prepared(staging_dir)
                state = self.state()
                self._validate_graph_state(pending.next_state)
                if pending.node_id in state.accepted:
                    continue
                if canonical_sha256(state.to_dict()) != pending.base_state_sha256:
                    raise RunSessionError(
                        "prepared write base state no longer matches the last accepted state"
                    )
                try:
                    expected = self.graph.apply(
                        state,
                        node_id=pending.node_id,
                        outputs=pending.outputs,
                        dependency_digests=pending.dependency_digests,
                        commit_id=pending.commit_id,
                    )
                except StateInvariantError as exc:
                    raise RunSessionError(str(exc)) from exc
                if canonical_sha256(expected.to_dict()) != pending.state_sha256:
                    raise RunSessionError(
                        "prepared write does not reproduce the graph transition"
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
        state, state_history = self._replay_event_chain()
        self._validate_current_pointer(state)
        changed: dict[str, str] = {}
        for node_id, acceptance in state.accepted.items():
            node = self.graph.node(node_id)
            for field_name, expected in acceptance.dependency_digests.items():
                if field_name in node.input_fields and field_name in supplied_input_digests:
                    actual = supplied_input_digests[field_name]
                    if actual != expected:
                        changed[field_name] = actual
        checkpoint_sequence = self._latest_matching_checkpoint(state_history)
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
            base_state = self.state()
            result = FieldInvalidator(self.graph).invalidate(
                base_state,
                changed_field_digests=changed_field_digests,
                reason=reason,
            )
            if result.invalidated_node_ids:
                self._append_state_event(
                    result.state,
                    pending=None,
                    invalidation_record=result.record,
                )
                self._write_current_pointer(result.state, pending=None)
                self.checkpoint()
            return result

    def _validate_run_record(self) -> None:
        record = self._run_record()
        expected_fields = {
            "schema_name",
            "schema_version",
            "run_id",
            "format_version",
            "graph",
            "graph_digest",
            RUN_RECORD_DIGEST_FIELD,
        }
        if set(record) != expected_fields:
            raise RunSessionError("RUN record fields do not match the v2.2 schema")
        if (
            record.get("schema_name") != RUN_SCHEMA_NAME
            or record.get("schema_version") != PERSISTENCE_SCHEMA_VERSION
            or record.get("format_version") != 1
        ):
            raise RunSessionError("unsupported RUN record schema")
        unsigned_record = {
            key: value
            for key, value in record.items()
            if key != RUN_RECORD_DIGEST_FIELD
        }
        if canonical_sha256(unsigned_record) != record.get(RUN_RECORD_DIGEST_FIELD):
            raise RunSessionError("RUN record digest is invalid")
        stored_run_id = _safe_run_id(record.get("run_id"))
        if stored_run_id != self.run_dir.name:
            raise RunSessionError("RUN record identity does not match its directory")
        stored_graph = record.get("graph")
        if canonical_sha256(stored_graph) != record.get("graph_digest"):
            raise RunSessionError("RUN graph descriptor digest is invalid")
        if canonical_sha256(self.graph.descriptor()) != record.get("graph_digest"):
            raise RunSessionError("requested graph does not match the run graph")

    def _run_record(self) -> Mapping[str, Any]:
        try:
            value = json.loads(
                (self.run_dir / RUN_FILENAME).read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RunSessionError("invalid RUN.json") from exc
        if not isinstance(value, Mapping):
            raise RunSessionError("RUN.json must contain an object")
        return value

    def _validate_current_pointer(self, state: PersistentGraphState) -> None:
        """Bind the mutable pointer to the trusted event and commit evidence."""

        path = self.current_pointer_path
        if not state.current_commit_id:
            if path.exists():
                raise RunSessionError("current pointer exists without an accepted commit")
            return
        if not path.is_file() or path.is_symlink():
            raise RunSessionError("current pointer must be a regular file")
        try:
            pointer = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RunSessionError("current pointer is invalid") from exc
        if not isinstance(pointer, Mapping):
            raise RunSessionError("current pointer must contain an object")

        legacy_fields = {"commit_id", "manifest_sha256", "updated_at_epoch"}
        graph_fields = {
            "sequence",
            "state_sha256",
            "commit_id",
            "manifest_sha256",
            "node_id",
        }
        fields = set(pointer)
        if fields not in (legacy_fields, graph_fields):
            raise RunSessionError("current pointer fields are invalid")
        if pointer.get("commit_id") != state.current_commit_id:
            raise RunSessionError("current pointer commit does not match the event chain")

        manifest_path = (
            self.run_dir
            / "commits"
            / state.current_commit_id
            / "COMMIT_MANIFEST.json"
        )
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise RunSessionError("current pointer commit manifest is missing")
        if pointer.get("manifest_sha256") != sha256(
            manifest_path.read_bytes()
        ).hexdigest():
            raise RunSessionError("current pointer manifest digest is invalid")

        if fields == graph_fields:
            if (
                isinstance(pointer.get("sequence"), bool)
                or pointer.get("sequence") != state.event_sequence
                or pointer.get("state_sha256")
                != canonical_sha256(state.to_dict())
            ):
                raise RunSessionError("current pointer state does not match the event chain")

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

    def _replay_event_chain(
        self,
    ) -> tuple[PersistentGraphState, Mapping[int, PersistentGraphState]]:
        """Replay graph transitions independently of checkpoint files.

        Checkpoints are recoverable performance snapshots, not an authority
        boundary: each is accepted only after it matches this commit-bound
        event chain. This prevents a re-hashed standalone checkpoint from
        becoming state authority.
        """

        state = PersistentGraphState.empty(self.run_id)
        history: dict[int, PersistentGraphState] = {0: state}
        for event in self._events():
            candidate = PersistentGraphState.from_dict(event["state"])
            if candidate.event_sequence <= state.event_sequence:
                continue
            if candidate.event_sequence != state.event_sequence + 1:
                raise RunSessionError("accepted state events have a sequence gap")
            self._validate_graph_state(candidate)
            transition = event.get("transition")
            if not isinstance(transition, Mapping):
                raise RunSessionError("state event transition is missing or invalid")
            base_state_sha256 = str(transition.get("base_state_sha256", ""))
            if base_state_sha256 != canonical_sha256(state.to_dict()):
                raise RunSessionError("state event base state does not match replay")
            kind = transition.get("kind")
            if kind == "node":
                pending_commit_id = str(event.get("commit_id") or "")
                legacy_manifest = (
                    self.run_dir
                    / "commits"
                    / pending_commit_id
                    / "COMMIT_MANIFEST.json"
                )
                if not legacy_manifest.is_file():
                    # A durable prepared event is intentionally appended before
                    # its staging directory is atomically promoted.
                    continue
            if kind == "node":
                self._validate_node_event(state, candidate, event)
            elif kind == "invalidation":
                self._validate_invalidation_event(state, candidate, event)
            else:
                raise RunSessionError("state event has an unknown transition kind")
            state = candidate
            history[state.event_sequence] = state
        return state, MappingProxyType(history)

    def _latest_matching_checkpoint(
        self, state_history: Mapping[int, PersistentGraphState]
    ) -> int:
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
                trusted = state_history.get(sequence)
                if (
                    state.event_sequence == sequence
                    and trusted is not None
                    and canonical_sha256(state.to_dict())
                    == canonical_sha256(trusted.to_dict())
                ):
                    return sequence
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return 0

    def _validate_graph_state(self, state: PersistentGraphState) -> None:
        try:
            self.graph.validate_state(state)
        except StateInvariantError as exc:
            raise RunSessionError(str(exc)) from exc
        for field_name, ref in state.outputs.items():
            if not self.artifacts.contains(ref):
                raise RunSessionError(
                    f"persisted artifact for '{field_name}' no longer verifies"
                )

    def _validate_node_event(
        self,
        state: PersistentGraphState,
        candidate: PersistentGraphState,
        event: Mapping[str, Any],
    ) -> None:
        commit_id = str(event.get("commit_id") or "")
        node_id = str(event.get("node_id") or "")
        if not commit_id or not node_id:
            raise RunSessionError("node state event requires commit_id and node_id")
        acceptance = candidate.accepted.get(node_id)
        if acceptance is None or acceptance.commit_id != commit_id:
            raise RunSessionError("node state event does not match node acceptance")
        node = self.graph.node(node_id)
        outputs = {
            field_name: candidate.outputs[field_name]
            for field_name in node.owns_fields
        }
        try:
            expected = self.graph.apply(
                state,
                node_id=node_id,
                outputs=outputs,
                dependency_digests=acceptance.dependency_digests,
                commit_id=commit_id,
                cache_key=acceptance.cache_key,
            )
        except StateInvariantError as exc:
            raise RunSessionError(str(exc)) from exc
        if canonical_sha256(expected.to_dict()) != canonical_sha256(candidate.to_dict()):
            raise RunSessionError("node state event does not reproduce its graph transition")
        if not self._is_promoted_commit(
            commit_id,
            str(event["state_sha256"]),
            node_id=node_id,
            base_state_sha256=canonical_sha256(state.to_dict()),
        ):
            raise RunSessionError("prepared node write is not yet atomically promoted")

    def _validate_invalidation_event(
        self,
        state: PersistentGraphState,
        candidate: PersistentGraphState,
        event: Mapping[str, Any],
    ) -> None:
        if str(event.get("commit_id") or "") != state.current_commit_id:
            raise RunSessionError("invalidation event must retain the current commit")
        if candidate.current_commit_id != state.current_commit_id:
            raise RunSessionError("invalidation event changed the current commit")
        raw_record = event.get("invalidation_record")
        if not isinstance(raw_record, Mapping):
            raise RunSessionError("invalidation event has no invalidation record")
        try:
            expected = FieldInvalidator(self.graph).invalidate(
                state,
                changed_field_digests=raw_record["changed_field_digests"],
                reason=str(raw_record["reason"]),
            )
        except (KeyError, StateInvariantError) as exc:
            raise RunSessionError("invalidation event record is invalid") from exc
        if canonical_sha256(expected.record.to_dict()) != canonical_sha256(
            raw_record
        ):
            raise RunSessionError("invalidation event record does not match graph closure")
        if canonical_sha256(expected.state.to_dict()) != canonical_sha256(
            candidate.to_dict()
        ):
            raise RunSessionError(
                "invalidation event does not reproduce its graph transition"
            )

    def _is_promoted_commit(
        self,
        commit_id: str,
        state_sha256: str,
        *,
        node_id: str,
        base_state_sha256: str,
    ) -> bool:
        commit_dir = self.run_dir / "commits" / commit_id
        legacy_manifest_path = commit_dir / "COMMIT_MANIFEST.json"
        if not commit_dir.is_dir() or not legacy_manifest_path.is_file():
            return False
        companion_path = commit_dir / "MANIFEST.json"
        if not companion_path.is_file() or companion_path.is_symlink():
            raise RunSessionError("promoted commit has no regular vNext commit manifest")
        try:
            legacy = json.loads(legacy_manifest_path.read_text(encoding="utf-8"))
            companion = json.loads(companion_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RunSessionError("commit manifest is invalid") from exc
        metadata = legacy.get("metadata")
        if not isinstance(metadata, Mapping):
            raise RunSessionError("commit manifest has no transition metadata")
        if not (
            companion.get("schema_name") == "mode_p_vnext_commit_manifest"
            and companion.get("schema_version") == PERSISTENCE_SCHEMA_VERSION
            and companion.get("commit_id") == commit_id
            and companion.get("node_id") == node_id
            and companion.get("base_state_sha256") == base_state_sha256
            and companion.get("state_sha256") == state_sha256
            and companion.get("legacy_manifest_sha256")
            == sha256(legacy_manifest_path.read_bytes()).hexdigest()
            and metadata.get("node_id") == node_id
            and metadata.get("base_state_sha256") == base_state_sha256
            and metadata.get("state_sha256") == state_sha256
        ):
            raise RunSessionError(
                "commit manifest does not bind the state event transition"
            )
        return True

    def _append_state_event(
        self,
        state: PersistentGraphState,
        pending: PendingNodeWrite | None,
        invalidation_record: InvalidationRecord | None = None,
    ) -> None:
        if pending is not None:
            transition: Mapping[str, Any] = {
                "kind": "node",
                "base_state_sha256": pending.base_state_sha256,
            }
            commit_id: str | None = pending.commit_id
            node_id: str | None = pending.node_id
            record: Mapping[str, object] | None = None
        else:
            if invalidation_record is None:
                raise RunSessionError("non-node state events require an invalidation record")
            if not state.current_commit_id:
                raise RunSessionError("invalidation requires an accepted current commit")
            prior_state, _ = self._replay_event_chain()
            transition = {
                "kind": "invalidation",
                "base_state_sha256": canonical_sha256(prior_state.to_dict()),
            }
            commit_id = state.current_commit_id
            node_id = None
            record = invalidation_record.to_dict()
        event = {
            "state": state.to_dict(),
            "state_sha256": canonical_sha256(state.to_dict()),
            "commit_id": commit_id,
            "node_id": node_id,
            "transition": transition,
            "invalidation_record": record,
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
            if self.session._unresolved_staging_dirs():
                raise RunSessionError(
                    "run has an unresolved prepared write; accept or recover it first"
                )
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
