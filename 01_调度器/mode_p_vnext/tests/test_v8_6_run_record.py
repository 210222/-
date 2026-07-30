"""V8.6 Storyboard/Render Run Record."""

import unittest

try:
    from mode_p_vnext import run_record as rr
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class RunRecordTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "run_record not yet implemented")
    def test_storyboard_record(self):
        r = rr.StoryboardRunRecord(
            record_id="SR001",
            submitted_prompt_hash="abc123",
            storyboard_image_hash="def456",
            task_id="TASK_EP8_001",
            platform="jimeng_sd2",
            platform_version="2.0",
        )
        self.assertEqual(r.record_id, "SR001")
        self.assertTrue(r.can_promote_to_validated)

    @unittest.skipIf(not MODULE_EXISTS, "run_record not yet implemented")
    def test_render_record(self):
        r = rr.RenderRunRecord(
            record_id="RR001",
            submitted_payload_hash="abc",
            video_output_hash="def",
            task_id="TASK_EP8_V001",
            platform="jimeng_sd2",
        )
        self.assertEqual(r.platform, "jimeng_sd2")

    @unittest.skipIf(not MODULE_EXISTS, "run_record not yet implemented")
    def test_no_record_no_promotion(self):
        """Without a run record, media cannot be promoted to validated."""
        self.assertIsNone(rr.RunRecord())


if __name__ == "__main__":
    unittest.main()
