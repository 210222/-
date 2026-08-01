"""Field- and capability-scoped invalidation for the v3.0 runtime ledger."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import DomainValidationError, require_sha256

from .graph import StateGraph
from .state import PersistentGraphState, StateInvariantError


def _digest(value: object, field_name: str) -> str:
    try:
        require_sha256(value, field_name)  # type: ignore[arg-type]
    except DomainValidationError as exc:
        raise StateInvariantError(str(exc)) from exc
    return value  # type: ignore[return-value]


@dataclass(frozen=True)
class InvalidationRecord:
    """Replayable runtime evidence; no domain payload is duplicated here."""

    reason: str
    changed_field_digests: Mapping[str, str]
    invalidated_node_ids: tuple[str, ...]
    invalidated_artifact_digests: tuple[str, ...]
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
        object.__setattr__(self, "changed_field_digests", MappingProxyType(frozen))
        object.__setattr__(self, "invalidated_node_ids", tuple(self.invalidated_node_ids))
        object.__setattr__(self, "invalidated_artifact_digests", tuple(self.invalidated_artifact_digests))

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "changed_field_digests": dict(self.changed_field_digests),
            "invalidated_node_ids": self.invalidated_node_ids,
            "invalidated_artifact_digests": self.invalidated_artifact_digests,
            "invalidation_kind": self.invalidation_kind,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "InvalidationRecord":
        expected = {
            "reason", "changed_field_digests", "invalidated_node_ids",
            "invalidated_artifact_digests", "invalidation_kind",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise StateInvariantError("invalidation record fields do not match the v3.0 schema")
        return cls(
            reason=value["reason"],
            changed_field_digests=value["changed_field_digests"],
            invalidated_node_ids=tuple(value["invalidated_node_ids"]),
            invalidated_artifact_digests=tuple(value["invalidated_artifact_digests"]),
            invalidation_kind=value["invalidation_kind"],
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
        seed = InvalidationRecord(
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
            record=InvalidationRecord(
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
                record=InvalidationRecord(
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
            record=InvalidationRecord(
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
                record=InvalidationRecord(
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
            record=InvalidationRecord(
                reason=reason,
                changed_field_digests={"knowledge_snapshot": digest},
                invalidated_node_ids=node_ids,
                invalidated_artifact_digests=artifact_digests,
                invalidation_kind="knowledge_snapshot",
            ),
        )
