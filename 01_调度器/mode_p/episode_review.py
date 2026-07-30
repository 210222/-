"""Stateful L6 episode-review protocol for MODE:P.

The Lead Director performs the semantic review.  This module only prepares a
minimal source-bound packet and enforces the loop:

    awaiting_review -> passed
                    -> revision_required -> new delivered scene versions
                                           -> awaiting_review
                    -> blocked (explicit reason only)

There is no fixed round limit.  A pass becomes stale whenever any bound input
changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from scene_bridge import (
    BridgeError,
    delivered_scene_state,
    load_batch_manifest,
)
from pipeline_telemetry import files_byte_size, record_event


_PLACEHOLDER_RE = re.compile(r"\[Director:|<Name>|<N>", re.IGNORECASE)
_AFFECTED_RE = re.compile(r"^Affected scenes:\s*(.+?)\s*$", re.MULTILINE)
_REASON_RE = re.compile(r"^Reason:\s*(.+?)\s*$", re.MULTILINE)
_ENTRY_RE = re.compile(r"^进入边界：\[D\]\s*(.+?)\s*$", re.MULTILINE)
_EXIT_RE = re.compile(r"^交出边界：\[D\]\s*(.+?)\s*$", re.MULTILINE)
_BOUNDARY_HEADER_RE = re.compile(
    r"^##\s+Boundary\s+[A-Za-z0-9_-]+-B\d+\s*\|.*$", re.MULTILINE
)
_HANDOFF_RE = re.compile(r"^交接描述：\[D\]\s*(.+?)\s*$", re.MULTILINE)
_RESULT_MODES = {
    "EPISODE REVIEW: PASS": "passed",
    "EPISODE REVIEW: REVISE": "revision_required",
    "EPISODE REVIEW: BLOCKED": "blocked",
}


class EpisodeReviewError(Exception):
    """Raised when review protocol or provenance is invalid."""


@dataclass
class ReviewItem:
    dimension: str
    scene_index: int | None
    status: str
    detail: str


@dataclass
class ReviewReport:
    checklist: list[ReviewItem] = field(default_factory=list)
    blocked: bool = False
    block_reason: str = ""

    @property
    def ok(self) -> bool:
        return (not self.blocked and
                all(item.status == "ok" for item in self.checklist))


def prepare_review(batch_manifest_path: Path, bible_path: Path,
                   ledger_path: Path, scene_session_dirs: dict[int, Path],
                   review_session_dir: Path) -> dict:
    """Prepare or refresh a minimal episode-review packet."""
    try:
        manifest = load_batch_manifest(batch_manifest_path)
    except BridgeError as exc:
        raise EpisodeReviewError(str(exc)) from exc
    expected_scenes = list(range(1, manifest["total_scenes"] + 1))
    if manifest["selected_scenes"] != expected_scenes:
        raise EpisodeReviewError(
            "Episode Review requires all episode scenes, not a local selection")
    if sorted(scene_session_dirs) != expected_scenes:
        raise EpisodeReviewError(
            f"Episode Review requires scene sessions {expected_scenes}; got "
            f"{sorted(scene_session_dirs)}")

    bible_text = _completed_episode_document(
        bible_path, "# EPISODE_VISUAL_BIBLE", "Visual Bible")
    ledger_text = _completed_episode_document(
        ledger_path, "# EPISODE_CONTINUITY_LEDGER", "Continuity Ledger")

    scene_packets: list[dict] = []
    scene_excerpts: list[tuple[int, str]] = []
    for scene_index in expected_scenes:
        session = scene_session_dirs[scene_index].resolve()
        try:
            state = delivered_scene_state(scene_index, session)
        except BridgeError as exc:
            raise EpisodeReviewError(str(exc)) from exc
        master_path = session / "DIRECTOR_MASTER.md"
        excerpt = _extract_review_excerpt(master_path)
        scene_packets.append({
            "scene_index": scene_index,
            "scene_id": state["scene_id"],
            "session_path": str(session),
            "master_path": str(master_path.resolve()),
            "master_content_hash": state["master_content_hash"],
            "manifest_sha256": state["manifest_sha256"],
            "storyboard_sha256": state["storyboard_sha256"],
            "video_prompt_sha256": state["video_prompt_sha256"],
            "opening_state_keys": state["opening_state_keys"],
            "closing_state_keys": state["closing_state_keys"],
        })
        scene_excerpts.append((scene_index, excerpt))

    unsigned_packet = {
        "schema_version": "1.0",
        "script_source_hash": manifest["script_source_hash"],
        "batch_manifest_path": str(batch_manifest_path.resolve()),
        "batch_manifest_sha256": _file_hash(batch_manifest_path),
        "visual_bible_path": str(bible_path.resolve()),
        "visual_bible_sha256": _file_hash(bible_path),
        "continuity_ledger_path": str(ledger_path.resolve()),
        "continuity_ledger_sha256": _file_hash(ledger_path),
        "scenes": scene_packets,
    }
    packet = dict(unsigned_packet)
    packet["review_input_sha256"] = _object_hash(unsigned_packet)

    review_session_dir.mkdir(parents=True, exist_ok=True)
    state_path = review_session_dir / "REVIEW_STATE.json"
    previous = _load_optional_state(state_path)
    if previous.get("status") == "blocked":
        raise EpisodeReviewError(
            "Episode Review is explicitly blocked; resolve its reason before resuming")
    if (previous.get("status") == "revision_required" and
            not _affected_versions_changed(previous, packet)):
        raise EpisodeReviewError(
            "Affected scenes have no new delivered Master versions; re-review is premature")
    if (previous.get("status") in {"awaiting_review", "passed"} and
            previous.get("review_input_sha256") == packet["review_input_sha256"]):
        return previous

    cycle = int(previous.get("cycle", 0)) + 1
    state = {
        "schema_version": "1.0",
        "status": "awaiting_review",
        "cycle": cycle,
        "review_input_sha256": packet["review_input_sha256"],
        "scene_master_hashes": {
            str(scene["scene_index"]): scene["master_content_hash"]
            for scene in scene_packets
        },
        "affected_scenes": [],
        "block_reason": "",
        "review_result_sha256": "",
    }
    _atomic_write_json(review_session_dir / "EPISODE_REVIEW_PACKET.json", packet)
    _atomic_write_text(
        review_session_dir / "EPISODE_REVIEW_PACKET.md",
        _render_review_packet(packet, scene_excerpts, bible_text, ledger_text))
    _atomic_write_json(state_path, state)
    return state


def submit_review(review_session_dir: Path, review_result_path: Path) -> dict:
    """Accept one natural-language Lead Director review result."""
    state_path = review_session_dir / "REVIEW_STATE.json"
    state = _load_required_json(state_path, "review state")
    packet = _load_required_json(
        review_session_dir / "EPISODE_REVIEW_PACKET.json", "review packet")
    _verify_packet(packet)
    if state.get("status") != "awaiting_review":
        raise EpisodeReviewError(
            f"Review result is only accepted from awaiting_review, got "
            f"{state.get('status')!r}")
    if state.get("review_input_sha256") != packet["review_input_sha256"]:
        raise EpisodeReviewError("Review state is not bound to the current packet")
    if not _packet_dependencies_current(packet):
        raise EpisodeReviewError("Review inputs changed; prepare a new review packet first")

    text = _read_text(review_result_path, "review result").strip()
    nonempty = [line.strip() for line in text.splitlines() if line.strip()]
    if not nonempty or nonempty[0] not in _RESULT_MODES:
        raise EpisodeReviewError(
            "First non-empty line must be EPISODE REVIEW: PASS, REVISE, or BLOCKED")
    status = _RESULT_MODES[nonempty[0]]
    all_scenes = {scene["scene_index"] for scene in packet["scenes"]}
    affected: list[int] = []
    block_reason = ""

    if status == "revision_required":
        match = _AFFECTED_RE.search(text)
        if not match:
            raise EpisodeReviewError("REVISE requires 'Affected scenes: N,...'")
        affected = _parse_scene_list(match.group(1))
        if not affected or any(scene not in all_scenes for scene in affected):
            raise EpisodeReviewError("Affected scenes must be a non-empty episode subset")
        issue_lines = [
            line for line in nonempty[1:]
            if not line.startswith("Affected scenes:")
        ]
        if not issue_lines:
            raise EpisodeReviewError("REVISE requires a concrete issue description")
    elif status == "blocked":
        match = _REASON_RE.search(text)
        if not match or not match.group(1).strip():
            raise EpisodeReviewError("BLOCKED requires a non-empty 'Reason:'")
        block_reason = match.group(1).strip()
    elif _AFFECTED_RE.search(text) or _REASON_RE.search(text):
        raise EpisodeReviewError("PASS must not contain affected scenes or a block reason")

    result_copy = review_session_dir / "EPISODE_REVIEW_RESULT.md"
    _atomic_write_text(result_copy, text + "\n")
    state.update({
        "status": status,
        "affected_scenes": affected,
        "block_reason": block_reason,
        "review_result_sha256": _file_hash(result_copy),
    })
    _atomic_write_json(state_path, state)
    return state


def review_gate(review_session_dir: Path) -> tuple[bool, str]:
    """Return true only for a current, source-bound PASS."""
    try:
        state = _load_required_json(
            review_session_dir / "REVIEW_STATE.json", "review state")
        packet = _load_required_json(
            review_session_dir / "EPISODE_REVIEW_PACKET.json", "review packet")
        _verify_packet(packet)
        if state.get("status") != "passed":
            return False, f"Episode Review status is {state.get('status')!r}, not passed"
        if state.get("review_input_sha256") != packet["review_input_sha256"]:
            return False, "Review state is stale relative to its packet"
        result_path = review_session_dir / "EPISODE_REVIEW_RESULT.md"
        if state.get("review_result_sha256") != _file_hash(result_path):
            return False, "Review result hash is stale"
        if not _packet_dependencies_current(packet):
            return False, "A bound review dependency changed after PASS"
        first = next(
            (line.strip() for line in _read_text(result_path, "review result").splitlines()
             if line.strip()), "")
        if first != "EPISODE REVIEW: PASS":
            return False, "Stored review result is not PASS"
        return True, "Episode Review PASS is current"
    except EpisodeReviewError as exc:
        return False, str(exc)


def check_ledger_continuity(ledger_path: Path,
                            batch_manifest_path: Path) -> ReviewReport:
    """Check structural scene/handoff coverage without judging semantics."""
    report = ReviewReport()
    try:
        manifest = load_batch_manifest(batch_manifest_path)
        ledger = _completed_episode_document(
            ledger_path, "# EPISODE_CONTINUITY_LEDGER", "Continuity Ledger")
    except (BridgeError, EpisodeReviewError) as exc:
        report.blocked = True
        report.block_reason = str(exc)
        return report
    scenes = manifest["selected_scenes"]
    for scene in scenes:
        marker = f"场景 {scene}"
        status = "ok" if marker in ledger else "flagged"
        report.checklist.append(ReviewItem(
            "scene_coverage", scene, status,
            "present" if status == "ok" else f"Ledger missing scene {scene}"))
    for left, right in zip(scenes, scenes[1:]):
        marker = f"场景 {left} → 场景 {right}"
        count = ledger.count(marker)
        report.checklist.append(ReviewItem(
            "transition", left, "ok" if count == 1 else "flagged",
            "present" if count == 1 else
            f"Ledger requires exactly one handoff {marker}; found {count}"))
    return report


def _extract_review_excerpt(master_path: Path) -> str:
    text = _read_text(master_path, "Director Master")
    section_match = re.search(
        r"^##\s+1\..*?(?=^##\s+(?:2\.|Boundary\b|Shot\b))",
        text,
        re.MULTILINE | re.DOTALL,
    )
    shared = list(_BOUNDARY_HEADER_RE.finditer(text))
    if shared:
        handoffs: list[str] = []
        for match in shared:
            tail = text[match.end():]
            next_heading = re.search(r"^##\s+", tail, re.MULTILINE)
            block = tail[:next_heading.start()] if next_heading else tail
            handoff = _HANDOFF_RE.search(block)
            if handoff is None:
                raise EpisodeReviewError(
                    f"Shared Boundary lacks handoff prose: {master_path}"
                )
            handoffs.append(handoff.group(1).strip())
        entries = [handoffs[0]]
        exits = [handoffs[-1]]
    else:
        entries = _ENTRY_RE.findall(text)
        exits = _EXIT_RE.findall(text)
    if not section_match or not section_match.group(0).strip():
        raise EpisodeReviewError(f"Master lacks a scene-level summary: {master_path}")
    if not entries or not exits:
        raise EpisodeReviewError(f"Master lacks entry/exit boundary prose: {master_path}")
    return (
        section_match.group(0).strip() + "\n\n"
        f"首镜进入边界：{entries[0]}\n"
        f"末镜交出边界：{exits[-1]}"
    )


def _render_review_packet(packet: dict, excerpts: list[tuple[int, str]],
                          _bible_text: str, _ledger_text: str) -> str:
    lines = [
        "# EPISODE REVIEW PACKET",
        "",
        "<!-- contract: episode_review_packet v1.0 -->",
        f"<!-- review_input_sha256: {packet['review_input_sha256']} -->",
        f"<!-- source_sha256: {packet['script_source_hash']} -->",
        "",
        "## Read These Episode Sources",
        f"- Visual Bible: {packet['visual_bible_path']}",
        f"- Continuity Ledger: {packet['continuity_ledger_path']}",
        "",
        "## Scene Summaries and Boundaries",
    ]
    scene_map = {scene["scene_index"]: scene for scene in packet["scenes"]}
    for scene_index, excerpt in excerpts:
        scene = scene_map[scene_index]
        lines.extend([
            "",
            f"### Scene {scene_index} ({scene['scene_id']})",
            f"Master hash: {scene['master_content_hash']}",
            excerpt,
            "",
            "Canonical opening state: " + _compact_state(scene["opening_state_keys"]),
            "Canonical closing state: " + _compact_state(scene["closing_state_keys"]),
        ])
    lines.extend([
        "",
        "## Result Contract",
        "Return one natural-language review file beginning with exactly one of:",
        "- EPISODE REVIEW: PASS",
        "- EPISODE REVIEW: REVISE (then `Affected scenes: N,...` and concrete issues)",
        "- EPISODE REVIEW: BLOCKED (then `Reason: ...`)",
        "",
    ])
    return "\n".join(lines)


def _compact_state(state: dict) -> str:
    characters = ", ".join(
        f"{item['entity_id']}@{item['position']}/{item['posture']}"
        f"/wardrobe={item.get('wardrobe', 'unspecified')}"
        f"/injury={item.get('injury', 'unspecified')}"
        for item in state["characters"]) or "none"
    props = ", ".join(
        f"{item['prop_id']}@{item['location']} held_by={item['held_by']}"
        for item in state["props"]) or "none"
    light = state["light_main"]
    extras = "; ".join(
        f"{key}={state[key]}"
        for key in ("story_time", "weather", "environment") if key in state)
    result = (
        f"characters[{characters}]; props[{props}]; light="
        f"{light['direction']}/{light['color_temp_k']}K/{light['ratio']}; "
        f"action={state['action_phase']}")
    return result + (f"; {extras}" if extras else "")


def _completed_episode_document(path: Path, title: str, label: str) -> str:
    text = _read_text(path, label)
    if title not in text:
        raise EpisodeReviewError(f"{label} has the wrong document type")
    if _PLACEHOLDER_RE.search(text):
        raise EpisodeReviewError(f"{label} still contains Director placeholders")
    return text


def _affected_versions_changed(previous: dict, packet: dict) -> bool:
    affected = previous.get("affected_scenes")
    old_hashes = previous.get("scene_master_hashes")
    if not isinstance(affected, list) or not affected or not isinstance(old_hashes, dict):
        return False
    current = {
        str(scene["scene_index"]): scene["master_content_hash"]
        for scene in packet["scenes"]
    }
    return all(current.get(str(scene)) != old_hashes.get(str(scene))
               for scene in affected)


def _packet_dependencies_current(packet: dict) -> bool:
    try:
        if _file_hash(Path(packet["batch_manifest_path"])) != packet["batch_manifest_sha256"]:
            return False
        if _file_hash(Path(packet["visual_bible_path"])) != packet["visual_bible_sha256"]:
            return False
        if _file_hash(Path(packet["continuity_ledger_path"])) != packet["continuity_ledger_sha256"]:
            return False
        for scene in packet["scenes"]:
            current = delivered_scene_state(
                scene["scene_index"], Path(scene["session_path"]))
            for key in (
                "master_content_hash", "manifest_sha256", "storyboard_sha256",
                "video_prompt_sha256", "opening_state_keys", "closing_state_keys",
            ):
                if current[key] != scene[key]:
                    return False
    except (BridgeError, EpisodeReviewError, KeyError, TypeError):
        return False
    return True


def _verify_packet(packet: dict) -> None:
    supplied = packet.get("review_input_sha256")
    unsigned = dict(packet)
    unsigned.pop("review_input_sha256", None)
    if supplied != _object_hash(unsigned):
        raise EpisodeReviewError("Episode review packet self-hash mismatch")


def _parse_scene_list(value: str) -> list[int]:
    try:
        scenes = [int(part.strip()) for part in value.split(",")]
    except ValueError as exc:
        raise EpisodeReviewError("Affected scenes must be comma-separated integers") from exc
    if scenes != sorted(set(scenes)):
        raise EpisodeReviewError("Affected scenes must be unique and ascending")
    return scenes


def _parse_scene_sessions(values: list[str]) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for value in values:
        try:
            raw_index, raw_path = value.split("=", 1)
            index = int(raw_index)
        except ValueError as exc:
            raise EpisodeReviewError(
                f"Invalid --scene-session {value!r}; expected INDEX=PATH") from exc
        if index in result:
            raise EpisodeReviewError(f"Duplicate scene session {index}")
        result[index] = Path(raw_path)
    return result


def _load_optional_state(path: Path) -> dict:
    if not path.exists():
        return {}
    return _load_required_json(path, "review state")


def _load_required_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EpisodeReviewError(f"Cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EpisodeReviewError(f"{label} root must be an object")
    return value


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise EpisodeReviewError(f"Cannot read {label} {path}: {exc}") from exc


def _file_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise EpisodeReviewError(f"Cannot hash {path}: {exc}") from exc


def _object_hash(value: dict) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _atomic_write_json(path: Path, value: dict) -> None:
    _atomic_write_text(
        path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise EpisodeReviewError(f"Cannot write {path}: {exc}") from exc


_prepare_review_impl = prepare_review
_submit_review_impl = submit_review


def prepare_review(batch_manifest_path: Path, bible_path: Path,
                   ledger_path: Path, scene_session_dirs: dict[int, Path],
                   review_session_dir: Path) -> dict:
    started = time.monotonic()
    root = batch_manifest_path.resolve().parent
    try:
        state = _prepare_review_impl(
            batch_manifest_path, bible_path, ledger_path,
            scene_session_dirs, review_session_dir,
        )
    except Exception as exc:
        record_event(
            root, event_type="local", stage="episode_review_prepare",
            status="failed", elapsed_s=time.monotonic() - started,
            input_bytes=files_byte_size([batch_manifest_path, bible_path, ledger_path]),
            result_code=1, error_code=type(exc).__name__,
        )
        raise
    record_event(
        root, event_type="local", stage="episode_review_prepare",
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([
            batch_manifest_path, bible_path, ledger_path,
            *[session / "DIRECTOR_MASTER.md" for session in scene_session_dirs.values()],
        ]),
        output_bytes=files_byte_size([
            review_session_dir / "EPISODE_REVIEW_PACKET.json",
            review_session_dir / "EPISODE_REVIEW_PACKET.md",
            review_session_dir / "REVIEW_STATE.json",
        ]),
    )
    return state


def submit_review(review_session_dir: Path, review_result_path: Path) -> dict:
    started = time.monotonic()
    try:
        packet = _load_required_json(
            review_session_dir / "EPISODE_REVIEW_PACKET.json", "review packet"
        )
        root = Path(packet["batch_manifest_path"]).resolve().parent
    except Exception:
        root = review_session_dir.resolve()
    try:
        state = _submit_review_impl(review_session_dir, review_result_path)
    except Exception as exc:
        record_event(
            root, event_type="local", stage="episode_review_submit",
            status="failed", elapsed_s=time.monotonic() - started,
            input_bytes=files_byte_size([review_result_path]),
            result_code=1, error_code=type(exc).__name__,
        )
        raise
    status = (
        "completed" if state["status"] == "passed"
        else "revision_required" if state["status"] == "revision_required"
        else "blocked"
    )
    record_event(
        root, event_type="local", stage="episode_review_submit", status=status,
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([
            review_session_dir / "EPISODE_REVIEW_PACKET.md", review_result_path
        ]),
        output_bytes=files_byte_size([
            review_session_dir / "EPISODE_REVIEW_RESULT.md",
            review_session_dir / "REVIEW_STATE.json",
        ]),
    )
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="MODE:P Episode Review protocol")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("batch_manifest", type=Path)
    prepare.add_argument("visual_bible", type=Path)
    prepare.add_argument("continuity_ledger", type=Path)
    prepare.add_argument("review_session", type=Path)
    prepare.add_argument("--scene-session", action="append", default=[])

    submit = sub.add_parser("submit")
    submit.add_argument("review_session", type=Path)
    submit.add_argument("review_result", type=Path)

    gate = sub.add_parser("gate")
    gate.add_argument("review_session", type=Path)

    ledger = sub.add_parser("ledger-check")
    ledger.add_argument("continuity_ledger", type=Path)
    ledger.add_argument("batch_manifest", type=Path)
    args = parser.parse_args()

    try:
        if args.command == "prepare":
            state = prepare_review(
                args.batch_manifest, args.visual_bible, args.continuity_ledger,
                _parse_scene_sessions(args.scene_session), args.review_session)
            print(f"Episode Review cycle {state['cycle']}: {state['status']}")
            return 0
        if args.command == "submit":
            state = submit_review(args.review_session, args.review_result)
            print(f"Episode Review cycle {state['cycle']}: {state['status']}")
            return 0
        if args.command == "gate":
            ok, detail = review_gate(args.review_session)
            print(detail)
            return 0 if ok else 1
        report = check_ledger_continuity(
            args.continuity_ledger, args.batch_manifest)
        if report.blocked:
            print(report.block_reason)
            return 1
        flagged = [item for item in report.checklist if item.status == "flagged"]
        for item in flagged:
            print(f"[{item.dimension}] Scene {item.scene_index}: {item.detail}")
        return 0 if not flagged else 1
    except EpisodeReviewError as exc:
        print(f"Episode review error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
