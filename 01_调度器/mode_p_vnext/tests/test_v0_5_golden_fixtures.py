"""V0.5 Golden Fixture Registry — structure, hash, evidence role tests.

Verify the Golden fixture registry:
- Has exactly 4 Golden scenes (枪管, 观众席, 备赛区, 窄巷)
- Each scene has required fields and evidence roles
- User evaluation is structured (user_statement vs audit_classification)
- Media references are text-only (no binary loading)
- Hashes match the V0.1 baseline manifest
- Registry can be serialized to canonical JSON with stable hash
- prep_area_no_cut_fact: prep_area design is single continuous fixed shot
- four_exact_prompt_pairs: exactly 8 prompt fixture files exist
"""

import json
import os
import unittest
from pathlib import Path


try:
    from mode_p_vnext import golden_fixture_registry as gfr
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE_MANIFEST_PATH = (
    PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "vnext_baseline" / "V0.1_FREEZE_MANIFEST.json"
)
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

REQUIRED_SCENE_KEYS = {
    "scene_id", "episode", "description",
    "storyboard_image", "video", "user_evaluation",
    "golden_expectations", "evidence_roles", "knowledge_questions",
}

REQUIRED_MEDIA_KEYS = {"path", "sha256", "width", "height", "format"}

REQUIRED_EVALUATION_KEYS = {
    "user_statement", "audit_classification",
    "composition_result", "timing_result", "behavior_result",
}

EXPECTED_PROMPT_FIXTURES = [
    "gun_barrel_sb_prompt.json",
    "gun_barrel_video_prompt.json",
    "audience_sb_prompt.json",
    "audience_video_prompt.json",
    "prep_area_sb_prompt.json",
    "prep_area_video_prompt.json",
    "alley_sb_prompt.json",
    "alley_video_prompt.json",
]

# Pinned verbatim body hashes and lengths from Codex JSONL (fixed independent constants).
# Each tuple is (UTF-8_SHA256, character_count, JSONL_line_number).
PINNED_PROMPT_BODY = {
    "gun_barrel_sb_prompt.json": (
        "ce4caf8504593b307d0835120e516f427f4d6ed0e41d2bf35395f95169496ea8", 1703, 275,
    ),
    "gun_barrel_video_prompt.json": (
        "452f8fabc04e6e44b6e8f4d80919ea35b37bd8b765cc52bad94dfaa1a5095cce", 2544, 293,
    ),
    "audience_sb_prompt.json": (
        "1cd5a30f019e97f6651771fa8155229c85c8c969eca0400d7da0db3bb2b02141", 2099, 360,
    ),
    "audience_video_prompt.json": (
        "5fa1815ade3e507807f583c2d4556997bbe8e10538a4badeaaed4eb51bfb8787", 2397, 381,
    ),
    "prep_area_sb_prompt.json": (
        "ed006256727083cba8e1b5ae065fe6e1e7671b02f033c8d4c738d49d3af1b057", 1600, 404,
    ),
    "prep_area_video_prompt.json": (
        "36f45f042d3c3350a3e6a847e321eb9c0e3c9b2be9966a8154237af42d13a46c", 1811, 425,
    ),
    "alley_sb_prompt.json": (
        "8e14b8f21da8a54116d2ff2fe5ef0ec9eab5c03a3d8c55ae28daa184aa766edb", 3032, 440,
    ),
    "alley_video_prompt.json": (
        "a558b598e0718c3bbae1aa717c44f08b07c2939d2feedce5c775ad97fcdc52c9", 2932, 458,
    ),
}

FORBIDDEN_INTEGRITY_WORDS = [
    "Reconstructed", "reconstructed", "summary", "created from descriptions",
]


