"""V2.2 Dynamic Visibility State — time-bound visibility with beat references."""

import unittest

try:
    from mode_p_vnext.schema.canonical_timeline import TimeInterval
    from mode_p_vnext.schema.visibility_contract import VisibilityContract
    from mode_p_vnext import dynamic_visibility as dv
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DynamicVisibilityStateTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "dynamic_visibility not yet implemented")
    def test_state_binds_contract_to_time_range(self):
        contract = VisibilityContract(visible_whitelist=["枪管"])
        state = dv.DynamicVisibilityState(
            state_id="VS1",
            valid_time_range=TimeInterval(0, 48000),
            contract=contract,
        )
        self.assertEqual(state.state_id, "VS1")
        self.assertTrue(state.contains_tick(24000))
        self.assertFalse(state.contains_tick(48000))

    @unittest.skipIf(not MODULE_EXISTS, "dynamic_visibility not yet implemented")
    def test_beat_reference_within_range_passes(self):
        state = dv.DynamicVisibilityState(
            "VS1", TimeInterval(0, 48000),
            VisibilityContract(visible_whitelist=["x"]),
        )
        violations = dv.check_beat_references(
            beat_at_tick=24000, beat_state_id="VS1",
            visibility_states=[state],
        )
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "dynamic_visibility not yet implemented")
    def test_beat_reference_outside_range_fails(self):
        state = dv.DynamicVisibilityState(
            "VS1", TimeInterval(0, 1000),
            VisibilityContract(visible_whitelist=["x"]),
        )
        violations = dv.check_beat_references(
            beat_at_tick=5000, beat_state_id="VS1",
            visibility_states=[state],
        )
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "dynamic_visibility not yet implemented")
    def test_beat_reference_nonexistent_state(self):
        violations = dv.check_beat_references(
            beat_at_tick=100, beat_state_id="GHOST",
            visibility_states=[],
        )
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "dynamic_visibility not yet implemented")
    def test_state_transition_valid(self):
        """Adjacent states: end of VS1 == start of VS2."""
        s1 = dv.DynamicVisibilityState("VS1", TimeInterval(0, 1000),
            VisibilityContract(visible_whitelist=["a"]))
        s2 = dv.DynamicVisibilityState("VS2", TimeInterval(1000, 2000),
            VisibilityContract(visible_whitelist=["b"]))
        violations = dv.check_visibility_transitions([s1, s2])
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "dynamic_visibility not yet implemented")
    def test_state_transition_gap_fails(self):
        s1 = dv.DynamicVisibilityState("VS1", TimeInterval(0, 500),
            VisibilityContract(visible_whitelist=["a"]))
        s2 = dv.DynamicVisibilityState("VS2", TimeInterval(1000, 2000),
            VisibilityContract(visible_whitelist=["b"]))
        violations = dv.check_visibility_transitions([s1, s2])
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "dynamic_visibility not yet implemented")
    def test_surface_orientation_change_recorded(self):
        s = dv.DynamicVisibilityState(
            "VS1", TimeInterval(0, 1000),
            VisibilityContract(visible_whitelist=["后壳"]),
            surface_orientation_change="手机后壳→正面（旋转中）",
        )
        self.assertEqual(s.surface_orientation_change, "手机后壳→正面（旋转中）")


if __name__ == "__main__":
    unittest.main()
