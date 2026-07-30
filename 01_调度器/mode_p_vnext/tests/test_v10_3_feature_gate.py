"""V10.3 — Rebuild cannot enable any vNext release gate."""

import json
import tempfile
import unittest
from pathlib import Path

try:
    from mode_p_vnext import feature_gate as fg
    from mode_p_vnext.rollback import RollbackController

    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class FeatureGateTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "feature_gate not yet implemented")
    def test_default_off_and_current(self):
        gate = fg.FeatureGate()
        self.assertFalse(gate.shadow_enabled)
        self.assertFalse(gate.pilot_enabled)
        self.assertFalse(gate.canary_enabled)
        self.assertFalse(gate.production_enabled)
        self.assertEqual(gate.status().effective_mode, "current")
        self.assertFalse(gate.status().vnext_invocation_allowed)

    @unittest.skipIf(not MODULE_EXISTS, "feature_gate not yet implemented")
    def test_every_gate_is_rejected_in_rebuild(self):
        gate = fg.FeatureGate()
        methods = (
            gate.enable_shadow,
            gate.enable_pilot,
            gate.enable_canary,
            gate.enable_production,
        )
        for method in methods:
            with self.subTest(method=method.__name__):
                with self.assertRaises(fg.GateError):
                    method(["EP35"])
        for name in ("shadow", "pilot", "canary", "production", "unknown"):
            self.assertFalse(gate.can_enable_in_rebuild(name))

    @unittest.skipIf(not MODULE_EXISTS, "feature_gate not yet implemented")
    def test_external_submission_is_rejected(self):
        with self.assertRaises(fg.GateError):
            fg.FeatureGate().assert_submission_allowed()

    @unittest.skipIf(not MODULE_EXISTS, "feature_gate not yet implemented")
    def test_corrupt_control_record_never_enables_vnext(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = RollbackController(root)
            controller.state_path.write_text("{not json", encoding="utf-8")
            gate = fg.FeatureGate(root)
            self.assertEqual(gate.status().effective_mode, "current")
            self.assertFalse(gate.status().vnext_invocation_allowed)

    @unittest.skipIf(not MODULE_EXISTS, "feature_gate not yet implemented")
    def test_rebuild_ignores_even_a_valid_future_release_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = RollbackController(root)
            state = controller.read_state()
            forged = type(state)(
                generation=1,
                active_mode="vnext_pilot",
                active_entry_id="vnext_pilot_entry",
                rollback_manifest_relative_path="",
                rollback_manifest_sha256="",
                rollback_reason_code="",
                rollback_actor="",
                rolled_back_at_utc="",
                affected_scope={"episode_ids": [], "scene_ids": []},
                kill_switch_armed=False,
                kill_reason_code="",
                armed_by="",
                armed_at_utc="",
                request_id="",
            ).with_integrity()
            controller.state_path.write_text(json.dumps(forged.to_dict()), encoding="utf-8")
            self.assertEqual(fg.FeatureGate(root).status().effective_mode, "current")


if __name__ == "__main__":
    unittest.main()
