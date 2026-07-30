"""Tests for pipeline_telemetry.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pipeline_telemetry import (
    Telemetry,
    TelemetrySession,
    load_events,
    record_event,
    summarize_events,
)


class TelemetryTests(unittest.TestCase):

    def test_records_stage_timing(self) -> None:
        session = TelemetrySession(session_id="test-1", script_sha256="a" * 64)
        telemetry = Telemetry(session)
        telemetry.start_stage("script_ingest")
        telemetry.end_stage(input_bytes=1024, output_bytes=512, cache_miss=True)
        telemetry.start_stage("master_compile")
        telemetry.end_stage(input_bytes=2048, output_bytes=1024, cache_hit=True)
        self.assertEqual(len(session.stages), 2)
        self.assertGreaterEqual(session.stages[0].elapsed_s, 0)
        self.assertTrue(session.stages[1].cache_hit)

    def test_write_and_load_roundtrip(self) -> None:
        session = TelemetrySession(session_id="rtt", script_sha256="b" * 64)
        telemetry = Telemetry(session)
        telemetry.start_stage("test")
        telemetry.end_stage(input_bytes=100, output_bytes=200)
        telemetry.finish()
        with tempfile.TemporaryDirectory(prefix="telemetry_") as tmp:
            path = Path(tmp) / "report.json"
            telemetry.write_report(path)
            self.assertTrue(path.exists())
            loaded = Telemetry.load(path)
            self.assertEqual(loaded.session_id, "rtt")
            self.assertEqual(len(loaded.stages), 1)

    def test_error_recording(self) -> None:
        session = TelemetrySession(session_id="err")
        telemetry = Telemetry(session)
        telemetry.start_stage("failing_stage")
        telemetry.end_stage(error="Simulated failure")
        self.assertEqual(session.stages[0].error, "Simulated failure")

    def test_immutable_events_summarize_calls_cache_and_scope_without_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="telemetry_events_") as tmp:
            root = Path(tmp)
            record_event(
                root, event_type="model", stage="director_batch",
                model_role="director", model_name="deepseek-v4-pro",
                model_call_id="director-call-1", input_bytes=1000,
                output_bytes=500, elapsed_s=2.5,
            )
            record_event(
                root, event_type="model", stage="director_batch",
                model_role="director", model_name="deepseek-v4-pro",
                model_call_id="director-call-1", input_bytes=1000,
                output_bytes=500, elapsed_s=2.5,
            )
            record_event(
                root, event_type="cache", stage="dp_review",
                cache_status="hit",
            )
            record_event(
                root, event_type="invalidation", stage="dependency_invalidation",
                invalidation_scope=["SCN2/master", "SCN2/views"],
            )
            summary = summarize_events(root)
            self.assertEqual(summary["model_calls"], {"director": 1, "dp": 0})
            self.assertEqual(summary["cache"]["hit"], 1)
            self.assertEqual(
                summary["invalidation_scope"], ["SCN2/master", "SCN2/views"]
            )
            serialized = json.dumps(load_events(root), ensure_ascii=False)
            self.assertNotIn("director-call-1", serialized)

    def test_concurrent_safe_event_names_do_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory(prefix="telemetry_unique_") as tmp:
            root = Path(tmp)
            for _ in range(20):
                record_event(root, event_type="local", stage="precheck")
            self.assertEqual(len(load_events(root)), 20)


if __name__ == "__main__":
    unittest.main()
