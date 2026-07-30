"""V4.4 Correction Impact Schema."""

import unittest

try:
    from mode_p_vnext.schema import correction_impact as ci
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class CorrectionImpactTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "correction_impact not yet implemented")
    def test_impact_levels(self):
        self.assertIn("clarification_only", ci.IMPACT_LEVELS)
        self.assertIn("topology_or_fact_change", ci.IMPACT_LEVELS)

    @unittest.skipIf(not MODULE_EXISTS, "correction_impact not yet implemented")
    def test_topology_change_invalidates_approval(self):
        c = ci.CorrectionImpact(
            correction_id="CORR1",
            impact_level="topology_or_fact_change",
            affected_items=["shot S2 boundary"],
            invalidates_approval=True,
        )
        self.assertTrue(c.invalidates_approval)

    @unittest.skipIf(not MODULE_EXISTS, "correction_impact not yet implemented")
    def test_clarification_only_does_not_invalidate(self):
        c = ci.CorrectionImpact(
            correction_id="CORR2",
            impact_level="clarification_only",
            affected_items=["解释已有画面"],
            invalidates_approval=False,
        )
        self.assertFalse(c.invalidates_approval)

    @unittest.skipIf(not MODULE_EXISTS, "correction_impact not yet implemented")
    def test_invalid_level_rejected(self):
        with self.assertRaises(ValueError):
            ci.CorrectionImpact("x", "imaginary_level", [])

    @unittest.skipIf(not MODULE_EXISTS, "correction_impact not yet implemented")
    def test_topology_change_cannot_be_false_invalidation(self):
        """topology_or_fact_change MUST invalidate approval."""
        c = ci.CorrectionImpact("CORR3", "topology_or_fact_change", ["x"],
                                 invalidates_approval=False)
        violations = ci.validate_correction_impact(c)
        self.assertGreater(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
