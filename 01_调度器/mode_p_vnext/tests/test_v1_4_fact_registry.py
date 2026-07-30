"""V1.4 Fact Registry Schema — structured narrative facts.

Verify:
- ScriptFact dataclass with stable fact_id, source line, type, criticality
- Visibility classification: visible/audio_only/narrative_only/not_in_segment
- Uncertain flag for unresolved facts
- Program validates structure only; does not author facts
- Canonical JSON serialization support
"""

import unittest


try:
    from mode_p_vnext.schema import fact_registry as fr
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


# ---------------------------------------------------------------------------
# ScriptFact schema
# ---------------------------------------------------------------------------

class ScriptFactSchemaTests(unittest.TestCase):
    """ScriptFact dataclass structure."""

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_fact_has_required_fields(self):
        f = fr.ScriptFact(
            fact_id="F001",
            source_line=42,
            fact_type="dialogue",
            summary="Pedro说：'球跑了'",
            criticality="critical",
            visibility="visible",
        )
        self.assertEqual(f.fact_id, "F001")
        self.assertEqual(f.source_line, 42)
        self.assertEqual(f.fact_type, "dialogue")
        self.assertEqual(f.criticality, "critical")
        self.assertEqual(f.visibility, "visible")
        self.assertFalse(f.uncertain)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_fact_id_must_be_nonempty(self):
        with self.assertRaises(ValueError):
            fr.ScriptFact(
                fact_id="", source_line=1, fact_type="event",
                summary="test", criticality="critical", visibility="visible",
            )

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_fact_type_must_be_valid(self):
        with self.assertRaises(ValueError):
            fr.ScriptFact(
                fact_id="F1", source_line=1, fact_type="invalid_type",
                summary="test", criticality="critical", visibility="visible",
            )

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_valid_fact_types_accepted(self):
        for ft in fr.FACT_TYPES:
            f = fr.ScriptFact(
                fact_id="F1", source_line=1, fact_type=ft,
                summary="test", criticality="critical", visibility="visible",
            )
            self.assertEqual(f.fact_type, ft)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_criticality_must_be_valid(self):
        with self.assertRaises(ValueError):
            fr.ScriptFact(
                fact_id="F1", source_line=1, fact_type="event",
                summary="test", criticality="urgent", visibility="visible",
            )

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_visibility_must_be_valid(self):
        with self.assertRaises(ValueError):
            fr.ScriptFact(
                fact_id="F1", source_line=1, fact_type="event",
                summary="test", criticality="critical", visibility="invisible",
            )

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_uncertain_flag_default(self):
        f = fr.ScriptFact(
            fact_id="F2", source_line=10, fact_type="event",
            summary="可能听到了声音", criticality="contextual",
            visibility="audio_only", uncertain=True,
        )
        self.assertTrue(f.uncertain)
        self.assertEqual(f.visibility, "audio_only")

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_fact_equals_by_id_only(self):
        """Two facts with same fact_id are equal regardless of other fields."""
        a = fr.ScriptFact("F1", 1, "event", "summary A", "critical", "visible")
        b = fr.ScriptFact("F1", 2, "dialogue", "summary B", "contextual", "narrative_only")
        self.assertEqual(a, b)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_fact_hash_by_id(self):
        a = fr.ScriptFact("F1", 1, "event", "x", "critical", "visible")
        b = fr.ScriptFact("F1", 99, "dialogue", "y", "contextual", "audio_only")
        self.assertEqual(hash(a), hash(b))
        # Can be used in a set
        s = {a, b}
        self.assertEqual(len(s), 1)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_fact_to_dict(self):
        f = fr.ScriptFact("F1", 5, "event", "描述",
                           "critical", "visible", uncertain=True)
        d = f.to_dict()
        self.assertEqual(d["fact_id"], "F1")
        self.assertEqual(d["source_line"], 5)
        self.assertTrue(d["uncertain"])


# ---------------------------------------------------------------------------
# Fact visibility classification
# ---------------------------------------------------------------------------

