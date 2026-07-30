"""MODE:P Pilot - independent-episode orchestrator for the Director pipeline.

Usage:
    python -m mode_p_pilot <episode-script> [--session-dir <dir>]

Production processes every scene in the uploaded episode. An active project
background is resolved automatically; the episode need not be a substring of it.

The orchestrator runs local deterministic steps (ingest, batch, facts, bible,
ledger) and prepares everything the Director LLM agent needs.
It does NOT make creative decisions or call LLMs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from script_ingest import ingest_script, IngestError
from batch_scheduler import ScheduleError, schedule_batches
from script_facts_tool import FactsError, generate_facts, load_digest, validate_facts
from episode_templates import (
    EpisodeTemplateError,
    generate_visual_bible,
    generate_continuity_ledger,
)
from episode_docs_check import check_episode_docs
from batch_state_machine import StateMachineError, load_state
from run_mode_p import initialise
from pipeline_telemetry import files_byte_size, record_event
from session_lock import LockError, session_lock
from project_context import (
    ProjectContextError,
    build_background_packet,
    resolve_episode,
)


def parse_scene_range(range_str: str, max_scenes: int) -> list[int]:
    """Parse '1-3', '2', or '1,3,5' into a list of 1-based scene indices."""
    indices: list[int] = []
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a.strip()), int(b.strip())
            if start < 1 or end > max_scenes or start > end:
                raise ValueError(f"Invalid scene range '{part}': must be 1-{max_scenes}")
            indices.extend(range(start, end + 1))
        else:
            n = int(part.strip())
            if n < 1 or n > max_scenes:
                raise ValueError(f"Scene {n} out of range (1-{max_scenes})")
            indices.append(n)
    return sorted(set(indices))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _scene_batch_map(batch_manifest: dict) -> dict[int, int]:
    result: dict[int, int] = {}
    for batch in batch_manifest["batches"]:
        for scene_index in batch["scene_indices"]:
            if scene_index in result:
                raise ValueError(f"scene {scene_index} occurs in multiple batches")
            result[scene_index] = batch["batch_index"]
    return result


def _read_script_lines(script_path: Path, encoding: str) -> list[str]:
    try:
        return script_path.read_text(encoding=encoding).splitlines()
    except (LookupError, UnicodeDecodeError):
        return script_path.read_text(encoding="utf-8-sig").splitlines()


def _render_scene_context(
    script_lines: list[str],
    scene: dict,
    shared_paths: list[Path],
    batch_index: int,
    total_batches: int,
    project_paths: list[Path] | None = None,
) -> str:
    start, end = scene["start_line"], scene["end_line"]
    numbered = [
        f"L{line_number}: {script_lines[line_number - 1]}"
        for line_number in range(start, end + 1)
    ]
    lines = [
        "# MODE:P Scene Context",
        "",
        f"Scene: {scene['index']} | Director batch: {batch_index}/{total_batches}",
        f"Header: {scene['header_line']}",
        "",
        "## Director Episode Context",
        "",
    ]
    for path in shared_paths:
        if path.name != "SCRIPT_STRUCTURE.json":
            lines.append(f"- `{path.resolve()}`")
    if project_paths:
        lines.extend(["", "## Selected Project Context", ""])
        for path in project_paths:
            lines.append(f"- `{path.resolve()}`")
    lines.extend(["", "## Exact Script Excerpt", "", *numbered, ""])
    return "\n".join(lines)


def _prepare_scene_sessions(
    script_path: Path,
    digest_data: dict,
    batch_manifest: dict,
    base_dir: Path,
    project_paths: list[Path] | None = None,
) -> dict[int, Path]:
    batch_map = _scene_batch_map(batch_manifest)
    script_lines = _read_script_lines(script_path, digest_data["encoding"])
    shared_paths = [
        base_dir / name for name in batch_manifest["shared_documents"]
    ]
    missing = [str(path) for path in shared_paths if not path.is_file()]
    if missing:
        raise ValueError(f"cannot prepare scene sessions; missing shared files: {missing}")
    by_index = {scene["index"]: scene for scene in digest_data["scenes"]}
    sessions: dict[int, Path] = {}
    records: list[dict] = []
    for scene_index in batch_manifest["selected_scenes"]:
        scene = by_index[scene_index]
        session = base_dir / "scenes" / f"scene_{scene_index:03d}"
        context = session / "SCENE_CONTEXT.md"
        body = _render_scene_context(
            script_lines,
            scene,
            shared_paths,
            batch_map[scene_index],
            batch_manifest["total_batches"],
            project_paths,
        )
        if context.exists() and context.read_text(encoding="utf-8") != body:
            if (session / "RUN_STATE.json").exists():
                raise ValueError(
                    f"scene {scene_index} context changed after initialization; "
                    "run dependency invalidation before continuing"
                )
            context.write_text(body, encoding="utf-8")
        elif not context.exists():
            context.parent.mkdir(parents=True, exist_ok=True)
            context.write_text(body, encoding="utf-8")
        if initialise(
            context,
            session,
            batch_map[scene_index],
            batch_manifest["total_batches"],
        ) != 0:
            raise ValueError(f"scene {scene_index} session initialization failed")
        sessions[scene_index] = session
        records.append({
            "scene_index": scene_index,
            "batch_index": batch_map[scene_index],
            "session_path": str(session.resolve()),
            "context_sha256": _sha256(context),
        })
    _atomic_json(base_dir / "SCENE_SESSIONS.json", {
        "schema_version": "1.0",
        "script_source_hash": digest_data["source_content_hash"],
        "scenes": records,
    })
    return sessions


def _root_stage(prep_stage: str, sessions: dict[int, Path], base_dir: Path) -> str:
    if prep_stage != "ready_for_scene_design":
        return prep_stage
    stages: list[str] = []
    for session in sessions.values():
        try:
            stages.append(load_state(session).stage)
        except StateMachineError:
            return "invalid_scene_state"
    if not stages or "director_batch" in stages:
        return "director_batch"
    for candidate in ("structural_precheck", "dp_batch", "final_check"):
        if candidate in stages:
            return candidate
    if all(stage == "batch_commit" for stage in stages):
        review_state = base_dir / "episode_review" / "REVIEW_STATE.json"
        if review_state.is_file():
            try:
                status = json.loads(review_state.read_text(encoding="utf-8")).get("status")
            except (OSError, UnicodeError, json.JSONDecodeError):
                return "invalid_episode_review"
            if status == "passed" and (base_dir / "delivery").is_dir():
                return "delivery"
            if status == "revision_required":
                return "director_batch"
            if status == "blocked":
                return "blocked"
        return "episode_review"
    return "batch_commit"


def _write_root_state(
    base_dir: Path,
    prep_stage: str,
    digest_data: dict,
    batch_manifest: dict,
    sessions: dict[int, Path],
) -> None:
    scene_states = []
    for index, session in sorted(sessions.items()):
        state = load_state(session)
        scene_states.append({
            "scene_index": index,
            "session_path": str(session.resolve()),
            "stage": state.stage,
            "artifact_generation": state.artifact_generation,
            "master_sha256": state.master_sha256,
            "manifest_sha256": state.manifest_sha256,
        })
    unsigned = {
        "schema_version": "1.0",
        "script_source_hash": digest_data["source_content_hash"],
        "stage": _root_stage(prep_stage, sessions, base_dir),
        "active_scenes": batch_manifest["selected_scenes"],
        "total_batches": batch_manifest["total_batches"],
        "scene_states": scene_states,
    }
    state = dict(unsigned)
    state["state_sha256"] = hashlib.sha256(
        json.dumps(
            unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    _atomic_json(base_dir / "RUN_STATE.json", state)


def _run_pilot_impl(script_path: Path, scenes: list[int] | None = None,
                     session_dir: Path | None = None,
                     max_scenes_per_batch: int | None = None,
                     project_binding: dict | None = None) -> int:
    """Advance local preparation without overwriting Director-authored files."""
    print(f"Ingesting script: {script_path}")
    try:
        digest = ingest_script(script_path)
    except IngestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"  Found {digest.scene_count} scene(s) in {digest.encoding}")
    if project_binding is None:
        try:
            project_binding = resolve_episode(script_path)
        except ProjectContextError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    base_dir = session_dir or Path(project_binding["session_dir"])
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR: Cannot create session directory: {exc}", file=sys.stderr)
        return 1
    print(f"Session directory: {base_dir}")
    _atomic_json(base_dir / "EPISODE_BINDING.json", project_binding)
    print(
        f"  Episode binding: {project_binding['episode_id']} "
        f"({project_binding['mode']})"
    )

    project_paths: list[Path] = []
    if project_binding.get("project_dir"):
        project_dir = Path(project_binding["project_dir"])
        for name in (
            "PROJECT_SOURCE_INDEX.json",
            "PROJECT_VISUAL_BIBLE.md",
            "PROJECT_CONTINUITY_LEDGER.md",
            "ASSET_REQUIREMENTS.md",
        ):
            path = project_dir / name
            if not path.is_file():
                print(f"ERROR: Missing project context file: {path}", file=sys.stderr)
                return 1
        try:
            background_packet = base_dir / "PROJECT_BACKGROUND_PACKET.md"
            build_background_packet(
                script_path, background_packet, project_binding=project_binding
            )
        except ProjectContextError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        project_paths = [
            background_packet,
            project_dir / "PROJECT_VISUAL_BIBLE.md",
            project_dir / "PROJECT_CONTINUITY_LEDGER.md",
        ]

    # A Director-resolved structure may replace an unresolved local parse, but
    # only while it remains bound to the exact same script content.
    digest_path = base_dir / "SCRIPT_STRUCTURE.json"
    digest_data = asdict(digest)
    if digest_path.is_file() and any(
            scene["status"] == "unresolved" for scene in digest_data["scenes"]):
        try:
            existing = load_digest(digest_path)
            if (existing["source_content_hash"] == digest.source_content_hash and
                    all(scene.get("status") == "resolved"
                        for scene in existing["scenes"])):
                digest_data = existing
                print("  Using Director-resolved scene boundaries from existing structure")
        except FactsError:
            pass

    available_scenes = [scene["index"] for scene in digest_data["scenes"]]
    active_scenes = available_scenes if scenes is None else list(scenes)
    if (not active_scenes or active_scenes != sorted(set(active_scenes)) or
            any(index not in available_scenes for index in active_scenes)):
        print(
            f"ERROR: Active scenes must be unique, ascending, and within {available_scenes}",
            file=sys.stderr)
        return 2
    if active_scenes == available_scenes:
        print(f"  Processing all {len(available_scenes)} scene(s)")
    else:
        print(
            f"  Active scenes: {active_scenes}; full-episode facts remain loaded "
            f"for all {len(available_scenes)} scenes")

    digest_data["active_scenes"] = active_scenes
    try:
        digest_path.write_text(
            json.dumps(digest_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Cannot write script structure: {exc}", file=sys.stderr)
        return 1
    print(f"  Script structure -> {digest_path}")

    unresolved_boundaries = any(
        scene.get("status") == "unresolved" for scene in digest_data["scenes"])
    if unresolved_boundaries:
        print("  [BLOCKED] Scene boundaries remain unresolved")

    # Generate the facts skeleton once.  A re-run must preserve Director work.
    facts_path = base_dir / "SCRIPT_FACTS.md"
    if not facts_path.exists():
        try:
            generate_facts(digest_path, facts_path)
        except FactsError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"  Facts skeleton -> {facts_path}")
    else:
        print(f"  Preserving existing facts -> {facts_path}")
    facts_report = validate_facts(facts_path, digest_path)
    facts_ready = facts_report.ok and not unresolved_boundaries

    bible_path = base_dir / "EPISODE_VISUAL_BIBLE.md"
    ledger_path = base_dir / "EPISODE_CONTINUITY_LEDGER.md"
    episode_docs_ready = False
    if facts_ready:
        try:
            if not bible_path.exists():
                generate_visual_bible(digest_path, facts_path, bible_path)
                print(f"  Visual Bible skeleton -> {bible_path}")
            else:
                print(f"  Preserving existing Visual Bible -> {bible_path}")
            if not ledger_path.exists():
                generate_continuity_ledger(digest_path, facts_path, ledger_path)
                print(f"  Continuity Ledger skeleton -> {ledger_path}")
            else:
                print(f"  Preserving existing Continuity Ledger -> {ledger_path}")
        except EpisodeTemplateError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        episode_docs_ready = check_episode_docs(
            digest_path, facts_path, bible_path, ledger_path).ok

    try:
        batch_manifest = schedule_batches(
            digest_path, max_scenes_per_batch, scene_indices=active_scenes,
            session_dir=base_dir)
    except ScheduleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    batch_path = base_dir / "BATCH_MANIFEST.json"
    try:
        batch_path.write_text(
            json.dumps(batch_manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Cannot write batch manifest: {exc}", file=sys.stderr)
        return 1
    print(f"  Batch manifest ({batch_manifest.mode}, {batch_manifest.total_batches} batch(es)) -> {batch_path}")
    if batch_manifest.warning:
        print(f"  [WARN] {batch_manifest.warning}")

    if unresolved_boundaries:
        prep_stage = "awaiting_scene_boundary_resolution"
    elif not facts_ready:
        prep_stage = "awaiting_script_facts"
    elif not episode_docs_ready:
        prep_stage = "awaiting_episode_documents"
    else:
        prep_stage = "ready_for_scene_design"

    scene_sessions: dict[int, Path] = {}
    if prep_stage == "ready_for_scene_design":
        try:
            scene_sessions = _prepare_scene_sessions(
                script_path, digest_data, batch_manifest.to_dict(), base_dir,
                project_paths,
            )
            print(f"  Scene sessions -> {base_dir / 'SCENE_SESSIONS.json'}")
        except (OSError, UnicodeError, ValueError, StateMachineError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    status_path = base_dir / "PILOT_PREP_STATUS.json"
    try:
        status_path.write_text(json.dumps({
            "schema_version": "1.0",
            "stage": prep_stage,
            "script_source_hash": digest_data["source_content_hash"],
            "episode_id": project_binding["episode_id"],
            "episode_version": project_binding["episode_sha256"],
            "project_mode": project_binding["mode"],
            "project_id": project_binding["project_id"],
            "active_scenes": active_scenes,
            "facts_ready": facts_ready,
            "episode_documents_ready": episode_docs_ready,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Cannot write preparation status: {exc}", file=sys.stderr)
        return 1

    try:
        _write_root_state(
            base_dir, prep_stage, digest_data, batch_manifest.to_dict(), scene_sessions
        )
    except (OSError, UnicodeError, ValueError, StateMachineError) as exc:
        print(f"ERROR: Cannot write root run state: {exc}", file=sys.stderr)
        return 1

    print()
    print("=" * 60)
    print(f"Local preparation stage: {prep_stage}")
    if prep_stage == "awaiting_scene_boundary_resolution":
        print("Next: Director resolves scene boundaries in SCRIPT_STRUCTURE.json.")
    elif prep_stage == "awaiting_script_facts":
        print("Next: the same Director fills SCRIPT_FACTS.md with source line references.")
    elif prep_stage == "awaiting_episode_documents":
        print("Next: the same Director completes Visual Bible and Continuity Ledger.")
    else:
        print("Next: the same Director designs every batch listed in BATCH_MANIFEST.json.")
        print("Each batch runs Master -> derived views -> structural precheck -> fresh DP.")
        print("After all batches, run Episode Review before delivery.")
    print("=" * 60)

    return 0


def run_pilot(script_path: Path, scenes: list[int] | None = None,
              session_dir: Path | None = None,
              max_scenes_per_batch: int | None = None) -> int:
    """Run local episode preparation and record real stage measurements."""
    try:
        project_binding = resolve_episode(script_path)
    except ProjectContextError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    base_dir = session_dir or Path(project_binding["session_dir"])
    started = time.monotonic()
    try:
        with session_lock(base_dir):
            result = _run_pilot_impl(
                script_path, scenes, base_dir, max_scenes_per_batch,
                project_binding,
            )
    except LockError as exc:
        print(f"ERROR: Concurrent MODE:P session is already running: {exc}", file=sys.stderr)
        result = 1
    record_event(
        base_dir,
        event_type="local",
        stage="pilot_prepare_or_refresh",
        status="completed" if result == 0 else "failed",
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([script_path]),
        output_bytes=files_byte_size([
            base_dir / "SCRIPT_STRUCTURE.json",
            base_dir / "SCRIPT_FACTS.md",
            base_dir / "EPISODE_VISUAL_BIBLE.md",
            base_dir / "EPISODE_CONTINUITY_LEDGER.md",
            base_dir / "BATCH_MANIFEST.json",
            base_dir / "SCENE_SESSIONS.json",
            base_dir / "RUN_STATE.json",
            base_dir / "EPISODE_BINDING.json",
        ]),
        result_code=result,
        error_code="" if result == 0 else f"return_{result}",
    )
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="MODE:P Pilot - current-episode orchestrator."
    )
    parser.add_argument("script", type=Path, help="Path to the current episode script")
    parser.add_argument("--session-dir", type=Path, default=None,
                        help=(
                            "Engineering override for the session output directory; "
                            "default is the automatic project/episode content-version path"
                        ))
    parser.add_argument("--max-scenes-per-batch", type=int, default=None,
                        help=(
                            "Engineering batch-size override; production users omit it and "
                            "the scheduler uses measured budgets"
                        ))
    args = parser.parse_args()

    if not args.script.is_file():
        print(f"Script not found: {args.script}", file=sys.stderr)
        return 2

    return run_pilot(args.script, None, args.session_dir, args.max_scenes_per_batch)


if __name__ == "__main__":
    raise SystemExit(main())
