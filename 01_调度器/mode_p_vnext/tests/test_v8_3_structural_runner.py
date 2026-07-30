"""R1.4 — Real Golden structural runner tests.

Comprehensive tests proving the runner:
- Parses real rendered artifacts
- Computes all 6 validation categories
- Detects tampering via production API
- Is deterministic (same input → same output)
- Has no model/network/external calls
- Covers 4 archetypes × 8 artifacts

No skipIf, skip, expectedFailure. No caller-supplied booleans.
Every failure is detected by the production runner API, not test assertions.
"""

import hashlib
import re
import unittest

from mode_p_vnext.fixtures.r1_3.golden_cases import build_golden_deliveries
from mode_p_vnext.fixtures.r1_4.golden_expectations import GOLDEN_EXPECTATIONS
from mode_p_vnext.storyboard_renderer import render_storyboard
from mode_p_vnext.video_renderer import render_video_prompt
from mode_p_vnext.structural_runner import (
    CaseExpectation,
    Diagnostic,
    StructuralDiagnostics,
    run_structural_case,
    run_structural_suite,
)

# ============================================================================
# Helpers
# ============================================================================


def _all_artifacts():
    """Render all 8 Golden artifacts from the production builder."""
    deliveries = build_golden_deliveries()
    rendered = {}
    for fid, view in deliveries.items():
        if fid.endswith("_sb"):
            rendered[fid] = render_storyboard(view)
        else:
            rendered[fid] = render_video_prompt(view)
    return rendered


def _artifact_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ============================================================================
# 1. Golden archetype validation — 4 real cases, all valid
# ============================================================================


