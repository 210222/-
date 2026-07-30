"""V1.1 Canonical Timeline Schema — rational timebase, integer ticks, intervals.

Tests for the foundational timeline data model:
- Rational timebase (ticks_per_second) with integer ticks
- [start, end) half-open intervals
- Instantaneous `at` markers
- Display seconds derivation (deterministic from ticks)
- Unknown framerate policy (no fake frame precision)
"""

import unittest
from pathlib import Path


try:
    from mode_p_vnext.schema import canonical_timeline as ct
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------

class TickTypeTests(unittest.TestCase):
    """Tick is always an integer — never float."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_tick_type_is_int(self):
        self.assertIs(ct.Tick, int)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_tick_from_seconds_returns_int(self):
        t = ct.tick_from_seconds(1.5, ticks_per_second=24000)
        self.assertIsInstance(t, int)
        self.assertEqual(t, 36000)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_tick_from_seconds_rounds_correctly(self):
        # 24000 ticks/s: 0.5s = 12000 ticks
        self.assertEqual(ct.tick_from_seconds(0.5, 24000), 12000)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_ticks_per_second_must_be_positive_integer(self):
        with self.assertRaises(ValueError):
            ct.CanonicalTimeline(ticks_per_second=0, duration_ticks=1000)
        with self.assertRaises(ValueError):
            ct.CanonicalTimeline(ticks_per_second=-100, duration_ticks=1000)


# ---------------------------------------------------------------------------
# TimeInterval
# ---------------------------------------------------------------------------

class TimeIntervalTests(unittest.TestCase):
    """[start, end) half-open intervals."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_interval_start_end_are_ticks(self):
        iv = ct.TimeInterval(start_tick=0, end_tick=48000)
        self.assertIsInstance(iv.start_tick, int)
        self.assertIsInstance(iv.end_tick, int)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_interval_end_must_be_after_start(self):
        with self.assertRaises(ValueError):
            ct.TimeInterval(start_tick=100, end_tick=50)
        with self.assertRaises(ValueError):
            ct.TimeInterval(start_tick=100, end_tick=100)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_interval_duration_ticks(self):
        iv = ct.TimeInterval(start_tick=1000, end_tick=5000)
        self.assertEqual(iv.duration_ticks, 4000)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_interval_contains_tick_half_open(self):
        iv = ct.TimeInterval(start_tick=0, end_tick=100)
        # [0, 100): 0 is inside, 100 is NOT
        self.assertTrue(iv.contains_tick(0))
        self.assertTrue(iv.contains_tick(50))
        self.assertTrue(iv.contains_tick(99))
        self.assertFalse(iv.contains_tick(100))
        self.assertFalse(iv.contains_tick(-1))

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_interval_adjacent_no_gap_no_overlap(self):
        """Adjacent: iv1.end == iv2.start — no gap, no overlap."""
        a = ct.TimeInterval(start_tick=0, end_tick=100)
        b = ct.TimeInterval(start_tick=100, end_tick=200)
        self.assertEqual(a.end_tick, b.start_tick)
        # No tick belongs to both
        self.assertFalse(a.contains_tick(100))
        self.assertTrue(b.contains_tick(100))

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_display_seconds(self):
        iv = ct.TimeInterval(start_tick=0, end_tick=120000)
        secs = iv.display_seconds(ticks_per_second=24000)
        self.assertAlmostEqual(secs, 5.0)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_interval_equals(self):
        a = ct.TimeInterval(start_tick=0, end_tick=100)
        b = ct.TimeInterval(start_tick=0, end_tick=100)
        c = ct.TimeInterval(start_tick=0, end_tick=200)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_interval_repr(self):
        iv = ct.TimeInterval(start_tick=0, end_tick=48000)
        r = repr(iv)
        self.assertIn("TimeInterval", r)
        self.assertIn("0", r)
        self.assertIn("48000", r)


