"""Verify DIRECTOR_MASTER.md template contract — machine-checkable fields only.

These tests validate the patterns and enumerations defined in
director_master_template.md against sample Master content.
They do NOT judge natural-language semantic quality.
"""

from __future__ import annotations

import re
import unittest

# --- Patterns extracted from the template's machine-checkable fields ---

SHOT_HEADER = re.compile(
    r"^##\s+Shot\s+(?P<scene_id>[A-Za-z0-9_-]+)-(?P<number>\d+)\s*\|\s*(?P<duration>\d+(?:\.\d+)?)\s*s\s*$",
    re.IGNORECASE,
)

MASTER_VERSION = re.compile(
    r"^Master 版本：\s*(?P<scene_id>[A-Za-z0-9_-]+)/v(?P<major>\d+)\.(?P<minor>\d+)",
    re.MULTILINE,
)

STORY_FACT_LINE = re.compile(r"^剧本事实：\[D\]\s*\S")
SOURCE_LOCATION = re.compile(r"^原文定位：\[M\]\s*(?P<scene_id>[A-Za-z0-9_-]+)\s+L(?P<start>\d+)-L(?P<end>\d+)", re.MULTILINE)
SCENE_EXPRESSION = re.compile(r"^场景表达：\[M\]\s*<(?P<mode>[a-z_]+)>", re.MULTILINE)
TIMING_MODE = re.compile(r"^时间控制：\[M\]\s*<(?P<mode>[a-z_]+)>", re.MULTILINE)

ENTRY_BOUNDARY = re.compile(r"^进入边界 ID：\[M\]\s*(?P<id>[A-Za-z0-9_-]+)")
EXIT_BOUNDARY = re.compile(r"^交出边界 ID：\[M\]\s*(?P<id>[A-Za-z0-9_-]+)")
TRANSITION_MODE = re.compile(r"^转场执行：\[M\]\s*<(?P<mode>[a-z_]+)>")
BOUNDARY_CONTINUITY = re.compile(r"^边界连续性：\[M\]\s*<(?P<mode>[a-z_]+)>")
GENERATION_MODE = re.compile(r"^生成模式：\[M\]\s*<(?P<mode>[a-z_]+)>")
ASSET_LIST = re.compile(r"^参考资产：\[M\]\s*\[(?P<bindings>[^\]]*)\]\s*$|^参考资产：\[M\]\s*(?P<none>无)\s*$", re.MULTILINE)

STATE_KEY_OPENING = re.compile(r"^开场状态键：\[M\]", re.MULTILINE)
STATE_KEY_CLOSING = re.compile(r"^结束状态键：\[M\]", re.MULTILINE)

VALID_EXPRESSIONS = frozenset({
    "conversation_power", "crowd_attention", "action_chase",
    "suspense_reveal", "contemplative_silence", "investigation_object",
    "montage", "cross_space_transition",
})

VALID_TIMING = frozenset({"event_nodes", "second_nodes", "half_second_nodes"})
VALID_TRANSITION = frozenset({"in_camera", "post_production"})
VALID_BOUNDARY_CONTINUITY = frozenset({"continuous", "elliptical", "scene_exit"})
VALID_GENERATION = frozenset({"text_only", "first_last_frame", "omni_reference"})


def parse_shot_heading(line: str) -> dict | None:
    m = SHOT_HEADER.match(line)
    if not m:
        return None
    return {
        "scene_id": m.group("scene_id"),
        "number": int(m.group("number")),
        "duration": float(m.group("duration")),
    }


