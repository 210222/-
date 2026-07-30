"""Production-safe routing from a sealed DP response to a local revision plan.

The router is intentionally narrow: it proves that the response came from the
current fresh DP packet, returns it to the persistent Director, scopes it to
the reported objects/boundaries, and allocates a different context for the
mandatory post-revision DP review. It never proposes an artistic solution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from mode_p_vnext.dp_manifest import DPPacketManifest, new_dp_context_id
from mode_p_vnext.dp_response_contract import DPResponse, DPResponseViolation
from mode_p_vnext.targeted_revision import (
    RevisionScopeError,
    RevisionTopology,
    TargetedRevision,
    targeted_revision_from_dp,
)


class DPRevisionRouteError(ValueError):
    """A response cannot safely enter a Director revision route."""


@dataclass(frozen=True)
class DPRevisionRoute:
    revision: TargetedRevision
    source_context_id: str
    next_context_id: str
    source_manifest_sha256: str
    validation_level: str = "TEXT_VALIDATED"


def route_dp_revision(
    *,
    revision_id: str,
    response: DPResponse,
    manifest: DPPacketManifest,
    topology: RevisionTopology,
    persistent_director_id: str,
    base_contract_sha256: str,
    revised_contract_sha256: str,
    modified_objects: Sequence[str] | None = None,
    affected_boundaries: Sequence[str] | None = None,
) -> DPRevisionRoute:
    """Create a fail-closed, same-Director local revision route."""
    if not base_contract_sha256 or not revised_contract_sha256:
        raise DPRevisionRouteError("base and revised contract hashes are required")
    if base_contract_sha256 == revised_contract_sha256:
        raise DPRevisionRouteError("unchanged contract cannot reuse or trigger a fresh DP review")
    try:
        manifest.validate_for_invocation()
        response.validate_against_manifest(
            manifest,
            available_scope_keys=tuple(topology.normalized_object_ids),
        )
    except (ValueError, DPResponseViolation) as exc:
        raise DPRevisionRouteError(str(exc)) from exc
    if response.verdict == "INPUT_BLOCK":
        raise DPRevisionRouteError("INPUT_BLOCK must repair input before any Director revision")
    if response.verdict != "DIRECTED_QUESTION":
        raise DPRevisionRouteError("only a directed DP question can route to Director")
    next_context_id = new_dp_context_id("DPCTX-REV")
    try:
        revision = targeted_revision_from_dp(
            revision_id,
            response,
            topology,
            director_id=persistent_director_id,
            parent_context_id=manifest.context_id,
            fresh_context_id=next_context_id,
            modified_objects=modified_objects,
            affected_boundaries=affected_boundaries,
            base_contract_sha256=base_contract_sha256,
            revised_contract_sha256=revised_contract_sha256,
        )
    except RevisionScopeError as exc:
        raise DPRevisionRouteError(str(exc)) from exc
    return DPRevisionRoute(
        revision=revision,
        source_context_id=manifest.context_id,
        next_context_id=next_context_id,
        source_manifest_sha256=manifest.content_sha256,
    )
