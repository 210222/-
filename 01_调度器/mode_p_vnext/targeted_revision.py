"""Directed, same-Director revision planning for DP findings.

This module routes a bounded DP question back to the persistent Director. It
does not answer the question or generate a replacement scene. Only referenced
review objects and truly adjacent boundaries may change; every revision must
then run precheck, derivation and a fresh DP review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence, Set, Tuple

from mode_p_vnext.dp_response_contract import DPResponse


class RevisionScopeError(ValueError):
    """A proposed correction escapes the directed DP scope."""


_REQUIRED_NEXT_STEPS: Tuple[str, ...] = (
    "PRECHECK_REQUIRED",
    "DERIVE_REQUIRED",
    "FRESH_DP_REQUIRED",
)
_GLOBAL_SCOPE_MARKERS: Tuple[str, ...] = (
    "whole scene", "entire scene", "all shots", "scene rewrite", "master rewrite",
    "全场", "整场", "全部镜头", "重写场景",
)


def _normalise_object_id(value: str) -> str:
    text = " ".join(value.strip().split())
    lowered = text.lower()
    for prefix in ("segment", "shot", "beat", "panel", "fidelity"):
        if lowered.startswith(prefix + " "):
            return prefix + ":" + text[len(prefix):].strip()
        if lowered.startswith(prefix + ":"):
            return prefix + ":" + text.split(":", 1)[1].strip()
    return text


def _is_global_scope(value: str) -> bool:
    lowered = " ".join(value.lower().split())
    return any(marker in lowered for marker in _GLOBAL_SCOPE_MARKERS)


@dataclass(frozen=True)
class RevisionTopology:
    """Validated object/boundary topology used to constrain a revision."""

    director_id: str
    object_ids: Tuple[str, ...]
    boundary_endpoints: Mapping[str, Tuple[str, str]] = field(default_factory=dict)
    frozen_segment_ids: Tuple[str, ...] = field(default_factory=tuple)
    object_segment_ids: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = [_normalise_object_id(item) for item in self.object_ids]
        if len(normalized) != len(set(normalized)):
            raise ValueError("RevisionTopology object_ids contains duplicates")
        for boundary_id, endpoints in self.boundary_endpoints.items():
            if not boundary_id or len(endpoints) != 2:
                raise ValueError("every boundary requires two endpoint object IDs")

    @property
    def normalized_object_ids(self) -> Set[str]:
        return {_normalise_object_id(item) for item in self.object_ids}

    def segment_for(self, object_id: str) -> str:
        normalized = _normalise_object_id(object_id)
        if normalized.startswith("segment:"):
            return normalized.split(":", 1)[1]
        return self.object_segment_ids.get(normalized, "")

    def adjacent_boundaries(self, scope_ids: Sequence[str]) -> Set[str]:
        scope = {_normalise_object_id(item) for item in scope_ids}
        result: Set[str] = set()
        for boundary_id, endpoints in self.boundary_endpoints.items():
            if scope & {_normalise_object_id(item) for item in endpoints}:
                result.add(boundary_id)
        return result


@dataclass
class TargetedRevision:
    revision_id: str
    director_id: str
    modified_objects: list[str] = field(default_factory=list)
    affected_boundaries: list[str] = field(default_factory=list)
    fresh_dp_required: bool = True
    source_response_id: str = ""
    source_issue_ids: list[str] = field(default_factory=list)
    parent_context_id: str = ""
    fresh_context_id: str = ""
    base_contract_sha256: str = ""
    revised_contract_sha256: str = ""
    required_next_steps: list[str] = field(default_factory=lambda: list(_REQUIRED_NEXT_STEPS))
    validation_level: str = "TEXT_VALIDATED"

    @property
    def requires_same_director(self) -> bool:
        return True

    @property
    def normalized_modified_objects(self) -> Tuple[str, ...]:
        return tuple(_normalise_object_id(item) for item in self.modified_objects)


def _issue_scope(response: DPResponse, issue_ids: Sequence[str]) -> tuple[Set[str], Set[str]]:
    wanted = set(issue_ids) if issue_ids else {issue.issue_id for issue in response.issues}
    issues = [issue for issue in response.issues if issue.issue_id in wanted]
    if not issues or len(issues) != len(wanted):
        raise RevisionScopeError("revision must cite current DP issues")
    objects: Set[str] = set()
    boundaries: Set[str] = set()
    for issue in issues:
        objects.update(issue.binding_keys)
        boundaries.update(issue.affected_boundaries)
    return objects, boundaries


def validate_targeted_revision(
    revision: TargetedRevision,
    response: DPResponse,
    topology: RevisionTopology,
    *,
    expected_director_id: str = "",
    before_hashes: Mapping[str, str] | None = None,
    after_hashes: Mapping[str, str] | None = None,
) -> None:
    """Fail closed unless revision scope exactly follows current DP evidence."""
    if response.verdict != "DIRECTED_QUESTION":
        raise RevisionScopeError("only DIRECTED_QUESTION may route to Director revision")
    if not revision.revision_id or not revision.director_id:
        raise RevisionScopeError("revision_id and director_id are required")
    persistent_director = expected_director_id or topology.director_id
    if revision.director_id != persistent_director:
        raise RevisionScopeError("revision must return to the same persistent Director")
    if revision.source_response_id and revision.source_response_id != response.response_id:
        raise RevisionScopeError("revision response ID does not match current DP response")
    if not revision.fresh_dp_required:
        raise RevisionScopeError("revision must require a fresh DP review")
    if revision.parent_context_id and revision.fresh_context_id == revision.parent_context_id:
        raise RevisionScopeError("revision must receive a new DP context")
    if revision.base_contract_sha256 and revision.revised_contract_sha256 and revision.base_contract_sha256 == revision.revised_contract_sha256:
        raise RevisionScopeError("revision claims no contract change; old DP cannot be reused as fresh")
    if tuple(revision.required_next_steps) != _REQUIRED_NEXT_STEPS:
        raise RevisionScopeError("revision must run precheck, derive and fresh DP in order")
    if revision.validation_level != "TEXT_VALIDATED":
        raise RevisionScopeError("text DP cannot claim storyboard or media validation")

    allowed_objects, issue_boundaries = _issue_scope(response, revision.source_issue_ids)
    known_objects = topology.normalized_object_ids
    for object_id in revision.normalized_modified_objects:
        if _is_global_scope(object_id):
            raise RevisionScopeError("whole-scene or global revision is forbidden")
        if object_id not in known_objects:
            raise RevisionScopeError(f"revision targets unknown object: {object_id}")
        if object_id not in allowed_objects:
            raise RevisionScopeError(f"revision escapes DP issue scope: {object_id}")
        segment_id = topology.segment_for(object_id)
        if segment_id and segment_id in topology.frozen_segment_ids:
            raise RevisionScopeError(f"revision targets frozen/completed segment: {segment_id}")

    allowed_boundaries = issue_boundaries | topology.adjacent_boundaries(tuple(allowed_objects))
    for boundary_id in revision.affected_boundaries:
        if _is_global_scope(boundary_id):
            raise RevisionScopeError("whole-scene boundary revision is forbidden")
        if boundary_id not in topology.boundary_endpoints:
            raise RevisionScopeError(f"revision targets unknown boundary: {boundary_id}")
        if boundary_id not in allowed_boundaries:
            raise RevisionScopeError(f"revision targets non-adjacent boundary: {boundary_id}")

    if before_hashes is not None and after_hashes is not None:
        allowed = set(revision.normalized_modified_objects)
        for object_id in set(before_hashes) & set(after_hashes):
            if _normalise_object_id(object_id) not in allowed and before_hashes[object_id] != after_hashes[object_id]:
                raise RevisionScopeError(f"unaffected object changed: {object_id}")


def targeted_revision_from_dp(
    revision_id: str,
    response: DPResponse,
    topology: RevisionTopology,
    *,
    director_id: str,
    parent_context_id: str,
    fresh_context_id: str,
    modified_objects: Sequence[str] | None = None,
    affected_boundaries: Sequence[str] | None = None,
    base_contract_sha256: str = "",
    revised_contract_sha256: str = "",
) -> TargetedRevision:
    """Create a bounded revision request from a DP response; never a new scene plan."""
    if response.verdict == "INPUT_BLOCK":
        raise RevisionScopeError("INPUT_BLOCK requires input repair, not Director revision")
    if response.verdict != "DIRECTED_QUESTION":
        raise RevisionScopeError("only DIRECTED_QUESTION can create a revision plan")
    issue_ids = [issue.issue_id for issue in response.issues]
    issue_objects, issue_boundaries = _issue_scope(response, issue_ids)
    revision = TargetedRevision(
        revision_id=revision_id,
        director_id=director_id,
        modified_objects=list(modified_objects) if modified_objects is not None else sorted(issue_objects),
        affected_boundaries=list(affected_boundaries) if affected_boundaries is not None else sorted(
            issue_boundaries | topology.adjacent_boundaries(tuple(issue_objects))
        ),
        source_response_id=response.response_id,
        source_issue_ids=issue_ids,
        parent_context_id=parent_context_id,
        fresh_context_id=fresh_context_id,
        base_contract_sha256=base_contract_sha256,
        revised_contract_sha256=revised_contract_sha256,
    )
    validate_targeted_revision(revision, response, topology)
    return revision
