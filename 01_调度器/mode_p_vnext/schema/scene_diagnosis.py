"""MODE:P vNext — Scene Diagnosis & Knowledge Query Schema (V3.4).

Director answers diagnostic questions before designing shots. The diagnosis
drives knowledge retrieval — NOT a single scene-type label.

Spec references: LOOP §5.10, §9 Step 3-4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# SceneDiagnosis
# ---------------------------------------------------------------------------

@dataclass
class SceneDiagnosis:
    """Director's pre-design diagnosis of a scene.

    Each dimension identifies a question the Director must answer.
    Empty lists mean "no issues in this dimension" — the Director has
    considered it and found nothing requiring special attention.
    """

    scene_id: str
    attention_path: str = ""           # 注意力路径
    space_issues: List[str] = field(default_factory=list)
    performance_issues: List[str] = field(default_factory=list)
    movement_issues: List[str] = field(default_factory=list)
    lighting_issues: List[str] = field(default_factory=list)
    transition_issues: List[str] = field(default_factory=list)
    model_risks: List[str] = field(default_factory=list)
    user_visual_constraints: List[str] = field(default_factory=list)

    # IMPORTANT: no `scene_type` field — diagnosis is multi-dimensional,
    # not a single label like "action" or "dialogue".


# ---------------------------------------------------------------------------
# KnowledgeQuery
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeQuery:
    """A structured query derived from the scene diagnosis.

    Each dimension with issues becomes a question that drives knowledge
    retrieval. Empty dimensions produce no questions.
    """

    scene_id: str
    dimension_questions: Dict[str, List[str]] = field(default_factory=dict)
    model_risk_queries: List[str] = field(default_factory=list)
    user_constraint_queries: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Query generation
# ---------------------------------------------------------------------------

_DIMENSION_MAP = {
    "attention": "attention_path",
    "space": "space_issues",
    "performance": "performance_issues",
    "movement": "movement_issues",
    "lighting": "lighting_issues",
    "transition": "transition_issues",
}


def generate_knowledge_query(diagnosis: SceneDiagnosis) -> KnowledgeQuery:
    """Generate a structured knowledge query from the diagnosis.

    Only dimensions with non-empty issues generate questions. This ensures
    the retriever only searches for what the scene actually needs.
    """
    query = KnowledgeQuery(scene_id=diagnosis.scene_id)

    for dim_key, field_name in _DIMENSION_MAP.items():
        issues = getattr(diagnosis, field_name, None)
        if isinstance(issues, str) and issues:
            query.dimension_questions[dim_key] = [issues]
        elif isinstance(issues, list) and issues:
            query.dimension_questions[dim_key] = list(issues)

    if diagnosis.model_risks:
        query.model_risk_queries = [
            f"如何避免: {risk}" for risk in diagnosis.model_risks
        ]

    if diagnosis.user_visual_constraints:
        query.user_constraint_queries = list(diagnosis.user_visual_constraints)

    return query
