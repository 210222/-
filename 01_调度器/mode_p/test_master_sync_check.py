"""Tests for master_sync_check.py — structural consistency across all four files."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from master_compiler import compile_to_file
from master_sync_check import check_sync
from view_deriver import derive_views


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_sync_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


_SINGLE_MASTER = """\
<!-- template: director_master v2.0 -->

Master 版本：TEST_S1/v1.0
父版本：无

场景蓝图：[D] 案情室内，Miguel 面对白板完成一次由观察到抬手的细小行动。
声音基调：[D] 安静室内底噪持续。

## Shot TEST_S1-1 | 8s

剧本事实：[D] Miguel stands at the whiteboard organizing case clues.
原文定位：[M] TEST_S1 L12-L15
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到本镜 duration。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

开场状态：[D] Miguel 背对镜头站在白板前。
开场状态键：[M]
  - character:Miguel position:whiteboard_front facing:N screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - light_main direction:top color_temp:5000K ratio:1:2
  - action_phase:static

动作时间轴：[D] Miguel 观察白板后抬起右手。
故事板关键帧：[D] - [开场] Miguel 背对镜头站在白板前。
  - [变化] Miguel 抬起右手。
  - [结束] Miguel 的右手停在照片前。
视频时间轴：[D] [0.0s] Miguel 背对镜头站在白板前。
  [4.0s] Miguel 的视线停在照片上，右肩开始抬起。
  [8.0s] Miguel 的右手停在照片前。
声音设计：[D] 室内底噪持续；4 秒出现轻微衣料声。

结束状态：[D] Miguel 抬手准备触碰照片。
结束状态键：[M]
  - character:Miguel position:whiteboard_front facing:NE screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - light_main direction:top color_temp:5000K ratio:1:2
  - action_phase:static

摄影设计：[D] 房间前部眼平固定机位，24mm。
构图设计：[D] 桌面、人物、白板前中后三级。
光影设计：[D] 四组顶灯提供 5000K 冷白柔光。
表演设计：[D] 手部动作与视线配合。

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] 从黑场淡入。
剪辑触发：[D] Miguel 抬起右手时硬切到门口视角。
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] 抬手动作完成。
转场执行：[M] <post_production>

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无
"""

_MULTI_MASTER = """\
<!-- template: director_master v2.0 -->

Master 版本：EP14/v1.0
父版本：无

场景蓝图：[D] 房间内，A 从门口冲到中部并继续跑向深处后停下，银幕方向保持从左向右。
声音基调：[D] 连续脚步与室内反射声贯穿两镜。

## Shot EP14-1 | 5s

剧本事实：[D] A runs from door to mid-room.
原文定位：[M] EP14 L1-L3
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <action_chase>
时间控制：[M] <half_second_nodes>

开场状态：[D] A 站在门口。
开场状态键：[M]
  - character:A position:door facing:S screen_direction:left_to_right posture:standing
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:prepare

动作时间轴：[D] A 从门口冲向房间中部。
故事板关键帧：[D] - [开场] A 站在门口，身体前倾准备起跑。
  - [峰值] A 横向冲过房间前部。
  - [结束] A 到达房间中部仍在奔跑。
视频时间轴：[D] [0.0s] A 站在门口，身体前倾。
  [0.5s] A 重心移向前脚。
  [1.0s] A 蹬地启动。
  [1.5s] A 离开门口向右奔跑。
  [2.0s] A 经过房间前部。
  [2.5s] A 保持向右奔跑。
  [3.0s] A 接近房间中部。
  [3.5s] A 的步幅保持稳定。
  [4.0s] A 进入房间中部。
  [4.5s] A 继续向右移动。
  [5.0s] A 到达房间中部仍在奔跑。
声音设计：[D] 脚步从 1 秒进入并随空间移动；无对白。

结束状态：[D] A 跑到房间中部。
结束状态键：[M]
  - character:A position:mid_room facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel

摄影设计：[D] 侧跟机位，35mm。
构图设计：[D] A 居中，背景流动。
光影设计：[D] 顶灯冷白，光比 1:3。
表演设计：[D] 爆发性起跑，持续速度。

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] 从黑场切入。
剪辑触发：[D] A 启动脚步时切。
交出边界 ID：[M] EP14-2
边界连续性：[M] <continuous>
交出边界：[D] A 到达房间中部。
转场执行：[M] <post_production>

生成模式：[M] <omni_reference>
参考资产：[M] [char_runner_01|identity]
参考职责：[D] char_runner_01 只约束身份和服装。
参考优先级：[D] 身份优先于运镜。

## Shot EP14-2 | 10s

剧本事实：[D] A continues running and stops.
原文定位：[M] EP14 L4-L6
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <action_chase>
时间控制：[M] <half_second_nodes>

开场状态：[D] A 在房间中部奔跑中。
开场状态键：[M]
  - character:A position:mid_room facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel

