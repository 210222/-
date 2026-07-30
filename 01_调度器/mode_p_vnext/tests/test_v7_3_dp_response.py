"""V7.3 DP Response Contract."""

import unittest

try:
    from mode_p_vnext import dp_response_contract as dp
    from mode_p_vnext import dp_manifest as dm
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DPResponseTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "dp_response_contract not yet implemented")
    def test_ready_response(self):
        r = dp.DPResponse(
            response_id="DPR001",
            verdict="READY",
        )
        self.assertTrue(r.is_ready)
        self.assertEqual(len(r.issues), 0)

    @unittest.skipIf(not MODULE_EXISTS, "dp_response_contract not yet implemented")
    def test_directed_question(self):
        r = dp.DPResponse(
            response_id="DPR002",
            verdict="DIRECTED_QUESTION",
            issues=[dp.DPIssue(
                issue_id="I001",
                question="Shot S2的构图是否可见？",
                bound_to_segment="SEG1",
                bound_to_shot="S2",
                bound_to_panel=2,
                fidelity_class="LOCKED",
            )],
        )
        self.assertFalse(r.is_ready)
        self.assertEqual(r.issues[0].bound_to_shot, "S2")

    @unittest.skipIf(not MODULE_EXISTS, "dp_response_contract not yet implemented")
    def test_input_block(self):
        r = dp.DPResponse(
            response_id="DPR003",
            verdict="INPUT_BLOCK",
            issues=[dp.DPIssue(
                issue_id="I002",
                question="缺少剧本事实F003的可见性分类",
                bound_to_segment="SEG1",
                fidelity_class="LOCKED",
            )],
        )
        self.assertEqual(r.verdict, "INPUT_BLOCK")

    @unittest.skipIf(not MODULE_EXISTS, "dp_response_contract not yet implemented")
    def test_invalid_verdict_rejected(self):
        with self.assertRaises(ValueError):
            dp.DPResponse(response_id="x", verdict="REJECT_ALL")

    @unittest.skipIf(not MODULE_EXISTS, "dp_response_contract not yet implemented")
    def test_directed_question_requires_bound_issue(self):
        with self.assertRaises(dp.DPResponseViolation):
            dp.DPResponse(response_id="DPR-EMPTY", verdict="DIRECTED_QUESTION")

    @unittest.skipIf(not MODULE_EXISTS, "dp_response_contract not yet implemented")
    def test_dp_cannot_redirect_creative_solution(self):
        with self.assertRaises(dp.DPResponseViolation):
            dp.DPIssue(
                issue_id="I-REDIRECT",
                question="Must use 35mm and rewrite the whole scene.",
                bound_to_shot="S2",
            )

    @unittest.skipIf(not MODULE_EXISTS, "dp_response_contract not yet implemented")
    def test_response_is_bound_to_current_manifest_and_scope(self):
        manifest = dm.create_dp_packet_manifest("DPM-RESPONSE", {"storyboard_view": "panel"}, context_id="CTX-R")
        response = dp.DPResponse(
            response_id="DPR-R", verdict="DIRECTED_QUESTION", context_id="CTX-R",
            manifest_sha256=manifest.content_sha256,
            issues=[dp.DPIssue(issue_id="I-R", question="Is the current surface visible?", bound_to_segment="SEG1", bound_to_shot="S2")],
        )
        response.validate_against_manifest(manifest, available_scope_keys=("segment:SEG1", "shot:S2"))
        with self.assertRaises(dp.DPResponseViolation):
            response.validate_against_manifest(manifest, available_scope_keys=("segment:SEG1",))


if __name__ == "__main__":
    unittest.main()
