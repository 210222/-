"""Runtime-ledger values for the v3.1 persistent state graph.

These records are deliberately *not* another business-domain model.  They
contain only immutable references to canonical ``mode_p_vnext.domain``
Artifacts plus the operational evidence needed to replay a transaction.  The
payloads themselves never enter the runtime ledger.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from mode_p_vnext.domain.artifact import (
    DOMAIN_SCHEMA_VERSION,
    ArtifactKind,
    DomainValidationError,
    ValidationStatus,
    canonical_sha256,
    require_sha256,
)


# This is the runtime storage layout version, not an architecture authority
# version.  v3.1 remains the sole frozen architecture package; 3.1.1 fails
# closed rather than attempting to read pre-retained-field snapshots as if
# they carried the adapter-only invalidation proof introduced below.
PERSISTENCE_SCHEMA_VERSION = "3.1.1"
PERSISTENT_STATE_SCHEMA_NAME = "mode_p_vnext_runtime_state_graph"
COMMITTED_NODE_STATUS = "committed"
ACTIVE_LIFECYCLE_STATUS = "active"
SUPERSEDED_LIFECYCLE_STATUS = "superseded"
RETAINED_LIFECYCLE_STATUS = "retained_for_atomic_rebuild"


class StateInvariantError(ValueError):
    """Raised when an operational graph ledger violates v3.1 invariants."""


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StateInvariantError(f"{field_name} must be a non-empty string")
    return value


def _digest(value: object, field_name: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    try:
        require_sha256(value, field_name)  # type: ignore[arg-type]
    except DomainValidationError as exc:
        raise StateInvariantError(str(exc)) from exc
    return value  # type: ignore[return-value]


def _non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StateInvariantError(f"{field_name} must be a non-negative integer")
    return value


def _freeze_digests(value: Mapping[str, str], field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise StateInvariantError(f"{field_name} must be a mapping")
    frozen: dict[str, str] = {}
    for key, digest in value.items():
        frozen[_text(key, f"{field_name} key")] = _digest(
            digest, f"{field_name}[{key}]"
        )  # type: ignore[assignment]
    return MappingProxyType(frozen)


@dataclass(frozen=True)
class ArtifactRef:
    """A reference to an immutable canonical ArtifactEnvelope.

    ``artifact_digest`` addresses the complete canonical envelope, whereas
    ``canonical_payload_sha256`` is the domain-owned payload digest.  Keeping
    both prevents a runtime cache from silently losing lineage metadata.
    """

    artifact_id: str
    artifact_type: ArtifactKind
    schema_version: str
    canonical_payload_sha256: str
    artifact_digest: str

    def __post_init__(self) -> None:
        _text(self.artifact_id, "artifact_id")
        if not isinstance(self.artifact_type, ArtifactKind):
            raise StateInvariantError("artifact_type must be an ArtifactKind")
        if self.schema_version != DOMAIN_SCHEMA_VERSION:
            raise StateInvariantError(
                f"schema_version must match canonical domain schema {DOMAIN_SCHEMA_VERSION}"
            )
        _digest(self.canonical_payload_sha256, "canonical_payload_sha256")
        _digest(self.artifact_digest, "artifact_digest")

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "schema_version": self.schema_version,
            "canonical_payload_sha256": self.canonical_payload_sha256,
            "artifact_digest": self.artifact_digest,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ArtifactRef":
        if not isinstance(value, Mapping) or set(value) != {
            "artifact_id",
            "artifact_type",
            "schema_version",
            "canonical_payload_sha256",
            "artifact_digest",
        }:
            raise StateInvariantError("ArtifactRef fields do not match the v3.1 schema")
        try:
            return cls(
                artifact_id=value["artifact_id"],
                artifact_type=ArtifactKind(value["artifact_type"]),
                schema_version=value["schema_version"],
                canonical_payload_sha256=value["canonical_payload_sha256"],
                artifact_digest=value["artifact_digest"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise StateInvariantError("invalid ArtifactRef") from exc


@dataclass(frozen=True)
class RetainedArtifact:
    """An immutable unaffected field retained while its atomic node rebuilds.

    A v3.1 Projection node records the whole bundle atomically, while an
    adapter-only input may invalidate just one delivery view.  The retained
    record preserves the unaffected content-addressed references and the
    candidate tuple that produced them.  A later replacement must present
    those exact references again; it cannot silently rewrite the AST or the
    other delivery view under an adapter-only invalidation.
    """

    field_name: str
    node_id: str
    artifact_ref: ArtifactRef
    source_candidate_revision: int
    source_candidate_digest: str
    lifecycle_status: str = RETAINED_LIFECYCLE_STATUS

    def __post_init__(self) -> None:
        _text(self.field_name, "retained field_name")
        _text(self.node_id, "retained node_id")
        if not isinstance(self.artifact_ref, ArtifactRef):
            raise StateInvariantError("retained artifact_ref must be an ArtifactRef")
        _non_negative_int(self.source_candidate_revision, "retained source_candidate_revision")
        _digest(self.source_candidate_digest, "retained source_candidate_digest")
        if self.lifecycle_status != RETAINED_LIFECYCLE_STATUS:
            raise StateInvariantError("retained artifact lifecycle_status is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "node_id": self.node_id,
            "artifact_ref": self.artifact_ref.to_dict(),
            "source_candidate_revision": self.source_candidate_revision,
            "source_candidate_digest": self.source_candidate_digest,
            "lifecycle_status": self.lifecycle_status,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RetainedArtifact":
        expected = {
            "field_name", "node_id", "artifact_ref", "source_candidate_revision",
            "source_candidate_digest", "lifecycle_status",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise StateInvariantError("RetainedArtifact fields do not match the v3.1.1 schema")
        try:
            return cls(
                field_name=value["field_name"],
                node_id=value["node_id"],
                artifact_ref=ArtifactRef.from_dict(value["artifact_ref"]),
                source_candidate_revision=value["source_candidate_revision"],
                source_candidate_digest=value["source_candidate_digest"],
                lifecycle_status=value["lifecycle_status"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise StateInvariantError("invalid RetainedArtifact") from exc


def _freeze_refs(value: Mapping[str, ArtifactRef], field_name: str) -> Mapping[str, ArtifactRef]:
    if not isinstance(value, Mapping):
        raise StateInvariantError(f"{field_name} must be a mapping")
    frozen: dict[str, ArtifactRef] = {}
    for key, ref in value.items():
        text = _text(key, f"{field_name} key")
        if not isinstance(ref, ArtifactRef):
            raise StateInvariantError(f"{field_name} must contain ArtifactRef values")
        frozen[text] = ref
    return MappingProxyType(frozen)


def candidate_digest_for(
    *,
    run_id: str,
    graph_digest: str,
    candidate_revision: int,
    outputs: Mapping[str, ArtifactRef],
) -> str:
    """Bind a candidate revision to its complete immutable output tuple.

    This digest is intentionally separate from the transaction state digest.
    A producer can therefore bind its read-only work to both the exact
    candidate revision and all currently accepted artifact references before a
    later write compares that tuple under the episode/scene lock.
    """

    _text(run_id, "run_id")
    _digest(graph_digest, "graph_digest")
    _non_negative_int(candidate_revision, "candidate_revision")
    frozen_outputs = _freeze_refs(outputs, "candidate outputs")
    return canonical_sha256(
        {
            "run_id": run_id,
            "graph_digest": graph_digest,
            "candidate_revision": candidate_revision,
            "outputs": {
                field_name: ref.to_dict()
                for field_name, ref in frozen_outputs.items()
            },
        }
    )


@dataclass(frozen=True)
class NodeAcceptance:
    """Committed operational evidence for one graph node.

    It records every graph input/output artifact reference, stage signature,
    selected knowledge snapshot, and capability profile.  No model payload or
    mutable process object is retained here.
    """

    node_id: str
    node_version: str
    stage_signature: str
    input_digests: Mapping[str, str]
    input_artifacts: Mapping[str, ArtifactRef]
    output_artifacts: Mapping[str, ArtifactRef]
    knowledge_snapshot_digest: str | None
    capability_profile_digest: str | None
    candidate_revision: int
    input_candidate_digest: str
    commit_id: str
    lifecycle_status: str = ACTIVE_LIFECYCLE_STATUS
    status: str = COMMITTED_NODE_STATUS

    def __post_init__(self) -> None:
        _text(self.node_id, "node_id")
        _text(self.node_version, "node_version")
        _digest(self.stage_signature, "stage_signature")
        _text(self.commit_id, "commit_id")
        if self.status != COMMITTED_NODE_STATUS:
            raise StateInvariantError("a persistent graph node must be committed")
        object.__setattr__(self, "input_digests", _freeze_digests(self.input_digests, "input_digests"))
        object.__setattr__(self, "input_artifacts", _freeze_refs(self.input_artifacts, "input_artifacts"))
        object.__setattr__(self, "output_artifacts", _freeze_refs(self.output_artifacts, "output_artifacts"))
        _digest(self.knowledge_snapshot_digest, "knowledge_snapshot_digest", optional=True)
        _digest(self.capability_profile_digest, "capability_profile_digest", optional=True)
        _non_negative_int(self.candidate_revision, "candidate_revision")
        _digest(self.input_candidate_digest, "input_candidate_digest")
        if self.lifecycle_status != ACTIVE_LIFECYCLE_STATUS:
            raise StateInvariantError("accepted graph nodes must have active lifecycle_status")

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_version": self.node_version,
            "stage_signature": self.stage_signature,
            "input_digests": dict(self.input_digests),
            "input_artifacts": {key: ref.to_dict() for key, ref in self.input_artifacts.items()},
            "output_artifacts": {key: ref.to_dict() for key, ref in self.output_artifacts.items()},
            "knowledge_snapshot_digest": self.knowledge_snapshot_digest,
            "capability_profile_digest": self.capability_profile_digest,
            "candidate_revision": self.candidate_revision,
            "input_candidate_digest": self.input_candidate_digest,
            "commit_id": self.commit_id,
            "lifecycle_status": self.lifecycle_status,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "NodeAcceptance":
        expected = {
            "node_id", "node_version", "stage_signature", "input_digests",
            "input_artifacts", "output_artifacts", "knowledge_snapshot_digest",
            "capability_profile_digest", "candidate_revision", "input_candidate_digest",
            "commit_id", "lifecycle_status", "status",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise StateInvariantError("NodeAcceptance fields do not match the v3.1 schema")
        try:
            raw_inputs = value["input_artifacts"]
            raw_outputs = value["output_artifacts"]
            if not isinstance(raw_inputs, Mapping) or not isinstance(raw_outputs, Mapping):
                raise StateInvariantError("node artifact references must be objects")
            return cls(
                node_id=value["node_id"],
                node_version=value["node_version"],
                stage_signature=value["stage_signature"],
                input_digests=value["input_digests"],
                input_artifacts={key: ArtifactRef.from_dict(ref) for key, ref in raw_inputs.items()},
                output_artifacts={key: ArtifactRef.from_dict(ref) for key, ref in raw_outputs.items()},
                knowledge_snapshot_digest=value["knowledge_snapshot_digest"],
                capability_profile_digest=value["capability_profile_digest"],
                candidate_revision=value["candidate_revision"],
                input_candidate_digest=value["input_candidate_digest"],
                commit_id=value["commit_id"],
                lifecycle_status=value["lifecycle_status"],
                status=value["status"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise StateInvariantError("invalid NodeAcceptance") from exc


@dataclass(frozen=True)
class PersistentGraphState:
    """Portable runtime-ledger snapshot for a single write scope."""

    run_id: str
    graph_digest: str
    outputs: Mapping[str, ArtifactRef]
    accepted: Mapping[str, NodeAcceptance]
    candidate_revision: int
    candidate_digest: str
    candidate_validation_status: ValidationStatus = ValidationStatus.DRAFT
    event_sequence: int = 0
    current_commit_id: str = ""
    retained_outputs: Mapping[str, RetainedArtifact] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _text(self.run_id, "run_id")
        _digest(self.graph_digest, "graph_digest")
        _non_negative_int(self.candidate_revision, "candidate_revision")
        if type(self.candidate_validation_status) is not ValidationStatus:
            raise StateInvariantError("candidate_validation_status must be a canonical ValidationStatus")
        if self.candidate_validation_status not in {
            ValidationStatus.DRAFT,
            ValidationStatus.TEXT_VALIDATED,
        }:
            raise StateInvariantError(
                "persistent graph cannot claim media or owner validation status"
            )
        if isinstance(self.event_sequence, bool) or not isinstance(self.event_sequence, int) or self.event_sequence < 0:
            raise StateInvariantError("event_sequence must be a non-negative integer")
        if self.event_sequence == 0 and self.candidate_revision != 0:
            raise StateInvariantError("the root state must use candidate_revision zero")
        if (
            self.event_sequence == 0
            and self.candidate_validation_status is not ValidationStatus.DRAFT
        ):
            raise StateInvariantError("the root state must begin at DRAFT validation status")
        if self.event_sequence == 0 and self.current_commit_id:
            raise StateInvariantError("an empty state cannot name a current commit")
        if self.event_sequence > 0:
            _text(self.current_commit_id, "current_commit_id")
        object.__setattr__(self, "outputs", _freeze_refs(self.outputs, "outputs"))
        if not isinstance(self.accepted, Mapping):
            raise StateInvariantError("accepted must be a mapping")
        accepted: dict[str, NodeAcceptance] = {}
        for node_id, result in self.accepted.items():
            text = _text(node_id, "accepted node")
            if not isinstance(result, NodeAcceptance) or result.node_id != text:
                raise StateInvariantError("accepted entries must match their node_id")
            accepted[text] = result
        object.__setattr__(self, "accepted", MappingProxyType(accepted))
        if not isinstance(self.retained_outputs, Mapping):
            raise StateInvariantError("retained_outputs must be a mapping")
        retained: dict[str, RetainedArtifact] = {}
        for field_name, value in self.retained_outputs.items():
            text = _text(field_name, "retained output field")
            if not isinstance(value, RetainedArtifact) or value.field_name != text:
                raise StateInvariantError("retained outputs must match their field names")
            retained[text] = value
        if self.event_sequence == 0 and (self.outputs or accepted or retained):
            raise StateInvariantError("an empty state cannot contain accepted or retained values")
        object.__setattr__(self, "retained_outputs", MappingProxyType(retained))
        expected_candidate_digest = candidate_digest_for(
            run_id=self.run_id,
            graph_digest=self.graph_digest,
            candidate_revision=self.candidate_revision,
            outputs=self.outputs,
        )
        _digest(self.candidate_digest, "candidate_digest")
        if self.candidate_digest != expected_candidate_digest:
            raise StateInvariantError(
                "candidate_digest does not bind run, graph, revision, and outputs"
            )

    @classmethod
    def empty(cls, run_id: str, *, graph_digest: str) -> "PersistentGraphState":
        return cls(
            run_id=run_id,
            graph_digest=graph_digest,
            outputs={},
            accepted={},
            candidate_revision=0,
            candidate_digest=candidate_digest_for(
                run_id=run_id,
                graph_digest=graph_digest,
                candidate_revision=0,
                outputs={},
            ),
            candidate_validation_status=ValidationStatus.DRAFT,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": PERSISTENT_STATE_SCHEMA_NAME,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "run_id": self.run_id,
            "graph_digest": self.graph_digest,
            "outputs": {field: ref.to_dict() for field, ref in self.outputs.items()},
            "accepted": {node_id: entry.to_dict() for node_id, entry in self.accepted.items()},
            "retained_outputs": {
                field: entry.to_dict() for field, entry in self.retained_outputs.items()
            },
            "candidate_revision": self.candidate_revision,
            "candidate_digest": self.candidate_digest,
            "candidate_validation_status": self.candidate_validation_status.value,
            "event_sequence": self.event_sequence,
            "current_commit_id": self.current_commit_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PersistentGraphState":
        expected = {
            "schema_name", "schema_version", "run_id", "graph_digest", "outputs",
            "accepted", "retained_outputs", "candidate_revision", "candidate_digest",
            "candidate_validation_status", "event_sequence", "current_commit_id",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise StateInvariantError("persistent state fields do not match the v3.1 schema")
        if value.get("schema_name") != PERSISTENT_STATE_SCHEMA_NAME or value.get("schema_version") != PERSISTENCE_SCHEMA_VERSION:
            raise StateInvariantError("unsupported persistent graph state schema")
        raw_outputs = value["outputs"]
        raw_accepted = value["accepted"]
        raw_retained = value["retained_outputs"]
        if (
            not isinstance(raw_outputs, Mapping)
            or not isinstance(raw_accepted, Mapping)
            or not isinstance(raw_retained, Mapping)
        ):
            raise StateInvariantError("persistent state outputs, accepted, and retained_outputs must be objects")
        try:
            validation_status = ValidationStatus(value["candidate_validation_status"])
        except (TypeError, ValueError) as exc:
            raise StateInvariantError(
                "candidate_validation_status is not a canonical ValidationStatus"
            ) from exc
        return cls(
            run_id=value["run_id"],
            graph_digest=value["graph_digest"],
            outputs={key: ArtifactRef.from_dict(ref) for key, ref in raw_outputs.items()},
            accepted={key: NodeAcceptance.from_dict(entry) for key, entry in raw_accepted.items()},
            retained_outputs={
                key: RetainedArtifact.from_dict(entry)
                for key, entry in raw_retained.items()
            },
            candidate_revision=value["candidate_revision"],
            candidate_digest=value["candidate_digest"],
            candidate_validation_status=validation_status,
            event_sequence=value["event_sequence"],
            current_commit_id=value["current_commit_id"],
        )
