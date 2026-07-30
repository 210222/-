"""V6.4 User Storyboard Approval Gate."""

import unittest

try:
    from mode_p_vnext import approval_gate as ag
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class ApprovalGateTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "approval_gate not yet implemented")
    def test_initial_pending(self):
        gate = ag.ApprovalGate("EP8")
        self.assertEqual(gate.status, "pending")

    @unittest.skipIf(not MODULE_EXISTS, "approval_gate not yet implemented")
    def test_approve_allows_payload(self):
        gate = ag.ApprovalGate("EP8")
        gate.approve(user_note="故事板OK")
        self.assertEqual(gate.status, "approved")
        self.assertTrue(gate.can_generate_payload)

    @unittest.skipIf(not MODULE_EXISTS, "approval_gate not yet implemented")
    def test_clarify_still_pending(self):
        gate = ag.ApprovalGate("EP8")
        gate.request_clarification("这个构图是什么意思？")
        self.assertEqual(gate.status, "clarification_requested")
        self.assertFalse(gate.can_generate_payload)

    @unittest.skipIf(not MODULE_EXISTS, "approval_gate not yet implemented")
    def test_revise_returns_to_master(self):
        gate = ag.ApprovalGate("EP8")
        gate.request_revision("镜头S3需要重新设计")
        self.assertEqual(gate.status, "revision_requested")
        self.assertFalse(gate.can_generate_payload)

    @unittest.skipIf(not MODULE_EXISTS, "approval_gate not yet implemented")
    def test_cannot_generate_payload_without_approval(self):
        gate = ag.ApprovalGate("EP8")
        self.assertFalse(gate.can_generate_payload)

    @unittest.skipIf(not MODULE_EXISTS, "approval_gate not yet implemented")
    def test_approval_records_bindings(self):
        gate = ag.ApprovalGate("EP8")
        gate.approve(asset_bindings=["@图片1: storyboard_reference"])
        self.assertTrue(any("@图片1" in b for b in gate.asset_bindings))


if __name__ == "__main__":
    unittest.main()
