"""Phase 2 multi-scene acceptance through facts, commits, and review gate."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from batch_scheduler import schedule_batches
from episode_docs_check import check_episode_docs
from episode_review import prepare_review, review_gate, submit_review
from episode_templates import generate_continuity_ledger, generate_visual_bible
from scene_bridge import (
    commit_batch_state,
    generate_ledger_snapshot,
    validate_handoff,
)
from script_facts_tool import validate_facts
from script_ingest import ingest_script


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_regress_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


_SCRIPT = """\
## Scene 1 — Office — Day

Detective Li sits at the desk wearing a dark grey suit jacket. A folder lies on the desk.

Assistant Chen enters and places a manila envelope beside the folder.

Chen: The lab results are back.

## Scene 2 — Interrogation Room — Night

Li sits across from a suspect. The folder is in Li's left hand. Li still wears the jacket.

Li slides a photo from the folder across the table.

Li: Recognize this?

Li puts the folder down on the table.

## Scene 3 — Office — Morning

Li enters without the jacket. The jacket hangs on the coat rack. A bandage covers Li's right hand.

Li grabs the car keys from the desk and exits.

## Scene 4 — Crime Scene — Dusk

Li arrives wearing the jacket with a cut on the left sleeve. The right-hand bandage remains.

Chen hands Li the same folder. Li opens it and sees a bloodstained letter.

## Scene 5 — Office — Night

Li sits at the desk. The folder is open. The jacket is draped over the chair.

A fresh bandage covers Li's right hand. Rain streaks the window.