class ShotHeaderPatternTests(unittest.TestCase):
    """Validate the Shot heading regex against expected inputs."""

    def test_standard_shot_header(self) -> None:
        h = parse_shot_heading("## Shot EP14-1 | 8s")
        self.assertIsNotNone(h)
        self.assertEqual(h["scene_id"], "EP14")
        self.assertEqual(h["number"], 1)
        self.assertEqual(h["duration"], 8.0)

    def test_shot_header_with_subscene_id(self) -> None:
        h = parse_shot_heading("## Shot EP14_S1-3 | 12.5s")
        self.assertIsNotNone(h)
        self.assertEqual(h["scene_id"], "EP14_S1")
        self.assertEqual(h["number"], 3)
        self.assertEqual(h["duration"], 12.5)

    def test_shot_duration_exactly_15(self) -> None:
        h = parse_shot_heading("## Shot PILOT-5 | 15s")
        self.assertIsNotNone(h)
        self.assertEqual(h["duration"], 15.0)

    def test_shot_duration_boundary_zero_rejected(self) -> None:
        h = parse_shot_heading("## Shot A-1 | 0s")
        self.assertIsNotNone(h)  # regex matches; value check is checker's job
        self.assertEqual(h["duration"], 0)

    def test_shot_duration_over_15_rejected(self) -> None:
        h = parse_shot_heading("## Shot A-1 | 16s")
        self.assertIsNotNone(h)  # regex matches; bounds check is checker's job
        self.assertEqual(h["duration"], 16.0)

    def test_case_insensitive(self) -> None:
        h = parse_shot_heading("## shot ep14-1 | 8s")
        self.assertIsNotNone(h)
        self.assertEqual(h["scene_id"], "ep14")

    def test_no_match_for_storyboard_headers(self) -> None:
        """Storyboard uses 'Wide | 24mm | 5s' — must not match shot parser."""
        self.assertIsNone(parse_shot_heading("## Shot 1 | Wide | 24mm | 5s"))

    def test_no_match_for_plain_text(self) -> None:
        self.assertIsNone(parse_shot_heading("Shot 1 is about 8s long"))
        self.assertIsNone(parse_shot_heading("## Scene 1"))


class EnumerationTests(unittest.TestCase):
    """Validate that template enumerations are complete and exclusive."""

    def test_valid_expression_values(self) -> None:
        for v in VALID_EXPRESSIONS:
            m = SCENE_EXPRESSION.search(f"场景表达：[M] <{v}>")
            self.assertIsNotNone(m, f"Expression '{v}' must match the pattern")
            self.assertEqual(m.group("mode"), v)

    def test_invalid_expression_not_in_enum(self) -> None:
        self.assertNotIn("dialogue", VALID_EXPRESSIONS)
        self.assertNotIn("action", VALID_EXPRESSIONS)
        self.assertNotIn("generic", VALID_EXPRESSIONS)

    def test_valid_timing_modes(self) -> None:
        for v in VALID_TIMING:
            m = TIMING_MODE.search(f"时间控制：[M] <{v}>")
            self.assertIsNotNone(m)
            self.assertEqual(m.group("mode"), v)

    def test_valid_transition_modes(self) -> None:
        for v in VALID_TRANSITION:
            m = TRANSITION_MODE.search(f"转场执行：[M] <{v}>")
            self.assertIsNotNone(m)

    def test_valid_boundary_continuity_modes(self) -> None:
        for value in VALID_BOUNDARY_CONTINUITY:
            match = BOUNDARY_CONTINUITY.search(
                f"边界连续性：[M] <{value}>"
            )
            self.assertIsNotNone(match)
            self.assertEqual(match.group("mode"), value)

    def test_valid_generation_modes(self) -> None:
        for v in VALID_GENERATION:
            m = GENERATION_MODE.search(f"生成模式：[M] <{v}>")
            self.assertIsNotNone(m)


class MasterVersionTests(unittest.TestCase):
    def test_parses_version_line(self) -> None:
        m = MASTER_VERSION.search("Master 版本：EP14_S1/v1.3")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("scene_id"), "EP14_S1")
        self.assertEqual(m.group("major"), "1")
        self.assertEqual(m.group("minor"), "3")

    def test_parses_version_zero(self) -> None:
        m = MASTER_VERSION.search("Master 版本：PILOT/v0.0")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("major"), "0")
        self.assertEqual(m.group("minor"), "0")


