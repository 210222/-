"""Deterministic prompt and schema budget gates."""

from __future__ import annotations

from dataclasses import dataclass

from .signatures import StageSignature


class PromptBudgetExceeded(ValueError):
    """Raised before a provider call when a hard architecture budget is exceeded."""


@dataclass(frozen=True)
class BudgetReport:
    stage: str
    kind: str
    character_count: int
    hard_limit: int
    soft_warning: bool


class PromptBudgetGate:
    """Measure complete compiled text; never truncate facts to fit a budget."""

    @staticmethod
    def validate_prompt(signature: StageSignature, text: str) -> BudgetReport:
        count = len(text)
        if count > signature.prompt_budget:
            raise PromptBudgetExceeded(
                f"{signature.stage.value} prompt exceeds hard limit "
                f"{signature.prompt_budget}: {count}"
            )
        return BudgetReport(
            stage=signature.stage.value,
            kind="prompt",
            character_count=count,
            hard_limit=signature.prompt_budget,
            soft_warning=bool(
                signature.soft_prompt_target is not None
                and count > signature.soft_prompt_target
            ),
        )

    @staticmethod
    def validate_schema(signature: StageSignature, text: str) -> BudgetReport:
        count = len(text)
        if count > signature.schema_budget:
            raise PromptBudgetExceeded(
                f"{signature.stage.value} schema exceeds hard limit "
                f"{signature.schema_budget}: {count}"
            )
        return BudgetReport(
            stage=signature.stage.value,
            kind="schema",
            character_count=count,
            hard_limit=signature.schema_budget,
            soft_warning=False,
        )
