"""MODE:P vNext — Video Prompt Golden Renderer (V5.4 R1.3).

Public render_video_prompt validates and renders. Fail-closed by default.
No invented defaults.

Spec references: LOOP §11.1-§11.9.
"""

from __future__ import annotations

from mode_p_vnext.storyboard_projection import (
    ContractError,
    DualOutputContract,
    FrozenNode,
    _format_time_display,
    derive_total_duration_s,
    validate_delivery_contract,
)
from mode_p_vnext.video_projection import VideoPromptView


def render_video_prompt(view: VideoPromptView,
                        ticks_per_second: int = 24000) -> str:
    """Render video prompt in Golden format. Validates before emitting any byte."""
    violations = validate_delivery_contract(view.contract, view.segment_id)
    if violations:
        raise ContractError(violations)
    return _render(view, ticks_per_second)


def _render(view: VideoPromptView, tps: int) -> str:
    contract = view.contract
    lines: list[str] = []

    # §1 @上传参考图
    refs = list(contract.reference_images) or view.reference_images
    if refs:
        lines.append("### @上传参考图")
        for i, ref in enumerate(refs, start=1):
            lines.append(f"@图片{i} {ref}")
        lines.append("")

    # §2 Per-reference duties
    for ref_id, duty in contract.reference_responsibilities:
        lines.append(f"**{ref_id}职责：** {duty}")
    if contract.reference_responsibilities:
        lines.append("")

    # Canonical duration is mechanically derived from contract bounds.  It is
    # rendered explicitly because Golden video prompts identify the generation
    # segment duration even when their final state label is duration - 1.
    duration_s = derive_total_duration_s(contract, tps)
    lines.append(f"**片段时长：{_fmt_duration(duration_s)}**")
    lines.append("")

    # §3 Numbering
    if contract.numbering_meaning:
        lines.append(contract.numbering_meaning)
        lines.append("")
    elif contract.phases:
        lines.append("**编号含义：**")
        for ph in contract.phases:
            parts = [ph.shot_size, ph.focal_length, ph.camera_motion]
            lines.append(f"  {ph.phase_id} [{ph.label}]：{'·'.join(p for p in parts if p)}")
        lines.append("")

    # §4 Arrow explanation
    if contract.arrow_explanation:
        lines.append(contract.arrow_explanation)
        lines.append("")

    # §5 Storyboard priority
    if contract.storyboard_priority:
        lines.append(contract.storyboard_priority)
        lines.append("")

    # §6 Target style
    if contract.target_style:
        lines.append(contract.target_style)
        lines.append("")

    # §7 Shared lighting
    if contract.shared_lighting_stability:
        lines.append(contract.shared_lighting_stability)
        lines.append("")

    # §8 Complete timeline (ALL nodes)
    if contract.nodes:
        phase_order: list[str] = []
        groups: dict[str, list[FrozenNode]] = {}
        for n in contract.nodes:
            pid = n.phase_id
            if pid not in groups:
                groups[pid] = []
                phase_order.append(pid)
            groups[pid].append(n)
        for pi, pid in enumerate(phase_order):
            if pi > 0:
                lines.append("---")
                lines.append("")
            for node in groups[pid]:
                _emit_node(lines, node, tps)
            lines.append("")

    # §9 @音轨
    audio = list(contract.audio_track) or view.audio_track
    if audio:
        lines.append("### @音轨")
        for a in audio:
            lines.append(f"- {a}")
        lines.append("")

    # §10 @禁止
    prohs = list(contract.prohibitions) or view.forbidden
    if prohs:
        lines.append("### @禁止")
        for p in prohs:
            lines.append(f"- {p}")
        if contract.prohibition_routing_marker:
            lines.append(f"  *[路由标记：{contract.prohibition_routing_marker}]*")
        lines.append("")

    # §11 @转场
    items: list[str] = []
    if contract.transition_description:
        items.append(contract.transition_description)
    if contract.handoff:
        items.append(contract.handoff)
    if not items and view.transitions:
        items.extend(view.transitions)
    if items:
        lines.append("### @转场")
        for t in items:
            lines.append(f"- {t}")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def _emit_node(lines: list[str], node: FrozenNode, tps: int) -> None:
    ss = _format_time_display(node.start_tick, tps)
    es = _format_time_display(node.end_tick, tps)
    desc = node.get_display("description", "")
    nt = node.node_type

    if nt == "boundary":
        lines.append(f"**{ss} [{node.node_id}]：** {desc}")
    elif nt == "hold":
        lines.append(f"**{ss}–{es} [保持]：** {desc}")
    elif nt == "audio":
        lines.append(f"**{ss}–{es} [@音轨]：** {desc}")
    elif nt == "transition":
        lines.append(f"**{ss} [@转场]：** {desc}")
    else:
        sz = node.get_display("shot_size", "")
        mo = node.get_display("camera_motion", "")
        hdr = " ".join(p for p in [node.phase_id, ss, sz, mo] if p)
        lines.append(f"**{hdr}**")
        if desc:
            lines.append(desc)

    ann = node.get_display("annotations", "")
    if ann:
        lines.append(ann)
    lines.append("")


def _fmt_duration(value: float) -> str:
    if value == int(value):
        return f"{int(value)}s"
    return f"{value:.3f}".rstrip("0").rstrip(".") + "s"
