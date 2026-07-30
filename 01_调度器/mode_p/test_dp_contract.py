"""Tests for Manifest-bound DP issue feedback and anti-stall identity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dp_contract import (
    DP_READY_SENTENCE,
    DpContractError,
    detect_stall,
    manifest_shot_ids,
    manifest_shot_ids_many,
    parse_dp_feedback,
    validate_dp_contract,
)


class ContractTests(unittest.TestCase):
    def test_explicit_missing_input_blocks_without_ready(self) -> None:
        feedback = parse_dp_feedback(
            "DP_INPUT_BLOCKED: Current Storyboard file is absent from the bound packet."
        )
        valid, problems = validate_dp_contract(feedback, {"S1-1"})
        self.assertTrue(valid, problems)
        self.assertEqual(feedback.status, "blocked")
        self.assertFalse(feedback.is_ready)

    def test_blocked_cannot_be_mixed_with_ready(self) -> None:
        feedback = parse_dp_feedback(
            "DP_INPUT_BLOCKED: Storyboard is absent.\n" + DP_READY_SENTENCE
        )
        valid, _ = validate_dp_contract(feedback, {"S1-1"})
        self.assertFalse(valid)

    def test_scene_specific_ready_evidence(self) -> None:
        feedback = parse_dp_feedback(DP_READY_SENTENCE)
        self.assertTrue(feedback.is_ready)
        self.assertEqual(validate_dp_contract(feedback, {"S1-1"}), (True, []))
        generic = parse_dp_feedback("READY S1: Shot S1-1 looks good.")
        self.assertFalse(validate_dp_contract(generic, {"S1-1"})[0])

    def test_ready_requires_every_scene_once_and_current_shots(self) -> None:
        feedback = parse_dp_feedback(
            "READY S1: Shot S1-1 的入口边界和人物位置一致，机位路径位于房间内。\n"
            "READY S2: Shot S2-2 的主光方向在窗户位置有明确空间来源。"
        )
        valid, problems = validate_dp_contract(feedback, {"S1-1", "S2-1", "S2-2"})
        self.assertTrue(valid, problems)
        missing = parse_dp_feedback(
            "READY S1: Shot S1-1 的入口边界和人物位置一致，机位路径位于房间内。"
        )
        self.assertFalse(validate_dp_contract(missing, {"S1-1", "S2-1"})[0])

    def test_ready_accepts_real_review_vocabulary_and_decimal_time_ranges(self) -> None:
        feedback = parse_dp_feedback(
            "READY scene_002: scene_002-2 的蒸汽光变具有物理锚点，时间线状态连续。\n"
            "READY scene_004: scene_004-2 的动作在2.0-3.0s完整可见，边界方向一致。"
        )

        valid, problems = validate_dp_contract(
            feedback, {"scene_002-2", "scene_004-2"}
        )

        self.assertTrue(valid, problems)

    def test_ready_and_issue_lines_cannot_mix(self) -> None:
        mixed = parse_dp_feedback(
            DP_READY_SENTENCE + "\nS1-1: camera_path — 路径穿过桌面。"
        )
        self.assertFalse(validate_dp_contract(mixed, {"S1-1"})[0])

    def test_natural_issue_lines_parse_with_optional_bullets(self) -> None:
        feedback = parse_dp_feedback(
            "- EP14_S1-2: camera_path — 推进轨迹会穿过桌面。\n"
            "Shot EP14_S1-4: light_source - 主光在空间中没有物理来源。"
        )
        valid, problems = validate_dp_contract(
            feedback, {"EP14_S1-2", "EP14_S1-4"}
        )
        self.assertTrue(valid, problems)
        self.assertEqual(len(feedback.issues), 2)

    def test_empty_unparseable_unknown_field_and_unknown_shot_fail(self) -> None:
        self.assertFalse(validate_dp_contract(parse_dp_feedback(""))[0])
        self.assertFalse(validate_dp_contract(parse_dp_feedback("Looks fine except camera."))[0])
        unknown_field = parse_dp_feedback("S1-1: aesthetic_opinion — I dislike it.")
        self.assertFalse(validate_dp_contract(unknown_field, {"S1-1"})[0])
        unknown_shot = parse_dp_feedback("S1-9: camera_path — blocked.")
        self.assertFalse(validate_dp_contract(unknown_shot, {"S1-1"})[0])

    def test_long_detail_and_duplicate_identity_fail_without_silent_truncation(self) -> None:
        long_feedback = parse_dp_feedback("S1-1: camera_path — " + "x" * 241)
        self.assertFalse(validate_dp_contract(long_feedback, {"S1-1"})[0])
        self.assertEqual(len(long_feedback.issues[0].detail), 241)
        duplicate = parse_dp_feedback(
            "S1-1: camera_path — blocked.\nS1-1: camera_path — still blocked."
        )
        self.assertFalse(validate_dp_contract(duplicate, {"S1-1"})[0])

    def test_no_false_hard_face_limit_field(self) -> None:
        from dp_contract import DP_VALID_FIELDS
        self.assertNotIn("face_count", DP_VALID_FIELDS)
        self.assertIn("composition_focus", DP_VALID_FIELDS)
        self.assertIn("performance_visibility", DP_VALID_FIELDS)


class FingerprintTests(unittest.TestCase):
    def test_wording_changes_do_not_evade_same_master_stall(self) -> None:
        first = parse_dp_feedback("S1-1: camera_path — blocked by desk.")
        second = parse_dp_feedback("S1-1: camera_path — desk intersects the path.")
        master = "a" * 64
        self.assertEqual(first.fingerprint(master), second.fingerprint(master))

    def test_master_change_prevents_false_stall(self) -> None:
        feedback = parse_dp_feedback("S1-1: camera_path — blocked.")
        self.assertNotEqual(feedback.fingerprint("a" * 64), feedback.fingerprint("b" * 64))

    def test_issue_order_is_irrelevant_but_issue_identity_is_not(self) -> None:
        first = parse_dp_feedback(
            "S1-1: camera_path — blocked.\nS1-2: light_source — unanchored."
        )
        second = parse_dp_feedback(
            "S1-2: light_source — changed words.\nS1-1: camera_path — changed words."
        )
        different = parse_dp_feedback("S1-1: composition_focus — unclear.")
        master = "c" * 64
        self.assertEqual(first.fingerprint(master), second.fingerprint(master))
        self.assertNotEqual(first.fingerprint(master), different.fingerprint(master))

    def test_detect_stall_and_invalid_hashes(self) -> None:
        fingerprint = parse_dp_feedback("S1-1: camera_path — blocked.").fingerprint("d" * 64)
        self.assertTrue(detect_stall([fingerprint], fingerprint))
        with self.assertRaises(DpContractError):
            detect_stall(["bad"], fingerprint)


class ManifestTests(unittest.TestCase):
    def test_manifest_shot_binding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dp_manifest_") as temp:
            path = Path(temp) / "manifest.json"
            path.write_text(json.dumps({
                "shots": [{"shot_id": "S1-1"}, {"shot_id": "S1-2"}]
            }), encoding="utf-8")
            self.assertEqual(manifest_shot_ids(path), {"S1-1", "S1-2"})
            path.write_text(json.dumps({
                "shots": [{"shot_id": "S1-1"}, {"shot_id": "S1-1"}]
            }), encoding="utf-8")
            with self.assertRaises(DpContractError):
                manifest_shot_ids(path)

    def test_manifest_union_is_disjoint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dp_manifest_union_") as temp:
            root = Path(temp)
            first = root / "first.json"
            second = root / "second.json"
            first.write_text(json.dumps({"shots": [{"shot_id": "S1-1"}]}), encoding="utf-8")
            second.write_text(json.dumps({"shots": [{"shot_id": "S2-1"}]}), encoding="utf-8")
            self.assertEqual(
                manifest_shot_ids_many([first, second]), {"S1-1", "S2-1"}
            )
            second.write_text(json.dumps({"shots": [{"shot_id": "S1-1"}]}), encoding="utf-8")
            with self.assertRaises(DpContractError):
                manifest_shot_ids_many([first, second])


if __name__ == "__main__":
    unittest.main()
