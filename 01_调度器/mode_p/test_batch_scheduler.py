"""Tests for measured input/output budget scheduling."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from batch_scheduler import ScheduleError, estimate_tokens, schedule_batches
from script_ingest import ingest_script


class SchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mode_p_schedule_")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def fixture(self, scene_count: int, lines_per_scene: int = 4) -> tuple[Path, Path]:
        script = self.root / f"script-{scene_count}-{lines_per_scene}.md"
        lines: list[str] = []
        for index in range(1, scene_count + 1):
            lines.append(f"## Scene {index} - Room - Day")
            lines.extend(f"Scene {index} event {line}." for line in range(lines_per_scene))
            lines.append("")
        script.write_text("\n".join(lines), encoding="utf-8")
        digest = ingest_script(script)
        digest_path = self.root / f"digest-{scene_count}-{lines_per_scene}.json"
        digest_path.write_text(json.dumps(asdict(digest), ensure_ascii=False), encoding="utf-8")
        session = self.root / f"session-{scene_count}-{lines_per_scene}"
        session.mkdir(exist_ok=True)
        for name in (
            "SCRIPT_FACTS.md", "EPISODE_VISUAL_BIBLE.md", "EPISODE_CONTINUITY_LEDGER.md"
        ):
            (session / name).write_text(f"# {name}\ncomplete", encoding="utf-8")
        return digest_path, session

    def profile(self, context: int, output: int) -> Path:
        path = self.root / f"profile-{context}-{output}.json"
        data = {
            "schema_version": "1.0", "profile_id": "test", "source": "runtime_detected",
            "context_window_tokens": context,
            "reserved_system_tool_tokens": 1000,
            "reserved_output_tokens": output,
            "max_output_tokens_per_call": output,
            "safety_margin_ratio": 0.1,
            "missing_document_reserve_tokens": 1000,
            "token_estimator_version": "unicode_conservative_v1",
        }
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_three_to_five_scene_pilot_is_one_authoritative_batch(self) -> None:
        for count in (3, 5):
            digest, session = self.fixture(count)
            manifest = schedule_batches(digest, session_dir=session)
            self.assertTrue(manifest.authoritative, manifest.provisional_reasons)
            self.assertEqual(manifest.mode, "single_batch")
            self.assertEqual(manifest.total_batches, 1)
            self.assertGreater(manifest.batches[0].input_headroom_tokens, 0)
            self.assertGreater(manifest.batches[0].output_headroom_tokens, 0)

    def test_six_short_scenes_are_not_split_by_arbitrary_scene_count(self) -> None:
        digest, session = self.fixture(6, 1)
        manifest = schedule_batches(digest, session_dir=session)
        self.assertEqual(manifest.total_batches, 1)
        self.assertEqual(manifest.batches[0].scene_indices, [1, 2, 3, 4, 5, 6])

    def test_explicit_user_scene_limit_is_recorded_split_reason(self) -> None:
        digest, session = self.fixture(6, 1)
        manifest = schedule_batches(digest, 3, session_dir=session)
        self.assertEqual(manifest.total_batches, 2)
        self.assertTrue(any("explicit scene limit" in item for item in manifest.split_reasons))

    def test_output_budget_causes_split(self) -> None:
        digest, session = self.fixture(4, 20)
        manifest = schedule_batches(
            digest, session_dir=session, budget_profile_path=self.profile(100_000, 8_000),
            expected_shots_by_scene={1: 3, 2: 3, 3: 3, 4: 3},
        )
        self.assertGreater(manifest.total_batches, 1)
        self.assertTrue(any("output budget" in item for item in manifest.split_reasons))
        self.assertTrue(all(batch.estimated_output_tokens <= 8_000 for batch in manifest.batches))

    def test_input_budget_and_capsule_union_are_measured(self) -> None:
        digest, session = self.fixture(3, 10)
        capsule = self.root / "capsule.md"
        capsule.write_text("知识" * 2000, encoding="utf-8")
        manifest = schedule_batches(
            digest, session_dir=session, budget_profile_path=self.profile(60_000, 20_000),
            capsules_by_scene={1: [capsule], 2: [capsule]},
        )
        self.assertEqual(manifest.batches[0].loaded_capsules, [capsule.resolve().as_posix()])
        self.assertEqual(
            manifest.batches[0].capsule_input_characters, len(capsule.read_text(encoding="utf-8"))
        )

    def test_single_scene_over_budget_fails_closed(self) -> None:
        digest, session = self.fixture(1, 200)
        with self.assertRaisesRegex(ScheduleError, "cannot fit"):
            schedule_batches(
                digest, session_dir=session,
                budget_profile_path=self.profile(10_000, 2_000),
                expected_shots_by_scene={1: 20},
            )

    def test_missing_documents_create_provisional_non_authoritative_manifest(self) -> None:
        digest, _ = self.fixture(2)
        missing_session = self.root / "missing-session"
        manifest = schedule_batches(digest, session_dir=missing_session)
        self.assertFalse(manifest.authoritative)
        self.assertIn("do not call Director", manifest.warning)
        self.assertTrue(manifest.provisional_reasons)

    def test_selected_scope_is_validated_and_preserved(self) -> None:
        digest, session = self.fixture(5)
        manifest = schedule_batches(digest, scene_indices=[2, 4], session_dir=session)
        self.assertEqual(manifest.selected_scenes, [2, 4])
        for invalid in ([], [2, 1], [1, 1], [9]):
            with self.assertRaises(ScheduleError):
                schedule_batches(digest, scene_indices=invalid, session_dir=session)

    def test_manifest_records_detected_budgets_and_actual_measurements(self) -> None:
        digest, session = self.fixture(3)
        manifest = schedule_batches(digest, session_dir=session)
        self.assertEqual(manifest.estimator_version, "unicode_conservative_v1")
        self.assertIn("detected_input_budget", manifest.budget_profile)
        self.assertEqual(len(manifest.scene_measurements), 3)
        self.assertTrue(all(item.source_measurement == "script_content" for item in manifest.scene_measurements))

    def test_language_estimator_counts_cjk_more_conservatively_than_ascii(self) -> None:
        self.assertGreater(estimate_tokens("汉" * 100), estimate_tokens("a" * 100))


if __name__ == "__main__":
    unittest.main()
