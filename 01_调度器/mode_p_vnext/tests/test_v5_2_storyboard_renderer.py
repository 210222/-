"""R1.3 — Storyboard renderer tests using source-grounded Golden builder."""

import unittest

from mode_p_vnext.fixtures.r1_3.golden_cases import build_golden_deliveries
from mode_p_vnext.storyboard_projection import StoryboardView
from mode_p_vnext.storyboard_renderer import render_storyboard


class GoldenArchetypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deliveries = build_golden_deliveries()
        cls.rendered = {}
        for fid, view in cls.deliveries.items():
            if fid.endswith("_sb"):
                cls.rendered[fid] = render_storyboard(view)

    def test_all_four_sb_render(self):
        for fid in ("gun_barrel_sb", "audience_sb", "prep_area_sb", "alley_sb"):
            self.assertGreater(len(self.rendered[fid]), 100, fid)

    def test_gun_barrel_seated_rico(self):
        out = self.rendered["gun_barrel_sb"]
        self.assertIn("Rico", out)
        self.assertNotIn("站在门口", out)

    def test_gun_barrel_13s(self):
        self.assertIn("13s", self.rendered["gun_barrel_sb"])

    def test_audience_12s(self):
        self.assertIn("12s", self.rendered["audience_sb"])

    def test_prep_iuri_at_5s(self):
        out = self.rendered["prep_area_sb"]
        self.assertIn("5s", out)

    def test_alley_pedro_not_rico(self):
        out = self.rendered["alley_sb"]
        self.assertIn("Pedro", out)
        self.assertNotIn("@Rico", out)

    def test_alley_stationary_car(self):
        out = self.rendered["alley_sb"]
        self.assertIn("静止", out)

    def test_no_fabricated_defaults(self):
        FORBIDDEN = ["紫色文字=镜头标签", "画面同前"]
        for fid, out in self.rendered.items():
            for f in FORBIDDEN:
                self.assertNotIn(f, out, f"{fid}: {f}")

    def test_no_node_count_footers(self):
        for fid, out in self.rendered.items():
            self.assertNotIn("个故事板节点", out)
            self.assertNotIn("个时间线节点", out)


if __name__ == "__main__":
    unittest.main()
