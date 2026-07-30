"""Tests for reference_plan_check.py — mode/asset/responsibility validation."""

from __future__ import annotations

import json
import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from master_compiler import compile_to_file
from reference_plan_check import RefIssue, check_references


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_refplan_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


def _compile(master_text: str, label: str) -> Path:
    p = _tmpdir() / f"{label}_master.md"
    p.write_text(master_text, encoding="utf-8")
    manifest_p = _tmpdir() / f"{label}_manifest.json"
    compile_to_file(p, manifest_p)
    return manifest_p


def _write_manifest(data: dict, label: str) -> Path:
    p = _tmpdir() / f"{label}_manifest.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


_VALID_TEXT_ONLY = """\
<!-- template: director_master v1.0 -->
Master 版本：TXT/v1.0

## Shot TXT-1 | 8s
剧本事实：[D] x
原文定位：[M] TXT L1-L1
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
"""

_VALID_OMNI = """\
<!-- template: director_master v1.0 -->
Master 版本：OMNI/v1.0

## Shot OMNI-1 | 8s
剧本事实：[D] x
原文定位：[M] OMNI L1-L1
生成单元：[M] x
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>
开场状态键：[M]
  - character:A position:p1 facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel
结束状态键：[M]
  - character:A position:p2 facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel
进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] x
转场执行：[M] <post_production>
生成模式：[M] <omni_reference>
参考资产：[M] [char_A|identity, loc_room|location]
参考职责：[D] char_A constrains identity, loc_room constrains location.
参考优先级：[D] Identity over camera.
"""

_VALID_FIRST_LAST = """\
<!-- template: director_master v1.0 -->
Master 版本：FRAME/v1.0

## Shot FRAME-1 | 8s
剧本事实：[D] x
原文定位：[M] FRAME L1-L1
生成单元：[M] x
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>
开场状态键：[M]
  - character:A position:p1 facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:launch
结束状态键：[M]
  - character:A position:p2 facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:recover
进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] x
转场执行：[M] <post_production>
生成模式：[M] <first_last_frame>
参考资产：[M] [frame_open|first_frame, frame_close|last_frame]
参考职责：[D] x
参考优先级：[D] x
"""

_BAD_FIRST_LAST_ROLES = _VALID_FIRST_LAST.replace(
    "frame_close|last_frame", "frame_close|continuity"
)

_TEXT_WITH_ASSETS_BAD = """\
<!-- template: director_master v1.0 -->
Master 版本：BADTXT/v1.0

## Shot BADTXT-1 | 8s
剧本事实：[D] x
原文定位：[M] BADTXT L1-L1
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
参考资产：[M] [char_A|identity]
参考职责：[D] x
参考优先级：[D] x
"""

_DUPLICATE_ASSET = """\
<!-- template: director_master v1.0 -->
Master 版本：DUP/v1.0

## Shot DUP-1 | 8s
剧本事实：[D] x
原文定位：[M] DUP L1-L1
生成单元：[M] x
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>
开场状态键：[M]
  - character:A position:p1 facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel
结束状态键：[M]
  - character:A position:p2 facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel
进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] x
转场执行：[M] <post_production>
生成模式：[M] <omni_reference>
参考资产：[M] [char_A|identity, char_A|continuity]
参考职责：[D] x
参考优先级：[D] x
"""

# For invalid responsibility, we test directly against the checker
# (compiler catches this first; checker is defense-in-depth for hand-edited manifests)
_BAD_RESP_MANIFEST = {
    "manifest_version": "1.0", "scene_id": "BADRESP",
    "master_version": "BADRESP/v1.0",
    "master_content_hash": "a" * 64, "compiler_version": "1.0.0",
    "shots": [{
        "shot_id": "BADRESP-1", "duration": 8.0,
        "scene_expression": "action_chase", "timing_mode": "event_nodes",
        "story_fact_ref": {"text_start": "x", "source_scene_id": "BADRESP", "source_line_start": 1, "source_line_end": 1},
        "opening_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "travel"},
        "closing_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "travel"},
        "entry_boundary_id": "SCENE_ENTRY", "exit_boundary_id": "SCENE_EXIT",
        "boundary_continuity": "scene_exit",
        "transition_execution": "post_production", "generation_mode": "omni_reference",
        "reference_assets": [{"asset_id": "char_A", "responsibility": "mood"}],
    }],
}

_CONFLICTING_RESPONSIBILITY = """\
<!-- template: director_master v1.0 -->
Master 版本：CONF/v1.0

## Shot CONF-1 | 8s
剧本事实：[D] x
原文定位：[M] CONF L1-L1
生成单元：[M] x
场景表达：[M] <action_chase>
时间控制：[M] <event_nodes>
开场状态键：[M]
  - character:A position:p1 facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel
结束状态键：[M]
  - character:A position:p2 facing:S screen_direction:left_to_right posture:running
  - light_main direction:top color_temp:4000K ratio:1:3
  - action_phase:travel
进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] x
交出边界 ID：[M] SCENE_EXIT
边界连续性：[M] <scene_exit>
交出边界：[D] x
转场执行：[M] <post_production>
生成模式：[M] <omni_reference>
参考资产：[M] [char_A|identity, photo_ref|identity]
参考职责：[D] x
参考优先级：[D] x
"""


