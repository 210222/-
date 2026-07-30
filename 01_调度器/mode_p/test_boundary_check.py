"""Tests for boundary_check.py — boundary ID chain and state key continuity."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from boundary_check import BoundaryIssue, check_boundaries
from master_compiler import compile_to_file


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_boundary_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


def _compile(master_text: str, label: str) -> Path:
    p = _tmpdir() / f"{label}_master.md"
    p.write_text(master_text, encoding="utf-8")
    manifest_p = _tmpdir() / f"{label}_manifest.json"
    compile_to_file(p, manifest_p)
    return manifest_p


def _tampered_boundary_manifest(label: str) -> Path:
    """Bypass the compiler's early guard to unit-test the downstream checker."""
    manifest_path = _compile(_BAD_BOUNDARY_IDS.replace("BAD-9", "BAD-1"), label)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["shots"][1]["entry_boundary_id"] = "BAD-9"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


# Fixtures
_VALID_TWO_SHOT = """\
<!-- template: director_master v1.0 -->

Master 版本：EP14/v1.0

## Shot EP14-1 | 5s

剧本事实：[D] A runs from door to mid-room.
原文定位：[M] EP14 L1-L3
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <action_chase>
时间控制：[M] <half_second_nodes>

开场状态键：[M]
  - character:A position:door facing:S screen_direction:left_to_right posture:standing
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:prepare

结束状态键：[M]
  - character:A position:mid_room facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] From black.
剪辑触发：[D] A starts.
交出边界 ID：[M] EP14-2
边界连续性：[M] <continuous>
交出边界：[D] A reaches mid-room.
转场执行：[M] <post_production>
生成模式：[M] <omni_reference>
参考资产：[M] [char_runner_01|identity]
参考职责：[D] char_runner_01 constrains identity.
参考优先级：[D] Identity first.

## Shot EP14-2 | 10s

剧本事实：[D] A continues running and stops.
原文定位：[M] EP14 L4-L6
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <action_chase>
时间控制：[M] <half_second_nodes>

开场状态键：[M]
  - character:A position:mid_room facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel

结束状态键：[M]
  - character:A position:far_end facing:S screen_direction:left_to_right posture:stopped
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:recover

进入边界 ID：[M] EP14-1
进入边界：[D] From EP14-1.
剪辑触发：[D] A stops.
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] A stands.
转场执行：[M] <post_production>
生成模式：[M] <omni_reference>
参考资产：[M] [char_runner_01|continuity]
参考职责：[D] char_runner_01 constrains continuity.
参考优先级：[D] Continuity first.
"""

_VALID_SINGLE_SHOT = """\
<!-- template: director_master v1.0 -->

Master 版本：TEST/v1.0

## Shot TEST-1 | 8s

剧本事实：[D] Miguel stands.
原文定位：[M] TEST L1-L3
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

开场状态键：[M]
  - character:Miguel position:desk_front facing:N screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - light_main direction:top color_temp:5000K ratio:1:2
  - action_phase:static

结束状态键：[M]
  - character:Miguel position:desk_front facing:NE screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - light_main direction:top color_temp:5000K ratio:1:2
  - action_phase:static

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] Fade in.
剪辑触发：[D] Hard cut.
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] Cut.
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] None.
参考优先级：[D] None.
"""

_BAD_BOUNDARY_IDS = """\
<!-- template: director_master v1.0 -->

Master 版本：BAD/v1.0

## Shot BAD-1 | 5s

剧本事实：[D] x
原文定位：[M] BAD L1-L1
生成单元：[M] x
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>

开场状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:static

结束状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:static

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] BAD-2
边界连续性：[M] <continuous>
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] x
参考优先级：[D] x

## Shot BAD-2 | 5s

剧本事实：[D] y
原文定位：[M] BAD L2-L2
生成单元：[M] x
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>

开场状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:static

结束状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:static

进入边界 ID：[M] BAD-9
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] x
参考优先级：[D] x
"""

