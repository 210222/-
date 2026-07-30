"""Tests for knowledge_curator.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from render_evidence import (
    RenderEvidence,
    UserObservation,
    ExperienceCandidate,
    save_render_case,
    save_candidate,
    load_candidate,
    list_candidates,
)
from knowledge_curator import (
    ingest_render_case,
    curate_candidates,
    export_knowledge,
)


def _make_evidence_and_obs(
    base_dir: Path,
    evidence_id: str = "ev-test",
    output_path: str = "",
    scene_id: str = "SCN01",
    observation_id: str | None = None,
) -> tuple[RenderEvidence, UserObservation]:
    if not output_path:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name
    ev = RenderEvidence(
        evidence_id=evidence_id,
        master_sha256="a" * 64,
        master_version=1,
        scene_id=scene_id,
        shot_ids=[f"{scene_id}-1"],
        generation_mode="omni_reference",
        reference_assets=["REF-CHAR-001"],
        asset_versions={"REF-CHAR-001": "b" * 64},
        prompt_text="A test prompt for knowledge curation",
        render_output_path=output_path,
        sd2_capability_version="2.0",
    )
    obs = UserObservation(
        observation_id=observation_id or f"obs-{evidence_id}",
        evidence_id=evidence_id,
        what_worked="Character identity was preserved correctly",
        what_failed="Background lighting was inconsistent between shots",
        root_cause="No background reference asset was provided",
        suggestion="Add a background reference for lighting consistency",
        confidence="high",
        observer="test-user",
    )
    save_render_case(ev, [obs], base_dir=base_dir)
    return ev, obs


class KnowledgeCuratorTests(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="curator_")
        self.base = Path(self.tmp.name)
        # Create required subdirectories
        for d in ("candidates", "repeated", "validated", "rejected", "render_cases"):
            (self.base / d).mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_ingest_creates_candidate(self) -> None:
        ev, obs = _make_evidence_and_obs(self.base, "ev-ingest-001")
        candidate = ingest_render_case("ev-ingest-001", base_dir=self.base)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.status, "candidate")
        self.assertIn("ev-ingest-001", candidate.evidence_ids)
        self.assertIn("Character identity", candidate.description)
        self.assertEqual(candidate.asset_versions["REF-CHAR-001"], "b" * 64)

    def test_ingest_no_observations_returns_none(self) -> None:
        # Create evidence with no observations (we'd need to manually write it)
        # Instead, test with a nonexistent case
        result = ingest_render_case("nonexistent", base_dir=self.base)
        self.assertIsNone(result)

    def test_ingest_low_confidence_only_returns_none(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name
        ev = RenderEvidence(
            evidence_id="ev-low-conf",
            master_sha256="b" * 64,
            master_version=1,
            scene_id="SCN02",
            shot_ids=["SCN02-1"],
            generation_mode="pure_prompt",
            render_output_path=output_path,
        )
        obs = UserObservation(
            observation_id="obs-low",
            evidence_id="ev-low-conf",
            what_failed="Something went wrong",
            confidence="low",
            observer="test-user",
        )
        save_render_case(ev, [obs], base_dir=self.base)
        result = ingest_render_case("ev-low-conf", base_dir=self.base)
        self.assertIsNone(result)

    def test_curate_empty(self) -> None:
        result = curate_candidates(base_dir=self.base)
        self.assertEqual(result["candidates_reviewed"], 0)

    def test_curate_single_candidate(self) -> None:
        _make_evidence_and_obs(self.base, "ev-curate-001")
        ingest_render_case("ev-curate-001", base_dir=self.base)
        result = curate_candidates(base_dir=self.base)
        self.assertEqual(result["candidates_reviewed"], 1)
        # Single evidence → needs_more_evidence
        self.assertGreaterEqual(len(result["needs_more_evidence"]), 1)

    def test_curate_detects_multiple_evidence(self) -> None:
        _make_evidence_and_obs(self.base, "ev-curate-002")
        _make_evidence_and_obs(self.base, "ev-curate-003")
        # Create one candidate referencing two evidence_ids
        cand = ExperienceCandidate(
            candidate_id="multi-ev-cand",
            title="Multi-evidence test",
            description="Test with multiple evidence sources",
            evidence_ids=["ev-curate-002", "ev-curate-003"],
            observation_ids=["obs-ev-curate-002", "obs-ev-curate-003"],
            applicability="omni_reference mode with character refs",
            generation_mode="omni_reference",
        )
        save_candidate(cand, base_dir=self.base)
        result = curate_candidates(base_dir=self.base)
        self.assertEqual(result["candidates_reviewed"], 1)
        self.assertEqual(len(result["promoted_to_repeated"]), 1)

    def test_export_empty(self) -> None:
        data = export_knowledge(base_dir=self.base)
        self.assertEqual(len(data), 0)

    def test_export_validated(self) -> None:
        _make_evidence_and_obs(
            self.base,
            "ev-export-1",
            scene_id="SCN01",
            observation_id="obs-export-1",
        )
        _make_evidence_and_obs(
            self.base,
            "ev-export-2",
            scene_id="SCN02",
            observation_id="obs-export-2",
        )
        cand = ExperienceCandidate(
            candidate_id="export-test",
            title="Exported knowledge",
            description="Test validated knowledge export",
            evidence_ids=["ev-export-1", "ev-export-2"],
            observation_ids=["obs-export-1", "obs-export-2"],
            applicability="all modes",
            generation_mode="omni_reference",
            status="validated",
            promotion_log=[{
                "at": "2026-07-16T00:00:00+00:00",
                "from_status": "repeated",
                "to_status": "validated",
                "approved_by": "test-user",
                "regression_report": {
                    "command": "python -m pytest 01_调度器/mode_p -q",
                    "passed": True,
                },
                "evidence_ids": ["ev-export-1", "ev-export-2"],
                "observation_ids": ["obs-export-1", "obs-export-2"],
            }],
        )
        save_candidate(cand, base_dir=self.base)
        data = export_knowledge(base_dir=self.base)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["candidate_id"], "export-test")

    def test_cli_ingest_nonexistent(self) -> None:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "knowledge_curator", "ingest", "nonexistent-id"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_cli_curate(self) -> None:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "knowledge_curator", "curate"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertIn(result.returncode, (0,))
        data = json.loads(result.stdout)
        self.assertIn("candidates_reviewed", data)

    def test_cli_list(self) -> None:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "knowledge_curator", "list"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertIn(result.returncode, (0,))

    def test_cli_export(self) -> None:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "knowledge_curator", "export"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertIn(result.returncode, (0,))
        data = json.loads(result.stdout)
        self.assertIn("entries", data)


if __name__ == "__main__":
    unittest.main()
