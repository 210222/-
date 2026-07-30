"""Tests for implicit project background and independent episode binding."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from project_context import (
    ProjectContextError,
    build_background_packet,
    infer_episode_id,
    load_active_project,
    register_background,
    resolve_episode,
)


SCRIPT = """# Complete story
## Scene 1 - Room - Day
Rico waits.
## Scene 2 - Street - Night
Isabela leaves.
"""


class ProjectContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mode_p_project_")
        self.root = Path(self.temp.name)
        self.active = self.root / "MODE_P_PROJECT.json"
        self.projects = self.root / "projects"
        self.background = self.root / "complete.md"
        self.background.write_text(SCRIPT, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _register(self) -> dict:
        return register_background(
            self.background,
            active_manifest_path=self.active,
            projects_root=self.projects,
        )

    def test_register_is_deterministic_and_creates_project_memory(self) -> None:
        first = self._register()
        second = self._register()
        self.assertEqual(first["project_id"], second["project_id"])
        project = Path(first["project_dir"])
        for name in (
            "PROJECT_SOURCE_INDEX.json",
            "PROJECT_VISUAL_BIBLE.md",
            "PROJECT_CONTINUITY_LEDGER.md",
            "ASSET_REQUIREMENTS.md",
        ):
            self.assertTrue((project / name).is_file())
        self.assertEqual(load_active_project(self.active)["project_id"], first["project_id"])

    def test_independent_episode_does_not_need_to_be_background_substring(self) -> None:
        project = self._register()
        episode = self.root / "EP07_rewrite.md"
        episode.write_text("# EP07\n## Scene 1\nA completely rewritten event.\n", encoding="utf-8")
        binding = resolve_episode(episode, active_manifest_path=self.active)
        self.assertEqual(binding["mode"], "project")
        self.assertEqual(binding["project_id"], project["project_id"])
        self.assertEqual(binding["episode_id"], "EP07")

    def test_episode_content_change_creates_a_new_version_directory(self) -> None:
        self._register()
        episode = self.root / "EP02.md"
        episode.write_text("# EP02\nFirst version.\n", encoding="utf-8")
        first = resolve_episode(episode, active_manifest_path=self.active)
        episode.write_text("# EP02\nSecond version.\n", encoding="utf-8")
        second = resolve_episode(episode, active_manifest_path=self.active)
        self.assertEqual(first["episode_id"], second["episode_id"])
        self.assertNotEqual(first["session_dir"], second["session_dir"])

    def test_no_project_runs_standalone(self) -> None:
        episode = self.root / "pilot.md"
        episode.write_text("## Scene 1\nStandalone.\n", encoding="utf-8")
        binding = resolve_episode(
            episode,
            active_manifest_path=self.active,
            standalone_root=self.root / "sessions",
        )
        self.assertEqual(binding["mode"], "standalone")
        self.assertEqual(binding["project_id"], "")

    def test_replacing_another_background_requires_explicit_intent(self) -> None:
        self._register()
        another = self.root / "another.md"
        another.write_text("## Scene 1\nAnother project.\n", encoding="utf-8")
        with self.assertRaisesRegex(ProjectContextError, "explicit replacement"):
            register_background(
                another,
                active_manifest_path=self.active,
                projects_root=self.projects,
            )
        replaced = register_background(
            another,
            active_manifest_path=self.active,
            projects_root=self.projects,
            replace=True,
        )
        self.assertEqual(Path(replaced["background_script"]["path"]), another.resolve())

    def test_stale_background_is_rejected(self) -> None:
        self._register()
        self.background.write_text(SCRIPT + "changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ProjectContextError, "background changed"):
            load_active_project(self.active)

    def test_episode_id_falls_back_to_filename(self) -> None:
        episode = self.root / "先导篇_修订版.md"
        episode.write_text("## Scene 1\nNo episode number.\n", encoding="utf-8")
        inferred = infer_episode_id(episode)
        self.assertTrue(inferred.startswith("episode_"))

    def test_background_packet_selects_relevant_exact_excerpts_without_hashes(self) -> None:
        self._register()
        episode = self.root / "EP03.md"
        episode.write_text(
            "# EP03\n## Scene 1\nRico returns to the room.\n",
            encoding="utf-8",
        )
        output = self.root / "PROJECT_BACKGROUND_PACKET.md"
        text = build_background_packet(
            episode,
            output,
            active_manifest_path=self.active,
            max_chars=2000,
        )
        self.assertIn("Rico waits", text)
        self.assertIn("current episode script is authoritative", text)
        self.assertNotIn("SHA-256", text)
        self.assertLessEqual(len(text), 2000)

    def test_background_packet_can_be_empty_for_independent_episode(self) -> None:
        self._register()
        episode = self.root / "EP08.md"
        episode.write_text(
            "# EP08\n## Scene 1\nUnrelated lunar observatory event.\n",
            encoding="utf-8",
        )
        text = build_background_packet(
            episode,
            self.root / "empty_packet.md",
            active_manifest_path=self.active,
        )
        self.assertIn("No relevant project-background excerpt", text)


if __name__ == "__main__":
    unittest.main()
