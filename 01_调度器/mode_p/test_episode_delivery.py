from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from episode_delivery import (
    EpisodeDeliveryError,
    assemble_episode_delivery,
    recover_episode_delivery,
    verify_episode_delivery,
)
from episode_review import prepare_review, submit_review
from test_episode_review import _inputs, _result, _rewrite_scene


class EpisodeDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prefix = next(tempfile._get_candidate_names())
        (
            self.manifest,
            self.bible,
            self.ledger,
            self.sessions,
            self.review,
        ) = _inputs(f"delivery_{self.prefix}")
        self.episode = Path(tempfile.mkdtemp(prefix="mode_p_episode_delivery_"))

    def _pass_review(self) -> None:
        prepare_review(
            self.manifest, self.bible, self.ledger, self.sessions, self.review
        )
        submit_review(
            self.review,
            _result(
                f"delivery_pass_{self.prefix}.md",
                "EPISODE REVIEW: PASS\n全片边界与连续性通过。\n",
            ),
        )

    def test_current_pass_assembles_exactly_two_files_in_scene_order(self) -> None:
        self._pass_review()
        assemble_episode_delivery(self.review, self.sessions, self.episode)
        delivery = self.episode / "delivery"
        self.assertEqual(
            sorted(path.name for path in delivery.iterdir()),
            ["STORYBOARD.md", "VIDEO_PROMPT.md"],
        )
        story = (delivery / "STORYBOARD.md").read_text(encoding="utf-8")
        self.assertLess(story.index("scene 1"), story.index("scene 2"))
        video = (delivery / "VIDEO_PROMPT.md").read_text(encoding="utf-8")
        for final_text in (story, video):
            self.assertNotIn("episode_review_input", final_text)
            self.assertNotIn("assembly: deterministic", final_text)
            self.assertNotIn("source_sha256", final_text)
        self.assertEqual(
            verify_episode_delivery(self.episode),
            (True, "Episode delivery is current and contains exactly two files"),
        )

    def test_delivery_rejects_missing_or_stale_review_pass(self) -> None:
        with self.assertRaises(EpisodeDeliveryError):
            assemble_episode_delivery(self.review, self.sessions, self.episode)
        self._pass_review()
        _rewrite_scene(self.sessions[1], 1, 1)
        with self.assertRaises(EpisodeDeliveryError):
            assemble_episode_delivery(self.review, self.sessions, self.episode)

    def test_recovery_finishes_interruption_after_backup(self) -> None:
        self._pass_review()
        assemble_episode_delivery(self.review, self.sessions, self.episode)
        _rewrite_scene(self.sessions[1], 1, 1)
        prepare_review(
            self.manifest, self.bible, self.ledger, self.sessions, self.review
        )
        submit_review(
            self.review,
            _result(
                f"delivery_repass_{self.prefix}.md",
                "EPISODE REVIEW: PASS\n修订版本已通过。\n",
            ),
        )
        with self.assertRaises(EpisodeDeliveryError):
            assemble_episode_delivery(
                self.review, self.sessions, self.episode,
                failpoint="after_backup",
            )
        recover_episode_delivery(self.episode)
        self.assertTrue(verify_episode_delivery(self.episode)[0])
        self.assertIn(
            "revision 1",
            (self.episode / "delivery" / "STORYBOARD.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_recovery_finalizes_interruption_after_publish(self) -> None:
        self._pass_review()
        with self.assertRaises(EpisodeDeliveryError):
            assemble_episode_delivery(
                self.review, self.sessions, self.episode,
                failpoint="after_publish",
            )
        recover_episode_delivery(self.episode)
        self.assertTrue(verify_episode_delivery(self.episode)[0])
        self.assertFalse(
            (self.episode / "EPISODE_DELIVERY_PENDING.json").exists()
        )


if __name__ == "__main__":
    unittest.main()
