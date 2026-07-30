"""Tests that transformed legacy patterns remain traceable and non-runtime."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


_ROOT = Path(__file__).parent.parent.parent
_TRANSFORMED = _ROOT / "04_共享" / "decision_patterns" / "TRANSFORMED_INDEX.json"


class PatternStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(_TRANSFORMED.read_text(encoding="utf-8"))

    def test_schema_and_top_level_are_closed(self) -> None:
        self.assertEqual(self.data["schema_version"], "2.1")
        self.assertEqual(set(self.data), {
            "schema_version", "description", "patterns", "no_match_policy"
        })

    def test_patterns_are_explicitly_not_runtime_eligible(self) -> None:
        for pattern in self.data["patterns"]:
            self.assertEqual(pattern["status"], "historical_unvalidated")
            self.assertIs(pattern["runtime_eligible"], False)
            self.assertEqual(pattern["evidence"]["evidence_level"], "design_output_only")
            self.assertEqual(pattern["evidence"]["render_evidence"], [])
            self.assertEqual(pattern["evidence"]["user_observations"], [])

    def test_all_patterns_have_closed_required_fields(self) -> None:
        required = {
            "case_id", "reference_ep", "status", "runtime_eligible",
            "applicability", "non_applicability", "evidence", "invariants", "variables",
        }
        for pattern in self.data["patterns"]:
            self.assertEqual(set(pattern), required)
            applicability = pattern["applicability"]
            self.assertEqual(set(applicability), {
                "scene_types", "drama_intents", "space_conditions",
                "character_count_range", "motion_complexity",
            })
            count_range = applicability["character_count_range"]
            self.assertGreaterEqual(count_range["min"], 0)
            self.assertGreaterEqual(count_range["max"], count_range["min"])
            self.assertTrue(pattern["non_applicability"])
            self.assertTrue(pattern["invariants"])
            self.assertTrue(pattern["variables"])

    def test_legacy_source_files_exist_and_hashes_match(self) -> None:
        for pattern in self.data["patterns"]:
            sources = pattern["evidence"]["source_files"]
            self.assertTrue(sources)
            for source in sources:
                self.assertEqual(set(source), {"path", "content_sha256"})
                path = _ROOT / source["path"]
                self.assertTrue(path.is_file(), path)
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    source["content_sha256"],
                )

    def test_no_match_never_loads_historical_patterns(self) -> None:
        policy = self.data["no_match_policy"]
        self.assertEqual(policy["action"], "load_core_only")
        self.assertTrue(any("runtime_eligible" in item for item in policy["forbidden_behaviors"]))

    def test_case_ids_are_unique(self) -> None:
        ids = [pattern["case_id"] for pattern in self.data["patterns"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_runtime_retriever_does_not_read_legacy_pattern_index(self) -> None:
        source = (Path(__file__).with_name("context_retriever.py")).read_text(encoding="utf-8")
        self.assertNotIn("TRANSFORMED_INDEX", source)
        self.assertNotIn("decision_patterns", source)


if __name__ == "__main__":
    unittest.main()
