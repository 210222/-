"""V1.5 Fact Coverage Checker — critical fact mapping enforcement.

Verify:
- Every critical fact must have an explicit render policy binding
- No silent drops — every fact in the registry must be accounted for
- Audio-only and narrative-only facts are explicitly declared
- User-approved omissions are recorded
"""

import unittest


try:
    from mode_p_vnext.schema.fact_registry import (
        ScriptFact, FactRegistry, validate_registry,
    )
    from mode_p_vnext import fact_coverage as fc
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


def _make_fact(fid, criticality="critical", visibility="visible"):
    return ScriptFact(fid, 1, "event", f"fact {fid}", criticality, visibility)


# ---------------------------------------------------------------------------
# FactBinding
# ---------------------------------------------------------------------------

class FactBindingTests(unittest.TestCase):
    """FactBinding dataclass — maps fact_id to render policy."""

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_binding_has_required_fields(self):
        b = fc.FactBinding(
            fact_id="F001",
            render_policy="visible",
            segment_id="S1",
        )
        self.assertEqual(b.fact_id, "F001")
        self.assertEqual(b.render_policy, "visible")
        self.assertIsNone(b.user_approval_omission)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_binding_with_user_omission(self):
        b = fc.FactBinding(
            fact_id="F002",
            render_policy="narrative_only",
            segment_id="S1",
            user_approval_omission="故事板阶段用户确认省略",
        )
        self.assertIsNotNone(b.user_approval_omission)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_render_policy_must_be_valid(self):
        with self.assertRaises(ValueError):
            fc.FactBinding("F1", "imaginary_policy", "S1")


# ---------------------------------------------------------------------------
# Coverage check
# ---------------------------------------------------------------------------

class CoverageCheckTests(unittest.TestCase):
    """Every critical fact must have a binding."""

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_all_critical_facts_covered(self):
        reg = FactRegistry()
        reg.add(_make_fact("F1", "critical"))
        reg.add(_make_fact("F2", "critical"))
        bindings = [
            fc.FactBinding("F1", "visible", "S1"),
            fc.FactBinding("F2", "visible", "S1"),
        ]
        result = fc.check_fact_coverage(reg, bindings)
        self.assertTrue(result.is_covered)
        self.assertEqual(len(result.missing_facts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_missing_critical_fact_detected(self):
        reg = FactRegistry()
        reg.add(_make_fact("F1", "critical"))
        reg.add(_make_fact("F2", "critical"))
        bindings = [
            fc.FactBinding("F1", "visible", "S1"),
            # F2 is missing — silent drop
        ]
        result = fc.check_fact_coverage(reg, bindings)
        self.assertFalse(result.is_covered)
        self.assertIn("F2", result.missing_facts)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_contextual_facts_not_required(self):
        """Contextual facts can be omitted without violation."""
        reg = FactRegistry()
        reg.add(_make_fact("F1", "critical"))
        reg.add(_make_fact("F2", "contextual"))
        bindings = [
            fc.FactBinding("F1", "visible", "S1"),
            # F2 contextual — not required
        ]
        result = fc.check_fact_coverage(reg, bindings)
        self.assertTrue(result.is_covered)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_all_facts_drop_check(self):
        """check_silent_drops reports any registry fact without a binding."""
        reg = FactRegistry()
        reg.add(_make_fact("F1", "critical"))
        reg.add(_make_fact("F2", "contextual"))
        bindings = [fc.FactBinding("F1", "visible", "S1")]
        drops = fc.check_silent_drops(reg, bindings)
        self.assertEqual(len(drops.unbound_facts), 1)
        self.assertIn("F2", drops.unbound_facts)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_empty_registry_passes(self):
        reg = FactRegistry()
        result = fc.check_fact_coverage(reg, [])
        self.assertTrue(result.is_covered)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_duplicate_binding_detected(self):
        reg = FactRegistry()
        reg.add(_make_fact("F1", "critical"))
        bindings = [
            fc.FactBinding("F1", "visible", "S1"),
            fc.FactBinding("F1", "visible", "S2"),  # same fact bound twice
        ]
        result = fc.check_fact_coverage(reg, bindings)
        self.assertFalse(result.is_covered)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_binding_for_nonexistent_fact(self):
        """Binding references a fact_id not in the registry."""
        reg = FactRegistry()
        reg.add(_make_fact("F1", "critical"))
        bindings = [
            fc.FactBinding("F1", "visible", "S1"),
            fc.FactBinding("GHOST", "visible", "S1"),  # phantom
        ]
        result = fc.check_fact_coverage(reg, bindings)
        self.assertFalse(result.is_covered)

    @unittest.skipIf(not MODULE_EXISTS, "fact_coverage not yet implemented")
    def test_coverage_result_includes_warnings(self):
        reg = FactRegistry()
        reg.add(_make_fact("F1", "critical"))
        reg.add(_make_fact("F2", "contextual"))
        bindings = [fc.FactBinding("F1", "visible", "S1")]
        result = fc.check_fact_coverage(reg, bindings)
        self.assertGreater(len(result.warnings), 0)


if __name__ == "__main__":
    unittest.main()
