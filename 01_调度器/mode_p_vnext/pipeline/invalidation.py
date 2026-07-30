"""Field and digest-edge invalidation for the canonical state graph."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from mode_p_vnext.domain.artifact import DomainValidationError, require_sha256

from .graph import StateGraph
from .state import PersistentGraphState, StateInvariantError


@dataclass(frozen=True)
class InvalidationRecord:
    reason: str
    changed_field_digests: Mapping[str, str]
    invalidated_node_ids: tuple[str, ...]
    invalidated_artifact_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise StateInvariantError("invalidation reason must be non-empty")
        frozen: dict[str, str] = {}
        for field_name, digest in self.changed_field_digests.items():
            if not isinstance(field_name, str) or not field_name.strip():
                raise StateInvariantError("changed fields must have non-empty names")
            try:
                require_sha256(digest, f"changed_field_digests[{field_name}]")
            except DomainValidationError as exc:
                raise StateInvariantError(str(exc)) from exc
            frozen[field_name] = digest
        object.__setattr__(self, "changed_field_digests", MappingProxyType(frozen))

    def to_dict(self) -> dict[str, object]:
        return {
            "reason": self.reason,
            "changed_field_digests": dict(self.changed_field_digests),
            "invalidated_node_ids": self.invalidated_node_ids,
            "invalidated_artifact_digests": self.invalidated_artifact_digests,
        }


@dataclass(frozen=True)
class InvalidationResult:
    state: PersistentGraphState
    record: InvalidationRecord

    @property
    def invalidated_node_ids(self) -> tuple[str, ...]:
        return self.record.invalidated_node_ids


class FieldInvalidator:
    def __init__(self, graph: StateGraph):
        self.graph = graph

    def invalidate(
        self,
        state: PersistentGraphState,
        *,
        changed_field_digests: Mapping[str, str],
        reason: str,
    ) -> InvalidationResult:
        seed = InvalidationRecord(
            reason=reason,
            changed_field_digests=changed_field_digests,
            invalidated_node_ids=(),
            invalidated_artifact_digests=(),
        )
        next_state, node_ids, artifact_digests = self.graph.invalidate(
            state, changed_fields=tuple(seed.changed_field_digests)
        )
        return InvalidationResult(
            state=next_state,
            record=InvalidationRecord(
                reason=seed.reason,
                changed_field_digests=seed.changed_field_digests,
                invalidated_node_ids=node_ids,
                invalidated_artifact_digests=artifact_digests,
            ),
        )
