"""V1.3 Boundary Ownership & HOLD — schema and validation tests.

Verify:
- InternalBoundary dataclass with required fields
- Boundary ownership: cut tick belongs to incoming shot
- N Shot = N+1 Boundary rule
- HOLD: explicit non-zero duration, held object declared
- Boundary ticks within timeline bounds
"""

import unittest
from pathlib import Path


try:
    from mode_p_vnext.schema.canonical_timeline import (
        CanonicalTimeline, TimeInterval, Instant, Tick,
    )
    from mode_p_vnext.schema import boundary as bd
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


# ---------------------------------------------------------------------------
# InternalBoundary schema tests
# ---------------------------------------------------------------------------

class InternalBoundarySchemaTests(unittest.TestCase):
    """InternalBoundary dataclass structure."""

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_boundary_has_required_fields(self):
        b = bd.InternalBoundary(
            at_tick=1000,
            boundary_type="hard_cut",
            preferred_execution="instant",
            fidelity_class="LOCKED",
            outgoing_anchor="右手持枪",
            incoming_anchor="手机特写",
            outgoing_state_id="s1",
            incoming_state_id="s2",
        )
        self.assertEqual(b.at_tick, 1000)
        self.assertEqual(b.boundary_type, "hard_cut")
        self.assertEqual(b.boundary_ownership, "incoming")

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_boundary_type_must_be_valid(self):
        with self.assertRaises(ValueError):
            bd.InternalBoundary(
                at_tick=1000, boundary_type="invalid_type",
                preferred_execution="instant", fidelity_class="LOCKED",
                outgoing_anchor="a", incoming_anchor="b",
                outgoing_state_id="s1", incoming_state_id="s2",
            )

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_valid_boundary_types_accepted(self):
        for bt in bd.BOUNDARY_TYPES:
            b = bd.InternalBoundary(
                at_tick=1000, boundary_type=bt,
                preferred_execution="instant", fidelity_class="LOCKED",
                outgoing_anchor="a", incoming_anchor="b",
                outgoing_state_id="s1", incoming_state_id="s2",
            )
            self.assertEqual(b.boundary_type, bt)

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_boundary_at_tick_is_int(self):
        b = bd.InternalBoundary(
            at_tick=24000, boundary_type="hard_cut",
            preferred_execution="instant", fidelity_class="ELASTIC",
            outgoing_anchor="a", incoming_anchor="b",
            outgoing_state_id="s1", incoming_state_id="s2",
        )
        self.assertIsInstance(b.at_tick, int)


# ---------------------------------------------------------------------------
# HOLD schema tests
# ---------------------------------------------------------------------------

class HoldSchemaTests(unittest.TestCase):
    """HOLD dataclass — non-zero duration, declared held object."""

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_hold_has_required_fields(self):
        h = bd.Hold(
            interval=TimeInterval(1000, 3000),
            held_object="枪管金属内壁",
            hold_reason="关键落幅注视",
        )
        self.assertEqual(h.interval.duration_ticks, 2000)
        self.assertEqual(h.held_object, "枪管金属内壁")

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_hold_zero_duration_rejected(self):
        with self.assertRaises(ValueError):
            bd.Hold(
                interval=TimeInterval(1000, 1000),  # zero duration
                held_object="x",
                hold_reason="y",
            )

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_hold_negative_duration_rejected(self):
        with self.assertRaises(ValueError):
            # TimeInterval itself rejects end<start, but Hold also validates
            bd.Hold(
                interval=TimeInterval(1000, 999),  # will be caught by TimeInterval
                held_object="x",
                hold_reason="y",
            )

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_hold_empty_object_rejected(self):
        with self.assertRaises(ValueError):
            bd.Hold(
                interval=TimeInterval(1000, 2000),
                held_object="",
                hold_reason="reason",
            )

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_hold_display_seconds(self):
        h = bd.Hold(
            interval=TimeInterval(0, 48000),
            held_object="落幅",
            hold_reason="注视",
        )
        self.assertAlmostEqual(h.display_seconds(24000), 2.0)


# ---------------------------------------------------------------------------
# N Shot = N+1 Boundary tests
# ---------------------------------------------------------------------------

