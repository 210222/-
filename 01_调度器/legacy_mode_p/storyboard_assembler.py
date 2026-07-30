#!/usr/bin/env python3
"""
storyboard_assembler.py v1.0 — deterministic storyboard generator. 0 LLM tokens.
Reads PLAN YAML (same input as script_assembler) → generates dispatcher v7.0
方式C storyboard: per-shot SEKO code blocks with anchor frames.
"""
import yaml, re, argparse
from script_assembler import (load_plan, zone_of, shot_type_key, word_count,
                               build_audio, build_prohibit, _sanitize)

NL = "\n"

def _perf_text(kf: dict) -> str:
    """Extract performance as compact visual text."""
    perf = kf.get("performance", {})
    if not perf: return ""
    parts = []
    for section in ["facial", "body"]:
        d = perf.get(section, {})
        for v in d.values():
            if v and len(str(v)) > 5:
                parts.append(_sanitize(str(v)))
    return "。".join(parts[:2]) if parts else ""

def _camera_desc(seg: dict) -> str:
    """Compact camera position description."""
    angle = seg.get("angle", "")
    cam_type = seg.get("camera_type", "")
    pos = seg.get("camera_position", "")[:60]
    return f"{angle} | {cam_type} | {pos}"

def _light_short(anchors: dict, seg: dict) -> str:
    """Short light description for storyboard grids."""
    lit = anchors.get("lighting", {})
    srcs = lit.get("anchor_sources", [])
    if not srcs: return ""
    z = zone_of(seg.get("camera_position", ""))
    # Return kelvin values for the relevant sources
    temps = [f"{s.get('source','')[:8]}{s.get('kelvin','')}K" for s in srcs[:3]]
    return " + ".join(temps) if temps else ""

def _anchor_summary(seg: dict, anchors: dict) -> str:
    """Generate shared visual anchor summary for all grids in this shot."""
    chars = seg.get("characters_in_frame", [])
    char_text = ""
    if chars:
        char_data = anchors.get("character", {})
        char_parts = []
        for ch in chars:
            if ch in char_data:
                traits = char_data[ch]
                if isinstance(traits, list):
                    char_parts.append(f"{ch}: {traits[0][:60]}")
                else:
                    char_parts.append(f"{ch}: {str(traits)[:60]}")
        char_text = " · ".join(char_parts)
    env = anchors.get("environment", {}).get("description", "")[:100]
    light = _light_short(anchors, seg)
    parts = [env, light]
    if char_text: parts.append(char_text)
    return " · ".join(p for p in parts if p)

def _expand_grids(seg: dict, anchors: dict, lit_name: str) -> list:
    """Expand keyframes into per-second grid frame descriptions."""
    sf = seg.get("segment_frames", {}) if isinstance(seg.get("segment_frames"), dict) else {}
    kfs = sf.get("keyframes", []) if sf else []
    dur = seg.get("duration_s", 0)
    start = seg.get("global_sec_start", 0)
    grids = []

    if not kfs:
        # Fallback: one grid per segment range
        for offset in range(dur):
            gs = start + offset
            grids.append({
                "sec": gs, "offset": offset,
                "desc": f"画面同前。{lit_name}。持续第{offset+1}秒。",
                "body": "", "camera": "", "comp": "", "light": lit_name
            })
        return grids

    kf_idx = 0
    for offset in range(dur):
        gs = start + offset
        # Advance keyframe index
        while (kf_idx + 1 < len(kfs) and
               kfs[kf_idx + 1].get("sec_offset", 0) <= offset):
            kf_idx += 1
        kf = kfs[kf_idx]
        kf_type = kf.get("type", "hold")
        action = _sanitize(kf.get("action_anchor", ""))
        desc = _sanitize(kf.get("description", ""))
        lighting = kf.get("lighting", lit_name)
        spatial = kf.get("spatial", "")
        perf = _perf_text(kf)
        cam_desc = ""
        if offset == 0 or kf_type == "event":
            cam_desc = f"{seg.get('shot_type','')}·{seg.get('focal_length','')}·{seg.get('movement','static')}"

        # Compact grid description
        parts = [action]
        if desc and desc != action: parts.append(desc)
        if perf: parts.append(perf)
        frame_desc = "。".join(p for p in parts if p)

        # Annotations
        body = kf.get("action_anchor", "")[:80]
        camera = f"静态0x" if seg.get("camera_fixed", True) else f"{seg.get('movement','')}"[:50]
        comp = spatial[:80] if spatial else seg.get("camera_position", "")[:80]
        light = lighting[:80]

        grids.append({
            "sec": gs, "offset": offset,
            "desc": frame_desc,
            "body": body, "camera": camera,
            "comp": comp, "light": light,
            "shot_type": seg.get("shot_type", ""),
            "focal": seg.get("focal_length", ""),
            "movement": seg.get("movement", "static"),
        })
    return grids

