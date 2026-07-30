"""V7.5 DP Cache & Anti-Idle."""

import unittest

try:
    from mode_p_vnext import dp_cache as dc
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DPCacheTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "dp_cache not yet implemented")
    def test_cache_key_includes_all_components(self):
        key = dc.compute_dp_cache_key(
            dp_view_hash="abc",
            capability_hash="def",
            asset_hash="ghi",
            implementation_version="0.1.0",
        )
        self.assertEqual(len(key), 64)

    @unittest.skipIf(not MODULE_EXISTS, "dp_cache not yet implemented")
    def test_same_inputs_same_key(self):
        k1 = dc.compute_dp_cache_key("a", "b", "c", "1.0")
        k2 = dc.compute_dp_cache_key("a", "b", "c", "1.0")
        self.assertEqual(k1, k2)

    @unittest.skipIf(not MODULE_EXISTS, "dp_cache not yet implemented")
    def test_different_inputs_different_key(self):
        k1 = dc.compute_dp_cache_key("a", "b", "c", "1.0")
        k2 = dc.compute_dp_cache_key("x", "b", "c", "1.0")
        self.assertNotEqual(k1, k2)

    @unittest.skipIf(not MODULE_EXISTS, "dp_cache not yet implemented")
    def test_anti_idle_detection(self):
        cache = dc.DPCache()
        key = dc.compute_dp_cache_key("a", "b", "c", "1.0")
        cache.record(key, "READY")
        self.assertTrue(cache.is_duplicate_question(key))

    @unittest.skipIf(not MODULE_EXISTS, "dp_cache not yet implemented")
    def test_fresh_context_is_single_use_after_revision(self):
        cache = dc.DPCache()
        key = dc.compute_dp_cache_key("view-2", "cap", "asset", "1.0")
        record = cache.record(key, "DIRECTED_QUESTION", context_id="CTX-1", revision_id="REV-1")
        self.assertEqual(record.context_id, "CTX-1")
        self.assertNotEqual(
            dc.compute_dp_invocation_key(key, "CTX-1", "REV-1"),
            dc.compute_dp_invocation_key(key, "CTX-2", "REV-1"),
        )
        with self.assertRaises(ValueError):
            cache.record(key, "READY", context_id="CTX-1", revision_id="REV-2")


if __name__ == "__main__":
    unittest.main()
