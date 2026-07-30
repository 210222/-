"""V2.1 Visibility Contract Schema — visible_whitelist, occluded, narrative_only, etc."""

import unittest

try:
    from mode_p_vnext.schema import visibility_contract as vc
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class VisibilityContractTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_contract_required_fields(self):
        c = vc.VisibilityContract(
            visible_whitelist=["实心哑光深色手机后壳", "镜头模组", "双手"],
            occluded_state=["手机正面由机身完全遮挡"],
            narrative_only=["人物正在进行的游戏内容"],
            audio_only=["画外对白"],
            positive_closure=["后壳保持完整不透明实体表面"],
            forbidden_qa=["未经设计的界面出现在画面"],
        )
        self.assertEqual(len(c.visible_whitelist), 3)
        self.assertEqual(len(c.forbidden_qa), 1)

    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_all_fields_optional(self):
        c = vc.VisibilityContract(visible_whitelist=["仅此一项"])
        self.assertEqual(len(c.visible_whitelist), 1)
        self.assertEqual(c.occluded_state, [])
        self.assertEqual(c.narrative_only, [])

    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_visible_whitelist_must_be_explicit(self):
        """Whitelist must not be empty — implicit 'everything visible' is a design risk."""
        c = vc.VisibilityContract()
        violations = vc.validate_visibility_contract(c)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_no_overlap_between_visible_and_occluded(self):
        """Same item must not appear in both visible_whitelist and occluded_state."""
        c = vc.VisibilityContract(
            visible_whitelist=["手机"],
            occluded_state=["手机"],  # conflict!
        )
        violations = vc.validate_visibility_contract(c)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_no_leakage_from_narrative_to_visible(self):
        """narrative_only items must not appear in visible_whitelist."""
        c = vc.VisibilityContract(
            visible_whitelist=["枪"],
            narrative_only=["枪"],  # leak — should be narrative_only only
        )
        violations = vc.validate_visibility_contract(c)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_negative_route_field(self):
        c = vc.VisibilityContract(
            visible_whitelist=["后壳"],
            negative_route="human_qa_only",
        )
        self.assertEqual(c.negative_route, "human_qa_only")

    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_negative_route_must_be_valid(self):
        with self.assertRaises(ValueError):
            vc.VisibilityContract(
                visible_whitelist=["x"],
                negative_route="impossible_mode",
            )

    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_to_dict(self):
        c = vc.VisibilityContract(
            visible_whitelist=["a", "b"],
            forbidden_qa=["no UI"],
        )
        d = c.to_dict()
        self.assertEqual(d["visible_whitelist"], ["a", "b"])
        self.assertEqual(d["forbidden_qa"], ["no UI"])

    @unittest.skipIf(not MODULE_EXISTS, "visibility_contract not yet implemented")
    def test_canonical_json_stable(self):
        from mode_p_vnext.canonical_serialization import canonical_json_dumps
        c = vc.VisibilityContract(visible_whitelist=["主体", "背景"])
        j1 = canonical_json_dumps(c.to_dict())
        j2 = canonical_json_dumps(c.to_dict())
        self.assertEqual(j1, j2)


if __name__ == "__main__":
    unittest.main()
