"""Stable prompts for the text-only DeepSeek Director provider."""

from __future__ import annotations

import json
from dataclasses import MISSING, fields, is_dataclass
from types import UnionType
from typing import Any, Literal, Mapping, Union, get_args, get_origin, get_type_hints

from .contracts import (
    HOLDER_HANDS,
    REFERENCE_BINDING_ROLES,
    REFERENCE_BINDING_SCOPES,
    REJECTION_CODES,
    SCREEN_POSITIONS,
    TRANSITION_MODES,
)


TEXT_ONLY_DIRECTOR_SYSTEM = """\
You are the persistent Director for one episode.
Work only from the approved text facts and bounded knowledge packet supplied.
Do not invent backstory, off-screen events, motivations, objects, locations, or
facts not present in those inputs.  If an input does not establish a fact,
express it as an unresolved question or omit it.
You are not an agentic CLI session. You have no tools. Do not invoke, request,
or discuss tools, skills, tasks, shell commands, files, browser actions, or
permissions. Work solely from the supplied prompt text and return directly.
Use maximum internal reasoning effort. Systematically stress-test approved
facts, constraint conflicts, alternatives, causal action paths, edge cases,
and failure modes before selecting an answer. Keep that reasoning private.
Output only the requested JSON contract. Where the named contract provides
reason, tradeoff, risk, or rejection fields, write concise auditable summaries
of decisive facts, rejected alternatives, and unresolved risks. Never output
chain-of-thought, hidden analysis, or intermediate reasoning steps.
When an exact output-field lock is supplied, it is the complete top-level
allowlist. Emit every listed field exactly once. Do not rename, omit, add,
nest, substitute, or use legacy aliases for any field, even if another
directing schema seems more natural.
Obey every locked JSON type literally: an array must be written with `[]` even
for one item, an object with `{}`, and a string must never replace either.
The exact output shape lock is recursive: every nested object has the same
exclusive-field rule. Do not replace a nested contract object with a semantic
summary, a legacy director schema, or a natural-language explanation.
When an exact enum lock is supplied, each value must match one listed literal
exactly. Do not use a synonym, a descriptive phrase, a different case, or an
invented spatial label.
Every path in an exact identifier lock must contain a non-empty approved
identifier. Never emit an empty string, null, prose, or a placeholder for any
`*_id` field, except the literal `none` where an explicit cross-field rule
requires that reserved sentinel.

You are a text model. You may validate textual contracts, timelines, field
homology, and stated constraints. You must never claim that an image or video
was visually inspected, that a mirror flip was absent in rendered media, or
that hands, gaze, blocking, wardrobe, lighting, or prop orientation were
visually verified. Those conclusions require separate frame evidence.

Return one JSON object only. Do not use Markdown fences, comments, prose before
or after JSON, global episode timestamps, internal state hashes, workflow
labels, image-slot numbers, or instructions to a later video.
"""


STAGE_RULES: Mapping[str, str] = {
    "E0": (
        "Define persistent episode-level dramatic direction. Do not prescribe "
        "shots, lenses, camera motion, cuts, or prompt wording. Keep every "
        "free-text field to one factual phrase of at most 180 characters; do "
        "not serialize private reasoning."
    ),
    "S1": (
        "Diagnose scene function, change, audience information, character "
        "knowledge, performance question, and director problems. Do not "
        "prescribe shots, lenses, camera motion, cuts, or prompt wording. Keep "
        "every free-text field to one factual phrase of at most 180 characters; "
        "do not serialize private reasoning."
    ),
    "B0": (
        "Commit motivated character, prop, gaze, action-path, and spatial "
        "states before any camera choice. Preserve every approved fact. For "
        "every beats[i], action_paths is mandatory and non-empty: provide one "
        "or more concise causal strings in the form 'character: motivation -> "
        "physical action -> spatial/result state'. Empty arrays, placeholders, "
        "and camera/edit language are invalid. Keep every free-text value to "
        "a compact factual phrase (at most 180 characters); internal reasoning "
        "may be extensive but must not be serialized."
    ),
    "B1": (
        "After B0 and K2, compare genuinely different execution candidates and "
        "produce the one VisualExecutionContract used by both storyboard and "
        "video projections. Use segment-local time beginning at tick 0. Keep "
        "each free-text field to a compact executable phrase of at most 240 "
        "characters; do not serialize private reasoning."
    ),
}


