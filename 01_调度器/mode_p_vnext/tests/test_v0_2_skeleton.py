"""V0.2 Package Skeleton — structure and isolation verification tests.

Verify the vNext package has:
- Proper __init__.py with version export
- version.py with VERSION constant
- schema/ directory
- fixtures/ directory (read-only)
- NO v4 creative compiler imports
- Isolation guard active on package import
"""

import importlib
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path


VNEXT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = VNEXT_ROOT.parent.parent
V4_MODE_P = PROJECT_ROOT / "01_调度器" / "mode_p"


def _v4_creative_modules() -> set[str]:
    """Return the set of v4 creative compiler module names that vNext must not import."""
    creative_patterns = [
        "master_compiler",
        "view_deriver",
        "director_session",
        "batch_scheduler",
        "batch_state_machine",
        "batch_dp",
        "dp_contract",
        "dp_adversarial_check",
        "episode_review",
        "episode_delivery",
        "episode_templates",
        "director_master_template",
        "director_runtime_contract",
        "mode_p_pilot",
        "pilot_strategy",
    ]
    return set(creative_patterns)


class SkeletonStructureTests(unittest.TestCase):
    """Verify the vNext package has the required directory structure."""

    def test_package_init_exists(self):
        init = VNEXT_ROOT / "__init__.py"
        self.assertTrue(init.exists(), f"Missing package init: {init}")

    def test_version_module_exists(self):
        version_py = VNEXT_ROOT / "version.py"
        self.assertTrue(version_py.exists(), f"Missing version module: {version_py}")

    def test_schema_directory_exists(self):
        schema_dir = VNEXT_ROOT / "schema"
        self.assertTrue(schema_dir.is_dir(), f"Missing schema directory: {schema_dir}")
        schema_init = schema_dir / "__init__.py"
        self.assertTrue(schema_init.exists(), f"Missing schema __init__.py: {schema_init}")

    def test_fixtures_directory_exists(self):
        fixtures_dir = VNEXT_ROOT / "fixtures"
        self.assertTrue(fixtures_dir.is_dir(), f"Missing fixtures directory: {fixtures_dir}")
        fixtures_init = fixtures_dir / "__init__.py"
        self.assertTrue(fixtures_init.exists(), f"Missing fixtures __init__.py: {fixtures_init}")

    def test_tests_directory_exists(self):
        tests_dir = VNEXT_ROOT / "tests"
        self.assertTrue(tests_dir.is_dir(), f"Missing tests directory: {tests_dir}")

    def test_readme_exists(self):
        readme = VNEXT_ROOT / "README.md"
        self.assertTrue(readme.exists(), f"Missing README.md: {readme}")


class PackageImportTests(unittest.TestCase):
    """Verify the vNext package can be imported and exports expected attributes."""

    @classmethod
    def setUpClass(cls):
        # Ensure the vNext root is on sys.path so we can import it
        vnext_parent = str(VNEXT_ROOT.parent)
        if vnext_parent not in sys.path:
            sys.path.insert(0, vnext_parent)
        cls.pkg = importlib.import_module("mode_p_vnext")

    def test_package_has_version(self):
        self.assertTrue(hasattr(self.pkg, "__version__"),
                        "Package must export __version__")
        version = self.pkg.__version__
        self.assertIsInstance(version, str)
        self.assertTrue(len(version) > 0)

    def test_package_has_vnext_marker(self):
        self.assertTrue(hasattr(self.pkg, "__mode_p_vnext__"),
                        "Package must export __mode_p_vnext__ marker")
        self.assertTrue(self.pkg.__mode_p_vnext__)

    def test_version_module_exports_version(self):
        version_mod = importlib.import_module("mode_p_vnext.version")
        self.assertTrue(hasattr(version_mod, "VERSION"),
                        "version.py must export VERSION")
        self.assertIsInstance(version_mod.VERSION, str)
        self.assertTrue(len(version_mod.VERSION) > 0)
        # Semantic version pattern
        import re
        self.assertTrue(re.match(r"^\d+\.\d+\.\d+", version_mod.VERSION),
                        f"VERSION must be semver-like, got: {version_mod.VERSION}")

    def test_schema_package_importable(self):
        schema = importlib.import_module("mode_p_vnext.schema")
        self.assertIsNotNone(schema)

    def test_fixtures_package_importable(self):
        fixtures = importlib.import_module("mode_p_vnext.fixtures")
        self.assertIsNotNone(fixtures)


