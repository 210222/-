"""Immutable artifact envelopes and canonical serialization."""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Generic, Mapping, Sequence, TypeVar


DOMAIN_SCHEMA_VERSION = "3.0"
CANONICAL_DOMAIN_TYPES = ("ArtifactEnvelope", "SourceRef", "ArtifactKind", "ValidationStatus")
_HEX = frozenset("0123456789abcdef")
T = TypeVar("T")


class DomainValidationError(ValueError):
    """Raised when a canonical domain invariant is violated."""


class ArtifactKind(str, enum.Enum):
    NORMALIZED_SOURCE = "normalized_source"
    FACT_REGISTRY = "fact_registry"
    SCRIPT_FACT = "script_fact"
    EPISODE_DIRECTION_DRAFT = "episode_direction_draft"
    SCENE_INTENT_DRAFT = "scene_intent_draft"
    KNOWLEDGE_CAPSULE = "knowledge_capsule"
    KNOWLEDGE_SNAPSHOT = "knowledge_snapshot"
    BLOCKING_DRAFT = "blocking_draft"
    BLOCKING_COMMIT = "blocking_commit"
    DECISION_DRAFT = "decision_draft"
    EXECUTION_DESIGN_DRAFT = "execution_design_draft"
    VISUAL_EXECUTION_CONTRACT = "visual_execution_contract"
    PROJECTION_AST = "projection_ast"
    PROJECTION_MANIFEST = "projection_manifest"
    CAPABILITY_ADAPTATION = "capability_adaptation"
    GATE0_RESULT = "gate0_result"
    REVIEW_PACKET = "review_packet"
    DP_REVIEW_RESULT = "dp_review_result"
    REVISION_REQUEST = "revision_request"
    MEDIA_RUN_RECORD = "media_run_record"
    FRAME_EVIDENCE_PLAN = "frame_evidence_plan"
    MEDIA_EVIDENCE = "media_evidence"
    VISUAL_VERIFICATION_RESULT = "visual_verification_result"
    OWNER_APPROVAL_RECORD = "owner_approval_record"
    RELEASE_DECISION = "release_decision"


class ValidationStatus(str, enum.Enum):
    DRAFT = "draft"
    TEXT_VALIDATED = "text_validated"
    VISUAL_EVIDENCED = "visual_evidenced"
    OWNER_APPROVED = "owner_approved"
    REJECTED = "rejected"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be a non-empty string")


def require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in _HEX for char in value):
        raise DomainValidationError(f"{field_name} must be a lowercase SHA-256")


def _require_utc_timestamp(value: str, field_name: str) -> None:
    _require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainValidationError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")


def _canonical_text(value: str) -> str:
    """Return the text form used by every canonical structured hash.

    Domain values may retain their source-facing presentation, but hashes must
    not drift merely because a Windows checkout or upstream text source used
    CRLF/CR line endings.  NFC is deliberately *not* applied here: that is a
    source-normalization responsibility, and applying it to arbitrary creative
    text would silently redefine persisted content beyond the architecture.
    """

    return value.replace("\r\n", "\n").replace("\r", "\n")


def _require_deeply_immutable(
    value: Any, field_name: str, active: set[int] | None = None
) -> None:
    if value is None or isinstance(value, (str, int, bool, enum.Enum)):
        return
    if isinstance(value, float):
        raise DomainValidationError(f"{field_name} cannot contain floating-point values")

    active = set() if active is None else active
    identity = id(value)
    if identity in active:
        raise DomainValidationError(f"{field_name} cannot contain recursive values")

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        params = getattr(value, "__dataclass_params__", None)
        if params is None or not params.frozen:
            raise DomainValidationError(f"{field_name} dataclass values must be frozen")
        active.add(identity)
        try:
            for item in dataclasses.fields(value):
                _require_deeply_immutable(
                    getattr(value, item.name), f"{field_name}.{item.name}", active
                )
        finally:
            active.remove(identity)
        return

    if isinstance(value, Mapping):
        if not isinstance(value, MappingProxyType):
            raise DomainValidationError(f"{field_name} retains a mutable mapping")
        active.add(identity)
        try:
            for key, item in value.items():
                _require_text(key, f"{field_name} key")
                _require_deeply_immutable(item, f"{field_name}[{key}]", active)
        finally:
            active.remove(identity)
        return

    if isinstance(value, tuple):
        active.add(identity)
        try:
            for index, item in enumerate(value):
                _require_deeply_immutable(item, f"{field_name}[{index}]", active)
        finally:
            active.remove(identity)
        return

    raise DomainValidationError(
        f"{field_name} retains mutable or unsupported type: {type(value).__name__}"
    )


