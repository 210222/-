"""V0.4 v4/vNext Contamination Scanner — isolation enforcement tests.

Verify:
- vNext code cannot write into v4 Session/delivery paths (ContaminationError)
- vNext code can write into its own territory
- v4 active entrypoints do not import unapproved vNext modules
- Explicit read-only baseline fixture cross-references are allowed
"""

import sys
import tempfile
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
try:
    from mode_p_vnext import contamination_scanner as cs
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VNEXT_ROOT = Path(__file__).resolve().parent.parent
MODE_P_ROOT = PROJECT_ROOT / "01_调度器" / "mode_p"


# ---------------------------------------------------------------------------
# Write safety tests
# ---------------------------------------------------------------------------

class WriteSafetyTests(unittest.TestCase):
    """vNext must not write into v4 Session or delivery territory."""

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_write_to_v4_session_dir_raises(self):
        target = MODE_P_ROOT / "sessions" / "ep1_sc1" / "output.json"
        with self.assertRaises(cs.ContaminationError):
            cs.check_vnext_write_safe(target)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_write_to_v4_delivery_dir_raises(self):
        target = MODE_P_ROOT / "delivery" / "STORYBOARD.md"
        with self.assertRaises(cs.ContaminationError):
            cs.check_vnext_write_safe(target)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_write_to_v4_cache_raises(self):
        target = MODE_P_ROOT / ".cache" / "knowledge.pkl"
        with self.assertRaises(cs.ContaminationError):
            cs.check_vnext_write_safe(target)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_write_to_vnext_dir_passes(self):
        target = VNEXT_ROOT / "output" / "test.json"
        # Must not raise
        cs.check_vnext_write_safe(target)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_write_to_project_root_passes(self):
        target = PROJECT_ROOT / "some_output.txt"
        cs.check_vnext_write_safe(target)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_write_to_vnext_baseline_passes(self):
        """Allowed cross-ref: baseline manifest is read-only fixture territory."""
        target = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "vnext_baseline" / "data.json"
        cs.check_vnext_write_safe(target)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_write_to_v4_knowledge_dir_raises(self):
        target = MODE_P_ROOT / "knowledge" / "core" / "new_file.md"
        with self.assertRaises(cs.ContaminationError):
            cs.check_vnext_write_safe(target)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_write_to_v4_top_level_raises(self):
        target = MODE_P_ROOT / "some_config.json"
        with self.assertRaises(cs.ContaminationError):
            cs.check_vnext_write_safe(target)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_check_write_safe_accepts_str_and_path(self):
        # Both str and Path should work
        cs.check_vnext_write_safe(str(VNEXT_ROOT / "ok.txt"))
        cs.check_vnext_write_safe(VNEXT_ROOT / "ok.txt")

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_error_message_contains_target_path(self):
        target = MODE_P_ROOT / "sessions" / "ep1" / "data.json"
        try:
            cs.check_vnext_write_safe(target)
            self.fail("Expected ContaminationError")
        except cs.ContaminationError as e:
            self.assertIn(str(target), str(e))


# ---------------------------------------------------------------------------
# v4 import scan tests
# ---------------------------------------------------------------------------

class V4ImportScanTests(unittest.TestCase):
    """v4 active entrypoints must not import unapproved vNext modules."""

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_scan_v4_entrypoints_no_violations(self):
        """Baseline: current v4 files do NOT import vNext."""
        violations = cs.scan_v4_for_vnext_imports()
        self.assertEqual(
            len(violations), 0,
            f"v4 files importing vNext found:\n" + "\n".join(violations)
        )

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_scan_returns_list_of_strings(self):
        result = cs.scan_v4_for_vnext_imports()
        self.assertIsInstance(result, list)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_detect_hypothetical_v4_import_of_vnext(self):
        """Use a temp file to verify detection works on a constructed violation."""
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write("import mode_p_vnext\n")
            f.write("from mode_p_vnext import something\n")
            tmp = Path(f.name)
        try:
            violations = cs._scan_file_for_vnext_imports(tmp)
            self.assertGreater(len(violations), 0)
            self.assertTrue(any("import mode_p_vnext" in v for v in violations))
        finally:
            tmp.unlink(missing_ok=True)

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_clean_file_no_violations(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write("import os\nimport json\nfrom pathlib import Path\n")
            tmp = Path(f.name)
        try:
            violations = cs._scan_file_for_vnext_imports(tmp)
            self.assertEqual(len(violations), 0)
        finally:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Allowed cross-references
# ---------------------------------------------------------------------------

class AllowedCrossRefsTests(unittest.TestCase):
    """Explicit read-only cross-references are permitted."""

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_allowed_cross_refs_is_a_set(self):
        self.assertIsInstance(cs.ALLOWED_VNEXT_REFS_FROM_V4, (set, frozenset))

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_baseline_manifest_is_allowed(self):
        """V0.1 baseline manifest is explicitly a read-only cross-ref."""
        baseline = "MODE_P_REDESIGN_PROJECT/vnext_baseline/"
        is_allowed = any(baseline in ref for ref in cs.ALLOWED_VNEXT_REFS_FROM_V4)
        self.assertTrue(is_allowed,
                        f"vnext_baseline must be in ALLOWED_VNEXT_REFS_FROM_V4")

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_v4_session_paths_not_in_allowed(self):
        """v4 session paths must NOT be in the allowed list."""
        suspicious = [ref for ref in cs.ALLOWED_VNEXT_REFS_FROM_V4
                       if "session" in ref.lower() or "delivery" in ref.lower()]
        self.assertEqual(len(suspicious), 0,
                         f"Suspicious refs in allowlist: {suspicious}")

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_is_readonly_baseline_positive(self):
        baseline = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "vnext_baseline" / "V0.1_FREEZE_MANIFEST.json"
        self.assertTrue(cs.is_allowed_readonly_ref(baseline))

    @unittest.skipIf(not MODULE_EXISTS, "contamination_scanner not yet implemented")
    def test_is_readonly_baseline_negative(self):
        not_allowed = MODE_P_ROOT / "mode_p_pilot.py"
        self.assertFalse(cs.is_allowed_readonly_ref(not_allowed))


if __name__ == "__main__":
    unittest.main()
