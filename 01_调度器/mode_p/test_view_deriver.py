"""Tests for view_deriver.py — derive skeletons, verify canonical fidelity."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from master_compiler import compile_to_file
from test_master_compiler import V4_SHARED_BOUNDARY_MASTER
from view_deriver import DeriverError, derive_views


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_views_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


# Reuse test fixtures from test_master_compiler
_SINGLE_SHOT_MASTER = """\
<!-- template: director_master v2.0 -->

Master 版本：TEST_S1/v1.0
父版本：无

场景蓝图：[D] 案情室内，Miguel 面对白板完成一次由观察到抬手的细小行动。
声音基调：[D] 安静室内底噪持续。

## Shot TEST_S1-1 | 8s

叙事职责：[D] 建立空间和主角的位置。
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

_MULTI_SHOT_MASTER = """\
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


def _v4_full_master() -> str:
    text = V4_SHARED_BOUNDARY_MASTER.replace(
        "Master 版本：V4_SCENE/v1.0\n",
        "Master 版本：V4_SCENE/v1.0\n"
        "场景蓝图：[D] A 从门口横穿房间并在远墙前停稳。\n"
        "声音基调：[D] 连续脚步与室内反射声贯穿全场。\n",
    )
    first_design = """时间控制：[M] <event_nodes>
摄影设计：[D] 35mm 眼平侧跟，摄影机与 A 同速向右移动。
构图设计：[D] A 位于右侧三分线，门口和远墙形成前后深度。
光影设计：[D] 左侧窗光 4000K，光比 1:3，方向保持稳定。
表演设计：[D] A 前倾起跑，步幅逐渐展开。
视觉时间线：[D] [0.0s][SB] A 位于门内，右脚落地，身体朝右前倾。
  [2.0s] A 加速横穿房间前部，双臂交替摆动。
  [5.0s][SB] A 到达房间中央，右脚触地，身体继续向右。
声音设计：[D] 0 秒脚步进入，2 秒后反射声增强。
生成模式"""
    second_design = """时间控制：[M] <event_nodes>
摄影设计：[D] 50mm 眼平固定机位，A 从画面左侧进入并向远墙移动。
构图设计：[D] A 从左侧三分线移动到中央，远墙占据后景。
光影设计：[D] 左侧窗光 4000K，光比 1:3，远墙亮度稳定。
表演设计：[D] A 缩短步幅，抬直上身后停稳。
视觉时间线：[D] [0.0s][SB] A 位于房间中央，右脚触地，身体继续向右。
  [3.0s][SB] A 接近远墙，步幅缩短，上身开始直立。
  [7.0s][SB] A 位于远墙前，双脚停稳，身体静止。
