"""V1.2 Timeline Validator/Compiler — monotonic, contiguous, containment tests.

Verify the validator checks:
- Monotonic ordering (no backwards intervals)
- Contiguous (adjacent intervals have no gaps)
- Total duration (segments sum to timeline total)
- Segment/Shot/Beat containment
- No overlaps or out-of-bounds
- Stable display time generation
"""

import unittest
from pathlib import Path


try:
    from mode_p_vnext.schema.canonical_timeline import (
        CanonicalTimeline, TimeInterval, Instant, Tick,
    )
    from mode_p_vnext import timeline_validator as tv
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


# ---------------------------------------------------------------------------
# Monotonic tests
# ---------------------------------------------------------------------------

class MonotonicTests(unittest.TestCase):
    """Verifying intervals don't go backwards."""

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_valid_monotonic_passes(self):
        intervals = [
            TimeInterval(0, 1000),
            TimeInterval(1000, 2000),
            TimeInterval(2000, 3000),
        ]
        violations = tv.check_monotonic(intervals)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_backwards_interval_fails(self):
        intervals = [
            TimeInterval(1000, 2000),
            TimeInterval(0, 1000),  # start < previous start → disorder
        ]
        violations = tv.check_monotonic(intervals)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_end_before_start_rejected_by_schema(self):
        """TimeInterval itself rejects end <= start — validator never sees it."""
        with self.assertRaises(ValueError):
            TimeInterval(1000, 500)


# ---------------------------------------------------------------------------
# Contiguous tests
# ---------------------------------------------------------------------------

class ContiguousTests(unittest.TestCase):
    """Verifying adjacent intervals have no gaps."""

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_valid_contiguous_passes(self):
        intervals = [
            TimeInterval(0, 1000),
            TimeInterval(1000, 2000),
        ]
        violations = tv.check_contiguous(intervals)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_gap_fails(self):
        intervals = [
            TimeInterval(0, 1000),
            TimeInterval(1500, 2500),  # gap: 1000→1500
        ]
        violations = tv.check_contiguous(intervals)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_overlap_fails(self):
        intervals = [
            TimeInterval(0, 1000),
            TimeInterval(800, 2000),  # overlap at 800..1000
        ]
        violations = tv.check_contiguous(intervals)
        self.assertGreater(len(violations), 0)


# ---------------------------------------------------------------------------
# Total duration tests
# ---------------------------------------------------------------------------

class TotalDurationTests(unittest.TestCase):
    """Verifying segments sum to timeline total."""

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_valid_total_duration_passes(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=3000)
        segments = [
            TimeInterval(0, 1000),
            TimeInterval(1000, 2000),
            TimeInterval(2000, 3000),
        ]
        violations = tv.check_total_duration(tl, segments)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_too_short_fails(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=5000)
        segments = [
            TimeInterval(0, 1000),
            TimeInterval(1000, 2000),  # only 2000 of 5000
        ]
        violations = tv.check_total_duration(tl, segments)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_too_long_fails(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=1000)
        segments = [
            TimeInterval(0, 1000),
            TimeInterval(1000, 2000),  # exceeds 1000
        ]
        violations = tv.check_total_duration(tl, segments)
        self.assertGreater(len(violations), 0)


# ---------------------------------------------------------------------------
# Containment tests — Shot within Segment
# ---------------------------------------------------------------------------

class ContainmentTests(unittest.TestCase):
    """Verifying Shots are fully within their parent Segment."""

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_shot_within_segment_passes(self):
        segment = TimeInterval(0, 3000)
        shots = [
            TimeInterval(0, 1000),
            TimeInterval(1000, 2000),
            TimeInterval(2000, 3000),
        ]
        violations = tv.check_containment(segment, shots)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_shot_before_segment_fails(self):
        segment = TimeInterval(1000, 3000)
        shots = [TimeInterval(0, 1000)]  # before segment
        violations = tv.check_containment(segment, shots)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_shot_after_segment_fails(self):
        segment = TimeInterval(0, 2000)
        shots = [TimeInterval(2000, 3000)]  # starts at segment end = ok if shots don't exceed
        # Actually [2000, 3000) starts at segment end, so not contained
        violations = tv.check_containment(segment, shots)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_shot_partial_overlap_fails(self):
        segment = TimeInterval(0, 2000)
        shots = [TimeInterval(1500, 3000)]  # overflows segment
        violations = tv.check_containment(segment, shots)
        self.assertGreater(len(violations), 0)


