"""V8.2 Multi-Axis Fidelity Scorer."""

import unittest

try:
    from mode_p_vnext import fidelity_scorer as fs
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class FidelityScorerTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "fidelity_scorer not yet implemented")
    def test_scorer_has_separate_axes(self):
        scores = fs.FidelityScores(
            opening_frame=1.0, camera_path=0.8,
            cut_points=1.0, character_positions=0.9,
            visibility=1.0, landing_frame=0.7,
            allowed_optimizations=0.5,
        )
        self.assertAlmostEqual(scores.opening_frame, 1.0)
        self.assertAlmostEqual(scores.landing_frame, 0.7)

    @unittest.skipIf(not MODULE_EXISTS, "fidelity_scorer not yet implemented")
    def test_not_collapsed_to_single_score(self):
        """Each axis is independently reported — no single similarity number."""
        scores = fs.FidelityScores(0.5, 0.9, 0.7, 0.8, 0.6, 0.4, 0.3)
        self.assertFalse(hasattr(scores, "overall_score"))
        self.assertFalse(hasattr(scores, "similarity"))

    @unittest.skipIf(not MODULE_EXISTS, "fidelity_scorer not yet implemented")
    def test_axis_names_match_expected(self):
        axes = fs.FIDELITY_AXES
        self.assertIn("opening_frame", axes)
        self.assertIn("landing_frame", axes)
        self.assertIn("camera_path", axes)
        self.assertIn("cut_points", axes)
        self.assertIn("character_positions", axes)
        self.assertIn("visibility", axes)
        self.assertIn("allowed_optimizations", axes)


if __name__ == "__main__":
    unittest.main()