声音设计：[D] 脚步间隔逐渐拉长，7 秒脚步停止。
生成模式"""
    text = text.replace(
        "时间控制：[M] <event_nodes>\n生成模式", first_design, 1
    )
    text = text.replace(
        "时间控制：[M] <event_nodes>\n生成模式", second_design, 1
    )
    return text.replace(
        "参考资产：[M] 无",
        "参考资产：[M] 无\n参考职责：[D] 无\n参考优先级：[D] 无",
    )


class DerivationTests(unittest.TestCase):
    """End-to-end: Master → Manifest → Views."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = _tmpdir()

    def _compile_and_derive(self, master_text: str, label: str) -> tuple[Path, Path, Path]:
        """Helper: write master, compile manifest, derive views, return paths."""
        master_p = self.tmp / f"{label}_master.md"
        master_p.write_text(master_text, encoding="utf-8")
        manifest_p = self.tmp / f"{label}_manifest.json"
        compile_to_file(master_p, manifest_p)
        story_p = self.tmp / f"{label}_STORYBOARD.md"
        video_p = self.tmp / f"{label}_VIDEO_PROMPT.md"
        derive_views(master_p, manifest_p, story_p, video_p)
        return story_p, video_p, manifest_p

    # -- storyboard tests --

    def test_storyboard_has_scene_header(self) -> None:
        story_p, _, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "sb1")
        text = story_p.read_text(encoding="utf-8")
        self.assertIn("# TEST_S1 — 故事板", text)
        self.assertIn("## 场景蓝图", text)

    def test_storyboard_hides_internal_derivation_metadata(self) -> None:
        story_p, _, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "sb2")
        text = story_p.read_text(encoding="utf-8")
        self.assertNotIn("<!-- canonical:", text)
        self.assertNotIn("<!-- derived from:", text)
        self.assertNotIn("Boundary:", text)

    def test_storyboard_has_shot_header_with_expression(self) -> None:
        story_p, _, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "sb3")
        text = story_p.read_text(encoding="utf-8")
        self.assertIn("## 镜头 TEST_S1-1 | 8s", text)

    def test_storyboard_has_composition_but_not_camera_lighting(self) -> None:
        story_p, _, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "sb4")
        text = story_p.read_text(encoding="utf-8")
        # Storyboard for conversation_power: composition (空间关系) + keyframes only.
        self.assertIn("前中后三级", text)
        self.assertNotIn("24mm", text)
        self.assertNotIn("5000K", text)

    def test_storyboard_profile_changes_focus_and_field_order(self) -> None:
        # Each profile: (marker, before, after) — 'before' must appear earlier in
        # the output than 'after'.  Extra fields are rendered before focus frames.
        expectations = {
            "conversation_power": ("关键帧：", "空间关系：", "关键帧："),
            "crowd_attention": ("注意力帧：", "注意力层级：", "注意力帧："),
            "action_chase": ("动作帧：", "空间轨迹：", "动作帧："),
            "suspense_reveal": ("揭示帧：", "信息缺口：", "揭示帧："),
            "contemplative_silence": ("静默帧：", "构图留白：", "静默帧："),
            "investigation_object": ("发现帧：", "视线链：", "发现帧："),
            "montage": ("节拍帧：", "视觉锚点：", "节拍帧："),
            "cross_space_transition": ("空间交接帧：", "匹配元素：", "空间交接帧："),
        }
        for profile, (marker, first, second) in expectations.items():
            with self.subTest(profile=profile):
                master = _SINGLE_SHOT_MASTER.replace(
                    "<conversation_power>", f"<{profile}>"
                )
                story_p, _, _ = self._compile_and_derive(master, f"profile_{profile}")
                text = story_p.read_text(encoding="utf-8")
                self.assertIn(marker, text)
                self.assertLess(text.index(first), text.index(second))

    def test_storyboard_is_final_and_has_no_director_placeholders(self) -> None:
        story_p, _, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "sb5")
        text = story_p.read_text(encoding="utf-8")
        self.assertNotIn("[Director:", text)
        self.assertIn("Miguel 的右手停在照片前", text)

    def test_storyboard_boundary_pairings_for_multi_shot(self) -> None:
        story_p, _, _ = self._compile_and_derive(_MULTI_SHOT_MASTER, "sb6")
        text = story_p.read_text(encoding="utf-8")
        self.assertIn("EP14-1", text)
        self.assertIn("EP14-2", text)
        # Each shot has its own handoff line (切出).
        self.assertIn("切出：", text)

    def test_storyboard_multi_shot_count(self) -> None:
        story_p, _, _ = self._compile_and_derive(_MULTI_SHOT_MASTER, "sb7")
        text = story_p.read_text(encoding="utf-8")
        # Count shot headers: "## 镜头 <id> | <dur>s"
        import re
        headers = re.findall(r"^## 镜头 .*\| \d+s$", text, re.MULTILINE)
        self.assertEqual(len(headers), 2)

    def test_v4_visual_timeline_is_the_only_source_for_both_views(self) -> None:
        story_p, video_p, _ = self._compile_and_derive(_v4_full_master(), "v4_same_source")
        story = story_p.read_text(encoding="utf-8")
        video = video_p.read_text(encoding="utf-8")
        shared_opening = "A 位于门内，右脚落地，身体朝右前倾。"
        video_only = "A 加速横穿房间前部，双臂交替摆动。"
        self.assertIn(shared_opening, story)
        self.assertIn(shared_opening, video)
        self.assertNotIn(video_only, story)
        self.assertIn(video_only, video)
        self.assertNotIn("[SB]", story)
        self.assertNotIn("[SB]", video)
        self.assertNotIn("故事板关键帧", _v4_full_master())
        self.assertNotIn("视频时间轴", _v4_full_master())
        handoff = "A 位于房间中央，身体继续向右运动。"
        self.assertEqual(story.count(handoff), 1)
        self.assertEqual(video.count(handoff), 1)

    def test_v4_same_source_derives_all_three_sd2_modes(self) -> None:
        cases = {
            "text_only": "纯提示词",
            "first_last_frame": "首尾帧",
            "omni_reference": "全能参考",
        }
        for mode, label in cases.items():
            master = _v4_full_master().replace("<text_only>", f"<{mode}>")
            if mode != "text_only":
                master = master.replace(
                    "参考资产：[M] 无",
                    "参考资产：[M] [ref_start|first_frame, ref_end|last_frame]",
                )
            story_p, video_p, _ = self._compile_and_derive(
                master, f"v4_mode_{mode}"
            )
            story = story_p.read_text(encoding="utf-8")
            video = video_p.read_text(encoding="utf-8")
            self.assertIn("A 位于门内", story)
            self.assertIn("A 位于门内", video)
            self.assertIn(f"生成模式：{label}", video)

    # -- video prompt tests --

    def test_video_has_scene_header(self) -> None:
        _, video_p, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "vp1")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("# TEST_S1 — 视频提示词", text)

    def test_video_has_timing_based_image_lines(self) -> None:
        _, video_p, _ = self._compile_and_derive(_MULTI_SHOT_MASTER, "vp2")
        text = video_p.read_text(encoding="utf-8")
        # half_second_nodes → many [N.ns] lines
        self.assertIn("[0.0s]", text)
        self.assertIn("[0.5s]", text)

    def test_video_event_nodes_has_fewer_lines(self) -> None:
        _, video_p, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "vp3")
        text = video_p.read_text(encoding="utf-8")
        # event_nodes: ~3 key moments
        lines = [l for l in text.splitlines() if l.strip().startswith("[")]
        self.assertLess(len(lines), 6)  # fewer than half_second resolution

    def test_video_has_generation_mode_and_references(self) -> None:
        _, video_p, _ = self._compile_and_derive(_MULTI_SHOT_MASTER, "vp4")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("生成模式：全能参考", text)
        self.assertIn("char_runner_01", text)
        self.assertIn("参考资产：", text)
        self.assertNotIn("Generation Control:", text)

    def test_video_text_only_has_no_algorithm_authored_control_prose(self) -> None:
        _, video_p, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "vp_text_only")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("生成模式：纯提示词", text)
        for mechanical in (
            "Generation Control:", "Profile:", "Timing:", "Boundary:",
            "Opening State:", "Action Source:", "Closing State:",
            "<!-- canonical:", "<!-- derived from:",
        ):
            self.assertNotIn(mechanical, text)

    def test_video_timeline_carries_absolute_opening_and_ending(self) -> None:
        _, video_p, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "vp5")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("[0.0s] Miguel 背对镜头站在白板前", text)
        self.assertIn("[8.0s] Miguel 的右手停在照片前", text)

    def test_video_has_sound_and_exit(self) -> None:
        _, video_p, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "vp6")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("声音：", text)
        self.assertIn("切出：", text)

    def test_video_camera_composition_lighting_copied(self) -> None:
        _, video_p, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "vp7")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("24mm", text)
        self.assertIn("5000K", text)

    def test_video_carries_director_performance_and_timeline_without_duplication(self) -> None:
        _, video_p, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "vp8")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("表演：手部动作与视线配合。", text)
        self.assertEqual(text.count("Miguel 的右手停在照片前"), 1)

    def test_reference_binding_preserves_machine_responsibility(self) -> None:
        _, video_p, _ = self._compile_and_derive(_MULTI_SHOT_MASTER, "vp9")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("char_runner_01|identity", text)
        self.assertIn("char_runner_01|continuity", text)

    def test_views_keep_handoffs_but_hide_runtime_boundary_and_timing_metadata(self) -> None:
        story_p, video_p, _ = self._compile_and_derive(
            _MULTI_SHOT_MASTER, "view_contract"
        )
        story = story_p.read_text(encoding="utf-8")
        video = video_p.read_text(encoding="utf-8")
        self.assertIn("切出：", story)
        self.assertIn("切出：", video)
        self.assertNotIn("Boundary:", story)
        self.assertNotIn("Boundary:", video)
        self.assertNotIn("Timing:", video)

    def test_fractional_duration_keeps_exact_final_timestamp(self) -> None:
        fractional = _SINGLE_SHOT_MASTER.replace(
            "## Shot TEST_S1-1 | 8s", "## Shot TEST_S1-1 | 8.5s"
        ).replace("[8.0s] Miguel 的右手停在照片前。",
                  "[8.5s] Miguel 的右手停在照片前。")
        _, video_p, _ = self._compile_and_derive(fractional, "vp_fractional")
        text = video_p.read_text(encoding="utf-8")
        self.assertIn("## 镜头 TEST_S1-1 | 8.5s", text)
        self.assertIn("[8.5s]", text)

    # -- fidelity tests: canonical values must not change --

    def test_shot_count_preserved(self) -> None:
        story_p, video_p, manifest_p = self._compile_and_derive(_MULTI_SHOT_MASTER, "fid1")
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
        expected = len(manifest["shots"])
        story_text = story_p.read_text(encoding="utf-8")
        video_text = video_p.read_text(encoding="utf-8")
        import re
        sb_count = len(re.findall(r"^## 镜头 .*\| \d+s$", story_text, re.MULTILINE))
        vp_count = len(re.findall(r"^## 镜头 .*\| \d+s$", video_text, re.MULTILINE))
        self.assertEqual(sb_count, expected)
        self.assertEqual(vp_count, expected)

    def test_durations_preserved(self) -> None:
        _, video_p, manifest_p = self._compile_and_derive(_MULTI_SHOT_MASTER, "fid2")
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
        video_text = video_p.read_text(encoding="utf-8")
        for shot in manifest["shots"]:
            self.assertIn(f"{shot['duration']}s", video_text)

    def test_no_manifest_json_in_views(self) -> None:
        """Views must not contain raw JSON or canonical field IDs meant for machines."""
        story_p, video_p, _ = self._compile_and_derive(_SINGLE_SHOT_MASTER, "fid3")
        for path in [story_p, video_p]:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn('"shot_id"', text)
            self.assertNotIn('"manifest_version"', text)

    # -- error cases --

    def test_mismatched_shot_count_raises(self) -> None:
        """If Master shot count differs from Manifest, derivation must fail."""
        master_p = self.tmp / "err_master.md"
        master_p.write_text(_SINGLE_SHOT_MASTER, encoding="utf-8")
        manifest_p = self.tmp / "err_manifest.json"
        # Write a manifest with wrong shot count
        manifest_p.write_text(json.dumps({
            "manifest_version": "1.0",
            "scene_id": "TEST_S1",
            "master_version": "TEST_S1/v1.0",
            "master_content_hash": "a" * 64,
            "compiler_version": "1.0.0",
            "shots": [
                {"shot_id": "TEST_S1-1", "duration": 1, "scene_expression": "action_chase",
                 "timing_mode": "event_nodes",
                 "story_fact_ref": {"text_start": "x", "source_scene_id": "X", "source_line_start": 1, "source_line_end": 2},
                 "opening_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "static"},
                 "closing_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "static"},
                 "entry_boundary_id": "SCENE_ENTRY", "exit_boundary_id": "SCENE_EXIT",
                 "transition_execution": "post_production", "generation_mode": "text_only",
                 "reference_assets": []},
                {"shot_id": "TEST_S1-2", "duration": 1, "scene_expression": "action_chase",
                 "timing_mode": "event_nodes",
                 "story_fact_ref": {"text_start": "y", "source_scene_id": "X", "source_line_start": 3, "source_line_end": 4},
                 "opening_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "static"},
                 "closing_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "static"},
                 "entry_boundary_id": "SCENE_ENTRY", "exit_boundary_id": "SCENE_EXIT",
                 "transition_execution": "post_production", "generation_mode": "text_only",
                 "reference_assets": []},
            ],
        }), encoding="utf-8")
        with self.assertRaises(DeriverError):
            derive_views(master_p, manifest_p,
                         self.tmp / "out_sb.md", self.tmp / "out_vp.md")

    def test_missing_master_raises(self) -> None:
        with self.assertRaises((DeriverError, FileNotFoundError, OSError)):
            derive_views(Path("/nonexistent/master.md"),
                         self.tmp / "m.json",
                         self.tmp / "sb.md", self.tmp / "vp.md")

    def test_stale_manifest_after_master_change_raises(self) -> None:
        master_p = self.tmp / "stale_master.md"
        master_p.write_text(_SINGLE_SHOT_MASTER, encoding="utf-8")
        manifest_p = self.tmp / "stale_manifest.json"
        compile_to_file(master_p, manifest_p)
        master_p.write_text(
            _SINGLE_SHOT_MASTER.replace("房间前部眼平固定机位", "门侧眼平固定机位"),
            encoding="utf-8",
        )
        with self.assertRaises(DeriverError) as ctx:
            derive_views(
                master_p,
                manifest_p,
                self.tmp / "stale_sb.md",
                self.tmp / "stale_vp.md",
            )
        self.assertIn("stale", str(ctx.exception))

    def test_missing_master_creative_source_field_raises(self) -> None:
        incomplete = _SINGLE_SHOT_MASTER.replace(
            "表演设计：[D] 手部动作与视线配合。", ""
        )
        master_p = self.tmp / "missing_creative_master.md"
        master_p.write_text(incomplete, encoding="utf-8")
        manifest_p = self.tmp / "missing_creative_manifest.json"
        compile_to_file(master_p, manifest_p)
        with self.assertRaises(DeriverError) as ctx:
            derive_views(
                master_p,
                manifest_p,
                self.tmp / "missing_creative_sb.md",
                self.tmp / "missing_creative_vp.md",
            )
        self.assertIn("performance", str(ctx.exception))


class CLITests(unittest.TestCase):
    """End-to-end CLI tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = _tmpdir()

    def test_cli_derives_and_exits_zero(self) -> None:
        import subprocess
        import sys
        master_p = self.tmp / "cli_master.md"
        master_p.write_text(_SINGLE_SHOT_MASTER, encoding="utf-8")
        manifest_p = self.tmp / "cli_manifest.json"
        compile_to_file(master_p, manifest_p)
        sb_p = self.tmp / "cli_sb.md"
        vp_p = self.tmp / "cli_vp.md"

        result = subprocess.run(
            [sys.executable, "-m", "view_deriver", str(master_p), str(manifest_p),
             "-s", str(sb_p), "-v", str(vp_p)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertTrue(sb_p.exists())
        self.assertTrue(vp_p.exists())
        self.assertIn("故事板", sb_p.read_text(encoding="utf-8"))
        self.assertIn("视频提示词", vp_p.read_text(encoding="utf-8"))

    def test_cli_missing_files_exits_nonzero(self) -> None:
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "view_deriver", "nonexistent.md", "nonexistent.json"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
