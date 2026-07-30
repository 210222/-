"""V9.2 Manual Storyboard Pause & Resume — 4 routes + idempotency."""

import unittest

try:
    from mode_p_vnext.schema.correction_impact import CorrectionImpact
    from mode_p_vnext.approval_gate import ApprovalGate
    from mode_p_vnext.session_state import SessionStateMachine
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class PauseResumeTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "modules not available")
    def test_approved_route_unblocks_payload(self):
        gate = ApprovalGate("EP8")
        gate.approve()
        self.assertTrue(gate.can_generate_payload)

    @unittest.skipIf(not MODULE_EXISTS, "modules not available")
    def test_clarification_route_keeps_pending(self):
        gate = ApprovalGate("EP8")
        gate.request_clarification("请解释构图")
        self.assertFalse(gate.can_generate_payload)
        # After clarification, re-approve
        gate.approve("已解释")
        self.assertTrue(gate.can_generate_payload)

    @unittest.skipIf(not MODULE_EXISTS, "modules not available")
    def test_visible_change_invalidates_and_resumes(self):
        sm = SessionStateMachine("EP8")
        for s in ["DIAGNOSIS_COMPLETE", "MASTER_DRAFT", "STORYBOARD_READY"]:
            sm.transition(s)
        # Visible change → rollback to Master
        sm.rollback_to("MASTER_DRAFT")
        self.assertEqual(sm.current_state, "MASTER_DRAFT")
        # Resume
        for s in ["STORYBOARD_READY", "STORYBOARD_APPROVAL_REQUIRED"]:
            sm.transition(s)
        self.assertTrue(sm.is_approval_required)

    @unittest.skipIf(not MODULE_EXISTS, "modules not available")
    def test_topology_change_goes_back_to_master(self):
        sm = SessionStateMachine("EP8")
        for s in ["DIAGNOSIS_COMPLETE", "MASTER_DRAFT", "STORYBOARD_READY"]:
            sm.transition(s)
        sm.rollback_to("MASTER_DRAFT")
        self.assertEqual(sm.current_state, "MASTER_DRAFT")
        # Re-approval required after topology change
        sm.transition("STORYBOARD_READY")
        sm.transition("STORYBOARD_APPROVAL_REQUIRED")
        self.assertTrue(sm.is_approval_required)

    @unittest.skipIf(not MODULE_EXISTS, "modules not available")
    def test_resume_idempotent(self):
        """Rollback to same state twice is idempotent."""
        sm = SessionStateMachine("EP8")
        for s in ["DIAGNOSIS_COMPLETE", "MASTER_DRAFT", "STORYBOARD_READY"]:
            sm.transition(s)
        sm.rollback_to("MASTER_DRAFT")
        sm.rollback_to("MASTER_DRAFT")  # idempotent — no error
        self.assertEqual(sm.current_state, "MASTER_DRAFT")


if __name__ == "__main__":
    unittest.main()
