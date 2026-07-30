"""Tests for master_compiler.py — parse Master, produce valid Manifest, fail-closed.

These tests use in-memory Master content, write to temp files, compile,
and validate the output manifest against the schema. They also cover
every failure mode the compiler must detect.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import jsonschema

from master_compiler import CompilerError, compile_master, compile_to_file

# Schema for validation
_SCHEMA_PATH = Path(__file__).with_name("shot_manifest_schema.json")
with open(_SCHEMA_PATH, encoding="utf-8") as fh:
    SCHEMA = json.load(fh)


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_compiler_"))


def _write_temp(name: str, content: str) -> Path:
    p = _TEMP_ROOT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# --- valid Master fixtures ---

SINGLE_SHOT_MASTER = """\
<!-- template: director_master v1.0 -->

Master 版本：TEST_S1/v1.0
父版本：无

## 1. 场景层设计
（场景描述由 Director 创作，编译器不解析）

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

结束状态：[D] Miguel 抬手准备触碰照片。
结束状态键：[M]
  - character:Miguel position:whiteboard_front facing:NE screen_direction:static posture:standing
  - prop:jacket held_by:none location:chair_back
  - light_main direction:top color_temp:5000K ratio:1:2
  - action_phase:static

摄影设计：[D] 房间前部眼平固定机位。
构图设计：[D] 桌面、人物、白板前中后三级。
光影设计：[D] 四组顶灯冷白柔光。
表演设计：[D] 手部动作与视线配合。

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] 从黑场淡入。
剪辑触发：[D] Miguel 抬手时切。
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] 抬手动作完成。
转场执行：[M] <post_production>

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无
"""

MULTI_SHOT_MASTER = """\
<!-- template: director_master v1.0 -->

Master 版本：EP14/v1.0
父版本：无

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
交出边界 ID：[M] EP14-2
边界连续性：[M] <continuous>
转场执行：[M] <post_production>
生成模式：[M] <omni_reference>
参考资产：[M] [char_runner_01|identity]
参考职责：[D] char_runner_01 约束身份和服装。
参考优先级：[D] 身份优先于运镜。

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
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
转场执行：[M] <post_production>
生成模式：[M] <omni_reference>
参考资产：[M] [char_runner_01|continuity]
参考职责：[D] char_runner_01 约束连续性。
参考优先级：[D] 连续性优先。
"""

MASTER_WITH_PROPS = """\
<!-- template: director_master v1.0 -->

Master 版本：INVEST/v1.0

## Shot INVEST-1 | 12s

剧本事实：[D] Detective examines the evidence on the table.
原文定位：[M] INVEST L5-L12
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <investigation_object>
时间控制：[M] <second_nodes>

开场状态键：[M]
  - character:Detective position:table_front facing:N screen_direction:static posture:seated
  - prop:notebook held_by:Detective location:left_hand
  - prop:magnifier held_by:none location:table_center
  - light_main direction:left color_temp:3200K ratio:1:4
  - action_phase:static

结束状态键：[M]
  - character:Detective position:table_front facing:N screen_direction:static posture:seated
  - prop:notebook held_by:Detective location:left_hand
  - prop:magnifier held_by:Detective location:right_hand
  - light_main direction:left color_temp:3200K ratio:1:4
  - action_phase:static

进入边界 ID：[M] SCENE_ENTRY
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
转场执行：[M] <in_camera>
生成模式：[M] <first_last_frame>
参考资产：[M] [loc_lab_01|location, prop_table_set_01|continuity]
参考职责：[D] loc_lab_01 约束空间材质；prop_table_set_01 约束道具摆放。
参考优先级：[D] 证据位置不可变。
"""

V4_SHARED_BOUNDARY_MASTER = """\
Master 版本：V4_SCENE/v1.0

## Boundary V4_SCENE-B0 | SCENE_ENTRY -> V4_SCENE-1
边界关系：[M] <scene_entry>
转场执行：[M] <post_production>
剪辑触发：[D] 黑场在脚步声响起时切入。
交接描述：[D] A 位于门内，右脚刚落地。
接入状态键：[M]
  - character:A position:door facing:E screen_direction:left_to_right posture:running
  - light_main direction:left color_temp:4000K ratio:1:3
  - action_phase:prepare

## Shot V4_SCENE-1 | 5s
剧本事实：[D] A runs from the door to mid-room.
原文定位：[M] V4_SCENE L1-L3
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>
生成模式：[M] <text_only>
参考资产：[M] 无