# ---------------------------------------------------------------------------
# Out-of-bounds tests
# ---------------------------------------------------------------------------

class OutOfBoundsTests(unittest.TestCase):
    """Verifying no tick exceeds the timeline."""

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_within_bounds_passes(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=3000)
        intervals = [TimeInterval(0, 3000)]
        violations = tv.check_out_of_bounds(tl, intervals)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_out_of_bounds_fails(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=2000)
        intervals = [TimeInterval(0, 3000)]  # exceeds duration
        violations = tv.check_out_of_bounds(tl, intervals)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_negative_tick_fails(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=2000)
        intervals = [TimeInterval(-100, 1000)]
        violations = tv.check_out_of_bounds(tl, intervals)
        self.assertGreater(len(violations), 0)


# ---------------------------------------------------------------------------
# Full validation
# ---------------------------------------------------------------------------

class FullValidationTests(unittest.TestCase):
    """End-to-end timeline validation."""

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_valid_timeline_no_violations(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=480000)
        segments = [TimeInterval(0, 480000)]
        shots_per_segment = {
            0: [
                TimeInterval(0, 240000),
                TimeInterval(240000, 480000),
            ],
        }
        result = tv.validate_timeline(tl, segments, shots_per_segment)
        self.assertTrue(result.is_valid, f"Violations: {result.violations}")

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_gap_in_shots_detected(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=480000)
        segments = [TimeInterval(0, 480000)]
        shots_per_segment = {
            0: [
                TimeInterval(0, 100000),
                TimeInterval(200000, 300000),  # gap 100000→200000; also only 200K of 480K
            ],
        }
        result = tv.validate_timeline(tl, segments, shots_per_segment)
        self.assertFalse(result.is_valid)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_multiple_segments_valid(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=6000)
        segments = [
            TimeInterval(0, 3000),
            TimeInterval(3000, 6000),
        ]
        shots_per_segment = {
            0: [
                TimeInterval(0, 1000),
                TimeInterval(1000, 2000),
                TimeInterval(2000, 3000),
            ],
            1: [
                TimeInterval(3000, 4500),
                TimeInterval(4500, 6000),
            ],
        }
        result = tv.validate_timeline(tl, segments, shots_per_segment)
        self.assertTrue(result.is_valid, f"Violations: {result.violations}")


# ---------------------------------------------------------------------------
# Display time compilation
# ---------------------------------------------------------------------------

class DisplayTimeCompilationTests(unittest.TestCase):
    """Stable display time generation."""

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_compile_display_times(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=480000)
        intervals = [
            TimeInterval(0, 240000),
            TimeInterval(240000, 480000),
        ]
        result = tv.compile_display_times(tl, intervals)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0]["start_s"], 0.0)
        self.assertAlmostEqual(result[0]["end_s"], 10.0, places=3)
        self.assertAlmostEqual(result[1]["start_s"], 10.0, places=3)
        self.assertAlmostEqual(result[1]["end_s"], 20.0, places=3)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_compile_display_times_stable(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=480000)
        intervals = [TimeInterval(0, 480000)]
        r1 = tv.compile_display_times(tl, intervals)
        r2 = tv.compile_display_times(tl, intervals)
        self.assertEqual(r1, r2)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_compile_includes_format_strings(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=240000)
        intervals = [TimeInterval(0, 120000)]
        result = tv.compile_display_times(tl, intervals)
        self.assertIn("display_range", result[0])
        self.assertIn("0.00", result[0]["display_range"])
        self.assertIn("5.00", result[0]["display_range"])


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

class ValidationResultTests(unittest.TestCase):
    """ValidationResult container."""

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_valid_result_is_valid(self):
        result = tv.ValidationResult(violations=[])
        self.assertTrue(result.is_valid)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_invalid_result_has_violations(self):
        result = tv.ValidationResult(violations=["gap at 1000→1500"])
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.violations), 1)

    @unittest.skipIf(not MODULE_EXISTS, "timeline_validator not yet implemented")
    def test_result_str(self):
        result = tv.ValidationResult(violations=["gap detected"])
        self.assertIn("gap", str(result))


if __name__ == "__main__":
    unittest.main()
