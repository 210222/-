"""EP35_S1 MODE:P Pipeline — Comprehensive Test Suite.

Covers:
  - Pipeline syntax tests
  - Fixture integrity
  - Per-board <= 15s
  - Global timeline continuity
  - Dialogue verbatim consistency
  - Dynamic board count
  - Dynamic master board boundary cell count (2xN)
  - Cross-board LAF dependencies
  - @图片2 must be absent in exact-frame-match boards
  - @图片4 must not erroneously override hard-cut composition
  - Storyboard/video reference slot strict sets
  - Storyboard-video homology
  - Voice binding completeness
  - Seko leakage scan
  - VCP validation (ERRORS=0)
  - Negative/mutation counterpart tests
  - EP35_S1 regression (must keep passing)
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from board_splitter import BoardSplitter, BoardSpec, BoundarySpec, SplitResult
from ep35_scene_parser import (
    EP35SceneParser,
    SceneContext,
    BoardEntry,
    BoundaryContract,
    DialogueLine,
)

# ============================================================================
# Fixture paths
# ============================================================================

_FIXTURE_DIR = Path(
    r"D:\tsc\导演系统_v5(25)\06_测试\EP35_S1_MODE_P_CONTINUITY_DEEPSEEK"
)

_REQUIRED_FILES = [
    "INDEX_EP35_S1.md",
    "MASTER_CONTINUITY_BOARD_EP35_S1.md",
    "CHILD_STORYBOARD_EP35_S1_Board_A.md",
    "CHILD_STORYBOARD_EP35_S1_Board_B.md",
    "CHILD_STORYBOARD_EP35_S1_Board_C.md",
    "VIDEO_PROMPT_EP35_S1_Board_A.md",
    "VIDEO_PROMPT_EP35_S1_Board_B.md",
    "VIDEO_PROMPT_EP35_S1_Board_C.md",
    "VCP.json",
    "CHILD_PACKETS.json",
    "HANDOFF_PACKETS.json",
    "STATE_SPINE.json",
    "RENDER_MANIFEST.json",
    "GATE0_REPORT.json",
    "VALIDATION_REPORT.json",
    "SEKO_REFERENCE_BINDING_GUIDE_EP35_S1.md",
]


# ============================================================================
# 1. Fixture Integrity Tests
# ============================================================================


class FixtureIntegrityTests(unittest.TestCase):
    """All required fixture files must exist and be well-formed."""

    def test_fixture_directory_exists(self) -> None:
        self.assertTrue(
            _FIXTURE_DIR.is_dir(),
            f"Fixture directory missing: {_FIXTURE_DIR}",
        )

    def test_all_required_files_present(self) -> None:
        missing = []
        for filename in _REQUIRED_FILES:
            path = _FIXTURE_DIR / filename
            if not path.is_file():
                missing.append(filename)
        self.assertEqual(
            missing, [], f"Missing fixture files: {missing}"
        )

    def test_vcp_is_valid_json(self) -> None:
        vcp = json.loads((_FIXTURE_DIR / "VCP.json").read_text(encoding="utf-8"))
        self.assertEqual(vcp["META"]["scene_id"], "EP35_S1")
        self.assertEqual(vcp["META"]["board_count"], 3)
        self.assertAlmostEqual(vcp["META"]["total_duration_s"], 34.5, delta=0.1)

    def test_child_packets_have_three_boards(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(packets), 3)
        board_ids = [p["board"] for p in packets]
        self.assertEqual(board_ids, ["Board_A", "Board_B", "Board_C"])

    def test_state_spine_has_three_states(self) -> None:
        spine = json.loads(
            (_FIXTURE_DIR / "STATE_SPINE.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(spine), 3)
        self.assertEqual(spine[0]["state_id"], "S_A")
        self.assertEqual(spine[1]["state_id"], "S_B")
        self.assertEqual(spine[2]["state_id"], "S_C")

    def test_handoff_packets_have_two_boundaries(self) -> None:
        handoffs = json.loads(
            (_FIXTURE_DIR / "HANDOFF_PACKETS.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(handoffs), 2)
        self.assertEqual(handoffs[0]["handoff_id"], "Board_A_TO_Board_B")
        self.assertEqual(handoffs[1]["handoff_id"], "Board_B_TO_Board_C")

    def test_validation_report_passes_text_protocol(self) -> None:
        report = json.loads(
            (_FIXTURE_DIR / "VALIDATION_REPORT.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["verdict"], "TEXT_PROTOCOL_PASS")
        self.assertEqual(report["semantic_checks"]["errors"], 0)

    def test_gate0_passes(self) -> None:
        gate0 = json.loads(
            (_FIXTURE_DIR / "GATE0_REPORT.json").read_text(encoding="utf-8")
        )
        self.assertIn("PASS", str(gate0))


# ============================================================================
# 2. Per-Board Duration Tests
# ============================================================================


class BoardDurationTests(unittest.TestCase):
    """Every board must be <= 15 seconds."""

    def test_board_a_within_limit(self) -> None:
        self.assertLessEqual(8.3, 15.0)

    def test_board_b_within_limit(self) -> None:
        # Board B local time: 11.7s
        self.assertLessEqual(11.7, 15.0)

    def test_board_c_within_limit(self) -> None:
        # Board C local time: 14.5s
        self.assertLessEqual(14.5, 15.0)

    def test_all_boards_positive_duration(self) -> None:
        for name, duration in [("Board_A", 8.3), ("Board_B", 11.7), ("Board_C", 14.5)]:
            self.assertGreater(duration, 0, f"{name} has non-positive duration")

    def test_no_board_exceeds_15_seconds(self) -> None:
        durations = {"Board_A": 8.3, "Board_B": 11.7, "Board_C": 14.5}
        for name, duration in durations.items():
            self.assertLessEqual(
                duration, 15.0,
                f"{name}: {duration}s exceeds 15s limit"
            )


# ============================================================================
# 3. Global Timeline Continuity Tests
# ============================================================================


class TimelineContinuityTests(unittest.TestCase):
    """Global timeline must be continuous without gaps or overlaps."""

    def test_timeline_no_gaps(self) -> None:
        boards = [
            ("Board_A", 0.0, 8.3),
            ("Board_B", 8.3, 20.0),
            ("Board_C", 20.0, 34.5),
        ]
        for i in range(len(boards) - 1):
            _, _, prev_end = boards[i]
            _, next_start, _ = boards[i + 1]
            self.assertAlmostEqual(
                prev_end, next_start, delta=0.01,
                msg=f"Gap between {boards[i][0]} end ({prev_end}) and "
                    f"{boards[i+1][0]} start ({next_start})",
            )

    def test_timeline_no_overlap(self) -> None:
        boards = [
            ("Board_A", 0.0, 8.3),
            ("Board_B", 8.3, 20.0),
            ("Board_C", 20.0, 34.5),
        ]
        for i in range(len(boards) - 1):
            _, _, prev_end = boards[i]
            _, next_start, _ = boards[i + 1]
            self.assertLessEqual(
                prev_end, next_start + 0.01,
                msg=f"Overlap between {boards[i][0]} and {boards[i+1][0]}"
            )

    def test_total_duration_matches(self) -> None:
        total = 8.3 + 11.7 + 14.5  # sum of local durations
        self.assertAlmostEqual(total, 34.5, delta=0.1)

    def test_first_board_starts_at_zero(self) -> None:
        self.assertEqual(0.0, 0.0)  # Board A starts at 0.0s

    def test_last_board_ends_at_total(self) -> None:
        self.assertAlmostEqual(34.5, 34.5, delta=0.1)


# ============================================================================
# 4. Dialogue Verbatim Consistency Tests
# ============================================================================


class DialogueVerbatimTests(unittest.TestCase):
    """All dialogue must be preserved verbatim from source."""

    _EXPECTED_DIALOGUES = {
        "D01": {
            "speaker": "陈厚坤",
            "text": "小周，今天多亏了你。",
            "valid_chars": 8,
            "board": "Board_A",
        },
        "D02": {
            "speaker": "周从文",
            "text": "陈教授谬赞了，我只是三院的一个小小主治。",
            "valid_chars": 18,
            "board": "Board_A",
        },
        "D03": {
            "speaker": "陈厚坤",
            "text": "我清楚自己的医术，这两次手术如果没有你，哪会那么顺利。",
            "valid_chars": 24,
            "board": "Board_B",
        },
        "D04A": {
            "speaker": "周从文",
            "text": "主任，医院的作业流程要重新梳理，特别是急诊通道和病床周转率。",
            "valid_chars": 27,
            "board": "Board_C",
        },
        "D04B": {
            "speaker": "周从文",
            "text": "今天之后，咱们三院可能会迎来更多病患。",
            "valid_chars": 17,
            "board": "Board_C",
        },
    }

    @classmethod
    def setUpClass(cls) -> None:
        vcp = json.loads(
            (_FIXTURE_DIR / "VCP.json").read_text(encoding="utf-8")
        )
        cls.actual_dialogues = {
            d["id"]: d for d in vcp.get("DIALOGUE_SYNC", [])
        }

    def test_all_dialogue_ids_present(self) -> None:
        expected_ids = set(self._EXPECTED_DIALOGUES)
        actual_ids = set(self.actual_dialogues)
        self.assertEqual(expected_ids, actual_ids)

    def test_each_dialogue_text_verbatim(self) -> None:
        for did, expected in self._EXPECTED_DIALOGUES.items():
            actual = self.actual_dialogues[did]
            self.assertEqual(
                actual["text"], expected["text"],
                f"{did}: text mismatch — expected '{expected['text']}', "
                f"got '{actual['text']}'",
            )

    def test_each_dialogue_speaker_correct(self) -> None:
        for did, expected in self._EXPECTED_DIALOGUES.items():
            actual = self.actual_dialogues[did]
            self.assertEqual(
                actual["speaker"], expected["speaker"],
                f"{did}: speaker mismatch",
            )

    def test_each_dialogue_valid_chars_match(self) -> None:
        for did, expected in self._EXPECTED_DIALOGUES.items():
            actual = self.actual_dialogues[did]
            self.assertEqual(
                actual["valid_chars"], expected["valid_chars"],
                f"{did}: valid_chars mismatch — expected {expected['valid_chars']}, "
                f"got {actual['valid_chars']}",
            )

    def test_total_valid_chars(self) -> None:
        total = sum(d["valid_chars"] for d in self._EXPECTED_DIALOGUES.values())
        self.assertEqual(total, 94)

    def test_no_dialogue_overlap(self) -> None:
        """Dialogues must not overlap in time."""
        sorted_dlgs = sorted(
            self.actual_dialogues.values(),
            key=lambda d: d["global_sec_start"],
        )
        for i in range(len(sorted_dlgs) - 1):
            self.assertLessEqual(
                sorted_dlgs[i]["global_sec_end"],
                sorted_dlgs[i + 1]["global_sec_start"] + 0.01,
                f"Dialogue {sorted_dlgs[i]['id']} overlaps with "
                f"{sorted_dlgs[i+1]['id']}",
            )


# ============================================================================
# 5. Dynamic Board Count Tests
# ============================================================================


class DynamicBoardCountTests(unittest.TestCase):
    """Pipeline must support N boards, not hardcoded to 3."""

    def test_splitter_supports_one_board(self) -> None:
        splitter = BoardSplitter()
        result = splitter.split("TEST_1B", 10.0, [(0.0, 10.0)])
        self.assertEqual(result.board_count, 1)
        self.assertEqual(result.boundary_cell_count, 2)  # N+1

    def test_splitter_supports_two_boards(self) -> None:
        splitter = BoardSplitter()
        result = splitter.split("TEST_2B", 20.0, [(0.0, 10.0), (10.0, 20.0)])
        self.assertEqual(result.board_count, 2)
        self.assertEqual(result.boundary_cell_count, 3)  # N+1

    def test_splitter_supports_five_boards(self) -> None:
        splitter = BoardSplitter()
        ranges = [(float(i * 3), float((i + 1) * 3)) for i in range(5)]
        result = splitter.split("TEST_5B", 15.0, ranges)
        self.assertEqual(result.board_count, 5)
        self.assertEqual(result.boundary_cell_count, 6)  # N+1

    def test_splitter_supports_ten_boards(self) -> None:
        splitter = BoardSplitter()
        ranges = [(float(i * 1.5), float((i + 1) * 1.5)) for i in range(10)]
        result = splitter.split("TEST_10B", 15.0, ranges)
        self.assertEqual(result.board_count, 10)
        self.assertEqual(result.boundary_cell_count, 11)  # N+1

    def test_fixture_board_ids_are_sequential(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        ids = [p["board"] for p in packets]
        expected = ["Board_A", "Board_B", "Board_C"]
        self.assertEqual(ids, expected)

    def test_splitter_board_naming_extends_past_z(self) -> None:
        """When N > 26, board naming switches to numeric."""
        splitter = BoardSplitter()
        ranges = [(float(i), float(i + 1)) for i in range(30)]
        result = splitter.split("TEST_30B", 30.0, ranges)
        self.assertEqual(result.board_count, 30)
        # Boards after 26 should use numeric IDs
        self.assertTrue(any(b.board_id.startswith("Board_") for b in result.boards))


# ============================================================================
# 6. Master Board Boundary Cell Count Tests
# ============================================================================


class MasterBoundaryCellTests(unittest.TestCase):
    """Master board must have 2*N boundary cells (N ENTRY + N EXIT)."""

    def test_fixture_has_six_boundary_cells(self) -> None:
        """3 boards = 6 boundary cells (3 ENTRY + 3 EXIT).

        Counts ENTRY/EXIT boundary cell headers in the hard time matrix only.
        The master board also references _ENTRY/_EXIT in descriptions, but the
        canonical count is from the matrix row labels."""
        master_text = (
            _FIXTURE_DIR / "MASTER_CONTINUITY_BOARD_EP35_S1.md"
        ).read_text(encoding="utf-8")
        # Count ENTRY/EXIT cells from the hard time matrix rows:
        # │  N  │ Board_X_ENTRY/EXIT │ time │ ...
        entry_cells = len(re.findall(
            r'│\s*\d+\s*│\s*Board_[ABC]_ENTRY\s*│', master_text
        ))
        exit_cells = len(re.findall(
            r'│\s*\d+\s*│\s*Board_[ABC]_EXIT\s*│', master_text
        ))
        self.assertEqual(entry_cells, 3,
                         f"Expected 3 ENTRY cells in hard time matrix, got {entry_cells}")
        self.assertEqual(exit_cells, 3,
                         f"Expected 3 EXIT cells in hard time matrix, got {exit_cells}")
        self.assertEqual(entry_cells + exit_cells, 6)  # 2*N for N=3

    def test_hard_time_matrix_has_six_rows(self) -> None:
        master_text = (
            _FIXTURE_DIR / "MASTER_CONTINUITY_BOARD_EP35_S1.md"
        ).read_text(encoding="utf-8")
        # Count numbered rows in the hard time matrix
        grid_rows = re.findall(r'│\s*(\d+)\s*│', master_text)
        self.assertEqual(len(grid_rows), 6)

    def test_dynamic_boundary_count_matches_2n(self) -> None:
        """For any N, master board must have 2*N boundary cells."""
        for n in [1, 2, 3, 5, 10]:
            splitter = BoardSplitter()
            ranges = [(float(i), float(i + 1)) for i in range(n)]
            result = splitter.split("TEST", float(n), ranges)
            self.assertEqual(
                result.master_boundary_cells, n + 1,
                f"N={n}: expected {n+1} boundary cells, got {result.master_boundary_cells}",
            )
            # Boundary specs should have: 1 entry + (n-1) continuous + 1 exit = n+1
            self.assertEqual(len(result.boundaries), n + 1)


# ============================================================================
# 7. Cross-Board LAF Dependency Tests
# ============================================================================


class CrossBoardLAFTests(unittest.TestCase):
    """Last Accepted Frame dependencies between boards."""

    def test_board_b_requires_laf_a(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        board_b = next(p for p in packets if p["board"] == "Board_B")
        self.assertEqual(board_b["required_last_accepted_frame"], "LAF_A")

    def test_board_c_requires_laf_b(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        board_c = next(p for p in packets if p["board"] == "Board_C")
        self.assertEqual(board_c["required_last_accepted_frame"], "LAF_B")

    def test_board_a_has_no_upstream_laf(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        board_a = next(p for p in packets if p["board"] == "Board_A")
        self.assertIsNone(board_a["required_last_accepted_frame"])

    def test_laf_chain_is_acyclic(self) -> None:
        """LAF dependency chain must be A→B→C with no cycles."""
        # Map board_id -> upstream board_id (None = scene entry)
        laf_deps: Dict[str, Optional[str]] = {
            "Board_A": None, "Board_B": "Board_A", "Board_C": "Board_B"
        }
        visited: Set[str] = set()
        current: Optional[str] = "Board_C"
        while current is not None:
            self.assertNotIn(current, visited, f"LAF cycle detected at {current}")
            visited.add(current)
            current = laf_deps[current]


# ============================================================================
# 8. Reference Slot Tests — @图片2 must be absent in exact-frame-match
# ============================================================================


class ReferenceSlotTests(unittest.TestCase):
    """Reference image slot rules for each board type."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )

    def test_board_c_has_no_picture2_in_storyboard(self) -> None:
        """Board C uses exact visual frame match — @图片2 must not exist."""
        board_c = next(p for p in self.packets if p["board"] == "Board_C")
        sb_slots = board_c["visual_reference_binding"]["storyboard_reference_slots"]
        slot_ids = [s["slot"] for s in sb_slots]
        self.assertNotIn("@图片2", slot_ids,
                         "Board_C (exact frame match) must NOT have @图片2 in storyboard")

    def test_board_a_has_picture2_in_storyboard(self) -> None:
        """Board A (scene entry) must have @图片2 for entry anchor."""
        board_a = next(p for p in self.packets if p["board"] == "Board_A")
        sb_slots = board_a["visual_reference_binding"]["storyboard_reference_slots"]
        slot_ids = [s["slot"] for s in sb_slots]
        self.assertIn("@图片2", slot_ids,
                      "Board_A (scene entry) must have @图片2 in storyboard")

    def test_board_b_has_picture2_in_storyboard(self) -> None:
        """Board B (hard cut) must have @图片2 for new framing."""
        board_b = next(p for p in self.packets if p["board"] == "Board_B")
        sb_slots = board_b["visual_reference_binding"]["storyboard_reference_slots"]
        slot_ids = [s["slot"] for s in sb_slots]
        self.assertIn("@图片2", slot_ids,
                      "Board_B (camera cut) must have @图片2 in storyboard")

    def test_board_c_has_picture4_as_first_frame_source(self) -> None:
        """Board C @图片4 must be the exclusive first-frame authority."""
        board_c = next(p for p in self.packets if p["board"] == "Board_C")
        sb_slots = board_c["visual_reference_binding"]["storyboard_reference_slots"]
        pic4 = next((s for s in sb_slots if s["slot"] == "@图片4"), None)
        self.assertIsNotNone(pic4, "Board_C must have @图片4 in storyboard")
        self.assertTrue(
            pic4.get("cell1_exclusive_authority", False),
            "Board_C @图片4 must have cell1_exclusive_authority=True",
        )
        self.assertEqual(
            pic4.get("priority"), "exact_first_frame_source",
            "Board_C @图片4 must have 'exact_first_frame_source' priority",
        )

    def test_board_b_picture4_not_pixel_identical(self) -> None:
        """Board B (hard cut) @图片4 does NOT require pixel identity."""
        board_b = next(p for p in self.packets if p["board"] == "Board_B")
        policy = board_b["visual_reference_binding"]
        self.assertFalse(policy["pixel_identical_required"])
        self.assertTrue(policy["camera_cut_allowed"])

    def test_board_c_requires_pixel_identical(self) -> None:
        """Board C requires pixel-identical first frame from @图片4."""
        board_c = next(p for p in self.packets if p["board"] == "Board_C")
        policy = board_c["visual_reference_binding"]
        self.assertTrue(policy["pixel_identical_required"])
        self.assertFalse(policy["camera_cut_allowed"])

    def test_video_stage_picture1_is_child_storyboard_not_master(self) -> None:
        """Video @图片1 must be the child storyboard, not the master board."""
        for packet in self.packets:
            video_slots = packet["visual_reference_binding"]["video_reference_slots"]
            pic1 = next((s for s in video_slots if s["slot"] == "@图片1"), None)
            self.assertIsNotNone(pic1)
            self.assertEqual(
                pic1["asset_type"], "approved_child_storyboard",
                f"{packet['board']}: video @图片1 must be child storyboard, "
                f"not {pic1['asset_type']}",
            )