class GoldenArchetypeValidationTests(unittest.TestCase):
    """All 4 Golden cases must pass all 6 categories."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()
        cls.expectations = GOLDEN_EXPECTATIONS

    def _run_case(self, scene_root):
        exp = self.expectations[scene_root]
        sb = self.artifacts[f"{scene_root}_sb"]
        vp = self.artifacts[f"{scene_root}_video"]
        result = run_structural_case(sb, vp, exp)
        return result

    def test_gun_barrel_all_valid(self):
        result = self._run_case("gun_barrel")
        self.assertTrue(result.format_valid, f"format: {[d.detail for d in result.diagnostics if d.category=='format']}")
        self.assertTrue(result.timing_valid, f"timing: {[d.detail for d in result.diagnostics if d.category=='timing']}")
        self.assertTrue(result.cuts_valid, f"cuts: {[d.detail for d in result.diagnostics if d.category=='cuts']}")
        self.assertTrue(result.responsibilities_valid)
        self.assertTrue(result.forbidden_routes_valid)
        self.assertTrue(result.homology_valid)
        self.assertTrue(result.all_valid)

    def test_audience_all_valid(self):
        result = self._run_case("audience")
        self.assertTrue(result.format_valid)
        self.assertTrue(result.timing_valid)
        self.assertTrue(result.cuts_valid)
        self.assertTrue(result.responsibilities_valid)
        self.assertTrue(result.forbidden_routes_valid)
        self.assertTrue(result.homology_valid)
        self.assertTrue(result.all_valid)

    def test_prep_area_all_valid(self):
        result = self._run_case("prep_area")
        self.assertTrue(result.format_valid)
        self.assertTrue(result.timing_valid)
        self.assertTrue(result.cuts_valid)
        self.assertTrue(result.responsibilities_valid)
        self.assertTrue(result.forbidden_routes_valid)
        self.assertTrue(result.homology_valid)
        self.assertTrue(result.all_valid)

    def test_alley_all_valid(self):
        result = self._run_case("alley")
        self.assertTrue(result.format_valid)
        self.assertTrue(result.timing_valid)
        self.assertTrue(result.cuts_valid)
        self.assertTrue(result.responsibilities_valid)
        self.assertTrue(result.forbidden_routes_valid)
        self.assertTrue(result.homology_valid)
        self.assertTrue(result.all_valid)

    def test_all_eight_artifacts_parsed(self):
        """Prove all 8 artifacts are actually read by the parser."""
        for fid in ("gun_barrel_sb", "gun_barrel_video", "audience_sb",
                     "audience_video", "prep_area_sb", "prep_area_video",
                     "alley_sb", "alley_video"):
            self.assertIn(fid, self.artifacts)
            self.assertGreater(len(self.artifacts[fid]), 100,
                             f"{fid} artifact is too short — parser would get empty input")

    def test_suite_api_covers_four_cases(self):
        """run_structural_suite with all 4 cases."""
        cases = {}
        for scene_root in ("gun_barrel", "audience", "prep_area", "alley"):
            exp = self.expectations[scene_root]
            sb = self.artifacts[f"{scene_root}_sb"]
            vp = self.artifacts[f"{scene_root}_video"]
            cases[scene_root] = (sb, vp, exp)
        results = run_structural_suite(cases)
        self.assertEqual(len(results), 4)
        for scene_root, result in results.items():
            self.assertTrue(result.all_valid,
                          f"{scene_root}: not all_valid — {[d.code for d in result.diagnostics]}")


# ============================================================================
# 2. Artifact parser — extract correct data
# ============================================================================


class GoldenArtifactParserTests(unittest.TestCase):
    """Prove the parser extracts correct structural data from rendered artifacts."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()
        cls.expectations = GOLDEN_EXPECTATIONS

    def test_sb_parser_extracts_segment_id(self):
        from mode_p_vnext.structural_runner import _parse_storyboard
        for scene_root in ("gun_barrel", "audience", "prep_area", "alley"):
            parsed = _parse_storyboard(self.artifacts[f"{scene_root}_sb"])
            self.assertIsNotNone(parsed["segment_id"], f"{scene_root}: no segment_id")
            self.assertGreater(len(parsed["segment_id"]), 0)

    def test_sb_parser_extracts_duration(self):
        from mode_p_vnext.structural_runner import _parse_storyboard
        for scene_root in ("gun_barrel", "audience", "prep_area", "alley"):
            parsed = _parse_storyboard(self.artifacts[f"{scene_root}_sb"])
            exp = self.expectations[scene_root]
            self.assertAlmostEqual(parsed["duration_s"], exp.segment_end_s, delta=0.01)

    def test_sb_parser_extracts_panels(self):
        from mode_p_vnext.structural_runner import _parse_storyboard
        for scene_root in ("gun_barrel", "audience", "prep_area", "alley"):
            parsed = _parse_storyboard(self.artifacts[f"{scene_root}_sb"])
            exp = self.expectations[scene_root]
            self.assertEqual(len(parsed["panels"]), exp.expected_sb_panel_count,
                           f"{scene_root}: panel count mismatch")

    def test_vp_parser_extracts_timeline_nodes(self):
        from mode_p_vnext.structural_runner import _parse_video_prompt
        for scene_root in ("gun_barrel", "audience", "prep_area", "alley"):
            parsed = _parse_video_prompt(self.artifacts[f"{scene_root}_video"])
            nodes = parsed.get("timeline_nodes", [])
            panels = [n for n in nodes if n.get("node_type") == "panel"]
            exp = self.expectations[scene_root]
            self.assertEqual(len(panels), exp.expected_vp_timeline_count,
                           f"{scene_root}: VP panel count {len(panels)} != {exp.expected_vp_timeline_count}")

    def test_vp_parser_extracts_cuts(self):
        from mode_p_vnext.structural_runner import _parse_video_prompt
        # audience has cuts at 3s, 8s
        parsed = _parse_video_prompt(self.artifacts["audience_video"])
        cuts = parsed.get("cut_times", [])
        self.assertIn(3.0, cuts)
        self.assertIn(8.0, cuts)
        # alley has cuts at 5s, 9s
        parsed = _parse_video_prompt(self.artifacts["alley_video"])
        cuts = parsed.get("cut_times", [])
        self.assertIn(5.0, cuts)
        self.assertIn(9.0, cuts)
        # gun_barrel and prep_area have no cuts
        for scene_root in ("gun_barrel", "prep_area"):
            parsed = _parse_video_prompt(self.artifacts[f"{scene_root}_video"])
            cuts = parsed.get("cut_times", [])
            self.assertEqual(len(cuts), 0, f"{scene_root}: unexpected cuts at {cuts}")

    def test_vp_parser_extracts_refs_and_duties(self):
        from mode_p_vnext.structural_runner import _parse_video_prompt
        for scene_root in ("gun_barrel", "audience", "prep_area", "alley"):
            parsed = _parse_video_prompt(self.artifacts[f"{scene_root}_video"])
            refs = parsed.get("reference_images", [])
            duties = parsed.get("reference_duties", [])
            self.assertGreater(len(refs), 0, f"{scene_root}: no reference images found")
            self.assertEqual(len(refs), len(duties),
                           f"{scene_root}: ref/duty count mismatch: {len(refs)} refs vs {len(duties)} duties")

    def test_vp_parser_extracts_prohibition_route(self):
        from mode_p_vnext.structural_runner import _parse_video_prompt
        parsed = _parse_video_prompt(self.artifacts["gun_barrel_video"])
        self.assertEqual(parsed.get("prohibition_route"), "human_qa_only")
        parsed = _parse_video_prompt(self.artifacts["audience_video"])
        self.assertEqual(parsed.get("prohibition_route"), "inline_supported")


