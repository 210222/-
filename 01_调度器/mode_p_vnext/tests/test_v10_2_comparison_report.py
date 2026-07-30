"""V10.2 v4/vNext Comparison Report — multi-axis, no single similarity."""

import unittest

try:
    from mode_p_vnext import comparison_report as cr
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class ComparisonReportTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "comparison_report not yet implemented")
    def test_report_multi_axis(self):
        report = cr.ComparisonReport(
            report_id="CMP001",
            structure_match=True,
            timing_match=True,
            cuts_match=False,
            visibility_match=True,
            knowledge_usage_diff=["v4 used capsule, vNext used decision card"],
            format_match=True,
        )
        self.assertTrue(report.structure_match)
        self.assertFalse(report.cuts_match)
        self.assertGreater(len(report.knowledge_usage_diff), 0)

    @unittest.skipIf(not MODULE_EXISTS, "comparison_report not yet implemented")
    def test_no_single_similarity_score(self):
        report = cr.ComparisonReport("CMP002", True, True, True, True, [], True)
        self.assertFalse(hasattr(report, "similarity_score"))
        self.assertFalse(hasattr(report, "overall_match"))

    @unittest.skipIf(not MODULE_EXISTS, "comparison_report not yet implemented")
    def test_comparison_axes_match_fidelity(self):
        """Comparison axes align with FidelityScores axes."""
        axes = cr.COMPARISON_AXES
        self.assertIn("structure", axes)
        self.assertIn("timing", axes)
        self.assertIn("cuts", axes)
        self.assertIn("visibility", axes)
        self.assertIn("knowledge_usage", axes)
        self.assertIn("format", axes)


if __name__ == "__main__":
    unittest.main()
