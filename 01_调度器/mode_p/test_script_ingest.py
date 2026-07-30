"""Tests for script_ingest.py — scene boundary parser."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from script_ingest import IngestError, ingest_script


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_ingest_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


def _write(name: str, content: str) -> Path:
    p = _tmpdir() / name
    p.write_text(content, encoding="utf-8")
    return p


# --- Test fixtures ---

_MARKDOWN_EN = """\
# Pilot Script

Character list: A, B

## Scene 1 — Office — Day

A sits at the desk. B enters from the door.

B: The report is ready.

A nods.

## Scene 2

A and B walk down the corridor.

## Scene 3 — Rooftop — Night

A looks at the city skyline.
"""

_MARKDOWN_CN = """\
# 剧本

## 第一场 — 客厅 — 日

父亲坐在沙发上。母亲从厨房出来。

## 第二场 — 厨房 — 夜

两人开始争吵。
"""

_SCREENPLAY = """\
TITLE: THE CASE

INT. POLICE HQ - DAY

Detective surveys the room.

INT. APARTMENT - NIGHT

A body is discovered.

EXT. ROOFTOP - DUSK

The detective makes a call.
"""

_CN_BRACKET = """\
剧本正文

【场景1：办公室】

张三坐在桌前。

【场景2：街道】

张三走出大楼。
"""

_CN_PLAIN = """\
场景 1

人物 A 走进房间。

场景 2

人物 B 跟随其后。
"""

_NO_SCENES = """\
This is just prose text without any scene markers.

It continues for a while but never defines scenes.
"""

_GBK_ENCODED = """\
## Scene 1 — 测试 — 日

