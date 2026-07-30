"""Phase-A diagnosis artifacts for the MODE:P vNext Director boundary.

The artifact answers *what requires judgement* before retrieval and before
shot design.  It deliberately carries problems, risks and open questions, not
focal lengths, camera placements, a shot count or a completed timeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256
from mode_p_vnext.schema.scene_diagnosis import SceneDiagnosis, generate_knowledge_query


def _hash(value: object) -> str:
    return stable_hash_sha256(canonical_json_dumps(value).encode("utf-8"))


def _contains_shot_answer(text: str) -> bool:
    lowered = " ".join(text.lower().split())
    return any(token in lowered for token in (
        "50mm", "35mm", "85mm", "three shots", "3 shots", "full timeline",
        "完整时间轴", "三镜头", "固定机位", "camera at ", "shot 1",
    ))


@dataclass
class DirectorProblemSet:
    """Complete non-creative Phase-A question set.

    These fields make retrieval inspectable without turning a scene into a
    generic label or prescribing a concrete shot.  Phase B owns the creative
    synthesis after blocking has been deliberately chosen.
    """

    dramatic_change: str = ""
    attention_path: str = ""
    spatial_topology: List[str] = field(default_factory=list)
    performance_visibility_problems: List[str] = field(default_factory=list)
    visibility_contract_problems: List[str] = field(default_factory=list)
    generative_leakage_risks: List[str] = field(default_factory=list)
    camera_questions: List[str] = field(default_factory=list)
    composition_questions: List[str] = field(default_factory=list)
    lighting_questions: List[str] = field(default_factory=list)
    editing_questions: List[str] = field(default_factory=list)
    generation_segment_questions: List[str] = field(default_factory=list)
    reference_questions: List[str] = field(default_factory=list)
    model_risks: List[str] = field(default_factory=list)
    user_style_relevance: List[str] = field(default_factory=list)
    knowledge_questions: List[str] = field(default_factory=list)
    decision_domains: List[str] = field(default_factory=list)
    creative_decisions_reserved_for_director: List[str] = field(
        default_factory=lambda: ["blocking", "camera", "composition", "edit", "final_execution"]
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dramatic_change": self.dramatic_change,
            "attention_path": self.attention_path,
            "spatial_topology": list(self.spatial_topology),
            "performance_visibility_problems": list(self.performance_visibility_problems),
            "visibility_contract_problems": list(self.visibility_contract_problems),
            "generative_leakage_risks": list(self.generative_leakage_risks),
            "camera_questions": list(self.camera_questions),
            "composition_questions": list(self.composition_questions),
            "lighting_questions": list(self.lighting_questions),
            "editing_questions": list(self.editing_questions),
            "generation_segment_questions": list(self.generation_segment_questions),
            "reference_questions": list(self.reference_questions),
            "model_risks": list(self.model_risks),
            "user_style_relevance": list(self.user_style_relevance),
            "knowledge_questions": list(self.knowledge_questions),
            "decision_domains": list(self.decision_domains),
            "creative_decisions_reserved_for_director": list(self.creative_decisions_reserved_for_director),
        }

    @property
    def content_sha256(self) -> str:
        return _hash(self.to_dict())

    def validate(self) -> List[str]:
        violations: List[str] = []
        if not self.knowledge_questions:
            violations.append("Phase-A problem set has no knowledge_questions")
        if not self.decision_domains:
            violations.append("Phase-A problem set has no decision_domains")
        if not self.creative_decisions_reserved_for_director:
            violations.append("Phase-A problem set must reserve final creative decisions for Director")
        for field_name, value in self.to_dict().items():
            values = value if isinstance(value, list) else [value]
            for item in values:
                if isinstance(item, str) and _contains_shot_answer(item):
                    violations.append(
                        f"Phase-A field '{field_name}' contains a fixed shot/camera answer"
                    )
        return violations


def build_director_problem_set(
    diagnosis: SceneDiagnosis,
    *,
    dramatic_change: str = "",
    visibility_contract_problems: Iterable[str] = (),
    generative_leakage_risks: Iterable[str] = (),
    camera_questions: Iterable[str] = (),
    composition_questions: Iterable[str] = (),
    generation_segment_questions: Iterable[str] = (),
    reference_questions: Iterable[str] = (),
    user_style_relevance: Iterable[str] = (),
) -> DirectorProblemSet:
    """Derive a full Phase-A problem set from the legacy diagnosis schema."""
    query = generate_knowledge_query(diagnosis)
    question_values: List[str] = []
    domains: List[str] = []
    for domain, values in query.dimension_questions.items():
        domains.append(domain)
        question_values.extend(values)
    if query.model_risk_queries:
        domains.append("model_risk")
        question_values.extend(query.model_risk_queries)
    if query.user_constraint_queries:
        domains.append("user_constraint")
        question_values.extend(query.user_constraint_queries)
    return DirectorProblemSet(
        dramatic_change=dramatic_change,
        attention_path=diagnosis.attention_path,
        spatial_topology=list(diagnosis.space_issues),
        performance_visibility_problems=list(diagnosis.performance_issues),
        visibility_contract_problems=list(visibility_contract_problems),
        generative_leakage_risks=list(generative_leakage_risks),
        camera_questions=list(camera_questions),
        composition_questions=list(composition_questions),
        lighting_questions=list(diagnosis.lighting_issues),
        editing_questions=list(diagnosis.transition_issues),
        generation_segment_questions=list(generation_segment_questions),
        reference_questions=list(reference_questions),
        model_risks=list(diagnosis.model_risks),
        user_style_relevance=list(user_style_relevance or diagnosis.user_visual_constraints),
        knowledge_questions=question_values,
        decision_domains=domains,
    )


@dataclass
class DiagnosisArtifact:
    """Formal pre-design artifact with auditable Phase-A content.

    Existing callers may still construct the first five fields positionally;
    ``problem_set`` and ``source_fact_ids`` are additive vNext evidence.
    """

    artifact_id: str
    episode_id: str
    diagnosis: SceneDiagnosis
    open_questions: List[str] = field(default_factory=list)
    user_visual_constraints: List[str] = field(default_factory=list)
    problem_set: Optional[DirectorProblemSet] = None
    source_fact_ids: List[str] = field(default_factory=list)

    def effective_problem_set(self) -> DirectorProblemSet:
        return self.problem_set or build_director_problem_set(
            self.diagnosis,
            user_style_relevance=self.user_visual_constraints,
        )

    def to_dict(self) -> Dict[str, Any]:
        problem_set = self.effective_problem_set()
        return {
            "artifact_id": self.artifact_id,
            "episode_id": self.episode_id,
            "scene_id": self.diagnosis.scene_id,
            "diagnosis": {
                "attention_path": self.diagnosis.attention_path,
                "space_issues": list(self.diagnosis.space_issues),
                "performance_issues": list(self.diagnosis.performance_issues),
                "movement_issues": list(self.diagnosis.movement_issues),
                "lighting_issues": list(self.diagnosis.lighting_issues),
                "transition_issues": list(self.diagnosis.transition_issues),
                "model_risks": list(self.diagnosis.model_risks),
                "user_visual_constraints": list(self.diagnosis.user_visual_constraints),
            },
            "open_questions": list(self.open_questions),
            "user_visual_constraints": list(self.user_visual_constraints),
            "source_fact_ids": list(self.source_fact_ids),
            "problem_set": problem_set.to_dict(),
            "phase": "A_DIAGNOSIS_ONLY",
        }

    @property
    def content_sha256(self) -> str:
        return _hash(self.to_dict())


def build_phase_a_artifact(
    artifact_id: str,
    episode_id: str,
    diagnosis: SceneDiagnosis,
    *,
    open_questions: Iterable[str] = (),
    user_visual_constraints: Iterable[str] = (),
    source_fact_ids: Iterable[str] = (),
    problem_set: Optional[DirectorProblemSet] = None,
) -> DiagnosisArtifact:
    """Build and validate an explicit Phase-A artifact without designing shots."""
    artifact = DiagnosisArtifact(
        artifact_id=artifact_id,
        episode_id=episode_id,
        diagnosis=diagnosis,
        open_questions=list(open_questions),
        user_visual_constraints=list(user_visual_constraints),
        problem_set=problem_set,
        source_fact_ids=list(source_fact_ids),
    )
    violations = validate_diagnosis_artifact(artifact)
    if violations:
        raise ValueError("invalid Phase-A artifact: " + "; ".join(violations))
    return artifact


def validate_diagnosis_artifact(artifact: DiagnosisArtifact) -> List[str]:
    """Validate the boundary; return violations rather than inventing a fix."""
    violations: List[str] = []
    if not artifact.artifact_id or not artifact.episode_id or not artifact.diagnosis.scene_id:
        violations.append("Diagnosis artifact requires artifact_id, episode_id and scene_id")
    if artifact.diagnosis.model_risks and not artifact.open_questions:
        violations.append(
            f"Diagnosis '{artifact.artifact_id}' has model_risks but no open_questions "
            "for the Director"
        )
    violations.extend(artifact.effective_problem_set().validate())
    for source_name, items in (
        ("open_questions", artifact.open_questions),
        ("user_visual_constraints", artifact.user_visual_constraints),
    ):
        for item in items:
            if _contains_shot_answer(item):
                violations.append(f"Phase-A field '{source_name}' contains a fixed shot/camera answer")
    return violations
