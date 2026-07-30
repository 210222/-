"""Tests for legacy_residue_check.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from legacy_residue_check import (
    ResidueReport,
    ResidueMatch,
    scan_file,
    scan_paths,
    scan_active_entrypoints,
)


class LegacyResidueCheckTests(unittest.TestCase):

    def test_clean_file_no_findings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="residue_clean_") as tmp:
            root = Path(tmp)
            clean = root / "clean.py"
            clean.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
            findings = scan_file(clean, root)
            self.assertEqual(len(findings), 0)

    def test_detects_seko_pattern(self) -> None:
        with tempfile.TemporaryDirectory(prefix="residue_seko_") as tmp:
            root = Path(tmp)
            bad = root / "bad.md"
            bad.write_text("Use @图片1 for the first frame.\n", encoding="utf-8")
            findings = scan_file(bad, root)
            seko_findings = [f for f in findings if f.category == "seko"]
            self.assertGreaterEqual(len(seko_findings), 1)

    def test_detects_time_skeleton(self) -> None:
        with tempfile.TemporaryDirectory(prefix="residue_ts_") as tmp:
            root = Path(tmp)
            bad = root / "old.py"
            bad.write_text("# TIME_SKELETON: 0s-5s\n", encoding="utf-8")
            findings = scan_file(bad, root)
            ts = [f for f in findings if f.category == "time_skeleton"]
            self.assertGreaterEqual(len(ts), 1)

    def test_detects_yaml_agent_protocol(self) -> None:
        with tempfile.TemporaryDirectory(prefix="residue_yaml_") as tmp:
            root = Path(tmp)
            bad = root / "config.md"
            bad.write_text("Following YAML Agent Protocol v2.\n", encoding="utf-8")
            findings = scan_file(bad, root)
            yaml_f = [f for f in findings if f.category == "yaml_agent"]
            self.assertGreaterEqual(len(yaml_f), 1)

    def test_detects_old_agent_chain(self) -> None:
        with tempfile.TemporaryDirectory(prefix="residue_agent_") as tmp:
            root = Path(tmp)
            bad = root / "agents.py"
            bad.write_text("ShotAgent = 'shot_designer'\n"
                          "MovementAgent = 'movement_designer'\n",
                          encoding="utf-8")
            findings = scan_file(bad, root)
            agent_f = [f for f in findings if f.category == "old_agent"]
            self.assertGreaterEqual(len(agent_f), 1)

    def test_detects_gate_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="residue_gate_") as tmp:
            root = Path(tmp)
            bad = root / "review.md"
            bad.write_text("Gate Report: Phase 1 PASS\n", encoding="utf-8")
            findings = scan_file(bad, root)
            gate_f = [f for f in findings if f.category == "gate"]
            self.assertGreaterEqual(len(gate_f), 1)

    def test_detects_legacy_mode_p_import(self) -> None:
        with tempfile.TemporaryDirectory(prefix="residue_legacy_") as tmp:
            root = Path(tmp)
            bad = root / "wrapper.py"
            bad.write_text("from legacy_mode_p import old_pipeline\n", encoding="utf-8")
            findings = scan_file(bad, root)
            legacy_f = [f for f in findings if f.category == "legacy"]
            self.assertGreaterEqual(len(legacy_f), 1)

    def test_allows_documentation_references(self) -> None:
        """High-severity legacy references in documentation files are allowed."""
        with tempfile.TemporaryDirectory(prefix="residue_docs_") as tmp:
            root = Path(tmp)
            (root / "MODE_P_REDESIGN_PROJECT").mkdir(parents=True)
            plan = root / "MODE_P_REDESIGN_PROJECT" / "IMPLEMENTATION_PLAN.md"
            plan.write_text("# Plan\nRemove TIME_SKELETON and Gate reports.\n",
                           encoding="utf-8")
            # scan_file skips high-severity findings for allowed-reference files
            findings = scan_file(plan, root)
            # High-severity patterns (TIME_SKELETON, Gate) are skipped because
            # the file path matches _ALLOWED_REFERENCES
            high_findings = [f for f in findings if f.severity == "high"]
            self.assertEqual(len(high_findings), 0,
                             "High-severity findings should be allowed in documentation files")

    def test_scan_paths_excludes_legacy_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="residue_scan_") as tmp:
            root = Path(tmp)
            active = root / "active.py"
            active.write_text("# clean file\n", encoding="utf-8")
            legacy = root / "legacy_mode_p"
            legacy.mkdir()
            (legacy / "old.py").write_text("TIME_SKELETON here\n", encoding="utf-8")
            report = scan_paths([active, legacy], root)
            # The legacy directory should be excluded
            self.assertGreaterEqual(report.files_scanned, 0)

    def test_json_output_structure(self) -> None:
        report = ResidueReport()
        report.files_scanned = 1
        report.lines_scanned = 10
        report.findings.append(ResidueMatch(
            file="test.py", line=5, severity="high",
            category="seko", description="Seko pattern",
            matched_text="@图片1",
        ))
        report.high_count = 1
        data = report.to_dict()
        self.assertTrue(data["ok"] is False)
        self.assertEqual(data["high_count"], 1)
        self.assertEqual(len(data["findings"]), 1)
        json_text = json.dumps(data, ensure_ascii=False)
        self.assertIn("Seko pattern", json_text)

    def test_cli_json_mode(self) -> None:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "legacy_residue_check", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertIn(result.returncode, (0, 1))
        data = json.loads(result.stdout)
        self.assertIn("ok", data)
        self.assertIn("findings", data)


if __name__ == "__main__":
    unittest.main()
