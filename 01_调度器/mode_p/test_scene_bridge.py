"""Tests for committed cross-batch continuity state."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from batch_scheduler import schedule_batches
from scene_bridge import (
    BridgeError,
    commit_batch_state,
    compute_handoffs,
    generate_ledger_snapshot,
    validate_handoff,
)
from master_compiler import compile_master
from test_master_compiler import V4_SHARED_BOUNDARY_MASTER


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_bridge_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


def _state(position: str = "desk", phase: str = "static") -> dict:
    return {
        "characters": [{
            "entity_id": "A",
            "position": position,
            "facing": "N",
            "screen_direction": "static",
            "posture": "standing",
        }],
        "props": [{"prop_id": "folder", "held_by": "A", "location": "left_hand"}],
        "light_main": {"direction": "top", "color_temp_k": 5000, "ratio": "1:3"},
        "action_phase": phase,
    }


def _shot_manifest(scene_index: int, opening: dict, closing: dict) -> dict:
    scene_id = f"S{scene_index}"
    return {
        "manifest_version": "1.0",
        "scene_id": scene_id,
        "master_version": f"{scene_id}/v1.0",
        "master_content_hash": f"{scene_index:x}" * 64,
        "compiler_version": "1.3.0",
        "shots": [{
            "shot_id": f"{scene_id}-1",
            "duration": 5,
            "scene_expression": "conversation_power",
            "timing_mode": "event_nodes",
            "story_fact_ref": {
                "text_start": f"Scene {scene_index} event",
                "source_scene_id": scene_id,
                "source_line_start": scene_index,
                "source_line_end": scene_index,
            },
            "opening_state_keys": opening,
            "closing_state_keys": closing,
            "entry_boundary_id": "SCENE_ENTRY",
            "exit_boundary_id": "SCENE_EXIT",
            "transition_execution": "post_production",
            "boundary_continuity": "scene_exit",
            "generation_mode": "text_only",
            "reference_assets": [],
        }],
    }


def _batch_manifest(scene_count: int = 4, capacity: int = 2,
                    prefix: str = "case") -> Path:
    digest_path = _tmpdir() / f"{prefix}_digest.json"
    digest_path.write_text(json.dumps({
        "file_path": str(_tmpdir() / f"{prefix}_script.md"),
        "encoding": "utf-8",
        "source_content_hash": "a" * 64,
        "total_lines": scene_count * 5,
        "scene_count": scene_count,
        "scenes": [
            {"index": index, "start_line": (index - 1) * 5 + 1,
             "end_line": index * 5, "header_line": f"## Scene {index}",
             "header_kind": "markdown_scene_en", "status": "resolved"}
            for index in range(1, scene_count + 1)
        ],
    }), encoding="utf-8")
    manifest = schedule_batches(digest_path, max_scenes_per_batch=capacity)
    path = _tmpdir() / f"{prefix}_batch_manifest.json"
    path.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def _ledger(prefix: str = "case") -> Path:
    path = _tmpdir() / f"{prefix}_ledger.md"
    path.write_text(
        "# EPISODE_CONTINUITY_LEDGER — Test\n\n"
        "## Completed continuity\nAll episode continuity is authored.\n",
        encoding="utf-8")
    return path


def _delivered_session(prefix: str, scene_index: int,
                       opening: dict, closing: dict) -> Path:
    session = _tmpdir() / f"{prefix}_scene_{scene_index}"
    working = session / "working"
    delivery = session / "delivery"
    working.mkdir(parents=True, exist_ok=True)
    delivery.mkdir(parents=True, exist_ok=True)
    (session / "STATUS.md").write_text(
        "# MODE:P Session\n\n状态：已交付。\n", encoding="utf-8")
    master_text = f"# Director Master for scene {scene_index}\n"
    (session / "DIRECTOR_MASTER.md").write_text(master_text, encoding="utf-8")
    manifest = _shot_manifest(scene_index, opening, closing)
    manifest["master_content_hash"] = hashlib.sha256(
        master_text.encode("utf-8")).hexdigest()
    (working / "SHOT_MANIFEST.json").write_text(
        json.dumps(manifest,
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (delivery / "STORYBOARD.md").write_text(
        f"# Scene {scene_index} Storyboard\n", encoding="utf-8")
    (delivery / "VIDEO_PROMPT.md").write_text(
        f"# Scene {scene_index} Video\n", encoding="utf-8")
    return session


def _delivered_v4_session(prefix: str, scene_index: int) -> Path:
    session = _tmpdir() / f"{prefix}_scene_{scene_index}"
    working = session / "working"
    delivery = session / "delivery"
    working.mkdir(parents=True, exist_ok=True)
    delivery.mkdir(parents=True, exist_ok=True)
    (session / "STATUS.md").write_text(
        "# MODE:P Session\n\n状态：已交付。\n", encoding="utf-8")
    scene_id = f"V4S{scene_index}"
    master_text = V4_SHARED_BOUNDARY_MASTER.replace("V4_SCENE", scene_id)
    master_path = session / "DIRECTOR_MASTER.md"
    master_path.write_text(master_text, encoding="utf-8")
    manifest = compile_master(master_path)
    (working / "SHOT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (delivery / "STORYBOARD.md").write_text(
        f"# Scene {scene_index} Storyboard\n", encoding="utf-8")
    (delivery / "VIDEO_PROMPT.md").write_text(
        f"# Scene {scene_index} Video\n", encoding="utf-8")
    return session


def _commit_first_batch(prefix: str, outgoing: dict | None = None
                        ) -> tuple[Path, Path, Path]:
    manifest = _batch_manifest(prefix=prefix)
    ledger = _ledger(prefix)
    session_1 = _delivered_session(prefix, 1, _state("entry"), _state("middle"))
    session_2 = _delivered_session(
        prefix, 2, _state("middle"), outgoing or _state("handoff", "travel"))
    commit_path = _tmpdir() / f"{prefix}_commit_1.json"
    commit_batch_state(
        1, manifest, ledger, {1: session_1, 2: session_2}, commit_path)
    return manifest, ledger, commit_path


class HandoffManifestTests(unittest.TestCase):

    def test_two_batches_have_one_pending_edge(self) -> None:
        report = compute_handoffs(_batch_manifest(prefix="handoffs"))
        self.assertEqual(len(report.handoffs), 1)
        self.assertEqual(report.handoffs[0].scene_from, 2)
        self.assertEqual(report.handoffs[0].scene_to, 3)
        self.assertEqual(report.handoffs[0].status, "pending")

    def test_single_batch_has_no_cross_batch_edge(self) -> None:
        report = compute_handoffs(
            _batch_manifest(scene_count=2, capacity=2, prefix="single"))
        self.assertTrue(report.ok)
        self.assertEqual(report.handoffs, [])

    def test_malformed_manifest_is_rejected(self) -> None:
        path = _batch_manifest(prefix="bad_manifest")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["total_batches"] = 99
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(BridgeError):
            compute_handoffs(path)


class CommitTests(unittest.TestCase):

    def test_commit_records_only_delivered_canonical_state(self) -> None:
        manifest, ledger, commit_path = _commit_first_batch("commit_valid")
        commit = json.loads(commit_path.read_text(encoding="utf-8"))
        self.assertEqual(commit["status"], "committed")
        self.assertEqual(commit["outgoing_scene_index"], 2)
        self.assertEqual(commit["outgoing_state"], _state("handoff", "travel"))
        self.assertEqual(len(commit["commit_sha256"]), 64)
        self.assertEqual(len(commit["scene_states"]), 2)

    def test_v4_shared_boundaries_commit_via_external_boundary_refs(self) -> None:
        manifest = _batch_manifest(
            scene_count=2, capacity=2, prefix="commit_v4_shared"
        )
        ledger = _ledger("commit_v4_shared")
        first = _delivered_v4_session("commit_v4_shared", 1)
        second = _delivered_session(
            "commit_v4_shared", 2, _state("entry"), _state("exit")
        )
        commit = commit_batch_state(
            1, manifest, ledger, {1: first, 2: second}
        )
        self.assertEqual(commit["status"], "committed")
        v4_manifest = json.loads(
            (first / "working" / "SHOT_MANIFEST.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            v4_manifest["shots"][0]["entry_boundary_id"], "V4S1-B0"
        )
        self.assertEqual(v4_manifest["boundaries"][0]["from_ref"], "SCENE_ENTRY")
        self.assertEqual(v4_manifest["boundaries"][-1]["to_ref"], "SCENE_EXIT")

    def test_undelivered_scene_cannot_be_committed(self) -> None:
        manifest = _batch_manifest(prefix="undelivered")
        ledger = _ledger("undelivered")
        first = _delivered_session("undelivered", 1, _state(), _state())
        second = _delivered_session("undelivered", 2, _state(), _state())
        (second / "STATUS.md").write_text("状态：等待导演修订。\n", encoding="utf-8")
        with self.assertRaises(BridgeError):
            commit_batch_state(1, manifest, ledger, {1: first, 2: second})

    def test_partial_or_extra_scene_map_is_rejected(self) -> None:
        manifest = _batch_manifest(prefix="partial")
        ledger = _ledger("partial")
        first = _delivered_session("partial", 1, _state(), _state())
        with self.assertRaises(BridgeError):
            commit_batch_state(1, manifest, ledger, {1: first})

    def test_unfinished_episode_ledger_is_rejected(self) -> None:
        manifest = _batch_manifest(prefix="ledger_placeholder")
        ledger = _ledger("ledger_placeholder")
        ledger.write_text(
            "# EPISODE_CONTINUITY_LEDGER\n[Director: fill]\n", encoding="utf-8")
        first = _delivered_session("ledger_placeholder", 1, _state(), _state())
        second = _delivered_session("ledger_placeholder", 2, _state(), _state())
        with self.assertRaises(BridgeError):
            commit_batch_state(1, manifest, ledger, {1: first, 2: second})


class SnapshotTests(unittest.TestCase):

    def test_first_batch_snapshot_has_no_inherited_commit(self) -> None:
        manifest = _batch_manifest(prefix="snapshot_first")
        ledger = _ledger("snapshot_first")
        text = generate_ledger_snapshot(1, manifest, ledger)
        self.assertIn("Opening batch: no prior batch state", text)
        self.assertNotIn("prior_commit_sha256", text)

    def test_later_batch_requires_and_renders_exact_prior_commit(self) -> None:
        manifest, ledger, commit = _commit_first_batch("snapshot_later")
        with self.assertRaises(BridgeError):
            generate_ledger_snapshot(2, manifest, ledger)
        text = generate_ledger_snapshot(2, manifest, ledger,
                                        prior_commit_path=commit)
        self.assertIn("prior_commit_sha256", text)
        self.assertIn("position=handoff", text)
        self.assertIn("Action phase: travel", text)

    def test_changed_episode_ledger_invalidates_prior_commit(self) -> None:
        manifest, ledger, commit = _commit_first_batch("snapshot_stale")
        ledger.write_text(
            ledger.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8")
        with self.assertRaises(BridgeError):
            generate_ledger_snapshot(
                2, manifest, ledger, prior_commit_path=commit)


class ValidateTests(unittest.TestCase):

    def _current_batch(self, prefix: str, manifest: Path, ledger: Path,
                       commit: Path, opening: dict) -> Path:
        directory = _tmpdir() / f"{prefix}_batch_2"
        working = directory / "working"
        working.mkdir(parents=True, exist_ok=True)
        (working / "SHOT_MANIFEST.json").write_text(
            json.dumps(_shot_manifest(3, opening, _state("end")),
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        generate_ledger_snapshot(
            2, manifest, ledger, directory / "LEDGER_SNAPSHOT.md", commit)
        return directory

    def test_continuous_matching_state_passes(self) -> None:
        outgoing = _state("same", "travel")
        manifest, ledger, commit = _commit_first_batch("match", outgoing)
        current = self._current_batch("match", manifest, ledger, commit, outgoing)
        report = validate_handoff(2, manifest, commit, current, "continuous")
        self.assertTrue(report.ok, report.handoffs[0].detail)

    def test_continuous_state_difference_fails(self) -> None:
        manifest, ledger, commit = _commit_first_batch("mismatch")
        current = self._current_batch(
            "mismatch", manifest, ledger, commit, _state("different", "travel"))
        report = validate_handoff(2, manifest, commit, current, "continuous")
        self.assertFalse(report.ok)
        self.assertIn("characters", report.handoffs[0].detail)

    def test_elliptical_change_passes_to_fresh_dp_review(self) -> None:
        manifest, ledger, commit = _commit_first_batch("elliptical")
        current = self._current_batch(
            "elliptical", manifest, ledger, commit, _state("new_location"))
        report = validate_handoff(2, manifest, commit, current, "elliptical")
        self.assertTrue(report.ok)
        self.assertIn("fresh DP semantic review", report.handoffs[0].detail)

    def test_missing_snapshot_proves_prior_state_was_not_loaded(self) -> None:
        manifest, _ledger_path, commit = _commit_first_batch("missing_snapshot")
        current = _tmpdir() / "missing_snapshot_batch_2"
        working = current / "working"
        working.mkdir(parents=True, exist_ok=True)
        (working / "SHOT_MANIFEST.json").write_text(
            json.dumps(_shot_manifest(3, _state(), _state())), encoding="utf-8")
        report = validate_handoff(2, manifest, commit, current)
        self.assertFalse(report.ok)
        self.assertIn("snapshot", report.handoffs[0].detail)

    def test_tampered_commit_is_rejected(self) -> None:
        manifest, ledger, commit = _commit_first_batch("tampered")
        data = json.loads(commit.read_text(encoding="utf-8"))
        data["outgoing_scene_index"] = 999
        commit.write_text(json.dumps(data), encoding="utf-8")
        current = _tmpdir() / "tampered_batch_2"
        current.mkdir(exist_ok=True)
        report = validate_handoff(2, manifest, commit, current)
        self.assertFalse(report.ok)
        self.assertIn("self-hash", report.handoffs[0].detail)


class CLITests(unittest.TestCase):

    def test_cli_handoffs_outputs_valid_json(self) -> None:
        manifest = _batch_manifest(prefix="cli_handoffs")
        result = subprocess.run(
            [sys.executable, "-m", "scene_bridge", "handoffs", str(manifest)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)), 1)

    def test_cli_commit_rejects_missing_scene_sessions_without_traceback(self) -> None:
        manifest = _batch_manifest(prefix="cli_commit")
        ledger = _ledger("cli_commit")
        result = subprocess.run(
            [sys.executable, "-m", "scene_bridge", "commit", "1",
             str(manifest), str(ledger), "-o", str(_tmpdir() / "bad_commit.json")],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Scene bridge error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
