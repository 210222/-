"""Tests for fail-closed, metadata-only Director knowledge retrieval."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from context_retriever import (
    RetrievalError,
    relevance,
    retrieve_context,
    write_context_md,
)


_INDEX = Path(__file__).with_name("knowledge") / "knowledge_index.json"


def _query(**overrides: object) -> dict:
    query = {
        "scene_types": [],
        "drama_intents": [],
        "space_conditions": [],
        "character_count": None,
        "motion_complexity": None,
        "requested_capsules": [],
    }
    query.update(overrides)
    return query


class ScoringTests(unittest.TestCase):
    def test_exact_match_scores_highest(self) -> None:
        entry = {
            "path": "capsules/dialogue_power.md",
            "scene_types": ["dialogue"],
            "drama_intents": ["relationship_change"],
            "space_conditions": ["indoor"],
            "character_count_range": {"min": 2, "max": 2},
            "motion_complexity": "low",
        }
        score, reasons = relevance(entry, _query(
            scene_types=["dialogue"],
            drama_intents=["relationship_change"],
            space_conditions=["indoor"],
            character_count=2,
            motion_complexity="low",
        ))
        self.assertEqual(score, 12)
        self.assertIn("character_count", reasons)

    def test_weak_numeric_match_cannot_select(self) -> None:
        entry = {
            "path": "capsules/action_chase.md",
            "scene_types": ["action"],
            "drama_intents": ["survival"],
            "space_conditions": ["open"],
            "character_count_range": {"min": 1, "max": None},
            "motion_complexity": "high",
        }
        self.assertEqual(relevance(entry, _query(character_count=2, motion_complexity="high")), (0, []))


class RetrievalTests(unittest.TestCase):
    def test_core_is_always_returned(self) -> None:
        summary = retrieve_context(_query(scene_types=["dialogue"]), _INDEX)
        self.assertEqual(len(summary["core"]), 4)
        self.assertEqual(summary["capsules"], [])

    def test_action_metadata_does_not_choose_a_capsule(self) -> None:
        summary = retrieve_context(_query(
            scene_types=["action"], drama_intents=["survival"],
            space_conditions=["open"], character_count=4,
            motion_complexity="high",
        ), _INDEX)
        self.assertEqual(summary["capsules"], [])

    def test_unmatched_scene_uses_core_without_historical_fallback(self) -> None:
        summary = retrieve_context(_query(scene_types=["musical_dance_number"]), _INDEX)
        self.assertTrue(summary["no_capsule_match"])
        self.assertEqual(summary["capsules"], [])
        self.assertFalse(summary["historical_fallback_used"])

    def test_max_three_capsules_and_deterministic_order(self) -> None:
        summary1 = retrieve_context(_query(
            requested_capsules=[
                "capsules/dialogue_power.md",
                "capsules/cross_space_transition.md",
                "capsules/omni_reference.md",
            ],
        ), _INDEX)
        summary2 = retrieve_context(summary1["query"], _INDEX)
        self.assertLessEqual(len(summary1["capsules"]), 3)
        self.assertEqual(summary1["capsules"], summary2["capsules"])

    def test_generation_mode_cannot_drive_retrieval(self) -> None:
        with self.assertRaisesRegex(RetrievalError, "unknown query fields"):
            retrieve_context({**_query(), "generation_mode": "omni_reference"}, _INDEX)

    def test_director_can_explicitly_request_indexed_capsule(self) -> None:
        summary = retrieve_context(_query(
            requested_capsules=["capsules/omni_reference.md"]
        ), _INDEX)
        self.assertEqual(summary["capsules"], ["capsules/omni_reference.md"])

    def test_unknown_requested_capsule_fails(self) -> None:
        with self.assertRaisesRegex(RetrievalError, "not indexed"):
            retrieve_context(_query(requested_capsules=["capsules/fake.md"]), _INDEX)

    def test_stale_index_hash_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix=f"mode_p_context_{os.getpid()}_") as temp:
            knowledge = Path(temp) / "knowledge"
            shutil.copytree(_INDEX.parent, knowledge)
            (knowledge / "core" / "director_core.md").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(RetrievalError, "failed closed"):
                retrieve_context(_query(scene_types=["dialogue"]), knowledge / "knowledge_index.json")

    def test_arbitrary_markdown_is_not_a_validated_experience(self) -> None:
        with tempfile.TemporaryDirectory(prefix=f"mode_p_exp_{os.getpid()}_") as temp:
            Path(temp, "unsafe.md").write_text("not validated", encoding="utf-8")
            summary = retrieve_context(
                _query(scene_types=["dialogue"]), _INDEX, Path(temp)
            )
            self.assertEqual(summary["experiences"], [])

    def test_validated_hashed_experience_can_load(self) -> None:
        with tempfile.TemporaryDirectory(prefix=f"mode_p_exp_{os.getpid()}_") as temp:
            root = Path(temp)
            content = root / "dialogue_case.md"
            content.write_text("render-verified dialogue case", encoding="utf-8")
            record = {
                "schema_version": "1.0",
                "experience_id": "exp-dialogue-001",
                "status": "validated",
                "content_path": "dialogue_case.md",
                "content_sha256": hashlib.sha256(content.read_bytes()).hexdigest(),
                "verified_count": 2,
                "render_evidence": ["render-case-001", "render-case-002"],
                "applicability": {
                    "scene_types": ["dialogue"],
                    "drama_intents": ["relationship_change"],
                    "space_conditions": ["indoor"],
                    "character_count_range": {"min": 2, "max": 2},
                    "motion_complexity": "low",
                },
            }
            (root / "dialogue.experience.json").write_text(
                json.dumps(record, ensure_ascii=False), encoding="utf-8"
            )
            summary = retrieve_context(
                _query(scene_types=["dialogue"], character_count=2), _INDEX, root
            )
            self.assertEqual(len(summary["experiences"]), 1)


class OutputAndCLITests(unittest.TestCase):
    def test_write_context_md_is_a_hashed_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix=f"mode_p_context_out_{os.getpid()}_") as temp:
            summary = retrieve_context(_query(scene_types=["dialogue"]), _INDEX)
            output = Path(temp) / "KNOWLEDGE_CONTEXT.md"
            write_context_md(summary, output)
            text = output.read_text(encoding="utf-8")
            self.assertIn("Knowledge index SHA-256", text)
            self.assertIn("Historical fallback used: `false`", text)

    def test_cli_outputs_json(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "context_retriever", "--scene-type", "investigation"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("knowledge_index_sha256", json.loads(result.stdout))

    def test_cli_rejects_negative_character_count(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "context_retriever", "--character-count", "-1"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