Test content.
"""


class SceneDetectionTests(unittest.TestCase):

    def test_markdown_en_detects_scenes(self) -> None:
        p = _write("md_en.md", _MARKDOWN_EN)
        digest = ingest_script(p)
        self.assertEqual(digest.scene_count, 3)
        self.assertEqual(digest.encoding, "utf-8")
        self.assertEqual(digest.scenes[0].header_kind, "markdown_scene_en")
        self.assertEqual(digest.scenes[0].scene_number, 1)
        self.assertEqual(digest.scenes[0].location_hint, "Office")
        self.assertEqual(digest.scenes[0].time_hint, "day")

    def test_markdown_cn_detects_scenes(self) -> None:
        p = _write("md_cn.md", _MARKDOWN_CN)
        digest = ingest_script(p)
        self.assertEqual(digest.scene_count, 2)
        self.assertEqual(digest.scenes[0].header_kind, "markdown_cn_numbered")
        self.assertEqual(digest.scenes[0].scene_number, 1)
        self.assertEqual(digest.scenes[0].location_hint, "客厅")
        self.assertEqual(digest.scenes[0].time_hint, "day")

    def test_screenplay_detects_scenes(self) -> None:
        p = _write("screenplay.md", _SCREENPLAY)
        digest = ingest_script(p)
        self.assertEqual(digest.scene_count, 3)
        self.assertEqual(digest.scenes[0].header_kind, "screenplay_header")
        self.assertEqual(digest.scenes[2].time_hint, "dusk")

    def test_cn_bracket_detects_scenes(self) -> None:
        p = _write("cn_bracket.md", _CN_BRACKET)
        digest = ingest_script(p)
        self.assertEqual(digest.scene_count, 2)
        self.assertEqual(digest.scenes[0].header_kind, "cn_bracket")

    def test_cn_plain_detects_scenes(self) -> None:
        p = _write("cn_plain.md", _CN_PLAIN)
        digest = ingest_script(p)
        self.assertEqual(digest.scene_count, 2)
        self.assertEqual(digest.scenes[0].header_kind, "cn_plain")
        self.assertEqual(digest.scenes[0].scene_number, 1)

    def test_line_ranges_are_sequential(self) -> None:
        p = _write("seq.md", _MARKDOWN_EN)
        digest = ingest_script(p)
        for i in range(len(digest.scenes) - 1):
            self.assertLess(digest.scenes[i].end_line, digest.scenes[i + 1].start_line)
        last = digest.scenes[-1]
        self.assertLessEqual(last.end_line, digest.total_lines)

    def test_no_scenes_returns_unresolved(self) -> None:
        p = _write("no_scenes.md", _NO_SCENES)
        digest = ingest_script(p)
        self.assertEqual(digest.scene_count, 1)
        self.assertEqual(digest.scenes[0].start_line, 1)
        self.assertEqual(digest.scenes[0].end_line, digest.total_lines)
        self.assertEqual(digest.scenes[0].status, "unresolved")
        self.assertEqual(digest.scenes[0].unresolved_reason, "implicit_scene_boundary")

    def test_empty_scene_header_is_not_registered(self) -> None:
        p = _write(
            "empty_scene.md",
            "## Scene 1\n\n## Scene 2\n\nActual scene content.\n",
        )
        digest = ingest_script(p)
        self.assertEqual(digest.scene_count, 1)
        self.assertEqual(digest.scenes[0].index, 1)
        self.assertEqual(digest.scenes[0].scene_number, 2)

    def test_empty_script_raises(self) -> None:
        p = _write("empty.md", " \n\t\n")
        with self.assertRaises(IngestError):
            ingest_script(p)

    def test_missing_file_is_wrapped_as_ingest_error(self) -> None:
        with self.assertRaises(IngestError):
            ingest_script(_tmpdir() / "does_not_exist.md")

    def test_source_hash_is_stable_and_content_sensitive(self) -> None:
        p = _write("hash.md", _MARKDOWN_EN)
        first = ingest_script(p).source_content_hash
        self.assertEqual(len(first), 64)
        self.assertEqual(first, ingest_script(p).source_content_hash)
        p.write_text(_MARKDOWN_EN + "\nChanged.\n", encoding="utf-8")
        self.assertNotEqual(first, ingest_script(p).source_content_hash)

    def test_front_matter_detected(self) -> None:
        p = _write("front.md", _MARKDOWN_EN)
        digest = ingest_script(p)
        self.assertIsNotNone(digest.front_matter_lines)
        self.assertEqual(digest.front_matter_lines[0], 1)

    def test_gbk_fallback(self) -> None:
        content = "## Scene 1 — 测试 — 日\n\n内容。\n"
        p = _tmpdir() / "gbk.md"
        p.write_bytes(content.encode("gbk"))
        digest = ingest_script(p)
        self.assertEqual(digest.encoding, "gbk")
        self.assertEqual(digest.scene_count, 1)


class MetadataTests(unittest.TestCase):

    def test_scene_number_extraction_en(self) -> None:
        p = _write("meta_en.md", "## Scene 12 — Hallway\n\nContent.\n")
        digest = ingest_script(p)
        self.assertEqual(digest.scenes[0].scene_number, 12)

    def test_scene_number_extraction_cn_digits(self) -> None:
        p = _write("meta_cn1.md", "## 第3场 办公室\n\n正文。\n")
        digest = ingest_script(p)
        self.assertEqual(digest.scenes[0].scene_number, 3)

    def test_scene_number_extraction_cn_hanzi(self) -> None:
        p = _write("meta_cn2.md", "## 第十四场 街道\n\n正文。\n")
        digest = ingest_script(p)
        self.assertEqual(digest.scenes[0].scene_number, 14)

    def test_screenplay_location_extraction(self) -> None:
        p = _write("meta_loc.md", "INT. POLICE HQ - DAY\n\nContent.")
        digest = ingest_script(p)
        self.assertEqual(digest.scenes[0].location_hint, "POLICE HQ")
        self.assertEqual(digest.scenes[0].time_hint, "day")

    def test_time_hint_variants(self) -> None:
        cases = [
            ("INT. A - 日", "day"),
            ("INT. B - 夜", "night"),
            ("INT. C - 晨", "morning"),
            ("INT. D - 黄昏", "dusk"),
        ]
        for header, expected in cases:
            p = _write("time_test.md", f"{header}\n\nContent.\n")
            digest = ingest_script(p)
            self.assertEqual(digest.scenes[0].time_hint, expected,
                             f"Failed for {header!r}")


class CLITests(unittest.TestCase):

    def test_cli_json_output(self) -> None:
        import subprocess
        import sys
        p = _write("cli_md.md", _MARKDOWN_EN)
        result = subprocess.run(
            [sys.executable, "-m", "script_ingest", str(p), "--json"],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(len(data["scenes"]), 3)
        self.assertEqual(data["scene_count"], 3)
        self.assertEqual(len(data["source_content_hash"]), 64)

    def test_cli_no_scenes_still_exits_zero(self) -> None:
        """No-scenes input now returns 0 with one unresolved scene (L0.2 contract: mark, don't error)."""
        import subprocess
        import sys
        p = _write("cli_bad.md", _NO_SCENES)
        result = subprocess.run(
            [sys.executable, "-m", "script_ingest", str(p)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("UNRESOLVED", result.stdout)

    def test_cli_human_readable_output(self) -> None:
        import subprocess
        import sys
        p = _write("cli_human.md", _MARKDOWN_EN)
        result = subprocess.run(
            [sys.executable, "-m", "script_ingest", str(p)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Scenes: 3", result.stdout)

    def test_cli_missing_file_exits_nonzero_without_traceback(self) -> None:
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "script_ingest",
             str(_tmpdir() / "missing_cli.md")],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Ingest error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
