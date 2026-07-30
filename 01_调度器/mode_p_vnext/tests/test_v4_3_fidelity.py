"""V4.3 Fidelity Contract — LOCKED/ELASTIC/OPTIMIZABLE/FORBIDDEN."""

import unittest

try:
    from mode_p_vnext.schema import fidelity_contract as fc
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class FidelityContractTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "fidelity_contract not yet implemented")
    def test_contract_binds_items(self):
        c = fc.FidelityContract(contract_id="FC1")
        c.bind("fact_id", "F001", "LOCKED", "关键行为事实")
        c.bind("user_constraint", "UC1", "LOCKED", "用户批准项")
        c.bind("composition", "COMP1", "ELASTIC", "")
        self.assertEqual(c.get_level("F001"), "LOCKED")

    @unittest.skipIf(not MODULE_EXISTS, "fidelity_contract not yet implemented")
    def test_downgrade_locked_to_elastic_blocked(self):
        c = fc.FidelityContract("FC1")
        c.bind("fact_id", "F001", "LOCKED", "关键事实")
        with self.assertRaises(ValueError):
            c.bind("fact_id", "F001", "ELASTIC", "试图降级")

    @unittest.skipIf(not MODULE_EXISTS, "fidelity_contract not yet implemented")
    def test_upgrade_allowed(self):
        c = fc.FidelityContract("FC1")
        c.bind("fact_id", "F001", "ELASTIC", "")
        c.bind("fact_id", "F001", "LOCKED", "升级")  # upgrade OK

    @unittest.skipIf(not MODULE_EXISTS, "fidelity_contract not yet implemented")
    def test_invalid_level_rejected(self):
        c = fc.FidelityContract("FC1")
        with self.assertRaises(ValueError):
            c.bind("x", "F1", "IMAGINARY", "")

    @unittest.skipIf(not MODULE_EXISTS, "fidelity_contract not yet implemented")
    def test_user_approved_items_cannot_be_downgraded(self):
        c = fc.FidelityContract("FC1")
        c.bind("user_constraint", "UC1", "LOCKED", "用户批准")
        violations = fc.check_user_approved_downgrades(c)
        self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
