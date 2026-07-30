"""MODE:P vNext — Complete Context Budget & Truncation Failure (V6.6).

Budgets facts, knowledge, assets, corrections, invocation protocol, and
output reserve separately. Any silent truncation MUST block.

Spec references: LOOP §26; Omission P0-15.
"""

from __future__ import annotations

from dataclasses import dataclass


class BudgetExceededError(Exception):
    pass


@dataclass
class ContextBudget:
    fact_budget: int
    knowledge_budget: int
    asset_budget: int
    correction_budget: int
    protocol_budget: int
    output_reserve: int

    def __post_init__(self):
        self._consumed: dict[str, int] = {
            "fact": 0, "knowledge": 0, "asset": 0,
            "correction": 0, "protocol": 0, "output": 0,
        }

    def _budget_for(self, category: str) -> int:
        map = {
            "fact": self.fact_budget, "knowledge": self.knowledge_budget,
            "asset": self.asset_budget, "correction": self.correction_budget,
            "protocol": self.protocol_budget, "output": self.output_reserve,
        }
        return map.get(category, 0)

    def remaining(self, category: str) -> int:
        return max(0, self._budget_for(category) - self._consumed[category])

    def consume(self, category: str, chars: int) -> None:
        if chars <= 0:
            return
        budget = self._budget_for(category)
        new_total = self._consumed[category] + chars
        if new_total > budget:
            raise BudgetExceededError(
                f"Budget exceeded for '{category}': "
                f"{new_total} > {budget} chars"
            )
        self._consumed[category] = new_total

    @property
    def total_budget(self) -> int:
        return (self.fact_budget + self.knowledge_budget +
                self.asset_budget + self.correction_budget +
                self.protocol_budget + self.output_reserve)
