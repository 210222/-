"""TypedState to PartialState graph rules for MODE:P vNext."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from mode_p_vnext.domain.artifact import ArtifactKind, DomainValidationError, require_sha256

from .state import ArtifactRef, NodeAcceptance, PersistentGraphState, StateInvariantError


def _tuple_of_text(value: Sequence[str], field_name: str, *, require_items: bool) -> tuple[str, ...]:
    values = tuple(value)
    if (require_items and not values) or any(not isinstance(item, str) or not item.strip() for item in values):
        raise StateInvariantError(f"{field_name} must contain non-empty strings")
    if len(values) != len(set(values)):
        raise StateInvariantError(f"{field_name} must not contain duplicates")
    return values


def _freeze_output_kinds(value: Mapping[str, ArtifactKind]) -> Mapping[str, ArtifactKind]:
    """Freeze the field-to-artifact contract that a node alone may publish."""
    if not isinstance(value, Mapping) or not value:
        raise StateInvariantError("output_kinds must be a non-empty mapping")
    frozen: dict[str, ArtifactKind] = {}
    for field_name, artifact_kind in value.items():
        if not isinstance(field_name, str) or not field_name.strip():
            raise StateInvariantError("output_kinds fields must be non-empty strings")
        if not isinstance(artifact_kind, ArtifactKind):
            raise StateInvariantError(
                f"output_kinds[{field_name}] must be an ArtifactKind"
            )
        frozen[field_name] = artifact_kind
    return MappingProxyType(frozen)


@dataclass(frozen=True)
class NodeSpec:
    node_id: str
    node_version: str
    output_kinds: Mapping[str, ArtifactKind]
    input_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.node_version.strip():
            raise StateInvariantError("node_id and node_version must be non-empty")
        output_kinds = _freeze_output_kinds(self.output_kinds)
        owns = tuple(output_kinds)
        inputs = _tuple_of_text(self.input_fields, "input_fields", require_items=False)
        if set(inputs) & set(owns):
            raise StateInvariantError("a node cannot read and own the same field")
        object.__setattr__(self, "output_kinds", output_kinds)
        object.__setattr__(self, "input_fields", inputs)

    @property
    def owns_fields(self) -> tuple[str, ...]:
        """The derived field list; kind authority stays in ``output_kinds``."""
        return tuple(self.output_kinds)


class StateGraph:
    """A deterministic field-owner graph with no implicit path dependencies."""

    def __init__(self, nodes: Sequence[NodeSpec]):
        values = tuple(nodes)
        if not values or not all(isinstance(item, NodeSpec) for item in values):
            raise StateInvariantError("StateGraph requires NodeSpec values")
        identifiers = tuple(item.node_id for item in values)
        if len(identifiers) != len(set(identifiers)):
            raise StateInvariantError("node_id must be unique")
        owners: dict[str, str] = {}
        output_kinds: dict[str, ArtifactKind] = {}
        for node in values:
            for field_name in node.owns_fields:
                if field_name in owners:
                    raise StateInvariantError(
                        f"field '{field_name}' has duplicate owners: {owners[field_name]}, {node.node_id}"
                )
                owners[field_name] = node.node_id
                output_kinds[field_name] = node.output_kinds[field_name]
        self._nodes = values
        self._by_id = MappingProxyType({item.node_id: item for item in values})
        self._owners = MappingProxyType(owners)
        self._output_kinds = MappingProxyType(output_kinds)

    @property
    def nodes(self) -> tuple[NodeSpec, ...]:
        return self._nodes

    def node(self, node_id: str) -> NodeSpec:
        try:
            return self._by_id[node_id]
        except KeyError as exc:
            raise StateInvariantError(f"unknown node '{node_id}'") from exc

    def descriptor(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "node_id": node.node_id,
                "node_version": node.node_version,
                "owns_fields": node.owns_fields,
                "output_kinds": {
                    field_name: artifact_kind.value
                    for field_name, artifact_kind in node.output_kinds.items()
                },
                "input_fields": node.input_fields,
            }
            for node in self._nodes
        )

    def expected_artifact_kind(self, field_name: str) -> ArtifactKind:
        try:
            return self._output_kinds[field_name]
        except KeyError as exc:
            raise StateInvariantError(f"unknown output field '{field_name}'") from exc

    def validate_state(self, state: PersistentGraphState) -> None:
        """Reject persisted state that is not a valid projection of this graph.

        ``PersistentGraphState`` intentionally carries no graph object so it
        can remain a portable value.  This graph-bound validation is therefore
        required whenever a state is loaded, recovered, or advanced.
        """
        if not isinstance(state, PersistentGraphState):
            raise StateInvariantError("state must be a PersistentGraphState")

        accepted_fields: set[str] = set()
        for node_id, acceptance in state.accepted.items():
            node = self.node(node_id)
            if acceptance.node_version != node.node_version:
                raise StateInvariantError(
                    f"accepted node '{node_id}' has a different node version"
                )
            if set(acceptance.output_digests) != set(node.owns_fields):
                raise StateInvariantError(
                    f"accepted node '{node_id}' output fields do not match its contract"
                )
            if set(acceptance.dependency_digests) != set(node.input_fields):
                raise StateInvariantError(
                    f"accepted node '{node_id}' dependency fields do not match its contract"
                )
            accepted_fields.update(node.owns_fields)
            for field_name in node.owns_fields:
                ref = state.outputs.get(field_name)
                if ref is None:
                    raise StateInvariantError(
                        f"accepted node '{node_id}' has no ArtifactRef for '{field_name}'"
                    )
                expected_kind = node.output_kinds[field_name]
                if ref.artifact_kind is not expected_kind:
                    raise StateInvariantError(
                        f"artifact kind for '{field_name}' must be "
                        f"{expected_kind.value}, got {ref.artifact_kind.value}"
                    )
                if acceptance.output_digests[field_name] != ref.content_sha256:
                    raise StateInvariantError(
                        f"accepted node '{node_id}' digest does not match '{field_name}'"
                    )
            for field_name, digest in acceptance.dependency_digests.items():
                if field_name in self._owners:
                    upstream = state.outputs.get(field_name)
                    if upstream is None or upstream.content_sha256 != digest:
                        raise StateInvariantError(
                            f"accepted node '{node_id}' dependency digest does not match "
                            f"'{field_name}'"
                        )

        if set(state.outputs) != accepted_fields:
            raise StateInvariantError(
                "persistent state outputs must be exactly the accepted node fields"
            )
        for field_name, ref in state.outputs.items():
            expected_kind = self.expected_artifact_kind(field_name)
            if ref.artifact_kind is not expected_kind:
                raise StateInvariantError(
                    f"artifact kind for '{field_name}' must be "
                    f"{expected_kind.value}, got {ref.artifact_kind.value}"
                )

    def apply(
        self,
        state: PersistentGraphState,
        *,
        node_id: str,
        outputs: Mapping[str, ArtifactRef],
        dependency_digests: Mapping[str, str],
        commit_id: str = "",
        cache_key: str = "",
    ) -> PersistentGraphState:
        if not isinstance(state, PersistentGraphState):
            raise StateInvariantError("state must be a PersistentGraphState")
        self.validate_state(state)
        node = self.node(node_id)
        if node_id in state.accepted:
            raise StateInvariantError(f"node '{node_id}' is already accepted")
        if not isinstance(outputs, Mapping):
            raise StateInvariantError("outputs must be a mapping")
        if set(outputs) != set(node.owns_fields):
            raise StateInvariantError(f"node '{node_id}' owns exactly {node.owns_fields}")
        if set(dependency_digests) != set(node.input_fields):
            raise StateInvariantError(f"node '{node_id}' dependency digests must match input fields")
        output_refs: dict[str, ArtifactRef] = {}
        for field_name in node.owns_fields:
            ref = outputs[field_name]
            if not isinstance(ref, ArtifactRef):
                raise StateInvariantError("node outputs must be ArtifactRef values")
            expected_kind = node.output_kinds[field_name]
            if ref.artifact_kind is not expected_kind:
                raise StateInvariantError(
                    f"artifact kind for '{field_name}' must be "
                    f"{expected_kind.value}, got {ref.artifact_kind.value}"
                )
            if field_name in state.outputs:
                raise StateInvariantError(f"owned field '{field_name}' already has an accepted value")
            output_refs[field_name] = ref
        for field_name, digest in dependency_digests.items():
            try:
                require_sha256(digest, f"dependency_digests[{field_name}]")
            except DomainValidationError as exc:
                raise StateInvariantError(str(exc)) from exc
            if field_name in self._owners:
                prior = state.outputs.get(field_name)
                if prior is None:
                    raise StateInvariantError(
                        f"node '{node_id}' cannot run before field '{field_name}' is accepted"
                    )
                if prior.content_sha256 != digest:
                    raise StateInvariantError(
                        f"dependency digest for '{field_name}' does not match its accepted ArtifactRef"
                    )
        next_outputs = dict(state.outputs)
        next_outputs.update(output_refs)
        next_accepted = dict(state.accepted)
        next_accepted[node_id] = NodeAcceptance(
            node_id=node_id,
            node_version=node.node_version,
            output_digests={field_name: ref.content_sha256 for field_name, ref in output_refs.items()},
            dependency_digests=dependency_digests,
            commit_id=commit_id,
            cache_key=cache_key,
        )
        next_state = PersistentGraphState(
            run_id=state.run_id,
            outputs=next_outputs,
            accepted=next_accepted,
            event_sequence=state.event_sequence + 1,
            current_commit_id=commit_id or state.current_commit_id,
        )
        self.validate_state(next_state)
        return next_state

    def runnable_node_ids(self, state: PersistentGraphState) -> tuple[str, ...]:
        runnable: list[str] = []
        for node in self._nodes:
            if node.node_id in state.accepted:
                continue
            if all(
                field_name not in self._owners or field_name in state.outputs
                for field_name in node.input_fields
            ):
                runnable.append(node.node_id)
        return tuple(runnable)

    def invalidation_closure(self, changed_fields: Sequence[str]) -> tuple[str, ...]:
        affected: list[str] = []
        pending = list(dict.fromkeys(changed_fields))
        cursor = 0
        while cursor < len(pending):
            field_name = pending[cursor]
            cursor += 1
            for node in self._nodes:
                if node.node_id in affected or field_name not in node.input_fields:
                    continue
                affected.append(node.node_id)
                pending.extend(node.owns_fields)
        return tuple(affected)

    def invalidate(
        self,
        state: PersistentGraphState,
        *,
        changed_fields: Sequence[str],
    ) -> tuple[PersistentGraphState, tuple[str, ...], tuple[str, ...]]:
        closure = self.invalidation_closure(changed_fields)
        node_ids = tuple(node_id for node_id in closure if node_id in state.accepted)
        if not node_ids:
            return state, (), ()
        invalidated_digests: list[str] = []
        next_outputs = dict(state.outputs)
        next_accepted = dict(state.accepted)
        for node_id in node_ids:
            acceptance = next_accepted.pop(node_id)
            node = self.node(node_id)
            for field_name in node.owns_fields:
                invalidated_digests.append(acceptance.output_digests[field_name])
                next_outputs.pop(field_name, None)
        return (
            PersistentGraphState(
                run_id=state.run_id,
                outputs=next_outputs,
                accepted=next_accepted,
                event_sequence=state.event_sequence + 1,
                current_commit_id=state.current_commit_id,
            ),
            node_ids,
            tuple(invalidated_digests),
        )
