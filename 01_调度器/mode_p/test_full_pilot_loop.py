from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from batch_dp import prepare_batch_dp, submit_batch_dp
from episode_delivery import assemble_episode_delivery, verify_episode_delivery
from episode_review import prepare_review, submit_review
from mode_p_pilot import run_pilot
from run_mode_p import do_precheck
from test_mode_p_pilot import (
    _MINI_SCRIPT,
    _complete_episode_doc,
    _valid_facts,
)
from test_structural_precheck import _VALID_MASTER
from pipeline_telemetry import record_event, summarize_events


def _ready_feedback(shot_ids: list[str]) -> str:
    by_scene: dict[str, list[str]] = {}
    for shot_id in shot_ids:
        by_scene.setdefault(shot_id.rsplit("-", 1)[0], []).append(shot_id)
    return "\n".join(
        f"READY {scene_id}: Shot {ids[0]} keeps the camera path executable and "
        "the visible action boundary and physical light source remain continuous."
        for scene_id, ids in sorted(by_scene.items())
    )


def _reviewable_master(scene_index: int) -> str:
    scene_id = f"SCN{scene_index}"
    text = _VALID_MASTER.replace("PRE", scene_id)
    text = text.replace(
        f"Master 版本：{scene_id}/v1.0\n",
        f"Master 版本：{scene_id}/v1.0\n\n"
        "## 1. 场景层设计\n\n"
        "### 1.1 戏剧变化与信息策略\n\n"
        f"场景 {scene_index} 完成源剧本中的明确动作与信息变化。\n\n"
        "## 2. 逐镜 Shot Contract\n",
    )
    return text


class FullPilotLoopTests(unittest.TestCase):
    def test_four_scene_single_batch_reaches_atomic_episode_delivery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mode_p_full_loop_") as directory:
            root = Path(directory)
            script = root / "pilot.md"
            session = root / "session"
            script.write_text(_MINI_SCRIPT, encoding="utf-8")

            self.assertEqual(run_pilot(script, session_dir=session), 0)
            structure = json.loads(
                (session / "SCRIPT_STRUCTURE.json").read_text(encoding="utf-8")
            )
            (session / "SCRIPT_FACTS.md").write_text(
                _valid_facts(structure["source_content_hash"]), encoding="utf-8"
            )
            self.assertEqual(run_pilot(script, session_dir=session), 0)
            for name in (
                "EPISODE_VISUAL_BIBLE.md",
                "EPISODE_CONTINUITY_LEDGER.md",
            ):
                path = session / name
                path.write_text(
                    _complete_episode_doc(path.read_text(encoding="utf-8")),
                    encoding="utf-8",
                )
            self.assertEqual(run_pilot(script, session_dir=session), 0)

            scene_map = json.loads(
                (session / "SCENE_SESSIONS.json").read_text(encoding="utf-8")
            )
            scenes = {
                item["scene_index"]: Path(item["session_path"])
                for item in scene_map["scenes"]
            }
            self.assertEqual(sorted(scenes), [1, 2, 3, 4])
            batch_manifest = json.loads(
                (session / "BATCH_MANIFEST.json").read_text(encoding="utf-8")
            )
            self.assertEqual(batch_manifest["total_batches"], 1)

            for scene_index, scene_session in scenes.items():
                master = scene_session / "DIRECTOR_MASTER.md"
                master.write_text(
                    _reviewable_master(scene_index), encoding="utf-8"
                )
                self.assertEqual(
                    do_precheck(master, scene_session, batch_index=1, total_batches=1),
                    0,
                )
            record_event(
                session,
                event_type="model",
                stage="director_batch",
                model_role="director",
                model_name="deepseek-v4-pro",
                model_call_id="persistent-director-dry-run",
                input_bytes=sum(
                    (scene / "SCENE_CONTEXT.md").stat().st_size
                    for scene in scenes.values()
                ),
                output_bytes=sum(
                    (scene / "DIRECTOR_MASTER.md").stat().st_size
                    for scene in scenes.values()
                ),
            )

            batch_review = session / "batches" / "batch_001" / "dp"
            packet = prepare_batch_dp(
                1,
                session / "BATCH_MANIFEST.json",
                scenes,
                batch_review,
                cache_dir=root / "dp_cache",
            )
            self.assertEqual(len(packet["shot_ids"]), 4)
            ready = root / "DP_RESPONSE.md"
            ready.write_text(
                _ready_feedback(packet["shot_ids"]) + "\n", encoding="utf-8"
            )
            dp_state = submit_batch_dp(
                batch_review,
                ready,
                model_name="deepseek-v4-pro",
                model_call_id="fresh-dp-dry-run",
                model_elapsed_s=1.0,
            )
            self.assertEqual(dp_state["status"], "committed")

            review_dir = session / "episode_review"
            prepare_review(
                session / "BATCH_MANIFEST.json",
                session / "EPISODE_VISUAL_BIBLE.md",
                session / "EPISODE_CONTINUITY_LEDGER.md",
                scenes,
                review_dir,
            )
            review_result = root / "EPISODE_REVIEW_RESULT.md"
            review_result.write_text(
                "EPISODE REVIEW: PASS\n全片边界与视觉策略一致。\n",
                encoding="utf-8",
            )
            submit_review(review_dir, review_result)
            assemble_episode_delivery(review_dir, scenes, session)
            self.assertTrue(verify_episode_delivery(session)[0])
            self.assertEqual(
                sorted(path.name for path in (session / "delivery").iterdir()),
                ["STORYBOARD.md", "VIDEO_PROMPT.md"],
            )
            for name in ("STORYBOARD.md", "VIDEO_PROMPT.md"):
                text = (session / "delivery" / name).read_text(encoding="utf-8")
                self.assertNotRegex(text, re.compile(r"\[Director:|TIME_SKELETON|Seko"))

            self.assertEqual(run_pilot(script, session_dir=session), 0)
            root_state = json.loads(
                (session / "RUN_STATE.json").read_text(encoding="utf-8")
            )
            self.assertEqual(root_state["stage"], "delivery")
            telemetry = summarize_events(session)
            self.assertEqual(telemetry["model_calls"], {"director": 1, "dp": 1})
            self.assertGreater(telemetry["total_input_bytes"], 0)
            self.assertGreater(telemetry["total_output_bytes"], 0)
            for stage in (
                "pilot_prepare_or_refresh",
                "structural_precheck",
                "batch_dp_prepare",
                "batch_dp_submit",
                "episode_review_prepare",
                "episode_review_submit",
                "episode_delivery",
            ):
                self.assertIn(stage, telemetry["stages"])


if __name__ == "__main__":
    unittest.main()
