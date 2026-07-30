"""V7.1 DP View Whitelist Compiler."""

import unittest

try:
    from mode_p_vnext import dp_view_compiler as dpv
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DPViewCompilerTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "dp_view_compiler not yet implemented")
    def test_includes_allowed_fields(self):
        allowed = dpv.DP_VIEW_WHITELIST
        self.assertIn("script_facts", allowed)
        self.assertIn("storyboard_view", allowed)
        self.assertIn("video_prompt_view", allowed)
        self.assertIn("used_capabilities", allowed)

    @unittest.skipIf(not MODULE_EXISTS, "dp_view_compiler not yet implemented")
    def test_excludes_forbidden_fields(self):
        forbidden = dpv.DP_VIEW_FORBIDDEN
        self.assertIn("master", forbidden)
        self.assertIn("knowledge_packet", forbidden)
        self.assertIn("director_reasoning", forbidden)
        self.assertIn("historical_dp_feedback", forbidden)

    @unittest.skipIf(not MODULE_EXISTS, "dp_view_compiler not yet implemented")
    def test_compile_filters_correctly(self):
        sources = {
            "script_facts": "F001: 枪在桌上",
            "master": "机位: 右侧45°",
            "knowledge_packet": "推镜保持注意力",
            "storyboard_view": "Panel 1...",
            "video_prompt_view": "Shot 1...",
            "director_reasoning": "选择推镜因为...",
            "historical_dp_feedback": "上轮DP说...",
            "used_capabilities": "SD2.0 internal_cuts",
            "asset_text_evidence": "@图片1 hash=abc",
        }
        result = dpv.compile_dp_view(sources)
        self.assertIn("script_facts", result)
        self.assertIn("storyboard_view", result)
        self.assertNotIn("master", result)
        self.assertNotIn("knowledge_packet", result)
        self.assertNotIn("director_reasoning", result)
        self.assertNotIn("historical_dp_feedback", result)

    @unittest.skipIf(not MODULE_EXISTS, "dp_view_compiler not yet implemented")
    def test_review_projections_are_allowed_but_internal_contract_is_not(self):
        sources = {
            "visibility_view": {"shot": "S2", "visible": ["phone back"]},
            "fidelity_view": {"F001": "LOCKED"},
            "handoff_view": {"from": "S1", "to": "S2"},
            "timeline_view": {"S2": "0-2s"},
            "fidelity_contract_internal": {"secret": "not for DP"},
        }
        result = dpv.compile_dp_view(sources)
        self.assertIn("visibility_view", result)
        self.assertNotIn("fidelity_contract_internal", result)

    @unittest.skipIf(not MODULE_EXISTS, "dp_view_compiler not yet implemented")
    def test_strict_view_rejects_forbidden_source(self):
        with self.assertRaises(dpv.DPViewViolation):
            dpv.compile_dp_view({"storyboard_view": "safe", "master": "internal"}, strict=True)

    @unittest.skipIf(not MODULE_EXISTS, "dp_view_compiler not yet implemented")
    def test_strict_view_rejects_unknown_source_instead_of_silently_dropping_it(self):
        with self.assertRaises(dpv.DPViewViolation):
            dpv.compile_dp_view({"storyboard_view": "safe", "unclassified_blob": "unknown"}, strict=True)


if __name__ == "__main__":
    unittest.main()
