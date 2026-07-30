"""Tests for knowledge_indexer.py — hash computation and validation."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from knowledge_indexer import compute_hashes, validate_index


_INDEX_DIR = Path(__file__).with_name("knowledge")
_INDEX_PATH = _INDEX_DIR / "knowledge_index.json"


class IndexerTests(unittest.TestCase):

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory(
            prefix=f"mode_p_knowledge_{os.getpid()}_"
        )
        self.tmp_dir = Path(self._temp.name) / "knowledge"
        shutil.copytree(_INDEX_DIR, self.tmp_dir)
        self.tmp_index = self.tmp_dir / "knowledge_index.json"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_index_has_all_hashes(self) -> None:
        data = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        for section in ("core", "capsules"):
            for entry in data[section]:
                self.assertIn("content_sha256", entry,
                              f"Missing hash: {entry['path']}")
                self.assertEqual(len(entry["content_sha256"]), 64,
                                 f"Bad hash length: {entry['path']}")
                self.assertIn("byte_size", entry,
                              f"Missing byte_size: {entry['path']}")

    def test_index_has_timestamp(self) -> None:
        data = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        self.assertIn("index_updated_at", data)
        self.assertIn("index_statistics", data)

    def test_validate_passes_on_valid_index(self) -> None:
        ok, issues = validate_index(_INDEX_PATH)
        self.assertTrue(ok, f"Validation issues: {issues}")

    def test_compute_hashes_is_idempotent(self) -> None:
        data1 = compute_hashes(_INDEX_PATH)
        data2 = compute_hashes(_INDEX_PATH)
        self.assertEqual(data1, data2)

    def test_statistics_are_accurate(self) -> None:
        data = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        stats = data["index_statistics"]
        self.assertGreater(stats["total_entries"], 10)
        self.assertGreater(stats["total_bytes"], 10000)

    def test_validate_detects_missing_file(self) -> None:
        data = json.loads(self.tmp_index.read_text(encoding="utf-8"))
        data["capsules"].append({
            "path": "capsules/nonexistent.md",
            "scene_types": ["test"],
            "drama_intents": ["test"],
            "space_conditions": ["test"],
            "character_count_range": {"min": 0, "max": None},
            "motion_complexity": "variable",
            "sd2_risk_tags": ["test"],
            "verified_count": 0,
            "experience_status": "none",
            "content_sha256": "a" * 64,
            "byte_size": 1,
        })
        self.tmp_index.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        ok, issues = validate_index(self.tmp_index)
        self.assertFalse(ok)
        self.assertTrue(any("MISSING" in i for i in issues))

    def test_validate_detects_hash_mismatch(self) -> None:
        data = json.loads(self.tmp_index.read_text(encoding="utf-8"))
        data["core"][0]["content_sha256"] = "b" * 64
        self.tmp_index.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        ok, issues = validate_index(self.tmp_index)
        self.assertFalse(ok)
        self.assertTrue(any("HASH MISMATCH" in i for i in issues))

    def test_validate_rejects_path_traversal(self) -> None:
        data = json.loads(self.tmp_index.read_text(encoding="utf-8"))
        data["core"][0]["path"] = "../outside.md"
        self.tmp_index.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        ok, issues = validate_index(self.tmp_index)
        self.assertFalse(ok)
        self.assertTrue(any("stay under core" in issue for issue in issues))

    def test_validate_rejects_duplicate_paths(self) -> None:
        data = json.loads(self.tmp_index.read_text(encoding="utf-8"))
        data["capsules"].append(dict(data["capsules"][0]))
        self.tmp_index.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        ok, issues = validate_index(self.tmp_index)
        self.assertFalse(ok)
        self.assertTrue(any("duplicate indexed paths" in issue for issue in issues))

    def test_validate_rejects_unknown_creative_selector(self) -> None:
        data = json.loads(self.tmp_index.read_text(encoding="utf-8"))
        data["capsules"][0]["generation_mode"] = "text_only"
        self.tmp_index.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        ok, issues = validate_index(self.tmp_index)
        self.assertFalse(ok)
        self.assertTrue(any("unknown fields" in issue for issue in issues))

    def test_validate_rejects_invalid_character_range(self) -> None:
        data = json.loads(self.tmp_index.read_text(encoding="utf-8"))
        data["capsules"][0]["character_count_range"] = {"min": 3, "max": 2}
        self.tmp_index.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        ok, issues = validate_index(self.tmp_index)
        self.assertFalse(ok)
        self.assertTrue(any("character_count_range.max" in issue for issue in issues))


class CLITests(unittest.TestCase):

    def test_cli_validate_passes(self) -> None:
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "knowledge_indexer", "validate", str(_INDEX_PATH)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)

    def test_cli_update_is_idempotent(self) -> None:
        import subprocess
        import sys
        import tempfile
        tmp = Path(tempfile.gettempdir()) / "test_cli_index.json"
        r1 = subprocess.run(
            [sys.executable, "-m", "knowledge_indexer", "update",
             str(_INDEX_PATH), "-o", str(tmp)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(r1.returncode, 0)
        r2 = subprocess.run(
            [sys.executable, "-m", "knowledge_indexer", "update",
             str(_INDEX_PATH), "-o", str(tmp)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(r2.returncode, 0)
        self.assertIn("0 changed", r2.stdout)


if __name__ == "__main__":
    unittest.main()
