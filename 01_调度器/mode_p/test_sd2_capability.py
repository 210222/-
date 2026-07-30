"""Tests for the evidence-bound SD2 capability profile."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sd2_capability_manager import get_hash, validate_profile


_PROFILE = Path(__file__).with_name("sd2_capability_profile.json")


class ProfileTests(unittest.TestCase):
    def test_profile_is_strictly_valid(self) -> None:
        ok, issues = validate_profile(_PROFILE)
        self.assertTrue(ok, issues)

    def test_director_owns_mode_selection(self) -> None:
        data = json.loads(_PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(data["product"]["mode_selection_owner"], "director")
        self.assertEqual(data["mode_contract"]["selection"], "exactly_one_per_shot")

    def test_all_three_modes_have_evidence_bound_limits(self) -> None:
        data = json.loads(_PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(set(data["modes"]), {
            "text_only", "first_last_frame", "omni_reference"
        })
        for mode in data["modes"].values():
            self.assertTrue(mode["asset_count"]["evidence_ids"])
            self.assertTrue(mode["allowed_media_types"]["evidence_ids"])

    def test_first_last_roles_are_explicit(self) -> None:
        mode = json.loads(_PROFILE.read_text(encoding="utf-8"))["modes"]["first_last_frame"]
        self.assertEqual(mode["required_responsibilities"], ["first_frame", "last_frame"])

    def test_unverified_numbers_are_not_hard_limits(self) -> None:
        data = json.loads(_PROFILE.read_text(encoding="utf-8"))
        serialized = json.dumps(data, ensure_ascii=False)
        for unsupported in ("max_total_size_mb", "max_video_duration_s", "max_resolution"):
            self.assertNotIn(unsupported, serialized)
        self.assertIn("reference_video_duration", data["unknown_limits"])

    def test_primary_model_limits_are_recorded_with_evidence(self) -> None:
        data = json.loads(_PROFILE.read_text(encoding="utf-8"))
        capabilities = data["model_capabilities"]
        self.assertEqual(capabilities["generation_duration_s"]["max"], 15)
        self.assertEqual(capabilities["native_output_resolutions"]["values"], ["480p", "720p"])
        self.assertEqual(capabilities["multimodal_reference_limits"]["image"], 9)
        self.assertEqual(capabilities["multimodal_reference_limits"]["canvas_total"], 12)

    def test_quality_rules_are_advisory(self) -> None:
        data = json.loads(_PROFILE.read_text(encoding="utf-8"))
        for heuristic in data["quality_heuristics"].values():
            self.assertEqual(heuristic["enforcement"], "advisory")

    def test_hash_is_stable(self) -> None:
        self.assertEqual(get_hash(_PROFILE), get_hash(_PROFILE))
        self.assertEqual(len(get_hash(_PROFILE)), 64)

    def test_unknown_hard_field_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix=f"mode_p_sd2_{os.getpid()}_") as temp:
            data = json.loads(_PROFILE.read_text(encoding="utf-8"))
            data["max_resolution"] = "2048x2048"
            path = Path(temp) / "bad.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            ok, _ = validate_profile(path)
            self.assertFalse(ok)

    def test_missing_evidence_reference_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix=f"mode_p_sd2_{os.getpid()}_") as temp:
            data = json.loads(_PROFILE.read_text(encoding="utf-8"))
            data["modes"]["omni_reference"]["asset_count"]["evidence_ids"] = ["missing"]
            path = Path(temp) / "bad.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            ok, issues = validate_profile(path)
            self.assertFalse(ok)
            self.assertTrue(any("known evidence" in issue for issue in issues))


class CLITests(unittest.TestCase):
    def test_cli_validate_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "sd2_capability_manager", "validate", str(_PROFILE)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cli_hash_outputs_64_chars(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "sd2_capability_manager", "hash", str(_PROFILE)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.strip()), 64)


if __name__ == "__main__":
    unittest.main()
