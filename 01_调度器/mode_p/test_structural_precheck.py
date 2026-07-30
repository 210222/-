"""Tests for structural_precheck.py — pre-DP check pipeline."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from master_compiler import compile_to_file
from structural_precheck import run_precheck, run_final_checks


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_precheck_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


_VALID_MASTER = """\
<!-- template: director_master v2.0 -->

Master 版本：PRE/v1.0

场景蓝图：[D] 冷白办公室内，Miguel 位于桌前，画面强调静止观察。
声音基调：[D] 安静室内底噪持续。

## Shot PRE-1 | 8s

剧本事实：[D] Miguel stands at the whiteboard.
原文定位：[M] PRE L1-L3
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

开场状态：[D] Miguel at desk.
开场状态键：[M]
  - character:Miguel position:desk_front facing:N screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - light_main direction:top color_temp:5000K ratio:1:2
  - action_phase:static

动作时间轴：[D] Miguel looks around.
故事板关键帧：[D] - [开场] Miguel 站在桌前。
  - [变化] Miguel 转头观察房间。
  - [结束] Miguel 仍站在桌前。
视频时间轴：[D] [0.0s] Miguel 站在桌前，身体静止。
  [4.0s] Miguel 转头观察房间。
  [8.0s] Miguel 回到桌前视线方向，身体静止。
声音设计：[D] 室内底噪持续，无对白。

结束状态：[D] Miguel still at desk.
结束状态键：[M]
  - character:Miguel position:desk_front facing:NE screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - light_main direction:top color_temp:5000K ratio:1:2
  - action_phase:static

摄影设计：[D] Fixed camera, 24mm.
构图设计：[D] Three layers.
光影设计：[D] Cold light.
表演设计：[D] Hand action.

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


class PrecheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = _tmpdir()

    def test_precheck_passes_on_valid_master(self) -> None:
        master = self.tmp / "master.md"
        master.write_text(_VALID_MASTER, encoding="utf-8")
        session = self.tmp / "session"
        report = run_precheck(master, session)
        self.assertTrue(report.ok, f"Failed: {[(r.name, r.output[:80]) for r in report.results if not r.passed]}")
        self.assertTrue((session / "working" / "SHOT_MANIFEST.json").exists())
        self.assertTrue((session / "working" / "STORYBOARD.md").exists())
        self.assertTrue((session / "working" / "VIDEO_PROMPT.md").exists())

    def test_final_checks_pass_after_precheck(self) -> None:
        master = self.tmp / "master2.md"
        master.write_text(_VALID_MASTER, encoding="utf-8")
        session = self.tmp / "session2"
        pre = run_precheck(master, session)
        self.assertTrue(pre.ok)

        final = run_final_checks(master, session)
        self.assertTrue(final.ok)


class CLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = _tmpdir()

    def test_cli_precheck_pass_exits_zero(self) -> None:
        import subprocess
        import sys
        master = self.tmp / "cli_master.md"
        master.write_text(_VALID_MASTER, encoding="utf-8")
        session = self.tmp / "cli_session"
        result = subprocess.run(
            [sys.executable, "-m", "structural_precheck", "precheck",
             str(master), str(session)],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")

    def test_cli_precheck_bad_master_fails(self) -> None:
        import subprocess
        import sys
        master = self.tmp / "bad_master.md"
        master.write_text("# Not a master\n", encoding="utf-8")
        session = self.tmp / "bad_session"
        result = subprocess.run(
            [sys.executable, "-m", "structural_precheck", "precheck",
             str(master), str(session)],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_run_mode_p_precheck_command(self) -> None:
        import subprocess
        import sys
        master = self.tmp / "rmp_master.md"
        master.write_text(_VALID_MASTER, encoding="utf-8")
        session = self.tmp / "rmp_session"
        result = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "precheck",
             str(master), str(session)],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn("ready for DP", result.stdout)


if __name__ == "__main__":
    unittest.main()