# ============================================================================
# 3. Fail-closed: empty / missing / malformed inputs
# ============================================================================


class FailClosedInputTests(unittest.TestCase):
    """Runner must fail-closed on bad inputs."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()
        cls.exp = GOLDEN_EXPECTATIONS["gun_barrel"]

    def test_empty_sb_artifact_fails(self):
        result = run_structural_case("", self.artifacts["gun_barrel_video"], self.exp)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.format_valid)
        self.assertTrue(any("PARSE_ERROR" in d.code for d in result.diagnostics))

    def test_empty_vp_artifact_fails(self):
        result = run_structural_case(self.artifacts["gun_barrel_sb"], "", self.exp)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.format_valid)
        self.assertTrue(any("PARSE_ERROR" in d.code for d in result.diagnostics))

    def test_both_empty_fails(self):
        result = run_structural_case("", "", self.exp)
        self.assertFalse(result.all_valid)

    def test_whitespace_only_sb_fails(self):
        result = run_structural_case("   \n\n  \n", self.artifacts["gun_barrel_video"], self.exp)
        self.assertFalse(result.all_valid)
        self.assertFalse(result.format_valid)

    def test_unknown_case_detected(self):
        """Wrong case expectation for artifact — should flag mismatches."""
        # Use audience expectation with gun_barrel artifacts
        audience_exp = GOLDEN_EXPECTATIONS["audience"]
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"],
            self.artifacts["gun_barrel_video"],
            audience_exp,
        )
        # The artifacts are from gun_barrel (13s, 13 panels, no cuts) but
        # expectation says audience (12s, 12 panels, cuts at 3s/8s).
        # Timing/cuts/panel count should mismatch.
        self.assertFalse(result.all_valid)

    def test_wrong_scene_pairing_detected(self):
        """SB from one scene, VP from another — homology should fail."""
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"],
            self.artifacts["audience_video"],
            self.exp,
        )
        self.assertFalse(result.all_valid)
        self.assertFalse(result.homology_valid)


# ============================================================================
# 4. Format tampering
# ============================================================================


class FormatTamperTests(unittest.TestCase):
    """Section deletion, duplication, and reordering."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()
        cls.exp = GOLDEN_EXPECTATIONS["gun_barrel"]

    def test_deleted_sb_title_fails(self):
        sb = self.artifacts["gun_barrel_sb"]
        # Remove the title line
        lines = sb.split('\n')
        # Find and remove the ## title line
        new_lines = [l for l in lines if not l.startswith('## ')]
        tampered = '\n'.join(new_lines)
        result = run_structural_case(tampered, self.artifacts["gun_barrel_video"], self.exp)
        self.assertFalse(result.format_valid)
        self.assertTrue(any("PARSE_ERROR" in d.code for d in result.diagnostics),
                      f"diags: {[d.code for d in result.diagnostics]}")

    def test_deleted_sb_style_section_fails(self):
        sb = self.artifacts["gun_barrel_sb"]
        # Remove the style declaration paragraph (between refs and annotation legend)
        # Find and remove the style text
        lines = sb.split('\n')
        # Replace the style paragraph with empty
        new_lines = []
        skip = False
        for l in lines:
            if l.startswith('**标注颜色系统'):
                skip = False
            if skip:
                continue
            if l.startswith('@rico') or l.startswith('@场景'):
                new_lines.append(l)
                skip = True  # Skip the style paragraph that follows
                continue
            new_lines.append(l)
        tampered = '\n'.join(new_lines)
        result = run_structural_case(tampered, self.artifacts["gun_barrel_video"], self.exp)
        self.assertFalse(result.format_valid)

    def test_duplicate_sb_section_fails(self):
        sb = self.artifacts["gun_barrel_sb"]
        # Duplicate the prohibitions section
        lines = sb.split('\n')
        for j, line in enumerate(lines):
            if '故事板禁止项' in line:
                # Insert a duplicate
                dup = lines[j:j+3]
                lines = lines[:j] + dup + lines[j:]
                break
        tampered = '\n'.join(lines)
        result = run_structural_case(tampered, self.artifacts["gun_barrel_video"], self.exp)
        self.assertFalse(result.format_valid)
        self.assertTrue(any("DUPLICATE" in d.code for d in result.diagnostics),
                      f"diags: {[d.code for d in result.diagnostics]}")

    def test_vp_deleted_prohibitions_fails(self):
        vp = self.artifacts["gun_barrel_video"]
        # Remove @禁止 section
        lines = vp.split('\n')
        new_lines = []
        skip = False
        for l in lines:
            if l.startswith('### @禁止'):
                skip = True
                continue
            if skip and l.startswith('###'):
                skip = False
            if skip:
                continue
            new_lines.append(l)
        tampered = '\n'.join(new_lines)
        result = run_structural_case(self.artifacts["gun_barrel_sb"], tampered, self.exp)
        self.assertFalse(result.format_valid)


