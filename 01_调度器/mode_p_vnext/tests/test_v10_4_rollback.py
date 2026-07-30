"""V10.4 — rollback manifest integrity and no-v4-mutation drill."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    from mode_p_vnext.rollback import ManifestIntegrityError, RollbackController, RollbackError

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


class RollbackManifestTests(unittest.TestCase):
    def _fixture(self, root: Path):
        archive = root / "v4-readonly-archive"
        vnext = root / "vnext-evidence"
        control = root / "vnext-control"
        archive.mkdir()
        vnext.mkdir()
        (archive / "entry.md").write_text("v4 remains unchanged", encoding="utf-8")
        (archive / "delivery.json").write_text('{"delivery":"kept"}', encoding="utf-8")
        (vnext / "release_evidence.json").write_text('{"release":"drill"}', encoding="utf-8")
        manifest = RollbackController(control).create_manifest(
            archive_root=archive,
            entry_relative_path="entry.md",
            archive_artifact_paths=["entry.md", "delivery.json"],
            vnext_root=vnext,
            release_evidence_relative_path="release_evidence.json",
            retained_commit_ids=["commit_a", "commit_b"],
            affected_scope={"episode_ids": ["EP35"], "scene_ids": ["S1"]},
            bundle_id="RB_TEST_1",
        )
        return archive, vnext, RollbackController(control), manifest

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_manifest_binds_hashes_and_never_mutates_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, vnext, controller, manifest = self._fixture(root)
            before_archive, before_vnext = _tree_digest(archive), _tree_digest(vnext)
            verified = controller.verify_manifest(manifest, archive_root=archive, vnext_root=vnext)
            self.assertEqual(verified.bundle_id, "RB_TEST_1")
            self.assertEqual(verified.affected_scope["episode_ids"], ["EP35"])
            self.assertEqual(before_archive, _tree_digest(archive))
            self.assertEqual(before_vnext, _tree_digest(vnext))

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_artifact_or_evidence_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, vnext, controller, manifest = self._fixture(root)
            (archive / "entry.md").write_text("tampered", encoding="utf-8")
            with self.assertRaises(ManifestIntegrityError):
                controller.verify_manifest(manifest, archive_root=archive, vnext_root=vnext)
            (archive / "entry.md").write_text("v4 remains unchanged", encoding="utf-8")
            (vnext / "release_evidence.json").write_text("tampered", encoding="utf-8")
            with self.assertRaises(ManifestIntegrityError):
                controller.verify_manifest(manifest, archive_root=archive, vnext_root=vnext)

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_tampered_manifest_and_unsafe_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, vnext, controller, manifest = self._fixture(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["rollback_target"]["entry_relative_path"] = "../outside.md"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises((ManifestIntegrityError, RollbackError)):
                controller.verify_manifest(manifest, archive_root=archive, vnext_root=vnext)

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_rollback_records_current_route_actor_reason_and_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, vnext, controller, manifest = self._fixture(root)
            state = controller.rollback_to_current(
                manifest_path=manifest,
                archive_root=archive,
                vnext_root=vnext,
                reason_code="DRILL",
                affected_scope={"episode_ids": ["EP35"], "scene_ids": ["S1"]},
                actor="operator_1",
                request_id="rollback_1",
            )
            self.assertEqual(state.active_mode, "current")
            self.assertEqual(state.rollback_actor, "operator_1")
            self.assertEqual(state.rollback_reason_code, "DRILL")
            self.assertTrue(state.rolled_back_at_utc)

    @unittest.skipIf(not MODULE_EXISTS, "rollback not yet implemented")
    def test_create_rejects_duplicate_or_escape_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "archive"
            vnext = root / "vnext"
            archive.mkdir()
            vnext.mkdir()
            (archive / "entry.md").write_text("entry", encoding="utf-8")
            (vnext / "evidence.json").write_text("evidence", encoding="utf-8")
            controller = RollbackController(root / "control")
            common = dict(
                archive_root=archive,
                entry_relative_path="entry.md",
                vnext_root=vnext,
                release_evidence_relative_path="evidence.json",
                retained_commit_ids=["commit_a"],
                affected_scope={"episode_ids": ["EP1"], "scene_ids": []},
            )
            with self.assertRaises(RollbackError):
                controller.create_manifest(archive_artifact_paths=["entry.md", "entry.md"], **common)
            with self.assertRaises(RollbackError):
                controller.create_manifest(archive_artifact_paths=["../entry.md"], **common)


if __name__ == "__main__":
    unittest.main()
