#!/usr/bin/env python3
"""
format_converter.py — 将 assembler/smoother 输出转为 MODE:P 标准中文格式
"""
import re, sys, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FIELD_MAP = {
    "Shot type": "景别", "Focal length": "焦段", "Aperture": "光圈",
    "Angle": "角度", "Camera type": "机位类型", "Camera position": "机位坐标",
    "Movement": "运镜", "Axis side": "轴线", "Model": "模型建议",
    "KB rules": "KB规则",
}

PFAL_CN = {
    "no frame text(P8)": "画面内禁止出现可读文字或字母——所有屏幕文字标注\"后期叠加\"",
    "no mm precision(P2)": "禁止mm级精度描述——使用相对描述（紧贴/微张/轻握/细线）",
    "no pupil change(P1)": "禁止描述瞳孔收缩/扩张——瞳孔固定于当前光照状态",
    "no sub-sec timing(P3)": "禁止亚秒级时序——使用持续描述（\"持续滴落\"而非\"每0.5秒\"）",
    "no facial drift(P1)": "禁止面部五官漂移或变形——特征点全程锁定",
    "max 2 audio layers(P4)": "禁止超过2个同时独立音效层",
    "no 2+ simultaneous mouth shapes(P10)": "禁止≥2个角色同时出现口型——严格交替单人口型",
    "no rendered screen text(P8)": "禁止Seko渲染屏幕文字——标注\"后期叠加\"",
    "no limb deformation from fast motion(P9)": "禁止快速运动导致肢体形变——运动控制在步行速度以下",
    "no flicker/strobe(P7)": "禁止高频视觉闪烁/条纹/噪点——背景简化·降低对比度",
}

def convert_param_card(lines):
    result = []
    for line in lines:
        line = line.strip().lstrip("- ")
        if not line or line.startswith("#"): continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip(); val = val.strip()
            cn_key = FIELD_MAP.get(key, key)
            result.append(f"- {cn_key}：{val}")
        elif line.startswith("KB"):
            result.append(f"- KB规则：{line.split(':',1)[1].strip() if ':' in line else line}")
    return "\n".join(result)

def convert_prohibit(lines):
    result = []
    for line in lines:
        line = line.strip()
        if not line or not line[0].isdigit(): continue
        text = line.split(". ", 1)[-1] if ". " in line else line
        cn = PFAL_CN.get(text, text)
        result.append(f"{len(result)+1}. {cn}")
    return "\n".join(result) if result else "1. 遵守全局P-FAL约束（参见§A）"

def convert_audio(lines):
    result = []
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.lower().startswith("ambience"):
            result.append(f"环境声：{line.split(':',1)[-1].strip() if ':' in line else line}")
        elif "@" in line:
            m = re.match(r"@(\d+)s\s*\|\s*(CV|VO)\s*([^:]*):\s*(.+)", line)
            if m:
                sec, tag, desc, text = m.groups()
                desc = desc.strip().strip("()")
                result.append(f"第{sec}秒——{tag}（{desc}）：{text.strip()}")
            else:
                result.append(line)
    return "\n".join(result) if result else "环境声：咖啡馆底噪（冷藏柜嗡嗡声）"

