"""Tests for mode_p_pilot.py — full-script orchestrator."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from mode_p_pilot import parse_scene_range, run_pilot


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_pilot_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


_MINI_SCRIPT = """\
## Scene 1 — Office — Day

A enters. B looks up.

B: Report ready.

A nods.

## Scene 2 — Hallway — Night

A walks. B follows.

B: Wait.

## Scene 3 — Rooftop — Dusk

A looks at the skyline. B appears.

B: It's done.

A turns and faces B.

## Scene 4 — Office — Morning

A sits alone. The phone rings.
"""


def _valid_facts(source_hash: str) -> str:
    sections = [
        (1, 3, "A enters and B looks up.", 5, "B: Report ready."),
        (2, 11, "A walks and B follows.", 13, "B: Wait."),
        (3, 17, "A sees the skyline and B appears.", 19, "B: It's done."),
        (4, 25, "A sits alone and the phone rings.", None, None),
    ]
    lines = [
        "# SCRIPT_FACTS — pilot.md",
        "<!-- contract: script_input v1.1 -->",
        f"<!-- source_sha256: {source_hash} -->",
        "",
    ]
    for scene, event_line, event, dialogue_line, dialogue in sections:
        lines.extend([
            f"## 场景 {scene} 事实",
            "### 事件",
            f"- [L{event_line}-L{event_line}] {event}",
            "### 对白",
            (f"- [L{dialogue_line}-L{dialogue_line}] {dialogue}"
             if dialogue_line else "- (无)"),
            "### 连续性入口",
            "- (无)" if scene == 1 else
            f"- [L{event_line}-L{event_line}] 场景进入状态。",
            "",
        ])
    return "\n".join(lines)


def _complete_episode_doc(text: str) -> str:
    text = re.sub(r"\[Director:.*?\]", "已完成", text, flags=re.DOTALL)
    return text.replace("<Name>", "A").replace("<N>", "1")


class SceneRangeParsingTests(unittest.TestCase):

    def test_single_scene(self) -> None:
        self.assertEqual(parse_scene_range("2", 4), [2])

    def test_range(self) -> None:
        self.assertEqual(parse_scene_range("1-3", 4), [1, 2, 3])

    def test_comma_list(self) -> None:
        self.assertEqual(parse_scene_range("1,3", 4), [1, 3])

    def test_out_of_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_scene_range("5", 4)

    def test_reversed_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_scene_range("3-1", 4)


class PilotOrchestratorTests(unittest.TestCase):

    def test_full_pilot_all_scenes(self) -> None:
        p = _tmpdir() / "script.md"
        p.write_text(_MINI_SCRIPT, encoding="utf-8")
        session = _tmpdir() / "out"
        ret = run_pilot(p, scenes=None, session_dir=session)
        self.assertEqual(ret, 0)
        self.assertTrue((session / "SCRIPT_STRUCTURE.json").exists())
        self.assertTrue((session / "SCRIPT_FACTS.md").exists())
        self.assertTrue((session / "BATCH_MANIFEST.json").exists())
        status = json.loads((session / "PILOT_PREP_STATUS.json").read_text(
            encoding="utf-8"))
        self.assertEqual(status["stage"], "awaiting_script_facts")

    def test_pilot_with_scene_range(self) -> None:
        p = _tmpdir() / "script2.md"
        p.write_text(_MINI_SCRIPT, encoding="utf-8")
        session = _tmpdir() / "out2"
        ret = run_pilot(p, scenes=[1, 2], session_dir=session)
        self.assertEqual(ret, 0)
        self.assertTrue((session / "SCRIPT_STRUCTURE.json").exists())
        # Verify active_scenes recorded correctly
        digest = json.loads((session / "SCRIPT_STRUCTURE.json").read_text(encoding="utf-8"))
        self.assertEqual(digest["active_scenes"], [1, 2])
        manifest = json.loads((session / "BATCH_MANIFEST.json").read_text(
            encoding="utf-8"))
        self.assertEqual(manifest["selected_scenes"], [1, 2])
        self.assertEqual(manifest["batches"][0]["scene_indices"], [1, 2])

    def test_pilot_prose_without_scenes_marks_unresolved(self) -> None:
        p = _tmpdir() / "bad.md"
        p.write_text("Just prose, no scene markers at all.", encoding="utf-8")
        session = _tmpdir() / "out_bad"
        ret = run_pilot(p, session_dir=session)
        self.assertEqual(ret, 0)  # returns 0 but marks scenes as unresolved
        digest = json.loads((session / "SCRIPT_STRUCTURE.json").read_text(encoding="utf-8"))
        self.assertEqual(digest["scenes"][0]["status"], "unresolved")
        status = json.loads((session / "PILOT_PREP_STATUS.json").read_text(
            encoding="utf-8"))
        self.assertEqual(status["stage"], "awaiting_scene_boundary_resolution")

    def test_rerun_preserves_director_facts_and_advances_in_stages(self) -> None:
        script = _tmpdir() / "resume.md"
        script.write_text(_MINI_SCRIPT, encoding="utf-8")
        session = _tmpdir() / "resume_out"
        self.assertEqual(run_pilot(script, session_dir=session), 0)

        structure = json.loads((session / "SCRIPT_STRUCTURE.json").read_text(
            encoding="utf-8"))
        authored_facts = _valid_facts(structure["source_content_hash"])
        facts_path = session / "SCRIPT_FACTS.md"
        facts_path.write_text(authored_facts, encoding="utf-8")

        self.assertEqual(run_pilot(script, session_dir=session), 0)
        self.assertEqual(facts_path.read_text(encoding="utf-8"), authored_facts)
        status = json.loads((session / "PILOT_PREP_STATUS.json").read_text(
            encoding="utf-8"))
        self.assertEqual(status["stage"], "awaiting_episode_documents")

        for name in ("EPISODE_VISUAL_BIBLE.md", "EPISODE_CONTINUITY_LEDGER.md"):
            path = session / name
            path.write_text(_complete_episode_doc(path.read_text(encoding="utf-8")),
                            encoding="utf-8")
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        self.assertEqual(facts_path.read_text(encoding="utf-8"), authored_facts)
        status = json.loads((session / "PILOT_PREP_STATUS.json").read_text(
            encoding="utf-8"))
        self.assertEqual(status["stage"], "ready_for_scene_design")
        scene_map = json.loads((session / "SCENE_SESSIONS.json").read_text(
            encoding="utf-8"))
        self.assertEqual(
            [item["scene_index"] for item in scene_map["scenes"]], [1, 2, 3, 4]
        )
        for item in scene_map["scenes"]:
            scene_session = Path(item["session_path"])
            self.assertTrue((scene_session / "SCENE_CONTEXT.md").is_file())
            self.assertTrue((scene_session / "RUN_STATE.json").is_file())
            context_text = (scene_session / "SCENE_CONTEXT.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("source_sha256", context_text)
            self.assertNotIn("SCRIPT_STRUCTURE.json", context_text)
            self.assertNotIn(" | `", context_text)
        root_state = json.loads((session / "RUN_STATE.json").read_text(
            encoding="utf-8"))
        self.assertEqual(root_state["stage"], "director_batch")
        self.assertEqual(root_state["active_scenes"], [1, 2, 3, 4])
        self.assertEqual(len(root_state["state_sha256"]), 64)

    def test_run_api_rejects_invalid_scene_selection(self) -> None:
        script = _tmpdir() / "invalid_selection.md"
        script.write_text(_MINI_SCRIPT, encoding="utf-8")
        self.assertNotEqual(
            run_pilot(script, scenes=[2, 1],
                      session_dir=_tmpdir() / "invalid_selection_out"),
            0)


class CLITests(unittest.TestCase):

    def test_cli_all_scenes(self) -> None:
        import subprocess
        import sys
        p = _tmpdir() / "cli_script.md"
        p.write_text(_MINI_SCRIPT, encoding="utf-8")
        session = _tmpdir() / "cli_out"
        result = subprocess.run(
            [sys.executable, "-m", "mode_p_pilot", str(p), "--session-dir", str(session)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn("Local preparation stage:", result.stdout)
        self.assertTrue((session / "SCRIPT_FACTS.md").exists())

    def test_cli_rejects_user_scene_range_in_v3(self) -> None:
        import subprocess
        import sys
        p = _tmpdir() / "cli_script2.md"
        p.write_text(_MINI_SCRIPT, encoding="utf-8")
        session = _tmpdir() / "cli_out2"
        result = subprocess.run(
            [sys.executable, "-m", "mode_p_pilot", str(p),
             "--scenes", "1-2", "--session-dir", str(session)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments: --scenes", result.stderr)
        self.assertFalse((session / "SCRIPT_STRUCTURE.json").exists())

    def test_cli_bad_range_fails(self) -> None:
        import subprocess
        import sys
        p = _tmpdir() / "cli_script3.md"
        p.write_text(_MINI_SCRIPT, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "mode_p_pilot", str(p), "--scenes", "99"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