def _prohibit_storyboard(seg: dict) -> str:
    """Generate storyboard-specific prohibitions."""
    chars = seg.get("characters_in_frame", [])
    p = []
    if chars:
        p.append("角色面部比例全程一致·五官不漂移")
    p.append("空间结构元素与参考图一致·不凭空添加")
    if not seg.get("camera_fixed", True):
        p.append("运镜速度均匀·起幅落幅静态清晰")
    p.append("不渲染文字·不出现水印Logo")
    return NL.join(f"{i+1}. {x}" for i, x in enumerate(p))

def _audio_storyboard(seg: dict, dial: list) -> str:
    """Generate storyboard audio annotations with SFX<> and VO{}."""
    dur = seg.get("duration_s", 6)
    start = seg.get("global_sec_start", 0)
    lines = []
    # Ambience
    z = zone_of(seg.get("camera_position", ""))
    amb = ("{凌晨安静·远处冰箱低鸣}" if z == "D" else
           "{城市清晨环境·低频远处交通}" if z == "ST" else
           "{室内安静·吊灯电流微嗡}")
    lines.append(amb)
    # Key events from keyframe data
    sf = seg.get("segment_frames", {}) if isinstance(seg.get("segment_frames"), dict) else {}
    kfs = sf.get("keyframes", []) if sf else []
    for kf in kfs:
        action = kf.get("action_anchor", "")
        gs = kf.get("global_sec", start + kf.get("sec_offset", 0))
        kf_type = kf.get("type", "hold")
        if "锁芯" in action and "弹" in action:
            lines.append(f"<锁芯弹开·咔嗒>")
        elif "甩镜" in action or "转头" in action:
            lines.append(f"<甩镜衣物急速摩擦>")
        elif "脚步" in action:
            lines.append(f"<走廊皮靴脚步声·由远及近>")
        elif "门" in action and ("闭" in action or "合" in action):
            lines.append(f"<门闭合铰链微声>")
        elif "钥匙" in action and ("插" in action or "拔" in action):
            lines.append(f"<钥匙金属摩擦声>")
        elif "扭" in action and "钥匙" in action:
            lines.append(f"<锁芯转动>")
    # Dialogue
    for d in dial:
        sp = d.get("s", d.get("speaker", "?"))
        t = d.get("t", d.get("text", ""))
        direction = d.get("d", d.get("direction", ""))
        tag = "VO" if sp == "VO" else f"CV {sp}"
        lines.append(f"{{{tag}({direction}): {t}}}")
    return NL.join(lines)

def build_storyboard_shot(seg: dict, anchors: dict, dial: list) -> str:
    """Build one shot's storyboard block in dispatcher v7.0 format."""
    sid = seg.get("shot_id", "?")
    dur = seg.get("duration_s", 0)
    st = seg.get("shot_type", "")
    chars = seg.get("characters_in_frame", [])
    lit_name = _light_short(anchors, seg)

    lines = []
    # Header
    desc_short = seg.get("camera_type", st)[:40]
    lines.append(f"镜{sid}: {desc_short} ({dur}s)")

    # @ references
    for ch in chars:
        ch_data = anchors.get("character", {}).get(ch, "")
        if isinstance(ch_data, list): ch_data = ch_data[0][:50]
        lines.append(f"@{ch} {str(ch_data)[:60]}")
    lit = anchors.get("lighting", {})
    for s in lit.get("anchor_sources", [])[:3]:
        lines.append(f"@{s.get('ref_grid','')} — {s.get('source','')[:20]}")

    lines.append("")
    lines.append("```  ← SEKO prompt代码块")
    lines.append("黑白手绘线稿故事板。N格电影分镜·按秒排列。16:9。粗糙铅笔线条，")
    lines.append("动态未完成感，强烈轮廓。纸张纹理。仅黑白——不渲染光影色彩材质。")
    lines.append("")
    lines.append("标注颜色系统: 🔴红=身体运动 🔵蓝=相机运动 🟢绿=构图 🟠橙=光线 ⚫黑=时间+景别+运镜")
    lines.append("")

    # Shared visual anchors
    anchor_text = _anchor_summary(seg, anchors)
    lines.append(f"共享视觉锚(全部{dur}格):")
    lines.append(f"{anchor_text[:300]}")
    lines.append("")

    # Numbered camera position
    lines.append("编号含义:")
    cam_desc = _camera_desc(seg)
    lines.append(f"① = {st}·{seg.get('focal_length','')}·{seg.get('movement','static')}·{cam_desc[:100]}")
    lines.append("")

    # Segment header
    mover = seg.get("movement", "static")
    lines.append("─" * 24)
    lines.append(f"① [0-{dur}s] {st}·{seg.get('focal_length','')}·{mover}·{cam_desc[:80]}")
    lines.append("─" * 24)
    lines.append("")

    # Per-second grids
    grids = _expand_grids(seg, anchors, lit_name)
    for g in grids:
        lines.append(f"格{g['sec']}s [{g['sec']}s] {g['desc'][:200]}")
        lines.append(f"🔴{g['body'][:80]}")
        lines.append(f"🔵{g['camera'][:80]}")
        lines.append(f"🟢{g['comp'][:80]}")
        lines.append(f"🟠{g['light'][:80]}")
        lines.append("")

    # Audio
    lines.append("@音轨:")
    audio_lines = _audio_storyboard(seg, dial)
    lines.append(audio_lines)
    lines.append("")

    # Prohibit
    lines.append("@禁止:")
    lines.append(_prohibit_storyboard(seg))
    lines.append("```")
    return NL.join(lines)

