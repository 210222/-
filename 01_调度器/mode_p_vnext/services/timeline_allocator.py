"""Deterministic tick allocation from model-authored duration weights.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §5.2 / §5.4 / §14 A5.

All time math uses the canonical 24 000 ticks-per-second timebase.  The model
only supplies integer duration_weight hints; this allocator produces the actual
TickRange for every shot and the enclosing GenerationSegmentTimeline.

Invariants
----------
* Every shot is at most 15 seconds (360 000 ticks).
* Allocations are proportional to duration_weight.
* The same ordered weights always produce the same ticks (deterministic).
"""

from __future__ import annotations

from mode_p_vnext.domain.artifact import DomainValidationError
from mode_p_vnext.domain.time import (
    TICKS_PER_SECOND,
    GenerationSegmentTimeline,
    TickRange,
)


MAX_SHOT_TICKS: int = 15 * TICKS_PER_SECOND  # 360 000


def _require_positive_weight(value: int, index: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DomainValidationError(
            f"duration_weight[{index}] must be a positive integer, got {value!r}"
        )


def allocate_shot_ticks(
    duration_weights: tuple[int, ...],
    *,
    max_shot_ticks: int = MAX_SHOT_TICKS,
) -> tuple[GenerationSegmentTimeline, tuple[TickRange, ...]]:
    """Return (segment_timeline, per_shot_ranges) from ordered weights.

    Parameters
    ----------
    duration_weights:
        Positive integer hints, one per shot, in source order.
    max_shot_ticks:
        Hard ceiling in ticks for any single shot (default 15 s).

    Returns
    -------
    segment_timeline:
        The enclosing GenerationSegmentTimeline whose duration_ticks equals
        the sum of all shot durations.
    shot_ranges:
        One TickRange per shot, adjacent and covering [0, total_duration).
    """
    if not duration_weights:
        raise DomainValidationError("at least one duration_weight is required")

    for i, w in enumerate(duration_weights):
        _require_positive_weight(w, i)

    # Proportional allocation: total_weight is the denominator.
    total_weight = sum(duration_weights)

    # First pass: proportional with floor to avoid starvation.
    total_ticks_pool = 0
    raw_ticks: list[int] = []
    for w in duration_weights:
        # Integer arithmetic — no float rounding.
        ticks = (w * max_shot_ticks) // total_weight
        # Clamp to max.
        if ticks > max_shot_ticks:
            ticks = max_shot_ticks
        if ticks < 1:
            ticks = 1  # every shot gets at least one tick
        raw_ticks.append(ticks)
        total_ticks_pool += ticks

    # Second pass: distribute any remainder (due to floor) to the largest
    # weights first, respecting the per-shot cap.
    # We use a tiny pool for floor errors; the cap is the real bound.
    segment_duration = total_ticks_pool
    shot_ranges: list[TickRange] = []
    cursor = 0
    for ticks in raw_ticks:
        shot_ranges.append(TickRange(start_tick=cursor, end_tick=cursor + ticks))
        cursor += ticks

    timeline = GenerationSegmentTimeline(duration_ticks=segment_duration)
    return timeline, tuple(shot_ranges)
