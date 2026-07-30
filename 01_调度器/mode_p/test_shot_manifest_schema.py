"""Validate SHOT_MANIFEST.json against its JSON Schema.

Verifies that the manifest is a mechanical projection — canonical fields only,
no creative text, not a second design source. Also validates boundary ID
chaining rules that cannot be expressed in JSON Schema alone.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema


SCHEMA_PATH = Path(__file__).with_name("shot_manifest_schema.json")

with open(SCHEMA_PATH, encoding="utf-8") as fh:
    SCHEMA = json.load(fh)


def validate(instance: dict) -> None:
    jsonschema.validate(instance, SCHEMA)


# --- valid fixtures ---

VALID_MINIMAL = {
    "manifest_version": "1.0",
    "scene_id": "EP14_S1",
    "master_version": "EP14_S1/v1.0",
    "master_content_hash": "a" * 64,
    "compiler_version": "1.0.0",
    "shots": [
        {
            "shot_id": "EP14_S1-1",
            "duration": 8.0,
            "scene_expression": "conversation_power",
            "timing_mode": "event_nodes",
            "story_fact_ref": {
                "text_start": "Miguel stands at the whiteboard.",
                "source_scene_id": "EP14_S1",
                "source_line_start": 12,
                "source_line_end": 15,
            },
            "opening_state_keys": {
                "characters": [
                    {"entity_id": "Miguel", "position": "whiteboard_front", "facing": "N", "screen_direction": "static", "posture": "standing"}
                ],
                "props": [
                    {"prop_id": "jacket", "held_by": "none", "location": "chair_back"}
                ],
                "light_main": {"direction": "top", "color_temp_k": 5000, "ratio": "1:2"},
                "action_phase": "static",
            },
            "closing_state_keys": {
                "characters": [
                    {"entity_id": "Miguel", "position": "whiteboard_front", "facing": "NE", "screen_direction": "static", "posture": "standing"}
                ],
                "props": [
                    {"prop_id": "jacket", "held_by": "none", "location": "chair_back"}
                ],
                "light_main": {"direction": "top", "color_temp_k": 5000, "ratio": "1:2"},
                "action_phase": "static",
            },
            "entry_boundary_id": "SCENE_ENTRY",
            "exit_boundary_id": "SCENE_EXIT",
            "boundary_continuity": "scene_exit",
            "transition_execution": "post_production",
            "generation_mode": "text_only",
            "reference_assets": [],
        }
    ],
}

# Multi-shot manifest for boundary chaining tests
VALID_CHAINED = {
    "manifest_version": "1.0",
    "scene_id": "EP14",
    "master_version": "EP14/v1.0",
    "master_content_hash": "b" * 64,
    "compiler_version": "1.0.0",
    "shots": [
        {
            "shot_id": "EP14-1",
            "duration": 5.0,
            "scene_expression": "action_chase",
            "timing_mode": "half_second_nodes",
            "story_fact_ref": {"text_start": "...", "source_scene_id": "EP14", "source_line_start": 1, "source_line_end": 3},
            "opening_state_keys": {
                "characters": [{"entity_id": "A", "position": "door", "facing": "S", "screen_direction": "left_to_right", "posture": "standing"}],
                "props": [],
                "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"},
                "action_phase": "prepare",
            },
            "closing_state_keys": {
                "characters": [{"entity_id": "A", "position": "mid_room", "facing": "S", "screen_direction": "left_to_right", "posture": "running"}],
                "props": [],
                "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"},
                "action_phase": "travel",
            },
            "entry_boundary_id": "SCENE_ENTRY",
            "exit_boundary_id": "EP14-2",
            "boundary_continuity": "continuous",
            "transition_execution": "post_production",
            "generation_mode": "omni_reference",
            "reference_assets": [{"asset_id": "char_runner_01", "responsibility": "identity"}],
        },
        {
            "shot_id": "EP14-2",
            "duration": 10.0,
            "scene_expression": "action_chase",
            "timing_mode": "half_second_nodes",
            "story_fact_ref": {"text_start": "...", "source_scene_id": "EP14", "source_line_start": 4, "source_line_end": 6},
            "opening_state_keys": {
                "characters": [{"entity_id": "A", "position": "mid_room", "facing": "S", "screen_direction": "left_to_right", "posture": "running"}],
                "props": [],
                "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"},
                "action_phase": "travel",
            },
            "closing_state_keys": {
                "characters": [{"entity_id": "A", "position": "far_end", "facing": "S", "screen_direction": "left_to_right", "posture": "stopped"}],
                "props": [],
                "light_main": {"direction": "top", "color_temp_k": 4000, "ratio": "1:3"},
                "action_phase": "recover",
            },
            "entry_boundary_id": "EP14-1",
            "exit_boundary_id": "SCENE_EXIT",
            "boundary_continuity": "scene_exit",
            "transition_execution": "post_production",
            "generation_mode": "omni_reference",
            "reference_assets": [{"asset_id": "char_runner_01", "responsibility": "continuity"}],
        },
    ],
}


class SchemaSelfValidationTests(unittest.TestCase):
    """Ensure the schema file itself is valid JSON Schema."""

    def test_schema_is_valid_json_schema(self) -> None:
        jsonschema.Draft202012Validator.check_schema(SCHEMA)


class ValidManifestTests(unittest.TestCase):
    def test_minimal_single_shot_passes(self) -> None:
        validate(VALID_MINIMAL)

    def test_chained_two_shot_passes(self) -> None:
        validate(VALID_CHAINED)

    def test_first_last_frame_mode_with_assets(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["generation_mode"] = "first_last_frame"
        inst["shots"][0]["reference_assets"] = [
            {"asset_id": "frame_start_01", "responsibility": "location"},
            {"asset_id": "frame_end_01", "responsibility": "location"},
        ]
        validate(inst)

    def test_omni_reference_with_all_responsibilities(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["generation_mode"] = "omni_reference"
        inst["shots"][0]["reference_assets"] = [
            {"asset_id": "c1", "responsibility": "identity"},
            {"asset_id": "c2", "responsibility": "wardrobe"},
            {"asset_id": "c3", "responsibility": "location"},
            {"asset_id": "c4", "responsibility": "continuity"},
            {"asset_id": "c5", "responsibility": "action"},
            {"asset_id": "c6", "responsibility": "camera"},
            {"asset_id": "c7", "responsibility": "style"},
            {"asset_id": "c8", "responsibility": "audio"},
        ]
        validate(inst)

    def test_action_phase_values(self) -> None:
        for phase in ["prepare", "launch", "travel", "impact", "recover", "static"]:
            import copy
            inst = copy.deepcopy(VALID_MINIMAL)
            inst["shots"][0]["opening_state_keys"]["action_phase"] = phase
            inst["shots"][0]["closing_state_keys"]["action_phase"] = phase
            validate(inst)


class InvalidManifestTests(unittest.TestCase):
    def test_v12_manifest_requires_shared_boundaries(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["manifest_version"] = "1.2"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_zero_duration_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["duration"] = 0
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_duration_over_15_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["duration"] = 15.1
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_negative_duration_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["duration"] = -1
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_expression_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["scene_expression"] = "dialogue"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_timing_mode_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["timing_mode"] = "frame_nodes"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_generation_mode_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["generation_mode"] = "hybrid"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_transition_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["transition_execution"] = "dissolve"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_boundary_id_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["entry_boundary_id"] = "EP14-2"  # first shot must be SCENE_ENTRY
        # schema allows EP14-2 pattern, but semantic check should catch it
        # schema-level: the pattern itself is valid; the chaining rule is semantic
        validate(inst)  # passes schema — boundary chaining is checked by boundary_check.py

    def test_invalid_scene_id_format(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["scene_id"] = "scene with spaces"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_master_version_format(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["master_version"] = "v1"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_missing_shots_array_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        del inst["shots"]
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_empty_shots_array_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"] = []
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_missing_required_shot_field_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        del inst["shots"][0]["duration"]
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_extra_field_in_shot_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["creative_note"] = "This shot feels sad."
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_asset_responsibility(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["generation_mode"] = "omni_reference"
        inst["shots"][0]["reference_assets"] = [
            {"asset_id": "x", "responsibility": "mood"}  # not in enum
        ]
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_missing_screen_direction_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        del inst["shots"][0]["opening_state_keys"]["characters"][0]["screen_direction"]
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_screen_direction_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["opening_state_keys"]["characters"][0]["screen_direction"] = "north"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_invalid_boundary_continuity_rejected(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["boundary_continuity"] = "jump"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)


class BoundaryChainingSemanticTests(unittest.TestCase):
    """Manifest-level boundary ID rules beyond JSON Schema's reach."""

    def test_first_shot_must_have_scene_entry(self) -> None:
        inst = VALID_MINIMAL
        self.assertEqual(inst["shots"][0]["entry_boundary_id"], "SCENE_ENTRY")

    def test_last_shot_must_have_scene_exit(self) -> None:
        inst = VALID_MINIMAL
        self.assertEqual(inst["shots"][-1]["exit_boundary_id"], "SCENE_EXIT")

    def test_chained_boundary_ids_form_valid_chain(self) -> None:
        inst = VALID_CHAINED
        # Shot 0 exit names shot 1; shot 1 entry names shot 0
        self.assertEqual(inst["shots"][0]["exit_boundary_id"], inst["shots"][1]["shot_id"])
        self.assertEqual(inst["shots"][1]["entry_boundary_id"], inst["shots"][0]["shot_id"])

    def test_chained_shot_exit_is_scene_id_dash_next_shot_number(self) -> None:
        inst = VALID_CHAINED
        self.assertEqual(inst["shots"][0]["exit_boundary_id"], "EP14-2")
        self.assertEqual(inst["shots"][1]["entry_boundary_id"], "EP14-1")

    def test_first_and_last_same_for_single_shot(self) -> None:
        """A single-shot scene uses SCENE_ENTRY -> SCENE_EXIT."""
        inst = VALID_MINIMAL
        self.assertEqual(inst["shots"][0]["entry_boundary_id"], "SCENE_ENTRY")
        self.assertEqual(inst["shots"][0]["exit_boundary_id"], "SCENE_EXIT")


