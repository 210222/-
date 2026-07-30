"""Tests for script_facts_tool.py provenance and completeness checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from script_facts_tool import FactsError, generate_facts, validate_facts
from script_ingest import ingest_script


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_facts_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


_SCRIPT = """\
## Scene 1 — Office — Day

A enters the room. B looks up from the desk.

B: The report is ready.

A nods and takes the folder.

## Scene 2 — Hallway — Night

A walks quickly. B follows.

B: Wait.

A stops but doesn't turn around.
"""


def _make_inputs(prefix: str = "case") -> tuple[Path, Path, dict]:
    script_path = _tmpdir() / f"{prefix}_script.md"
    script_path.write_text(_SCRIPT, encoding="utf-8")
    digest = ingest_script(script_path)
    data = asdict(digest)
    digest_path = _tmpdir() / f"{prefix}_digest.json"
    digest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return script_path, digest_path, data


def _valid_facts(data: dict) -> str:
    source_hash = data["source_content_hash"]
    return f"""\
# SCRIPT_FACTS — test.md

<!-- contract: script_input v1.1 -->
<!-- source_sha256: {source_hash} -->

## 源信息
- 文件：{data['file_path']}
- 编码：utf-8
- 总行数：{data['total_lines']}
- 场景数：2

## 场景清单
| # | 标题 | 行号 | 地点 | 时间 | 状态 |
|---|------|------|------|------|------|
| 1 | Scene 1 | L1-L8 | Office | day | resolved |
| 2 | Scene 2 | L9-L15 | Hallway | night | resolved |

## 角色清单
| 角色 | 首次出现行 | 确定度 | 说明 |
|------|-----------|--------|------|
| A | L3 | confirmed | |
| B | L3 | confirmed | |

## 场景 1 事实
_原文：Scene 1_  _行号：L1-L8_

### 事件
- [L3-L3] A enters and B looks up.
- [L7-L7] A takes the folder.

### 对白
- [L5-L5] B: The report is ready.

### 连续性入口
- (无)

### 未确定项
- (无)

## 场景 2 事实
_原文：Scene 2_  _行号：L9-L15_

### 事件
- [L11-L11] A walks and B follows.
- [L15-L15] A stops.

### 对白
- [L13-L13] B: Wait.

### 连续性入口
- [L11-L11] A and B are both in the hallway.

