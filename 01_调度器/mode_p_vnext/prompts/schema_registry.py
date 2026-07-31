"""Compact native transport schemas for creative Drafts only."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
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
        "required": ["thematic_axis", "dramatic_direction", "visual_principles"],
        "properties": {
            "thematic_axis": {"type": "string", "maxLength": 180},
            "dramatic_direction": {"type": "string", "maxLength": 180},
            "visual_principles": {"type": "array", "items": {"type": "string", "maxLength": 180}, "maxItems": 6},
        },
    },
    Stage.S1: {
        "type": "object", "title": "SceneIntentDraft", "additionalProperties": False,
        "required": ["scene_objective", "dramatic_turn", "director_questions"],
        "properties": {
            "scene_objective": {"type": "string", "maxLength": 180},
            "dramatic_turn": {"type": "string", "maxLength": 180},
            "director_questions": {"type": "array", "items": {"type": "string", "maxLength": 180}, "minItems": 1, "maxItems": 6},
        },
    },
    Stage.B0: {
        "type": "object", "title": "BlockingDraft", "additionalProperties": False,
        "required": ["beats", "entry_state", "exit_state"],
        "properties": {
            "entry_state": {"type": "string", "maxLength": 180},
            "exit_state": {"type": "string", "maxLength": 180},
            "beats": {
                "type": "array", "minItems": 1, "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["ordinal", "dramatic_action", "action_paths"],
                    "properties": {
                        "ordinal": {"type": "integer", "minimum": 1},
                        "dramatic_action": {"type": "string", "maxLength": 180},
                        "action_paths": {"type": "array", "minItems": 1, "items": {"type": "string", "maxLength": 180}},
                        "spatial_result": {"type": "string", "maxLength": 180},
                    },
                },
            },
        },
    },
    Stage.B1: {
        "type": "object", "title": "ExecutionDesignDraft", "additionalProperties": False,
        "required": ["curve_points", "decisions", "shots", "transition_intents", "audio_intents", "reference_intents", "handoff_intent"],
        "properties": {
            "curve_points": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["beat_ordinal", "attention"], "properties": {"beat_ordinal": {"type": "integer", "minimum": 1}, "attention": {"type": "string", "maxLength": 240}}}},
            "decisions": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["scope", "options", "selected_index", "tradeoff"], "properties": {"scope": {"type": "string", "maxLength": 120}, "options": {"type": "array", "minItems": 1, "maxItems": 2, "items": {"type": "string", "maxLength": 240}}, "selected_index": {"type": "integer", "minimum": 0, "maximum": 1}, "tradeoff": {"type": "string", "maxLength": 240}}}},
            "shots": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["beat_ordinal", "purpose", "subject_state", "attention", "duration_weight", "visual_beats"], "properties": {"beat_ordinal": {"type": "integer", "minimum": 1}, "purpose": {"type": "string", "maxLength": 240}, "subject_state": {"type": "string", "maxLength": 240}, "attention": {"type": "string", "maxLength": 240}, "duration_weight": {"type": "number", "exclusiveMinimum": 0}, "visual_beats": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["phase", "subject_state", "attention", "storyboard_role"], "properties": {"phase": {"enum": ["entry", "action", "reaction", "handoff"]}, "subject_state": {"type": "string", "maxLength": 240}, "attention": {"type": "string", "maxLength": 240}, "storyboard_role": {"enum": ["required", "optional", "omit"]}}}}}}},
            "transition_intents": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "audio_intents": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "reference_intents": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "handoff_intent": {"type": "string", "maxLength": 240},
        },
    },
}


class DraftSchemaRegistry:
    """Resolve a versioned compact schema and enforce its stage budget."""

    def schema_for(self, signature: StageSignature) -> DraftSchema:
        document = _SCHEMAS.get(signature.stage)
        if document is None:
            raise ValueError(f"no schema registered for {signature.stage.value}")
        if document["title"] != signature.contract_name:
            raise ValueError("signature contract does not match registered schema")
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
