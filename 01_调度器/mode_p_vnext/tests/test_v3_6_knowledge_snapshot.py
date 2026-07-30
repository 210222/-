"""V3.6 Knowledge Snapshot & Replayable Evidence."""

import unittest

try:
    from mode_p_vnext.schema.decision_card import DecisionCard
    from mode_p_vnext import knowledge_snapshot as ks
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class KnowledgeSnapshotTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "knowledge_snapshot not yet implemented")
    def test_snapshot_records_selected_cards(self):
        cards = [DecisionCard("C1", "claim", "golden_evidence")]
        snap = ks.KnowledgeSnapshot(
            snapshot_id="KS001",
            selected_card_ids=["C1"],
            conflict_ids=[],
            not_selected={"C2": "below quality threshold"},
            budget_used=1,
            budget_total=3,
        )
        self.assertEqual(snap.selected_card_ids, ["C1"])
        self.assertIn("C2", snap.not_selected)

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_snapshot not yet implemented")
    def test_snapshot_has_content_hash(self):
        cards = [DecisionCard("C1", "测试", "golden_evidence")]
        snap = ks.create_snapshot(
            snapshot_id="KS1",
            selected_cards=cards,
            not_selected={},
            budget_total=3,
        )
        self.assertTrue(len(snap.content_sha256) > 0)
        self.assertEqual(len(snap.content_sha256), 64)

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_snapshot not yet implemented")
    def test_snapshot_does_not_claim_reproducible(self):
        """Snapshot records what was selected, NOT that model output is reproducible."""
        snap = ks.create_snapshot("KS1", [], {}, 5)
        d = snap.to_dict()
        self.assertNotIn("output_reproducible", d)
        self.assertNotIn("model_output_hash", d)

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_snapshot not yet implemented")
    def test_conflicts_recorded(self):
        snap = ks.KnowledgeSnapshot(
            snapshot_id="KS2",
            selected_card_ids=[],
            conflict_ids=["conflict_001"],
            not_selected={},
            budget_used=0,
            budget_total=5,
        )
        self.assertIn("conflict_001", snap.conflict_ids)

    @unittest.skipIf(not MODULE_EXISTS, "knowledge_snapshot not yet implemented")
    def test_retrieval_snapshot_records_query_and_detects_mutation(self):
        selected = [DecisionCard("C1", "claim", "golden_evidence", source_hash="h1")]
        snapshot = ks.create_retrieval_snapshot(
            snapshot_id="KS-V2",
            query={"scene_id": "S1", "dimension_questions": {"attention": ["focus"]}},
            selected_cards=selected,
            candidate_cards=selected,
            exclusions={"C2": "expired"},
            conflicts=[{"conflict_id": "KCON-1", "option_card_ids": ["C1", "C2"]}],
            index_sha256="index-hash",
            retriever_version="retriever-1",
            ranking_version="ranking-1",
            stage_budgets={"primary_limit": 3, "primary_used": 1},
            selection_reasons={"C1": "matched_explicit_diagnosis_question"},
        )
        self.assertTrue(snapshot.verify_integrity())
        self.assertTrue(snapshot.query_sha256)
        replay = ks.replay_snapshot(snapshot)
        self.assertEqual(replay.selected_card_records[0]["card_id"], "C1")
        snapshot.selected_card_ids.append("tampered")
        self.assertFalse(snapshot.verify_integrity())
        with self.assertRaises(ValueError):
            ks.replay_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
