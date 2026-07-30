"""Tests for trusted Visual Bible and Continuity Ledger skeleton generation."""

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

from episode_templates import (
    EpisodeTemplateError,
    generate_continuity_ledger,
    generate_visual_bible,
)
from episode_docs_check import check_episode_docs
from script_ingest import ingest_script


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_episode_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


_SCRIPT = """\
## Scene 1 — Office — Day

A enters. B looks up.

B: Report ready.

## Scene 2 — Hallway — Night

A walks quickly. B follows.

## Scene 3 — Rooftop — Dusk

A looks at the skyline.
"""


def _facts_text(data: dict) -> str:
    return f"""\
# SCRIPT_FACTS — episode.md
<!-- contract: script_input v1.1 -->
<!-- source_sha256: {data['source_content_hash']} -->

## 场景 1 事实
### 事件
- [L3-L3] A enters and B looks up.
### 对白
- [L5-L5] B: Report ready.
### 连续性入口
- (无)

## 场景 2 事实
### 事件
- [L9-L9] A and B walk through the hallway.
### 对白
- (无)
### 连续性入口
- [L9-L9] A and B are in the hallway.

## 场景 3 事实
### 事件
- [L13-L13] A looks at the skyline.
### 对白
- (无)
### 连续性入口
- [L13-L13] A is on the rooftop.
"""


def _make_inputs(prefix: str = "episode") -> tuple[Path, Path, Path, dict]:
    script_path = _tmpdir() / f"{prefix}.md"
    script_path.write_text(_SCRIPT, encoding="utf-8")
    data = asdict(ingest_script(script_path))
    digest_path = _tmpdir() / f"{prefix}.json"
    digest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    facts_path = _tmpdir() / f"{prefix}_facts.md"
    facts_path.write_text(_facts_text(data), encoding="utf-8")
    return script_path, digest_path, facts_path, data


def _complete_skeleton(text: str) -> str:
    text = re.sub(r"\[Director:.*?\]", "已完成", text, flags=re.DOTALL)
    return text.replace("<Name>", "A").replace("<N>", "1")


class VisualBibleTests(unittest.TestCase):

    def test_generates_source_bound_skeleton(self) -> None:
        _script, digest_path, facts_path, data = _make_inputs("bible")
        output_path = _tmpdir() / "bible.md"
        text = generate_visual_bible(digest_path, facts_path, output_path)
        facts_hash = hashlib.sha256(facts_path.read_bytes()).hexdigest()
        self.assertTrue(output_path.exists())
        self.assertIn("EPISODE_VISUAL_BIBLE", text)
        self.assertIn(f"source_sha256: {data['source_content_hash']}", text)
        self.assertIn(f"script_facts_sha256: {facts_hash}", text)
        for location in ("Office", "Hallway", "Rooftop"):
            self.assertIn(location, text)

    def test_returns_text_without_output_path(self) -> None:
        _script, digest_path, facts_path, _data = _make_inputs("bible_text")
        text = generate_visual_bible(digest_path, facts_path)
        self.assertIn("EPISODE_VISUAL_BIBLE", text)

    def test_skeleton_does_not_supply_a_default_shot_solution(self) -> None:
        _script, digest_path, facts_path, _data = _make_inputs("bible_neutral")
        text = generate_visual_bible(digest_path, facts_path)
        self.assertNotIn("双人中景逐渐变为单人特写", text)
        self.assertIn("模板不提供默认镜头答案", text)


class ContinuityLedgerTests(unittest.TestCase):

    def test_generates_all_scene_handoffs(self) -> None:
        _script, digest_path, facts_path, _data = _make_inputs("ledger")
        output_path = _tmpdir() / "ledger.md"
        text = generate_continuity_ledger(digest_path, facts_path, output_path)
        self.assertTrue(output_path.exists())
        self.assertIn("EPISODE_CONTINUITY_LEDGER", text)
        self.assertIn("场景 1 → 场景 2", text)
        self.assertIn("场景 2 → 场景 3", text)
        self.assertIn("场景 3 → 结束", text)

    def test_rejects_unfilled_script_facts(self) -> None:
        _script, digest_path, facts_path, _data = _make_inputs("unfilled")
        facts_path.write_text("# SCRIPT_FACTS\n[Director: fill me]\n", encoding="utf-8")
        with self.assertRaises(EpisodeTemplateError):
            generate_continuity_ledger(digest_path, facts_path)

    def test_rejects_inconsistent_digest(self) -> None:
        _script, digest_path, facts_path, data = _make_inputs("bad_digest")
        data["scene_count"] = 99
        digest_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(EpisodeTemplateError):
            generate_visual_bible(digest_path, facts_path)

    def test_rejects_stale_facts_after_script_change(self) -> None:
        script_path, digest_path, facts_path, _data = _make_inputs("stale")
        script_path.write_text(_SCRIPT + "\nChanged.\n", encoding="utf-8")
        with self.assertRaises(EpisodeTemplateError):
            generate_continuity_ledger(digest_path, facts_path)


