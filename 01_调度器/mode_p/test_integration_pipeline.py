"""End-to-end integration: Master → Manifest → Views → Precheck → DP → Delivery.

This is the Phase 1 vertical slice acceptance test. It exercises the full
MODE:P toolchain as a user would: via run_mode_p CLI commands.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from run_mode_p import initialise, submit


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_integration_"))

READY = (
    "READY EP14_S1: Shot EP14_S1-1 and EP14_S1-2 preserve the desk-to-door "
    "action direction and keep both physical light sources anchored."
)


def _tmpdir() -> Path:
    return _TEMP_ROOT


# A realistic 2-shot scene Master (dialogue + action, omni_reference)
_REALISTIC_MASTER = """\
<!-- template: director_master v2.0 -->

Master 版本：EP14_S1/v1.0
父版本：无

场景蓝图：[D] 封闭案情室内，Miguel 从白板前的分析状态转向取物离开，冷白顶光与门口暖光建立行动方向。
声音基调：[D] 格栅灯电流底噪和封闭房间空气声持续，门口方向带入轻微走廊声。

## 1. 场景层设计

### 1.1 戏剧变化与信息策略
场景前状态：案情室空无一人。
戏剧变化：Miguel 从分析线索到做出离开决定。
信息策略：前半段让观众读案件信息，后半段聚焦 Miguel 的行动转变。

### 1.2 空间调度
场景空间：封闭案情室 6m×5m，白板占北墙。
关系线：白板与门口纵深方向。
人物路径：Miguel 从白板前走向桌侧取夹克和钥匙，再走向门口。

## Shot EP14_S1-1 | 8s

叙事职责：[D] 建立空间和白板焦点，让观众读取案件信息。
剧本事实：[D] Miguel stands at the whiteboard organizing case clues.
原文定位：[M] EP14_S1 L12-L15
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到本镜 duration。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

开场状态：[D] Miguel 背对镜头站在白板前，右手停在照片旁。
开场状态键：[M]
  - character:Miguel position:whiteboard_front facing:N screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - prop:car_key held_by:none location:desk_edge
  - light_main direction:top color_temp:5000K ratio:1:2
  - action_phase:static

动作时间轴：[D] Miguel 观察白板上红线连接的案件照片，然后抬起右手。
故事板关键帧：[D] - [开场] Miguel 背对镜头站在白板前，右手停在照片旁。
  - [变化] Miguel 抬起右手并转向桌侧。
  - [结束] Miguel 到达桌侧，夹克和钥匙位于面前。
视频时间轴：[D] [0.0s] Miguel 背对镜头站在白板前，右手停在照片旁。
  [4.0s] Miguel 抬起右手，视线离开白板转向桌侧。
  [8.0s] Miguel 到达桌侧，面对椅背夹克与桌边钥匙。
声音设计：[D] 房间底噪持续；衣料轻响在 4 秒进入。
结束状态：[D] Miguel 已走向桌侧，准备取夹克和车钥匙。
结束状态键：[M]
  - character:Miguel position:desk_side facing:W screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - prop:car_key held_by:none location:desk_edge
  - light_main direction:top color_temp:5000K ratio:1:3
  - action_phase:prepare

摄影设计：[D] 房间前部眼平固定机位，24mm 深景深，朝向白板。
构图设计：[D] 桌面前景、Miguel 中景、白板背景三层；白板为视觉中心。
光影设计：[D] 四组 5000K 冷白格栅顶灯，低光比，白板为最亮区域。
表演设计：[D] Miguel 从静止观察到微抬右手的犹豫动作。

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] 从黑场淡入。
剪辑触发：[D] Miguel 抬起右手时硬切到下一镜。
交出边界 ID：[M] EP14_S1-2
边界连续性：[M] <elliptical>
交出边界：[D] Miguel 走到桌侧，准备取夹克和钥匙。
转场执行：[M] <post_production>

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

## Shot EP14_S1-2 | 9s

叙事职责：[D] Miguel 取夹克和钥匙，走向门口离开。
剧本事实：[D] Miguel grabs his jacket and car keys, walks to the door.
原文定位：[M] EP14_S1 L40-L45
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到本镜 duration。
场景表达：[M] <action_chase>
时间控制：[M] <second_nodes>

开场状态：[D] Miguel 站在桌侧，椅背上有夹克，桌上有车钥匙。
开场状态键：[M]
  - character:Miguel position:desk_side facing:W screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - prop:car_key held_by:none location:desk_edge
  - light_main direction:top color_temp:5000K ratio:1:3
  - action_phase:prepare

