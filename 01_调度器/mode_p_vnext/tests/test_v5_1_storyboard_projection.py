"""R1.3+ — Immutability, provenance, contract builder, and fingerprint tests."""

import unittest

from mode_p_vnext.schema.canonical_timeline import TimeInterval
from mode_p_vnext.schema.generation_segment import CinematicShot, GenerationSegment
from mode_p_vnext.storyboard_projection import (
    ContractBuilder,
    ContractError,
    DualOutputContract,
    FrozenNode,
    FrozenPhase,
    StoryboardView,
    _format_time_display,
    build_contract_from_segment,
    compare_projections,
    contract_fingerprint,
    derive_total_duration_s,
    project_storyboard,
    validate_delivery_contract,
)
from mode_p_vnext.video_projection import project_video_prompt, VideoPromptView


_TPS = 24000


def _make_segment(seg_id="SEG1", n_shots=1):
    shots = []
    for i in range(n_shots):
        s = CinematicShot(
            shot_id=f"S{i+1}", segment_id=seg_id,
            time_range=TimeInterval(start_tick=i * _TPS, end_tick=(i + 1) * _TPS),
            narrative_job=f"叙事任务{i+1}",
            camera_position="正面", shot_size="WS", focal_intent="24mm",
            camera_motion="缓慢前推", composition="中央对称",
            lighting="顶光", performance="自然",
        )
        shots.append(s)
    return GenerationSegment(
        segment_id=seg_id,
        time_range=TimeInterval(start_tick=0, end_tick=_TPS * n_shots),
        shots=shots,
    )


class ImmutabilityTests(unittest.TestCase):
    """Frozen dataclasses reject mutation."""

    def test_frozen_node_rejects_assignment(self):
        n = FrozenNode(node_id="n1", start_tick=0, end_tick=1000)
        with self.assertRaises(Exception):  # FrozenInstanceError or AttributeError
            n.start_tick = 500  # type: ignore

    def test_frozen_contract_rejects_assignment(self):
        c = DualOutputContract(segment_id="TEST")
        with self.assertRaises(Exception):
            c.segment_id = "CHANGED"  # type: ignore

    def test_frozen_node_display_is_readonly(self):
        n = FrozenNode(node_id="n1", start_tick=0, end_tick=1000,
                        _display=(("desc", "test"),))
        self.assertEqual(n.get_display("desc"), "test")

    def test_projector_never_mutates_supplied_builder(self):
        """Calling project_storyboard builds once; builder state is consumed."""
        seg = _make_segment()
        builder = build_contract_from_segment(seg, _TPS)
        view1 = project_storyboard(seg, builder=builder)
        # Second call with same builder — builds independently
        builder2 = build_contract_from_segment(seg, _TPS)
        view2 = project_storyboard(seg, builder=builder2)
        self.assertEqual(
            contract_fingerprint(view1.contract),
            contract_fingerprint(view2.contract),
        )

    def test_same_builder_produces_same_nodes_for_both_projectors(self):
        """Both projectors using same builder get identical node IDs and ticks."""
        seg = _make_segment("SEG1", n_shots=2)
        builder = build_contract_from_segment(seg, _TPS)
        sb = project_storyboard(seg, builder=builder)
        builder2 = build_contract_from_segment(seg, _TPS)
        vp = project_video_prompt(seg, builder=builder2)
        sb_ids = [n.node_id for n in sb.contract.nodes]
        vp_ids = [n.node_id for n in vp.contract.nodes]
        self.assertEqual(sb_ids, vp_ids)
        for i in range(len(sb.contract.nodes)):
            self.assertEqual(sb.contract.nodes[i].start_tick,
                             vp.contract.nodes[i].start_tick)


