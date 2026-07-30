"""Derive final STORYBOARD.md and VIDEO_PROMPT.md from Master + Manifest.

This is a deterministic local program. It:
1. Reads DIRECTOR_MASTER.md (creative source) and SHOT_MANIFEST.json (canonical)
2. Sanitises Director-authored creative text for view consumption
3. Applies profile-adaptive field selection per LOOP_SPEC v4.0 SS9-11
4. Fails closed when view-specific creative source text is absent from Master
5. MUST NOT invent creative content, timing, sound, or canonical values

Sanitisation removes: line-number references, dB mixing values,
Director-internal parenthetical notes, comparative-analysis fragments,
and internal notation markers.  Spatial/directional parentheticals are
preserved when they describe visible on-screen position.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

from master_compiler import CompilerError, compile_master

# ---------------------------------------------------------------------------
# Sanitisation — strip Director-internal language from view-facing text
# ---------------------------------------------------------------------------

# Phrases that mark a parenthetical as Director-internal (not visible on screen).
_DIRECTOR_INTERNAL_MARKERS: list[str] = [
    "CG", "特效", "准备训话", "职业面具", "占据空间", "构图变化",
    "服务.*释放", "视觉化", "运镜落稳", "OS开始的标志", "而非",
    "权力.*转移", "用透视表达", "呼应", "信息释放", "景别需要收紧",
    "空间关系需要重置", "攻击尚未结束",
    # Audio production notes
    "reverb", "wet/dry", "约.*秒.*无对白", "渐至.*dB",
]

# Combined pattern: parentheticals containing any internal marker.
_INTERNAL_PAREN_RE = re.compile(
    r"\s*[（(][^）)]*?(?:" + "|".join(_DIRECTOR_INTERNAL_MARKERS) + r")[^）)]*?[）)]",
)

# Line-number references: L3, L4-L9, L14–L16, etc.
# Use lookarounds instead of \b so CJK characters adjacent to digits are handled.
_LINE_REF_RE = re.compile(r"(?<![a-zA-Z0-9])L\d+(?:\s*[-–—]\s*L?\d+)?(?![a-zA-Z0-9])")

# Decibel values: -12dB, —30dB, etc.
_DB_RE = re.compile(r"[-–—]\d+\s*dB")

# Comparative-analysis fragments: "——这是A而非B" style Director reasoning.
_COMPARE_RE = re.compile(r"——\s*这是\s*\S+\s*而非\s*\S+[。，]?")

# Director-intent commentary after em-dash: "——从...力量到...后果" etc.
_DIRECTOR_DASH_RE = re.compile(
    r"——\s*[^。]*(?:力量|后果|信息释放|视觉化|权力|呼应|服务|表达|转移|释放)[^。]*[。]?"
)

# Internal notation phrases to strip wholesale.
_INTERNAL_NOTATION_RE = re.compile(
    r"(?:OS开始的标志|OS开始后|准备训话|构图变化服务信息释放|运镜落稳后固定至镜尾"
    r"|用透视表达[^。，]+?视觉化)"
)

# Slash between Chinese words = unresolved branch: 站/坐, 前景/侧景.
_SLASH_BRANCH_RE = re.compile(r"([一-鿿]+)/([一-鿿]+)")

# Trailing artifacts from sanitisation passes.
_ARTIFACT_RE = re.compile(r"\s*[（(]\s*[）)]")  # empty parens
_MULTISPACE_RE = re.compile(r" {2,}")
_MULTICOMMA_RE = re.compile(r"[,，]\s*[,，]")
_MULTIDASH_RE = re.compile(r"[-–—]\s*[-–—]")


def _sanitize(text: str, *, strip_parentheticals: bool = False) -> str:
    """Clean Director-authored creative prose for view consumption.

    Removes (in order): internal notation phrases, comparative-analysis
    fragments, Director-internal parenthetical notes, line-number
    references, and dB mixing values.  When *strip_parentheticals* is
    true (storyboard path), ALL remaining parentheticals are also
    removed to produce the cleanest keyframe descriptions.  Finally,
    whitespace / punctuation artefacts are collapsed.
    """
    if not text:
        return text

    # 1. Internal notation phrases.
    text = _INTERNAL_NOTATION_RE.sub("", text)

    # 2. Comparative-analysis fragments and Director dash-commentary.
    text = _COMPARE_RE.sub("", text)
    text = _DIRECTOR_DASH_RE.sub("。", text)

    # 3. Parentheticals containing Director-internal markers.
    for _ in range(4):  # nested parens need a few passes
        new_text = _INTERNAL_PAREN_RE.sub("", text)
        if new_text == text:
            break
        text = new_text

    # 4. Line-number references.
    text = _LINE_REF_RE.sub("", text)

    # 5. Decibel values.
    text = _DB_RE.sub("", text)

    # 6. Resolve slash-branches: keep first option, discard /second.
    text = _SLASH_BRANCH_RE.sub(r"\1", text)

    # 7. Storyboard path: strip ALL remaining parentheticals.
    if strip_parentheticals:
        text = re.sub(r"\s*[（(][^）)]*?[）)]", "", text)

    # 8. Collapse artefacts.
    text = _ARTIFACT_RE.sub("", text)
    text = _MULTISPACE_RE.sub(" ", text)
    text = _MULTICOMMA_RE.sub("，", text)
    text = _MULTIDASH_RE.sub("——", text)

    # 8. Trim dangling punctuation connectors.
    text = re.sub(r"^[,，、]\s*", "", text)
    text = re.sub(r"\s*[,，、]$", "", text)
    text = re.sub(r"[,，]\s*[。．]", "。", text)
    text = re.sub(r"[。．]\s*[,，]", "。", text)

    return text.strip()


# --- Regex patterns for parsing creative fields from Master ---

_SHOT_HEADER_RE = re.compile(
    r"^##\s+Shot\s+(?P<scene_id>[A-Za-z0-9_-]+)-(?P<number>\d+)\s*\|\s*(?P<duration>\d+(?:\.\d+)?)\s*s\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_BOUNDARY_HEADER_RE = re.compile(
    r"^##\s+Boundary\s+(?P<boundary_id>[A-Za-z0-9_-]+-B\d+)\s*\|\s*"
    r"(?P<from_ref>SCENE_ENTRY|[A-Za-z0-9_-]+-\d+)\s*->\s*"
    r"(?P<to_ref>SCENE_EXIT|[A-Za-z0-9_-]+-\d+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Creative (Director-only) fields — extracted as raw text
_CAMERA_RE = re.compile(r"^摄影设计：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_COMPOSITION_RE = re.compile(r"^构图设计：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_LIGHTING_RE = re.compile(r"^光影设计：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_PERFORMANCE_RE = re.compile(r"^表演设计：\[D\]\s*(?P<text>.+)", re.MULTILINE)

_STORYBOARD_FRAMES_RE = re.compile(r"^故事板关键帧：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_VIDEO_TIMELINE_RE = re.compile(r"^视频时间轴：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_VISUAL_TIMELINE_RE = re.compile(r"^视觉时间线：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_SOUND_DESIGN_RE = re.compile(r"^声音设计：\[D\]\s*(?P<text>.+)", re.MULTILINE)

_ENTRY_BOUNDARY_DESC_RE = re.compile(r"^进入边界：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_EXIT_BOUNDARY_DESC_RE = re.compile(r"^交出边界：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_TRANSITION_CUT_RE = re.compile(r"^剪辑触发：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_BOUNDARY_HANDOFF_RE = re.compile(r"^交接描述：\[D\]\s*(?P<text>.+)", re.MULTILINE)

_REF_RESPONSIBILITY_RE = re.compile(r"^参考职责：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_REF_PRIORITY_RE = re.compile(r"^参考优先级：\[D\]\s*(?P<text>.+)", re.MULTILINE)

_STORY_FACT_RE = re.compile(r"^剧本事实：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_SCENE_EXPRESSION_RE = re.compile(r"^场景表达：\[M\]\s*<(?P<mode>[a-z_]+)>", re.MULTILINE)

# Scene-level creative text — used for Storyboard scene context
_SCENE_BLUEPRINT_RE = re.compile(r"^场景蓝图：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_SOUND_BASELINE_RE = re.compile(r"^声音基调：\[D\]\s*(?P<text>.+)", re.MULTILINE)
_TIMELINE_NODE_RE = re.compile(
    r"^\[(?P<time>\d+(?:\.\d+)?)s\](?P<storyboard>\[SB\])?\s*"
    r"(?P<text>\S.*)$",
    re.MULTILINE,
)


class DeriverError(Exception):
    """Raised when derivation cannot proceed due to missing/corrupt input."""


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def derive_views(master_path: Path, manifest_path: Path,
                 storyboard_path: Path, video_path: Path) -> None:
    """Read Master + Manifest and write two final, source-bound views."""
    master_text = _read_text(master_path)
    try:
        manifest = json.loads(_read_text(manifest_path))
    except (json.JSONDecodeError, OSError) as exc:
        raise DeriverError(f"Cannot read valid Manifest JSON: {manifest_path}") from exc

    try:
        expected_manifest = compile_master(master_path)
    except CompilerError as exc:
        raise DeriverError(f"Master cannot be compiled: {exc}") from exc
    if manifest != expected_manifest:
        raise DeriverError(
            "Manifest is stale or does not mechanically match the current Master; "
            "recompile before deriving views"
        )

    boundaries = (
        _extract_boundaries_from_master(master_text, manifest)
        if manifest.get("boundaries") else None
    )
    shots_data = _extract_shots_from_master(master_text, manifest, boundaries)
    scene_context = _build_scene_context(master_text, manifest)

    _write_storyboard(storyboard_path, manifest, shots_data, scene_context)
    _write_video_prompt(video_path, manifest, shots_data, scene_context)


# ---------------------------------------------------------------------------
# internal: read & parse
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="gbk")
        except Exception:
            raise DeriverError(f"Cannot decode {path}")


def _single_line(pattern: re.Pattern, block: str, default: str = "") -> str:
    m = pattern.search(block)
    if not m:
        return default
    lines = [m.group("text").strip()]
    for continuation in block[m.end():].splitlines():
        if not continuation.strip():
            continue
        if not continuation.startswith((" ", "\t")):
            break
        lines.append(continuation.strip())
    return "\n".join(line for line in lines if line).strip()


def _extract_shots_from_master(
    text: str,
    manifest: dict,
    boundaries: dict[str, dict] | None = None,
) -> list[dict]:
    """Split Master into per-shot blocks and extract creative fields."""
    # Split by shot headers
    shot_blocks_raw: list[tuple[str, str]] = []
    current_start = None
    current_id = None

    for match in _SHOT_HEADER_RE.finditer(text):
        if current_id is not None:
            shot_blocks_raw.append((current_id, text[current_start:match.start()]))
        current_id = match.group(0).strip()
        current_start = match.start()
    if current_id is not None:
        shot_blocks_raw.append((current_id, text[current_start:]))

    manifest_shots = manifest["shots"]
    if len(shot_blocks_raw) != len(manifest_shots):
        raise DeriverError(
            f"Shot count mismatch: Master has {len(shot_blocks_raw)}, "
            f"Manifest has {len(manifest_shots)}"
        )

    result = []
    for (header, block), mshot in zip(shot_blocks_raw, manifest_shots):
        hm = _SHOT_HEADER_RE.match(header)
        assert hm is not None
        shot_id = f"{hm.group('scene_id')}-{hm.group('number')}"
        if shot_id != mshot["shot_id"]:
            raise DeriverError(f"Shot ID mismatch: Master '{shot_id}' vs Manifest '{mshot['shot_id']}'")

        unified_timeline = _single_line(_VISUAL_TIMELINE_RE, block) if boundaries else ""
        storyboard_frames = ""
        video_timeline = ""
        if unified_timeline:
            nodes = _validate_visual_timeline(
                shot_id,
                unified_timeline,
                mshot["timing_mode"],
                Decimal(str(mshot["duration"])),
            )
            storyboard_frames = "\n".join(
                f"[{_format_timestamp(node['time'])}s] {node['text']}"
                for node in nodes if node["storyboard"]
            )
            video_timeline = "\n".join(
                f"[{_format_timestamp(node['time'])}s] {node['text']}"
                for node in nodes
            )

        shot_data = {
            "shot_id": shot_id,
            "duration": mshot["duration"],
            "scene_expression": mshot["scene_expression"],
            "timing_mode": mshot["timing_mode"],
            "generation_mode": mshot["generation_mode"],
            "transition_execution": mshot["transition_execution"],
            "reference_assets": mshot["reference_assets"],
            "entry_boundary_id": mshot["entry_boundary_id"],
            "exit_boundary_id": mshot["exit_boundary_id"],
            "boundary_continuity": mshot["boundary_continuity"],
            # creative fields from Master
            "story_fact": _single_line(_STORY_FACT_RE, block),
            "camera": _single_line(_CAMERA_RE, block),
            "composition": _single_line(_COMPOSITION_RE, block),
            "lighting": _single_line(_LIGHTING_RE, block),
            "performance": _single_line(_PERFORMANCE_RE, block),
            "storyboard_frames": (
                storyboard_frames if boundaries
                else _single_line(_STORYBOARD_FRAMES_RE, block)
            ),
            "video_timeline": (
                video_timeline if boundaries
                else _single_line(_VIDEO_TIMELINE_RE, block)
            ),
            "visual_timeline": unified_timeline,
            "sound_design": _single_line(_SOUND_DESIGN_RE, block),
            "entry_boundary_desc": (
                boundaries[mshot["entry_boundary_id"]]["handoff"]
                if boundaries else _single_line(_ENTRY_BOUNDARY_DESC_RE, block)
            ),
            "exit_boundary_desc": (
                boundaries[mshot["exit_boundary_id"]]["handoff"]
                if boundaries else _single_line(_EXIT_BOUNDARY_DESC_RE, block)
            ),
            "cut_trigger": (
                boundaries[mshot["exit_boundary_id"]]["cut_trigger"]
                if boundaries else _single_line(_TRANSITION_CUT_RE, block)
            ),
            "ref_responsibility": _single_line(_REF_RESPONSIBILITY_RE, block),
            "ref_priority": _single_line(_REF_PRIORITY_RE, block),
        }
        required_creative = {
            "camera", "composition", "lighting", "performance",
            "storyboard_frames", "video_timeline", "sound_design",
            "entry_boundary_desc", "exit_boundary_desc", "cut_trigger",
            "ref_responsibility", "ref_priority",
        }
        missing = sorted(key for key in required_creative if not shot_data[key])
        if missing:
            raise DeriverError(
                f"Master {shot_id} lacks required Director source fields: {missing}; "
                "repair Master before deriving views"
            )
        if not boundaries:
            _validate_video_timeline(
                shot_id,
                shot_data["video_timeline"],
                shot_data["timing_mode"],
                Decimal(str(shot_data["duration"])),
            )
        if any("[Director:" in shot_data[key] for key in required_creative):
            raise DeriverError(
                f"Master {shot_id} contains an unresolved Director placeholder"
            )
        result.append(shot_data)
    return result


def _extract_boundaries_from_master(text: str, manifest: dict) -> dict[str, dict]:
    """Extract each shared creative handoff exactly once from active Masters."""
    matches = list(_BOUNDARY_HEADER_RE.finditer(text))
    if len(matches) != len(manifest.get("boundaries", [])):
        raise DeriverError(
            "Master/Manifest shared Boundary count mismatch"
        )
    result: dict[str, dict] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        # A Shot may occur before the next Boundary. Stop at the next level-two
        # block so creative fields cannot leak across blocks.
        next_heading = re.search(r"^##\s+", text[match.end():end], re.MULTILINE)
        block_end = match.end() + next_heading.start() if next_heading else end
        block = text[match.start():block_end]
        boundary_id = match.group("boundary_id")
        if boundary_id in result:
            raise DeriverError(f"Duplicate shared Boundary '{boundary_id}'")
        handoff = _single_line(_BOUNDARY_HANDOFF_RE, block)
        cut_trigger = _single_line(_TRANSITION_CUT_RE, block)
        if not handoff or not cut_trigger:
            raise DeriverError(
                f"Boundary {boundary_id} requires one Director-authored handoff and cut trigger"
            )
        result[boundary_id] = {
            "handoff": handoff,
            "cut_trigger": cut_trigger,
        }
    expected = {item["boundary_id"] for item in manifest["boundaries"]}
    if set(result) != expected:
        raise DeriverError("Master shared Boundary IDs do not match Manifest")
    return result


def _build_scene_context(text: str, manifest: dict) -> dict:
    """Extract scene-level context from Master for the view headers."""
    scene = {
        "scene_id": manifest["scene_id"],
        "master_version": manifest["master_version"],
        "blueprint": _single_line(_SCENE_BLUEPRINT_RE, text),
        "sound_baseline": _single_line(_SOUND_BASELINE_RE, text),
    }
    missing = [key for key in ("blueprint", "sound_baseline") if not scene[key]]
    if missing:
        raise DeriverError(
            "Master lacks scene-level Director source fields: " + ", ".join(missing)
        )
    if "[Director:" in scene["blueprint"] or "[Director:" in scene["sound_baseline"]:
        raise DeriverError("Master contains an unresolved scene-level placeholder")
    return scene


def _validate_video_timeline(
    shot_id: str,
    timeline: str,
    timing_mode: str,
    duration: Decimal,
) -> None:
    matches = list(_TIMELINE_NODE_RE.finditer(timeline))
    if not matches:
        raise DeriverError(f"Master {shot_id} video timeline has no timed nodes")
    covered = "\n".join(match.group(0) for match in matches).strip()
    if covered != timeline.strip():
        raise DeriverError(
            f"Master {shot_id} video timeline must contain one visible event per timed line"
        )
    times = [Decimal(match.group("time")) for match in matches]
    if times[0] != 0 or times[-1] != duration:
        raise DeriverError(
            f"Master {shot_id} video timeline must start at 0s and end at {duration}s"
        )
    if any(right <= left for left, right in zip(times, times[1:])):
        raise DeriverError(f"Master {shot_id} video timeline nodes must increase")
    maximum_gap = {
        "second_nodes": Decimal("1"),
        "half_second_nodes": Decimal("0.5"),
    }.get(timing_mode)
    if maximum_gap is not None and any(
        right - left > maximum_gap for left, right in zip(times, times[1:])
    ):
        raise DeriverError(
            f"Master {shot_id} {timing_mode} timeline has a gap larger than {maximum_gap}s"
        )


def _validate_visual_timeline(
    shot_id: str,
    timeline: str,
    timing_mode: str,
    duration: Decimal,
) -> list[dict]:
    """Validate one source timeline and return mechanical storyboard tags."""
    matches = list(_TIMELINE_NODE_RE.finditer(timeline))
    if not matches:
        raise DeriverError(f"Master {shot_id} visual timeline has no timed nodes")
    covered = "\n".join(match.group(0) for match in matches).strip()
    if covered != timeline.strip():
        raise DeriverError(
            f"Master {shot_id} visual timeline must contain one visible event per timed line"
        )
    nodes = [
        {
            "time": Decimal(match.group("time")),
            "storyboard": bool(match.group("storyboard")),
            "text": match.group("text").strip(),
        }
        for match in matches
    ]
    times = [node["time"] for node in nodes]
    if times[0] != 0 or times[-1] != duration:
        raise DeriverError(
            f"Master {shot_id} visual timeline must start at 0s and end at {duration}s"
        )
    if any(right <= left for left, right in zip(times, times[1:])):
        raise DeriverError(f"Master {shot_id} visual timeline nodes must increase")
    maximum_gap = {
        "second_nodes": Decimal("1"),
        "half_second_nodes": Decimal("0.5"),
    }.get(timing_mode)
    if maximum_gap is not None and any(
        right - left > maximum_gap for left, right in zip(times, times[1:])
    ):
        raise DeriverError(
            f"Master {shot_id} {timing_mode} timeline has a gap larger than {maximum_gap}s"
        )
    storyboard_nodes = [node for node in nodes if node["storyboard"]]
    if len(storyboard_nodes) < 2:
        raise DeriverError(
            f"Master {shot_id} needs at least two [SB] nodes for an independent storyboard"
        )
    if not nodes[0]["storyboard"] or not nodes[-1]["storyboard"]:
        raise DeriverError(
            f"Master {shot_id} first and final visual nodes must carry [SB]"
        )
    return nodes


# ---------------------------------------------------------------------------
# Profile field configs — LOOP_SPEC v4.0 SS9-11
# ---------------------------------------------------------------------------

# Storyboard: each profile outputs only the fields its consumer needs.
# (focus_label, extra_labels) where extra_labels maps field_key -> Chinese label.
_SB_PROFILE: dict[str, tuple[str, dict[str, str]]] = {
    "conversation_power": (
        "关键帧", {"composition": "空间关系"},
    ),
    "crowd_attention": (
        "注意力帧", {"composition": "注意力层级", "performance": "群体调度"},
    ),
    "action_chase": (
        "动作帧", {"camera": "空间轨迹"},
    ),
    "suspense_reveal": (
        "揭示帧", {"composition": "信息缺口"},
    ),
    "contemplative_silence": (
        "静默帧", {"composition": "构图留白"},
    ),
    "investigation_object": (
        "发现帧", {"composition": "视线链"},
    ),
    "montage": (
        "节拍帧", {"composition": "视觉锚点"},
    ),
    "cross_space_transition": (
        "空间交接帧", {"composition": "匹配元素"},
    ),
}

# Video Prompt: every profile outputs the same four creative blocks, but
# field order shifts to match the profile's attention priority.
_VIDEO_FIELD_ORDER: dict[str, tuple[str, ...]] = {
    "conversation_power": ("composition", "performance", "camera", "lighting"),
    "crowd_attention": ("composition", "performance", "camera", "lighting"),
    "action_chase": ("camera", "performance", "composition", "lighting"),
    "suspense_reveal": ("composition", "lighting", "camera", "performance"),
    "contemplative_silence": ("composition", "lighting", "performance", "camera"),
    "investigation_object": ("composition", "camera", "lighting", "performance"),
    "montage": ("camera", "composition", "lighting", "performance"),
    "cross_space_transition": ("camera", "composition", "lighting", "performance"),
}

_VIDEO_FIELD_LABELS: dict[str, str] = {
    "camera": "摄影",
    "composition": "构图",
    "lighting": "光影",
    "performance": "表演",
}


# ---------------------------------------------------------------------------
# Storyboard derivation
# ---------------------------------------------------------------------------

def _write_storyboard(path: Path, manifest: dict, shots: list[dict],
                      scene: dict) -> None:
    lines = []
    sid = scene["scene_id"]
    lines.append(f"# {sid} — 故事板")
    lines.append("")

    blueprint = _sanitize(scene["blueprint"], strip_parentheticals=True)
    lines.append("## 场景蓝图")
    lines.append("")
    lines.append(blueprint)
    lines.append("")

    for i, shot in enumerate(shots):
        dur_str = f"{_format_seconds(shot['duration'])}s"
        lines.append(f"## 镜头 {shot['shot_id']} | {dur_str}")
        lines.append("")

        mode = shot["scene_expression"]
        focus_label, extra_fields = _SB_PROFILE.get(
            mode, ("关键帧", {"composition": "空间关系"})
        )

        # Per-profile extra fields (sanitised, no parentheticals).
        for field_key, cn_label in extra_fields.items():
            value = _sanitize(shot.get(field_key, ""), strip_parentheticals=True)
            if value:
                lines.append(f"{cn_label}：{value}")
                lines.append("")

        # Keyframes — Director-tagged [SB] nodes, sanitised.
        sb_frames = _sanitize(shot["storyboard_frames"], strip_parentheticals=True)
        if sb_frames:
            lines.append(f"{focus_label}：")
            lines.append(sb_frames)
            lines.append("")

        # Entry (first shot only).
        if i == 0:
            entry = _sanitize(shot["entry_boundary_desc"], strip_parentheticals=True)
            lines.append(f"进入：{entry}")
            lines.append("")

        # Exit handoff (sanitised; no cut-trigger reasoning).
        exit_desc = _sanitize(shot["exit_boundary_desc"], strip_parentheticals=True)
        lines.append(f"切出：{exit_desc}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Video Prompt derivation
# ---------------------------------------------------------------------------

def _write_video_prompt(path: Path, manifest: dict, shots: list[dict],
                        scene: dict) -> None:
    lines = []
    sid = scene["scene_id"]
    lines.append(f"# {sid} — 视频提示词")
    lines.append("")

    blueprint = _sanitize(scene["blueprint"])
    sound_bl = _sanitize(scene["sound_baseline"])
    lines.append("## 场景蓝图")
    lines.append("")
    lines.append(blueprint)
    lines.append(f"声音基调：{sound_bl}")
    lines.append("")

    for index, shot in enumerate(shots):
        dur_str = f"{_format_seconds(shot['duration'])}s"
        lines.append(f"## 镜头 {shot['shot_id']} | {dur_str}")
        lines.append("")

        mode = shot["scene_expression"]
        creative = {
            "camera": ("摄影", _sanitize(shot["camera"])),
            "composition": ("构图", _sanitize(shot["composition"])),
            "lighting": ("光影", _sanitize(shot["lighting"])),
            "performance": ("表演", _sanitize(shot["performance"])),
        }
        for field_key in _VIDEO_FIELD_ORDER.get(mode, ("composition", "performance", "camera", "lighting")):
            label, value = creative[field_key]
            if value:
                lines.append(f"{label}：{value}")
                lines.append("")

        # Entry (first shot only).
        if index == 0:
            entry = _sanitize(shot["entry_boundary_desc"])
            lines.append(f"进入：{entry}")
            lines.append("")

        # Generation mode.
        gen_labels = {"text_only": "纯提示词", "first_last_frame": "首尾帧", "omni_reference": "全能参考"}
        lines.append(f"生成模式：{gen_labels.get(shot['generation_mode'], shot['generation_mode'])}")
        if shot["reference_assets"]:
            assets_str = ", ".join(
                f"{a['asset_id']}|{a['responsibility']}"
                for a in shot["reference_assets"]
            )
            lines.append(f"参考资产：[{assets_str}]")
        lines.append("")

        # Image timeline — all nodes, sanitised.
        video_tl = _sanitize(shot["video_timeline"])
        lines.append("画面：")
        lines.append(video_tl)
        lines.append("")

        # Sound — sanitised, dB already stripped by _sanitize.
        sound = _sanitize(shot["sound_design"])
        lines.append(f"声音：{sound}")
        lines.append("")

        # Exit.
        trans = "后期完成" if shot["transition_execution"] == "post_production" else "镜内完成"
        exit_desc = _sanitize(shot["exit_boundary_desc"])
        lines.append(f"切出：{trans}。{exit_desc}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_seconds(value: Decimal | float | int) -> str:
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    text = format(decimal_value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _format_timestamp(value: Decimal | float | int) -> str:
    text = _format_seconds(value)
    return text if "." in text else f"{text}.0"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive STORYBOARD.md and VIDEO_PROMPT.md from Master + Manifest"
    )
    parser.add_argument("master", type=Path, help="Path to DIRECTOR_MASTER.md")
    parser.add_argument("manifest", type=Path, help="Path to SHOT_MANIFEST.json")
    parser.add_argument("-s", "--storyboard", type=Path, default=None,
                        help="Output path for STORYBOARD.md (default: manifest dir)")
    parser.add_argument("-v", "--video", type=Path, default=None,
                        help="Output path for VIDEO_PROMPT.md (default: manifest dir)")
    args = parser.parse_args()

    for p in [args.master, args.manifest]:
        if not p.is_file():
            print(f"File not found: {p}", file=sys.stderr)
            return 2

    base = args.manifest.parent
    storyboard_path = args.storyboard or base / "STORYBOARD.md"
    video_path = args.video or base / "VIDEO_PROMPT.md"

    try:
        derive_views(args.master, args.manifest, storyboard_path, video_path)
        print(f"Storyboard -> {storyboard_path}")
        print(f"Video Prompt -> {video_path}")
        return 0
    except DeriverError as exc:
        print(f"Deriver error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
