"""V6.7 cross-process locks, leases, and persistent idempotency."""

import json
import multiprocessing
import os
import tempfile
import unittest
from pathlib import Path

try:
    from mode_p_vnext import concurrency_lock as cl
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


def _collision_worker(lock_root, ready, start, release, results, owner):
    lock = cl.SessionLock(
        "EP8/SCENE1",
        lock_root=Path(lock_root),
        lease_seconds=30,
    )
    ready.put(owner)
    start.wait(10)
    acquired = lock.acquire(owner)
    results.put((owner, acquired))
    if acquired:
        release.wait(10)
        lock.release(owner)


class ConcurrencyLockTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_acquire_free_lock(self):
        lock = cl.SessionLock("EP8")
        self.assertTrue(lock.acquire("owner1"))
        self.assertEqual(lock.owner, "owner1")

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_acquire_held_lock_fails(self):
        lock = cl.SessionLock("EP8")
        lock.acquire("owner1")
        self.assertFalse(lock.acquire("owner2"))

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_release_and_reacquire(self):
        lock = cl.SessionLock("EP8")
        lock.acquire("owner1")
        lock.release("owner1")
        self.assertTrue(lock.acquire("owner2"))

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_release_by_wrong_owner_fails(self):
        lock = cl.SessionLock("EP8")
        lock.acquire("owner1")
        with self.assertRaises(cl.LockError):
            lock.release("owner2")

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_stale_lock_detection(self):
        lock = cl.SessionLock("EP8", lease_seconds=0)  # instantly stale
        lock.acquire("owner1")
        self.assertTrue(lock.is_stale)

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_idempotent_duplicate_detection(self):
        tracker = cl.IdempotencyTracker()
        self.assertTrue(tracker.check_and_record("TX001"))
        self.assertFalse(tracker.check_and_record("TX001"))  # duplicate

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_filesystem_lock_is_visible_to_independent_instances(self):
        with tempfile.TemporaryDirectory(prefix="vnext_lock_") as temp:
            first = cl.SessionLock("EP8", lock_root=Path(temp))
            second = cl.SessionLock("EP8", lock_root=Path(temp))
            self.assertTrue(first.acquire("owner1"))
            self.assertFalse(second.acquire("owner2"))
            first.release("owner1")
            self.assertTrue(second.acquire("owner2"))
            second.release("owner2")

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_multiprocess_collision_has_exactly_one_winner(self):
        with tempfile.TemporaryDirectory(prefix="vnext_lock_") as temp:
            context = multiprocessing.get_context("spawn")
            ready = context.Queue()
            results = context.Queue()
            start = context.Event()
            release = context.Event()
            processes = [
                context.Process(
                    target=_collision_worker,
                    args=(
                        temp,
                        ready,
                        start,
                        release,
                        results,
                        f"owner{index}",
                    ),
                )
                for index in (1, 2)
            ]
            for process in processes:
                process.start()
            self.assertEqual(
                {ready.get(timeout=15), ready.get(timeout=15)},
                {"owner1", "owner2"},
            )
            start.set()
            outcomes = [results.get(timeout=15), results.get(timeout=15)]
            self.assertEqual(sum(1 for _, won in outcomes if won), 1)
            release.set()
            for process in processes:
                process.join(timeout=15)
                self.assertEqual(process.exitcode, 0)

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_expired_dead_process_lock_can_be_taken_over_and_is_audited(self):
        with tempfile.TemporaryDirectory(prefix="vnext_lock_") as temp:
            lock_root = Path(temp)
            first = cl.SessionLock("EP8", lock_root=lock_root)
            self.assertTrue(first.acquire("owner1"))
            record = first.read_record()
            self.assertIsNotNone(record)
            record["lease_expires_at_epoch"] = 0
            record["process_id"] = 2_147_000_000
            first.lock_path.write_text(
                json.dumps(record),
                encoding="utf-8",
            )

            second = cl.SessionLock("EP8", lock_root=lock_root)
            self.assertTrue(second.acquire("owner2"))
            self.assertEqual(second.read_record()["owner_id"], "owner2")
            audit = (lock_root / "lock_audit.jsonl").read_text(
                encoding="utf-8"
            )
            self.assertIn("LOCK_TAKEOVER", audit)
            second.release("owner2")

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_expired_live_process_lock_is_not_taken_over(self):
        with tempfile.TemporaryDirectory(prefix="vnext_lock_") as temp:
            lock_root = Path(temp)
            first = cl.SessionLock("EP8", lock_root=lock_root)
            self.assertTrue(first.acquire("owner1"))
            record = first.read_record()
            record["lease_expires_at_epoch"] = 0
            record["process_id"] = os.getpid()
            first.lock_path.write_text(
                json.dumps(record),
                encoding="utf-8",
            )
            second = cl.SessionLock("EP8", lock_root=lock_root)
            self.assertFalse(second.acquire("owner2"))
            first.release("owner1")

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_active_commit_marker_blocks_stale_takeover(self):
        with tempfile.TemporaryDirectory(prefix="vnext_lock_") as temp:
            lock_root = Path(temp)
            marker = lock_root / "commit.in_progress"
            first = cl.SessionLock("EP8", lock_root=lock_root)
            self.assertTrue(first.acquire("owner1"))
            record = first.read_record()
            record["lease_expires_at_epoch"] = 0
            record["process_id"] = 2_147_000_000
            first.lock_path.write_text(
                json.dumps(record),
                encoding="utf-8",
            )
            marker.write_text("active", encoding="utf-8")

            second = cl.SessionLock(
                "EP8",
                lock_root=lock_root,
                active_commit_marker=marker,
            )
            self.assertFalse(second.acquire("owner2"))
            marker.unlink()
            self.assertTrue(second.acquire("owner2"))
            second.release("owner2")

    @unittest.skipIf(not MODULE_EXISTS, "concurrency_lock not yet implemented")
    def test_persistent_idempotency_is_cross_instance(self):
        with tempfile.TemporaryDirectory(prefix="vnext_idem_") as temp:
            first = cl.IdempotencyTracker(Path(temp))
            second = cl.IdempotencyTracker(Path(temp))
            self.assertTrue(first.check_and_record("TX001"))
            self.assertFalse(second.check_and_record("TX001"))


if __name__ == "__main__":
    unittest.main()