def _deep_freeze(value: Any, field_name: str, active: set[int] | None = None) -> Any:
    """Create an immutable canonical snapshot without retaining mutable aliases."""

    if value is None or isinstance(value, (str, int, bool, enum.Enum)):
        return value
    if isinstance(value, float):
        raise DomainValidationError(f"{field_name} cannot contain floating-point values")
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        _require_deeply_immutable(value, field_name)
        return value

    active = set() if active is None else active
    identity = id(value)
    if identity in active:
        raise DomainValidationError(f"{field_name} cannot contain recursive values")

    if isinstance(value, Mapping):
        active.add(identity)
        try:
            frozen: dict[str, Any] = {}
            for key, item in value.items():
                _require_text(key, f"{field_name} key")
                frozen[key] = _deep_freeze(item, f"{field_name}[{key}]", active)
            return MappingProxyType(frozen)
        finally:
            active.remove(identity)

    if isinstance(value, (tuple, list)):
        active.add(identity)
        try:
            return tuple(
                _deep_freeze(item, f"{field_name}[{index}]", active)
                for index, item in enumerate(value)
            )
        finally:
            active.remove(identity)

    raise DomainValidationError(
        f"{field_name} contains unsupported canonical type: {type(value).__name__}"
    )


def freeze_mapping(value: Mapping[str, Any], field_name: str = "mapping") -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DomainValidationError(f"{field_name} must be a mapping")
    frozen = _deep_freeze(value, field_name)
    if not isinstance(frozen, Mapping):
        raise DomainValidationError(f"{field_name} must be a mapping")
    return frozen


