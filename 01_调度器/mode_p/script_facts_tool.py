"""Generate and validate SCRIPT_FACTS.md from script ingest output.

L0.3: Director generates SCRIPT_FACTS from scene boundaries, attaching
source line ranges to each fact.
L0.4: Local program checks that all fact references exist within scene bounds.

This tool provides two commands:
  generate — create a SCRIPT_FACTS.md skeleton from script_ingest JSON
  validate — check that a filled SCRIPT_FACTS.md has valid references
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_FACT_REF_RE = re.compile(r"^\s*-\s*\[L(\d+)(?:-L(\d+))?\]\s+(.+?)\s*$")
_SCENE_HEADER_RE = re.compile(
    r"^##\s+场景\s+(\d+)\s+事实\s*$"
)
_SUBSECTION_RE = re.compile(r"^###\s+(.+?)\s*$")
_SOURCE_HASH_RE = re.compile(
    r"<!--\s*source_sha256:\s*([0-9a-fA-F]{64})\s*-->"
)
_DIRECTOR_PLACEHOLDER_RE = re.compile(r"\[Director:", re.IGNORECASE)
_REQUIRED_FACT_SECTIONS = {"事件", "对白", "连续性入口"}
_REFERENCE_FACT_SECTIONS = _REQUIRED_FACT_SECTIONS | {"未确定项"}


@dataclass
class FactRefIssue:
    location: str  # e.g. "场景 2, line 15"
    detail: str


@dataclass
class ValidateReport:
    issues: list[FactRefIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


class FactsError(Exception):
    """Raised when facts inputs cannot be read or do not satisfy the contract."""


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def generate_facts(ingest_json_path: Path, output_path: Path | None = None) -> str:
    """Generate a SCRIPT_FACTS.md skeleton from ingest JSON."""
    digest = load_digest(ingest_json_path)
    source_hash = digest.get("source_content_hash")
    if not isinstance(source_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", source_hash):
        raise FactsError("Ingest digest is missing a valid source_content_hash")
    lines: list[str] = []
    script_name = Path(digest["file_path"]).name

    lines.append(f"# SCRIPT_FACTS — {script_name}")
    lines.append("")
    lines.append("<!-- contract: script_input v1.1 -->")
    lines.append(f"<!-- source_sha256: {source_hash} -->")
    lines.append("")
    lines.append("## 源信息")
    lines.append(f"- 文件：{digest['file_path']}")
    lines.append(f"- 编码：{digest['encoding']}")
    lines.append(f"- 总行数：{digest['total_lines']}")
    lines.append(f"- 场景数：{digest['scene_count']}")
    lines.append("")
    lines.append("## 场景清单")
    lines.append("| # | 标题 | 行号 | 地点 | 时间 | 状态 |")
    lines.append("|---|------|------|------|------|------|")
    for s in digest["scenes"]:
        title = s.get("header_line", "(无标题)")[:40]
        loc = s.get("location_hint") or "UNKNOWN"
        time = s.get("time_hint") or "UNKNOWN"
        status = s.get("status", "resolved")
        lines.append(
            f"| {s['index']} | {title} | L{s['start_line']}-L{s['end_line']} "
            f"| {loc} | {time} | {status} |"
        )
    lines.append("")

    lines.append("## 角色清单")
    lines.append("| 角色 | 首次出现行 | 确定度 | 说明 |")
    lines.append("|------|-----------|--------|------|")
    lines.append("| [Director: 从剧本中识别角色名称和首次出现行号；完成后删除本行] | | | |")
    lines.append("")

    for s in digest["scenes"]:
        lines.append(f"## 场景 {s['index']} 事实")
        title = s.get("header_line", "(无标题)")[:60]
        lines.append(f"_原文：{title}_  _行号：L{s['start_line']}-L{s['end_line']}_")
        lines.append("")
        lines.append("### 事件")
        lines.append("[Director: 列出本场所有叙事事件；单行使用 '- [Lx] 事件描述'，跨行使用 '- [Lx-Ly] 事件描述'，完成后删除本行。]")
        lines.append("")
        lines.append("### 对白")
        lines.append("[Director: 列出本场所有对白；单行使用 '- [Lx] 说话人：对白'，跨行使用 '- [Lx-Ly] 说话人：对白'；无对白写 '- (无)'，完成后删除本行。]")
        lines.append("")
        lines.append("### 连续性入口")
        lines.append("[Director: 列出从上一场继承的可见状态；单行使用 '- [Lx] 状态'，跨行使用 '- [Lx-Ly] 状态'；首场无继承写 '- (无)'，完成后删除本行。]")
        lines.append("")
        lines.append("### 未确定项")
        if s.get("status") == "unresolved":
            lines.append("- 场景边界未确定；Director 必须先解析边界，后续验证保持失败关闭。")
        else:
            lines.append("- (无)")
        lines.append("")

    text = "\n".join(lines) + "\n"
    if output_path:
        try:
            output_path.write_text(text, encoding="utf-8")
        except OSError as exc:
            raise FactsError(f"Cannot write facts skeleton {output_path}: {exc}") from exc
    return text


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def validate_facts(facts_path: Path, ingest_json_path: Path) -> ValidateReport:
    """Validate provenance, completeness, and scene-local source references."""
    report = ValidateReport()
    try:
        facts_text = facts_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report.issues.append(FactRefIssue("facts file", f"Cannot read facts: {exc}"))
        return report
    try:
        digest = load_digest(ingest_json_path)
    except FactsError as exc:
        report.issues.append(FactRefIssue("ingest digest", str(exc)))
        return report

    digest_hash = digest.get("source_content_hash")
    hash_match = _SOURCE_HASH_RE.search(facts_text)
    if not hash_match:
        report.issues.append(FactRefIssue(
            "source hash", "Missing <!-- source_sha256: ... --> binding"))
    elif hash_match.group(1).lower() != digest_hash:
        report.issues.append(FactRefIssue(
            "source hash", "Facts source hash does not match ingest digest"))

    try:
        source_hash = _hash_source_file(
            Path(digest["file_path"]), digest["encoding"])
        if source_hash != digest_hash:
            report.issues.append(FactRefIssue(
                "source hash", "Script content changed after ingest digest was created"))
    except FactsError as exc:
        report.issues.append(FactRefIssue("source file", str(exc)))

    for match in _DIRECTOR_PLACEHOLDER_RE.finditer(facts_text):
        line_no = facts_text.count("\n", 0, match.start()) + 1
        report.issues.append(FactRefIssue(
            f"line {line_no}", "Unresolved Director placeholder"))

    scene_ranges: dict[int, tuple[int, int]] = {}
    resolved_scenes: set[int] = set()
    for scene in digest["scenes"]:
        number = scene["index"]
        scene_ranges[number] = (scene["start_line"], scene["end_line"])
        if scene.get("status", "resolved") == "unresolved":
            report.issues.append(FactRefIssue(
                f"场景 {number}", "Scene boundary remains unresolved"))
        else:
            resolved_scenes.add(number)

    current_scene: int | None = None
    current_subsection: str | None = None
    seen_scene_order: list[int] = []
    seen_sections: dict[int, set[str]] = {number: set() for number in scene_ranges}
    valid_events: dict[int, int] = {number: 0 for number in scene_ranges}

    for line_no, line in enumerate(facts_text.splitlines(), 1):
        stripped = line.strip()
        scene_match = _SCENE_HEADER_RE.fullmatch(stripped)
        if scene_match:
            current_scene = int(scene_match.group(1))
            current_subsection = None
            if current_scene in seen_scene_order:
                report.issues.append(FactRefIssue(
                    f"line {line_no}", f"Duplicate scene facts section: {current_scene}"))
            seen_scene_order.append(current_scene)
            if current_scene not in scene_ranges:
                report.issues.append(FactRefIssue(
                    f"line {line_no}",
                    f"Scene {current_scene} not found in ingest data"))
            continue

        if stripped.startswith("## "):
            current_scene = None
            current_subsection = None
            continue

        subsection_match = _SUBSECTION_RE.fullmatch(stripped)
        if subsection_match and current_scene is not None:
            current_subsection = subsection_match.group(1)
            if current_scene in seen_sections:
                seen_sections[current_scene].add(current_subsection)
            continue

        fact_match = _FACT_REF_RE.fullmatch(line)
        if current_scene is not None and current_subsection in _REFERENCE_FACT_SECTIONS:
            if not stripped or stripped.startswith("<!--"):
                continue
            if re.fullmatch(r"\s*-\s*\(无\)\s*", line):
                continue
            if not fact_match:
                report.issues.append(FactRefIssue(
                    f"场景 {current_scene}, line {line_no}",
                    "Fact entry must be a bullet beginning with [Lx] or [Lx-Ly]"))
                continue
            if current_scene not in scene_ranges:
                continue
            l_start = int(fact_match.group(1))
            l_end = int(fact_match.group(2) or fact_match.group(1))
            s_start, s_end = scene_ranges[current_scene]
            range_valid = True
            if l_start > l_end:
                report.issues.append(FactRefIssue(
                    f"场景 {current_scene}, line {line_no}",
                    f"Invalid range: L{l_start} > L{l_end}"))
                range_valid = False
            if l_start < s_start or l_end > s_end:
                report.issues.append(FactRefIssue(
                    f"场景 {current_scene}, line {line_no}",
                    f"Reference [L{l_start}-L{l_end}] outside scene bounds "
                    f"[L{s_start}-L{s_end}]"))
                range_valid = False
            if range_valid and current_subsection == "事件":
                valid_events[current_scene] += 1
            continue

        if fact_match:
            report.issues.append(FactRefIssue(
                f"line {line_no}",
                "Fact reference appears outside 事件、对白、连续性入口或未确定项"))

    expected_order = list(scene_ranges)
    if seen_scene_order != expected_order:
        report.issues.append(FactRefIssue(
            "scene sections",
            f"Expected scene sections {expected_order}, got {seen_scene_order}"))
    for scene_number in expected_order:
        missing = _REQUIRED_FACT_SECTIONS - seen_sections[scene_number]
        if missing:
            report.issues.append(FactRefIssue(
                f"场景 {scene_number}",
                "Missing fact subsections: " + ", ".join(sorted(missing))))
        if scene_number in resolved_scenes and valid_events[scene_number] == 0:
            report.issues.append(FactRefIssue(
                f"场景 {scene_number}",
                "Resolved scene must contain at least one valid event fact"))

    return report


def load_digest(path: Path) -> dict:
    """Read and minimally validate a script-ingest digest."""
    try:
        digest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FactsError(f"Cannot read ingest digest {path}: {exc}") from exc
    if not isinstance(digest, dict):
        raise FactsError("Ingest digest root must be an object")
    required = {
        "file_path": str,
        "encoding": str,
        "source_content_hash": str,
        "total_lines": int,
        "scene_count": int,
        "scenes": list,
    }
    for key, expected_type in required.items():
        if not isinstance(digest.get(key), expected_type):
            raise FactsError(f"Ingest digest field {key!r} is missing or invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", digest["source_content_hash"]):
        raise FactsError("Ingest digest source_content_hash must be lowercase SHA-256")
    if digest["scene_count"] != len(digest["scenes"]) or not digest["scenes"]:
        raise FactsError("Ingest digest scene_count does not match a non-empty scenes list")
    seen: set[int] = set()
    for scene in digest["scenes"]:
        if not isinstance(scene, dict):
            raise FactsError("Each ingest scene must be an object")
        for key in ("index", "start_line", "end_line"):
            if not isinstance(scene.get(key), int):
                raise FactsError(f"Ingest scene field {key!r} is missing or invalid")
        if scene["index"] in seen or scene["index"] != len(seen) + 1:
            raise FactsError("Ingest scene indexes must be unique and consecutive from 1")
        if scene["start_line"] < 1 or scene["start_line"] > scene["end_line"]:
            raise FactsError(f"Invalid line range for ingest scene {scene['index']}")
        if scene["end_line"] > digest["total_lines"]:
            raise FactsError(f"Ingest scene {scene['index']} exceeds total_lines")
        seen.add(scene["index"])
    return digest


def _hash_source_file(path: Path, encoding: str) -> str:
    try:
        text = path.read_text(encoding=encoding).lstrip("\ufeff")
    except (OSError, UnicodeError, LookupError) as exc:
        raise FactsError(f"Cannot verify source script {path}: {exc}") from exc
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate SCRIPT_FACTS.md"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate SCRIPT_FACTS.md skeleton")
    gen.add_argument("ingest_json", type=Path, help="script_ingest output JSON")
    gen.add_argument("-o", "--output", type=Path, default=None, help="Output path")

    val = sub.add_parser("validate", help="Validate fact references")
    val.add_argument("facts_md", type=Path, help="Filled SCRIPT_FACTS.md")
    val.add_argument("ingest_json", type=Path, help="script_ingest output JSON")

    args = parser.parse_args()

    if args.command == "generate":
        try:
            output = generate_facts(args.ingest_json, args.output)
        except FactsError as exc:
            print(f"Facts error: {exc}", file=sys.stderr)
            return 1
        if not args.output:
            print(output)
        else:
            print(f"SCRIPT_FACTS.md skeleton written to {args.output}")
        return 0
    else:
        report = validate_facts(args.facts_md, args.ingest_json)
        if report.ok:
            print("All fact references are valid.")
            return 0
        for issue in report.issues:
            print(f"[{issue.location}] {issue.detail}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
