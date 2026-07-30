"""Tests for render_evidence.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from render_evidence import (
    EVIDENCE_SCHEMA_VERSION,
    RenderEvidence,
    UserObservation,
    ExperienceCandidate,
    validate_evidence,
    validate_candidate,
    validate_candidate_evidence,
    save_render_case,
    load_render_case,
    save_candidate,
    load_candidate,
    list_candidates,
    promote_candidate,
    rollback_promotion,
)


def _make_evidence(
    evidence_id: str = "ev-001",
    output_path: str = "",
    scene_id: str = "SCN01",
) -> RenderEvidence:
    if not output_path:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name
    return RenderEvidence(
        evidence_id=evidence_id,
        master_sha256="a" * 64,
        master_version=1,
        scene_id=scene_id,
        shot_ids=[f"{scene_id}-1", f"{scene_id}-2"],
        generation_mode="omni_reference",
        reference_assets=["REF-CHAR-001"],
        asset_versions={"REF-CHAR-001": "b" * 64},
        prompt_text="A test prompt",
        render_output_path=output_path,
        sd2_capability_version="2.0",
    )


def _make_observation(
    evidence_id: str = "ev-001",
    observation_id: str = "obs-001",
) -> UserObservation:
    return UserObservation(
        observation_id=observation_id,
        evidence_id=evidence_id,
        what_worked="Character identity preserved",
        what_failed="Hand gestures blurred",
        root_cause="Motion too fast for 15s clip",
        suggestion="Reduce action speed or split into two shots",
        confidence="high",
        observer="test-user",
    )


def _make_candidate(candidate_id: str = "cand-001") -> ExperienceCandidate:
    return ExperienceCandidate(
        candidate_id=candidate_id,
        title="Fast hand gestures cause blur in omni-reference mode",
        description="When hand gestures are too fast within a 15s omni-reference shot, "
                    "SD2.0 fails to maintain finger clarity.",
        evidence_ids=["ev-001"],
        observation_ids=["obs-001"],
        applicability="omni_reference mode with rapid hand/object interaction",
        non_applicability="Static or slow gesture shots, pure_prompt mode",
        invariants=["Shot duration <= 15s", "Omni-reference with character ref"],
        variables=["Gesture speed", "Number of hand pose changes"],
        generation_mode="omni_reference",
        reference_pattern="REF-CHAR-001:identity",
        master_version=1,
        asset_versions={"REF-CHAR-001": "b" * 64},
    )


def _make_repeated_ready_candidate(candidate_id: str = "cand-ready") -> ExperienceCandidate:
    cand = _make_candidate(candidate_id)
    cand.evidence_ids = ["ev-001", "ev-002"]
    cand.observation_ids = ["obs-001", "obs-002"]
    return cand


def _save_render_case(
    base: Path,
    evidence_id: str,
    observation_id: str,
    scene_id: str,
) -> None:
    save_render_case(
        _make_evidence(evidence_id=evidence_id, scene_id=scene_id),
        [_make_observation(evidence_id, observation_id)],
        base_dir=base,
    )


def _save_two_render_cases(base: Path, *, same_scene: bool = False) -> None:
    _save_render_case(base, "ev-001", "obs-001", "SCN01")
    _save_render_case(base, "ev-002", "obs-002", "SCN01" if same_scene else "SCN02")


class RenderEvidenceTests(unittest.TestCase):

    def test_validate_valid_evidence(self) -> None:
        ev = _make_evidence()
        errors = validate_evidence(ev)
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

    def test_validate_rejects_missing_master_sha256(self) -> None:
        ev = _make_evidence()
        ev.master_sha256 = "short"
        errors = validate_evidence(ev)
        self.assertGreater(len(errors), 0)

    def test_validate_rejects_missing_render_output(self) -> None:
        ev = _make_evidence()
        ev.render_output_path = "/nonexistent/path.png"
        errors = validate_evidence(ev)
        self.assertGreater(len(errors), 0)

    def test_validate_rejects_missing_reference_asset_version(self) -> None:
        ev = _make_evidence()
        ev.asset_versions = {}
        errors = validate_evidence(ev)
        self.assertGreater(len(errors), 0)

    def test_validate_rejects_unknown_generation_mode(self) -> None:
        ev = _make_evidence()
        ev.generation_mode = "unknown_mode"
        errors = validate_evidence(ev)
        self.assertGreater(len(errors), 0)

    def test_save_and_load_render_case_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render_case_") as tmp:
            base = Path(tmp)
            ev = _make_evidence()
            obs = _make_observation()
            case_dir = save_render_case(ev, [obs], base_dir=base)
            self.assertTrue((case_dir / "evidence.json").exists())
            self.assertTrue((case_dir / "observations.json").exists())
            loaded_ev, loaded_obs = load_render_case(ev.evidence_id, base_dir=base)
            self.assertEqual(loaded_ev.evidence_id, ev.evidence_id)
            self.assertEqual(loaded_ev.master_sha256, ev.master_sha256)
            self.assertEqual(len(loaded_obs), 1)
            self.assertEqual(loaded_obs[0].what_worked, "Character identity preserved")

    def test_observation_must_reference_correct_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render_obs_") as tmp:
            base = Path(tmp)
            ev = _make_evidence("ev-001")
            obs = _make_observation("ev-002")  # wrong evidence_id
            with self.assertRaises(ValueError):
                save_render_case(ev, [obs], base_dir=base)


class ExperienceCandidateTests(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="experience_")
        self.base = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_validate_valid_candidate(self) -> None:
        cand = _make_candidate()
        errors = validate_candidate(cand)
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

    def test_validate_rejects_empty_evidence(self) -> None:
        cand = _make_candidate()
        cand.evidence_ids = []
        errors = validate_candidate(cand)
        self.assertGreater(len(errors), 0)

    def test_validate_rejects_missing_applicability(self) -> None:
        cand = _make_candidate()
        cand.applicability = ""
        errors = validate_candidate(cand)
        self.assertGreater(len(errors), 0)

    def test_validate_rejects_rejected_without_reason(self) -> None:
        cand = _make_candidate()
        cand.status = "rejected"
        errors = validate_candidate(cand)
        self.assertGreater(len(errors), 0)

    def test_save_and_load_candidate_roundtrip(self) -> None:
        cand = _make_candidate()
        path = save_candidate(cand, base_dir=self.base)
        self.assertTrue(path.exists())
        loaded = load_candidate(cand.candidate_id, base_dir=self.base)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.title, cand.title)  # type: ignore[union-attr]
        self.assertEqual(loaded.status, "candidate")

    def test_list_candidates(self) -> None:
        for i in range(3):
            cand = _make_candidate(f"cand-{i:03d}")
            save_candidate(cand, base_dir=self.base)
        ids = list_candidates("candidate", base_dir=self.base)
        self.assertEqual(len(ids), 3)

    def test_promote_candidate_to_repeated(self) -> None:
        _save_two_render_cases(self.base)
        cand = _make_repeated_ready_candidate("promo-001")
        save_candidate(cand, base_dir=self.base)
        promoted = promote_candidate("promo-001", "repeated", base_dir=self.base)
        loaded = load_candidate("promo-001", base_dir=self.base)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.status, "repeated")  # type: ignore[union-attr]
        self.assertGreaterEqual(len(loaded.promotion_log), 1)  # type: ignore[union-attr]

    def test_promote_repeated_to_validated(self) -> None:
        _save_two_render_cases(self.base)
        cand = _make_repeated_ready_candidate("promo-002")
        cand.status = "repeated"
        save_candidate(cand, base_dir=self.base)
        promote_candidate(
            "promo-002",
            "validated",
            base_dir=self.base,
            approved_by="test-user",
            regression_report={"command": "python -m pytest mode_p", "passed": True},
        )
        loaded = load_candidate("promo-002", base_dir=self.base)
        self.assertEqual(loaded.status, "validated")  # type: ignore[union-attr]
        self.assertEqual(
            loaded.promotion_log[-1]["approved_by"], "test-user"  # type: ignore[union-attr]
        )

    def test_validated_requires_two_different_scenes(self) -> None:
        _save_two_render_cases(self.base, same_scene=True)
        cand = _make_repeated_ready_candidate("promo-same-scene")
        cand.status = "repeated"
        save_candidate(cand, base_dir=self.base)
        with self.assertRaises(ValueError):
            promote_candidate(
                "promo-same-scene",
                "validated",
                base_dir=self.base,
                approved_by="test-user",
                regression_report={"command": "pytest", "passed": True},
            )

    def test_invalid_promotion_blocked(self) -> None:
        cand = _make_candidate("promo-003")
        save_candidate(cand, base_dir=self.base)
        with self.assertRaises(ValueError):
            promote_candidate("promo-003", "validated", base_dir=self.base)

    def test_repeated_requires_multiple_evidence(self) -> None:
        cand = _make_candidate("promo-single")
        save_candidate(cand, base_dir=self.base)
        with self.assertRaises(ValueError):
            promote_candidate("promo-single", "repeated", base_dir=self.base)

    def test_repeated_requires_real_render_cases(self) -> None:
        cand = _make_repeated_ready_candidate("promo-no-cases")
        save_candidate(cand, base_dir=self.base)
        with self.assertRaises(ValueError):
            promote_candidate("promo-no-cases", "repeated", base_dir=self.base)

    def test_candidate_evidence_rejects_unknown_observation(self) -> None:
        _save_two_render_cases(self.base)
        cand = _make_repeated_ready_candidate("bad-observation")
        cand.observation_ids = ["obs-001", "obs-missing"]
        errors, _scene_ids = validate_candidate_evidence(cand, base_dir=self.base)
        self.assertGreater(len(errors), 0)

    def test_validated_requires_human_approval_and_regression(self) -> None:
        cand = _make_repeated_ready_candidate("promo-approval")
        cand.status = "repeated"
        save_candidate(cand, base_dir=self.base)
        with self.assertRaises(ValueError):
            promote_candidate(
                "promo-approval",
                "validated",
                base_dir=self.base,
                regression_report={"command": "pytest", "passed": True},
            )
        with self.assertRaises(ValueError):
            promote_candidate(
                "promo-approval",
                "validated",
                base_dir=self.base,
                approved_by="test-user",
                regression_report={"command": "pytest", "passed": False},
            )

    def test_save_validated_without_promotion_log_is_rejected(self) -> None:
        cand = _make_repeated_ready_candidate("bad-validated")
        cand.status = "validated"
        with self.assertRaises(ValueError):
            save_candidate(cand, base_dir=self.base)

    def test_rollback_promotion_restores_previous_status(self) -> None:
        _save_two_render_cases(self.base)
        cand = _make_repeated_ready_candidate("rollback-001")
        save_candidate(cand, base_dir=self.base)
        promote_candidate("rollback-001", "repeated", base_dir=self.base)
        self.assertEqual(
            load_candidate("rollback-001", base_dir=self.base).status,  # type: ignore[union-attr]
            "repeated",
        )
        restored = rollback_promotion("rollback-001", base_dir=self.base)
        self.assertEqual(restored.status, "candidate")
        self.assertIsNotNone(load_candidate("rollback-001", base_dir=self.base))

    def test_rejected_can_be_reopened(self) -> None:
        cand = _make_candidate("promo-004")
        cand.status = "rejected"
        cand.rejection_reason = "Insufficient evidence"
        save_candidate(cand, base_dir=self.base)
        promote_candidate("promo-004", "candidate", base_dir=self.base)
        loaded = load_candidate("promo-004", base_dir=self.base)
        self.assertEqual(loaded.status, "candidate")  # type: ignore[union-attr]

    def test_schema_version_in_saved_output(self) -> None:
        cand = _make_candidate("schema-test")
        path = save_candidate(cand, base_dir=self.base)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], EVIDENCE_SCHEMA_VERSION)


class EvidenceCLITests(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="render_ev_cli_")
        self.base = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_cli_list_empty(self) -> None:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "render_evidence", "list"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertIn(result.returncode, (0,))
        self.assertIn("(no candidate", result.stdout)

    def test_cli_validate_missing(self) -> None:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "render_evidence", "validate", "nonexistent"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