## Boundary V4_SCENE-B1 | V4_SCENE-1 -> V4_SCENE-2
边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] A 的右脚触地时硬切。
交接描述：[D] A 位于房间中央，身体继续向右运动。
交出状态键：[M]
  - character:A position:mid_room facing:E screen_direction:left_to_right posture:running
  - light_main direction:left color_temp:4000K ratio:1:3
  - action_phase:travel
接入状态键：[M] <same>

## Shot V4_SCENE-2 | 7s
剧本事实：[D] A continues running and stops at the far wall.
原文定位：[M] V4_SCENE L4-L6
生成单元：[M] 一个独立 SD2.0 视频段。
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>
生成模式：[M] <text_only>
参考资产：[M] 无

## Boundary V4_SCENE-B2 | V4_SCENE-2 -> SCENE_EXIT
边界关系：[M] <scene_exit>
转场执行：[M] <post_production>
剪辑触发：[D] A 停稳后切出。
交接描述：[D] A 位于远墙前，身体静止。
交出状态键：[M]
  - character:A position:far_wall facing:E screen_direction:static posture:standing
  - light_main direction:left color_temp:4000K ratio:1:3
  - action_phase:recover
"""


class SuccessfulCompilationTests(unittest.TestCase):
    """Verify correct compilation of valid Master files."""

    def test_single_shot_compiles_and_validates(self) -> None:
        path = _write_temp("master_single.md", SINGLE_SHOT_MASTER)
        manifest = compile_master(path)
        jsonschema.validate(manifest, SCHEMA)
        self.assertEqual(manifest["scene_id"], "TEST_S1")
        self.assertEqual(len(manifest["shots"]), 1)
        shot = manifest["shots"][0]
        self.assertEqual(shot["shot_id"], "TEST_S1-1")
        self.assertEqual(shot["duration"], 8.0)
        self.assertEqual(shot["scene_expression"], "conversation_power")
        self.assertEqual(shot["generation_mode"], "text_only")
        self.assertEqual(shot["reference_assets"], [])
        self.assertEqual(shot["entry_boundary_id"], "SCENE_ENTRY")
        self.assertEqual(shot["exit_boundary_id"], "SCENE_EXIT")

    def test_continuity_sensitive_state_fields_are_projected(self) -> None:
        enhanced = SINGLE_SHOT_MASTER.replace(
            "posture:standing",
            "posture:standing wardrobe:grey_suit injury:none",
        ).replace(
            "  - action_phase:static",
            "  - action_phase:static\n"
            "  - story_time:day\n"
            "  - weather:rain\n"
            "  - environment:office_wet_windows",
        )
        path = _write_temp("master_continuity_fields.md", enhanced)
        manifest = compile_master(path)
        jsonschema.validate(manifest, SCHEMA)
        self.assertEqual(manifest["manifest_version"], "1.1")
        for key in ("opening_state_keys", "closing_state_keys"):
            state = manifest["shots"][0][key]
            self.assertEqual(state["characters"][0]["wardrobe"], "grey_suit")
            self.assertEqual(state["characters"][0]["injury"], "none")
            self.assertEqual(state["story_time"], "day")
            self.assertEqual(state["weather"], "rain")
            self.assertEqual(state["environment"], "office_wet_windows")

    def test_multi_shot_compiles_with_chained_boundaries(self) -> None:
        path = _write_temp("master_multi.md", MULTI_SHOT_MASTER)
        manifest = compile_master(path)
        jsonschema.validate(manifest, SCHEMA)
        self.assertEqual(len(manifest["shots"]), 2)
        s0, s1 = manifest["shots"]
        self.assertEqual(s0["exit_boundary_id"], "EP14-2")
        self.assertEqual(s1["entry_boundary_id"], "EP14-1")
        self.assertEqual(s0["exit_boundary_id"], s1["shot_id"])
        self.assertEqual(s1["entry_boundary_id"], s0["shot_id"])
        self.assertEqual(s0["reference_assets"], [
            {"asset_id": "char_runner_01", "responsibility": "identity"}
        ])
        self.assertEqual(s1["reference_assets"], [
            {"asset_id": "char_runner_01", "responsibility": "continuity"}
        ])

    def test_v4_master_projects_shared_boundaries_once(self) -> None:
        path = _write_temp("master_v4_shared.md", V4_SHARED_BOUNDARY_MASTER)
        manifest = compile_master(path)
        jsonschema.validate(manifest, SCHEMA)
        self.assertEqual(manifest["manifest_version"], "1.2")
        self.assertEqual(len(manifest["boundaries"]), 3)
        shared = manifest["boundaries"][1]
        self.assertEqual(shared["boundary_id"], "V4_SCENE-B1")
        self.assertEqual(shared["outgoing_state_keys"], shared["incoming_state_keys"])
        self.assertEqual(manifest["shots"][0]["exit_boundary_id"], "V4_SCENE-B1")
        self.assertEqual(manifest["shots"][1]["entry_boundary_id"], "V4_SCENE-B1")
        self.assertEqual(
            manifest["shots"][0]["closing_state_keys"],
            manifest["shots"][1]["opening_state_keys"],
        )

    def test_v4_machine_enums_accept_bare_values(self) -> None:
        bare = V4_SHARED_BOUNDARY_MASTER
        for value in (
            "scene_entry", "continuous", "scene_exit", "post_production",
            "action_chase", "event_nodes", "text_only", "same",
        ):
            bare = bare.replace(f"<{value}>", value)
        manifest = compile_master(_write_temp("master_v4_bare_enums.md", bare))

        self.assertEqual(manifest["shots"][0]["scene_expression"], "action_chase")
        self.assertEqual(manifest["shots"][0]["timing_mode"], "event_nodes")
        self.assertEqual(manifest["shots"][0]["generation_mode"], "text_only")
        self.assertEqual(manifest["boundaries"][1]["relation"], "continuous")
        self.assertEqual(
            manifest["boundaries"][1]["outgoing_state_keys"],
            manifest["boundaries"][1]["incoming_state_keys"],
        )

    def test_v4_continuous_boundary_rejects_duplicate_incoming_state(self) -> None:
        bad = V4_SHARED_BOUNDARY_MASTER.replace(
            "接入状态键：[M] <same>",
            "接入状态键：[M]\n"
            "  - character:A position:mid_room facing:E screen_direction:left_to_right posture:running\n"
            "  - light_main direction:left color_temp:4000K ratio:1:3\n"
            "  - action_phase:travel",
        )
        with self.assertRaisesRegex(CompilerError, "continuous requires"):
            compile_master(_write_temp("master_v4_duplicate_state.md", bad))

    def test_investigation_with_props(self) -> None:
        path = _write_temp("master_props.md", MASTER_WITH_PROPS)
        manifest = compile_master(path)
        jsonschema.validate(manifest, SCHEMA)
        shot = manifest["shots"][0]
        self.assertEqual(len(shot["opening_state_keys"]["props"]), 2)
        self.assertEqual(shot["opening_state_keys"]["props"][0]["held_by"], "Detective")
        self.assertEqual(shot["closing_state_keys"]["props"][1]["held_by"], "Detective")
        self.assertEqual(shot["transition_execution"], "in_camera")
        self.assertEqual(shot["generation_mode"], "first_last_frame")

    def test_master_hash_is_consistent(self) -> None:
        path1 = _write_temp("master_hash_a.md", SINGLE_SHOT_MASTER)
        path2 = _write_temp("master_hash_b.md", SINGLE_SHOT_MASTER)
        h1 = compile_master(path1)["master_content_hash"]
        h2 = compile_master(path2)["master_content_hash"]
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_master_hash_differs_when_content_changes(self) -> None:
        path1 = _write_temp("master_h1.md", SINGLE_SHOT_MASTER)
        path2 = _write_temp("master_h2.md", SINGLE_SHOT_MASTER.replace("8s", "9s"))
        h1 = compile_master(path1)["master_content_hash"]
        h2 = compile_master(path2)["master_content_hash"]
        self.assertNotEqual(h1, h2)

    def test_compile_to_file_writes_valid_json(self) -> None:
        master = _write_temp("master_file.md", SINGLE_SHOT_MASTER)
        out = _write_temp("out.json", "{}")
        compile_to_file(master, out)
        manifest = json.loads(out.read_text(encoding="utf-8"))
        jsonschema.validate(manifest, SCHEMA)
        self.assertEqual(manifest["compiler_version"], "2.0.0")

    def test_gbk_encoded_master(self) -> None:
        content = MULTI_SHOT_MASTER.encode("gbk")
        p = _TEMP_ROOT / "master_gbk.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        manifest = compile_master(p)
        jsonschema.validate(manifest, SCHEMA)
        self.assertEqual(len(manifest["shots"]), 2)


class FailureTests(unittest.TestCase):
    """Every required field missing or invalid must raise CompilerError."""

    def test_no_shot_headers_raises(self) -> None:
        p = _write_temp("no_shots.md", "Master 版本：X/v1.0\n\n# No shots here\n")
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("No Shot headers", str(ctx.exception))

    def test_missing_master_version_raises(self) -> None:
        p = _write_temp("no_version.md", "## Shot X-1 | 5s\n剧本事实：[D] x\n原文定位：[M] X L1-L2\n" +
                        "生成单元：[M] x\n场景表达：[M] <action_chase>\n时间控制：[M] <event_nodes>\n" +
                        "开场状态键：[M]\n  - light_main direction:top color_temp:4000K ratio:1:3\n  - action_phase:static\n" +
                        "结束状态键：[M]\n  - light_main direction:top color_temp:4000K ratio:1:3\n  - action_phase:static\n" +
                        "进入边界 ID：[M] SCENE_ENTRY\n交出边界 ID：[M] SCENE_EXIT\n转场执行：[M] <post_production>\n生成模式：[M] <text_only>\n参考资产：[M] 无\n")
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Master version", str(ctx.exception))

    def test_scene_id_mismatch_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("TEST_S1-1 | 8s", "WRONG-1 | 8s")
        p = _write_temp("mismatch.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("does not match", str(ctx.exception))

    def test_missing_source_location_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("原文定位：[M] TEST_S1 L12-L15", "")
        p = _write_temp("no_source.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("原文定位", str(ctx.exception))

    def test_invalid_expression_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("<conversation_power>", "<dialogue>")
        p = _write_temp("bad_expr.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("scene_expression", str(ctx.exception))

    def test_invalid_timing_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("<event_nodes>", "<frame_nodes>")
        p = _write_temp("bad_timing.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("timing_mode", str(ctx.exception))

    def test_invalid_generation_mode_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("<text_only>", "<hybrid>")
        p = _write_temp("bad_gen.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("generation_mode", str(ctx.exception))

    def test_invalid_transition_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("<post_production>", "<dissolve>")
        p = _write_temp("bad_trans.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("transition_execution", str(ctx.exception))

    def test_missing_boundary_continuity_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace(
            "边界连续性：[M] <scene_exit>", ""
        )
        p = _write_temp("missing_boundary_continuity.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("boundary_continuity", str(ctx.exception))

    def test_invalid_boundary_continuity_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace(
            "<scene_exit>", "<jump_without_contract>"
        )
        p = _write_temp("invalid_boundary_continuity.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("boundary_continuity", str(ctx.exception))

    def test_missing_entry_boundary_is_derived(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("进入边界 ID：[M] SCENE_ENTRY", "")
        p = _write_temp("no_entry.md", bad)
        manifest = compile_master(p)
        self.assertEqual(manifest["shots"][0]["entry_boundary_id"], "SCENE_ENTRY")

    def test_missing_exit_boundary_is_derived(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("交出边界 ID：[M] SCENE_EXIT", "")
        p = _write_temp("no_exit.md", bad)
        manifest = compile_master(p)
        self.assertEqual(manifest["shots"][0]["exit_boundary_id"], "SCENE_EXIT")

    def test_declared_boundary_must_match_derived_chain(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace(
            "交出边界 ID：[M] SCENE_EXIT",
            "交出边界 ID：[M] TEST_S1-9",
        )
        p = _write_temp("wrong_declared_exit.md", bad)
        with self.assertRaisesRegex(CompilerError, "mechanical chain"):
            compile_master(p)

    def test_missing_assets_field_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("参考资产：[M] 无", "")
        p = _write_temp("no_assets.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("参考资产", str(ctx.exception))

    def test_missing_opening_state_keys_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("开场状态键：[M]", "")
        p = _write_temp("no_open.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("开场状态键", str(ctx.exception))

    def test_missing_closing_state_keys_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("结束状态键：[M]", "")
        p = _write_temp("no_close.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("结束状态键", str(ctx.exception))

    def test_missing_light_main_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("  - light_main direction:top color_temp:5000K ratio:1:2", "")
        p = _write_temp("no_light.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("light_main", str(ctx.exception))

    def test_empty_story_fact_raises(self) -> None:
        import re
        bad = re.sub(
            r"^剧本事实：\[D\] .+$",
            "剧本事实：[D] ",
            SINGLE_SHOT_MASTER,
            flags=re.MULTILINE,
        )
        p = _write_temp("empty_fact.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Empty", str(ctx.exception))

    def test_invalid_action_phase_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("action_phase:static", "action_phase:flying")
        p = _write_temp("bad_phase.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("action_phase", str(ctx.exception))

    def test_missing_action_phase_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("  - action_phase:static\n", "")
        p = _write_temp("missing_phase.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("action_phase", str(ctx.exception))

    def test_asset_responsibility_is_required(self) -> None:
        bad = MULTI_SHOT_MASTER.replace(
            "[char_runner_01|identity]", "[char_runner_01]", 1
        )
        p = _write_temp("missing_asset_responsibility.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("<asset_id>|<responsibility>", str(ctx.exception))

    def test_invalid_asset_responsibility_raises(self) -> None:
        bad = MULTI_SHOT_MASTER.replace(
            "char_runner_01|identity", "char_runner_01|mood", 1
        )
        p = _write_temp("bad_asset_responsibility.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Invalid responsibility", str(ctx.exception))

    def test_duplicate_machine_field_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace(
            "时间控制：[M] <event_nodes>",
            "时间控制：[M] <event_nodes>\n时间控制：[M] <event_nodes>",
        )
        p = _write_temp("duplicate_field.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Duplicate 'timing_mode'", str(ctx.exception))

    def test_source_scene_mismatch_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace(
            "原文定位：[M] TEST_S1 L12-L15",
            "原文定位：[M] WRONG L12-L15",
        )
        p = _write_temp("source_scene_mismatch.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Source scene_id", str(ctx.exception))

    def test_reversed_source_range_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace("L12-L15", "L15-L12")
        p = _write_temp("source_range_reversed.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("reversed", str(ctx.exception))

    def test_nonconsecutive_shot_numbers_raise(self) -> None:
        bad = MULTI_SHOT_MASTER.replace("## Shot EP14-2", "## Shot EP14-3")
        p = _write_temp("shot_gap.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("consecutive", str(ctx.exception))

    def test_malformed_shot_header_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace(
            "## Shot TEST_S1-1 | 8s", "## Shot TEST_S1-1 | eight seconds"
        )
        p = _write_temp("malformed_header.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Malformed Shot header", str(ctx.exception))

    def test_malformed_state_key_line_raises(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace(
            "position:whiteboard_front", "position whiteboard_front", 1
        )
        p = _write_temp("malformed_state.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Malformed or unknown state-key", str(ctx.exception))

    def test_duplicate_state_entity_raises(self) -> None:
        line = "  - character:Miguel position:whiteboard_front facing:N screen_direction:static posture:standing"
        bad = SINGLE_SHOT_MASTER.replace(line, f"{line}\n{line}", 1)
        p = _write_temp("duplicate_entity.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Duplicate character", str(ctx.exception))

    def test_opening_closing_entity_sets_must_match(self) -> None:
        bad = SINGLE_SHOT_MASTER.replace(
            "character:Miguel position:whiteboard_front facing:NE screen_direction:static",
            "character:Other position:whiteboard_front facing:NE screen_direction:static",
        )
        p = _write_temp("state_entity_mismatch.md", bad)
        with self.assertRaises(CompilerError) as ctx:
            compile_master(p)
        self.assertIn("Opening/closing characters keys differ", str(ctx.exception))

    def test_unreadable_file_raises(self) -> None:
        p = _TEMP_ROOT / "nonexistent.md"
        with self.assertRaises((CompilerError, FileNotFoundError, OSError)):
            compile_master(p)


class CLITests(unittest.TestCase):
    """End-to-end CLI tests using the real command."""

    def test_cli_compiles_and_exits_zero(self) -> None:
        import subprocess
        import sys
        master = _write_temp("cli_master.md", SINGLE_SHOT_MASTER)
        out = _write_temp("cli_out.json", "{}")
        result = subprocess.run(
            [sys.executable, "-m", "master_compiler", str(master), str(out)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        manifest = json.loads(out.read_text(encoding="utf-8"))
        jsonschema.validate(manifest, SCHEMA)

    def test_cli_missing_file_exits_nonzero(self) -> None:
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "master_compiler", "nonexistent_file.md"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_cli_bad_master_exits_nonzero(self) -> None:
        import subprocess
        import sys
        bad = _write_temp("cli_bad.md", "# Not a master\n")
        result = subprocess.run(
            [sys.executable, "-m", "master_compiler", str(bad)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)


class ManifestRoundtripTests(unittest.TestCase):
    """Compiled manifest must round-trip: re-read and validate identically."""

    def test_roundtrip_single_shot(self) -> None:
        master = _write_temp("rt_master.md", SINGLE_SHOT_MASTER)
        out = _write_temp("rt_out.json", "{}")
        compile_to_file(master, out)
        m1 = json.loads(out.read_text(encoding="utf-8"))
        m2 = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(m1, m2)

    def test_manifest_has_no_creative_fields(self) -> None:
        master = _write_temp("nc_master.md", SINGLE_SHOT_MASTER)
        manifest = compile_master(master)
        creative_keys = {"narrative", "camera_prose", "composition_prose",
                         "lighting_prose", "performance_prose", "director_notes"}
        for shot in manifest["shots"]:
            for key in creative_keys:
                self.assertNotIn(key, shot)


if __name__ == "__main__":
    unittest.main()