def assemble_storyboard(plan_path: str, script_path: str, output_path: str) -> str:
    plan = load_plan(plan_path)
    scene, anchors, segments = plan["scene"], plan["anchors"], plan["segments"]
    dialogue_map = plan.get("dialogue_map", [])

    # Build dialogue distribution (same logic as script_assembler)
    from script_assembler import parse_dialogue_from_script, build_dialogue_map
    dlgs_raw = parse_dialogue_from_script(script_path)
    dm_by_shot = {dm.get("shot_id", ""): dm.get("entries", []) for dm in dialogue_map} if dialogue_map else {}
    ddist = {}
    for seg in segments:
        sid = seg["shot_id"]
        if sid in dm_by_shot:
            ddist[sid] = [{"s": e["speaker"], "t": e.get("text_pt", e.get("text", "")),
                          "d": e.get("direction", ""),
                          "o": (e.get("global_sec_start", 0) - seg.get("global_sec_start", 0)) / max(1, seg.get("duration_s", 6)),
                          "du": e.get("duration_s", 2.5)} for e in dm_by_shot[sid]]
        else:
            ddist[sid] = []
    if not any(v for v in ddist.values()):
        ddist = build_dialogue_map(dlgs_raw, segments)

    # Merge segment_frames
    segment_frames = plan.get("segment_frames", [])
    sf_by_id = {sf.get("segment_id", sf.get("shot_id", "")): sf for sf in segment_frames} if segment_frames else {}
    for seg in segments:
        sid = seg["shot_id"]
        if sid in sf_by_id:
            seg["segment_frames"] = sf_by_id[sid]
            if "characters_in_frame" in sf_by_id[sid]:
                seg["characters_in_frame"] = sf_by_id[sid]["characters_in_frame"]

    out = [f"# STORYBOARD · EP2 Act1 · Rico工作室 · {scene.get('total_shots',0)}镜·{scene.get('total_duration_s',0)}s{NL}"]
    out.append(f"> **生成:** storyboard_assembler v1.0 · deterministic · 0 LLM tokens")
    out.append(f"> **格式:** dispatcher v7.0 §故事板 方式C · 每镜独立SEKO代码块{NL}")

    for seg in segments:
        sid = seg.get("shot_id", "?")
        dial = ddist.get(sid, [])
        out.append(build_storyboard_shot(seg, anchors, dial))
        out.append(f"{NL}---{NL}")

    out.append(f"> **storyboard_assembler v1.0** | deterministic | 0 LLM tokens | 0 Agent calls")
    result = NL.join(out)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"OK: {output_path}")
    print(f"    {len(segments)} shots, {scene.get('total_duration_s',0)}s, {len(result)} chars")
    return result

def main():
    p = argparse.ArgumentParser(description="storyboard_assembler.py v1.0")
    p.add_argument("--plan", required=True, help="PLAN YAML file path")
    p.add_argument("--script", required=True, help="Original script .txt path")
    p.add_argument("--output", required=True, help="Output storyboard .md path")
    args = p.parse_args()
    assemble_storyboard(args.plan, args.script, args.output)

if __name__ == "__main__":
    main()
