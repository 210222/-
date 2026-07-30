"""V2.3 Positive Closure & Negative Route — high-risk surface safeguards."""

import unittest

try:
    from mode_p_vnext.schema.visibility_contract import VisibilityContract
    from mode_p_vnext import positive_closure as pc
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class PositiveClosureTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "positive_closure not yet implemented")
    def test_contract_with_closure_passes(self):
        c = VisibilityContract(
            visible_whitelist=["后壳", "镜头模组"],
            positive_closure=["后壳保持完整不透明实体表面"],
            forbidden_qa=["界面出现在后壳"],
        )
        violations = pc.check_positive_closure(c)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "positive_closure not yet implemented")
    def test_forbidden_without_closure_fails(self):
        """forbidden_qa without positive_closure is a risk — negation alone is weak."""
        c = VisibilityContract(
            visible_whitelist=["后壳"],
            forbidden_qa=["不要透明后壳"],  # negation without positive closure
        )
        violations = pc.check_positive_closure(c)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "positive_closure not yet implemented")
    def test_high_risk_surface_must_have_closure(self):
        """Transparent surface risk items must have positive closure."""
        c = VisibilityContract(
            visible_whitelist=["手机屏幕", "后壳"],
            leakage_risks=["后壳被透明化"],
            positive_closure=["手机屏幕保持不透明"],  # only screen, not back-shell
        )
        violations = pc.check_positive_closure(c)
        # back-shell is in leakage_risks but not in positive_closure
        self.assertGreater(len(violations), 0)


class NegativeRouteTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "positive_closure not yet implemented")
    def test_inline_route_requires_warning(self):
        c = VisibilityContract(
            visible_whitelist=["x"],
            negative_route="inline",
            forbidden_qa=["不要漩涡"],
        )
        warnings = pc.check_negative_route(c)
        self.assertGreater(len(warnings), 0)

    @unittest.skipIf(not MODULE_EXISTS, "positive_closure not yet implemented")
    def test_separate_channel_no_warning(self):
        c = VisibilityContract(
            visible_whitelist=["x"],
            negative_route="separate_channel",
        )
        warnings = pc.check_negative_route(c)
        self.assertEqual(len(warnings), 0)

    @unittest.skipIf(not MODULE_EXISTS, "positive_closure not yet implemented")
    def test_token_leakage_risk_flagged(self):
        c = VisibilityContract(
            visible_whitelist=["后壳"],
            negative_route="token_leakage_risk",
            forbidden_qa=["禁止UI"],
        )
        warnings = pc.check_negative_route(c)
        self.assertGreater(len(warnings), 0)

    @unittest.skipIf(not MODULE_EXISTS, "positive_closure not yet implemented")
    def test_human_qa_only_requires_documentation(self):
        c = VisibilityContract(
            visible_whitelist=["x"],
            negative_route="human_qa_only",
        )
        warnings = pc.check_negative_route(c)
        # human_qa_only is acceptable if documented
        self.assertGreater(len(warnings), 0)


if __name__ == "__main__":
    unittest.main()
