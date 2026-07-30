"""Tests for evidence-bound MODE:P batch transitions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from batch_state_machine import (
    FINAL_CHECKS,
    STRUCTURAL_CHECKS,
    BatchStage,
    StateMachineError,
    bind_manifest,
    init_state,
    is_complete,
    load_state,
    record_batch_commit,
    record_check,
    record_dp_review,
    record_episode_review,
    transition,
)
from dp_contract import DP_READY_SENTENCE


class StateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix=f"mode_p_state_{os.getpid()}_")
        self.session = Path(self.temp.name) / "session"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _file(self, name: str, content: str = "evidence") -> Path:
        path = self.session / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _to_precheck(self, total: int = 1) -> tuple[Path, Path]:
        init_state(self.session, 1, total)
        transition(self.session, BatchStage.SCRIPT_PARSE)
        transition(self.session, BatchStage.DIRECTOR_BATCH)
        master = self._file("working/DIRECTOR_MASTER.md", "master-v1")
        transition(self.session, BatchStage.STRUCTURAL_PRECHECK, master_path=master)
        manifest = self._file(
            "working/SHOT_MANIFEST.json",
            json.dumps({"shots": [{"shot_id": "S1-1"}], "revision": 1}),
        )
        bind_manifest(self.session, manifest)
        return master, manifest

    def _record_structural_pass(self) -> None:
        for name in sorted(STRUCTURAL_CHECKS):
            record_check(self.session, name, True, self._file(f"reports/{name}.txt", "PASS"))

    def _to_batch_commit(self, total: int = 1) -> None:
        self._to_precheck(total)
        self._record_structural_pass()
        transition(self.session, BatchStage.DP_BATCH)
        record_dp_review(
            self.session, "ready", self._file("reports/DP.md", DP_READY_SENTENCE)
        )
        transition(self.session, BatchStage.FINAL_CHECK)
        record_check(
            self.session, "final_master_sync", True,
            self._file("reports/final_master_sync.txt", "PASS"),
        )
        transition(self.session, BatchStage.BATCH_COMMIT)

    def test_init_is_versioned_and_cannot_overwrite(self) -> None:
        state = init_state(self.session, 1, 2)
        self.assertEqual(state.schema_version, "1.1")
        self.assertTrue(state.state_sha256)
        with self.assertRaisesRegex(StateMachineError, "already exists"):
            init_state(self.session, 1, 2)

    def test_cannot_skip_or_enter_dp_without_exact_checks(self) -> None:
        self._to_precheck()
        with self.assertRaisesRegex(StateMachineError, "do not authorize"):
            transition(self.session, BatchStage.DP_BATCH)
        record_check(
            self.session, "master_compiler", True,
            self._file("reports/compiler.txt", "PASS"),
        )
        with self.assertRaisesRegex(StateMachineError, "do not authorize"):
            transition(self.session, BatchStage.DP_BATCH)

    def test_stale_master_invalidates_all_checks(self) -> None:
        master, _ = self._to_precheck()
        self._record_structural_pass()
        master.write_text("master-v2", encoding="utf-8")
        with self.assertRaisesRegex(StateMachineError, "Master changed"):
            transition(self.session, BatchStage.DP_BATCH)

    def test_tampered_structural_report_cannot_authorize_dp(self) -> None:
        self._to_precheck()
        self._record_structural_pass()
        (self.session / "reports/master_compiler.txt").write_text(
            "changed after pass", encoding="utf-8"
        )
        with self.assertRaisesRegex(StateMachineError, "report evidence changed"):
            transition(self.session, BatchStage.DP_BATCH)

    def test_dp_revise_returns_to_director_without_round_limit(self) -> None:
        self._to_precheck()
        self._record_structural_pass()
        transition(self.session, BatchStage.DP_BATCH)
        for attempt in range(12):
            record_dp_review(
                self.session, "revise",
                self._file(
                    f"reports/dp-{attempt}.md",
                    "S1-1: camera_path — The path intersects the desk.",
                ),
            )
            transition(self.session, BatchStage.DIRECTOR_BATCH)
            master = self._file("working/DIRECTOR_MASTER.md", f"master-{attempt + 2}")
            transition(self.session, BatchStage.STRUCTURAL_PRECHECK, master_path=master)
            manifest = self._file(
                "working/SHOT_MANIFEST.json",
                json.dumps({
                    "shots": [{"shot_id": "S1-1"}], "revision": attempt + 2
                }),
            )
            bind_manifest(self.session, manifest)
            self._record_structural_pass()
            transition(self.session, BatchStage.DP_BATCH)
        state = load_state(self.session)
        self.assertEqual(state.revision_count, 12)
        self.assertEqual(state.dp_attempts, 12)

    def test_empty_or_status_mismatched_dp_feedback_cannot_mutate_state(self) -> None:
        self._to_precheck()
        self._record_structural_pass()
        transition(self.session, BatchStage.DP_BATCH)
        with self.assertRaisesRegex(StateMachineError, "invalid DP feedback"):
            record_dp_review(self.session, "revise", self._file("reports/empty.md", ""))
        with self.assertRaisesRegex(StateMachineError, "does not match"):
            record_dp_review(
                self.session, "ready",
                self._file("reports/issues.md", "S1-1: camera_path — blocked."),
            )
        state = load_state(self.session)
        self.assertEqual(state.dp_attempts, 0)
        self.assertIsNone(state.dp_review)

    def test_same_issue_on_unchanged_master_pauses_without_round_limit(self) -> None:
        self._to_precheck()
        self._record_structural_pass()
        transition(self.session, BatchStage.DP_BATCH)
        record_dp_review(
            self.session, "revise",
            self._file("reports/first.md", "S1-1: camera_path — blocked by desk."),
        )
        transition(self.session, BatchStage.DIRECTOR_BATCH)
        # Director returned the exact same Master content, so a wording-only DP
        # change must not create another unproductive revision cycle.
        master = self._file("working/DIRECTOR_MASTER.md", "master-v1")
        transition(self.session, BatchStage.STRUCTURAL_PRECHECK, master_path=master)
        manifest = self._file(
            "working/SHOT_MANIFEST.json",
            json.dumps({"shots": [{"shot_id": "S1-1"}], "revision": 2}),
        )
        bind_manifest(self.session, manifest)
        self._record_structural_pass()
        transition(self.session, BatchStage.DP_BATCH)
        state = record_dp_review(
            self.session, "revise",
            self._file(
                "reports/second.md",
                "S1-1: camera_path — the desk still intersects this path.",
            ),
        )
        self.assertEqual(state.dp_review["status"], "blocked")
        self.assertTrue(state.dp_review["stalled"])
        self.assertEqual(state.dp_attempts, 2)
        self.assertEqual(len(state.dp_issue_history), 1)
        with self.assertRaisesRegex(StateMachineError, "revise evidence"):
            transition(self.session, BatchStage.DIRECTOR_BATCH)

    def test_dp_ready_and_final_evidence_authorize_commit(self) -> None:
        self._to_batch_commit()
        state = load_state(self.session)
        self.assertEqual(state.stage, "batch_commit")
        self.assertEqual(state.dp_attempts, 1)

    def test_tampered_dp_review_cannot_authorize_final_check(self) -> None:
        self._to_precheck()
        self._record_structural_pass()
        transition(self.session, BatchStage.DP_BATCH)
        review = self._file("reports/DP.md", DP_READY_SENTENCE)
        record_dp_review(self.session, "ready", review)
        review.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(StateMachineError, "DP review evidence changed"):
            transition(self.session, BatchStage.FINAL_CHECK)

    def test_tampered_final_report_cannot_authorize_commit(self) -> None:
        self._to_precheck()
        self._record_structural_pass()
        transition(self.session, BatchStage.DP_BATCH)
        record_dp_review(
            self.session, "ready", self._file("reports/DP.md", DP_READY_SENTENCE)
        )
        transition(self.session, BatchStage.FINAL_CHECK)
        report = self._file("reports/final_master_sync.txt", "PASS")
        record_check(self.session, "final_master_sync", True, report)
        report.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(StateMachineError, "report evidence changed"):
            transition(self.session, BatchStage.BATCH_COMMIT)

    def test_batch_commit_evidence_required_before_episode_review(self) -> None:
        self._to_batch_commit()
        with self.assertRaisesRegex(StateMachineError, "no commit evidence"):
            transition(self.session, BatchStage.EPISODE_REVIEW)
        record_batch_commit(self.session, self._file("commits/batch-1.json", "commit"))
        state = transition(self.session, BatchStage.EPISODE_REVIEW)
        self.assertEqual(state.stage, "episode_review")

    def test_two_batches_progress_sequentially(self) -> None:
        self._to_batch_commit(total=2)
        record_batch_commit(self.session, self._file("commits/batch-1.json", "commit-1"))
        transition(self.session, BatchStage.DIRECTOR_BATCH)
        self.assertEqual(load_state(self.session).batch_index, 2)
        master = self._file("working/DIRECTOR_MASTER.md", "master-b2")
        transition(self.session, BatchStage.STRUCTURAL_PRECHECK, master_path=master)
        manifest = self._file(
            "working/SHOT_MANIFEST.json",
            json.dumps({"shots": [{"shot_id": "S1-1"}], "revision": "b2"}),
        )
        bind_manifest(self.session, manifest)
        self._record_structural_pass()
        transition(self.session, BatchStage.DP_BATCH)
        record_dp_review(
            self.session, "ready", self._file("reports/dp-b2.md", DP_READY_SENTENCE)
        )
        transition(self.session, BatchStage.FINAL_CHECK)
        record_check(self.session, "final_master_sync", True, self._file("reports/final-b2", "PASS"))
        transition(self.session, BatchStage.BATCH_COMMIT)
        record_batch_commit(self.session, self._file("commits/batch-2.json", "commit-2"))
        transition(self.session, BatchStage.EPISODE_REVIEW)
        self.assertEqual(len(load_state(self.session).committed_batches), 2)

    def test_tampered_batch_commit_blocks_progress(self) -> None:
        self._to_batch_commit(total=2)
        evidence = self._file("commits/batch-1.json", "commit-1")
        record_batch_commit(self.session, evidence)
        evidence.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(StateMachineError, "commit evidence changed"):
            transition(self.session, BatchStage.DIRECTOR_BATCH)

    def test_episode_pass_must_bind_current_commits(self) -> None:
        self._to_batch_commit()
        record_batch_commit(self.session, self._file("commits/batch-1.json", "commit"))
        transition(self.session, BatchStage.EPISODE_REVIEW)
        with self.assertRaisesRegex(StateMachineError, "PASS evidence"):
            transition(self.session, BatchStage.DELIVERY)
        record_episode_review(self.session, "pass", self._file("reports/episode.md", "PASS"))
        transition(self.session, BatchStage.DELIVERY)
        self.assertTrue(is_complete(self.session))

    def test_tampered_episode_review_blocks_delivery(self) -> None:
        self._to_batch_commit()
        record_batch_commit(self.session, self._file("commits/batch-1.json", "commit"))
        transition(self.session, BatchStage.EPISODE_REVIEW)
        review = self._file("reports/episode.md", "PASS")
        record_episode_review(self.session, "pass", review)
        review.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(StateMachineError, "episode review evidence changed"):
            transition(self.session, BatchStage.DELIVERY)

    def test_tampered_state_fails_integrity_check(self) -> None:
        init_state(self.session, 1, 1)
        path = self.session / "RUN_STATE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["stage"] = "delivery"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(StateMachineError, "integrity hash mismatch"):
            load_state(self.session)

    def test_evidence_outside_session_is_rejected(self) -> None:
        init_state(self.session, 1, 1)
        transition(self.session, BatchStage.SCRIPT_PARSE)
        transition(self.session, BatchStage.DIRECTOR_BATCH)
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("master", encoding="utf-8")
        with self.assertRaisesRegex(StateMachineError, "inside session"):
            transition(self.session, BatchStage.STRUCTURAL_PRECHECK, master_path=outside)


class CLITests(unittest.TestCase):
    def test_cli_init_and_show(self) -> None:
        with tempfile.TemporaryDirectory(prefix=f"mode_p_state_cli_{os.getpid()}_") as temp:
            session = Path(temp) / "session"
            init = subprocess.run(
                [sys.executable, "-m", "batch_state_machine", "init", str(session)],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            show = subprocess.run(
                [sys.executable, "-m", "batch_state_machine", "show", str(session)],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertEqual(json.loads(show.stdout)["stage"], "bootstrap")


if __name__ == "__main__":
    unittest.main()
