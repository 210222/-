"""Tests for layered cache inputs and verified content-addressed storage."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bootstrap_loader import load_bootstrap
from cache_manager import (
    CacheError,
    build_asset_key,
    build_capability_key,
    build_check_key,
    build_core_bundle_key,
    build_dp_key,
    build_knowledge_context_key,
    build_master_key,
    build_scene_context_key,
    build_script_key,
    build_views_key,
    build_visual_bible_key,
    load_cache_manifest,
    lookup_cache,
    restore_cache,
    store_in_cache,
)
from pipeline_telemetry import summarize_events


class KeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bootstrap = load_bootstrap()
        assert cls.bootstrap.ok, cls.bootstrap.errors

    def test_layered_keys_are_deterministic_and_stage_specific(self) -> None:
        core = build_core_bundle_key(self.bootstrap)
        script = build_script_key("script", self.bootstrap)
        bible = build_visual_bible_key(script, core, "constraint", "continuity")
        self.assertEqual(core.compute(), build_core_bundle_key(self.bootstrap).compute())
        self.assertNotEqual(core.compute(), script.compute())
        self.assertEqual(len(bible.compute()), 64)

    def test_real_instruction_and_parser_fingerprints_change_keys(self) -> None:
        changed_instruction = copy.deepcopy(self.bootstrap)
        path = next(key for key in changed_instruction.runtime_fingerprints if key.endswith("mode-p-director.md"))
        changed_instruction.runtime_fingerprints[path] = "f" * 64
        self.assertNotEqual(
            build_core_bundle_key(self.bootstrap).compute(),
            build_core_bundle_key(changed_instruction).compute(),
        )
        changed_parser = copy.deepcopy(self.bootstrap)
        changed_parser.checker_fingerprints["script_ingest.py"] = "e" * 64
        self.assertNotEqual(
            build_script_key("same", self.bootstrap).compute(),
            build_script_key("same", changed_parser).compute(),
        )

    def test_scene_context_changes_only_for_actual_context_input(self) -> None:
        first = build_scene_context_key("scene", "left/right", "bible excerpt")
        same = build_scene_context_key("scene", "left/right", "bible excerpt")
        changed = build_scene_context_key("scene changed", "left/right", "bible excerpt")
        self.assertEqual(first.compute(), same.compute())
        self.assertNotEqual(first.compute(), changed.compute())

    def test_knowledge_key_reads_only_selected_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cache_knowledge_") as temp:
            root = Path(temp)
            selected = root / "selected.md"
            unselected = root / "unselected.md"
            selected.write_text("A", encoding="utf-8")
            unselected.write_text("X", encoding="utf-8")
            first = build_knowledge_context_key(self.bootstrap, {"A": selected}, {})
            unselected.write_text("Y", encoding="utf-8")
            second = build_knowledge_context_key(self.bootstrap, {"A": selected}, {})
            selected.write_text("B", encoding="utf-8")
            third = build_knowledge_context_key(self.bootstrap, {"A": selected}, {})
        self.assertEqual(first.compute(), second.compute())
        self.assertNotEqual(first.compute(), third.compute())

    def test_asset_key_uses_only_selected_records(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cache_assets_") as temp:
            root = Path(temp)
            index = root / "ASSET_INDEX.json"
            data = {
                "schema_version": "1.1", "description": "test assets",
                "updated_at": "2026-01-01T00:00:00+00:00", "asset_root": ".",
                "asset_count": 2,
                "assets": [
                    {"asset_id": "a", "path": "a.png", "media_type": "image", "content_sha256": "a" * 64, "byte_size": 1, "status": "available", "responsibilities": ["identity"]},
                    {"asset_id": "b", "path": "b.png", "media_type": "image", "content_sha256": "b" * 64, "byte_size": 1, "status": "available", "responsibilities": ["location"]},
                ],
            }
            index.write_text(json.dumps(data), encoding="utf-8")
            first = build_asset_key(index, ["a"])
            data["assets"][1]["content_sha256"] = "c" * 64
            index.write_text(json.dumps(data), encoding="utf-8")
            second = build_asset_key(index, ["a"])
            data["assets"][0]["status"] = "missing"
            index.write_text(json.dumps(data), encoding="utf-8")
            third = build_asset_key(index, ["a"])
        self.assertEqual(first.compute(), second.compute())
        self.assertNotEqual(first.compute(), third.compute())

    def test_master_dp_and_check_keys_include_every_named_input(self) -> None:
        scene = build_scene_context_key("scene", "adjacent", "bible")
        knowledge = build_knowledge_context_key(self.bootstrap, {}, {})
        capability = build_capability_key(self.bootstrap)
        assets = build_asset_key(Path(__file__).parents[2] / "ASSET_INDEX.json", [])
        master_key = build_master_key(scene, knowledge, capability, assets, self.bootstrap)
        self.assertEqual(len(master_key.compute()), 64)
        first_dp = build_dp_key(
            script_facts="facts", scene_context="scene", visual_bible_excerpt="bible",
            master="master", storyboard="story", video_prompt="video",
            reference_plan="refs", capability_key=capability, bootstrap=self.bootstrap,
        )
        changed_dp = build_dp_key(
            script_facts="facts", scene_context="scene", visual_bible_excerpt="bible",
            master="master", storyboard="story changed", video_prompt="video",
            reference_plan="refs", capability_key=capability, bootstrap=self.bootstrap,
        )
        self.assertNotEqual(first_dp.compute(), changed_dp.compute())
        check = build_check_key(
            master="master", manifest="manifest", storyboard="story", video_prompt="video",
            capability_key=capability, asset_key=assets,
            checker_names=["master_sync_check.py", "boundary_check.py"],
            bootstrap=self.bootstrap,
        )
        self.assertEqual(len(check.compute()), 64)
        self.assertEqual(len(build_views_key("master", self.bootstrap).compute()), 64)

    def test_wrong_stage_dependency_and_invalid_bootstrap_fail_closed(self) -> None:
        core = build_core_bundle_key(self.bootstrap)
        capability = build_capability_key(self.bootstrap)
        assets = build_asset_key(Path(__file__).parents[2] / "ASSET_INDEX.json", [])
        with self.assertRaises(CacheError):
            build_master_key(core, core, capability, assets, self.bootstrap)
        invalid = copy.deepcopy(self.bootstrap)
        invalid.errors.append("broken")
        with self.assertRaises(CacheError):
            build_script_key("script", invalid)


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mode_p_cache_")
        self.root = Path(self.temp.name)
        self.cache = self.root / "cache"
        self.bootstrap = load_bootstrap()
        self.key = build_script_key("script", self.bootstrap)
        self.output = self.root / "output.md"
        self.output.write_text("cached output", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_store_lookup_and_manifest_integrity(self) -> None:
        entry = store_in_cache(self.cache, self.key, {"SCRIPT_FACTS.md": self.output})
        self.assertEqual(entry.stage, "script")
        self.assertIsNotNone(lookup_cache(self.cache, self.key))
        manifest = load_cache_manifest(self.cache)
        self.assertEqual(len(manifest.entries), 1)
        self.assertEqual(len(manifest.manifest_sha256), 64)

    def test_output_tampering_and_untracked_file_are_cache_misses(self) -> None:
        entry = store_in_cache(self.cache, self.key, {"out.md": self.output})
        object_root = self.cache.joinpath(*Path(entry.object_root).parts)
        (object_root / "out.md").write_text("tampered", encoding="utf-8")
        self.assertIsNone(lookup_cache(self.cache, self.key))
        store_in_cache(self.cache, self.key, {"out.md": self.output})
        (object_root / "extra.md").write_text("extra", encoding="utf-8")
        self.assertIsNone(lookup_cache(self.cache, self.key))

    def test_manifest_tampering_is_a_cache_miss(self) -> None:
        store_in_cache(self.cache, self.key, {"out.md": self.output})
        path = self.cache / "CACHE_MANIFEST.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["entries"][0]["stage"] = "dp"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIsNone(lookup_cache(self.cache, self.key))

    def test_traversal_empty_and_missing_outputs_are_rejected(self) -> None:
        with self.assertRaises(CacheError):
            store_in_cache(self.cache, self.key, {})
        with self.assertRaises(CacheError):
            store_in_cache(self.cache, self.key, {"../escape.md": self.output})
        with self.assertRaises(CacheError):
            store_in_cache(self.cache, self.key, {"missing.md": self.root / "missing"})

    def test_verified_restore_and_real_hit_miss_telemetry(self) -> None:
        telemetry = self.root / "episode"
        entry = store_in_cache(
            self.cache,
            self.key,
            {"restored/output.md": self.output},
            telemetry_session=telemetry,
        )
        hit = lookup_cache(
            self.cache, self.key, telemetry_session=telemetry
        )
        self.assertIsNotNone(hit)
        destination = self.root / "restore_target"
        restored = restore_cache(self.cache, entry, destination)
        self.assertEqual(
            restored["restored/output.md"].read_text(encoding="utf-8"),
            "cached output",
        )
        missing_key = build_script_key("different script", self.bootstrap)
        self.assertIsNone(lookup_cache(
            self.cache, missing_key, telemetry_session=telemetry
        ))
        summary = summarize_events(telemetry)
        self.assertEqual(summary["cache"], {"hit": 1, "miss": 1, "store": 1})


if __name__ == "__main__":
    unittest.main()
