"""Atomically assemble the two episode deliverables after a current L6 PASS."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from episode_review import EpisodeReviewError, review_gate
from scene_bridge import BridgeError, delivered_scene_state
from session_lock import LockError, session_lock
from pipeline_telemetry import files_byte_size, record_event


SCHEMA_VERSION = "1.0"
_DELIVERY_FILES = ("STORYBOARD.md", "VIDEO_PROMPT.md")


class EpisodeDeliveryError(ValueError):
    """Raised when the review gate or atomic delivery evidence is invalid."""


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise EpisodeDeliveryError(f"cannot hash {path}: {exc}") from exc


def _object_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EpisodeDeliveryError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise EpisodeDeliveryError(f"{label} must be a JSON object")
    return value


def _safe_child(root: Path, raw: str, label: str) -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise EpisodeDeliveryError(f"invalid {label} path")
    path = (root / Path(raw)).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise EpisodeDeliveryError(f"{label} escapes episode session") from exc
    return path


def _verify_delivery(directory: Path, expected: dict[str, str]) -> None:
    if not directory.is_dir():
        raise EpisodeDeliveryError("episode delivery directory is missing")
    names = sorted(path.name for path in directory.iterdir() if path.is_file())
    if names != sorted(_DELIVERY_FILES):
        raise EpisodeDeliveryError(
            "episode delivery must contain exactly STORYBOARD.md and VIDEO_PROMPT.md"
        )
    for name in _DELIVERY_FILES:
        if _sha256(directory / name) != expected[name]:
            raise EpisodeDeliveryError(f"episode delivery hash mismatch: {name}")


def _render_episode(
    label: str,
    scenes: list[dict[str, Any]],
) -> str:
    lines = [
        f"# MODE:P Episode {label}",
    ]
    source_name = "STORYBOARD.md" if label == "Storyboard" else "VIDEO_PROMPT.md"
    for scene in scenes:
        source = Path(scene["session_path"]) / "delivery" / source_name
        text = source.read_text(encoding="utf-8").strip()
        lines.extend([
            "",
            "---",
            "",
            text,
        ])
    lines.append("")
    return "\n".join(lines)


def _build_commit(
    review_session_dir: Path,
    packet: dict[str, Any],
    scene_session_dirs: dict[int, Path],
    stage: Path,
) -> dict[str, Any]:
    expected = [scene["scene_index"] for scene in packet["scenes"]]
    if sorted(scene_session_dirs) != expected:
        raise EpisodeDeliveryError(
            f"episode delivery requires scene sessions {expected}; got "
            f"{sorted(scene_session_dirs)}"
        )
    scenes: list[dict[str, Any]] = []
    for packet_scene in packet["scenes"]:
        index = packet_scene["scene_index"]
        session = scene_session_dirs[index].resolve()
        state = delivered_scene_state(index, session)
        if (
            state["scene_id"] != packet_scene["scene_id"]
            or state["master_content_hash"] != packet_scene["master_content_hash"]
            or state["storyboard_sha256"] != packet_scene["storyboard_sha256"]
            or state["video_prompt_sha256"] != packet_scene["video_prompt_sha256"]
        ):
            raise EpisodeDeliveryError(
                f"scene {index} no longer matches the Episode Review packet"
            )
        scenes.append({
            "scene_index": index,
            "scene_id": state["scene_id"],
            "session_path": str(session),
            "master_content_hash": state["master_content_hash"],
            "storyboard_sha256": state["storyboard_sha256"],
            "video_prompt_sha256": state["video_prompt_sha256"],
        })

    review_hash = packet["review_input_sha256"]
    stage.mkdir(parents=True, exist_ok=False)
    (stage / "STORYBOARD.md").write_text(
        _render_episode("Storyboard", scenes), encoding="utf-8"
    )
    (stage / "VIDEO_PROMPT.md").write_text(
        _render_episode("Video Prompt", scenes), encoding="utf-8"
    )
    unsigned = {
        "schema_version": SCHEMA_VERSION,
        "status": "committed",
        "review_session_path": str(review_session_dir.resolve()),
        "review_input_sha256": review_hash,
        "scenes": scenes,
        "files": {name: _sha256(stage / name) for name in _DELIVERY_FILES},
    }
    commit = dict(unsigned)
    commit["commit_sha256"] = _object_hash(unsigned)
    return commit


def _verify_commit_record(commit: dict[str, Any]) -> None:
    supplied = commit.get("commit_sha256")
    unsigned = dict(commit)
    unsigned.pop("commit_sha256", None)
    if (
        commit.get("schema_version") != SCHEMA_VERSION
        or commit.get("status") != "committed"
        or supplied != _object_hash(unsigned)
    ):
        raise EpisodeDeliveryError("episode delivery commit record is invalid")
    files = commit.get("files")
    if not isinstance(files, dict) or set(files) != set(_DELIVERY_FILES):
        raise EpisodeDeliveryError("episode delivery commit file set is invalid")


def _recover_unlocked(episode_session_dir: Path) -> None:
    pending_path = episode_session_dir / "EPISODE_DELIVERY_PENDING.json"
    if not pending_path.exists():
        return
    pending = _load_json(pending_path, "pending episode delivery")
    commit = pending.get("commit")
    if not isinstance(commit, dict):
        raise EpisodeDeliveryError("pending episode delivery has no commit evidence")
    _verify_commit_record(commit)
    target = episode_session_dir / "delivery"
    stage = _safe_child(episode_session_dir, pending.get("stage", ""), "stage")
    backup = _safe_child(episode_session_dir, pending.get("backup", ""), "backup")

    if target.is_dir():
        try:
            _verify_delivery(target, commit["files"])
        except EpisodeDeliveryError:
            if backup.is_dir():
                shutil.rmtree(target)
                backup.replace(target)
                pending_path.unlink(missing_ok=True)
                return
            raise
    elif stage.is_dir():
        stage.replace(target)
        _verify_delivery(target, commit["files"])
    elif backup.is_dir():
        backup.replace(target)
        pending_path.unlink(missing_ok=True)
        return
    else:
        raise EpisodeDeliveryError("cannot recover interrupted episode delivery")

    _atomic_json(episode_session_dir / "EPISODE_DELIVERY_COMMIT.json", commit)
    if backup.is_dir():
        shutil.rmtree(backup)
    pending_path.unlink(missing_ok=True)


def recover_episode_delivery(episode_session_dir: Path) -> None:
    """Finish or roll back an interrupted root delivery switch."""
    with session_lock(episode_session_dir):
        _recover_unlocked(episode_session_dir)


def assemble_episode_delivery(
    review_session_dir: Path,
    scene_session_dirs: dict[int, Path],
    episode_session_dir: Path,
    *,
    failpoint: str | None = None,
) -> dict[str, Any]:
    """Publish exactly two episode files after a source-current review PASS."""
    if failpoint not in {None, "after_backup", "after_publish"}:
        raise EpisodeDeliveryError("unknown delivery failpoint")
    gate_ok, gate_detail = review_gate(review_session_dir)
    if not gate_ok:
        raise EpisodeDeliveryError(f"Episode Review gate is closed: {gate_detail}")
    packet = _load_json(
        review_session_dir / "EPISODE_REVIEW_PACKET.json", "Episode Review packet"
    )

    episode_session_dir.mkdir(parents=True, exist_ok=True)
    with session_lock(episode_session_dir):
        _recover_unlocked(episode_session_dir)
        gate_ok, gate_detail = review_gate(review_session_dir)
        if not gate_ok:
            raise EpisodeDeliveryError(f"Episode Review gate changed: {gate_detail}")

        transaction = uuid.uuid4().hex
        stage = episode_session_dir / "staging" / f"episode-delivery-{transaction}"
        backup = episode_session_dir / f".delivery.backup-{transaction}"
        commit = _build_commit(
            review_session_dir, packet, scene_session_dirs, stage
        )
        target = episode_session_dir / "delivery"
        pending = {
            "schema_version": SCHEMA_VERSION,
            "stage": stage.relative_to(episode_session_dir).as_posix(),
            "backup": backup.relative_to(episode_session_dir).as_posix(),
            "commit": commit,
        }
        _atomic_json(
            episode_session_dir / "EPISODE_DELIVERY_PENDING.json", pending
        )
        if target.exists():
            target.replace(backup)
        if failpoint == "after_backup":
            raise EpisodeDeliveryError("simulated interruption after backup")
        stage.replace(target)
        if failpoint == "after_publish":
            raise EpisodeDeliveryError("simulated interruption after publish")
        _verify_delivery(target, commit["files"])
        _atomic_json(episode_session_dir / "EPISODE_DELIVERY_COMMIT.json", commit)
        if backup.is_dir():
            shutil.rmtree(backup)
        (episode_session_dir / "EPISODE_DELIVERY_PENDING.json").unlink(missing_ok=True)
        return commit


def verify_episode_delivery(episode_session_dir: Path) -> tuple[bool, str]:
    try:
        commit = _load_json(
            episode_session_dir / "EPISODE_DELIVERY_COMMIT.json",
            "episode delivery commit",
        )
        _verify_commit_record(commit)
        review_dir = Path(commit["review_session_path"])
        gate_ok, detail = review_gate(review_dir)
        if not gate_ok:
            return False, f"Episode Review is stale: {detail}"
        packet = _load_json(
            review_dir / "EPISODE_REVIEW_PACKET.json", "Episode Review packet"
        )
        if packet.get("review_input_sha256") != commit["review_input_sha256"]:
            return False, "episode delivery is bound to a different review input"
        _verify_delivery(episode_session_dir / "delivery", commit["files"])
        return True, "Episode delivery is current and contains exactly two files"
    except (EpisodeDeliveryError, EpisodeReviewError, OSError, KeyError) as exc:
        return False, str(exc)


def _parse_scene_sessions(values: list[str]) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for value in values:
        try:
            raw_index, raw_path = value.split("=", 1)
            index = int(raw_index)
        except (ValueError, TypeError) as exc:
            raise EpisodeDeliveryError("scene session must be INDEX=PATH") from exc
        if index < 1 or index in result or not raw_path.strip():
            raise EpisodeDeliveryError(f"invalid scene session mapping: {value}")
        result[index] = Path(raw_path)
    return result


_assemble_episode_delivery_impl = assemble_episode_delivery
_recover_episode_delivery_impl = recover_episode_delivery


def assemble_episode_delivery(
    review_session_dir: Path,
    scene_session_dirs: dict[int, Path],
    episode_session_dir: Path,
    *,
    failpoint: str | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        commit = _assemble_episode_delivery_impl(
            review_session_dir, scene_session_dirs, episode_session_dir,
            failpoint=failpoint,
        )
    except Exception as exc:
        record_event(
            episode_session_dir, event_type="local", stage="episode_delivery",
            status="failed", elapsed_s=time.monotonic() - started,
            input_bytes=files_byte_size([review_session_dir]),
            result_code=1, error_code=type(exc).__name__,
        )
        raise
    record_event(
        episode_session_dir, event_type="local", stage="episode_delivery",
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([
            review_session_dir,
            *[session / "delivery" for session in scene_session_dirs.values()],
        ]),
        output_bytes=files_byte_size([
            episode_session_dir / "delivery",
            episode_session_dir / "EPISODE_DELIVERY_COMMIT.json",
        ]),
    )
    return commit


def recover_episode_delivery(episode_session_dir: Path) -> None:
    started = time.monotonic()
    try:
        _recover_episode_delivery_impl(episode_session_dir)
    except Exception as exc:
        record_event(
            episode_session_dir, event_type="local",
            stage="episode_delivery_recovery", status="failed",
            elapsed_s=time.monotonic() - started,
            result_code=1, error_code=type(exc).__name__,
        )
        raise
    record_event(
        episode_session_dir, event_type="local",
        stage="episode_delivery_recovery",
        elapsed_s=time.monotonic() - started,
        output_bytes=files_byte_size([
            episode_session_dir / "delivery",
            episode_session_dir / "EPISODE_DELIVERY_COMMIT.json",
        ]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble MODE:P episode delivery")
    sub = parser.add_subparsers(dest="command", required=True)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("review_session", type=Path)
    assemble.add_argument("episode_session", type=Path)
    assemble.add_argument("--scene-session", action="append", default=[])
    recover = sub.add_parser("recover")
    recover.add_argument("episode_session", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("episode_session", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "assemble":
            commit = assemble_episode_delivery(
                args.review_session,
                _parse_scene_sessions(args.scene_session),
                args.episode_session,
            )
            print(f"Episode delivery -> {args.episode_session / 'delivery'}")
            print(f"Commit SHA-256: {commit['commit_sha256']}")
            return 0
        if args.command == "recover":
            recover_episode_delivery(args.episode_session)
            print("Episode delivery recovery complete.")
            return 0
        ok, detail = verify_episode_delivery(args.episode_session)
        print(detail)
        return 0 if ok else 1
    except (
        EpisodeDeliveryError, EpisodeReviewError, BridgeError, LockError,
        OSError, ValueError,
    ) as exc:
        print(f"Episode delivery error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
