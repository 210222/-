"""MODE:P vNext — Knowledge/Constraint Ablation (V8.5).

Tests minimum knowledge, removes single constraint categories, runs without
Golden experience to identify true contributors.

Spec references: LOOP §13.8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AblationConfig:
    config_id: str
    remove_knowledge: List[str] = field(default_factory=list)
    remove_constraints: List[str] = field(default_factory=list)
    use_golden_experience: bool = True
    use_minimal_knowledge: bool = False


@dataclass
class AblationResult:
    config_id: str
    baseline_fidelity: Dict[str, float] = field(default_factory=dict)
    ablated_fidelity: Dict[str, float] = field(default_factory=dict)

    def delta(self, axis: str) -> float:
        base = self.baseline_fidelity.get(axis, 0.0)
        ablated = self.ablated_fidelity.get(axis, 0.0)
        return ablated - base
