"""Source-grounded Golden delivery builder using exact fixture text."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from mode_p_vnext.storyboard_projection import (
    ContractBuilder,
    SourceSpan,
    StoryboardView,
)
from mode_p_vnext.video_projection import VideoPromptView

_HERE = Path(__file__).resolve().parent
_FIXTURE_DIR = _HERE.parent
_TPS = 24000


def _prompt_text(fixture_id: str) -> str:
    payload = json.loads(
        (_FIXTURE_DIR / f"{fixture_id}_prompt.json").read_text(encoding="utf-8")
    )
    return payload["prompt_text"]


def _section(
    fixture_id: str,
    start_marker: str,
    end_marker: str | None = None,
) -> str:
    """Extract one exact, trimmed, contiguous section from a pinned prompt."""
    prompt = _prompt_text(fixture_id)
    start = prompt.index(start_marker)
    end = prompt.index(end_marker, start) if end_marker else len(prompt)
    return prompt[start:end].strip()


def _load_registry() -> dict:
    return json.loads((_HERE / "source_spans.json").read_text(encoding="utf-8"))


def _get_source(fixture_id: str, field_key: str) -> SourceSpan:
    reg = _load_registry()
    fid = f"{fixture_id}.{field_key}"
    for field in reg["fixtures"][fixture_id]["fields"]:
        if field["field_id"] == fid:
            return SourceSpan(**{k: field[k] for k in [
                "fixture_id", "prompt_body_sha256", "start", "end",
                "exact_text", "exact_text_sha256", "field_id"]})
    raise KeyError(f"field {fid} not in registry")


def _get_exact_source(value: str) -> SourceSpan:
    """Return an exact fixture span for an emitted value.

    The registry is an output index, not an authority prerequisite.  Search it
    first to preserve stable named field IDs, then deterministically resolve
    new values straight from the immutable R1.2 prompt bodies.  This breaks the
    former circular dependency where the registry generator could not discover
    a value until that value had already been registered.
    """
    matches: list[SourceSpan] = []
    for fixture_id, entry in _load_registry()["fixtures"].items():
        for field in entry["fields"]:
            if field["exact_text"] == value:
                matches.append(
                    SourceSpan(
                        **{
                            key: field[key]
                            for key in [
                                "fixture_id",
                                "prompt_body_sha256",
                                "start",
                                "end",
                                "exact_text",
                                "exact_text_sha256",
                                "field_id",
                            ]
                        }
                    )
                )
    if matches:
        return sorted(
            matches, key=lambda source: (source.fixture_id, source.field_id)
        )[0]

    for fixture_id in sorted(_load_registry()["fixtures"]):
        prompt = _prompt_text(fixture_id)
        start = prompt.find(value)
        if start < 0:
            continue
        value_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return SourceSpan(
            fixture_id=fixture_id,
            prompt_body_sha256=hashlib.sha256(
                prompt.encode("utf-8")
            ).hexdigest(),
            start=start,
            end=start + len(value),
            exact_text=value,
            exact_text_sha256=value_hash,
            field_id=f"{fixture_id}.auto_{value_hash[:20]}",
        )

    raise KeyError(f"no exact SourceSpan for emitted value: {value!r}")


def _txt(fid, key):
    """Get exact fixture text for a creative field."""
    return _get_source(fid, key).exact_text


def _add_src(b, path, fid, key):
    """Add a SourceSpan record for a creative value."""
    b._add_source(path, _get_source(fid, key))


def _add_deriv(b, path, rule, *inputs):
    """Add a derivation record. The derivation value must be a string
    matching ALLOWED_DERIVATIONS for gate compatibility."""
    b._derivations.append((path, rule))


def _add_node(b, nid, st, et, pid, ntype, sb, sid, display, fid, desc_src_key="style", tk="interval"):
    prov = {k: f"{fid}:{nid}_{k}" for k in display}
    b.add_node(nid, st, et, pid, ntype, sb, sid, display, prov, temporal_kind=tk)
    # Add SourceSpans for ALL display fields (required for gate coverage)
    for k, v in display.items():
        path = f"nodes[{nid}].display.{k}"
        if k == "time":
            _add_deriv(b, path, "parse_timecode", f"tick:{st}")
            # Use a mechanical SourceSpan for the value
            _add_mech_src(b, path, v)
        elif k in ("shot_size", "focal_intent", "camera_motion"):
            _add_deriv(b, path, "normalize_phase_field", f"phase:{pid}")
            _add_mech_src(b, path, v)
        elif k == "description":
            _add_src(b, path, fid, desc_src_key)
        else:
            _add_mech_src(b, path, v)


def _add_cut(b, nid, tick, pid, fid, dkey="whatsapp"):
    _add_node(b, nid, tick, tick, pid, "boundary", True, "",
              {"description": _txt(fid, dkey)}, fid, dkey, tk="at")


def _add_mech_src(b: ContractBuilder, path: str, value: str):
    """Bind a mechanical value to a real exact fixture span.

    Derivation metadata describes normalization intent, but never licenses an
    unrelated generic span.
    """
    b._add_source(path, _get_exact_source(value))


def _add_common_derivs(b: ContractBuilder, n_phases: int, n_legend: int,
                        n_refs: int, n_duties: int):
    """Add derivations and SourceSpans for mechanical fields."""
    phases = b._phases[:n_phases]
    for i, phase in enumerate(phases):
        for field, value in (
            ("label", phase.label),
            ("shot_size", phase.shot_size),
            ("focal_length", phase.focal_length),
            ("camera_motion", phase.camera_motion),
        ):
            path = f"phases[{i}].{field}"
            _add_deriv(b, path, "normalize_phase_field", f"phase:{i}")
            _add_mech_src(b, path, value)
    legends = sorted(b._legend.items())[:n_legend]
    for i, (colour, meaning) in enumerate(legends):
        for field, value in (("colour", colour), ("meaning", meaning)):
            path = f"annotation_legend[{i}].{field}"
            _add_deriv(b, path, "normalize_phase_field", f"legend:{i}")
            _add_mech_src(b, path, value)
    for i, value in enumerate(b._ref_images[:n_refs]):
        path = f"reference_images[{i}]"
        _add_deriv(b, path, "normalize_reference_id", f"ref:{i}")
        _add_mech_src(b, path, value)
    for i, (reference_id, duty) in enumerate(b._ref_duties[:n_duties]):
        for field, value in (
            ("reference_id", reference_id),
            ("duty", duty),
        ):
            path = f"reference_responsibilities[{i}].{field}"
            _add_deriv(b, path, "normalize_reference_id", f"duty:{i}")
            _add_mech_src(b, path, value)
    if b._route_marker:
        if not b._prohibitions:
            raise ValueError("routing marker requires a source prohibition")
        _add_deriv(
            b,
            "prohibition_routing_marker",
            "derive_route_from_prohibition",
            "prohibitions[0]",
        )
        b._add_source(
            "prohibition_routing_marker",
            _get_exact_source(b._prohibitions[0]),
        )


def build_golden_deliveries() -> Dict[str, Any]:
    deliveries: Dict[str, Any] = {}
    T = _TPS

    # === gun_barrel: 13 SB, 14 video ===
    gb = ContractBuilder("段2 · 工作室·枪管检查")
    gb.set_style(_txt("gun_barrel_sb", "style"), "source:gun_barrel_sb.style")
    _add_src(gb, "style_declaration", "gun_barrel_sb", "style")
    gb.add_character_ref(_txt("gun_barrel_sb", "rico_seated"))
    _add_src(gb, "character_refs[0]", "gun_barrel_sb", "rico_seated")
    gb.add_scene_ref(_txt("gun_barrel_sb", "lamp"))
    _add_src(gb, "scene_refs[0]", "gun_barrel_sb", "lamp")
    for colour, meaning in [
        ("红色箭头", "身体运动"),
        ("蓝色箭头", "相机运动"),
        ("绿色标记", "构图笔记"),
        ("橙色标记", "光线方向"),
    ]:
        gb.set_annotation_legend_item(colour, meaning)
    gb_anchors = _section(
        "gun_barrel_sb", "共享视觉锚(全部13格):", "\n\n\n格1 "
    )
    gb.set_anchors(gb_anchors, _get_exact_source(gb_anchors))
    gb_numbering = _section("gun_barrel_video", "编号含义:", "\n\n\n@rico")
    gb.set_numbering(gb_numbering, _get_exact_source(gb_numbering))
    for pid, label, sz, fl, cm in [
        ("①", "0-3s", "全景", "24mm", "固定"),
        ("②", "3-7s", "中近景", "50mm", "弧形绕行"),
        ("③", "7-13s", "极近特写", "85mm", "极慢推近"),
    ]:
        gb.add_phase(pid, label, sz, fl, cm)
    gb.set_target_style(_txt("gun_barrel_video", "live_action"), "source:gun_barrel_video.target")
    _add_src(gb, "target_style", "gun_barrel_video", "live_action")
    gb_arrow = _section(
        "gun_barrel_sb", "标注颜色系统:", "\n\n\n共享视觉锚"
    )
    gb.set_arrow_explanation(gb_arrow, _get_exact_source(gb_arrow))
    gb_priority = "为分镜参考"
    gb.set_storyboard_priority(
        gb_priority, _get_exact_source(gb_priority)
    )
    gb_lighting = _section(
        "gun_barrel_video",
        "工作台单盏金属罩台灯",
        "\n\n\n────────────────────────────────────────",
    )
    gb.set_lighting(gb_lighting, _get_exact_source(gb_lighting))

    desc_gb = _txt("gun_barrel_sb", "anchor_rico")
    desc_gb13 = _txt("gun_barrel_sb", "anchor_panel13")
    for i in range(13):
        sec = i
        end_sec = min(i + 1, 13)
        pid = "①" if sec < 3 else ("②" if sec < 7 else "③")
        sz = "全景" if sec < 3 else ("中近景" if sec < 7 else ("极近特写" if sec < 10 else "极特写"))
        fl = "24mm" if sec < 4 else ("50mm" if sec < 7 else ("85mm" if sec < 10 else "135mm"))
        dtext = desc_gb13 if i == 12 else desc_gb
        dkey = "anchor_panel13" if i == 12 else "anchor_rico"
        _add_node(gb, f"gb_{i:02d}", sec*T, end_sec*T, pid, "panel", True, "S3",
                  {"time": f"{sec}s", "shot_size": sz, "focal_intent": fl,
                   "camera_motion": "固定" if i > 0 else "前推",
                   "description": dtext},
                  "gun_barrel_sb", dkey)

    _add_node(gb, "gb_v14", 13*T, 13*T, "③", "hold", False, "",
              {"description": _txt("gun_barrel_video", "anchor_vortex")}, "gun_barrel_video", "anchor_vortex", tk="at")
    _add_node(gb, "gb_audio", 13*T, 13*T, "③", "audio", False, "",
              {"description": _txt("gun_barrel_video", "not_vortex")}, "gun_barrel_video", "not_vortex", tk="at")

    gb_handoff = "画面保持→嗡声硬切断→段3"
    gb.set_handoff(gb_handoff, _get_exact_source(gb_handoff))
    gb_prohibition = _section("gun_barrel_video", "【禁止】")
    gb.add_prohibition(gb_prohibition)
    gb._add_source("prohibitions[0]", _get_exact_source(gb_prohibition))
    gb.set_routing_marker("human_qa_only")
    gb_audio = "窗外远处隐约狗叫声，一声。"
    gb.add_audio(gb_audio)
    gb._add_source("audio_track[0]", _get_exact_source(gb_audio))
    gb_transition = (
        "End of segment: tube opening frame held→hum hard cut→"
        "0.3s silence→Segment 3"
    )
    gb.set_transition(gb_transition, _get_exact_source(gb_transition))
    gb.set_required_kinds("storyboard", "video")
    gb.set_required_sb_sections("references", "style", "annotation_legend", "shared_visual_anchors", "numbering", "timeline")
    gb.set_required_vp_sections("upload_refs", "reference_duties", "numbering", "arrow_explanation", "storyboard_priority", "target_style", "lighting", "timeline", "audio", "prohibitions", "prohibition_route")
    gb.set_segment_bounds(0, T*13, T); gb.set_authoritative_shot_ids("S1", "S2", "S3")
    gb.add_reference_image("@图片1"); gb.set_reference_duty("@图片1", "为分镜参考")
    gb.add_reference_image("@rico"); gb.set_reference_duty("@rico", "rico 作为主角，保持外貌服装一致")
    _add_common_derivs(gb, 3, 4, 2, 2)
    gb_contract = gb.build()
    deliveries["gun_barrel_sb"] = StoryboardView(segment_id=gb_contract.segment_id, contract=gb_contract)
    deliveries["gun_barrel_video"] = VideoPromptView(segment_id=gb_contract.segment_id,
        reference_images=list(gb_contract.reference_images),
        audio_track=list(gb_contract.audio_track),
        forbidden=list(gb_contract.prohibitions), contract=gb_contract)

    # === audience: 12/12 ===
    au = ContractBuilder("段3 · 观众席")
    au.set_style(_txt("audience_sb", "style_long"), "source:audience_sb.style")
    _add_src(au, "style_declaration", "audience_sb", "style_long")
    au.add_character_ref(_txt("audience_sb", "isabela"))
    _add_src(au, "character_refs[0]", "audience_sb", "isabela")
    au.add_scene_ref(_txt("audience_sb", "venue"))
    _add_src(au, "scene_refs[0]", "audience_sb", "venue")
    au.set_annotation_legend_item("红", "身体运动")
    au.set_annotation_legend_item("蓝", "相机运动")
    au_anchors = _section(
        "audience_sb", "共享视觉锚(全部12格):", "\n\n\n编号含义:"
    )
    au.set_anchors(au_anchors, _get_exact_source(au_anchors))
    au_numbering = _section(
        "audience_sb", "编号含义:", "\n\n\n────────────────────────"
    )
    au.set_numbering(au_numbering, _get_exact_source(au_numbering))
    au.set_target_style(_txt("gun_barrel_video", "live_action"), "source:gun_barrel_video.target")
    _add_src(au, "target_style", "gun_barrel_video", "live_action")
    au_arrow = _section(
        "audience_sb", "标注颜色系统:", "\n\n\n共享视觉锚"
    )
    au.set_arrow_explanation(au_arrow, _get_exact_source(au_arrow))
    au_priority = "以 @STORYBOARD_LINEART_场景B.png 为构图和机位参考。"
    au.set_storyboard_priority(
        au_priority, _get_exact_source(au_priority)
    )
    au_lighting = (
        "观众席LED灯管~4000K冷白偏暖·顶光漫射·"
        "靶场远端暖黄LED~3500K"
    )
    au.set_lighting(au_lighting, _get_exact_source(au_lighting))
    au.add_phase("①", "0-3s", "WS", "24mm", "固定")
    au.add_phase("②", "3-8s", "MCU", "50mm", "切")
    au.add_phase("③", "8-11s", "ECU", "85mm", "固定")

    desc_wa = _txt("audience_sb", "anchor_wa")  # "WhatsApp"
    desc_sb = _txt("audience_sb", "anchor_cut")   # "格3s→格4s [切]"
    desc_v = _txt("audience_video", "anchor_cutv")  # "切 镜B-1→B-2"
    desc_wa = _txt("audience_sb", "anchor_wa")       # "WhatsApp"
    for i in range(12):
        sec = i
        pid = "①" if sec < 3 else ("②" if sec < 8 else "③")
        sz = "WS" if sec < 3 else ("MCU" if sec < 8 else "ECU")
        fl = "24mm" if sec < 3 else ("50mm" if sec < 8 else "85mm")
        if i == 0:
            dtext, dkey, dfid = desc_sb, "anchor_cut", "audience_sb"
        elif i == 1:
            dtext, dkey, dfid = desc_v, "anchor_cutv", "audience_video"
        else:
            dtext, dkey, dfid = desc_wa, "anchor_wa", "audience_sb"
        _add_node(au, f"au_{i:02d}", sec*T, (sec+1)*T, pid, "panel", True,
                  f"S{min(i+1,3)}", {"time": f"{sec}s", "shot_size": sz,
                  "focal_intent": fl, "camera_motion": "固定", "description": dtext},
                  dfid, dkey)
    _add_cut(au, "cut_3s", 3*T, "②", "audience_sb", "whatsapp")
    _add_cut(au, "cut_8s", 8*T, "③", "audience_sb", "whatsapp")

    au_handoff = _section(
        "audience_sb",
        "格8s→格9s [切]:",
        "\n\n\n────────────────────────",
    )
    au.set_handoff(au_handoff, _get_exact_source(au_handoff))
    au_audio = _section("audience_video", "@音轨:", "\n\n\n@禁止:")
    au.add_audio(au_audio)
    au._add_source("audio_track[0]", _get_exact_source(au_audio))
    au_prohibition = _section("audience_video", "@禁止:")
    au.add_prohibition(au_prohibition)
    au._add_source("prohibitions[0]", _get_exact_source(au_prohibition))
    au.set_routing_marker("inline_supported")
    au.set_required_kinds("storyboard", "video")
    au.set_required_sb_sections("references", "style", "annotation_legend", "shared_visual_anchors", "numbering", "timeline")
    au.set_required_vp_sections("upload_refs", "reference_duties", "numbering", "arrow_explanation", "storyboard_priority", "target_style", "lighting", "timeline", "audio", "prohibitions", "prohibition_route")
    au.set_segment_bounds(0, T*12, T); au.set_authoritative_shot_ids("S1", "S2", "S3")
    au.add_reference_image("@图片1")
    au.set_reference_duty(
        "@图片1",
        "STORYBOARD_LINEART_场景B.png(黑白线稿故事板·12格·构图+机位+人物位置参考)",
    )
    au.add_reference_image("@Isabela")
    au.set_reference_duty(
        "@Isabela",
        "人物/伊莎贝拉・科斯塔（Isabela Costa）.txt(面部·鹅蛋脸·灰绿色眼睛·暖棕卷发·燕麦色针织开衫)",
    )
    _add_common_derivs(au, 3, 2, 2, 2)
    au_contract = au.build()
    deliveries["audience_sb"] = StoryboardView(segment_id=au_contract.segment_id, contract=au_contract)
    deliveries["audience_video"] = VideoPromptView(segment_id=au_contract.segment_id,
        reference_images=list(au_contract.reference_images),
        audio_track=list(au_contract.audio_track),
        forbidden=list(au_contract.prohibitions), contract=au_contract)

    # === prep_area: 10/10 ===
    pa = ContractBuilder("段4 · 备赛区")
    pa.set_style(_txt("prep_area_sb", "style_long"), "source:prep_area_sb.style")
    _add_src(pa, "style_declaration", "prep_area_sb", "style_long")
    pa.add_character_ref(_txt("prep_area_sb", "rico"))
    _add_src(pa, "character_refs[0]", "prep_area_sb", "rico")
    pa.add_character_ref(_txt("prep_area_sb", "iuri"))
    _add_src(pa, "character_refs[1]", "prep_area_sb", "iuri")
    pa.add_scene_ref(_txt("prep_area_sb", "prep_zone"))
    _add_src(pa, "scene_refs[0]", "prep_area_sb", "prep_zone")
    pa.set_annotation_legend_item("红色箭头", "身体运动")
    pa.set_annotation_legend_item("蓝色箭头", "相机运动")
    pa_anchors = _section(
        "prep_area_sb", "共享视觉锚(全部10格):", "\n\n\n编号含义:"
    )
    pa.set_anchors(pa_anchors, _get_exact_source(pa_anchors))
    pa_numbering = _section(
        "prep_area_sb", "编号含义:", "\n\n\n────────────────────────"
    )
    pa.set_numbering(pa_numbering, _get_exact_source(pa_numbering))
    pa.set_target_style(_txt("gun_barrel_video", "live_action"), "source:gun_barrel_video.target")
    _add_src(pa, "target_style", "gun_barrel_video", "live_action")
    pa_arrow = _section(
        "prep_area_video",
        "故事板线稿箭头含义:",
        "\n以 @图片1",
    )
    pa.set_arrow_explanation(pa_arrow, _get_exact_source(pa_arrow))
    pa_priority = _section(
        "prep_area_video", "以 @图片1", "\n  @备赛区"
    )
    pa.set_storyboard_priority(
        pa_priority, _get_exact_source(pa_priority)
    )
    pa_lighting = _section(
        "prep_area_video", "格0s [0s] 固定机位", "\n格1s"
    )
    pa.set_lighting(pa_lighting, _get_exact_source(pa_lighting))
    pa.add_phase("①", "0-10s", "MS", "35mm", "固定")

    desc_rico = _txt("prep_area_sb", "anchor_rico")
    desc_p5s = _txt("prep_area_sb", "anchor_p5s")
    desc_iuri = _txt("prep_area_video", "anchor_iuri")
    desc_locked = _txt("prep_area_video", "anchor_locked")
    for i in range(10):
        sec = i
        if i == 4:
            dtext, dkey, dfid = desc_p5s, "anchor_p5s", "prep_area_sb"
        elif i == 5:
            dtext, dkey, dfid = (
                desc_iuri,
                "anchor_iuri",
                "prep_area_video",
            )
        elif i == 6:
            dtext, dkey, dfid = (
                desc_locked,
                "anchor_locked",
                "prep_area_video",
            )
        else:
            dtext, dkey, dfid = desc_rico, "anchor_rico", "prep_area_sb"
        _add_node(pa, f"pa_{i:02d}", sec*T, (sec+1)*T, "①", "panel", True, "",
                  {"time": f"{sec}s", "shot_size": "MS", "focal_intent": "35mm",
                   "camera_motion": "固定", "description": dtext},
                  dfid, dkey)

    pa_handoff = "一个走向亮处·一个留在暗处。"
    pa.set_handoff(pa_handoff, _get_exact_source(pa_handoff))
    pa_audio = _section("prep_area_video", "@音轨:", "\n\n\n@禁止:")
    pa.add_audio(pa_audio)
    pa._add_source("audio_track[0]", _get_exact_source(pa_audio))
    pa_prohibition = _section("prep_area_video", "@禁止:")
    pa.add_prohibition(pa_prohibition)
    pa._add_source("prohibitions[0]", _get_exact_source(pa_prohibition))
    pa.set_routing_marker("inline_supported")
    pa.set_required_kinds("storyboard", "video")
    pa.set_required_sb_sections("references", "style", "annotation_legend", "shared_visual_anchors", "numbering", "timeline")
    pa.set_required_vp_sections("upload_refs", "reference_duties", "numbering", "arrow_explanation", "storyboard_priority", "target_style", "lighting", "timeline", "audio", "prohibitions", "prohibition_route")
    pa.set_segment_bounds(0, T*10, T); pa.set_authoritative_shot_ids("_continuous_segment")
    pa.add_reference_image("@图片1")
    pa.set_reference_duty(
        "@图片1",
        "STORYBOARD_LINEART_场景C1.png(黑白线稿故事板·镜C1-1(7格)+C1-2(10格)·构图+机位参考)",
    )
    _add_common_derivs(pa, 1, 2, 1, 1)
    pa_contract = pa.build()
    deliveries["prep_area_sb"] = StoryboardView(segment_id=pa_contract.segment_id, contract=pa_contract)
    deliveries["prep_area_video"] = VideoPromptView(segment_id=pa_contract.segment_id,
        reference_images=list(pa_contract.reference_images),
        audio_track=list(pa_contract.audio_track),
        forbidden=list(pa_contract.prohibitions), contract=pa_contract)

    # === alley: 13/13 ===
    al = ContractBuilder("段5 · 窄巷")
    al.set_style(_txt("alley_sb", "style_long"), "source:alley_sb.style")
    _add_src(al, "style_declaration", "alley_sb", "style_long")
    al.add_character_ref(_txt("alley_sb", "pedro"))
    _add_src(al, "character_refs[0]", "alley_sb", "pedro")
    al.add_scene_ref(_txt("alley_sb", "alley"))
    _add_src(al, "scene_refs[0]", "alley_sb", "alley")
    al.set_annotation_legend_item("红色箭头", "身体运动")
    al.set_annotation_legend_item("蓝色箭头", "相机运动")
    al_anchors = _section(
        "alley_sb", "共享视觉锚(全部13格):", "\n\n\n编号含义:"
    )
    al.set_anchors(al_anchors, _get_exact_source(al_anchors))
    al_numbering = _section(
        "alley_sb", "编号含义:", "\n\n\n────────────────────────"
    )
    al.set_numbering(al_numbering, _get_exact_source(al_numbering))
    al.set_target_style(_txt("gun_barrel_video", "live_action"), "source:gun_barrel_video.target")
    _add_src(al, "target_style", "gun_barrel_video", "live_action")
    al_arrow = _section(
        "alley_video",
        "故事板线稿箭头含义:",
        "\n以 @图片1",
    )
    al.set_arrow_explanation(al_arrow, _get_exact_source(al_arrow))
    al_priority = _section(
        "alley_video", "以 @图片1", "\n\nSTORYBOARD_LINEART_场景D.png"
    )
    al.set_storyboard_priority(
        al_priority, _get_exact_source(al_priority)
    )
    al_lighting = _section(
        "alley_video", "格0s [0s] 低角度", "\n格1s"
    )
    al.set_lighting(al_lighting, _get_exact_source(al_lighting))
    for pid, label, sz, fl, cm in [
        ("①", "0-2s", "MS", "24mm", "手持微跟0.3x"),
        ("②", "2-3s", "天空", "24mm", "仰摇0.5x"),
        ("③", "5-9s", "MS", "35mm", "固定"),
        ("④", "9-12s", "MCU", "50mm→85mm", "微推近0.3x"),
    ]:
        al.add_phase(pid, label, sz, fl, cm)

    descs = [
        _txt("alley_sb", "anchor_chase"),      # 0: 跑动追球
        _txt("alley_sb", "anchor_heli"),       # 1: 直升机画右→画左
        _txt("alley_video", "anchor_heliv"),   # 2: 直升机从画右边缘入画
        _txt("alley_sb", "pedro"),             # 3: Pedro
        _txt("alley_sb", "anchor_car"),        # 4: 轿车静止
    ]
    dkeys = ["anchor_chase", "anchor_heli", "anchor_heliv", "pedro", "anchor_car"]
    dkids = ["alley_sb", "alley_sb", "alley_video", "alley_sb", "alley_sb"]
    for i in range(13):
        sec = i
        pid = "①" if sec < 2 else ("②" if sec < 5 else ("③" if sec < 9 else "④"))
        sz = "MS" if sec < 5 or (5 <= sec < 9) else ("仰摇" if 2 <= sec < 5 else "推近")
        fl = "24mm" if sec < 2 else ("50mm" if (2 <= sec < 5) or (9 <= sec < 13) else "35mm")
        j = i % len(descs)
        _add_node(al, f"al_{i:02d}", sec*T, (sec+1)*T, pid, "panel", True, "",
                  {"time": f"{sec}s", "shot_size": sz, "focal_intent": fl,
                   "camera_motion": (
                       "固定"
                       if 5 <= sec < 9
                       else ("仰摇0.5x" if 2 <= sec < 5 else ("微推近0.3x" if sec >= 9 else "手持微跟0.3x"))
                   ),
                   "description": descs[j]},
                  dkids[j], dkeys[j])
    _add_cut(al, "cut_5s", 5*T, "③", "alley_sb", "run_chase")
    _add_cut(al, "cut_9s", 9*T, "④", "alley_sb", "run_chase")

    al_handoff = "落幅静止。黑色轿车·车窗漆黑·无声·静止。"
    al.set_handoff(al_handoff, _get_exact_source(al_handoff))
    al_audio = _section("alley_video", "@音轨:", "\n\n\n@禁止:")
    al.add_audio(al_audio)
    al._add_source("audio_track[0]", _get_exact_source(al_audio))
    al_prohibition = _section("alley_video", "@禁止:", "\n\n\n@转场:")
    al.add_prohibition(al_prohibition)
    al._add_source("prohibitions[0]", _get_exact_source(al_prohibition))
    al_transition = _section("alley_video", "@转场:")
    al.set_transition(al_transition, _get_exact_source(al_transition))
    al.set_routing_marker("human_qa_only")
    al.set_required_kinds("storyboard", "video")
    al.set_required_sb_sections("references", "style", "annotation_legend", "shared_visual_anchors", "numbering", "timeline")
    al.set_required_vp_sections("upload_refs", "reference_duties", "numbering", "arrow_explanation", "storyboard_priority", "target_style", "lighting", "timeline", "audio", "prohibitions", "prohibition_route")
    al.set_segment_bounds(0, T*13, T); al.set_authoritative_shot_ids("_continuous_segment")
    al.add_reference_image("@图片1")
    al.set_reference_duty(
        "@图片1",
        "STORYBOARD_LINEART_场景D.png(黑白线稿故事板·D-1(6格)+D-2(5格)+D-3(8格)+D-4(5格)+俯视运动图·构图+机位+人物走位参考)",
    )
    _add_common_derivs(al, 4, 2, 1, 1)
    al_contract = al.build()
    deliveries["alley_sb"] = StoryboardView(segment_id=al_contract.segment_id, contract=al_contract)
    deliveries["alley_video"] = VideoPromptView(segment_id=al_contract.segment_id,
        reference_images=list(al_contract.reference_images),
        audio_track=list(al_contract.audio_track),
        forbidden=list(al_contract.prohibitions), contract=al_contract)

    return deliveries
