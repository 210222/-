"""Tests for evidence-bound model allocation benchmark."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from benchmark_harness import (
    RUN_RECORD_SCHEMA_VERSION,
    BenchmarkReport,
    ModelRunRecord,
    allocation_advice,
    load_model_run_records,
    run_benchmarks,
)


class BenchmarkHarnessTests(unittest.TestCase):
    def test_fixed_regressions_pass_and_cover_director_and_dp(self) -> None:
        report = run_benchmarks(iterations=1)
        self.assertTrue(report.ok, [item.to_dict() for item in report.results])
        self.assertIn("director_structural_regression", report.case_ids("director"))
        self.assertEqual(
            report.case_ids("dp"),
            {"dp_ready_clean", "dp_expected_issues", "dp_rejects_unknown_shot"},
        )
        director = next(item for item in report.results if item.role == "director")
        self.assertTrue(director.checks["master_compiler"])
        self.assertTrue(director.checks["view_deriver"])
        self.assertTrue(director.checks["master_sync_check"])
        self.assertTrue(director.checks["sd2_preflight"])

    def test_json_serializable(self) -> None:
        report = run_benchmarks(iterations=1)
        text = json.dumps(report.to_dict(), ensure_ascii=False)
        self.assertIn("schema_version", text)
        self.assertIn("director_structural_regression", text)

    def test_no_real_model_records_means_no_dp_downgrade(self) -> None:
        report = run_benchmarks(iterations=1)
        advice = allocation_advice(report, [])
        self.assertEqual(advice["status"], "insufficient_evidence")
        self.assertEqual(advice["dp_model"], "retain_current_dp_model_until_real_evidence")
        self.assertNotIn("deepseek", json.dumps(advice, ensure_ascii=False).lower())

    def test_dp_candidate_requires_complete_passing_faster_evidence(self) -> None:
        report = run_benchmarks(iterations=1)
        case_ids = sorted(report.case_ids("dp"))
        records = []
        for case_id in case_ids:
            records.append(_record("dp-baseline", case_id, 2.0, True))
            records.append(_record("dp-fast", case_id, 0.8, True))
        advice = allocation_advice(report, records, current_dp_model="dp-baseline")
        self.assertEqual(advice["status"], "eligible")
        self.assertEqual(advice["dp_model"], "dp-fast")

    def test_failed_or_incomplete_candidate_is_not_eligible(self) -> None:
        report = run_benchmarks(iterations=1)
        case_ids = sorted(report.case_ids("dp"))
        records = []
        for case_id in case_ids:
            records.append(_record("dp-baseline", case_id, 2.0, True))
        records.append(_record("dp-fast", case_ids[0], 0.5, True))
        records.append(_record("dp-fast", case_ids[1], 0.5, False))
        advice = allocation_advice(report, records, current_dp_model="dp-baseline")
        self.assertEqual(advice["status"], "retain")
        self.assertEqual(advice["dp_model"], "dp-baseline")

    def test_load_real_run_records(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mode_p_run_records_") as temp:
            root = Path(temp)
            record = _record("dp-baseline", "dp_ready_clean", 1.2, True)
            (root / "run.json").write_text(
                json.dumps(record.to_dict(), ensure_ascii=False),
                encoding="utf-8",
            )
            (root / "ignore.json").write_text(
                json.dumps({"schema_version": "other"}),
                encoding="utf-8",
            )
            loaded = load_model_run_records(root)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].model, "dp-baseline")

    def test_cli_json_advice(self) -> None:
        result = subprocess.run(
            [
                sys.executable, "-m", "benchmark_harness",
                "--iterations", "1", "--json", "--advice",
            ],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["allocation_advice"]["status"], "insufficient_evidence")


def _record(model: str, case_id: str, elapsed: float, passed: bool) -> ModelRunRecord:
    return ModelRunRecord(
        schema_version=RUN_RECORD_SCHEMA_VERSION,
        role="dp",
        model=model,
        case_id=case_id,
        input_hash="a" * 64,
        output_hash="b" * 64,
        elapsed_s=elapsed,
        passed=passed,
    )


if __name__ == "__main__":
    unittest.main()
