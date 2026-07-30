"""Tests for knowledge directory structure and index integrity."""

from __future__ import annotations

import json
import hashlib
import re
import unittest
from pathlib import Path


_KNOWLEDGE_DIR = Path(__file__).with_name("knowledge")
_INDEX_PATH = _KNOWLEDGE_DIR / "knowledge_index.json"


class KnowledgeStructureTests(unittest.TestCase):

    def test_core_directory_has_all_required_files(self) -> None:
        core = _KNOWLEDGE_DIR / "core"
        self.assertTrue(core.is_dir(), "core/ directory must exist")
        required = {"director_core.md", "sd2.md", "performance.md", "editing_transition.md"}
        actual = {p.name for p in core.iterdir() if p.suffix == ".md"}
        self.assertEqual(actual, required, f"Missing or extra core files: {required ^ actual}")

    def test_capsules_directory_has_required_minimum(self) -> None:
        capsules = _KNOWLEDGE_DIR / "capsules"
        self.assertTrue(capsules.is_dir(), "capsules/ directory must exist")
        required = {
            "dialogue_power.md", "action_chase.md", "suspense_reveal.md",
            "contemplative_silence.md", "crowd_attention.md",
            "investigation_object.md", "montage.md", "cross_space_transition.md",
            "omni_reference.md",
        }
        actual = {p.name for p in capsules.iterdir() if p.suffix == ".md"}
        self.assertEqual(actual, required, f"Missing or extra capsules: {required ^ actual}")

    def test_index_maps_all_disk_files(self) -> None:
        self.assertTrue(_INDEX_PATH.exists(), "knowledge_index.json must exist")
        index = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))

        # Core
        core_disk = {p.relative_to(_KNOWLEDGE_DIR).as_posix()
                     for p in (_KNOWLEDGE_DIR / "core").iterdir() if p.suffix == ".md"}
        core_indexed = {entry["path"] for entry in index["core"]}
        self.assertEqual(core_indexed, core_disk, "Indexed core files must match disk")

        # Capsules
        cap_disk = {p.relative_to(_KNOWLEDGE_DIR).as_posix()
                    for p in (_KNOWLEDGE_DIR / "capsules").iterdir() if p.suffix == ".md"}
        cap_indexed = {entry["path"] for entry in index["capsules"]}
        self.assertEqual(cap_indexed, cap_disk, "Indexed capsules must match disk")

    def test_core_entries_are_marked_always_load(self) -> None:
        index = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        for entry in index["core"]:
            self.assertTrue(entry.get("always_load", False),
                            f"Core entry {entry['path']} must have always_load: true")

    def test_capsules_have_required_fields(self) -> None:
        index = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        required = {"path", "scene_types", "drama_intents", "space_conditions",
                    "character_count_range", "motion_complexity", "sd2_risk_tags",
                    "verified_count", "experience_status"}
        for entry in index["capsules"]:
            missing = required - set(entry.keys())
            self.assertFalse(missing, f"Capsule {entry.get('path', '?')} missing fields: {missing}")

    def test_capsule_files_are_readable_and_non_empty(self) -> None:
        for entry in json.loads(_INDEX_PATH.read_text(encoding="utf-8"))["capsules"]:
            path = _KNOWLEDGE_DIR / entry["path"]
            self.assertTrue(path.is_file(), f"Capsule not found: {path}")
            text = path.read_text(encoding="utf-8")
            self.assertTrue(len(text) > 200, f"Capsule {entry['path']} too short ({len(text)} chars)")
            # New capsules must have the unified structure; legacy capsules are grandfathered
            new_capsules = {"crowd_attention.md", "investigation_object.md",
                            "montage.md", "cross_space_transition.md", "omni_reference.md"}
            if entry["path"].split("/")[-1] in new_capsules:
                required_headers = ["适用信号", "核心问题", "可用手段", "SD2.0 适配", "常见失败"]
                for header in required_headers:
                    self.assertIn(header, text, f"{entry['path']} missing section: {header}")

    def test_core_contains_the_directing_decision_chain_without_bloat(self) -> None:
        core = _KNOWLEDGE_DIR / "core"
        texts = {
            path.name: path.read_text(encoding="utf-8")
            for path in core.glob("*.md")
        }
        total_bytes = sum(len(text.encode("utf-8")) for text in texts.values())
        self.assertGreaterEqual(total_bytes, 10000)
        self.assertLessEqual(total_bytes, 20000)

        director_terms = {
            "叙事视点", "戏剧节拍", "演员", "焦段", "负空间",
            "物理因果", "跨域联动", "裁决顺序",
        }
        performance_terms = {"目标", "策略", "基线", "刺激", "反应", "视线", "呼吸", "景别"}
        editing_terms = {"继续停留", "切点", "锚点", "in_camera", "post_production", "声音桥"}
        sd2_terms = {"sd2_capability_profile.json", "Director", "first_last_frame", "omni_reference"}
        for term in director_terms:
            self.assertIn(term, texts["director_core.md"])
        for term in performance_terms:
            self.assertIn(term, texts["performance.md"])
        for term in editing_terms:
            self.assertIn(term, texts["editing_transition.md"])
        for term in sd2_terms:
            self.assertIn(term, texts["sd2.md"])

    def test_runtime_knowledge_has_no_legacy_or_false_hard_claims(self) -> None:
        corpus = "\n".join(
            path.read_text(encoding="utf-8")
            for path in _KNOWLEDGE_DIR.rglob("*.md")
        )
        forbidden = {
            "Seko": "legacy platform",
            "@图片": "legacy platform reference syntax",
            "Gate 0": "legacy audit chain",
            "最多两个清晰主脸": "unverified face hard limit",
            "每镜最多两张": "unverified face hard limit",
            "SD2.0 无法理解抽象的时间压缩": "unsupported absolute capability claim",
            "手部特写是 SD2.0 强项": "unsupported strength claim",
            "最强的连续性保证": "unsupported guarantee",
            "当前能力互斥": "unversioned platform claim",
        }
        for phrase, reason in forbidden.items():
            self.assertNotIn(phrase, corpus, f"{reason}: {phrase}")
        self.assertIsNone(
            re.search(r"\b(?:R\d{2}|D-[A-Z]{2,})\b", corpus),
            "runtime knowledge must not expose legacy rule IDs",
        )

    def test_index_schema_version_is_valid(self) -> None:
        index = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        self.assertIn("schema_version", index)
        self.assertEqual(index["schema_version"], "1.1")

    def test_index_does_not_choose_generation_mode(self) -> None:
        index = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        for entry in index["capsules"]:
            self.assertNotIn("generation_mode", entry)

    def test_index_has_no_duplicate_paths(self) -> None:
        index = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        all_paths = [e["path"] for e in index["core"]] + [e["path"] for e in index["capsules"]]
        self.assertEqual(len(all_paths), len(set(all_paths)), "Duplicate paths in index")


if __name__ == "__main__":
    unittest.main()
