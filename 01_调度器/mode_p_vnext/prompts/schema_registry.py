"""Compact native transport schemas for Drafts and scoped repair patches."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, Mapping

from .budgets import BudgetReport, PromptBudgetGate
from .signatures import Stage, StageSignature


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class DraftSchema:
    contract_name: str
    version: str
    document: Mapping[str, Any]
    canonical_json: str
    digest: str
    budget_report: BudgetReport

    @property
    def character_count(self) -> int:
        return len(self.canonical_json)


class _FrozenSchemaDict(dict[str, Any]):
    """A JSON-serializable mapping that cannot alter a sealed schema."""

    def __init__(self, values: Mapping[str, Any]) -> None:
        dict.__init__(self)
        dict.update(self, values)

    @staticmethod
    def _immutable(*_args: object, **_kwargs: object) -> None:
        raise TypeError("schema document is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable

    def __ior__(self, _other: object) -> "_FrozenSchemaDict":
        self._immutable()
        raise AssertionError("unreachable")


class _FrozenSchemaList(list[Any]):
    """A JSON-serializable list that cannot alter a sealed schema."""

    def __init__(self, values: list[Any]) -> None:
        list.__init__(self, values)

    @staticmethod
    def _immutable(*_args: object, **_kwargs: object) -> None:
        raise TypeError("schema document is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    __iadd__ = _immutable
    __imul__ = _immutable
    append = _immutable
    clear = _immutable
    extend = _immutable
    insert = _immutable
    pop = _immutable
    remove = _immutable
    reverse = _immutable
    sort = _immutable


def _freeze_schema_document(value: Any) -> Any:
    """Recursively seal the shared schema authority without losing JSON support."""

    if isinstance(value, Mapping):
        return _FrozenSchemaDict(
            {str(key): _freeze_schema_document(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return _FrozenSchemaList([_freeze_schema_document(item) for item in value])
    return value


_SCHEMAS: Mapping[Stage, Mapping[str, Any]] = {
    Stage.I0: {
        "type": "object",
        "title": "FactExtractionDraft",
        "additionalProperties": False,
        "required": ["facts"],
        "properties": {
            "facts": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "source_start",
                        "source_end",
                        "semantic_type",
                        "statement",
                    ],
                    "properties": {
                        "source_start": {"type": "integer", "minimum": 0},
                        "source_end": {"type": "integer", "minimum": 1},
                        "semantic_type": {
                            "enum": [
                                "narrative",
                                "character",
                                "wardrobe",
                                "prop",
                                "setting",
                                "dialogue",
                                "continuity",
                                "asset",
                            ]
                        },
                        "statement": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 1_000,
                        },
                        "subject_id": {"type": "string", "minLength": 1, "maxLength": 160},
                        "spoken_text": {"type": "string", "minLength": 1, "maxLength": 1_000},
                    },
                },
            }
        },
    },
    Stage.E0: {
        "type": "object", "title": "EpisodeDirectionDraft", "additionalProperties": False,
        "required": ["dramatic_promise", "audience_contract", "tension_curve", "visual_principles", "continuity_priorities", "unresolved_questions"],
        "properties": {
            "dramatic_promise": {"type": "string", "maxLength": 180},
            "audience_contract": {"type": "string", "maxLength": 180},
            "tension_curve": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
            "visual_principles": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
            "continuity_priorities": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
            "unresolved_questions": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
        },
    },
    Stage.S1: {
        "type": "object", "title": "SceneIntentDraft", "additionalProperties": False,
        "required": ["scene_purpose", "state_change", "audience_information", "character_knowledge", "performance_questions", "director_problems", "continuity_effects", "unresolved_questions"],
        "properties": {
            "scene_purpose": {"type": "string", "maxLength": 180},
            "state_change": {"type": "string", "maxLength": 180},
            "audience_information": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
            "character_knowledge": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
            "performance_questions": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
            "director_problems": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
            "continuity_effects": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
            "unresolved_questions": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}},
        },
    },
    Stage.B0: {
        "type": "object", "title": "BlockingDraft", "additionalProperties": False,
        "required": ["beats"],
        "properties": {
            "beats": {
                "type": "array", "minItems": 1, "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["ordinal", "dramatic_action", "character_states", "prop_states", "gaze_relations", "action_paths", "continuity_effect"],
                    "properties": {
                        "ordinal": {"type": "integer", "minimum": 1},
                        "dramatic_action": {"type": "string", "maxLength": 180},
                        "character_states": {"type": "array", "minItems": 1, "maxItems": 12, "items": {"type": "object", "additionalProperties": {"type": "string", "maxLength": 180}}},
                        "prop_states": {"type": "array", "maxItems": 12, "items": {"type": "object", "additionalProperties": {"type": "string", "maxLength": 180}}},
                        "gaze_relations": {"type": "array", "maxItems": 12, "items": {"type": "string", "maxLength": 180}},
                        "action_paths": {"type": "array", "minItems": 1, "maxItems": 12, "items": {"type": "string", "maxLength": 180}},
                        "continuity_effect": {"type": "string", "maxLength": 180},
                    },
                },
            },
        },
    },
    Stage.B1: {
        "type": "object",
        "title": "ExecutionDesignDraft",
        "additionalProperties": False,
        "required": [
            "curve_points", "decisions", "shots", "transition_intents", "handoff_intent",
        ],
        "properties": {
            "curve_points": {"type": "array", "minItems": 1, "maxItems": 24, "items": {"type": "object", "additionalProperties": False, "required": ["dramatic_beat_ordinal", "intensity", "explanation"], "properties": {"dramatic_beat_ordinal": {"type": "integer", "minimum": 1}, "intensity": {"type": "integer", "minimum": 0, "maximum": 100}, "explanation": {"type": "string", "maxLength": 240}}}},
            "decisions": {"type": "array", "minItems": 1, "maxItems": 24, "items": {"type": "object", "additionalProperties": False, "required": ["scope", "basis", "locked_by", "options", "selected_index", "rationale", "tradeoff"], "properties": {"scope": {"type": "string", "maxLength": 120}, "basis": {"enum": ["locked", "choice"]}, "locked_by": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}}, "options": {"type": "array", "minItems": 1, "maxItems": 2, "items": {"type": "string", "maxLength": 240}}, "selected_index": {"type": "integer", "minimum": 0, "maximum": 1}, "rationale": {"type": "string", "maxLength": 240}, "tradeoff": {"type": "string", "maxLength": 240}}, "allOf": [{"if": {"properties": {"basis": {"const": "locked"}}, "required": ["basis"]}, "then": {"properties": {"options": {"maxItems": 1}, "locked_by": {"minItems": 1}}}}, {"if": {"properties": {"basis": {"const": "choice"}}, "required": ["basis"]}, "then": {"properties": {"options": {"minItems": 2, "maxItems": 2}, "locked_by": {"maxItems": 0}}}}]}},
            "shots": {
                "type": "array", "minItems": 1, "maxItems": 48,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": [
                        "shot_ordinal", "blocking_beat_ordinal", "duration_intent",
                        "generation_mode", "composition", "camera", "lighting",
                        "performance", "visual_beats", "reference_binding_intents",
                        "dialogue_binding_intents", "creative_notes",
                    ],
                    "properties": {
                        "shot_ordinal": {"type": "integer", "minimum": 1},
                        "blocking_beat_ordinal": {"type": "integer", "minimum": 1},
                        "duration_intent": {"enum": ["brief", "standard", "extended"]},
                        "generation_mode": {"enum": ["text_only", "first_last_frame", "omni_reference"]},
                        "composition": {"type": "string", "minLength": 1, "maxLength": 240},
                        "camera": {"type": "string", "minLength": 1, "maxLength": 240},
                        "lighting": {"type": "string", "minLength": 1, "maxLength": 240},
                        "performance": {"type": "string", "minLength": 1, "maxLength": 240},
                        "visual_beats": {
                            "type": "array", "minItems": 1, "maxItems": 4,
                            "items": {
                                "type": "object", "additionalProperties": False,
                                "required": ["visual_beat_ordinal", "phase", "subject_state", "attention", "storyboard_role"],
                                "properties": {
                                    "visual_beat_ordinal": {"type": "integer", "minimum": 1},
                                    "phase": {"enum": ["entry", "action", "reaction", "handoff"]},
                                    "subject_state": {"type": "string", "minLength": 1, "maxLength": 240},
                                    "attention": {"type": "string", "minLength": 1, "maxLength": 240},
                                    "storyboard_role": {"enum": ["required", "optional", "omit"]},
                                },
                            },
                        },
                        "reference_binding_intents": {
                            "type": "array", "maxItems": 16,
                            "items": {
                                "type": "object", "additionalProperties": False,
                                "required": ["shot_ordinal", "visual_beat_ordinal", "fact_handle", "responsibility"],
                                "properties": {
                                    "shot_ordinal": {"type": "integer", "minimum": 1},
                                    "visual_beat_ordinal": {"anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
                                    "fact_handle": {"type": "string", "pattern": "^fh:[0-9a-f]{64}$"},
                                    "responsibility": {"enum": ["character_identity", "wardrobe_continuity", "prop_identity", "setting_continuity", "first_frame", "last_frame"]},
                                },
                            },
                        },
                        "dialogue_binding_intents": {
                            "type": "array", "maxItems": 16,
                            "items": {
                                "type": "object", "additionalProperties": False,
                                "required": ["shot_ordinal", "visual_beat_ordinal", "fact_handle", "placement_phase"],
                                "properties": {
                                    "shot_ordinal": {"type": "integer", "minimum": 1},
                                    "visual_beat_ordinal": {"type": "integer", "minimum": 1},
                                    "fact_handle": {"type": "string", "pattern": "^fh:[0-9a-f]{64}$"},
                                    "placement_phase": {"enum": ["opening", "early", "middle", "late", "closing"]},
                                },
                            },
                        },
                        "creative_notes": {"type": "string", "minLength": 1, "maxLength": 240},
                    },
                },
            },
            "transition_intents": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "handoff_intent": {"type": "string", "maxLength": 240},
        },
    },
}

# A StageSchema is local deterministic authority.  The compiler, native
# transport and local decoder may all read this same document, but no caller
# may mutate it after its canonical JSON and digest have been established.
_SCHEMAS = MappingProxyType(
    {
        stage: _freeze_schema_document(document)
        for stage, document in _SCHEMAS.items()
    }
)


def _repair_schema_document(signature: StageSignature) -> Mapping[str, Any]:
    """Return the compact native schema for one scoped ContractPatch response."""

    return {
        "type": "object",
        "title": "ContractPatch",
        "additionalProperties": False,
        "required": ["stage", "draft_digest", "repair_scope", "values"],
        "properties": {
            "stage": {"enum": [signature.stage.value]},
            "draft_digest": {"type": "string", "minLength": 64, "maxLength": 64},
            "repair_scope": {
                "type": "array",
                "minItems": 1,
                "maxItems": 16,
                "items": {"type": "string", "minLength": 1, "maxLength": 512},
            },
            "values": {"type": "object", "additionalProperties": True},
        },
    }


def _assert_repair_contract(
    signature: StageSignature, document: Mapping[str, Any]
) -> None:
    """Ensure a repair transport cannot silently become a full Draft request."""

    expected = {"type", "title", "additionalProperties", "required", "properties"}
    fields = {"stage", "draft_digest", "repair_scope", "values"}
    if set(document) != expected or document.get("title") != "ContractPatch":
        raise ValueError("repair schema must be the compact ContractPatch")
    if document.get("additionalProperties") is not False:
        raise ValueError("repair schema must reject fields outside ContractPatch")
    if set(document.get("required", ())) != fields or set(document.get("properties", {})) != fields:
        raise ValueError("repair schema must declare only ContractPatch fields")
    if document["properties"]["stage"].get("enum") != [signature.stage.value]:
        raise ValueError("repair schema must bind the requested stage")


def _assert_schema_node_matches_draft(
    node: Mapping[str, Any], draft_type: type[Any], label: str
) -> None:
    expected = {field.name for field in fields(draft_type)}
    properties = node.get("properties")
    required = node.get("required")
    if not isinstance(properties, Mapping) or not isinstance(required, list):
        raise ValueError(f"{label} must declare properties and required fields")
    if set(properties) != expected or set(required) != expected:
        raise ValueError(
            f"{label} diverges from its canonical creative Draft contract"
        )


def _assert_canonical_draft_contract(
    stage: Stage, document: Mapping[str, Any]
) -> None:
    """Fail before provider I/O if the transport cannot decode its v3.1 Draft."""

    from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingDraft
    from mode_p_vnext.domain.decisions import DecisionDraft, VisualCurvePointDraft
    from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
    from mode_p_vnext.domain.vec import (
        ExecutionDesignDraft,
        DialogueBindingIntent,
        ReferenceBindingIntent,
        ShotDesignDraft,
        VisualBeatDraft,
    )

    if stage is Stage.I0:
        if set(document) != {
            "type", "title", "additionalProperties", "required", "properties"
        } or document.get("title") != "FactExtractionDraft":
            raise ValueError("I0 schema must be the compact FactExtractionDraft")
        facts = document.get("properties", {}).get("facts")
        if not isinstance(facts, Mapping) or facts.get("type") != "array":
            raise ValueError("I0 facts schema must be an array")
        item = facts.get("items")
        if not isinstance(item, Mapping) or item.get("additionalProperties") is not False:
            raise ValueError("I0 fact schema must be a closed object")
        required = {"source_start", "source_end", "semantic_type", "statement"}
        expected = required | {"subject_id", "spoken_text"}
        if set(item.get("properties", {})) != expected or set(item.get("required", ())) != required:
            raise ValueError("I0 fact schema must declare only source-anchored fields")
        if item["properties"]["semantic_type"].get("enum") != [
            "narrative", "character", "wardrobe", "prop", "setting",
            "dialogue", "continuity", "asset",
        ]:
            raise ValueError("I0 semantic_type schema must match canonical fact semantics")
        for field_name in ("statement", "subject_id", "spoken_text"):
            if item["properties"][field_name].get("minLength") != 1:
                raise ValueError(f"I0 {field_name} schema must reject empty text")
        return
    if stage is Stage.E0:
        _assert_schema_node_matches_draft(
            document, EpisodeDirectionDraft, "E0 schema"
        )
        return
    if stage is Stage.S1:
        _assert_schema_node_matches_draft(
            document, SceneIntentDraft, "S1 schema"
        )
        return
    if stage is Stage.B0:
        _assert_schema_node_matches_draft(document, BlockingDraft, "B0 schema")
        beats = document["properties"]["beats"]["items"]
        if not isinstance(beats, Mapping):
            raise ValueError("B0 beats schema must be an object")
        _assert_schema_node_matches_draft(
            beats, BlockingBeatDraft, "B0 beat schema"
        )
        return
    if stage is Stage.B1:
        _assert_schema_node_matches_draft(
            document, ExecutionDesignDraft, "B1 schema"
        )
        properties = document["properties"]
        curve = properties["curve_points"]["items"]
        decisions = properties["decisions"]["items"]
        shots = properties["shots"]["items"]
        if not all(isinstance(node, Mapping) for node in (curve, decisions, shots)):
            raise ValueError("B1 nested schemas must be objects")
        _assert_schema_node_matches_draft(
            curve, VisualCurvePointDraft, "B1 curve-point schema"
        )
        _assert_schema_node_matches_draft(
            decisions, DecisionDraft, "B1 decision schema"
        )
        _assert_schema_node_matches_draft(shots, ShotDesignDraft, "B1 shot schema")
        visual_beats = shots["properties"]["visual_beats"]["items"]
        if not isinstance(visual_beats, Mapping):
            raise ValueError("B1 visual-beat schema must be an object")
        _assert_schema_node_matches_draft(
            visual_beats, VisualBeatDraft, "B1 visual-beat schema"
        )
        references = shots["properties"]["reference_binding_intents"]["items"]
        dialogue = shots["properties"]["dialogue_binding_intents"]["items"]
        if not isinstance(references, Mapping) or not isinstance(dialogue, Mapping):
            raise ValueError("B1 binding schemas must be objects")
        _assert_schema_node_matches_draft(
            references, ReferenceBindingIntent, "B1 reference-binding schema"
        )
        _assert_schema_node_matches_draft(
            dialogue, DialogueBindingIntent, "B1 dialogue-binding schema"
        )
        return
    raise ValueError(f"unsupported Draft stage: {stage.value}")


class DraftSchemaRegistry:
    """Resolve a versioned compact schema and enforce its stage budget."""

    def schema_for(self, signature: StageSignature) -> DraftSchema:
        document = _SCHEMAS.get(signature.stage)
        if document is None:
            raise ValueError(f"no schema registered for {signature.stage.value}")
        if document["title"] != signature.contract_name:
            raise ValueError("signature contract does not match registered schema")
        _assert_canonical_draft_contract(signature.stage, document)
        canonical = _canonical_json(document)
        report = PromptBudgetGate.validate_schema(signature, canonical)
        return DraftSchema(
            contract_name=signature.contract_name,
            version=signature.version,
            document=document,
            canonical_json=canonical,
            digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            budget_report=report,
        )

    def repair_schema_for(self, signature: StageSignature) -> DraftSchema:
        """Resolve the separately transported, non-recursive ContractPatch schema."""

        document = _freeze_schema_document(_repair_schema_document(signature))
        _assert_repair_contract(signature, document)
        canonical = _canonical_json(document)
        report = PromptBudgetGate.validate_schema(signature, canonical)
        return DraftSchema(
            contract_name="ContractPatch",
            version=signature.version,
            document=document,
            canonical_json=canonical,
            digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            budget_report=report,
        )
