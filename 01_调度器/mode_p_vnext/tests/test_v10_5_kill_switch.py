"""V10.5 — kill switch atomically fails closed and preserves evidence."""

import hashlib
import tempfile
import unittest
from pathlib import Path

try:
    from mode_p_vnext import feature_gate as fg
    from mode_p_vnext.rollback import KillSwitchActive, RollbackController

    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


class KillSwitchTests(unittest.TestCase):
    def _fixture(self, root: Path):
        archive = root / "v4-archive"
        vnext = root / "vnext"
        archive.mkdir()
        vnext.mkdir()
        (archive / "entry.md").write_text("do not overwrite", encoding="utf-8")
        (vnext / "evidence.json").write_text("retain evidence", encoding="utf-8")
        controller = RollbackController(root / "control")
        manifest = controller.create_manifest(
            archive_root=archive,
            entry_relative_path="entry.md",
            archive_artifact_paths=["entry.md"],
            vnext_root=vnext,
            release_evidence_relative_path="evidence.json",
            retained_commit_ids=["commit_1"],
            affected_scope={"episode_ids": ["EP9"], "scene_ids": []},
            bundle_id="RB_KILL_1",
        )
        return archive, vnext, controller, manifest

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_kill_switch_routes_control_state_to_current_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, vnext, controller, manifest = self._fixture(root)
            archive_digest, vnext_digest = _tree_digest(archive), _tree_digest(vnext)
            state = controller.arm_kill_switch(
                manifest_path=manifest,
                archive_root=archive,
                vnext_root=vnext,
                reason_code="SAFETY_STOP",
                affected_scope={"episode_ids": ["EP9"], "scene_ids": []},
                actor="operator_1",
                request_id="incident_1",
            )
            self.assertTrue(state.kill_switch_armed)
            self.assertEqual(state.active_mode, "current")
            effective = controller.resolve_effective_entry()
            self.assertEqual(effective.mode, "current")
            self.assertTrue(effective.kill_switch_armed)
            self.assertEqual(archive_digest, _tree_digest(archive))
            self.assertEqual(vnext_digest, _tree_digest(vnext))
            self.assertTrue(fg.FeatureGate(controller.control_root).status().kill_switch_armed)

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_kill_switch_is_idempotent_only_for_same_incident(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, vnext, controller, manifest = self._fixture(root)
            args = dict(
                manifest_path=manifest,
                archive_root=archive,
                vnext_root=vnext,
                reason_code="SAFETY_STOP",
                affected_scope={"episode_ids": ["EP9"], "scene_ids": []},
                actor="operator_1",
                request_id="incident_1",
            )
            first = controller.arm_kill_switch(**args)
            second = controller.arm_kill_switch(**args)
            self.assertEqual(first.integrity_sha256, second.integrity_sha256)
            args["request_id"] = "incident_2"
            with self.assertRaises(KillSwitchActive):
                controller.arm_kill_switch(**args)

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_gate_cannot_be_reenabled_after_kill_switch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, vnext, controller, manifest = self._fixture(root)
            controller.arm_kill_switch(
                manifest_path=manifest,
                archive_root=archive,
                vnext_root=vnext,
                reason_code="SAFETY_STOP",
                affected_scope={"episode_ids": ["EP9"], "scene_ids": []},
                actor="operator_1",
                request_id="incident_1",
            )
            gate = fg.FeatureGate(controller.control_root)
            with self.assertRaises(fg.GateError):
                gate.enable_shadow(["EP9"])
            self.assertEqual(gate.status().effective_mode, "current")

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_operations_runbook_declares_rebuild_and_director_boundaries(self):
        project_root = Path(__file__).resolve().parents[3]
        document = project_root / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_OPERATIONS.md"
        content = document.read_text(encoding="utf-8")
        for required in (
            "Rebuild",
            "没有可调用的启用命令",
            "真实 `/mode-p-pilot` 入口在 R3.1 **没有被修改**",
            "不得手改",
            "不得自动恢复",
            "导演决策优化",
        ):
            with self.subTest(required=required):
                self.assertIn(required, content)


if __name__ == "__main__":
    unittest.main()
