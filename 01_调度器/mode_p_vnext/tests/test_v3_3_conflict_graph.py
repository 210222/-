"""V3.3 Dedup & Conflict Graph — same-source dupes, near-dupes, conflicting claims."""

import unittest

try:
    from mode_p_vnext.schema.decision_card import DecisionCard
    from mode_p_vnext.schema.scene_diagnosis import SceneDiagnosis
    from mode_p_vnext import conflict_graph as cg
    from mode_p_vnext.diagnosis_artifact import build_phase_a_artifact
    from mode_p_vnext.knowledge_flow import (
        KnowledgeCandidate,
        KnowledgeCatalog,
        RetrievalContext,
        retrieve_for_diagnosis,
    )
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False

def _card(cid, claim, source_file="s1.md"):
    return DecisionCard(card_id=cid, claim=claim, source_quality="golden_evidence",
                        source_file=source_file)


class DedupTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "conflict_graph not yet implemented")
    def test_exact_duplicate_detected(self):
        cards = [_card("C1", "推镜保持注意力"), _card("C2", "推镜保持注意力")]
        dupes = cg.find_duplicates(cards)
        self.assertEqual(len(dupes), 1)

    @unittest.skipIf(not MODULE_EXISTS, "conflict_graph not yet implemented")
    def test_same_source_duplicate_detected(self):
        cards = [_card("C1", "claim A", "f1.md"), _card("C2", "claim B", "f1.md")]
        dupes = cg.find_same_source_duplicates(cards)
        self.assertGreater(len(dupes), 0)

    @unittest.skipIf(not MODULE_EXISTS, "conflict_graph not yet implemented")
    def test_distinct_claims_no_duplicate(self):
        cards = [_card("C1", "推镜好"), _card("C2", "切镜好")]
        dupes = cg.find_duplicates(cards)
        self.assertEqual(len(dupes), 0)


class ConflictGraphTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "conflict_graph not yet implemented")
    def test_conflicting_claims_detected(self):
        """Two cards that claim opposite things about the same topic."""
        cards = [
            _card("C1", "推镜比切镜更适合注意力保持"),
            _card("C2", "切镜比推镜更适合注意力变化"),
        ]
        graph = cg.build_conflict_graph(cards)
        self.assertGreater(len(graph.conflicts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "conflict_graph not yet implemented")
    def test_non_conflicting_claims(self):
        cards = [
            _card("C1", "推镜保持注意力"),
            _card("C2", "手机背面用实心不透明描述"),
        ]
        graph = cg.build_conflict_graph(cards)
        self.assertEqual(len(graph.conflicts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "conflict_graph not yet implemented")
    def test_conflict_graph_exposes_not_resolves(self):
        """Algorithm MUST expose conflicts, NOT pick a winner."""
        cards = [_card("C1", "A方法好"), _card("C2", "B方法好")]
        graph = cg.build_conflict_graph(cards)
        # If there's a conflict, it's reported — no auto-resolution
        for conflict in graph.conflicts:
            self.assertNotIn("winner", conflict)
            self.assertIn("card_ids", conflict)

    @unittest.skipIf(not MODULE_EXISTS, "knowledge flow not yet implemented")
    def test_runtime_conflict_is_exposed_not_ranked_to_winner(self):
        first = KnowledgeCandidate(
            card=_card("K1", "keep attention continuous", "one.md"),
            decision_domain="attention",
            director_question="Which attention trade-off needs Director judgement?",
            query_tags=("attention",), project_scope=("P1",),
            director_variables=("attention emphasis",), observable_failures=("ambiguous focus",),
            must_not_decide=("final execution",), contradicts=("K2",),
        )
        second = KnowledgeCandidate(
            card=_card("K2", "change attention deliberately", "two.md"),
            decision_domain="attention",
            director_question="Which attention trade-off needs Director judgement?",
            query_tags=("attention",), project_scope=("P1",),
            director_variables=("attention emphasis",), observable_failures=("ambiguous focus",),
            must_not_decide=("final execution",), contradicts=("K1",),
        )
        artifact = build_phase_a_artifact(
            "DA-CONFLICT", "P1", SceneDiagnosis("SC-CONFLICT", attention_path="attention conflict"),
            open_questions=["Which alternative should the Director choose?"],
        )
        result = retrieve_for_diagnosis(
            artifact,
            KnowledgeCatalog((first, second)),
            RetrievalContext(project_id="P1", as_of="2026-07-29"),
        )
        self.assertEqual(len(result.packet.conflict_exposures), 1)
        exposure = result.packet.conflict_exposures[0].to_dict()
        self.assertEqual(exposure["option_card_ids"], ["K1", "K2"])
        self.assertNotIn("winner", exposure)


if __name__ == "__main__":
    unittest.main()
