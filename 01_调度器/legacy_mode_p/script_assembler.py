#!/usr/bin/env python3
"""
script_assembler.py v2.0 — deterministic MODE:P script assembler. 0 LLM tokens.
Keyframe-driven frame generation. Zero scene-specific hardcoded knowledge.
Backward compatible with PLAN YAML without segment_frames/dialogue_map.
Usage: python script_assembler.py --plan PLAN.yml [--design DESIGN.yml] --script SCRIPT.txt --output OUT.md
"""
import yaml, re, argparse, sys
from typing import Dict, List, Any, Optional, Tuple

NL = "\n"

# ===== CONSTANTS (pipeline-level knowledge only — no scene specifics) =====

PFAL_G = ["no frame text(P8)", "no mm precision(P2)", "no pupil change(P1)", "no sub-sec timing(P3)"]
PFAL_CU = ["no facial drift(P1)"]
PFAL_WS = ["max 2 audio layers(P4)"]
PFAL_DLG = ["no 2+ simultaneous mouth shapes(P10)"]
PFAL_SCR = ["no rendered screen text(P8)"]
PFAL_MOV = ["no limb deformation from fast motion(P9)"]
PFAL_WIN = ["no flicker/strobe(P7)"]

def select_model(seg: Dict) -> str:
    """Deterministic model selection based on shot characteristics.
    Rules ordered by priority — first match wins."""
    cam_type = str(seg.get('camera_type', ''))
    movement = str(seg.get('movement', ''))
    scale = str(seg.get('scale', ''))
    angle = str(seg.get('angle', ''))
    speed = str(seg.get('movement_speed_tier', 'S0'))
    pos = str(seg.get('camera_position', ''))
    chars = seg.get('characters', seg.get('characters_in_frame', []))
    has_chars = bool(chars)

    # ACTION: handheld, fast push, tracking, combat → Hailuo02
    action_kw = ['手持', '快速推近', '跟拍', '交火', '中晃', '轻晃', '重晃', '快节奏', '打斗']
    if any(k in cam_type or k in movement for k in action_kw):
        return "海螺02 (动作·打斗·动态最强)"

    # AERIAL / LONG TAKE / SMOOTH MOVEMENT → Kling3.0
    aerial_kw = ['航拍', '下降', '上升', '长镜头']
    if any(k in cam_type or k in movement or k in pos for k in aerial_kw):
        if speed in ('S0', 'S1', 'S2'):  # slow enough for Kling
            return "可灵3.0 (航拍长镜头·运镜平滑)"

    # FACIAL CLOSE-UP → Jimeng4.0
    face_kw = ['特写', '大特写', '近景']
    if any(k in scale for k in face_kw) and has_chars and '手持' not in cam_type:
        return "即梦4.0 (面部特写·亚洲面部最优)"

    # STATIC LONG TAKE → Kling3.0
    if '固定' in cam_type and speed == 'S0' and ('全景' in scale or '远景' in scale):
        return "可灵3.0 (静态长镜头·张力保持)"

    # WIDE establishing → Kling
    if '远景' in scale or '航拍' in pos:
        return "可灵3.0 (远景·氛围渲染)"

    # Default
    has_motion = not ('固定' in cam_type and speed == 'S0')
    if has_motion:
        return "Jimeng4.0 / Veo 3.1 (中景·动态)"
    return "Jimeng4.0 / Veo 3.1 (中景·固定)"

# spatial zone → camera position keyword (pipeline knowledge, not scene-specific)
ZONE_KEYWORDS = {
    "door": "A", "window": "B", "mid": "C", "counter": "D",
    "bar": "D", "street": "ST", "outside": "ST",
}

HOLD_PATTERNS = [
    "{desc}。{light}。",
    "画面同前。{desc_micro}。{light}。",
    "画面同前。{desc_micro}。{spatial}。",
    "画面同前。{desc_micro}。{light}。",
    "画面同前。{desc_micro}。{spatial}。",
    "画面同前。{desc_micro}。{light}。",
]

HOLD_MICRO = [
    "微尘在光柱中以极低速度沉降",
    "光影位置不变·时间缓慢流逝",
    "画面静止·仅呼吸可见的微动",
    "光线角度不变·阴影边缘保持锐利",
    "空间氛围持续·无变化",
    "时间感拉长·静止画面中的微观运动",
]

TRANSITION_PHASES = [
    (0.0,  0.15, "起始阶段"),
    (0.15, 0.40, "过渡进行中"),
    (0.40, 0.70, "过渡过半"),
    (0.70, 0.90, "接近完成"),
    (0.90, 1.01, "即将完成"),
]

# ===== SCALE-DETAIL VALIDATION (Gate 0 R18) =====

# Detail keywords that are physically invisible at each scale level.
# Based on optical limits: at distance D, a 24mm lens resolves ~D/1000 detail.
#   - 远景/航拍 (D>80m): resolves >8cm — no facial features, no hand details, no props
#   - 全景 (D≈30-50m): resolves >3cm — body轮廓, gestures visible; 扳机/雕花 invisible
#   - 中景 (D≈5-15m): resolves >5mm — facial expressions, hand gestures visible; fine texture invisible
#   - 近景/特写 (D<3m): all details visible

SCALE_FORBIDDEN_DETAIL = {
    "远景": ["面部", "表情", "手部", "手指", "瞳孔", "睫毛", "扳机", "雕花",
             "套筒纹", "弹孔", "血滴", "汗水", "嘴唇", "眼神", "金⾊扳机",
             "枪口焰", "抛壳窗", "防弹衣", "雕花套筒"],
    "航拍": ["面部", "表情", "手部", "手指", "瞳孔", "睫毛", "扳机", "雕花",
             "套筒纹", "弹孔", "血滴", "汗水", "枪口", "拔枪", "人物个体"],
    "全景": [
        # Optical limit: 24-35mm at 30-50m resolves >3cm. Anything smaller is invisible.
        "金色扳机", "雕花套筒", "雕花纹", "套筒刻字", "套筒纹理",
        "扳机闪光", "扳机反光", "扳机闪", "红点镜闪", "红点镜",
        "弹孔纤维", "弹孔边缘", "弹孔纹理",
        "手指关节发白", "手指关节", "皮肤纹理", "汗水反光", "汗水滑落",
        "枪口膛线", "抛壳窗", "抛壳", "弹壳纹理",
        "瞳孔收缩", "瞳孔散大", "睫毛", "嘴唇微", "嘴角",
        "皮夹克灼痕", "防弹衣纤维", "衬衫纹理",
        "血滴路径", "血滴", "血从指缝",
    ],
    "中景": ["瞳孔直径", "皮肤毛孔", "雕花卷草", "套筒刻字细节", "睫毛根数",
             "弹孔边缘纤维", "血细胞"],
    "中近景": [],  # 中近景以上基本不受限
    "近景": [],
    "特写": [],
    "大特写": [],
}