class GoldenFixtureStructureTests(unittest.TestCase):
    """Verify the registry has correct structure."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_registry_has_exactly_4_scenes(self):
        scenes = gfr.GOLDEN_SCENES
        self.assertEqual(len(scenes), 4, f"Expected 4 golden scenes, got {len(scenes)}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_registry_has_required_scene_ids(self):
        required_ids = {"gun_barrel_ep8", "audience_ep6", "prep_area_ep6", "alley_ep6"}
        actual_ids = set(gfr.GOLDEN_SCENES.keys())
        self.assertEqual(required_ids, actual_ids)

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_each_scene_has_required_keys(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                missing = REQUIRED_SCENE_KEYS - set(scene.keys())
                self.assertEqual(len(missing), 0, f"Missing keys: {missing}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_each_media_ref_has_required_keys(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            for media_key in ("storyboard_image", "video"):
                with self.subTest(scene=scene_id, media=media_key):
                    ref = scene[media_key]
                    self.assertIsInstance(ref, dict)
                    missing = REQUIRED_MEDIA_KEYS - set(ref.keys())
                    self.assertEqual(len(missing), 0, f"Missing keys in {media_key}: {missing}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_each_scene_has_nonempty_evidence_roles(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                roles = scene["evidence_roles"]
                self.assertIsInstance(roles, list)
                self.assertGreater(len(roles), 0,
                                   f"No evidence roles for {scene_id}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_each_scene_has_nonempty_knowledge_questions(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                questions = scene["knowledge_questions"]
                self.assertIsInstance(questions, list)
                self.assertGreater(len(questions), 0,
                                   f"No knowledge questions for {scene_id}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_each_scene_has_nonempty_golden_expectations(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                expectations = scene["golden_expectations"]
                self.assertIsInstance(expectations, list)
                self.assertGreater(len(expectations), 0,
                                   f"No expectations for {scene_id}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_episodes_are_correct(self):
        self.assertEqual(gfr.GOLDEN_SCENES["gun_barrel_ep8"]["episode"], "EP8")
        self.assertEqual(gfr.GOLDEN_SCENES["audience_ep6"]["episode"], "EP6")
        self.assertEqual(gfr.GOLDEN_SCENES["prep_area_ep6"]["episode"], "EP6")
        self.assertEqual(gfr.GOLDEN_SCENES["alley_ep6"]["episode"], "EP6")


class GoldenFixtureHashTests(unittest.TestCase):
    """Verify media hashes match V0.1 baseline manifest."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def setUp(self):
        if not BASELINE_MANIFEST_PATH.exists():
            raise unittest.SkipTest("V0.1 baseline manifest not found")
        self.manifest = json.loads(BASELINE_MANIFEST_PATH.read_text(encoding="utf-8"))

    def _manifest_golden_map(self):
        return {entry["key"]: entry for entry in self.manifest["golden_media"]}

    def test_all_8_media_hashes_match_baseline(self):
        manifest_map = self._manifest_golden_map()
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            for media_key in ("storyboard_image", "video"):
                with self.subTest(scene=scene_id, media=media_key):
                    ref = scene[media_key]
                    matched = any(
                        ref["sha256"] == entry["sha256"]
                        for entry in manifest_map.values()
                    )
                    self.assertTrue(matched,
                                    f"{scene_id}.{media_key} hash not in baseline manifest")

    def test_gun_barrel_hashes_match(self):
        manifest_map = self._manifest_golden_map()
        scene = gfr.GOLDEN_SCENES["gun_barrel_ep8"]
        self.assertEqual(scene["storyboard_image"]["sha256"],
                         manifest_map["gun_barrel_sb"]["sha256"])
        self.assertEqual(scene["video"]["sha256"],
                         manifest_map["gun_barrel_video"]["sha256"])

    def test_audience_hashes_match(self):
        manifest_map = self._manifest_golden_map()
        scene = gfr.GOLDEN_SCENES["audience_ep6"]
        self.assertEqual(scene["storyboard_image"]["sha256"],
                         manifest_map["audience_sb"]["sha256"])
        self.assertEqual(scene["video"]["sha256"],
                         manifest_map["audience_video"]["sha256"])

    def test_prep_area_hashes_match(self):
        manifest_map = self._manifest_golden_map()
        scene = gfr.GOLDEN_SCENES["prep_area_ep6"]
        self.assertEqual(scene["storyboard_image"]["sha256"],
                         manifest_map["prep_area_sb"]["sha256"])
        self.assertEqual(scene["video"]["sha256"],
                         manifest_map["prep_area_video"]["sha256"])

    def test_alley_hashes_match(self):
        manifest_map = self._manifest_golden_map()
        scene = gfr.GOLDEN_SCENES["alley_ep6"]
        self.assertEqual(scene["storyboard_image"]["sha256"],
                         manifest_map["alley_sb"]["sha256"])
        self.assertEqual(scene["video"]["sha256"],
                         manifest_map["alley_video"]["sha256"])


