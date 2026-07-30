"""V4.5 Master Parser & Validator — fail-closed, no guessing."""

import unittest

try:
    from mode_p_vnext.schema.canonical_timeline import TimeInterval
    from mode_p_vnext.schema.generation_segment import GenerationSegment, CinematicShot
    from mode_p_vnext import master_parser as mp
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


def _valid_master_dict():
    return {
        "master_id": "MASTER_EP8",
        "episode_id": "EP8",
        "schema_version": "4.0",
        "diagnosis_artifact_id": "DA001",
        "segments": [{
            "segment_id": "SEG1",
            "start_tick": 0, "end_tick": 24000,
            "shots": [{
                "shot_id": "S1", "segment_id": "SEG1",
                "start_tick": 0, "end_tick": 24000,
                "narrative_job": "建立空间", "camera_position": "右45°",
                "shot_size": "WS", "focal_intent": "交代环境",
                "camera_motion": "静止", "composition": "人物右",
                "lighting": "顶光", "performance": "无",
            }],
        }],
    }


class MasterParserTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "master_parser not yet implemented")
    def test_parse_valid_master(self):
        master = mp.parse_master(_valid_master_dict())
        self.assertEqual(master.master_id, "MASTER_EP8")
        self.assertEqual(len(master.segments), 1)

    @unittest.skipIf(not MODULE_EXISTS, "master_parser not yet implemented")
    def test_parse_missing_segments_fails(self):
        d = _valid_master_dict()
        del d["segments"]
        with self.assertRaises(mp.MasterParseError):
            mp.parse_master(d)

    @unittest.skipIf(not MODULE_EXISTS, "master_parser not yet implemented")
    def test_validate_segment_shot_containment(self):
        master = mp.parse_master(_valid_master_dict())
        violations = mp.validate_master(master)
        self.assertEqual(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "master_parser not yet implemented")
    def test_shot_outside_segment_detected(self):
        d = _valid_master_dict()
        d["segments"][0]["end_tick"] = 10000  # segment shorter than shot
        with self.assertRaises(mp.MasterParseError):
            mp.parse_master(d)

    @unittest.skipIf(not MODULE_EXISTS, "master_parser not yet implemented")
    def test_parser_does_not_guess_missing_fields(self):
        """Missing required fields → fail, don't fill defaults."""
        d = _valid_master_dict()
        del d["segments"][0]["shots"][0]["shot_size"]
        with self.assertRaises(mp.MasterParseError):
            mp.parse_master(d)


if __name__ == "__main__":
    unittest.main()