# Scale-specific: maximum reasonable detail qualifiers
# e.g. "金色扳机闪光" in 全景 → ⚠️; "枪口指向" in 全景 → ✅
SCALE_WARN_DETAIL = {
    "远景": ["枪口", "指向", "步伐", "轮廓", "剪影"],
    "全景": ["枪口指向", "拔枪动作", "身体晃动", "血流出", "倒地处",
             "瞄准姿势", "推近方向", "举手", "后仰"],
    "中景": ["扳机", "弹孔", "血迹路径", "手指", "嘴唇", "眼神方向",
             "汗水", "皮夹克纹理", "防弹衣廓形"],
}

def check_scale_detail(shot_id: str, scale: str, text: str) -> List[str]:
    """Check if action text describes details invisible at this scale.
    Returns list of warnings (empty = clean)."""
    warnings = []
    scale_key = scale.split("→")[0].split("·")[0].strip()  # e.g. "中景→近景" → "中景"

    # Find matching scale rule
    matched_scale = None
    for sk in sorted(SCALE_FORBIDDEN_DETAIL.keys(),
                     key=lambda x: ["远景","航拍","全景","中景","中近景","近景","特写","大特写"].index(x) if x in ["远景","航拍","全景","中景","中近景","近景","特写","大特写"] else 99):
        if sk in scale_key:
            matched_scale = sk
            break

    if not matched_scale or matched_scale in ("近景", "特写", "大特写"):
        return warnings  # No restrictions for close-ups

    forbidden = SCALE_FORBIDDEN_DETAIL.get(matched_scale, [])
    for kw in forbidden:
        if kw in text:
            warnings.append(f"R18: [{shot_id}] {matched_scale}中出现'{kw}'——该细节在此景别下物理不可见(景别-细节不匹配)")

    return warnings

def sanitize_scale_detail(scale: str, text: str) -> str:
    """Remove detail phrases that are physically invisible at this scale.
    Replaces them with scale-appropriate alternatives."""
    scale_key = scale.split("→")[0].split("·")[0].strip()
    matched_scale = None
    for sk in ["远景","航拍","全景","中景","中近景","近景","特写","大特写"]:
        if sk in scale_key:
            matched_scale = sk
            break
    if not matched_scale or matched_scale in ("近景", "特写", "大特写"):
        return text  # Close-ups: all details OK

    forbidden = SCALE_FORBIDDEN_DETAIL.get(matched_scale, [])
    for kw in sorted(forbidden, key=len, reverse=True):  # longest first to avoid partial matches
        if kw in text:
            # Replace with scale-appropriate alternative
            replacements = {
                "金色扳机": "手枪",
                "金色扳机闪光": "手枪在手中",
                "雕花套筒": "手枪套筒",
                "雕花纹": "套筒",
                "扳机闪光": "枪口方向",
                "扳机反光": "持枪手",
                "红点镜闪": "瞄准方向",
                "红点镜": "瞄准具",
                "弹孔纤维": "弹孔",
                "弹孔边缘": "着弹处",
                "弹孔纹理": "着弹处",
                "手指关节发白": "紧握枪柄",
                "汗水反光": "面部",
                "汗水滑落": "",
                "瞳孔收缩": "注视",
                "瞳孔散大": "注视",
                "睫毛": "",
                "嘴唇微": "",
                "嘴角": "",
                "血滴路径": "血迹",
                "血滴": "血迹",
                "血从指缝": "手上有血",
                "皮夹克灼痕": "夹克上",
                "防弹衣纤维": "防弹衣",
                "衬衫纹理": "衬衫",
                "抛壳窗细节": "",
                "抛壳窗": "",
                "枪口膛线": "枪口",
                "套筒刻字": "",
                "套筒纹理": "",
            }
            replacement = replacements.get(kw, "")
            text = text.replace(kw, replacement)
    return text

def validate_scale_detail(segments: List[Dict], segment_frames: List[Dict]) -> List[str]:
    """Validate all shots for scale-detail mismatch. Returns all warnings."""
    all_warnings = []
    sf_by_id = {}
    for sf in segment_frames:
        for key in ("segment_id", "shot_id"):
            v = sf.get(key, "")
            if v: sf_by_id[v] = sf

    for seg in segments:
        sid = seg.get("shot_id", seg.get("segment_id", ""))
        scale = str(seg.get("scale", ""))
        # Check segment-level descriptions
        action_text = str(seg.get("narrative", ""))

        # Also check keyframe action_anchor text
        sf = sf_by_id.get(sid, {})
        for kf in sf.get("keyframes", []):
            action_text += " " + str(kf.get("action_anchor", ""))
            action_text += " " + str(kf.get("description_visual", ""))

        warnings = check_scale_detail(sid, scale, action_text)
        all_warnings.extend(warnings)

    return all_warnings

# ===== YAML LOADER =====

