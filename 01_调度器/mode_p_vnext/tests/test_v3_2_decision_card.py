"""V3.2 Atomic Claim/Decision Card Schema."""

import unittest

try:
    from mode_p_vnext.schema import decision_card as dc
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DecisionCardTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "decision_card not yet implemented")
    def test_card_required_fields(self):
        card = dc.DecisionCard(
            card_id="DC001",
            claim="推镜比切镜更能保持注意力连续",
            source_quality="golden_evidence",
            render_evidence=["枪管EP8视频验证"],
            applicability_conditions=["单一主体", "注意力路径明确"],
            counter_examples=["多主体场景推镜可能造成迷失"],
        )
        self.assertEqual(card.card_id, "DC001")
        self.assertEqual(card.source_quality, "golden_evidence")
        self.assertEqual(card.cross_scene_repeat, 1)

    @unittest.skipIf(not MODULE_EXISTS, "decision_card not yet implemented")
    def test_source_quality_must_be_valid(self):
        with self.assertRaises(ValueError):
            dc.DecisionCard(card_id="x", claim="x", source_quality="imaginary")

    @unittest.skipIf(not MODULE_EXISTS, "decision_card not yet implemented")
    def test_counter_examples_required_for_uncertain_source(self):
        card = dc.DecisionCard(
            card_id="DC2", claim="test",
            source_quality="user_opinion",
            render_evidence=["some"],
            applicability_conditions=["cond"],
            counter_examples=[],  # empty — should warn
        )
        warnings = dc.validate_decision_card(card)
        self.assertGreater(len(warnings), 0)

    @unittest.skipIf(not MODULE_EXISTS, "decision_card not yet implemented")
    def test_user_approval_recorded(self):
        card = dc.DecisionCard(
            card_id="DC3", claim="x",
            source_quality="cross_project",
            user_approved=True,
            user_approval_note="EP13验收通过",
        )
        self.assertTrue(card.user_approved)

    @unittest.skipIf(not MODULE_EXISTS, "decision_card not yet implemented")
    def test_cross_scene_repeat_tracking(self):
        card = dc.DecisionCard(
            card_id="DC4", claim="x",
            source_quality="golden_evidence",
            cross_scene_repeat=3,
        )
        self.assertEqual(card.cross_scene_repeat, 3)

    @unittest.skipIf(not MODULE_EXISTS, "decision_card not yet implemented")
    def test_to_dict(self):
        card = dc.DecisionCard(
            card_id="DC1", claim="测试声明",
            source_quality="golden_evidence",
        )
        d = card.to_dict()
        self.assertEqual(d["card_id"], "DC1")
        self.assertIn("source_quality", d)


if __name__ == "__main__":
    unittest.main()
