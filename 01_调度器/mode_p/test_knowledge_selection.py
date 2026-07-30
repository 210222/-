"""Phase 3 acceptance: knowledge selection across scene types and reference modes.

Tests context_retriever capsule selection and reference_plan_check mode validation
for all major scene types: dialogue, action, suspense, crowd, cross-space,
no-match, first-last-frame, omni-reference, and conflicting assets.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from context_retriever import retrieve_context, normalize_query
from reference_plan_check import check_references
from master_compiler import compile_to_file


_INDEX = Path(__file__).with_name("knowledge") / "knowledge_index.json"
_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_knowledge_selection_"))


def _compile(master_text: str, label: str) -> Path:
    p = _TEMP_ROOT / f"{label}_master.md"
    p.write_text(master_text, encoding="utf-8")
    manifest_p = _TEMP_ROOT / f"{label}_manifest.json"
    compile_to_file(p, manifest_p)
    return manifest_p


def _base_master(mode: str, assets: str, scene_expr: str = "conversation_power") -> str:
    return f"""\
<!-- template: director_master v1.0 -->
Master 版本：SEL/v1.0

## Shot SEL-1 | 8s
剧本事实：[D] Test scene.
原文定位：[M] SEL L1-L1
生成单元：[M] x
场景表达：[M] <{scene_expr}>
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
生成模式：[M] <{mode}>
参考资产：[M] {assets}
参考职责：[D] x
参考优先级：[D] x
"""


class KnowledgeRetrievalTests(unittest.TestCase):
    """Verify that Director requests, not keyword scoring, select capsules."""

    def test_director_selects_dialogue_capsule(self) -> None:
        q = normalize_query({"scene_types": ["dialogue"], "drama_intents": ["relationship_change"],
                              "space_conditions": ["indoor"], "character_count": 2,
                              "motion_complexity": "low",
                              "requested_capsules": ["capsules/dialogue_power.md"]})
        summary = retrieve_context(q, _INDEX)
        self.assertIn("capsules/dialogue_power.md", summary["capsules"])

    def test_director_selects_action_capsule(self) -> None:
        q = normalize_query({"scene_types": ["action", "chase"], "drama_intents": ["survival"],
                              "space_conditions": ["open"], "character_count": 2,
                              "motion_complexity": "high",
                              "requested_capsules": ["capsules/action_chase.md"]})
        summary = retrieve_context(q, _INDEX)
        self.assertIn("capsules/action_chase.md", summary["capsules"])

    def test_director_selects_suspense_capsule(self) -> None:
        q = normalize_query({"scene_types": ["suspense"], "drama_intents": ["hide_reveal"],
                              "space_conditions": ["enclosed"], "character_count": 1,
                              "requested_capsules": ["capsules/suspense_reveal.md"]})
        summary = retrieve_context(q, _INDEX)
        self.assertTrue(any("suspense" in c for c in summary["capsules"]))

    def test_director_selects_crowd_capsule(self) -> None:
        q = normalize_query({"scene_types": ["crowd", "multi_person"],
                              "drama_intents": ["attention_handoff"],
                              "space_conditions": ["indoor"], "character_count": 4,
                              "motion_complexity": "medium",
                              "requested_capsules": ["capsules/crowd_attention.md"]})
        summary = retrieve_context(q, _INDEX)
        self.assertIn("capsules/crowd_attention.md", summary["capsules"])

    def test_director_selects_transition_capsule(self) -> None:
        q = normalize_query({"scene_types": ["transition", "multi_location"],
                              "drama_intents": ["location_change"],
                              "space_conditions": ["multiple_locations"],
                              "character_count": 2,
                              "requested_capsules": ["capsules/cross_space_transition.md"]})
        summary = retrieve_context(q, _INDEX)
        self.assertIn("capsules/cross_space_transition.md", summary["capsules"])

    def test_scene_metadata_alone_returns_core_only(self) -> None:
        q = normalize_query({"scene_types": ["musical_dance_number"],
                              "character_count": 20})
        summary = retrieve_context(q, _INDEX)
        self.assertTrue(summary["no_capsule_match"])
        self.assertEqual(len(summary["capsules"]), 0)
        self.assertEqual(len(summary["core"]), 4)
        self.assertFalse(summary.get("historical_fallback_used", False))

    def test_director_requested_capsule_is_loaded_exactly(self) -> None:
        q = normalize_query({"scene_types": ["musical_dance_number"],
                              "requested_capsules": ["capsules/omni_reference.md"]})
        summary = retrieve_context(q, _INDEX)
        self.assertEqual(summary["capsules"], ["capsules/omni_reference.md"])


class ReferenceSelectionTests(unittest.TestCase):
    """Verify reference plan checking for each generation mode."""

    def setUp(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    def test_text_only_mode_rejects_assets(self) -> None:
        mp = _compile(_base_master("text_only", "[char_A|identity]"), "txt")
        report = check_references(mp)
        self.assertFalse(report.ok)
        cats = {i.category for i in report.issues}
        self.assertIn("asset_count", cats)

    def test_text_only_empty_passes(self) -> None:
        mp = _compile(_base_master("text_only", "无"), "txt_ok")
        report = check_references(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_omni_reference_min_one_asset(self) -> None:
        mp = _compile(_base_master("omni_reference", "[char_A|identity]", "action_chase"), "omni")
        report = check_references(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_omni_reference_empty_fails(self) -> None:
        mp = _compile(_base_master("omni_reference", "无", "action_chase"), "omni_empty")
        report = check_references(mp)
        self.assertFalse(report.ok)

    def test_first_last_frame_exactly_two(self) -> None:
        mp = _compile(_base_master("first_last_frame",
                                    "[frame_start|first_frame, frame_end|last_frame]",
                                    "action_chase"), "flf_ok")
        report = check_references(mp)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_first_last_frame_wrong_count_fails(self) -> None:
        mp = _compile(_base_master("first_last_frame",
                                    "[frame_start|first_frame]", "action_chase"), "flf_bad")
        report = check_references(mp)
        self.assertFalse(report.ok)

    def test_conflicting_identity_assets_detected(self) -> None:
        """Truly duplicate asset (same id + same responsibility) — tested via hand-edited manifest."""
        p = _TEMP_ROOT / "dup_manifest.json"
        p.write_text(json.dumps({
            "manifest_version": "1.0", "scene_id": "DUP", "master_version": "DUP/v1.0",
            "master_content_hash": "a" * 64, "compiler_version": "1.5.0",
            "shots": [{
                "shot_id": "DUP-1", "duration": 5, "scene_expression": "action_chase",
                "timing_mode": "event_nodes",
                "story_fact_ref": {"text_start": "x", "source_scene_id": "D", "source_line_start": 1, "source_line_end": 1},
                "opening_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "static"},
                "closing_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "static"},
                "entry_boundary_id": "SCENE_ENTRY", "exit_boundary_id": "SCENE_EXIT",
                "boundary_continuity": "scene_exit",
                "transition_execution": "post_production", "generation_mode": "omni_reference",
                "reference_assets": [
                    {"asset_id": "char_A", "responsibility": "identity"},
                    {"asset_id": "char_A", "responsibility": "identity"},
                ],
            }],
        }), encoding="utf-8")
        report = check_references(p)
        self.assertFalse(report.ok)
        # Duplicate objects with same asset_id are rejected by schema validation
        cats = {i.category for i in report.issues}
        self.assertIn("manifest", cats)

    def test_invalid_responsibility_caught_by_schema(self) -> None:
        """Hand-edited manifest with invalid responsibility is caught by JSON schema validation."""
        p = _TEMP_ROOT / "bad_resp_manifest.json"
        p.write_text(json.dumps({
            "manifest_version": "1.0", "scene_id": "BAD", "master_version": "BAD/v1.0",
            "master_content_hash": "a" * 64, "compiler_version": "1.5.0",
            "shots": [{
                "shot_id": "BAD-1", "duration": 5, "scene_expression": "action_chase",
                "timing_mode": "event_nodes",
                "story_fact_ref": {"text_start": "x", "source_scene_id": "B", "source_line_start": 1, "source_line_end": 1},
                "opening_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "static"},
                "closing_state_keys": {"characters": [], "props": [], "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"}, "action_phase": "static"},
                "entry_boundary_id": "SCENE_ENTRY", "exit_boundary_id": "SCENE_EXIT",
                "boundary_continuity": "scene_exit",
                "transition_execution": "post_production", "generation_mode": "omni_reference",
                "reference_assets": [{"asset_id": "bad", "responsibility": "invalid_role"}],
            }],
        }), encoding="utf-8")
        report = check_references(p)
        self.assertFalse(report.ok)
        # Schema validates responsibility enum; caught as manifest error
        cats = {i.category for i in report.issues}
        self.assertIn("manifest", cats)


if __name__ == "__main__":
    unittest.main()
