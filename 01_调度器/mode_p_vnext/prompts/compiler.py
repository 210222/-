"""Compile compact, stage-scoped text without serializing output schemas."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from mode_p_vnext.ports.structured_text import ViolationSet

from .budgets import BudgetReport, PromptBudgetGate
from .fragments import conditional_fragments, core_for_signature
from .schema_registry import DraftSchema, DraftSchemaRegistry
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
    """Create stage-scoped prompts and fail before provider invocation."""

    def __init__(self, schema_registry: DraftSchemaRegistry | None = None) -> None:
        self._schemas = schema_registry or DraftSchemaRegistry()

    def compile(
        self, signature: StageSignature, approved_input: Mapping[str, Any]
    ) -> CompiledPrompt:
        signature.assert_approved_input(approved_input)
        return self._compile(
            signature,
            approved_input,
            schema=self._schemas.schema_for(signature),
            contract_name=signature.contract_name,
            semantic_goal=signature.semantic_goal,
            output_semantics=signature.output_semantics,
        )

    def compile_repair(
        self, signature: StageSignature, violations: ViolationSet
    ) -> CompiledPrompt:
        """Compile a compact repair request without re-sending the full Draft."""

        if signature.stage is not violations.stage:
            raise ValueError("signature stage must match violation set stage")
        approved_input = {
            "violation_set": {
                "stage": violations.stage.value,
                "draft_digest": violations.draft_digest,
                "violations": [
                    {
                        "code": item.code,
                        "json_path": item.json_path,
                        "expected": item.expected,
                        "observed_summary": item.observed_summary,
                    }
                    for item in violations.violations
                ],
                "repair_scope": violations.repair_scope,
            }
        }
        return self._compile(
            signature,
            approved_input,
            schema=self._schemas.repair_schema_for(signature),
            contract_name="ContractPatch",
            semantic_goal=(
                "Repair only the fields named by the supplied ViolationSet; "
                "do not return or rewrite the full Draft."
            ),
            output_semantics=("whitelisted patch values",),
        )

    @staticmethod
    def _compact_input(approved_input: Mapping[str, Any]) -> str:
        if not isinstance(approved_input, Mapping):
            raise TypeError("approved_input must be a mapping")
        try:
            return json.dumps(
                dict(approved_input), ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("approved_input must be JSON-serializable") from exc

    def _compile(
        self,
        signature: StageSignature,
        approved_input: Mapping[str, Any],
        *,
        schema: DraftSchema,
        contract_name: str,
        semantic_goal: str,
        output_semantics: tuple[str, ...],
    ) -> CompiledPrompt:
        compact_input = self._compact_input(approved_input)
        fragments = conditional_fragments(approved_input, stage=signature.stage)
        system_message = core_for_signature(signature)
        user_payload = {
            "stage": signature.stage.value,
            "signature": {
                "version": signature.version,
                "contract_name": contract_name,
                "schema_digest": schema.digest,
                "semantic_goal": semantic_goal,
                "output_semantics": output_semantics,
            },
            "conditional_fragments": fragments,
            "approved_input": json.loads(compact_input),
            "return_contract": "Return one JSON object matching the separately transmitted schema only.",
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
