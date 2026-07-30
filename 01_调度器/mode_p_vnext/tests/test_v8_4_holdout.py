"""V8.4 Holdout Set."""

import unittest

try:
    from mode_p_vnext import holdout_set as hs
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class HoldoutSetTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "holdout_set not yet implemented")
    def test_holdout_has_entries(self):
        self.assertGreater(len(hs.HOLDOUT_SCENES), 0)

    @unittest.skipIf(not MODULE_EXISTS, "holdout_set not yet implemented")
    def test_holdout_no_overlap_with_golden(self):
        from mode_p_vnext.golden_registration import GOLDEN_CASES
        golden_ids = set(GOLDEN_CASES.keys())
        holdout_ids = set(hs.HOLDOUT_SCENES.keys())
        self.assertTrue(golden_ids.isdisjoint(holdout_ids))

    @unittest.skipIf(not MODULE_EXISTS, "holdout_set not yet implemented")
    def test_holdout_marked_not_for_template_design(self):
        for sid, entry in hs.HOLDOUT_SCENES.items():
            self.assertTrue(entry["holdout"],
                            f"{sid} must be marked holdout=True")


if __name__ == "__main__":
    unittest.main()
