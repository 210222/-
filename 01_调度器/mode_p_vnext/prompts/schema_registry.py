"""Compact native transport schemas for creative Drafts only."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
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


_SCHEMAS: Mapping[Stage, Mapping[str, Any]] = {
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
        "type": "object", "title": "ExecutionDesignDraft", "additionalProperties": False,
        "required": ["curve_points", "decisions", "shots", "transition_intents", "audio_intents", "reference_intents", "handoff_intent"],
        "properties": {
            "curve_points": {"type": "array", "minItems": 1, "maxItems": 24, "items": {"type": "object", "additionalProperties": False, "required": ["dramatic_beat_ordinal", "intensity", "explanation"], "properties": {"dramatic_beat_ordinal": {"type": "integer", "minimum": 1}, "intensity": {"type": "integer", "minimum": 0, "maximum": 100}, "explanation": {"type": "string", "maxLength": 240}}}},
            "decisions": {"type": "array", "minItems": 1, "maxItems": 24, "items": {"type": "object", "additionalProperties": False, "required": ["scope", "basis", "locked_by", "options", "selected_index", "rationale", "tradeoff"], "properties": {"scope": {"type": "string", "maxLength": 120}, "basis": {"enum": ["locked", "choice"]}, "locked_by": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 180}}, "options": {"type": "array", "minItems": 1, "maxItems": 2, "items": {"type": "string", "maxLength": 240}}, "selected_index": {"type": "integer", "minimum": 0, "maximum": 1}, "rationale": {"type": "string", "maxLength": 240}, "tradeoff": {"type": "string", "maxLength": 240}}}},
            "shots": {"type": "array", "minItems": 1, "maxItems": 48, "items": {"type": "object", "additionalProperties": False, "required": ["blocking_beat_ordinal", "dramatic_function", "attention_target", "information_action", "framing_intent", "camera_pose", "camera_motion", "composition", "lighting", "performance", "duration_weight", "visual_beats"], "properties": {"blocking_beat_ordinal": {"type": "integer", "minimum": 1}, "dramatic_function": {"type": "string", "maxLength": 240}, "attention_target": {"type": "string", "maxLength": 240}, "information_action": {"type": "string", "maxLength": 240}, "framing_intent": {"type": "string", "maxLength": 240}, "camera_pose": {"type": "string", "maxLength": 240}, "camera_motion": {"type": "string", "maxLength": 240}, "composition": {"type": "string", "maxLength": 240}, "lighting": {"type": "string", "maxLength": 240}, "performance": {"type": "string", "maxLength": 240}, "duration_weight": {"type": "integer", "minimum": 1}, "visual_beats": {"type": "array", "minItems": 1, "maxItems": 4, "items": {"type": "object", "additionalProperties": False, "required": ["phase", "subject_state", "attention", "storyboard_role"], "properties": {"phase": {"enum": ["entry", "action", "reaction", "handoff"]}, "subject_state": {"type": "string", "maxLength": 240}, "attention": {"type": "string", "maxLength": 240}, "storyboard_role": {"enum": ["required", "optional", "omit"]}}}}}}},
            "transition_intents": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "audio_intents": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "reference_intents": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "handoff_intent": {"type": "string", "maxLength": 240},
        },
    },
}


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
    """Fail before provider I/O if the transport cannot decode a v2.1 Draft."""

    from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingDraft
    from mode_p_vnext.domain.decisions import DecisionDraft, VisualCurvePointDraft
    from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
    from mode_p_vnext.domain.vec import (
        ExecutionDesignDraft,
        ShotDesignDraft,
        VisualBeatDraft,
    )

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