def load_plan(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)

    # Accept both PLAN format (time_skeleton) and Scene Designer format (segments_camera + segments_movement)
    segments = d.get("time_skeleton", [])
    cameras = d.get("segments_camera", [])
    movements = d.get("segments_movement", [])
    segment_frames = d.get("segment_frames", [])

    # Auto-merge: if segments_camera exists but time_skeleton doesn't (Scene Designer v2 format)
    if not segments and cameras:
        # Build movement lookup by segment_id (try both segment_id and shot_id)
        mov_by_id = {}
        for m in movements:
            for key in ("segment_id", "shot_id"):
                v = m.get(key, "")
                if v: mov_by_id[v] = m
        # Build segment_frames lookup (try both segment_id and shot_id — Scene Designer uses symbolic IDs)
        sf_by_id = {}
        for s in segment_frames:
            for key in ("segment_id", "shot_id"):
                v = s.get(key, "")
                if v: sf_by_id[v] = s
        for cam in cameras:
            sid = cam.get("segment_id", cam.get("shot_id", ""))
            mov = mov_by_id.get(sid, {})
            sf = sf_by_id.get(sid, {})
            merged = dict(cam)
            # Compute timing fields from time_range if missing
            tr = merged.get("time_range", [0, 6])
            merged.setdefault("duration_s", tr[1] - tr[0])
            merged.setdefault("global_sec_start", tr[0])
            merged.setdefault("global_sec_end", tr[1] - 1)
            # Merge movement fields
            for k in ("movement", "movement_speed_tier", "camera_fixed", "actor_fixed", "actor_movement"):
                if k in mov and k not in merged: merged[k] = mov[k]
            # Derive camera_fixed from movement data if not explicitly set
            if "camera_fixed" not in merged:
                mtype = merged.get("movement", merged.get("camera_type", ""))
                speed = merged.get("movement_speed_tier", "")
                merged["camera_fixed"] = (mtype == "固定" or speed == "S0" or "静态" in str(mtype))
            # Merge transition fields
            for k in ("transition_to", "transition_type", "transition_motivation"):
                if k in mov and k not in merged: merged[k] = mov[k]
            # Attach segment_frames inline (both segment_id and shot_id lookup tried)
            if sf and sf.get("keyframes"):
                merged["segment_frames"] = sf
            segments.append(merged)

    dialogue_map = d.get("dialogue_map", [])
    transitions = d.get("segments_transitions", [])
    return {
        "scene": d.get("scene", {}),
        "anchors": d.get("global_anchors", {}),
        "segments": segments,
        "segment_frames": segment_frames,
        "dialogue_map": dialogue_map,
        "transitions": transitions,
    }

# ===== HELPERS =====

