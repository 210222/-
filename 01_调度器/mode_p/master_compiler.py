"""Compile a DIRECTOR_MASTER.md into SHOT_MANIFEST.json.

This is a deterministic mechanical extractor. It reads ONLY machine-checkable
fields defined in the active Director Master contract and produces a manifest
that validates against shot_manifest_schema.json.

It MUST fail closed: any unparseable field raises CompilerError.
It MUST NOT interpret creative natural-language fields.
It MUST NOT be called by an LLM Agent — it is a local program.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Optional

import jsonschema

# --- Schema ---

SCHEMA_PATH = Path(__file__).with_name("shot_manifest_schema.json")
with open(SCHEMA_PATH, encoding="utf-8") as _fh:
    _SCHEMA = json.load(_fh)


# --- Regex patterns (synced with director_master_template.md v1.0) ---

_MASTER_VERSION_RE = re.compile(
    r"^Master 版本：\s*(?P<scene_id>[A-Za-z0-9_-]+)/v(?P<major>\d+)\.(?P<minor>\d+)\s*$",
    re.MULTILINE,
)
_SHOT_HEADER_RE = re.compile(
    r"^##\s+Shot\s+(?P<scene_id>[A-Za-z0-9_-]+)-(?P<number>\d+)\s*\|\s*(?P<duration>\d+(?:\.\d+)?)\s*s\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_BOUNDARY_HEADER_RE = re.compile(
    r"^##\s+Boundary\s+(?P<boundary_id>[A-Za-z0-9_-]+-B(?P<number>\d+))\s*\|\s*"
    r"(?P<from_ref>SCENE_ENTRY|[A-Za-z0-9_-]+-\d+)\s*->\s*"
    r"(?P<to_ref>SCENE_EXIT|[A-Za-z0-9_-]+-\d+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_SOURCE_LOCATION_RE = re.compile(
    r"^原文定位：\[M\]\s*(?P<scene_id>[A-Za-z0-9_-]+)\s+L(?P<start>\d+)-L(?P<end>\d+)\s*$",
    re.MULTILINE,
)
_SCENE_EXPRESSION_RE = re.compile(
    r"^场景表达：\[M\]\s*(?P<angle><)?(?P<mode>[a-z_]+)(?(angle)>)\s*$",
    re.MULTILINE,
)
_TIMING_MODE_RE = re.compile(
    r"^时间控制：\[M\]\s*(?P<angle><)?(?P<mode>[a-z_]+)(?(angle)>)\s*$",
    re.MULTILINE,
)
_ENTRY_BOUNDARY_RE = re.compile(
    r"^进入边界 ID：\[M\]\s*(?P<id>[A-Za-z0-9_-]+)\s*$",
    re.MULTILINE,
)
_EXIT_BOUNDARY_RE = re.compile(
    r"^交出边界 ID：\[M\]\s*(?P<id>[A-Za-z0-9_-]+)\s*$",
    re.MULTILINE,
)
_BOUNDARY_CONTINUITY_RE = re.compile(
    r"^边界连续性：\[M\]\s*(?P<angle><)?(?P<mode>[a-z_]+)(?(angle)>)\s*$",
    re.MULTILINE,
)
_TRANSITION_RE = re.compile(
    r"^转场执行：\[M\]\s*(?P<angle><)?(?P<mode>[a-z_]+)(?(angle)>)\s*$",
    re.MULTILINE,
)
_BOUNDARY_RELATION_RE = re.compile(
    r"^边界关系：\[M\]\s*(?P<angle><)?(?P<mode>[a-z_]+)(?(angle)>)\s*$",
    re.MULTILINE,
)
_GENERATION_MODE_RE = re.compile(
    r"^生成模式：\[M\]\s*(?P<angle><)?(?P<mode>[a-z_]+)(?(angle)>)\s*$",
    re.MULTILINE,
)
_ASSET_LIST_RE = re.compile(
    r"^参考资产：\[M\]\s*(?:\[(?P<ids>[^\]]*)\]|(?P<none>无))\s*$",
    re.MULTILINE,
)
_STORY_FACT_RE = re.compile(
    r"^剧本事实：\[D\][ \t]*(?P<text>.*)$",
    re.MULTILINE,
)

# State key sub-parsers
_OPENING_STATE_MARKER = "开场状态键：[M]"
_CLOSING_STATE_MARKER = "结束状态键：[M]"
_OUTGOING_STATE_MARKER = "交出状态键：[M]"
_INCOMING_STATE_MARKER = "接入状态键：[M]"
_INCOMING_SAME_RE = re.compile(
    r"^接入状态键：\[M\]\s*(?:<same>|same)\s*$",
    re.MULTILINE,
)
_CHARACTER_LINE = re.compile(r"^\s*-\s*character:(?P<entity_id>\S+)\s+position:(?P<position>\S+)\s+facing:(?P<facing>\S+)\s+screen_direction:(?P<screen_direction>left_to_right|right_to_left|depth_in|depth_out|static)\s+posture:(?P<posture>\S+)(?:\s+wardrobe:(?P<wardrobe>\S+))?(?:\s+injury:(?P<injury>\S+))?\s*$")
_PROP_LINE = re.compile(r"^\s*-\s*prop:(?P<prop_id>\S+)\s+held_by:(?P<held_by>\S+)\s+location:(?P<location>\S+)\s*$")
_LIGHT_LINE = re.compile(r"^\s*-\s*light_main\s+direction:(?P<direction>\S+)\s+color_temp:(?P<k>\d+)K?\s+ratio:(?P<ratio>\S+)\s*$")
_ACTION_PHASE_LINE = re.compile(r"^\s*-\s*action_phase:(?P<phase>\S+)\s*$")
_STORY_TIME_LINE = re.compile(r"^\s*-\s*story_time:(?P<value>\S+)\s*$")
_WEATHER_LINE = re.compile(r"^\s*-\s*weather:(?P<value>\S+)\s*$")
_ENVIRONMENT_LINE = re.compile(r"^\s*-\s*environment:(?P<value>\S+)\s*$")

VALID_EXPRESSIONS = frozenset({
    "conversation_power", "crowd_attention", "action_chase",
    "suspense_reveal", "contemplative_silence", "investigation_object",
    "montage", "cross_space_transition",
})
VALID_TIMING = frozenset({"event_nodes", "second_nodes", "half_second_nodes"})
VALID_TRANSITION = frozenset({"in_camera", "post_production"})
VALID_BOUNDARY_CONTINUITY = frozenset({"continuous", "elliptical", "scene_exit"})
VALID_BOUNDARY_RELATIONS = frozenset({
    "scene_entry", "continuous", "elliptical", "scene_exit",
})
VALID_GENERATION = frozenset({"text_only", "first_last_frame", "omni_reference"})
VALID_ACTION_PHASES = frozenset({"prepare", "launch", "travel", "impact", "recover", "static"})
VALID_RESPONSIBILITIES = frozenset({
    "identity", "wardrobe", "location", "continuity",
    "action", "camera", "style", "audio", "first_frame", "last_frame",
})

COMPILER_VERSION = "2.0.0"


class CompilerError(Exception):
    """Raised when the compiler cannot parse a required field."""


def _require_single_match(pattern: re.Pattern, text: str, field_name: str) -> re.Match:
    """Return exactly one match or fail closed on missing/duplicate fields."""
    matches = list(pattern.finditer(text))
    if not matches:
        raise CompilerError(f"Missing or unparseable '{field_name}'")
    if len(matches) > 1:
        raise CompilerError(f"Duplicate '{field_name}' fields ({len(matches)} found)")
    return matches[0]


# ---------------------------------------------------------------------------
# public entry points
# ---------------------------------------------------------------------------

def compile_master(master_path: Path) -> dict:
    """Read a Master file and return a validated manifest dict.

    Raises CompilerError on any unparseable required field.
    """
    text = _read_text(master_path)
    master_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    scene_id, master_version = _parse_version(text)
    if _BOUNDARY_HEADER_RE.search(text):
        shots, boundaries = _parse_v4_scene(text, scene_id)
        manifest_version = "1.2"
    else:
        # Historical evidence remains readable, but active Director contracts no
        # longer expose this duplicated-boundary form.
        shots = _parse_shots(text, scene_id)
        boundaries = None
        manifest_version = "1.1"

    manifest = {
        "manifest_version": manifest_version,
        "scene_id": scene_id,
        "master_version": master_version,
        "master_content_hash": master_hash,
        "compiler_version": COMPILER_VERSION,
        "shots": shots,
    }
    if boundaries is not None:
        manifest["boundaries"] = boundaries

    try:
        jsonschema.validate(manifest, _SCHEMA)
    except jsonschema.ValidationError as exc:
        raise CompilerError(f"Manifest failed schema validation: {exc.message}") from exc

    return manifest


def _parse_v4_scene(text: str, scene_id: str) -> tuple[list[dict], list[dict]]:
    """Compile the active one-timeline, shared-Boundary Master contract."""
    shot_blocks = _split_level_two_blocks(text, _SHOT_HEADER_RE, "Shot")
    boundary_blocks = _split_level_two_blocks(text, _BOUNDARY_HEADER_RE, "Boundary")
    if not shot_blocks:
        raise CompilerError("No Shot headers found in Master")

    shots = [
        _parse_single_shot_v4(header, block, scene_id)
        for header, block in shot_blocks
    ]
    numbers = [int(_SHOT_HEADER_RE.match(header).group("number")) for header, _ in shot_blocks]
    if numbers != list(range(1, len(numbers) + 1)):
        raise CompilerError(
            f"Shot numbers must be unique and consecutive from 1; got {numbers}"
        )

    boundaries = [
        _parse_single_boundary(header, block, scene_id)
        for header, block in boundary_blocks
    ]
    boundaries.sort(key=lambda item: item["number"])
    expected_numbers = list(range(0, len(shots) + 1))
    actual_numbers = [item["number"] for item in boundaries]
    if actual_numbers != expected_numbers:
        raise CompilerError(
            "Shared Boundaries must be unique and consecutive from B0 through "
            f"B{len(shots)}; got {actual_numbers}"
        )

    for index, boundary in enumerate(boundaries):
        expected_id = f"{scene_id}-B{index}"
        expected_from = "SCENE_ENTRY" if index == 0 else shots[index - 1]["shot_id"]
        expected_to = "SCENE_EXIT" if index == len(shots) else shots[index]["shot_id"]
        expected_relation = (
            "scene_entry" if index == 0
            else "scene_exit" if index == len(shots)
            else None
        )
        if boundary["boundary_id"] != expected_id:
            raise CompilerError(
                f"Boundary B{index} must use ID '{expected_id}', got "
                f"'{boundary['boundary_id']}'"
            )
        if boundary["from_ref"] != expected_from or boundary["to_ref"] != expected_to:
            raise CompilerError(
                f"Boundary {expected_id} must connect {expected_from} -> {expected_to}"
            )
        if expected_relation is not None and boundary["relation"] != expected_relation:
            raise CompilerError(
                f"Boundary {expected_id} must use relation '{expected_relation}'"
            )
        if expected_relation is None and boundary["relation"] not in {"continuous", "elliptical"}:
            raise CompilerError(
                f"Internal Boundary {expected_id} must be continuous or elliptical"
            )

        outgoing = boundary["outgoing_state_keys"]
        incoming = boundary["incoming_state_keys"]
        incoming_same = boundary.pop("_incoming_same")
        if boundary["relation"] == "scene_entry":
            if outgoing is not None or incoming is None or incoming_same:
                raise CompilerError(
                    f"Boundary {expected_id} scene_entry requires only an explicit incoming state"
                )
        elif boundary["relation"] == "scene_exit":
            if outgoing is None or incoming is not None or incoming_same:
                raise CompilerError(
                    f"Boundary {expected_id} scene_exit requires only an explicit outgoing state"
                )
        elif boundary["relation"] == "continuous":
            if outgoing is None or not incoming_same or incoming is not None:
                raise CompilerError(
                    f"Boundary {expected_id} continuous requires an outgoing state and "
                    "'接入状态键：[M] <same>'"
                )
            boundary["incoming_state_keys"] = copy.deepcopy(outgoing)
        else:  # elliptical
            if outgoing is None or incoming is None or incoming_same:
                raise CompilerError(
                    f"Boundary {expected_id} elliptical requires explicit outgoing and incoming states"
                )

    for index, shot in enumerate(shots):
        entry = boundaries[index]
        exit_ = boundaries[index + 1]
        shot.update({
            "opening_state_keys": copy.deepcopy(entry["incoming_state_keys"]),
            "closing_state_keys": copy.deepcopy(exit_["outgoing_state_keys"]),
            "entry_boundary_id": entry["boundary_id"],
            "exit_boundary_id": exit_["boundary_id"],
            "boundary_continuity": exit_["relation"],
            "transition_execution": exit_["transition_execution"],
        })

    for boundary in boundaries:
        boundary.pop("number")
    return shots, boundaries


def _split_level_two_blocks(
    text: str,
    wanted: re.Pattern,
    label: str,
) -> list[tuple[str, str]]:
    """Slice wanted level-two blocks without absorbing a different block type."""
    all_headers = list(re.finditer(r"^##\s+.*$", text, re.MULTILINE))
    result: list[tuple[str, str]] = []
    candidate_prefix = re.compile(rf"^##\s+{re.escape(label)}\b", re.IGNORECASE)
    valid_headers = {match.start(): match for match in wanted.finditer(text)}
    for index, header in enumerate(all_headers):
        if not candidate_prefix.match(header.group(0)):
            continue
        valid = valid_headers.get(header.start())
        if valid is None:
            raise CompilerError(f"Malformed {label} header: {header.group(0)!r}")
        end = all_headers[index + 1].start() if index + 1 < len(all_headers) else len(text)
        result.append((valid.group(0).strip(), text[header.start():end]))
    return result


def _parse_single_shot_v4(header: str, block: str, expected_scene_id: str) -> dict:
    hm = _SHOT_HEADER_RE.match(header)
    if hm is None:
        raise CompilerError(f"Unparseable shot header: {header!r}")
    if hm.group("scene_id") != expected_scene_id:
        raise CompilerError(
            f"Shot scene_id '{hm.group('scene_id')}' does not match Master "
            f"scene_id '{expected_scene_id}'"
        )
    shot_id = f"{expected_scene_id}-{hm.group('number')}"
    source = _parse_source_location(block)
    if source["scene_id"] != expected_scene_id or source["start"] > source["end"]:
        raise CompilerError(f"Invalid source location in {shot_id}")
    return {
        "shot_id": shot_id,
        "duration": float(hm.group("duration")),
        "scene_expression": _parse_enum_field(
            block, _SCENE_EXPRESSION_RE, "scene_expression", VALID_EXPRESSIONS
        ),
        "timing_mode": _parse_enum_field(
            block, _TIMING_MODE_RE, "timing_mode", VALID_TIMING
        ),
        "story_fact_ref": {
            "text_start": _parse_story_fact_text(block)[:80],
            "source_scene_id": source["scene_id"],
            "source_line_start": source["start"],
            "source_line_end": source["end"],
        },
        "generation_mode": _parse_enum_field(
            block, _GENERATION_MODE_RE, "generation_mode", VALID_GENERATION
        ),
        "reference_assets": _parse_asset_list(block),
    }


def _parse_single_boundary(header: str, block: str, scene_id: str) -> dict:
    hm = _BOUNDARY_HEADER_RE.match(header)
    if hm is None:
        raise CompilerError(f"Unparseable Boundary header: {header!r}")
    boundary_id = hm.group("boundary_id")
    if not boundary_id.startswith(f"{scene_id}-B"):
        raise CompilerError(
            f"Boundary ID '{boundary_id}' does not belong to scene '{scene_id}'"
        )
    relation = _parse_enum_field(
        block, _BOUNDARY_RELATION_RE, "boundary_relation", VALID_BOUNDARY_RELATIONS
    )
    transition = _parse_enum_field(
        block, _TRANSITION_RE, "transition_execution", VALID_TRANSITION
    )
    incoming_same = bool(_INCOMING_SAME_RE.search(block))
    return {
        "number": int(hm.group("number")),
        "boundary_id": boundary_id,
        "from_ref": hm.group("from_ref"),
        "to_ref": hm.group("to_ref"),
        "relation": relation,
        "transition_execution": transition,
        "outgoing_state_keys": _parse_optional_state_keys(
            block, _OUTGOING_STATE_MARKER
        ),
        "incoming_state_keys": (
            None if incoming_same else _parse_optional_state_keys(
                block, _INCOMING_STATE_MARKER
            )
        ),
        "_incoming_same": incoming_same,
    }


def compile_to_file(master_path: Path, output_path: Path) -> None:
    """Compile a Master file and write the manifest to disk."""
    manifest = compile_master(master_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# internal parsing
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="gbk")
        except Exception:
            raise CompilerError(f"Cannot decode {path}; expected UTF-8 or GBK")


def _parse_version(text: str) -> tuple[str, str]:
    m = _require_single_match(_MASTER_VERSION_RE, text, "Master version")
    scene_id = m.group("scene_id")
    master_version = f"{scene_id}/v{m.group('major')}.{m.group('minor')}"
    return scene_id, master_version


def _parse_shots(text: str, expected_scene_id: str) -> list[dict]:
    """Find all Shot blocks and extract canonical fields from each."""
    candidate_headers = re.findall(r"^##\s+Shot\b.*$", text, re.IGNORECASE | re.MULTILINE)
    valid_headers = list(_SHOT_HEADER_RE.finditer(text))
    if len(candidate_headers) != len(valid_headers):
        valid_text = {match.group(0) for match in valid_headers}
        malformed = [header for header in candidate_headers if header not in valid_text]
        raise CompilerError(f"Malformed Shot header(s): {malformed}")

    # Split by shot headers
    shot_blocks = []
    current_start = None
    current_id = None

    for match in valid_headers:
        if current_id is not None:
            shot_blocks.append((current_id, text[current_start:match.start()]))
        current_id = match.group(0).strip()
        current_start = match.start()

    if current_id is not None:
        shot_blocks.append((current_id, text[current_start:]))

    if not shot_blocks:
        raise CompilerError("No Shot headers found in Master. Expected format: '## Shot <scene_id>-<N> | <duration>s'")

    numbers = [int(match.group("number")) for match in valid_headers]
    expected_numbers = list(range(1, len(numbers) + 1))
    if numbers != expected_numbers:
        raise CompilerError(
            f"Shot numbers must be unique and consecutive from 1; got {numbers}"
        )

    shots = []
    for header, block in shot_blocks:
        shot = _parse_single_shot(header, block, expected_scene_id)
        shots.append(shot)

    for index, shot in enumerate(shots):
        expected_entry = "SCENE_ENTRY" if index == 0 else shots[index - 1]["shot_id"]
        expected_exit = "SCENE_EXIT" if index == len(shots) - 1 else shots[index + 1]["shot_id"]
        declared_entry = shot.pop("_declared_entry_boundary_id")
        declared_exit = shot.pop("_declared_exit_boundary_id")
        if declared_entry is not None and declared_entry != expected_entry:
            raise CompilerError(
                f"Declared entry_boundary_id for {shot['shot_id']} is "
                f"'{declared_entry}', but the mechanical chain requires '{expected_entry}'"
            )
        if declared_exit is not None and declared_exit != expected_exit:
            raise CompilerError(
                f"Declared exit_boundary_id for {shot['shot_id']} is "
                f"'{declared_exit}', but the mechanical chain requires '{expected_exit}'"
            )
        shot["entry_boundary_id"] = expected_entry
        shot["exit_boundary_id"] = expected_exit

    return shots


def _parse_single_shot(header: str, block: str, expected_scene_id: str) -> dict:
    hm = _SHOT_HEADER_RE.match(header)
    if not hm:
        raise CompilerError(f"Unparseable shot header: {header!r}")
    shot_scene_id = hm.group("scene_id")
    if shot_scene_id != expected_scene_id:
        raise CompilerError(
            f"Shot scene_id '{shot_scene_id}' does not match Master scene_id '{expected_scene_id}'. "
            f"Header: {header!r}"
        )
    shot_id = f"{shot_scene_id}-{hm.group('number')}"
    duration = float(hm.group("duration"))

    # --- field extractors (each may raise CompilerError) ---
    source = _parse_source_location(block)
    expression = _parse_enum_field(block, _SCENE_EXPRESSION_RE, "scene_expression", VALID_EXPRESSIONS)
    timing = _parse_enum_field(block, _TIMING_MODE_RE, "timing_mode", VALID_TIMING)
    transition = _parse_enum_field(block, _TRANSITION_RE, "transition_execution", VALID_TRANSITION)
    boundary_continuity = _parse_enum_field(
        block, _BOUNDARY_CONTINUITY_RE, "boundary_continuity",
        VALID_BOUNDARY_CONTINUITY,
    )
    gen_mode = _parse_enum_field(block, _GENERATION_MODE_RE, "generation_mode", VALID_GENERATION)
    entry = _parse_optional_boundary(block, _ENTRY_BOUNDARY_RE, "entry_boundary_id")
    exit_ = _parse_optional_boundary(block, _EXIT_BOUNDARY_RE, "exit_boundary_id")
    assets = _parse_asset_list(block)
    story_text = _parse_story_fact_text(block)
    opening = _parse_state_keys(block, _OPENING_STATE_MARKER)
    closing = _parse_state_keys(block, _CLOSING_STATE_MARKER)

    if source["scene_id"] != expected_scene_id:
        raise CompilerError(
            f"Source scene_id '{source['scene_id']}' does not match Master scene_id "
            f"'{expected_scene_id}' in {shot_id}"
        )
    if source["start"] > source["end"]:
        raise CompilerError(
            f"Source line range is reversed in {shot_id}: "
            f"L{source['start']}-L{source['end']}"
        )

    for key in ("characters", "props"):
        identity_key = "entity_id" if key == "characters" else "prop_id"
        opening_ids = {item[identity_key] for item in opening[key]}
        closing_ids = {item[identity_key] for item in closing[key]}
        if opening_ids != closing_ids:
            raise CompilerError(
                f"Opening/closing {key} keys differ in {shot_id}: "
                f"{sorted(opening_ids)} vs {sorted(closing_ids)}"
            )

    return {
        "shot_id": shot_id,
        "duration": duration,
        "scene_expression": expression,
        "timing_mode": timing,
        "story_fact_ref": {
            "text_start": story_text[:80],
            "source_scene_id": source["scene_id"],
            "source_line_start": source["start"],
            "source_line_end": source["end"],
        },
        "opening_state_keys": opening,
        "closing_state_keys": closing,
        "_declared_entry_boundary_id": entry,
        "_declared_exit_boundary_id": exit_,
        "boundary_continuity": boundary_continuity,
        "transition_execution": transition,
        "generation_mode": gen_mode,
        "reference_assets": assets,
    }


def _parse_source_location(block: str) -> dict:
    m = _require_single_match(_SOURCE_LOCATION_RE, block, "原文定位：[M]")
    return {
        "scene_id": m.group("scene_id"),
        "start": int(m.group("start")),
        "end": int(m.group("end")),
    }


def _parse_enum_field(block: str, pattern: re.Pattern, field_name: str, valid: frozenset) -> str:
    m = _require_single_match(pattern, block, field_name)
    value = m.group("mode")
    if value not in valid:
        raise CompilerError(f"Invalid {field_name} '{value}'; must be one of {sorted(valid)}")
    return value


def _parse_boundary(block: str, pattern: re.Pattern, field_name: str) -> str:
    m = _require_single_match(pattern, block, field_name)
    return m.group("id")


def _parse_optional_boundary(
    block: str, pattern: re.Pattern, field_name: str
) -> str | None:
    matches = list(pattern.finditer(block))
    if len(matches) > 1:
        raise CompilerError(f"Duplicate field '{field_name}' in Shot block")
    return matches[0].group("id") if matches else None


def _parse_asset_list(block: str) -> list[dict]:
    m = _require_single_match(_ASSET_LIST_RE, block, "参考资产：[M]")
    if m.group("none") is not None:
        return []
    raw = m.group("ids").strip()
    if not raw:
        return []
    result = []
    seen: set[tuple[str, str]] = set()
    for token in raw.split(","):
        binding = token.strip()
        if not binding:
            raise CompilerError("Empty asset binding in '参考资产：[M]'")
        if binding.count("|") != 1:
            raise CompilerError(
                "Each reference asset must use '<asset_id>|<responsibility>'; "
                f"got '{binding}'"
            )
        asset_id, responsibility = (part.strip() for part in binding.split("|", 1))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", asset_id):
            raise CompilerError(f"Invalid asset_id '{asset_id}'")
        if responsibility not in VALID_RESPONSIBILITIES:
            raise CompilerError(
                f"Invalid responsibility '{responsibility}' for '{asset_id}'; "
                f"must be one of {sorted(VALID_RESPONSIBILITIES)}"
            )
        pair = (asset_id, responsibility)
        if pair in seen:
            raise CompilerError(f"Duplicate asset binding '{binding}'")
        seen.add(pair)
        result.append({"asset_id": asset_id, "responsibility": responsibility})
    return result


def _parse_story_fact_text(block: str) -> str:
    m = _require_single_match(_STORY_FACT_RE, block, "剧本事实：[D]")
    text = m.group("text").strip()
    if not text:
        raise CompilerError("Empty '剧本事实：[D]' field in shot block")
    return text


def _parse_optional_state_keys(block: str, marker: str) -> dict | None:
    marker_pattern = re.compile(rf"^{re.escape(marker)}\s*$", re.MULTILINE)
    matches = list(marker_pattern.finditer(block))
    if not matches:
        return None
    if len(matches) > 1:
        raise CompilerError(f"Duplicate state block '{marker}'")
    return _parse_state_keys(block, marker)


def _parse_state_keys(block: str, marker: str) -> dict:
    """Extract structured state keys from a state block.

    The state block starts with the marker line and contains indented lines
    with key:value pairs for characters, props, light_main, and action_phase.
    """
    marker_pattern = re.compile(rf"^{re.escape(marker)}\s*$", re.MULTILINE)
    marker_match = _require_single_match(marker_pattern, block, marker)
    section = block[marker_match.end():]

    characters = []
    props = []
    light_main = None
    action_phase = None
    scene_state: dict[str, str] = {}
    character_ids: set[str] = set()
    prop_ids: set[str] = set()
    machine_block_started = False

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # State keys are a contiguous Markdown bullet block immediately after
        # the marker. The next unindented Director label ends this block.
        if not line.startswith("-"):
            if machine_block_started:
                break
            raise CompilerError(f"Expected state-key bullet after '{marker}', got: {line!r}")
        machine_block_started = True

        cm = _CHARACTER_LINE.match(line)
        if cm:
            entity_id = cm.group("entity_id")
            if entity_id in character_ids:
                raise CompilerError(f"Duplicate character '{entity_id}' in {marker}")
            character_ids.add(entity_id)
            character = {
                "entity_id": entity_id,
                "position": cm.group("position"),
                "facing": cm.group("facing"),
                "screen_direction": cm.group("screen_direction"),
                "posture": cm.group("posture"),
            }
            if cm.group("wardrobe"):
                character["wardrobe"] = cm.group("wardrobe")
            if cm.group("injury"):
                character["injury"] = cm.group("injury")
            characters.append(character)
            continue

        pm = _PROP_LINE.match(line)
        if pm:
            prop_id = pm.group("prop_id")
            if prop_id in prop_ids:
                raise CompilerError(f"Duplicate prop '{prop_id}' in {marker}")
            prop_ids.add(prop_id)
            props.append({
                "prop_id": prop_id,
                "held_by": pm.group("held_by"),
                "location": pm.group("location"),
            })
            continue

        lm = _LIGHT_LINE.match(line)
        if lm:
            if light_main is not None:
                raise CompilerError(f"Duplicate 'light_main' in {marker}")
            light_main = {
                "direction": lm.group("direction"),
                "color_temp_k": int(lm.group("k")),
                "ratio": lm.group("ratio"),
            }
            continue

        am = _ACTION_PHASE_LINE.match(line)
        if am:
            if action_phase is not None:
                raise CompilerError(f"Duplicate 'action_phase' in {marker}")
            phase = am.group("phase")
            if phase not in VALID_ACTION_PHASES:
                raise CompilerError(
                    f"Invalid action_phase '{phase}' in {marker}; must be one of {sorted(VALID_ACTION_PHASES)}"
                )
            action_phase = phase
            continue

        for key, pattern in (
            ("story_time", _STORY_TIME_LINE),
            ("weather", _WEATHER_LINE),
            ("environment", _ENVIRONMENT_LINE),
        ):
            state_match = pattern.match(line)
            if state_match:
                if key in scene_state:
                    raise CompilerError(f"Duplicate '{key}' in {marker}")
                scene_state[key] = state_match.group("value")
                break
        else:
            raise CompilerError(f"Malformed or unknown state-key line in {marker}: {line!r}")
        continue

    if light_main is None:
        raise CompilerError(f"Missing 'light_main' in {marker} block")
    if action_phase is None:
        raise CompilerError(f"Missing 'action_phase' in {marker} block")

    result = {
        "characters": characters,
        "props": props,
        "light_main": light_main,
        "action_phase": action_phase,
    }
    result.update(scene_state)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile DIRECTOR_MASTER.md into SHOT_MANIFEST.json"
    )
    parser.add_argument("master", type=Path, help="Path to DIRECTOR_MASTER.md")
    parser.add_argument("output", type=Path, nargs="?", help="Output path for SHOT_MANIFEST.json (default: same dir)")
    args = parser.parse_args()

    master_path: Path = args.master
    if not master_path.is_file():
        print(f"Master file not found: {master_path}", file=sys.stderr)
        return 2

    output_path: Path = args.output or master_path.with_name("SHOT_MANIFEST.json")

    try:
        compile_to_file(master_path, output_path)
        manifest = json.loads(output_path.read_text(encoding="utf-8"))
        shot_count = len(manifest["shots"])
        print(f"Manifest compiled: {shot_count} shot(s) -> {output_path}")
        return 0
    except CompilerError as exc:
        print(f"Compiler error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
