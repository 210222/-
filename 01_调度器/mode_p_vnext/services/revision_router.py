"""Bounded revision router — routes DP findings without rewriting the VEC.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.3 / §14 A7.

The router turns scoped RevisionRequests into routes:

- LOCAL_DERIVATION: deterministic local repair (no model call, no budget);
- SCOPED_PATCH: one model patch that consumes part of the patch budget;
- REJECT: fail-closed when the budget is exhausted.

The router never rewrites the VEC — it only emits requests and routes.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from mode_p_vnext.domain.artifact import DomainValidationError

# Failure types that local deterministic derivation can repair without a model.
_LOCAL_REPAIRABLE_FAILURES = frozenset(
    {"schema", "range", "enum", "integrity", "reference_closure", "tick"}
)


class RevisionRouteKind(str, enum.Enum):
    LOCAL_DERIVATION = "LOCAL_DERIVATION"
    SCOPED_PATCH = "SCOPED_PATCH"
    REJECT = "REJECT"


@dataclass(frozen=True)
class RevisionRequest:
    """A scoped finding from DP: never a VEC rewrite, always a request."""

    target_artifact_id: str
    field_path: str
    failure_type: str
    reason: str

    def __post_init__(self) -> None:
        for field_name in ("target_artifact_id", "field_path", "failure_type", "reason"):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name):
                raise DomainValidationError(f"{field_name} must be non-empty")


@dataclass(frozen=True)
class RevisionRoute:
    """One routed revision decision."""

    kind: RevisionRouteKind
    request: RevisionRequest
    patch_budget_remaining: int


def route_revisions(
    requests: tuple[RevisionRequest, ...],
    *,
    patch_budget: int,
) -> tuple[RevisionRoute, ...]:
    """Route requests under a fixed patch budget, fail-closed on exhaustion.

    Local derivation repairs never consume budget.  Creative/choice failures
    require a scoped model patch; when the budget is exhausted they are
    rejected instead of silently downgraded.
    """
    if isinstance(patch_budget, bool) or not isinstance(patch_budget, int) or patch_budget < 0:
        raise DomainValidationError("patch_budget must be a non-negative integer")

    remaining = patch_budget
    routes: list[RevisionRoute] = []
    for request in requests:
        if request.failure_type in _LOCAL_REPAIRABLE_FAILURES:
            routes.append(
                RevisionRoute(
                    kind=RevisionRouteKind.LOCAL_DERIVATION,
                    request=request,
                    patch_budget_remaining=remaining,
                )
            )
        elif remaining > 0:
            remaining -= 1
            routes.append(
                RevisionRoute(
                    kind=RevisionRouteKind.SCOPED_PATCH,
                    request=request,
                    patch_budget_remaining=remaining,
                )
            )
        else:
            routes.append(
                RevisionRoute(
                    kind=RevisionRouteKind.REJECT,
                    request=request,
                    patch_budget_remaining=0,
                )
            )
    return tuple(routes)
