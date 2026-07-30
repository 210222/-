"""Deterministic MODE:P project-background registration and episode binding.

The user never needs to provide project or episode flags. Claude Code invokes
``register`` when the user identifies a complete script as project background;
normal Pilot runs call ``resolve_episode`` automatically. No model is called.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from script_ingest import IngestError, ingest_script


SCHEMA_VERSION = "1.0"
_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parents[1]
_ACTIVE_MANIFEST = _PROJECT_ROOT / "MODE_P_PROJECT.json"
_PROJECTS_ROOT = _MODULE_DIR / "projects"
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_-]+")
_EPISODE_RE = re.compile(
    r"(?:^|[^A-Za-z0-9])(?P<id>EP\s*[-_]?\s*\d{1,4})(?:[^A-Za-z0-9]|$)",
    re.IGNORECASE,
)
_CN_EPISODE_RE = re.compile(r"第\s*(?P<number>\d{1,4})\s*集")


class ProjectContextError(ValueError):
    """Raised when persisted project binding is ambiguous or stale."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _script_content_hash(path: Path) -> str:
    try:
        return ingest_script(path).source_content_hash
    except IngestError as exc:
        raise ProjectContextError(str(exc)) from exc


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _safe_id(value: str, fallback: str) -> str:
    ascii_value = _SAFE_ID_RE.sub("_", value).strip("_-")
    if ascii_value:
        return ascii_value[:96]
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{fallback}_{digest}"


def infer_episode_id(script_path: Path) -> str:
    """Infer an episode identity from the first script lines, then file stem."""
    try:
        head = "\n".join(script_path.read_text(encoding="utf-8-sig").splitlines()[:80])
    except (OSError, UnicodeError) as exc:
        raise ProjectContextError(f"cannot read episode script: {exc}") from exc
    match = _EPISODE_RE.search(head)
    if match:
        digits = re.search(r"\d+", match.group("id"))
        assert digits is not None
        return f"EP{int(digits.group()):02d}"
    match = _CN_EPISODE_RE.search(head)
    if match:
        return f"EP{int(match.group('number')):02d}"
    return _safe_id(script_path.stem, "episode")


def _initial_project_docs(project_dir: Path, source_path: Path, source_hash: str) -> None:
    visual_bible = project_dir / "PROJECT_VISUAL_BIBLE.md"
    if not visual_bible.exists():
        _atomic_text(visual_bible, (
            "# Project Visual Bible\n\n"
            "Status: pending_director\n\n"
            "The first episode Director records only stable cross-episode visual choices here.\n"
        ))
    ledger = project_dir / "PROJECT_CONTINUITY_LEDGER.md"
    if not ledger.exists():
        _atomic_text(ledger, (
            "# Project Continuity Ledger\n\n"
            "No committed episode state yet. Current episode scripts override conflicting "
            "background assumptions.\n"
        ))
    requirements = project_dir / "ASSET_REQUIREMENTS.md"
    if not requirements.exists():
        _atomic_text(requirements, (
            "# Project Asset Requirements\n\n"
            "No asset slots declared yet. Missing assets never block text-only design.\n"
        ))


def register_background(
    script_path: Path,
    *,
    active_manifest_path: Path = _ACTIVE_MANIFEST,
    projects_root: Path = _PROJECTS_ROOT,
    replace: bool = False,
) -> dict[str, Any]:
    """Register one complete script as the active project background."""
    source = script_path.resolve()
    if not source.is_file():
        raise ProjectContextError(f"background script not found: {source}")
    try:
        digest = ingest_script(source)
    except IngestError as exc:
        raise ProjectContextError(str(exc)) from exc
    source_hash = digest.source_content_hash
    path_identity = hashlib.sha256(str(source).casefold().encode("utf-8")).hexdigest()[:8]
    project_id = f"{_safe_id(source.stem, 'project')}-{path_identity}"
    project_dir = (projects_root / project_id).resolve()

    if active_manifest_path.is_file():
        current = load_active_project(active_manifest_path, verify_source=False)
        if Path(current["background_script"]["path"]) != source and not replace:
            raise ProjectContextError(
                "another active project background exists; explicit replacement is required"
            )

    now = datetime.now(timezone.utc).isoformat()
    source_index = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "background_script": {
            "path": str(source),
            "content_sha256": source_hash,
            "encoding": digest.encoding,
            "line_count": digest.total_lines,
            "scene_count": digest.scene_count,
        },
        "scenes": [asdict(scene) for scene in digest.scenes],
    }
    _atomic_json(project_dir / "PROJECT_SOURCE_INDEX.json", source_index)
    _initial_project_docs(project_dir, source, source_hash)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "active",
        "project_id": project_id,
        "project_dir": str(project_dir),
        "background_script": {
            "path": str(source),
            "content_sha256": source_hash,
        },
        "source_index": str(project_dir / "PROJECT_SOURCE_INDEX.json"),
        "registered_at": now,
    }
    _atomic_json(active_manifest_path, manifest)
    return manifest


