"""MODE:P vNext — Generation Segment / Cinematic Shot / Beat Schema (V4.2).

Generation Segment wraps one or more Cinematic Shots. The segment is the
generation unit; shots are the cinematic language units within it.

Spec references: LOOP §7, §8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from mode_p_vnext.schema.canonical_timeline import TimeInterval


# ---------------------------------------------------------------------------
# CinematicShot
# ---------------------------------------------------------------------------

@dataclass
class CinematicShot:
    """One shot within a generation segment — NOT a separate generation file."""

    shot_id: str
    segment_id: str
    time_range: TimeInterval
    narrative_job: str
    camera_position: str
    shot_size: str            # WS, FS, MS, MCU, CU, ECU, INSERT
    focal_intent: str
    camera_motion: str
    composition: str
    lighting: str
    performance: str
    fact_ids: List[str] = field(default_factory=list)
    visibility_state_id: str = ""
    entry_state_id: str = ""
    exit_state_id: str = ""


# ---------------------------------------------------------------------------
# GenerationSegment
# ---------------------------------------------------------------------------

@dataclass
class GenerationSegment:
    """A generation segment — the unit of model invocation.

    One segment produces one video generation call. It may contain multiple
    CinematicShots that the model executes as internal cuts.
    """

    segment_id: str
    time_range: TimeInterval
    shots: List[CinematicShot] = field(default_factory=list)
    scene_id: str = ""
    narrative_summary: str = ""
    fact_bindings: List[str] = field(default_factory=list)
    final_handoff_state_id: str = ""
    knowledge_snapshot_id: str = ""
