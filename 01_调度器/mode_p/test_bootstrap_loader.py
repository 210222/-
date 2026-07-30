"""Tests for strict, metadata-only bootstrap loading."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest import mock

from bootstrap_loader import (
    compute_cache_key,
    load_bootstrap,
    write_bootstrap_manifest,
)


class BootstrapTests(unittest.TestCase):
    def test_loads_stable_core_indexes_runtime_and_checkers(self) -> None:
        manifest = load_bootstrap()
        self.assertTrue(manifest.ok, manifest.errors)
        self.assertEqual(manifest.knowledge_core_count, 4)
        self.assertGreater(manifest.knowledge_capsule_count, 0)
        self.assertEqual(len(manifest.core_documents), 4)
        self.assertEqual(len(manifest.manifest_sha256), 64)
        self.assertIn(".claude/agents/mode-p-director.md", manifest.runtime_fingerprints)
        self.assertIn("master_sync_check.py", manifest.checker_fingerprints)
        self.assertGreater(len(manifest.compiler_version), 0)
        self.assertEqual(manifest.asset_card_count, 0)
        self.assertIn("asset_card_registry.py", manifest.checker_fingerprints)

    def test_capsule_and_media_bodies_are_not_read(self) -> None:
        original = Path.read_bytes

        def guarded(path: Path) -> bytes:
            normalized = path.as_posix()
            if "/knowledge/capsules/" in normalized or path.suffix.lower() in {
                ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".mp3", ".wav"
            }:
                raise AssertionError(f"bootstrap read forbidden body: {path}")
            return original(path)

        with mock.patch.object(Path, "read_bytes", guarded):
            manifest = load_bootstrap()
        self.assertTrue(manifest.ok, manifest.errors)

    def test_manifest_is_deterministic_for_unchanged_inputs(self) -> None:
        first = load_bootstrap()
        second = load_bootstrap()
        self.assertTrue(first.ok and second.ok)
        self.assertEqual(first.manifest_sha256, second.manifest_sha256)

    def test_missing_asset_index_is_fatal(self) -> None:
        manifest = load_bootstrap(asset_index_path=Path("Z:/missing/ASSET_INDEX.json"))
        self.assertFalse(manifest.ok)
        self.assertTrue(any(item.startswith("asset_index:") for item in manifest.errors))

    def test_missing_asset_card_index_is_fatal(self) -> None:
        manifest = load_bootstrap(
            asset_card_index_path=Path("Z:/missing/ASSET_CARD_INDEX.json")
        )
        self.assertFalse(manifest.ok)
        self.assertTrue(any(
            item.startswith("asset_card_index:") for item in manifest.errors
        ))

    def test_invalid_core_hash_fails_without_loading_capsules(self) -> None:
        source = Path(__file__).parent / "knowledge"
        with tempfile.TemporaryDirectory(prefix=f"bootstrap_{os.getpid()}_") as temp:
            root = Path(temp) / "knowledge"
            (root / "core").mkdir(parents=True)
            index = json.loads((source / "knowledge_index.json").read_text(encoding="utf-8"))
            for entry in index["core"]:
                src = source / entry["path"]
                dst = root / entry["path"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
            for entry in index["capsules"]:
                dst = root / entry["path"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text("metadata-only fixture", encoding="utf-8")
            (root / "knowledge_index.json").write_text(
                json.dumps(index, ensure_ascii=False), encoding="utf-8"
            )
            (root / index["core"][0]["path"]).write_text("tampered", encoding="utf-8")
            manifest = load_bootstrap(knowledge_index_path=root / "knowledge_index.json")
        self.assertFalse(manifest.ok)
        self.assertTrue(any("Core content" in item for item in manifest.errors))

    def test_cache_key_rejects_invalid_bootstrap_and_bad_scene_scope(self) -> None:
        valid = load_bootstrap()
        self.assertEqual(
            compute_cache_key(valid, "script", [1, 2]),
            compute_cache_key(valid, "script", [2, 1]),
        )
        with self.assertRaises(ValueError):
            compute_cache_key(valid, "", [1])
        with self.assertRaises(ValueError):
            compute_cache_key(valid, "script", [1, 1])
        invalid = load_bootstrap(asset_index_path=Path("Z:/missing/index.json"))
        with self.assertRaises(ValueError):
            compute_cache_key(invalid, "script", [1])

    def test_persisted_manifest_has_integrity_hash(self) -> None:
        manifest = load_bootstrap()
        with tempfile.TemporaryDirectory(prefix="bootstrap_output_") as temp:
            output = Path(temp) / "CORE_BUNDLE_MANIFEST.json"
            write_bootstrap_manifest(output, manifest)
            data = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(data["manifest_sha256"], manifest.manifest_sha256)
        self.assertNotIn("capsule text", json.dumps(asdict(manifest), ensure_ascii=False))


class CLITests(unittest.TestCase):
    def test_cli_json_and_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="bootstrap_cli_") as temp:
            output = Path(temp) / "CORE_BUNDLE_MANIFEST.json"
            result = subprocess.run(
                [sys.executable, "-m", "bootstrap_loader", "--json", "--output", str(output)],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True, encoding="utf-8",
                timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())
            self.assertEqual(len(json.loads(result.stdout)["manifest_sha256"]), 64)

    def test_cli_bad_index_is_error(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "bootstrap_loader", "--knowledge-index", "Z:/missing.json"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
