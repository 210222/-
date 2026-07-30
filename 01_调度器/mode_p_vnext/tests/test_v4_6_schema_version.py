"""V4.6 Schema Version & Migration Strategy."""

import unittest

try:
    from mode_p_vnext import schema_version as sv
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class SchemaVersionTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "schema_version not yet implemented")
    def test_current_version(self):
        self.assertEqual(sv.CURRENT_SCHEMA_VERSION, "4.0")

    @unittest.skipIf(not MODULE_EXISTS, "schema_version not yet implemented")
    def test_compatible_versions(self):
        self.assertTrue(sv.is_compatible("4.0", "4.0"))
        self.assertTrue(sv.is_compatible("4.0", "4.1"))

    @unittest.skipIf(not MODULE_EXISTS, "schema_version not yet implemented")
    def test_major_version_incompatible(self):
        self.assertFalse(sv.is_compatible("3.0", "4.0"))
        self.assertFalse(sv.is_compatible("4.0", "5.0"))

    @unittest.skipIf(not MODULE_EXISTS, "schema_version not yet implemented")
    def test_major_change_invalidates_approvals(self):
        self.assertTrue(sv.major_change_invalidates("3.9", "4.0"))
        self.assertFalse(sv.major_change_invalidates("4.0", "4.1"))

    @unittest.skipIf(not MODULE_EXISTS, "schema_version not yet implemented")
    def test_no_writeback_to_old_sessions(self):
        """Migration is read-only — never writes back to old schema sessions."""
        self.assertTrue(sv.MIGRATION_READ_ONLY)


if __name__ == "__main__":
    unittest.main()
