"""Fail-closed persistence for the A8 raw-source text shadow.

The runtime graph already owns canonical Artifact storage and atomic node
acceptance.  This adapter adds only the A8-specific control records needed to
resume a *composition* run without recalling accepted model stages:

* a hash-bound run configuration;
* immutable structured-Draft / DP audit records; and
* a hash-bound terminal text-shadow report.

None of these records is a second domain artifact authority.  Final values
remain canonical ``ArtifactEnvelope`` instances owned by ``mode_p_vnext``'s
domain and runtime modules.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import ArtifactEnvelope, canonical_json_bytes, canonical_sha256, require_sha256
from mode_p_vnext.pipeline.graph import StateGraph
from mode_p_vnext.runtime.session import RunSession, RunSessionError


RUN_RECORD_FILENAME = "TEXT_SHADOW_RUN.json"
RESULT_FILENAME = "TEXT_SHADOW_RESULT.json"
STAGE_RECORDS_DIRNAME = "stage_records"
RUN_RECORD_SCHEMA = "mode_p_vnext_a8_text_shadow_run"
STAGE_RECORD_SCHEMA = "mode_p_vnext_a8_stage_record"
RESULT_SCHEMA = "mode_p_vnext_a8_text_shadow_result"
SCHEMA_VERSION = "3.0"
_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STAGE_ID = re.compile(r"^[A-Z][A-Z0-9_]{0,31}$")


class TextShadowStorageError(RuntimeError):
    """Raised when A8 persistent evidence is unsafe, stale, or tampered."""


def _safe_component(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SAFE_COMPONENT.fullmatch(value) is None:
        raise TextShadowStorageError(f"{field_name} must be a safe path component")
    return value


def _require_digest(value: object, field_name: str) -> str:
    try:
        require_sha256(value, field_name)  # type: ignore[arg-type]
    except Exception as exc:
        raise TextShadowStorageError(f"{field_name} must be a lowercase SHA-256") from exc
    return str(value)


def _read_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise TextShadowStorageError(f"{label} is not a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TextShadowStorageError(f"{label} is invalid JSON") from exc
    if not isinstance(value, dict):
        raise TextShadowStorageError(f"{label} must contain a JSON object")
    return value


def _atomic_write_immutable(path: Path, payload: bytes) -> None:
    """Publish exact canonical bytes once, never silently overwrite evidence."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise TextShadowStorageError("immutable evidence parent is not a regular directory")
    if path.exists() or path.is_symlink():
        if path.is_file() and not path.is_symlink() and path.read_bytes() == payload:
            return
        raise TextShadowStorageError("immutable evidence path already has different bytes")
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if not path.is_file() or path.is_symlink() or path.read_bytes() != payload:
                raise TextShadowStorageError("concurrent evidence write has different bytes")
        except OSError as exc:
            # A no-overwrite atomic publication primitive is mandatory here.
            # Falling back to os.replace could overwrite a concurrent immutable
            # record, so an unsupported filesystem fails closed instead.
            raise TextShadowStorageError(
                "filesystem does not provide atomic no-overwrite evidence publication"
            ) from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _ensure_safe_runs_root(value: Path) -> Path:
    root = Path(value).expanduser().resolve()
    if root == Path(root.anchor) or root.name in {"", ".", ".."}:
        raise TextShadowStorageError("run root must be a dedicated directory")
    if root.exists() and root.is_symlink():
        raise TextShadowStorageError("run root must not be a symlink")

    # The A8 text shadow may write an evidence directory under the repository,
    # but it may never write into v4 or into the vNext source package itself.
    package_root = Path(__file__).resolve().parents[2]
    scheduler_root = package_root.parent
    v4_root = (scheduler_root / "mode_p").resolve()
    for forbidden, label in ((package_root, "vNext source package"), (v4_root, "v4 runtime")):
        try:
            root.relative_to(forbidden)
        except ValueError:
            continue
        raise TextShadowStorageError(f"run root must not be inside the {label}")
    return root