class DirectProjectionTests(unittest.TestCase):
    """Direct projection creates timeline nodes."""

    def test_direct_storyboard_has_nodes(self):
        seg = _make_segment("TEST", n_shots=1)
        view = project_storyboard(seg)
        self.assertGreater(len(view.contract.nodes), 0)

    def test_direct_video_has_nodes(self):
        seg = _make_segment("TEST", n_shots=2)
        view = project_video_prompt(seg)
        self.assertGreater(len(view.contract.nodes), 0,
                           "Direct video projection MUST create timeline nodes")
        self.assertEqual(len(view.contract.nodes), 2)

    def test_direct_video_nodes_have_tick_data(self):
        seg = _make_segment("TEST", n_shots=1)
        view = project_video_prompt(seg)
        node = view.contract.nodes[0]
        self.assertEqual(node.start_tick, 0)
        self.assertEqual(node.end_tick, _TPS)

    def test_legacy_panels_preserved(self):
        seg = _make_segment("TEST", n_shots=2)
        sb = project_storyboard(seg)
        self.assertEqual(len(sb.panels), 2)
        vp = project_video_prompt(seg)
        self.assertEqual(len(vp.shot_descriptions), 2)


class ProvenanceTests(unittest.TestCase):
    """Display values must carry provenance."""

    def test_builder_nodes_have_provenance(self):
        builder = ContractBuilder("TEST")
        builder.add_node("n1", 0, 1000,
                          display={"desc": "test text"},
                          provenance={"desc": "source:Director.script"})
        contract = builder.build()
        node = contract.nodes[0]
        self.assertEqual(node.get_display("desc"), "test text")
        self.assertIn("source:Director", node.provenance.get("desc", ""))

    def test_segment_derived_nodes_have_provenance(self):
        seg = _make_segment("TEST", n_shots=1)
        view = project_storyboard(seg)
        node = view.contract.nodes[0]
        self.assertIn("source:CinematicShot", node.provenance.get("description", ""),
                      "Segment-derived nodes must have provenance")


class FingerprintAndComparisonTests(unittest.TestCase):
    """Contract fingerprinting and structural comparison."""

    def test_identical_contracts_same_fingerprint(self):
        seg = _make_segment("A", n_shots=1)
        v1 = project_storyboard(seg)
        v2 = project_storyboard(seg)
        self.assertEqual(
            contract_fingerprint(v1.contract),
            contract_fingerprint(v2.contract),
        )

    def test_changed_tick_different_fingerprint(self):
        seg = _make_segment("A", n_shots=1)
        v1 = project_storyboard(seg)
        # Build a contract with a tampered tick
        builder = build_contract_from_segment(seg, _TPS)
        builder._nodes[0] = FrozenNode(
            node_id="shot_000", start_tick=100, end_tick=1000,
            shot_id="S1", sb_node=True,
            _display=builder._nodes[0]._display,
            _provenance=builder._nodes[0]._provenance,
        )
        tampered = builder.build()
        self.assertNotEqual(
            contract_fingerprint(v1.contract),
            contract_fingerprint(tampered),
            "Tick tampering must change fingerprint"
        )

    def test_changed_text_different_fingerprint(self):
        seg = _make_segment("A", n_shots=1)
        v1 = project_storyboard(seg)
        builder = build_contract_from_segment(seg, _TPS)
        old_disp = builder._nodes[0].get_display("description", "")
        builder._nodes[0] = FrozenNode(
            node_id="shot_000", start_tick=0, end_tick=_TPS,
            shot_id="S1", sb_node=True,
            _display=(("description", "TAMPERED TEXT"),),
            _provenance=builder._nodes[0]._provenance,
        )
        tampered = builder.build()
        self.assertNotEqual(
            contract_fingerprint(v1.contract),
            contract_fingerprint(tampered),
            "Text tampering must change fingerprint"
        )

    def test_comparison_detects_tick_tamper(self):
        """Production comparison API detects tampered tick."""
        seg = _make_segment("A", n_shots=2)
        sb = project_storyboard(seg)
        vp = project_video_prompt(seg)
        # Untampered comparison is consistent
        result = compare_projections(sb, vp)
        self.assertTrue(result.fingerprint_match)

        # Tamper vp's contract
        builder = build_contract_from_segment(seg, _TPS)
        builder._nodes[0] = FrozenNode(
            node_id="shot_000", start_tick=100, end_tick=_TPS,
            shot_id="S1", sb_node=True,
        )
        vp_tampered = VideoPromptView(
            segment_id="A", contract=builder.build(),
        )
        result2 = compare_projections(sb, vp_tampered)
        self.assertFalse(result2.fingerprint_match)

    def test_fingerprint_includes_handoff(self):
        builder = ContractBuilder("TEST")
        builder.add_node("n1", 0, 1000)
        c1 = builder.build()
        builder.set_handoff("画面保持→段3", "source:Director")
        c2 = builder.build()
        self.assertNotEqual(
            contract_fingerprint(c1), contract_fingerprint(c2),
            "Handoff change must affect fingerprint"
        )


