"""Behavior tests for the vNext deterministic rebuild control plane."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mode_p_vnext.rebuild_control import (
    ControlError,
    LOCK_REL,
    RebuildControl,
    STATE_REL,
    TASKS_REL,
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class RebuildControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="vnext_rebuild_control_")
        self.root = Path(self.temp.name)
        self.tasks = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status_after_all": "V_TASK_REVALIDATION_REQUIRED",
            "tasks": [
                {
                    "task_id": "R0.1",
                    "title": "首个任务",
                    "depends_on": [],
                    "spec_refs": ["spec"],
                    "allowed_paths": ["work/**", "evidence/**"],
                    "required_checks": ["focused", "regression"],
                    "verification_commands": [
                        {
                            "name": "focused",
                            "argv": ["{python}", "-c", "raise SystemExit(0)"],
                            "cwd": ".",
                            "timeout_seconds": 30,
                        }
                    ],
                },
                {
                    "task_id": "R0.2",
                    "title": "second",
                    "depends_on": ["R0.1"],
                    "spec_refs": ["spec"],
                    "allowed_paths": ["work/**", "evidence/**"],
                    "required_checks": ["focused"],
                    "verification_commands": [
                        {
                            "name": "focused",
                            "argv": ["{python}", "-c", "raise SystemExit(0)"],
                            "cwd": ".",
                            "timeout_seconds": 30,
                        }
                    ],
                },
            ],
        }
        self.state = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status": "REPAIR_REQUIRED",
            "current_task": None,
            "current_owner": None,
            "lock_token": None,
            "completed_tasks": [],
            "evidence_records": {},
            "last_failure": None,
            "next_task": "R0.1",
            "production_entry": "v4_unchanged",
        }
        _write_json(self.root / TASKS_REL, self.tasks)
        _write_json(self.root / STATE_REL, self.state)
        artifact = self.root / "work/module.py"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("initial", encoding="utf-8")
        self.control = RebuildControl(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _evidence(self, task_id: str, *, failed: bool = False) -> Path:
        path = self.root / "evidence" / f"{task_id}.json"
        checks = [
            {"name": "focused", "exit_code": 1 if failed else 0},
            {"name": "regression", "exit_code": 0},
        ]
        _write_json(
            path,
            {
                "task_id": task_id,
                "changed_paths": ["work/module.py", f"evidence/{task_id}.json"],
                "checks": checks,
            },
        )
        return path

    def test_task_graph_and_initial_state_audit(self) -> None:
        self.assertEqual(self.control.audit(), [])
        self.assertEqual(self.control.next_task().task_id, "R0.1")

    def test_missing_dependency_is_rejected(self) -> None:
        self.tasks["tasks"][1]["depends_on"] = ["MISSING"]
        _write_json(self.root / TASKS_REL, self.tasks)
        issues = self.control.audit()
        self.assertTrue(any("missing dependency" in issue for issue in issues))

    def test_atomic_claim_rejects_second_writer(self) -> None:
        lock = self.control.claim("R0.1", "owner-a")
        self.assertTrue((self.root / LOCK_REL).exists())
        with self.assertRaises(ControlError):
            self.control.claim("R0.1", "owner-b")
        state = self.control.load_state()
        self.assertEqual(state["lock_token"], lock["token"])

    def test_wrong_owner_or_token_cannot_complete(self) -> None:
        lock = self.control.claim("R0.1", "owner-a")
        evidence = self._evidence("R0.1")
        with self.assertRaises(ControlError):
            self.control.complete("R0.1", "owner-b", lock["token"], evidence)
        with self.assertRaises(ControlError):
            self.control.complete("R0.1", "owner-a", "wrong", evidence)

    def test_completion_requires_all_checks_to_pass(self) -> None:
        lock = self.control.claim("R0.1", "owner-a")
        with self.assertRaises(ControlError):
            self.control.complete(
                "R0.1", "owner-a", lock["token"], self._evidence("R0.1", failed=True)
            )
        self.assertTrue((self.root / LOCK_REL).exists())

    def test_completion_executes_authoritative_verification_command(self) -> None:
        self.tasks["tasks"][0]["verification_commands"][0]["argv"] = [
            "{python}",
            "-c",
            "raise SystemExit(7)",
        ]
        _write_json(self.root / TASKS_REL, self.tasks)
        lock = self.control.claim("R0.1", "owner-a")
        with self.assertRaisesRegex(ControlError, "verification command failed"):
            self.control.complete(
                "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
            )
        self.assertTrue((self.root / LOCK_REL).exists())

    def test_completion_records_hashed_evidence_and_advances(self) -> None:
        lock = self.control.claim("R0.1", "owner-a")
        state = self.control.complete(
            "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
        )
        self.assertEqual(state["completed_tasks"], ["R0.1"])
        self.assertEqual(state["next_task"], "R0.2")
        self.assertEqual(state["status"], "REPAIR_REQUIRED")
        self.assertFalse((self.root / LOCK_REL).exists())
        self.assertEqual(len(state["evidence_records"]["R0.1"]["sha256"]), 64)
        self.assertEqual(
            state["evidence_records"]["R0.1"]["verification_results"][0][
                "exit_code"
            ],
            0,
        )
        self.assertEqual(
            len(
                state["evidence_records"]["R0.1"]["artifact_hashes"][
                    "work/module.py"
                ]
            ),
            64,
        )

    def test_audit_detects_completed_artifact_drift(self) -> None:
        artifact = self.root / "work/module.py"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("before", encoding="utf-8")
        lock = self.control.claim("R0.1", "owner-a")
        self.control.complete(
            "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
        )
        artifact.write_text("after", encoding="utf-8")
        self.assertTrue(
            any("artifact drift" in issue for issue in self.control.audit())
        )

    def test_invalidate_reopens_completed_task_with_audit_trail(self) -> None:
        lock = self.control.claim("R0.1", "owner-a")
        self.control.complete(
            "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
        )
        state = self.control.invalidate(
            "R0.1", owner="auditor", reason="post-completion regression"
        )
        self.assertEqual(state["completed_tasks"], [])
        self.assertEqual(state["next_task"], "R0.1")
        self.assertEqual(state["invalidated_records"][-1]["task_id"], "R0.1")
        self.assertEqual(self.control.claim("R0.1", "owner-b")["owner"], "owner-b")

    def test_completion_rejects_out_of_scope_path(self) -> None:
        lock = self.control.claim("R0.1", "owner-a")
        evidence = self._evidence("R0.1")
        value = json.loads(evidence.read_text(encoding="utf-8"))
        value["changed_paths"].append("01_调度器/mode_p/production.py")
        _write_json(evidence, value)
        with self.assertRaises(ControlError):
            self.control.complete("R0.1", "owner-a", lock["token"], evidence)

    def test_completed_task_without_evidence_is_audit_failure(self) -> None:
        self.state["completed_tasks"] = ["R0.1"]
        self.state["next_task"] = "R0.2"
        _write_json(self.root / STATE_REL, self.state)
        issues = self.control.audit()
        self.assertIn("completed task R0.1 lacks evidence record", issues)

    def test_fail_releases_lock_and_keeps_task_next(self) -> None:
        lock = self.control.claim("R0.1", "owner-a")
        state = self.control.fail("R0.1", "owner-a", lock["token"], None)
        self.assertEqual(state["status"], "REPAIR_REQUIRED")
        self.assertEqual(state["next_task"], "R0.1")
        self.assertFalse((self.root / LOCK_REL).exists())

    def test_real_cli_emits_utf8_json(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mode_p_vnext.rebuild_control",
                "--project-root",
                str(self.root),
                "next",
            ],
            cwd=str(Path(__file__).resolve().parents[2]),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["task_id"], "R0.1")
        self.assertEqual(payload["title"], "首个任务")
        self.assertIn("work/**", payload["allowed_paths"])


class LockedVerificationInputTests(unittest.TestCase):
    """Tests for locked_verification_inputs: claim, complete, audit."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="vnext_locked_")
        self.root = Path(self.temp.name)
        # Create locked gate file outside worker paths.
        locked_dir = self.root / "MODE_P_REDESIGN_PROJECT/vnext_acceptance"
        locked_dir.mkdir(parents=True, exist_ok=True)
        self.locked_file = locked_dir / "locked_gate.py"
        self.locked_file.write_text("locked content v1", encoding="utf-8")
        self.locked_hash = _sha256_file(self.locked_file)
        self.locked_rel = (
            "MODE_P_REDESIGN_PROJECT/vnext_acceptance/locked_gate.py"
        )

        self.tasks = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status_after_all": "V_TASK_REVALIDATION_REQUIRED",
            "tasks": [
                {
                    "task_id": "R0.1",
                    "title": "controller task",
                    "depends_on": [],
                    "spec_refs": ["spec"],
                    "allowed_paths": ["work/**", "evidence/**"],
                    "required_checks": ["focused"],
                    "locked_verification_inputs": {
                        self.locked_rel: self.locked_hash,
                    },
                    "verification_commands": [
                        {
                            "name": "focused",
                            "argv": ["{python}", "-c", "raise SystemExit(0)"],
                            "cwd": ".",
                            "timeout_seconds": 30,
                        }
                    ],
                },
            ],
        }
        self.state = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status": "REPAIR_REQUIRED",
            "current_task": None,
            "current_owner": None,
            "lock_token": None,
            "completed_tasks": [],
            "evidence_records": {},
            "last_failure": None,
            "next_task": "R0.1",
            "production_entry": "v4_unchanged",
        }
        _write_json(self.root / TASKS_REL, self.tasks)
        _write_json(self.root / STATE_REL, self.state)
        artifact = self.root / "work/module.py"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("initial", encoding="utf-8")
        self.control = RebuildControl(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _evidence(self, task_id: str) -> Path:
        path = self.root / "evidence" / f"{task_id}.json"
        _write_json(
            path,
            {
                "task_id": task_id,
                "changed_paths": ["work/module.py", f"evidence/{task_id}.json"],
                "checks": [{"name": "focused", "exit_code": 0}],
            },
        )
        return path

    def test_locked_input_correctly_passes_claim(self):
        """Locked input with correct hash allows claim."""
        lock = self.control.claim("R0.1", "owner-a")
        self.assertIsNotNone(lock["token"])

    def test_locked_input_hash_drift_blocks_claim(self):
        """Locked input with wrong hash blocks claim."""
        self.locked_file.write_text("tampered content", encoding="utf-8")
        with self.assertRaises(ControlError):
            self.control.claim("R0.1", "owner-a")

    def test_locked_input_missing_file_blocks_claim(self):
        """Missing locked input file blocks claim."""
        self.locked_file.unlink()
        with self.assertRaises(ControlError):
            self.control.claim("R0.1", "owner-a")

    def test_locked_input_hash_drift_blocks_complete(self):
        """Locked input tampered after claim blocks complete."""
        lock = self.control.claim("R0.1", "owner-a")
        self.locked_file.write_text("post-claim tamper", encoding="utf-8")
        with self.assertRaises(ControlError):
            self.control.complete(
                "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
            )

    def test_locked_input_worker_writable_is_rejected(self):
        """Locked input that matches worker allowed_paths is rejected at load."""
        bad_tasks = json.loads(json.dumps(self.tasks))
        bad_tasks["tasks"][0]["locked_verification_inputs"] = {
            "work/module.py": "a" * 64,
        }
        _write_json(self.root / TASKS_REL, bad_tasks)
        with self.assertRaises(ControlError):
            self.control.load_tasks()

    def test_state_records_verification_input_hashes(self):
        """After complete, state record contains verification_input_hashes."""
        lock = self.control.claim("R0.1", "owner-a")
        state = self.control.complete(
            "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
        )
        record = state["evidence_records"]["R0.1"]
        self.assertIn("verification_input_hashes", record)
        self.assertEqual(
            record["verification_input_hashes"][self.locked_rel],
            self.locked_hash,
        )

    def test_empty_locked_inputs_is_ok(self):
        """Task without locked_verification_inputs should still work."""
        tasks_no_lock = json.loads(json.dumps(self.tasks))
        del tasks_no_lock["tasks"][0]["locked_verification_inputs"]
        _write_json(self.root / TASKS_REL, tasks_no_lock)
        control = RebuildControl(self.root)
        lock = control.claim("R0.1", "owner-a")
        state = control.complete(
            "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
        )
        self.assertIn("R0.1", state["completed_tasks"])


class WorkspaceDeltaTests(unittest.TestCase):
    """Tests for claim-time manifest and complete-time delta detection.

    All test work files are created under MODE_P_REDESIGN_PROJECT/
    which is a supervised root in _SUPERVISED_ROOTS.
    """

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="vnext_delta_")
        self.root = Path(self.temp.name)
        # Work dir under supervised root MODE_P_REDESIGN_PROJECT/
        work_dir = self.root / "MODE_P_REDESIGN_PROJECT/test_work"
        work_dir.mkdir(parents=True, exist_ok=True)
        self.work_file = work_dir / "module.py"
        self.work_file.write_text("initial", encoding="utf-8")
        # Evidence dir
        ev_dir = self.root / "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence"
        ev_dir.mkdir(parents=True, exist_ok=True)

        self.tasks = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status_after_all": "V_TASK_REVALIDATION_REQUIRED",
            "tasks": [
                {
                    "task_id": "R0.1",
                    "title": "test",
                    "depends_on": [],
                    "spec_refs": ["spec"],
                    "allowed_paths": [
                        "MODE_P_REDESIGN_PROJECT/test_work/**",
                        "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/**",
                    ],
                    "required_checks": ["focused"],
                    "verification_commands": [
                        {
                            "name": "focused",
                            "argv": ["{python}", "-c", "raise SystemExit(0)"],
                            "cwd": ".",
                            "timeout_seconds": 30,
                        }
                    ],
                },
            ],
        }
        self.state = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status": "REPAIR_REQUIRED",
            "current_task": None,
            "current_owner": None,
            "lock_token": None,
            "completed_tasks": [],
            "evidence_records": {},
            "last_failure": None,
            "next_task": "R0.1",
            "production_entry": "v4_unchanged",
        }
        _write_json(self.root / TASKS_REL, self.tasks)
        _write_json(self.root / STATE_REL, self.state)
        self.control = RebuildControl(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _evidence(self, task_id: str, extra_paths=None) -> Path:
        path = self.root / "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence" / f"{task_id}.json"
        changed = [
            "MODE_P_REDESIGN_PROJECT/test_work/module.py",
            f"MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/{task_id}.json",
        ]
        if extra_paths:
            changed.extend(extra_paths)
        _write_json(
            path,
            {
                "task_id": task_id,
                "changed_paths": changed,
                "checks": [{"name": "focused", "exit_code": 0}],
            },
        )
        return path

    def test_undeclared_allowed_file_change_blocks_complete(self):
        """Creating undeclared file in supervised root blocks complete."""
        lock = self.control.claim("R0.1", "owner-a")
        # Modify declared file.
        self.work_file.write_text("modified", encoding="utf-8")
        # Create an extra file — not declared in evidence.
        extra = self.root / "MODE_P_REDESIGN_PROJECT/test_work/extra.py"
        extra.write_text("undeclared", encoding="utf-8")
        with self.assertRaises(ControlError):
            self.control.complete(
                "R0.1", "owner-a", lock["token"],
                self._evidence("R0.1")
            )

    def test_out_of_scope_create_blocks_complete(self):
        """Creating a file outside allowed_paths blocks complete."""
        lock = self.control.claim("R0.1", "owner-a")
        out_of_scope = self.root / "MODE_P_REDESIGN_PROJECT/forbidden.py"
        out_of_scope.parent.mkdir(parents=True, exist_ok=True)
        out_of_scope.write_text("forbidden", encoding="utf-8")
        with self.assertRaises(ControlError):
            self.control.complete(
                "R0.1", "owner-a", lock["token"],
                self._evidence("R0.1", extra_paths=["MODE_P_REDESIGN_PROJECT/forbidden.py"])
            )

    def test_out_of_scope_delete_blocks_complete(self):
        """Deleting a file in supervised root blocks complete."""
        # Create file before claim so it's in manifest.
        extra = self.root / "MODE_P_REDESIGN_PROJECT/delete_me.py"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("to be deleted", encoding="utf-8")
        lock = self.control.claim("R0.1", "owner-a")
        self.work_file.write_text("modified", encoding="utf-8")
        extra.unlink()
        with self.assertRaises(ControlError):
            self.control.complete(
                "R0.1", "owner-a", lock["token"],
                self._evidence("R0.1")
            )

    def test_declared_but_unchanged_artifact_can_rebind(self):
        """Evidence can declare an unchanged file for re-binding."""
        unchanged = self.root / "MODE_P_REDESIGN_PROJECT/test_work/unchanged.py"
        unchanged.write_text("unchanged content", encoding="utf-8")
        lock = self.control.claim("R0.1", "owner-a")
        self.work_file.write_text("modified", encoding="utf-8")
        evidence = self._evidence("R0.1", extra_paths=[
            "MODE_P_REDESIGN_PROJECT/test_work/unchanged.py"
        ])
        state = self.control.complete(
            "R0.1", "owner-a", lock["token"], evidence
        )
        self.assertIn("R0.1", state["completed_tasks"])
        self.assertIn(
            "MODE_P_REDESIGN_PROJECT/test_work/unchanged.py",
            state["evidence_records"]["R0.1"]["artifact_hashes"],
        )

    def test_cache_and_state_changes_dont_false_positive(self):
        """Changes to __pycache__ don't block complete."""
        lock = self.control.claim("R0.1", "owner-a")
        self.work_file.write_text("modified", encoding="utf-8")
        # Create cache files — should be excluded.
        cache_dir = self.root / "MODE_P_REDESIGN_PROJECT/__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "module.cpython-312.pyc").write_text("cache", encoding="utf-8")
        state = self.control.complete(
            "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
        )
        self.assertIn("R0.1", state["completed_tasks"])


class EvidenceAuthorityTests(unittest.TestCase):
    """Tests for evidence layering: verification_results authority."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="vnext_evidence_")
        self.root = Path(self.temp.name)
        work_dir = self.root / "work"
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "module.py").write_text("initial", encoding="utf-8")

        self.tasks = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status_after_all": "V_TASK_REVALIDATION_REQUIRED",
            "tasks": [
                {
                    "task_id": "R0.1",
                    "title": "test",
                    "depends_on": [],
                    "spec_refs": ["spec"],
                    "allowed_paths": ["work/**", "evidence/**"],
                    "required_checks": ["focused"],
                    "verification_commands": [
                        {
                            "name": "focused_only",
                            "argv": ["{python}", "-c", "raise SystemExit(0)"],
                            "cwd": ".",
                            "timeout_seconds": 30,
                        }
                    ],
                },
            ],
        }
        self.state = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status": "REPAIR_REQUIRED",
            "current_task": None,
            "current_owner": None,
            "lock_token": None,
            "completed_tasks": [],
            "evidence_records": {},
            "last_failure": None,
            "next_task": "R0.1",
            "production_entry": "v4_unchanged",
        }
        _write_json(self.root / TASKS_REL, self.tasks)
        _write_json(self.root / STATE_REL, self.state)
        self.control = RebuildControl(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_evidence_unregistered_verification_result_blocked(self):
        """Evidence verification_results with name not in registry blocks."""
        lock = self.control.claim("R0.1", "owner-a")
        evidence = self.root / "evidence" / "R0.1.json"
        _write_json(
            evidence,
            {
                "task_id": "R0.1",
                "changed_paths": ["work/module.py", "evidence/R0.1.json"],
                "checks": [{"name": "focused", "exit_code": 0}],
                "verification_results": [
                    {"name": "not_in_registry", "exit_code": 0},
                ],
            },
        )
        with self.assertRaises(ControlError):
            self.control.complete("R0.1", "owner-a", lock["token"], evidence)

    def test_evidence_registered_verification_result_accepted(self):
        """Evidence verification_results matching registry are accepted."""
        lock = self.control.claim("R0.1", "owner-a")
        evidence = self.root / "evidence" / "R0.1.json"
        _write_json(
            evidence,
            {
                "task_id": "R0.1",
                "changed_paths": ["work/module.py", "evidence/R0.1.json"],
                "checks": [{"name": "focused", "exit_code": 0}],
                "verification_results": [
                    {"name": "focused_only", "exit_code": 0},
                ],
            },
        )
        state = self.control.complete("R0.1", "owner-a", lock["token"], evidence)
        self.assertIn("R0.1", state["completed_tasks"])

    def test_informational_results_must_have_authority_marker(self):
        """informational_results without authority marker are rejected."""
        lock = self.control.claim("R0.1", "owner-a")
        evidence = self.root / "evidence" / "R0.1.json"
        _write_json(
            evidence,
            {
                "task_id": "R0.1",
                "changed_paths": ["work/module.py", "evidence/R0.1.json"],
                "checks": [{"name": "focused", "exit_code": 0}],
                "informational_results": [
                    {"name": "manual_test", "exit_code": 0},
                ],
            },
        )
        with self.assertRaises(ControlError):
            self.control.complete("R0.1", "owner-a", lock["token"], evidence)

    def test_informational_results_with_correct_authority_accepted(self):
        """informational_results with correct authority marker are accepted."""
        lock = self.control.claim("R0.1", "owner-a")
        evidence = self.root / "evidence" / "R0.1.json"
        _write_json(
            evidence,
            {
                "task_id": "R0.1",
                "changed_paths": ["work/module.py", "evidence/R0.1.json"],
                "checks": [{"name": "focused", "exit_code": 0}],
                "informational_results": [
                    {
                        "name": "manual_r1_3",
                        "exit_code": 0,
                        "authority": "manual_untrusted_until_controller_or_supervisor_audit",
                    },
                ],
            },
        )
        state = self.control.complete("R0.1", "owner-a", lock["token"], evidence)
        self.assertIn("R0.1", state["completed_tasks"])


class AuditLockedInputDriftTests(unittest.TestCase):
    """Tests that audit detects post-completion locked input drift."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="vnext_audit_drift_")
        self.root = Path(self.temp.name)
        work_dir = self.root / "work"
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "module.py").write_text("initial", encoding="utf-8")

        locked_dir = self.root / "MODE_P_REDESIGN_PROJECT/vnext_acceptance"
        locked_dir.mkdir(parents=True, exist_ok=True)
        self.locked_file = locked_dir / "locked_gate.py"
        self.locked_file.write_text("locked v1", encoding="utf-8")
        self.locked_hash = _sha256_file(self.locked_file)
        self.locked_rel = (
            "MODE_P_REDESIGN_PROJECT/vnext_acceptance/locked_gate.py"
        )

        self.tasks = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status_after_all": "V_TASK_REVALIDATION_REQUIRED",
            "tasks": [
                {
                    "task_id": "R0.1",
                    "title": "test",
                    "depends_on": [],
                    "spec_refs": ["spec"],
                    "allowed_paths": ["work/**", "evidence/**"],
                    "required_checks": ["focused"],
                    "locked_verification_inputs": {
                        self.locked_rel: self.locked_hash,
                    },
                    "verification_commands": [
                        {
                            "name": "focused",
                            "argv": ["{python}", "-c", "raise SystemExit(0)"],
                            "cwd": ".",
                            "timeout_seconds": 30,
                        }
                    ],
                },
            ],
        }
        self.state = {
            "schema_version": "1.0",
            "queue_id": "test",
            "status": "REPAIR_REQUIRED",
            "current_task": None,
            "current_owner": None,
            "lock_token": None,
            "completed_tasks": [],
            "evidence_records": {},
            "last_failure": None,
            "next_task": "R0.1",
            "production_entry": "v4_unchanged",
        }
        _write_json(self.root / TASKS_REL, self.tasks)
        _write_json(self.root / STATE_REL, self.state)
        self.control = RebuildControl(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _evidence(self, task_id: str) -> Path:
        path = self.root / "evidence" / f"{task_id}.json"
        _write_json(
            path,
            {
                "task_id": task_id,
                "changed_paths": ["work/module.py", f"evidence/{task_id}.json"],
                "checks": [{"name": "focused", "exit_code": 0}],
            },
        )
        return path

    def test_audit_detects_locked_input_post_completion_drift(self):
        """After complete, tampering with locked input must fail audit."""
        lock = self.control.claim("R0.1", "owner-a")
        self.control.complete(
            "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
        )
        self.assertEqual(self.control.audit(), [])
        # Tamper with locked input.
        self.locked_file.write_text("drifted content", encoding="utf-8")
        issues = self.control.audit()
        self.assertTrue(
            any("locked input" in issue and "drift" in issue.lower()
                for issue in issues),
            f"audit should detect locked input drift; got: {issues}",
        )

    def test_audit_passes_when_locked_input_unchanged(self):
        """After complete with unchanged locked input, audit is clean."""
        lock = self.control.claim("R0.1", "owner-a")
        self.control.complete(
            "R0.1", "owner-a", lock["token"], self._evidence("R0.1")
        )
        self.assertEqual(self.control.audit(), [])


def _sha256_file(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
