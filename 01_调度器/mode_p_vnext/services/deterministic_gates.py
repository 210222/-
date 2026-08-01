"""Deterministic Gate 0 — zero-model validation of assembled artifacts.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.1–§9.2 / §14 A7.

Gate 0 makes only mechanical judgments: schema/shape, ID uniqueness and
reference closure, tick integrity, fact coverage (no invention), projection
homology (both projections derive from the same AST), and the claim ceiling
(text can never claim visual acceptance).  A Gate 0 failure needs no DP
"judgment" and no model call.
"""

from __future__ import annotations

from dataclasses import dataclass

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    canonical_sha256,
)
from mode_p_vnext.domain.evidence import OutcomeAttribution
from mode_p_vnext.domain.vec import VisualExecutionContract
from mode_p_vnext.pipeline.verification_nodes import (
    AttributionLayer,
    TEXT_VALIDATED,
    gate0_attribution,
)
from mode_p_vnext.services.projection_compiler import (
    ProjectionAST,
    StoryboardProjection,
    VideoProjection,
)


@dataclass(frozen=True)
class Gate0Issue:
    """One deterministic violation found by Gate 0."""

    rule: str
    path: str
    detail: str


@dataclass(frozen=True)
class Gate0Result:
    """The Gate 0 verdict with every mechanical issue."""

    result_id: str
    passed: bool
    issues: tuple[Gate0Issue, ...]
    input_digests: dict[str, str]
    attribution: OutcomeAttribution | None = None


def _vec_node_ids(vec: VisualExecutionContract) -> list[str]:
    ids: list[str] = [vec.contract_id]
    for segment in vec.segments:
        ids.append(segment.segment_id)
    for decision in vec.decisions:
        ids.append(decision.decision_id)
    for curve in vec.curve_points:
        ids.append(curve.point_id)
    for shot in vec.shots:
        ids.append(shot.shot_id)
        for beat in shot.visual_beats:
            ids.append(beat.beat_id)
            # start/end state ids are chained references (a beat's exit state
            # is the next beat's entry state) and are deliberately shared.
    for boundary in vec.boundaries:
        ids.append(boundary.boundary_id)
    for event in vec.audio_events:
        ids.append(event.event_id)
    for voice in vec.voice_requirements:
        ids.append(voice.requirement_id)
    for reference in vec.reference_requirements:
        ids.append(reference.requirement_id)
    return ids


def _check_id_uniqueness(vec: VisualExecutionContract, issues: list[Gate0Issue]) -> None:
    node_ids = _vec_node_ids(vec)
    seen: set[str] = set()
    for node_id in node_ids:
        if node_id in seen:
            issues.append(
                Gate0Issue(
                    rule="id_uniqueness",
                    path=node_id,
                    detail="duplicate machine-generated ID in VEC",
                )
            )
        seen.add(node_id)


def _check_tick_integrity(vec: VisualExecutionContract, issues: list[Gate0Issue]) -> None:
    for segment in vec.segments:
        duration = segment.timeline.duration_ticks
        shot_ids = segment.shot_ids
        if not shot_ids:
            issues.append(
                Gate0Issue(
                    rule="tick_integrity",
                    path=segment.segment_id,
                    detail="segment covers no shots",
                )
            )
            continue
        shots = [shot for shot in vec.shots if shot.shot_id in shot_ids]
        shots.sort(key=lambda shot: shot.interval.start_tick)
        if shots[0].interval.start_tick != 0:
            issues.append(
                Gate0Issue(
                    rule="tick_integrity",
                    path=segment.segment_id,
                    detail="first shot must start at local tick 0",
                )
            )
        for left, right in zip(shots, shots[1:]):
            if left.interval.end_tick != right.interval.start_tick:
                issues.append(
                    Gate0Issue(
                        rule="tick_integrity",
                        path=segment.segment_id,
                        detail="adjacent shots must be contiguous",
                    )
                )
        if shots[-1].interval.end_tick != duration:
            issues.append(
                Gate0Issue(
                    rule="tick_integrity",
                    path=segment.segment_id,
                    detail="final shot must end at the segment duration",
                )
            )
        for shot in shots:
            for beat in shot.visual_beats:
                if not (
                    shot.interval.start_tick
                    <= beat.interval.start_tick
                    < beat.interval.end_tick
                    <= shot.interval.end_tick
                ):
                    issues.append(
                        Gate0Issue(
                            rule="tick_integrity",
                            path=beat.beat_id,
                            detail="beat interval escapes its shot interval",
                        )
                    )