_PROP_DISCONTINUITY = """\
<!-- template: director_master v1.0 -->

Master 版本：PROP/v1.0

## Shot PROP-1 | 5s

剧本事实：[D] x
原文定位：[M] PROP L1-L1
生成单元：[M] x
场景表达：[M] <investigation_object>
时间控制：[M] <event_nodes>

开场状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - prop:key held_by:A location:right_hand
  - light_main direction:top color_temp:4000K ratio:1:2
  - action_phase:static

结束状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - prop:key held_by:A location:right_hand
  - light_main direction:top color_temp:4000K ratio:1:2
  - action_phase:static

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] PROP-2
边界连续性：[M] <continuous>
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] x
参考优先级：[D] x

## Shot PROP-2 | 5s

剧本事实：[D] y
原文定位：[M] PROP L2-L2
生成单元：[M] x
场景表达：[M] <investigation_object>
时间控制：[M] <event_nodes>

开场状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - prop:key held_by:none location:table
  - light_main direction:top color_temp:4000K ratio:1:2
  - action_phase:static

结束状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - prop:key held_by:none location:table
  - light_main direction:top color_temp:4000K ratio:1:2
  - action_phase:static

进入边界 ID：[M] PROP-1
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] x
参考优先级：[D] x
"""

_LIGHT_JUMP = """\
<!-- template: director_master v1.0 -->

Master 版本：LIGHT/v1.0

## Shot LIGHT-1 | 5s

剧本事实：[D] x
原文定位：[M] LIGHT L1-L1
生成单元：[M] x
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>

开场状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:left color_temp:5600K ratio:1:2
  - action_phase:static

结束状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:left color_temp:5600K ratio:1:2
  - action_phase:static

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] LIGHT-2
边界连续性：[M] <continuous>
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] x
参考优先级：[D] x

## Shot LIGHT-2 | 5s

剧本事实：[D] y
原文定位：[M] LIGHT L2-L2
生成单元：[M] x
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>

开场状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:right color_temp:3200K ratio:1:4
  - action_phase:static

结束状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:right color_temp:3200K ratio:1:4
  - action_phase:static

进入边界 ID：[M] LIGHT-1
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] x
参考优先级：[D] x
"""


