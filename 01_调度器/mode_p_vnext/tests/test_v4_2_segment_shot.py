"""V4.2 Generation Segment/Shot/Beat Schema."""

import unittest

try:
    from mode_p_vnext.schema.canonical_timeline import TimeInterval
    from mode_p_vnext.schema import generation_segment as gs
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class CinematicShotTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "generation_segment not yet implemented")
    def test_shot_required_fields(self):
        s = gs.CinematicShot(
            shot_id="S1",
            segment_id="SEG1",
            time_range=TimeInterval(0, 24000),
            narrative_job="建立空间关系",
            camera_position="人物右侧45°",
            shot_size="WS",
            focal_intent="交代环境与人物位置",
            camera_motion="缓慢推近",
            composition="人物画右，空间画左",
            lighting="顶光",
            performance="无特殊表演",
        )
        self.assertEqual(s.shot_id, "S1")
        self.assertEqual(s.shot_size, "WS")

    @unittest.skipIf(not MODULE_EXISTS, "generation_segment not yet implemented")
    def test_shot_binds_fact_ids(self):
        s = gs.CinematicShot(
            shot_id="S1", segment_id="SEG1",
            time_range=TimeInterval(0, 1000),
            narrative_job="x", camera_position="x", shot_size="WS",
            focal_intent="x", camera_motion="x", composition="x",
            lighting="x", performance="x",
            fact_ids=["F001", "F002"],
        )
        self.assertIn("F001", s.fact_ids)


class GenerationSegmentTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "generation_segment not yet implemented")
    def test_segment_contains_shots(self):
        shots = [
            gs.CinematicShot("S1", "SEG1", TimeInterval(0, 1000),
                             "job", "cam", "WS", "focal", "mot", "comp", "light", "perf"),
            gs.CinematicShot("S2", "SEG1", TimeInterval(1000, 2000),
                             "job2", "cam", "MCU", "focal", "mot", "comp", "light", "perf"),
        ]
        seg = gs.GenerationSegment(
            segment_id="SEG1",
            time_range=TimeInterval(0, 2000),
            shots=shots,
        )
        self.assertEqual(len(seg.shots), 2)

    @unittest.skipIf(not MODULE_EXISTS, "generation_segment not yet implemented")
    def test_segment_separates_from_shots(self):
        """Generation Segment ≠ Cinematic Shot — one segment can have multiple shots."""
        seg = gs.GenerationSegment(
            segment_id="SEG1",
            time_range=TimeInterval(0, 3000),
            shots=[
                gs.CinematicShot("S1", "SEG1", TimeInterval(0, 1000),
                                 "job", "cam", "WS", "f", "m", "c", "l", "p"),
                gs.CinematicShot("S2", "SEG1", TimeInterval(1000, 2000),
                                 "job", "cam", "MCU", "f", "m", "c", "l", "p"),
                gs.CinematicShot("S3", "SEG1", TimeInterval(2000, 3000),
                                 "job", "cam", "ECU", "f", "m", "c", "l", "p"),
            ],
        )
        self.assertEqual(len(seg.shots), 3)

    @unittest.skipIf(not MODULE_EXISTS, "generation_segment not yet implemented")
    def test_segment_binds_handoff(self):
        shots = [gs.CinematicShot("S1", "SEG1", TimeInterval(0, 1000),
                                  "j", "c", "WS", "f", "m", "co", "l", "p")]
        seg = gs.GenerationSegment(
            segment_id="SEG1", time_range=TimeInterval(0, 1000),
            shots=shots,
            final_handoff_state_id="HANDOFF_SEG1",
        )
        self.assertEqual(seg.final_handoff_state_id, "HANDOFF_SEG1")


if __name__ == "__main__":
    unittest.main()
