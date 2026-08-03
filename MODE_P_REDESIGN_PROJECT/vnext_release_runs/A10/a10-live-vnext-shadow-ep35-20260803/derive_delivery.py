# -*- coding: utf-8 -*-
"""A10 本地驱动 — 从 shadow run 的 ProjectionAST 确定性派生 vNext 轨交付视图。

调用链(全部为 v3.1 官方代码,本脚本只做编排与排版):
  projection_ast artifact -> ProjectionAST
    -> derive_video / derive_storyboard        (services/projection_compiler.py)
    -> render_video / render_storyboard        (adapters/delivery/*.py)
    -> 本地排版为中文 Markdown 交付文件

约束:
  - 只读 run artifacts,不改任何项目代码/状态;
  - 时间戳由 start_tick/24000 确定性换算(本地代码行为,非模型手写);
  - 内容全部来自 AST 节点 attributes(导演产物),本脚本不做任何创意改写;
  - 交付 profile 显式绑定调用方 CapabilityProfile,digest 校验通过(manifest 默认
    携带的是时长能力 profile digest,这是 v3.1 adapter 契约的既有行为)。
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path

RUN_DIR = Path(__file__).resolve().parent
ARTIFACTS = RUN_DIR / "artifacts"
TICKS_PER_SECOND = 24_000

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "01_调度器"))

from mode_p_vnext.adapters.delivery.capability import (  # noqa: E402
    CapabilityProfile,
    capability_profile_digest,
)
from mode_p_vnext.adapters.delivery.storyboard_adapter import (  # noqa: E402
    render_storyboard,
)
from mode_p_vnext.adapters.delivery.video_adapter import render_video  # noqa: E402
from mode_p_vnext.domain.projection import ProjectionAST, ProjectionNode  # noqa: E402
from mode_p_vnext.domain.time import TickRange  # noqa: E402
from mode_p_vnext.services.projection_compiler import (  # noqa: E402
    derive_storyboard,
    derive_video,
)


def load_artifact(kind: str) -> dict:
    files = list((ARTIFACTS / kind).glob("*.json"))
    if len(files) != 1:
        raise SystemExit(f"expected exactly one {kind} artifact, found {len(files)}")
    with open(files[0], encoding="utf-8") as fh:
        return json.load(fh)["payload"]


def build_node(raw: dict) -> ProjectionNode:
    children = tuple(build_node(child) for child in raw.get("children", []))
    return ProjectionNode(
        node_id=raw["node_id"],
        source_beat_id=raw["source_beat_id"],
        source_shot_id=raw["source_shot_id"],
        interval=TickRange(raw["interval"]["start_tick"], raw["interval"]["end_tick"]),
        start_state_id=raw["start_state_id"],
        end_state_id=raw["end_state_id"],
        decision_ids=tuple(raw["decision_ids"]),
        attributes=dict(raw["attributes"]),
        children=children,
    )


def build_ast(payload: dict) -> ProjectionAST:
    return ProjectionAST(
        projection_id=payload["projection_id"],
        source_vec_artifact_id=payload["source_vec_artifact_id"],
        nodes=tuple(build_node(node) for node in payload["nodes"]),
    )


def fmt_seconds(tick: int) -> str:
    seconds = tick / TICKS_PER_SECOND
    text = f"{seconds:.1f}"
    return text.rstrip("0").rstrip(".") + ".0" if text.endswith(".0") and tick % TICKS_PER_SECOND else text


def attr(node, key: str, default: str = "") -> str:
    value = node.attributes.get(key, default)
    return value if isinstance(value, str) else default


def render_video_markdown(delivery) -> str:
    lines: list[str] = []
    lines.append("# VIDEO_PROMPT — 35.1 人民医院门口 · 夜 · 外(EP35)vNext 轨")
    lines.append("")
    lines.append(
        "> 来源:ProjectionAST 派生(v3.1 derive_video + render_video,本地确定性排版)"
        "> 补丁产物:A10 交付缺口(A10_DELIVERY_PATH_GAP_001)的临时缓解,非项目交付能力;"
        "> A10 已由 owner 决定挂起,等待 V3.2 交付接线包。"
    )
    lines.append("> 内容:全部视觉节拍节点,按镜头分组;每个镜头为一个独立生成单元")
    lines.append("")

    # Group nodes by shot, preserving order.
    by_shot: list[list] = []
    for node in delivery.nodes:
        if not by_shot or by_shot[-1][0].source_shot_id != node.source_shot_id:
            by_shot.append([node])
        else:
            by_shot[-1].append(node)

    for shot_index, nodes in enumerate(by_shot, start=1):
        # Each shot is an independent generation unit: local timeline from 0.
        shot_start = nodes[0].interval.start_tick
        first, last = nodes[0], nodes[-1]
        duration_s = fmt_seconds(last.interval.end_tick - shot_start)
        lines.append(f"## 镜头 scene-{shot_index} | {duration_s}s")
        lines.append("")
        entering = first.attributes.get("entering_boundary")
        if (
            isinstance(entering, Mapping)
            and entering.get("transition_intent")
            and entering["transition_intent"] != "scene entrance"
        ):
            lines.append(f"进入:{entering['transition_intent']}")
            lines.append("")
        for node in nodes:
            start_s = fmt_seconds(node.interval.start_tick - shot_start)
            end_s = fmt_seconds(node.interval.end_tick - shot_start)
            lines.append(f"### [{start_s}s~{end_s}s]")
            for label, key in (
                ("构图", "composition"),
                ("机位", "camera"),
                ("灯光", "lighting"),
                ("表演", "performance"),
            ):
                text = attr(node, key)
                if text:
                    lines.append(f"{label}:{text}")
            notes = attr(node, "creative_notes")
            if notes:
                lines.append(f"注意点:{notes}")
            lines.append("")
        # Shot-level transition out (from last node's exiting boundary).
        exiting = nodes[-1].attributes.get("exiting_boundary")
        if (
            isinstance(exiting, Mapping)
            and exiting.get("transition_intent")
            and exiting["transition_intent"] != "scene exit"
        ):
            lines.append(f"切出:{exiting['transition_intent']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def render_storyboard_markdown(delivery, node_by_id: dict) -> str:
    lines: list[str] = []
    lines.append("# STORYBOARD — 35.1 人民医院门口 · 夜 · 外(EP35)vNext 轨")
    lines.append("")
    lines.append(
        "> 来源:ProjectionAST 派生(v3.1 derive_storyboard + render_storyboard,本地确定性排版)"
        "> 补丁产物:A10 交付缺口(A10_DELIVERY_PATH_GAP_001)的临时缓解,非项目交付能力;"
        "> A10 已由 owner 决定挂起,等待 V3.2 交付接线包。"
    )
    lines.append("> 内容:故事板视图 = [SB] 必选帧(+能力允许的可选帧)")
    lines.append("")

    role_label = {"required": "必选", "optional": "可选"}
    for index, panel in enumerate(delivery.panels, start=1):
        node = node_by_id[panel.source_node_id]
        start_s = fmt_seconds(panel.start_tick)
        end_s = fmt_seconds(panel.end_tick)
        role = role_label.get(attr(node, "storyboard_role"), "")
        lines.append(f"## [SB] 帧 {index} — {start_s}s~{end_s}s({role})")
        lines.append("")
        for label, key in (
            ("构图", "composition"),
            ("机位", "camera"),
            ("灯光", "lighting"),
            ("表演", "performance"),
        ):
            text = attr(node, key)
            if text:
                lines.append(f"{label}:{text}")
        notes = attr(node, "creative_notes")
        if notes:
            lines.append(f"注意点:{notes}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def render_input_markdown(delivery, node_by_id: dict) -> str:
    """Per-shot copy-paste generation input (Jimeng-style).  No creative rewrite."""
    lines: list[str] = []
    lines.append("# vNext 轨渲染输入 — 每镜头一段可复制提示词(35.1)")
    lines.append("")
    lines.append("> 每镜头 = 一个生成单元(≤15s);内容来自 ProjectionAST,仅排版,无改写")
    lines.append("> 补丁产物:A10 交付缺口(A10_DELIVERY_PATH_GAP_001)的临时缓解,非项目交付能力;")
    lines.append("> A10 已由 owner 决定挂起,等待 V3.2 交付接线包。")
    lines.append("")

    by_shot: list[list] = []
    for node in delivery.nodes:
        if not by_shot or by_shot[-1][0].source_shot_id != node.source_shot_id:
            by_shot.append([node])
        else:
            by_shot[-1].append(node)

    for shot_index, nodes in enumerate(by_shot, start=1):
        # Each shot is an independent generation unit: local timeline from 0.
        shot_start = nodes[0].interval.start_tick
        first, last = nodes[0], nodes[-1]
        duration_s = fmt_seconds(last.interval.end_tick - shot_start)
        lines.append(f"## 镜头 {shot_index} | {duration_s}s(生成单元 {shot_index}/6)")
        lines.append("")
        entering = first.attributes.get("entering_boundary")
        exiting = last.attributes.get("exiting_boundary")
        if (
            isinstance(entering, Mapping)
            and entering.get("transition_intent")
            and entering["transition_intent"] != "scene entrance"
        ):
            lines.append(f"**进入**:{entering['transition_intent']}")
        lines.append("")
        lines.append("```text")
        for node in nodes:
            start_s = fmt_seconds(node.interval.start_tick - shot_start)
            end_s = fmt_seconds(node.interval.end_tick - shot_start)
            parts: list[str] = []
            for label, key in (
                ("构图", "composition"),
                ("机位", "camera"),
                ("灯光", "lighting"),
                ("表演", "performance"),
            ):
                text = attr(node, key)
                if text:
                    parts.append(f"{label}:{text}")
            notes = attr(node, "creative_notes")
            if notes:
                parts.append(f"注意点:{notes}")
            lines.append(f"[{start_s}s~{end_s}s] " + " ".join(parts))
            lines.append("")
        lines.append("```")
        if (
            isinstance(exiting, Mapping)
            and exiting.get("transition_intent")
            and exiting["transition_intent"] != "scene exit"
        ):
            lines.append(f"**切出**:{exiting['transition_intent']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## 生成约束")
    lines.append("- 每镜头独立生成(硬切拼接),无开场淡入/结尾淡出")
    lines.append("- 人物身份/场景连续性硬要求:同一医院门口,同一两人")
    lines.append("- 冷蓝主调 + 医院钠灯暖色对比贯穿全片")
    lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> int:
    ast_payload = load_artifact("projection_ast")
    ast = build_ast(ast_payload)

    # Delivery capability profile: bounded, SD2.0-style snapshot used by the
    # pure adapters.  Bound it explicitly so the digest check passes and the
    # manifest records the profile actually applied.
    profile = CapabilityProfile(
        platform="sd2.0",
        version="3.1.0",
        max_prompt_chars=12_000,
        reference_slots=1,
        internal_cuts_supported=False,
    )
    bound_digest = capability_profile_digest(profile)

    video_projection = derive_video(ast, capability_profile_digest=bound_digest)
    video_delivery = render_video(video_projection, profile=profile)
    (RUN_DIR / "VNEXT_VIDEO_PROMPT.md").write_text(
        render_video_markdown(video_delivery), encoding="utf-8"
    )

    storyboard_projection = derive_storyboard(
        ast, capability_profile_digest=bound_digest
    )
    storyboard_delivery = render_storyboard(storyboard_projection, profile=profile)
    node_by_id = {node.node_id: node for node in ast.nodes}
    (RUN_DIR / "VNEXT_STORYBOARD.md").write_text(
        render_storyboard_markdown(storyboard_delivery, node_by_id), encoding="utf-8"
    )
    (RUN_DIR / "VNEXT_RENDER_INPUT.md").write_text(
        render_input_markdown(video_delivery, node_by_id), encoding="utf-8"
    )

    print(f"nodes={len(video_delivery.nodes)} panels={len(storyboard_delivery.panels)}")
    print(f"video chunks={len(video_delivery.prompt_chunks)}")
    for record in (*video_delivery.adaptation_records, *storyboard_delivery.adaptation_records):
        print(f"adaptation: {record.adaptation_code} semantic_loss={record.semantic_loss}")
    print("wrote VNEXT_VIDEO_PROMPT.md / VNEXT_STORYBOARD.md / VNEXT_RENDER_INPUT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
