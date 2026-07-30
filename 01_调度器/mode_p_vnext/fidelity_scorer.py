"""MODE:P vNext — Multi-Axis Fidelity Scorer (V8.2).

Separate scores for opening frame, path, cut points, character positions,
visibility, landing frame, and allowed optimizations. NOT collapsed into
a single similarity number.

Spec references: LOOP §13.2-§13.7.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

FIDELITY_AXES: FrozenSet[str] = frozenset({
    "opening_frame",
    "camera_path",
    "cut_points",
    "character_positions",
    "visibility",
    "landing_frame",
    "allowed_optimizations",
})


@dataclass
class FidelityScores:
    opening_frame: float
    camera_path: float
    cut_points: float
    character_positions: float
    visibility: float
    landing_frame: float
    allowed_optimizations: float

    # Explicitly NO `overall_score` or `similarity` — each axis is independent