STAGE_SEMANTIC_CHECKLISTS: Mapping[str, tuple[str, ...]] = {
    "E0": (
        "Every free-text value is at most 180 characters and contains only a concise episode-intent fact.",
        "No camera, edit, prompt, hidden analysis, or media-verification language appears.",
    ),
    "S1": (
        "Every free-text value is at most 180 characters and contains only a concise scene-intent or Director-problem fact.",
        "No camera, edit, prompt, hidden analysis, or media-verification language appears.",
    ),
    "B0": (
        "Every beats[i].character_states contains at least one state.",
        "Every beats[i].action_paths contains at least one causal action path; [] is invalid.",
        "Every beats[i].constraint_refs contains at least one approved fact or user constraint reference.",
        "Each action path names a motivated physical change and its resulting spatial state, not a camera action.",
        "Each B0 free-text value is at most 180 characters and contains no hidden analysis or explanatory prose.",
        "For each beats[].prop_states[]: holder_hand='none' requires holder_character_id='none'; otherwise holder_character_id must exactly equal a character_id present in that same beat.",
        "No shot, lens, camera, cut, video-prompt, image-slot, or media-verification claim appears in B0.",
    ),
    "B1": (
        "Every free-text value is at most 240 characters and describes only an executable VEC field.",
        "Every visual_execution_draft.segments[i].start_tick is exactly 0; each segment is an independently generated local timeline, never a cumulative episode timeline.",
        "Every candidate has non-empty evidence_refs and freedom_corridor arrays.",
        "Emit every required reference binding supplied in approved_input, including character identity and wardrobe, prop geometry, and scene layout requirements.",
        "No global timestamp, workflow label, state hash, image-slot notation, next-video instruction, or hidden analysis appears.",
    ),
}


_FIELD_ENUMS: Mapping[tuple[str, str], tuple[str, ...]] = {
    ("DirectorProblem", "priority"): ("normal", "high"),
    ("CharacterBlockingState", "screen_position"): tuple(sorted(SCREEN_POSITIONS)),
    ("PropBlockingState", "holder_hand"): tuple(sorted(HOLDER_HANDS)),
    ("RejectedOption", "rejection_code"): tuple(sorted(REJECTION_CODES)),
    ("InternalBoundary", "mode"): tuple(sorted(TRANSITION_MODES)),
    ("ReferenceBindingRequirement", "role"): tuple(sorted(REFERENCE_BINDING_ROLES)),
    ("ReferenceBindingRequirement", "scope_kind"): tuple(sorted(REFERENCE_BINDING_SCOPES)),
}


# The transport schema must reject impossible empty collections before the
# response reaches the semantic dataclass constructor.  This list mirrors only
# fields whose local contracts explicitly require at least one item; it does
# not turn optional creative fields into false mandatory constraints.
_FIELD_MIN_ITEMS: Mapping[tuple[str, str], int] = {
    ("CharacterBlockingState", "visible_body_parts"): 1,
    ("BlockingBeat", "character_states"): 1,
    ("BlockingBeat", "action_paths"): 1,
    ("BlockingBeat", "constraint_refs"): 1,
    ("BlockingCommit", "beats"): 1,
    ("BlockingCommit", "constraint_refs"): 1,
}


def _shape(annotation: Any) -> Any:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if is_dataclass(annotation):
        hints = get_type_hints(annotation)
        return {
            field.name: _shape(hints[field.name])
            for field in fields(annotation)
        }
    if origin in {tuple, list}:
        item = args[0] if args else Any
        return [_shape(item)]
    if origin in {dict, Mapping}:
        value = args[1] if len(args) > 1 else Any
        return {"<key>": _shape(value)}
    if origin in {Union, UnionType}:
        non_none = [item for item in args if item is not type(None)]
        return {
            "one_of": [_shape(item) for item in non_none],
            "nullable": len(non_none) != len(args),
        }
    if annotation is str:
        return "<string>"
    if annotation is int:
        return "<integer>"
    if annotation is bool:
        return "<boolean>"
    if annotation is float:
        return "<number>"
    if origin is Literal and len(args) == 1:
        return args[0]
    return "<value>"