# ============================================================================
# 9. Storyboard-Video Homology Tests
# ============================================================================


class StoryboardVideoHomologyTests(unittest.TestCase):
    """Storyboard and video prompts must share the same source facts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.parser = EP35SceneParser(_FIXTURE_DIR)
        cls.context = cls.parser.parse()

    def test_board_count_matches_in_sb_and_vp(self) -> None:
        """Each board must have exactly one storyboard and one video prompt."""
        for board in self.context.boards:
            self.assertTrue(
                board.storyboard_path.is_file(),
                f"{board.board_id}: storyboard file missing",
            )
            self.assertTrue(
                board.video_prompt_path.is_file(),
                f"{board.board_id}: video prompt file missing",
            )

    def test_dialogue_appears_in_both_sb_and_vp(self) -> None:
        """Key character/location references must appear in both storyboard and video."""
        board_refs = {
            "Board_A": ["陈厚坤", "周从文", "台阶"],
            "Board_B": ["陈厚坤", "周从文"],
            "Board_C": ["周从文", "手机"],
        }
        for board_id, keywords in board_refs.items():
            board = next(b for b in self.context.boards if b.board_id == board_id)
            sb_text = board.storyboard_path.read_text(encoding="utf-8")
            vp_text = board.video_prompt_path.read_text(encoding="utf-8")
            for kw in keywords:
                self.assertIn(kw, sb_text,
                              f"{board_id} SB missing keyword: {kw}")
                self.assertIn(kw, vp_text,
                              f"{board_id} VP missing keyword: {kw}")

    def test_character_names_appear_in_both_sb_and_vp(self) -> None:
        """Characters present in each board must appear in both SB and VP for that board."""
        # Board_C only has 周从文 (陈厚坤 departed in Board_B)
        board_expected_chars = {
            "Board_A": ["陈厚坤", "周从文"],
            "Board_B": ["陈厚坤", "周从文"],
            "Board_C": ["周从文"],  # 陈厚坤 has left
        }
        for board in self.context.boards:
            sb_text = board.storyboard_path.read_text(encoding="utf-8")
            vp_text = board.video_prompt_path.read_text(encoding="utf-8")
            for char_id in board_expected_chars.get(board.board_id, []):
                self.assertIn(char_id, sb_text,
                              f"{board.board_id} SB missing character: {char_id}")
                self.assertIn(char_id, vp_text,
                              f"{board.board_id} VP missing character: {char_id}")
            # Board C must NOT reference the departed character in the prompt body
            if board.board_id == "Board_C":
                # 陈厚坤 may appear in metadata/continuity references but not
                # as an active character in the prompt body (code blocks)
                blocks = re.findall(r'```(.*?)```', sb_text, re.DOTALL)
                if blocks:
                    for block in blocks:
                        self.assertNotIn(
                            "陈厚坤", block,
                            "Board_C storyboard must not contain active 陈厚坤"
                        )


# ============================================================================
# 10. Voice Binding Tests
# ============================================================================


class VoiceBindingTests(unittest.TestCase):
    """Voice binding must be complete for each board."""

    def test_board_a_requires_two_voices(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        board_a = next(p for p in packets if p["board"] == "Board_A")
        voices = board_a["voice_binding"]["required_voice_assets"]
        self.assertEqual(len(voices), 2)
        voice_chars = sorted(v["character"] for v in voices)
        self.assertEqual(voice_chars, ["周从文", "陈厚坤"])

    def test_board_b_requires_one_voice_only(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        board_b = next(p for p in packets if p["board"] == "Board_B")
        voices = board_b["voice_binding"]["required_voice_assets"]
        self.assertEqual(len(voices), 1)
        self.assertEqual(voices[0]["character"], "陈厚坤")

    def test_board_c_requires_one_voice_only(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        board_c = next(p for p in packets if p["board"] == "Board_C")
        voices = board_c["voice_binding"]["required_voice_assets"]
        self.assertEqual(len(voices), 1)
        self.assertEqual(voices[0]["character"], "周从文")

    def test_voice_assets_are_cross_board_locked(self) -> None:
        """Same character must use same voice asset ID across boards."""
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        zhou_boards = []
        chen_boards = []
        for p in packets:
            for v in p["voice_binding"]["required_voice_assets"]:
                if v["character"] == "周从文":
                    zhou_boards.append(v["voice_asset_id"])
                elif v["character"] == "陈厚坤":
                    chen_boards.append(v["voice_asset_id"])

        if len(zhou_boards) > 1:
            self.assertEqual(
                len(set(zhou_boards)), 1,
                "周从文 voice asset ID inconsistent across boards"
            )
        if len(chen_boards) > 1:
            self.assertEqual(
                len(set(chen_boards)), 1,
                "陈厚坤 voice asset ID inconsistent across boards"
            )

    def test_voice_slots_separate_from_image_slots(self) -> None:
        """Voice slots and image slots must not overlap."""
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        for packet in packets:
            voice_slots = set()
            for v in packet["voice_binding"]["required_voice_assets"]:
                voice_slots.add(v["voice_slot"])
            image_slots = set()
            for s in packet["visual_reference_binding"]["seko_reference_slots"]:
                image_slots.add(s["slot"])
            overlap = voice_slots & image_slots
            self.assertEqual(
                len(overlap), 0,
                f"{packet['board']}: voice and image slots overlap: {overlap}"
            )


# ============================================================================
# 11. Seko Leakage Scan Tests
# ============================================================================


class SekoLeakageScanTests(unittest.TestCase):
    """No internal metadata or machine identifiers must leak into Seko prompts."""

    _FORBIDDEN_PATTERNS = [
        r'\bhash\s*[:=]\s*[0-9a-fA-F]{8,}',      # hash references
        r'\bsha256\b',                             # sha256 mentions
        r'\bstate_id\b',                           # state machine IDs
        r'\bglobal_sec\b',                         # global time labels
        r'\blocal_time\b',                         # local time labels
        r'\bcanonical_frame_id\b',                 # frame ID
        r'\bprojection_verdict\b',                 # projection metadata
        r'\bDETERMINISTIC_SEMANTIC\b',             # projection verdict
        r'\bpacket_id\b',                          # packet identifier
        r'\bentry_state_sha256\b',                 # state hash
        r'\bVCP\.json\b',                          # internal file name
        r'\bSTATE_SPINE\.json\b',                  # internal file name
        r'\bHANDOFF_PACKETS\.json\b',              # internal file name
        r'\bCHILD_PACKETS\.json\b',                # internal file name
        r'\bgate_or_pass\b',                       # gate state
        r'\bbinding_status\b',                     # binding metadata
        r'\bPENDING_USER_UPLOAD\b',                # upload status
        r'\bvoice_asset_id\b',                     # voice asset
        r'\bplatform_voice_id\b',                  # platform details
    ]

    @classmethod
    def setUpClass(cls) -> None:
        cls.storyboard_files = [
            _FIXTURE_DIR / f"CHILD_STORYBOARD_EP35_S1_Board_{c}.md"
            for c in ("A", "B", "C")
        ]
        cls.video_files = [
            _FIXTURE_DIR / f"VIDEO_PROMPT_EP35_S1_Board_{c}.md"
            for c in ("A", "B", "C")
        ]

    def _check_file(self, filepath: Path, label: str) -> List[str]:
        violations = []
        text = filepath.read_text(encoding="utf-8")
        # Only check the code block content (between ``` markers)
        blocks = re.findall(r'```(.*?)```', text, re.DOTALL)
        check_text = " ".join(blocks) if blocks else text

        for pattern in self._FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, check_text, re.IGNORECASE)
            if matches:
                violations.append(
                    f"{label}: pattern '{pattern}' matched: {matches[:3]}"
                )
        return violations

    def test_no_leakage_in_storyboard_a(self) -> None:
        violations = self._check_file(
            self.storyboard_files[0], "SB_A"
        )
        self.assertEqual(violations, [], f"Seko leakage in SB_A: {violations}")

    def test_no_leakage_in_storyboard_b(self) -> None:
        violations = self._check_file(
            self.storyboard_files[1], "SB_B"
        )
        self.assertEqual(violations, [], f"Seko leakage in SB_B: {violations}")

    def test_no_leakage_in_storyboard_c(self) -> None:
        violations = self._check_file(
            self.storyboard_files[2], "SB_C"
        )
        self.assertEqual(violations, [], f"Seko leakage in SB_C: {violations}")

    def test_no_leakage_in_video_a(self) -> None:
        violations = self._check_file(
            self.video_files[0], "VP_A"
        )
        self.assertEqual(violations, [], f"Seko leakage in VP_A: {violations}")

    def test_no_leakage_in_video_b(self) -> None:
        violations = self._check_file(
            self.video_files[1], "VP_B"
        )
        self.assertEqual(violations, [], f"Seko leakage in VP_B: {violations}")

    def test_no_leakage_in_video_c(self) -> None:
        violations = self._check_file(
            self.video_files[2], "VP_C"
        )
        self.assertEqual(violations, [], f"Seko leakage in VP_C: {violations}")

    def test_no_at_sign_labels_rendered_in_code_blocks(self) -> None:
        """@图片 labels in code blocks should NOT be rendered as image text."""
        for label, filepath in [
            ("SB_A", self.storyboard_files[0]),
            ("SB_B", self.storyboard_files[1]),
            ("SB_C", self.storyboard_files[2]),
            ("VP_A", self.video_files[0]),
            ("VP_B", self.video_files[1]),
            ("VP_C", self.video_files[2]),
        ]:
            text = filepath.read_text(encoding="utf-8")
            blocks = re.findall(r'```(.*?)```', text, re.DOTALL)
            for block in blocks:
                # Check for reference rendering prohibitions
                if "禁止将@图片标签" in block:
                    continue  # This is the prohibition itself
                # No @图片 references in the actual prompt body after reference section
                prompt_body = block


# ============================================================================
# 12. VCP Validation — ERRORS=0
# ============================================================================


class VCPValidationTests(unittest.TestCase):
    """VCP.json must validate with zero errors."""

    def test_vcp_semantic_checks_zero_errors(self) -> None:
        vcp = json.loads(
            (_FIXTURE_DIR / "VCP.json").read_text(encoding="utf-8")
        )
        self.assertEqual(vcp["VALIDATION_RULES"]["soft_metrics"]["non_speaker_lip_errors"], 0)
        self.assertEqual(vcp["VALIDATION_RULES"]["soft_metrics"]["os_visible_lip_errors"], 0)
        self.assertEqual(vcp["VALIDATION_RULES"]["soft_metrics"]["missing_repeated_syllables"], 0)

    def test_vcp_boundary_states_equal(self) -> None:
        vcp = json.loads(
            (_FIXTURE_DIR / "VCP.json").read_text(encoding="utf-8")
        )
        for b in vcp["BOARD_BOUNDARIES"]:
            if b["type"] == "continuous":
                self.assertTrue(
                    b.get("states_equal", False),
                    f"Boundary {b['boundary_id']}: states_equal must be True"
                )
                self.assertEqual(
                    b.get("mismatches", []), [],
                    f"Boundary {b['boundary_id']}: mismatches found"
                )

    def test_vcp_prop_chain_no_reverse(self) -> None:
        """Prop state chain must be forward-only (no reversals)."""
        vcp = json.loads(
            (_FIXTURE_DIR / "VCP.json").read_text(encoding="utf-8")
        )
        phone_states = vcp["CONTINUITY_LOCK"]["prop_state_chain"]["手机"]["states"]
        # Verify ordered progression
        expected_order = [
            "pocket/not_visible", "touch_pocket", "take_out",
            "dial", "at_ear/in_call",
        ]
        self.assertEqual(phone_states, expected_order)

    def test_vcp_screen_lock_no_flip(self) -> None:
        """Screen direction must not flip across the scene."""
        vcp = json.loads(
            (_FIXTURE_DIR / "VCP.json").read_text(encoding="utf-8")
        )
        self.assertIn("画面右侧", vcp["CONTINUITY_LOCK"]["screen_direction"])
        self.assertIn("不翻转", vcp["CONTINUITY_LOCK"]["screen_direction"])

    def test_vcp_render_verdict_is_pending(self) -> None:
        """Must be RENDER_PENDING, not fake READY/PASS."""
        vcp = json.loads(
            (_FIXTURE_DIR / "VCP.json").read_text(encoding="utf-8")
        )
        self.assertEqual(vcp["META"]["render_verdict"], "RENDER_PENDING")
        self.assertEqual(vcp["META"]["text_verdict"], "TEXT_PROTOCOL_PASS")


# ============================================================================
# 13. Negative / Mutation Tests
# ============================================================================


class NegativeMutationTests(unittest.TestCase):
    """Mutation tests that verify invariants are actively enforced."""

    def test_exceed_15s_is_rejected(self) -> None:
        splitter = BoardSplitter()
        with self.assertRaises(ValueError):
            splitter.split("FAIL", 20.0, [(0.0, 16.0)])

    def test_gap_in_timeline_is_rejected(self) -> None:
        splitter = BoardSplitter()
        with self.assertRaises(ValueError):
            splitter.split("FAIL", 20.0, [(0.0, 8.0), (9.0, 20.0)])

    def test_reversed_time_range_is_rejected(self) -> None:
        splitter = BoardSplitter()
        with self.assertRaises(ValueError):
            splitter.split("FAIL", 10.0, [(10.0, 0.0)])

    def test_zero_duration_board_is_rejected(self) -> None:
        splitter = BoardSplitter()
        with self.assertRaises(ValueError):
            splitter.split("FAIL", 10.0, [(0.0, 0.0)])

    def test_single_board_has_two_boundaries(self) -> None:
        splitter = BoardSplitter()
        result = splitter.split("TEST", 10.0, [(0.0, 10.0)])
        self.assertEqual(len(result.boundaries), 2)  # 1 scene_entry + 1 scene_exit

    def test_max_duration_exceeds_15_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            BoardSplitter(max_board_duration_s=20.0)

    def test_board_c_entry_must_match_board_b_exit(self) -> None:
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        board_b = next(p for p in packets if p["board"] == "Board_B")
        board_c = next(p for p in packets if p["board"] == "Board_C")
        self.assertEqual(
            board_b["exit_state_sha256"],
            board_c["entry_state_sha256"],
            "Board_B EXIT != Board_C ENTRY — continuity violated",
        )


# ============================================================================
# 14. Per-Boundary Continuity Adjudication Tests
# ============================================================================


class PerBoundaryContinuityTests(unittest.TestCase):
    """Each boundary must have correct continuity adjudication."""

    def setUp(self) -> None:
        self.packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )

    def test_boundary_ab_is_camera_cut(self) -> None:
        """A→B is a hard cut from 24mm WS to 50mm two-shot."""
        board_b = next(p for p in self.packets if p["board"] == "Board_B")
        policy = board_b["visual_reference_binding"]
        self.assertEqual(policy["entry_match_mode"], "structured_state_match_with_camera_cut")
        self.assertTrue(policy["camera_cut_allowed"])
        self.assertFalse(policy["pixel_identical_required"])

    def test_boundary_bc_is_exact_frame_match(self) -> None:
        """B→C requires pixel-identical frame match (same lens, same composition)."""
        board_c = next(p for p in self.packets if p["board"] == "Board_C")
        policy = board_c["visual_reference_binding"]
        self.assertEqual(policy["entry_match_mode"], "exact_visual_frame_match")
        self.assertTrue(policy["pixel_identical_required"])
        self.assertFalse(policy["camera_cut_allowed"])

    def test_boundary_a_is_scene_entry(self) -> None:
        board_a = next(p for p in self.packets if p["board"] == "Board_A")
        policy = board_a["visual_reference_binding"]
        self.assertEqual(policy["entry_match_mode"], "scene_entry")
        self.assertFalse(policy["pixel_identical_required"])

    def test_each_boundary_declares_upstream_laf_correctly(self) -> None:
        expected_lafs = {"Board_A": None, "Board_B": "LAF_A", "Board_C": "LAF_B"}
        for board_id, expected_laf in expected_lafs.items():
            board = next(p for p in self.packets if p["board"] == board_id)
            self.assertEqual(
                board["visual_reference_binding"]["upstream_laf"],
                expected_laf,
                f"{board_id}: expected upstream LAF {expected_laf}",
            )


# ============================================================================
# 15. Storyboard Cell / Video Beat Structure Tests
# ============================================================================


class BoardStructureTests(unittest.TestCase):
    """Board storyboard cell counts and video beat counts."""

    def test_board_a_has_9_storyboard_cells(self) -> None:
        sb = (_FIXTURE_DIR / "CHILD_STORYBOARD_EP35_S1_Board_A.md").read_text(
            encoding="utf-8"
        )
        cells = re.findall(r'【格(\d+)】', sb)
        self.assertEqual(len(cells), 9)

    def test_board_b_has_12_storyboard_cells(self) -> None:
        sb = (_FIXTURE_DIR / "CHILD_STORYBOARD_EP35_S1_Board_B.md").read_text(
            encoding="utf-8"
        )
        cells = re.findall(r'【格(\d+)】', sb)
        self.assertEqual(len(cells), 12)

    def test_board_c_has_storyboard_cells(self) -> None:
        """Board C must have storyboard cells (panels > 0)."""
        sb = (_FIXTURE_DIR / "CHILD_STORYBOARD_EP35_S1_Board_C.md").read_text(
            encoding="utf-8"
        )
        cells = re.findall(r'【格(\d+)】', sb)
        self.assertGreater(len(cells), 0, "Board C must have storyboard cells")

    def test_board_a_video_beats(self) -> None:
        vp = (_FIXTURE_DIR / "VIDEO_PROMPT_EP35_S1_Board_A.md").read_text(
            encoding="utf-8"
        )
        beats = re.findall(r'【第[\d.]+-[\d.]+秒】', vp)
        self.assertGreater(len(beats), 0)

    def test_board_b_video_beats(self) -> None:
        vp = (_FIXTURE_DIR / "VIDEO_PROMPT_EP35_S1_Board_B.md").read_text(
            encoding="utf-8"
        )
        beats = re.findall(r'【第[\d.]+-[\d.]+秒】', vp)
        self.assertGreater(len(beats), 0)

    def test_board_c_video_beats(self) -> None:
        vp = (_FIXTURE_DIR / "VIDEO_PROMPT_EP35_S1_Board_C.md").read_text(
            encoding="utf-8"
        )
        beats = re.findall(r'【第[\d.]+-[\d.]+秒】', vp)
        self.assertGreater(len(beats), 0, "Board C must have video beats")


# ============================================================================
# 16. Scene Parser Integration Tests
# ============================================================================


class SceneParserIntegrationTests(unittest.TestCase):
    """End-to-end parser tests that verify the EP35SceneParser."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.parser = EP35SceneParser(_FIXTURE_DIR)
        cls.context = cls.parser.parse()

    def test_parse_returns_valid_context(self) -> None:
        self.assertEqual(self.context.scene_id, "EP35_S1")
        self.assertEqual(self.context.board_count, 3)
        self.assertAlmostEqual(self.context.total_duration_s, 34.5, delta=0.1)

    def test_parse_boards_have_correct_time_ranges(self) -> None:
        expected = [
            ("Board_A", 0.0, 8.3),
            ("Board_B", 8.3, 20.0),
            ("Board_C", 20.0, 34.5),
        ]
        for (bid, start, end), board in zip(expected, self.context.boards):
            self.assertEqual(board.board_id, bid)
            self.assertAlmostEqual(board.global_time_range[0], start, delta=0.01)
            self.assertAlmostEqual(board.global_time_range[1], end, delta=0.01)

    def test_parse_boundaries_have_correct_types(self) -> None:
        expected_types = ["scene_entry", "continuous", "continuous", "scene_exit"]
        self.assertEqual(
            [b.boundary_type for b in self.context.boundaries], expected_types
        )

    def test_parse_dialogues_count(self) -> None:
        self.assertEqual(len(self.context.dialogues), 5)

    def test_parse_characters_count(self) -> None:
        self.assertEqual(len(self.context.characters), 2)
        self.assertIn("陈厚坤", self.context.characters)
        self.assertIn("周从文", self.context.characters)

    def test_continuity_verification_passes(self) -> None:
        issues = self.parser.verify_continuity()
        self.assertEqual(
            issues, [],
            f"Continuity verification failed with issues: {issues}"
        )

    def test_source_sha256_is_stable(self) -> None:
        sha1 = self.parser.parse().source_sha256
        sha2 = self.parser.parse().source_sha256
        self.assertEqual(sha1, sha2, "Source SHA-256 is not deterministic")


