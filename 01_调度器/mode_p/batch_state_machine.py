"""Evidence-bound MODE:P batch state machine.

The state file records hashes for the exact Master, Manifest, local reports,
DP response, batch commit, and episode review that authorize each transition.
No revision limit or heuristic stop condition exists here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from pathlib import Path, PurePosixPath
from typing import Any, Callable, TypeVar


class BatchStage(Enum):
    BOOTSTRAP = "bootstrap"
    SCRIPT_PARSE = "script_parse"
    DIRECTOR_BATCH = "director_batch"
    STRUCTURAL_PRECHECK = "structural_precheck"
    DP_BATCH = "dp_batch"
    FINAL_CHECK = "final_check"
    BATCH_COMMIT = "batch_commit"
    EPISODE_REVIEW = "episode_review"
    DELIVERY = "delivery"


VALID_TRANSITIONS = {
    BatchStage.BOOTSTRAP: {BatchStage.SCRIPT_PARSE},
    BatchStage.SCRIPT_PARSE: {BatchStage.DIRECTOR_BATCH},
    BatchStage.DIRECTOR_BATCH: {BatchStage.STRUCTURAL_PRECHECK},
    BatchStage.STRUCTURAL_PRECHECK: {BatchStage.DIRECTOR_BATCH, BatchStage.DP_BATCH},
    BatchStage.DP_BATCH: {BatchStage.DIRECTOR_BATCH, BatchStage.FINAL_CHECK},
    BatchStage.FINAL_CHECK: {BatchStage.DIRECTOR_BATCH, BatchStage.BATCH_COMMIT},
    BatchStage.BATCH_COMMIT: {BatchStage.DIRECTOR_BATCH, BatchStage.EPISODE_REVIEW},
    BatchStage.EPISODE_REVIEW: {BatchStage.DIRECTOR_BATCH, BatchStage.DELIVERY},
    BatchStage.DELIVERY: set(),
}

STRUCTURAL_CHECKS = {
    "master_compiler", "view_deriver", "master_sync_check",
    "boundary_check", "reference_plan_check", "sd2_preflight",
}
FINAL_CHECKS = {"final_master_sync"}
_HASH_LENGTH = 64


@dataclass
class BatchState:
    schema_version: str
    session_id: str
    stage: str
    batch_index: int
    total_batches: int
    artifact_generation: int = 0
    master_path: str = ""
    master_sha256: str = ""
    manifest_path: str = ""
    manifest_sha256: str = ""
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    dp_review: dict[str, Any] | None = None
    dp_issue_history: list[dict[str, Any]] = field(default_factory=list)
    episode_review: dict[str, Any] | None = None
    committed_batches: list[dict[str, Any]] = field(default_factory=list)
    dp_attempts: int = 0
    revision_count: int = 0
    transition_sequence: int = 0
    updated_at: str = ""
    state_sha256: str = ""


class StateMachineError(ValueError):
    """Raised when state or transition evidence is invalid."""


_T = TypeVar("_T")


def _locked_mutation(function: Callable[..., _T]) -> Callable[..., _T]:
    """Serialize every state mutation through the session writer lock."""
    @wraps(function)
    def wrapped(session_dir: Path, *args: Any, **kwargs: Any) -> _T:
        from session_lock import session_lock

        with session_lock(session_dir):
            return function(session_dir, *args, **kwargs)

    return wrapped


def _canonical_hash(data: dict[str, Any]) -> str:
    payload = {key: value for key, value in data.items() if key != "state_sha256"}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_hash(path: Path) -> str:
    if not path.is_file():
        raise StateMachineError(f"evidence file not found: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _session_relative(session_dir: Path, path: Path) -> str:
    session = session_dir.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(session)
    except ValueError as exc:
        raise StateMachineError(f"evidence must stay inside session: {path}") from exc
    return relative.as_posix()


def _state_file(session_dir: Path, raw: str, field_name: str) -> Path:
    if not raw or "\\" in raw:
        raise StateMachineError(f"{field_name} is not a portable session path")
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts:
        raise StateMachineError(f"{field_name} escapes the session")
    path = (session_dir / Path(*pure.parts)).resolve()
    try:
        path.relative_to(session_dir.resolve())
    except ValueError as exc:
        raise StateMachineError(f"{field_name} escapes the session") from exc
    return path


def _validate_state(state: BatchState, session_dir: Path) -> None:
    if state.schema_version != "1.1":
        raise StateMachineError("unsupported RUN_STATE schema_version")
    if state.session_id != session_dir.name:
        raise StateMachineError("RUN_STATE session_id does not match its directory")
    try:
        BatchStage(state.stage)
    except ValueError as exc:
        raise StateMachineError(f"invalid stage: {state.stage}") from exc
    if (
        isinstance(state.batch_index, bool) or not isinstance(state.batch_index, int)
        or isinstance(state.total_batches, bool) or not isinstance(state.total_batches, int)
        or state.total_batches < 1 or not 1 <= state.batch_index <= state.total_batches
    ):
        raise StateMachineError("invalid batch index/total")
    for name in ("artifact_generation", "dp_attempts", "revision_count", "transition_sequence"):
        value = getattr(state, name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise StateMachineError(f"invalid {name}")
    for name in ("master_sha256", "manifest_sha256", "state_sha256"):
        value = getattr(state, name)
        if value and (not isinstance(value, str) or len(value) != _HASH_LENGTH):
            raise StateMachineError(f"invalid {name}")
    if bool(state.master_path) != bool(state.master_sha256):
        raise StateMachineError("Master path/hash binding is incomplete")
    if bool(state.manifest_path) != bool(state.manifest_sha256):
        raise StateMachineError("Manifest path/hash binding is incomplete")
    if state.master_path:
        _state_file(session_dir, state.master_path, "master_path")
    if state.manifest_path:
        _state_file(session_dir, state.manifest_path, "manifest_path")
    if not isinstance(state.checks, dict):
        raise StateMachineError("checks must be an object")
    if not isinstance(state.dp_issue_history, list):
        raise StateMachineError("dp_issue_history must be an array")
    for record in state.dp_issue_history:
        if not isinstance(record, dict) or set(record) != {
            "master_sha256", "fingerprint", "issue_identities", "attempt"
        }:
            raise StateMachineError("dp_issue_history contains a malformed record")
        if any(
            not isinstance(record[name], str) or len(record[name]) != _HASH_LENGTH
            for name in ("master_sha256", "fingerprint")
        ):
            raise StateMachineError("dp_issue_history contains an invalid hash")
        if (
            not isinstance(record["issue_identities"], list)
            or any(not isinstance(item, str) or not item for item in record["issue_identities"])
            or len(record["issue_identities"]) != len(set(record["issue_identities"]))
        ):
            raise StateMachineError("dp_issue_history issue identities are malformed")
        if (
            isinstance(record["attempt"], bool) or not isinstance(record["attempt"], int)
            or record["attempt"] < 1
        ):
            raise StateMachineError("dp_issue_history attempt is invalid")
    if not isinstance(state.committed_batches, list):
        raise StateMachineError("committed_batches must be an array")
    committed_indices = [item.get("batch_index") for item in state.committed_batches if isinstance(item, dict)]
    if len(committed_indices) != len(state.committed_batches) or len(committed_indices) != len(set(committed_indices)):
        raise StateMachineError("committed_batches are malformed or duplicated")
    try:
        datetime.fromisoformat(state.updated_at)
    except (TypeError, ValueError) as exc:
        raise StateMachineError("updated_at must be ISO-8601") from exc


def write_state(session_dir: Path, state: BatchState) -> None:
    session_dir.mkdir(parents=True, exist_ok=True)
    state.updated_at = datetime.now(timezone.utc).isoformat()
    raw = asdict(state)
    state.state_sha256 = _canonical_hash(raw)
    raw["state_sha256"] = state.state_sha256
    path = session_dir / "RUN_STATE.json"
    temporary = path.with_name(f".RUN_STATE.tmp-{os.getpid()}-{time.time_ns()}")
    temporary.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


@_locked_mutation
def init_state(session_dir: Path, batch_index: int, total_batches: int) -> BatchState:
    if total_batches < 1 or not 1 <= batch_index <= total_batches:
        raise StateMachineError("batch index must be within 1..total_batches")
    if (session_dir / "RUN_STATE.json").exists():
        raise StateMachineError("RUN_STATE already exists; load it instead of overwriting")
    state = BatchState(
        schema_version="1.1",
        session_id=session_dir.name,
        stage=BatchStage.BOOTSTRAP.value,
        batch_index=batch_index,
        total_batches=total_batches,
    )
    write_state(session_dir, state)
    return state


def load_state(session_dir: Path) -> BatchState:
    path = session_dir / "RUN_STATE.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateMachineError(f"cannot read RUN_STATE: {exc}") from exc
    expected_fields = {item.name for item in fields(BatchState)}
    if not isinstance(raw, dict) or set(raw) != expected_fields:
        raise StateMachineError("RUN_STATE fields do not match schema")
    expected_hash = raw.get("state_sha256")
    if expected_hash != _canonical_hash(raw):
        raise StateMachineError("RUN_STATE integrity hash mismatch")
    try:
        state = BatchState(**raw)
    except TypeError as exc:
        raise StateMachineError(f"invalid RUN_STATE: {exc}") from exc
    _validate_state(state, session_dir)
    return state


def _assert_master_current(state: BatchState, session_dir: Path) -> None:
    if not state.master_path:
        raise StateMachineError("no Master is bound to this design generation")
    path = _state_file(session_dir, state.master_path, "master_path")
    if _file_hash(path) != state.master_sha256:
        raise StateMachineError("Master changed; prior evidence is stale")


def _assert_artifacts_current(state: BatchState, session_dir: Path) -> None:
    _assert_master_current(state, session_dir)
    if not state.manifest_path:
        raise StateMachineError("no Manifest is bound to this design generation")
    path = _state_file(session_dir, state.manifest_path, "manifest_path")
    if _file_hash(path) != state.manifest_sha256:
        raise StateMachineError("Manifest changed; prior evidence is stale")


@_locked_mutation
def bind_manifest(session_dir: Path, manifest_path: Path) -> BatchState:
    state = load_state(session_dir)
    if state.stage != BatchStage.STRUCTURAL_PRECHECK.value:
        raise StateMachineError("Manifest can only be bound during structural_precheck")
    _assert_master_current(state, session_dir)
    state.manifest_path = _session_relative(session_dir, manifest_path)
    state.manifest_sha256 = _file_hash(manifest_path)
    state.checks = {}
    write_state(session_dir, state)
    return state


@_locked_mutation
def record_check(
    session_dir: Path, check_name: str, passed: bool, report_path: Path
) -> BatchState:
    state = load_state(session_dir)
    stage = BatchStage(state.stage)
    allowed = STRUCTURAL_CHECKS if stage == BatchStage.STRUCTURAL_PRECHECK else (
        FINAL_CHECKS if stage == BatchStage.FINAL_CHECK else set()
    )
    if check_name not in allowed:
        raise StateMachineError(f"check '{check_name}' is not valid during {stage.value}")
    if not isinstance(passed, bool):
        raise StateMachineError("passed must be boolean")
    if stage == BatchStage.STRUCTURAL_PRECHECK and passed and not state.manifest_path:
        raise StateMachineError("a successful structural check requires a bound Manifest")
    if state.manifest_path:
        _assert_artifacts_current(state, session_dir)
    else:
        _assert_master_current(state, session_dir)
    state.checks[check_name] = {
        "passed": passed,
        "stage": stage.value,
        "artifact_generation": state.artifact_generation,
        "master_sha256": state.master_sha256,
        "manifest_sha256": state.manifest_sha256,
        "report_path": _session_relative(session_dir, report_path),
        "report_sha256": _file_hash(report_path),
    }
    write_state(session_dir, state)
    return state


@_locked_mutation
def record_dp_review(session_dir: Path, status: str, review_path: Path) -> BatchState:
    state = load_state(session_dir)
    if state.stage != BatchStage.DP_BATCH.value:
        raise StateMachineError("DP result can only be recorded during dp_batch")
    if status not in {"ready", "revise"}:
        raise StateMachineError("DP status must be ready or revise; blocked is derived from stall evidence")
    _assert_artifacts_current(state, session_dir)
    from dp_contract import (
        DpContractError,
        detect_stall,
        manifest_shot_ids,
        parse_dp_feedback,
        validate_dp_contract,
    )

    try:
        feedback = parse_dp_feedback(review_path.read_text(encoding="utf-8"))
        manifest_path = _state_file(session_dir, state.manifest_path, "manifest_path")
        valid, problems = validate_dp_contract(
            feedback, manifest_shot_ids(manifest_path)
        )
    except (OSError, UnicodeError, DpContractError) as exc:
        raise StateMachineError(f"invalid DP feedback: {exc}") from exc
    if not valid:
        raise StateMachineError("invalid DP feedback: " + "; ".join(problems))
    parsed_status = "ready" if feedback.is_ready else "revise"
    if status != parsed_status:
        raise StateMachineError(
            f"declared DP status {status} does not match feedback status {parsed_status}"
        )
    state.dp_attempts += 1
    issue_fingerprint: str | None = None
    stalled = False
    recorded_status = status
    if feedback.status == "issues":
        issue_fingerprint = feedback.fingerprint(state.master_sha256)
        stalled = detect_stall(
            [record["fingerprint"] for record in state.dp_issue_history],
            issue_fingerprint,
        )
        if not stalled:
            state.dp_issue_history.append({
                "master_sha256": state.master_sha256,
                "fingerprint": issue_fingerprint,
                "issue_identities": sorted(
                    f"{issue.shot_id}:{issue.field}" for issue in feedback.issues
                ),
                "attempt": state.dp_attempts,
            })
        else:
            recorded_status = "blocked"
    state.dp_review = {
        "status": recorded_status,
        "artifact_generation": state.artifact_generation,
        "master_sha256": state.master_sha256,
        "manifest_sha256": state.manifest_sha256,
        "review_path": _session_relative(session_dir, review_path),
        "review_sha256": _file_hash(review_path),
        "issue_fingerprint": issue_fingerprint,
        "stalled": stalled,
    }
    write_state(session_dir, state)
    return state


@_locked_mutation
def record_batch_commit(session_dir: Path, commit_path: Path) -> BatchState:
    state = load_state(session_dir)
    if state.stage != BatchStage.BATCH_COMMIT.value:
        raise StateMachineError("batch commit evidence requires batch_commit stage")
    _assert_artifacts_current(state, session_dir)
    state.committed_batches = [
        item for item in state.committed_batches if item["batch_index"] != state.batch_index
    ]
    state.committed_batches.append({
        "batch_index": state.batch_index,
        "artifact_generation": state.artifact_generation,
        "master_sha256": state.master_sha256,
        "manifest_sha256": state.manifest_sha256,
        "commit_path": _session_relative(session_dir, commit_path),
        "commit_sha256": _file_hash(commit_path),
    })
    state.committed_batches.sort(key=lambda item: item["batch_index"])
    write_state(session_dir, state)
    return state


@_locked_mutation
def record_episode_review(session_dir: Path, status: str, review_path: Path) -> BatchState:
    state = load_state(session_dir)
    if state.stage != BatchStage.EPISODE_REVIEW.value:
        raise StateMachineError("episode result requires episode_review stage")
    if status not in {"pass", "revise", "blocked"}:
        raise StateMachineError("episode status must be pass, revise, or blocked")
    _assert_commits_current(state, session_dir)
    state.episode_review = {
        "status": status,
        "review_path": _session_relative(session_dir, review_path),
        "review_sha256": _file_hash(review_path),
        "committed_batch_hashes": [item["commit_sha256"] for item in state.committed_batches],
    }
    write_state(session_dir, state)
    return state


def _assert_record_file_current(
    state: BatchState,
    session_dir: Path,
    record: dict[str, Any] | None,
    path_key: str,
    hash_key: str,
    label: str,
) -> None:
    if not isinstance(record, dict):
        raise StateMachineError(f"{label} evidence is malformed")
    raw_path = record.get(path_key)
    expected_hash = record.get(hash_key)
    if (
        not isinstance(raw_path, str) or not raw_path
        or not isinstance(expected_hash, str) or len(expected_hash) != _HASH_LENGTH
    ):
        raise StateMachineError(f"{label} evidence binding is malformed")
    path = _state_file(session_dir, raw_path, path_key)
    if _file_hash(path) != expected_hash:
        raise StateMachineError(f"{label} evidence changed; prior decision is stale")


def _assert_commits_current(state: BatchState, session_dir: Path) -> None:
    for record in state.committed_batches:
        _assert_record_file_current(
            state, session_dir, record,
            "commit_path", "commit_sha256",
            f"batch {record.get('batch_index')} commit",
        )


def _checks_authorize(
    state: BatchState,
    session_dir: Path,
    required: set[str],
    stage: BatchStage,
) -> bool:
    if set(state.checks) != required:
        return False
    for check_name, record in state.checks.items():
        if (
            record.get("passed") is not True
            or record.get("stage") != stage.value
            or record.get("artifact_generation") != state.artifact_generation
            or record.get("master_sha256") != state.master_sha256
            or record.get("manifest_sha256") != state.manifest_sha256
        ):
            return False
        _assert_record_file_current(
            state, session_dir, record,
            "report_path", "report_sha256", f"{check_name} report",
        )
    return True


def _reset_design_evidence(state: BatchState) -> None:
    state.artifact_generation += 1
    state.master_path = ""
    state.master_sha256 = ""
    state.manifest_path = ""
    state.manifest_sha256 = ""
    state.checks = {}
    state.dp_review = None
    state.episode_review = None


@_locked_mutation
def transition(
    session_dir: Path,
    to_stage: BatchStage,
    *,
    master_path: Path | None = None,
    next_batch_index: int | None = None,
) -> BatchState:
    state = load_state(session_dir)
    current = BatchStage(state.stage)
    if to_stage not in VALID_TRANSITIONS[current]:
        raise StateMachineError(
            f"cannot transition from {current.value} to {to_stage.value}; "
            f"allowed: {sorted(stage.value for stage in VALID_TRANSITIONS[current])}"
        )

    if current == BatchStage.DIRECTOR_BATCH and to_stage == BatchStage.STRUCTURAL_PRECHECK:
        if master_path is None:
            raise StateMachineError("Director output must bind a Master before precheck")
        state.artifact_generation += 1
        state.master_path = _session_relative(session_dir, master_path)
        state.master_sha256 = _file_hash(master_path)
        state.manifest_path = ""
        state.manifest_sha256 = ""
        state.checks = {}
        state.dp_review = None
        state.episode_review = None
    elif master_path is not None:
        raise StateMachineError("master_path is only accepted when entering structural_precheck")

    if current == BatchStage.STRUCTURAL_PRECHECK and to_stage == BatchStage.DP_BATCH:
        _assert_artifacts_current(state, session_dir)
        if not _checks_authorize(
            state, session_dir, STRUCTURAL_CHECKS, BatchStage.STRUCTURAL_PRECHECK
        ):
            raise StateMachineError("current structural checks do not authorize DP")
    elif current == BatchStage.STRUCTURAL_PRECHECK and to_stage == BatchStage.DIRECTOR_BATCH:
        if not any(record.get("passed") is False for record in state.checks.values()):
            raise StateMachineError("return to Director requires a recorded structural failure")
        for name, record in state.checks.items():
            _assert_record_file_current(
                state, session_dir, record,
                "report_path", "report_sha256", f"{name} report",
            )
        state.revision_count += 1
        _reset_design_evidence(state)

    if current == BatchStage.DP_BATCH and to_stage == BatchStage.FINAL_CHECK:
        _assert_artifacts_current(state, session_dir)
        if not state.dp_review or state.dp_review.get("status") != "ready":
            raise StateMachineError("DP READY evidence is required before final_check")
        _assert_record_file_current(
            state, session_dir, state.dp_review,
            "review_path", "review_sha256", "DP review",
        )
        state.checks = {}
    elif current == BatchStage.DP_BATCH and to_stage == BatchStage.DIRECTOR_BATCH:
        if not state.dp_review or state.dp_review.get("status") != "revise":
            raise StateMachineError("return to Director requires DP revise evidence")
        _assert_record_file_current(
            state, session_dir, state.dp_review,
            "review_path", "review_sha256", "DP review",
        )
        state.revision_count += 1
        _reset_design_evidence(state)

    if current == BatchStage.FINAL_CHECK and to_stage == BatchStage.BATCH_COMMIT:
        _assert_artifacts_current(state, session_dir)
        if not _checks_authorize(
            state, session_dir, FINAL_CHECKS, BatchStage.FINAL_CHECK
        ):
            raise StateMachineError("current final checks do not authorize batch_commit")
    elif current == BatchStage.FINAL_CHECK and to_stage == BatchStage.DIRECTOR_BATCH:
        if not any(record.get("passed") is False for record in state.checks.values()):
            raise StateMachineError("return to Director requires a recorded final-check failure")
        for name, record in state.checks.items():
            _assert_record_file_current(
                state, session_dir, record,
                "report_path", "report_sha256", f"{name} report",
            )
        state.revision_count += 1
        _reset_design_evidence(state)

    if current == BatchStage.BATCH_COMMIT:
        _assert_commits_current(state, session_dir)
        committed = {item["batch_index"] for item in state.committed_batches}
        if state.batch_index not in committed:
            raise StateMachineError("current batch has no commit evidence")
        if to_stage == BatchStage.DIRECTOR_BATCH:
            expected = state.batch_index + 1
            if expected > state.total_batches:
                raise StateMachineError("all batches are committed; enter episode_review")
            if next_batch_index is not None and next_batch_index != expected:
                raise StateMachineError(f"next batch must be {expected}")
            state.batch_index = expected
            _reset_design_evidence(state)
        else:
            if committed != set(range(1, state.total_batches + 1)):
                raise StateMachineError("episode_review requires every batch commit")

    if current == BatchStage.EPISODE_REVIEW and to_stage == BatchStage.DELIVERY:
        if not state.episode_review or state.episode_review.get("status") != "pass":
            raise StateMachineError("episode PASS evidence is required for delivery")
        current_hashes = [item["commit_sha256"] for item in state.committed_batches]
        if state.episode_review.get("committed_batch_hashes") != current_hashes:
            raise StateMachineError("episode review is stale for current commits")
        _assert_commits_current(state, session_dir)
        _assert_record_file_current(
            state, session_dir, state.episode_review,
            "review_path", "review_sha256", "episode review",
        )
    elif current == BatchStage.EPISODE_REVIEW and to_stage == BatchStage.DIRECTOR_BATCH:
        if not state.episode_review or state.episode_review.get("status") != "revise":
            raise StateMachineError("return to Director requires episode revise evidence")
        _assert_commits_current(state, session_dir)
        _assert_record_file_current(
            state, session_dir, state.episode_review,
            "review_path", "review_sha256", "episode review",
        )
        if next_batch_index is None or not 1 <= next_batch_index <= state.total_batches:
            raise StateMachineError("episode revision requires an affected batch index")
        state.batch_index = next_batch_index
        state.committed_batches = [
            item for item in state.committed_batches if item["batch_index"] < next_batch_index
        ]
        state.revision_count += 1
        _reset_design_evidence(state)

    state.stage = to_stage.value
    state.transition_sequence += 1
    write_state(session_dir, state)
    return state


def is_complete(session_dir: Path) -> bool:
    try:
        return load_state(session_dir).stage == BatchStage.DELIVERY.value
    except StateMachineError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Operate the MODE:P batch state machine.")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("session", type=Path)
    init.add_argument("--batch", type=int, default=1)
    init.add_argument("--total", type=int, default=1)
    show = sub.add_parser("show")
    show.add_argument("session", type=Path)
    advance = sub.add_parser("advance")
    advance.add_argument("session", type=Path)
    advance.add_argument("stage", choices=[stage.value for stage in BatchStage])
    advance.add_argument("--master", type=Path)
    advance.add_argument("--next-batch", type=int)
    bind = sub.add_parser("bind-manifest")
    bind.add_argument("session", type=Path)
    bind.add_argument("manifest", type=Path)
    check = sub.add_parser("check")
    check.add_argument("session", type=Path)
    check.add_argument("name")
    check.add_argument("result", choices=["pass", "fail"])
    check.add_argument("report", type=Path)
    dp = sub.add_parser("dp")
    dp.add_argument("session", type=Path)
    dp.add_argument("status", choices=["ready", "revise"])
    dp.add_argument("review", type=Path)
    commit = sub.add_parser("commit")
    commit.add_argument("session", type=Path)
    commit.add_argument("evidence", type=Path)
    episode = sub.add_parser("episode")
    episode.add_argument("session", type=Path)
    episode.add_argument("status", choices=["pass", "revise", "blocked"])
    episode.add_argument("review", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "init":
            state = init_state(args.session, args.batch, args.total)
        elif args.command == "show":
            state = load_state(args.session)
            print(json.dumps(asdict(state), ensure_ascii=False, indent=2))
            return 0
        elif args.command == "advance":
            state = transition(
                args.session, BatchStage(args.stage),
                master_path=args.master, next_batch_index=args.next_batch,
            )
        elif args.command == "bind-manifest":
            state = bind_manifest(args.session, args.manifest)
        elif args.command == "check":
            state = record_check(args.session, args.name, args.result == "pass", args.report)
        elif args.command == "dp":
            state = record_dp_review(args.session, args.status, args.review)
        elif args.command == "commit":
            state = record_batch_commit(args.session, args.evidence)
        else:
            state = record_episode_review(args.session, args.status, args.review)
        print(f"State: {state.stage} batch {state.batch_index}/{state.total_batches}")
        return 0
    except (StateMachineError, ValueError) as exc:
        print(f"State operation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
