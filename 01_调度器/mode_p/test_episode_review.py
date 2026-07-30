"""Tests for the source-bound, unbounded Episode Review loop."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from batch_scheduler import schedule_batches
from episode_review import (
    EpisodeReviewError,
    _extract_review_excerpt,
    check_ledger_continuity,
    prepare_review,
    review_gate,
    submit_review,
)


_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="mode_p_review_"))


def _tmpdir() -> Path:
    return _TEMP_ROOT


def _state(position: str) -> dict:
    return {
        "characters": [{
            "entity_id": "A", "position": position, "facing": "N",
            "screen_direction": "static", "posture": "standing",
        }],
        "props": [],
        "light_main": {"direction": "top", "color_temp_k": 5000, "ratio": "1:3"},
        "action_phase": "static",
    }


def _manifest(scene_index: int, master_hash: str) -> dict:
    scene_id = f"S{scene_index}"
    return {
        "manifest_version": "1.0",
        "scene_id": scene_id,
        "master_version": f"{scene_id}/v1.0",
        "master_content_hash": master_hash,
        "compiler_version": "1.3.0",
        "shots": [{
            "shot_id": f"{scene_id}-1", "duration": 5,
            "scene_expression": "conversation_power",
            "timing_mode": "event_nodes",
            "story_fact_ref": {
                "text_start": f"Scene {scene_index} event",
                "source_scene_id": scene_id,
                "source_line_start": scene_index,
                "source_line_end": scene_index,
            },
            "opening_state_keys": _state(f"scene_{scene_index}_start"),
            "closing_state_keys": _state(f"scene_{scene_index}_end"),
            "entry_boundary_id": "SCENE_ENTRY",
            "exit_boundary_id": "SCENE_EXIT",
            "transition_execution": "post_production",
            "boundary_continuity": "scene_exit",
            "generation_mode": "text_only",
            "reference_assets": [],
        }],
    }


def _master(scene_index: int, revision: int) -> str:
    return f"""\
