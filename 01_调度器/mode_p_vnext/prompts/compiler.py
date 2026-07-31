"""Compile compact, stage-scoped text without serializing output schemas."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .budgets import BudgetReport, PromptBudgetGate
from .fragments import DIRECTOR_CORE, conditional_fragments
from .schema_registry import DraftSchemaRegistry
from .signatures import StageSignature


@dataclass(frozen=True)
class CompiledPrompt:
    signature: StageSignature
    system_message: str
    user_message: str
    schema_digest: str
    approved_input_digest: str
    budget_report: BudgetReport

    @property
    def prompt_text(self) -> str:
        return self.system_message + "\n" + self.user_message

    @property
    def character_count(self) -> int:
        return self.budget_report.character_count


class PromptCompiler:
    """Create the four allowed prompt parts and fail before provider invocation."""

    def __init__(self, schema_registry: DraftSchemaRegistry | None = None) -> None:
        self._schemas = schema_registry or DraftSchemaRegistry()

    def compile(
        self, signature: StageSignature, approved_input: Mapping[str, Any]
    ) -> CompiledPrompt:
        if not isinstance(approved_input, Mapping):
            raise TypeError("approved_input must be a mapping")
        try:
            compact_input = json.dumps(
                dict(approved_input), ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("approved_input must be JSON-serializable") from exc
        schema = self._schemas.schema_for(signature)
        fragments = conditional_fragments(approved_input)
        system_message = DIRECTOR_CORE
        user_payload = {
            "stage": signature.stage.value,
            "signature": {
                "version": signature.version,
                "contract_name": signature.contract_name,
                "schema_digest": schema.digest,
                "semantic_goal": signature.semantic_goal,
                "output_semantics": signature.output_semantics,
            },
            "conditional_fragments": fragments,
            "approved_input": json.loads(compact_input),
            "return_contract": "Return one JSON object matching the separately transmitted schema.",
        }
        user_message = json.dumps(user_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        report = PromptBudgetGate.validate_prompt(
            signature, system_message + "\n" + user_message
        )
        return CompiledPrompt(
            signature=signature,
            system_message=system_message,
            user_message=user_message,
            schema_digest=schema.digest,
            approved_input_digest=hashlib.sha256(compact_input.encode("utf-8")).hexdigest(),
            budget_report=report,
        )
