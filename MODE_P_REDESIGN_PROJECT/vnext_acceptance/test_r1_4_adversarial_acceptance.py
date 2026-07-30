"""Second locked external gate for MODE:P vNext R1.4.

This gate covers category-specific structural mutations that are not exercised
by ``test_r1_4_external_acceptance.py``.  A global artifact hash mismatch is
necessary but not sufficient: the responsible structural category must also
reject the mutation so diagnostics remain useful for future non-Golden output.

Owned by the independent Codex audit.  The DeepSeek repair worker must not
edit, replace, monkeypatch, skip, xfail, or copy this file.
"""

from __future__ import annotations

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
from mode_p_vnext.storyboard_projection import contract_fingerprint
from mode_p_vnext.storyboard_renderer import render_storyboard
from mode_p_vnext.structural_runner import run_structural_case
from mode_p_vnext.video_renderer import render_video_prompt


def _render_all(deliveries=None) -> dict[str, str]:
    if deliveries is None:
        deliveries = build_golden_deliveries()
    artifacts: dict[str, str] = {}
    for fixture_id, delivery in deliveries.items():
        if fixture_id.endswith("_sb"):
            artifacts[fixture_id] = render_storyboard(delivery)
        else:
            artifacts[fixture_id] = render_video_prompt(delivery)
    return artifacts


def _run(artifacts: dict[str, str], scene: str, *, sb=None, vp=None):
    return run_structural_case(
        artifacts[f"{scene}_sb"] if sb is None else sb,
        artifacts[f"{scene}_video"] if vp is None else vp,
        GOLDEN_EXPECTATIONS[scene],
    )


def _codes(result) -> tuple[str, ...]:
    return tuple(d.code for d in result.diagnostics)


def _empty_section(text: str, start_marker: str, end_marker: str) -> str:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(start_marker))
    end = next(
        i for i, line in enumerate(lines[start + 1 :], start + 1)
        if line.startswith(end_marker)
    )
    return "\n".join(lines[: start + 1] + [""] + lines[end:])


def _rewrite_first_bullet_after(text: str, marker: str, replacement: str) -> str:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(marker))
    index = next(
        i for i, line in enumerate(lines[start + 1 :], start + 1)
        if line.strip().startswith("- ")
    )
    lines[index] = f"- {replacement}"
    return "\n".join(lines)


class CategorySpecificAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deliveries = build_golden_deliveries()
        cls.artifacts = _render_all(cls.deliveries)

    def test_vp_duplicate_and_missing_second_fail_timing(self):
        scene = "gun_barrel"
        lines = self.artifacts[f"{scene}_video"].splitlines()
        index = next(
            i for i, line in enumerate(lines)
            if line.startswith("**") and " 6s " in line
        )
        lines[index] = lines[index].replace(" 6s ", " 5s ", 1)
        result = _run(self.artifacts, scene, vp="\n".join(lines))
        self.assertFalse(result.all_valid)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")

    def test_hold_interval_end_is_validated(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("13s–13s [保持]", vp)
        tampered = vp.replace("13s–13s [保持]", "13s–99s [保持]", 1)
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")

    def test_hold_node_kind_change_breaks_homology(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("[保持]", vp)
        tampered = vp.replace("[保持]", "[@音轨]", 1)
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_boundary_node_id_change_breaks_homology(self):
        scene = "audience"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("[cut_3s]", vp)
        tampered = vp.replace("[cut_3s]", "[forged_boundary_id]", 1)
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.cuts_valid, f"codes={_codes(result)}")
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_removed_vp_panel_description_breaks_homology(self):
        scene = "gun_barrel"
        lines = self.artifacts[f"{scene}_video"].splitlines()
        panel_index = next(
            i for i, line in enumerate(lines)
            if line.startswith("**") and " 0s " in line
        )
        self.assertTrue(lines[panel_index + 1].strip())
        lines[panel_index + 1] = ""
        result = _run(self.artifacts, scene, vp="\n".join(lines))
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_reference_target_rewrite_fails_responsibilities(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("@图片2 @rico", vp)
        tampered = vp.replace("@图片2 @rico", "@图片2 @evil", 1)
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(
            result.responsibilities_valid,
            f"codes={_codes(result)}",
        )

    def test_unknown_section_is_format_failure(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("### @禁止", vp)
        tampered = vp.replace(
            "### @禁止",
            "### @UNKNOWN_INJECT\n- injected\n\n### @禁止",
            1,
        )
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.format_valid, f"codes={_codes(result)}")

    def test_camera_motion_rewrite_breaks_homology(self):
        scene = "gun_barrel"
        lines = self.artifacts[f"{scene}_video"].splitlines()
        panel_index = next(
            i for i, line in enumerate(lines)
            if line.startswith("**") and " 0s " in line
        )
        original = lines[panel_index]
        self.assertIn("前推", original)
        lines[panel_index] = original.replace("前推", "横移", 1)
        result = _run(self.artifacts, scene, vp="\n".join(lines))
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_public_expectation_fingerprint_is_authoritative(self):
        scene = "gun_barrel"
        canonical = GOLDEN_EXPECTATIONS[scene]
        tampered = replace(canonical, expectation_fingerprint="0" * 64)
        result = run_structural_case(
            self.artifacts[f"{scene}_sb"],
            self.artifacts[f"{scene}_video"],
            tampered,
        )
        self.assertFalse(result.all_valid)
        self.assertFalse(result.integrity_valid, f"codes={_codes(result)}")

    def test_expectations_bind_r1_3_contract_and_source_authority(self):
        mismatches = []
        for scene in ("gun_barrel", "audience", "prep_area", "alley"):
            expectation = GOLDEN_EXPECTATIONS[scene]
            sb_contract = self.deliveries[f"{scene}_sb"].contract
            vp_contract = self.deliveries[f"{scene}_video"].contract
            sb_fingerprint = contract_fingerprint(sb_contract)
            vp_fingerprint = contract_fingerprint(vp_contract)
            if sb_fingerprint != vp_fingerprint:
                mismatches.append(f"{scene}: SB/VP contract fingerprints differ")
            if getattr(expectation, "contract_fingerprint", None) != sb_fingerprint:
                mismatches.append(f"{scene}: expectation lacks exact contract binding")
            if (
                getattr(expectation, "semantic_sources_sha256", None)
                != sb_contract.semantic_sources_sha256
            ):
                mismatches.append(f"{scene}: expectation lacks exact source binding")
        self.assertEqual([], mismatches)

    def test_storyboard_segment_identity_change_breaks_homology(self):
        scene = "gun_barrel"
        lines = self.artifacts[f"{scene}_sb"].splitlines()
        self.assertTrue(lines[0].startswith("## "))
        duration_suffix = lines[0][lines[0].rfind(" (") :]
        lines[0] = f"## FORGED_SEGMENT{duration_suffix}"
        result = _run(self.artifacts, scene, sb="\n".join(lines))
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_unparseable_duration_is_timing_failure(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("**片段时长：13s**", vp)
        tampered = vp.replace(
            "**片段时长：13s**",
            "**片段时长：UNKNOWN**",
            1,
        )
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")

    def test_empty_required_audio_section_is_format_failure(self):
        scene = "gun_barrel"
        vp = _empty_section(
            self.artifacts[f"{scene}_video"],
            "### @音轨",
            "### @禁止",
        )
        result = _run(self.artifacts, scene, vp=vp)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.format_valid, f"codes={_codes(result)}")

    def test_unparseable_bold_timeline_node_is_format_failure(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        first_panel = "**① 0s 全景 前推**"
        self.assertIn(first_panel, vp)
        tampered = vp.replace(
            first_panel,
            f"{first_panel}\nFORGED DESCRIPTION\n\n**UNPARSEABLE_NODE**",
            1,
        )
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.format_valid, f"codes={_codes(result)}")

    def test_forbidden_text_leak_into_positive_body_fails_route(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        lines = vp.splitlines()
        prohibition_start = next(
            i for i, line in enumerate(lines) if line.startswith("### @禁止")
        )
        forbidden_text = next(
            line.strip()[2:]
            for line in lines[prohibition_start + 1 :]
            if line.strip().startswith("- ")
        )
        panel_index = next(
            i for i, line in enumerate(lines)
            if line.startswith("**") and " 0s " in line
        )
        lines.insert(panel_index, f"正向创意正文：{forbidden_text}")
        result = _run(self.artifacts, scene, vp="\n".join(lines))
        self.assertFalse(result.all_valid)
        self.assertFalse(
            result.forbidden_routes_valid,
            f"codes={_codes(result)}",
        )

    def test_storyboard_reference_rewrite_breaks_homology(self):
        scene = "gun_barrel"
        sb = self.artifacts[f"{scene}_sb"]
        self.assertIn("@人物 Rico背对镜头", sb)
        tampered = sb.replace(
            "@人物 Rico背对镜头",
            "@人物 FORGED_CHARACTER",
            1,
        )
        result = _run(self.artifacts, scene, sb=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_per_node_phase_rewrite_breaks_homology(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("**① 1s 全景 固定**", vp)
        tampered = vp.replace(
            "**① 1s 全景 固定**",
            "**1s 全景 固定**",
            1,
        )
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_shot_size_rewrite_breaks_homology(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("**① 0s 全景 前推**", vp)
        tampered = vp.replace(
            "**① 0s 全景 前推**",
            "**① 0s 极特写 前推**",
            1,
        )
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_hold_removal_fails_timing_and_homology(self):
        scene = "gun_barrel"
        lines = self.artifacts[f"{scene}_video"].splitlines()
        index = next(i for i, line in enumerate(lines) if "[保持]" in line)
        del lines[index]
        result = _run(self.artifacts, scene, vp="\n".join(lines))
        self.assertFalse(result.all_valid)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_transition_semantic_rewrite_breaks_homology(self):
        scene = "gun_barrel"
        tampered = _rewrite_first_bullet_after(
            self.artifacts[f"{scene}_video"],
            "### @转场",
            "FORGED_TRANSITION",
        )
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid, f"codes={_codes(result)}")

    def test_reference_image_id_rewrite_fails_responsibilities(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("@图片2 @rico", vp)
        tampered = vp.replace("@图片2 @rico", "@图片9 @rico", 1)
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(
            result.responsibilities_valid,
            f"codes={_codes(result)}",
        )

    def test_audio_interval_end_is_validated(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("13s–13s [@音轨]", vp)
        tampered = vp.replace(
            "13s–13s [@音轨]",
            "13s–99s [@音轨]",
            1,
        )
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")

    def test_panel_at_exclusive_segment_end_is_timing_failure(self):
        scene = "gun_barrel"
        vp = self.artifacts[f"{scene}_video"]
        self.assertIn("**③ 12s 极特写 固定**", vp)
        tampered = vp.replace(
            "**③ 12s 极特写 固定**",
            "**③ 13s 极特写 固定**",
            1,
        )
        result = _run(self.artifacts, scene, vp=tampered)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.timing_valid, f"codes={_codes(result)}")


if __name__ == "__main__":
    unittest.main()
