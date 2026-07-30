from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from director_session import (
    DirectorSessionError,
    bind_director,
    record_resume,
    verify_director,
)


class DirectorSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mode_p_director_session_")
        self.session = Path(self.temp.name) / "episode-001"
        self.session.mkdir()
        self.now = datetime(2026, 7, 18, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_one_agent_persists_across_batches_and_episode_review(self) -> None:
        bind_director(
            self.session, "director-agent-1", "deepseek-v4-pro[1m]", now=self.now
        )
        record_resume(
            self.session, "director-agent-1", "deepseek-v4-pro[1m]", "batch-002",
            now=self.now,
        )
        state = record_resume(
            self.session, "director-agent-1", "deepseek-v4-pro[1m]", "episode-review",
            now=self.now,
        )
        self.assertEqual(state["director_agent_id"], "director-agent-1")
        self.assertEqual(
            [item["event_id"] for item in state["resume_events"]],
            ["batch-002", "episode-review"],
        )

    def test_replacement_agent_or_model_is_rejected(self) -> None:
        bind_director(self.session, "director-agent-1", "model-a", now=self.now)
        with self.assertRaisesRegex(DirectorSessionError, "replacement rejected"):
            verify_director(self.session, "director-agent-2", "model-a")
        with self.assertRaisesRegex(DirectorSessionError, "model changed"):
            verify_director(self.session, "director-agent-1", "model-b")

    def test_duplicate_resume_event_is_rejected(self) -> None:
        bind_director(self.session, "director-agent-1", "model-a", now=self.now)
        record_resume(
            self.session, "director-agent-1", "model-a", "batch-002", now=self.now
        )
        with self.assertRaisesRegex(DirectorSessionError, "already recorded"):
            record_resume(
                self.session, "director-agent-1", "model-a", "batch-002", now=self.now
            )


if __name__ == "__main__":
    unittest.main()