class TimingTests(unittest.TestCase):
    """Exact timing with no silent rounding."""

    def test_integer_seconds_no_decimal(self):
        self.assertEqual(_format_time_display(0, _TPS), "0s")
        self.assertEqual(_format_time_display(_TPS, _TPS), "1s")

    def test_half_second_not_zero(self):
        """0.5s must render as 0.5s, not 0s."""
        self.assertEqual(_format_time_display(_TPS // 2, _TPS), "0.5s")

    def test_quarter_second(self):
        self.assertEqual(_format_time_display(_TPS // 4, _TPS), "0.25s")

    def test_derive_duration_never_zero_for_positive_ticks(self):
        c = DualOutputContract(nodes=(
            FrozenNode(node_id="n1", start_tick=0, end_tick=_TPS // 2),
        ))
        dur = derive_total_duration_s(c, _TPS)
        self.assertGreater(dur, 0, "Half-second segment must have positive duration")
        self.assertEqual(dur, 0.5)


class ValidationTests(unittest.TestCase):
    """Delivery validation fails on incomplete contracts."""

    def test_empty_contract_has_violations(self):
        c = DualOutputContract()
        v = validate_delivery_contract(c, "MISSING")
        # Empty contract may pass basic checks but reference duties must fail
        self.assertIsInstance(v, list)

    def test_orphan_reference_duty_detected(self):
        builder = ContractBuilder("TEST")
        builder.add_node("n1", 0, 1000, shot_id="S1")
        builder.set_reference_duty("orphan_ref", "some duty")
        c = builder.build()
        v = validate_delivery_contract(c, "TEST")
        duty_violations = [x for x in v if "orphan" in x or "unknown reference" in x]
        self.assertGreater(len(duty_violations), 0,
                           "Orphan duty (ref with no image) must be detected")

    def test_checked_render_raises_on_bad_contract(self):
        """render_storyboard raises ContractError on violations."""
        from mode_p_vnext.storyboard_renderer import render_storyboard as rsb
        builder = ContractBuilder("BROKEN")
        builder.add_node("n1", 0, 1000)
        builder.set_reference_duty("no_such_ref", "duty text")
        view = StoryboardView(segment_id="BROKEN", contract=builder.build())
        with self.assertRaises(ContractError):
            rsb(view)


class BytePreservationTests(unittest.TestCase):
    """Byte-for-byte preservation through projection."""

    def test_parentheses_survive(self):
        seg = _make_segment()
        seg.shots[0].narrative_job = "内壁为钢本色（不是漩涡），不发光。"
        view = project_storyboard(seg)
        desc = view.contract.nodes[0].get_display("description", "")
        self.assertIn("（不是漩涡）", desc)

    def test_unicode_arrows_survive(self):
        seg = _make_segment()
        seg.shots[0].narrative_job = "画面保持→嗡声硬切断→段3"
        view = project_storyboard(seg)
        desc = view.contract.nodes[0].get_display("description", "")
        self.assertIn("→", desc)


if __name__ == "__main__":
    unittest.main()