def convert(source_path, output_path):
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into shots
    shots = re.split(r"\n## Shot ", content)
    header = shots[0]
    shots = ["## Shot " + s for s in shots[1:]]

    out = []
    # Extract scene metadata from header
    scene_name = "EP2 Cafe da Isa"
    m = re.search(r"Scene:\s*(.+?)\s*\|", header)
    if m: scene_name = m.group(1).strip()
    total_dur = "168"
    m = re.search(r"(\d+)s\s*\|\s*\d+\s*shots", header)
    if m: total_dur = m.group(1)
    total_shots = "18"
    m = re.search(r"\|\s*(\d+)\s*shots", header)
    if m: total_shots = m.group(1)

    out.append(f"# {scene_name} — 导演台本\n")
    out.append(f"> **管道：** MODE:P · M-Level · v7.0")
    out.append(f"> **场景：** {scene_name} · {total_dur}秒 · {total_shots}镜")
    out.append(f"> **⚠️ 本文件为Seko可执行提示词——请勿手动修改格式**\n")
    out.append("---\n")

    # Check if SA anchors section exists
    sa_match = re.search(r"## SA.*?Global Anchors.*?\n(.*?)(?=\n## Shot|\n---\n##)", header + shots[0] if shots else header, re.DOTALL)
    if sa_match:
        out.append("## §A 全局锚点\n")
        out.append(sa_match.group(1).strip())
        out.append("\n---\n")

    for shot in shots:
        # Extract shot header
        m = re.match(r"## Shot (#?\d+):\s*(.+?)\s*\|\s*(\d+)s", shot)
        if not m: continue
        shot_id, shot_type, duration = m.groups()

        out.append(f"## 镜{shot_id}：{shot_type} · {duration}秒\n")

        # --- Camera Parameter Card ---
        card_match = re.search(r"### Camera Parameter Card\n(.*?)(?=\n###)", shot, re.DOTALL)
        if card_match:
            lines = card_match.group(1).strip().split("\n")
            out.append("### 【镜头参数卡】\n")
            out.append(convert_param_card(lines))
            out.append("")

        # --- Reference Images ---
        ref_match = re.search(r"### Reference Images?\n(.*?)(?=\n###)", shot, re.DOTALL)
        if ref_match:
            refs = ref_match.group(1).strip()
            out.append("### 【传入参考图】\n")
            out.append(refs)
            out.append("")

        # --- Action Frames ---
        action_match = re.search(r"### Action Frames.*?\n(.*?)(?=\n### Audio)", shot, re.DOTALL)
        if action_match:
            action_text = action_match.group(1).strip()
            out.append("### 【生成指令】\n")
            # Try to preserve second-by-second structure
            frame_lines = re.findall(r"^(\d+s:.*)$", action_text, re.MULTILINE)
            cam_lines = [l for l in action_text.split("\n") if l.startswith("# CAM") or l.startswith("# ZONE") or l.startswith("# LIGHT")]
            if frame_lines:
                for fl in frame_lines:
                    out.append(fl)
            elif cam_lines:
                # Has structured markers, use them as context
                for cl in cam_lines:
                    out.append(cl.replace("# CAM:", "📐").replace("# ZONE:", "📍").replace("# LIGHT:", "💡"))
                # Add the prose text
                prose = re.sub(r"^#.*$", "", action_text, flags=re.MULTILINE).strip()
                if prose:
                    out.append("")
                    out.append(prose)
            else:
                out.append(action_text)
            out.append("")

        # --- Audio ---
        audio_match = re.search(r"### Audio Track\n(.*?)(?=\n###)", shot, re.DOTALL)
        if audio_match:
            audio_lines = audio_match.group(1).strip().split("\n")
            out.append("### 【音轨】\n")
            out.append(convert_audio(audio_lines))
            out.append("")

        # --- Prohibit ---
        prohibit_match = re.search(r"### Prohibit List.*?\n(.*?)(?=\n###)", shot, re.DOTALL)
        if prohibit_match:
            prohibit_lines = prohibit_match.group(1).strip().split("\n")
            out.append("### 【禁止】\n")
            out.append(convert_prohibit(prohibit_lines))
            out.append("")

        # --- Transition ---
        trans_match = re.search(r"### Segment Transition\n(.*?)(?=\n---|\n##|\Z)", shot, re.DOTALL)
        if trans_match:
            trans_text = trans_match.group(1).strip()
            if "BLACK SCREEN" in trans_text.upper() or "END" in trans_text.upper():
                trans_text = "黑屏。全场景结束。"
            elif "HARD CUT" in trans_text.upper():
                trans_text = "硬切。" + trans_text.split(". ", 1)[-1] if ". " in trans_text else "硬切。"
            out.append("### 【段末转场】\n")
            out.append(trans_text)
            out.append("")

        out.append("---\n")

    result = "\n".join(out)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"Converted: {output_path}")
    print(f"  {len(shots)} shots, {len(result)} chars")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    convert(args.source, args.output)
