"""Immutable artifact envelopes and canonical serialization."""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Generic, Mapping, Sequence, TypeVar


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("ArtifactEnvelope", "SourceRef", "ArtifactKind", "ValidationStatus")
_HEX = frozenset("0123456789abcdef")
T = TypeVar("T")


class DomainValidationError(ValueError):
    """Raised when a canonical domain invariant is violated."""


class ArtifactKind(str, enum.Enum):
    SCRIPT_FACT = "script_fact"
    EPISODE_DIRECTION = "episode_direction"
    SCENE_INTENT = "scene_intent"
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
    REVIEW_PACKET = "review_packet"
    REVISION_REQUEST = "revision_request"
    MEDIA_RUN_RECORD = "media_run_record"
    FRAME_EVIDENCE_PLAN = "frame_evidence_plan"
    MEDIA_EVIDENCE = "media_evidence"
    VISUAL_VERIFICATION_RESULT = "visual_verification_result"
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
        for key in sorted(value):
            if not isinstance(key, str):
                raise DomainValidationError("canonical mappings require string keys")
            result[key] = _canonical_value(value[key])
        return result
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
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
    artifact_kind: ArtifactKind
    schema_version: str
    program_version: str
    payload: T
    source_refs: tuple[SourceRef, ...]
    dependency_digests: Mapping[str, str] = field(default_factory=dict)
    content_sha256: str = ""
    created_at: str = ""
    validation_status: ValidationStatus = ValidationStatus.DRAFT

    def __post_init__(self) -> None:
        _require_text(self.artifact_id, "artifact_id")
        if not isinstance(self.artifact_kind, ArtifactKind):
            raise DomainValidationError("artifact_kind must be an ArtifactKind")
        _require_text(self.schema_version, "schema_version")
        _require_text(self.program_version, "program_version")
        _require_text(self.created_at, "created_at")
        if not isinstance(self.validation_status, ValidationStatus):
            raise DomainValidationError("validation_status must be a ValidationStatus")
        payload = _deep_freeze(self.payload, "payload")
        declared_kind = getattr(payload, "ARTIFACT_KIND", None)
        if declared_kind is not None and declared_kind is not self.artifact_kind:
            raise DomainValidationError(
                "artifact_kind does not match the payload's canonical authority"
            )
        refs = tuple(self.source_refs)
        if not refs or not all(isinstance(ref, SourceRef) for ref in refs):
            raise DomainValidationError("source_refs must contain at least one SourceRef")
        dependencies = freeze_mapping(self.dependency_digests, "dependency_digests")
        for key, digest in dependencies.items():
            require_sha256(digest, f"dependency_digests[{key}]")
        object.__setattr__(self, "source_refs", refs)
        object.__setattr__(self, "dependency_digests", dependencies)
        object.__setattr__(self, "payload", payload)
        require_sha256(self.content_sha256, "content_sha256")
        expected = self.content_digest_for(
            artifact_kind=self.artifact_kind,
            schema_version=self.schema_version,
            program_version=self.program_version,
            payload=payload,
            source_refs=refs,
            dependency_digests=dependencies,
        )
        if self.content_sha256 != expected:
            raise DomainValidationError("content_sha256 does not match canonical artifact content")

    @staticmethod
    def content_digest_for(
        *,
        artifact_kind: ArtifactKind,
        schema_version: str,
        program_version: str,
        payload: T,
        source_refs: Sequence[SourceRef],
        dependency_digests: Mapping[str, str],
    ) -> str:
        return canonical_sha256(
            {
                "artifact_kind": artifact_kind,
                "schema_version": schema_version,
                "program_version": program_version,
                "payload": payload,
                "source_refs": tuple(source_refs),
                "dependency_digests": dependency_digests,
            }
        )

    @classmethod
    def create(
        cls,
        *,
        artifact_id: str,
        artifact_kind: ArtifactKind,
        schema_version: str,
        program_version: str,
        payload: T,
        source_refs: Sequence[SourceRef],
        dependency_digests: Mapping[str, str],
        created_at: str,
        validation_status: ValidationStatus = ValidationStatus.DRAFT,
    ) -> "ArtifactEnvelope[T]":
        refs = tuple(source_refs)
        dependencies = freeze_mapping(dependency_digests, "dependency_digests")
        return cls(
            artifact_id=artifact_id,
            artifact_kind=artifact_kind,
            schema_version=schema_version,
            program_version=program_version,
            payload=payload,
            source_refs=refs,
            dependency_digests=dependencies,
            content_sha256=cls.content_digest_for(
                artifact_kind=artifact_kind,
                schema_version=schema_version,
                program_version=program_version,
                payload=payload,
                source_refs=refs,
                dependency_digests=dependencies,
            ),
            created_at=created_at,
            validation_status=validation_status,
        )
