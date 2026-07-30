from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from batch_state_machine import load_state
from run_mode_p import do_precheck, initialise, submit
from test_structural_precheck import _VALID_MASTER


READY = (
    "READY PRE: Shot PRE-1 keeps the camera path inside the room and the "
    "ceiling light remains physically anchored across the shot."
)


class ModePLoopTests(unittest.TestCase):

    def _prepare(self, root: Path, master_text: str = _VALID_MASTER) -> tuple[Path, Path]:
        context = root / "context.md"
        master = root / "master.md"
        session = root / "session"
        context.write_text("# Scene Context\n", encoding="utf-8")
        master.write_text(master_text, encoding="utf-8")
        self.assertEqual(initialise(context, session), 0)
        self.assertEqual(do_precheck(master, session), 0)
        self.assertEqual(load_state(session).stage, "dp_batch")
        return session, master

    def test_ready_delivers_only_two_master_derived_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, master = self._prepare(root)
            feedback = root / "feedback.md"
            feedback.write_text(READY, encoding="utf-8")
            working = session / "working"
            self.assertEqual(submit(
                session,
                working / "STORYBOARD.md",
                working / "VIDEO_PROMPT.md",
                feedback,
                master,
            ), 0)
            self.assertEqual(
                sorted(path.name for path in (session / "delivery").iterdir()),
                ["STORYBOARD.md", "VIDEO_PROMPT.md"],
            )
            self.assertEqual(load_state(session).stage, "batch_commit")

    def test_submit_before_master_precheck_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = root / "context.md"
            session = root / "session"
            context.write_text("# Scene Context\n", encoding="utf-8")
            self.assertEqual(initialise(context, session), 0)
            for name, body in (
                ("storyboard.md", "# Storyboard\n"),
                ("video.md", "## Shot PRE-1 | 8s\nImage: test\n"),
                ("feedback.md", READY),
            ):
                (root / name).write_text(body, encoding="utf-8")
            self.assertEqual(submit(
                session, root / "storyboard.md", root / "video.md",
                root / "feedback.md",
            ), 1)
            self.assertFalse((session / "delivery").exists())

    def test_valid_issue_requests_master_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, master = self._prepare(root)
            feedback = root / "feedback.md"
            feedback.write_text(
                "PRE-1: light_source — 主光方向在当前空间描述中没有物理来源。\n",
                encoding="utf-8",
            )
            working = session / "working"
            self.assertEqual(submit(
                session, working / "STORYBOARD.md", working / "VIDEO_PROMPT.md",
                feedback, master,
            ), 1)
            self.assertTrue((session / "DIRECTOR_REVISION_REQUEST.md").is_file())
            self.assertEqual(load_state(session).stage, "director_batch")

    def test_malformed_dp_feedback_does_not_advance_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, master = self._prepare(root)
            feedback = root / "feedback.md"
            feedback.write_text(
                "Shot PRE-1 has no physical light source.", encoding="utf-8"
            )
            working = session / "working"
            self.assertEqual(submit(
                session, working / "STORYBOARD.md", working / "VIDEO_PROMPT.md",
                feedback, master,
            ), 1)
            self.assertEqual(load_state(session).stage, "dp_batch")
            self.assertIsNone(load_state(session).dp_review)

    def test_independently_authored_view_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, master = self._prepare(root)
            fake = root / "fake_storyboard.md"
            fake.write_text("# independently authored\n", encoding="utf-8")
            feedback = root / "feedback.md"
            feedback.write_text(READY, encoding="utf-8")
            working = session / "working"
            self.assertEqual(submit(
                session, fake, working / "VIDEO_PROMPT.md", feedback, master,
            ), 1)
            self.assertEqual(load_state(session).stage, "dp_batch")

    def test_hard_prompt_error_blocks_before_dp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = _VALID_MASTER.replace(
                "[4.0s] Miguel 转头观察房间。",
                "[4.0s] 不要抖动。",
            )
            context = root / "context.md"
            master = root / "master.md"
            session = root / "session"
            context.write_text("# Scene Context\n", encoding="utf-8")
            master.write_text(bad, encoding="utf-8")
            self.assertEqual(initialise(context, session), 0)
            self.assertEqual(do_precheck(master, session), 1)
            self.assertEqual(load_state(session).stage, "director_batch")
            self.assertIn(
                "sd2_preflight",
                (session / "CHECK_REPORT.md").read_text(encoding="utf-8"),
            )

    def test_repeated_issue_with_unchanged_master_blocks_loop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, master = self._prepare(root)
            feedback = root / "feedback.md"
            feedback.write_text(
                "PRE-1: camera_path — 摄影路径与桌面占位发生冲突。\n",
                encoding="utf-8",
            )
            working = session / "working"
            self.assertEqual(submit(
                session, working / "STORYBOARD.md", working / "VIDEO_PROMPT.md",
                feedback, master,
            ), 1)
            self.assertEqual(do_precheck(master, session), 0)
            working = session / "working"
            self.assertEqual(submit(
                session, working / "STORYBOARD.md", working / "VIDEO_PROMPT.md",
                feedback, master,
            ), 3)
            self.assertEqual(load_state(session).dp_review["status"], "blocked")

    def test_ready_feedback_accepts_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session, master = self._prepare(root)
            feedback = root / "feedback.md"
            feedback.write_text("\ufeff" + READY, encoding="utf-8")
            working = session / "working"
            self.assertEqual(submit(
                session, working / "STORYBOARD.md", working / "VIDEO_PROMPT.md",
                feedback, master,
            ), 0)


if __name__ == "__main__":
    unittest.main()