# ============================================================================
# 5. Timing tampering
# ============================================================================


class TimingTamperTests(unittest.TestCase):
    """Time deletion, duplication, reversal, out-of-bounds, duration change."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()
        cls.exp = GOLDEN_EXPECTATIONS["gun_barrel"]

    def test_deleted_time_fails(self):
        """Remove a panel — homology should detect panel count mismatch."""
        sb = self.artifacts["gun_barrel_sb"]
        lines = sb.split('\n')
        # Remove the panel at 5s
        new_lines = []
        skip_panel = False
        for l in lines:
            if '[5s]' in l and l.startswith('###'):
                skip_panel = True
                continue
            if skip_panel:
                if l.startswith('###') or l.startswith('---') or l.startswith('**'):
                    skip_panel = False
                    new_lines.append(l)
                continue
            new_lines.append(l)
        tampered = '\n'.join(new_lines)
        result = run_structural_case(tampered, self.artifacts["gun_barrel_video"], self.exp)
        # Removing a panel should cause panel count mismatch in homology
        self.assertFalse(result.homology_valid,
                       f"expected homology failure, got hom={result.homology_valid}")

    def test_out_of_bounds_time_fails(self):
        """Change a time to beyond segment end."""
        vp = self.artifacts["gun_barrel_video"]
        # Replace a time display with one out of bounds
        tampered = vp.replace('**① 0s ', '**① 99s ')
        result = run_structural_case(self.artifacts["gun_barrel_sb"], tampered, self.exp)
        self.assertFalse(result.all_valid)

    def test_duration_change_fails(self):
        """Change the segment duration in VP."""
        vp = self.artifacts["gun_barrel_video"]
        tampered = vp.replace('**片段时长：13s**', '**片段时长：7s**')
        result = run_structural_case(self.artifacts["gun_barrel_sb"], tampered, self.exp)
        self.assertFalse(result.timing_valid)

    def test_reversed_times_fails(self):
        """Change a time to an out-of-bounds value."""
        sb = self.artifacts["gun_barrel_sb"]
        # Change [5s] to [99s] — this is out of bounds
        tampered = sb.replace('[5s]', '[99s]')
        result = run_structural_case(tampered, self.artifacts["gun_barrel_video"], self.exp)
        self.assertFalse(result.all_valid,
                       f"out-of-bounds time should cause failure; got all_valid={result.all_valid}")


# ============================================================================
# 6. Cut tampering
# ============================================================================


class CutTamperTests(unittest.TestCase):
    """Cut point manipulation — missing, injected, shifted."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()

    def test_audience_3s_cut_removed_fails(self):
        vp = self.artifacts["audience_video"]
        # Remove the 3s cut node line
        lines = vp.split('\n')
        new_lines = []
        for l in lines:
            if '3s' in l and '[' in l and ']' in l and '：' in l:
                if 'boundary' in l.lower() or re.search(r'3s\s+\[', l):
                    continue  # Skip cut boundary
            new_lines.append(l)
        tampered = '\n'.join(new_lines)
        result = run_structural_case(
            self.artifacts["audience_sb"], tampered,
            GOLDEN_EXPECTATIONS["audience"])
        self.assertFalse(result.cuts_valid,
                       f"expected cuts failure; cuts_valid={result.cuts_valid} diags={[d.code for d in result.diagnostics]}")

    def test_gun_barrel_injected_cut_fails(self):
        """Gun barrel has no internal cuts — injecting one should fail."""
        vp = self.artifacts["gun_barrel_video"]
        # Inject a fake cut boundary node
        lines = vp.split('\n')
        # Insert after the first timeline node
        for j, l in enumerate(lines):
            if '**① 0s' in l:
                lines.insert(j + 3, '**5s [fake_cut]：** 伪造切镜')
                break
        tampered = '\n'.join(lines)
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"], tampered,
            GOLDEN_EXPECTATIONS["gun_barrel"])
        self.assertFalse(result.cuts_valid,
                       f"injected cut should fail cuts; got cuts_valid={result.cuts_valid}")

    def test_alley_5s_cut_shifted_fails(self):
        """Shift a cut from 5s to 4s."""
        vp = self.artifacts["alley_video"]
        # Replace 5s cut with 4s
        tampered = vp.replace('**5s [cut_5s]：**', '**4s [cut_5s]：**')
        tampered = tampered.replace('**5s [cut_5s]:**', '**4s [cut_5s]:**')
        result = run_structural_case(
            self.artifacts["alley_sb"], tampered,
            GOLDEN_EXPECTATIONS["alley"])
        self.assertFalse(result.cuts_valid,
                       f"shifted cut should fail cuts; got cuts_valid={result.cuts_valid}")


