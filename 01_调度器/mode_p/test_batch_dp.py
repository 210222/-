from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from batch_dp import (
    BatchDpError,
    cache_dp_response,
    prepare_batch_dp,
    submit_batch_dp,
)
from batch_state_machine import BatchStage, load_state
from dp_contract import DP_READY_FORMAT
from run_mode_p import do_precheck, initialise
from test_structural_precheck import _VALID_MASTER
from pipeline_telemetry import summarize_events
from scene_bridge import BridgeError


BATCH_READY = (
    "READY S1: Shot S1-1 的机位位于房间内部，入口边界与0秒人物位置一致。\n"
    "READY S2: Shot S2-1 的主光方向和边界动作状态在当前提示词中一致。"
)


class BatchDpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mode_p_batch_dp_")
        self.root = Path(self.temp.name)
        self.manifest = self.root / "BATCH_MANIFEST.json"
        source_hash = "a" * 64
        self.manifest.write_text(json.dumps({
            "schema_version": "1.0",
            "script_source_hash": source_hash,
            "mode": "single_batch",
            "total_scenes": 2,
            "selected_scenes": [1, 2],
            "total_batches": 1,
            "batches": [{"batch_index": 1, "scene_indices": [1, 2]}],
            "shared_documents": [
                "SCRIPT_STRUCTURE.json",
                "SCRIPT_FACTS.md",
                "EPISODE_VISUAL_BIBLE.md",
                "EPISODE_CONTINUITY_LEDGER.md",
            ],
        }, ensure_ascii=False), encoding="utf-8")
        (self.root / "SCRIPT_STRUCTURE.json").write_text(
            json.dumps({"source_content_hash": source_hash}), encoding="utf-8"
        )
        (self.root / "SCRIPT_FACTS.md").write_text(
            "# SCRIPT_FACTS\ncompleted\n", encoding="utf-8"
        )
        (self.root / "EPISODE_VISUAL_BIBLE.md").write_text(
            "# EPISODE_VISUAL_BIBLE\ncompleted\n", encoding="utf-8"
        )
        (self.root / "EPISODE_CONTINUITY_LEDGER.md").write_text(
            "# EPISODE_CONTINUITY_LEDGER\ncompleted\n", encoding="utf-8"
        )
        self.sessions: dict[int, Path] = {}
        for index in (1, 2):
            session = self.root / "scenes" / f"scene_{index:03d}"
            context = self.root / f"context_{index}.md"
            context.write_text(
                f"# Scene Context\n\nScene {index}\n", encoding="utf-8"
            )
            self.assertEqual(initialise(context, session), 0)
            master = self.root / f"master_{index}.md"
            master.write_text(
                _VALID_MASTER.replace("PRE", f"S{index}"), encoding="utf-8"
            )
            self.assertEqual(do_precheck(master, session), 0)
            self.sessions[index] = session
        self.review = self.root / "batches" / "batch_001" / "dp"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _prepare(self, cache_dir: Path | None = None) -> dict:
        return prepare_batch_dp(
            1, self.manifest, self.sessions, self.review, cache_dir=cache_dir
        )

    def test_packet_binds_union_and_all_current_files(self) -> None:
        packet = self._prepare()
        self.assertEqual(packet["shot_ids"], ["S1-1", "S2-1"])
        self.assertEqual(packet["dp_model"], "inherit")
        self.assertEqual(len(packet["scenes"]), 2)
        markdown = (self.review / "DP_PACKET.md").read_text(encoding="utf-8")
        self.assertIn(DP_READY_FORMAT, markdown)
        self.assertIn("S1-1", markdown)
        self.assertIn("S2-1", markdown)
        self.assertIn("Used capability digest", markdown)
        self.assertIn("none (text_only)", markdown)
        self.assertIn("DP_EVIDENCE_SCENE_001.md", markdown)
        evidence = (self.review / "DP_EVIDENCE_SCENE_001.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Scene 1", evidence)
        self.assertIn("Committed Continuity Digest", evidence)
        self.assertNotIn("source_sha256", evidence)
        for forbidden in (
            "DIRECTOR_MASTER.md",
            "SHOT_MANIFEST.json",
            "KNOWLEDGE_CONTEXT.md",
            "knowledge_index.json",
            "dp_contract.py",
            "mode-p-dp.md",
            "02_Agent\\dp_agent.md",
            "SHA-256:",
        ):
            self.assertNotIn(forbidden, markdown)

    def test_issue_routes_only_to_affected_scene(self) -> None:
        self._prepare()
        feedback = self.root / "issues.md"
        feedback.write_text(
            "S2-1: light_source — 当前主光在空间中没有物理来源。\n",
            encoding="utf-8",
        )
        state = submit_batch_dp(self.review, feedback)
        self.assertEqual(state["status"], "revision_required")
        self.assertEqual(state["affected_scenes"], [2])
        self.assertEqual(load_state(self.sessions[1]).stage, BatchStage.DP_BATCH.value)
        self.assertEqual(load_state(self.sessions[2]).stage, BatchStage.DIRECTOR_BATCH.value)
        self.assertFalse((self.sessions[1] / "delivery").exists())

    def test_missing_dp_input_blocks_without_committing_or_revising(self) -> None:
        self._prepare()
        feedback = self.root / "blocked.md"
        feedback.write_text(
            "DP_INPUT_BLOCKED: The current Storyboard file is absent from the packet.\n",
            encoding="utf-8",
        )
        state = submit_batch_dp(self.review, feedback)
        self.assertEqual(state["status"], "input_blocked")
        self.assertEqual(state["committed_scenes"], [])
        for session in self.sessions.values():
            self.assertEqual(load_state(session).stage, BatchStage.DP_BATCH.value)
            self.assertFalse((session / "delivery").exists())

    def test_ready_commits_every_scene_and_batch_ledger(self) -> None:
        self._prepare(self.root / "ready_dp_cache")
        feedback = self.root / "ready.md"
        feedback.write_text(BATCH_READY + "\n", encoding="utf-8")
        state = submit_batch_dp(
            self.review,
            feedback,
            model_name="deepseek-v4-pro",
            model_call_id="fresh-dp-call-1",
            model_elapsed_s=1.25,
        )
        self.assertEqual(state["status"], "committed")
        self.assertEqual(state["committed_scenes"], [1, 2])
        self.assertTrue((self.review / "LEDGER_COMMIT.json").is_file())
        for session in self.sessions.values():
            self.assertEqual(
                sorted(path.name for path in (session / "delivery").iterdir()),
                ["STORYBOARD.md", "VIDEO_PROMPT.md"],
            )
        telemetry = summarize_events(self.root)
        self.assertEqual(telemetry["model_calls"]["dp"], 1)
        self.assertGreaterEqual(telemetry["cache"]["store"], 1)

    def test_ready_prevalidates_entire_batch_before_first_delivery(self) -> None:
        self._prepare()
        feedback = self.root / "ready_prevalidation_failure.md"
        feedback.write_text(BATCH_READY + "\n", encoding="utf-8")
        with patch(
            "batch_dp.validate_batch_commit_inputs",
            side_effect=BridgeError("final Boundary is invalid"),
        ):
            with self.assertRaisesRegex(BatchDpError, "cannot commit any scene"):
                submit_batch_dp(self.review, feedback)
        for session in self.sessions.values():
            self.assertEqual(load_state(session).stage, BatchStage.DP_BATCH.value)
            self.assertFalse((session / "delivery").exists())

    def test_production_dp_records_actual_model_without_global_allowlist(self) -> None:
        self._prepare()
        feedback = self.root / "flash.md"
        feedback.write_text(BATCH_READY + "\n", encoding="utf-8")
        state = submit_batch_dp(
            self.review,
            feedback,
            model_name="deepseek-v4-flash",
            model_call_id="flash-call",
        )
        self.assertEqual(state["status"], "committed")
        telemetry = summarize_events(self.root)
        self.assertEqual(telemetry["model_calls"]["dp"], 1)

    def test_changed_input_invalidates_dp_packet(self) -> None:
        self._prepare()
        video = self.sessions[2] / "working" / "VIDEO_PROMPT.md"
        video.write_text(video.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
        feedback = self.root / "ready_stale.md"
        feedback.write_text(BATCH_READY, encoding="utf-8")
        with self.assertRaises(BatchDpError):
            submit_batch_dp(self.review, feedback)
        self.assertFalse((self.sessions[1] / "delivery").exists())

    def test_unknown_shot_feedback_is_rejected(self) -> None:
        self._prepare()
        feedback = self.root / "unknown.md"
        feedback.write_text(
            "S9-1: camera_path — 轨迹越过墙体。\n", encoding="utf-8"
        )
        with self.assertRaises(BatchDpError):
            submit_batch_dp(self.review, feedback)

    def test_verified_dp_cache_hit_restores_response_and_skips_model_call(self) -> None:
        cache = self.root / "isolated_dp_cache"
        packet = self._prepare(cache)
        ready = self.root / "actual_dp_response.md"
        ready.write_text(BATCH_READY + "\n", encoding="utf-8")
        cache_dp_response(packet, ready, self.root)

        second_review = self.root / "batches" / "batch_001" / "dp_cached"
        second_packet = prepare_batch_dp(
            1, self.manifest, self.sessions, second_review, cache_dir=cache
        )
        self.assertEqual(
            second_packet["review_content_sha256"],
            packet["review_content_sha256"],
        )
        state = json.loads((second_review / "DP_STATE.json").read_text(
            encoding="utf-8"))
        self.assertEqual(state["status"], "cached_dp_available")
        cached = Path(state["cached_response_path"])
        self.assertEqual(cached.read_text(encoding="utf-8"), BATCH_READY + "\n")
        result = submit_batch_dp(second_review, cached)
        self.assertEqual(result["status"], "committed")
        telemetry = summarize_events(self.root)
        self.assertGreaterEqual(telemetry["cache"]["hit"], 1)
        self.assertEqual(telemetry["model_calls"]["dp"], 0)


if __name__ == "__main__":
    unittest.main()