class NBoundaryTests(unittest.TestCase):
    """Verifying N shots ⇒ N+1 boundaries."""

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_one_shot_two_boundaries(self):
        shots = [TimeInterval(0, 1000)]
        boundaries = [
            bd.InternalBoundary(0, "hard_cut", "instant", "LOCKED",
                                "entry", "s1_start", "entry", "s1"),
            bd.InternalBoundary(1000, "hard_cut", "instant", "LOCKED",
                                "s1_end", "exit", "s1", "exit"),
        ]
        violations = bd.check_boundary_shot_count(shots, boundaries)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_two_shots_three_boundaries(self):
        shots = [TimeInterval(0, 1000), TimeInterval(1000, 2000)]
        boundaries = [
            bd.InternalBoundary(0, "hard_cut", "instant", "LOCKED",
                                "entry", "s1", "entry", "s1"),
            bd.InternalBoundary(1000, "hard_cut", "instant", "LOCKED",
                                "s1", "s2", "s1", "s2"),
            bd.InternalBoundary(2000, "hard_cut", "instant", "LOCKED",
                                "s2", "exit", "s2", "exit"),
        ]
        violations = bd.check_boundary_shot_count(shots, boundaries)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_wrong_boundary_count_fails(self):
        shots = [TimeInterval(0, 1000)]
        boundaries = [
            bd.InternalBoundary(0, "hard_cut", "instant", "LOCKED",
                                "entry", "s1", "entry", "s1"),
            # Missing exit boundary — only 1 for 1 shot (need 2)
        ]
        violations = bd.check_boundary_shot_count(shots, boundaries)
        self.assertGreater(len(violations), 0)


# ---------------------------------------------------------------------------
# Boundary ownership tests
# ---------------------------------------------------------------------------

class BoundaryOwnershipTests(unittest.TestCase):
    """Cut tick belongs to incoming shot."""

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_boundary_tick_in_incoming_shot(self):
        """Boundary at t=1000: outgoing shot [0,1000), incoming shot [1000,2000)."""
        shots = [TimeInterval(0, 1000), TimeInterval(1000, 2000)]
        boundary = bd.InternalBoundary(
            1000, "hard_cut", "instant", "LOCKED",
            "s1", "s2", "s1", "s2",
        )
        # Boundary tick 1000 is in incoming shot (contains_tick [1000,2000))
        self.assertTrue(shots[1].contains_tick(boundary.at_tick))
        # NOT in outgoing shot
        self.assertFalse(shots[0].contains_tick(boundary.at_tick))

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_check_boundary_belongs_to_a_shot(self):
        shots = [TimeInterval(0, 1000), TimeInterval(1000, 2000)]
        boundaries = [
            bd.InternalBoundary(0, "hard_cut", "instant", "LOCKED",
                                "entry", "s1", "entry", "s1"),
            bd.InternalBoundary(1000, "hard_cut", "instant", "LOCKED",
                                "s1", "s2", "s1", "s2"),
            bd.InternalBoundary(2000, "hard_cut", "instant", "LOCKED",
                                "s2", "exit", "s2", "exit"),
        ]
        violations = bd.check_boundary_ownership(shots, boundaries)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_orphan_boundary_fails(self):
        """Boundary tick not in any shot."""
        shots = [TimeInterval(0, 1000)]
        boundaries = [
            bd.InternalBoundary(500, "hard_cut", "instant", "LOCKED",
                                "entry", "s1", "entry", "s1"),
            bd.InternalBoundary(2000, "hard_cut", "instant", "LOCKED",  # orphan
                                "s1", "exit", "s1", "exit"),
        ]
        violations = bd.check_boundary_ownership(shots, boundaries)
        self.assertGreater(len(violations), 0)


# ---------------------------------------------------------------------------
# Boundary out-of-bounds tests
# ---------------------------------------------------------------------------

class BoundaryOutOfBoundsTests(unittest.TestCase):
    """Boundary ticks must be within timeline."""

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_valid_boundary_in_bounds(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=3000)
        boundaries = [
            bd.InternalBoundary(0, "hard_cut", "instant", "LOCKED",
                                "entry", "s1", "entry", "s1"),
            bd.InternalBoundary(3000, "hard_cut", "instant", "LOCKED",
                                "s1", "exit", "s1", "exit"),
        ]
        violations = bd.check_boundary_in_bounds(tl, boundaries)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_boundary_beyond_timeline_fails(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=2000)
        boundaries = [
            bd.InternalBoundary(3000, "hard_cut", "instant", "LOCKED",
                                "s1", "exit", "s1", "exit"),
        ]
        violations = bd.check_boundary_in_bounds(tl, boundaries)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "boundary module not yet implemented")
    def test_boundary_negative_tick_fails(self):
        tl = CanonicalTimeline(ticks_per_second=24000, duration_ticks=2000)
        boundaries = [
            bd.InternalBoundary(-100, "hard_cut", "instant", "LOCKED",
                                "entry", "s1", "entry", "s1"),
        ]
        violations = bd.check_boundary_in_bounds(tl, boundaries)
        self.assertGreater(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