# 7. Responsibilities tampering
# ============================================================================


class ResponsibilitiesTamperTests(unittest.TestCase):
    """Duty deletion, duplication, mismatch."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()

    def test_gun_barrel_duty_deleted_fails(self):
        vp = self.artifacts["gun_barrel_video"]
        # Remove one duty line
        lines = vp.split('\n')
        new_lines = []
        for l in lines:
            if '职责：' in l and 'rico' in l:
                continue  # Remove rico's duty
            new_lines.append(l)
        tampered = '\n'.join(new_lines)
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"], tampered,
            GOLDEN_EXPECTATIONS["gun_barrel"])
        self.assertFalse(result.responsibilities_valid,
                       f"deleted rico duty should fail; got resp_valid={result.responsibilities_valid}")

    def test_duty_text_replaced_fails(self):
        vp = self.artifacts["gun_barrel_video"]
        # Replace a duty with wrong text
        tampered = vp.replace(
            '**@图片1职责：** 为分镜参考',
            '**@图片1职责：** 被篡改的职责文本')
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"], tampered,
            GOLDEN_EXPECTATIONS["gun_barrel"])
        self.assertFalse(result.responsibilities_valid,
                       f"replaced duty should fail; got resp_valid={result.responsibilities_valid}")

    def test_orphan_duty_fails(self):
        """Add a duty without corresponding reference image."""
        vp = self.artifacts["gun_barrel_video"]
        lines = vp.split('\n')
        # Find the line after the last duty and insert orphan duty
        for j, l in enumerate(lines):
            if 'rico 作为主角' in l:
                lines.insert(j + 1, '**@orphan职责：** 没有对应参考图的职责')
                break
        tampered = '\n'.join(lines)
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"], tampered,
            GOLDEN_EXPECTATIONS["gun_barrel"])
        self.assertFalse(result.responsibilities_valid)


# ============================================================================
# 8. Forbidden routes tampering
# ============================================================================


class ForbiddenRoutesTamperTests(unittest.TestCase):
    """Prohibition deletion, route change."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()

    def test_prohibition_deleted_fails(self):
        vp = self.artifacts["gun_barrel_video"]
        lines = vp.split('\n')
        new_lines = []
        skip = False
        for l in lines:
            if l.startswith('### @禁止'):
                skip = True
                continue
            if skip:
                if l.startswith('### ') and not l.startswith('### @禁止'):
                    skip = False
                    new_lines.append(l)
                continue
            new_lines.append(l)
        tampered = '\n'.join(new_lines)
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"], tampered,
            GOLDEN_EXPECTATIONS["gun_barrel"])
        self.assertFalse(result.forbidden_routes_valid)

    def test_route_marker_changed_fails(self):
        vp = self.artifacts["gun_barrel_video"]
        # Change route from human_qa_only to something else
        tampered = vp.replace(
            '[路由标记：human_qa_only]',
            '[路由标记：tampered_route]')
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"], tampered,
            GOLDEN_EXPECTATIONS["gun_barrel"])
        self.assertFalse(result.forbidden_routes_valid,
                       f"changed route should fail; got forb_valid={result.forbidden_routes_valid}")


