"""Generate EPISODE_VISUAL_BIBLE.md and EPISODE_CONTINUITY_LEDGER.md skeletons.

These are L1 (Lead Director) documents. The local program generates structured
skeletons from a validated script-facts package; the Director fills in the
creative content. Implements LOOP_SPEC v2.1 §8.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from script_facts_tool import FactsError, load_digest, validate_facts


class EpisodeTemplateError(Exception):
    """Raised when L1 documents cannot be generated from trusted inputs."""


def _prepare_inputs(ingest_json_path: Path, facts_path: Path) -> tuple[dict, str]:
    try:
        digest = load_digest(ingest_json_path)
    except FactsError as exc:
        raise EpisodeTemplateError(str(exc)) from exc
    report = validate_facts(facts_path, ingest_json_path)
    if not report.ok:
        details = "; ".join(
            f"{issue.location}: {issue.detail}" for issue in report.issues[:5])
        raise EpisodeTemplateError(f"SCRIPT_FACTS validation failed: {details}")
    try:
        facts_hash = hashlib.sha256(facts_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise EpisodeTemplateError(f"Cannot read SCRIPT_FACTS {facts_path}: {exc}") from exc
    return digest, facts_hash


def _write_output(path: Path | None, text: str) -> None:
    if path is None:
        return
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise EpisodeTemplateError(f"Cannot write episode document {path}: {exc}") from exc


# ---------------------------------------------------------------------------
# EPISODE_VISUAL_BIBLE.md
# ---------------------------------------------------------------------------

def generate_visual_bible(ingest_json_path: Path, facts_path: Path,
                          output_path: Path | None = None) -> str:
    """Generate an EPISODE_VISUAL_BIBLE.md skeleton."""
    digest, facts_hash = _prepare_inputs(ingest_json_path, facts_path)
    script_name = Path(digest["file_path"]).name
    scene_count = digest["scene_count"]

    lines: list[str] = []
    lines.append(f"# EPISODE_VISUAL_BIBLE — {script_name}")
    lines.append("")
    lines.append("<!-- contract: episode_docs v1.0 -->")
    lines.append(f"<!-- source_sha256: {digest['source_content_hash']} -->")
    lines.append(f"<!-- script_facts_sha256: {facts_hash} -->")
    lines.append("<!-- Director must replace every [Director: ...] placeholder. -->")
    lines.append("")

    # 1. Drama & Information Arc
    lines.append("## 1. 全片戏剧与信息释放弧线")
    lines.append("")
    lines.append("[Director: 描述全片（共 {} 场）的戏剧结构。".format(scene_count))
    lines.append("  - 主要冲突线、转折点和情感高潮位置。")
    lines.append("  - 信息释放顺序：观众何时知道、误解或发现什么。")
    lines.append("  - 哪些场景承载揭示，哪些承载铺垫或后果。]")
    lines.append("")

    # 2. Character Visual Relationships
    lines.append("## 2. 人物视觉关系")
    lines.append("")
    lines.append("[Director: 为每对关键关系描述视觉距离、角度、景别和占画比例的演变；")
    lines.append("  根据本集戏剧关系自行决定视觉策略，模板不提供默认镜头答案。]")
    lines.append("")
    lines.append("### 场景级关系变化")
    for s in digest["scenes"]:
        loc = s.get("location_hint") or "?"
        lines.append(f"- **场景 {s['index']}** ({loc}): [Director: 人物视觉关系]")
    lines.append("")

    # 3. Color & Light Arc
    lines.append("## 3. 色彩、光比与稳定性变化")
    lines.append("")
    lines.append("[Director: 定义全片色彩路径（冷暖、饱和度变化）、")
    lines.append("  光比范围和高低点、镜头稳定性（手持/稳定器/固定）的变化时机。]")
    lines.append("")
    for s in digest["scenes"]:
        loc = s.get("location_hint") or "?"
        time = s.get("time_hint") or "?"
        lines.append(f"- **场景 {s['index']}** ({loc}, {time}): [Director: 色彩/光比/稳定性描述]")
    lines.append("")

    # 4. Spatial Logic
    lines.append("## 4. 关键空间拍摄逻辑")
    lines.append("")
    lines.append("[Director: 每个重复出现的关键空间，描述其固定拍摄方向、")
    lines.append("  可重复的视觉锚点和空间关系线。]")
    lines.append("")

    # 5. Visual Motifs
    lines.append("## 5. 视觉母题与使用边界")
    lines.append("")
    lines.append("[Director: 列出必须保留的视觉母题（如特定构图、色彩、物体、光线模式）")
    lines.append("  以及使用边界（何时出现、何时不能出现）。]")
    lines.append("")

    # 6. Per-Scene Functions
    lines.append("## 6. 各场景戏剧功能与视觉强度")
    lines.append("")
    lines.append("| # | 场景 | 行号 | 戏剧功能 | 视觉强度 | 转场意图 |")
    lines.append("|---|------|------|----------|----------|----------|")
    for s in digest["scenes"]:
        title = (s.get("header_line", "") or f"Scene {s['index']}")[:30]
        loc = s.get("location_hint") or "?"
        lines.append(
            f"| {s['index']} | {title} "
            f"| L{s['start_line']}-L{s['end_line']} "
            f"| [Director: 功能] | [Director: 低/中/高] | [Director: 意图] |"
        )
    lines.append("")

    text = "\n".join(lines) + "\n"
    _write_output(output_path, text)
    return text


# ---------------------------------------------------------------------------
# EPISODE_CONTINUITY_LEDGER.md
# ---------------------------------------------------------------------------

def generate_continuity_ledger(ingest_json_path: Path, facts_path: Path,
                               output_path: Path | None = None) -> str:
    """Generate an EPISODE_CONTINUITY_LEDGER.md skeleton."""
    digest, facts_hash = _prepare_inputs(ingest_json_path, facts_path)
    script_name = Path(digest["file_path"]).name

    lines: list[str] = []
    lines.append(f"# EPISODE_CONTINUITY_LEDGER — {script_name}")
    lines.append("")
    lines.append("<!-- contract: episode_docs v1.0 -->")
    lines.append(f"<!-- source_sha256: {digest['source_content_hash']} -->")
    lines.append(f"<!-- script_facts_sha256: {facts_hash} -->")
    lines.append("<!-- Director must replace every [Director: ...] placeholder. -->")
    lines.append("")

    # 1. Character Continuity
    lines.append("## 1. 人物连续性")
    lines.append("")
    lines.append("[Director: 为每个角色创建连续性条目。]")
    lines.append("")
    lines.append("### 模板")
    lines.append("```")
    lines.append("## 角色：<Name>")
    lines.append("  首次出现：场景 <N>")
    lines.append("  ")
    lines.append("  场景 1: 外观= 服装= 伤势= 携带物= 位置=")
    lines.append("  场景 2: 外观= 服装= 伤势= 携带物= 位置=")
    lines.append("  ...")
    lines.append("```")
    lines.append("")

    # 2. Prop Continuity
    lines.append("## 2. 道具连续性")
    lines.append("")
    lines.append("[Director: 为每个重要道具记录跨场归属、位置和状态变化。]")
    lines.append("")
    for s in digest["scenes"]:
        loc = s.get("location_hint") or "?"
        lines.append(f"- **场景 {s['index']}** ({loc}): [Director: 道具及状态]")
    lines.append("")

    # 3. Time / Weather / Environment
    lines.append("## 3. 时间、天气与环境")
    lines.append("")
    lines.append("| 场景 | 时间 | 天气 | 环境光源 | 备注 |")
    lines.append("|------|------|------|----------|------|")
    for s in digest["scenes"]:
        time = s.get("time_hint") or "UNKNOWN"
        lines.append(
            f"| {s['index']} | {time} "
            f"| [Director: 天气] | [Director: 环境光] | [Director: 备注] |"
        )
    lines.append("")

    # 4. Scene Handoff States
    lines.append("## 4. 场间交接状态")
    lines.append("")
    lines.append("[Director: 记录每场如何结束、下一场必须从什么事实开始。")
    lines.append("  这些是跨场边界契约，确保场景间连续性。]")
    lines.append("")
    for i, s in enumerate(digest["scenes"]):
        loc = s.get("location_hint") or "?"
        if i == 0:
            lines.append(f"- **开篇 → 场景 1**: [Director: 开场世界状态（时间、天气、已有事实）]")
        if i < len(digest["scenes"]) - 1:
            nxt = digest["scenes"][i + 1]
            nxt_loc = nxt.get("location_hint") or "?"
            lines.append(f"- **场景 {s['index']} → 场景 {nxt['index']}** ({loc} → {nxt_loc}): "
                         f"[Director: 交出状态（人物位置/道具/光线/动作阶段）]")
        else:
            lines.append(f"- **场景 {s['index']} → 结束**: [Director: 全片结束状态]")
    lines.append("")

    # 5. Known Facts Summary
    lines.append("## 5. 已知事实摘要")
    lines.append("")
    lines.append("[Director: 从 SCRIPT_FACTS.md 提取关键连续性事实，按类别组织。")
    lines.append("  这是快速参考，不替代逐场细节。]")
    lines.append("")
    lines.append("- **人物外观**: [Director: 摘要]")
    lines.append("- **重要道具**: [Director: 摘要]")
    lines.append("- **环境**: [Director: 摘要]")
    lines.append("- **时间线**: [Director: 摘要]")
    lines.append("")

    text = "\n".join(lines) + "\n"
    _write_output(output_path, text)
    return text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Episode Visual Bible and Continuity Ledger skeletons."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    vb = sub.add_parser("bible", help="Generate EPISODE_VISUAL_BIBLE.md")
    vb.add_argument("ingest_json", type=Path, help="script_ingest output JSON")
    vb.add_argument("facts_md", type=Path, help="validated SCRIPT_FACTS.md")
    vb.add_argument("-o", "--output", type=Path, default=None)

    cl = sub.add_parser("ledger", help="Generate EPISODE_CONTINUITY_LEDGER.md")
    cl.add_argument("ingest_json", type=Path, help="script_ingest output JSON")
    cl.add_argument("facts_md", type=Path, help="validated SCRIPT_FACTS.md")
    cl.add_argument("-o", "--output", type=Path, default=None)

    both = sub.add_parser("all", help="Generate both Bible and Ledger")
    both.add_argument("ingest_json", type=Path, help="script_ingest output JSON")
    both.add_argument("facts_md", type=Path, help="validated SCRIPT_FACTS.md")
    both.add_argument("-d", "--output-dir", type=Path, default=None)

    args = parser.parse_args()

    try:
        if args.command == "bible":
            out = args.output
            text = generate_visual_bible(args.ingest_json, args.facts_md, out)
            if not out:
                print(text)
            else:
                print(f"Visual Bible -> {out}")
        elif args.command == "ledger":
            out = args.output
            text = generate_continuity_ledger(args.ingest_json, args.facts_md, out)
            if not out:
                print(text)
            else:
                print(f"Continuity Ledger -> {out}")
        elif args.command == "all":
            base = args.output_dir or args.ingest_json.parent
            base.mkdir(parents=True, exist_ok=True)
            vb_out = base / "EPISODE_VISUAL_BIBLE.md"
            cl_out = base / "EPISODE_CONTINUITY_LEDGER.md"
            generate_visual_bible(args.ingest_json, args.facts_md, vb_out)
            generate_continuity_ledger(args.ingest_json, args.facts_md, cl_out)
            print(f"Visual Bible -> {vb_out}")
            print(f"Continuity Ledger -> {cl_out}")
    except (EpisodeTemplateError, OSError) as exc:
        print(f"Episode template error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    from cli_stdio import configure_utf8_stdio

    configure_utf8_stdio()
    raise SystemExit(main())
