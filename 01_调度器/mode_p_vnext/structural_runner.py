"""MODE:P vNext — Golden Structural Runner (V8.3 R1.4 integrity).

Deterministic, fail-closed artifact validator. Parses rendered Storyboard
and Video Prompt artifacts, computes 7 structural categories including
integrity, and returns immutable diagnostics. No model calls, no network,
no external services.

Spec references: LOOP §13, §29.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# Expectation authority — independent fixed constants, never trusted from caller
# ============================================================================

_AUTHORIZED_CASES = frozenset({"gun_barrel", "audience", "prep_area", "alley"})

# SHA-256 of canonical JSON serialization of each authorised CaseExpectation
# (all fields except expectation_fingerprint).  These are fixture constants;
# the runner compares the passed expectation against them.
_EXPECTATION_AUTHORITY: Dict[str, str] = {
    "gun_barrel": "2af8bc25d6f2e0d7da2833018ecbee00d9f086251833d35220276b10db3a015d",
    "audience":   "be92ae296437a87450ed376881384ef8d7cc8cecaf8aa64689e6f1e5fa61d8fa",
    "prep_area":  "2d8a3a6991f54bded65ed801db75ca1c3213526ec016980658b70ab98aaf77d3",
    "alley":      "167f511c9bba318f9a311a722ec8d564bd298cd1a522619d71e143131c42b3a3",
}

# SHA-256 of the full normalized prohibition body text for each scene.
_EXPECTED_PROHIBITION_BODY: Dict[str, str] = {
    "gun_barrel": "202bd0aebb29974e4f47ae3768d0bbdc40e50a4f1a8aa5193fba0f592937d971",
    "audience":   "0cfe10791feea31bd1b0e8ad1a9ef01ddbb77eeb59a32785ee3c2d5bd070ca1c",
    "prep_area":  "baebbc7aa218f8bfbbcf760290b0309985314a628efbbbf4af59eb885af2de4b",
    "alley":      "82813ce3ac9bcd11d54ba93a925b0e0ec57a4e7982cc58ddc2b1770afa0bed1f",
}


def _compute_expectation_fingerprint(exp: "CaseExpectation") -> str:
    """Canonical SHA-256 fingerprint of expectation fields (excl. fingerprint)."""
    fp_data: Dict[str, Any] = {
        "case_id": exp.case_id,
        "segment_start_s": exp.segment_start_s,
        "segment_end_s": exp.segment_end_s,
        "expected_sb_panel_count": exp.expected_sb_panel_count,
        "expected_vp_timeline_count": exp.expected_vp_timeline_count,
        "expected_cut_times": sorted(exp.expected_cut_times),
        "expected_ref_duties": sorted(exp.expected_ref_duties),
        "prohibition_route": exp.prohibition_route,
        "required_sb_sections": list(exp.required_sb_sections),
        "required_vp_sections": list(exp.required_vp_sections),
        "canonical_sb_sha256": exp.canonical_sb_sha256,
        "canonical_vp_sha256": exp.canonical_vp_sha256,
        "scene_root": exp.scene_root,
        "prohibition_body_sha256": exp.prohibition_body_sha256,
        "contract_fingerprint": exp.contract_fingerprint,
        "semantic_sources_sha256": exp.semantic_sources_sha256,
        "expected_segment_id": exp.expected_segment_id,
        "expected_sb_character_refs": list(exp.expected_sb_character_refs),
        "expected_sb_scene_refs": list(exp.expected_sb_scene_refs),
        "expected_sb_prop_refs": list(exp.expected_sb_prop_refs),
        "expected_terminal_nodes": [
            list(node) for node in exp.expected_terminal_nodes
        ],
        "expected_transitions": list(exp.expected_transitions),
    }
    canonical = json.dumps(
        fp_data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ============================================================================
# Immutable types
# ============================================================================


@dataclass(frozen=True)
class Diagnostic:
    """One structural finding."""
    case_id: str
    artifact_kind: str   # "storyboard" | "video" | "homology"
    category: str        # format|timing|cuts|responsibilities|forbidden_routes|homology|integrity
    code: str            # machine-readable code
    detail: str          # human-readable detail


@dataclass(frozen=True)
class StructuralDiagnostics:
    """Complete structural validation result for one case (SB+VP pair).

    Every boolean is computed by the runner — never supplied by the caller.
    integrity_valid gates hash mismatches, expectation authority, and known cases.
    """
    case_id: str
    format_valid: bool
    timing_valid: bool
    cuts_valid: bool
    responsibilities_valid: bool
    forbidden_routes_valid: bool
    homology_valid: bool
    integrity_valid: bool
    diagnostics: Tuple[Diagnostic, ...] = ()

    @property
    def all_valid(self) -> bool:
        return all([
            self.format_valid, self.timing_valid, self.cuts_valid,
            self.responsibilities_valid, self.forbidden_routes_valid,
            self.homology_valid, self.integrity_valid,
        ])


@dataclass(frozen=True)
class CaseExpectation:
    """Immutable expected structural properties for one Golden case.

    Stores stable constants only — no pre-computed pass/fail booleans.
    canonical hashes are fixture constants, never recomputed at test time
    from the artifact under test.
    """
    case_id: str
    segment_start_s: float = 0.0
    segment_end_s: float = 0.0
    expected_sb_panel_count: int = 0
    expected_vp_timeline_count: int = 0
    expected_cut_times: Tuple[float, ...] = ()
    expected_ref_duties: Tuple[Tuple[str, str], ...] = ()
    prohibition_route: str = ""
    prohibition_body_sha256: str = ""
    required_sb_sections: Tuple[str, ...] = ()
    required_vp_sections: Tuple[str, ...] = ()
    canonical_sb_sha256: str = ""
    canonical_vp_sha256: str = ""
    scene_root: str = ""
    contract_fingerprint: str = ""
    semantic_sources_sha256: str = ""
    expected_segment_id: str = ""
    expected_sb_character_refs: Tuple[str, ...] = ()
    expected_sb_scene_refs: Tuple[str, ...] = ()
    expected_sb_prop_refs: Tuple[str, ...] = ()
    expected_terminal_nodes: Tuple[Tuple[str, float, float], ...] = ()
    expected_transitions: Tuple[str, ...] = ()
    expectation_fingerprint: str = ""


# ============================================================================
# Time helpers
# ============================================================================

def _parse_time_display(text: str) -> Optional[float]:
    """Parse a time display like '0s', '3s', '12.5s', '0.000042s' to float seconds."""
    m = re.match(r'^(-?\d+\.?\d*)s$', text.strip())
    if m:
        return float(m.group(1))
    return None


# ============================================================================
# Storyboard artifact parser
# ============================================================================

def _parse_storyboard(text: str) -> Dict[str, Any]:
    """Parse rendered storyboard artifact text into structured data.

    Section-aware parser: finds section boundary markers, classifies sections,
    extracts panels, times, refs, duties, prohibitions.
    Fail-closed: raises ValueError on unparseable content.
    """
    if not text or not text.strip():
        raise ValueError("empty storyboard artifact")

    result: Dict[str, Any] = {
        "sections": [],
        "section_spans": {},
        "panels": [],
        "times": [],
        "hold_text": None,
        "handoff_text": None,
        "prohibitions": [],
        "character_refs": [],
        "scene_refs": [],
        "prop_refs": [],
        "style_text": None,
        "segment_id": None,
        "duration_s": None,
    }

    lines = text.split('\n')
    n = len(lines)

    # Find all section boundary line indices
    boundaries: List[Tuple[int, str]] = []

    for j, line in enumerate(lines):
        if re.match(r'^##\s+', line):
            boundaries.append((j, "title"))
        elif re.match(r'^@(人物|场景|道具)\s+', line):
            if not boundaries or boundaries[-1][1] != "references":
                boundaries.append((j, "references"))
        elif re.match(r'\*\*标注颜色系统', line):
            boundaries.append((j, "annotation_legend"))
        elif re.match(r'\*\*共享视觉锚', line):
            boundaries.append((j, "shared_visual_anchors"))
        elif '编号含义' in line and not line.startswith('**'):
            boundaries.append((j, "numbering"))
        elif re.match(r'^###\s+', line):
            if not boundaries or boundaries[-1][1] != "timeline":
                boundaries.append((j, "timeline"))
        elif re.match(r'\*\*画面保持', line):
            boundaries.append((j, "hold"))
        elif re.match(r'\*\*故事板禁止', line):
            boundaries.append((j, "prohibitions"))

    # ── Extract sections by boundaries ──
    for bi, (start_idx, sec_name) in enumerate(boundaries):
        end_idx = boundaries[bi + 1][0] if bi + 1 < len(boundaries) else n
        result["sections"].append(sec_name)
        result["section_spans"][sec_name] = (start_idx, end_idx)

    # ── §1 Title ──
    if "title" not in result["sections"]:
        raise ValueError("storyboard: missing title line (## segment_id)")
    title_line = lines[boundaries[0][0]]
    title_m = re.match(r'^##\s+(.+?)\s+\((\d+\.?\d*s)\)', title_line)
    if not title_m:
        raise ValueError(f"storyboard: unparseable title: {title_line[:80]!r}")
    result["segment_id"] = title_m.group(1).strip()
    dur_val = _parse_time_display(title_m.group(2))
    if dur_val is None:
        raise ValueError(f"storyboard: unparseable duration in title: {title_m.group(2)!r}")
    result["duration_s"] = dur_val

    # ── §2 References ──
    if "references" in result["sections"]:
        start, end = result["section_spans"]["references"]
        for j in range(start, end):
            line = lines[j]
            if line.startswith('@人物 '):
                result["character_refs"] = line[len('@人物 '):].strip().split()
            elif line.startswith('@场景 '):
                result["scene_refs"] = line[len('@场景 '):].strip().split()
            elif line.startswith('@道具 '):
                result["prop_refs"] = line[len('@道具 '):].strip().split()

    # ── §3 Style ──
    _next_after_refs = None
    for sec in ("annotation_legend", "shared_visual_anchors", "numbering", "timeline"):
        if sec in result["section_spans"]:
            _next_after_refs = sec
            break
    if _next_after_refs and "references" in result["section_spans"]:
        ref_start, ref_span_end = result["section_spans"]["references"]
        ref_content_end = ref_start
        for j in range(ref_start, ref_span_end):
            if re.match(r'^@(人物|场景|道具)\s+', lines[j]):
                ref_content_end = j + 1
        style_end_line = result["section_spans"][_next_after_refs][0]
        style_lines = []
        for j in range(ref_content_end, style_end_line):
            if lines[j].strip() and not lines[j].startswith('---'):
                style_lines.append(lines[j])
        if style_lines:
            result["style_text"] = '\n'.join(style_lines)
            _insert_at = result["sections"].index(_next_after_refs)
            result["sections"].insert(_insert_at, "style")
            result["section_spans"]["style"] = (ref_content_end, style_end_line)

    # ── §7 Timeline panels ──
    if "timeline" in result["sections"]:
        start, end = result["section_spans"]["timeline"]
        for j in range(start, end):
            line = lines[j]
            if line.startswith('### '):
                header = line[4:]
                time_m = re.search(r'\[(\d+\.?\d*s)\]', header)
                time_val = _parse_time_display(time_m.group(1)) if time_m else None
                panel = {"header": header.strip(), "time": time_val}
                boundary_m = re.fullmatch(
                    r'([①②③④⑤⑥⑦⑧⑨⑩])\s+\[(\d+\.?\d*s)\]',
                    header.strip(),
                )
                panel_m = re.fullmatch(
                    r'([①②③④⑤⑥⑦⑧⑨⑩])\s+\[(\d+\.?\d*s)\]\s+'
                    r'(\S+)\s+(\S+)\s+(.+)',
                    header.strip(),
                )
                if boundary_m:
                    panel["phase_id"] = boundary_m.group(1)
                    panel["node_type"] = "boundary"
                    panel["shot_size"] = ""
                    panel["focal_length"] = ""
                    panel["camera_motion"] = ""
                elif panel_m:
                    panel["phase_id"] = panel_m.group(1)
                    panel["node_type"] = "panel"
                    panel["shot_size"] = panel_m.group(3)
                    panel["focal_length"] = panel_m.group(4)
                    panel["camera_motion"] = panel_m.group(5)
                else:
                    panel["phase_id"] = ""
                    panel["node_type"] = "unparseable"
                    panel["shot_size"] = ""
                    panel["focal_length"] = ""
                    panel["camera_motion"] = ""
                desc_lines = []
                k = j + 1
                while k < end and lines[k].strip() and not lines[k].startswith('###') and not lines[k].startswith('---') and not lines[k].startswith('**画面保持') and not lines[k].startswith('**故事板禁止'):
                    desc_lines.append(lines[k])
                    k += 1
                panel["description"] = '\n'.join(desc_lines)
                result["panels"].append(panel)
                if time_val is not None:
                    result["times"].append(time_val)

    # ── §8 HOLD ──
    if "hold" in result["sections"]:
        start, _ = result["section_spans"]["hold"]
        result["hold_text"] = lines[start]

    # ── §9 Handoff ──
    _after_timeline = result["section_spans"]["timeline"][1] if "timeline" in result["section_spans"] else 0
    if "hold" in result["section_spans"]:
        _after_timeline = max(_after_timeline, result["section_spans"]["hold"][1])
    _proh_start = result["section_spans"]["prohibitions"][0] if "prohibitions" in result["section_spans"] else n
    handoff_lines = []
    for j in range(_after_timeline, _proh_start):
        if lines[j].strip():
            handoff_lines.append(lines[j])
    if handoff_lines:
        result["handoff_text"] = '\n'.join(handoff_lines)
        _insert_at = result["sections"].index("prohibitions") if "prohibitions" in result["sections"] else len(result["sections"])
        result["sections"].insert(_insert_at, "handoff")
        result["section_spans"]["handoff"] = (_after_timeline, _proh_start)

    # ── §10 Prohibitions ──
    if "prohibitions" in result["sections"]:
        start, end = result["section_spans"]["prohibitions"]
        for j in range(start, end):
            if lines[j].strip().startswith('- '):
                result["prohibitions"].append(lines[j].strip()[2:])

    return result


# ============================================================================
# Video prompt artifact parser
# ============================================================================

def _parse_video_prompt(text: str) -> Dict[str, Any]:
    """Parse rendered video prompt artifact text into structured data.

    Section-aware parser: finds section boundary markers, classifies sections,
    extracts timeline nodes, times, cuts, refs, duties, prohibitions (full body),
    route.
    Fail-closed: raises ValueError on unparseable content.
    """
    if not text or not text.strip():
        raise ValueError("empty video prompt artifact")

    result: Dict[str, Any] = {
        "sections": [],
        "section_spans": {},
        "reference_images": [],
        "reference_duties": [],
        "duration_s": None,
        "timeline_nodes": [],
        "cut_times": [],
        "audio": [],
        "prohibitions": [],
        "prohibition_body_text": "",  # full normalized body
        "prohibition_route": None,
        "transitions": [],
        "unknown_sections": [],
        "unparsed_timeline_nodes": [],
        "positive_body_text": "",
    }

    lines = text.split('\n')
    n = len(lines)

    boundaries: List[Tuple[int, str]] = []

    for j, line in enumerate(lines):
        if line.startswith('### @上传参考图'):
            boundaries.append((j, "upload_refs"))
        elif line.startswith('**') and '职责：' in line and '片段时长' not in line:
            if not boundaries or boundaries[-1][1] != "reference_duties":
                boundaries.append((j, "reference_duties"))
        elif line.startswith('**片段时长：'):
            boundaries.append((j, "duration"))
        elif '编号含义' in line and not line.startswith('**') and not line.startswith('###'):
            boundaries.append((j, "numbering"))
        elif '标注颜色系统' in line or '箭头含义' in line:
            boundaries.append((j, "arrow_explanation"))
        elif re.match(r'^(以 @|为分镜参考)', line):
            prev_sec = boundaries[-1][1] if boundaries else ""
            if prev_sec in ("arrow_explanation", "storyboard_priority"):
                boundaries.append((j, "storyboard_priority"))
        elif re.search(r'实拍|电影级光影|8K|分辨率', line) and not line.startswith('**'):
            boundaries.append((j, "target_style"))
        elif re.match(r'^\*\*[①②③④⑤⑥⑦⑧⑨⑩]?\s*\d+\.?\d*s', line):
            if not boundaries or boundaries[-1][1] != "timeline":
                boundaries.append((j, "timeline"))
        elif re.match(r'^\*\*\d+\.?\d*s\s+\[', line):
            if not boundaries or boundaries[-1][1] != "timeline":
                boundaries.append((j, "timeline"))
        elif line.startswith('### @音轨'):
            boundaries.append((j, "audio"))
        elif line.startswith('### @禁止'):
            boundaries.append((j, "prohibitions"))
        elif line.startswith('### @转场'):
            boundaries.append((j, "transitions"))
        elif line.startswith('### @'):
            result["unknown_sections"].append(line.strip())

    # ── Extract sections by boundaries ──
    for bi, (start_idx, sec_name) in enumerate(boundaries):
        end_idx = boundaries[bi + 1][0] if bi + 1 < len(boundaries) else n
        result["sections"].append(sec_name)
        result["section_spans"][sec_name] = (start_idx, end_idx)

    # ── Post-scan: Lighting ──
    if "timeline" in result["section_spans"]:
        tl_start = result["section_spans"]["timeline"][0]
        light_end = tl_start
        light_start = tl_start
        for j in range(tl_start - 1, -1, -1):
            if lines[j].strip() and not lines[j].startswith('**') and not lines[j].startswith('###') and not lines[j].startswith('---') and '实拍' not in lines[j] and '8K' not in lines[j] and '为分镜参考' not in lines[j] and '以 @' not in lines[j] and '箭头' not in lines[j] and '编号含义' not in lines[j]:
                light_start = j
            elif lines[j].strip():
                break
        if light_start < light_end:
            light_lines = [l for l in lines[light_start:light_end] if l.strip()]
            if light_lines:
                result["sections"].insert(result["sections"].index("timeline"), "lighting")
                result["section_spans"]["lighting"] = (light_start, light_end)

    # ── §1 Upload refs ──
    if "upload_refs" in result["sections"]:
        start, end = result["section_spans"]["upload_refs"]
        for j in range(start, end):
            if lines[j].startswith('@图片'):
                ref_m = re.match(r'^(@图片\d+)\s+(.+)', lines[j])
                if ref_m:
                    result["reference_images"].append((ref_m.group(1), ref_m.group(2)))

    # ── §2 Reference duties ──
    if "reference_duties" in result["sections"]:
        start, end = result["section_spans"]["reference_duties"]
        for j in range(start, end):
            if '职责：' in lines[j]:
                duty_m = re.match(r'^\*\*(.+?)职责：\*\*\s*(.*)', lines[j])
                if duty_m:
                    result["reference_duties"].append((duty_m.group(1).strip(), duty_m.group(2).strip()))

    # ── §3 Duration ──
    if "duration" in result["sections"]:
        start, _ = result["section_spans"]["duration"]
        dur_m = re.search(r'(\d+\.?\d*)s', lines[start])
        if dur_m:
            result["duration_s"] = float(dur_m.group(1))

    # ── §9 Timeline ──
    if "timeline" in result["sections"]:
        start, end = result["section_spans"]["timeline"]
        j = start
        while j < end:
            line = lines[j]
            if not line.startswith('**') or '片段时长' in line or '职责：' in line:
                j += 1
                continue

            inner = line.strip('*').strip()
            node: Dict[str, Any] = {"raw": inner}
            j += 1

            # Consume description/continuation lines (shared by all node types)
            desc_lines: List[str] = []
            while j < end and lines[j].strip() and not lines[j].startswith('**') and not lines[j].startswith('###') and not lines[j].startswith('---'):
                desc_lines.append(lines[j])
                j += 1

            # Try to match node type from the bold header
            matched = False

            # Boundary: **Xs [node_id]：** desc
            bm = re.match(r'^(\d+\.?\d*s)\s+\[(.+?)\][：:]\s*(.*)', inner)
            if bm:
                t = _parse_time_display(bm.group(1))
                node["start_time"] = t
                node["end_time"] = t
                node["node_id"] = bm.group(2)
                node["node_type"] = "boundary"
                node["description"] = bm.group(3) or ('\n'.join(desc_lines))
                if t is not None:
                    result["cut_times"].append(t)
                matched = True

            # Hold: **Xs–Ys [保持]：** desc
            if not matched:
                hm = re.match(r'^(\d+\.?\d*s)–(\d+\.?\d*s)\s+\[保持\][：:]\s*(.*)', inner)
                if hm:
                    node["start_time"] = _parse_time_display(hm.group(1))
                    node["end_time"] = _parse_time_display(hm.group(2))
                    node["node_type"] = "hold"
                    node["description"] = hm.group(3) or ('\n'.join(desc_lines))
                    matched = True

            # Audio node: **Xs–Ys [@音轨]：** desc
            if not matched:
                am = re.match(r'^(\d+\.?\d*s)–(\d+\.?\d*s)\s+\[@音轨\][：:]\s*(.*)', inner)
                if am:
                    node["start_time"] = _parse_time_display(am.group(1))
                    node["end_time"] = _parse_time_display(am.group(2))
                    node["node_type"] = "audio"
                    node["description"] = am.group(3) or ('\n'.join(desc_lines))
                    matched = True

            # Transition: **Xs [@转场]：** desc
            if not matched:
                tm = re.match(r'^(\d+\.?\d*s)\s+\[@转场\][：:]\s*(.*)', inner)
                if tm:
                    node["start_time"] = _parse_time_display(tm.group(1))
                    node["end_time"] = node["start_time"]
                    node["node_type"] = "transition"
                    node["description"] = tm.group(3) if tm.lastindex and tm.lastindex >= 3 else ('\n'.join(desc_lines))
                    matched = True

            # Panel: **{phase_id} {time}s {shot_size} {camera_motion}**
            if not matched:
                pm = re.match(r'^([①②③④⑤⑥⑦⑧⑨⑩]\s+)?(\d+\.?\d*s)\s+(\S+)\s+(.*)', inner)
                if pm:
                    node["start_time"] = _parse_time_display(pm.group(2))
                    node["end_time"] = node["start_time"]
                    node["phase_id"] = (pm.group(1) or "").strip()
                    node["shot_size"] = pm.group(3)
                    node["camera_motion"] = pm.group(4) if pm.group(4) else ""
                    node["node_type"] = "panel"
                    node["description"] = '\n'.join(desc_lines)
                    matched = True

            result["timeline_nodes"].append(node)
            if not matched:
                result["unparsed_timeline_nodes"].append(inner)

    # ── §10 Audio ──
    if "audio" in result["sections"]:
        start, end = result["section_spans"]["audio"]
        for j in range(start, end):
            if lines[j].strip().startswith('- '):
                result["audio"].append(lines[j].strip()[2:])

    # ── §11 Prohibitions — full body parsing ──
    if "prohibitions" in result["sections"]:
        start, end = result["section_spans"]["prohibitions"]
        raw_body_lines: List[str] = []
        for j in range(start, end):
            stripped = lines[j].strip()
            if stripped.startswith('- '):
                result["prohibitions"].append(stripped[2:])
                # Include bullet text after the prefix as body content
                raw_body_lines.append(stripped[2:])
            elif '*[路由标记' in stripped:
                rm = re.search(r'路由标记[：:]\s*(\S+)\]', stripped)
                if rm:
                    result["prohibition_route"] = rm.group(1)
            elif stripped and not stripped.startswith('### '):
                # Continuation body line (indented text between bullets and route)
                raw_body_lines.append(stripped)
        # Normalize: collapse whitespace, join with spaces
        body_text = ' '.join(' '.join(raw_body_lines).split())
        result["prohibition_body_text"] = body_text

    # ── §12 Transitions ──
    if "transitions" in result["sections"]:
        start, end = result["section_spans"]["transitions"]
        for j in range(start, end):
            if lines[j].strip().startswith('- '):
                result["transitions"].append(lines[j].strip()[2:])

    prohibition_start = (
        result["section_spans"]["prohibitions"][0]
        if "prohibitions" in result["section_spans"]
        else n
    )
    result["positive_body_text"] = " ".join(
        " ".join(lines[:prohibition_start]).split()
    )

    return result


# ============================================================================
# Validators — each returns (bool, list of Diagnostic)
# ============================================================================

def _d(case_id: str, kind: str, cat: str, code: str, detail: str) -> Diagnostic:
    return Diagnostic(case_id=case_id, artifact_kind=kind, category=cat, code=code, detail=detail)


# ── Format (full section order) ──

def _validate_sb_format(case_id: str, parsed: Dict[str, Any],
                         required: Tuple[str, ...]) -> Tuple[bool, List[Diagnostic]]:
    diags: List[Diagnostic] = []
    sections = parsed.get("sections", [])

    # Full sequence check: compare actual sections against required order
    # Filter sections to only those in the required list (ignore meta sections)
    req_set = set(required)
    actual_filtered = [s for s in sections if s in req_set or s == "title"]

    # Check each required section is present
    for sec in required:
        if sec not in sections:
            diags.append(_d(case_id, "storyboard", "format",
                           "SB_MISSING_SECTION", f"missing required section: {sec}"))

    # Check no duplicate sections
    seen = set()
    for sec in sections:
        if sec in seen:
            diags.append(_d(case_id, "storyboard", "format",
                           "SB_DUPLICATE_SECTION", f"duplicate section: {sec}"))
        seen.add(sec)

    # Check ordering: required sections must appear in the specified relative order
    prev_idx = -1
    for sec in required:
        if sec in sections:
            cur_idx = sections.index(sec)
            if cur_idx < prev_idx:
                diags.append(_d(case_id, "storyboard", "format",
                               "SB_SECTION_ORDER",
                               f"section '{sec}' out of order (after previous required section)"))
            prev_idx = cur_idx

    # Timeline must have panels
    panels = parsed.get("panels", [])
    if not panels:
        diags.append(_d(case_id, "storyboard", "format",
                       "SB_NO_PANELS", "no panels found in timeline"))
    for panel in panels:
        if panel.get("node_type") == "unparseable":
            diags.append(_d(
                case_id, "storyboard", "format", "SB_UNPARSEABLE_PANEL",
                f"unparseable storyboard panel header: {panel.get('header', '')!r}",
            ))

    return len(diags) == 0, diags


def _validate_vp_format(case_id: str, parsed: Dict[str, Any],
                         required: Tuple[str, ...]) -> Tuple[bool, List[Diagnostic]]:
    diags: List[Diagnostic] = []
    sections = parsed.get("sections", [])

    for sec in required:
        if sec not in sections:
            diags.append(_d(case_id, "video", "format",
                           "VP_MISSING_SECTION", f"missing required section: {sec}"))

    # Check no duplicate sections
    seen = set()
    for sec in sections:
        if sec in seen:
            diags.append(_d(case_id, "video", "format",
                           "VP_DUPLICATE_SECTION", f"duplicate section: {sec}"))
        seen.add(sec)

    # Full order check: required sections must appear in relative order
    prev_idx = -1
    for sec in required:
        if sec in sections:
            cur_idx = sections.index(sec)
            if cur_idx < prev_idx:
                diags.append(_d(case_id, "video", "format",
                               "VP_SECTION_ORDER",
                               f"section '{sec}' out of order"))
            prev_idx = cur_idx

    timeline_nodes = parsed.get("timeline_nodes", [])
    if not timeline_nodes:
        diags.append(_d(case_id, "video", "format",
                       "VP_NO_TIMELINE", "no timeline nodes found"))

    for section in parsed.get("unknown_sections", []):
        diags.append(_d(
            case_id, "video", "format", "VP_UNKNOWN_SECTION",
            f"unknown section header: {section}",
        ))

    for node in parsed.get("unparsed_timeline_nodes", []):
        diags.append(_d(
            case_id, "video", "format", "VP_UNPARSEABLE_TIMELINE_NODE",
            f"unparseable bold timeline node: {node!r}",
        ))

    required_content = {
        "upload_refs": parsed.get("reference_images", []),
        "reference_duties": parsed.get("reference_duties", []),
        "timeline": timeline_nodes,
        "audio": parsed.get("audio", []),
        "prohibitions": parsed.get("prohibitions", []),
        "transitions": parsed.get("transitions", []),
    }
    for section, content in required_content.items():
        if section in required and section in sections and not content:
            diags.append(_d(
                case_id, "video", "format", "VP_EMPTY_REQUIRED_SECTION",
                f"required section '{section}' has no parseable content",
            ))

    return len(diags) == 0, diags


# ── Timing (raw order reversals + sorted coverage + missing seconds) ──

def _validate_timing(case_id: str, sb_parsed: Dict[str, Any],
                      vp_parsed: Dict[str, Any],
                      expectation: CaseExpectation) -> Tuple[bool, List[Diagnostic]]:
    diags: List[Diagnostic] = []

    seg_end = expectation.segment_end_s
    if seg_end <= 0:
        diags.append(_d(case_id, "video", "timing",
                       "TIMING_NO_BOUNDS", "segment bounds not defined"))
        return False, diags

    # ── SB timing: raw order checks ──
    sb_times_raw = sb_parsed.get("times", [])
    sb_times = list(sb_times_raw)  # keep raw order

    if sb_times:
        # Phase 1: check raw artifact order for true reversals.
        # Boundary at-nodes appear after panels in their phase group, so a
        # "reversal" involving a known cut-point time is expected.  Only flag
        # reversals where NEITHER time is at a known cut point.
        expected_cuts = set(expectation.expected_cut_times)
        for j in range(1, len(sb_times)):
            if sb_times[j] < sb_times[j-1]:
                if sb_times[j] not in expected_cuts and sb_times[j-1] not in expected_cuts:
                    diags.append(_d(case_id, "storyboard", "timing",
                                   "SB_TIME_REVERSED",
                                   f"time {sb_times[j]}s follows {sb_times[j-1]}s — true reversal"))

        # Phase 1b: check for duplicate seconds in raw order
        # Count occurrences; at cut points a panel+boundary share a second legitimately
        from collections import Counter
        time_counts = Counter(sb_times)
        expected_cuts = set(expectation.expected_cut_times)
        for t, count in time_counts.items():
            if t in expected_cuts:
                max_allowed = 2  # panel + boundary at cut point
            else:
                max_allowed = 1  # unique panel per second
            if count > max_allowed:
                diags.append(_d(case_id, "storyboard", "timing",
                               "SB_DUPLICATE_TIME",
                               f"time {t}s appears {count}x (max {max_allowed} allowed)"))

        # Phase 2: sorted checks for out-of-bounds
        sb_times_sorted = sorted(sb_times)
        for t in sb_times_sorted:
            if t < 0 or t >= seg_end:
                diags.append(_d(case_id, "storyboard", "timing",
                               "SB_TIME_OUT_OF_BOUNDS",
                               f"time {t}s out of segment bounds [0, {seg_end}s)"))

        # Phase 3: missing seconds check
        time_set = set(sb_times_sorted)
        for sec in range(int(seg_end)):
            if sec not in time_set:
                diags.append(_d(case_id, "storyboard", "timing",
                               "SB_MISSING_SECOND",
                               f"second {sec}s missing from timeline"))

    # ── VP timing ──
    tl_nodes = vp_parsed.get("timeline_nodes", [])
    vp_times: List[float] = []
    for nd in tl_nodes:
        st = nd.get("start_time")
        et = nd.get("end_time")
        node_type = nd.get("node_type")
        if st is None or et is None:
            continue
        vp_times.append(st)
        if et < st:
            diags.append(_d(
                case_id, "video", "timing", "VP_INTERVAL_REVERSED",
                f"{node_type or 'unknown'} interval {st}s–{et}s is reversed",
            ))
        if node_type == "panel":
            if st < 0 or st >= seg_end or et != st:
                diags.append(_d(
                    case_id, "video", "timing", "VP_PANEL_TIME_OUT_OF_BOUNDS",
                    f"panel time {st}s must be an instant in [0, {seg_end}s)",
                ))
        elif st < 0 or st > seg_end or et < 0 or et > seg_end:
            diags.append(_d(
                case_id, "video", "timing", "VP_INTERVAL_OUT_OF_BOUNDS",
                f"{node_type or 'unknown'} interval {st}s–{et}s "
                f"out of bounds [0, {seg_end}s]",
            ))

    from collections import Counter

    panel_times = [
        nd.get("start_time") for nd in tl_nodes
        if nd.get("node_type") == "panel" and nd.get("start_time") is not None
    ]
    panel_counts = Counter(panel_times)
    for sec in range(int(seg_end)):
        count = panel_counts.get(float(sec), 0)
        if count == 0:
            diags.append(_d(
                case_id, "video", "timing", "VP_MISSING_SECOND",
                f"second {sec}s missing from panel timeline",
            ))
        elif count > 1:
            diags.append(_d(
                case_id, "video", "timing", "VP_DUPLICATE_SECOND",
                f"second {sec}s appears in {count} video panels",
            ))

    expected_terminal = Counter(expectation.expected_terminal_nodes)
    actual_terminal = Counter(
        (
            str(nd.get("node_type")),
            float(nd.get("start_time")),
            float(nd.get("end_time")),
        )
        for nd in tl_nodes
        if nd.get("node_type") in {"hold", "audio", "transition"}
        and nd.get("start_time") is not None
        and nd.get("end_time") is not None
    )
    if actual_terminal != expected_terminal:
        diags.append(_d(
            case_id, "video", "timing", "VP_TERMINAL_TOPOLOGY_MISMATCH",
            f"terminal nodes {sorted(actual_terminal.elements())!r} "
            f"!= expected {sorted(expected_terminal.elements())!r}",
        ))

    # VP raw order reversals (exclude boundary at-node placements)
    vp_expected_cuts = set(expectation.expected_cut_times)
    for j in range(1, len(vp_times)):
        if vp_times[j] < vp_times[j-1]:
            if vp_times[j] not in vp_expected_cuts and vp_times[j-1] not in vp_expected_cuts:
                diags.append(_d(case_id, "video", "timing",
                               "VP_TIME_REVERSED", f"time reversed at node index {j}"))

    # Duration consistency
    sb_dur = sb_parsed.get("duration_s")
    vp_dur = vp_parsed.get("duration_s")
    if sb_dur is not None and abs(sb_dur - seg_end) > 0.01:
        diags.append(_d(case_id, "storyboard", "timing",
                       "SB_DURATION_MISMATCH",
                       f"SB title duration {sb_dur}s != expected {seg_end}s"))
    if vp_dur is None:
        diags.append(_d(case_id, "video", "timing",
                       "VP_DURATION_UNPARSEABLE",
                       "video duration is missing or unparseable"))
    elif abs(vp_dur - seg_end) > 0.01:
        diags.append(_d(case_id, "video", "timing",
                       "VP_DURATION_MISMATCH",
                       f"VP duration {vp_dur}s != expected {seg_end}s"))

    # Last time check
    if sb_times and seg_end > 0:
        max_t = max(sb_times)
        expected_last = seg_end - 1
        if abs(max_t - expected_last) > 0.5:
            diags.append(_d(case_id, "storyboard", "timing",
                           "SB_LAST_TIME_SUSPECT",
                           f"last SB panel at {max_t}s, expected ~{expected_last}s for {seg_end}s segment"))

    return len(diags) == 0, diags


# ── Cuts ──

def _validate_cuts(case_id: str, vp_parsed: Dict[str, Any],
                    expectation: CaseExpectation) -> Tuple[bool, List[Diagnostic]]:
    diags: List[Diagnostic] = []
    expected_cuts = {
        (float(ct), f"cut_{ct:g}s") for ct in expectation.expected_cut_times
    }
    actual_cuts = {
        (float(nd["start_time"]), str(nd.get("node_id", "")))
        for nd in vp_parsed.get("timeline_nodes", [])
        if nd.get("node_type") == "boundary"
        and nd.get("start_time") is not None
    }

    for cut in sorted(expected_cuts):
        if cut not in actual_cuts:
            diags.append(_d(
                case_id, "video", "cuts", "CUT_MISSING_OR_RENAMED",
                f"expected boundary {cut!r} not found",
            ))

    for cut in sorted(actual_cuts):
        if cut not in expected_cuts:
            diags.append(_d(
                case_id, "video", "cuts", "CUT_UNEXPECTED_OR_RENAMED",
                f"unexpected boundary {cut!r}",
            ))

    return len(diags) == 0, diags


# ── Responsibilities (exact set equality) ──

def _validate_responsibilities(case_id: str, vp_parsed: Dict[str, Any],
                                expectation: CaseExpectation) -> Tuple[bool, List[Diagnostic]]:
    diags: List[Diagnostic] = []

    ref_images = vp_parsed.get("reference_images", [])
    ref_duties = vp_parsed.get("reference_duties", [])

    # Count check
    if len(ref_images) != len(ref_duties):
        diags.append(_d(case_id, "video", "responsibilities",
                       "REF_DUTY_COUNT_MISMATCH",
                       f"{len(ref_images)} reference images vs {len(ref_duties)} duties"))

    # No duplicate reference image IDs
    seen_refs = set()
    for ref_id, _ in ref_images:
        if ref_id in seen_refs:
            diags.append(_d(case_id, "video", "responsibilities",
                           "REF_DUPLICATE_ID", f"duplicate reference image: {ref_id}"))
        seen_refs.add(ref_id)

    expected_upload_ids = [
        f"@图片{index}" for index in range(1, len(ref_images) + 1)
    ]
    actual_upload_ids = [ref_id for ref_id, _ in ref_images]
    if actual_upload_ids != expected_upload_ids:
        diags.append(_d(
            case_id, "video", "responsibilities", "REF_ID_SEQUENCE_MISMATCH",
            f"upload ids {actual_upload_ids!r} != {expected_upload_ids!r}",
        ))

    # No duplicate duties
    seen_duties = set()
    for ref_id, _ in ref_duties:
        if ref_id in seen_duties:
            diags.append(_d(case_id, "video", "responsibilities",
                           "DUTY_DUPLICATE_ID", f"duplicate duty for: {ref_id}"))
        seen_duties.add(ref_id)

    upload_targets = [target for _, target in ref_images]
    duty_ids = [ref_id for ref_id, _ in ref_duties]
    if sorted(upload_targets) != sorted(duty_ids):
        diags.append(_d(
            case_id, "video", "responsibilities", "REF_TARGET_DUTY_MISMATCH",
            f"upload targets {upload_targets!r} do not bind exactly to "
            f"duty ids {duty_ids!r}",
        ))

    # Exact set equality
    expected_pairs = set(expectation.expected_ref_duties)
    actual_pairs = set(ref_duties)

    # Missing expected pairs
    for pair in sorted(expected_pairs):
        if pair not in actual_pairs:
            diags.append(_d(case_id, "video", "responsibilities",
                           "REF_DUTY_MISSING",
                           f"expected duty pair {pair!r} not found in artifact"))

    # Unexpected extra pairs
    for pair in sorted(actual_pairs):
        if pair not in expected_pairs:
            diags.append(_d(case_id, "video", "responsibilities",
                           "REF_DUTY_UNEXPECTED",
                           f"unexpected duty pair {pair!r} not in expectation"))

    return len(diags) == 0, diags


# ── Forbidden routes (full body fingerprint + route) ──

def _validate_forbidden_routes(case_id: str, vp_parsed: Dict[str, Any],
                                expectation: CaseExpectation) -> Tuple[bool, List[Diagnostic]]:
    diags: List[Diagnostic] = []

    prohibitions = vp_parsed.get("prohibitions", [])
    route = vp_parsed.get("prohibition_route")
    expected_route = expectation.prohibition_route
    body_text = vp_parsed.get("prohibition_body_text", "")

    if "prohibitions" not in vp_parsed.get("sections", []):
        diags.append(_d(case_id, "video", "forbidden_routes",
                       "FORBIDDEN_SECTION_MISSING", "@禁止 section missing"))
        return False, diags

    if not prohibitions:
        diags.append(_d(case_id, "video", "forbidden_routes",
                       "FORBIDDEN_EMPTY", "@禁止 section has no prohibition items"))

    # Full body fingerprint check
    expected_body_fp = expectation.prohibition_body_sha256
    if expected_body_fp:
        actual_body_fp = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
        if actual_body_fp != expected_body_fp:
            diags.append(_d(case_id, "video", "forbidden_routes",
                           "FORBIDDEN_BODY_TAMPERED",
                           f"prohibition body fingerprint {actual_body_fp} != expected {expected_body_fp}"))

    # Route marker check
    if expected_route and route != expected_route:
        diags.append(_d(case_id, "video", "forbidden_routes",
                       "ROUTE_MISMATCH",
                       f"prohibition route '{route}' != expected '{expected_route}'"))
    if expected_route and route is None:
        diags.append(_d(case_id, "video", "forbidden_routes",
                       "ROUTE_MISSING", f"prohibition route missing, expected '{expected_route}'"))

    positive_body = " ".join(
        vp_parsed.get("positive_body_text", "").split()
    )
    for prohibition in prohibitions:
        normalized = " ".join(prohibition.split())
        if normalized and normalized in positive_body:
            diags.append(_d(
                case_id, "video", "forbidden_routes",
                "FORBIDDEN_TEXT_LEAKED_TO_POSITIVE_BODY",
                "a canonical prohibition item appears in positive creative text",
            ))
            break

    return len(diags) == 0, diags


# ── Homology (shared contract comparisons, not just sorted time subsets) ──

def _validate_homology(case_id: str, sb_parsed: Dict[str, Any],
                        vp_parsed: Dict[str, Any],
                        expectation: CaseExpectation) -> Tuple[bool, List[Diagnostic]]:
    diags: List[Diagnostic] = []

    sb_times = sb_parsed.get("times", [])
    vp_nodes = vp_parsed.get("timeline_nodes", [])

    if (
        expectation.expected_segment_id
        and sb_parsed.get("segment_id") != expectation.expected_segment_id
    ):
        diags.append(_d(
            case_id, "homology", "homology", "SEGMENT_ID_DIVERGE",
            f"storyboard segment {sb_parsed.get('segment_id')!r} != "
            f"{expectation.expected_segment_id!r}",
        ))

    expected_ref_groups = (
        ("character", tuple(sb_parsed.get("character_refs", [])),
         expectation.expected_sb_character_refs),
        ("scene", tuple(sb_parsed.get("scene_refs", [])),
         expectation.expected_sb_scene_refs),
        ("prop", tuple(sb_parsed.get("prop_refs", [])),
         expectation.expected_sb_prop_refs),
    )
    for ref_kind, actual_refs, expected_refs in expected_ref_groups:
        if actual_refs != expected_refs:
            diags.append(_d(
                case_id, "homology", "homology", "SB_REFERENCE_DIVERGE",
                f"{ref_kind} refs {actual_refs!r} != expected {expected_refs!r}",
            ))

    # ── Panel count check ──
    expected_sb = expectation.expected_sb_panel_count
    if expected_sb > 0 and len(sb_times) != expected_sb:
        diags.append(_d(case_id, "homology", "homology",
                       "SB_PANEL_COUNT",
                       f"SB has {len(sb_times)} panels, expected {expected_sb}"))

    expected_vp = expectation.expected_vp_timeline_count
    if expected_vp > 0:
        actual_vp = len([n for n in vp_nodes if n.get("node_type") == "panel"])
        if actual_vp != expected_vp:
            diags.append(_d(case_id, "homology", "homology",
                           "VP_PANEL_COUNT",
                           f"VP has {actual_vp} timeline panels, expected {expected_vp}"))

    sb_regular_panels = [
        panel for panel in sb_parsed.get("panels", [])
        if panel.get("node_type") == "panel"
    ]
    vp_regular_panels = [
        node for node in vp_nodes if node.get("node_type") == "panel"
    ]
    if len(sb_regular_panels) != len(vp_regular_panels):
        diags.append(_d(
            case_id, "homology", "homology", "PANEL_TOPOLOGY_COUNT_DIVERGE",
            f"{len(sb_regular_panels)} storyboard panels != "
            f"{len(vp_regular_panels)} video panels",
        ))

    panel_fields = (
        ("time", "start_time"),
        ("phase_id", "phase_id"),
        ("shot_size", "shot_size"),
        ("camera_motion", "camera_motion"),
    )
    for index, (sb_panel, vp_panel) in enumerate(
        zip(sb_regular_panels, vp_regular_panels)
    ):
        for sb_field, vp_field in panel_fields:
            if sb_panel.get(sb_field) != vp_panel.get(vp_field):
                diags.append(_d(
                    case_id, "homology", "homology",
                    "PANEL_DIRECTING_FIELD_DIVERGE",
                    f"panel {index} field {sb_field}: "
                    f"{sb_panel.get(sb_field)!r} != {vp_panel.get(vp_field)!r}",
                ))
        sb_desc = sb_panel.get("description", "").strip()
        vp_desc = vp_panel.get("description", "").strip()
        if not sb_desc or not vp_desc:
            diags.append(_d(
                case_id, "homology", "homology", "PANEL_DESCRIPTION_MISSING",
                f"panel {index} lacks a storyboard or video description",
            ))
        elif sb_desc not in vp_desc and vp_desc not in sb_desc:
            diags.append(_d(
                case_id, "homology", "homology",
                "PANEL_DESCRIPTION_DIVERGE",
                f"panel {index} storyboard/video descriptions diverge",
            ))

    expected_boundaries = {
        (float(ct), f"cut_{ct:g}s") for ct in expectation.expected_cut_times
    }
    actual_boundaries = {
        (float(node["start_time"]), str(node.get("node_id", "")))
        for node in vp_nodes
        if node.get("node_type") == "boundary"
        and node.get("start_time") is not None
    }
    if actual_boundaries != expected_boundaries:
        diags.append(_d(
            case_id, "homology", "homology", "BOUNDARY_TOPOLOGY_DIVERGE",
            f"boundaries {sorted(actual_boundaries)!r} != "
            f"{sorted(expected_boundaries)!r}",
        ))

    actual_terminal_nodes = tuple(
        (
            str(node.get("node_type")),
            float(node["start_time"]),
            float(node["end_time"]),
        )
        for node in vp_nodes
        if node.get("node_type") in {"hold", "audio", "transition"}
        and node.get("start_time") is not None
        and node.get("end_time") is not None
    )
    if actual_terminal_nodes != expectation.expected_terminal_nodes:
        diags.append(_d(
            case_id, "homology", "homology", "TERMINAL_TOPOLOGY_DIVERGE",
            f"terminal nodes {actual_terminal_nodes!r} != "
            f"{expectation.expected_terminal_nodes!r}",
        ))

    actual_transitions = tuple(vp_parsed.get("transitions", []))
    if actual_transitions != expectation.expected_transitions:
        diags.append(_d(
            case_id, "homology", "homology", "TRANSITION_DIVERGE",
            f"transitions {actual_transitions!r} != "
            f"{expectation.expected_transitions!r}",
        ))

    # ── Time topology: raw-order check for non-cut-point times ──
    # Extract the sequence of SB times that are NOT at known cut points.
    # This sequence must be strictly increasing in raw artifact order.
    # (Boundary at-nodes at cut points can appear out of order legitimately.)
    expected_cuts = set(expectation.expected_cut_times)
    sb_non_cut_times = [t for t in sb_times if t not in expected_cuts]
    for j in range(1, len(sb_non_cut_times)):
        if sb_non_cut_times[j] <= sb_non_cut_times[j-1]:
            diags.append(_d(case_id, "homology", "homology",
                           "SB_TIME_TOPOLOGY",
                           f"non-cut times not strictly increasing: {sb_non_cut_times[j]}s after {sb_non_cut_times[j-1]}s"))

    # ── Time subset check (sorted, for coverage) ──
    sb_times_sorted = sorted(sb_times)
    vp_all_times = []
    for nd in vp_nodes:
        st = nd.get("start_time")
        if st is not None:
            vp_all_times.append(st)

    vp_all_times_sorted = sorted(vp_all_times)
    vp_idx = 0
    for sb_t in sb_times_sorted:
        found = False
        while vp_idx < len(vp_all_times_sorted):
            if abs(vp_all_times_sorted[vp_idx] - sb_t) < 0.01:
                found = True
                vp_idx += 1
                break
            vp_idx += 1
        if not found:
            diags.append(_d(case_id, "homology", "homology",
                           "SB_VP_TIME_DIVERGE",
                           f"SB time {sb_t}s not found in VP timeline"))

    # ── Semantic anchor comparison ──
    # For each SB panel, verify its description text appears in at least one
    # VP node at the same time position.  If a SB description was modified
    # (tampered) and no longer matches any VP node at that time, the shared
    # contract semantics have diverged.
    sb_panels = sb_parsed.get("panels", [])
    for panel in sb_panels:
        sb_desc = panel.get("description", "").strip()
        sb_time = panel.get("time")
        if not sb_desc or sb_time is None:
            continue
        # Find VP nodes at the same time
        vp_descs_at_time = []
        for nd in vp_nodes:
            nd_time = nd.get("start_time")
            if nd_time is not None and abs(nd_time - sb_time) < 0.01:
                nd_desc = nd.get("description", "").strip()
                if nd_desc:
                    vp_descs_at_time.append(nd_desc)
        # If there are VP descriptions at this time but none match the SB
        # description, the semantic content has diverged.
        if vp_descs_at_time and not any(
            sb_desc in vd or vd in sb_desc for vd in vp_descs_at_time
        ):
            diags.append(_d(case_id, "homology", "homology",
                           "SEMANTIC_ANCHOR_DIVERGE",
                           f"SB desc at {sb_time}s ({sb_desc[:50]}...) not found in VP at same time"))

    # ── Phase order check ──
    sb_phases: List[str] = []
    for panel in sb_panels:
        header = panel.get("header", "")
        pm = re.match(r'^([①②③④⑤⑥⑦⑧⑨⑩])', header)
        if pm:
            pid = pm.group(1)
            if pid not in sb_phases:
                sb_phases.append(pid)

    vp_phases: List[str] = []
    for nd in vp_nodes:
        if nd.get("node_type") == "panel":
            pid = nd.get("phase_id", "")
            if pid and pid not in vp_phases:
                vp_phases.append(pid)

    if sb_phases and vp_phases and sb_phases != vp_phases:
        diags.append(_d(case_id, "homology", "homology",
                       "PHASE_ORDER_DIVERGE",
                       f"SB phases {sb_phases} != VP phases {vp_phases}"))

    return len(diags) == 0, diags


# ── Integrity (hash mismatches + expectation authority + known case) ──

def _validate_integrity(
    case_id: str,
    sb_artifact: str,
    vp_artifact: str,
    expectation: CaseExpectation,
) -> Tuple[bool, List[Diagnostic]]:
    diags: List[Diagnostic] = []

    # ── Known case check ──
    if expectation.case_id not in _AUTHORIZED_CASES:
        diags.append(_d(case_id, "homology", "integrity",
                       "UNKNOWN_CASE",
                       f"case_id '{expectation.case_id}' not in authorized allowlist"))

    # ── Expectation authority check ──
    expected_fp = _EXPECTATION_AUTHORITY.get(expectation.case_id)
    if expected_fp:
        actual_fp = _compute_expectation_fingerprint(expectation)
        if (
            actual_fp != expected_fp
            or expectation.expectation_fingerprint != expected_fp
        ):
            diags.append(_d(case_id, "homology", "integrity",
                           "EXPECTATION_TAMPERED",
                           f"computed/public expectation fingerprints "
                           f"{actual_fp}/{expectation.expectation_fingerprint} "
                           f"!= authority {expected_fp}"))
    elif expectation.case_id in _AUTHORIZED_CASES:
        # Authorized case has no authority fingerprint → configuration error
        diags.append(_d(case_id, "homology", "integrity",
                       "EXPECTATION_NO_AUTHORITY",
                       f"no authority fingerprint for authorized case {expectation.case_id}"))

    # ── Hash mismatch check ──
    expected_sb_hash = expectation.canonical_sb_sha256
    if expected_sb_hash:
        actual_sb_hash = hashlib.sha256(sb_artifact.encode("utf-8")).hexdigest()
        if actual_sb_hash != expected_sb_hash:
            diags.append(_d(case_id, "storyboard", "integrity",
                           "SB_HASH_MISMATCH",
                           f"SB SHA-256 {actual_sb_hash} != expected {expected_sb_hash}"))

    expected_vp_hash = expectation.canonical_vp_sha256
    if expected_vp_hash:
        actual_vp_hash = hashlib.sha256(vp_artifact.encode("utf-8")).hexdigest()
        if actual_vp_hash != expected_vp_hash:
            diags.append(_d(case_id, "video", "integrity",
                           "VP_HASH_MISMATCH",
                           f"VP SHA-256 {actual_vp_hash} != expected {expected_vp_hash}"))

    return len(diags) == 0, diags


# ============================================================================
# Public API
# ============================================================================

def run_structural_case(sb_artifact: str, vp_artifact: str,
                         expectation: CaseExpectation) -> StructuralDiagnostics:
    """Parse both artifacts and validate all 7 structural categories.

    Args:
        sb_artifact: Rendered storyboard text.
        vp_artifact: Rendered video prompt text.
        expectation: Immutable case expectation (constants only).

    Returns:
        StructuralDiagnostics with all 7 booleans computed by the runner.
        integrity_valid gates hash mismatches, expectation authority, and
        known case allowlist — any violation forces all_valid=False.
    """
    case_id = expectation.case_id
    all_diags: List[Diagnostic] = []

    # ── Integrity first (before parsing, to catch forged expectations early) ──
    int_ok, int_d = _validate_integrity(case_id, sb_artifact, vp_artifact, expectation)
    all_diags.extend(int_d)

    # ── Parse ──
    try:
        sb_parsed = _parse_storyboard(sb_artifact)
    except ValueError as e:
        return StructuralDiagnostics(
            case_id=case_id,
            format_valid=False, timing_valid=False, cuts_valid=False,
            responsibilities_valid=False, forbidden_routes_valid=False,
            homology_valid=False, integrity_valid=int_ok,
            diagnostics=(_d(case_id, "storyboard", "format",
                          "SB_PARSE_ERROR", str(e)),) + tuple(int_d),
        )

    try:
        vp_parsed = _parse_video_prompt(vp_artifact)
    except ValueError as e:
        return StructuralDiagnostics(
            case_id=case_id,
            format_valid=False, timing_valid=False, cuts_valid=False,
            responsibilities_valid=False, forbidden_routes_valid=False,
            homology_valid=False, integrity_valid=int_ok,
            diagnostics=(_d(case_id, "video", "format",
                          "VP_PARSE_ERROR", str(e)),) + tuple(int_d),
        )

    # ── Validate each category ──
    fmt_sb_ok, fmt_sb_d = _validate_sb_format(
        case_id, sb_parsed, expectation.required_sb_sections)
    fmt_vp_ok, fmt_vp_d = _validate_vp_format(
        case_id, vp_parsed, expectation.required_vp_sections)
    fmt_ok = fmt_sb_ok and fmt_vp_ok
    all_diags.extend(fmt_sb_d)
    all_diags.extend(fmt_vp_d)

    tim_ok, tim_d = _validate_timing(case_id, sb_parsed, vp_parsed, expectation)
    all_diags.extend(tim_d)

    cut_ok, cut_d = _validate_cuts(case_id, vp_parsed, expectation)
    all_diags.extend(cut_d)

    resp_ok, resp_d = _validate_responsibilities(case_id, vp_parsed, expectation)
    all_diags.extend(resp_d)

    forb_ok, forb_d = _validate_forbidden_routes(case_id, vp_parsed, expectation)
    all_diags.extend(forb_d)

    hom_ok, hom_d = _validate_homology(case_id, sb_parsed, vp_parsed, expectation)
    all_diags.extend(hom_d)

    return StructuralDiagnostics(
        case_id=case_id,
        format_valid=fmt_ok,
        timing_valid=tim_ok,
        cuts_valid=cut_ok,
        responsibilities_valid=resp_ok,
        forbidden_routes_valid=forb_ok,
        homology_valid=hom_ok,
        integrity_valid=int_ok,
        diagnostics=tuple(all_diags),
    )


def run_structural_suite(
    cases: Dict[str, Tuple[str, str, CaseExpectation]]
) -> Dict[str, StructuralDiagnostics]:
    """Run structural validation over multiple cases.

    Args:
        cases: Dict mapping case_id to (sb_artifact, vp_artifact, expectation).

    Returns:
        Dict mapping case_id to StructuralDiagnostics. Same input → same output.
    """
    return {
        case_id: run_structural_case(sb, vp, exp)
        for case_id, (sb, vp, exp) in sorted(cases.items())
    }
