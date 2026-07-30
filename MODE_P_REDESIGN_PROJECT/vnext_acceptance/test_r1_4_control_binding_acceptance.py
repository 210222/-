"""Locked control-plane binding gate for MODE:P vNext R1.4.

The R1.4 worker suite and Evidence are not independent authorities.  The
controller must execute the Codex-owned acceptance gates itself, preserve them
outside the worker's allowed write paths, and record those executions in the
machine state.  Hand-authored ``verification_results`` inside Evidence do not
meet that requirement.

Owned by the independent Codex audit.  Repair workers must not edit, replace,
skip, xfail, monkeypatch, or copy this file.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASKS_PATH = ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_REPAIR_TASKS.json"
STATE_PATH = ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_REBUILD_STATE.json"

LOCKED_GATES = {
    "test_r1_4_external_acceptance.py",
    "test_r1_4_adversarial_acceptance.py",
}
LOCKED_GATE_PATHS = {
    f"MODE_P_REDESIGN_PROJECT/vnext_acceptance/{name}" for name in LOCKED_GATES
}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class R14ControlBindingAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tasks_document = _read_json(TASKS_PATH)
        cls.task = next(
            task for task in tasks_document["tasks"] if task["task_id"] == "R1.4"
        )
        cls.state = _read_json(STATE_PATH)
        record = cls.state["evidence_records"]["R1.4"]
        cls.recorded_results = tuple(record.get("verification_results", ()))
        cls.evidence = _read_json(ROOT / record["path"])

    def test_controller_registry_executes_both_locked_gates(self):
        registered = {
            Path(argument).name
            for command in self.task["verification_commands"]
            for argument in command["argv"]
            if argument.endswith(".py")
        }
        self.assertTrue(
            LOCKED_GATES.issubset(registered),
            f"controller R1.4 commands omit locked gates: "
            f"{sorted(LOCKED_GATES - registered)}",
        )

    def test_locked_gates_are_outside_worker_write_scope(self):
        allowed = tuple(self.task["allowed_paths"])
        for gate in LOCKED_GATES:
            with self.subTest(gate=gate):
                self.assertFalse(
                    any(gate in path for path in allowed),
                    f"locked gate is worker-writable: {gate}",
                )

    def test_registry_pins_locked_gate_input_hashes(self):
        locked_inputs = self.task.get("locked_verification_inputs")
        self.assertIsInstance(locked_inputs, dict)
        self.assertEqual(LOCKED_GATE_PATHS, set(locked_inputs))
        for relative_path in sorted(LOCKED_GATE_PATHS):
            with self.subTest(relative_path=relative_path):
                self.assertEqual(
                    _sha256(ROOT / relative_path),
                    locked_inputs[relative_path],
                )

    def test_machine_state_records_controller_executed_locked_gates(self):
        recorded_names = {item["name"] for item in self.recorded_results}
        self.assertIn("r1_4_external_gate", recorded_names)
        self.assertIn("r1_4_adversarial_gate", recorded_names)

    def test_machine_state_binds_verification_input_hashes(self):
        record = self.state["evidence_records"]["R1.4"]
        recorded_hashes = record.get("verification_input_hashes")
        self.assertIsInstance(recorded_hashes, dict)
        self.assertEqual(
            self.task.get("locked_verification_inputs"),
            recorded_hashes,
        )

    def test_evidence_cannot_claim_unrecorded_verification(self):
        controller_names = {item["name"] for item in self.recorded_results}
        evidence_names = {
            item["name"] for item in self.evidence.get("verification_results", ())
        }
        unbound = evidence_names - controller_names
        self.assertEqual(
            set(),
            unbound,
            f"Evidence contains results not executed/recorded by controller: "
            f"{sorted(unbound)}",
        )


if __name__ == "__main__":
    unittest.main()
