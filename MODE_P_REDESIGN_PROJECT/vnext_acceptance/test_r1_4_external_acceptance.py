"""Locked external acceptance gate for MODE:P vNext R1.4 integrity repair.

Owned by the independent Codex audit.  The DeepSeek R1.4 worker may repair
R1.4 production code and worker-owned tests, but must not edit, replace,
monkeypatch, skip, xfail, or copy this gate.

Run from ``01_调度器``:

    python -m pytest ../MODE_P_REDESIGN_PROJECT/vnext_acceptance/\
test_r1_4_external_acceptance.py -q

This gate exists because the first R1.4 completion detected hash mismatches in
diagnostics while still returning ``all_valid=True``.  Every mutation below
goes through the production ``run_structural_case`` API.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "01_调度器"
if str(DISPATCHER) not in sys.path:
    sys.path.insert(0, str(DISPATCHER))

from mode_p_vnext.fixtures.r1_3.golden_cases import build_golden_deliveries
from mode_p_vnext.fixtures.r1_4.golden_expectations import GOLDEN_EXPECTATIONS
from mode_p_vnext.storyboard_renderer import render_storyboard
from mode_p_vnext.structural_runner import run_structural_case
from mode_p_vnext.video_renderer import render_video_prompt


SCENES = ("gun_barrel", "audience", "prep_area", "alley")


def _render_all() -> dict[str, str]:
    deliveries = build_golden_deliveries()
    artifacts: dict[str, str] = {}
    for fixture_id, delivery in deliveries.items():
        if fixture_id.endswith("_sb"):
            artifacts[fixture_id] = render_storyboard(delivery)
        else:
            artifacts[fixture_id] = render_video_prompt(delivery)
    return artifacts


def _codes(result) -> tuple[str, ...]:
    return tuple(d.code for d in result.diagnostics)


def _assert_integrity_failure(test: unittest.TestCase, result) -> None:
    test.assertFalse(
        result.all_valid,
        f"tampered input was approved; flags="
        f"{(result.format_valid, result.timing_valid, result.cuts_valid, result.responsibilities_valid, result.forbidden_routes_valid, result.homology_valid)} "
        f"diagnostics={_codes(result)}",
    )


def _swap_section_blocks(text: str, first: str, second: str, following: str) -> str:
    first_at = text.index(first)
    second_at = text.index(second, first_at)
    following_at = text.index(following, second_at)
    first_block = text[first_at:second_at]
    second_block = text[second_at:following_at]
    return text[:first_at] + second_block + first_block + text[following_at:]


class CanonicalGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = _render_all()

    def test_all_four_canonical_pairs_pass(self):
        for scene in SCENES:
            with self.subTest(scene=scene):
                result = run_structural_case(
                    self.artifacts[f"{scene}_sb"],
                    self.artifacts[f"{scene}_video"],
                    GOLDEN_EXPECTATIONS[scene],
                )
                self.assertTrue(
                    result.all_valid,
                    f"{scene}: canonical pair rejected: {_codes(result)}",
                )


class FailClosedIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = _render_all()
        cls.sb = cls.artifacts["gun_barrel_sb"]
        cls.vp = cls.artifacts["gun_barrel_video"]
        cls.exp = GOLDEN_EXPECTATIONS["gun_barrel"]

    def test_storyboard_single_byte_tamper_is_not_approved(self):
        result = run_structural_case(self.sb + " ", self.vp, self.exp)
        self.assertIn("SB_HASH_MISMATCH", _codes(result))
        _assert_integrity_failure(self, result)

    def test_video_single_byte_tamper_is_not_approved(self):
        result = run_structural_case(self.sb, self.vp + "\n", self.exp)
        self.assertIn("VP_HASH_MISMATCH", _codes(result))
        _assert_integrity_failure(self, result)

    def test_caller_cannot_reauthorize_tamper_by_replacing_expected_hash(self):
        tampered = self.sb + " "
        forged = replace(
            self.exp,
            canonical_sb_sha256=hashlib.sha256(tampered.encode("utf-8")).hexdigest(),
        )
        result = run_structural_case(tampered, self.vp, forged)
        _assert_integrity_failure(self, result)
        self.assertTrue(
            any(
                marker in code
                for code in _codes(result)
                for marker in ("EXPECTATION", "MANIFEST", "AUTHORITY", "INTEGRITY")
            ),
            f"forged expectation was not diagnosed: {_codes(result)}",
        )

    def test_unknown_case_expectation_fails_closed(self):
        forged = replace(self.exp, case_id="forged_unknown_case")
        result = run_structural_case(self.sb, self.vp, forged)
        _assert_integrity_failure(self, result)


class TemporalSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = _render_all()
        cls.sb = cls.artifacts["gun_barrel_sb"]
        cls.vp = cls.artifacts["gun_barrel_video"]
        cls.exp = GOLDEN_EXPECTATIONS["gun_barrel"]

    def test_true_time_reversal_is_timing_failure(self):
        tampered = (
            self.sb.replace("[4s]", "[__R14_TMP__]")
            .replace("[5s]", "[4s]")
            .replace("[__R14_TMP__]", "[5s]")
        )
        result = run_structural_case(tampered, self.vp, self.exp)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)

    def test_duplicate_second_is_timing_failure(self):
        tampered = self.sb.replace("[6s]", "[5s]", 1)
        result = run_structural_case(tampered, self.vp, self.exp)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)

    def test_missing_second_is_timing_failure(self):
        tampered = self.sb.replace("[6s]", "[missing]", 1)
        result = run_structural_case(tampered, self.vp, self.exp)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)


class ExactStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = _render_all()
        cls.sb = cls.artifacts["gun_barrel_sb"]
        cls.vp = cls.artifacts["gun_barrel_video"]
        cls.exp = GOLDEN_EXPECTATIONS["gun_barrel"]

    def test_required_section_order_is_exact(self):
        tampered = _swap_section_blocks(
            self.vp, "### @音轨", "### @禁止", "### @转场"
        )
        result = run_structural_case(self.sb, tampered, self.exp)
        self.assertFalse(result.format_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)

    def test_forbidden_body_deletion_is_forbidden_route_failure(self):
        start = self.vp.index("- 【禁止】")
        route = self.vp.index("*[路由标记：", start)
        tampered = self.vp[:start] + "- 【禁止】\n  " + self.vp[route:]
        result = run_structural_case(self.sb, tampered, self.exp)
        self.assertFalse(result.forbidden_routes_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)

    def test_forbidden_semantic_rewrite_is_forbidden_route_failure(self):
        needle = "光区外不使用任何补光"
        self.assertIn(needle, self.vp)
        tampered = self.vp.replace(needle, "光区外允许任何补光", 1)
        result = run_structural_case(self.sb, tampered, self.exp)
        self.assertFalse(result.forbidden_routes_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)

    def test_unexpected_reference_and_duty_are_rejected(self):
        lines = self.vp.splitlines()
        upload_line = lines[2]
        duty_line = lines[5]
        closing = duty_line.find("** ", 2)
        self.assertGreater(closing, 2)
        injected_ref = upload_line.rsplit(" ", 1)[0][:-1] + "3 @evil"
        duty_prefix = duty_line[: closing + 3].replace("@rico", "@evil", 1)
        injected_duty = duty_prefix + "inject untrusted reference"
        tampered = self.vp.replace(
            upload_line, upload_line + "\n" + injected_ref, 1
        ).replace(duty_line, duty_line + "\n" + injected_duty, 1)
        result = run_structural_case(self.sb, tampered, self.exp)
        self.assertFalse(result.responsibilities_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)


class HomologySemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = _render_all()
        cls.sb = cls.artifacts["gun_barrel_sb"]
        cls.vp = cls.artifacts["gun_barrel_video"]
        cls.exp = GOLDEN_EXPECTATIONS["gun_barrel"]

    def test_storyboard_semantic_anchor_rewrite_breaks_homology(self):
        needle = "Rico背对镜头坐在台灯后"
        self.assertIn(needle, self.sb)
        tampered = self.sb.replace(needle, "Rico背对镜头坐在台灯旁", 1)
        result = run_structural_case(tampered, self.vp, self.exp)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)

    def test_time_label_swap_breaks_homology(self):
        tampered = (
            self.sb.replace("[4s]", "[__R14_TMP__]")
            .replace("[5s]", "[4s]")
            .replace("[__R14_TMP__]", "[5s]")
        )
        result = run_structural_case(tampered, self.vp, self.exp)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")
        _assert_integrity_failure(self, result)


if __name__ == "__main__":
    unittest.main()
