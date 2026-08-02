"""Deterministic ownership and replay rules for the v3.0 state graph."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from mode_p_vnext.domain.artifact import ArtifactKind, DomainValidationError, canonical_sha256, require_sha256

from .state import ArtifactRef, NodeAcceptance, PersistentGraphState, StateInvariantError


def _texts(value: Sequence[str], field_name: str, *, required: bool = False) -> tuple[str, ...]:
    values = tuple(value)
    if (required and not values) or any(not isinstance(item, str) or not item.strip() for item in values):
        raise StateInvariantError(f"{field_name} must contain non-empty strings")
    if len(values) != len(set(values)):
        raise StateInvariantError(f"{field_name} must not contain duplicates")
    return values


def _output_types(value: Mapping[str, ArtifactKind]) -> Mapping[str, ArtifactKind]:
    if not isinstance(value, Mapping) or not value:
        raise StateInvariantError("output_types must be a non-empty mapping")
    frozen: dict[str, ArtifactKind] = {}
    for field_name, artifact_type in value.items():
        if not isinstance(field_name, str) or not field_name.strip():
            raise StateInvariantError("output_types fields must be non-empty strings")
        if not isinstance(artifact_type, ArtifactKind):
            raise StateInvariantError(f"output_types[{field_name}] must be an ArtifactKind")
        frozen[field_name] = artifact_type
    return MappingProxyType(frozen)


def _optional_digest(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    try:
        require_sha256(value, field_name)
    except DomainValidationError as exc:
        raise StateInvariantError(str(exc)) from exc
    return value


@dataclass(frozen=True)
class NodeSpec:
    """Static, local graph configuration; it never contains model output."""

    node_id: str
    node_version: str
    output_types: Mapping[str, ArtifactKind]
    input_fields: tuple[str, ...] = ()
    uses_knowledge_snapshot: bool = False
    uses_capability_profile: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise StateInvariantError("node_id must be non-empty")
        if not isinstance(self.node_version, str) or not self.node_version.strip():
            raise StateInvariantError("node_version must be non-empty")
        if not isinstance(self.uses_knowledge_snapshot, bool) or not isinstance(self.uses_capability_profile, bool):
            raise StateInvariantError("node profile flags must be booleans")
        outputs = _output_types(self.output_types)
        inputs = _texts(self.input_fields, "input_fields")
        if set(inputs) & set(outputs):
            raise StateInvariantError("a node cannot read and own the same field")
        object.__setattr__(self, "output_types", outputs)
        object.__setattr__(self, "input_fields", inputs)

    @property
    def owns_fields(self) -> tuple[str, ...]:
        return tuple(self.output_types)

    @property
    def stage_signature(self) -> str:
        """A locally-derived configuration signature, never model supplied."""
        return canonical_sha256(
            {
                "node_id": self.node_id,
                "node_version": self.node_version,
                "output_types": {field: kind.value for field, kind in self.output_types.items()},
                "input_fields": self.input_fields,
                "uses_knowledge_snapshot": self.uses_knowledge_snapshot,
                "uses_capability_profile": self.uses_capability_profile,
            }
        )

    def descriptor(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "node_version": self.node_version,
            "output_types": {field: kind.value for field, kind in self.output_types.items()},
            "input_fields": self.input_fields,
            "uses_knowledge_snapshot": self.uses_knowledge_snapshot,
            "uses_capability_profile": self.uses_capability_profile,
            "stage_signature": self.stage_signature,
        }


class StateGraph:
    """A field-owner DAG with explicit digest edges and no implicit routing."""

    def __init__(self, nodes: Sequence[NodeSpec]) -> None:
        values = tuple(nodes)
        if not values or not all(isinstance(item, NodeSpec) for item in values):
            raise StateInvariantError("StateGraph requires NodeSpec values")
        node_ids = tuple(node.node_id for node in values)
        if len(node_ids) != len(set(node_ids)):
            raise StateInvariantError("node_id must be unique")
        owners: dict[str, str] = {}
        output_types: dict[str, ArtifactKind] = {}
        for node in values:
            for field_name, artifact_type in node.output_types.items():
                if field_name in owners:
                    raise StateInvariantError(
                        f"field '{field_name}' has duplicate owners: {owners[field_name]}, {node.node_id}"
                    )
                owners[field_name] = node.node_id
                output_types[field_name] = artifact_type
        self._validate_acyclic(values, owners)
        self._nodes = values
        self._by_id = MappingProxyType({node.node_id: node for node in values})
        self._owners = MappingProxyType(owners)
        self._output_types = MappingProxyType(output_types)
        self._known_fields = frozenset(
            set(owners).union(
                field_name
                for node in values
                for field_name in node.input_fields
            )
        )

    @staticmethod
    def _validate_acyclic(nodes: Sequence[NodeSpec], owners: Mapping[str, str]) -> None:
        """Reject configuration cycles before they can become unrecoverable state.

        A node may consume an external input field, which has no graph owner.
        Only inputs owned by another node form dependency edges.  Validating
        those edges at construction time prevents a persisted run from naming
        a graph in which no first committed node can ever exist.
        """
        dependencies = {
            node.node_id: tuple(
                owners[field_name]
                for field_name in node.input_fields
                if field_name in owners
            )
            for node in nodes
        }
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str, path: tuple[str, ...]) -> None:
            if node_id in visited:
                return
            if node_id in visiting:
                cycle = " -> ".join((*path, node_id))
                raise StateInvariantError(f"StateGraph dependency cycle is not allowed: {cycle}")
            visiting.add(node_id)
            for dependency in dependencies[node_id]:
                visit(dependency, (*path, node_id))
            visiting.remove(node_id)
            visited.add(node_id)

        for node in nodes:
            visit(node.node_id, ())

    @property
    def nodes(self) -> tuple[NodeSpec, ...]:
        return self._nodes

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def descriptor(self) -> tuple[dict[str, object], ...]:
        return tuple(node.descriptor() for node in self._nodes)

    def node(self, node_id: str) -> NodeSpec:
        try:
            return self._by_id[node_id]
        except KeyError as exc:
            raise StateInvariantError(f"unknown node '{node_id}'") from exc

    def expected_artifact_type(self, field_name: str) -> ArtifactKind:
        try:
            return self._output_types[field_name]
        except KeyError as exc:
            raise StateInvariantError(f"unknown output field '{field_name}'") from exc

    def _validate_profile_context(
        self,
        node: NodeSpec,
        *,
        knowledge_snapshot_digest: str | None,
        capability_profile_digest: str | None,
    ) -> None:
        _optional_digest(knowledge_snapshot_digest, "knowledge_snapshot_digest")
        _optional_digest(capability_profile_digest, "capability_profile_digest")
        if node.uses_knowledge_snapshot != (knowledge_snapshot_digest is not None):
            raise StateInvariantError(
                f"node '{node.node_id}' knowledge snapshot presence does not match its declared contract"
            )
        if node.uses_capability_profile != (capability_profile_digest is not None):
            raise StateInvariantError(
                f"node '{node.node_id}' capability profile presence does not match its declared contract"
            )

    def validate_state(self, state: PersistentGraphState) -> None:
        if not isinstance(state, PersistentGraphState):
            raise StateInvariantError("state must be a PersistentGraphState")
        if state.event_sequence == 0:
            if state.outputs or state.accepted:
                raise StateInvariantError("an empty state cannot contain accepted values")
            return
        accepted_fields: set[str] = set()
        for node_id, acceptance in state.accepted.items():
            node = self.node(node_id)
            if acceptance.node_version != node.node_version:
                raise StateInvariantError(f"accepted node '{node_id}' has a different node version")
            if acceptance.stage_signature != node.stage_signature:
                raise StateInvariantError(f"accepted node '{node_id}' has a different stage signature")
            if acceptance.status != "committed":
                raise StateInvariantError(f"accepted node '{node_id}' is not committed")
            if set(acceptance.output_artifacts) != set(node.owns_fields):
                raise StateInvariantError(f"accepted node '{node_id}' output fields do not match its contract")
            if set(acceptance.input_digests) != set(node.input_fields):
                raise StateInvariantError(f"accepted node '{node_id}' input digests do not match its contract")
            owned_inputs = {field for field in node.input_fields if field in self._owners}
            if set(acceptance.input_artifacts) != owned_inputs:
                raise StateInvariantError(f"accepted node '{node_id}' input ArtifactRefs do not match graph ownership")
            self._validate_profile_context(
                node,
                knowledge_snapshot_digest=acceptance.knowledge_snapshot_digest,
                capability_profile_digest=acceptance.capability_profile_digest,
            )
            accepted_fields.update(node.owns_fields)
            for field_name in node.owns_fields:
                ref = acceptance.output_artifacts[field_name]
                if ref.artifact_type is not node.output_types[field_name]:
                    raise StateInvariantError(f"artifact type for '{field_name}' does not match node contract")
                if state.outputs.get(field_name) != ref:
                    raise StateInvariantError(f"accepted node '{node_id}' output is absent from state")
            for field_name in owned_inputs:
                ref = acceptance.input_artifacts[field_name]
                upstream = state.outputs.get(field_name)
                if upstream != ref or ref.artifact_digest != acceptance.input_digests[field_name]:
                    raise StateInvariantError(f"accepted node '{node_id}' input digest no longer matches its Artifact")
        if set(state.outputs) != accepted_fields:
            raise StateInvariantError("state outputs must be exactly the accepted node fields")
        for field_name, ref in state.outputs.items():
            if ref.artifact_type is not self.expected_artifact_type(field_name):
                raise StateInvariantError(f"artifact type for '{field_name}' does not match graph ownership")

    def apply(
        self,
        state: PersistentGraphState,
        *,
        node_id: str,
        outputs: Mapping[str, ArtifactRef],
        input_digests: Mapping[str, str],
        knowledge_snapshot_digest: str | None,
        capability_profile_digest: str | None,
        commit_id: str,
    ) -> PersistentGraphState:
        self.validate_state(state)
        node = self.node(node_id)
        if node_id in state.accepted:
            raise StateInvariantError(f"node '{node_id}' is already accepted")
        if not isinstance(outputs, Mapping) or set(outputs) != set(node.owns_fields):
            raise StateInvariantError(f"node '{node_id}' owns exactly {node.owns_fields}")
        if not isinstance(input_digests, Mapping) or set(input_digests) != set(node.input_fields):
            raise StateInvariantError(f"node '{node_id}' input digests must match its input fields")
        if not isinstance(commit_id, str) or not commit_id.strip():
            raise StateInvariantError("commit_id must be non-empty")
        self._validate_profile_context(
            node,
            knowledge_snapshot_digest=knowledge_snapshot_digest,
            capability_profile_digest=capability_profile_digest,
        )

        output_refs: dict[str, ArtifactRef] = {}
        for field_name in node.owns_fields:
            ref = outputs[field_name]
            if not isinstance(ref, ArtifactRef):
                raise StateInvariantError("node outputs must be ArtifactRef values")
            if ref.artifact_type is not node.output_types[field_name]:
                raise StateInvariantError(f"artifact type for '{field_name}' does not match node contract")
            if field_name in state.outputs:
                raise StateInvariantError(f"owned field '{field_name}' already has an accepted value")
            output_refs[field_name] = ref

        input_artifacts: dict[str, ArtifactRef] = {}
        for field_name, digest in input_digests.items():
            _optional_digest(digest, f"input_digests[{field_name}]")
            if field_name in self._owners:
                upstream = state.outputs.get(field_name)
                if upstream is None or upstream.artifact_digest != digest:
                    raise StateInvariantError(
                        f"node '{node_id}' cannot accept an unbound or stale upstream input '{field_name}'"
                    )
                input_artifacts[field_name] = upstream

        next_outputs = dict(state.outputs)
        next_outputs.update(output_refs)
        next_accepted = dict(state.accepted)
        next_accepted[node_id] = NodeAcceptance(
            node_id=node_id,
            node_version=node.node_version,
            stage_signature=node.stage_signature,
            input_digests=input_digests,
            input_artifacts=input_artifacts,
            output_artifacts=output_refs,
            knowledge_snapshot_digest=knowledge_snapshot_digest,
            capability_profile_digest=capability_profile_digest,
            commit_id=commit_id,
        )
        next_state = PersistentGraphState(
            run_id=state.run_id,
            outputs=next_outputs,
            accepted=next_accepted,
            event_sequence=state.event_sequence + 1,
            current_commit_id=commit_id,
        )
        self.validate_state(next_state)
        return next_state

    def runnable_node_ids(self, state: PersistentGraphState) -> tuple[str, ...]:
        self.validate_state(state)
        return tuple(
            node.node_id
            for node in self._nodes
            if node.node_id not in state.accepted
            and all(field not in self._owners or field in state.outputs for field in node.input_fields)
        )

    def invalidation_closure(self, changed_fields: Sequence[str]) -> tuple[str, ...]:
        """Return a deterministic, transitive closure from changed fields.

        An owned field means its producer is stale too; an external field only
        invalidates its consumers.  That distinction prevents a source/fact
        mutation from being mistaken for an already-accepted artifact.
        """
        seeds = _texts(changed_fields, "changed_fields", required=True)
        unknown = tuple(field_name for field_name in seeds if field_name not in self._known_fields)
        if unknown:
            raise StateInvariantError(
                "changed fields are not declared in StateGraph: "
                + ", ".join(unknown)
            )
        affected: list[str] = []
        pending_fields = list(seeds)
        cursor = 0
        while cursor < len(pending_fields):
            field_name = pending_fields[cursor]
            cursor += 1
            candidates: list[str] = []
            if field_name in self._owners:
                candidates.append(self._owners[field_name])
            candidates.extend(node.node_id for node in self._nodes if field_name in node.input_fields)
            for node_id in candidates:
                if node_id in affected:
                    continue
                affected.append(node_id)
                pending_fields.extend(self.node(node_id).owns_fields)
        return tuple(affected)

    def invalidate(
        self,
        state: PersistentGraphState,
        *,
        changed_fields: Sequence[str],
        commit_id: str,
    ) -> tuple[PersistentGraphState, tuple[str, ...], tuple[str, ...]]:
        self.validate_state(state)
        if not isinstance(commit_id, str) or not commit_id.strip():
            raise StateInvariantError("commit_id must be non-empty")
        closure = self.invalidation_closure(changed_fields)
        return self.invalidate_node_ids(state, node_ids=closure, commit_id=commit_id)

    def invalidate_node_ids(
        self,
        state: PersistentGraphState,
        *,
        node_ids: Sequence[str],
        commit_id: str,
    ) -> tuple[PersistentGraphState, tuple[str, ...], tuple[str, ...]]:
        """Commit a precomputed closure without inventing a changed field."""
        self.validate_state(state)
        if not isinstance(commit_id, str) or not commit_id.strip():
            raise StateInvariantError("commit_id must be non-empty")
        node_ids = tuple(node_id for node_id in node_ids if node_id in state.accepted)
        if not node_ids:
            return state, (), ()
        next_outputs = dict(state.outputs)
        next_accepted = dict(state.accepted)
        invalidated_digests: list[str] = []
        for node_id in node_ids:
            acceptance = next_accepted.pop(node_id)
            for field_name, ref in acceptance.output_artifacts.items():
                invalidated_digests.append(ref.artifact_digest)
                next_outputs.pop(field_name, None)
        next_state = PersistentGraphState(
            run_id=state.run_id,
            outputs=next_outputs,
            accepted=next_accepted,
            event_sequence=state.event_sequence + 1,
            current_commit_id=commit_id,
        )
        self.validate_state(next_state)
        return next_state, node_ids, tuple(invalidated_digests)
