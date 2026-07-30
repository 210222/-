"""V9.6 Telemetry, SLO & Error Classification."""

import unittest

try:
    from mode_p_vnext import telemetry as tm
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class TelemetryTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "telemetry not yet implemented")
    def test_stage_event_records_timing(self):
        event = tm.StageEvent(
            stage="MASTER_DRAFT",
            duration_ms=1500,
            budget_remaining=3000,
            cache_hit=False,
        )
        self.assertEqual(event.stage, "MASTER_DRAFT")
        self.assertEqual(event.duration_ms, 1500)

    @unittest.skipIf(not MODULE_EXISTS, "telemetry not yet implemented")
    def test_error_event_classified(self):
        event = tm.ErrorEvent(
            error_type="BudgetExceededError",
            stage="KNOWLEDGE_SELECTED",
            message="Knowledge budget exceeded: 3500 > 3000 chars",
        )
        self.assertEqual(event.error_type, "BudgetExceededError")

    @unittest.skipIf(not MODULE_EXISTS, "telemetry not yet implemented")
    def test_no_private_reasoning_logged(self):
        """Telemetry records metrics only — never Director reasoning or media."""
        event = tm.StageEvent(stage="DIAGNOSIS_COMPLETE", duration_ms=100,
                               budget_remaining=5000, cache_hit=True)
        self.assertFalse(hasattr(event, "director_reasoning"))
        self.assertFalse(hasattr(event, "media_content"))
        self.assertFalse(hasattr(event, "prompt_text"))

    @unittest.skipIf(not MODULE_EXISTS, "telemetry not yet implemented")
    def test_approval_event(self):
        event = tm.ApprovalEvent(
            episode_id="EP8",
            status="approved",
            duration_since_storyboard_ready_ms=30000,
        )
        self.assertEqual(event.status, "approved")


if __name__ == "__main__":
    unittest.main()