Li closes the folder and rests her head in her hands.
"""


_EVENTS = {
    1: "Li wears the grey jacket; the folder and envelope are on the office desk.",
    2: "Li still wears the jacket and moves the folder from hand to table.",
    3: "Li leaves the jacket on the rack; a right-hand bandage is visible; Li takes the keys.",
    4: "Li wears the cut jacket and bandage; Chen transfers the folder to Li.",
    5: "Li removes the jacket; the folder is open; a fresh bandage and rain are visible.",
}


def _facts_text(digest: dict, source_lines: list[str]) -> str:
    lines = [
        "# SCRIPT_FACTS — continuity_regression.md",
        "<!-- contract: script_input v1.1 -->",
        f"<!-- source_sha256: {digest['source_content_hash']} -->",
        "",
    ]
    for scene in digest["scenes"]:
        index = scene["index"]
        start, end = scene["start_line"], scene["end_line"]
        dialogue_lines = [
            line_no for line_no in range(start, end + 1)
            if ":" in source_lines[line_no - 1]
            and not source_lines[line_no - 1].startswith("##")
        ]
        first_body = next(
            line_no for line_no in range(start + 1, end + 1)
            if source_lines[line_no - 1].strip())
        lines.extend([
            f"## 场景 {index} 事实",
            "### 事件",
            f"- [L{first_body}-L{end}] {_EVENTS[index]}",
            "### 对白",
        ])
        if dialogue_lines:
            for line_no in dialogue_lines:
                lines.append(
                    f"- [L{line_no}-L{line_no}] {source_lines[line_no - 1]}")
        else:
            lines.append("- (无)")
        lines.extend([
            "### 连续性入口",
            "- (无)" if index == 1 else
            f"- [L{first_body}-L{first_body}] 本场入场的服装、伤势、道具和环境状态。",
            "",
        ])
    return "\n".join(lines)


def _complete_skeleton(text: str) -> str:
    text = re.sub(r"\[Director:.*?\]", "已完成并由全片事实约束", text,
                  flags=re.DOTALL)
    return text.replace("<Name>", "Detective_Li").replace("<N>", "1")


def _character(wardrobe: str, injury: str, position: str) -> dict:
    return {
        "entity_id": "Li", "position": position, "facing": "N",
        "screen_direction": "static", "posture": "standing",
        "wardrobe": wardrobe, "injury": injury,
    }


def _state(scene: int, *, wardrobe: str, injury: str, position: str,
           folder_holder: str, folder_location: str, story_time: str,
           weather: str, environment: str, jacket_location: str) -> dict:
    return {
        "characters": [_character(wardrobe, injury, position)],
        "props": [
            {"prop_id": "folder", "held_by": folder_holder,
             "location": folder_location},
            {"prop_id": "jacket", "held_by": "Li" if wardrobe != "no_jacket" else "none",
             "location": jacket_location},
        ],
        "light_main": {
            "direction": "window" if scene in (1, 3) else "top",
            "color_temp_k": 5600 if story_time in ("day", "morning", "dusk") else 4200,
            "ratio": "1:3",
        },
        "action_phase": "static",
        "story_time": story_time,
        "weather": weather,
        "environment": environment,
    }


_SCENE_STATES = {
    1: (
        _state(1, wardrobe="grey_jacket", injury="none", position="office_desk",
               folder_holder="none", folder_location="desk", story_time="day",
               weather="clear", environment="office", jacket_location="on_body"),
        _state(1, wardrobe="grey_jacket", injury="none", position="office_desk",
               folder_holder="none", folder_location="desk", story_time="day",
               weather="clear", environment="office", jacket_location="on_body"),
    ),
    2: (
        _state(2, wardrobe="grey_jacket", injury="none", position="interrogation_table",
               folder_holder="Li", folder_location="left_hand", story_time="night",
               weather="clear", environment="interrogation_room", jacket_location="on_body"),
        _state(2, wardrobe="grey_jacket", injury="none", position="interrogation_table",
               folder_holder="none", folder_location="table", story_time="night",
               weather="clear", environment="interrogation_room", jacket_location="on_body"),
    ),
    3: (
        _state(3, wardrobe="no_jacket", injury="right_hand_bandage", position="office_desk",
               folder_holder="none", folder_location="offscreen", story_time="morning",
               weather="clear", environment="office", jacket_location="coat_rack"),
        _state(3, wardrobe="no_jacket", injury="right_hand_bandage", position="office_exit",
               folder_holder="none", folder_location="offscreen", story_time="morning",
               weather="clear", environment="office", jacket_location="coat_rack"),
    ),
    4: (
        _state(4, wardrobe="grey_jacket_cut_left_sleeve",
               injury="right_hand_bandage", position="crime_scene_entry",
               folder_holder="Chen", folder_location="chen_hand", story_time="dusk",
               weather="cloudy", environment="crime_scene", jacket_location="on_body"),
        _state(4, wardrobe="grey_jacket_cut_left_sleeve",
               injury="right_hand_bandage", position="evidence_markers",
               folder_holder="Li", folder_location="left_hand", story_time="dusk",
               weather="cloudy", environment="crime_scene", jacket_location="on_body"),
    ),
    5: (
        _state(5, wardrobe="no_jacket", injury="right_hand_fresh_bandage",
               position="office_desk", folder_holder="none", folder_location="desk_open",
               story_time="night", weather="rain", environment="office_wet_windows",
               jacket_location="chair"),
        _state(5, wardrobe="no_jacket", injury="right_hand_fresh_bandage",
               position="office_desk", folder_holder="none", folder_location="desk_closed",
               story_time="night", weather="rain", environment="office_wet_windows",
               jacket_location="chair"),
    ),
}


def _master(scene: int) -> str:
    return f"""\