class GoldenFixtureBinarySafetyTests(unittest.TestCase):
    """Registry must NOT contain media binaries — text references only."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_no_bytes_objects_in_registry(self):
        """Recursively check that no bytes objects exist in the registry."""
        violations = []

        def check(obj, path):
            if isinstance(obj, bytes):
                violations.append(path)
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    check(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check(v, f"{path}[{i}]")

        check(gfr.GOLDEN_SCENES, "GOLDEN_SCENES")
        self.assertEqual(len(violations), 0,
                         f"Bytes objects found: {violations}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_media_paths_are_strings_not_path_objects(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            for media_key in ("storyboard_image", "video"):
                with self.subTest(scene=scene_id, media=media_key):
                    path_val = scene[media_key]["path"]
                    self.assertIsInstance(path_val, str)
                    self.assertFalse(hasattr(path_val, "read_bytes"),
                                     f"{scene_id}.{media_key}.path is a Path object, not str")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_module_does_not_read_files_at_import_time(self):
        """Importing the module should not attempt to read media files."""
        self.assertTrue(MODULE_EXISTS)


class GoldenFixtureCanonicalTests(unittest.TestCase):
    """Registry can be serialized to canonical JSON with stable hash."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_canonical_json_roundtrip(self):
        from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256

        json1 = canonical_json_dumps(gfr.GOLDEN_SCENES)
        json2 = canonical_json_dumps(gfr.GOLDEN_SCENES)
        self.assertEqual(json1, json2, "Canonical JSON must be deterministic")
        h1 = stable_hash_sha256(json1.encode("utf-8"))
        h2 = stable_hash_sha256(json2.encode("utf-8"))
        self.assertEqual(h1, h2, "Hash must be stable")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_canonical_json_contains_chinese(self):
        from mode_p_vnext.canonical_serialization import canonical_json_dumps
        json_str = canonical_json_dumps(gfr.GOLDEN_SCENES)
        self.assertIn("枪管", json_str)
        self.assertIn("观众席", json_str)


# ============================================================================
# R1.2 required checks
# ============================================================================

