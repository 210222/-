"""Deterministic ownership and replay rules for the v3.1 state graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Sequence

from mode_p_vnext.domain.artifact import (
    ArtifactKind,
    DomainValidationError,
    ValidationStatus,
    canonical_sha256,
    require_sha256,
)

from .state import (
    ACTIVE_LIFECYCLE_STATUS,
    ArtifactRef,
    NodeAcceptance,
    PersistentGraphState,
    RetainedArtifact,
    StateInvariantError,
    candidate_digest_for,
)


V31_CANONICAL_NODE_ORDER = (
    "I0", "E0", "S1", "K1", "B0", "K2", "B1", "VEC", "Projection", "G0", "DP",
)
V31_NODE_VERSION = "v3.1"


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


def _optional_output_types(value: Mapping[str, ArtifactKind]) -> Mapping[str, ArtifactKind]:
    if not isinstance(value, Mapping):
        raise StateInvariantError("optional_output_types must be a mapping")
    frozen: dict[str, ArtifactKind] = {}
    for field_name, artifact_type in value.items():
        if not isinstance(field_name, str) or not field_name.strip():
            raise StateInvariantError("optional_output_types fields must be non-empty strings")
        if not isinstance(artifact_type, ArtifactKind):
            raise StateInvariantError(
                f"optional_output_types[{field_name}] must be an ArtifactKind"
            )
        frozen[field_name] = artifact_type
    return MappingProxyType(frozen)


def _output_input_dependencies(
    value: Mapping[str, Sequence[str]],
    *,
    output_fields: Sequence[str],
    input_fields: Sequence[str],
) -> Mapping[str, tuple[str, ...]]:
    """Freeze per-output input ownership for field-level invalidation.

    Omitting this optional static declaration is deliberately conservative:
    every output depends on every declared input.  A node that wants a more
    precise invalidation boundary must declare all of its output dependencies
    explicitly, so a missing field can never silently become independent.
    """

    if not isinstance(value, Mapping):
        raise StateInvariantError("output_input_dependencies must be a mapping")
    fields = tuple(output_fields)
    inputs = tuple(input_fields)
    if not value:
        return MappingProxyType({field_name: inputs for field_name in fields})
    if set(value) != set(fields):
        raise StateInvariantError(
            "output_input_dependencies must declare every required and optional output"
        )
    frozen: dict[str, tuple[str, ...]] = {}
    for field_name, dependencies in value.items():
        if not isinstance(field_name, str) or field_name not in fields:
            raise StateInvariantError("output dependency field is not owned by the node")
        if isinstance(dependencies, (str, bytes)) or not isinstance(dependencies, Sequence):
            raise StateInvariantError("output dependencies must be a sequence of input fields")
        dependency_fields = _texts(
            tuple(dependencies), f"output dependencies for '{field_name}'"
        )
        if not set(dependency_fields).issubset(inputs):
            raise StateInvariantError(
                f"output dependencies for '{field_name}' are not declared node inputs"
            )
        frozen[field_name] = dependency_fields
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
    optional_output_types: Mapping[str, ArtifactKind] = field(default_factory=dict)
    output_input_dependencies: Mapping[str, Sequence[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise StateInvariantError("node_id must be non-empty")
        if not isinstance(self.node_version, str) or not self.node_version.strip():
            raise StateInvariantError("node_version must be non-empty")
        if not isinstance(self.uses_knowledge_snapshot, bool) or not isinstance(self.uses_capability_profile, bool):
            raise StateInvariantError("node profile flags must be booleans")
        outputs = _output_types(self.output_types)
        optional_outputs = _optional_output_types(self.optional_output_types)
        if set(outputs) & set(optional_outputs):
            raise StateInvariantError("required and optional output fields must not overlap")
        inputs = _texts(self.input_fields, "input_fields")
        if set(inputs) & (set(outputs) | set(optional_outputs)):
            raise StateInvariantError("a node cannot read and own the same field")
        dependencies = _output_input_dependencies(
            self.output_input_dependencies,
            output_fields=(*outputs, *optional_outputs),
            input_fields=inputs,
        )
        object.__setattr__(self, "output_types", outputs)
        object.__setattr__(self, "optional_output_types", optional_outputs)
        object.__setattr__(self, "input_fields", inputs)
        object.__setattr__(self, "output_input_dependencies", dependencies)

    @property
    def owns_fields(self) -> tuple[str, ...]:
        return (*self.output_types, *self.optional_output_types)

    @property
    def required_output_fields(self) -> tuple[str, ...]:
        return tuple(self.output_types)

    @property
    def all_output_types(self) -> Mapping[str, ArtifactKind]:
        return MappingProxyType({**self.output_types, **self.optional_output_types})

    def artifact_type_for(self, field_name: str) -> ArtifactKind:
        try:
            return self.output_types[field_name]
        except KeyError:
            try:
                return self.optional_output_types[field_name]
            except KeyError as exc:
                raise StateInvariantError(
                    f"field '{field_name}' is not owned by node '{self.node_id}'"
                ) from exc

    def input_dependencies_for_output(self, field_name: str) -> tuple[str, ...]:
        try:
            return self.output_input_dependencies[field_name]
        except KeyError as exc:
            raise StateInvariantError(
                f"field '{field_name}' is not owned by node '{self.node_id}'"
            ) from exc

    @property
    def stage_signature(self) -> str:
        """A locally-derived configuration signature, never model supplied."""
        return canonical_sha256(
            {
                "node_id": self.node_id,
                "node_version": self.node_version,
                "output_types": {field: kind.value for field, kind in self.output_types.items()},
                "optional_output_types": {
                    field: kind.value for field, kind in self.optional_output_types.items()
                },
                "output_input_dependencies": {
                    field: dependencies
                    for field, dependencies in self.output_input_dependencies.items()
                },
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
            "optional_output_types": {
                field: kind.value for field, kind in self.optional_output_types.items()
            },
            "output_input_dependencies": {
                field: dependencies
                for field, dependencies in self.output_input_dependencies.items()
            },
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
            for field_name, artifact_type in node.all_output_types.items():
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
        if state.graph_digest != self.digest:
            raise StateInvariantError("persistent state is bound to a different graph digest")
        if state.event_sequence == 0:
            if state.outputs or state.accepted or state.candidate_revision != 0:
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
            if acceptance.lifecycle_status != ACTIVE_LIFECYCLE_STATUS:
                raise StateInvariantError(f"accepted node '{node_id}' is not active")
            if acceptance.candidate_revision > state.candidate_revision:
                raise StateInvariantError(
                    f"accepted node '{node_id}' belongs to a future candidate revision"
                )
            output_fields = set(acceptance.output_artifacts)
            if not set(node.required_output_fields).issubset(output_fields) or not output_fields.issubset(node.owns_fields):
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
            accepted_fields.update(acceptance.output_artifacts)
            for field_name in acceptance.output_artifacts:
                ref = acceptance.output_artifacts[field_name]
                if ref.artifact_type is not node.artifact_type_for(field_name):
                    raise StateInvariantError(f"artifact type for '{field_name}' does not match node contract")
                if state.outputs.get(field_name) != ref:
                    raise StateInvariantError(f"accepted node '{node_id}' output is absent from state")
            for field_name in owned_inputs:
                ref = acceptance.input_artifacts[field_name]
                upstream = state.outputs.get(field_name)
                if upstream != ref or ref.artifact_digest != acceptance.input_digests[field_name]:
                    raise StateInvariantError(f"accepted node '{node_id}' input digest no longer matches its Artifact")
        retained_fields: set[str] = set()
        for field_name, retained in state.retained_outputs.items():
            node = self.node(retained.node_id)
            if retained.source_candidate_revision >= state.candidate_revision:
                raise StateInvariantError(
                    f"retained output '{field_name}' is not bound to an earlier candidate"
                )
            if retained.node_id in state.accepted:
                raise StateInvariantError(
                    f"retained output '{field_name}' overlaps an active node acceptance"
                )
            if field_name not in node.owns_fields:
                raise StateInvariantError(
                    f"retained output '{field_name}' is not owned by '{retained.node_id}'"
                )
            if retained.artifact_ref.artifact_type is not node.artifact_type_for(field_name):
                raise StateInvariantError(
                    f"retained output '{field_name}' has a different artifact type"
                )
            if state.outputs.get(field_name) != retained.artifact_ref:
                raise StateInvariantError(
                    f"retained output '{field_name}' is absent from the state outputs"
                )
            retained_fields.add(field_name)
        if accepted_fields & retained_fields:
            raise StateInvariantError("accepted and retained outputs must not overlap")
        if set(state.outputs) != accepted_fields | retained_fields:
            raise StateInvariantError(
                "state outputs must be exactly the active or retained node fields"
            )
        for field_name, ref in state.outputs.items():
            if ref.artifact_type is not self.expected_artifact_type(field_name):
                raise StateInvariantError(f"artifact type for '{field_name}' does not match graph ownership")
        artifact_ids = tuple(ref.artifact_id for ref in state.outputs.values())
        artifact_digests = tuple(ref.artifact_digest for ref in state.outputs.values())
        if len(artifact_ids) != len(set(artifact_ids)):
            raise StateInvariantError("live graph fields cannot alias one artifact_id")
        if len(artifact_digests) != len(set(artifact_digests)):
            raise StateInvariantError("live graph fields cannot alias one artifact_digest")
        if state.candidate_validation_status is ValidationStatus.TEXT_VALIDATED:
            if state.retained_outputs:
                raise StateInvariantError(
                    "TEXT_VALIDATED cannot retain a partial node for atomic rebuild"
                )
            dp = state.accepted.get("DP")
            if (
                dp is None
                or "dp_conclusion" not in dp.output_artifacts
                or "revision_request" in dp.output_artifacts
            ):
                raise StateInvariantError(
                    "TEXT_VALIDATED requires an active DP READY conclusion without a revision request"
                )

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
        candidate_revision: int | None = None,
        candidate_digest: str | None = None,
        candidate_validation_status: ValidationStatus | None = None,
    ) -> PersistentGraphState:
        self.validate_state(state)
        if candidate_revision is not None:
            if isinstance(candidate_revision, bool) or not isinstance(candidate_revision, int):
                raise StateInvariantError("candidate_revision must be a non-negative integer")
            if candidate_revision != state.candidate_revision:
                raise StateInvariantError("stale candidate revision does not match the active state")
        if candidate_digest is not None:
            _optional_digest(candidate_digest, "candidate_digest")
            if candidate_digest != state.candidate_digest:
                raise StateInvariantError("stale candidate digest does not match the active state")
        node = self.node(node_id)
        next_validation_status = (
            state.candidate_validation_status
            if candidate_validation_status is None
            else candidate_validation_status
        )
        if type(next_validation_status) is not ValidationStatus:
            raise StateInvariantError("candidate_validation_status must be a canonical ValidationStatus")
        if next_validation_status != state.candidate_validation_status:
            if (
                node_id != "DP"
                or state.candidate_validation_status is not ValidationStatus.DRAFT
                or next_validation_status is not ValidationStatus.TEXT_VALIDATED
            ):
                raise StateInvariantError(
                    "only a DP READY transition may advance candidate_validation_status"
                )
        if node_id in state.accepted:
            raise StateInvariantError(f"node '{node_id}' is already accepted")
        retained_for_node = {
            field_name: retained
            for field_name, retained in state.retained_outputs.items()
            if retained.node_id == node_id
        }
        if (
            not isinstance(outputs, Mapping)
            or not set(node.required_output_fields).issubset(outputs)
            or not set(outputs).issubset(node.owns_fields)
        ):
            raise StateInvariantError(
                f"node '{node_id}' requires {node.required_output_fields} and may own {node.owns_fields}"
            )
        if not set(retained_for_node).issubset(outputs):
            raise StateInvariantError(
                f"node '{node_id}' must re-present every retained output during its atomic rebuild"
            )
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
        live_artifact_ids = {
            ref.artifact_id
            for field_name, ref in state.outputs.items()
            if field_name not in retained_for_node
        }
        live_artifact_digests = {
            ref.artifact_digest
            for field_name, ref in state.outputs.items()
            if field_name not in retained_for_node
        }
        for field_name in node.owns_fields:
            if field_name not in outputs:
                continue
            ref = outputs[field_name]
            if not isinstance(ref, ArtifactRef):
                raise StateInvariantError("node outputs must be ArtifactRef values")
            if ref.artifact_type is not node.artifact_type_for(field_name):
                raise StateInvariantError(f"artifact type for '{field_name}' does not match node contract")
            if field_name in state.outputs:
                retained = retained_for_node.get(field_name)
                if retained is None:
                    raise StateInvariantError(
                        f"owned field '{field_name}' already has an accepted value"
                    )
                if ref != retained.artifact_ref:
                    raise StateInvariantError(
                        f"node '{node_id}' cannot rewrite retained output '{field_name}' during a partial rebuild"
                    )
            if ref.artifact_id in live_artifact_ids:
                raise StateInvariantError("node outputs cannot alias a live artifact_id")
            if ref.artifact_digest in live_artifact_digests:
                raise StateInvariantError("node outputs cannot alias a live artifact_digest")
            output_refs[field_name] = ref
            live_artifact_ids.add(ref.artifact_id)
            live_artifact_digests.add(ref.artifact_digest)
        if (
            next_validation_status is ValidationStatus.TEXT_VALIDATED
            and "revision_request" in output_refs
        ):
            raise StateInvariantError(
                "a DP revision request cannot advance the candidate to TEXT_VALIDATED"
            )

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
            candidate_revision=state.candidate_revision,
            input_candidate_digest=state.candidate_digest,
            commit_id=commit_id,
        )
        next_retained = {
            field_name: retained
            for field_name, retained in state.retained_outputs.items()
            if retained.node_id != node_id
        }
        next_state = PersistentGraphState(
            run_id=state.run_id,
            graph_digest=state.graph_digest,
            outputs=next_outputs,
            accepted=next_accepted,
            candidate_revision=state.candidate_revision,
            candidate_digest=candidate_digest_for(
                run_id=state.run_id,
                graph_digest=state.graph_digest,
                candidate_revision=state.candidate_revision,
                outputs=next_outputs,
            ),
            candidate_validation_status=next_validation_status,
            event_sequence=state.event_sequence + 1,
            current_commit_id=commit_id,
            retained_outputs=next_retained,
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
        seeds = _texts(changed_fields, "changed_fields", required=True)
        closure = self.invalidation_closure(seeds)
        closure_set = set(closure)
        invalidated_fields_by_node: dict[str, tuple[str, ...]] = {}
        for node_id in closure:
            node = self.node(node_id)
            # A changed output means its producer is no longer authoritative;
            # it is never safe to retain an arbitrary subset of that producer.
            producer_output_changed = bool(set(node.owns_fields) & set(seeds))
            changed_inputs = {
                field_name
                for field_name in node.input_fields
                if field_name in seeds or self._owners.get(field_name) in closure_set
            }
            if producer_output_changed:
                stale_fields = node.owns_fields
            else:
                stale_fields = tuple(
                    field_name
                    for field_name in node.owns_fields
                    if set(node.input_dependencies_for_output(field_name)) & changed_inputs
                )
                # A closure node without a declared causal output is unsafe to
                # partially retain.  Default to a complete rebuild instead.
                if not stale_fields:
                    stale_fields = node.owns_fields
            invalidated_fields_by_node[node_id] = stale_fields
        return self.invalidate_node_ids(
            state,
            node_ids=closure,
            commit_id=commit_id,
            invalidated_fields_by_node=invalidated_fields_by_node,
        )

    def invalidate_node_ids(
        self,
        state: PersistentGraphState,
        *,
        node_ids: Sequence[str],
        commit_id: str,
        invalidated_fields_by_node: Mapping[str, Sequence[str]] | None = None,
    ) -> tuple[PersistentGraphState, tuple[str, ...], tuple[str, ...]]:
        """Commit a precomputed closure without inventing a changed field.

        ``invalidated_fields_by_node`` is used only for a deterministic
        field-level closure.  Absent that map (capability/knowledge churn), a
        node is conservatively invalidated as a whole.
        """
        self.validate_state(state)
        if not isinstance(commit_id, str) or not commit_id.strip():
            raise StateInvariantError("commit_id must be non-empty")
        requested_node_ids = _texts(node_ids, "node_ids")
        for node_id in requested_node_ids:
            self.node(node_id)
        requested_fields: dict[str, tuple[str, ...]] = {}
        if invalidated_fields_by_node is not None:
            if not isinstance(invalidated_fields_by_node, Mapping):
                raise StateInvariantError("invalidated_fields_by_node must be a mapping")
            if not set(invalidated_fields_by_node).issubset(requested_node_ids):
                raise StateInvariantError(
                    "invalidated field declarations must name a requested node"
                )
            for node_id, fields in invalidated_fields_by_node.items():
                node = self.node(node_id)
                if isinstance(fields, (str, bytes)) or not isinstance(fields, Sequence):
                    raise StateInvariantError("invalidated node fields must be a sequence")
                values = _texts(tuple(fields), f"invalidated fields for '{node_id}'", required=True)
                if not set(values).issubset(node.owns_fields):
                    raise StateInvariantError(
                        f"invalidated fields for '{node_id}' are not node outputs"
                    )
                requested_fields[node_id] = values
        retained_node_ids = {
            retained.node_id for retained in state.retained_outputs.values()
        }
        node_ids = tuple(
            node_id
            for node_id in requested_node_ids
            if node_id in state.accepted or node_id in retained_node_ids
        )
        if not node_ids:
            return state, (), ()
        next_outputs = dict(state.outputs)
        next_accepted = dict(state.accepted)
        next_retained = dict(state.retained_outputs)
        invalidated_digests: list[str] = []
        for node_id in node_ids:
            node = self.node(node_id)
            acceptance = next_accepted.pop(node_id, None)
            live_fields: dict[str, ArtifactRef] = {}
            if acceptance is not None:
                live_fields.update(acceptance.output_artifacts)
            for field_name, retained in tuple(next_retained.items()):
                if retained.node_id == node_id:
                    if field_name in live_fields:
                        raise StateInvariantError(
                            f"node '{node_id}' has overlapping active and retained outputs"
                        )
                    live_fields[field_name] = retained.artifact_ref
            stale_fields = set(requested_fields.get(node_id, node.owns_fields))
            for field_name, ref in live_fields.items():
                if field_name in stale_fields:
                    invalidated_digests.append(ref.artifact_digest)
                    next_outputs.pop(field_name, None)
                    next_retained.pop(field_name, None)
                elif acceptance is not None:
                    next_retained[field_name] = RetainedArtifact(
                        field_name=field_name,
                        node_id=node_id,
                        artifact_ref=ref,
                        source_candidate_revision=state.candidate_revision,
                        source_candidate_digest=state.candidate_digest,
                    )
        next_state = PersistentGraphState(
            run_id=state.run_id,
            graph_digest=state.graph_digest,
            outputs=next_outputs,
            accepted=next_accepted,
            candidate_revision=state.candidate_revision + 1,
            candidate_digest=candidate_digest_for(
                run_id=state.run_id,
                graph_digest=state.graph_digest,
                candidate_revision=state.candidate_revision + 1,
                outputs=next_outputs,
            ),
            candidate_validation_status=ValidationStatus.DRAFT,
            event_sequence=state.event_sequence + 1,
            current_commit_id=commit_id,
            retained_outputs=next_retained,
        )
        self.validate_state(next_state)
        return next_state, node_ids, tuple(invalidated_digests)


def canonical_v31_state_graph() -> StateGraph:
    """Return the only v3.1 execution graph topology.

    This is deliberately a local static configuration, not a model-produced
    route.  A later work package may orchestrate these nodes, but it must not
    replace their ownership, ordering, or the atomic Projection bundle shape.
    """

    return StateGraph(
        (
            NodeSpec(
                "I0",
                V31_NODE_VERSION,
                {
                    "normalized_source": ArtifactKind.NORMALIZED_SOURCE,
                    "fact_registry": ArtifactKind.FACT_REGISTRY,
                },
                ("raw_source",),
            ),
            NodeSpec(
                "E0",
                V31_NODE_VERSION,
                {"episode_direction": ArtifactKind.EPISODE_DIRECTION_DRAFT},
                ("fact_registry",),
            ),
            NodeSpec(
                "S1",
                V31_NODE_VERSION,
                {"scene_intent": ArtifactKind.SCENE_INTENT_DRAFT},
                ("fact_registry", "episode_direction"),
            ),
            NodeSpec(
                "K1",
                V31_NODE_VERSION,
                {"k1_snapshot": ArtifactKind.KNOWLEDGE_SNAPSHOT},
                ("episode_direction", "scene_intent"),
            ),
            NodeSpec(
                "B0",
                V31_NODE_VERSION,
                {
                    "blocking_draft": ArtifactKind.BLOCKING_DRAFT,
                    "blocking_commit": ArtifactKind.BLOCKING_COMMIT,
                },
                ("scene_intent", "k1_snapshot"),
                uses_knowledge_snapshot=True,
            ),
            NodeSpec(
                "K2",
                V31_NODE_VERSION,
                {"k2_snapshot": ArtifactKind.KNOWLEDGE_SNAPSHOT},
                ("scene_intent", "blocking_commit"),
            ),
            NodeSpec(
                "B1",
                V31_NODE_VERSION,
                {"execution_design": ArtifactKind.EXECUTION_DESIGN_DRAFT},
                ("fact_registry", "scene_intent", "blocking_commit", "k2_snapshot"),
                uses_knowledge_snapshot=True,
                uses_capability_profile=True,
            ),
            NodeSpec(
                "VEC",
                V31_NODE_VERSION,
                {"vec": ArtifactKind.VISUAL_EXECUTION_CONTRACT},
                ("fact_registry", "blocking_commit", "execution_design"),
                uses_capability_profile=True,
            ),
            NodeSpec(
                "Projection",
                V31_NODE_VERSION,
                {
                    "projection_ast": ArtifactKind.PROJECTION_AST,
                    "storyboard_manifest": ArtifactKind.PROJECTION_MANIFEST,
                    "video_manifest": ArtifactKind.PROJECTION_MANIFEST,
                    "storyboard_adaptation": ArtifactKind.CAPABILITY_ADAPTATION,
                    "video_adaptation": ArtifactKind.CAPABILITY_ADAPTATION,
                },
                (
                    "vec",
                    "storyboard_adapter_signature",
                    "video_adapter_signature",
                ),
                uses_capability_profile=True,
                output_input_dependencies={
                    "projection_ast": ("vec",),
                    "storyboard_manifest": ("vec", "storyboard_adapter_signature"),
                    "video_manifest": ("vec", "video_adapter_signature"),
                    "storyboard_adaptation": ("vec", "storyboard_adapter_signature"),
                    "video_adaptation": ("vec", "video_adapter_signature"),
                },
            ),
            NodeSpec(
                "G0",
                V31_NODE_VERSION,
                {"gate0_receipt": ArtifactKind.GATE0_RESULT},
                (
                    "vec",
                    "projection_ast",
                    "storyboard_manifest",
                    "video_manifest",
                    "storyboard_adaptation",
                    "video_adaptation",
                    "gate_policy_signature",
                ),
                uses_capability_profile=True,
            ),
            NodeSpec(
                "DP",
                V31_NODE_VERSION,
                {
                    "review_packet": ArtifactKind.REVIEW_PACKET,
                    "dp_conclusion": ArtifactKind.DP_REVIEW_RESULT,
                },
                (
                    "fact_registry",
                    "episode_direction",
                    "scene_intent",
                    "vec",
                    "projection_ast",
                    "storyboard_manifest",
                    "video_manifest",
                    "gate0_receipt",
                    "dp_rule_signature",
                    "dp_prompt_signature",
                ),
                optional_output_types={
                    "revision_request": ArtifactKind.REVISION_REQUEST,
                },
                uses_capability_profile=True,
            ),
        )
    )