动作时间轴：[D] Miguel 右手拿起夹克、左手取钥匙、穿上夹克、转向门口走动。
故事板关键帧：[D] - [开场] Miguel 站在桌侧，夹克在椅背，钥匙在桌边。
  - [动作] Miguel 双手分别取夹克与钥匙。
  - [峰值] Miguel 穿上夹克并转向门口。
  - [结束] Miguel 穿着夹克，左手持钥匙走向门口。
视频时间轴：[D] [0.0s] Miguel 站在桌侧，夹克位于椅背，钥匙位于桌边。
  [1.0s] Miguel 右手伸向夹克。
  [2.0s] Miguel 右手提起夹克，左手伸向钥匙。
  [3.0s] Miguel 左手拿起钥匙。
  [4.0s] Miguel 展开夹克。
  [5.0s] Miguel 右臂穿入衣袖。
  [6.0s] Miguel 左臂穿入衣袖。
  [7.0s] Miguel 整理夹克并转向门口。
  [8.0s] Miguel 左手持钥匙走向门口。
  [9.0s] Miguel 到达门侧，身体朝向出口。
声音设计：[D] 夹克布料声在 2-7 秒连续；3 秒出现钥匙金属轻响；脚步从 8 秒进入。
结束状态：[D] Miguel 朝门口方向移动，夹克已穿上，钥匙在左手。
结束状态键：[M]
  - character:Miguel position:door_side facing:W screen_direction:right_to_left posture:walking
  - prop:jacket held_by:Miguel location:on_body
  - prop:car_key held_by:Miguel location:left_hand
  - light_main direction:top color_temp:5000K ratio:1:3
  - action_phase:travel

摄影设计：[D] A 侧桌面高度固定机位，50mm 中等景深。
构图设计：[D] 桌面物件虚化前景、Miguel 中景右侧、门口背景左侧。
光影设计：[D] 5000K 顶灯为主，门口 3500K 暖黄光提供方向性提示。
表演设计：[D] Miguel 取物迅速、穿衣果断、走向门口的步态坚定。

进入边界 ID：[M] EP14_S1-1
进入边界：[D] 从 EP14_S1-1 的动作切接入。
剪辑触发：[D] Miguel 向门口移动出画时硬切离场。
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] Miguel 离开案情室，走廊光占据门口。
转场执行：[M] <post_production>

