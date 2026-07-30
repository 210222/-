"""V1.6 Structured Handoff Contract — entry/exit/handoff schema and validation.

Verify:
- HandoffState with character, prop, camera, light, surface, audio fields
- Entry/Exit/Handoff required minimum fields
- Adjacent shot handoff conflict detection
- Algorithm validates continuity only, does not design handoffs
"""

import unittest


try:
    from mode_p_vnext.schema import handoff as ho
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


# ---------------------------------------------------------------------------
# HandoffState schema
# ---------------------------------------------------------------------------

class HandoffStateSchemaTests(unittest.TestCase):
    """HandoffState dataclass structure."""

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_state_has_required_fields(self):
        s = ho.HandoffState(
            character_positions={"pedro": "画右，面向画左"},
            character_gaze={"pedro": "看向手机"},
            action_phase="擦枪中段",
            prop_ownership={"枪": "pedro右手"},
            camera_side="pedro左后侧45°",
            camera_motion_phase="缓慢推近",
            focus_target="枪管",
            key_light_direction="顶光偏右",
            visible_surfaces=["pedro侧脸", "枪管金属面", "双手"],
            audio_continuity="画外直升机持续",
        )
        self.assertEqual(s.character_positions["pedro"], "画右，面向画左")
        self.assertEqual(s.camera_motion_phase, "缓慢推近")
        self.assertIn("pedro侧脸", s.visible_surfaces)

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_state_empty_characters_allowed(self):
        s = ho.HandoffState()  # all fields optional
        self.assertEqual(s.character_positions, {})
        self.assertEqual(s.visible_surfaces, [])

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_state_to_dict(self):
        s = ho.HandoffState(
            character_positions={"isa": "画左"},
            camera_side="正面",
        )
        d = s.to_dict()
        self.assertEqual(d["character_positions"], {"isa": "画左"})
        self.assertEqual(d["camera_side"], "正面")


# ---------------------------------------------------------------------------
# ShotHandoff
# ---------------------------------------------------------------------------

class ShotHandoffTests(unittest.TestCase):
    """ShotHandoff wraps entry and exit states."""

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_shot_handoff(self):
        entry = ho.HandoffState(character_positions={"pedro": "画外入"})
        exit_s = ho.HandoffState(character_positions={"pedro": "画中"})
        sh = ho.ShotHandoff(shot_id="S1", entry_state=entry, exit_state=exit_s)
        self.assertEqual(sh.shot_id, "S1")
        self.assertEqual(sh.entry_state, entry)
        self.assertEqual(sh.exit_state, exit_s)


# ---------------------------------------------------------------------------
# SegmentHandoff
# ---------------------------------------------------------------------------

class SegmentHandoffTests(unittest.TestCase):
    """SegmentHandoff wraps per-shot handoffs + final_handoff."""

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_segment_handoff(self):
        shots = [
            ho.ShotHandoff("S1",
                ho.HandoffState(character_positions={"pedro": "画右"}),
                ho.HandoffState(character_positions={"pedro": "画中"})),
            ho.ShotHandoff("S2",
                ho.HandoffState(character_positions={"pedro": "画中"}),
                ho.HandoffState(character_positions={"pedro": "画左"})),
        ]
        final = ho.HandoffState(character_positions={"pedro": "画左"})
        seg = ho.SegmentHandoff(
            segment_id="SEG1",
            shot_handoffs=shots,
            final_handoff=final,
        )
        self.assertEqual(len(seg.shot_handoffs), 2)
        self.assertEqual(seg.final_handoff, final)


# ---------------------------------------------------------------------------
# Adjacent conflict check
# ---------------------------------------------------------------------------

