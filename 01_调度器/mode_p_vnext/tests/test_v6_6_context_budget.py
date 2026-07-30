"""V6.6 Complete Context Budget & Truncation Failure."""

import unittest

try:
    from mode_p_vnext import context_budget as cb
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class ContextBudgetTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "context_budget not yet implemented")
    def test_budget_tracks_categories(self):
        b = cb.ContextBudget(
            fact_budget=2000, knowledge_budget=3000,
            asset_budget=1000, correction_budget=500,
            protocol_budget=2000, output_reserve=3000,
        )
        self.assertEqual(b.remaining("fact"), 2000)

    @unittest.skipIf(not MODULE_EXISTS, "context_budget not yet implemented")
    def test_consume_reduces_remaining(self):
        b = cb.ContextBudget(fact_budget=2000, knowledge_budget=1000,
                              asset_budget=500, correction_budget=500,
                              protocol_budget=1000, output_reserve=2000)
        b.consume("fact", 500)
        self.assertEqual(b.remaining("fact"), 1500)

    @unittest.skipIf(not MODULE_EXISTS, "context_budget not yet implemented")
    def test_exceeded_budget_raises(self):
        b = cb.ContextBudget(fact_budget=1000, knowledge_budget=1000,
                              asset_budget=500, correction_budget=500,
                              protocol_budget=1000, output_reserve=2000)
        with self.assertRaises(cb.BudgetExceededError):
            b.consume("fact", 2000)

    @unittest.skipIf(not MODULE_EXISTS, "context_budget not yet implemented")
    def test_silent_truncation_blocked(self):
        """Budget exceeded must raise, not silently truncate."""
        b = cb.ContextBudget(fact_budget=100, knowledge_budget=1000,
                              asset_budget=500, correction_budget=500,
                              protocol_budget=1000, output_reserve=2000)
        with self.assertRaises(cb.BudgetExceededError):
            b.consume("knowledge", 2000)

    @unittest.skipIf(not MODULE_EXISTS, "context_budget not yet implemented")
    def test_total_budget(self):
        b = cb.ContextBudget(fact_budget=1000, knowledge_budget=2000,
                              asset_budget=500, correction_budget=500,
                              protocol_budget=1000, output_reserve=1000)
        self.assertEqual(b.total_budget, 6000)


if __name__ == "__main__":
    unittest.main()