class V4IsolationTests(unittest.TestCase):
    """Verify the vNext package does NOT import v4 creative compiler modules."""

    @classmethod
    def setUpClass(cls):
        vnext_parent = str(VNEXT_ROOT.parent)
        if vnext_parent not in sys.path:
            sys.path.insert(0, vnext_parent)

    def test_no_v4_modules_in_sys_modules_after_import(self):
        """Import isolation must not mutate the main pytest module graph.

        The old test deleted every ``mode_p_vnext`` entry from this process's
        ``sys.modules``.  Collected tests can retain classes/functions from the
        old module objects, so that deletion caused unrelated full-suite
        failures on Windows.  A child interpreter gives the same import proof
        without invalidating the parent process's module identities.
        """
        v4_creative = _v4_creative_modules()
        blocked_modules = [f"mode_p.{name}" for name in sorted(v4_creative)]
        probe = (
            "import importlib,json,sys;"
            f"sys.path.insert(0,{str(VNEXT_ROOT.parent)!r});"
            "importlib.import_module('mode_p_vnext');"
            f"blocked={blocked_modules!r};"
            "print(json.dumps([name for name in blocked if name in sys.modules]))"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])

    def test_init_does_not_contain_v4_import_statements(self):
        """The vNext __init__.py must not contain import statements referencing v4."""
        init_path = VNEXT_ROOT / "__init__.py"
        if not init_path.exists():
            raise unittest.SkipTest("__init__.py does not exist yet")
        content = init_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            # Check for v4 package imports
            self.assertNotIn("import mode_p", stripped,
                             f"v4 import found in __init__.py: {stripped}")
            self.assertNotIn("from mode_p", stripped,
                             f"v4 import found in __init__.py: {stripped}")
            # Check for import via relative path to v4
            self.assertNotIn("01_调度器.mode_p", stripped,
                             f"v4 path reference in __init__.py: {stripped}")

    def test_all_vnext_modules_no_v4_imports(self):
        """Scan every .py file under mode_p_vnext for v4 imports."""
        violations = []
        for py_file in VNEXT_ROOT.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            # Skip test files that deliberately reference "mode_p" for assertion purposes
            if py_file.name.startswith("test_"):
                continue
            content = py_file.read_text(encoding="utf-8")
            rel_path = py_file.relative_to(PROJECT_ROOT)
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or not stripped:
                    continue
                # Only catch actual import statements, not string references
                if re.match(r"^(import mode_p|from mode_p\s)", stripped):
                    violations.append(f"{rel_path}: {stripped}")
        self.assertEqual(
            len(violations), 0,
            f"v4 imports found in vNext modules:\n" + "\n".join(violations)
        )


class FixturesReadOnlyMarkerTests(unittest.TestCase):
    """Verify the fixtures directory is marked as read-only data."""

    def test_fixtures_init_has_readonly_marker(self):
        fixtures_init = VNEXT_ROOT / "fixtures" / "__init__.py"
        if not fixtures_init.exists():
            raise unittest.SkipTest("fixtures/__init__.py does not exist yet")
        content = fixtures_init.read_text(encoding="utf-8")
        has_marker = (
            "READ_ONLY" in content or
            "read_only" in content or
            "readonly" in content
        )
        self.assertTrue(has_marker,
                        "fixtures/__init__.py must declare read-only marker")


if __name__ == "__main__":
    unittest.main()
