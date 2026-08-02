"""Fail-closed routing for bounded v3.0 DP revision requests.

The DP never patches a VEC or ProjectionAST.  A validated request either
returns to a Director-owned Draft field, triggers a deterministic projection
recompile, or is rejected.  The route is a control DTO, not a second
persistent revision authority.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from mode_p_vnext.domain.artifact import DomainValidationError
from mode_p_vnext.domain.evidence import RevisionFailureType, RevisionRequest


class RevisionRouteKind(str, enum.Enum):
    DIRECTOR_DRAFT_REVISION = "DIRECTOR_DRAFT_REVISION"
    PROJECTION_RECOMPILE = "PROJECTION_RECOMPILE"
    REJECT = "REJECT"


@dataclass(frozen=True)
class RevisionScope:
    """Local allowlist for one target artifact and its writable Draft fields."""

    target_artifact_id: str
    route_kind: RevisionRouteKind
    allowed_field_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.target_artifact_id, str) or not self.target_artifact_id:
            raise DomainValidationError("target_artifact_id must be non-empty")
        if self.route_kind is RevisionRouteKind.REJECT:
            raise DomainValidationError("a RevisionScope cannot authorize REJECT")
        paths = tuple(self.allowed_field_paths)
        if not paths or any(
            not isinstance(item, str) or not item.strip() for item in paths
        ):
            raise DomainValidationError("allowed_field_paths must be non-empty paths")
        if len(paths) != len(set(paths)):
            raise DomainValidationError("allowed_field_paths must not contain duplicates")
        object.__setattr__(self, "allowed_field_paths", paths)


@dataclass(frozen=True)
class RevisionRoute:
    kind: RevisionRouteKind
    request: RevisionRequest
    patch_budget_remaining: int
    reason: str


def _path_is_bounded(path: str, allowed: tuple[str, ...]) -> bool:
    return any(path == root or path.startswith(root + ".") for root in allowed)


def validate_revision_request(
    request: RevisionRequest,
    *,
    scope: RevisionScope,
    allowed_fact_refs: tuple[str, ...],
) -> None:
    """Prove that a canonical request remains inside its local packet scope."""

    if type(request) is not RevisionRequest:
        raise DomainValidationError("request must use the exact canonical RevisionRequest")
    if request.target_artifact_id != scope.target_artifact_id:
        raise DomainValidationError("revision target is outside its authorized scope")
    if not set(request.fact_refs).issubset(allowed_fact_refs):
        raise DomainValidationError("revision request references facts outside its ReviewPacket")
    if not all(_path_is_bounded(item, scope.allowed_field_paths) for item in request.field_paths):
        raise DomainValidationError("revision request field path exceeds its bounded scope")
    projection_failure = request.failure_type in {
        RevisionFailureType.PROJECTION_DIVERGENCE,
        RevisionFailureType.CAPABILITY,
    }
    if projection_failure != (scope.route_kind is RevisionRouteKind.PROJECTION_RECOMPILE):
        raise DomainValidationError("revision failure type does not match the authorized route")


def route_revisions(
    requests: tuple[RevisionRequest, ...],
    *,
    scopes: tuple[RevisionScope, ...],
    allowed_fact_refs: tuple[str, ...],
    patch_budget: int,
) -> tuple[RevisionRoute, ...]:
    """Route exact, bounded requests under a fixed Director-patch budget."""

    if isinstance(patch_budget, bool) or not isinstance(patch_budget, int) or patch_budget < 0:
        raise DomainValidationError("patch_budget must be a non-negative integer")
    if not all(type(item) is RevisionRequest for item in requests):
        raise DomainValidationError("requests must contain canonical RevisionRequest values")
    scope_by_target = {item.target_artifact_id: item for item in scopes}
    if len(scope_by_target) != len(scopes):
        raise DomainValidationError("revision target scopes must be unique")

    remaining = patch_budget
    routes: list[RevisionRoute] = []
    for request in requests:
        scope = scope_by_target.get(request.target_artifact_id)
        if scope is None:
            routes.append(
                RevisionRoute(
                    kind=RevisionRouteKind.REJECT,
                    request=request,
                    patch_budget_remaining=remaining,
                    reason="target artifact is not authorized",
                )
            )
            continue
        try:
            validate_revision_request(
                request,
                scope=scope,
                allowed_fact_refs=allowed_fact_refs,
            )
        except DomainValidationError as exc:
            routes.append(
                RevisionRoute(
                    kind=RevisionRouteKind.REJECT,
                    request=request,
                    patch_budget_remaining=remaining,
                    reason=str(exc),
                )
            )
            continue
        if scope.route_kind is RevisionRouteKind.PROJECTION_RECOMPILE:
            routes.append(
                RevisionRoute(
                    kind=scope.route_kind,
                    request=request,
                    patch_budget_remaining=remaining,
                    reason="deterministic recompile; canonical VEC remains unchanged",
                )
            )
        elif remaining > 0:
            remaining -= 1
            routes.append(
                RevisionRoute(
                    kind=RevisionRouteKind.DIRECTOR_DRAFT_REVISION,
                    request=request,
                    patch_budget_remaining=remaining,
                    reason="return to bounded Director Draft field",
                )
            )
        else:
            routes.append(
                RevisionRoute(
                    kind=RevisionRouteKind.REJECT,
                    request=request,
                    patch_budget_remaining=0,
                    reason="Director revision budget exhausted",
                )
            )
    return tuple(routes)


__all__ = [
    "RevisionFailureType",
    "RevisionRequest",
    "RevisionRoute",
    "RevisionRouteKind",
    "RevisionScope",
    "route_revisions",
    "validate_revision_request",
]
