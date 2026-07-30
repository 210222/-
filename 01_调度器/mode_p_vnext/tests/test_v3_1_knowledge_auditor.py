"""V3.1 Knowledge Source Auditor — 24-file inventory with disposition tracking."""

import unittest
from pathlib import Path

try:
    from mode_p_vnext import knowledge_auditor as ka
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class KnowledgeAuditorTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "knowledge_auditor not yet implemented")
    def test_inventory_has_24_entries(self):
        inv = ka.load_knowledge_inventory()
        self.assertEqual(len(inv), 24)

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_auditor not yet implemented")
    def test_each_entry_has_required_fields(self):
        required = {"path", "sha256", "bytes", "source_group", "disposition",
                     "license_status", "e0_isolated"}
        for entry in ka.load_knowledge_inventory():
            with self.subTest(path=entry["path"]):
                self.assertTrue(required.issubset(entry.keys()))

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_auditor not yet implemented")
    def test_all_hashes_match_baseline(self):
        manifest = ka._load_baseline_manifest()
        for entry in ka.load_knowledge_inventory():
            with self.subTest(path=entry["path"]):
                # Find matching manifest entry
                match = [m for m in manifest["knowledge_files"]
                          if m["path"] == entry["path"]]
                self.assertEqual(len(match), 1, f"No baseline match for {entry['path']}")
                self.assertEqual(entry["sha256"], match[0]["sha256"])

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_auditor not yet implemented")
    def test_no_undisposed_entries(self):
        """Every knowledge file must have a disposition (not 'pending')."""
        for entry in ka.load_knowledge_inventory():
            with self.subTest(path=entry["path"]):
                self.assertNotEqual(entry["disposition"], "pending",
                                    f"{entry['path']} has pending disposition")

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_auditor not yet implemented")
    def test_offline_sources_are_e0_isolated(self):
        for entry in ka.load_knowledge_inventory():
            if entry["source_group"] == "offline_source":
                with self.subTest(path=entry["path"]):
                    self.assertTrue(entry["e0_isolated"],
                                    f"offline source not E0 isolated: {entry['path']}")

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_auditor not yet implemented")
    def test_audit_report_generated(self):
        report = ka.audit_knowledge_sources()
        self.assertIn("total_files", report)
        self.assertEqual(report["total_files"], 24)
        self.assertIn("by_group", report)
        self.assertIn("disposition_summary", report)

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_auditor not yet implemented")
    def test_no_full_library_load(self):
        """Runtime is permitted a metadata index, never K0/v4 source text."""
        raw_entry = {
            "path": "03_knowledge/archive_book.md",
            "sha256": "raw-hash",
            "source_group": "offline_source",
        }
        index = ka.build_runtime_metadata_index([raw_entry])
        self.assertFalse(index[0]["runtime_allowed"])
        self.assertEqual(index[0]["runtime_reason"], "k0_or_v4_archive_is_read_only_outside_runtime")
        with self.assertRaises(ka.RuntimeKnowledgeIsolationError):
            ka.assert_runtime_source_allowed(
                "offline_source",
                operation="read_full_text",
                source_path=raw_entry["path"],
            )


if __name__ == "__main__":
    unittest.main()