class CLITests(unittest.TestCase):

    def test_cli_all_writes_both_documents(self) -> None:
        _script, digest_path, facts_path, _data = _make_inputs("cli_all")
        output_dir = _tmpdir() / "cli_output"
        result = subprocess.run(
            [sys.executable, "-m", "episode_templates", "all",
             str(digest_path), str(facts_path), "-d", str(output_dir)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((output_dir / "EPISODE_VISUAL_BIBLE.md").exists())
        self.assertTrue((output_dir / "EPISODE_CONTINUITY_LEDGER.md").exists())

    def test_cli_bad_facts_fails_without_traceback(self) -> None:
        _script, digest_path, facts_path, _data = _make_inputs("cli_bad")
        facts_path.write_text("# empty facts\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "episode_templates", "bible",
             str(digest_path), str(facts_path)],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Episode template error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class EpisodeDocsCheckTests(unittest.TestCase):

    def _completed_files(self, prefix: str) -> tuple[Path, Path, Path, Path]:
        _script, digest_path, facts_path, _data = _make_inputs(prefix)
        bible_path = _tmpdir() / f"{prefix}_bible.md"
        ledger_path = _tmpdir() / f"{prefix}_ledger.md"
        bible_path.write_text(_complete_skeleton(
            generate_visual_bible(digest_path, facts_path)), encoding="utf-8")
        ledger_path.write_text(_complete_skeleton(
            generate_continuity_ledger(digest_path, facts_path)), encoding="utf-8")
        return digest_path, facts_path, bible_path, ledger_path

    def test_completed_documents_pass_structural_check(self) -> None:
        paths = self._completed_files("docs_valid")
        report = check_episode_docs(*paths)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_unfilled_skeleton_is_rejected(self) -> None:
        _script, digest_path, facts_path, _data = _make_inputs("docs_unfilled")
        bible_path = _tmpdir() / "docs_unfilled_bible.md"
        ledger_path = _tmpdir() / "docs_unfilled_ledger.md"
        generate_visual_bible(digest_path, facts_path, bible_path)
        generate_continuity_ledger(digest_path, facts_path, ledger_path)
        report = check_episode_docs(
            digest_path, facts_path, bible_path, ledger_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("placeholder" in issue.detail for issue in report.issues))

    def test_missing_scene_handoff_is_rejected(self) -> None:
        digest_path, facts_path, bible_path, ledger_path = self._completed_files(
            "docs_handoff")
        text = ledger_path.read_text(encoding="utf-8").replace(
            "场景 2 → 场景 3", "场景 2 接下一场")
        ledger_path.write_text(text, encoding="utf-8")
        report = check_episode_docs(
            digest_path, facts_path, bible_path, ledger_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("Required handoff" in issue.detail
                            for issue in report.issues))

    def test_facts_change_invalidates_both_documents(self) -> None:
        digest_path, facts_path, bible_path, ledger_path = self._completed_files(
            "docs_stale")
        facts_path.write_text(
            facts_path.read_text(encoding="utf-8") + "\n<!-- editorial note -->\n",
            encoding="utf-8")
        report = check_episode_docs(
            digest_path, facts_path, bible_path, ledger_path)
        self.assertFalse(report.ok)
        stale = [issue for issue in report.issues if "FACTS hash" in issue.detail]
        self.assertEqual(len(stale), 2)

    def test_cli_returns_nonzero_for_unfilled_documents(self) -> None:
        _script, digest_path, facts_path, _data = _make_inputs("docs_cli")
        bible_path = _tmpdir() / "docs_cli_bible.md"
        ledger_path = _tmpdir() / "docs_cli_ledger.md"
        generate_visual_bible(digest_path, facts_path, bible_path)
        generate_continuity_ledger(digest_path, facts_path, ledger_path)
        result = subprocess.run(
            [sys.executable, "-m", "episode_docs_check", str(digest_path),
             str(facts_path), str(bible_path), str(ledger_path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("placeholder", result.stdout)


if __name__ == "__main__":
    unittest.main()