# Director Master S{scene}
## 1. 场景层设计
场景 {scene}：{_EVENTS[scene]}
### 1.1 戏剧变化与信息策略
本场视觉策略来自全片 Visual Bible 和对应剧本事实。
## 2. 逐镜 Shot Contract
进入边界：[D] 场景 {scene} 的绝对入场状态。
交出边界：[D] 场景 {scene} 的绝对结束状态。
"""


def _manifest(scene: int, master_hash: str, source_start: int, source_end: int) -> dict:
    opening, closing = _SCENE_STATES[scene]
    return {
        "manifest_version": "1.1", "scene_id": f"S{scene}",
        "master_version": f"S{scene}/v1.0", "master_content_hash": master_hash,
        "compiler_version": "1.4.0",
        "shots": [{
            "shot_id": f"S{scene}-1", "duration": 8,
            "scene_expression": "investigation_object",
            "timing_mode": "event_nodes",
            "story_fact_ref": {
                "text_start": _EVENTS[scene][:80], "source_scene_id": f"S{scene}",
                "source_line_start": source_start, "source_line_end": source_end,
            },
            "opening_state_keys": opening, "closing_state_keys": closing,
            "entry_boundary_id": "SCENE_ENTRY", "exit_boundary_id": "SCENE_EXIT",
            "transition_execution": "post_production",
            "boundary_continuity": "scene_exit", "generation_mode": "text_only",
            "reference_assets": [],
        }],
    }


def _delivered_session(scene: int, scene_range: tuple[int, int]) -> Path:
    session = _tmpdir() / f"scene_{scene}"
    working = session / "working"
    delivery = session / "delivery"
    working.mkdir(parents=True, exist_ok=True)
    delivery.mkdir(parents=True, exist_ok=True)
    master = _master(scene)
    master_hash = hashlib.sha256(master.encode("utf-8")).hexdigest()
    (session / "DIRECTOR_MASTER.md").write_text(master, encoding="utf-8")
    (session / "STATUS.md").write_text(
        "# MODE:P Session\n\n状态：已交付。\n", encoding="utf-8")
    (working / "SHOT_MANIFEST.json").write_text(
        json.dumps(_manifest(scene, master_hash, *scene_range),
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (delivery / "STORYBOARD.md").write_text(
        f"# Scene {scene} Storyboard\n", encoding="utf-8")
    (delivery / "VIDEO_PROMPT.md").write_text(
        f"# Scene {scene} Video Prompt\n", encoding="utf-8")
    return session


class MultiSceneRegressionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.script_path = _tmpdir() / "continuity_regression.md"
        cls.script_path.write_text(_SCRIPT, encoding="utf-8")
        cls.digest = ingest_script(cls.script_path)
        cls.digest_data = asdict(cls.digest)
        cls.digest_path = _tmpdir() / "SCRIPT_STRUCTURE.json"
        cls.digest_path.write_text(
            json.dumps(cls.digest_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

        source_lines = _SCRIPT.splitlines()
        cls.facts_path = _tmpdir() / "SCRIPT_FACTS.md"
        cls.facts_path.write_text(
            _facts_text(cls.digest_data, source_lines), encoding="utf-8")

        cls.bible_path = _tmpdir() / "EPISODE_VISUAL_BIBLE.md"
        cls.ledger_path = _tmpdir() / "EPISODE_CONTINUITY_LEDGER.md"
        cls.bible_path.write_text(_complete_skeleton(
            generate_visual_bible(cls.digest_path, cls.facts_path)), encoding="utf-8")
        cls.ledger_path.write_text(_complete_skeleton(
            generate_continuity_ledger(cls.digest_path, cls.facts_path)), encoding="utf-8")

        cls.batch_manifest = schedule_batches(
            cls.digest_path, max_scenes_per_batch=3)
        cls.batch_path = _tmpdir() / "BATCH_MANIFEST.json"
        cls.batch_path.write_text(
            json.dumps(cls.batch_manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

        cls.sessions = {
            scene.index: _delivered_session(
                scene.index, (scene.start_line, scene.end_line))
            for scene in cls.digest.scenes
        }
        cls.commit_1 = _tmpdir() / "LEDGER_COMMIT_BATCH_1.json"
        commit_batch_state(
            1, cls.batch_path, cls.ledger_path,
            {index: cls.sessions[index] for index in (1, 2, 3)}, cls.commit_1)
        generate_ledger_snapshot(
            2, cls.batch_path, cls.ledger_path,
            cls.sessions[4] / "LEDGER_SNAPSHOT.md", cls.commit_1)
        cls.bridge_report = validate_handoff(
            2, cls.batch_path, cls.commit_1, cls.sessions[4], "elliptical")
        cls.commit_2 = _tmpdir() / "LEDGER_COMMIT_BATCH_2.json"
        commit_batch_state(
            2, cls.batch_path, cls.ledger_path,
            {index: cls.sessions[index] for index in (4, 5)}, cls.commit_2)

        cls.review_dir = _tmpdir() / "episode_review"
        prepare_review(
            cls.batch_path, cls.bible_path, cls.ledger_path,
            cls.sessions, cls.review_dir)
        result = _tmpdir() / "EPISODE_REVIEW_RESULT_SOURCE.md"
        result.write_text(
            "EPISODE REVIEW: PASS\n"
            "服装、伤势、道具、时间、空间和场间转场已按 Ledger 与各场 Master 回看。\n",
            encoding="utf-8")
        submit_review(cls.review_dir, result)

    def test_scene_order_locations_and_time_are_preserved(self) -> None:
        self.assertEqual(self.digest.scene_count, 5)
        self.assertEqual([scene.scene_number for scene in self.digest.scenes],
                         [1, 2, 3, 4, 5])
        self.assertEqual([scene.time_hint for scene in self.digest.scenes],
                         ["day", "night", "morning", "dusk", "night"])
        self.assertEqual(
            [scene.location_hint for scene in self.digest.scenes].count("Office"), 3)

    def test_director_facts_are_source_bound_and_complete(self) -> None:
        report = validate_facts(self.facts_path, self.digest_path)
        self.assertTrue(report.ok, report.issues)
        text = self.facts_path.read_text(encoding="utf-8")
        for term in ("grey jacket", "bandage", "folder", "rain"):
            self.assertIn(term, text)

    def test_episode_documents_share_the_same_fact_source(self) -> None:
        report = check_episode_docs(
            self.digest_path, self.facts_path, self.bible_path, self.ledger_path)
        self.assertTrue(report.ok, report.issues)

    def test_long_episode_is_split_without_losing_full_episode_context(self) -> None:
        self.assertEqual(self.batch_manifest.total_batches, 2)
        self.assertEqual(self.batch_manifest.batches[0].scene_indices, [1, 2, 3])
        self.assertEqual(self.batch_manifest.batches[1].scene_indices, [4, 5])
        self.assertIn("SCRIPT_FACTS.md", self.batch_manifest.shared_documents)
        self.assertIn("EPISODE_CONTINUITY_LEDGER.md",
                      self.batch_manifest.shared_documents)

    def test_first_commit_carries_wardrobe_injury_prop_and_time(self) -> None:
        commit = json.loads(self.commit_1.read_text(encoding="utf-8"))
        outgoing = commit["outgoing_state"]
        li = outgoing["characters"][0]
        self.assertEqual(li["wardrobe"], "no_jacket")
        self.assertEqual(li["injury"], "right_hand_bandage")
        props = {prop["prop_id"]: prop for prop in outgoing["props"]}
        self.assertEqual(props["jacket"]["location"], "coat_rack")
        self.assertEqual(outgoing["story_time"], "morning")

    def test_second_batch_reads_exact_prior_commit_before_elliptical_change(self) -> None:
        self.assertTrue(self.bridge_report.ok, self.bridge_report.handoffs[0].detail)
        self.assertIn("fresh DP semantic review", self.bridge_report.handoffs[0].detail)
        snapshot = (self.sessions[4] / "LEDGER_SNAPSHOT.md").read_text(
            encoding="utf-8")
        for marker in (
            "wardrobe=no_jacket", "injury=right_hand_bandage",
            "jacket", "Story time: morning",
        ):
            self.assertIn(marker, snapshot)

    def test_final_commit_contains_resulting_rain_and_fresh_bandage(self) -> None:
        commit = json.loads(self.commit_2.read_text(encoding="utf-8"))
        outgoing = commit["outgoing_state"]
        self.assertEqual(outgoing["characters"][0]["injury"],
                         "right_hand_fresh_bandage")
        self.assertEqual(outgoing["weather"], "rain")
        self.assertEqual(outgoing["environment"], "office_wet_windows")
        folder = next(prop for prop in outgoing["props"]
                      if prop["prop_id"] == "folder")
        self.assertEqual(folder["location"], "desk_closed")

    def test_episode_review_pass_is_current_for_all_five_deliveries(self) -> None:
        ok, detail = review_gate(self.review_dir)
        self.assertTrue(ok, detail)
        packet = json.loads(
            (self.review_dir / "EPISODE_REVIEW_PACKET.json").read_text(
                encoding="utf-8"))
        self.assertEqual([scene["scene_index"] for scene in packet["scenes"]],
                         [1, 2, 3, 4, 5])

    def test_user_entry_defaults_to_all_scenes_and_stops_for_facts(self) -> None:
        session = _tmpdir() / "pilot_bootstrap"
        result = subprocess.run(
            [sys.executable, "-m", "mode_p_pilot", str(self.script_path),
             "--session-dir", str(session)],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        status = json.loads((session / "PILOT_PREP_STATUS.json").read_text(
            encoding="utf-8"))
        self.assertEqual(status["active_scenes"], [1, 2, 3, 4, 5])
        self.assertEqual(status["stage"], "awaiting_script_facts")


if __name__ == "__main__":
    unittest.main()
