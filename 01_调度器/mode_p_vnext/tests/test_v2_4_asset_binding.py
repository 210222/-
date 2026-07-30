"""V2.4 Reference/Asset Binding — hash, slot, responsibility, conflict resolution."""

import unittest

try:
    from mode_p_vnext.schema import asset_binding as ab
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class AssetBindingTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_binding_required_fields(self):
        b = ab.AssetBinding(
            asset_id="@图片1",
            content_sha256="d995353f808a",
            version="1.0",
            platform_slot="reference_image_0",
            responsibility="storyboard_reference",
        )
        self.assertEqual(b.asset_id, "@图片1")
        self.assertEqual(b.responsibility, "storyboard_reference")
        self.assertTrue(b.authorized)

    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_unauthorized_binding(self):
        b = ab.AssetBinding(
            asset_id="@未授权素材",
            content_sha256="abc123",
            version="1.0",
            platform_slot="ref_1",
            responsibility="storyboard_reference",
            authorized=False,
        )
        self.assertFalse(b.authorized)

    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_binding_with_crop(self):
        b = ab.AssetBinding(
            asset_id="@图片1", content_sha256="abc", version="1",
            platform_slot="ref_0", responsibility="storyboard_reference",
            crop="16:9→9:16 center",
        )
        self.assertEqual(b.crop, "16:9→9:16 center")

    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_time_range(self):
        from mode_p_vnext.schema.canonical_timeline import TimeInterval
        b = ab.AssetBinding(
            asset_id="@图片1", content_sha256="abc", version="1",
            platform_slot="ref_0", responsibility="storyboard_reference",
            valid_time_range=TimeInterval(0, 48000),
        )
        self.assertEqual(b.valid_time_range.start_tick, 0)

    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_project_isolation_default(self):
        b = ab.AssetBinding(
            asset_id="@图片1", content_sha256="abc", version="1",
            platform_slot="ref_0", responsibility="storyboard_reference",
        )
        self.assertEqual(b.project_id, "")

    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_conflict_same_slot_different_asset(self):
        b1 = ab.AssetBinding("@A", "hashA", "1", "slot_0", "storyboard_reference")
        b2 = ab.AssetBinding("@B", "hashB", "1", "slot_0", "storyboard_reference")
        conflicts = ab.check_asset_conflicts([b1, b2])
        self.assertGreater(len(conflicts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_no_conflict_different_slots(self):
        b1 = ab.AssetBinding("@A", "hashA", "1", "slot_0", "storyboard_reference")
        b2 = ab.AssetBinding("@B", "hashB", "1", "slot_1", "video_reference")
        conflicts = ab.check_asset_conflicts([b1, b2])
        self.assertEqual(len(conflicts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_unauthorized_binding_flagged(self):
        b = ab.AssetBinding("@X", "hash", "1", "slot_0", "storyboard_reference",
                            authorized=False)
        violations = ab.check_asset_authorization([b])
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "asset_binding not yet implemented")
    def test_to_dict(self):
        b = ab.AssetBinding("@img", "abc123", "2.0", "ref_0",
                            "storyboard_reference", crop="9:16")
        d = b.to_dict()
        self.assertEqual(d["asset_id"], "@img")
        self.assertEqual(d["content_sha256"], "abc123")


if __name__ == "__main__":
    unittest.main()