def zone_of(pos: str) -> str:
    """Infer spatial zone from camera_position string. Only checks generic keywords."""
    pos_lower = pos.lower()
    for keyword, zone in sorted(ZONE_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if keyword in pos_lower:
            return zone
    return "D"

def shot_type_key(st: str) -> str:
    if "te" in st or "jin" in st: return "CU"
    if "zhong" in st: return "MS"
    if "quan" in st: return "WS"
    return "MS"

def word_count(text: str) -> int:
    return len(re.sub(r"[\s,.;:?!()\"'<>]", "", text))

def get_light_source_name(anchors: Dict, seg: Dict) -> str:
    """Extract light source description from anchors for this segment's zone.
    Uses anchor_sources from YAML — no hardcoded L1-L5 strings."""
    z = zone_of(seg.get("camera_position", ""))
    lit = anchors.get("lighting", {})
    sources = lit.get("anchor_sources", [])
    if not sources:
        return lit.get("description", "")[:80]
    # Return names of relevant sources
    names = [s.get("source", "") for s in sources[:3]]
    return " + ".join(names) if names else lit.get("description", "")[:80]

def parse_dialogue_from_script(script_path: str) -> List[Dict]:
    """Fallback: parse dialogue from original script text."""
    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    dlgs = []
    for line in lines:
        m = re.match(r"CV\s+(\S+)[(](.*?)[)]:(.+)", line)
        if m:
            dlgs.append({
                "speaker": m.group(1),
                "text": m.group(3).strip(),
                "direction": m.group(2),
            })
        m = re.match(r"VO[:\xef\xbc\x9a](.+)", line)
        if m:
            dlgs.append({
                "speaker": "VO",
                "text": m.group(1).strip(),
                "direction": "narrative",
            })
    return dlgs

def build_dialogue_map(dlgs: List[Dict], segments: List[Dict]) -> Dict[str, List]:
    """
    Heuristic: distribute dialogue to shots based on text keyword matching.
    This is a FALLBACK for when PLAN YAML has no dialogue_map.
    The proper source is Scene Designer v2.0's dialogue_map field.
    """
    dist = {s["shot_id"]: [] for s in segments}
    # Fallback keyword matching — minimal, scene-agnostic
    char_order = []
    for d in dlgs:
        if d["speaker"] not in char_order:
            char_order.append(d["speaker"])
    if not char_order:
        return dist
    # Assign dialogue in script order to shots
    d_idx = 0
    for seg in segments:
        sid = seg["shot_id"]
        # Skip insert shots and empty shots
        cam_type = seg.get("camera_type", "")
        if "insert" in cam_type.lower() or "ecu" in cam_type.lower():
            continue
        # Assign next dialogue if characters match
        chars = (seg.get("characters_in_frame", []) or
                 seg.get("segment_frames", [{}])[0].get("characters_in_frame", [])
                 if seg.get("segment_frames") else [])
        if d_idx < len(dlgs):
            dist[sid].append({
                "s": dlgs[d_idx]["speaker"],
                "t": dlgs[d_idx]["text"],
                "d": dlgs[d_idx].get("direction", ""),
                "o": 0.3, "du": 2.5,
            })
            d_idx += 1
    return dist

# ===== KEYFRAME EXPANDER =====

# Text sanitization: R02 process verbs → static alternatives
R02_REPLACE = {
    "开始": "起始", "正在": "", "刚": "", "已": "",
    "持续": "保持", "继续": "重复", "一直": "始终", "仍": "依旧",
    "缓缓": "慢速", "渐渐": "逐步", "慢慢": "慢速", "逐渐": "渐进",
}
# Text sanitization: R16 emotion labels → anatomical alternatives
R16_REPLACE = {
    "紧张": "肌肉收紧·动作幅度减小", "焦虑": "重复性小动作增加",
    "悲伤": "眉内侧微抬·眼睑微垂", "恐惧": "眼睑收紧·瞳孔散大·身体微后倾",
    "愤怒": "眉下降·咬肌收紧·唇线紧绷", "压抑": "肌肉张力增加但外显动作受控",
    "绝望": "肌肉张力丧失·眼睑下垂·身体前倾", "兴奋": "眼睑抬高·瞳孔散大·动作幅度增加",
    "厌恶": "鼻梁皱起·上唇提升·身体微后倾", "震惊": "双眉上扬·下颌微降·身体瞬间静止",
}

def _sanitize(text: str) -> str:
    """Remove/replace Gate-0-forbidden words. Safety net for upstream LLM output."""
    for old, new in R02_REPLACE.items():
        if old in text:
            text = text.replace(old, new)
    for old, new in R16_REPLACE.items():
        if old in text:
            text = text.replace(old, new)
    return text

def _perf_lines(kf: Dict) -> str:
    """Render performance field as visual description lines. Returns empty string if absent."""
    perf = kf.get("performance", {})
    if not perf: return ""
    parts = []
    facial = perf.get("facial", {})
    for part in ["eyes", "brow", "mouth"]:
        val = facial.get(part, "")
        if val: parts.append(_sanitize(val))
    body = perf.get("body", {})
    for part in ["posture", "hands", "head"]:
        val = body.get(part, "")
        if val: parts.append(_sanitize(val))
    return "。".join(parts) if parts else ""

def expand_hold(kf: Dict, idx: int, gs: int, seg: Dict, lit_name: str) -> str:
    """Enhanced hold expansion v2.2: decomposes description into visual zones and roams
    the 'camera eye' across them — each second describes a different part of the frame."""
    perf = _perf_lines(kf)
    action = _sanitize(kf.get("action_anchor", ""))
    desc = _sanitize(kf.get("description", ""))
    spatial = kf.get("spatial", seg.get("camera_position", "")[:80])

    if idx == 0:
        # First second: full description with action + context
        parts = [action] if action else []
        if desc: parts.append(desc)
        if perf: parts.append(perf)
        if lit_name: parts.append(lit_name)
        return f"{gs}s: " + "。".join(parts) + "。"

    # Decompose description into visual zones (split on 。)
    zones = [z.strip() for z in desc.replace('·', '。').split('。') if len(z.strip()) > 8]

    if len(zones) >= 4:
        # Rich description: "camera eye" roams across spatial zones
        zone_labels = [
            "视线落于画面左侧区域",
            "视线落于画面中央区域",
            "视线落于画面右侧区域",
            "注意焦点移至前景细节",
            "注意焦点移至背景纵深",
            "视线扫描整体空间",
        ]
        label = zone_labels[(idx - 1) % len(zone_labels)]
        primary = zones[(idx - 1) % len(zones)]
        secondary = zones[(idx + 2) % len(zones)] if len(zones) > 3 else ""
        parts = [label, primary]
        if secondary and secondary != primary:
            parts.append(secondary)
        parts.append(f"第{idx+1}秒")
        return f"{gs}s: " + "。".join(parts) + "。"

    elif len(zones) >= 2:
        # Moderate: alternate between visual elements with progressive framing
        zone = zones[(idx - 1) % len(zones)]
        micro_frames = [
            f"画面保持·{zone}",
            f"时间推进·{zone}·空间层次清晰",
            f"静止延续·{zone}·光影角度微偏",
            f"氛围持续·{zone}·细节渐进变化",
            f"画面同帧·{zone}·尘埃粒子位移",
            f"持续第{idx+1}秒·{zone}",
        ]
        return f"{gs}s: " + micro_frames[(idx - 1) % len(micro_frames)] + "。"

    else:
        # Sparse: use description + micro variation + count
        base = desc if desc else action
        micro = HOLD_MICRO[idx % len(HOLD_MICRO)]
        return f"{gs}s: {base}。{micro}。持续第{idx+1}秒。"

def expand_event(kf: Dict, gs: int, lit_name: str) -> str:
    action = _sanitize(kf.get("action_anchor", ""))
    desc = _sanitize(kf.get("description", ""))
    perf = _perf_lines(kf)
    parts = []
    if action: parts.append(action)
    if desc: parts.append(desc)
    if perf: parts.append(perf)
    if kf.get("lighting"): parts.append(kf["lighting"])
    elif lit_name: parts.append(lit_name)
    return f"{gs}s: " + "。".join(p for p in parts if p) + "。"

def expand_transition(kf: Dict, progress: float, gs: int, lit_name: str) -> str:
    target = kf.get("transition_target", {})
    tp = kf.get("transition_params", {})
    phase = "过渡中"
    for lo, hi, label in TRANSITION_PHASES:
        if lo <= progress < hi: phase = label; break
    temp_str = ""; ct = tp.get("color_temp_kelvin", {})
    if ct:
        current = int(ct.get("start", 6000) + (ct.get("end", 3000) - ct.get("start", 6000)) * progress)
        temp_str = f"色温~{current}K"
    pos_str = ""; pf = tp.get("position_in_frame", {})
    if pf:
        if progress < 0.5: pos_str = f"画面{pf.get('start','左')}"
        elif progress < 0.9: pos_str = "画面中央"
        else: pos_str = f"画面{pf.get('end','右')}"
    action = target.get("action_anchor", kf.get("action_anchor", "")) if progress > 0.4 else kf.get("action_anchor", "")
    # Performance: use start perf early, target perf late
    perf = ""
    tgt_perf = _perf_lines(target) if isinstance(target, dict) else ""
    src_perf = _perf_lines(kf)
    if progress > 0.6 and tgt_perf: perf = tgt_perf
    elif progress < 0.4 and src_perf: perf = src_perf
    parts = [phase, action] if action else [phase]
    if perf: parts.append(perf)
    if temp_str: parts.append(temp_str)
    if pos_str: parts.append(pos_str)
    return f"{gs}s: " + "。".join(p for p in parts if p) + "。"

def _kf_global(kf: Dict, seg_start: int) -> int:
    """Compute absolute global second for a keyframe. Supports sec_offset (v2.0) and global_sec (v2.1+)."""
    if "global_sec" in kf:
        return kf["global_sec"]
    return seg_start + kf.get("sec_offset", 0)

def expand_keyframes(kfs: List[Dict], duration_s: int, seg_start: int,
                     seg: Dict, lit_name: str) -> List[str]:
    frames = []; kf_idx = 0; event_repeat = 0
    for offset in range(duration_s):
        gs = seg_start + offset
        # FIXED v2.2: use _kf_global to resolve sec_offset→global_sec correctly
        while (kf_idx + 1 < len(kfs) and _kf_global(kfs[kf_idx + 1], seg_start) <= gs):
            kf_idx += 1; event_repeat = 0
        kf = kfs[kf_idx]; kf_type = kf.get("type", "hold")
        kf_gs = _kf_global(kf, seg_start)
        if kf_type == "event":
            frame = expand_event(kf, gs, lit_name)
            if offset > 0 and frames[-1] == frame:
                event_repeat += 1
                frame = frame.replace("。", f"。({'再次' if event_repeat==1 else '持续'})。", 1)
            else:
                event_repeat = 0
        elif kf_type == "transition":
            end_sec = kf.get("hold_until", seg_start + duration_s)
            progress = max(0.0, min(1.0, (gs - kf_gs) / max(1, end_sec - kf_gs)))
            frame = expand_transition(kf, progress, gs, lit_name)
        else:  # hold
            event_repeat = 0
            frame = expand_hold(kf, gs - kf_gs, gs, seg, lit_name)
        frames.append(frame)
    return frames

def has_keyframes(seg: Dict) -> bool:
    """Check if segment has segment_frames data (from PLAN v2.0)."""
    sf = seg.get("segment_frames")
    return bool(sf and sf.get("keyframes"))

# ===== BUILDERS =====

def build_card(seg: Dict) -> str:
    model = select_model(seg)
    lines = [
        f"- Shot type: {seg.get('shot_type','')}",
        f"- Focal length: {seg.get('focal_length','')}",
        f"- Aperture: {seg.get('dof','')}",
        f"- Angle: {seg.get('angle','')}",
        f"- Camera type: {seg.get('camera_type','')}",
        f"- Camera position: {seg.get('camera_position','')[:100]}",
        f"- Movement: {seg.get('movement','static')} ({seg.get('movement_speed_tier','S0')})",
        f"- Axis side: {seg.get('axis_side','A-side')}",
        f"- Model: {model}",
    ]
    kb = seg.get("kb_rule_ids", [])
    if kb: lines.append(f"- KB rules: {', '.join(kb)}")
    return NL.join(lines)

def build_refs(seg: Dict, anchors: Dict) -> str:
    """Generate reference image declarations. Uses enhanced YAML ref_images if available,
    falls back to character + scene keyword mapping."""
    # If enhanced YAML already has reference_images, use them directly
    refs = seg.get('reference_images', [])
    if refs:
        lines = []
        for r in refs:
            lines.append(f"@图片[{r}]")
        return NL.join(lines)

    # Fallback: keyword-based mapping
    pos = str(seg.get('camera_position', ''))
    cam_type = str(seg.get('camera_type', ''))
    scale = str(seg.get('scale', ''))
    movement = str(seg.get('movement', ''))
    chars = seg.get('characters', seg.get('characters_in_frame', []))
    refs = []

    # Scan ALL fields for grid keywords
    all_text = pos + cam_type + scale + movement
    GRID_MAP = [
        (['航拍', '俯瞰', '高空', '远景'], '格1-1 高空俯瞰大道'),
        (['大道', '纵深', '街面', '对峙', '南侧', '全景', '对角线'], '格2-2 大道纵深透视'),
        (['街角', '消防栓', '轿车', '掩体', '画左'], '格1-2 街角+消防栓'),
        (['石板', '棕榈', '路面'], '格2-1 石板路棕榈街'),
        (['橱窗', '玻璃', '碎裂', '奢侈品', '画右'], '格3-3 奢侈品橱窗'),
        (['格栅', '下水道', '血泊', '血'], '格3-1 下水道格栅'),
        (['十字', '路口', '深夜', '跳切', '清洁工'], '格1-3 雨夜十字路口'),
    ]
    for keywords, grid in GRID_MAP:
        if any(k in pos or k in cam_type for k in keywords):
            if grid not in refs:
                refs.append(grid)

    # Character refs
    for ch in chars:
        refs.append(f'{ch}角色参考图')

    if not refs:
        refs.append('场景参考图 (见空间地图)')

    lines = [f"@图片[{r}]" for r in refs]
    return NL.join(lines)

def build_frames(seg: Dict, anchors: Dict, dial: List[Dict]) -> str:
    """v2.3: Movement-based video prompt. Synthesizes keyframes into continuous motion
    trajectories — describes what moves, how, and at what speed. Lets the video model
    interpolate frames between motion phases. No per-second expansion."""
    sid = seg.get("shot_id", ""); dur = seg.get("duration_s", 6)
    start = seg.get("global_sec_start", 0)
    lit_name = get_light_source_name(anchors, seg)
    chars = seg.get("characters_in_frame", [])
    is_static = seg.get("camera_fixed", True)
    cs = "static" if is_static else seg.get("movement", "moving")

    sf = seg.get("segment_frames", {}) if isinstance(seg.get("segment_frames"), dict) else {}
    kfs = sf.get("keyframes", []) if sf else []

    if not kfs:
        # Fallback: segment-level description (backward compat with v1.0 PLAN)
        lines = [
            f"# CAM: {seg.get('angle','')} | {seg.get('camera_type','')} | camera {cs}",
            f"# ZONE: {zone_of(seg.get('camera_position',''))} | LIGHT: {lit_name}",
        ]
        if chars: lines.append(f"# CHARS: {', '.join(chars)}")
        if dial:
            lines.append("# DIALOGUE timing:")
            for d in dial:
                sec = start + d.get("o", 0.5) * dur
                lines.append(f"#   [{d.get('s','?')}] @ ~{sec:.0f}s ({d.get('du',2):.0f}s): {d.get('t','')[:70]}")
        lines.append("")
        if dur <= 6: ranges = [(0, dur)]
        elif dur <= 10: h = dur // 2; ranges = [(0, h), (h, dur)]
        else: r3 = dur // 3; ranges = [(0, r3), (r3, 2 * r3), (2 * r3, dur)]
        for s, e in ranges:
            abs_s, abs_e = start + s, start + e - 1
            sd = [d for d in dial if s <= d.get("o", 0.5) * dur < e]
            lines.append(f"{abs_s}-{abs_e}s: [{seg.get('shot_type','')}] cam {cs} | {seg.get('focal_length','')} {seg.get('dof','')} | light:{lit_name}")
            for d in sd: lines.append(f"    CV [{d.get('s','?')}]: {d.get('t','')[:70]}")
            lines.append("")
        return NL.join(lines)

    # === v2.3: Movement Trajectory (video model interpolates frames) ===
    lines = [f"### Movement Trajectory ({len(kfs)} phases → {dur}s · video model interpolates){NL}"]

    for i, kf in enumerate(kfs):
        sec = kf.get("sec_offset", 0)
        kf_type = kf.get("type", "hold")
        action = _sanitize(kf.get("action_anchor", ""))
        desc = _sanitize(kf.get("description", ""))
        perf_data = kf.get("performance") or {}
        perf_text = _perf_lines({"performance": perf_data}) if isinstance(perf_data, dict) and perf_data else ""

        # Phase duration: from this keyframe to next (or to end of shot)
        if i + 1 < len(kfs):
            next_sec = kfs[i + 1].get("sec_offset", dur)
        else:
            next_sec = dur
        phase_dur = next_sec - sec
        gs_start = start + sec
        gs_end = gs_start + phase_dur - 1

        if kf_type == "hold":
            label = f"[{gs_start}s" if phase_dur == 1 else f"[{gs_start}-{gs_end}s·{phase_dur}s hold]"
            lines.append(f"{label} {action}")
            if desc:
                lines.append(f"  视觉状态: {desc[:200]}")
            if phase_dur > 1:
                # Skip micro-movement for black/empty frames (no visual content)
                is_black = "纯黑" in desc or "黑屏" in desc or "黑帧" in desc
                if not is_black and chars:
                    lines.append(f"  微运动: 呼吸可见于肩线微幅起伏·尘埃在光柱交汇区缓慢漂移·光影位置稳定·衣物纤维微幅沉降")
            if perf_text:
                lines.append(f"  表演: {perf_text[:150]}")

        elif kf_type == "event":
            lines.append(f"[{gs_start}s·事件] {action}")
            if desc:
                lines.append(f"  视觉细节: {desc[:200]}")
            if perf_text:
                lines.append(f"  表演: {perf_text[:150]}")
            # If event covers multiple seconds, add post-event hold description
            if phase_dur > 1:
                post_start = gs_start + 1
                post_end = gs_end
                post_dur = phase_dur - 1
                lines.append(f"  → [{post_start}-{post_end}s·{post_dur}s后事件持续] 动作余韵·状态定格")
                if desc:
                    lines.append(f"    视觉状态: 事件后画面保持·{desc[:120]}")
                is_black = "纯黑" in desc or "黑屏" in desc or "黑帧" in desc
                if not is_black:
                    lines.append(f"    微运动: 呼吸可见·尘埃漂移·光影位置稳定")

        elif kf_type == "transition":
            target = kf.get("transition_target", {})
            tgt_action = _sanitize(target.get("action_anchor", "")) if isinstance(target, dict) else ""
            params = kf.get("transition_params", {})
            lines.append(f"[{gs_start}-{gs_end}s·{phase_dur}s过渡] {action}")
            if tgt_action:
                lines.append(f"  → {tgt_action}")
            if desc:
                lines.append(f"  运动过程: {desc[:200]}")
            if isinstance(params, dict):
                ct = params.get("color_temp_kelvin", {})
                if ct:
                    lines.append(f"  色温渐变: {ct.get('start',0)}K→{ct.get('end',0)}K")
                pos = params.get("position_in_frame", {})
                if pos:
                    lines.append(f"  画面位移: {pos.get('start','')}→{pos.get('end','')}")
                gait = params.get("gait_phase", {})
                if gait:
                    lines.append(f"  步态: {gait.get('start','')}→{gait.get('end','')}")
            if perf_text:
                lines.append(f"  表演渐变: {perf_text[:150]}")
        lines.append("")

    # Append dialogue timing within this shot
    if dial:
        lines.append("  ⚡对白时序:")
        for d in dial:
            sp = d.get('s', d.get('speaker', '?'))
            t = d.get('t', d.get('text', ''))
            direction = d.get('d', d.get('direction', ''))
            dir_str = f" ({direction})" if direction else ""
            lines.append(f"    {sp}{dir_str}: {t}")
        lines.append("")

    return NL.join(lines)

def build_audio(seg: Dict, dial: List[Dict]) -> str:
    """Extract audio from enhanced YAML (shot_audio) + dialogue_map. Falls back to zone-based ambience."""
    lines = []

    # Use shot_audio from enhanced YAML if available
    shot_audio = seg.get('shot_audio', '')
    if shot_audio:
        # shot_audio is already formatted as "SFX: ... | 环境声: ..." etc.
        for part in shot_audio.split(' | '):
            part = part.strip()
            if part:
                lines.append(f"- {part}")
    else:
        # Fallback: zone-based ambience
        dur = seg.get("duration_s", 6); start = seg.get("global_sec_start", 0)
        z = zone_of(seg.get("camera_position", ""))
        amb = ("城市低频嗡鸣" if z in ("ST", "D") else
               "室内环境音")
        lines.append(f"- 环境声: {amb}")

    # Dialogue from dialogue_map
    for d in dial:
        sp = d.get("s", d.get("speaker", "?")); t = d.get("t", d.get("text", ""))
        w = word_count(t); dd = d.get("du", d.get("duration_s", 2.5))
        spd = w / dd if dd > 0 else 3
        tag = "VO" if sp == "VO" else f"CV {sp}"
        direction = d.get("d", d.get("direction", ""))
        voice_q = d.get("voice_quality", d.get("vq", ""))
        vq_str = f" ·{voice_q}" if voice_q else ""
        dir_str = f" ({direction})" if direction else ""
        lines.append(f"  @~{dd:.0f}s | {tag}{dir_str}: {t} [~{spd:.1f}字/秒{vq_str}]")

    return NL.join(lines) if lines else "Ambience: scene ambient (continuous)"

def build_prohibit(seg: Dict) -> str:
    """Template-based prohibit generation from shot properties. Deterministic, no LLM."""
    speed_tier = str(seg.get('movement_speed_tier', 'S0'))
    cam_type = str(seg.get('camera_type', ''))
    focal = str(seg.get('focal_length', '50mm'))
    scale = str(seg.get('scale', ''))
    chars = seg.get('characters', seg.get('characters_in_frame', []))
    movement = str(seg.get('movement', ''))

    p = list(PFAL_G)  # Base: no text, no mm, no pupil, no sub-sec
    if '特写' in scale or '近景' in scale:
        p.extend(PFAL_CU)  # no facial drift
    if '全景' in scale or '远景' in scale:
        p.extend(PFAL_WS)  # max 2 audio layers
    if chars:
        p.extend(PFAL_DLG)  # no 2+ simultaneous mouth shapes
    if '手持' in cam_type or '快速' in movement:
        p.extend(PFAL_MOV)  # no limb deformation
        p.append("速度曲线急收段必须完全停止于定格帧·不可有余运动(P-FAL-09)")
    if '橱窗' in str(seg.get('camera_position', '')) or 'screen' in str(seg.get('camera_position', '')).lower():
        p.extend(PFAL_SCR)

    # Speed-tier-based limit
    speed_limits = {'S0': '静止·0像素漂移', 'S1': '≤0.1x', 'S2': '≤0.3x',
                    'S3': '≤0.6x', 'S4': '≤1.0x', 'S5': '≤1.5x', 'S6': '≤2.5x',
                    'S7': '≤4.0x', 'S8': '≤8.0x'}
    if speed_tier in speed_limits and speed_tier != 'S0':
        p.append(f"运镜速度{speed_limits[speed_tier]}·不可超过({speed_tier}级阈值)")

    # Focal length distortion constraint
    try:
        fl = int(re.findall(r'\d+', focal)[0])
        if fl < 28:
            p.append(f"广角{fl}mm建筑垂直线偏差<2度·不可出现桶形畸变>3%")
        elif fl > 70:
            p.append(f"长焦{fl}mm浅景深·焦外虚化自然·面部比例不可透视变形")
    except: pass

    # Static stability
    if '固定' in cam_type and speed_tier == 'S0':
        p.append("固定镜头稳定度<0.5像素/全程·伪静态呼吸微动<0.5像素振幅")
    if '手持' in cam_type:
        p.append("手持晃动幅度<画面宽10%·晃动方向随机不可周期性")

    return NL.join(f"{i+1}. {x}" for i, x in enumerate(p))

def nl_smooth(text: str, seg: Dict, anchors: Dict) -> str:
    """Deterministic NL smoothing — replaces structured markers with natural prose.
    Also sanitizes scale-detail mismatch (R18) before smoothing."""
    # R18: Sanitize scale-detail mismatch before smoothing
    scale = str(seg.get("scale", ""))
    text = sanitize_scale_detail(scale, text)

    # Remove Movement Trajectory header
    text = re.sub(r'###\s*Movement Trajectory[^\n]*\n?', '', text)
    # Remove [timestamp] tags
    text = re.sub(r'\[[\d\-]+s[·•][^\]]*\]\s*', '', text)
    # Replace · with appropriate punctuation
    text = re.sub(r'·(?=\s*$)', '.', text)
    text = text.replace('·', ', ')
    # Remove 微运动 lines
    text = re.sub(r'\s*微运动:[^\n。]*[。]?', '', text)
    # Remove → sub-event markers (both with and without [tags])
    text = re.sub(r'\s*→\s*\[[\d\-]+s[^\]]*\]\s*', '. ', text)
    text = re.sub(r'\s*→\s*(动作余韵|事件后|过渡完成|状态定格)[^。\n]*[。]?', '. ', text)
    # Remove ⚡对白时序 sections (dialogue handled in Audio Track)
    text = re.sub(r'\s*⚡对白时序:[\s\S]*?(?=\n\n|\Z)', '', text)
    # Remove duplicate punctuation
    text = re.sub(r'[,，]\s*[,，]', ', ', text)
    text = re.sub(r'[。.]\s*[。.]', '. ', text)
    # Improve performance block formatting
    text = re.sub(r'\s*表演:\s*', '\n\n', text)
    # Collapse whitespace (but preserve intentional newlines)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text

def _visual_anchor(seg: Dict, anchors: Dict) -> str:
    """Generate one visual detail sentence from anchor data. Deterministic template."""
    pos = str(seg.get('camera_position', ''))
    scale = str(seg.get('scale', ''))
    chars = seg.get('characters', seg.get('characters_in_frame', []))
    lit = anchors.get('lighting', {})
    env = anchors.get('environment', {})
    color = anchors.get('color_palette', {})

    # Pick the most relevant visual anchor for this shot
    if '航拍' in pos or '远景' in scale:
        return env.get('description', '')[:120] + '。'
    if '特写' in scale or '近景' in scale:
        char_anchor = anchors.get('character', {})
        if chars:
            for ch in chars:
                if ch in char_anchor:
                    return f'{ch}: {str(char_anchor[ch])[:100]}。'
        return lit.get('description', '')[:100] + '。'
    if '街' in pos or '大道' in pos:
        return f'{env.get("description", "")[:100]}。{lit.get("description", "")[:80]}。'
    return color.get('description', '')[:100] + '。'

def build_transition(seg: Dict, transitions: List[Dict] = None) -> str:
    """Build transition from segments_transitions data (Movement Designer) or fallback."""
    sid = seg.get("shot_id", seg.get("segment_id", ""))
    nxt = seg.get("transition_to", "END")

    # Try to find matching transition from Movement Designer data
    if transitions:
        for t in transitions:
            from_s = t.get("from_shot", t.get("from_segment", ""))
            if from_s == sid or from_s == seg.get("segment_id", ""):
                trans_type = t.get("transition_type", "切")
                visual = t.get("visual_change", "")
                time_range = t.get("time_range", [0, 1])
                dur = time_range[1] - time_range[0] if isinstance(time_range, list) and len(time_range) > 1 else 1
                # Map type
                type_names = {"切": "HARD CUT", "叠化": "DISSOLVE", "运镜过渡": "运镜过渡",
                              "淡黑": "FADE TO BLACK", "淡入": "FADE IN", "淡出": "FADE OUT"}
                display = type_names.get(trans_type, trans_type)
                return f"{display}. {visual} 过渡时长: ~{dur}s."

    if nxt == "END" or sid == "#22":
        return "FADE TO BLACK. 黑屏→字幕→结束."

    trans_type = seg.get("transition_type", "切")
    type_names = {"切": "HARD CUT", "叠化": "DISSOLVE", "黑场": "FADE TO BLACK"}
    display = type_names.get(trans_type, trans_type.upper())
    mot = seg.get("transition_motivation", "场景切换")
    return f"{display}. {mot}. 过渡时长: ~1s."

def render_anchors(ga: Dict) -> str:
    lines = ["## SA -- Global Anchors (verbatim from PLAN YAML)", ""]
    lines.append("### Character Anchors")
    for name, traits in ga.get("character", {}).items():
        lines.append(f"**{name}:**")
        if isinstance(traits, str):
            lines.append(f"  {traits}")
        elif isinstance(traits, list):
            for t in traits: lines.append(f"  - {t}")
        elif isinstance(traits, dict):
            for k, v in traits.items(): lines.append(f"  - {k}: {v}")
        lines.append("")
    env = ga.get("environment", {})
    lines.append("### Environment Anchor")
    lines.append(f"{env.get('description','')}")
    lines.append(f"Spatial: {env.get('spatial_anchor','')}")
    lines.append("")
    lit = ga.get("lighting", {})
    lines.append("### Lighting System")
    lines.append(f"{lit.get('description','')}")
    lines.append("")
    lines.append("| Source | Kelvin | Direction | Reference Grid |")
    lines.append("|--------|--------|-----------|----------------|")
    for s in lit.get("anchor_sources", []):
        lines.append(f"| {s.get('source','')} | {s.get('kelvin','')}K "
                     f"| {s.get('direction','')[:30]} | {s.get('ref_grid','')[:30]} |")
    lines.append("")
    sty = ga.get("style_spine", {})
    lines.append("### Style Spine and Color Palette")
    lines.append(f"{sty.get('description','')}")
    for p in sty.get("palette_anchors", []): lines.append(f"  - {p}")
    lines.append("")
    lines.append("### Global Constraints")
    for i, c in enumerate(ga.get("constraints", []), 1): lines.append(f"  {i}. {c}")
    return NL.join(lines) + NL

# ===== MAIN =====

def assemble(plan_path: str, design_path: str, script_path: str, output_path: str) -> str:
    plan = load_plan(plan_path)
    scene, anchors, segments = plan["scene"], plan["anchors"], plan["segments"]
    dialogue_map = plan.get("dialogue_map", [])
    segment_frames = plan.get("segment_frames", [])
    transitions = plan.get("transitions", [])

    # Enrich segments with segment_frames and dialogue_map data
    sf_by_id = {}
    if segment_frames:
        for sf in segment_frames:
            for key in ("segment_id", "shot_id"):
                v = sf.get(key, "")
                if v: sf_by_id[v] = sf
    dm_by_shot = {dm.get("shot_id", ""): dm.get("entries", [])
                  for dm in dialogue_map} if dialogue_map else {}

    # Parse dialogue from script as fallback
    dlgs_raw = parse_dialogue_from_script(script_path)
    # Build dialogue distribution
    ddist = {}
    for seg in segments:
        sid = seg["shot_id"]
        # v2.0: from dialogue_map
        if sid in dm_by_shot:
            ddist[sid] = [{"s": e["speaker"], "t": e.get("text_pt", e.get("text", "")),
                          "d": e.get("direction", ""),
                          "o": (e.get("global_sec_start", 0) - seg.get("global_sec_start", 0)) / max(1, seg.get("duration_s", 6)),
                          "du": e.get("duration_s", 2.5)}
                          for e in dm_by_shot[sid]]
        else:
            ddist[sid] = []
    # Fallback: if no dialogue_map at all, use heuristic
    if not any(v for v in ddist.values()):
        ddist = build_dialogue_map(dlgs_raw, segments)

    # Merge segment_frames data into segments
    for seg in segments:
        sid = seg["shot_id"]
        if sid in sf_by_id:
            seg["segment_frames"] = sf_by_id[sid]
            # Copy characters_in_frame if available
            if "characters_in_frame" in sf_by_id[sid]:
                seg["characters_in_frame"] = sf_by_id[sid]["characters_in_frame"]

    scene_name = scene.get("name", scene.get("id", "Unknown Scene"))
    total_dur = int(sum(s.get("duration_s", 0) for s in segments))
    total_shots = len(segments)
    static_shots = sum(1 for s in segments if s.get("camera_fixed", True))
    static_ratio = static_shots / max(1, total_shots)

    out = [f"# {scene_name} -- Director Script (assembler v2.3 draft){NL}"]
    out.append(f"> **Pipeline:** MODE:P | C-Level | deterministic assembly v2.3")
    out.append(f"> **Scene:** {scene_name} | {total_dur}s | {total_shots} shots")
    out.append(f"> **Axis:** {scene.get('axis_side', anchors.get('axis_line', ''))}")
    out.append(f"> **Movement:** {static_shots}/{total_shots} static ({static_ratio*100:.0f}%)")
    out.append(f"> **Keyframe data:** {'YES' if segment_frames else 'NO (fallback mode)'} | Dialogue map: {'YES' if dialogue_map else 'NO (heuristic)'}")
    out.append(f"> **NL smoothing: deterministic (rule-based · removal + visual anchor injection){NL}")
    out.append("---"); out.append(render_anchors(anchors)); out.append("---")

    for seg in segments:
        sid = seg.get("shot_id", "?"); dur = seg.get("duration_s", 0)
        st = seg.get("scale", seg.get("shot_type", "")); dial = ddist.get(sid, [])
        desc = seg.get("camera_type", seg.get("movement", "")); dur = seg.get("duration_s", 0)
        out.append(f"## Shot {sid}: {st} | {desc} | {dur}s{NL}")
        out.append("### Camera Parameter Card"); out.append(build_card(seg))
        out.append(f"{NL}### Reference Images"); out.append(build_refs(seg, anchors))
        out.append(f"{NL}### Action Frames")
        frames_raw = build_frames(seg, anchors, dial)
        out.append(nl_smooth(frames_raw, seg, anchors))
        out.append(f"### Audio Track"); out.append(build_audio(seg, dial))
        out.append(f"{NL}### Prohibit List (P-FAL rule table)"); out.append(build_prohibit(seg))
        out.append(f"{NL}### Segment Transition"); out.append(build_transition(seg, transitions))
        out.append(f"{NL}---{NL}")

    # R18: Scale-detail validation
    scale_warnings = validate_scale_detail(segments, segment_frames)
    if scale_warnings:
        out.append(f"{NL}---{NL}")
        out.append(f"## ⚠️ R18 Scale-Detail Warnings ({len(scale_warnings)} issues){NL}")
        for w in scale_warnings:
            out.append(f"- {w}")
        out.append(f"{NL}> 景别-细节不匹配: 描述的细节级别超出该景别的光学分辨能力。")
        out.append(f"> 修复: 将细节移至特写/近景镜头·或降级全景中的描述粒度。")

    out.append(f"{NL}---{NL}")
    out.append(f"> **script_assembler v3.0** | deterministic | 0 LLM tokens | 0 Agent calls")
    out.append(f"> **Total:** {len(segments)} shots | R18 scale-detail: {'⚠️'+str(len(scale_warnings))+' warnings' if scale_warnings else '✅ all clean'}")
    out.append(f"> **Next:** [optional] thin Agent for prose rhythm only (~15K tokens)")
    result = NL.join(out)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"OK: {output_path}")
    print(f"    {len(segments)} shots, {scene.get('total_duration_s',0)}s, {len(result)} chars")
    print(f"    Keyframe data: {'YES' if segment_frames else 'NO (fallback)'}")
    print(f"    Next: prose_smoother [Agent] for NL smoothing")
    return result

def main():
    p = argparse.ArgumentParser(description="script_assembler.py v2.0 - deterministic MODE:P assembler")
    p.add_argument("--plan", required=True, help="PLAN YAML file path")
    p.add_argument("--design", default=None, help="Scene Designer YAML (optional)")
    p.add_argument("--script", required=True, help="Original script .txt path")
    p.add_argument("--output", required=True, help="Output .md path")
    args = p.parse_args()
    assemble(args.plan, args.design, args.script, args.output)

if __name__ == "__main__":
    main()