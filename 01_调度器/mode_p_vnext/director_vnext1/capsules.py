"""Offline capsule selection for the two-stage Director vNext.1 workflow."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Sequence, Tuple

from .contracts import (
    K1_TYPES,
    K2_TYPES,
    CapsuleApplicabilityRecord,
    ConflictDecisionRecord,
    DecisionPacket,
    DirectorContractError,
    DirectorProblemSet,
    KnowledgeCapsule,
)


@dataclass(frozen=True)
class RetrievalContext:
    scene_tags: Tuple[str, ...]
    approved_context: Tuple[str, ...]
    impact_level: str = "normal"

    def __post_init__(self) -> None:
        if self.impact_level not in {"normal", "high"}:
            raise DirectorContractError("retrieval impact_level must be normal or high")


def _token_set(values: Iterable[str]) -> set[str]:
    return {value.strip().lower() for value in values if value and value.strip()}


def _matches(capsule: KnowledgeCapsule, problems: DirectorProblemSet, context: RetrievalContext) -> tuple[bool, Tuple[str, ...]]:
    problem_tags = _token_set(
        token for problem in problems.problems for token in (*problem.tags, problem.domain)
    )
    available = problem_tags | _token_set(context.scene_tags)
    triggers = _token_set(capsule.triggers)
    contraindications = _token_set(capsule.contraindications)
    required = _token_set(capsule.required_context)
    approved = _token_set(context.approved_context)
    trigger_hits = tuple(sorted(triggers & available))
    if not trigger_hits or contraindications & available or not required.issubset(approved):
        return False, ()
    if capsule.review_status != "approved":
        return False, ()
    if context.impact_level == "high" and capsule.confidence_level == "low":
        return False, ()
    return True, trigger_hits


def _problem_ids_for(capsule: KnowledgeCapsule, problems: DirectorProblemSet) -> Tuple[str, ...]:
    capsule_tags = _token_set((*capsule.tags, *capsule.triggers, capsule.director_problem))
    matched = [
        problem.problem_id
        for problem in problems.problems
        if capsule_tags & _token_set((*problem.tags, problem.domain, problem.question))
    ]
    return tuple(matched) or (problems.problems[0].problem_id,)


def _select(
    *,
    packet_id: str,
    stage: str,
    problems: DirectorProblemSet,
    catalog: Sequence[KnowledgeCapsule],
    context: RetrievalContext,
    blocking_commit_id: str = "",
) -> DecisionPacket:
    allowed_types = K1_TYPES if stage == "K1" else K2_TYPES
    matching: list[tuple[KnowledgeCapsule, Tuple[str, ...]]] = []
    anti_patterns: list[tuple[KnowledgeCapsule, Tuple[str, ...]]] = []
    for capsule in sorted(catalog, key=lambda item: item.capsule_id):
        matched, trigger_hits = _matches(capsule, problems, context)
        if not matched:
            continue
        if capsule.primary_type == "anti_pattern" or capsule.anti_pattern_tags:
            anti_patterns.append((capsule, trigger_hits))
        elif capsule.primary_type in allowed_types:
            matching.append((capsule, trigger_hits))
    primary_pairs: list[tuple[KnowledgeCapsule, Tuple[str, ...]]] = []
    conflict: KnowledgeCapsule | None = None
    for candidate, trigger_hits in matching:
        primary_ids = {item.capsule_id for item, _ in primary_pairs}
        conflicts_with_primary = bool(
            set(candidate.conflicting_capsule_ids) & primary_ids
        ) or any(
            candidate.capsule_id in item.conflicting_capsule_ids
            for item, _ in primary_pairs
        )
        if conflicts_with_primary:
            if conflict is None:
                conflict = candidate
            continue
        if len(primary_pairs) < 3:
            primary_pairs.append((candidate, trigger_hits))
    primary = tuple(item[0] for item in primary_pairs)
    anti = anti_patterns[0][0] if anti_patterns else None
    if not primary:
        return DecisionPacket(
            packet_id=packet_id,
            scene_id=problems.scene_id,
            stage=stage,
            primary_capsules=(),
            application_records=(),
            blocking_commit_id=blocking_commit_id,
            no_match=True,
        )
    records = tuple(
        CapsuleApplicabilityRecord(
            capsule_id=capsule.capsule_id,
            stage=stage,
            problem_ids=_problem_ids_for(capsule, problems),
            trigger_evidence=trigger_hits,
            contraindication_check="clear",
            confidence_level=capsule.confidence_level,
            allowed_use=capsule.allowed_uses[0],
            influenced_fields=("director_problem" if stage == "K1" else "execution_constraint",),
        )
        for capsule, trigger_hits in primary_pairs
    )
    return DecisionPacket(
        packet_id=packet_id,
        scene_id=problems.scene_id,
        stage=stage,
        primary_capsules=primary,
        application_records=records,
        conflict_capsule=conflict,
        anti_pattern_capsule=anti,
        blocking_commit_id=blocking_commit_id,
    )


def retrieve_k1(
    packet_id: str,
    problems: DirectorProblemSet,
    catalog: Sequence[KnowledgeCapsule],
    context: RetrievalContext,
) -> DecisionPacket:
    """Retrieve problem/blocked-performance knowledge before spatial commitment."""

    return _select(
        packet_id=packet_id,
        stage="K1",
        problems=problems,
        catalog=catalog,
        context=context,
    )


def retrieve_k2(
    packet_id: str,
    problems: DirectorProblemSet,
    catalog: Sequence[KnowledgeCapsule],
    context: RetrievalContext,
    *,
    blocking_commit_id: str,
) -> DecisionPacket:
    """Retrieve execution knowledge only after a verified BlockingCommit exists."""

    if not blocking_commit_id.strip():
        raise DirectorContractError("K2 retrieval requires a verified BlockingCommit ID")
    return _select(
        packet_id=packet_id,
        stage="K2",
        problems=problems,
        catalog=catalog,
        context=context,
        blocking_commit_id=blocking_commit_id,
    )


def attach_conflict_decision(
    packet: DecisionPacket,
    decision: ConflictDecisionRecord,
) -> DecisionPacket:
    """Attach an explicit Director choice after retrieval exposed a conflict."""

    if packet.conflict_capsule is None:
        raise DirectorContractError(
            "cannot adjudicate a packet that exposes no capsule conflict"
        )
    return replace(packet, conflict_decision=decision)
