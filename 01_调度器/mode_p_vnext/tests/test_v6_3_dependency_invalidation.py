"""V6.3 Dependency Invalidation."""

import unittest

try:
    from mode_p_vnext import dependency_invalidation as di
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DependencyInvalidationTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "dependency_invalidation not yet implemented")
    def test_fact_change_invalidates_master(self):
        deps = di.DependencyGraph()
        deps.add("F001", "fact")
        deps.add("MASTER_EP8", "master", depends_on=["F001"])
        deps.add("SB_EP8", "storyboard", depends_on=["MASTER_EP8"])
        invalidated = deps.invalidate("F001")
        self.assertIn("MASTER_EP8", invalidated)
        self.assertIn("SB_EP8", invalidated)

    @unittest.skipIf(not MODULE_EXISTS, "dependency_invalidation not yet implemented")
    def test_capability_change_invalidates_payload(self):
        deps = di.DependencyGraph()
        deps.add("CAP_v2", "capability")
        deps.add("PAYLOAD_EP8", "payload", depends_on=["CAP_v2"])
        invalidated = deps.invalidate("CAP_v2")
        self.assertIn("PAYLOAD_EP8", invalidated)

    @unittest.skipIf(not MODULE_EXISTS, "dependency_invalidation not yet implemented")
    def test_unrelated_change_no_effect(self):
        deps = di.DependencyGraph()
        deps.add("F001", "fact")
        deps.add("MASTER_EP8", "master", depends_on=["F001"])
        deps.add("F002", "fact")
        invalidated = deps.invalidate("F002")  # master doesn't depend on F002
        self.assertNotIn("MASTER_EP8", invalidated)


if __name__ == "__main__":
    unittest.main()