def _enum_locks(annotation: Any, *, path: str = "$") -> Mapping[str, tuple[str, ...]]:
    """Flatten enum-bound contract fields into compact JSON-path locks."""

    origin = get_origin(annotation)
    args = get_args(annotation)
    if is_dataclass(annotation):
        locks: dict[str, tuple[str, ...]] = {}
        hints = get_type_hints(annotation)
        for field in fields(annotation):
            field_path = f"{path}.{field.name}"
            allowed = _FIELD_ENUMS.get((annotation.__name__, field.name))
            if allowed is not None:
                locks[field_path] = allowed
            locks.update(_enum_locks(hints[field.name], path=field_path))
        return locks
    if origin in {tuple, list}:
        item = args[0] if args else Any
        return _enum_locks(item, path=f"{path}[]")
    if origin in {Union, UnionType}:
        locks: dict[str, tuple[str, ...]] = {}
        for item in args:
            if item is not type(None):
                locks.update(_enum_locks(item, path=path))
        return locks
    return {}


def _identifier_locks(annotation: Any, *, path: str = "$") -> tuple[str, ...]:
    """Flatten non-empty identifier fields into compact JSON-path locks."""

    origin = get_origin(annotation)
    args = get_args(annotation)
    if is_dataclass(annotation):
        locks: list[str] = []
        hints = get_type_hints(annotation)
        for field in fields(annotation):
            field_path = f"{path}.{field.name}"
            if field.name.endswith("_id"):
                locks.append(field_path)
            locks.extend(_identifier_locks(hints[field.name], path=field_path))
        return tuple(locks)
    if origin in {tuple, list}:
        item = args[0] if args else Any
        return _identifier_locks(item, path=f"{path}[]")
    if origin in {Union, UnionType}:
        locks: list[str] = []
        for item in args:
            if item is not type(None):
                locks.extend(_identifier_locks(item, path=path))
        return tuple(locks)
    return ()


def contract_shape(contract_type: type) -> Mapping[str, Any]:
    shape = _shape(contract_type)
    if not isinstance(shape, dict):
        raise TypeError("Director output contract must be a dataclass object")
    return shape


def _shape_json_type(value: Any) -> str:
    """Return the literal JSON container type represented by a shape value."""

    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int | float):
        return "number"
    if value is None:
        return "null"
    return "string"


