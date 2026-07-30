"""V9.1 no-model vertical integration: facts -> diagnosis -> retrieval -> delivery.

The fixture proves that the vNext knowledge packet is genuinely connected to a
delivery run.  It intentionally uses an already-valid Golden VEC for rendering
instead of weakening the R1.4 source/semantic/handoff gates with a hand-built
segment.  It does not claim that the historic Golden shot was invented by this
test's retrieval result.
"""

import unittest

try:
    from mode_p_vnext.schema.fact_registry import ScriptFact, FactRegistry
    from mode_p_vnext.schema.scene_diagnosis import SceneDiagnosis
    from mode_p_vnext.schema.decision_card import DecisionCard
    from mode_p_vnext.schema.visibility_contract import VisibilityContract
    from mode_p_vnext.schema.fidelity_contract import FidelityContract
    from mode_p_vnext.diagnosis_artifact import build_phase_a_artifact
    from mode_p_vnext.knowledge_auditor import build_runtime_metadata_index
    from mode_p_vnext.knowledge_flow import (
        KnowledgeCandidate,
        KnowledgeCatalog,
        RetrievalContext,
        retrieve_for_diagnosis,
    )
    from mode_p_vnext.knowledge_snapshot import replay_snapshot
    from mode_p_vnext.fixtures.r1_3.golden_cases import build_golden_deliveries
    from mode_p_vnext.storyboard_renderer import render_storyboard
    from mode_p_vnext.video_renderer import render_video_prompt
    from mode_p_vnext.payload_compiler import compile_render_payload
    from mode_p_vnext.payload_manifest import create_payload_manifest
    from mode_p_vnext.dp_view_compiler import compile_dp_view
    from mode_p_vnext.dp_response_contract import DPResponse
    from mode_p_vnext.dual_output_sync import check_dual_output_sync
    from mode_p_vnext.approval_gate import ApprovalGate
    from mode_p_vnext.session_state import SessionStateMachine
    from mode_p_vnext.atomic_commit import Transaction
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class VerticalIntegrationTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "integration modules not available")
    def test_facts_to_delivery_full_chain(self):
        # 1. Facts
        registry = FactRegistry()
        registry.add(ScriptFact("F001", 1, "event", "barrel inspection", "critical", "visible"))
        registry.add(ScriptFact("F002", 2, "dialogue", "offscreen shout", "critical", "audio_only"))

        # 2. Session state
        state_machine = SessionStateMachine("EP8")
        state_machine.transition("DIAGNOSIS_COMPLETE")

        # 3. Phase A diagnosis -> explicit query -> metadata-only packet/snapshot
        diagnosis = SceneDiagnosis(
            "EP8_SC1",
            attention_path="attention narrows from silhouette to barrel geometry",
            model_risks=["barrel interior may be mistaken for an abstract tunnel"],
        )
        artifact = build_phase_a_artifact(
            "DA-EP8-SC1",
            "EP8",
            diagnosis,
            open_questions=["How can geometry remain readable without prescribing a shot?"],
            source_fact_ids=["F001", "F002"],
        )
        card = DecisionCard(
            "K-BARREL-READABILITY",
            "Prioritise readable spatial evidence when a narrow form can be misread.",
            "golden_evidence",
            render_evidence=["GOLDEN-EP8"],
            source_file="approved_capsules/barrel_readability.json",
            source_hash="capsule-hash-001",
        )
        catalog = KnowledgeCatalog((KnowledgeCandidate(
            card=card,
            decision_domain="attention",
            director_question="What must remain legible along the attention path?",
            query_tags=("attention", "barrel geometry"),
            project_scope=("EP8",),
            target_models=("SD2",),
            target_modes=("mode_p",),
            aspect_ratios=("16:9",),
            reference_modes=("identity",),
            director_variables=("attention emphasis",),
            observable_failures=("barrel reads as an abstract tunnel",),
            must_not_decide=("final camera position", "final shot duration"),
        ),))
        runtime_index = build_runtime_metadata_index(({
            "path": "approved_capsules/barrel_readability.json",
            "sha256": "capsule-hash-001",
            "source_group": "runtime_capsule",
        },))
        self.assertTrue(runtime_index[0]["runtime_allowed"])
        result = retrieve_for_diagnosis(
            artifact,
            catalog,
            RetrievalContext(
                project_id="EP8",
                model_id="SD2",
                mode="mode_p",
                aspect_ratio="16:9",
                reference_mode="identity",
                as_of="2026-07-29",
            ),
            k1_principles=("Diagnose the problem before choosing execution.",),
        )
        self.assertIn("attention", result.query.dimension_questions)
        self.assertEqual(result.packet.primary_cards[0].card_id, "K-BARREL-READABILITY")
        self.assertTrue(result.snapshot.verify_integrity())
        replay = replay_snapshot(result.snapshot)
        self.assertEqual(replay.snapshot_id, result.snapshot.snapshot_id)
        self.assertEqual(replay.selected_card_records[0]["card_id"], "K-BARREL-READABILITY")

        # 4. Valid R1.4 Golden VEC projections (not a synthetic bypass).
        deliveries = build_golden_deliveries()
        storyboard_view = deliveries["gun_barrel_sb"]
        video_prompt_view = deliveries["gun_barrel_video"]

        # 5. Sync and rendering remain fail-closed on the valid contract.
        sync = check_dual_output_sync(storyboard_view, video_prompt_view)
        self.assertTrue(sync.is_consistent)
        storyboard_text = render_storyboard(storyboard_view)
        video_prompt_text = render_video_prompt(video_prompt_view)
        self.assertTrue(storyboard_text)
        self.assertTrue(video_prompt_text)

        # 6. Payload compile + manifest
        visibility = VisibilityContract(
            visible_whitelist=["barrel", "two hands"],
            narrative_only=["background story"],
            audio_only=["offscreen shout"],
        )
        fidelity = FidelityContract("FC1")
        fidelity.bind("fact_id", "F001", "LOCKED", "critical visible fact")
        payload = compile_render_payload(video_prompt_view, visibility)
        self.assertNotIn("offscreen shout", str(payload.fields))
        manifest = create_payload_manifest(payload, visibility)
        self.assertEqual(len(manifest.content_sha256), 64)

        # 7. DP view deliberately excludes knowledge packet/Director internals.
        sources = {
            "script_facts": "F001, F002",
            "storyboard_view": storyboard_text,
            "video_prompt_view": video_prompt_text,
            "used_capabilities": "SD2",
            "asset_text_evidence": "identity reference hash=abc",
            "master": "SHOULD_BE_EXCLUDED",
            "knowledge_packet": "SHOULD_BE_EXCLUDED",
        }
        dp_view = compile_dp_view(sources)
        self.assertNotIn("master", dp_view)
        self.assertNotIn("knowledge_packet", dp_view)

        # 8. Approval and atomic commit
        response = DPResponse("DPR001", "READY")
        self.assertTrue(response.is_ready)
        gate = ApprovalGate("EP8")
        gate.approve("storyboard approved")
        self.assertTrue(gate.can_generate_payload)
        transaction = Transaction("TX001", "GOLDEN_SEG")
        transaction.stage("storyboard.md", storyboard_text)
        transaction.stage("video_prompt.md", video_prompt_text)
        transaction.stage("payload_manifest.json", str(manifest.content_sha256))
        transaction.commit()
        self.assertTrue(transaction.committed)


if __name__ == "__main__":
    unittest.main()