### 未确定项
- (无)
"""


def _write_facts(name: str, text: str) -> Path:
    path = _tmpdir() / name
    path.write_text(text, encoding="utf-8")
    return path


class GenerateTests(unittest.TestCase):

    def test_generate_binds_source_and_has_no_concrete_fake_reference(self) -> None:
        _script, digest_path, data = _make_inputs("generate")
        output_path = _tmpdir() / "generated_facts.md"
        text = generate_facts(digest_path, output_path)
        self.assertTrue(output_path.exists())
        self.assertIn(f"source_sha256: {data['source_content_hash']}", text)
        self.assertIn("[Director:", text)
        self.assertNotIn("- [L1-L3] [事件描述]", text)

    def test_generated_skeleton_cannot_pass_before_director_fills_it(self) -> None:
        _script, digest_path, _data = _make_inputs("skeleton")
        facts_path = _tmpdir() / "skeleton_facts.md"
        generate_facts(digest_path, facts_path)
        report = validate_facts(facts_path, digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("placeholder" in issue.detail for issue in report.issues))
        self.assertTrue(any("at least one valid event" in issue.detail
                            for issue in report.issues))

    def test_generate_rejects_digest_without_source_hash(self) -> None:
        _script, digest_path, data = _make_inputs("missing_hash_generate")
        data.pop("source_content_hash")
        digest_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(FactsError):
            generate_facts(digest_path)


class ValidateTests(unittest.TestCase):

    def test_valid_facts_pass(self) -> None:
        _script, digest_path, data = _make_inputs("valid")
        facts_path = _write_facts("valid_facts.md", _valid_facts(data))
        report = validate_facts(facts_path, digest_path)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_single_line_refs_and_sourced_uncertainties_pass(self) -> None:
        _script, digest_path, data = _make_inputs("single_refs")
        text = _valid_facts(data)
        for line_no in (3, 5, 7, 11, 13, 15):
            text = text.replace(f"[L{line_no}-L{line_no}]", f"[L{line_no}]")
        lines = text.splitlines()
        last_empty_bullet = max(
            index for index, line in enumerate(lines) if line.startswith("- (")
        )
        lines[last_empty_bullet] = "- [L15] The later outcome is not stated."
        facts_path = _write_facts("single_refs_facts.md", "\n".join(lines) + "\n")
        report = validate_facts(facts_path, digest_path)
        self.assertTrue(report.ok, f"Issues: {report.issues}")

    def test_out_of_bounds_reference_is_rejected(self) -> None:
        _script, digest_path, data = _make_inputs("bounds")
        text = _valid_facts(data).replace("[L3-L3] A enters", "[L1-L99] A enters")
        report = validate_facts(_write_facts("bounds.md", text), digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("outside scene bounds" in issue.detail
                            for issue in report.issues))

    def test_reversed_reference_is_rejected(self) -> None:
        _script, digest_path, data = _make_inputs("reverse")
        text = _valid_facts(data).replace("[L3-L3] A enters", "[L7-L3] A enters")
        report = validate_facts(_write_facts("reverse.md", text), digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("Invalid range" in issue.detail for issue in report.issues))

    def test_unreferenced_fact_bullet_is_rejected(self) -> None:
        _script, digest_path, data = _make_inputs("unreferenced")
        text = _valid_facts(data).replace(
            "- [L3-L3] A enters and B looks up.",
            "- A enters and B looks up.")
        report = validate_facts(_write_facts("unreferenced.md", text), digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("must be a bullet beginning" in issue.detail
                            for issue in report.issues))

    def test_empty_facts_file_is_rejected(self) -> None:
        _script, digest_path, _data = _make_inputs("empty")
        report = validate_facts(_write_facts("empty.md", ""), digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("Missing" in issue.detail or "Expected" in issue.detail
                            for issue in report.issues))

    def test_missing_source_hash_is_rejected(self) -> None:
        _script, digest_path, data = _make_inputs("no_hash")
        text = _valid_facts(data).replace(
            f"<!-- source_sha256: {data['source_content_hash']} -->\n", "")
        report = validate_facts(_write_facts("no_hash.md", text), digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("Missing <!-- source_sha256" in issue.detail
                            for issue in report.issues))

    def test_stale_facts_hash_is_rejected(self) -> None:
        _script, digest_path, data = _make_inputs("stale_facts")
        text = _valid_facts(data).replace(
            data["source_content_hash"], "0" * 64)
        report = validate_facts(_write_facts("stale_facts.md", text), digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("does not match ingest" in issue.detail
                            for issue in report.issues))

    def test_script_change_after_ingest_is_rejected(self) -> None:
        script_path, digest_path, data = _make_inputs("source_change")
        facts_path = _write_facts("source_change.md", _valid_facts(data))
        script_path.write_text(_SCRIPT + "\nChanged after ingest.\n", encoding="utf-8")
        report = validate_facts(facts_path, digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("changed after ingest" in issue.detail
                            for issue in report.issues))

    def test_each_resolved_scene_requires_an_event(self) -> None:
        _script, digest_path, data = _make_inputs("no_event")
        text = _valid_facts(data).replace(
            "- [L11-L11] A walks and B follows.\n- [L15-L15] A stops.",
            "- (无)")
        report = validate_facts(_write_facts("no_event.md", text), digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("场景 2" in issue.location and
                            "at least one valid event" in issue.detail
                            for issue in report.issues))

    def test_unresolved_scene_boundary_is_rejected(self) -> None:
        script_path = _tmpdir() / "implicit.md"
        script_path.write_text("A paragraph without explicit scene headers.\n",
                               encoding="utf-8")
        digest = asdict(ingest_script(script_path))
        digest_path = _tmpdir() / "implicit.json"
        digest_path.write_text(json.dumps(digest), encoding="utf-8")
        skeleton = _tmpdir() / "implicit_facts.md"
        generate_facts(digest_path, skeleton)
        report = validate_facts(skeleton, digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any("boundary remains unresolved" in issue.detail
                            for issue in report.issues))

    def test_malformed_digest_returns_report_instead_of_traceback(self) -> None:
        digest_path = _tmpdir() / "malformed.json"
        digest_path.write_text("{bad json", encoding="utf-8")
        report = validate_facts(_write_facts("anything.md", "# facts\n"), digest_path)
        self.assertFalse(report.ok)
        self.assertTrue(any(issue.location == "ingest digest"
                            for issue in report.issues))


class CLITests(unittest.TestCase):

    def test_cli_generated_skeleton_fails_until_filled(self) -> None:
        _script, digest_path, _data = _make_inputs("cli_skeleton")
        facts_path = _tmpdir() / "cli_skeleton.md"
        generated = subprocess.run(
            [sys.executable, "-m", "script_facts_tool", "generate",
             str(digest_path), "-o", str(facts_path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(generated.returncode, 0, generated.stderr)
        validated = subprocess.run(
            [sys.executable, "-m", "script_facts_tool", "validate",
             str(facts_path), str(digest_path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(validated.returncode, 0)

    def test_cli_valid_filled_facts_pass(self) -> None:
        _script, digest_path, data = _make_inputs("cli_valid")
        facts_path = _write_facts("cli_valid.md", _valid_facts(data))
        result = subprocess.run(
            [sys.executable, "-m", "script_facts_tool", "validate",
             str(facts_path), str(digest_path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_malformed_digest_fails_without_traceback(self) -> None:
        digest_path = _tmpdir() / "cli_bad_digest.json"
        digest_path.write_text("not-json", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "script_facts_tool", "generate",
             str(digest_path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Facts error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
