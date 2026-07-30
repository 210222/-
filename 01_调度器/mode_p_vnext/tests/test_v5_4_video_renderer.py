"""R1.3 — Video renderer tests using source-grounded Golden builder."""

import unittest

from mode_p_vnext.fixtures.r1_3.golden_cases import build_golden_deliveries
from mode_p_vnext.video_renderer import render_video_prompt


class GoldenVideoArchetypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deliveries = build_golden_deliveries()
        cls.rendered = {}
        for fid, view in cls.deliveries.items():
            if fid.endswith("_video"):
                cls.rendered[fid] = render_video_prompt(view)

    def test_all_four_video_render(self):
        for fid in ("gun_barrel_video", "audience_video", "prep_area_video", "alley_video"):
            self.assertGreater(len(self.rendered[fid]), 100, fid)

    def test_all_have_upload_refs(self):
        for fid, out in self.rendered.items():
            self.assertIn("@上传参考图", out)

    def test_all_have_prohibitions(self):
        for fid, out in self.rendered.items():
            self.assertIn("@禁止", out)

    def test_gun_barrel_seated_rico(self):
        self.assertIn("Rico", self.rendered["gun_barrel_video"])
        self.assertNotIn("站在门口", self.rendered["gun_barrel_video"])

    def test_audience_12s(self):
        self.assertIn("12s", self.rendered["audience_video"])

    def test_prep_iuri_at_5s(self):
        self.assertIn("5s", self.rendered["prep_area_video"])

    def test_alley_pedro_no_rico(self):
        out = self.rendered["alley_video"]
        self.assertIn("Pedro", out)
        self.assertNotIn("Rico", out)

    def test_alley_stationary_car(self):
        self.assertIn("静止", self.rendered["alley_video"])

    def test_no_fabricated_defaults(self):
        for fid, out in self.rendered.items():
            self.assertNotIn("画面同前", out, f"{fid}")

    def test_no_node_count_footers(self):
        for fid, out in self.rendered.items():
            self.assertNotIn("个时间线节点", out)

    def test_no_a_b_variants(self):
        for fid, out in self.rendered.items():
            self.assertNotIn("方案A", out)
            self.assertNotIn("方案B", out)


if __name__ == "__main__":
    unittest.main()