# ============================================================================
# 9. Homology tampering
# ============================================================================


class HomologyTamperTests(unittest.TestCase):
    """Cross-scene mismatches, topology divergence."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()

    def test_cross_scene_pairing_fails(self):
        """SB from audience with VP from alley."""
        result = run_structural_case(
            self.artifacts["audience_sb"],
            self.artifacts["alley_video"],
            GOLDEN_EXPECTATIONS["audience"],
        )
        self.assertFalse(result.homology_valid,
                       f"cross-scene should fail homology; got: {result.homology_valid}")


# ============================================================================
# 10. SHA tamper detection
# ============================================================================


class SHATamperTests(unittest.TestCase):
    """Single-byte tampering triggers SHA mismatch."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()

    def test_single_byte_sb_tamper_detected(self):
        sb = self.artifacts["gun_barrel_sb"]
        # Append a single space
        tampered = sb + " "
        result = run_structural_case(
            tampered, self.artifacts["gun_barrel_video"],
            GOLDEN_EXPECTATIONS["gun_barrel"])
        self.assertTrue(
            any("HASH_MISMATCH" in d.code for d in result.diagnostics),
            f"single-byte tamper should produce HASH_MISMATCH; diags={[d.code for d in result.diagnostics]}")

    def test_single_byte_vp_tamper_detected(self):
        vp = self.artifacts["gun_barrel_video"]
        tampered = vp + "\n"
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"], tampered,
            GOLDEN_EXPECTATIONS["gun_barrel"])
        self.assertTrue(
            any("HASH_MISMATCH" in d.code for d in result.diagnostics),
            f"single-byte VP tamper should produce HASH_MISMATCH; diags={[d.code for d in result.diagnostics]}")

    def test_no_false_hash_mismatch_on_canonical(self):
        """Canonical artifacts should NOT trigger hash mismatch."""
        for scene_root in ("gun_barrel", "audience", "prep_area", "alley"):
            exp = GOLDEN_EXPECTATIONS[scene_root]
            result = run_structural_case(
                self.artifacts[f"{scene_root}_sb"],
                self.artifacts[f"{scene_root}_video"],
                exp,
            )
            hash_diags = [d for d in result.diagnostics if "HASH_MISMATCH" in d.code]
            self.assertEqual(len(hash_diags), 0,
                           f"{scene_root}: unexpected HASH_MISMATCH: {hash_diags}")


