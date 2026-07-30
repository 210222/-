"""V6.2 Transaction, real staging, atomic commit, and recovery."""

import json
import tempfile
import unittest
from pathlib import Path

try:
    from mode_p_vnext import atomic_commit as ac
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class AtomicCommitTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_staging_write_and_commit(self):
        tx = ac.Transaction("TX001", "SEG1")
        tx.stage("master.json", '{"test": 1}')
        self.assertIn("master.json", tx.staging)
        tx.commit()
        self.assertTrue(tx.committed)

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_staging_validates_manifest(self):
        tx = ac.Transaction("TX002", "SEG1")
        tx.stage("file.json", "data")
        violations = tx.validate()
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_failed_commit_does_not_expose_partial(self):
        tx = ac.Transaction("TX003", "SEG1")
        tx.stage("a.json", "a")
        tx.stage("b.json", "b")
        tx.fail("simulated failure")
        self.assertFalse(tx.committed)
        self.assertTrue(tx.failed)

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_cannot_commit_after_fail(self):
        tx = ac.Transaction("TX004", "SEG1")
        tx.stage("x.json", "x")
        tx.fail("error")
        with self.assertRaises(ac.TransactionError):
            tx.commit()

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_filesystem_commit_publishes_only_complete_version(self):
        with tempfile.TemporaryDirectory(prefix="vnext_atomic_") as temp:
            scene_root = Path(temp) / "scene"
            tx = ac.Transaction(
                "C001",
                "SEG1",
                scene_root=scene_root,
            )
            tx.stage("STORYBOARD.md", "storyboard-v1")
            tx.stage("nested/VIDEO_PROMPT.md", "video-v1")

            staging_dir = scene_root / "staging" / "C001"
            self.assertTrue((staging_dir / "STORYBOARD.md").is_file())
            self.assertFalse((scene_root / "current.json").exists())

            tx.commit()

            pointer = json.loads(
                (scene_root / "current.json").read_text(encoding="utf-8")
            )
            delivery_pointer = json.loads(
                (scene_root / "delivery" / "current.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(pointer["commit_id"], "C001")
            self.assertEqual(delivery_pointer["commit_id"], "C001")
            delivery = scene_root / "delivery" / "versions" / "C001"
            self.assertEqual(
                (delivery / "STORYBOARD.md").read_text(encoding="utf-8"),
                "storyboard-v1",
            )
            self.assertEqual(
                (delivery / "nested" / "VIDEO_PROMPT.md").read_text(
                    encoding="utf-8"
                ),
                "video-v1",
            )
            self.assertFalse(staging_dir.exists())

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_second_commit_atomically_replaces_pointers_not_old_version(self):
        with tempfile.TemporaryDirectory(prefix="vnext_atomic_") as temp:
            scene_root = Path(temp) / "scene"
            first = ac.Transaction("C001", "SEG1", scene_root=scene_root)
            first.stage("A.txt", "old-a")
            first.stage("B.txt", "old-b")
            first.commit()

            second = ac.Transaction(
                "C002",
                "SEG1",
                scene_root=scene_root,
                parent_commit_id="C001",
            )
            second.stage("A.txt", "new-a")
            second.stage("C.txt", "new-c")
            second.commit()

            current = json.loads(
                (scene_root / "current.json").read_text(encoding="utf-8")
            )
            delivery_current = json.loads(
                (scene_root / "delivery" / "current.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(current["commit_id"], "C002")
            self.assertEqual(delivery_current["commit_id"], "C002")
            old_version = scene_root / "delivery" / "versions" / "C001"
            new_version = scene_root / "delivery" / "versions" / "C002"
            self.assertTrue((old_version / "B.txt").is_file())
            self.assertFalse((new_version / "B.txt").exists())
            self.assertEqual(
                sorted(
                    p.relative_to(new_version).as_posix()
                    for p in new_version.rglob("*")
                    if p.is_file() and p.name != ac.MANIFEST_NAME
                ),
                ["A.txt", "C.txt"],
            )

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_recovery_promotes_one_complete_prepared_staging(self):
        with tempfile.TemporaryDirectory(prefix="vnext_recover_") as temp:
            scene_root = Path(temp) / "scene"
            tx = ac.Transaction("C001", "SEG1", scene_root=scene_root)
            tx.stage("A.txt", "complete")
            tx.prepare()

            report = ac.recover_scene(scene_root)

            self.assertEqual(report.errors, ())
            self.assertEqual(report.promoted_commit_ids, ("C001",))
            self.assertEqual(report.current_commit_id, "C001")
            self.assertTrue(
                (scene_root / "commits" / "C001" / "A.txt").is_file()
            )

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_generation_id_may_differ_from_commit_id(self):
        with tempfile.TemporaryDirectory(prefix="vnext_recover_") as temp:
            scene_root = Path(temp) / "scene"
            tx = ac.Transaction(
                "C001",
                "SEG1",
                scene_root=scene_root,
                generation_id="GEN-001",
            )
            tx.stage("A.txt", "complete")
            tx.prepare()

            report = ac.recover_scene(scene_root)

            self.assertEqual(report.errors, ())
            self.assertEqual(report.promoted_commit_ids, ("C001",))
            self.assertFalse(
                (scene_root / "staging" / "GEN-001").exists()
            )

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_recovery_abandons_incomplete_staging_without_stitching(self):
        with tempfile.TemporaryDirectory(prefix="vnext_recover_") as temp:
            scene_root = Path(temp) / "scene"
            tx = ac.Transaction("C001", "SEG1", scene_root=scene_root)
            tx.stage("A.txt", "partial")

            report = ac.recover_scene(scene_root)

            self.assertEqual(report.current_commit_id, "")
            self.assertEqual(report.promoted_commit_ids, ())
            self.assertEqual(len(report.abandoned_staging), 1)
            abandoned = scene_root / report.abandoned_staging[0]
            self.assertTrue((abandoned / "A.txt").is_file())
            self.assertTrue((abandoned / ac.ABANDONED_NAME).is_file())
            self.assertFalse((scene_root / "current.json").exists())

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_recovery_repairs_delivery_pointer_from_valid_current(self):
        with tempfile.TemporaryDirectory(prefix="vnext_recover_") as temp:
            scene_root = Path(temp) / "scene"
            tx = ac.Transaction("C001", "SEG1", scene_root=scene_root)
            tx.stage("A.txt", "complete")
            tx.commit()
            (scene_root / "delivery" / "current.json").unlink()

            report = ac.recover_scene(scene_root)

            self.assertEqual(report.errors, ())
            self.assertTrue(report.delivery_repaired)
            delivery_pointer = json.loads(
                (scene_root / "delivery" / "current.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(delivery_pointer["commit_id"], "C001")

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_artifact_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="vnext_atomic_") as temp:
            tx = ac.Transaction(
                "C001",
                "SEG1",
                scene_root=Path(temp) / "scene",
            )
            with self.assertRaises(ac.TransactionError):
                tx.stage("../outside.txt", "escape")
            with self.assertRaises(ac.TransactionError):
                ac.Transaction(
                    "..",
                    "SEG1",
                    scene_root=Path(temp) / "scene",
                )

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_stale_parent_cannot_overwrite_current_pointer(self):
        with tempfile.TemporaryDirectory(prefix="vnext_atomic_") as temp:
            scene_root = Path(temp) / "scene"
            first = ac.Transaction("C001", "SEG1", scene_root=scene_root)
            first.stage("A.txt", "first")
            first.commit()
            stale = ac.Transaction(
                "C002",
                "SEG1",
                scene_root=scene_root,
                parent_commit_id="WRONG",
            )
            stale.stage("A.txt", "stale")
            with self.assertRaises(ac.TransactionError):
                stale.commit()
            current = json.loads(
                (scene_root / "current.json").read_text(encoding="utf-8")
            )
            self.assertEqual(current["commit_id"], "C001")

    @unittest.skipIf(not MODULE_EXISTS, "atomic_commit not yet implemented")
    def test_ambiguous_complete_recovery_candidates_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="vnext_recover_") as temp:
            scene_root = Path(temp) / "scene"
            for commit_id in ("C001", "C002"):
                tx = ac.Transaction(
                    commit_id,
                    "SEG1",
                    scene_root=scene_root,
                )
                tx.stage(f"{commit_id}.txt", "complete")
                tx.prepare()

            report = ac.recover_scene(scene_root)

            self.assertTrue(
                any("ambiguous recovery candidates" in e for e in report.errors)
            )
            self.assertEqual(report.promoted_commit_ids, ())
            self.assertFalse((scene_root / "current.json").exists())


if __name__ == "__main__":
    unittest.main()
