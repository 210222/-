"""V9.3 External Feedback Integration — accept but don't auto-modify knowledge."""

import unittest

try:
    from mode_p_vnext import external_feedback as ef
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class ExternalFeedbackTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "external_feedback not yet implemented")
    def test_human_evaluation_accepted(self):
        fb = ef.ExternalFeedback(
            feedback_id="FB001",
            source="human_evaluation",
            content="视频切镜时机准确",
            segment_id="SEG1",
        )
        self.assertEqual(fb.source, "human_evaluation")
        self.assertFalse(fb.auto_modify_knowledge)

    @unittest.skipIf(not MODULE_EXISTS, "external_feedback not yet implemented")
    def test_ffmpeg_evidence_accepted(self):
        fb = ef.ExternalFeedback(
            feedback_id="FB002",
            source="ffmpeg_mechanical",
            content="detected cut at 4.0s",
            segment_id="SEG1",
        )
        self.assertEqual(fb.source, "ffmpeg_mechanical")

    @unittest.skipIf(not MODULE_EXISTS, "external_feedback not yet implemented")
    def test_multimodal_report_accepted(self):
        fb = ef.ExternalFeedback(
            feedback_id="FB003",
            source="multimodal_report",
            content="后壳表面正确渲染为不透明实体",
            segment_id="SEG1",
        )
        self.assertEqual(fb.source, "multimodal_report")

    @unittest.skipIf(not MODULE_EXISTS, "external_feedback not yet implemented")
    def test_never_auto_modifies_knowledge(self):
        """External feedback is recorded but NEVER auto-modifies knowledge."""
        fb = ef.ExternalFeedback("FB004", "human_evaluation", "good", "S1")
        self.assertFalse(fb.auto_modify_knowledge)
        self.assertIsNone(fb.knowledge_modification)


if __name__ == "__main__":
    unittest.main()