动作时间轴：[D] A 继续跑向房间深处然后停下。
故事板关键帧：[D] - [开场] A 在房间中部奔跑。
  - [变化] A 跑向房间深处并开始减速。
  - [结束] A 在远处站定。
视频时间轴：[D] [0.0s] A 在房间中部向右奔跑。
  [0.5s] A 保持步幅。
  [1.0s] A 继续向房间深处移动。
  [1.5s] A 的身体略向前倾。
  [2.0s] A 经过中部标记。
  [2.5s] A 继续向右奔跑。
  [3.0s] A 接近房间后部。
  [3.5s] A 的步幅开始缩短。
  [4.0s] A 进入减速阶段。
  [4.5s] A 上身逐渐直立。
  [5.0s] A 保持向右移动。
  [5.5s] A 的脚步间距缩短。
  [6.0s] A 接近远端位置。
  [6.5s] A 抬起上身。
  [7.0s] A 继续减速。
  [7.5s] A 迈出最后两步。
  [8.0s] A 到达远端。
  [8.5s] A 的前脚落地制动。
  [9.0s] A 身体停止前移。
  [9.5s] A 稳定站姿。
  [10.0s] A 在房间远处站定。
声音设计：[D] 连续脚步在 8 秒后减慢，10 秒只保留室内底噪。

结束状态：[D] A 在房间远处停下。
结束状态键：[M]
  - character:A position:far_end facing:S screen_direction:left_to_right posture:stopped
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:recover

摄影设计：[D] 正面固定机位，50mm。
构图设计：[D] A 从远处跑来。
光影设计：[D] 顶灯冷白。
表演设计：[D] 减速停止。

进入边界 ID：[M] EP14-1
进入边界：[D] 从 EP14-1 动作切接入。
剪辑触发：[D] A 停止时切。
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] A 站定。
转场执行：[M] <post_production>