class TextShadowStorage:
    """A small, immutable A8 control layer around :class:`RunSession`."""

    def __init__(self, session: RunSession, run_record: Mapping[str, Any]) -> None:
        self.session = session
        self.run_dir = session.run_dir
        self._run_record = dict(run_record)

    @property
    def run_record_path(self) -> Path:
        return self.run_dir / RUN_RECORD_FILENAME

    @property
    def stage_records_dir(self) -> Path:
        return self.run_dir / STAGE_RECORDS_DIRNAME

    @property
    def result_path(self) -> Path:
        return self.run_dir / RESULT_FILENAME

    @property
    def run_record(self) -> Mapping[str, Any]:
        return dict(self._run_record)

    @classmethod
    def create_or_open(
        cls,
        *,
        runs_root: Path,
        run_id: str,
        graph: StateGraph,
        write_scope: str,
        episode_id: str,
        scene_id: str,
        source_id: str,
        source_digest: str,
        program_version: str,
        provider_id: str,
        dp_reviewer_id: str,
        created_at_utc: str | None,
    ) -> "TextShadowStorage":
        root = _ensure_safe_runs_root(runs_root)
        safe_run_id = _safe_component(run_id, "run_id")
        for value, name in (
            (episode_id, "episode_id"),
            (scene_id, "scene_id"),
            (source_id, "source_id"),
            (program_version, "program_version"),
            (provider_id, "provider_id"),
            (dp_reviewer_id, "dp_reviewer_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise TextShadowStorageError(f"{name} must be non-empty")
        _require_digest(source_digest, "source_digest")
        if not isinstance(graph, StateGraph):
            raise TextShadowStorageError("graph must be a StateGraph")

        run_dir = root / safe_run_id
        stored_record: dict[str, Any] | None = None
        if run_dir.exists():
            stored_record = cls._validated_record(
                run_dir / RUN_RECORD_FILENAME, RUN_RECORD_SCHEMA, "run record"
            )
            if created_at_utc is None:
                created_at_utc = stored_record.get("created_at_utc")
        if not isinstance(created_at_utc, str) or not created_at_utc.strip():
            raise TextShadowStorageError("created_at_utc is required for a new run")
        expected_body = {
            "schema_name": RUN_RECORD_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "run_id": safe_run_id,
            "write_scope": write_scope,
            "episode_id": episode_id,
            "scene_id": scene_id,
            "source_id": source_id,
            "source_digest": source_digest,
            "program_version": program_version,
            "provider_id": provider_id,
            "dp_reviewer_id": dp_reviewer_id,
            "claim_ceiling": "TEXT_VALIDATED",
            "graph_digest": graph.digest,
            "external_media_started": False,
            "v4_write": False,
            "created_at_utc": created_at_utc,
        }
        try:
            session = (
                RunSession.open(run_dir, graph=graph)
                if run_dir.exists()
                else RunSession.create(
                    root,
                    run_id=safe_run_id,
                    graph=graph,
                    write_scope=write_scope,
                )
            )
        except (RunSessionError, OSError) as exc:
            raise TextShadowStorageError(f"cannot open A8 run session: {exc}") from exc

        record_path = session.run_dir / RUN_RECORD_FILENAME
        if record_path.exists():
            stored = stored_record or cls._validated_record(record_path, RUN_RECORD_SCHEMA, "run record")
            body = {key: value for key, value in stored.items() if key != "record_sha256"}
            if body != expected_body:
                raise TextShadowStorageError("run configuration does not match the existing hash-bound run")
            return cls(session, stored)

        record = {**expected_body, "record_sha256": canonical_sha256(expected_body)}
        _atomic_write_immutable(record_path, canonical_json_bytes(record))
        return cls(session, record)

    @staticmethod
    def _validated_record(path: Path, schema_name: str, label: str) -> dict[str, Any]:
        record = _read_object(path, label)
        supplied = record.get("record_sha256")
        if not isinstance(supplied, str):
            raise TextShadowStorageError(f"{label} lacks record_sha256")
        body = {key: value for key, value in record.items() if key != "record_sha256"}
        if body.get("schema_name") != schema_name or body.get("schema_version") != SCHEMA_VERSION:
            raise TextShadowStorageError(f"{label} schema is unsupported")
        if canonical_sha256(body) != supplied:
            raise TextShadowStorageError(f"{label} digest is invalid")
        return record

    def assert_run_record(self) -> Mapping[str, Any]:
        """Re-read both run records so mutation is rejected before resuming."""

        try:
            # ``RunSession`` validates its separately hash-bound RUN.json.
            self.session._validate_run_record()  # noqa: SLF001 - mandatory A8 integrity boundary
        except RunSessionError as exc:
            raise TextShadowStorageError(f"runtime RUN.json is invalid: {exc}") from exc
        record = self._validated_record(self.run_record_path, RUN_RECORD_SCHEMA, "run record")
        if record != self._run_record:
            raise TextShadowStorageError("run record changed after storage was opened")
        return dict(record)

    def _stage_path(self, stage_id: str) -> Path:
        if not isinstance(stage_id, str) or _STAGE_ID.fullmatch(stage_id) is None:
            raise TextShadowStorageError("stage_id must use a restricted uppercase identifier")
        return self.stage_records_dir / f"{stage_id}.json"

    def load_stage(self, stage_id: str, *, input_sha256: str) -> Mapping[str, Any] | None:
        self.assert_run_record()
        _require_digest(input_sha256, "input_sha256")
        path = self._stage_path(stage_id)
        if not path.exists():
            return None
        record = self._validated_record(path, STAGE_RECORD_SCHEMA, f"{stage_id} stage record")
        body = {key: value for key, value in record.items() if key != "record_sha256"}
        expected = {
            "schema_name",
            "schema_version",
            "stage_id",
            "input_sha256",
            "payload",
            "audit",
        }
        if set(body) != expected or body["stage_id"] != stage_id:
            raise TextShadowStorageError(f"{stage_id} stage record fields are invalid")
        if body["input_sha256"] != input_sha256:
            raise TextShadowStorageError(f"{stage_id} stage record is bound to different inputs")
        if not isinstance(body["payload"], (dict, list)) or not isinstance(body["audit"], dict):
            raise TextShadowStorageError(f"{stage_id} stage record has an invalid payload or audit")
        return dict(body)

    def store_stage(
        self,
        stage_id: str,
        *,
        input_sha256: str,
        payload: Mapping[str, Any] | list[Any],
        audit: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        self.assert_run_record()
        _require_digest(input_sha256, "input_sha256")
        if not isinstance(payload, (Mapping, list)) or not isinstance(audit, Mapping):
            raise TextShadowStorageError("stage payload and audit must be JSON objects or arrays")
        path = self._stage_path(stage_id)
        body: dict[str, Any] = {
            "schema_name": STAGE_RECORD_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "stage_id": stage_id,
            "input_sha256": input_sha256,
            "payload": dict(payload) if isinstance(payload, Mapping) else list(payload),
            "audit": dict(audit),
        }
        record = {**body, "record_sha256": canonical_sha256(body)}
        _atomic_write_immutable(path, canonical_json_bytes(record))
        return dict(body)

    def assert_artifact(self, field_name: str, artifact: ArtifactEnvelope[Any]) -> None:
        """Prove a rehydrated value is exactly the accepted canonical output."""

        if not isinstance(field_name, str) or not field_name.strip():
            raise TextShadowStorageError("field_name must be non-empty")
        if not isinstance(artifact, ArtifactEnvelope):
            raise TextShadowStorageError("rehydrated value must be a canonical ArtifactEnvelope")
        state = self.session.state()
        ref = state.outputs.get(field_name)
        if ref is None:
            raise TextShadowStorageError(f"accepted state has no artifact field '{field_name}'")
        if (
            ref.artifact_id != artifact.artifact_id
            or ref.artifact_type is not artifact.artifact_type
            or ref.schema_version != artifact.schema_version
            or ref.canonical_payload_sha256 != artifact.canonical_payload_sha256
            or ref.artifact_digest != canonical_sha256(artifact)
            or not self.session.artifacts.contains(ref)
        ):
            raise TextShadowStorageError(f"rehydrated '{field_name}' differs from its accepted artifact")

    def write_result(self, result: Mapping[str, Any]) -> Mapping[str, Any]:
        self.assert_run_record()
        if not isinstance(result, Mapping):
            raise TextShadowStorageError("text-shadow result must be a mapping")
        body = {
            "schema_name": RESULT_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "run_id": self.session.run_id,
            "result": dict(result),
        }
        record = {**body, "record_sha256": canonical_sha256(body)}
        _atomic_write_immutable(self.result_path, canonical_json_bytes(record))
        return dict(record)

    def load_result(self) -> Mapping[str, Any] | None:
        self.assert_run_record()
        if not self.result_path.exists():
            return None
        record = self._validated_record(self.result_path, RESULT_SCHEMA, "text-shadow result")
        if record.get("run_id") != self.session.run_id or not isinstance(record.get("result"), dict):
            raise TextShadowStorageError("text-shadow result is not bound to this run")
        return dict(record)
