"""V2.6 Audio/Lipsync Contract — dialogue attribution, lip visibility, off-screen dialogue."""

import unittest

try:
    from mode_p_vnext.schema.canonical_timeline import TimeInterval
    from mode_p_vnext.schema import audio_contract as ac
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class AudioContractTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "audio_contract not yet implemented")
    def test_dialogue_line_fields(self):
        d = ac.DialogueLine(
            line_id="DL1",
            character_id="pedro",
            text="球跑了",
            start_tick=1000, end_tick=3000,
            lip_visible=True,
        )
        self.assertEqual(d.character_id, "pedro")
        self.assertTrue(d.lip_visible)

    @unittest.skipIf(not MODULE_EXISTS, "audio_contract not yet implemented")
    def test_offscreen_dialogue(self):
        d = ac.DialogueLine(
            line_id="DL2", character_id="voice",
            text="画外喊声", start_tick=0, end_tick=1000,
            lip_visible=False,
            source="offscreen",
        )
        self.assertFalse(d.lip_visible)
        self.assertEqual(d.source, "offscreen")

    @unittest.skipIf(not MODULE_EXISTS, "audio_contract not yet implemented")
    def test_audio_bridge(self):
        b = ac.AudioBridge(
            bridge_id="AB1",
            sound_description="直升机持续",
            from_tick=48000,
            to_tick=72000,
            crosses_segment_boundary=True,
        )
        self.assertTrue(b.crosses_segment_boundary)

    @unittest.skipIf(not MODULE_EXISTS, "audio_contract not yet implemented")
    def test_audio_contract_contains_dialogue_and_bridges(self):
        dl = [ac.DialogueLine("DL1", "pedro", "text", 0, 1000, True)]
        bridges = [ac.AudioBridge("AB1", "helicopter", 0, 5000, False)]
        contract = ac.AudioContract(
            segment_id="SEG1",
            dialogue_lines=dl,
            audio_bridges=bridges,
        )
        self.assertEqual(len(contract.dialogue_lines), 1)
        self.assertEqual(len(contract.audio_bridges), 1)

    @unittest.skipIf(not MODULE_EXISTS, "audio_contract not yet implemented")
    def test_lip_sync_warning_when_lips_not_visible(self):
        """Dialogue attributed to character on screen but lips not visible → warn."""
        dl = ac.DialogueLine("DL1", "pedro", "说话", 0, 1000,
                             lip_visible=False, source="on_screen")
        warnings = ac.check_lipsync([dl])
        self.assertGreater(len(warnings), 0)

    @unittest.skipIf(not MODULE_EXISTS, "audio_contract not yet implemented")
    def test_offscreen_dialogue_no_lipsync_warning(self):
        dl = ac.DialogueLine("DL1", "pedro", "说话", 0, 1000,
                             lip_visible=False, source="offscreen")
        warnings = ac.check_lipsync([dl])
        self.assertEqual(len(warnings), 0)

    @unittest.skipIf(not MODULE_EXISTS, "audio_contract not yet implemented")
    def test_overlapping_dialogue_detected(self):
        dl = [
            ac.DialogueLine("DL1", "a", "x", 0, 2000, True),
            ac.DialogueLine("DL2", "b", "y", 1000, 3000, True),  # overlaps DL1
        ]
        conflicts = ac.check_dialogue_overlaps(dl)
        self.assertGreater(len(conflicts), 0)


if __name__ == "__main__":
    unittest.main()
