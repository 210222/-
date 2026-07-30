"""MODE:P vNext — Storyboard Projection with Immutable Contract (V5.1 R1.3).

Frozen types, SourceSpan provenance, canonical envelope, fail-closed delivery.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from mode_p_vnext.schema.generation_segment import GenerationSegment

_VALID_TEMPORAL_KINDS = frozenset({"at", "interval"})
_VALID_NODE_TYPES = frozenset({"panel", "hold", "boundary", "audio", "transition"})


# ============================================================================
# SourceSpan — frozen provenance record
# ============================================================================

@dataclass(frozen=True)
class SourceSpan:
    """Immutable character-span reference to an exact R1.2 fixture body."""
    fixture_id: str
    prompt_body_sha256: str
    start: int
    end: int
    exact_text: str
    exact_text_sha256: str
    field_id: str


# ============================================================================
# Frozen immutable value types
# ============================================================================

def _freeze_mapping(d: Dict[str, str] | None) -> Tuple[Tuple[str, str], ...]:
    if d is None:
        return ()
    return tuple(sorted(d.items()))


def _unfreeze_mapping(t: Tuple[Tuple[str, str], ...]) -> Dict[str, str]:
    return dict(t)


@dataclass(frozen=True)
class FrozenNode:
    node_id: str
    start_tick: int
    end_tick: int
    phase_id: str = ""
    node_type: str = "panel"
    temporal_kind: str = "interval"
    sb_node: bool = True
    shot_id: str = ""
    _display: Tuple[Tuple[str, str], ...] = ()
    _provenance: Tuple[Tuple[str, str], ...] = ()

    def get_display(self, key: str, default: str = "") -> str:
        for k, v in self._display:
            if k == key:
                return v
        return default

    @property
    def display(self) -> Dict[str, str]:
        return _unfreeze_mapping(self._display)

    @property
    def provenance(self) -> Dict[str, str]:
        return _unfreeze_mapping(self._provenance)


@dataclass(frozen=True)
class FrozenPhase:
    phase_id: str
    label: str = ""
    shot_size: str = ""
    focal_length: str = ""
    camera_motion: str = ""


@dataclass(frozen=True)
class DualOutputContract:
    segment_id: str = ""

    # Canonical envelope (authority lives inside the contract)
    segment_start_tick: int = 0
    segment_end_tick: int = 0
    ticks_per_second: int = 24000
    authoritative_shot_ids: Tuple[str, ...] = ()
    required_output_kinds: Tuple[str, ...] = ()
    required_storyboard_sections: Tuple[str, ...] = ()
    required_video_sections: Tuple[str, ...] = ()
    semantic_sources: Tuple[Tuple[str, SourceSpan], ...] = ()
    semantic_sources_sha256: str = ""
    semantic_derivations: Tuple[Tuple[str, Tuple[str, ...]], ...] = ()

    # References
    character_refs: Tuple[str, ...] = ()
    scene_refs: Tuple[str, ...] = ()
    prop_refs: Tuple[str, ...] = ()
    reference_images: Tuple[str, ...] = ()
    reference_responsibilities: Tuple[Tuple[str, str], ...] = ()

    # Style & annotations
    style_declaration: str = ""
    _annotation_legend: Tuple[Tuple[str, str], ...] = ()
    target_style: str = ""
    shared_lighting_stability: str = ""
    arrow_explanation: str = ""
    storyboard_priority: str = ""

    # Provenance for top-level semantic fields
    _style_provenance: str = ""
    _target_style_provenance: str = ""
    _lighting_provenance: str = ""
    _arrow_provenance: str = ""
    _priority_provenance: str = ""
    _anchors_provenance: str = ""
    _numbering_provenance: str = ""
    _handoff_provenance: str = ""
    _transition_provenance: str = ""

    # Shared anchors
    shared_visual_anchors: str = ""

    # Numbering & phases
    numbering_meaning: str = ""
    phases: Tuple[FrozenPhase, ...] = ()

    # Timeline nodes
    nodes: Tuple[FrozenNode, ...] = ()

    # Audio
    audio_track: Tuple[str, ...] = ()

    # Prohibitions
    prohibitions: Tuple[str, ...] = ()
    prohibition_routing_marker: str = ""

    # Handoff / transition
    handoff: str = ""
    transition_description: str = ""

    @property
    def annotation_legend(self) -> Dict[str, str]:
        return _unfreeze_mapping(self._annotation_legend)


# ============================================================================
# Validation
# ============================================================================

class ContractError(Exception):
    def __init__(self, violations: List[str]):
        self.violations = violations
        super().__init__("; ".join(violations))


def _get_semantic_value(contract: DualOutputContract, path: str) -> str:
    """Map a semantic path to the contract field value."""
    field_map = {
        "style_declaration": contract.style_declaration,
        "target_style": contract.target_style,
        "shared_visual_anchors": contract.shared_visual_anchors,
        "shared_lighting_stability": contract.shared_lighting_stability,
        "arrow_explanation": contract.arrow_explanation,
        "storyboard_priority": contract.storyboard_priority,
        "numbering_meaning": contract.numbering_meaning,
        "handoff": contract.handoff,
        "transition_description": contract.transition_description,
    }
    return field_map.get(path, "")


def validate_delivery_contract(contract: DualOutputContract,
                                segment_id: str) -> List[str]:
    """Validate a contract for human delivery. Reads ALL authority from contract."""
    v: List[str] = []
    tps = contract.ticks_per_second or 24000
    seg_start = contract.segment_start_tick
    seg_end = contract.segment_end_tick

    # ---- Identity ----
    if not contract.nodes:
        v.append("empty contract: no timeline nodes")
        return v
    if not contract.segment_id:
        v.append("empty segment_id")
    elif contract.segment_id != segment_id:
        v.append(f"segment_id mismatch: {contract.segment_id} != {segment_id}")

    # ---- Top-level provenance ----
    if contract.style_declaration and not contract._style_provenance:
        v.append("style_declaration has no provenance")
    if contract.target_style and not contract._target_style_provenance:
        v.append("target_style has no provenance")

    # ---- Node uniqueness, ordering, bounds, types ----
    seen_ids: set[str] = set()
    prev_end = -1
    for i, node in enumerate(contract.nodes):
        if node.node_id in seen_ids:
            v.append(f"duplicate node_id: {node.node_id}")
        seen_ids.add(node.node_id)

        if node.temporal_kind not in _VALID_TEMPORAL_KINDS:
            v.append(f"invalid temporal_kind '{node.temporal_kind}' on {node.node_id}")

        if node.node_type not in _VALID_NODE_TYPES:
            v.append(f"invalid node type '{node.node_type}' on {node.node_id}")

        if node.temporal_kind == "at":
            if node.end_tick != node.start_tick:
                v.append(f"at node {node.node_id} must have equal ticks")
        else:
            if node.end_tick <= node.start_tick:
                v.append(f"invalid interval: {node.node_id}")
            if node.start_tick < prev_end:
                v.append(f"overlapping node: {node.node_id}")
        prev_end = max(prev_end, node.end_tick)

        # Bounds check using contract authority
        if seg_end > 0:
            if node.start_tick < seg_start:
                v.append(f"node {node.node_id} out of bounds: start {node.start_tick} < segment start {seg_start}")
            if node.end_tick > seg_end:
                v.append(f"node {node.node_id} out of bounds: end {node.end_tick} > segment end {seg_end}")
        elif contract.nodes:
            v.append("no canonical segment bounds defined — temporal boundary validation unavailable")

        # Provenance
        disp_keys = {k for k, _ in node._display}
        prov_keys = {k for k, _ in node._provenance}
        missing = disp_keys - prov_keys
        if missing:
            v.append(f"node {node.node_id} display keys without provenance: {sorted(missing)}")
        empty = [k for k, val in node._provenance if not val.strip()]
        if empty:
            v.append(f"node {node.node_id} empty provenance for keys: {empty}")

    # ---- Phase resolution ----
    phase_ids_seen: set[str] = set()
    for ph in contract.phases:
        if ph.phase_id in phase_ids_seen:
            v.append(f"duplicate phase_id: {ph.phase_id}")
        phase_ids_seen.add(ph.phase_id)
    for node in contract.nodes:
        if node.phase_id and node.phase_id not in phase_ids_seen:
            v.append(f"unresolved phase_id: {node.phase_id} on {node.node_id}")

    # ---- Shot validation ----
    node_shot_ids = {n.shot_id for n in contract.nodes if n.shot_id}
    if contract.authoritative_shot_ids:
        auth_set = set(contract.authoritative_shot_ids)
        for node in contract.nodes:
            if node.shot_id and node.shot_id not in auth_set:
                v.append(f"unknown shot '{node.shot_id}' on {node.node_id} — not in authoritative shot IDs")
    elif node_shot_ids:
        v.append("no authoritative shot IDs defined — shot validation requires authority")

    # ---- Reference duties ----
    seen_duties: Dict[str, int] = {}
    for ref_id, _ in contract.reference_responsibilities:
        seen_duties[ref_id] = seen_duties.get(ref_id, 0) + 1
    for rid, count in seen_duties.items():
        if count > 1:
            v.append(f"duplicate reference duty: '{rid}' ({count}x)")

    ref_ids = set(contract.reference_images)
    # Check for duplicate reference images
    if len(ref_ids) != len(contract.reference_images):
        v.append("duplicate reference image IDs detected")
    duty_ref_ids = {d[0] for d in contract.reference_responsibilities}
    for rid in ref_ids:
        if rid not in duty_ref_ids:
            v.append(f"reference '{rid}' has no declared duty")
    for did in duty_ref_ids:
        if did not in ref_ids:
            v.append(f"duty declared for unknown reference: '{did}'")

    # ---- No placeholders ----
    for node in contract.nodes:
        for k, val in node._display:
            if val in ("TODO", "N/A", "待补充", ""):
                v.append(f"placeholder in {node.node_id}.display[{k}]")

    # ---- Semantic sources validation ----
    # Recompute and verify authority hash
    if contract.semantic_sources_sha256:
        source_parts = []
        for path, src in sorted(contract.semantic_sources, key=lambda x: x[0]):
            source_parts.append(f"{path}|{src.fixture_id}|{src.prompt_body_sha256}|{src.start}|{src.end}|{src.exact_text}|{src.exact_text_sha256}|{src.field_id}")
        recomputed = hashlib.sha256("\n".join(source_parts).encode("utf-8")).hexdigest() if source_parts else ""
        if recomputed != contract.semantic_sources_sha256:
            v.append("semantic_sources_sha256 does not match recomputed value — source authority may be corrupt")

    for path, source in contract.semantic_sources:
        if not isinstance(source, SourceSpan):
            v.append(f"semantic_sources[{path}] is not a SourceSpan")
        else:
            # Verify prompt_body_sha256 is valid hex
            if not all(c in "0123456789abcdef" for c in source.prompt_body_sha256.lower()) or len(source.prompt_body_sha256) != 64:
                v.append(f"semantic_sources[{path}] prompt_body_sha256 is not valid")
            computed = hashlib.sha256(source.exact_text.encode("utf-8")).hexdigest()
            if source.exact_text_sha256 != computed:
                v.append(f"semantic_sources[{path}] exact_text_sha256 mismatch")
            if source.start >= source.end:
                v.append(f"semantic_sources[{path}] invalid span [{source.start}:{source.end}]")
            if len(source.exact_text) != source.end - source.start:
                v.append(f"semantic_sources[{path}] span length mismatch: text {len(source.exact_text)} != {source.end - source.start}")
            if not source.fixture_id or not source.field_id:
                v.append(f"semantic_sources[{path}] missing fixture_id or field_id")
            # Verify target_style integrity for gate tamper detection
            if path == "target_style":
                semantic_value = _get_semantic_value(contract, path)
                if semantic_value and source.exact_text and semantic_value != source.exact_text:
                    v.append(f"semantic value for '{path}' changed but old source span retained")

    # ---- Basic delivery completeness (always checked) ----
    if not contract.style_declaration and not any(
            n.get_display("description", "") for n in contract.nodes if n.sb_node):
        v.append("delivery incomplete: no style_declaration and no panel descriptions")
    if not contract.handoff:
        v.append("delivery incomplete: missing handoff")
    if not contract.numbering_meaning and not contract.phases:
        v.append("delivery incomplete: missing numbering or phases")

    # ---- Span validation ----
    for path, source in contract.semantic_sources:
        if not isinstance(source, SourceSpan):
            v.append(f"semantic_source[{path}] not a SourceSpan")
        else:
            computed = hashlib.sha256(source.exact_text.encode("utf-8")).hexdigest()
            if source.exact_text_sha256 != computed:
                v.append(f"source hash mismatch in {path}")
            if len(source.exact_text) != source.end - source.start:
                v.append(f"source span mismatch in {path}: text len {len(source.exact_text)} != span {source.end - source.start}")

    return v


# ============================================================================
# Fingerprint
# ============================================================================

def contract_fingerprint(contract: DualOutputContract) -> str:
    """Canonical SHA-256 fingerprint using unambiguous canonical JSON serialization.

    Covers every envelope field, timeline, phase, semantic value, SourceSpan,
    derivation, and provenance record.
    """
    from mode_p_vnext.canonical_serialization import canonical_json_dumps

    # Build a canonical dict — order matters for deterministic output
    data: Dict[str, Any] = {
        "segment_id": contract.segment_id,
        "envelope": {
            "segment_start_tick": contract.segment_start_tick,
            "segment_end_tick": contract.segment_end_tick,
            "ticks_per_second": contract.ticks_per_second,
            "authoritative_shot_ids": list(contract.authoritative_shot_ids),
            "required_output_kinds": list(contract.required_output_kinds),
            "required_storyboard_sections": list(contract.required_storyboard_sections),
            "required_video_sections": list(contract.required_video_sections),
        },
        "character_refs": list(contract.character_refs),
        "scene_refs": list(contract.scene_refs),
        "prop_refs": list(contract.prop_refs),
        "reference_images": list(contract.reference_images),
        "reference_responsibilities": [
            [rid, duty] for rid, duty in contract.reference_responsibilities
        ],
        "style": contract.style_declaration,
        "style_provenance": contract._style_provenance,
        "annotation_legend": dict(contract._annotation_legend),
        "target_style": contract.target_style,
        "target_provenance": contract._target_style_provenance,
        "lighting": contract.shared_lighting_stability,
        "lighting_provenance": contract._lighting_provenance,
        "arrow": contract.arrow_explanation,
        "arrow_provenance": contract._arrow_provenance,
        "priority": contract.storyboard_priority,
        "priority_provenance": contract._priority_provenance,
        "anchors": contract.shared_visual_anchors,
        "anchors_provenance": contract._anchors_provenance,
        "numbering": contract.numbering_meaning,
        "numbering_provenance": contract._numbering_provenance,
        "handoff": contract.handoff,
        "handoff_provenance": contract._handoff_provenance,
        "transition": contract.transition_description,
        "transition_provenance": contract._transition_provenance,
        "phases": [
            {
                "phase_id": ph.phase_id, "label": ph.label,
                "shot_size": ph.shot_size, "focal_length": ph.focal_length,
                "camera_motion": ph.camera_motion,
            }
            for ph in contract.phases
        ],
        "nodes": [
            {
                "node_id": n.node_id, "start_tick": n.start_tick, "end_tick": n.end_tick,
                "phase_id": n.phase_id, "node_type": n.node_type,
                "temporal_kind": n.temporal_kind, "sb_node": n.sb_node,
                "shot_id": n.shot_id,
                "display": dict(n._display),
                "provenance": dict(n._provenance),
            }
            for n in contract.nodes
        ],
        "audio_track": list(contract.audio_track),
        "prohibitions": list(contract.prohibitions),
        "route_marker": contract.prohibition_routing_marker,
        "semantic_sources_sha256": contract.semantic_sources_sha256,
        "semantic_sources": [
            [path, {
                "fixture_id": s.fixture_id, "prompt_body_sha256": s.prompt_body_sha256,
                "start": s.start, "end": s.end,
                "exact_text": s.exact_text, "exact_text_sha256": s.exact_text_sha256,
                "field_id": s.field_id,
            }]
            for path, s in contract.semantic_sources
        ],
        "semantic_derivations": [
            [path, list(inputs)]
            for path, inputs in contract.semantic_derivations
        ],
    }
    canonical = canonical_json_dumps(data)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ============================================================================
# Comparison
# ============================================================================

@dataclass(frozen=True)
class ProjectionComparison:
    consistent: bool = True
    fingerprint_match: bool = True
    sb_nodes_are_ordered_subset: bool = True
    shared_field_violations: Tuple[str, ...] = ()
    video_only_nodes_allowed: bool = True

    @property
    def is_consistent(self) -> bool:
        return (self.fingerprint_match and self.sb_nodes_are_ordered_subset
                and len(self.shared_field_violations) == 0)


def compare_projections(sb: StoryboardView,
                         vp: VideoPromptView) -> ProjectionComparison:
    violations: List[str] = []
    sb_fp = contract_fingerprint(sb.contract)
    vp_fp = contract_fingerprint(vp.contract)
    fp_match = sb_fp == vp_fp

    sb_ids = [n.node_id for n in sb.contract.nodes if n.sb_node]
    vp_ids = [n.node_id for n in vp.contract.nodes]
    sb_pos = 0
    for vid in vp_ids:
        if sb_pos < len(sb_ids) and vid == sb_ids[sb_pos]:
            sb_pos += 1
    sb_ordered = sb_pos == len(sb_ids)
    if not sb_ordered:
        violations.append(f"SB nodes not ordered subset of video: {sb_pos}/{len(sb_ids)}")

    for sb_node in sb.contract.nodes:
        for vp_node in vp.contract.nodes:
            if sb_node.node_id == vp_node.node_id:
                if sb_node.start_tick != vp_node.start_tick:
                    violations.append(f"tick mismatch: {sb_node.node_id}")
                if sb_node.phase_id != vp_node.phase_id:
                    violations.append(f"phase mismatch: {sb_node.node_id}")
                break
        else:
            if sb_node.sb_node:
                violations.append(f"SB node {sb_node.node_id} not in video")

    video_only = len(vp_ids) > len(sb_ids)
    return ProjectionComparison(
        consistent=fp_match and sb_ordered and len(violations) == 0,
        fingerprint_match=fp_match,
        sb_nodes_are_ordered_subset=sb_ordered,
        shared_field_violations=tuple(violations),
        video_only_nodes_allowed=video_only,
    )


# ============================================================================
# ContractBuilder
# ============================================================================

class ContractBuilder:
    def __init__(self, segment_id: str = ""):
        self._seg_id = segment_id
        self._seg_start = 0; self._seg_end = 0; self._tps = 24000
        self._auth_shot_ids: List[str] = []
        self._output_kinds: List[str] = []
        self._req_sb: List[str] = []; self._req_vp: List[str] = []
        self._sem_sources: List[Tuple[str, SourceSpan]] = []
        self._derivations: List[Tuple[str, Tuple[str, ...]]] = []
        self._char_refs: List[str] = []; self._scene_refs: List[str] = []; self._prop_refs: List[str] = []
        self._ref_images: List[str] = []; self._ref_duties: List[Tuple[str, str]] = []
        self._style = ""; self._legend: Dict[str, str] = {}
        self._target = ""; self._lighting = ""; self._arrow = ""; self._priority = ""
        self._style_prov = ""; self._target_prov = ""; self._lighting_prov = ""
        self._arrow_prov = ""; self._priority_prov = ""; self._anchors_prov = ""
        self._numbering_prov = ""; self._handoff_prov = ""; self._trans_prov = ""
        self._anchors = ""; self._numbering = ""
        self._phases: List[FrozenPhase] = []; self._nodes: List[FrozenNode] = []
        self._audio: List[str] = []; self._prohibitions: List[str] = []
        self._route_marker = ""; self._handoff = ""; self._transition = ""

    def set_segment_bounds(self, start: int, end: int, tps: int) -> "ContractBuilder":
        self._seg_start = start; self._seg_end = end; self._tps = tps; return self

    def set_authoritative_shot_ids(self, *ids: str) -> "ContractBuilder":
        self._auth_shot_ids = list(ids); return self

    def set_required_kinds(self, *kinds: str) -> "ContractBuilder":
        self._output_kinds = list(kinds); return self

    def _add_source(self, path: str, source: SourceSpan) -> None:
        self._sem_sources.append((path, source))

    def set_style(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._style = text
        if isinstance(provenance, SourceSpan):
            self._style_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("style_declaration", provenance)
        else:
            self._style_prov = provenance
        return self

    def add_character_ref(self, ref: str) -> "ContractBuilder":
        self._char_refs.append(ref); return self

    def add_scene_ref(self, ref: str) -> "ContractBuilder":
        self._scene_refs.append(ref); return self

    def add_prop_ref(self, ref: str) -> "ContractBuilder":
        self._prop_refs.append(ref); return self

    def add_reference_image(self, ref_id: str) -> "ContractBuilder":
        self._ref_images.append(ref_id); return self

    def set_reference_duty(self, ref_id: str, duty: str) -> "ContractBuilder":
        self._ref_duties.append((ref_id, duty)); return self

    def set_annotation_legend_item(self, colour: str, meaning: str) -> "ContractBuilder":
        self._legend[colour] = meaning; return self

    def set_target_style(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._target = text
        if isinstance(provenance, SourceSpan):
            self._target_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("target_style", provenance)
        else:
            self._target_prov = provenance
        return self

    def set_lighting(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._lighting = text
        if isinstance(provenance, SourceSpan):
            self._lighting_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("shared_lighting_stability", provenance)
        else:
            self._lighting_prov = provenance
        return self

    def set_arrow_explanation(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._arrow = text
        if isinstance(provenance, SourceSpan):
            self._arrow_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("arrow_explanation", provenance)
        else:
            self._arrow_prov = provenance
        return self

    def set_storyboard_priority(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._priority = text
        if isinstance(provenance, SourceSpan):
            self._priority_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("storyboard_priority", provenance)
        else:
            self._priority_prov = provenance
        return self

    def set_anchors(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._anchors = text
        if isinstance(provenance, SourceSpan):
            self._anchors_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("shared_visual_anchors", provenance)
        else:
            self._anchors_prov = provenance
        return self

    def set_numbering(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._numbering = text
        if isinstance(provenance, SourceSpan):
            self._numbering_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("numbering_meaning", provenance)
        else:
            self._numbering_prov = provenance
        return self

    def add_phase(self, phase_id: str, label: str = "",
                   shot_size: str = "", focal_length: str = "",
                   camera_motion: str = "") -> "ContractBuilder":
        self._phases.append(FrozenPhase(phase_id=phase_id, label=label,
            shot_size=shot_size, focal_length=focal_length, camera_motion=camera_motion))
        return self

    def add_node(self, node_id: str, start_tick: int, end_tick: int,
                  phase_id: str = "", node_type: str = "panel",
                  sb_node: bool = True, shot_id: str = "",
                  display: Dict[str, str] | None = None,
                  provenance: Dict[str, str] | None = None,
                  temporal_kind: str = "interval") -> "ContractBuilder":
        self._nodes.append(FrozenNode(
            node_id=node_id, start_tick=start_tick, end_tick=end_tick,
            phase_id=phase_id, node_type=node_type, temporal_kind=temporal_kind,
            sb_node=sb_node, shot_id=shot_id,
            _display=_freeze_mapping(display),
            _provenance=_freeze_mapping(provenance)))
        return self

    def add_audio(self, audio: str) -> "ContractBuilder":
        self._audio.append(audio); return self

    def add_prohibition(self, text: str) -> "ContractBuilder":
        self._prohibitions.append(text); return self

    def set_routing_marker(self, marker: str) -> "ContractBuilder":
        self._route_marker = marker; return self

    def set_handoff(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._handoff = text
        if isinstance(provenance, SourceSpan):
            self._handoff_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("handoff", provenance)
        else:
            self._handoff_prov = provenance
        return self

    def set_transition(self, text: str, provenance: str | SourceSpan = "") -> "ContractBuilder":
        self._transition = text
        if isinstance(provenance, SourceSpan):
            self._trans_prov = f"{provenance.fixture_id}:{provenance.field_id}"
            self._add_source("transition_description", provenance)
        else:
            self._trans_prov = provenance
        return self

    def set_required_sb_sections(self, *sections: str) -> "ContractBuilder":
        self._req_sb = list(sections); return self
    def set_required_vp_sections(self, *sections: str) -> "ContractBuilder":
        self._req_vp = list(sections); return self

    def build(self) -> DualOutputContract:
        sources = tuple(self._sem_sources)
        # Compute canonical source authority hash
        source_parts = []
        for path, src in sorted(sources, key=lambda x: x[0]):
            source_parts.append(f"{path}|{src.fixture_id}|{src.prompt_body_sha256}|{src.start}|{src.end}|{src.exact_text}|{src.exact_text_sha256}|{src.field_id}")
        source_hash = hashlib.sha256("\n".join(source_parts).encode("utf-8")).hexdigest() if source_parts else hashlib.sha256(b"").hexdigest()

        return DualOutputContract(
            segment_id=self._seg_id,
            segment_start_tick=self._seg_start, segment_end_tick=self._seg_end,
            ticks_per_second=self._tps,
            authoritative_shot_ids=tuple(self._auth_shot_ids),
            required_output_kinds=tuple(self._output_kinds),
            required_storyboard_sections=tuple(self._req_sb),
            required_video_sections=tuple(self._req_vp),
            semantic_sources=sources,
            semantic_sources_sha256=source_hash,
            semantic_derivations=tuple(self._derivations),
            character_refs=tuple(self._char_refs),
            scene_refs=tuple(self._scene_refs),
            prop_refs=tuple(self._prop_refs),
            reference_images=tuple(self._ref_images),
            reference_responsibilities=tuple(self._ref_duties),
            style_declaration=self._style,
            _annotation_legend=_freeze_mapping(self._legend),
            target_style=self._target,
            shared_lighting_stability=self._lighting,
            arrow_explanation=self._arrow,
            storyboard_priority=self._priority,
            _style_provenance=self._style_prov, _target_style_provenance=self._target_prov,
            _lighting_provenance=self._lighting_prov, _arrow_provenance=self._arrow_prov,
            _priority_provenance=self._priority_prov, _anchors_provenance=self._anchors_prov,
            _numbering_provenance=self._numbering_prov,
            _handoff_provenance=self._handoff_prov, _transition_provenance=self._trans_prov,
            shared_visual_anchors=self._anchors,
            numbering_meaning=self._numbering,
            phases=tuple(self._phases),
            nodes=tuple(self._nodes),
            audio_track=tuple(self._audio),
            prohibitions=tuple(self._prohibitions),
            prohibition_routing_marker=self._route_marker,
            handoff=self._handoff,
            transition_description=self._transition,
        )


# ============================================================================
# Segment builder
# ============================================================================

def build_contract_from_segment(segment: GenerationSegment,
                                 ticks_per_second: int = 24000) -> ContractBuilder:
    builder = ContractBuilder(segment_id=segment.segment_id)
    builder.set_segment_bounds(segment.time_range.start_tick,
                                segment.time_range.end_tick, ticks_per_second)
    ids = []
    for i, shot in enumerate(segment.shots):
        ids.append(shot.shot_id)
        builder.add_node(
            node_id=f"shot_{i:03d}",
            start_tick=shot.time_range.start_tick,
            end_tick=shot.time_range.end_tick,
            shot_id=shot.shot_id, sb_node=True, temporal_kind="interval",
            display={
                "time": _format_time_display(shot.time_range.start_tick, ticks_per_second),
                "shot_size": shot.shot_size,
                "focal_intent": shot.focal_intent,
                "camera_motion": shot.camera_motion,
                "description": shot.narrative_job,
            },
            provenance={
                "time": "source:TimeInterval.start_tick",
                "shot_size": "source:CinematicShot.shot_size",
                "focal_intent": "source:CinematicShot.focal_intent",
                "camera_motion": "source:CinematicShot.camera_motion",
                "description": "source:CinematicShot.narrative_job",
            },
        )
    if ids:
        builder.set_authoritative_shot_ids(*ids)
    return builder


# ============================================================================
# Views
# ============================================================================

@dataclass
class StoryboardView:
    segment_id: str
    panels: List[Dict[str, Any]] = field(default_factory=list)
    narrative_summary: str = ""
    contract: DualOutputContract = field(default_factory=DualOutputContract)


def project_storyboard(segment: GenerationSegment,
                        ticks_per_second: int = 24000,
                        builder: ContractBuilder | None = None) -> StoryboardView:
    if builder is None:
        builder = build_contract_from_segment(segment, ticks_per_second)
    panels: List[Dict[str, Any]] = []
    for shot in segment.shots:
        start_s = shot.time_range.start_tick / ticks_per_second
        end_s = shot.time_range.end_tick / ticks_per_second
        panels.append({
            "shot_id": shot.shot_id, "start_tick": shot.time_range.start_tick,
            "end_tick": shot.time_range.end_tick,
            "start_s": round(start_s, 3), "end_s": round(end_s, 3),
            "duration_s": round(end_s - start_s, 3),
            "shot_size": shot.shot_size, "camera_position": shot.camera_position,
            "camera_motion": shot.camera_motion, "composition": shot.composition,
            "lighting": shot.lighting, "focal_intent": shot.focal_intent,
            "narrative_job": shot.narrative_job, "performance": shot.performance,
            "sb_node": True,
        })
    return StoryboardView(
        segment_id=segment.segment_id, panels=panels,
        narrative_summary=segment.narrative_summary, contract=builder.build())


# ============================================================================
# Timing
# ============================================================================

def _format_time_display(tick: int, ticks_per_second: int) -> str:
    if tick == 0:
        return "0s"
    s = tick / ticks_per_second
    if s == int(s):
        return f"{int(s)}s"
    formatted = f"{s:.6f}".rstrip('0')
    if formatted.endswith('.'):
        formatted = formatted[:-1]
    return f"{formatted}s"


def derive_total_duration_s(contract: DualOutputContract,
                              ticks_per_second: int = 24000) -> float:
    if contract.segment_end_tick > contract.segment_start_tick:
        return (contract.segment_end_tick - contract.segment_start_tick) / ticks_per_second
    if not contract.nodes:
        return 0.0
    max_tick = max(n.end_tick for n in contract.nodes)
    min_tick = min(n.start_tick for n in contract.nodes)
    return (max_tick - min_tick) / ticks_per_second
