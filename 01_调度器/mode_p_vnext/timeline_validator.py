"""MODE:P vNext — Timeline Validator / Compiler (V1.2).

Deterministic checks and display-time compilation for the Canonical Timeline:
- Monotonic: intervals don't go backwards
- Contiguous: no gaps between adjacent intervals
- Total duration: segments sum to the timeline total
- Containment: Shots within Segments, Beats within Shots
- Out-of-bounds: no tick exceeds timeline scope
- Stable display times: derived from ticks, never stored as machine facts

Spec references: LOOP §7.2a, §12.8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from mode_p_vnext.schema.canonical_timeline import (
    CanonicalTimeline,
    TimeInterval,
    Tick,
)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """The result of a timeline validation pass."""

    violations: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    def __str__(self) -> str:
        if self.is_valid:
            return "ValidationResult: VALID — no violations"
        header = f"ValidationResult: INVALID — {len(self.violations)} violation(s)"
        return header + "\n  " + "\n  ".join(self.violations)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_monotonic(intervals: Sequence[TimeInterval]) -> List[str]:
    """Return violations where intervals are not strictly forward-ordered.

    Each interval must have ``start < end``, and the list must be sorted
    by increasing start_tick.
    """
    violations: List[str] = []
    for i, iv in enumerate(intervals):
        if iv.end_tick <= iv.start_tick:
            violations.append(
                f"Item {i}: end_tick ({iv.end_tick}) <= start_tick ({iv.start_tick})"
            )
        if i > 0:
            prev = intervals[i - 1]
            if iv.start_tick < prev.start_tick:
                violations.append(
                    f"Item {i}: start_tick ({iv.start_tick}) < "
                    f"previous start_tick ({prev.start_tick}) — not monotonic"
                )
    return violations


def check_contiguous(intervals: Sequence[TimeInterval]) -> List[str]:
    """Return violations where adjacent intervals have gaps or overlaps.

    Adjacent means: for sorted intervals, ``prev.end_tick != next.start_tick``
    is a violation (gap if <, overlap if >).
    """
    violations: List[str] = []
    for i in range(1, len(intervals)):
        prev = intervals[i - 1]
        cur = intervals[i]
        if prev.end_tick != cur.start_tick:
            if prev.end_tick < cur.start_tick:
                violations.append(
                    f"Gap between item {i - 1} (end={prev.end_tick}) and "
                    f"item {i} (start={cur.start_tick}): "
                    f"missing {cur.start_tick - prev.end_tick} ticks"
                )
            else:
                violations.append(
                    f"Overlap between item {i - 1} (end={prev.end_tick}) and "
                    f"item {i} (start={cur.start_tick}): "
                    f"{prev.end_tick - cur.start_tick} ticks overlap"
                )
    return violations


def check_total_duration(
    timeline: CanonicalTimeline,
    segments: Sequence[TimeInterval],
) -> List[str]:
    """Return violations where segments don't sum to the timeline total."""
    violations: List[str] = []
    total = sum(iv.duration_ticks for iv in segments)
    if total != timeline.duration_ticks:
        violations.append(
            f"Total segment duration ({total} ticks) != "
            f"timeline duration ({timeline.duration_ticks} ticks): "
            f"difference = {timeline.duration_ticks - total} ticks"
        )
    return violations


def check_containment(
    container: TimeInterval,
    children: Sequence[TimeInterval],
    label: str = "child",
) -> List[str]:
    """Return violations where *children* are not fully inside *container*."""
    violations: List[str] = []
    for i, child in enumerate(children):
        if child.start_tick < container.start_tick:
            violations.append(
                f"{label}[{i}] start ({child.start_tick}) is before "
                f"container start ({container.start_tick})"
            )
        if child.end_tick > container.end_tick:
            violations.append(
                f"{label}[{i}] end ({child.end_tick}) exceeds "
                f"container end ({container.end_tick})"
            )
    return violations


def check_out_of_bounds(
    timeline: CanonicalTimeline,
    intervals: Sequence[TimeInterval],
) -> List[str]:
    """Return violations where any interval exceeds the timeline bounds."""
    violations: List[str] = []
    for i, iv in enumerate(intervals):
        if iv.start_tick < 0:
            violations.append(
                f"Item {i}: negative start_tick ({iv.start_tick})"
            )
        if iv.end_tick > timeline.duration_ticks:
            violations.append(
                f"Item {i}: end_tick ({iv.end_tick}) exceeds "
                f"timeline duration ({timeline.duration_ticks})"
            )
    return violations


# ---------------------------------------------------------------------------
# Full validation
# ---------------------------------------------------------------------------

def validate_timeline(
    timeline: CanonicalTimeline,
    segments: Sequence[TimeInterval],
    shots_per_segment: Dict[int, Sequence[TimeInterval]],
) -> ValidationResult:
    """Run all timeline checks and return a ``ValidationResult``.

    Parameters
    ----------
    timeline:
        The canonical timeline to validate against.
    segments:
        Ordered top-level time intervals (Generation Segments).
    shots_per_segment:
        Mapping of segment index → ordered shot intervals.
    """
    all_violations: List[str] = []

    # Segments: monotonic, contiguous, total duration, out-of-bounds
    all_violations.extend(check_monotonic(segments))
    all_violations.extend(check_contiguous(segments))
    all_violations.extend(check_total_duration(timeline, segments))
    all_violations.extend(check_out_of_bounds(timeline, segments))

    # For each segment, check its shots
    for seg_idx, seg_iv in enumerate(segments):
        shots = shots_per_segment.get(seg_idx, [])
        if not shots:
            all_violations.append(f"Segment {seg_idx}: no shots defined")
            continue

        all_violations.extend(
            check_monotonic(shots)
        )
        all_violations.extend(
            check_contiguous(shots)
        )
        all_violations.extend(
            check_containment(seg_iv, shots, label=f"Segment {seg_idx} shot")
        )
        all_violations.extend(
            check_out_of_bounds(timeline, shots)
        )

    return ValidationResult(violations=all_violations)


# ---------------------------------------------------------------------------
# Display time compilation
# ---------------------------------------------------------------------------

def compile_display_times(
    timeline: CanonicalTimeline,
    intervals: Sequence[TimeInterval],
) -> List[Dict[str, Any]]:
    """Generate a stable display-time digest for each interval.

    Returns a list of dicts with keys:
    - ``start_tick``, ``end_tick``, ``duration_ticks``
    - ``start_s``, ``end_s``, ``duration_s`` (derived floats)
    - ``display_range`` (human-readable string, e.g. "0.00s – 5.00s")
    """
    results: List[Dict[str, Any]] = []
    for iv in intervals:
        start_s = iv.start_tick / timeline.ticks_per_second
        end_s = iv.end_tick / timeline.ticks_per_second
        dur_s = iv.duration_ticks / timeline.ticks_per_second
        results.append({
            "start_tick": iv.start_tick,
            "end_tick": iv.end_tick,
            "duration_ticks": iv.duration_ticks,
            "start_s": round(start_s, timeline.display_precision),
            "end_s": round(end_s, timeline.display_precision),
            "duration_s": round(dur_s, timeline.display_precision),
            "display_range": (
                f"{start_s:.{timeline.display_precision}f}s"
                " – "
                f"{end_s:.{timeline.display_precision}f}s"
            ),
        })
    return results
