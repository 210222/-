"""Evidence-bound single-scene runtime used by the full-script MODE:P host.

The Claude Code task owns creative Director work and invokes a fresh DP.  This
module owns deterministic precheck, state transitions, atomic working/delivery
publishing, and crash recovery.  It never accepts independently authored views:
both views must be the current local derivation of the canonical Master.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

from batch_state_machine import (
    BatchStage,
    StateMachineError,
    bind_manifest,
    init_state,
    load_state,
    record_batch_commit,
    record_check,
    record_dp_review,
    transition,
)
from dp_contract import DP_READY_SENTENCE, parse_dp_feedback
from session_lock import (
    LockError,
    commit,
    prepare_staging,
    recover,
    verify_commit,
)
from structural_precheck import PrecheckReport, run_final_checks, run_precheck
from model_acceptance_guard import (
    AcceptanceGuardError,
    require_acceptance_director_provenance,
)
from pipeline_telemetry import (
    files_byte_size,
    record_event,
    telemetry_root_for_scene,
)


READY = DP_READY_SENTENCE


def read_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="gbk")
    return text.lstrip("\ufeff")


def _atomic_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    temporary.write_text(body, encoding="utf-8")
    temporary.replace(path)


def _atomic_copy(source: Path, target: Path) -> None:
    if source.resolve() == target.resolve():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.{time.time_ns()}.tmp")
    shutil.copy2(source, temporary)
    temporary.replace(target)


def write_status(session: Path, status: str, detail: str = "") -> None:
    body = f"# MODE:P Scene Session\n\n状态：{status}。\n"
    if detail:
        body += f"\n{detail.strip()}\n"
    _atomic_text(session / "STATUS.md", body)


def _ensure_state(session: Path, batch_index: int, total_batches: int) -> None:
    state_path = session / "RUN_STATE.json"
    if state_path.exists():
        state = load_state(session)
        if state.batch_index != batch_index or state.total_batches != total_batches:
            raise StateMachineError(
                "existing scene state is bound to a different batch plan"
            )
        return
    init_state(session, batch_index, total_batches)
    transition(session, BatchStage.SCRIPT_PARSE)
    transition(session, BatchStage.DIRECTOR_BATCH)


def initialise(
    context: Path,
    session: Path,
    batch_index: int = 1,
    total_batches: int = 1,
) -> int:
    """Create or safely resume one scene session."""
    if not context.is_file():
        print(f"Scene Context does not exist: {context}", file=sys.stderr)
        return 2
    try:
        session.mkdir(parents=True, exist_ok=True)
        recover(session)
        target = session / "SCENE_CONTEXT.md"
        if target.exists() and target.read_bytes() != context.read_bytes():
            if (session / "RUN_STATE.json").exists():
                raise StateMachineError(
                    "Scene Context changed after state initialization; invalidate the session first"
                )
        else:
            _atomic_copy(context, target)
        _ensure_state(session, batch_index, total_batches)
        state = load_state(session)
        if state.stage == BatchStage.BATCH_COMMIT.value:
            write_status(session, "已交付")
        elif state.stage == BatchStage.DP_BATCH.value:
            write_status(session, "等待全新 DP")
        elif state.stage == BatchStage.STRUCTURAL_PRECHECK.value:
            write_status(session, "结构预检进行中")
        elif state.stage == BatchStage.FINAL_CHECK.value:
            write_status(session, "最终检查进行中")
        else:
            write_status(session, "等待导演 Master")
        print(f"Scene session ready: {session}")
        return 0
    except (OSError, LockError, StateMachineError) as exc:
        print(f"Scene initialization failed: {exc}", file=sys.stderr)
        return 1


def _write_check_reports(
    session: Path,
    generation: int,
    report: PrecheckReport,
    prefix: str,
) -> dict[str, Path]:
    root = session / "reports" / f"generation-{generation:04d}"
    paths: dict[str, Path] = {}
    for result in report.results:
        name = f"{prefix}{result.name}"
        path = root / f"{name}.txt"
        status = "PASS" if result.passed else "FAIL"
        _atomic_text(path, f"{status} {result.name}\n{result.output.strip()}\n")
        paths[result.name] = path
    return paths


def _revision_report(session: Path, title: str, report: PrecheckReport) -> None:
    failures = [result for result in report.results if not result.passed]
    lines = ["# Director Revision Request", "", title, "", "## Failures", ""]
    for result in failures:
        detail = result.output.strip() or "deterministic check failed"
        lines.append(f"- {result.name}: {detail[:600]}")
    body = "\n".join(lines) + "\n"
    _atomic_text(session / "DIRECTOR_REVISION_REQUEST.md", body)
    _atomic_text(session / "CHECK_REPORT.md", body)


def _cleanup_build(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    parent = path.parent
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()


def do_precheck(
    master: Path,
    session: Path,
    batch_index: int = 1,
    total_batches: int = 1,
) -> int:
    """Compile and atomically publish one Master-derived working tree."""
    if not master.is_file():
        print(f"Master file not found: {master}", file=sys.stderr)
        return 2
    build = session / ".build" / uuid.uuid4().hex
    try:
        require_acceptance_director_provenance(session)
        session.mkdir(parents=True, exist_ok=True)
        recover(session)
        _ensure_state(session, batch_index, total_batches)
        state = load_state(session)
        canonical_master = session / "DIRECTOR_MASTER.md"
        if state.stage == BatchStage.DIRECTOR_BATCH.value:
            _atomic_copy(master, canonical_master)
            state = transition(
                session, BatchStage.STRUCTURAL_PRECHECK,
                master_path=canonical_master,
            )
        elif state.stage == BatchStage.STRUCTURAL_PRECHECK.value:
            if not canonical_master.is_file() or canonical_master.read_bytes() != master.read_bytes():
                raise StateMachineError(
                    "cannot replace Master while structural evidence is in progress"
                )
        else:
            raise StateMachineError(
                f"precheck requires director_batch, got {state.stage}"
            )

        report = run_precheck(canonical_master, session, build)
        state = load_state(session)
        report_paths = _write_check_reports(
            session, state.artifact_generation, report, ""
        )
        manifest_build = build / "SHOT_MANIFEST.json"

        if not report.ok:
            if manifest_build.is_file():
                bind_manifest(session, manifest_build)
            for result in report.results:
                record_check(
                    session, result.name, result.passed, report_paths[result.name]
                )
            _revision_report(
                session,
                "结构预检失败。只修复列出的 Master 字段或受影响边界。",
                report,
            )
            transition(session, BatchStage.DIRECTOR_BATCH)
            write_status(session, "结构预检失败，等待导演修复")
            print(f"Structural precheck FAILED. See {session / 'DIRECTOR_REVISION_REQUEST.md'}")
            return 1

        required = {
            "SHOT_MANIFEST.json": build / "SHOT_MANIFEST.json",
            "STORYBOARD.md": build / "STORYBOARD.md",
            "VIDEO_PROMPT.md": build / "VIDEO_PROMPT.md",
        }
        transaction = prepare_staging(session, required)
        published = commit(
            session,
            "structural_precheck",
            batch_index,
            transaction.name,
            target="working",
        )
        ok, issues = verify_commit(session, "working")
        if not ok:
            raise LockError(f"working commit verification failed: {issues}")

        bind_manifest(session, session / "working" / "SHOT_MANIFEST.json")
        for result in report.results:
            record_check(
                session, result.name, result.passed, report_paths[result.name]
            )
        transition(session, BatchStage.DP_BATCH)
        (session / "DIRECTOR_REVISION_REQUEST.md").unlink(missing_ok=True)
        (session / "CHECK_REPORT.md").unlink(missing_ok=True)
        write_status(
            session,
            "等待全新 DP",
            f"working commit: {published.manifest_sha256}",
        )
        print("Structural precheck passed - ready for DP.")
        return 0
    except (
        OSError,
        LockError,
        StateMachineError,
        AcceptanceGuardError,
        ValueError,
    ) as exc:
        print(f"Structural precheck failed: {exc}", file=sys.stderr)
        return 1
    finally:
        _cleanup_build(build)


def _same_file_content(left: Path, right: Path) -> bool:
    return left.is_file() and right.is_file() and left.read_bytes() == right.read_bytes()


def _copy_dp_feedback(session: Path, source: Path, attempt: int) -> Path:
    destination = session / "reviews" / f"dp-{attempt:04d}.md"
    _atomic_text(destination, read_text(source).strip() + "\n")
    return destination


def submit(
    session: Path,
    storyboard: Path,
    video: Path,
    dp_feedback: Path,
    master: Path | None = None,
) -> int:
    """Record current DP evidence and publish only source-bound derived views."""
    if not session.is_dir():
        print(f"Session does not exist: {session}", file=sys.stderr)
        return 2
    try:
        recover(session)
        state = load_state(session)
        if state.stage != BatchStage.DP_BATCH.value:
            raise StateMachineError(f"DP submit requires dp_batch, got {state.stage}")

        canonical_master = session / "DIRECTOR_MASTER.md"
        if master is not None and not _same_file_content(master, canonical_master):
            raise StateMachineError("submitted Master is not the bound canonical Master")
        working_storyboard = session / "working" / "STORYBOARD.md"
        working_video = session / "working" / "VIDEO_PROMPT.md"
        if not _same_file_content(storyboard, working_storyboard):
            raise StateMachineError("Storyboard is not the current Master-derived view")
        if not _same_file_content(video, working_video):
            raise StateMachineError("Video Prompt is not the current Master-derived view")
        if not dp_feedback.is_file():
            raise StateMachineError(f"DP feedback does not exist: {dp_feedback}")
        ok, issues = verify_commit(session, "working")
        if not ok:
            raise LockError(f"working tree is not a valid atomic commit: {issues}")

        parsed = parse_dp_feedback(read_text(dp_feedback))
        review_path = _copy_dp_feedback(session, dp_feedback, state.dp_attempts + 1)
        if parsed.status == "blocked":
            from dp_contract import validate_dp_contract
            valid, problems = validate_dp_contract(parsed)
            if not valid:
                raise StateMachineError(
                    "invalid DP feedback: " + "; ".join(problems)
                )
            write_status(session, "DP 输入阻断", parsed.block_reason)
            print("DP review blocked by a required missing input.")
            return 3

        declared = "ready" if parsed.is_ready else "revise"
        state = record_dp_review(session, declared, review_path)
        if state.dp_review and state.dp_review.get("status") == "blocked":
            write_status(
                session,
                "已阻断",
                "同一 DP 问题在 Master 未变化时重复；需要检查输入或人工裁决。",
            )
            print("DP loop blocked by repeated unchanged issue evidence.")
            return 3

        if declared == "revise":
            feedback = read_text(review_path).strip()
            _atomic_text(
                session / "DIRECTOR_REVISION_REQUEST.md",
                "# Director Revision Request\n\n"
                "只修复下列 Shot 及真正受影响的相邻边界；先修改 Master。\n\n"
                f"{feedback}\n",
            )
            transition(session, BatchStage.DIRECTOR_BATCH)
            write_status(session, "等待导演修订")
            print("Revision requested.")
            return 1

        transition(session, BatchStage.FINAL_CHECK)
        final_report = run_final_checks(canonical_master, session)
        state = load_state(session)
        _write_check_reports(
            session, state.artifact_generation, final_report, "final_"
        )
        composite = session / "reports" / f"generation-{state.artifact_generation:04d}" / "final_master_sync.txt"
        final_lines = []
        for result in final_report.results:
            final_lines.append(
                f"{'PASS' if result.passed else 'FAIL'} {result.name}\n{result.output.strip()}"
            )
        _atomic_text(composite, "\n\n".join(final_lines) + "\n")
        record_check(session, "final_master_sync", final_report.ok, composite)
        if not final_report.ok:
            _revision_report(
                session,
                "DP 已 READY，但最终哈希/结构检查失败；READY 已失效。",
                final_report,
            )
            transition(session, BatchStage.DIRECTOR_BATCH)
            write_status(session, "最终检查失败，等待导演修复")
            print("Final checks failed; READY invalidated.")
            return 1

        transition(session, BatchStage.BATCH_COMMIT)
        state = load_state(session)
        files = {
            "STORYBOARD.md": working_storyboard,
            "VIDEO_PROMPT.md": working_video,
        }
        transaction = prepare_staging(session, files)
        manifest = commit(
            session,
            "scene_delivery",
            state.batch_index,
            transaction.name,
            target="delivery",
        )
        ok, issues = verify_commit(session, "delivery")
        if not ok:
            raise LockError(f"delivery commit verification failed: {issues}")
        commit_evidence = (
            session / "commits" /
            f"delivery-{manifest.transaction_id}.json"
        )
        record_batch_commit(session, commit_evidence)
        (session / "DIRECTOR_REVISION_REQUEST.md").unlink(missing_ok=True)
        (session / "CHECK_REPORT.md").unlink(missing_ok=True)
        write_status(
            session,
            "已交付",
            f"delivery commit: {manifest.manifest_sha256}",
        )
        print(f"Delivered atomically: {session / 'delivery'}")
        return 0
    except (OSError, LockError, StateMachineError, ValueError) as exc:
        print(f"Submission failed: {exc}", file=sys.stderr)
        return 1


_initialise_impl = initialise
_do_precheck_impl = do_precheck
_submit_impl = submit


def initialise(
    context: Path,
    session: Path,
    batch_index: int = 1,
    total_batches: int = 1,
) -> int:
    started = time.monotonic()
    result = _initialise_impl(context, session, batch_index, total_batches)
    record_event(
        telemetry_root_for_scene(session),
        event_type="local",
        stage="scene_initialize",
        status="completed" if result == 0 else "failed",
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([context]),
        output_bytes=files_byte_size([
            session / "SCENE_CONTEXT.md",
            session / "RUN_STATE.json",
            session / "STATUS.md",
        ]),
        result_code=result,
        error_code="" if result == 0 else f"return_{result}",
    )
    return result


def do_precheck(
    master: Path,
    session: Path,
    batch_index: int = 1,
    total_batches: int = 1,
) -> int:
    started = time.monotonic()
    result = _do_precheck_impl(master, session, batch_index, total_batches)
    record_event(
        telemetry_root_for_scene(session),
        event_type="local",
        stage="structural_precheck",
        status="completed" if result == 0 else "failed",
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([master, session / "SCENE_CONTEXT.md"]),
        output_bytes=files_byte_size([
            session / "working", session / "reports", session / "CHECK_REPORT.md"
        ]),
        result_code=result,
        error_code="" if result == 0 else f"return_{result}",
    )
    return result


def submit(
    session: Path,
    storyboard: Path,
    video: Path,
    dp_feedback: Path,
    master: Path | None = None,
) -> int:
    started = time.monotonic()
    result = _submit_impl(session, storyboard, video, dp_feedback, master)
    if result == 0:
        status = "completed"
    elif result == 3:
        status = "blocked"
    elif result == 1 and (session / "DIRECTOR_REVISION_REQUEST.md").is_file():
        status = "revision_required"
    else:
        status = "failed"
    record_event(
        telemetry_root_for_scene(session),
        event_type="local",
        stage="scene_dp_submit_and_final_check",
        status=status,
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([
            storyboard, video, dp_feedback, *([master] if master else [])
        ]),
        output_bytes=files_byte_size([
            session / "delivery", session / "reviews", session / "reports",
            session / "DIRECTOR_REVISION_REQUEST.md",
        ]),
        result_code=result,
        error_code="" if status in {"completed", "revision_required"} else f"return_{result}",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Operate one evidence-bound MODE:P scene session."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("context", type=Path)
    init.add_argument("session", type=Path)
    init.add_argument("--batch", type=int, default=1)
    init.add_argument("--total", type=int, default=1)

    precheck = subparsers.add_parser("precheck")
    precheck.add_argument("master", type=Path)
    precheck.add_argument("session", type=Path)
    precheck.add_argument("--batch", type=int, default=1)
    precheck.add_argument("--total", type=int, default=1)

    submitted = subparsers.add_parser("submit")
    submitted.add_argument("session", type=Path)
    submitted.add_argument("storyboard", type=Path)
    submitted.add_argument("video", type=Path)
    submitted.add_argument("dp_feedback", type=Path)
    submitted.add_argument("--master", type=Path)

    status = subparsers.add_parser("status")
    status.add_argument("session", type=Path)

    args = parser.parse_args()
    if args.command == "init":
        return initialise(args.context, args.session, args.batch, args.total)
    if args.command == "precheck":
        return do_precheck(args.master, args.session, args.batch, args.total)
    if args.command == "submit":
        return submit(
            args.session, args.storyboard, args.video, args.dp_feedback, args.master
        )
    try:
        print(json.dumps(load_state(args.session).__dict__, ensure_ascii=False, indent=2))
        return 0
    except StateMachineError as exc:
        print(f"State read failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
