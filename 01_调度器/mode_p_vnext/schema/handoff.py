"""MODE:P vNext — Structured Handoff Contract (V1.6).

Defines Entry/Exit/Handoff states per shot and segment, with deterministic
adjacent-conflict checking.  The Director authors creative handoff intent;
the algorithm validates continuity — it never designs transitions.

Spec references: LOOP §7.10a; Omission P0-10.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# HandoffState
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HandoffState:
    """The state of a shot at its entry or exit boundary.

    All fields are optional — an empty state means \"no specific handoff
    constraints declared.\" The Director populates what matters; the
    algorithm only checks consistency across populated fields.
    """

    character_positions: Dict[str, str] = field(default_factory=dict)
    character_gaze: Dict[str, str] = field(default_factory=dict)
    action_phase: str = ""
    prop_ownership: Dict[str, str] = field(default_factory=dict)
    prop_state: Dict[str, str] = field(default_factory=dict)
    camera_side: str = ""
    camera_motion_phase: str = ""
    focus_target: str = ""
    key_light_direction: str = ""
    key_light_continuity: str = ""
    visible_surfaces: List[str] = field(default_factory=list)
    visibility_state_id: str = ""
    audio_continuity: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.character_positions:
            d["character_positions"] = dict(self.character_positions)
        if self.character_gaze:
            d["character_gaze"] = dict(self.character_gaze)
        if self.action_phase:
            d["action_phase"] = self.action_phase
        if self.prop_ownership:
            d["prop_ownership"] = dict(self.prop_ownership)
        if self.prop_state:
            d["prop_state"] = dict(self.prop_state)
        if self.camera_side:
            d["camera_side"] = self.camera_side
        if self.camera_motion_phase:
            d["camera_motion_phase"] = self.camera_motion_phase
        if self.focus_target:
            d["focus_target"] = self.focus_target
        if self.key_light_direction:
            d["key_light_direction"] = self.key_light_direction
        if self.key_light_continuity:
            d["key_light_continuity"] = self.key_light_continuity
        if self.visible_surfaces:
            d["visible_surfaces"] = list(self.visible_surfaces)
        if self.visibility_state_id:
            d["visibility_state_id"] = self.visibility_state_id
        if self.audio_continuity:
            d["audio_continuity"] = self.audio_continuity
        return d


# ---------------------------------------------------------------------------
# ShotHandoff
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShotHandoff:
    """Wraps entry and exit handoff states for a single shot."""

    shot_id: str
    entry_state: HandoffState = field(default_factory=HandoffState)
    exit_state: HandoffState = field(default_factory=HandoffState)


# ---------------------------------------------------------------------------
# SegmentHandoff
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SegmentHandoff:
    """Complete handoff contract for a generation segment."""

    segment_id: str
    shot_handoffs: List[ShotHandoff] = field(default_factory=list)
    final_handoff: HandoffState = field(default_factory=HandoffState)


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class HandoffValidationResult:
    """Result of segment handoff validation."""

    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_consistent(self) -> bool:
        return len(self.conflicts) == 0


# ---------------------------------------------------------------------------
# Adjacent conflict check
# ---------------------------------------------------------------------------

def check_adjacent_handoff_conflicts(
    prev: ShotHandoff,
    next: ShotHandoff,
) -> List[str]:
    """Return conflicts between prev.exit_state and next.entry_state.

    A conflict is a populated field that has different values on both sides.
    Empty strings / empty dicts are treated as \"not constrained\" and do
    not conflict.
    """
    conflicts: List[str] = []
    prev_exit = prev.exit_state
    next_entry = next.entry_state

    # Character positions: compare per-character
    for char_id in set(prev_exit.character_positions) & set(next_entry.character_positions):
        pv = prev_exit.character_positions[char_id]
        nv = next_entry.character_positions[char_id]
        if pv and nv and pv != nv:
            conflicts.append(
                f"{prev.shot_id}→{next.shot_id}: character '{char_id}' "
                f"position exit='{pv}' vs entry='{nv}'"
            )

    # Character gaze: compare per-character
    for char_id in set(prev_exit.character_gaze) & set(next_entry.character_gaze):
        pv = prev_exit.character_gaze[char_id]
        nv = next_entry.character_gaze[char_id]
        if pv and nv and pv != nv:
            conflicts.append(
                f"{prev.shot_id}→{next.shot_id}: character '{char_id}' "
                f"gaze exit='{pv}' vs entry='{nv}'"
            )

    # Scalar fields: conflict only if BOTH sides are populated and differ
    _scalar_conflict(conflicts, prev, next, "camera_side",
                     lambda s: s.camera_side)
    _scalar_conflict(conflicts, prev, next, "focus_target",
                     lambda s: s.focus_target)
    _scalar_conflict(conflicts, prev, next, "key_light_direction",
                     lambda s: s.key_light_direction)
    _scalar_conflict(conflicts, prev, next, "visibility_state_id",
                     lambda s: s.visibility_state_id)

    return conflicts


def _scalar_conflict(
    conflicts: List[str],
    prev: ShotHandoff,
    next: ShotHandoff,
    field_name: str,
    getter,
) -> None:
    pv = getter(prev.exit_state)
    nv = getter(next.entry_state)
    if pv and nv and pv != nv:
        conflicts.append(
            f"{prev.shot_id}→{next.shot_id}: {field_name} "
            f"exit='{pv}' vs entry='{nv}'"
        )


# ---------------------------------------------------------------------------
# Completeness check
# ---------------------------------------------------------------------------

def check_handoff_completeness(
    shot_handoffs: Sequence[ShotHandoff],
) -> List[str]:
    """Return warnings about potentially incomplete handoff declarations.

    Warns when a shot's entry state is empty but the previous shot's exit
    state had constraints defined (potential information loss).
    """
    warnings: List[str] = []
    for i in range(1, len(shot_handoffs)):
        prev_exit = shot_handoffs[i - 1].exit_state
        cur_entry = shot_handoffs[i].entry_state
        prev_has_info = _state_has_any_field(prev_exit)
        cur_has_info = _state_has_any_field(cur_entry)
        if prev_has_info and not cur_has_info:
            warnings.append(
                f"{shot_handoffs[i].shot_id}: entry_state is empty but "
                f"{shot_handoffs[i - 1].shot_id}.exit_state has constraints"
            )
    return warnings


def _state_has_any_field(s: HandoffState) -> bool:
    """Return True if any field in the state is populated."""
    return bool(
        s.character_positions
        or s.character_gaze
        or s.action_phase
        or s.prop_ownership
        or s.prop_state
        or s.camera_side
        or s.camera_motion_phase
        or s.focus_target
        or s.key_light_direction
        or s.key_light_continuity
        or s.visible_surfaces
        or s.visibility_state_id
        or s.audio_continuity
    )


# ---------------------------------------------------------------------------
# Full segment validation
# ---------------------------------------------------------------------------

def validate_segment_handoff(seg: SegmentHandoff) -> HandoffValidationResult:
    """Run all handoff checks on a segment and return the result."""
    result = HandoffValidationResult()

    for i in range(1, len(seg.shot_handoffs)):
        conflicts = check_adjacent_handoff_conflicts(
            seg.shot_handoffs[i - 1],
            seg.shot_handoffs[i],
        )
        result.conflicts.extend(conflicts)

    result.warnings.extend(check_handoff_completeness(seg.shot_handoffs))

    return result