# Director Master S{scene_index}
## 1. 场景层设计
场景 {scene_index} 的摘要，修订 {revision}。
### 1.1 戏剧变化与信息策略
本场承担全片中的明确戏剧功能。
## 2. 逐镜 Shot Contract
进入边界：[D] 场景 {scene_index} 的首镜进入状态。
交出边界：[D] 场景 {scene_index} 的末镜交出状态。
"""


def _scene_session(prefix: str, scene_index: int, revision: int = 0) -> Path:
    session = _tmpdir() / f"{prefix}_scene_{scene_index}"
    working = session / "working"
    delivery = session / "delivery"
    working.mkdir(parents=True, exist_ok=True)
    delivery.mkdir(parents=True, exist_ok=True)
    text = _master(scene_index, revision)
    master_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    (session / "DIRECTOR_MASTER.md").write_text(text, encoding="utf-8")
    (session / "STATUS.md").write_text(
        "# MODE:P Session\n\n状态：已交付。\n", encoding="utf-8")
    (working / "SHOT_MANIFEST.json").write_text(
        json.dumps(_manifest(scene_index, master_hash), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (delivery / "STORYBOARD.md").write_text(
        f"# Storyboard scene {scene_index} revision {revision}\n", encoding="utf-8")
    (delivery / "VIDEO_PROMPT.md").write_text(
        f"# Video scene {scene_index} revision {revision}\n", encoding="utf-8")
    return session


def _rewrite_scene(session: Path, scene_index: int, revision: int) -> None:
    text = _master(scene_index, revision)
    master_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    (session / "DIRECTOR_MASTER.md").write_text(text, encoding="utf-8")
    (session / "working" / "SHOT_MANIFEST.json").write_text(
        json.dumps(_manifest(scene_index, master_hash), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (session / "delivery" / "STORYBOARD.md").write_text(
        f"# Storyboard scene {scene_index} revision {revision}\n", encoding="utf-8")
    (session / "delivery" / "VIDEO_PROMPT.md").write_text(
        f"# Video scene {scene_index} revision {revision}\n", encoding="utf-8")


def _inputs(prefix: str = "case", scene_count: int = 2
            ) -> tuple[Path, Path, Path, dict[int, Path], Path]:
    digest = _tmpdir() / f"{prefix}_digest.json"
    digest.write_text(json.dumps({
        "file_path": str(_tmpdir() / f"{prefix}_script.md"),
        "encoding": "utf-8", "source_content_hash": "a" * 64,
        "total_lines": scene_count * 5, "scene_count": scene_count,
        "scenes": [
            {"index": index, "start_line": (index - 1) * 5 + 1,
             "end_line": index * 5, "header_line": f"Scene {index}",
             "header_kind": "test", "status": "resolved"}
            for index in range(1, scene_count + 1)
        ],
    }), encoding="utf-8")
    manifest = schedule_batches(digest)
    manifest_path = _tmpdir() / f"{prefix}_batch.json"
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    bible = _tmpdir() / f"{prefix}_bible.md"
    bible.write_text(
        "# EPISODE_VISUAL_BIBLE — Test\n\nCompleted visual arc.\n",
        encoding="utf-8")
    ledger = _tmpdir() / f"{prefix}_ledger.md"
    ledger_lines = ["# EPISODE_CONTINUITY_LEDGER — Test", ""]
    for index in range(1, scene_count + 1):
        ledger_lines.append(f"## 场景 {index}\nCommitted state {index}.\n")
    for index in range(1, scene_count):
        ledger_lines.append(f"场景 {index} → 场景 {index + 1}\n")
    ledger.write_text("\n".join(ledger_lines), encoding="utf-8")
    sessions = {
        index: _scene_session(prefix, index)
        for index in range(1, scene_count + 1)
    }
    review_dir = _tmpdir() / f"{prefix}_review"
    return manifest_path, bible, ledger, sessions, review_dir


def _result(name: str, text: str) -> Path:
    path = _tmpdir() / name
    path.write_text(text, encoding="utf-8")
    return path


class PrepareTests(unittest.TestCase):

    def test_extract_review_excerpt_accepts_interleaved_v4_master(self) -> None:
        master = _tmpdir() / "interleaved_v4_master.md"
        master.write_text(
            "# Director Master S1\n"
            "## 1. 场景设计\n"
            "场景摘要。\n"
            "## Boundary S1-B0 | SCENE_ENTRY -> S1-1\n"
            "交接描述：[D] 首镜进入状态。\n"
            "## Shot S1-1 | 5s\n"
            "镜头内容。\n"
            "## Boundary S1-B1 | S1-1 -> SCENE_EXIT\n"
            "交接描述：[D] 末镜交出状态。\n",
            encoding="utf-8",
        )

        excerpt = _extract_review_excerpt(master)

        self.assertIn("场景摘要。", excerpt)
        self.assertIn("首镜进入边界：首镜进入状态。", excerpt)
        self.assertIn("末镜交出边界：末镜交出状态。", excerpt)
        self.assertNotIn("镜头内容。", excerpt)

    def test_prepare_requires_all_delivered_scenes(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("all_scenes")
        with self.assertRaises(EpisodeReviewError):
            prepare_review(manifest, bible, ledger, {1: sessions[1]}, review_dir)

    def test_prepare_packet_contains_summaries_not_full_video_prompts(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("packet")
        state = prepare_review(manifest, bible, ledger, sessions, review_dir)
        self.assertEqual(state["status"], "awaiting_review")
        packet = (review_dir / "EPISODE_REVIEW_PACKET.md").read_text(encoding="utf-8")
        self.assertIn("场景 1 的摘要", packet)
        self.assertIn("首镜进入边界", packet)
        self.assertNotIn("# Video scene", packet)

    def test_unfinished_bible_is_rejected(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("placeholder")
        bible.write_text(
            "# EPISODE_VISUAL_BIBLE\n[Director: fill]\n", encoding="utf-8")
        with self.assertRaises(EpisodeReviewError):
            prepare_review(manifest, bible, ledger, sessions, review_dir)


class ReviewLoopTests(unittest.TestCase):

    def test_pass_opens_delivery_gate(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("pass")
        prepare_review(manifest, bible, ledger, sessions, review_dir)
        state = submit_review(
            review_dir,
            _result("pass.md", "EPISODE REVIEW: PASS\n全片连续且方向统一。\n"))
        self.assertEqual(state["status"], "passed")
        self.assertEqual(review_gate(review_dir),
                         (True, "Episode Review PASS is current"))

    def test_revision_requires_new_affected_scene_delivery_then_rereview(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("revise")
        first = prepare_review(manifest, bible, ledger, sessions, review_dir)
        self.assertEqual(first["cycle"], 1)
        submit_review(
            review_dir,
            _result("revise.md",
                    "EPISODE REVIEW: REVISE\nAffected scenes: 1\n"
                    "场景 1 到场景 2 的交出状态不清楚。\n"))
        with self.assertRaises(EpisodeReviewError):
            prepare_review(manifest, bible, ledger, sessions, review_dir)

        _rewrite_scene(sessions[1], 1, 1)
        second = prepare_review(manifest, bible, ledger, sessions, review_dir)
        self.assertEqual(second["cycle"], 2)
        self.assertEqual(second["status"], "awaiting_review")
        self.assertFalse(review_gate(review_dir)[0])
        submit_review(
            review_dir, _result("repass.md", "EPISODE REVIEW: PASS\n已修复。\n"))
        self.assertTrue(review_gate(review_dir)[0])

    def test_no_fixed_revision_limit(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("unbounded")
        prepare_review(manifest, bible, ledger, sessions, review_dir)
        for revision in range(1, 13):
            submit_review(
                review_dir,
                _result(
                    f"unbounded_{revision}.md",
                    "EPISODE REVIEW: REVISE\nAffected scenes: 1\n"
                    f"第 {revision} 轮仍有明确问题。\n"))
            _rewrite_scene(sessions[1], 1, revision)
            state = prepare_review(manifest, bible, ledger, sessions, review_dir)
            self.assertEqual(state["status"], "awaiting_review")
        self.assertEqual(state["cycle"], 13)

    def test_explicit_block_requires_reason(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("blocked")
        prepare_review(manifest, bible, ledger, sessions, review_dir)
        with self.assertRaises(EpisodeReviewError):
            submit_review(
                review_dir, _result("bad_block.md", "EPISODE REVIEW: BLOCKED\n"))
        state = submit_review(
            review_dir,
            _result("block.md",
                    "EPISODE REVIEW: BLOCKED\nReason: 剧本中的时间冲突需要用户裁决。\n"))
        self.assertEqual(state["status"], "blocked")
        with self.assertRaises(EpisodeReviewError):
            prepare_review(manifest, bible, ledger, sessions, review_dir)

    def test_dependency_change_invalidates_old_pass(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("stale")
        prepare_review(manifest, bible, ledger, sessions, review_dir)
        submit_review(
            review_dir, _result("stale_pass.md", "EPISODE REVIEW: PASS\n"))
        self.assertTrue(review_gate(review_dir)[0])
        bible.write_text(
            bible.read_text(encoding="utf-8") + "Updated direction.\n",
            encoding="utf-8")
        ok, detail = review_gate(review_dir)
        self.assertFalse(ok)
        self.assertIn("dependency changed", detail)

    def test_malformed_review_result_is_rejected(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("malformed")
        prepare_review(manifest, bible, ledger, sessions, review_dir)
        with self.assertRaises(EpisodeReviewError):
            submit_review(review_dir, _result("malformed.md", "Looks good.\n"))


class LedgerCheckTests(unittest.TestCase):

    def test_structurally_complete_ledger_passes(self) -> None:
        manifest, _bible, ledger, _sessions, _review = _inputs("ledger_good")
        self.assertTrue(check_ledger_continuity(ledger, manifest).ok)

    def test_missing_handoff_is_flagged(self) -> None:
        manifest, _bible, ledger, _sessions, _review = _inputs("ledger_bad")
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace("场景 1 → 场景 2", "missing"),
            encoding="utf-8")
        self.assertFalse(check_ledger_continuity(ledger, manifest).ok)


class CLITests(unittest.TestCase):

    def test_cli_prepare_submit_and_gate(self) -> None:
        manifest, bible, ledger, sessions, review_dir = _inputs("cli")
        command = [
            sys.executable, "-m", "episode_review", "prepare",
            str(manifest), str(bible), str(ledger), str(review_dir),
        ]
        for index, session in sessions.items():
            command.extend(["--scene-session", f"{index}={session}"])
        prepared = subprocess.run(
            command, capture_output=True, text=True, timeout=10)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        result_path = _result("cli_result.md", "EPISODE REVIEW: PASS\n")
        submitted = subprocess.run(
            [sys.executable, "-m", "episode_review", "submit",
             str(review_dir), str(result_path)],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(submitted.returncode, 0, submitted.stderr)
        gated = subprocess.run(
            [sys.executable, "-m", "episode_review", "gate", str(review_dir)],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(gated.returncode, 0, gated.stdout + gated.stderr)


if __name__ == "__main__":
    unittest.main()
