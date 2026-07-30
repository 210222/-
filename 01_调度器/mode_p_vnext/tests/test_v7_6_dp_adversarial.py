"""V7.6 adversarial DP textual visibility and redirection safety."""

import unittest

try:
    from mode_p_vnext import dp_adversarial as dpa
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DPAdversarialTests(unittest.TestCase):
    def _view(self):
        return {
            "storyboard_view": "derived panel evidence",
            "video_prompt_view": "derived timing evidence",
            "visibility_view": {"S2": "phone rear surface only"},
            "fidelity_view": {"F001": "LOCKED"},
        }

    @unittest.skipIf(not MODULE_EXISTS, "dp_adversarial not yet implemented")
    def test_phone_back_ui_leak_and_missing_positive_closure_are_reported(self):
        case = dpa.VisibilityReviewCase(
            case_id="PHONE", segment_id="SEG1", shot_id="S2",
            positive_visual_text="A game UI is visible on the rear of the phone.",
            visible_whitelist=("phone back", "hand"),
            narrative_only=("game UI",),
            rear_surface_only=("game UI",),
            leakage_risks=("screen content may leak through rear surface",),
        )
        review = dpa.review_dp_adversarial(self._view(), [case], response_id="DPR-PHONE")
        codes = {issue.issue_code for issue in review.response.issues}
        self.assertEqual(review.validation_level, "TEXT_VALIDATED")
        self.assertEqual(review.response.verdict, "DIRECTED_QUESTION")
        self.assertIn("VISIBLE_SURFACE_LEAK", codes)
        self.assertIn("UNDECLARED_UI_OR_REAR_SURFACE_LEAK", codes)
        self.assertIn("MISSING_POSITIVE_CLOSURE", codes)
        self.assertTrue(all(issue.bound_to_shot == "S2" for issue in review.response.issues))

    @unittest.skipIf(not MODULE_EXISTS, "dp_adversarial not yet implemented")
    def test_occlusion_audio_reflection_future_and_human_qa_leaks_are_reported(self):
        case = dpa.VisibilityReviewCase(
            case_id="MIXED", segment_id="SEG1", shot_id="S3", beat_id="B3", panel=3,
            positive_visual_text=(
                "The occluded witness, offscreen caller, future reveal, forbidden reflection, "
                "rear serial number and QA token are all visible."
            ),
            positive_closure=("opaque rear housing",),
            occluded_only=("occluded witness",),
            audio_only=("offscreen caller",),
            future_only=("future reveal",),
            undeclared_reflection_terms=("forbidden reflection",),
            rear_surface_only=("rear serial number",),
            human_qa_only=("QA token",),
        )
        review = dpa.review_dp_adversarial(self._view(), [case], response_id="DPR-MIXED")
        codes = {issue.issue_code for issue in review.response.issues}
        self.assertTrue({
            "OCCLUDED_STATE_LEAK", "AUDIO_ONLY_VISUAL_LEAK", "VISIBILITY_STATE_TIME_VIOLATION",
            "REFLECTION_PATH_LEAK", "UNDECLARED_UI_OR_REAR_SURFACE_LEAK", "HUMAN_QA_ONLY_LEAK",
        }.issubset(codes))

    @unittest.skipIf(not MODULE_EXISTS, "dp_adversarial not yet implemented")
    def test_clean_text_contract_is_ready_not_visual_claim(self):
        case = dpa.VisibilityReviewCase(
            case_id="CLEAN", segment_id="SEG2", shot_id="S1",
            positive_visual_text="Opaque phone rear housing and the holder's hand remain visible.",
            visible_whitelist=("phone rear housing", "hand"),
            positive_closure=("opaque phone rear housing",),
            leakage_risks=("screen content",),
        )
        review = dpa.review_dp_adversarial(self._view(), [case], response_id="DPR-CLEAN")
        self.assertTrue(review.response.is_ready)
        self.assertEqual(review.validation_level, "TEXT_VALIDATED")

    @unittest.skipIf(not MODULE_EXISTS, "dp_adversarial not yet implemented")
    def test_forbidden_dp_input_is_blocked(self):
        case = dpa.VisibilityReviewCase(
            case_id="SAFE", segment_id="SEG1", shot_id="S1", positive_visual_text="visible hand",
        )
        with self.assertRaises(dpa.DPAdversarialViolation):
            dpa.review_dp_adversarial({"master": "internal"}, [case], response_id="DPR-BAD")

    @unittest.skipIf(not MODULE_EXISTS, "dp_adversarial not yet implemented")
    def test_forward_payload_field_routing_is_checked_without_prompt_negatives(self):
        case = dpa.VisibilityReviewCase(
            case_id="ROUTE", segment_id="SEG3", shot_id="S2", positive_visual_text="opaque rear housing",
            forward_payload_field_ids=("visible.phone_rear", "qa.hidden_ui"),
            allowed_forward_field_ids=("visible.phone_rear",),
            human_qa_only_field_ids=("qa.hidden_ui",),
        )
        review = dpa.review_dp_adversarial(self._view(), [case], response_id="DPR-ROUTE")
        codes = {issue.issue_code for issue in review.response.issues}
        self.assertIn("FORWARD_FIELD_ROUTE_LEAK", codes)
        self.assertIn("HUMAN_QA_ONLY_FIELD_LEAK", codes)


if __name__ == "__main__":
    unittest.main()