def _check_fact_coverage(vec: VisualExecutionContract, issues: list[Gate0Issue]) -> None:
    if not vec.source_fact_ids:
        issues.append(
            Gate0Issue(
                rule="fact_coverage",
                path=vec.contract_id,
                detail="VEC binds no source facts",
            )
        )
    approved = set(vec.source_fact_ids)
    for event in vec.audio_events:
        if event.source_fact_id not in approved:
            issues.append(
                Gate0Issue(
                    rule="fact_invention",
                    path=event.event_id,
                    detail=f"audio event sourced from unapproved fact {event.source_fact_id}",
                )
            )
    for reference in vec.reference_requirements:
        if not set(reference.source_fact_ids).issubset(approved):
            issues.append(
                Gate0Issue(
                    rule="fact_invention",
                    path=reference.requirement_id,
                    detail="reference requirement binds facts outside the VEC set",
                )
            )


def _check_projection_homology(
    ast: ProjectionAST,
    storyboard: StoryboardProjection,
    video: VideoProjection,
    issues: list[Gate0Issue],
) -> None:
    ast_sources = set(ast.source_node_ids)
    for node in storyboard.nodes:
        if node.source_id not in ast_sources:
            issues.append(
                Gate0Issue(
                    rule="projection_homology",
                    path=node.source_id,
                    detail="storyboard node is not sourced from the ProjectionAST",
                )
            )
    video_sources = [node.source_id for node in video.nodes]
    if tuple(video_sources) != tuple(ast.source_node_ids):
        issues.append(
            Gate0Issue(
                rule="projection_homology",
                path="video",
                detail="video projection must carry every AST node in order",
            )
        )


def run_gate0(
    *,
    vec: VisualExecutionContract,
    ast: ProjectionAST,
    storyboard: StoryboardProjection,
    video: VideoProjection,
    claim_ceiling: str,
) -> Gate0Result:
    """Run the deterministic Gate 0 over the assembled artifacts.

    Pure and deterministic: identical inputs always produce identical issues
    and result_id.  ``claim_ceiling`` must be TEXT_VALIDATED — any visual
    claim from a text pipeline is rejected.
    """
    issues: list[Gate0Issue] = []

    if claim_ceiling != TEXT_VALIDATED:
        issues.append(
            Gate0Issue(
                rule="claim_ceiling",
                path="pipeline",
                detail=(
                    f"text pipeline claim ceiling must be {TEXT_VALIDATED}, "
                    f"got {claim_ceiling}"
                ),
            )
        )

    if ast.vec_digest != canonical_sha256(vec):
        issues.append(
            Gate0Issue(
                rule="digest_binding",
                path=ast.ast_id,
                detail="ProjectionAST vec_digest does not match the VEC",
            )
        )

    _check_id_uniqueness(vec, issues)
    _check_tick_integrity(vec, issues)
    _check_fact_coverage(vec, issues)
    _check_projection_homology(ast, storyboard, video, issues)

    passed = not issues
    input_digests = {
        "vec_digest": canonical_sha256(vec),
        "projection_ast_digest": ast.ast_digest,
    }
    result_id = canonical_sha256(
        {
            "input_digests": input_digests,
            "claim_ceiling": claim_ceiling,
            "issues": issues,
        }
    )
    attribution = None
    if not passed:
        attribution = gate0_attribution(
            scene_id=vec.scene_id,
            reason="; ".join(f"{issue.rule}:{issue.path}" for issue in issues[:3]),
        )

    return Gate0Result(
        result_id=result_id,
        passed=passed,
        issues=tuple(issues),
        input_digests=input_digests,
        attribution=attribution,
    )