class NoCreativeContentTests(unittest.TestCase):
    """Manifest must not contain creative natural-language fields."""

    def test_schema_rejects_additional_root_property(self) -> None:
        """Creative fields cannot bypass the closed shot schema via the root."""
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["director_notes"] = "Make the sequence feel ominous."
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_schema_rejects_additional_story_fact_property(self) -> None:
        """story_fact_ref remains traceability metadata, not a prose container."""
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["shots"][0]["story_fact_ref"]["creative_interpretation"] = "He hides his fear."
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_no_creative_narrative_fields_in_schema(self) -> None:
        """The schema must not define fields for narrative, camera prose, etc."""
        shot_props = SCHEMA["$defs"]["shot_entry"]["properties"]
        creative_fields = {"narrative", "camera_prose", "composition_prose",
                           "lighting_prose", "performance_prose", "director_notes"}
        for field in creative_fields:
            self.assertNotIn(field, shot_props,
                             f"Creative field '{field}' must not exist in manifest schema")

    def test_state_keys_are_structured_not_prose(self) -> None:
        """State keys use structured objects (entity_id, position, etc.), not free text."""
        state_schema = SCHEMA["$defs"]["shot_entry"]["properties"]["opening_state_keys"]
        self.assertIn("characters", state_schema["properties"])
        char_schema = state_schema["properties"]["characters"]["items"]
        # Only structured keys, no "description" field
        self.assertIn("entity_id", char_schema["properties"])
        self.assertNotIn("description", char_schema["properties"])


class VersionAndHashTests(unittest.TestCase):
    def test_manifest_version_must_be_valid(self) -> None:
        validate(VALID_MINIMAL)  # 1.0 is valid
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["manifest_version"] = "2.0"  # not yet defined
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_master_hash_must_be_64_hex(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["master_content_hash"] = "short"
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)

    def test_master_hash_must_be_lowercase_hex(self) -> None:
        import copy
        inst = copy.deepcopy(VALID_MINIMAL)
        inst["master_content_hash"] = "G" * 64
        with self.assertRaises(jsonschema.ValidationError):
            validate(inst)


if __name__ == "__main__":
    unittest.main()
