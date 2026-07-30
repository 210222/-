"""MODE:P vNext — v4/vNext Comparison Report (V10.2).

Multi-axis comparison of structure, timing, cuts, visibility, knowledge
usage, and format. Explicitly NO single text-similarity score.

Spec references: LOOP §13, §27.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, List

COMPARISON_AXES: FrozenSet[str] = frozenset({
    "structure",
    "timing",
    "cuts",
    "visibility",
    "knowledge_usage",
    "format",
})


@dataclass
class ComparisonReport:
    report_id: str
    structure_match: bool
    timing_match: bool
    cuts_match: bool
    visibility_match: bool
    knowledge_usage_diff: List[str] = field(default_factory=list)
    format_match: bool = True

    # Explicitly NO similarity_score or overall_match — multi-axis only
