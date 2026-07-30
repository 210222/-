"""Resilience tests: cold start, hot recovery, cache corruption, concurrency.

Tests that the MODE:P toolchain behaves correctly under adverse conditions.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import time
import unittest
import copy
import hashlib
from pathlib import Path

from batch_state_machine import init_state, load_state, transition, BatchStage
from bootstrap_loader import load_bootstrap
from session_lock import (
    LockError,
    session_lock,
    prepare_staging,
    commit,
    verify_commit,
    rollback,
)
from cache_manager import (
    build_script_key,
    load_cache_manifest,
    lookup_cache,
    store_in_cache,
)
from batch_dp import (
    BatchDpError,
    cache_dp_response,
    prepare_batch_dp,
    submit_batch_dp,
)
from mode_p_pilot import run_pilot
from pipeline_telemetry import record_event, summarize_events
from run_mode_p import do_precheck, initialise
from test_full_pilot_loop import _reviewable_master
from test_mode_p_pilot import _MINI_SCRIPT, _valid_facts, _complete_episode_doc
from test_structural_precheck import _VALID_MASTER


def _ready_feedback(shot_ids: list[str]) -> str:
    by_scene: dict[str, list[str]] = {}
    for shot_id in shot_ids:
        by_scene.setdefault(shot_id.rsplit("-", 1)[0], []).append(shot_id)
    return "\n".join(
        f"READY {scene_id}: Shot {ids[0]} keeps the camera path executable and "
        "the visible action boundary and physical light source remain continuous."
        for scene_id, ids in sorted(by_scene.items())
    )


def _temp_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix=f"mode_p_resilience_{os.getpid()}_"))


def _prepared_current_batch(root: Path) -> tuple[Path, dict[int, Path], Path]:
    manifest = root / "BATCH_MANIFEST.json"
    manifest.write_text(json.dumps({
        "schema_version": "1.0",
        "script_source_hash": "a" * 64,
        "mode": "single_batch",
        "total_scenes": 2,
        "selected_scenes": [1, 2],
        "total_batches": 1,
        "batches": [{"batch_index": 1, "scene_indices": [1, 2]}],
        "shared_documents": [
            "SCRIPT_STRUCTURE.json", "SCRIPT_FACTS.md",
            "EPISODE_VISUAL_BIBLE.md", "EPISODE_CONTINUITY_LEDGER.md",
        ],
    }, ensure_ascii=False), encoding="utf-8")
    (root / "SCRIPT_STRUCTURE.json").write_text(
        json.dumps({"source_content_hash": "a" * 64}), encoding="utf-8"
    )
    (root / "SCRIPT_FACTS.md").write_text("# SCRIPT_FACTS\ncomplete\n", encoding="utf-8")
    (root / "EPISODE_VISUAL_BIBLE.md").write_text(
        "# EPISODE_VISUAL_BIBLE\ncomplete\n", encoding="utf-8"
    )
    (root / "EPISODE_CONTINUITY_LEDGER.md").write_text(
        "# EPISODE_CONTINUITY_LEDGER\ncomplete\n", encoding="utf-8"
    )
    sessions: dict[int, Path] = {}
    for index in (1, 2):
        session = root / "scenes" / f"scene_{index:03d}"
        context = root / f"scene_{index}_context.md"
        context.write_text(f"# Scene Context\nScene {index}\n", encoding="utf-8")
        if initialise(context, session) != 0:
            raise AssertionError("scene initialization failed")
        master = root / f"scene_{index}_master.md"
        master.write_text(
            _VALID_MASTER.replace("PRE", f"R{index}"), encoding="utf-8"
        )
        if do_precheck(master, session) != 0:
            raise AssertionError("scene precheck failed")
        sessions[index] = session
    return manifest, sessions, root / "batches" / "batch_001" / "dp"


class ColdStartTests(unittest.TestCase):
    """Verify fresh session initialization works from scratch."""

    def test_fresh_session_bootstrap_ok(self) -> None:
        b = load_bootstrap()
        self.assertTrue(b.ok, f"Bootstrap errors on cold start: {b.errors}")

    def test_fresh_session_state_init(self) -> None:
        d = _temp_dir()
        state = init_state(d, 1, 1)
        self.assertEqual(state.stage, "bootstrap")
        loaded = load_state(d)
        self.assertEqual(loaded.session_id, d.name)

    def test_cache_empty_on_cold_start(self) -> None:
        d = _temp_dir()
        key = build_script_key(b"test", load_bootstrap())
        self.assertIsNone(lookup_cache(d / "cache", key))


class HotRecoveryTests(unittest.TestCase):
    """Verify that a session can be resumed after interruption."""

    def setUp(self) -> None:
        self.d = _temp_dir()
        init_state(self.d, 1, 1)

    def test_resume_after_init(self) -> None:
        state = load_state(self.d)
        self.assertEqual(state.stage, "bootstrap")
        transition(self.d, BatchStage.SCRIPT_PARSE)
        state2 = load_state(self.d)
        self.assertEqual(state2.stage, "script_parse")

    def test_resume_preserves_revision_count(self) -> None:
        master = self.d / "master.md"
        master.write_text("# Master", encoding="utf-8")
        # Forward progress through stages and verify state persists
        transition(self.d, BatchStage.SCRIPT_PARSE)
        self.assertEqual(load_state(self.d).stage, "script_parse")
        transition(self.d, BatchStage.DIRECTOR_BATCH)
        transition(self.d, BatchStage.STRUCTURAL_PRECHECK, master_path=master)
        # Interruption — reload and verify stage is preserved
        reloaded = load_state(self.d)
        self.assertEqual(reloaded.stage, "structural_precheck")
        self.assertGreater(reloaded.artifact_generation, 0)

    def test_recovery_reads_saved_commit(self) -> None:
        src = self.d / "input.md"
        src.write_text("test", encoding="utf-8")
        prepare_staging(self.d, {"test.md": src})
        manifest = commit(self.d, "batch_commit", 1)
        ok, _ = verify_commit(self.d)
        self.assertTrue(ok)
        self.assertEqual(manifest.total_files, 1)


class CorruptionTests(unittest.TestCase):
    """Verify that corrupted state or cache is detected and handled."""

    def setUp(self) -> None:
        self.d = _temp_dir()

    def test_tampered_state_detected(self) -> None:
        init_state(self.d, 1, 1)
        path = self.d / "RUN_STATE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["stage"] = "delivery"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(Exception):
            load_state(self.d)

    def test_commit_verification_detects_tampered_file(self) -> None:
        src = self.d / "original.md"
        src.write_text("original", encoding="utf-8")
        prepare_staging(self.d, {"file.md": src})
        commit(self.d, "batch_commit", 1)
        (self.d / "working" / "file.md").write_text("tampered", encoding="utf-8")
        ok, issues = verify_commit(self.d)
        self.assertFalse(ok)

    def test_corrupted_cache_key_does_not_crash(self) -> None:
        d = _temp_dir()
        cache = d / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        # Write invalid manifest
        (cache / "CACHE_MANIFEST.json").write_text("not json", encoding="utf-8")
        key = build_script_key(b"test", load_bootstrap())
        self.assertIsNone(lookup_cache(cache, key))
        # Second call should also not crash
        self.assertIsNone(lookup_cache(cache, key))


class ConcurrencyTests(unittest.TestCase):
    """Verify lock prevents concurrent writes."""

    def setUp(self) -> None:
        self.d = _temp_dir()
        init_state(self.d, 1, 1)

    def test_concurrent_locks_block(self) -> None:
        acquired = threading.Event()
        released = threading.Event()

        def holder():
            with session_lock(self.d):
                acquired.set()
                time.sleep(0.3)
            released.set()

        t = threading.Thread(target=holder)
        t.start()
        acquired.wait(timeout=2)

        with self.assertRaises(LockError):
            with session_lock(self.d, timeout=0.1):
                pass
        released.wait(timeout=2)
        t.join()

    def test_lock_released_on_exception(self) -> None:
        try:
            with session_lock(self.d):
                raise RuntimeError("simulated crash")
        except RuntimeError:
            pass
        # Lock should be released — should be able to acquire again
        with session_lock(self.d, timeout=1.0):
            pass  # success

    def test_rollback_cleans_staging(self) -> None:
        src = self.d / "src.md"
        src.write_text("data", encoding="utf-8")
        prepare_staging(self.d, {"file.md": src})
        self.assertTrue((self.d / "staging").exists())
        rollback(self.d)
        self.assertFalse((self.d / "staging").exists())

    def test_concurrent_real_pilot_start_fails_without_partial_structure(self) -> None:
        root = _temp_dir()
        script = root / "pilot.md"
        session = root / "episode"
        script.write_text(_MINI_SCRIPT, encoding="utf-8")
        with session_lock(session):
            self.assertEqual(run_pilot(script, session_dir=session), 1)
            self.assertFalse((session / "SCRIPT_STRUCTURE.json").exists())
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        data = json.loads((session / "SCRIPT_STRUCTURE.json").read_text(
            encoding="utf-8"))
        self.assertEqual(data["scene_count"], 4)


class ActiveBatchRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = _temp_dir()
        self.manifest, self.sessions, self.review = _prepared_current_batch(self.root)
        self.cache = self.root / "dp_cache"

    def test_fresh_dp_interruption_leaves_bound_packet_and_no_delivery(self) -> None:
        first = prepare_batch_dp(
            1, self.manifest, self.sessions, self.review, cache_dir=self.cache
        )
        self.assertEqual(
            json.loads((self.review / "DP_STATE.json").read_text(encoding="utf-8"))["status"],
            "awaiting_fresh_dp",
        )
        self.assertFalse(any((session / "delivery").exists()
                             for session in self.sessions.values()))
        second = prepare_batch_dp(
            1, self.manifest, self.sessions, self.review, cache_dir=self.cache
        )
        self.assertEqual(first["packet_sha256"], second["packet_sha256"])
        self.assertEqual(summarize_events(self.root)["model_calls"]["dp"], 0)

    def test_ready_commit_resumes_after_first_scene_interruption(self) -> None:
        packet = prepare_batch_dp(
            1, self.manifest, self.sessions, self.review, cache_dir=self.cache
        )
        ready = self.root / "ready.md"
        ready.write_text(
            _ready_feedback(packet["shot_ids"]) + "\n", encoding="utf-8"
        )
        with self.assertRaises(BatchDpError):
            submit_batch_dp(
                self.review, ready, failpoint_after_scene=1
            )
        self.assertTrue((self.sessions[1] / "delivery").is_dir())
        self.assertFalse((self.sessions[2] / "delivery").exists())
        self.assertFalse((self.review / "LEDGER_COMMIT.json").exists())
        state = submit_batch_dp(self.review, ready)
        self.assertEqual(state["status"], "committed")
        self.assertEqual(state["committed_scenes"], [1, 2])
        self.assertTrue((self.sessions[2] / "delivery").is_dir())
        self.assertTrue((self.review / "LEDGER_COMMIT.json").is_file())

    def test_corrupted_real_dp_cache_becomes_miss_and_never_restores(self) -> None:
        packet = prepare_batch_dp(
            1, self.manifest, self.sessions, self.review, cache_dir=self.cache
        )
        ready = self.root / "cache_ready.md"
        ready.write_text(
            _ready_feedback(packet["shot_ids"]) + "\n", encoding="utf-8"
        )
        cache_dp_response(packet, ready, self.root)
        entry = load_cache_manifest(self.cache).entries[0]
        cached_file = self.cache.joinpath(*Path(entry.object_root).parts) / entry.outputs[0].path
        cached_file.write_text("corrupted", encoding="utf-8")
        next_review = self.root / "batches" / "batch_001" / "dp_after_corruption"
        prepare_batch_dp(
            1, self.manifest, self.sessions, next_review, cache_dir=self.cache
        )
        state = json.loads((next_review / "DP_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "awaiting_fresh_dp")
        self.assertFalse((next_review / "CACHED_DP_RESPONSE.md").exists())


class VersionUpgradeTests(unittest.TestCase):
    """Verify that implementation version changes are detected."""

    def test_compiler_version_is_stable(self) -> None:
        from master_compiler import COMPILER_VERSION
        self.assertIsInstance(COMPILER_VERSION, str)
        self.assertTrue(COMPILER_VERSION.count(".") >= 2)

    def test_bootstrap_detects_checker_versions(self) -> None:
        b = load_bootstrap()
        self.assertGreater(len(b.checker_fingerprints), 3)
        for name, fp in b.checker_fingerprints.items():
            self.assertEqual(len(fp), 64, f"Checker {name} has invalid fingerprint")
            self.assertTrue(fp.islower(), f"Checker {name} fingerprint not lowercase")

    def test_cache_key_changes_with_bootstrap(self) -> None:
        b1 = load_bootstrap()
        b2 = copy.deepcopy(b1)
        b2.checker_fingerprints["script_ingest.py"] = hashlib.sha256(
            b"upgraded parser implementation"
        ).hexdigest()
        self.assertNotEqual(
            build_script_key(b"test", b1).compute(),
            build_script_key(b"test", b2).compute(),
        )


class FullPathRecoveryTests(unittest.TestCase):
    """Stage-by-stage recovery on the real full-batch pilot path."""

    def _fresh_pilot(self) -> tuple[Path, Path]:
        d = _temp_dir()
        script = d / "pilot.md"
        script.write_text(_MINI_SCRIPT, encoding="utf-8")
        session = d / "episode"
        return script, session

    def _advance_through_prepare(self, script: Path, session: Path) -> dict:
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        structure = json.loads(
            (session / "SCRIPT_STRUCTURE.json").read_text(encoding="utf-8")
        )
        source_hash = structure["source_content_hash"]
        (session / "SCRIPT_FACTS.md").write_text(
            _valid_facts(source_hash), encoding="utf-8"
        )
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        for name in ("EPISODE_VISUAL_BIBLE.md", "EPISODE_CONTINUITY_LEDGER.md"):
            path = session / name
            path.write_text(
                _complete_episode_doc(path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        return json.loads((session / "SCENE_SESSIONS.json").read_text(encoding="utf-8"))

    def test_cold_start_through_prepare_stage_produces_scene_sessions(self) -> None:
        script, session = self._fresh_pilot()
        scene_map = self._advance_through_prepare(script, session)
        scenes = {item["scene_index"]: Path(item["session_path"])
                   for item in scene_map["scenes"]}
        self.assertEqual(len(scenes), 4)
        for idx, sess in scenes.items():
            self.assertTrue(sess.is_dir(), f"Scene {idx} session missing")
            self.assertTrue((sess / "SCENE_CONTEXT.md").is_file())
        root_state = json.loads(
            (session / "RUN_STATE.json").read_text(encoding="utf-8")
        )
        self.assertEqual(root_state["stage"], "director_batch")

    def test_recover_after_prepare_interruption_reuses_structure(self) -> None:
        script, session = self._fresh_pilot()
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        structure_path = session / "SCRIPT_STRUCTURE.json"
        self.assertTrue(structure_path.is_file())
        structure_hash = json.loads(structure_path.read_text(encoding="utf-8"))[
            "source_content_hash"
        ]
        result = run_pilot(script, session_dir=session)
        self.assertEqual(result, 0)
        reloaded_hash = json.loads(structure_path.read_text(encoding="utf-8"))[
            "source_content_hash"
        ]
        self.assertEqual(structure_hash, reloaded_hash)

    def test_recover_after_precheck_interruption_keeps_working_tree(self) -> None:
        script, session = self._fresh_pilot()
        scene_map = self._advance_through_prepare(script, session)
        scenes = {item["scene_index"]: Path(item["session_path"])
                   for item in scene_map["scenes"]}

        master = scenes[1] / "DIRECTOR_MASTER.md"
        master.write_text(
            _VALID_MASTER.replace("PRE", "SCN1"), encoding="utf-8"
        )
        self.assertEqual(
            do_precheck(master, scenes[1], batch_index=1, total_batches=1), 0
        )
        self.assertTrue((scenes[1] / "working" / "STORYBOARD.md").is_file())
        self.assertTrue((scenes[1] / "working" / "VIDEO_PROMPT.md").is_file())
        storyboard_text = (scenes[1] / "working" / "STORYBOARD.md").read_text(
            encoding="utf-8"
        )
        run_pilot(script, session_dir=session)
        self.assertEqual(
            (scenes[1] / "working" / "STORYBOARD.md").read_text(encoding="utf-8"),
            storyboard_text,
        )

    def test_recovery_after_dp_ready_preserves_delivery(self) -> None:
        script, session = self._fresh_pilot()
        scene_map = self._advance_through_prepare(script, session)
        scenes = {item["scene_index"]: Path(item["session_path"])
                   for item in scene_map["scenes"]}
        for si, s in scenes.items():
            master = s / "DIRECTOR_MASTER.md"
            master.write_text(
                _VALID_MASTER.replace("PRE", f"SCN{si}"), encoding="utf-8"
            )
            self.assertEqual(
                do_precheck(master, s, batch_index=1, total_batches=1), 0
            )
        record_event(
            session,
            event_type="model",
            stage="director_batch",
            model_role="director",
            model_name="deepseek-v4-pro",
            model_call_id="recovery-dir",
            input_bytes=1000,
            output_bytes=500,
        )
        review = session / "batches" / "batch_001" / "dp"
        prepare_batch_dp(
            1, session / "BATCH_MANIFEST.json", scenes, review,
            cache_dir=session / "dp_cache",
        )
        ready = session / "DP_RESPONSE.md"
        packet = json.loads(
            (review / "DP_PACKET.json").read_text(encoding="utf-8")
        )
        ready.write_text(
            _ready_feedback(packet["shot_ids"]) + "\n", encoding="utf-8"
        )
        dp_state = submit_batch_dp(
            review, ready, model_name="deepseek-v4-pro", model_call_id="dp-recovery",
            model_elapsed_s=0.5,
        )
        self.assertEqual(dp_state["status"], "committed")
        for si in (1, 2, 3, 4):
            self.assertTrue(
                (scenes[si] / "delivery" / "STORYBOARD.md").is_file(),
                f"Scene {si} delivery missing after commit",
            )
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        for si in (1, 2, 3, 4):
            self.assertTrue(
                (scenes[si] / "delivery" / "STORYBOARD.md").is_file(),
                f"Scene {si} delivery lost after recovery",
            )

    def test_staging_cleanup_after_crash_does_not_corrupt_committed_delivery(self) -> None:
        d = _temp_dir()
        init_state(d, 1, 1)
        src = d / "src.md"
        src.write_text("committed content", encoding="utf-8")
        prepare_staging(d, {"file.md": src})
        commit(d, "scene_delivery", 1, target="delivery")
        (d / "delivery" / "file.md").write_text("committed content", encoding="utf-8")
        prepare_staging(d, {"file.md": src})
        self.assertTrue((d / "staging").is_dir())
        rollback(d)
        self.assertFalse((d / "staging").exists())
        self.assertTrue((d / "delivery" / "file.md").is_file())
        self.assertEqual(
            (d / "delivery" / "file.md").read_text(encoding="utf-8"),
            "committed content",
        )

    def test_pilot_recovery_after_full_delivery_reports_delivery_stage(self) -> None:
        script, session = self._fresh_pilot()
        scene_map = self._advance_through_prepare(script, session)
        scenes = {item["scene_index"]: Path(item["session_path"])
                   for item in scene_map["scenes"]}
        for si, s in scenes.items():
            master = s / "DIRECTOR_MASTER.md"
            master.write_text(_reviewable_master(si), encoding="utf-8")
            self.assertEqual(
                do_precheck(master, s, batch_index=1, total_batches=1), 0
            )
        record_event(
            session,
            event_type="model",
            stage="director_batch",
            model_role="director",
            model_name="deepseek-v4-pro",
            model_call_id="final-recovery",
            input_bytes=2000,
            output_bytes=1000,
        )
        review = session / "batches" / "batch_001" / "dp"
        prepare_batch_dp(
            1, session / "BATCH_MANIFEST.json", scenes, review,
            cache_dir=session / "dp_cache",
        )
        ready = session / "DP_RESPONSE.md"
        packet = json.loads(
            (review / "DP_PACKET.json").read_text(encoding="utf-8")
        )
        ready.write_text(
            _ready_feedback(packet["shot_ids"]) + "\n", encoding="utf-8"
        )
        submit_batch_dp(
            review, ready, model_name="deepseek-v4-pro", model_call_id="dp-final",
            model_elapsed_s=0.5,
        )
        from episode_review import prepare_review, submit_review
        from episode_delivery import assemble_episode_delivery
        review_dir = session / "episode_review"
        prepare_review(
            session / "BATCH_MANIFEST.json",
            session / "EPISODE_VISUAL_BIBLE.md",
            session / "EPISODE_CONTINUITY_LEDGER.md",
            scenes, review_dir,
        )
        result = session / "review_result.md"
        result.write_text("EPISODE REVIEW: PASS\n全片一致。\n", encoding="utf-8")
        submit_review(review_dir, result)
        assemble_episode_delivery(review_dir, scenes, session)
        self.assertTrue((session / "delivery" / "STORYBOARD.md").is_file())
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        root_state = json.loads(
            (session / "RUN_STATE.json").read_text(encoding="utf-8")
        )
        self.assertEqual(root_state["stage"], "delivery")

    def test_concurrent_pilot_lock_prevents_double_prepare(self) -> None:
        script, session = self._fresh_pilot()
        self.assertEqual(run_pilot(script, session_dir=session), 0)
        with session_lock(session):
            self.assertEqual(run_pilot(script, session_dir=session), 1)
        self.assertEqual(run_pilot(script, session_dir=session), 0)


if __name__ == "__main__":
    unittest.main()