# ---------------------------------------------------------------------------
# Instant
# ---------------------------------------------------------------------------

class InstantTests(unittest.TestCase):
    """Instantaneous `at` marker — must not be used as a duration."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_instant_at_tick_is_int(self):
        inst = ct.Instant(at_tick=24000)
        self.assertIsInstance(inst.at_tick, int)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_instant_has_no_duration(self):
        inst = ct.Instant(at_tick=24000)
        self.assertIsNone(inst.duration_ticks)
        with self.assertRaises(AttributeError):
            _ = inst.end_tick

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_instant_display_seconds(self):
        inst = ct.Instant(at_tick=48000)
        secs = inst.display_seconds(ticks_per_second=24000)
        self.assertAlmostEqual(secs, 2.0)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_instant_not_a_duration(self):
        """Instant must not be usable where TimeInterval is expected."""
        inst = ct.Instant(at_tick=100)
        self.assertIsNone(inst.duration_ticks)
        # Type check: Instant != TimeInterval
        with self.assertRaises(AttributeError):
            _ = inst.end_tick  # Not exposed on Instant

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_instant_equals(self):
        a = ct.Instant(at_tick=100)
        b = ct.Instant(at_tick=100)
        c = ct.Instant(at_tick=200)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


# ---------------------------------------------------------------------------
# CanonicalTimeline
# ---------------------------------------------------------------------------

class CanonicalTimelineTests(unittest.TestCase):
    """The overall timeline container."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_default_timebase(self):
        tl = ct.CanonicalTimeline(ticks_per_second=24000, duration_ticks=240000)
        self.assertEqual(tl.ticks_per_second, 24000)
        self.assertEqual(tl.duration_ticks, 240000)
        self.assertAlmostEqual(tl.duration_seconds, 10.0)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_required_fields(self):
        tl = ct.CanonicalTimeline(
            ticks_per_second=24000,
            duration_ticks=480000,
            display_precision=3,
            boundary_ownership="incoming",
            output_fps_status="unknown",
            rounding_policy="nearest",
        )
        self.assertEqual(tl.ticks_per_second, 24000)
        self.assertEqual(tl.boundary_ownership, "incoming")
        self.assertEqual(tl.output_fps_status, "unknown")
        self.assertEqual(tl.rounding_policy, "nearest")

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_output_fps_status_must_be_verified_or_unknown(self):
        ct.CanonicalTimeline(ticks_per_second=24000, duration_ticks=1000,
                             output_fps_status="verified", output_fps=24.0)
        ct.CanonicalTimeline(ticks_per_second=24000, duration_ticks=1000,
                             output_fps_status="unknown")
        with self.assertRaises(ValueError):
            ct.CanonicalTimeline(ticks_per_second=24000, duration_ticks=1000,
                                 output_fps_status="maybe")

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_boundary_ownership_must_be_incoming(self):
        tl = ct.CanonicalTimeline(ticks_per_second=24000, duration_ticks=1000)
        self.assertEqual(tl.boundary_ownership, "incoming")

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_duration_ticks_must_be_positive(self):
        with self.assertRaises(ValueError):
            ct.CanonicalTimeline(ticks_per_second=24000, duration_ticks=0)
        with self.assertRaises(ValueError):
            ct.CanonicalTimeline(ticks_per_second=24000, duration_ticks=-100)


# ---------------------------------------------------------------------------
# Display seconds derivation
# ---------------------------------------------------------------------------

