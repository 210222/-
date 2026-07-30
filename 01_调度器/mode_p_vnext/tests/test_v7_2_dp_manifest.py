"""V7.2 DP Packet Manifest."""

import unittest

try:
    from mode_p_vnext import dp_manifest as dm
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DPManifestTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "dp_manifest not yet implemented")
    def test_manifest_fields(self):
        m = dm.DPPacketManifest(
            manifest_id="DPM001",
            context_id="CTX_fresh_001",
            whitelist_fields=["script_facts", "storyboard_view"],
            field_hashes={"script_facts": "abc123"},
        )
        self.assertEqual(m.context_id, "CTX_fresh_001")
        self.assertIn("script_facts", m.whitelist_fields)

    @unittest.skipIf(not MODULE_EXISTS, "dp_manifest not yet implemented")
    def test_manifest_fresh_context_id(self):
        """Each DP invocation gets a fresh context_id."""
        m = dm.DPPacketManifest(
            manifest_id="DPM002",
            context_id="CTX_20260722_001",
            whitelist_fields=[],
            field_hashes={},
        )
        self.assertTrue(len(m.context_id) > 0)
        self.assertTrue(m.is_fresh_context)

    @unittest.skipIf(not MODULE_EXISTS, "dp_manifest not yet implemented")
    def test_content_hash(self):
        m = dm.DPPacketManifest(
            manifest_id="DPM003", context_id="CTX_001",
            whitelist_fields=["x"], field_hashes={"x": "abc"},
        )
        self.assertEqual(len(m.content_sha256), 64)

    @unittest.skipIf(not MODULE_EXISTS, "dp_manifest not yet implemented")
    def test_fresh_registry_rejects_context_reuse(self):
        registry = dm.FreshDPContextRegistry()
        sources = {"storyboard_view": "panel one", "visibility_view": {"S1": "clear"}}
        first = dm.create_dp_packet_manifest("DPM-FRESH-1", sources, context_id="CTX-FRESH-1", registry=registry)
        self.assertTrue(first.verify_integrity())
        with self.assertRaises(dm.DPContextReuseError):
            dm.create_dp_packet_manifest("DPM-FRESH-2", sources, context_id="CTX-FRESH-1", registry=registry)

    @unittest.skipIf(not MODULE_EXISTS, "dp_manifest not yet implemented")
    def test_child_context_cannot_equal_parent_context(self):
        registry = dm.FreshDPContextRegistry()
        manifest = dm.create_dp_packet_manifest(
            "DPM-CHILD", {"storyboard_view": "panel"}, context_id="CTX-ONE",
            parent_context_id="CTX-ONE",
        )
        with self.assertRaises(dm.DPContextReuseError):
            registry.register(manifest)


if __name__ == "__main__":
    unittest.main()