class BoundaryCheckTests(unittest.TestCase):
    """Test boundary checking on manifest files."""

    def test_single_shot_passes(self) -> None:
        mp = _compile(_VALID_SINGLE_SHOT, "bc1")
        report = check_boundaries(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_two_shot_clean_chain_passes(self) -> None:
        mp = _compile(_VALID_TWO_SHOT, "bc2")
        report = check_boundaries(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_bad_boundary_ids_detected(self) -> None:
        mp = _tampered_boundary_manifest("bc3")
        report = check_boundaries(mp)
        self.assertFalse(report.ok)
        ids = [i.category for i in report.issues]
        self.assertIn("boundary_id", ids)

    def test_prop_discontinuity_detected(self) -> None:
        mp = _compile(_PROP_DISCONTINUITY, "bc4")
        report = check_boundaries(mp)
        self.assertFalse(report.ok)
        prop_issues = [i for i in report.issues if i.category == "prop"]
        self.assertTrue(len(prop_issues) > 0, f"No prop issues found: {report.issues}")

    def test_light_jump_detected(self) -> None:
        mp = _compile(_LIGHT_JUMP, "bc5")
        report = check_boundaries(mp)
        self.assertFalse(report.ok)
        cats = {i.category for i in report.issues}
        self.assertTrue({"light"}.intersection(cats), f"No light issues: {report.issues}")

    def test_action_phase_invalid_transition_detected(self) -> None:
        marker = "## Shot EP14-2"
        head, tail = _VALID_TWO_SHOT.split(marker, 1)
        tail = tail.replace("  - action_phase:travel", "  - action_phase:impact", 1)
        mp = _compile(head + marker + tail, "bc6")
        report = check_boundaries(mp)
        self.assertTrue(any(
            issue.category == "action_phase" for issue in report.issues
        ))

    def test_screen_direction_reversal_detected_independently_of_facing(self) -> None:
        marker = "## Shot EP14-2"
        head, tail = _VALID_TWO_SHOT.split(marker, 1)
        tail = tail.replace(
            "screen_direction:left_to_right",
            "screen_direction:right_to_left",
            1,
        )
        mp = _compile(head + marker + tail, "bc_direction")
        report = check_boundaries(mp)
        self.assertTrue(any(issue.category == "direction" for issue in report.issues))

    def test_small_color_temperature_jump_is_not_hidden(self) -> None:
        marker = "## Shot LIGHT-2"
        head, tail = _LIGHT_JUMP.split(marker, 1)
        tail = tail.replace("color_temp:3200K", "color_temp:5500K")
        tail = tail.replace("direction:right", "direction:left")
        tail = tail.replace("ratio:1:4", "ratio:1:2")
        mp = _compile(head + marker + tail, "bc_small_light_jump")
        report = check_boundaries(mp)
        self.assertTrue(any(
            issue.category == "light" and "color_temp_k" in issue.detail
            for issue in report.issues
        ))

    def test_light_ratio_jump_detected(self) -> None:
        marker = "## Shot LIGHT-2"
        head, tail = _LIGHT_JUMP.split(marker, 1)
        tail = tail.replace("color_temp:3200K", "color_temp:5600K")
        tail = tail.replace("direction:right", "direction:left")
        mp = _compile(head + marker + tail, "bc_light_ratio")
        report = check_boundaries(mp)
        self.assertTrue(any(
            issue.category == "light" and "ratio" in issue.detail
            for issue in report.issues
        ))

    def test_invalid_manifest_returns_report_instead_of_crashing(self) -> None:
        path = _tmpdir() / "invalid_manifest.json"
        path.write_text('{"shots": "wrong"}', encoding="utf-8")
        report = check_boundaries(path)
        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].category, "manifest")

    def test_elliptical_boundary_defers_state_delta_to_dp(self) -> None:
        changed = _VALID_TWO_SHOT.replace(
            "边界连续性：[M] <continuous>",
            "边界连续性：[M] <elliptical>",
            1,
        )
        marker = "## Shot EP14-2"
        head, tail = changed.split(marker, 1)
        tail = tail.replace("position:mid_room", "position:desk_side", 1)
        tail = tail.replace("action_phase:travel", "action_phase:prepare", 1)
        mp = _compile(head + marker + tail, "bc_elliptical")
        report = check_boundaries(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_nonfinal_scene_exit_mode_rejected(self) -> None:
        bad = _VALID_TWO_SHOT.replace(
            "边界连续性：[M] <continuous>",
            "边界连续性：[M] <scene_exit>",
            1,
        )
        mp = _compile(bad, "bc_early_exit")
        report = check_boundaries(mp)
        self.assertTrue(any(
            issue.category == "boundary_continuity" for issue in report.issues
        ))

    def test_final_shot_requires_scene_exit_mode(self) -> None:
        bad = _VALID_SINGLE_SHOT.replace(
            "边界连续性：[M] <scene_exit>",
            "边界连续性：[M] <continuous>",
        )
        mp = _compile(bad, "bc_final_mode")
        report = check_boundaries(mp)
        self.assertTrue(any(
            issue.category == "boundary_continuity" for issue in report.issues
        ))

    def test_specific_boundary_issue_details(self) -> None:
        mp = _tampered_boundary_manifest("bc7")
        report = check_boundaries(mp)
        detail_texts = [i.detail for i in report.issues]
        # Shot BAD-2 entry is BAD-9, should be BAD-1
        self.assertTrue(any("BAD-9" in d for d in detail_texts),
                        f"No BAD-9 mention in: {detail_texts}")


class CLITests(unittest.TestCase):
    def test_cli_pass_exits_zero(self) -> None:
        import subprocess
        import sys
        mp = _compile(_VALID_TWO_SHOT, "cli_bc1")
        result = subprocess.run(
            [sys.executable, "-m", "boundary_check", str(mp)],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn("passed", result.stdout)

    def test_cli_fail_exits_nonzero(self) -> None:
        import subprocess
        import sys
        mp = _tampered_boundary_manifest("cli_bc2")
        result = subprocess.run(
            [sys.executable, "-m", "boundary_check", str(mp)],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
