"""V9.4 v4 Compatibility & Legacy Session Isolation."""

import importlib
import sys
import unittest
from pathlib import Path

from mode_p_vnext.tests._baseline_cohort_support import assert_registered_v4_collection


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODE_P = PROJECT_ROOT / "01_调度器" / "mode_p"
VNEXT = PROJECT_ROOT / "01_调度器" / "mode_p_vnext"

# v4 creative modules that must NOT be imported by vNext
_V4_CREATIVE = frozenset({
    "mode_p.master_compiler", "mode_p.mode_p_pilot", "mode_p.director_session",
    "mode_p.batch_scheduler", "mode_p.batch_state_machine", "mode_p.batch_dp",
    "mode_p.dp_contract", "mode_p.episode_review", "mode_p.episode_delivery",
    "mode_p.pilot_strategy", "mode_p.view_deriver",
})


class V4CompatibilityTests(unittest.TestCase):
    """Verify v4 remains unchanged and vNext/v4 isolation holds."""

    def test_v4_entry_point_exists(self):
        """v4 mode_p_pilot.py must still exist."""
        entry = MODE_P / "mode_p_pilot.py"
        self.assertTrue(entry.exists(), f"v4 entry missing: {entry}")

    def test_v4_collection_matches_registered_cohorts(self):
        """v4 must have no unregistered collection drift or cohort overlap."""
        assert_registered_v4_collection()

    def test_v4_run_command_unchanged(self):
        """v4 can still be invoked via its documented command."""
        pilot = MODE_P / "mode_p_pilot.py"
        content = pilot.read_text(encoding="utf-8")
        self.assertIn("def run_pilot", content)
        self.assertIn("def main", content)

    def test_vnext_no_v4_creative_imports(self):
        """No .py file in vNext imports v4 creative modules."""
        violations = []
        for py_file in VNEXT.rglob("*.py"):
            if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
                continue
            content = py_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                s = line.strip()
                if s.startswith("#") or not s:
                    continue
                if s.startswith("import mode_p."):
                    mod = s.split()[1]
                    if mod in _V4_CREATIVE or mod.startswith("mode_p."):
                        violations.append(f"{py_file.name}: {s}")
                if s.startswith("from mode_p.") and "import" in s:
                    parts = s.split()
                    mod = "mode_p." + parts[1].split(".")[0]
                    if mod in _V4_CREATIVE:
                        violations.append(f"{py_file.name}: {s}")
        self.assertEqual(len(violations), 0,
                         f"v4 imports in vNext: {violations}")

    def test_v4_no_vnext_imports(self):
        """No .py file in v4 imports vNext modules."""
        violations = []
        for py_file in MODE_P.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            content = py_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                s = line.strip()
                if s.startswith("#") or not s:
                    continue
                if "mode_p_vnext" in s and (s.startswith("import") or s.startswith("from")):
                    rel = py_file.relative_to(PROJECT_ROOT)
                    violations.append(f"{rel}: {s}")
        self.assertEqual(len(violations), 0,
                         f"vNext imports in v4: {violations}")

    def test_vnext_standalone_import(self):
        """mode_p_vnext can be imported without triggering v4 imports."""
        import mode_p_vnext
        self.assertTrue(mode_p_vnext.__mode_p_vnext__)
        # Verify no v4 creative modules are now in sys.modules
        for mod in _V4_CREATIVE:
            self.assertNotIn(mod, sys.modules,
                             f"v4 module '{mod}' loaded by vNext import")


if __name__ == "__main__":
    unittest.main()