class DisplaySecondsTests(unittest.TestCase):
    """Human-readable seconds are deterministically derived from ticks."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_display_seconds_from_ticks(self):
        self.assertAlmostEqual(ct.display_seconds(24000, 24000), 1.0)
        self.assertAlmostEqual(ct.display_seconds(48000, 24000), 2.0)
        self.assertAlmostEqual(ct.display_seconds(12000, 24000), 0.5)
        self.assertAlmostEqual(ct.display_seconds(0, 24000), 0.0)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_display_seconds_negative_ticks(self):
        with self.assertRaises(ValueError):
            ct.display_seconds(-1, 24000)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_display_format_string(self):
        """format_display_seconds returns a human-readable string."""
        result = ct.format_display_seconds(36000, 24000, precision=2)
        self.assertIsInstance(result, str)
        self.assertIn("1.50", result)


# ---------------------------------------------------------------------------
# Unknown framerate policy
# ---------------------------------------------------------------------------

class UnknownFrameratePolicyTests(unittest.TestCase):
    """Do not fake frame precision when output fps is unverified."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_frame_number_raises_when_fps_unknown(self):
        """When output_fps_status is unknown, frame_number() must raise."""
        tl = ct.CanonicalTimeline(
            ticks_per_second=24000, duration_ticks=480000,
            output_fps_status="unknown",
        )
        with self.assertRaises(ct.FramerateUnknownError):
            tl.frame_number(12000)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_frame_number_works_when_fps_verified(self):
        tl = ct.CanonicalTimeline(
            ticks_per_second=24000, duration_ticks=480000,
            output_fps_status="verified", output_fps=24.0,
        )
        fn = tl.frame_number(24000)  # exactly 1 second at 24fps = frame 24
        self.assertEqual(fn, 24)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_time_tolerance_not_frame_precision(self):
        """When fps is unknown, use time tolerance, not frame claims."""
        tl = ct.CanonicalTimeline(
            ticks_per_second=24000, duration_ticks=480000,
            output_fps_status="unknown",
        )
        # time_tolerance should work regardless of fps status
        tolerance_s = tl.time_tolerance_at_tick(24000, tolerance_ticks=240)
        self.assertAlmostEqual(tolerance_s, 0.01)  # 240 ticks / 24000 = 0.01s

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_cannot_claim_frame_N_without_verified_fps(self):
        tl = ct.CanonicalTimeline(
            ticks_per_second=24000, duration_ticks=480000,
            output_fps_status="unknown",
        )
        with self.assertRaises(ct.FramerateUnknownError):
            tl.format_frame_claim(36000)  # "Frame 36" claim is banned


# ---------------------------------------------------------------------------
# Canonical JSON roundtrip
# ---------------------------------------------------------------------------

class TimelineCanonicalTests(unittest.TestCase):
    """Timeline data must be serializable to canonical JSON."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_timeline_to_dict(self):
        tl = ct.CanonicalTimeline(
            ticks_per_second=24000,
            duration_ticks=480000,
            output_fps_status="unknown",
        )
        d = tl.to_dict()
        self.assertEqual(d["ticks_per_second"], 24000)
        self.assertEqual(d["duration_ticks"], 480000)
        self.assertEqual(d["boundary_ownership"], "incoming")

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_timeline_canonical_json_stable(self):
        from mode_p_vnext.canonical_serialization import (
            canonical_json_dumps, stable_hash_sha256,
        )
        tl = ct.CanonicalTimeline(
            ticks_per_second=24000, duration_ticks=480000,
        )
        j1 = canonical_json_dumps(tl.to_dict())
        j2 = canonical_json_dumps(tl.to_dict())
        self.assertEqual(j1, j2)
        self.assertEqual(stable_hash_sha256(j1.encode("utf-8")),
                         stable_hash_sha256(j2.encode("utf-8")))

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_interval_to_dict(self):
        iv = ct.TimeInterval(start_tick=0, end_tick=48000)
        d = iv.to_dict()
        self.assertEqual(d["start_tick"], 0)
        self.assertEqual(d["end_tick"], 48000)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_timeline module not yet implemented")
    def test_instant_to_dict(self):
        inst = ct.Instant(at_tick=24000)
        d = inst.to_dict()
        self.assertEqual(d["at_tick"], 24000)
        self.assertEqual(d["type"], "instant")


if __name__ == "__main__":
    unittest.main()
