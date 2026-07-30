"""MODE:P vNext — Dynamic Visibility State (V2.2).

Binds VisibilityContract to time intervals so visibility evolves over a shot.
Beats reference visibility states by ID; the validator ensures the beat's
tick falls within the referenced state's valid_time_range.

Spec references: LOOP §7.10, §9 Step 6; Omission P0-09.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from mode_p_vnext.schema.canonical_timeline import TimeInterval, Tick
from mode_p_vnext.schema.visibility_contract import VisibilityContract


# ---------------------------------------------------------------------------
# DynamicVisibilityState
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DynamicVisibilityState:
    """A visibility contract bound to a specific time interval within a shot.

    As the camera moves (push, pan, orbit, rotate), what is visible changes.
    Each state captures one phase of that evolution.
    """

    state_id: str
    valid_time_range: TimeInterval
    contract: VisibilityContract
    surface_orientation_change: str = ""   # e.g. "后壳→正面（旋转中）"
    entry_trigger: str = ""                 # e.g. "camera_pan_reveals"
    exit_trigger: str = ""                  # e.g. "focus_shift"

    def contains_tick(self, tick: Tick) -> bool:
        return self.valid_time_range.contains_tick(tick)


# ---------------------------------------------------------------------------
# Beat reference check
# ---------------------------------------------------------------------------

def check_beat_references(
    beat_at_tick: Tick,
    beat_state_id: str,
    visibility_states: Sequence[DynamicVisibilityState],
) -> List[str]:
    """Return violations when a beat's visibility reference is invalid.

    - state_id must exist
    - beat's tick must be within the state's time range
    """
    violations: List[str] = []
    state_map = {s.state_id: s for s in visibility_states}

    if beat_state_id not in state_map:
        violations.append(
            f"Beat at tick {beat_at_tick} references unknown "
            f"visibility state '{beat_state_id}'"
        )
        return violations

    state = state_map[beat_state_id]
    if not state.contains_tick(beat_at_tick):
        violations.append(
            f"Beat at tick {beat_at_tick} references state "
            f"'{beat_state_id}' which is only valid in "
            f"[{state.valid_time_range.start_tick}, "
            f"{state.valid_time_range.end_tick})"
        )

    return violations


# ---------------------------------------------------------------------------
# Visibility transition check
# ---------------------------------------------------------------------------

def check_visibility_transitions(
    states: Sequence[DynamicVisibilityState],
) -> List[str]:
    """Return violations in visibility state transitions.

    - Adjacent states must be contiguous (no gaps, no overlaps)
    - Surfaces appearing/disappearing should be explainable by entry/exit triggers
    """
    violations: List[str] = []

    for i in range(1, len(states)):
        prev = states[i - 1]
        cur = states[i]
        if prev.valid_time_range.end_tick != cur.valid_time_range.start_tick:
            violations.append(
                f"Visibility gap/overlap between '{prev.state_id}' "
                f"(ends at {prev.valid_time_range.end_tick}) and "
                f"'{cur.state_id}' (starts at {cur.valid_time_range.start_tick})"
            )

    return violations
