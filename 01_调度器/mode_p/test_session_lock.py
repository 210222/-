"""Regression tests for exclusive writes and directory-level commits."""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from batch_state_machine import init_state
from session_lock import (
    LockError,
    commit,
    prepare_staging,
    recover,
    rollback,
    session_lock,
    verify_commit,
)


class SessionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mode_p_commit_"))
        init_state(self.tmp, 1, 1)

    def source(self, name: str, content: str) -> Path:
        path = self.tmp / f"source-{name}"
        path.write_text(content, encoding="utf-8")
        return path


class LockTests(SessionTestCase):
    def test_acquire_release_and_live_owner_exclusion(self) -> None:
        with session_lock(self.tmp):
            self.assertTrue((self.tmp / "SESSION.lock").is_file())
            with self.assertRaises(LockError):
                with session_lock(self.tmp):
                    pass
        self.assertFalse((self.tmp / "SESSION.lock").exists())

    def test_dead_owner_lock_is_recovered(self) -> None:
        record = {
            "schema_version": "1.0",
            "pid": 2_147_483_647,
            "token": "dead-owner",
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        (self.tmp / "SESSION.lock").write_text(json.dumps(record), encoding="utf-8")
        with session_lock(self.tmp):
            current = json.loads((self.tmp / "SESSION.lock").read_text(encoding="utf-8"))
            self.assertEqual(current["pid"], os.getpid())

    def test_malformed_fresh_lock_is_not_stolen(self) -> None:
        (self.tmp / "SESSION.lock").write_text("", encoding="utf-8")
        with self.assertRaises(LockError):
            with session_lock(self.tmp):
                pass

    def test_wait_timeout_is_bounded(self) -> None:
        started = time.monotonic()
        with session_lock(self.tmp):
            with self.assertRaises(LockError):
                with session_lock(self.tmp, timeout=0.06):
                    pass
        self.assertLess(time.monotonic() - started, 0.5)


class StagingTests(SessionTestCase):
    def test_unique_transaction_and_nested_copy(self) -> None:
        stage = prepare_staging(
            self.tmp,
            {"scenes/S1/DIRECTOR_MASTER.md": self.source("master.md", "master")},
            "tx-one",
        )
        self.assertEqual(stage.name, "tx-one")
        self.assertEqual(
            (stage / "scenes" / "S1" / "DIRECTOR_MASTER.md").read_text(encoding="utf-8"),
            "master",
        )

    def test_empty_traversal_absolute_and_duplicate_paths_fail(self) -> None:
        source = self.source("a.md", "a")
        with self.assertRaises(LockError):
            prepare_staging(self.tmp, {})
        with self.assertRaises(LockError):
            prepare_staging(self.tmp, {"../outside.md": source})
        with self.assertRaises(LockError):
            prepare_staging(self.tmp, {str(source.resolve()): source})
        with self.assertRaises(LockError):
            prepare_staging(self.tmp, {"A.md": source, "a.md": source})

    def test_missing_source_and_duplicate_transaction_fail(self) -> None:
        with self.assertRaises(LockError):
            prepare_staging(self.tmp, {"x.md": self.tmp / "missing"})
        prepare_staging(self.tmp, {"x.md": self.source("x.md", "x")}, "same")
        with self.assertRaises(LockError):
            prepare_staging(self.tmp, {"y.md": self.source("y.md", "y")}, "same")


class CommitTests(SessionTestCase):
    def stage(self, transaction: str, content: str = "v1") -> None:
        prepare_staging(
            self.tmp,
            {
                "STORYBOARD.md": self.source(f"{transaction}-story.md", content),
                "VIDEO_PROMPT.md": self.source(f"{transaction}-video.md", content),
            },
            transaction,
        )

    def test_commit_publishes_one_complete_directory_and_manifest(self) -> None:
        self.stage("tx1")
        manifest = commit(self.tmp, "batch_commit", 1, "tx1")
        self.assertEqual(manifest.total_files, 2)
        self.assertTrue((self.tmp / "working" / "STORYBOARD.md").is_file())
        self.assertTrue((self.tmp / "working" / "COMMIT_MANIFEST.json").is_file())
        ok, issues = verify_commit(self.tmp)
        self.assertTrue(ok, issues)

    def test_second_commit_replaces_directory_without_mixing_versions(self) -> None:
        self.stage("tx1", "v1")
        commit(self.tmp, "batch_commit", 1, "tx1")
        prepare_staging(
            self.tmp,
            {"ONLY_NEW.md": self.source("new.md", "v2")},
            "tx2",
        )
        commit(self.tmp, "batch_commit", 1, "tx2")
        self.assertFalse((self.tmp / "working" / "STORYBOARD.md").exists())
        self.assertEqual((self.tmp / "working" / "ONLY_NEW.md").read_text(encoding="utf-8"), "v2")
        self.assertFalse(any(self.tmp.glob(".working.backup-*")))

    def test_delivery_target_is_separate_and_verifiable(self) -> None:
        self.stage("delivery-tx")
        commit(self.tmp, "delivery", 1, "delivery-tx", target="delivery")
        self.assertTrue((self.tmp / "delivery" / "STORYBOARD.md").is_file())
        ok, issues = verify_commit(self.tmp, "delivery")
        self.assertTrue(ok, issues)

    def test_ambiguous_transaction_requires_id(self) -> None:
        self.stage("one")
        self.stage("two")
        with self.assertRaises(LockError):
            commit(self.tmp, "batch_commit", 1)

    def test_content_manifest_and_untracked_tampering_are_detected(self) -> None:
        self.stage("tx1")
        commit(self.tmp, "batch_commit", 1, "tx1")
        (self.tmp / "working" / "STORYBOARD.md").write_text("tampered", encoding="utf-8")
        ok, issues = verify_commit(self.tmp)
        self.assertFalse(ok)
        self.assertTrue(any("MISMATCH" in issue for issue in issues))
        (self.tmp / "working" / "extra.md").write_text("extra", encoding="utf-8")
        ok, issues = verify_commit(self.tmp)
        self.assertFalse(ok)
        self.assertTrue(any("UNTRACKED" in issue for issue in issues))

    def test_root_manifest_tampering_is_detected(self) -> None:
        self.stage("tx1")
        commit(self.tmp, "batch_commit", 1, "tx1")
        path = self.tmp / "COMMIT_MANIFEST.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["stage"] = "forged"
        path.write_text(json.dumps(raw), encoding="utf-8")
        ok, issues = verify_commit(self.tmp)
        self.assertFalse(ok)
        self.assertTrue(any("integrity" in issue for issue in issues))

    def test_manifest_records_state_and_implementation_fingerprints(self) -> None:
        state_path = self.tmp / "RUN_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["checks"] = {"master_compiler": {}}
        state.pop("state_sha256")
        payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        state["state_sha256"] = __import__("hashlib").sha256(payload).hexdigest()
        state_path.write_text(json.dumps(state), encoding="utf-8")
        self.stage("tx1")
        manifest = commit(self.tmp, "batch_commit", 1, "tx1")
        self.assertEqual(manifest.state_sha256, state["state_sha256"])
        self.assertIn("master_compiler", manifest.implementation_fingerprints)

    def test_recovery_restores_previous_complete_target(self) -> None:
        self.stage("tx1")
        commit(self.tmp, "batch_commit", 1, "tx1")
        backup = self.tmp / ".working.backup-interrupted"
        (self.tmp / "working").replace(backup)
        pending = {
            "schema_version": "1.0",
            "transaction_id": "interrupted",
            "target": "working",
            "backup": backup.name,
        }
        (self.tmp / ".COMMIT_PENDING.json").write_text(json.dumps(pending), encoding="utf-8")
        recover(self.tmp)
        ok, issues = verify_commit(self.tmp)
        self.assertTrue(ok, issues)
        self.assertFalse(backup.exists())

    def test_rollback_discards_only_uncommitted_staging(self) -> None:
        self.stage("committed")
        commit(self.tmp, "batch_commit", 1, "committed")
        self.stage("unfinished", "v2")
        rollback(self.tmp)
        self.assertFalse((self.tmp / "staging").exists())
        ok, issues = verify_commit(self.tmp)
        self.assertTrue(ok, issues)


if __name__ == "__main__":
    unittest.main()
