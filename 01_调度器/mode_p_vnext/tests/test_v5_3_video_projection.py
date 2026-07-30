"""R1.3+ — Video projection tests: reference duties, single execution, legacy compat."""

import unittest

from mode_p_vnext.schema.canonical_timeline import TimeInterval
from mode_p_vnext.schema.generation_segment import CinematicShot, GenerationSegment
from mode_p_vnext.storyboard_projection import (
    ContractBuilder,
    DualOutputContract,
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
            narrative_job=f"叙事{i+1}", camera_position="正面",
            shot_size="WS", focal_intent="24mm",
            camera_motion="缓慢前推", composition="中央对称",
            lighting="顶光", performance="自然",
        )
        shots.append(s)
    return GenerationSegment(
        segment_id=seg_id,
        time_range=TimeInterval(start_tick=0, end_tick=_TPS * n_shots),
        shots=shots,
    )


class VideoProjectionTests(unittest.TestCase):

    def test_direct_projection_has_nodes(self):
        seg = _make_segment("TEST", n_shots=2)
        view = project_video_prompt(seg)
        self.assertEqual(len(view.contract.nodes), 2)

    def test_legacy_shot_descriptions_preserved(self):
        seg = _make_segment("TEST", n_shots=2)
        view = project_video_prompt(seg)
        self.assertEqual(len(view.shot_descriptions), 2)
        self.assertIn("shot_id", view.shot_descriptions[0])
        self.assertIn("start_tick", view.shot_descriptions[0])

    def test_single_preferred_execution(self):
        seg = _make_segment()
        view = project_video_prompt(seg)
        self.assertFalse(hasattr(view, "variants"))

    def test_reference_images_flow_to_contract(self):
        seg = _make_segment()
        view = project_video_prompt(seg, storyboard_refs=["ref1"])
        self.assertIn("ref1", view.contract.reference_images)

    def test_forbidden_items_flow_to_prohibitions(self):
        seg = _make_segment()
        view = project_video_prompt(seg, forbidden_items=["禁止特效"])
        self.assertIn("禁止特效", view.contract.prohibitions)


class ReferenceDutyTests(unittest.TestCase):
    """One-to-one reference image to responsibility mapping."""

    def _make_contract_with_duties(self, refs, duties):
        b = ContractBuilder("REF_TEST")
        b.add_node("n1", 0, 1000, shot_id="S1")
        for r in refs:
            b.add_reference_image(r)
        for rid, duty in duties:
            b.set_reference_duty(rid, duty)
        return b.build()

    def test_one_to_one_mapping_passes_validation(self):
        c = self._make_contract_with_duties(
            ["img1", "img2"],
            [("img1", "构图"), ("img2", "色彩")],
        )
        v = validate_delivery_contract(c, "REF_TEST")
        ref_violations = [x for x in v if "reference" in x.lower() or "duty" in x.lower()]
        self.assertEqual(len(ref_violations), 0,
                         f"One-to-one mapping should pass: got {ref_violations}")

    def test_orphan_duty_detected(self):
        c = self._make_contract_with_duties(
            ["img1"],
            [("img1", "构图"), ("img2", "色彩")],
        )
        v = validate_delivery_contract(c, "REF_TEST")
        orphan_violations = [x for x in v if "img2" in x or "unknown reference" in x]
        self.assertGreater(len(orphan_violations), 0,
                           "Duty for non-existent reference must be detected")

    def test_missing_duty_detected(self):
        c = self._make_contract_with_duties(
            ["img1", "img2"],
            [("img1", "构图")],
        )
        v = validate_delivery_contract(c, "REF_TEST")
        missing = [x for x in v if "img2" in x or "no declared duty" in x]
        self.assertGreater(len(missing), 0,
                           "Reference without duty must be detected")


if __name__ == "__main__":
    unittest.main()