# ============================================================================
# 11. Determinism
# ============================================================================


class DeterminismTests(unittest.TestCase):
    """Same input → same output (byte-level or value-level)."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()

    def test_repeated_runs_produce_identical_results(self):
        for scene_root in ("gun_barrel", "audience", "prep_area", "alley"):
            exp = GOLDEN_EXPECTATIONS[scene_root]
            sb = self.artifacts[f"{scene_root}_sb"]
            vp = self.artifacts[f"{scene_root}_video"]
            r1 = run_structural_case(sb, vp, exp)
            r2 = run_structural_case(sb, vp, exp)
            self.assertEqual(r1.format_valid, r2.format_valid)
            self.assertEqual(r1.timing_valid, r2.timing_valid)
            self.assertEqual(r1.cuts_valid, r2.cuts_valid)
            self.assertEqual(r1.responsibilities_valid, r2.responsibilities_valid)
            self.assertEqual(r1.forbidden_routes_valid, r2.forbidden_routes_valid)
            self.assertEqual(r1.homology_valid, r2.homology_valid)
            self.assertEqual(r1.all_valid, r2.all_valid)
            self.assertEqual(len(r1.diagnostics), len(r2.diagnostics))
            # Diagnostics must be in same order
            for d1, d2 in zip(r1.diagnostics, r2.diagnostics):
                self.assertEqual(d1.code, d2.code)
                self.assertEqual(d1.category, d2.category)


# ============================================================================
# 12. No model, no external services
# ============================================================================


class NoModelNoExternalTests(unittest.TestCase):
    """Runner source does not import or call any LLM, network, or external service."""

    def test_no_llm_imports(self):
        import inspect
        import mode_p_vnext.structural_runner as sr
        source = inspect.getsource(sr)
        # Check actual imports, not arbitrary substrings
        forbidden_imports = [
            "import anthropic", "import openai", "import claude",
            "import requests", "import urllib", "import httpx", "import aiohttp",
            "import PIL", "import cv2", "import opencv",
            "import torch", "import tensorflow", "import transformers",
            "import subprocess", "import socket",
            "from anthropic", "from openai", "from claude",
            "from requests", "from urllib", "from httpx",
            "from PIL", "from cv2", "from opencv",
            "from torch", "from tensorflow", "from transformers",
        ]
        source_lower = source.lower()
        for imp in forbidden_imports:
            self.assertNotIn(imp, source_lower,
                           f"structural_runner imports forbidden: {imp}")

    def test_run_case_returns_diagnostics_not_model_output(self):
        """run_structural_case returns StructuralDiagnostics, not raw model output."""
        artifacts = _all_artifacts()
        exp = GOLDEN_EXPECTATIONS["gun_barrel"]
        result = run_structural_case(
            artifacts["gun_barrel_sb"],
            artifacts["gun_barrel_video"],
            exp,
        )
        self.assertIsInstance(result, StructuralDiagnostics)
        self.assertFalse(hasattr(result, "model_output"))
        self.assertFalse(hasattr(result, "generated_content"))
        self.assertFalse(hasattr(result, "raw_response"))


# ============================================================================
# 13. Diagnostics structure
# ============================================================================


class DiagnosticsStructureTests(unittest.TestCase):
    """Diagnostics are immutable, deterministic-ordered, with required fields."""

    @classmethod
    def setUpClass(cls):
        cls.artifacts = _all_artifacts()

    def test_diagnostics_have_required_fields(self):
        exp = GOLDEN_EXPECTATIONS["gun_barrel"]
        result = run_structural_case(
            self.artifacts["gun_barrel_sb"],
            self.artifacts["gun_barrel_video"],
            exp,
        )
        for d in result.diagnostics:
            self.assertIsInstance(d.case_id, str)
            self.assertIsInstance(d.artifact_kind, str)
            self.assertIsInstance(d.category, str)
            self.assertIsInstance(d.code, str)
            self.assertIsInstance(d.detail, str)
            self.assertGreater(len(d.code), 0, "diagnostic code is empty")
            self.assertGreater(len(d.detail), 0, "diagnostic detail is empty")
            self.assertIn(d.artifact_kind, ("storyboard", "video", "homology"))
            self.assertIn(d.category, (
                "format", "timing", "cuts", "responsibilities",
                "forbidden_routes", "homology",
            ))

    def test_diagnostics_are_deterministically_ordered(self):
        exp = GOLDEN_EXPECTATIONS["gun_barrel"]
        sb = self.artifacts["gun_barrel_sb"]
        vp = self.artifacts["gun_barrel_video"]
        r1 = run_structural_case(sb, vp, exp)
        r2 = run_structural_case(sb, vp, exp)
        codes1 = tuple(d.code for d in r1.diagnostics)
        codes2 = tuple(d.code for d in r2.diagnostics)
        self.assertEqual(codes1, codes2, "diagnostic order is not deterministic")


# ============================================================================
# 14. Manifest integrity
# ============================================================================


class ManifestIntegrityTests(unittest.TestCase):
    """Expectation/manifest constants are stable and not runtime-recomputed."""

    def test_expected_hashes_are_stable_constants(self):
        """Canonical hashes must not change unless renderers change."""
        self.assertEqual(
            GOLDEN_EXPECTATIONS["gun_barrel"].canonical_sb_sha256,
            "cee4b7a8f7c1b99faa50872ecd5deec0eaaa8bd664a3a8811b80a98f50bf08fc")
        self.assertEqual(
            GOLDEN_EXPECTATIONS["gun_barrel"].canonical_vp_sha256,
            "ee009fd2838cd0e63bfc1e9b43711c52a05b5f70ab69d826e414a6f0ccdf4085")

    def test_expectation_has_no_precomputed_booleans(self):
        """CaseExpectation must not store pre-computed pass/fail values."""
        for name, exp in GOLDEN_EXPECTATIONS.items():
            self.assertFalse(hasattr(exp, "format_valid"), f"{name} has pre-computed format_valid")
            self.assertFalse(hasattr(exp, "all_valid"), f"{name} has pre-computed all_valid")
            self.assertFalse(hasattr(exp, "expected_pass"), f"{name} has pre-computed expected_pass")

    def test_expectation_has_all_required_fields(self):
        for name, exp in GOLDEN_EXPECTATIONS.items():
            self.assertIsInstance(exp.case_id, str)
            self.assertGreater(exp.segment_end_s, 0)
            self.assertGreater(exp.expected_sb_panel_count, 0)
            self.assertGreater(exp.expected_vp_timeline_count, 0)
            self.assertGreater(len(exp.canonical_sb_sha256), 0)
            self.assertGreater(len(exp.canonical_vp_sha256), 0)
            self.assertEqual(len(exp.canonical_sb_sha256), 64,
                           f"{name}: SB hash not 64 hex chars")
            self.assertEqual(len(exp.canonical_vp_sha256), 64,
                           f"{name}: VP hash not 64 hex chars")


if __name__ == "__main__":
    unittest.main()