def load_active_project(
    active_manifest_path: Path = _ACTIVE_MANIFEST, *, verify_source: bool = True
) -> dict[str, Any]:
    try:
        data = json.loads(active_manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ProjectContextError("no active MODE:P project")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectContextError(f"cannot read active project: {exc}") from exc
    required = {
        "schema_version", "status", "project_id", "project_dir",
        "background_script", "source_index", "registered_at",
    }
    if not isinstance(data, dict) or set(data) != required:
        raise ProjectContextError("active project manifest has an invalid shape")
    if data["schema_version"] != SCHEMA_VERSION or data["status"] != "active":
        raise ProjectContextError("active project manifest is not usable")
    project_dir = Path(data["project_dir"])
    source_index = Path(data["source_index"])
    source = Path(data["background_script"].get("path", ""))
    expected_hash = data["background_script"].get("content_sha256")
    if not project_dir.is_dir() or not source_index.is_file():
        raise ProjectContextError("active project files are missing")
    if verify_source and (
        not source.is_file()
        or not isinstance(expected_hash, str)
        or _script_content_hash(source) != expected_hash
    ):
        raise ProjectContextError(
            "active project background changed; register the updated complete script"
        )
    return data


def _retrieval_terms(text: str) -> set[str]:
    stop_terms = {
        "scene", "scenes", "episode", "complete", "story", "interior",
        "exterior", "morning", "afternoon", "evening", "night", "day",
    }
    terms = {
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9_]{3,}", text)
        if token.casefold() not in stop_terms
    }
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        for width in (2, 3):
            terms.update(
                chunk[index:index + width]
                for index in range(max(0, len(chunk) - width + 1))
            )
    return terms


def build_background_packet(
    episode_script: Path,
    output_path: Path,
    *,
    active_manifest_path: Path = _ACTIVE_MANIFEST,
    project_binding: dict[str, Any] | None = None,
    max_chars: int = 6000,
    max_scenes: int = 3,
) -> str:
    """Select compact exact background excerpts without an LLM or semantic rewrite."""
    if not 1 <= max_chars <= 10000 or not 1 <= max_scenes <= 6:
        raise ProjectContextError("background packet budget is invalid")
    project = project_binding or load_active_project(active_manifest_path)
    source_index = json.loads(Path(project["source_index"]).read_text(encoding="utf-8"))
    source = Path(source_index["background_script"]["path"])
    episode = episode_script.resolve()
    if source == episode:
        selected: list[tuple[int, dict[str, Any], list[str]]] = []
    else:
        try:
            episode_text = episode.read_text(encoding="utf-8-sig")
            source_lines = source.read_text(
                encoding=source_index["background_script"]["encoding"]
            ).splitlines()
        except (OSError, UnicodeError, LookupError) as exc:
            raise ProjectContextError(f"cannot build project background packet: {exc}") from exc
        episode_terms = _retrieval_terms(episode_text)
        ranked: list[tuple[int, int, dict[str, Any], list[str]]] = []
        for scene in source_index["scenes"]:
            start, end = scene["start_line"], scene["end_line"]
            excerpt_lines = source_lines[start - 1:end]
            score = len(episode_terms & _retrieval_terms("\n".join(excerpt_lines)))
            if score:
                ranked.append((-score, scene["index"], scene, excerpt_lines))
        selected = [
            (-negative_score, scene, excerpt_lines)
            for negative_score, _, scene, excerpt_lines in sorted(ranked)[:max_scenes]
        ]

    lines = [
        "# Project Background Packet",
        "",
        "The current episode script is authoritative. These are optional exact "
        "background excerpts and must be ignored where they conflict.",
        "",
    ]
    if not selected:
        lines.extend([
            "No relevant project-background excerpt was selected. Design from the "
            "current episode and committed project memory.",
            "",
        ])
    else:
        used = len("\n".join(lines))
        for score, scene, excerpt_lines in selected:
            numbered = [
                f"L{scene['start_line'] + offset}: {line}"
                for offset, line in enumerate(excerpt_lines)
            ]
            block = [
                f"## Background Scene {scene['index']} | lexical relevance {score}",
                "",
                *numbered,
                "",
            ]
            block_text = "\n".join(block)
            if used + len(block_text) > max_chars:
                continue
            lines.extend(block)
            used += len(block_text)
    text = "\n".join(lines).rstrip() + "\n"
    _atomic_text(output_path, text)
    return text


def resolve_episode(
    script_path: Path,
    *,
    active_manifest_path: Path = _ACTIVE_MANIFEST,
    standalone_root: Path | None = None,
) -> dict[str, Any]:
    """Bind an independent episode script to the sole active project, if any."""
    episode = script_path.resolve()
    if not episode.is_file():
        raise ProjectContextError(f"episode script not found: {episode}")
    episode_hash = _sha256(episode)
    episode_id = infer_episode_id(episode)
    project: dict[str, Any] | None
    try:
        project = load_active_project(active_manifest_path)
    except ProjectContextError as exc:
        if str(exc) != "no active MODE:P project":
            raise
        project = None

    if project:
        session_dir = (
            Path(project["project_dir"]) / "episodes" / episode_id
            / "versions" / episode_hash[:12]
        )
        project_id = project["project_id"]
        mode = "project"
    else:
        root = (standalone_root or (_MODULE_DIR / "sessions")).resolve()
        session_dir = root / episode_id / episode_hash[:12]
        project_id = ""
        mode = "standalone"
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "project_id": project_id,
        "project_manifest": str(active_manifest_path.resolve()) if project else "",
        "project_dir": project["project_dir"] if project else "",
        "episode_id": episode_id,
        "episode_script": str(episode),
        "episode_sha256": episode_hash,
        "session_dir": str(session_dir.resolve()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage implicit MODE:P project context")
    sub = parser.add_subparsers(dest="command", required=True)
    register = sub.add_parser("register")
    register.add_argument("background_script", type=Path)
    register.add_argument("--replace", action="store_true")
    resolve = sub.add_parser("resolve")
    resolve.add_argument("episode_script", type=Path)
    sub.add_parser("show")
    args = parser.parse_args()
    try:
        if args.command == "register":
            result = register_background(args.background_script, replace=args.replace)
        elif args.command == "resolve":
            result = resolve_episode(args.episode_script)
        else:
            result = load_active_project()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ProjectContextError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Project context failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
