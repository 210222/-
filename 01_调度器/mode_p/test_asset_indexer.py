"""Tests for the strict, stable MODE:P asset index."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from asset_indexer import AssetIndexError, scan_directory, update_status, validate_assets


class AssetIndexerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix=f"mode_p_assets_{os.getpid()}_")
        self.root = Path(self.temp.name)
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.index = self.root / "ASSET_INDEX.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_empty_scan_is_valid(self) -> None:
        data = scan_directory(self.assets, self.index)
        self.assertEqual(data["asset_count"], 0)
        self.assertEqual(validate_assets(self.index), (True, []))

    def test_scan_hashes_assets_and_creates_manifest_safe_ids(self) -> None:
        (self.assets / "角色").mkdir()
        (self.assets / "角色" / "主角.PNG").write_bytes(b"image")
        (self.assets / "beat.mp3").write_bytes(b"audio")
        data = scan_directory(self.assets, self.index)
        self.assertEqual(data["asset_count"], 2)
        for asset in data["assets"]:
            self.assertRegex(asset["asset_id"], r"^[A-Za-z0-9][A-Za-z0-9_-]+$")
            self.assertEqual(len(asset["content_sha256"]), 64)
        self.assertEqual(validate_assets(self.index), (True, []))

    def test_rescan_preserves_id_and_director_responsibilities(self) -> None:
        path = self.assets / "hero.png"
        path.write_bytes(b"v1")
        first = scan_directory(self.assets, self.index)
        data = json.loads(self.index.read_text(encoding="utf-8"))
        data["assets"][0]["responsibilities"] = ["identity", "first_frame"]
        self.index.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        path.write_bytes(b"v2")
        second = scan_directory(self.assets, self.index)
        self.assertEqual(first["assets"][0]["asset_id"], second["assets"][0]["asset_id"])
        self.assertEqual(second["assets"][0]["responsibilities"], ["identity", "first_frame"])
        self.assertNotEqual(first["assets"][0]["content_sha256"], second["assets"][0]["content_sha256"])

    def test_rescan_marks_disappeared_asset_missing(self) -> None:
        path = self.assets / "hero.png"
        path.write_bytes(b"v1")
        scan_directory(self.assets, self.index)
        path.unlink()
        data = scan_directory(self.assets, self.index)
        self.assertEqual(data["assets"][0]["status"], "missing")
        self.assertEqual(validate_assets(self.index), (True, []))

    def test_hash_and_size_mismatch_fail(self) -> None:
        path = self.assets / "hero.png"
        path.write_bytes(b"v1")
        scan_directory(self.assets, self.index)
        path.write_bytes(b"changed")
        ok, issues = validate_assets(self.index)
        self.assertFalse(ok)
        self.assertTrue(any("hash mismatch" in issue for issue in issues))

    def test_path_traversal_fails(self) -> None:
        scan_directory(self.assets, self.index)
        data = json.loads(self.index.read_text(encoding="utf-8"))
        data["assets"] = [{
            "asset_id": "escape", "path": "../outside.png", "media_type": "image",
            "content_sha256": "a" * 64, "byte_size": 1, "status": "missing",
            "responsibilities": [],
        }]
        data["asset_count"] = 1
        self.index.write_text(json.dumps(data), encoding="utf-8")
        self.assertFalse(validate_assets(self.index)[0])

    def test_unknown_status_target_fails(self) -> None:
        scan_directory(self.assets, self.index)
        with self.assertRaisesRegex(AssetIndexError, "unknown asset_id"):
            update_status(self.index, "unknown", "deprecated")

    def test_missing_file_cannot_be_marked_available(self) -> None:
        path = self.assets / "hero.png"
        path.write_bytes(b"v1")
        data = scan_directory(self.assets, self.index)
        asset_id = data["assets"][0]["asset_id"]
        path.unlink()
        scan_directory(self.assets, self.index)
        with self.assertRaisesRegex(AssetIndexError, "missing file"):
            update_status(self.index, asset_id, "available")

    def test_bundled_index_is_honestly_valid(self) -> None:
        bundled = Path(__file__).parent.parent.parent / "ASSET_INDEX.json"
        self.assertEqual(validate_assets(bundled), (True, []))

    def test_cli_scan_and_validate(self) -> None:
        (self.assets / "hero.png").write_bytes(b"image")
        scan = subprocess.run(
            [sys.executable, "-m", "asset_indexer", "scan", str(self.assets), "-o", str(self.index)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(scan.returncode, 0, scan.stderr)
        validate = subprocess.run(
            [sys.executable, "-m", "asset_indexer", "validate", str(self.index)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(validate.returncode, 0, validate.stderr)


if __name__ == "__main__":
    unittest.main()
