"""R2.2 engineering CLI and durable session regression tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mode_p_vnext import session_state as state_module
from mode_p_vnext.session_state import (
    InvalidStateTransition,
    PersistentSession,
    SessionStateError,
)


DISPATCHER_ROOT = Path(__file__).resolve().parents[2]


class EngineeringCliTests(unittest.TestCase):
    def _module(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, "-B", "-m", "mode_p_vnext", *arguments],
            cwd=DISPATCHER_ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_module_help_is_available_without_writing_a_session(self):
        result = self._module("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("engineering CLI", result.stdout)
        self.assertIn("shadow", result.stdout)

    def test_cli_persists_reloads_and_audits_an_explicit_transition(self):
        with tempfile.TemporaryDirectory() as temporary:
            session_dir = Path(temporary) / "episode-35-scene-2"
            created = self._module(
                "session",
                "init",
                "--session-dir",
                str(session_dir),
                "--scope",
                "scene",
                "--episode-id",
                "EP35",
                "--scene-id",
                "S2",
                "--artifact-hash",
                "script=" + "a" * 64,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertEqual(json.loads(created.stdout)["session"]["state"], "NEW")

            advanced = self._module(
                "session",
                "transition",
                "--session-dir",
                str(session_dir),
                "--to",
                "FACTS_BOUND",
                "--reason-code",
                "SCRIPT_FACTS_BOUND",
                "--input-commit-id",
                "input-001",
                "--output-commit-id",
                "output-001",
                "--correlation-id",
                "corr-001",
                "--artifact-hash",
                "facts=" + "b" * 64,
            )
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            payload = json.loads(advanced.stdout)
            self.assertEqual(payload["session"]["state"], "FACTS_BOUND")
            self.assertEqual(payload["session"]["current_commit_id"], "output-001")

            reloaded = self._module("session", "status", "--session-dir", str(session_dir))
            self.assertEqual(reloaded.returncode, 0, reloaded.stderr)
            snapshot = json.loads(reloaded.stdout)["session"]
            self.assertEqual(snapshot["state"], "FACTS_BOUND")
            self.assertEqual(snapshot["artifact_hashes"], {"facts": "b" * 64})
            self.assertEqual(snapshot["event_count"], 2)

            events = [
                json.loads(line)
                for line in (session_dir / "STATE_EVENTS.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(events), 2)
            required = {
                "event_id",
                "timestamp_utc",
                "episode_id",
                "scene_id",
                "from_state",
                "to_state",
                "actor",
                "reason_code",
                "input_commit_id",
                "output_commit_id",
                "correlation_id",
            }
            self.assertTrue(required.issubset(events[-1]))
            self.assertEqual(events[-1]["from_state"], "NEW")
            self.assertEqual(events[-1]["to_state"], "FACTS_BOUND")

    def test_invalid_transition_fails_closed_and_does_not_append_an_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = PersistentSession.create(
                Path(temporary) / "scene",
                "EP1",
                "S1",
                scope="scene",
            )
            before = session.status().event_count
            with self.assertRaises(InvalidStateTransition):
                session.transition(
                    "MASTER_DRAFTED",
                    actor="test",
                    reason_code="INVALID_SHORTCUT",
                )
            self.assertEqual(session.status().event_count, before)

    def test_v4_protected_session_target_is_rejected(self):
        protected = DISPATCHER_ROOT / "mode_p" / "sessions" / "must-not-write"
        with self.assertRaises(SessionStateError):
            PersistentSession.create(protected, "EP1", "S1", scope="scene")

    def test_corrupt_state_fails_closed_instead_of_inferring_state_from_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "scene"
            PersistentSession.create(root, "EP1", "S1", scope="scene")
            (root / "SESSION_STATE.json").write_text("{not-json", encoding="utf-8")
            with self.assertRaises(SessionStateError):
                PersistentSession.open(root)

    def test_open_recovers_a_durable_transition_event_not_yet_reflected_in_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "scene"
            session = PersistentSession.create(root, "EP1", "S1", scope="scene")
            record = json.loads((root / "SESSION_STATE.json").read_text(encoding="utf-8"))
            event = session._event(
                record,
                from_state="NEW",
                to_state="FACTS_BOUND",
                actor="test",
                reason_code="RECOVERY_FAULT_INJECTION",
                input_commit_id="",
                output_commit_id="commit-recovered",
                correlation_id="corr-recovery",
                artifact_hashes={"facts": "c" * 64},
            )
            # Simulate a process failure after durable append and before the
            # atomic state snapshot replacement.
            state_module._append_event(root / "STATE_EVENTS.jsonl", event)
            recovered = PersistentSession.open(root).status()
            self.assertEqual(recovered.state, "FACTS_BOUND")
            self.assertEqual(recovered.current_commit_id, "commit-recovered")
            self.assertEqual(recovered.event_count, 2)


if __name__ == "__main__":
    unittest.main()