class ReferencePlanTests(unittest.TestCase):

    def test_text_only_empty_assets_passes(self) -> None:
        mp = _compile(_VALID_TEXT_ONLY, "rp1")
        report = check_references(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_omni_with_valid_assets_passes(self) -> None:
        mp = _compile(_VALID_OMNI, "rp2")
        report = check_references(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_first_last_frame_requires_explicit_roles(self) -> None:
        report = check_references(_compile(_VALID_FIRST_LAST, "rp_first_last"))
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_first_last_frame_missing_role_fails(self) -> None:
        report = check_references(_compile(_BAD_FIRST_LAST_ROLES, "rp_bad_frames"))
        self.assertFalse(report.ok)
        self.assertTrue(any("last_frame" in issue.detail for issue in report.issues))

    def test_text_only_with_assets_detected(self) -> None:
        mp = _compile(_TEXT_WITH_ASSETS_BAD, "rp3")
        report = check_references(mp)
        self.assertFalse(report.ok)
        cats = {i.category for i in report.issues}
        self.assertIn("asset_count", cats)

    def test_same_asset_can_have_explicit_multiple_responsibilities(self) -> None:
        mp = _compile(_DUPLICATE_ASSET, "rp4")
        report = check_references(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_invalid_responsibility_detected(self) -> None:
        mp = _write_manifest(_BAD_RESP_MANIFEST, "rp5")
        report = check_references(mp)
        self.assertFalse(report.ok)
        self.assertTrue(any("manifest" == i.category for i in report.issues))

    def test_multiple_assets_may_share_one_responsibility(self) -> None:
        mp = _compile(_CONFLICTING_RESPONSIBILITY, "rp6")
        report = check_references(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_with_asset_index_file_check(self) -> None:
        mp = _compile(_VALID_OMNI, "rp7")
        idx = _tmpdir() / "asset_index.json"
        idx.write_text(json.dumps({
            "schema_version": "1.1",
            "description": "test asset index",
            "updated_at": "2026-07-16T00:00:00+08:00",
            "asset_root": ".",
            "asset_count": 2,
            "assets": [
                {"asset_id": "char_A", "path": "char_A.png",
                 "media_type": "image", "content_sha256": "a" * 64,
                 "byte_size": 0, "status": "missing", "responsibilities": ["identity"]},
                {"asset_id": "loc_room", "path": "loc_room.png",
                 "media_type": "image", "content_sha256": "b" * 64,
                 "byte_size": 0, "status": "missing", "responsibilities": ["location"]},
            ]
        }), encoding="utf-8")
        # Files don't exist, so we expect "file" issues
        report = check_references(mp, idx)
        self.assertFalse(report.ok)
        cats = {i.category for i in report.issues}
        self.assertIn("file", cats)

    def test_empty_asset_index_does_not_skip_missing_asset_checks(self) -> None:
        mp = _compile(_VALID_OMNI, "rp_empty_index")
        idx = _tmpdir() / "empty_asset_index.json"
        idx.write_text(json.dumps({
            "schema_version": "1.1", "description": "empty test index",
            "updated_at": "2026-07-16T00:00:00+08:00", "asset_root": ".",
            "asset_count": 0, "assets": [],
        }), encoding="utf-8")
        report = check_references(mp, idx)
        self.assertFalse(report.ok)
        self.assertTrue(any("not found" in issue.detail for issue in report.issues))

    def test_relative_asset_paths_resolve_from_index_directory(self) -> None:
        mp = _compile(_VALID_OMNI, "rp_relative")
        index_dir = _tmpdir() / "relative_assets"
        index_dir.mkdir(exist_ok=True)
        (index_dir / "char_A.png").write_bytes(b"image")
        (index_dir / "loc_room.png").write_bytes(b"image")
        idx = index_dir / "ASSET_INDEX.json"
        idx.write_text(json.dumps({
            "schema_version": "1.1",
            "description": "test asset index",
            "updated_at": "2026-07-16T00:00:00+08:00",
            "asset_root": ".",
            "asset_count": 2,
            "assets": [
                {"asset_id": "char_A", "path": "char_A.png", "media_type": "image",
                 "content_sha256": hashlib.sha256(b"image").hexdigest(),
                 "byte_size": 5, "status": "available", "responsibilities": ["identity"]},
                {"asset_id": "loc_room", "path": "loc_room.png", "media_type": "image",
                 "content_sha256": hashlib.sha256(b"image").hexdigest(),
                 "byte_size": 5, "status": "available", "responsibilities": ["location"]},
            ]
        }), encoding="utf-8")
        report = check_references(mp, idx)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_capability_profile_controls_asset_count(self) -> None:
        mp = _compile(_VALID_OMNI, "rp_capability")
        profile = _tmpdir() / "limited_capability.json"
        bundled = Path(__file__).with_name("sd2_capability_profile.json")
        profile_data = json.loads(bundled.read_text(encoding="utf-8"))
        profile_data["modes"]["omni_reference"]["asset_count"]["max"] = 1
        profile.write_text(json.dumps(profile_data, ensure_ascii=False), encoding="utf-8")
        report = check_references(mp, capability_profile_path=profile)
        self.assertFalse(report.ok)
        self.assertTrue(any(issue.category == "asset_count" for issue in report.issues))


class CLITests(unittest.TestCase):
    def test_cli_pass_exits_zero(self) -> None:
        import subprocess
        import sys
        mp = _compile(_VALID_TEXT_ONLY, "cli_rp1")
        result = subprocess.run(
            [sys.executable, "-m", "reference_plan_check", str(mp)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")

    def test_cli_fail_exits_nonzero(self) -> None:
        import subprocess
        import sys
        mp = _compile(_TEXT_WITH_ASSETS_BAD, "cli_rp2")
        result = subprocess.run(
            [sys.executable, "-m", "reference_plan_check", str(mp)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
