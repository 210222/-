"""V8.5 Knowledge/Constraint Ablation."""

import unittest

try:
    from mode_p_vnext import ablation as ab
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class AblationTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "ablation not yet implemented")
    def test_ablation_config(self):
        config = ab.AblationConfig(
            config_id="ABL001",
            remove_knowledge=["capsule_action_chase"],
            remove_constraints=["visibility_contract"],
            use_golden_experience=False,
        )
        self.assertFalse(config.use_golden_experience)
        self.assertIn("capsule_action_chase", config.remove_knowledge)

    @unittest.skipIf(not MODULE_EXISTS, "ablation not yet implemented")
    def test_result_tracks_delta(self):
        result = ab.AblationResult(
            config_id="ABL001",
            baseline_fidelity={"opening_frame": 1.0},
            ablated_fidelity={"opening_frame": 0.6},
        )
        self.assertAlmostEqual(result.delta("opening_frame"), -0.4)


if __name__ == "__main__":
    unittest.main()
