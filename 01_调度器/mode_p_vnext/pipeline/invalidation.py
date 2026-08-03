"""Field- and capability-scoped invalidation for the v3.1 runtime ledger."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    ValidationStatus,
    require_sha256,
)

from .graph import StateGraph
from .state import (
    SUPERSEDED_LIFECYCLE_STATUS,
    PersistentGraphState,
    StateInvariantError,
)


def _digest(value: object, field_name: str) -> str:
    try:
        require_sha256(value, field_name)  # type: ignore[arg-type]
    except DomainValidationError as exc:
        raise StateInvariantError(str(exc)) from exc
    return value  # type: ignore[return-value]


def _non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StateInvariantError(f"{field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class InvalidationRecord:
    """Replayable runtime evidence; no domain payload is duplicated here."""

    reason: str
    changed_field_digests: Mapping[str, str]
    invalidated_node_ids: tuple[str, ...]
    invalidated_artifact_digests: tuple[str, ...]
    retained_artifact_digests: tuple[str, ...]
    source_candidate_revision: int
    source_candidate_digest: str
    source_candidate_validation_status: str
    next_candidate_revision: int
    next_candidate_digest: str
    next_candidate_validation_status: str
    retired_lifecycle_status: str | None
    invalidation_kind: str = "field"

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise StateInvariantError("invalidation reason must be non-empty")
        if self.invalidation_kind not in {"field", "capability_profile", "knowledge_snapshot"}:
            raise StateInvariantError("invalid invalidation_kind")
        if not isinstance(self.changed_field_digests, Mapping) or not self.changed_field_digests:
            raise StateInvariantError("changed_field_digests must be a non-empty mapping")
        frozen: dict[str, str] = {}
        for field_name, digest in self.changed_field_digests.items():
            if not isinstance(field_name, str) or not field_name.strip():
                raise StateInvariantError("changed fields must have non-empty names")
            frozen[field_name] = _digest(digest, f"changed_field_digests[{field_name}]")
        if len(self.invalidated_node_ids) != len(set(self.invalidated_node_ids)):
            raise StateInvariantError("invalidated_node_ids must not contain duplicates")
        for node_id in self.invalidated_node_ids:
            if not isinstance(node_id, str) or not node_id.strip():
                raise StateInvariantError("invalidated node IDs must be non-empty")
        for digest in self.invalidated_artifact_digests:
            _digest(digest, "invalidated_artifact_digests")
        if len(self.retained_artifact_digests) != len(set(self.retained_artifact_digests)):
            raise StateInvariantError("retained_artifact_digests must not contain duplicates")
        for digest in self.retained_artifact_digests:
            _digest(digest, "retained_artifact_digests")
        if set(self.invalidated_artifact_digests) & set(self.retained_artifact_digests):
            raise StateInvariantError("an artifact cannot be invalidated and retained together")
        _non_negative_int(self.source_candidate_revision, "source_candidate_revision")
        _digest(self.source_candidate_digest, "source_candidate_digest")
        try:
            source_status = ValidationStatus(self.source_candidate_validation_status)
            next_status = ValidationStatus(self.next_candidate_validation_status)
        except (TypeError, ValueError) as exc:
            raise StateInvariantError(
                "invalidation candidate validation statuses must be canonical values"
            ) from exc
        if source_status not in {ValidationStatus.DRAFT, ValidationStatus.TEXT_VALIDATED}:
            raise StateInvariantError("invalidation source status cannot claim media or owner validation")
        if next_status not in {ValidationStatus.DRAFT, ValidationStatus.TEXT_VALIDATED}:
            raise StateInvariantError("invalidation target status cannot claim media or owner validation")
        _non_negative_int(self.next_candidate_revision, "next_candidate_revision")
        _digest(self.next_candidate_digest, "next_candidate_digest")
        if self.invalidated_node_ids:
            if self.next_candidate_revision != self.source_candidate_revision + 1:
                raise StateInvariantError("an invalidation must advance candidate_revision exactly once")
            if self.retired_lifecycle_status != SUPERSEDED_LIFECYCLE_STATUS:
                raise StateInvariantError("invalidated nodes must be recorded as superseded")
            if next_status is not ValidationStatus.DRAFT:
                raise StateInvariantError("a replacement candidate must restart at DRAFT")
        elif (
            self.next_candidate_revision != self.source_candidate_revision
            or self.next_candidate_digest != self.source_candidate_digest
            or next_status is not source_status
            or self.retired_lifecycle_status is not None
            or self.retained_artifact_digests
        ):
            raise StateInvariantError("a no-op invalidation cannot change candidate lifecycle")
        object.__setattr__(self, "changed_field_digests", MappingProxyType(frozen))
        object.__setattr__(self, "invalidated_node_ids", tuple(self.invalidated_node_ids))
        object.__setattr__(self, "invalidated_artifact_digests", tuple(self.invalidated_artifact_digests))

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "changed_field_digests": dict(self.changed_field_digests),
            "invalidated_node_ids": self.invalidated_node_ids,
            "invalidated_artifact_digests": self.invalidated_artifact_digests,
            "retained_artifact_digests": self.retained_artifact_digests,
            "source_candidate_revision": self.source_candidate_revision,
            "source_candidate_digest": self.source_candidate_digest,
            "source_candidate_validation_status": self.source_candidate_validation_status,
            "next_candidate_revision": self.next_candidate_revision,
            "next_candidate_digest": self.next_candidate_digest,
            "next_candidate_validation_status": self.next_candidate_validation_status,
            "retired_lifecycle_status": self.retired_lifecycle_status,
            "invalidation_kind": self.invalidation_kind,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "InvalidationRecord":
        expected = {
            "reason", "changed_field_digests", "invalidated_node_ids",
            "invalidated_artifact_digests", "retained_artifact_digests", "source_candidate_revision",
            "source_candidate_digest", "source_candidate_validation_status",
            "next_candidate_revision", "next_candidate_digest",
            "next_candidate_validation_status", "retired_lifecycle_status", "invalidation_kind",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise StateInvariantError("invalidation record fields do not match the v3.1 schema")
        return cls(
            reason=value["reason"],
            changed_field_digests=value["changed_field_digests"],
            invalidated_node_ids=tuple(value["invalidated_node_ids"]),
            invalidated_artifact_digests=tuple(value["invalidated_artifact_digests"]),
            retained_artifact_digests=tuple(value["retained_artifact_digests"]),
            source_candidate_revision=value["source_candidate_revision"],
            source_candidate_digest=value["source_candidate_digest"],
            source_candidate_validation_status=value["source_candidate_validation_status"],
            next_candidate_revision=value["next_candidate_revision"],
            next_candidate_digest=value["next_candidate_digest"],
            next_candidate_validation_status=value["next_candidate_validation_status"],
            retired_lifecycle_status=value["retired_lifecycle_status"],
            invalidation_kind=value["invalidation_kind"],
        )


def _record(
    *,
    state: PersistentGraphState,
    next_state: PersistentGraphState,
    reason: str,
    changed_field_digests: Mapping[str, str],
    invalidated_node_ids: tuple[str, ...],
    invalidated_artifact_digests: tuple[str, ...],
    invalidation_kind: str,
) -> InvalidationRecord:
    """Create transition evidence that binds lifecycle to candidate identity."""

    return InvalidationRecord(
        reason=reason,
        changed_field_digests=changed_field_digests,
        invalidated_node_ids=invalidated_node_ids,
        invalidated_artifact_digests=invalidated_artifact_digests,
        retained_artifact_digests=tuple(
            retained.artifact_ref.artifact_digest
            for field_name, retained in sorted(next_state.retained_outputs.items())
            if state.retained_outputs.get(field_name) != retained
        ),
        source_candidate_revision=state.candidate_revision,
        source_candidate_digest=state.candidate_digest,
        source_candidate_validation_status=state.candidate_validation_status.value,
        next_candidate_revision=next_state.candidate_revision,
        next_candidate_digest=next_state.candidate_digest,
        next_candidate_validation_status=next_state.candidate_validation_status.value,
        retired_lifecycle_status=(
            SUPERSEDED_LIFECYCLE_STATUS if invalidated_node_ids else None
        ),
        invalidation_kind=invalidation_kind,
    )


@dataclass(frozen=True)
class InvalidationResult:
    state: PersistentGraphState
    record: InvalidationRecord

    @property
    def invalidated_node_ids(self) -> tuple[str, ...]:
        return self.record.invalidated_node_ids


class FieldInvalidator:
    """Maps explicit changed fields to the minimal graph dependency closure."""

    def __init__(self, graph: StateGraph):
        self.graph = graph

    def invalidate(
        self,
        state: PersistentGraphState,
        *,
        changed_field_digests: Mapping[str, str],
        reason: str,
        commit_id: str,
        invalidation_kind: str = "field",
    ) -> InvalidationResult:
        self.graph.validate_state(state)
        seed = _record(
            state=state,
            next_state=state,
            reason=reason,
            changed_field_digests=changed_field_digests,
            invalidated_node_ids=(),
            invalidated_artifact_digests=(),
            invalidation_kind=invalidation_kind,
        )
        next_state, node_ids, artifact_digests = self.graph.invalidate(
            state,
            changed_fields=tuple(seed.changed_field_digests),
            commit_id=commit_id,
        )
        return InvalidationResult(
            state=next_state,
            record=_record(
                state=state,
                next_state=next_state,
                reason=seed.reason,
                changed_field_digests=seed.changed_field_digests,
                invalidated_node_ids=node_ids,
                invalidated_artifact_digests=artifact_digests,
                invalidation_kind=seed.invalidation_kind,
            ),
        )

    def invalidate_capability_profile(
        self,
        state: PersistentGraphState,
        *,
        capability_profile_digest: str,
        reason: str,
        commit_id: str,
    ) -> InvalidationResult:
        """Invalidate only accepted capability consumers and their dependents."""
        self.graph.validate_state(state)
        digest = _digest(capability_profile_digest, "capability_profile_digest")
        roots: list[str] = []
        for node in self.graph.nodes:
            acceptance = state.accepted.get(node.node_id)
            if (
                acceptance is not None
                and node.uses_capability_profile
                and acceptance.capability_profile_digest != digest
            ):
                roots.append(node.node_id)
        if not roots:
            return InvalidationResult(
                state=state,
                record=_record(
                    state=state,
                    next_state=state,
                    reason=reason,
                    changed_field_digests={"capability_profile": digest},
                    invalidated_node_ids=(),
                    invalidated_artifact_digests=(),
                    invalidation_kind="capability_profile",
                ),
            )
        closure: list[str] = []
        for root in roots:
            for node_id in self.graph.invalidation_closure(self.graph.node(root).owns_fields):
                if node_id not in closure:
                    closure.append(node_id)
        next_state, node_ids, artifact_digests = self.graph.invalidate_node_ids(
            state, node_ids=closure, commit_id=commit_id
        )
        return InvalidationResult(
            state=next_state,
            record=_record(
                state=state,
                next_state=next_state,
                reason=reason,
                changed_field_digests={"capability_profile": digest},
                invalidated_node_ids=node_ids,
                invalidated_artifact_digests=artifact_digests,
                invalidation_kind="capability_profile",
            ),
        )

    def invalidate_knowledge_snapshot(
        self,
        state: PersistentGraphState,
        *,
        knowledge_snapshot_digest: str,
        reason: str,
        commit_id: str,
    ) -> InvalidationResult:
        """Candidate churn without a selected-snapshot change is a strict no-op."""
        self.graph.validate_state(state)
        digest = _digest(knowledge_snapshot_digest, "knowledge_snapshot_digest")
        roots: list[str] = []
        for node in self.graph.nodes:
            acceptance = state.accepted.get(node.node_id)
            if (
                acceptance is not None
                and node.uses_knowledge_snapshot
                and acceptance.knowledge_snapshot_digest != digest
            ):
                roots.append(node.node_id)
        if not roots:
            return InvalidationResult(
                state=state,
                record=_record(
                    state=state,
                    next_state=state,
                    reason=reason,
                    changed_field_digests={"knowledge_snapshot": digest},
                    invalidated_node_ids=(),
                    invalidated_artifact_digests=(),
                    invalidation_kind="knowledge_snapshot",
                ),
            )
        closure: list[str] = []
        for root in roots:
            for node_id in self.graph.invalidation_closure(self.graph.node(root).owns_fields):
                if node_id not in closure:
                    closure.append(node_id)
        next_state, node_ids, artifact_digests = self.graph.invalidate_node_ids(
            state, node_ids=closure, commit_id=commit_id
        )
        return InvalidationResult(
            state=next_state,
            record=_record(
                state=state,
                next_state=next_state,
                reason=reason,
                changed_field_digests={"knowledge_snapshot": digest},
                invalidated_node_ids=node_ids,
                invalidated_artifact_digests=artifact_digests,
                invalidation_kind="knowledge_snapshot",
            ),
        )
