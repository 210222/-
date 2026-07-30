"""V8.1 Four Golden Case Structured Registration — R1.2 extended tests.

Verifies:
- 4 Golden cases registered with required fields
- Hashes match V0.5 fixture registry
- Section references are correct (prep_area→§9, alley→§8)
- user_statement and audit_classification are separate
- prep_area_no_cut_fact is correctly stated
"""

import unittest

try:
    from mode_p_vnext import golden_registration as gr
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


REQUIRED_CASE_KEYS = {
    "scene_name", "episode",
    "storyboard_prompt_ref", "video_prompt_ref",
    "storyboard_image_sha256", "video_sha256",
    "user_statement", "audit_classification",
    "evidence_roles",
}


class GoldenRegistrationStructureTests(unittest.TestCase):
    """Verify 4 cases exist with required structure."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_four_cases_registered(self):
        cases = gr.GOLDEN_CASES
        self.assertEqual(len(cases), 4)
        self.assertIn("gun_barrel_ep8", cases)
        self.assertIn("audience_ep6", cases)
        self.assertIn("prep_area_ep6", cases)
        self.assertIn("alley_ep6", cases)

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_each_case_has_all_required_keys(self):
        for case_id, case in gr.GOLDEN_CASES.items():
            with self.subTest(case=case_id):
                missing = REQUIRED_CASE_KEYS - set(case.keys())
                self.assertEqual(len(missing), 0,
                                 f"{case_id}: missing keys: {missing}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_user_statement_and_audit_classification_separate(self):
        """R1.2: user_statement and audit_classification must be distinct fields."""
        for case_id, case in gr.GOLDEN_CASES.items():
            with self.subTest(case=case_id):
                stmt = case["user_statement"]
                cls_text = case["audit_classification"]
                self.assertIsInstance(stmt, str)
                self.assertIsInstance(cls_text, str)
                self.assertGreater(len(stmt.strip()), 0,
                                   f"{case_id}: user_statement empty")
                self.assertGreater(len(cls_text.strip()), 0,
                                   f"{case_id}: audit_classification empty")
                self.assertIn("INFERENCE", cls_text,
                              f"{case_id}: audit_classification must be labeled INFERENCE")

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_hashes_match_v0_5_fixtures(self):
        from mode_p_vnext.golden_fixture_registry import GOLDEN_SCENES
        for case_id, case in gr.GOLDEN_CASES.items():
            fixture = GOLDEN_SCENES[case_id]
            self.assertEqual(case["storyboard_image_sha256"],
                             fixture["storyboard_image"]["sha256"])
            self.assertEqual(case["video_sha256"],
                             fixture["video"]["sha256"])


class SectionReferenceAccuracyTests(unittest.TestCase):
    """R1.2: Verify cross-references point to correct evidence report sections.

    Evidence report structure: §6=枪管 §7=观众席 §8=窄巷(alley) §9=备赛区(prep_area)
    """

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_gun_barrel_references_section_6(self):
        case = gr.GOLDEN_CASES["gun_barrel_ep8"]
        self.assertIn("§6.2", case["storyboard_prompt_ref"])
        self.assertIn("§6.4", case["video_prompt_ref"])

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_audience_references_section_7(self):
        case = gr.GOLDEN_CASES["audience_ep6"]
        self.assertIn("§7.2", case["storyboard_prompt_ref"])
        self.assertIn("§7.4", case["video_prompt_ref"])

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_prep_area_references_section_9(self):
        """Regression: was incorrectly §8.2/§8.4 — prep_area is §9 in evidence report."""
        case = gr.GOLDEN_CASES["prep_area_ep6"]
        self.assertIn("§9.2", case["storyboard_prompt_ref"],
                      "prep_area sb must reference §9.2 (not §8.2)")
        self.assertIn("§9.4", case["video_prompt_ref"],
                      "prep_area video must reference §9.4 (not §8.4)")

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_alley_references_section_8(self):
        """Regression: was incorrectly §9.2/§9.4 — alley is §8 in evidence report."""
        case = gr.GOLDEN_CASES["alley_ep6"]
        self.assertIn("§8.2", case["storyboard_prompt_ref"],
                      "alley sb must reference §8.2 (not §9.2)")
        self.assertIn("§8.4", case["video_prompt_ref"],
                      "alley video must reference §8.4 (not §9.4)")


class PrepAreaNoCutFactRegistrationTests(unittest.TestCase):
    """R1.2: prep_area registration must not claim design had internal cuts."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_prep_area_user_statement_does_not_claim_lost_cuts(self):
        case = gr.GOLDEN_CASES["prep_area_ep6"]
        stmt = case["user_statement"]
        self.assertNotIn("丢失内部切镜", stmt,
                         "prep_area user_statement must NOT claim '丢失内部切镜'")
        self.assertNotIn("合并为单一无切镜", stmt,
                         "prep_area user_statement must NOT claim '合并为单一无切镜'")

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_prep_area_audit_classification_confirms_no_cut(self):
        case = gr.GOLDEN_CASES["prep_area_ep6"]
        cls_text = case["audit_classification"]
        self.assertIn("固定机位", cls_text,
                      "classification must confirm fixed camera position")
        self.assertNotIn("丢失内部切镜", cls_text,
                         "classification must NOT claim cuts were 'lost'")

    @unittest.skipIf(not MODULE_EXISTS, "golden_registration not yet implemented")
    def test_prep_area_evidence_roles_exclude_missing_cut(self):
        case = gr.GOLDEN_CASES["prep_area_ep6"]
        roles = case["evidence_roles"]
        self.assertNotIn("missing_internal_cut_diagnostic", roles,
                         "evidence_roles must NOT include 'missing_internal_cut_diagnostic'")


if __name__ == "__main__":
    unittest.main()
