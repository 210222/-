"""V2.5 Aspect Reframe Contract — 16:9→9:16 protected relationships."""

import unittest

try:
    from mode_p_vnext.schema import aspect_reframe as ar
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class AspectReframeTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "aspect_reframe not yet implemented")
    def test_contract_fields(self):
        c = ar.AspectReframeContract(
            source_aspect="16:9",
            target_aspect="9:16",
            protected_relationships=["人物左右关系", "视线方向"],
            allowed_reframe=["垂直裁切", "上下扩展"],
            forbidden=["水平镜像", "180°旋转"],
        )
        self.assertEqual(c.source_aspect, "16:9")
        self.assertIn("水平镜像", c.forbidden)

    @unittest.skipIf(not MODULE_EXISTS, "aspect_reframe not yet implemented")
    def test_same_aspect_no_reframe_needed(self):
        c = ar.AspectReframeContract(
            source_aspect="16:9", target_aspect="16:9",
            protected_relationships=["主体关系"],
        )
        self.assertTrue(c.is_identity)

    @unittest.skipIf(not MODULE_EXISTS, "aspect_reframe not yet implemented")
    def test_different_aspect_needs_reframe(self):
        c = ar.AspectReframeContract(
            source_aspect="16:9", target_aspect="9:16",
            protected_relationships=["主体关系"],
        )
        self.assertFalse(c.is_identity)

    @unittest.skipIf(not MODULE_EXISTS, "aspect_reframe not yet implemented")
    def test_mirror_forbidden_by_default(self):
        c = ar.AspectReframeContract(
            source_aspect="16:9", target_aspect="9:16",
            protected_relationships=["x"],
        )
        violations = ar.validate_reframe(c)
        self.assertTrue(any("镜像" in v or "mirror" in v.lower() for v in violations))

    @unittest.skipIf(not MODULE_EXISTS, "aspect_reframe not yet implemented")
    def test_protected_relationships_not_empty(self):
        c = ar.AspectReframeContract(
            source_aspect="16:9", target_aspect="9:16",
            protected_relationships=[],
        )
        violations = ar.validate_reframe(c)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "aspect_reframe not yet implemented")
    def test_mirror_explicitly_allowed_suppresses_warning(self):
        c = ar.AspectReframeContract(
            source_aspect="16:9", target_aspect="9:16",
            protected_relationships=["主体"],
            allowed_reframe=["水平镜像"],  # explicit exception
        )
        violations = ar.validate_reframe(c)
        self.assertFalse(any("镜像" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