def _json_schema(
    annotation: Any,
    *,
    max_string_length: int | None = None,
) -> Mapping[str, Any]:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if is_dataclass(annotation):
        hints = get_type_hints(annotation)
        contract_fields = tuple(fields(annotation))
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                field.name
                for field in contract_fields
                if field.default is MISSING and field.default_factory is MISSING
            ],
            "properties": {
                field.name: _field_json_schema(
                    annotation.__name__,
                    field.name,
                    hints[field.name],
                    max_string_length=max_string_length,
                )
                for field in contract_fields
            },
        }
    if origin in {tuple, list}:
        return {
            "type": "array",
            "items": _json_schema(
                args[0] if args else Any,
                max_string_length=max_string_length,
            ),
        }
    if origin in {dict, Mapping}:
        return {
            "type": "object",
            "additionalProperties": _json_schema(
                args[1] if len(args) > 1 else Any,
                max_string_length=max_string_length,
            ),
        }
    if origin in {Union, UnionType}:
        return {
            "anyOf": [
                _json_schema(item, max_string_length=max_string_length)
                for item in args
                if item is not type(None)
            ]
            + ([{"type": "null"}] if type(None) in args else []),
        }
    if origin is Literal:
        return {"enum": list(args)} if args else {}
    if annotation is str:
        schema: dict[str, Any] = {"type": "string", "minLength": 1}
        if max_string_length is not None:
            schema["maxLength"] = max_string_length
        return schema
    if annotation is int:
        return {"type": "integer"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is float:
        return {"type": "number"}
    return {}


def _field_json_schema(
    owner_name: str,
    field_name: str,
    annotation: Any,
    *,
    max_string_length: int | None = None,
) -> Mapping[str, Any]:
    schema = dict(
        _json_schema(annotation, max_string_length=max_string_length)
    )
    allowed = _FIELD_ENUMS.get((owner_name, field_name))
    if allowed is not None:
        schema["enum"] = list(allowed)
    min_items = _FIELD_MIN_ITEMS.get((owner_name, field_name))
    if min_items is not None:
        schema["minItems"] = min_items
    return schema


def strict_json_schema(
    contract_type: type,
    *,
    max_string_length: int | None = None,
) -> Mapping[str, Any]:
    """Return the CLI transport schema; semantic validation remains local."""

    if max_string_length is not None and max_string_length < 1:
        raise ValueError("max_string_length must be positive")
    schema = _json_schema(
        contract_type,
        max_string_length=max_string_length,
    )
    if schema.get("type") != "object":
        raise TypeError("Director output contract must be a dataclass object")
    return schema


def build_stage_messages(
    *,
    stage: str,
    contract_type: type,
    approved_input: Mapping[str, Any],
    include_contract_shape: bool = True,
) -> tuple[Mapping[str, str], Mapping[str, str]]:
    if stage not in STAGE_RULES:
        raise ValueError(f"unknown Director stage: {stage}")
    output_shape = contract_shape(contract_type)
    enum_locks = _enum_locks(contract_type)
    identifier_locks = _identifier_locks(contract_type)
    payload: dict[str, Any] = {
        "stage": stage,
        "stage_rule": STAGE_RULES[stage],
        "approved_input": approved_input,
        "required_output_contract": contract_type.__name__,
        "exact_output_field_lock": {
            "allowed_top_level_fields": sorted(output_shape),
            "required_top_level_fields": sorted(output_shape),
            "additional_top_level_fields_forbidden": True,
            "top_level_json_types": {
                field: _shape_json_type(output_shape[field])
                for field in sorted(output_shape)
            },
        },
        "exact_output_shape_lock": output_shape,
        "output_status_ceiling": "TEXT_VALIDATED",
    }
    if enum_locks:
        payload["exact_output_enum_lock"] = {
            path: list(values) for path, values in sorted(enum_locks.items())
        }
    if identifier_locks:
        payload["exact_identifier_lock"] = list(identifier_locks)
    if stage == "B0":
        payload["exact_cross_field_lock"] = [
            "$.beats[].prop_states[]: holder_hand='none' => holder_character_id='none'",
            "$.beats[].prop_states[]: holder_hand!='none' => holder_character_id equals a $.beats[].character_states[].character_id in the same beat",
        ]
    if stage == "B1":
        payload["exact_cross_field_lock"] = [
            "$.visual_execution_draft.segments[].start_tick = 0",
            "$.visual_execution_draft.segments[].end_tick > 0",
            "Each generation segment has its own local clock; never carry a prior segment's end_tick into the next segment's start_tick.",
            "$.visual_execution_draft.shots[].mirror_flip_forbidden = true",
            "$.candidates[].evidence_refs and $.candidates[].freedom_corridor are non-empty arrays.",
            "$.visual_execution_draft.reference_binding_requirements covers every approved_input.required_reference_bindings tuple of role, scope_kind, and scope_id.",
        ]
    checklist = STAGE_SEMANTIC_CHECKLISTS.get(stage)
    if checklist:
        payload["semantic_preflight_checklist"] = checklist
    if include_contract_shape:
        # Retain the legacy marker for the stdin fallback contract without
        # serializing a second copy of a potentially large B1 shape.
        payload["required_output_shape"] = {
            "source": "exact_output_shape_lock",
            "locally_enforced": True,
        }
    return (
        {"role": "system", "content": TEXT_ONLY_DIRECTOR_SYSTEM},
        {
            "role": "user",
            "content": json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        },
    )


__all__ = [
    "STAGE_RULES",
    "TEXT_ONLY_DIRECTOR_SYSTEM",
    "build_stage_messages",
    "contract_shape",
    "strict_json_schema",
]
