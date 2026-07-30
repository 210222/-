"""MODE:P vNext — Storyboard Golden Renderer (V5.2 R1.3).

Public render_storyboard validates and renders. Fail-closed by default.
No invented defaults.

Spec references: LOOP §10.1-§10.5.
"""

from __future__ import annotations

from mode_p_vnext.storyboard_projection import (
    ContractError,
    DualOutputContract,
    FrozenNode,
    StoryboardView,
    _format_time_display,
    derive_total_duration_s,
    validate_delivery_contract,
)


def render_storyboard(view: StoryboardView,
                      ticks_per_second: int = 24000) -> str:
    """Render storyboard in Golden format. Validates before emitting any byte."""
    violations = validate_delivery_contract(view.contract, view.segment_id)
    if violations:
        raise ContractError(violations)
    return _render(view, ticks_per_second)


def _render(view: StoryboardView, tps: int) -> str:
    contract = view.contract
    lines: list[str] = []
    duration_s = derive_total_duration_s(contract, tps)

    # §1 Scene title + duration
    sid = contract.segment_id or view.segment_id
    dur_str = _fmt_dur(duration_s)
    lines.append(f"## {sid} ({dur_str})")
    lines.append("")

    # §2 @references
    if contract.character_refs:
        lines.append(f"@人物 {' '.join(contract.character_refs)}")
    if contract.scene_refs:
        lines.append(f"@场景 {' '.join(contract.scene_refs)}")
    if contract.prop_refs:
        lines.append(f"@道具 {' '.join(contract.prop_refs)}")
    if contract.character_refs or contract.scene_refs or contract.prop_refs:
        lines.append("")

    # §3 Style
    if contract.style_declaration:
        lines.append(contract.style_declaration)
        lines.append("")

    # §4 Annotation legend
    legend = contract.annotation_legend
    if legend:
        lines.append("**标注颜色系统：**")
        for colour, meaning in legend.items():
            lines.append(f"  {colour}={meaning}")
        lines.append("")

    # §5 Shared anchors
    if contract.shared_visual_anchors:
        lines.append(f"**共享视觉锚：** {contract.shared_visual_anchors}")
        lines.append("")

    # §6 Numbering
    if contract.numbering_meaning:
        lines.append(contract.numbering_meaning)
        lines.append("")
    elif contract.phases:
        lines.append("**编号含义：**")
        for ph in contract.phases:
            parts = [ph.shot_size, ph.focal_length, ph.camera_motion]
            lines.append(f"  {ph.phase_id} [{ph.label}]：{'·'.join(p for p in parts if p)}")
        lines.append("")

    # §7 Phase-separated panels ([SB] only)
    sb_nodes = [n for n in contract.nodes if n.sb_node]
    if sb_nodes:
        phase_order: list[str] = []
        groups: dict[str, list[FrozenNode]] = {}
        for n in sb_nodes:
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
                _emit_panel(lines, node, tps)
            lines.append("")

    # §8 HOLD
    for hn in contract.nodes:
        if hn.node_type == "hold" and hn.sb_node:
            desc = hn.get_display("description", "")
            lines.append(f"**画面保持：** {desc}" if desc else "**画面保持**")
            lines.append("")

    # §9 Handoff
    if contract.handoff:
        lines.append(contract.handoff)
        lines.append("")

    # §10 Prohibitions
    if contract.prohibitions:
        lines.append("**故事板禁止项：**")
        for p in contract.prohibitions:
            lines.append(f"- {p}")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def _emit_panel(lines: list[str], node: FrozenNode, tps: int) -> None:
    time_str = _format_time_display(node.start_tick, tps)
    sz = node.get_display("shot_size", "")
    fl = node.get_display("focal_intent", "")
    mo = node.get_display("camera_motion", "")
    desc = node.get_display("description", "")
    ann = node.get_display("annotations", "")
    hdr = " ".join(p for p in [node.phase_id, f"[{time_str}]", sz, fl, mo] if p)
    lines.append(f"### {hdr}")
    if desc:
        lines.append(desc)
    if ann:
        lines.append(ann)
    lines.append("")


def _fmt_dur(d: float) -> str:
    if d == int(d):
        return f"{int(d)}s"
    f = f"{d:.3f}".rstrip('0')
    if f.endswith('.'):
        f = f[:-1]
    return f"{f}s"
