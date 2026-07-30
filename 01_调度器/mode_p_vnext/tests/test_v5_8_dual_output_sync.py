"""R1.3+ — Dual output sync: production fingerprint, comparison, contract-aware tamper detection."""

import unittest

from mode_p_vnext.schema.canonical_timeline import TimeInterval
from mode_p_vnext.schema.generation_segment import CinematicShot, GenerationSegment
from mode_p_vnext.storyboard_projection import (
    ContractBuilder,
    FrozenNode,
    build_contract_from_segment,
    compare_projections,
    contract_fingerprint,
    project_storyboard,
)
from mode_p_vnext.video_projection import project_video_prompt, VideoPromptView
from mode_p_vnext import dual_output_sync as dos


_TPS = 24000


def _make_segment(n_shots=2):
    shots = []
    for i in range(n_shots):
        s = CinematicShot(
            shot_id=f"S{i+1}", segment_id="SEG1",
            time_range=TimeInterval(start_tick=i * _TPS, end_tick=(i + 1) * _TPS),
            narrative_job=f"job{i+1}", camera_position=f"cam{i+1}",
            shot_size="WS", focal_intent="24mm",
            camera_motion=f"m{i+1}", composition=f"co{i+1}",
            lighting=f"l{i+1}", performance=f"p{i+1}",
        )
        shots.append(s)
    return GenerationSegment("SEG1", TimeInterval(0, _TPS * n_shots), shots)


class LegacySyncTests(unittest.TestCase):
    """Legacy dual_output_sync still works for backward compat."""

    def test_consistent_views_pass(self):
        seg = _make_segment()
        sb = project_storyboard(seg)
        vp = project_video_prompt(seg)
        result = dos.check_dual_output_sync(sb, vp)
        self.assertTrue(result.is_consistent)

    def test_shot_count_mismatch_detected(self):
        seg = _make_segment()
        sb = project_storyboard(seg)
        vp = project_video_prompt(seg)
        vp.shot_descriptions.pop()
        result = dos.check_dual_output_sync(sb, vp)
        self.assertFalse(result.is_consistent)

    def test_no_nl_similarity_used(self):
        seg = _make_segment()
        sb = project_storyboard(seg)
        vp = project_video_prompt(seg)
        result = dos.check_dual_output_sync(sb, vp)
        self.assertFalse(hasattr(result, "nl_similarity_score"))


class ProductionComparisonTests(unittest.TestCase):
    """Real production fingerprint comparison API detects tampering."""

    def test_untampered_projections_match(self):
        seg = _make_segment(n_shots=2)
        sb = project_storyboard(seg)
        vp = project_video_prompt(seg)
        result = compare_projections(sb, vp)
        self.assertTrue(result.fingerprint_match)
        self.assertTrue(result.is_consistent)

    def test_tick_tamper_detected_via_comparison(self):
        """Tampering a tick in one projection must be detected."""
        seg = _make_segment(n_shots=2)
        sb = project_storyboard(seg)
        vp = project_video_prompt(seg)

        # Tamper: rebuild vp's contract with a different tick
        builder = build_contract_from_segment(seg, _TPS)
        builder._nodes[0] = FrozenNode(
            node_id="shot_000", start_tick=500, end_tick=_TPS,
            shot_id="S1", sb_node=True,
        )
        tampered_view = VideoPromptView(
            segment_id="SEG1", contract=builder.build(),
        )
        result = compare_projections(sb, tampered_view)
        self.assertFalse(result.fingerprint_match,
                         "Tick tamper must break fingerprint match")

    def test_phase_id_tamper_detected(self):
        seg = _make_segment(n_shots=2)
        sb = project_storyboard(seg)
        vp = project_video_prompt(seg)

        builder = build_contract_from_segment(seg, _TPS)
        old_node = builder._nodes[0]
        builder._nodes[0] = FrozenNode(
            node_id=old_node.node_id, start_tick=old_node.start_tick,
            end_tick=old_node.end_tick, phase_id="TAMPERED",
            shot_id=old_node.shot_id, sb_node=old_node.sb_node,
            _display=old_node._display, _provenance=old_node._provenance,
        )
        tampered = VideoPromptView(segment_id="SEG1", contract=builder.build())
        result = compare_projections(sb, tampered)
        self.assertFalse(result.fingerprint_match)

    def test_handoff_tamper_detected(self):
        seg = _make_segment(n_shots=1)
        sb = project_storyboard(seg)
        builder = build_contract_from_segment(seg, _TPS)
        builder.set_handoff("TAMPERED_HANDOFF", "source:attacker")
        tampered = VideoPromptView(segment_id="SEG1", contract=builder.build())
        result = compare_projections(sb, tampered)
        self.assertFalse(result.fingerprint_match)

    def test_sb_nodes_are_ordered_subset(self):
        seg = _make_segment(n_shots=2)
        sb = project_storyboard(seg)
        vp = project_video_prompt(seg)
        result = compare_projections(sb, vp)
        self.assertTrue(result.sb_nodes_are_ordered_subset)

    def test_sb_node_not_in_video_detected(self):
        """Adding an SB node only to storyboard is detected."""
        seg = _make_segment(n_shots=1)
        sb_builder = build_contract_from_segment(seg, _TPS)
        sb_builder.add_node("sb_only", 1000, 2000, sb_node=True, node_type="panel")
        sb = project_storyboard(seg, builder=sb_builder)
        vp = project_video_prompt(seg)
        result = compare_projections(sb, vp)
        self.assertFalse(result.sb_nodes_are_ordered_subset)


if __name__ == "__main__":
    unittest.main()
