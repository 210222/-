"""V6.1 vNext Session State Machine."""

import unittest

try:
    from mode_p_vnext import session_state as ss
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class SessionStateMachineTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "session_state not yet implemented")
    def test_initial_state(self):
        sm = ss.SessionStateMachine("EP8")
        self.assertEqual(sm.current_state, "SCRIPT_PARSED")

    @unittest.skipIf(not MODULE_EXISTS, "session_state not yet implemented")
    def test_valid_transitions(self):
        sm = ss.SessionStateMachine("EP8")
        sm.transition("DIAGNOSIS_COMPLETE")
        self.assertEqual(sm.current_state, "DIAGNOSIS_COMPLETE")
        sm.transition("MASTER_DRAFT")
        self.assertEqual(sm.current_state, "MASTER_DRAFT")

    @unittest.skipIf(not MODULE_EXISTS, "session_state not yet implemented")
    def test_invalid_transition_raises(self):
        sm = ss.SessionStateMachine("EP8")
        sm.transition("DIAGNOSIS_COMPLETE")
        with self.assertRaises(ss.InvalidStateTransition):
            sm.transition("SCRIPT_PARSED")  # can't go backward

    @unittest.skipIf(not MODULE_EXISTS, "session_state not yet implemented")
    def test_storyboard_approval_required_state(self):
        sm = ss.SessionStateMachine("EP8")
        for s in ["DIAGNOSIS_COMPLETE", "MASTER_DRAFT", "STORYBOARD_READY"]:
            sm.transition(s)
        self.assertEqual(sm.current_state, "STORYBOARD_READY")
        sm.transition("STORYBOARD_APPROVAL_REQUIRED")
        self.assertTrue(sm.is_approval_required)

    @unittest.skipIf(not MODULE_EXISTS, "session_state not yet implemented")
    def test_partial_rollback(self):
        sm = ss.SessionStateMachine("EP8")
        for s in ["DIAGNOSIS_COMPLETE", "MASTER_DRAFT", "STORYBOARD_READY"]:
            sm.transition(s)
        sm.rollback_to("MASTER_DRAFT")
        self.assertEqual(sm.current_state, "MASTER_DRAFT")

    @unittest.skipIf(not MODULE_EXISTS, "session_state not yet implemented")
    def test_rollback_to_later_state_raises(self):
        sm = ss.SessionStateMachine("EP8")
        sm.transition("DIAGNOSIS_COMPLETE")
        with self.assertRaises(ss.InvalidStateTransition):
            sm.rollback_to("MASTER_DRAFT")  # haven't reached it yet


if __name__ == "__main__":
    unittest.main()
