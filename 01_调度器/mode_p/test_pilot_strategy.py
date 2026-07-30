"""Tests for executable Director/DP batch strategies."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from pilot_strategy import plan_strategy
from script_ingest import ingest_script


class StrategyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mode_p_strategy_")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def fixture(self, scenes: int, complete: bool = True) -> tuple[Path, Path, Path]:
        script = self.root / f"script-{scenes}.md"
        script.write_text("\n".join(
            line
            for index in range(1, scenes + 1)
            for line in (f"## Scene {index} - Room - Day", "A crosses the room.", "")
        ), encoding="utf-8")
        digest = ingest_script(script)
        digest_path = self.root / f"digest-{scenes}.json"
        digest_path.write_text(json.dumps(asdict(digest), ensure_ascii=False), encoding="utf-8")
        session = self.root / f"session-{scenes}"
        session.mkdir()
        if complete:
            for name in (
                "SCRIPT_FACTS.md", "EPISODE_VISUAL_BIBLE.md", "EPISODE_CONTINUITY_LEDGER.md"
            ):
                (session / name).write_text(f"# {name}\ncomplete", encoding="utf-8")
        return script, digest_path, session

    def test_five_scene_pilot_is_exactly_one_director_and_one_fresh_dp(self) -> None:
        script, digest, session = self.fixture(5)
        report = plan_strategy(script, digest, session_dir=session)
        self.assertTrue(report.executable)
        self.assertTrue(report.is_pilot)
        self.assertEqual(report.baseline_director_calls, 1)
        self.assertEqual(report.baseline_dp_calls, 1)
        self.assertEqual(
            report.execution_batches[0]["dp_context_policy"],
            "fresh_subagent_no_prior_dp_context",
        )

    def test_long_budget_split_uses_one_fresh_dp_per_director_batch(self) -> None:
        script, digest, session = self.fixture(8)
        report = plan_strategy(script, digest, max_scenes_per_batch=3, session_dir=session)
        self.assertTrue(report.is_long_form)
        self.assertEqual(report.baseline_director_calls, report.total_batches)
        self.assertEqual(report.baseline_dp_calls, report.total_batches)
        self.assertTrue(report.execution_batches[1]["prior_committed_ledger_required"])
        self.assertTrue(all(item["fresh_dp_required"] for item in report.execution_batches))

    def test_incomplete_inputs_never_claim_model_call_counts(self) -> None:
        script, digest, session = self.fixture(4, complete=False)
        report = plan_strategy(script, digest, session_dir=session)
        self.assertFalse(report.executable)
        self.assertEqual(report.mode, "provisional")
        self.assertIsNone(report.baseline_director_calls)
        self.assertIsNone(report.baseline_dp_calls)
        self.assertTrue(report.blockers)

    def test_local_scope_is_not_mislabeled_full_pilot(self) -> None:
        script, digest, session = self.fixture(8)
        report = plan_strategy(script, digest, [2, 3, 4], session_dir=session)
        self.assertEqual(report.mode, "local_scope")
        self.assertEqual(report.selected_scenes, [2, 3, 4])


if __name__ == "__main__":
    unittest.main()
