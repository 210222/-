"""Deterministically rebuild the R1.3 SourceSpan registry.

The eight R1.2 prompt fixtures are immutable authority.  Existing named fields
are retained as declarative needles, then every exact semantic value emitted by
the four shared Golden contracts is indexed as a stable auto field.  Offsets
and hashes are always recomputed from the fixture bodies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

_HERE = Path(__file__).resolve().parent
_FIXTURE_DIR = _HERE.parent
_OUTPUT = _HERE / "source_spans.json"

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


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_prompts() -> dict[str, str]:
    prompts: dict[str, str] = {}
    for fixture_id, (filename, expected_length, expected_hash) in PINNED.items():
        payload = json.loads(
            (_FIXTURE_DIR / filename).read_text(encoding="utf-8")
        )
        text = payload["prompt_text"]
        if len(text) != expected_length:
            raise ValueError(
                f"{fixture_id}: length {len(text)} != {expected_length}"
            )
        if _sha(text) != expected_hash:
            raise ValueError(f"{fixture_id}: prompt body hash drift")
        prompts[fixture_id] = text
    return prompts


def _semantic_values(contract: Any) -> dict[str, str]:
    """Mirror the production-facing semantic surface used by the gate."""
    values: dict[str, str] = {}

    def add(path: str, value: Any) -> None:
        if isinstance(value, str) and value:
            if path in values:
                raise ValueError(f"duplicate semantic path: {path}")
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


def _choose_fixture(
    value: str,
    prompts: dict[str, str],
    preferred: Iterable[str],
) -> str:
    order = list(dict.fromkeys([*preferred, *sorted(prompts)]))
    for fixture_id in order:
        if value in prompts[fixture_id]:
            return fixture_id
    raise ValueError(f"emitted semantic value is absent from all fixtures: {value!r}")


def _record(
    fixture_id: str,
    field_id: str,
    exact_text: str,
    prompts: dict[str, str],
    previous_start: int | None = None,
) -> dict[str, Any]:
    prompt = prompts[fixture_id]
    if (
        previous_start is not None
        and prompt[previous_start : previous_start + len(exact_text)] == exact_text
    ):
        start = previous_start
    else:
        start = prompt.find(exact_text)
    if start < 0:
        raise ValueError(
            f"{field_id}: exact text not present in {fixture_id}: {exact_text!r}"
        )
    end = start + len(exact_text)
    return {
        "fixture_id": fixture_id,
        "prompt_body_sha256": _sha(prompt),
        "start": start,
        "end": end,
        "exact_text": exact_text,
        "exact_text_sha256": _sha(exact_text),
        "field_id": field_id,
    }


def build_registry() -> dict[str, Any]:
    prompts = _load_prompts()
    current = json.loads(_OUTPUT.read_text(encoding="utf-8"))
    records: dict[tuple[str, str], dict[str, Any]] = {}

    # Existing named entries are the stable declarative needles used directly
    # by golden_cases.py. Recompute, never trust their stored offsets/hashes.
    for fixture_id, entry in current["fixtures"].items():
        for item in entry["fields"]:
            key = (fixture_id, item["field_id"])
            records[key] = _record(
                fixture_id,
                item["field_id"],
                item["exact_text"],
                prompts,
                item.get("start"),
            )

    # The current registry is sufficient to bootstrap the Golden builder.
    # Add one stable exact record for every emitted value, preferring the
    # scene's own storyboard/video pair.
    from mode_p_vnext.fixtures.r1_3.golden_cases import (
        build_golden_deliveries,
    )

    deliveries = build_golden_deliveries()
    seen_contracts: set[int] = set()
    for delivery_id, view in deliveries.items():
        contract = view.contract
        if id(contract) in seen_contracts:
            continue
        seen_contracts.add(id(contract))
        scene = delivery_id.removesuffix("_sb").removesuffix("_video")
        preferred = (f"{scene}_sb", f"{scene}_video")
        for value in sorted(set(_semantic_values(contract).values())):
            if any(
                record["exact_text"] == value for record in records.values()
            ):
                continue
            fixture_id = _choose_fixture(value, prompts, preferred)
            suffix = _sha(value)[:20]
            field_id = f"{fixture_id}.auto_{suffix}"
            records[(fixture_id, field_id)] = _record(
                fixture_id, field_id, value, prompts
            )

    fixtures: dict[str, Any] = {}
    for fixture_id, (filename, _length, prompt_hash) in PINNED.items():
        fields = [
            record
            for (record_fixture, _field_id), record in records.items()
            if record_fixture == fixture_id
        ]
        fields.sort(key=lambda item: item["field_id"])
        fixtures[fixture_id] = {
            "fixture_file": filename,
            "prompt_body_sha256": prompt_hash,
            "fields": fields,
        }
    return {"schema_version": "1.0", "fixtures": fixtures}


def canonical_text(registry: dict[str, Any]) -> str:
    return json.dumps(
        registry, ensure_ascii=False, indent=2, sort_keys=False
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace source_spans.json with canonical regenerated content",
    )
    args = parser.parse_args()
    generated = canonical_text(build_registry())
    current = _OUTPUT.read_text(encoding="utf-8")
    if args.write:
        _OUTPUT.write_text(generated, encoding="utf-8", newline="\n")
        print(f"wrote {_OUTPUT} ({len(json.loads(generated)['fixtures'])} fixtures)")
        return 0
    if current != generated:
        print("source_spans.json is not reproducible; run with --write")
        return 1
    print("source_spans.json is reproducible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