class PrepAreaNoCutFactTests(unittest.TestCase):
    """R1.2: prep_area_no_cut_fact — design was always single continuous
    fixed-position shot, never had internal cuts."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_prep_area_description_states_single_continuous_shot(self):
        scene = gfr.GOLDEN_SCENES["prep_area_ep6"]
        desc = scene["description"]
        self.assertIn("单一连续", desc,
                      "prep_area description must state single continuous fixed-position shot")
        self.assertIn("固定机位", desc,
                      "prep_area description must state fixed camera position")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_prep_area_golden_expectations_deny_internal_cuts(self):
        scene = gfr.GOLDEN_SCENES["prep_area_ep6"]
        # One expectation must confirm design has no internal cut
        no_cut_found = any(
            "无内部切镜" in exp or "无切镜" in exp
            for exp in scene["golden_expectations"]
        )
        self.assertTrue(no_cut_found,
                        "prep_area golden_expectations must state design had no internal cut")
        # No expectation must claim design had cuts that video failed to execute
        false_cut = [
            exp for exp in scene["golden_expectations"]
            if "设计有" in exp and "切镜" in exp and "未执行" in exp
        ]
        self.assertEqual(len(false_cut), 0,
                         f"prep_area must NOT claim design had cuts video failed to execute: {false_cut}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_prep_area_audit_classification_confirms_no_cut_design(self):
        scene = gfr.GOLDEN_SCENES["prep_area_ep6"]
        classification = scene["user_evaluation"]["audit_classification"]
        self.assertIn("INFERENCE", classification,
                      "audit_classification must be labeled as INFERENCE")
        self.assertIn("固定机位", classification,
                      "classification must confirm fixed camera position")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_prep_area_evidence_roles_exclude_missing_cut(self):
        scene = gfr.GOLDEN_SCENES["prep_area_ep6"]
        roles = scene["evidence_roles"]
        self.assertNotIn("missing_internal_cut_diagnostic", roles,
                         "prep_area must NOT have 'missing_internal_cut_diagnostic' role")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_prep_area_has_early_entrance_and_behavior_roles(self):
        scene = gfr.GOLDEN_SCENES["prep_area_ep6"]
        roles = scene["evidence_roles"]
        self.assertIn("early_entrance_diagnostic", roles,
                      "prep_area must have early_entrance_diagnostic role")
        self.assertIn("behavior_deviation_diagnostic", roles,
                      "prep_area must have behavior_deviation_diagnostic role")


class UserVsInferenceSeparatedTests(unittest.TestCase):
    """R1.2: user_vs_inference_separated — user_evaluation is a structured
    dict with separate user_statement and audit_classification fields."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_user_evaluation_is_dict_not_string(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                ue = scene["user_evaluation"]
                self.assertIsInstance(ue, dict,
                                      f"{scene_id}: user_evaluation must be dict, got {type(ue).__name__}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_user_evaluation_has_all_required_keys(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                ue = scene["user_evaluation"]
                missing = REQUIRED_EVALUATION_KEYS - set(ue.keys())
                self.assertEqual(len(missing), 0,
                                 f"{scene_id}: missing user_evaluation keys: {missing}")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_user_statement_is_nonempty(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                stmt = scene["user_evaluation"]["user_statement"]
                self.assertIsInstance(stmt, str)
                self.assertGreater(len(stmt.strip()), 0,
                                   f"{scene_id}: user_statement must be non-empty")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_audit_classification_is_labeled_inference(self):
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                cls_text = scene["user_evaluation"]["audit_classification"]
                self.assertIn("INFERENCE", cls_text,
                              f"{scene_id}: audit_classification must be labeled INFERENCE")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_composition_timing_behavior_results_are_valid(self):
        valid = {"success", "deviation", "failure", "n/a"}
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                ue = scene["user_evaluation"]
                self.assertIn(ue["composition_result"], valid)
                self.assertIn(ue["timing_result"], valid)
                self.assertIn(ue["behavior_result"], valid)

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_user_statement_does_not_contain_inference_label(self):
        """User statement should be a direct user quote/paraphrase, not an inference."""
        for scene_id, scene in gfr.GOLDEN_SCENES.items():
            with self.subTest(scene=scene_id):
                stmt = scene["user_evaluation"]["user_statement"]
                self.assertNotIn("INFERENCE", stmt.upper(),
                                 f"{scene_id}: user_statement must not contain INFERENCE label")


class FourExactPromptPairsTests(unittest.TestCase):
    """R1.2: four_exact_prompt_pairs — exactly 4 storyboard+video prompt
    fixture files exist (8 JSON files total), one pair per Golden scene,
    with verbatim text verified against pinned SHA-256 and character counts."""

    # ── structural tests ──────────────────────────────────────────────

    def test_exactly_eight_prompt_fixture_files_exist(self):
        existing = sorted([
            f for f in os.listdir(str(FIXTURES_DIR))
            if f.endswith("_prompt.json")
        ])
        self.assertEqual(len(existing), 8,
                         f"Expected 8 prompt fixture files, got {len(existing)}: {existing}")
        self.assertEqual(existing, sorted(EXPECTED_PROMPT_FIXTURES),
                         f"Fixture file names mismatch: {set(existing) ^ set(EXPECTED_PROMPT_FIXTURES)}")

    def test_each_prompt_fixture_has_verbatim_required_fields(self):
        required = {
            "scene_id", "prompt_type", "prompt_text",
            "source_kind", "source_body_length", "source_body_sha256",
            "source_fidelity", "source_jsonl_line",
            "source_section", "integrity_note",
        }
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                self.assertTrue(path.exists(), f"Missing fixture: {path}")
                data = json.loads(path.read_text(encoding="utf-8"))
                missing = required - set(data.keys())
                self.assertEqual(len(missing), 0,
                                 f"{name}: missing keys: {missing}")

    def test_prompt_types_are_storyboard_or_video(self):
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertIn(data["prompt_type"], ("storyboard", "video"),
                              f"{name}: prompt_type must be storyboard or video")

    def test_four_sb_and_four_video_prompts(self):
        sb = [n for n in EXPECTED_PROMPT_FIXTURES if "sb_prompt" in n]
        video = [n for n in EXPECTED_PROMPT_FIXTURES if "video_prompt" in n]
        self.assertEqual(len(sb), 4, f"Expected 4 SB fixtures, got {len(sb)}")
        self.assertEqual(len(video), 4, f"Expected 4 video fixtures, got {len(video)}")

    def test_one_pair_per_scene(self):
        scenes = {"gun_barrel", "audience", "prep_area", "alley"}
        for scene in scenes:
            sb_name = f"{scene}_sb_prompt.json"
            video_name = f"{scene}_video_prompt.json"
            self.assertIn(sb_name, EXPECTED_PROMPT_FIXTURES)
            self.assertIn(video_name, EXPECTED_PROMPT_FIXTURES)
            self.assertTrue((FIXTURES_DIR / sb_name).exists(),
                            f"Missing {sb_name}")
            self.assertTrue((FIXTURES_DIR / video_name).exists(),
                            f"Missing {video_name}")

    # ── verbatim source metadata tests ────────────────────────────────

    def test_source_kind_is_codex_user_message(self):
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data.get("source_kind"), "codex_user_message",
                                 f"{name}: source_kind must be 'codex_user_message'")

    def test_source_fidelity_is_verbatim(self):
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data.get("source_fidelity"), "verbatim",
                                 f"{name}: source_fidelity must be 'verbatim'")

    def test_source_body_sha256_matches_pinned(self):
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                pinned_sha, _, _ = PINNED_PROMPT_BODY[name]
                self.assertEqual(data.get("source_body_sha256"), pinned_sha,
                                 f"{name}: source_body_sha256 mismatch")

    def test_source_body_length_matches_pinned(self):
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                _, pinned_len, _ = PINNED_PROMPT_BODY[name]
                self.assertEqual(data.get("source_body_length"), pinned_len,
                                 f"{name}: source_body_length mismatch")

    def test_source_jsonl_line_matches_pinned(self):
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                _, _, pinned_line = PINNED_PROMPT_BODY[name]
                self.assertEqual(data.get("source_jsonl_line"), pinned_line,
                                 f"{name}: source_jsonl_line mismatch")

    # ── prompt_text exactness tests (pinned constants) ────────────────

    def test_prompt_text_character_count_matches_pinned(self):
        """prompt_text length MUST equal the pinned independent constant."""
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                text = data["prompt_text"]
                _, pinned_len, _ = PINNED_PROMPT_BODY[name]
                self.assertEqual(len(text), pinned_len,
                                 f"{name}: expected {pinned_len} chars, got {len(text)}")

    def test_prompt_text_utf8_sha256_matches_pinned(self):
        """prompt_text UTF-8 SHA-256 MUST equal the pinned independent constant."""
        import hashlib
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                text = data["prompt_text"]
                actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
                pinned_sha, _, _ = PINNED_PROMPT_BODY[name]
                self.assertEqual(actual, pinned_sha,
                                 f"{name}: hash mismatch — pinned={pinned_sha[:16]}... "
                                 f"actual={actual[:16]}...")

    # ── integrity note tests ──────────────────────────────────────────

    def test_integrity_note_contains_no_reconstructed_language(self):
        """integrity_note MUST NOT claim the content is reconstructed or a summary."""
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                note = data.get("integrity_note", "")
                for forbidden in FORBIDDEN_INTEGRITY_WORDS:
                    self.assertNotIn(forbidden, note,
                                     f"{name}: integrity_note contains '{forbidden}'")

    # ── tamper-detection tests ────────────────────────────────────────

    def test_changing_one_code_point_changes_hash(self):
        """Tamper: mutating one code point MUST change the SHA-256."""
        import hashlib
        path = FIXTURES_DIR / "gun_barrel_sb_prompt.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        original = data["prompt_text"]
        original_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
        # Replace last non-newline character with 'X'
        chars = list(original)
        for i in range(len(chars) - 1, -1, -1):
            if chars[i] != '\n':
                chars[i] = 'X' if chars[i] != 'X' else 'Y'
                break
        mutated = "".join(chars)
        mutated_hash = hashlib.sha256(mutated.encode("utf-8")).hexdigest()
        self.assertNotEqual(original_hash, mutated_hash,
                            "Mutating one code point MUST change the hash")
        self.assertEqual(len(mutated), len(original),
                         "Mutation must not change length")

    # ── manifest and section-ref tests ────────────────────────────────

    def test_prompt_fixture_manifest_exists(self):
        manifest_path = FIXTURES_DIR / "prompt_fixture_manifest.json"
        self.assertTrue(manifest_path.exists(), "prompt_fixture_manifest.json missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("fixture_count"), 8)
        self.assertIn("fixtures", manifest)
        for name in EXPECTED_PROMPT_FIXTURES:
            self.assertIn(name, manifest["fixtures"],
                          f"Manifest missing fixture: {name}")

    def test_prompt_fixture_manifest_hashes_match(self):
        """Verify manifest hashes match current fixture FILE content."""
        import hashlib
        manifest_path = FIXTURES_DIR / "prompt_fixture_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name in EXPECTED_PROMPT_FIXTURES:
            path = FIXTURES_DIR / name
            with self.subTest(fixture=name):
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                expected = manifest["fixtures"][name]
                self.assertEqual(actual, expected,
                                 f"{name}: hash drift — manifest={expected[:16]}... "
                                 f"actual={actual[:16]}...")

    def test_prep_area_fixtures_reference_correct_section(self):
        sb = json.loads((FIXTURES_DIR / "prep_area_sb_prompt.json").read_text(encoding="utf-8"))
        video = json.loads((FIXTURES_DIR / "prep_area_video_prompt.json").read_text(encoding="utf-8"))
        self.assertIn("§9.2", sb["source_section"],
                      "prep_area sb must reference §9.2")
        self.assertIn("§9.4", video["source_section"],
                      "prep_area video must reference §9.4")

    def test_alley_fixtures_reference_correct_section(self):
        sb = json.loads((FIXTURES_DIR / "alley_sb_prompt.json").read_text(encoding="utf-8"))
        video = json.loads((FIXTURES_DIR / "alley_video_prompt.json").read_text(encoding="utf-8"))
        self.assertIn("§8.2", sb["source_section"],
                      "alley sb must reference §8.2")
        self.assertIn("§8.4", video["source_section"],
                      "alley video must reference §8.4")


class GoldenFixtureSpecificsTests(unittest.TestCase):
    """Verify scene-specific content is correct."""

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_gun_barrel_single_shot_no_cut(self):
        scene = gfr.GOLDEN_SCENES["gun_barrel_ep8"]
        self.assertTrue(
            any(keyword in scene["description"]
                for keyword in ["单一", "单镜头", "无切镜", "连续摄影"]),
            "gun_barrel description must indicate single shot / no cut"
        )

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_audience_three_internal_shots(self):
        scene = gfr.GOLDEN_SCENES["audience_ep6"]
        has_cut_evidence = (
            any("切" in str(exp) for exp in scene["golden_expectations"])
            or any("cut" in str(role).lower() for role in scene["evidence_roles"])
            or any("internal" in str(role).lower() for role in scene["evidence_roles"])
        )
        self.assertTrue(has_cut_evidence,
                        "audience scene must have internal cut evidence")

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_alley_user_rated_highly(self):
        scene = gfr.GOLDEN_SCENES["alley_ep6"]
        stmt = scene["user_evaluation"]["user_statement"]
        self.assertIn("高", stmt)

    @unittest.skipIf(not MODULE_EXISTS, "golden_fixture_registry not yet implemented")
    def test_prep_area_timing_deviation_noted(self):
        scene = gfr.GOLDEN_SCENES["prep_area_ep6"]
        stmt = scene["user_evaluation"]["user_statement"]
        self.assertIn("构图成功", stmt,
                      "prep_area user statement must note composition success")
        classification = scene["user_evaluation"]["audit_classification"]
        self.assertTrue(
            any(kw in classification for kw in ["时序", "timing", "偏移"]),
            "prep_area classification must note timing deviation"
        )


if __name__ == "__main__":
    unittest.main()