class AdjacentConflictTests(unittest.TestCase):
    """Verify adjacent shot exit/entry continuity."""

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_consistent_adjacent_passes(self):
        """Shot 1 exit matches Shot 2 entry — no conflict."""
        s1 = ho.ShotHandoff("S1",
            ho.HandoffState(character_positions={"pedro": "画中"}),
            ho.HandoffState(character_positions={"pedro": "画中"}),
        )
        s2 = ho.ShotHandoff("S2",
            ho.HandoffState(character_positions={"pedro": "画中"}),
            ho.HandoffState(character_positions={"pedro": "画左"}),
        )
        conflicts = ho.check_adjacent_handoff_conflicts(s1, s2)
        self.assertEqual(len(conflicts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_conflicting_character_position_detected(self):
        """S1 exit: pedro画中, S2 entry: pedro画右 — conflict."""
        s1 = ho.ShotHandoff("S1",
            ho.HandoffState(),
            ho.HandoffState(character_positions={"pedro": "画中"}),
        )
        s2 = ho.ShotHandoff("S2",
            ho.HandoffState(character_positions={"pedro": "画右"}),
            ho.HandoffState(),
        )
        conflicts = ho.check_adjacent_handoff_conflicts(s1, s2)
        self.assertGreater(len(conflicts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_conflicting_camera_side_detected(self):
        s1 = ho.ShotHandoff("S1",
            ho.HandoffState(),
            ho.HandoffState(camera_side="画左"),
        )
        s2 = ho.ShotHandoff("S2",
            ho.HandoffState(camera_side="画右"),
            ho.HandoffState(),
        )
        conflicts = ho.check_adjacent_handoff_conflicts(s1, s2)
        self.assertGreater(len(conflicts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_empty_states_no_conflict(self):
        """Empty states on both sides — nothing to conflict about."""
        s1 = ho.ShotHandoff("S1", ho.HandoffState(), ho.HandoffState())
        s2 = ho.ShotHandoff("S2", ho.HandoffState(), ho.HandoffState())
        conflicts = ho.check_adjacent_handoff_conflicts(s1, s2)
        self.assertEqual(len(conflicts), 0)

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_missing_entry_state_flagged(self):
        s1 = ho.ShotHandoff("S1",
            ho.HandoffState(),
            ho.HandoffState(character_positions={"pedro": "画中"}),
        )
        s2 = ho.ShotHandoff("S2",
            ho.HandoffState(),  # empty entry — may be intentional but flagged
            ho.HandoffState(),
        )
        warnings = ho.check_handoff_completeness([s1, s2])
        # S2 has empty entry after S1 has populated exit — completeness warning
        self.assertGreater(len(warnings), 0)

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_full_segment_conflict_check(self):
        shots = [
            ho.ShotHandoff("S1",
                ho.HandoffState(character_positions={"pedro": "画右"}),
                ho.HandoffState(character_positions={"pedro": "画中"})),
            ho.ShotHandoff("S2",
                ho.HandoffState(character_positions={"pedro": "画中"}),
                ho.HandoffState(character_positions={"pedro": "画左"})),
        ]
        final = ho.HandoffState(character_positions={"pedro": "画左"})
        seg = ho.SegmentHandoff("SEG1", shots, final)
        result = ho.validate_segment_handoff(seg)
        self.assertTrue(result.is_consistent,
                        f"Conflicts: {result.conflicts}")

    @unittest.skipIf(not MODULE_EXISTS, "handoff module not yet implemented")
    def test_full_segment_detects_conflict_chain(self):
        shots = [
            ho.ShotHandoff("S1",
                ho.HandoffState(),
                ho.HandoffState(character_positions={"pedro": "画中"})),
            ho.ShotHandoff("S2",
                ho.HandoffState(character_positions={"pedro": "画右"}),  # mismatch!
                ho.HandoffState()),
        ]
        final = ho.HandoffState()
        seg = ho.SegmentHandoff("SEG1", shots, final)
        result = ho.validate_segment_handoff(seg)
        self.assertFalse(result.is_consistent)


if __name__ == "__main__":
    unittest.main()