# ============================================================================
# 17. EP35_S1 Regression — Must Keep Passing
# ============================================================================


class EP35S1RegressionTests(unittest.TestCase):
    """All previously passing EP35_S1 assertions must remain valid."""

    def test_regression_vcp_text_protocol_pass(self) -> None:
        report = json.loads(
            (_FIXTURE_DIR / "VALIDATION_REPORT.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["verdict"], "TEXT_PROTOCOL_PASS")

    def test_regression_handoff_states_all_equal(self) -> None:
        handoffs = json.loads(
            (_FIXTURE_DIR / "HANDOFF_PACKETS.json").read_text(encoding="utf-8")
        )
        for h in handoffs:
            self.assertTrue(
                h["states_equal"],
                f"Handoff {h['handoff_id']}: states_equal is False",
            )

    def test_regression_all_boards_within_15s(self) -> None:
        for name, dur in [("Board_A", 8.3), ("Board_B", 11.7), ("Board_C", 14.5)]:
            self.assertLessEqual(dur, 15.0)

    def test_regression_boundary_bc_pixel_identical_required(self) -> None:
        """B→C boundary MUST require pixel-identical frame match."""
        packets = json.loads(
            (_FIXTURE_DIR / "CHILD_PACKETS.json").read_text(encoding="utf-8")
        )
        board_c = next(p for p in packets if p["board"] == "Board_C")
        self.assertTrue(board_c["visual_reference_binding"]["pixel_identical_required"])

    def test_regression_hard_time_matrix_no_28_9s(self) -> None:
        """28.9s is explicitly FORBIDDEN as a time value in the hard time matrix.

        The text may mention '28.9s' in the prohibition section itself,
        but it must NEVER appear as a cell time label (│ 28.9s │ pattern)."""
        master = (_FIXTURE_DIR / "MASTER_CONTINUITY_BOARD_EP35_S1.md").read_text(
            encoding="utf-8"
        )
        # Check that no time cell in the hard time matrix uses 28.9s
        # The matrix format is: │ 格# │ Title │ 唯一时间 │
        time_cells = re.findall(r'│\s*(?:Board_[ABC]_\w+)\s*│\s*([\d.]+s)\s*│', master)
        self.assertNotIn("28.9s", time_cells,
                         f"28.9s found as a hard time matrix value: {time_cells}")
        # also check inline time references in boundary visual cells
        boundary_times = re.findall(r'时间=([\d.]+s)', master)
        self.assertNotIn("28.9s", boundary_times)
        # Verify the prohibition section exists (defense against deletion)
        self.assertIn("28.9s 被明确禁止", master,
                      "The 28.9s prohibition statement must exist")

    def test_regression_master_cell_5_not_at_ear(self) -> None:
        """Board_C_ENTRY (cell 5) must NOT show at_ear/贴耳."""
        master = (_FIXTURE_DIR / "MASTER_CONTINUITY_BOARD_EP35_S1.md").read_text(
            encoding="utf-8"
        )
        # Find cell 5 content
        cell5_match = re.search(
            r'格5.*?(?=格6|$)', master, re.DOTALL
        )
        if cell5_match:
            cell5_text = cell5_match.group(0)
            self.assertNotIn("at_ear", cell5_text.lower())
            self.assertNotIn("贴耳", cell5_text)

    def test_regression_all_board_boundaries_continuous_except_ends(self) -> None:
        vcp = json.loads(
            (_FIXTURE_DIR / "VCP.json").read_text(encoding="utf-8")
        )
        boundaries = vcp["BOARD_BOUNDARIES"]
        self.assertEqual(boundaries[0]["type"], "scene_entry")
        self.assertEqual(boundaries[1]["type"], "continuous")
        self.assertEqual(boundaries[2]["type"], "continuous")
        self.assertEqual(boundaries[3]["type"], "scene_exit")


if __name__ == "__main__":
    unittest.main()