def _canonical_value(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return _canonical_value(value.value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {item.name: _canonical_value(getattr(value, item.name)) for item in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key in value:
            key = raw_key
            if not isinstance(key, str):
                raise DomainValidationError("canonical mappings require string keys")
            key = _canonical_text(key)
            if key in result:
                raise DomainValidationError(
                    "canonical mapping keys collide after line-ending normalization"
                )
            result[key] = _canonical_value(value[raw_key])
        return {key: result[key] for key in sorted(result)}
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, str):
        return _canonical_text(value)
    if value is None or isinstance(value, (int, bool)):
        return value
    if isinstance(value, float):
        raise DomainValidationError("floating-point values are forbidden in canonical artifacts")
    raise DomainValidationError(f"unsupported canonical value type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _canonical_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def binary_sha256(value: bytes | bytearray | memoryview) -> str:
    """Hash binary evidence without text normalization or transcoding."""

    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise DomainValidationError("binary_sha256 requires bytes-like input")
    return hashlib.sha256(bytes(value)).hexdigest()


def _canonical_payload_type(artifact_kind: ArtifactKind) -> type[Any]:
    """Return the sole payload authority for a persistent artifact kind.

    Imports stay local so the pure domain modules can declare their payload
    classes without an import cycle at module load time.
    """

    from .blocking import BlockingCommit, BlockingDraft
    from .decisions import DecisionDraft
    from .direction import EpisodeDirectionDraft, SceneIntentDraft
    from .evidence import (
        DeterministicGateResult,
        FrameEvidencePlan,
        IndependentDPReviewResult,
        MediaEvidence,
        MediaRunRecord,
        OwnerApprovalRecord,
        ReviewPacket,
        RevisionRequest,
        VisualVerificationResult,
    )
    from .facts import FactRegistry, NormalizedSource, ScriptFact
    from .knowledge import KnowledgeCapsuleV2, KnowledgeSnapshot
    from .projection import (
        CapabilityAdaptationRecord,
        ProjectionAST,
        ProjectionManifest,
    )
    from .release import ReleaseGateRecord
    from .vec import ExecutionDesignDraft, VisualExecutionContract

    authorities: dict[ArtifactKind, type[Any]] = {
        ArtifactKind.NORMALIZED_SOURCE: NormalizedSource,
        ArtifactKind.FACT_REGISTRY: FactRegistry,
        ArtifactKind.SCRIPT_FACT: ScriptFact,
        ArtifactKind.EPISODE_DIRECTION_DRAFT: EpisodeDirectionDraft,
        ArtifactKind.SCENE_INTENT_DRAFT: SceneIntentDraft,
        ArtifactKind.KNOWLEDGE_CAPSULE: KnowledgeCapsuleV2,
        ArtifactKind.KNOWLEDGE_SNAPSHOT: KnowledgeSnapshot,
        ArtifactKind.BLOCKING_DRAFT: BlockingDraft,
        ArtifactKind.BLOCKING_COMMIT: BlockingCommit,
        ArtifactKind.DECISION_DRAFT: DecisionDraft,
        ArtifactKind.EXECUTION_DESIGN_DRAFT: ExecutionDesignDraft,
        ArtifactKind.VISUAL_EXECUTION_CONTRACT: VisualExecutionContract,
        ArtifactKind.PROJECTION_AST: ProjectionAST,
        ArtifactKind.PROJECTION_MANIFEST: ProjectionManifest,
        ArtifactKind.CAPABILITY_ADAPTATION: CapabilityAdaptationRecord,
        ArtifactKind.GATE0_RESULT: DeterministicGateResult,
        ArtifactKind.REVIEW_PACKET: ReviewPacket,
        ArtifactKind.DP_REVIEW_RESULT: IndependentDPReviewResult,
        ArtifactKind.REVISION_REQUEST: RevisionRequest,
        ArtifactKind.MEDIA_RUN_RECORD: MediaRunRecord,
        ArtifactKind.FRAME_EVIDENCE_PLAN: FrameEvidencePlan,
        ArtifactKind.MEDIA_EVIDENCE: MediaEvidence,
        ArtifactKind.VISUAL_VERIFICATION_RESULT: VisualVerificationResult,
        ArtifactKind.OWNER_APPROVAL_RECORD: OwnerApprovalRecord,
        ArtifactKind.RELEASE_DECISION: ReleaseGateRecord,
    }
    try:
        return authorities[artifact_kind]
    except KeyError as exc:
        raise DomainValidationError(
            f"artifact_kind has no canonical payload authority: {artifact_kind.value}"
        ) from exc


@dataclass(frozen=True)
class SourceRef:
    source_id: str
    digest: str
    locator: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.source_id, "source_id")
        require_sha256(self.digest, "digest")
        if self.locator is not None:
            _require_text(self.locator, "locator")


@dataclass(frozen=True)
class ArtifactEnvelope(Generic[T]):
    artifact_id: str
    artifact_type: ArtifactKind
    schema_version: str
    payload: T
    canonical_payload_sha256: str
    producer_stage: str
    parent_artifact_ids: tuple[str, ...]
    source_provenance: tuple[SourceRef, ...]
    knowledge_snapshot_digest: str | None
    created_at_utc: str

    def __post_init__(self) -> None:
        _require_text(self.artifact_id, "artifact_id")
        if not isinstance(self.artifact_type, ArtifactKind):
            raise DomainValidationError("artifact_type must be an ArtifactKind")
        _require_text(self.schema_version, "schema_version")
        if self.schema_version != DOMAIN_SCHEMA_VERSION:
            raise DomainValidationError(
                f"schema_version must match canonical domain schema {DOMAIN_SCHEMA_VERSION}"
            )
        _require_text(self.producer_stage, "producer_stage")
        _require_utc_timestamp(self.created_at_utc, "created_at_utc")
        payload = _deep_freeze(self.payload, "payload")
        expected_payload_type = _canonical_payload_type(self.artifact_type)
        if type(payload) is not expected_payload_type:
            raise DomainValidationError(
                "payload type does not match artifact_kind canonical authority: "
                f"expected {expected_payload_type.__name__}, got {type(payload).__name__}"
            )
        declared_kind = getattr(payload, "ARTIFACT_KIND", None)
        if declared_kind is not self.artifact_type:
            raise DomainValidationError(
                "artifact_type does not match the payload's canonical authority"
            )
        parents = tuple(self.parent_artifact_ids)
        if any(not isinstance(item, str) or not item.strip() for item in parents):
            raise DomainValidationError("parent_artifact_ids must contain non-empty IDs")
        if len(parents) != len(set(parents)):
            raise DomainValidationError("parent_artifact_ids must not contain duplicates")
        if self.artifact_id in parents:
            raise DomainValidationError("an Artifact cannot be its own parent")
        refs = tuple(self.source_provenance)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError("source_provenance must contain at least one SourceRef")
        if self.knowledge_snapshot_digest is not None:
            require_sha256(self.knowledge_snapshot_digest, "knowledge_snapshot_digest")
        object.__setattr__(self, "parent_artifact_ids", parents)
        object.__setattr__(self, "source_provenance", refs)
        object.__setattr__(self, "payload", payload)
        require_sha256(self.canonical_payload_sha256, "canonical_payload_sha256")
        if self.canonical_payload_sha256 != canonical_sha256(payload):
            raise DomainValidationError(
                "canonical_payload_sha256 does not match canonical payload"
            )

    @classmethod
    def create(
        cls,
        *,
        artifact_id: str,
        artifact_type: ArtifactKind,
        payload: T,
        producer_stage: str,
        parent_artifact_ids: Sequence[str],
        source_provenance: Sequence[SourceRef],
        knowledge_snapshot_digest: str | None,
        created_at_utc: str,
        schema_version: str = DOMAIN_SCHEMA_VERSION,
    ) -> "ArtifactEnvelope[T]":
        return cls(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            schema_version=schema_version,
            payload=payload,
            canonical_payload_sha256=canonical_sha256(payload),
            producer_stage=producer_stage,
            parent_artifact_ids=tuple(parent_artifact_ids),
            source_provenance=tuple(source_provenance),
            knowledge_snapshot_digest=knowledge_snapshot_digest,
            created_at_utc=created_at_utc,
        )