生成模式：[M] <omni_reference>
参考资产：[M] [char_miguel|identity, loc_case_room|location, prop_keys|continuity]
参考职责：[D] char_miguel 约束身份和服装；loc_case_room 约束空间材质和光源；prop_keys 约束道具外观。
参考优先级：[D] 身份 > 空间 > 道具；光线温度不可变。
"""


class IntegrationPipelineTests(unittest.TestCase):
    """Full vertical-slice acceptance tests."""

    def setUp(self) -> None:
        self.tmp = _tmpdir()
        # Clean delivery from prior test runs
        for d in self.tmp.glob("session*"):
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def _full_happy_path(self) -> tuple[Path, Path]:
        """Run the complete happy-path pipeline. Returns (session_dir, delivery_dir)."""
        import subprocess
        import sys

        session = self.tmp / "session"
        working = session / "working"
        delivery = session / "delivery"

        # 1. Init session from scene context
        ctx = self.tmp / "context.md"
        ctx.write_text("# Scene Context\n\n## Script\nTest.\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "init", str(ctx), str(session)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(r.returncode, 0, f"init failed: {r.stderr}")

        # 2. Write Master to session
        master = session / "DIRECTOR_MASTER.md"
        master.write_text(_REALISTIC_MASTER, encoding="utf-8")

        # 3. Run precheck (compile + derive + all checks)
        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "precheck", str(master), str(session)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(r.returncode, 0, f"precheck failed:\n{r.stdout}\n{r.stderr}")

        # Verify working/ has all expected files
        self.assertTrue(working.exists())
        self.assertTrue((working / "SHOT_MANIFEST.json").exists())
        storyboard = working / "STORYBOARD.md"
        video = working / "VIDEO_PROMPT.md"
        self.assertTrue(storyboard.exists())
        self.assertTrue(video.exists())

        # 4. Simulate DP READY by writing DP feedback
        dp_feedback = self.tmp / "dp_feedback.md"
        dp_feedback.write_text(READY + "\n", encoding="utf-8")

        # 5. Submit with Master (triggers final checks)
        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "submit",
             str(session), str(storyboard), str(video), str(dp_feedback),
             "--master", str(master)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(r.returncode, 0, f"submit failed:\n{r.stdout}\n{r.stderr}")

        # 6. Verify delivery
        self.assertTrue(delivery.exists(), "Delivery directory not created")
        names = sorted(p.name for p in delivery.iterdir())
        self.assertEqual(names, ["STORYBOARD.md", "VIDEO_PROMPT.md"],
                         f"Delivery has unexpected files: {names}")

        return session, delivery

    def test_full_happy_path(self) -> None:
        """Master → Manifest → Views → Precheck → DP READY → Delivery."""
        session, delivery = self._full_happy_path()
        # Read delivery files and verify content
        sb = (delivery / "STORYBOARD.md").read_text(encoding="utf-8")
        vp = (delivery / "VIDEO_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("EP14_S1", sb)
        self.assertIn("EP14_S1", vp)
        self.assertIn("镜头 EP14_S1-1", sb)
        self.assertIn("镜头 EP14_S1-2", vp)
        # No Director placeholders should remain unfilled in delivery
        # (In reality these would be filled by Director; here we verify structure)

    def test_tampered_storyboard_caught_by_sync(self) -> None:
        """If working storyboard diverges from Master, final sync must catch it.

        Submit re-derives views from Master, so we must tamper after derivation
        but before final validation. We simulate this by running precheck first,
        then tampering the working/ file, then running final checks directly."""
        import subprocess
        import sys

        session = self.tmp / "session_sync"
        ctx = self.tmp / "ctx_sync.md"
        ctx.write_text("# Scene Context\n\n## Script\nTest.\n", encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "run_mode_p", "init", str(ctx), str(session)],
            capture_output=True, text=True, timeout=10,
        )

        master = session / "DIRECTOR_MASTER.md"
        master.write_text(_REALISTIC_MASTER, encoding="utf-8")

        # Precheck passes (derives views from Master)
        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "precheck", str(master), str(session)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(r.returncode, 0)

        # Tamper with working storyboard AFTER derivation
        sb = session / "working" / "STORYBOARD.md"
        text = sb.read_text(encoding="utf-8")
        text = text.replace("EP14_S1-1", "HACKED-1")
        sb.write_text(text, encoding="utf-8")

        # Run final checks directly — they should fail
        r = subprocess.run(
            [sys.executable, "-m", "structural_precheck", "final",
             str(master), str(session)],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertNotEqual(r.returncode, 0, "Final checks should have failed on tampered storyboard")
        self.assertIn("FAIL", r.stdout)

    def test_full_pipeline_with_dp_revision_loop(self) -> None:
        """Simulate DP finding an issue → Director revises → DP approves."""
        import subprocess
        import sys

        session = self.tmp / "session_rev"
        ctx = self.tmp / "ctx_rev.md"
        ctx.write_text("# Scene Context\n\n## Script\nTest.\n", encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "run_mode_p", "init", str(ctx), str(session)],
            capture_output=True, text=True, timeout=10,
        )

        master = session / "DIRECTOR_MASTER.md"
        master.write_text(_REALISTIC_MASTER, encoding="utf-8")

        # Precheck passes
        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "precheck", str(master), str(session)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(r.returncode, 0)

        # DP finds an issue (not READY)
        sb = session / "working" / "STORYBOARD.md"
        video = session / "working" / "VIDEO_PROMPT.md"
        dp1 = self.tmp / "dp_rev.md"
        dp1.write_text(
            "EP14_S1-2: light_source — 当前开场主光在空间描述中没有物理来源。\n",
            encoding="utf-8",
        )
        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "submit",
             str(session), str(sb), str(video), str(dp1),
             "--master", str(master)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertNotEqual(r.returncode, 0)  # Revision requested
        self.assertTrue((session / "DIRECTOR_REVISION_REQUEST.md").exists())

        # Director revises Master (simulate small fix — adjust lighting description)
        revised = _REALISTIC_MASTER.replace(
            "光影设计：[D] 5000K 顶灯为主，门口 3500K 暖黄光提供方向性提示。",
            "光影设计：[D] 5000K 顶灯为主，门口 3500K 暖黄光在门框内侧形成明确光源区域；光比为 1:3。"
        )
        master.write_text(revised, encoding="utf-8")

        # Re-run precheck after revision
        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "precheck", str(master), str(session)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(r.returncode, 0, f"precheck after revision failed:\n{r.stdout}\n{r.stderr}")

        # DP approves revised version
        dp2 = self.tmp / "dp_ready.md"
        dp2.write_text(READY + "\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "submit",
             str(session), str(sb), str(video), str(dp2),
             "--master", str(master)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(r.returncode, 0, f"submit after revision failed:\n{r.stdout}\n{r.stderr}")
        self.assertTrue((session / "delivery").exists())
        names = sorted(p.name for p in (session / "delivery").iterdir())
        self.assertEqual(names, ["STORYBOARD.md", "VIDEO_PROMPT.md"])

    def test_bad_master_fails_precheck(self) -> None:
        """A Master missing required fields must fail precheck."""
        import subprocess
        import sys

        session = self.tmp / "session_bad"
        ctx = self.tmp / "ctx_bad.md"
        ctx.write_text("# Scene Context\n\n## Script\nTest.\n", encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "run_mode_p", "init", str(ctx), str(session)],
            capture_output=True, text=True, timeout=10,
        )

        # Bad master: missing story_fact
        bad = """\