生成模式：[M] <omni_reference>
参考资产：[M] [char_runner_01|continuity]
参考职责：[D] char_runner_01 约束连续性。
参考优先级：[D] 连续性优先。
"""


class SyncCheckTests(unittest.TestCase):
    """End-to-end: compile → derive → check."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = _tmpdir()

    def _full_pipeline(self, master_text: str, label: str) -> tuple[Path, Path, Path, Path]:
        """Return (master, manifest, storyboard, video) paths."""
        master_p = self.tmp / f"{label}_master.md"
        master_p.write_text(master_text, encoding="utf-8")
        manifest_p = self.tmp / f"{label}_manifest.json"
        compile_to_file(master_p, manifest_p)
        story_p = self.tmp / f"{label}_STORYBOARD.md"
        video_p = self.tmp / f"{label}_VIDEO_PROMPT.md"
        derive_views(master_p, manifest_p, story_p, video_p)
        return master_p, manifest_p, story_p, video_p

    # -- clean sync tests --

    def test_single_shot_passes_sync(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_SINGLE_MASTER, "s1")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_multi_shot_passes_sync(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_MULTI_MASTER, "s2")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    # -- failure tests: tampered views --

    def test_changed_shot_id_in_storyboard_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_SINGLE_MASTER, "f1")
        text = story_p.read_text(encoding="utf-8")
        text = text.replace("TEST_S1-1", "TEST_S1-9")
        story_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)

    def test_changed_duration_in_video_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_SINGLE_MASTER, "f2")
        text = video_p.read_text(encoding="utf-8")
        text = text.replace("| 8s", "| 12s")
        video_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)

    def test_removed_shot_in_storyboard_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_MULTI_MASTER, "f3")
        text = story_p.read_text(encoding="utf-8")
        # Remove EP14-2 section
        idx = text.find("## 镜头 EP14-2")
        if idx > 0:
            text = text[:idx].rstrip()
            story_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)

    def test_tampered_story_text_detected_without_exposed_hash(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_SINGLE_MASTER, "f4")
        text = story_p.read_text(encoding="utf-8")
        text = text.replace("前中后三级", "错误单层", 1)
        story_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)
        self.assertTrue(any(issue.field == "derived_content" for issue in report.issues))

    def test_changed_generation_mode_in_video_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_MULTI_MASTER, "f5")
        text = video_p.read_text(encoding="utf-8")
        text = text.replace("全能参考", "纯提示词")
        video_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)

    def test_changed_reference_assets_in_video_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_MULTI_MASTER, "f6")
        text = video_p.read_text(encoding="utf-8")
        text = text.replace("char_runner_01", "wrong_asset")
        video_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)

    def test_missing_camera_field_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(_SINGLE_MASTER, "f7")
        text = video_p.read_text(encoding="utf-8")
        import re
        text = re.sub(r"^摄影：.+$", "摄影：", text, flags=re.MULTILINE)
        video_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)

    def test_fractional_duration_passes_without_integer_truncation(self) -> None:
        fractional = _SINGLE_MASTER.replace(
            "## Shot TEST_S1-1 | 8s", "## Shot TEST_S1-1 | 8.5s"
        ).replace("[8.0s] Miguel 的右手停在照片前。",
                  "[8.5s] Miguel 的右手停在照片前。")
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            fractional, "fractional"
        )
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_master_changed_after_manifest_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            _SINGLE_MASTER, "stale_master"
        )
        master_p.write_text(
            _SINGLE_MASTER.replace("24mm", "35mm"), encoding="utf-8"
        )
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)
        self.assertTrue(any(
            issue.file == "SHOT_MANIFEST.json" and issue.field == "master_content_hash"
            for issue in report.issues
        ))

    def test_views_do_not_expose_master_version_comments(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            _SINGLE_MASTER, "bad_version_comment"
        )
        text = story_p.read_text(encoding="utf-8")
        self.assertNotIn("derived from:", text)
        self.assertNotIn("canonical:", text)
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertTrue(report.ok)

    def test_changed_reference_responsibility_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            _MULTI_MASTER, "bad_ref_responsibility"
        )
        text = video_p.read_text(encoding="utf-8").replace(
            "char_runner_01|identity", "char_runner_01|style", 1
        )
        video_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertFalse(report.ok)

    def test_missing_performance_detected_without_duplicate_action_source(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            _SINGLE_MASTER, "missing_sources"
        )
        text = video_p.read_text(encoding="utf-8")
        text = re.sub(r"^表演：.+$", "", text, flags=re.MULTILINE)
        video_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        fields = {issue.field for issue in report.issues}
        self.assertIn("表演", fields)
        self.assertIn("derived_content", fields)
        self.assertNotIn("Action Source", fields)

    def test_missing_storyboard_transition_detected(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            _SINGLE_MASTER, "missing_story_transition"
        )
        text = re.sub(
            r"^切出：.+$", "", story_p.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
        story_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertTrue(any(issue.field == "exit" for issue in report.issues))

    def test_tampered_storyboard_creative_text_detected_as_non_derived(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            _SINGLE_MASTER, "tampered_story_creative"
        )
        text = story_p.read_text(encoding="utf-8").replace(
            "Miguel 抬起右手。", "Miguel 抬起左手。", 1
        )
        story_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertTrue(any(
            issue.file == "STORYBOARD.md" and issue.field == "derived_content"
            for issue in report.issues
        ))

    def test_tampered_video_creative_text_detected_as_non_derived(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            _SINGLE_MASTER, "tampered_video_creative"
        )
        text = video_p.read_text(encoding="utf-8").replace(
            "室内底噪持续；4 秒出现轻微衣料声。",
            "室内底噪持续；4 秒出现玻璃破碎声。",
        )
        video_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertTrue(any(
            issue.file == "VIDEO_PROMPT.md" and issue.field == "derived_content"
            for issue in report.issues
        ))

    def test_tampered_exit_detected_without_boundary_metadata(self) -> None:
        master_p, manifest_p, story_p, video_p = self._full_pipeline(
            _MULTI_MASTER, "bad_boundary_mode"
        )
        text = video_p.read_text(encoding="utf-8").replace(
            "切出：后期完成", "切出：镜内完成", 1
        )
        video_p.write_text(text, encoding="utf-8")
        report = check_sync(master_p, manifest_p, story_p, video_p)
        self.assertTrue(any(issue.field == "derived_content" for issue in report.issues))


class CLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = _tmpdir()

    def test_cli_pass_exits_zero(self) -> None:
        import subprocess
        import sys
        master_p = self.tmp / "cli_master.md"
        master_p.write_text(_SINGLE_MASTER, encoding="utf-8")
        manifest_p = self.tmp / "cli_manifest.json"
        compile_to_file(master_p, manifest_p)
        story_p = self.tmp / "cli_story.md"
        video_p = self.tmp / "cli_video.md"
        derive_views(master_p, manifest_p, story_p, video_p)

        result = subprocess.run(
            [sys.executable, "-m", "master_sync_check",
             str(master_p), str(manifest_p), str(story_p), str(video_p)],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn("passed", result.stdout)

    def test_cli_fail_exits_nonzero(self) -> None:
        import subprocess
        import sys
        master_p = self.tmp / "cli_bad_master.md"
        master_p.write_text(_SINGLE_MASTER, encoding="utf-8")
        manifest_p = self.tmp / "cli_bad_manifest.json"
        compile_to_file(master_p, manifest_p)
        story_p = self.tmp / "cli_bad_story.md"
        video_p = self.tmp / "cli_bad_video.md"
        derive_views(master_p, manifest_p, story_p, video_p)
        # Tamper
        text = story_p.read_text(encoding="utf-8")
        text = text.replace("TEST_S1-1", "WRONG-1")
        story_p.write_text(text, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "-m", "master_sync_check",
             str(master_p), str(manifest_p), str(story_p), str(video_p)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
