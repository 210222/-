"""Port contract for a structured creative-Draft model call."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from mode_p_vnext.prompts.signatures import Stage, StageSignature


TEXT_VALIDATED = "TEXT_VALIDATED"


class CapabilityUnsupportedError(RuntimeError):
    """The provider cannot satisfy a required transport capability."""


@dataclass(frozen=True)
class GenerationPolicy:
    requested_model: str
    temperature: float = 0.2
    max_output_tokens: int = 2_000
    require_native_schema: bool = True

    def __post_init__(self) -> None:
        if not self.requested_model.strip():
            raise ValueError("requested_model must be non-empty")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be within [0, 2]")
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")


@dataclass(frozen=True)
class ModelDraft:
    """Unsealed creative output. It is never a VEC or release artifact."""

    stage: Stage
    contract_name: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class TextCallEvidence:
    """Audit metadata only; no prompt, response text, credentials, or reasoning."""

    provider: str
    requested_model: str
    resolved_model: str
    stage: Stage
    signature_version: str
    schema_digest: str
    approved_input_digest: str
    request_digest: str
    response_digest: str
    prompt_characters: int
    schema_characters: int
    response_characters: int
    latency_ms: int
    attempt: int
    accepted: bool
    rejection_code: str | None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_hit: bool | None = None
    claim_ceiling: str = TEXT_VALIDATED

    def __post_init__(self) -> None:
        if self.claim_ceiling != TEXT_VALIDATED:
            raise ValueError("text port claim ceiling must remain TEXT_VALIDATED")
        if self.attempt < 1 or self.latency_ms < 0:
            raise ValueError("attempt and latency must be non-negative")
        if self.accepted and self.rejection_code is not None:
            raise ValueError("accepted calls cannot contain a rejection code")
        for value in (
            self.schema_digest,
            self.approved_input_digest,
            self.request_digest,
            self.response_digest,
        ):
            if len(value) != 64:
                raise ValueError("text evidence digests must be SHA-256 values")


@dataclass(frozen=True)
class Violation:
    code: str
    json_path: str
    expected: str
    observed_summary: str

    def __post_init__(self) -> None:
        if not self.code or not self.json_path.startswith("$"):
            raise ValueError("violation needs a code and JSON path")
        if not self.expected or not self.observed_summary:
            raise ValueError("violation needs expected and observed summaries")


@dataclass(frozen=True)
class ViolationSet:
    """A compact local-validation result suitable for one scoped model repair."""

    stage: Stage
    draft_digest: str
    violations: tuple[Violation, ...]
    repair_scope: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.draft_digest) != 64:
            raise ValueError("draft_digest must be a SHA-256 value")
        if not self.violations or not self.repair_scope:
            raise ValueError("violation set must contain violations and a repair scope")
        if any(not path.startswith("$") for path in self.repair_scope):
            raise ValueError("repair scope paths must be JSON paths")
        if len(self.repair_scope) != len(set(self.repair_scope)):
            raise ValueError("repair scope paths must be unique")


@dataclass(frozen=True)
class ContractPatch:
    """A narrow patch request; it cannot resend the full prompt or failed Draft."""

    stage: Stage
    draft_digest: str
    repair_scope: tuple[str, ...]
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        if len(self.draft_digest) != 64:
            raise ValueError("draft_digest must be a SHA-256 value")
        scope = tuple(self.repair_scope)
        if not scope or len(scope) != len(set(scope)):
            raise ValueError("repair scope must be non-empty and unique")
        if set(self.values) - set(scope):
            raise ValueError("patch values outside the approved repair scope")
        if not self.values:
            raise ValueError("contract patch must contain at least one scoped value")

    def compact_payload(self, violations: ViolationSet) -> Mapping[str, Any]:
        if self.stage is not violations.stage or self.draft_digest != violations.draft_digest:
            raise ValueError("contract patch must bind the violation set")
        if not set(self.repair_scope).issubset(set(violations.repair_scope)):
            raise ValueError("patch repair scope exceeds the violation set")
        return {
            "stage": self.stage.value,
            "draft_digest": self.draft_digest,
            "violations": [
                {
                    "code": item.code,
                    "json_path": item.json_path,
                    "expected": item.expected,
                    "observed_summary": item.observed_summary,
                }
                for item in violations.violations
            ],
            "repair_scope": self.repair_scope,
            "values": dict(self.values),
        }


@dataclass
class RepairBudget:
    """At most one creative contract repair per stage execution."""

    maximum: int = 1
    used: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.maximum != 1:
            raise ValueError("architecture permits exactly one scoped contract repair")

    def ensure_available(self, violations: ViolationSet, patch: ContractPatch) -> None:
        patch.compact_payload(violations)
        if self.used >= self.maximum:
            raise ValueError("repair budget exhausted")

    def consume(self, violations: ViolationSet, patch: ContractPatch) -> int:
        self.ensure_available(violations, patch)
        self.used += 1
        return self.used


class StructuredGenerationPort(Protocol):
    """The only provider boundary consumed by later vNext pipeline nodes."""

    def generate(
        self,
        signature: StageSignature,
        approved_input: Mapping[str, Any],
        policy: GenerationPolicy,
    ) -> tuple[ModelDraft, TextCallEvidence]: ...
