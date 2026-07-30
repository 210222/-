"""Locked external acceptance gate for MODE:P vNext R1.3.

This file is owned by the independent Codex audit, not by the R1.3 repair
worker.  A repair may change production R1.3 files and R1.3-local fixtures, but
must not edit, replace, copy, monkeypatch, skip, or xfail this gate.

Run from ``01_调度器``:

    python -m pytest ../MODE_P_REDESIGN_PROJECT/vnext_acceptance/\
test_r1_3_external_acceptance.py -q

The gate deliberately tests production behavior and exact R1.2 prompt bodies.
It does not accept a green worker-owned V5 suite as a substitute.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "01_调度器"
if str(DISPATCHER) not in sys.path:
    sys.path.insert(0, str(DISPATCHER))

FIXTURE_DIR = DISPATCHER / "mode_p_vnext" / "fixtures"
R13_DIR = FIXTURE_DIR / "r1_3"
SOURCE_REGISTRY = R13_DIR / "source_spans.json"

PINNED = {
    "gun_barrel_sb": (
        "gun_barrel_sb_prompt.json",
        1703,
        "ce4caf8504593b307d0835120e516f427f4d6ed0e41d2bf35395f95169496ea8",
    ),
    "gun_barrel_video": (
        "gun_barrel_video_prompt.json",
        2544,
        "452f8fabc04e6e44b6e8f4d80919ea35b37bd8b765cc52bad94dfaa1a5095cce",
    ),
    "audience_sb": (
        "audience_sb_prompt.json",
        2099,
        "1cd5a30f019e97f6651771fa8155229c85c8c969eca0400d7da0db3bb2b02141",
    ),
    "audience_video": (
        "audience_video_prompt.json",
        2397,
        "5fa1815ade3e507807f583c2d4556997bbe8e10538a4badeaaed4eb51bfb8787",
    ),
    "prep_area_sb": (
        "prep_area_sb_prompt.json",
        1600,
        "ed006256727083cba8e1b5ae065fe6e1e7671b02f033c8d4c738d49d3af1b057",
    ),
    "prep_area_video": (
        "prep_area_video_prompt.json",
        1811,
        "36f45f042d3c3350a3e6a847e321eb9c0e3c9b2be9966a8154237af42d13a46c",
    ),
    "alley_sb": (
        "alley_sb_prompt.json",
        3032,
        "8e14b8f21da8a54116d2ff2fe5ef0ec9eab5c03a3d8c55ae28daa184aa766edb",
    ),
    "alley_video": (
        "alley_video_prompt.json",
        2932,
        "a558b598e0718c3bbae1aa717c44f08b07c2939d2feedce5c775ad97fcdc52c9",
    ),
}

# These are exact substrings from the pinned prompt bodies.  At least one
# source-span record must cover every anchor, and the rendered delivery must
# preserve it.  They are intentionally about the user's successful data, not
# a model-authored synopsis.
EXACT_OUTPUT_ANCHORS = {
    "gun_barrel_sb": (
        "Rico背对镜头坐在台灯后",
        "格13 [12-13s·极特写·135mm·静止]",
    ),
    "gun_barrel_video": (
        "摄影机在门口",
        "那不是漩涡不是幻觉",
    ),
    "audience_sb": (
        "格3s→格4s [切]",
        "WhatsApp",
    ),
    "audience_video": (
        "切 镜B-1→B-2",
        "WhatsApp",
    ),
    "prep_area_sb": (
        "格5s [5s·MS·35-50mm·固定]",
        "Rico低头擦枪·没抬头",
    ),
    "prep_area_video": (
        "格5s [5s] 伊乌里从画左走入备赛区",
        "Rico低头擦枪·视线锁定在手枪上",
    ),
    "alley_sb": (
        "跑动追球",
        "直升机画右→画左",
        "轿车静止",
    ),
    "alley_video": (
        "跑动追球",
        "直升机从画右边缘入画",
        "轿车静止",
    ),
}

REQUIRED_CONTRACT_ENVELOPE = {
    "segment_start_tick",
    "segment_end_tick",
    "ticks_per_second",
    "authoritative_shot_ids",
    "required_output_kinds",
    "required_storyboard_sections",
    "required_video_sections",
    "semantic_sources",
    "semantic_sources_sha256",
    "semantic_derivations",
}

REQUIRED_SOURCE_FIELDS = {
    "fixture_id",
    "prompt_body_sha256",
    "start",
    "end",
    "exact_text",
    "exact_text_sha256",
    "field_id",
}

SB_REQUIRED_SECTIONS = {
    "references",
    "style",
    "annotation_legend",
    "shared_visual_anchors",
    "numbering",
    "timeline",
}

VIDEO_REQUIRED_SECTIONS = {
    "upload_refs",
    "reference_duties",
    "numbering",
    "arrow_explanation",
    "storyboard_priority",
    "target_style",
    "lighting",
    "timeline",
    "audio",
    "prohibitions",
    "prohibition_route",
}

EXPECTED_STATE_NODE_COUNTS = {
    "gun_barrel_sb": 13,
    "gun_barrel_video": 14,  # explicit 0s through 13s states
    "audience_sb": 12,
    "audience_video": 12,
    "prep_area_sb": 10,
    "prep_area_video": 10,
    "alley_sb": 13,
    "alley_video": 13,
}

EXPECTED_BOUNDARY_TICKS = {
    "audience_sb": {3 * 24000, 8 * 24000},
    "audience_video": {3 * 24000, 8 * 24000},
    "alley_sb": {5 * 24000, 9 * 24000},
    "alley_video": {5 * 24000, 9 * 24000},
}

STORYBOARD_SENTINELS = {
    "gun_barrel_sb": ("黑白手绘线稿故事板", "13格电影分镜", "共享视觉锚"),
    "audience_sb": ("黑白手绘线稿故事板", "12格电影分镜", "共享视觉锚"),
    "prep_area_sb": ("黑白手绘线稿故事板", "10格电影分镜", "共享视觉锚"),
    "alley_sb": ("黑白手绘线稿故事板", "13格电影分镜", "共享视觉锚"),
}

VIDEO_SENTINELS = {
    fixture_id: (
        "@上传参考图",
        "真人实拍风格",
        "电影级光影",
        "@音轨",
        "@禁止",
    )
    for fixture_id in (
        "gun_barrel_video",
        "audience_video",
        "prep_area_video",
        "alley_video",
    )
}

ALLOWED_DERIVATIONS = {
    "extract_exact_substring",
    "parse_timecode",
    "normalize_reference_id",
    "normalize_phase_field",
    "derive_route_from_prohibition",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_prompt(fixture_id: str) -> tuple[dict[str, Any], str]:
    filename, expected_length, expected_sha = PINNED[fixture_id]
    data = json.loads((FIXTURE_DIR / filename).read_text(encoding="utf-8"))
    text = data["prompt_text"]
    if len(text) != expected_length:
        raise AssertionError(
            f"{fixture_id}: length {len(text)} != {expected_length}"
        )
    if _sha(text) != expected_sha:
        raise AssertionError(
            f"{fixture_id}: body SHA {_sha(text)} != {expected_sha}"
        )
    return data, text


def _load_registry() -> dict[str, Any]:
    if not SOURCE_REGISTRY.is_file():
        raise AssertionError(
            "R1.3 source-span registry is missing: "
            f"{SOURCE_REGISTRY}. A structural signature is not source grounding."
        )
    registry = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise AssertionError("source_spans.json must contain a JSON object")
    return registry


def _load_golden_module():
    try:
        return importlib.import_module(
            "mode_p_vnext.fixtures.r1_3.golden_cases"
        )
    except Exception as exc:  # pragma: no cover - message is the assertion
        raise AssertionError(
            "Missing source-grounded Golden delivery builder "
            "mode_p_vnext.fixtures.r1_3.golden_cases"
        ) from exc


def _load_deliveries() -> dict[str, Any]:
    module = _load_golden_module()
    builder = getattr(module, "build_golden_deliveries", None)
    if not callable(builder):
        raise AssertionError(
            "golden_cases.py must expose build_golden_deliveries()"
        )
    deliveries = builder()
    if not isinstance(deliveries, dict):
        raise AssertionError("build_golden_deliveries() must return a dict")
    if set(deliveries) != set(PINNED):
        raise AssertionError(
            f"Golden deliveries must be exactly {sorted(PINNED)}, "
            f"got {sorted(deliveries)}"
        )
    return deliveries


def _public_render(fixture_id: str, view: Any) -> str:
    if fixture_id.endswith("_sb"):
        module = importlib.import_module("mode_p_vnext.storyboard_renderer")
        render = module.render_storyboard
    else:
        module = importlib.import_module("mode_p_vnext.video_renderer")
        render = module.render_video_prompt
    return render(view)


def _validation_messages(contract: Any, segment_id: str) -> list[str]:
    projection = importlib.import_module("mode_p_vnext.storyboard_projection")
    messages = projection.validate_delivery_contract(contract, segment_id)
    return [str(item) for item in messages]


def _registry_source_records() -> dict[tuple[str, str], dict[str, Any]]:
    registry = _load_registry()
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for fixture_id, entry in registry["fixtures"].items():
        for record in entry["fields"]:
            key = (fixture_id, record["field_id"])
            if key in records:
                raise AssertionError(f"duplicate registry source record: {key}")
            records[key] = record
    return records


def _semantic_values(contract: Any) -> dict[str, str]:
    """Enumerate every output-emitted creative string independently."""
    values: dict[str, str] = {}

    def add(path: str, value: Any) -> None:
        if isinstance(value, str) and value:
            if path in values:
                raise AssertionError(f"duplicate semantic path: {path}")
            values[path] = value

    for i, value in enumerate(contract.character_refs):
        add(f"character_refs[{i}]", value)
    for i, value in enumerate(contract.scene_refs):
        add(f"scene_refs[{i}]", value)
    for i, value in enumerate(contract.prop_refs):
        add(f"prop_refs[{i}]", value)
    for i, value in enumerate(contract.reference_images):
        add(f"reference_images[{i}]", value)
    for i, (ref_id, duty) in enumerate(contract.reference_responsibilities):
        add(f"reference_responsibilities[{i}].reference_id", ref_id)
        add(f"reference_responsibilities[{i}].duty", duty)

    add("style_declaration", contract.style_declaration)
    for i, (colour, meaning) in enumerate(contract._annotation_legend):
        add(f"annotation_legend[{i}].colour", colour)
        add(f"annotation_legend[{i}].meaning", meaning)
    add("target_style", contract.target_style)
    add("shared_lighting_stability", contract.shared_lighting_stability)
    add("arrow_explanation", contract.arrow_explanation)
    add("storyboard_priority", contract.storyboard_priority)
    add("shared_visual_anchors", contract.shared_visual_anchors)
    add("numbering_meaning", contract.numbering_meaning)

    for i, phase in enumerate(contract.phases):
        add(f"phases[{i}].label", phase.label)
        add(f"phases[{i}].shot_size", phase.shot_size)
        add(f"phases[{i}].focal_length", phase.focal_length)
        add(f"phases[{i}].camera_motion", phase.camera_motion)

    for node in contract.nodes:
        for key, value in node._display:
            add(f"nodes[{node.node_id}].display.{key}", value)

    for i, value in enumerate(contract.audio_track):
        add(f"audio_track[{i}]", value)
    for i, value in enumerate(contract.prohibitions):
        add(f"prohibitions[{i}]", value)
    add("handoff", contract.handoff)
    add("transition_description", contract.transition_description)
    return values


def _is_creative_identity_path(path: str) -> bool:
    """Creative prose may not be paraphrased under a derivation label."""
    return (
        path in {
            "style_declaration",
            "target_style",
            "shared_lighting_stability",
            "arrow_explanation",
            "storyboard_priority",
            "shared_visual_anchors",
            "numbering_meaning",
            "handoff",
            "transition_description",
        }
        or ".display.description" in path
        or path.startswith("audio_track[")
        or path.startswith("prohibitions[")
        or path.endswith(".duty")
        or path.endswith(".meaning")
    )


class ExactSourceSpanGate(unittest.TestCase):
    def test_all_eight_r1_2_prompt_bodies_are_still_exact(self):
        for fixture_id in PINNED:
            _load_prompt(fixture_id)

    def test_registry_has_exact_closed_fixture_set(self):
        registry = _load_registry()
        self.assertEqual(registry.get("schema_version"), "1.0")
        self.assertEqual(set(registry.get("fixtures", {})), set(PINNED))

    def test_registry_does_not_duplicate_full_prompt_bodies(self):
        registry = _load_registry()

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                forbidden = {"prompt_text", "prompt_body", "body"} & set(value)
                self.assertFalse(
                    forbidden,
                    f"source registry duplicates a full prompt body: {forbidden}",
                )
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(registry)

    def test_every_source_span_matches_exact_fixture_bytes(self):
        registry = _load_registry()
        seen_field_ids: set[str] = set()
        for fixture_id, (filename, _, expected_sha) in PINNED.items():
            _, prompt_text = _load_prompt(fixture_id)
            entry = registry["fixtures"][fixture_id]
            self.assertEqual(entry.get("fixture_file"), filename)
            self.assertEqual(entry.get("prompt_body_sha256"), expected_sha)
            fields = entry.get("fields")
            self.assertIsInstance(fields, list)
            self.assertGreater(
                len(fields), 0, f"{fixture_id} has no grounded semantic fields"
            )
            for field in fields:
                self.assertTrue(
                    REQUIRED_SOURCE_FIELDS <= set(field),
                    f"{fixture_id} source record lacks required keys: {field}",
                )
                self.assertEqual(field["fixture_id"], fixture_id)
                self.assertEqual(field["prompt_body_sha256"], expected_sha)
                start, end = field["start"], field["end"]
                self.assertIsInstance(start, int)
                self.assertIsInstance(end, int)
                self.assertGreaterEqual(start, 0)
                self.assertGreater(end, start)
                exact = prompt_text[start:end]
                self.assertEqual(exact, field["exact_text"])
                self.assertEqual(_sha(exact), field["exact_text_sha256"])
                field_id = field["field_id"]
                self.assertIsInstance(field_id, str)
                self.assertTrue(field_id.strip())
                self.assertNotIn(field_id, seen_field_ids)
                seen_field_ids.add(field_id)

    def test_exact_success_facts_are_covered_by_source_spans(self):
        registry = _load_registry()
        for fixture_id, anchors in EXACT_OUTPUT_ANCHORS.items():
            texts = [
                record["exact_text"]
                for record in registry["fixtures"][fixture_id]["fields"]
            ]
            for anchor in anchors:
                self.assertTrue(
                    any(anchor in text for text in texts),
                    f"{fixture_id}: no source span covers exact anchor {anchor!r}",
                )


class ProductionFailClosedGate(unittest.TestCase):
    @staticmethod
    def _minimal_segment():
        timeline = importlib.import_module(
            "mode_p_vnext.schema.canonical_timeline"
        )
        schema = importlib.import_module(
            "mode_p_vnext.schema.generation_segment"
        )
        tps = 24000
        shot = schema.CinematicShot(
            shot_id="S1",
            segment_id="MINIMAL",
            time_range=timeline.TimeInterval(0, tps),
            narrative_job="job",
            camera_position="door",
            shot_size="WS",
            focal_intent="24mm",
            camera_motion="fixed",
            composition="center",
            lighting="lamp",
            performance="still",
        )
        return schema.GenerationSegment(
            "MINIMAL", timeline.TimeInterval(0, tps), [shot]
        )

    def test_raw_storyboard_renderer_rejects_empty_contract(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        renderer = importlib.import_module("mode_p_vnext.storyboard_renderer")
        view = projection.StoryboardView(
            segment_id="EMPTY", contract=projection.DualOutputContract()
        )
        with self.assertRaises(projection.ContractError):
            renderer.render_storyboard(view)

    def test_raw_video_renderer_rejects_empty_contract(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        video_projection = importlib.import_module(
            "mode_p_vnext.video_projection"
        )
        renderer = importlib.import_module("mode_p_vnext.video_renderer")
        view = video_projection.VideoPromptView(
            segment_id="EMPTY", contract=projection.DualOutputContract()
        )
        with self.assertRaises(projection.ContractError):
            renderer.render_video_prompt(view)

    def test_direct_minimal_storyboard_projection_cannot_be_delivered(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        renderer = importlib.import_module("mode_p_vnext.storyboard_renderer")
        view = projection.project_storyboard(self._minimal_segment())
        with self.assertRaises(projection.ContractError):
            renderer.render_storyboard(view)

    def test_direct_minimal_video_projection_cannot_be_delivered(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        video_projection = importlib.import_module(
            "mode_p_vnext.video_projection"
        )
        renderer = importlib.import_module("mode_p_vnext.video_renderer")
        view = video_projection.project_video_prompt(self._minimal_segment())
        with self.assertRaises(projection.ContractError):
            renderer.render_video_prompt(view)


class CanonicalEnvelopeAndGoldenDeliveryGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deliveries = _load_deliveries()

    def test_contract_has_canonical_envelope(self):
        for fixture_id, view in self.deliveries.items():
            contract = view.contract
            missing = REQUIRED_CONTRACT_ENVELOPE - set(
                getattr(contract, "__dataclass_fields__", {})
            )
            self.assertFalse(
                missing, f"{fixture_id}: missing contract envelope {missing}"
            )
            self.assertGreater(contract.ticks_per_second, 0)
            self.assertGreater(
                contract.segment_end_tick, contract.segment_start_tick
            )
            self.assertTrue(contract.authoritative_shot_ids)
            self.assertTrue(contract.required_output_kinds)
            self.assertTrue(contract.semantic_sources)

    def test_nodes_declare_temporal_kind(self):
        for fixture_id, view in self.deliveries.items():
            self.assertTrue(view.contract.nodes, fixture_id)
            for node in view.contract.nodes:
                self.assertTrue(
                    hasattr(node, "temporal_kind"),
                    f"{fixture_id}/{node.node_id}: temporal_kind missing",
                )
                self.assertIn(node.temporal_kind, {"at", "interval"})

    def test_semantic_sources_are_frozen_verified_records(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        source_type = getattr(projection, "SourceSpan", None)
        self.assertIsNotNone(
            source_type, "storyboard_projection.SourceSpan is required"
        )
        self.assertTrue(dataclasses.is_dataclass(source_type))
        self.assertTrue(
            source_type.__dataclass_params__.frozen,
            "SourceSpan must be frozen",
        )
        source_field_names = set(source_type.__dataclass_fields__)
        self.assertTrue(REQUIRED_SOURCE_FIELDS <= source_field_names)

        for fixture_id, view in self.deliveries.items():
            semantic_sources = view.contract.semantic_sources
            paths: set[str] = set()
            for item in semantic_sources:
                self.assertIsInstance(item, tuple)
                self.assertEqual(len(item), 2)
                semantic_path, source = item
                self.assertIsInstance(semantic_path, str)
                self.assertTrue(semantic_path)
                self.assertNotIn(semantic_path, paths)
                paths.add(semantic_path)
                self.assertIsInstance(source, source_type)
                self.assertIn(source.fixture_id, PINNED)
                _, prompt_text = _load_prompt(source.fixture_id)
                self.assertEqual(
                    prompt_text[source.start:source.end], source.exact_text
                )
                self.assertEqual(_sha(source.exact_text), source.exact_text_sha256)

    def test_all_eight_valid_deliveries_render_through_public_modules(self):
        for fixture_id, view in self.deliveries.items():
            violations = _validation_messages(view.contract, view.segment_id)
            self.assertEqual(violations, [], f"{fixture_id}: {violations}")
            rendered = _public_render(fixture_id, view)
            self.assertGreater(len(rendered), 100, fixture_id)

    def test_rendered_outputs_preserve_exact_success_facts(self):
        for fixture_id, view in self.deliveries.items():
            rendered = _public_render(fixture_id, view)
            for anchor in EXACT_OUTPUT_ANCHORS[fixture_id]:
                self.assertIn(anchor, rendered, f"{fixture_id}: {anchor!r}")

    def test_no_cross_scene_character_leakage(self):
        rendered = {
            key: _public_render(key, value)
            for key, value in self.deliveries.items()
        }
        self.assertNotIn("Pedro", rendered["gun_barrel_video"])
        self.assertNotIn("Pedro", rendered["audience_video"])
        self.assertNotIn("Rico", rendered["alley_video"])
        self.assertIn("Pedro", rendered["alley_video"])
        self.assertIn("Rico", rendered["prep_area_video"])


class StructuralNegativeMatrixGate(unittest.TestCase):
    def test_specific_invalid_cases_are_reported_without_optional_authority_args(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        tps = 24000

        cases: list[tuple[str, Any, tuple[str, ...]]] = []

        builder = projection.ContractBuilder("BAD_SHOT")
        builder.add_node(
            "n",
            0,
            1000,
            shot_id="BOGUS",
            display={"description": "x"},
            provenance={"description": "source:x"},
        )
        cases.append(("unknown shot", builder.build(), ("shot", "authoritative")))

        builder = projection.ContractBuilder("OUT_OF_BOUNDS")
        builder.add_node(
            "n",
            0,
            tps * 99,
            display={"description": "x"},
            provenance={"description": "source:x"},
        )
        cases.append(("out of bounds", builder.build(), ("bound", "segment")))

        builder = projection.ContractBuilder("DUP_PHASE")
        builder.add_phase("P")
        builder.add_phase("P")
        builder.add_node(
            "n",
            0,
            1000,
            phase_id="P",
            display={"description": "x"},
            provenance={"description": "source:x"},
        )
        cases.append(("duplicate phase", builder.build(), ("duplicate", "phase")))

        builder = projection.ContractBuilder("BAD_NODE_TYPE")
        builder.add_node(
            "n",
            0,
            1000,
            node_type="MAGIC",
            display={"description": "x"},
            provenance={"description": "source:x"},
        )
        cases.append(("invalid node type", builder.build(), ("node", "type")))

        builder = projection.ContractBuilder("DUP_REF")
        builder.add_reference_image("r")
        builder.add_reference_image("r")
        builder.set_reference_duty("r", "d")
        builder.add_node(
            "n",
            0,
            1000,
            display={"description": "x"},
            provenance={"description": "source:x"},
        )
        cases.append(
            ("duplicate reference", builder.build(), ("duplicate", "reference"))
        )

        builder = projection.ContractBuilder("NO_STYLE_SOURCE")
        builder.set_style("invented style")
        builder.add_node(
            "n",
            0,
            1000,
            display={"description": "x"},
            provenance={"description": "source:x"},
        )
        cases.append(
            (
                "missing style provenance",
                builder.build(),
                ("style", "provenance"),
            )
        )

        for label, contract, required_words in cases:
            messages = " | ".join(
                _validation_messages(contract, contract.segment_id)
            ).lower()
            for word in required_words:
                self.assertIn(
                    word,
                    messages,
                    f"{label}: missing specific diagnostic {word!r}: {messages}",
                )

    def test_source_hash_and_span_tampering_fail_delivery(self):
        deliveries = _load_deliveries()
        fixture_id = "gun_barrel_video"
        view = deliveries[fixture_id]
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        semantic_sources = list(view.contract.semantic_sources)
        path, source = semantic_sources[0]

        bad_hash_source = dataclasses.replace(
            source, exact_text_sha256="0" * 64
        )
        semantic_sources[0] = (path, bad_hash_source)
        bad_hash_contract = dataclasses.replace(
            view.contract, semantic_sources=tuple(semantic_sources)
        )
        bad_hash_view = dataclasses.replace(view, contract=bad_hash_contract)
        with self.assertRaises(projection.ContractError):
            _public_render(fixture_id, bad_hash_view)

        semantic_sources = list(view.contract.semantic_sources)
        path, source = semantic_sources[0]
        bad_span_source = dataclasses.replace(source, start=source.start + 1)
        semantic_sources[0] = (path, bad_span_source)
        bad_span_contract = dataclasses.replace(
            view.contract, semantic_sources=tuple(semantic_sources)
        )
        bad_span_view = dataclasses.replace(view, contract=bad_span_contract)
        with self.assertRaises(projection.ContractError):
            _public_render(fixture_id, bad_span_view)


class FullSemanticCoverageAndTopologyGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deliveries = _load_deliveries()

    def test_worker_renderer_tests_use_source_grounded_builder(self):
        for filename in (
            "test_v5_2_storyboard_renderer.py",
            "test_v5_4_video_renderer.py",
        ):
            text = (
                DISPATCHER / "mode_p_vnext" / "tests" / filename
            ).read_text(encoding="utf-8")
            self.assertIn(
                "build_golden_deliveries",
                text,
                f"{filename} still does not use the locked Golden builder",
            )
            for forbidden in (
                "def _gb(",
                "def _aud(",
                "def _pa(",
                "def _al(",
                "def _gbv(",
                "def _auv(",
                "def _pav(",
                "def _alv(",
                '_G = "source:Golden.fixture"',
            ):
                self.assertNotIn(
                    forbidden,
                    text,
                    f"{filename} still contains a hand-authored substitute",
                )

    def test_required_section_sets_are_declared(self):
        for fixture_id, view in self.deliveries.items():
            contract = view.contract
            if fixture_id.endswith("_sb"):
                self.assertTrue(
                    SB_REQUIRED_SECTIONS
                    <= set(contract.required_storyboard_sections),
                    f"{fixture_id}: incomplete storyboard section authority",
                )
            else:
                self.assertTrue(
                    VIDEO_REQUIRED_SECTIONS
                    <= set(contract.required_video_sections),
                    f"{fixture_id}: incomplete video section authority",
                )

    def test_rendered_outputs_have_complete_golden_format_sentinels(self):
        for fixture_id, sentinels in {
            **STORYBOARD_SENTINELS,
            **VIDEO_SENTINELS,
        }.items():
            rendered = _public_render(
                fixture_id, self.deliveries[fixture_id]
            )
            for sentinel in sentinels:
                self.assertIn(
                    sentinel,
                    rendered,
                    f"{fixture_id}: missing full-format sentinel {sentinel!r}",
                )

    def test_full_per_second_state_timeline_is_preserved(self):
        for fixture_id, expected_count in EXPECTED_STATE_NODE_COUNTS.items():
            contract = self.deliveries[fixture_id].contract
            state_nodes = [
                node
                for node in contract.nodes
                if node.node_type in {"panel", "hold"}
                and (
                    fixture_id.endswith("_video")
                    or node.sb_node
                )
            ]
            self.assertEqual(
                len(state_nodes),
                expected_count,
                f"{fixture_id}: simplified phase synopsis replaced the "
                "per-second Golden timeline",
            )

    def test_internal_cuts_are_zero_duration_at_boundaries(self):
        for fixture_id, expected_ticks in EXPECTED_BOUNDARY_TICKS.items():
            contract = self.deliveries[fixture_id].contract
            actual = {
                node.start_tick
                for node in contract.nodes
                if node.node_type == "boundary"
                and node.temporal_kind == "at"
                and node.start_tick == node.end_tick
            }
            self.assertTrue(
                expected_ticks <= actual,
                f"{fixture_id}: missing exact cut boundaries "
                f"{sorted(expected_ticks - actual)}",
            )
            self.assertEqual(
                _validation_messages(contract, contract.segment_id),
                [],
                f"{fixture_id}: valid instant boundaries must validate",
            )

    def test_each_scene_pair_shares_one_immutable_contract(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        for scene in ("gun_barrel", "audience", "prep_area", "alley"):
            sb = self.deliveries[f"{scene}_sb"]
            video = self.deliveries[f"{scene}_video"]
            self.assertIs(
                sb.contract,
                video.contract,
                f"{scene}: storyboard and video were independently authored",
            )
            comparison = projection.compare_projections(sb, video)
            self.assertTrue(
                comparison.is_consistent,
                f"{scene}: shared topology comparison failed: {comparison}",
            )

    def test_every_emitted_semantic_value_has_exact_source_binding(self):
        registry_records = _registry_source_records()
        for fixture_id, view in self.deliveries.items():
            contract = view.contract
            values = _semantic_values(contract)
            source_pairs = list(contract.semantic_sources)
            source_map = dict(source_pairs)
            self.assertEqual(
                len(source_map),
                len(source_pairs),
                f"{fixture_id}: duplicate semantic source paths",
            )
            derivations = dict(contract.semantic_derivations)
            self.assertEqual(
                len(derivations),
                len(contract.semantic_derivations),
                f"{fixture_id}: duplicate semantic derivation paths",
            )

            missing = set(values) - set(source_map)
            self.assertFalse(
                missing,
                f"{fixture_id}: emitted values without SourceSpan: "
                f"{sorted(missing)}",
            )
            orphan = set(source_map) - (
                set(values) | {"prohibition_routing_marker"}
            )
            self.assertFalse(
                orphan,
                f"{fixture_id}: orphan semantic source paths: {sorted(orphan)}",
            )

            for path, value in values.items():
                source = source_map[path]
                record = registry_records.get(
                    (source.fixture_id, source.field_id)
                )
                self.assertIsNotNone(
                    record,
                    f"{fixture_id}/{path}: SourceSpan is not a registry record",
                )
                for field_name in REQUIRED_SOURCE_FIELDS:
                    self.assertEqual(
                        getattr(source, field_name),
                        record[field_name],
                        f"{fixture_id}/{path}: source record drift in "
                        f"{field_name}",
                    )

                if source.exact_text == value:
                    continue

                rule = derivations.get(path)
                self.assertIn(
                    rule,
                    ALLOWED_DERIVATIONS,
                    f"{fixture_id}/{path}: changed source text without a "
                    "declared deterministic rule",
                )
                if _is_creative_identity_path(path):
                    self.fail(
                        f"{fixture_id}/{path}: creative text must be exact; "
                        f"source={source.exact_text!r}, value={value!r}"
                    )
                if rule == "extract_exact_substring":
                    self.assertIn(value, source.exact_text)

            route = contract.prohibition_routing_marker
            if route:
                self.assertIn(
                    "prohibition_routing_marker",
                    source_map,
                    f"{fixture_id}: route marker has no source",
                )
                self.assertEqual(
                    derivations.get("prohibition_routing_marker"),
                    "derive_route_from_prohibition",
                    f"{fixture_id}: route marker derivation is not explicit",
                )

    def test_semantic_source_authority_hash_is_present_and_stable(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        fixture_id = "gun_barrel_video"
        view = self.deliveries[fixture_id]
        contract = view.contract
        self.assertRegex(contract.semantic_sources_sha256, r"^[0-9a-f]{64}$")

        path, source = contract.semantic_sources[0]
        mutations = (
            dataclasses.replace(source, prompt_body_sha256="0" * 64),
            dataclasses.replace(
                source, start=source.start + 1, end=source.end + 1
            ),
            dataclasses.replace(source, field_id="invented.field"),
        )
        for mutated in mutations:
            pairs = list(contract.semantic_sources)
            pairs[0] = (path, mutated)
            broken_contract = dataclasses.replace(
                contract, semantic_sources=tuple(pairs)
            )
            broken_view = dataclasses.replace(
                view, contract=broken_contract
            )
            with self.assertRaises(projection.ContractError):
                _public_render(fixture_id, broken_view)

    def test_semantic_text_cannot_change_while_old_source_survives(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        fixture_id = "gun_barrel_video"
        view = self.deliveries[fixture_id]
        contract = dataclasses.replace(
            view.contract, target_style="INVENTED TARGET STYLE"
        )
        broken = dataclasses.replace(view, contract=contract)
        with self.assertRaises(projection.ContractError):
            _public_render(fixture_id, broken)

    def test_fingerprint_uses_unambiguous_canonical_serialization(self):
        projection = importlib.import_module(
            "mode_p_vnext.storyboard_projection"
        )
        contract_type = projection.DualOutputContract
        first = contract_type(
            segment_id="X", reference_images=("x\nref:y",)
        )
        second = contract_type(
            segment_id="X", reference_images=("x", "y")
        )
        self.assertNotEqual(
            projection.contract_fingerprint(first),
            projection.contract_fingerprint(second),
            "delimiter-concatenated fingerprint collision",
        )

        view = self.deliveries["gun_barrel_video"]
        path, source = view.contract.semantic_sources[0]
        for mutated in (
            dataclasses.replace(source, prompt_body_sha256="0" * 64),
            dataclasses.replace(
                source, start=source.start + 1, end=source.end + 1
            ),
            dataclasses.replace(source, exact_text=source.exact_text + "x"),
        ):
            pairs = list(view.contract.semantic_sources)
            pairs[0] = (path, mutated)
            changed = dataclasses.replace(
                view.contract, semantic_sources=tuple(pairs)
            )
            self.assertNotEqual(
                projection.contract_fingerprint(view.contract),
                projection.contract_fingerprint(changed),
                "SourceSpan authority field omitted from fingerprint",
            )


if __name__ == "__main__":
    unittest.main()