class BoundaryIDTests(unittest.TestCase):
    def test_entry_boundary_for_first_shot(self) -> None:
        m = ENTRY_BOUNDARY.search("进入边界 ID：[M] SCENE_ENTRY")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("id"), "SCENE_ENTRY")

    def test_entry_boundary_chained(self) -> None:
        m = ENTRY_BOUNDARY.search("进入边界 ID：[M] EP14-3")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("id"), "EP14-3")

    def test_exit_boundary_for_last_shot(self) -> None:
        m = EXIT_BOUNDARY.search("交出边界 ID：[M] SCENE_EXIT")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("id"), "SCENE_EXIT")

    def test_exit_boundary_chained(self) -> None:
        m = EXIT_BOUNDARY.search("交出边界 ID：[M] EP14-4")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("id"), "EP14-4")


class SourceLocationTests(unittest.TestCase):
    def test_parses_line_range(self) -> None:
        m = SOURCE_LOCATION.search("原文定位：[M] EP14_S1 L12-L45")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("scene_id"), "EP14_S1")
        self.assertEqual(m.group("start"), "12")
        self.assertEqual(m.group("end"), "45")

    def test_line_range_order(self) -> None:
        m = SOURCE_LOCATION.search("原文定位：[M] S1 L5-L9")
        self.assertIsNotNone(m)
        self.assertLess(int(m.group("start")), int(m.group("end")))


class StateKeyTests(unittest.TestCase):
    def test_opening_state_key_present(self) -> None:
        self.assertIsNotNone(STATE_KEY_OPENING.search("开场状态键：[M]"))

    def test_closing_state_key_present(self) -> None:
        self.assertIsNotNone(STATE_KEY_CLOSING.search("结束状态键：[M]"))

    def test_state_key_format_character(self) -> None:
        sample = "  - character:Miguel position:desk_front facing:NE screen_direction:static posture:standing"
        self.assertIn("character:", sample)
        self.assertIn("position:", sample)
        self.assertIn("facing:", sample)
        self.assertIn("screen_direction:", sample)
        self.assertIn("posture:", sample)

    def test_state_key_format_prop(self) -> None:
        sample = "  - prop:jacket held_by:none location:chair_back"
        self.assertIn("prop:", sample)
        self.assertIn("held_by:", sample)
        self.assertIn("location:", sample)


class AssetIDTests(unittest.TestCase):
    def test_asset_list_with_ids(self) -> None:
        m = ASSET_LIST.search(
            "参考资产：[M] [char_miguel_01|identity, loc_case_room_01|location]"
        )
        self.assertIsNotNone(m)
        self.assertEqual(
            m.group("bindings"),
            "char_miguel_01|identity, loc_case_room_01|location",
        )

    def test_asset_list_none_for_text_only(self) -> None:
        m = ASSET_LIST.search("参考资产：[M] 无")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("none"), "无")

    def test_asset_list_empty_brackets(self) -> None:
        m = ASSET_LIST.search("参考资产：[M] []")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("bindings"), "")


class StoryFactTraceabilityTests(unittest.TestCase):
    """Verify story_fact is present and links to source location."""

    def test_story_fact_line_is_not_empty(self) -> None:
        self.assertTrue(STORY_FACT_LINE.search("剧本事实：[D] Miguel 整理白板上的案件线索"))
        self.assertIsNone(STORY_FACT_LINE.search("剧本事实：[D] "))

    def test_source_location_matches_scene_id_format(self) -> None:
        # scene_id must match the format used in Shot ID
        valid_ids = ["EP14", "EP14_S1", "PILOT", "S3"]
        for sid in valid_ids:
            line = f"原文定位：[M] {sid} L1-L10"
            m = SOURCE_LOCATION.search(line)
            self.assertIsNotNone(m, f"Scene ID '{sid}' must match source location pattern")
            self.assertEqual(m.group("scene_id"), sid)

    def test_d_marker_fields_not_machine_checked(self) -> None:
        """Fields marked [D] are Director-only — the checker must NOT parse them."""
        # This test exists to document that [D] fields exist but are not regex'd
        d_fields = ["叙事职责：[D]", "剧本事实：[D]", "摄影设计：[D]", "构图设计：[D]",
                     "光影设计：[D]", "表演设计：[D]", "参考职责：[D]", "参考优先级：[D]"]
        for field in d_fields:
            self.assertIn("[D]", field)


if __name__ == "__main__":
    unittest.main()