class FactVisibilityTests(unittest.TestCase):
    """Correct visibility classifications."""

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_visible_fact(self):
        f = fr.ScriptFact("F1", 1, "prop", "枪在桌上",
                           "critical", "visible")
        self.assertEqual(f.visibility, "visible")

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_audio_only_fact(self):
        f = fr.ScriptFact("F1", 1, "dialogue", "画外喊声",
                           "critical", "audio_only")
        self.assertEqual(f.visibility, "audio_only")

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_narrative_only_fact(self):
        f = fr.ScriptFact("F1", 1, "event", "他三年前杀了人",
                           "contextual", "narrative_only")
        self.assertEqual(f.visibility, "narrative_only")

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_not_in_segment_fact(self):
        f = fr.ScriptFact("F1", 1, "continuity", "前场留下的伤",
                           "important", "not_in_segment")
        self.assertEqual(f.visibility, "not_in_segment")

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_locked_execution_fact(self):
        f = fr.ScriptFact("F1", 1, "event", "开枪",
                           "critical", "locked_execution")
        self.assertEqual(f.visibility, "locked_execution")


# ---------------------------------------------------------------------------
# FactRegistry container
# ---------------------------------------------------------------------------

class FactRegistryTests(unittest.TestCase):
    """FactRegistry container — validate structure, don't author facts."""

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_registry_add_and_lookup(self):
        reg = fr.FactRegistry()
        f = fr.ScriptFact("F001", 42, "dialogue", "你好",
                           "critical", "visible")
        reg.add(f)
        self.assertEqual(reg.get("F001"), f)
        self.assertIsNone(reg.get("NONEXISTENT"))

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_registry_duplicate_id_rejected(self):
        reg = fr.FactRegistry()
        f1 = fr.ScriptFact("F001", 1, "event", "a", "critical", "visible")
        f2 = fr.ScriptFact("F001", 2, "dialogue", "b", "critical", "visible")
        reg.add(f1)
        with self.assertRaises(ValueError):
            reg.add(f2)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_registry_len_and_iter(self):
        reg = fr.FactRegistry()
        reg.add(fr.ScriptFact("F1", 1, "event", "a", "critical", "visible"))
        reg.add(fr.ScriptFact("F2", 2, "event", "b", "critical", "visible"))
        self.assertEqual(len(reg), 2)
        self.assertEqual(len(list(reg)), 2)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_registry_critical_facts_only(self):
        reg = fr.FactRegistry()
        reg.add(fr.ScriptFact("F1", 1, "event", "关键", "critical", "visible"))
        reg.add(fr.ScriptFact("F2", 2, "event", "次要", "contextual", "visible"))
        critical = list(reg.critical_facts())
        self.assertEqual(len(critical), 1)
        self.assertEqual(critical[0].fact_id, "F1")

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_registry_uncertain_facts(self):
        reg = fr.FactRegistry()
        reg.add(fr.ScriptFact("F1", 1, "event", "确定", "critical", "visible"))
        reg.add(fr.ScriptFact("F2", 2, "event", "可能",
                               "contextual", "visible", uncertain=True))
        uncertain = list(reg.uncertain_facts())
        self.assertEqual(len(uncertain), 1)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_registry_to_dict(self):
        reg = fr.FactRegistry()
        reg.add(fr.ScriptFact("F1", 1, "event", "测试", "critical", "visible"))
        d = reg.to_dict()
        self.assertIn("facts", d)
        self.assertEqual(len(d["facts"]), 1)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_registry_empty_is_valid(self):
        reg = fr.FactRegistry()
        violations = fr.validate_registry(reg)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_validate_registry_detects_duplicate_lines(self):
        """Two facts from the same source_line should be flagged as review item."""
        reg = fr.FactRegistry()
        reg.add(fr.ScriptFact("F1", 10, "event", "a", "critical", "visible"))
        reg.add(fr.ScriptFact("F2", 10, "dialogue", "b", "critical", "visible"))
        violations = fr.validate_registry(reg)
        self.assertGreater(len(violations), 0)


# ---------------------------------------------------------------------------
# Canonical serialization
# ---------------------------------------------------------------------------

class FactCanonicalTests(unittest.TestCase):
    """Fact registry can be serialized to canonical JSON."""

    @unittest.skipIf(not MODULE_EXISTS, "fact_registry not yet implemented")
    def test_canonical_json_stable(self):
        from mode_p_vnext.canonical_serialization import (
            canonical_json_dumps, stable_hash_sha256,
        )
        reg = fr.FactRegistry()
        reg.add(fr.ScriptFact("F1", 1, "event", "测试事实",
                               "critical", "visible"))
        j1 = canonical_json_dumps(reg.to_dict())
        j2 = canonical_json_dumps(reg.to_dict())
        self.assertEqual(j1, j2)
        self.assertEqual(
            stable_hash_sha256(j1.encode("utf-8")),
            stable_hash_sha256(j2.encode("utf-8")),
        )


if __name__ == "__main__":
    unittest.main()
