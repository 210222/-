"""Deterministic checks for completed L1 episode documents.

The checker verifies provenance and structural coverage only.  It never judges
the Director's visual choices or rewrites creative content.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from script_facts_tool import FactsError, load_digest, validate_facts


_SOURCE_HASH_RE = re.compile(
    r"<!--\s*source_sha256:\s*([0-9a-f]{64})\s*-->")
_FACTS_HASH_RE = re.compile(
    r"<!--\s*script_facts_sha256:\s*([0-9a-f]{64})\s*-->")
_PLACEHOLDER_RE = re.compile(
    r"\[Director:|<Name>|<N>", re.IGNORECASE)

_BIBLE_HEADINGS = (
    "## 1. 全片戏剧与信息释放弧线",
    "## 2. 人物视觉关系",
    "## 3. 色彩、光比与稳定性变化",
    "## 4. 关键空间拍摄逻辑",
    "## 5. 视觉母题与使用边界",
    "## 6. 各场景戏剧功能与视觉强度",
)
_LEDGER_HEADINGS = (
    "## 1. 人物连续性",
    "## 2. 道具连续性",
    "## 3. 时间、天气与环境",
    "## 4. 场间交接状态",
    "## 5. 已知事实摘要",
)


@dataclass
class EpisodeDocIssue:
    document: str
    detail: str


@dataclass
class EpisodeDocsReport:
    issues: list[EpisodeDocIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def check_episode_docs(ingest_json_path: Path, facts_path: Path,
                       bible_path: Path, ledger_path: Path) -> EpisodeDocsReport:
    report = EpisodeDocsReport()
    try:
        digest = load_digest(ingest_json_path)
    except FactsError as exc:
        report.issues.append(EpisodeDocIssue("ingest digest", str(exc)))
        return report

    facts_report = validate_facts(facts_path, ingest_json_path)
    if not facts_report.ok:
        for issue in facts_report.issues[:10]:
            report.issues.append(EpisodeDocIssue(
                "SCRIPT_FACTS.md", f"{issue.location}: {issue.detail}"))
        return report

    try:
        facts_hash = hashlib.sha256(facts_path.read_bytes()).hexdigest()
    except OSError as exc:
        report.issues.append(EpisodeDocIssue(
            "SCRIPT_FACTS.md", f"Cannot read facts: {exc}"))
        return report

    documents: dict[str, str] = {}
    for name, path in (
        ("EPISODE_VISUAL_BIBLE.md", bible_path),
        ("EPISODE_CONTINUITY_LEDGER.md", ledger_path),
    ):
        try:
            documents[name] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            report.issues.append(EpisodeDocIssue(name, f"Cannot read document: {exc}"))

    if len(documents) != 2:
        return report

    for name, text in documents.items():
        source_hashes = _SOURCE_HASH_RE.findall(text)
        if source_hashes != [digest["source_content_hash"]]:
            report.issues.append(EpisodeDocIssue(
                name, "Source hash is missing, duplicated, or stale"))
        facts_hashes = _FACTS_HASH_RE.findall(text)
        if facts_hashes != [facts_hash]:
            report.issues.append(EpisodeDocIssue(
                name, "SCRIPT_FACTS hash is missing, duplicated, or stale"))
        match = _PLACEHOLDER_RE.search(text)
        if match:
            line_no = text.count("\n", 0, match.start()) + 1
            report.issues.append(EpisodeDocIssue(
                name, f"Unresolved Director placeholder at line {line_no}"))

    bible = documents["EPISODE_VISUAL_BIBLE.md"]
    ledger = documents["EPISODE_CONTINUITY_LEDGER.md"]
    _check_headings(report, "EPISODE_VISUAL_BIBLE.md", bible, _BIBLE_HEADINGS)
    _check_headings(report, "EPISODE_CONTINUITY_LEDGER.md", ledger, _LEDGER_HEADINGS)
    _check_bible_scene_table(report, bible, digest["scenes"])
    _check_ledger_scene_table(report, ledger, digest["scenes"])
    _check_handoffs(report, ledger, digest["scenes"])
    return report


def _check_headings(report: EpisodeDocsReport, name: str, text: str,
                    required: tuple[str, ...]) -> None:
    positions: list[int] = []
    for heading in required:
        count = text.count(heading)
        if count != 1:
            report.issues.append(EpisodeDocIssue(
                name, f"Required heading must appear once: {heading}"))
            continue
        positions.append(text.index(heading))
    if len(positions) == len(required) and positions != sorted(positions):
        report.issues.append(EpisodeDocIssue(name, "Required headings are out of order"))


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    rest = text[start + len(heading):]
    next_heading = re.search(r"^##\s+", rest, re.MULTILINE)
    return rest[:next_heading.start()] if next_heading else rest


def _table_scene_rows(section: str) -> list[tuple[int, int | None, int | None]]:
    rows: list[tuple[int, int | None, int | None]] = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not cells[0].isdigit():
            continue
        range_match = re.search(r"L(\d+)-L(\d+)", line)
        rows.append((
            int(cells[0]),
            int(range_match.group(1)) if range_match else None,
            int(range_match.group(2)) if range_match else None,
        ))
    return rows


def _check_bible_scene_table(report: EpisodeDocsReport, text: str,
                             scenes: list[dict]) -> None:
    rows = _table_scene_rows(_section(text, _BIBLE_HEADINGS[-1]))
    expected = [
        (scene["index"], scene["start_line"], scene["end_line"])
        for scene in scenes
    ]
    if rows != expected:
        report.issues.append(EpisodeDocIssue(
            "EPISODE_VISUAL_BIBLE.md",
            f"Scene function table mismatch: expected {expected}, got {rows}"))


def _check_ledger_scene_table(report: EpisodeDocsReport, text: str,
                             scenes: list[dict]) -> None:
    rows = _table_scene_rows(_section(text, _LEDGER_HEADINGS[2]))
    indexes = [row[0] for row in rows]
    expected = [scene["index"] for scene in scenes]
    if indexes != expected:
        report.issues.append(EpisodeDocIssue(
            "EPISODE_CONTINUITY_LEDGER.md",
            f"Environment table scene order mismatch: expected {expected}, got {indexes}"))


def _check_handoffs(report: EpisodeDocsReport, text: str,
                    scenes: list[dict]) -> None:
    handoff_section = _section(text, _LEDGER_HEADINGS[3])
    required = ["开篇 → 场景 1"]
    required.extend(
        f"场景 {left['index']} → 场景 {right['index']}"
        for left, right in zip(scenes, scenes[1:])
    )
    required.append(f"场景 {scenes[-1]['index']} → 结束")
    for marker in required:
        if handoff_section.count(marker) != 1:
            report.issues.append(EpisodeDocIssue(
                "EPISODE_CONTINUITY_LEDGER.md",
                f"Required handoff must appear once: {marker}"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check completed L1 episode documents")
    parser.add_argument("ingest_json", type=Path)
    parser.add_argument("facts_md", type=Path)
    parser.add_argument("visual_bible", type=Path)
    parser.add_argument("continuity_ledger", type=Path)
    args = parser.parse_args()

    report = check_episode_docs(
        args.ingest_json, args.facts_md, args.visual_bible, args.continuity_ledger)
    if report.ok:
        print("Episode documents: PASS")
        return 0
    for issue in report.issues:
        print(f"[{issue.document}] {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
