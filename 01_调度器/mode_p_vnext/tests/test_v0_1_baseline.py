"""V0.1 Baseline Freeze Manifest — schema and hash verification tests.

These tests verify the vNext baseline manifest records accurate hashes and
metadata for all frozen v4 assets: 24 knowledge files, 8 Golden media files,
v4 entry contracts, and the historic 686-test regression baseline.  Current
collection is checked through the R3.2 registered-cohort reconciliation rather
than by rewriting the historical manifest.

The tests will FAIL if:
- The manifest file is missing or malformed.
- Any recorded hash does not match the actual file on disk.
- The manifest schema is missing required fields.
- Current v4 collection contains an unregistered test delta.
"""

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = (
    PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "vnext_baseline" / "V0.1_FREEZE_MANIFEST.json"
)
MODE_P_DIR = PROJECT_ROOT / "01_调度器" / "mode_p"
COHORT_RECONCILIATION_PATH = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_baseline"
    / "V0.1_CURRENT_COLLECTION_COHORT_RECONCILIATION.json"
)


def _sha256_hex(file_path: Path) -> str:
    """Return lowercase SHA-256 hex digest of file contents."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def _ids_sha256(ids: set[str]) -> str:
    """Return the canonical digest used by the collection reconciliation."""
    canonical = "\n".join(sorted(ids)) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _collect_v4_test_ids(*selection: str) -> set[str]:
    """Collect pytest node IDs without creating cache state."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--co",
            "-q",
            "-p",
            "no:cacheprovider",
            *selection,
        ],
        cwd=str(MODE_P_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "v4 collection failed: "
            f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    ids = {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("test_") and "::" in line
    }
    if not ids:
        raise AssertionError(f"could not parse test IDs:\n{result.stdout}")
    return ids


class ManifestSchemaTests(unittest.TestCase):
    """Verify the baseline manifest exists and has the required schema."""

    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.exists():
            raise unittest.SkipTest(f"Manifest not found: {MANIFEST_PATH}")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_has_required_top_level_keys(self):
        required = [
            "manifest_version",
            "frozen_at",
            "v4_entry_contract",
            "v4_output_products",
            "v4_regression_baseline",
            "knowledge_files",
            "golden_media",
        ]
        for key in required:
            with self.subTest(key=key):
                self.assertIn(key, self.manifest)

    def test_manifest_version_is_v0_1(self):
        self.assertEqual(self.manifest["manifest_version"], "V0.1")

    def test_v4_entry_contract_has_required_fields(self):
        entry = self.manifest["v4_entry_contract"]
        required = ["primary_entry", "entry_module", "entry_function", "cli_command"]
        for key in required:
            with self.subTest(key=key):
                self.assertIn(key, entry)

    def test_v4_output_products_are_listed(self):
        products = self.manifest["v4_output_products"]
        self.assertIsInstance(products, list)
        self.assertGreater(len(products), 0)
        for p in products:
            with self.subTest(product=p.get("name", "unknown")):
                self.assertIn("name", p)
                self.assertIn("path", p)

    def test_v4_regression_baseline_has_count(self):
        baseline = self.manifest["v4_regression_baseline"]
        self.assertIn("test_count", baseline)
        self.assertIn("last_verified", baseline)
        self.assertEqual(baseline["test_count"], 686)

    def test_knowledge_files_has_24_entries(self):
        kf = self.manifest["knowledge_files"]
        self.assertEqual(len(kf), 24, f"Expected 24 knowledge files, got {len(kf)}")

    def test_golden_media_has_8_entries(self):
        gm = self.manifest["golden_media"]
        self.assertEqual(len(gm), 8, f"Expected 8 Golden media files, got {len(gm)}")


class KnowledgeFileHashTests(unittest.TestCase):
    """Verify every knowledge file hash recorded in the manifest."""

    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.exists():
            raise unittest.SkipTest(f"Manifest not found: {MANIFEST_PATH}")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.knowledge_files = cls.manifest["knowledge_files"]

    def _path_for(self, rel_path: str) -> Path:
        return PROJECT_ROOT / rel_path

    def test_all_24_knowledge_files_exist_on_disk(self):
        for entry in self.knowledge_files:
            fpath = self._path_for(entry["path"])
            with self.subTest(path=entry["path"]):
                self.assertTrue(fpath.exists(), f"Missing: {fpath}")

    def test_all_24_knowledge_hashes_match(self):
        for entry in self.knowledge_files:
            fpath = self._path_for(entry["path"])
            if not fpath.exists():
                continue
            with self.subTest(path=entry["path"]):
                actual = _sha256_hex(fpath)
                self.assertEqual(
                    actual, entry["sha256"],
                    f"Hash mismatch for {entry['path']}"
                )

    def test_each_knowledge_entry_has_required_fields(self):
        required = {"path", "sha256", "bytes", "source_group", "disposition"}
        for entry in self.knowledge_files:
            with self.subTest(path=entry["path"]):
                self.assertTrue(required.issubset(entry.keys()),
                                f"Missing fields: {required - set(entry.keys())}")


def _validate_golden_media_entry(entry, project_root):
    """Validate one golden_media entry against its status contract.

    Returns (ok: bool, errors: list[str], info: dict).

    status=available: file MUST exist; SHA-256 and byte count MUST match.
    status=missing:  file may be absent; missing_reason MUST be non-empty.
    Any other status value or missing status field is an error.
    """
    errors = []
    info = {"key": entry.get("key", "unknown")}

    status = entry.get("status")
    if status not in ("available", "missing"):
        errors.append(
            f"Golden media '{info['key']}': status must be 'available' or 'missing', "
            f"got {status!r}"
        )
        return (False, errors, info)

    info["status"] = status
    fpath = Path(entry["path"])
    file_exists = fpath.exists()
    info["file_exists"] = file_exists

    if status == "available":
        if not file_exists:
            errors.append(
                f"Golden media '{info['key']}': status=available but file is MISSING: {fpath}"
            )
            return (False, errors, info)
        # Verify SHA-256
        actual_sha256 = _sha256_hex(fpath)
        info["sha256_match"] = (actual_sha256 == entry["sha256"])
        if not info["sha256_match"]:
            errors.append(
                f"Golden media '{info['key']}': hash mismatch — "
                f"manifest={entry['sha256'][:16]}... actual={actual_sha256[:16]}..."
            )
        # Verify byte count
        actual_bytes = fpath.stat().st_size
        info["bytes_match"] = (actual_bytes == entry["bytes"])
        if not info["bytes_match"]:
            errors.append(
                f"Golden media '{info['key']}': byte count mismatch — "
                f"manifest={entry['bytes']} actual={actual_bytes}"
            )
    elif status == "missing":
        reason = entry.get("missing_reason", "")
        info["missing_reason"] = reason
        if not reason or not reason.strip():
            errors.append(
                f"Golden media '{info['key']}': status=missing but missing_reason is empty"
            )
        # If the file happens to exist for a "missing" entry, that is not an error
        # (the manifest declares it unavailable regardless of disk state).

    return (len(errors) == 0, errors, info)


class GoldenMediaHashTests(unittest.TestCase):
    """Verify Golden media file integrity against the baseline manifest.

    Every entry MUST carry a ``status`` field (``available`` or ``missing``).
    Silent skip (``continue`` on absent file) is FORBIDDEN — the R1.1 repair
    plan requires explicit marking of unavailable media.
    """

    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.exists():
            raise unittest.SkipTest(f"Manifest not found: {MANIFEST_PATH}")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.golden = cls.manifest["golden_media"]

    # ── schema tests ──────────────────────────────────────────────────

    def test_each_golden_entry_has_required_fields(self):
        required = {"key", "scene", "media_type", "path", "sha256", "bytes",
                     "width", "height", "format", "status"}
        for entry in self.golden:
            with self.subTest(key=entry.get("key", "unknown")):
                missing = required - set(entry.keys())
                self.assertFalse(missing, f"Missing fields: {missing}")

    def test_golden_media_status_closed_vocabulary(self):
        """Every entry status must be 'available' or 'missing'."""
        for entry in self.golden:
            with self.subTest(key=entry.get("key", "unknown")):
                status = entry.get("status")
                self.assertIn(status, ("available", "missing"),
                              f"Invalid status {status!r}")

    def test_all_8_golden_entries_accounted_once(self):
        keys = {e["key"] for e in self.golden}
        expected = {"gun_barrel_sb", "gun_barrel_video",
                    "audience_sb", "audience_video",
                    "prep_area_sb", "prep_area_video",
                    "alley_sb", "alley_video"}
        self.assertEqual(keys, expected,
                         f"Golden key set mismatch: {keys ^ expected}")

    # ── existence + hash tests (status-aware) ─────────────────────────

    def test_all_golden_media_exist_on_disk(self):
        """status=available entries MUST exist.  status=missing entries
        produce an explicit structured record and never masquerade as
        verified media."""
        available_count = 0
        missing_entries = []
        for entry in self.golden:
            ok, errors, info = _validate_golden_media_entry(entry, PROJECT_ROOT)
            with self.subTest(key=entry.get("key", "unknown")):
                if info.get("status") == "available":
                    available_count += 1
                    self.assertTrue(
                        info.get("file_exists", False),
                        f"status=available but file is MISSING: {entry['path']}"
                    )
                elif info.get("status") == "missing":
                    missing_entries.append({
                        "key": entry["key"],
                        "path": entry["path"],
                        "missing_reason": info.get("missing_reason", ""),
                    })
                # Accumulate all validation errors
                for err in errors:
                    self.fail(err)
        # Report structured missing record for auditability
        if missing_entries:
            # This is NOT a failure — it is a structured audit record
            pass  # available in self._missing_entries if needed downstream
        self._missing_entries = missing_entries
        self._available_count = available_count

    def test_all_golden_hashes_match(self):
        """Verify SHA-256 and byte count for every available entry.
        Missing entries are validated by the existence test above."""
        for entry in self.golden:
            ok, errors, info = _validate_golden_media_entry(entry, PROJECT_ROOT)
            with self.subTest(key=entry.get("key", "unknown")):
                for err in errors:
                    self.fail(err)

    def test_golden_media_missing_has_reason(self):
        """Every status=missing entry MUST carry a non-empty missing_reason."""
        for entry in self.golden:
            if entry.get("status") != "missing":
                continue
            with self.subTest(key=entry.get("key", "unknown")):
                reason = entry.get("missing_reason", "")
                self.assertTrue(
                    reason and reason.strip(),
                    f"status=missing but missing_reason is absent or whitespace-only"
                )

    # ── controlled-fixture tests ──────────────────────────────────────

    def test_controlled_available_missing_file_fails(self):
        """A status=available entry whose path does not exist MUST fail."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            temp_root = Path(td)
            # Create a real file so we can hash it, then DELETE it
            real = temp_root / "will_be_deleted.bin"
            real.write_bytes(b"controlled-fixture-content-v1")
            real_sha256 = _sha256_hex(real)
            real_bytes = real.stat().st_size
            real.unlink()  # file no longer exists

            entry = {
                "key": "controlled_test",
                "scene": "fixture",
                "media_type": "storyboard_image",
                "path": str(real),
                "sha256": real_sha256,
                "bytes": real_bytes,
                "width": 2560,
                "height": 1440,
                "format": "PNG",
                "status": "available",
            }
            ok, errors, info = _validate_golden_media_entry(entry, temp_root)
            self.assertFalse(ok, "status=available with missing file MUST fail")
            self.assertFalse(info.get("file_exists", True),
                             "file should not exist after unlink")
            self.assertGreater(len(errors), 0,
                               "Expected at least one error for missing file")

    def test_controlled_missing_produces_explicit_record(self):
        """A status=missing entry with a reason MUST pass validation and
        produce an explicit structured record — never a silent pass."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            temp_root = Path(td)
            nonexistent = temp_root / "does_not_exist.png"

            entry = {
                "key": "controlled_missing_test",
                "scene": "fixture",
                "media_type": "video",
                "path": str(nonexistent),
                "sha256": "0" * 64,
                "bytes": 0,
                "width": 0,
                "height": 0,
                "format": "unknown",
                "status": "missing",
                "missing_reason": "External drive disconnected; will revalidate on reconnect.",
            }
            ok, errors, info = _validate_golden_media_entry(entry, temp_root)
            self.assertTrue(ok, f"status=missing with reason should pass: {errors}")
            self.assertEqual(info.get("status"), "missing")
            self.assertFalse(info.get("file_exists", True),
                             "file should not exist")
            self.assertEqual(info.get("missing_reason"),
                             "External drive disconnected; will revalidate on reconnect.")

    def test_controlled_missing_without_reason_fails(self):
        """A status=missing entry with empty missing_reason MUST fail."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            temp_root = Path(td)
            nonexistent = temp_root / "also_absent.png"

            entry = {
                "key": "no_reason_test",
                "scene": "fixture",
                "media_type": "video",
                "path": str(nonexistent),
                "sha256": "0" * 64,
                "bytes": 0,
                "width": 0,
                "height": 0,
                "format": "unknown",
                "status": "missing",
                "missing_reason": "",
            }
            ok, errors, info = _validate_golden_media_entry(entry, temp_root)
            self.assertFalse(ok, "status=missing with empty reason MUST fail")
            self.assertIn("missing_reason", errors[0].lower() if errors else "",
                          "error should mention missing_reason")

    def test_controlled_corrupt_hash_fails(self):
        """A status=available entry with wrong SHA-256 MUST fail."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            temp_root = Path(td)
            real = temp_root / "corrupt_test.bin"
            real.write_bytes(b"actual-content")
            actual_sha256 = _sha256_hex(real)

            entry = {
                "key": "corrupt_hash_test",
                "scene": "fixture",
                "media_type": "storyboard_image",
                "path": str(real),
                "sha256": "0" * 64,  # deliberately wrong
                "bytes": real.stat().st_size,
                "width": 2560,
                "height": 1440,
                "format": "PNG",
                "status": "available",
            }
            ok, errors, info = _validate_golden_media_entry(entry, temp_root)
            self.assertFalse(ok, "Wrong SHA-256 MUST fail")
            self.assertFalse(info.get("sha256_match", True),
                             "sha256_match must be False")

    def test_controlled_bytes_mismatch_fails(self):
        """A status=available entry with wrong byte count MUST fail."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            temp_root = Path(td)
            real = temp_root / "bytes_test.bin"
            real.write_bytes(b"exact-content")
            real_sha256 = _sha256_hex(real)

            entry = {
                "key": "bytes_mismatch_test",
                "scene": "fixture",
                "media_type": "storyboard_image",
                "path": str(real),
                "sha256": real_sha256,
                "bytes": 999999,  # deliberately wrong
                "width": 2560,
                "height": 1440,
                "format": "PNG",
                "status": "available",
            }
            ok, errors, info = _validate_golden_media_entry(entry, temp_root)
            self.assertFalse(ok, "Wrong byte count MUST fail")
            self.assertFalse(info.get("bytes_match", True),
                             "bytes_match must be False")

    def test_no_status_field_fails(self):
        """An entry without a 'status' field MUST fail validation."""
        entry = {
            "key": "no_status_test",
            "scene": "fixture",
            "media_type": "storyboard_image",
            "path": "/nonexistent/path.png",
            "sha256": "0" * 64,
            "bytes": 100,
            "width": 2560,
            "height": 1440,
            "format": "PNG",
        }
        ok, errors, info = _validate_golden_media_entry(entry, PROJECT_ROOT)
        self.assertFalse(ok, "Missing status field MUST fail")
        self.assertIn("status", errors[0].lower() if errors else "",
                      "error should mention 'status'")

    def test_no_silent_continue_behavior(self):
        """Regression: the ``_validate_golden_media_entry`` function MUST NOT
        contain a ``continue`` statement after a file-existence check.
        This is the R1.1 defect — ``if not fpath.exists(): continue``."""
        import inspect
        import re
        source = inspect.getsource(_validate_golden_media_entry)
        lines = source.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'\bcontinue\b', stripped):
                for j in range(max(0, i - 3), i):
                    prev = lines[j].strip()
                    if prev.startswith("#"):
                        continue
                    if re.search(r'(?:exists\(\)|\.exists\(\))', prev, re.IGNORECASE):
                        self.fail(
                            f"Silent continue in _validate_golden_media_entry: "
                            f"line {i+1} '{stripped}' follows existence check "
                            f"at line {j+1} '{prev}'"
                        )


class V4RegressionFreshnessTests(unittest.TestCase):
    """Verify the v4 regression baseline is still current."""

    def test_v4_collection_matches_registered_cohorts(self):
        """Keep 686 historical while failing closed on current unregistered drift."""
        self.assertTrue(COHORT_RECONCILIATION_PATH.is_file())
        reconciliation = json.loads(
            COHORT_RECONCILIATION_PATH.read_text(encoding="utf-8")
        )
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        frozen = reconciliation["frozen_manifest"]
        cohorts = reconciliation["cohorts"]
        relation = reconciliation["set_relation"]
        generic = cohorts["reconstructed_generic_candidate"]
        legacy = cohorts["legacy_ep35_s1_post_freeze"]

        self.assertEqual(
            manifest["v4_regression_baseline"]["test_count"],
            frozen["declared_test_count"],
        )
        self.assertEqual(frozen["declared_test_count"], 686)
        self.assertFalse(frozen["historical_exact_collection_ids_available"])
        self.assertFalse(
            generic["may_be_described_as_exact_2026_07_22_frozen_id_set"]
        )
        self.assertFalse(legacy["design_source_for_vnext"])

        legacy_source = PROJECT_ROOT / legacy["source_path"]
        self.assertTrue(legacy_source.is_file())
        self.assertEqual(_sha256_hex(legacy_source), legacy["source_sha256"])

        all_ids = _collect_v4_test_ids()
        legacy_ids = _collect_v4_test_ids(*legacy["selection"])
        generic_ids = _collect_v4_test_ids(*generic["selection"])

        self.assertEqual(len(all_ids), reconciliation["current_collection"]["count"])
        self.assertEqual(
            _ids_sha256(all_ids),
            reconciliation["current_collection"]["sorted_test_ids_sha256"],
        )
        self.assertEqual(len(legacy_ids), legacy["count"])
        self.assertEqual(_ids_sha256(legacy_ids), legacy["sorted_test_ids_sha256"])
        self.assertEqual(len(generic_ids), generic["count"])
        self.assertEqual(_ids_sha256(generic_ids), generic["sorted_test_ids_sha256"])
        self.assertEqual(
            len(legacy_ids & generic_ids),
            relation["legacy_intersects_reconstructed_generic"],
        )
        self.assertEqual(
            len(legacy_ids | generic_ids),
            relation["legacy_union_reconstructed_generic_count"],
        )
        self.assertEqual(legacy_ids | generic_ids, all_ids)
        self.assertTrue(relation["current_collection_equals_registered_union"])
        self.assertEqual(relation["unexplained_delta_count"], 0)


class AuthorityFileHashTests(unittest.TestCase):
    """Verify all authority file hashes in the baseline manifest.

    Authority files are project-controlled text files (Agent defs, commands,
    LOOP specs, audits, asset indexes). Unlike Golden media, these must NEVER
    be silently skipped — a missing authority file is a hard failure.
    """

    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.exists():
            raise unittest.SkipTest(f"Manifest not found: {MANIFEST_PATH}")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.authority_files = cls.manifest.get("authority_files", [])

    def test_authority_files_section_exists(self):
        self.assertIn("authority_files", self.manifest)
        self.assertIsInstance(self.authority_files, list)
        self.assertGreater(len(self.authority_files), 0,
                           "authority_files must not be empty")

    def test_exactly_13_authority_files(self):
        self.assertEqual(len(self.authority_files), 13,
                         f"Expected 13 authority files, got {len(self.authority_files)}")

    def test_all_authority_files_have_required_fields(self):
        required = {"path", "role", "sha256"}
        for entry in self.authority_files:
            with self.subTest(path=entry.get("path", "unknown")):
                missing = required - set(entry.keys())
                self.assertFalse(missing, f"Missing fields: {missing}")

    def test_no_null_authority_hash(self):
        """Regression: all 13 were null before R1.1 repair."""
        nulls = [e["path"] for e in self.authority_files
                 if e.get("sha256") is None]
        self.assertEqual(len(nulls), 0,
                         f"Authority files with null SHA-256: {nulls}. "
                         f"All must have real hashes.")

    def test_all_authority_files_exist_on_disk(self):
        """Authority files must exist — no silent skipping."""
        for entry in self.authority_files:
            fpath = PROJECT_ROOT / entry["path"]
            with self.subTest(path=entry["path"]):
                self.assertTrue(fpath.exists(),
                                f"Authority file MISSING: {fpath}. "
                                f"Either restore it or remove it from the manifest "
                                f"with an explicit 'status: unavailable' field.")

    def test_all_authority_hashes_match(self):
        """Every authority file hash must match current disk content."""
        for entry in self.authority_files:
            fpath = PROJECT_ROOT / entry["path"]
            if not fpath.exists():
                self.fail(f"Cannot verify hash: {entry['path']} is missing.")
            with self.subTest(path=entry["path"]):
                actual = _sha256_hex(fpath)
                expected = entry["sha256"]
                self.assertEqual(
                    actual, expected,
                    f"Authority DRIFT detected for {entry['path']}\n"
                    f"  manifest hash: {expected}\n"
                    f"  disk hash:     {actual}\n"
                    f"  The file has changed since the baseline was frozen."
                )


if __name__ == "__main__":
    unittest.main()
