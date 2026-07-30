"""Parse a script file to extract scene boundaries and metadata.

This is a deterministic local parser implementing script_input_contract.md v1.1.
It identifies scene headers, extracts line ranges, and outputs structured data.
It does NOT interpret plot, characters, or events — those are Director's job.

Implements LOOP_SPEC v2.1 L0.2: "本地解析器提取显式场景边界、编码和原文行号；
无法确定的边界标记 unresolved"。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Scene header patterns from script_input_contract.md §2.1 (priority order)
_PATTERNS: list[tuple[int, str, re.Pattern]] = [
    (1, "markdown_scene_en", re.compile(r"^##\s+Scene\b", re.IGNORECASE)),
    (2, "markdown_cn_numbered", re.compile(r"^##\s+第.+场")),
    (3, "markdown_cn_any", re.compile(r"^#+\s+第.+场")),
    (4, "screenplay_header", re.compile(r"^(INT\.|EXT\.|INT/EXT\.|EXT/INT\.)\s", re.IGNORECASE)),
    (5, "cn_bracket", re.compile(r"^【场景.*】")),
    (6, "cn_plain", re.compile(r"^场景\s*\d+")),
    (7, "cn_episode_scene", re.compile(
        r"^\d+\.\d+\s+.+\s+"
        r"(日|夜|晨|早晨|上午|中午|下午|黄昏|傍晚|凌晨"
        r"|DAY|NIGHT|MORNING|DUSK|DAWN|AFTERNOON|EVENING)"
        r"\s+(内|外)\s*$")),
]

# Metadata extraction
_SCENE_NUMBER_EN = re.compile(r"Scene\s*(\d+)", re.IGNORECASE)
_SCENE_NUMBER_CN = re.compile(r"第\s*(\d+|[一二三四五六七八九十]+)\s*场")
_SCENE_NUMBER_PLAIN = re.compile(r"^场景\s*(\d+)")
_SCENE_NUMBER_EP_SC = re.compile(r"^(\d+)\.(\d+)")
_LOCATION_HINT_SCREENPLAY = re.compile(
    r"^(?:INT\.|EXT\.|INT/EXT\.|EXT/INT\.)\s*(.+?)(?:\s*-\s*.*)?$", re.IGNORECASE)
_LOCATION_HINT_MD = re.compile(
    r"^(?:##\s+(?:Scene\s*\d*\s*|第.+场\s*))[-—–]+\s*(.+?)(?:\s*[-—–]+\s*.*)?$")
_TIME_HINT = re.compile(r"[-—–]\s*(日|夜|晨|早晨|上午|中午|下午|黄昏|傍晚|凌晨|DAY|NIGHT|MORNING|DUSK|DAWN|AFTERNOON|EVENING)\s*$", re.IGNORECASE)


@dataclass
class SceneEntry:
    index: int           # 1-based scene index
    start_line: int      # inclusive
    end_line: int        # inclusive
    header_line: str     # the raw header line
    header_kind: str     # which pattern matched
    scene_number: int | None = None
    location_hint: str | None = None
    time_hint: str | None = None
    status: str = "resolved"  # resolved | unresolved
    unresolved_reason: str | None = None


@dataclass
class ScriptDigest:
    file_path: str
    encoding: str
    source_content_hash: str
    total_lines: int
    scene_count: int
    scenes: list[SceneEntry] = field(default_factory=list)
    front_matter_lines: tuple[int, int] | None = None  # (start, end) or None


class IngestError(Exception):
    """Raised when the parser cannot process the script file."""


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def ingest_script(script_path: Path) -> ScriptDigest:
    """Parse a script file and return a digest of scene boundaries.

    Raises IngestError on unreadable files or completely unparseable content.
    """
    text, encoding = _read_with_fallback(script_path)
    if not text.strip():
        raise IngestError(f"Script is empty: {script_path}")

    source_content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    lines = text.splitlines(keepends=True)
    total = len(lines)

    # Find scene headers
    scene_starts: list[tuple[int, str, str]] = []  # (line_no, header_kind, raw_line)
    for i, line in enumerate(lines):
        stripped = line.strip()
        for prio, kind, pattern in _PATTERNS:
            if pattern.search(stripped):
                scene_starts.append((i + 1, kind, stripped))  # 1-indexed
                break  # first match wins

    if not scene_starts:
        # The local parser must not invent narrative boundaries.  Preserve the
        # whole source as one unresolved range so the Director can resolve it.
        scene = SceneEntry(
            index=1,
            start_line=1,
            end_line=total,
            header_line="[implicit whole-script scene]",
            header_kind="implicit",
            status="unresolved",
            unresolved_reason="implicit_scene_boundary",
        )
        return ScriptDigest(
            file_path=str(script_path.resolve()),
            encoding=encoding,
            source_content_hash=source_content_hash,
            total_lines=total,
            scene_count=1,
            scenes=[scene],
            front_matter_lines=None,
        )

    # Build scene entries
    scenes: list[SceneEntry] = []
    for idx, (start, kind, header) in enumerate(scene_starts):
        next_start = scene_starts[idx + 1][0] if idx + 1 < len(scene_starts) else total + 1
        end = next_start - 1
        body = "".join(lines[start:next_start - 1])
        if not body.strip():
            # A header with no body is not a scene and must not perturb the
            # stable indexes of scenes that actually contain source material.
            continue
        scene = SceneEntry(
            index=len(scenes) + 1,
            start_line=start,
            end_line=end,
            header_line=header,
            header_kind=kind,
        )
        # Extract metadata
        _extract_metadata(scene, header)
        scenes.append(scene)

    if not scenes:
        raise IngestError(f"All detected scene headers have empty bodies: {script_path}")

    # Front matter: lines before first scene
    front_matter = None
    first_header_line = scene_starts[0][0]
    if first_header_line > 1:
        fm_start = 1
        fm_end = first_header_line - 1
        # Only record if there's actual content (not just whitespace)
        fm_text = "".join(lines[fm_start - 1:fm_end])
        if fm_text.strip():
            front_matter = (fm_start, fm_end)

    return ScriptDigest(
        file_path=str(script_path.resolve()),
        encoding=encoding,
        source_content_hash=source_content_hash,
        total_lines=total,
        scene_count=len(scenes),
        scenes=scenes,
        front_matter_lines=front_matter,
    )


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------

def _read_with_fallback(path: Path) -> tuple[str, str]:
    """Try UTF-8, then GBK. Raise IngestError on failure."""
    for enc in ("utf-8", "gbk"):
        try:
            text = path.read_text(encoding=enc)
            return text.lstrip("﻿"), enc  # strip BOM
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            raise IngestError(f"Cannot read {path}: {exc}") from exc
    raise IngestError(f"Cannot decode {path}; expected UTF-8 or GBK")


def _extract_metadata(scene: SceneEntry, header: str) -> None:
    """Extract scene_number, location_hint, time_hint from header text."""
    # Scene number — try multiple patterns
    if scene.header_kind == "cn_episode_scene":
        m = _SCENE_NUMBER_EP_SC.search(header)
        if m:
            scene.scene_number = int(m.group(2))  # scene number within episode
    else:
        m = _SCENE_NUMBER_EN.search(header)
        if m:
            scene.scene_number = int(m.group(1))
        else:
            m = _SCENE_NUMBER_CN.search(header)
            if m:
                digits = m.group(1)
                if digits.isdigit():
                    scene.scene_number = int(digits)
                else:
                    scene.scene_number = _cn_to_int(digits)
            else:
                m = _SCENE_NUMBER_PLAIN.search(header)
                if m:
                    scene.scene_number = int(m.group(1))

    # Location hint — try episode-scene format first, then screenplay, then markdown
    if scene.header_kind == "cn_episode_scene":
        parts = header.split()
        if len(parts) >= 4:
            # "<ep>.<sc> <location tokens...> <time> <int/ext>"
            scene.location_hint = " ".join(parts[1:-2])
    else:
        m = _LOCATION_HINT_SCREENPLAY.search(header)
        if m:
            scene.location_hint = m.group(1).strip().rstrip("-–—").strip()
        else:
            m = _LOCATION_HINT_MD.search(header)
            if m:
                scene.location_hint = m.group(1).strip().rstrip("-–—").strip()

    # Time hint
    if scene.header_kind == "cn_episode_scene":
        parts = header.split()
        if len(parts) >= 3:
            t = parts[-2]  # second-to-last token is time keyword
            mapping = {"日": "day", "夜": "night", "晨": "morning", "早晨": "morning",
                       "上午": "morning", "中午": "noon", "下午": "afternoon",
                       "黄昏": "dusk", "傍晚": "evening", "凌晨": "dawn"}
            scene.time_hint = mapping.get(t, t.lower())
    else:
        m = _TIME_HINT.search(header)
        if m:
            t = m.group(1).strip()
            mapping = {"日": "day", "夜": "night", "晨": "morning", "早晨": "morning",
                       "上午": "morning", "中午": "noon", "下午": "afternoon",
                       "黄昏": "dusk", "傍晚": "evening", "凌晨": "dawn"}
            scene.time_hint = mapping.get(t, t.lower())


def _cn_to_int(s: str) -> int | None:
    """Convert simple Chinese numeral to int. Returns None for complex cases."""
    mapping = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
               "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
               "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
               "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20}
    # Handle "二十一" etc.
    if s in mapping:
        return mapping[s]
    if s.startswith("二十") and len(s) == 3:
        unit = mapping.get(s[2])
        if unit is not None:
            return 20 + unit
    if s.startswith("三十") and len(s) == 3:
        unit = mapping.get(s[2])
        if unit is not None:
            return 30 + unit
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a script file to extract scene boundaries."
    )
    parser.add_argument("script", type=Path, help="Path to script file")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output JSON path (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        digest = ingest_script(args.script)
    except IngestError as exc:
        print(f"Ingest error: {exc}", file=sys.stderr)
        return 1

    if args.json or args.output:
        data = {
            "file_path": digest.file_path,
            "encoding": digest.encoding,
            "source_content_hash": digest.source_content_hash,
            "total_lines": digest.total_lines,
            "scene_count": digest.scene_count,
            "scenes": [asdict(s) for s in digest.scenes],
        }
        if digest.front_matter_lines:
            data["front_matter_lines"] = list(digest.front_matter_lines)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
            print(f"Scene digest written to {args.output}")
        else:
            print(text)
    else:
        print(f"File: {digest.file_path}")
        print(f"Encoding: {digest.encoding}  Lines: {digest.total_lines}  Scenes: {digest.scene_count}")
        if digest.front_matter_lines:
            print(f"Front matter: lines {digest.front_matter_lines[0]}-{digest.front_matter_lines[1]}")
        for s in digest.scenes:
            meta = []
            if s.scene_number is not None:
                meta.append(f"#{s.scene_number}")
            if s.location_hint:
                meta.append(s.location_hint)
            if s.time_hint:
                meta.append(s.time_hint)
            meta_str = " | ".join(meta) if meta else "(no metadata)"
            unresolved = " [UNRESOLVED]" if s.status == "unresolved" else ""
            print(f"  [{s.start_line}-{s.end_line}] {s.header_kind}: {meta_str}{unresolved}")

    return 0 if digest.scene_count > 0 else 1


if __name__ == "__main__":
    from cli_stdio import configure_utf8_stdio

    configure_utf8_stdio()
    raise SystemExit(main())