<!-- template: director_master v1.0 -->
Master 版本：BAD/v1.0
## Shot BAD-1 | 5s
缺失剧本事实字段。
"""
        master = session / "DIRECTOR_MASTER.md"
        master.write_text(bad, encoding="utf-8")

        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "precheck", str(master), str(session)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertNotEqual(r.returncode, 0, "Precheck should fail on bad Master")

    def test_submit_without_master_cannot_bypass_strict_pipeline(self) -> None:
        """Views and READY cannot bypass Master compilation and structural precheck."""
        import subprocess
        import sys

        session = self.tmp / "session_legacy"
        ctx = self.tmp / "ctx_legacy.md"
        ctx.write_text("# Scene Context\n", encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "run_mode_p", "init", str(ctx), str(session)],
            capture_output=True, text=True, timeout=10,
        )

        # Write minimal valid video prompt
        sb = self.tmp / "sb.md"
        sb.write_text("# Storyboard\n", encoding="utf-8")
        video = self.tmp / "video.md"
        video.write_text("# Video Prompt\n## Shot 1 | 8s\nImage: test\nSound: quiet.\nExit: hard cut.\n", encoding="utf-8")
        dp = self.tmp / "dp.md"
        dp.write_text(READY + "\n", encoding="utf-8")

        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "submit",
             str(session), str(sb), str(video), str(dp)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((session / "delivery").exists())

    def test_delivery_has_exactly_two_files(self) -> None:
        """The final delivery directory must contain only STORYBOARD.md and VIDEO_PROMPT.md."""
        session, delivery = self._full_happy_path()
        self.assertEqual(sorted(p.name for p in delivery.iterdir()),
                         ["STORYBOARD.md", "VIDEO_PROMPT.md"])

    def test_check_report_generated_on_precheck_failure(self) -> None:
        """When precheck fails, CHECK_REPORT.md must be written to session root."""
        import subprocess
        import sys

        session = self.tmp / "session_report"
        ctx = self.tmp / "ctx_report.md"
        ctx.write_text("# Scene Context\n\n## Script\nTest.\n", encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "run_mode_p", "init", str(ctx), str(session)],
            capture_output=True, text=True, timeout=10,
        )

        # Bad master that passes compiler but fails sync (e.g., duplicate shot numbers)
        bad_master = """\
<!-- template: director_master v1.0 -->
Master 版本：REPORT/v1.0
## Shot REPORT-1 | 5s
剧本事实：[D] x
原文定位：[M] REPORT L1-L1
生成单元：[M] x
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>
开场状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:top color_temp:4000K ratio:1:2
  - action_phase:static
结束状态键：[M]
  - character:A position:p1 facing:N screen_direction:static posture:standing
  - light_main direction:top color_temp:4000K ratio:1:2
  - action_phase:static
进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] x
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] x
参考优先级：[D] x
## Shot REPORT-1 | 5s
剧本事实：[D] y
原文定位：[M] REPORT L2-L2
生成单元：[M] x
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>
开场状态键：[M]
  - character:A position:p2 facing:N screen_direction:static posture:standing
  - light_main direction:top color_temp:4000K ratio:1:2
  - action_phase:static
结束状态键：[M]
  - character:A position:p2 facing:N screen_direction:static posture:standing
  - light_main direction:top color_temp:4000K ratio:1:2
  - action_phase:static
进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] x
转场执行：[M] <post_production>
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] x
参考优先级：[D] x
"""
        master = session / "DIRECTOR_MASTER.md"
        master.write_text(bad_master, encoding="utf-8")

        r = subprocess.run(
            [sys.executable, "-m", "run_mode_p", "precheck", str(master), str(session)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertNotEqual(r.returncode, 0)
        report_path = session / "CHECK_REPORT.md"
        self.assertTrue(report_path.exists(), "CHECK_REPORT.md should exist after precheck failure")
        report = report_path.read_text(encoding="utf-8")
        self.assertIn("Failures", report)


if __name__ == "__main__":
    unittest.main()
