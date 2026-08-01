"""Fail-closed Claude CLI transport for a structured DeepSeek Draft call.

This adapter does not import the historical director runtime and performs no
process or network I/O at import time.  It transports system text, compact
approved input, and JSON Schema through distinct request fields.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from mode_p_vnext.ports.structured_text import (
    CapabilityUnsupportedError,
    ContractPatch,
    GenerationPolicy,
    ModelDraft,
    RepairBudget,
    StructuredGenerationPort,
    TextCallEvidence,
    ViolationSet,
)
from mode_p_vnext.prompts.compiler import PromptCompiler
from mode_p_vnext.prompts.schema_registry import DraftSchema, DraftSchemaRegistry
from mode_p_vnext.prompts.signatures import Stage, StageSignature


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProviderCapabilities:
    native_json_schema: bool


@dataclass(frozen=True)
class StructuredTransportRequest:
    executable: str
    requested_model: str
    system_message: str
    user_message: str
    json_schema: Mapping[str, Any]
    temperature: float
    max_output_tokens: int


class StructuredTransportError(RuntimeError):
    """A non-creative CLI/transport failure with no raw output persistence."""


def resolve_windows_claude_binary(
    candidates: Sequence[str], *, is_windows: bool | None = None
) -> str:
    """Choose only native ``claude.exe`` on Windows, never a ``.cmd`` shim."""

    windows = os.name == "nt" if is_windows is None else is_windows
    if not candidates:
        raise CapabilityUnsupportedError("CAPABILITY_UNSUPPORTED: no Claude executable candidate")
    if not windows:
        return candidates[0]
    for candidate in candidates:
        basename = candidate.replace("\\", "/").rsplit("/", 1)[-1].casefold()
        if basename == "claude.exe":
            return candidate
    raise CapabilityUnsupportedError(
        "CAPABILITY_UNSUPPORTED: native claude.exe is required on Windows"
    )


class ClaudeCodeNativeRunner:
    """Invoke the authenticated Claude Code CLI only as a text transport.

    The runner is inert until called by ``generate``.  It sends the system
    contract, compact approved input, and native JSON Schema through separate
    process channels, exposes no tools, and returns only a decoded Draft plus
    non-sensitive usage metadata.
    """

    def __init__(
        self,
        *,
        executable: str = "claude.exe",
        cwd: str | None = None,
        timeout_seconds: int = 600,
        subprocess_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        if timeout_seconds < 1 or timeout_seconds > 1_800:
            raise ValueError("timeout_seconds must be within 1..1800")
        self._executable = resolve_windows_claude_binary((executable,))
        self._cwd = cwd
        self._timeout_seconds = timeout_seconds
        self._subprocess_runner = subprocess_runner

    def __call__(self, request: StructuredTransportRequest) -> Mapping[str, Any]:
        if request.executable != self._executable:
            raise StructuredTransportError("transport executable does not match configured native binary")
        schema_json = json.dumps(
            request.json_schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        argv = [
            self._executable,
            "-p",
            "--model",
            request.requested_model,
            "--effort",
            "max",
            "--permission-mode",
            "bypassPermissions",
            "--tools",
            "",
            "--disable-slash-commands",
            "--safe-mode",
            "--no-session-persistence",
            "--system-prompt",
            request.system_message,
            "--no-chrome",
            "--output-format",
            "json",
            "--json-schema",
            schema_json,
        ]
        try:
            completed = self._subprocess_runner(
                argv,
                input=request.user_message,
                cwd=self._cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise StructuredTransportError(
                f"Claude Code structured transport failed: {type(exc).__name__}"
            ) from exc
        if completed.returncode != 0:
            raise StructuredTransportError(
                "Claude Code structured transport returned non-zero; "
                f"exit_code={completed.returncode}; "
                f"stdout_sha256={_sha256_text(completed.stdout or '')}; "
                f"stderr_sha256={_sha256_text(completed.stderr or '')}"
            )
        try:
            envelope = json.loads(completed.stdout or "")
        except json.JSONDecodeError as exc:
            raise StructuredTransportError("Claude Code did not return a JSON envelope") from exc
        if not isinstance(envelope, Mapping):
            raise StructuredTransportError("Claude Code envelope must be a JSON object")
        raw_result = envelope.get("result", envelope)
        if isinstance(raw_result, str):
            try:
                payload = json.loads(raw_result)
            except json.JSONDecodeError as exc:
                raise StructuredTransportError("Claude Code result is not a JSON Draft") from exc
        else:
            payload = raw_result
        if not isinstance(payload, Mapping):
            raise StructuredTransportError("Claude Code Draft must be a JSON object")
        model_usage = envelope.get("modelUsage")
        model_record = (
            model_usage.get(request.requested_model, {})
            if isinstance(model_usage, Mapping)
            else {}
        )
        usage = envelope.get("usage")
        return {
            "payload": dict(payload),
            "resolved_model": str(model_record.get("canonicalModel") or request.requested_model),
            "usage": dict(usage) if isinstance(usage, Mapping) else {},
        }


class ClaudeDeepSeekStructuredAdapter(StructuredGenerationPort):
    """A native-schema-only structured Draft transport.

    Unsupported schema capability is rejected before invoking ``runner``.
    Transport errors do not touch ``RepairBudget``; only a submitted scoped
    ``ContractPatch`` consumes that budget.
    """

    def __init__(
        self,
        *,
        runner: Callable[[StructuredTransportRequest], Mapping[str, Any] | str] | None = None,
        executable: str,
        capabilities: ProviderCapabilities = ProviderCapabilities(native_json_schema=True),
        compiler: PromptCompiler | None = None,
        schema_registry: DraftSchemaRegistry | None = None,
        provider_name: str = "claude_deepseek",
    ) -> None:
        if not executable.strip():
            raise ValueError("executable must be non-empty")
        self._executable = resolve_windows_claude_binary((executable,))
        self._runner = runner or ClaudeCodeNativeRunner(executable=self._executable)
        self._capabilities = capabilities
        self._schemas = schema_registry or DraftSchemaRegistry()
        self._compiler = compiler or PromptCompiler(self._schemas)
        self._provider_name = provider_name

    def generate(
        self,
        signature: StageSignature,
        approved_input: Mapping[str, Any],
        policy: GenerationPolicy,
    ) -> tuple[ModelDraft, TextCallEvidence]:
        self._require_native_schema_capability()
        compiled = self._compiler.compile(signature, approved_input)
        schema = self._schemas.schema_for(signature)
        if schema.digest != compiled.schema_digest:
            raise RuntimeError("compiled prompt/schema digest mismatch")
        payload, evidence = self._invoke(
            signature, compiled, schema, policy, attempt=1
        )
        return ModelDraft(signature.stage, signature.contract_name, payload), evidence

    def repair(
        self,
        signature: StageSignature,
        violations: ViolationSet,
        policy: GenerationPolicy,
        repair_budget: RepairBudget,
    ) -> tuple[ContractPatch, TextCallEvidence]:
        """Request one native, scoped ContractPatch without re-sending a Draft."""

        if signature.stage is not violations.stage:
            raise ValueError("signature stage must match violation set stage")
        repair_budget.ensure_available(violations)
        self._require_native_schema_capability()
        compiled = self._compiler.compile_repair(signature, violations)
        schema = self._schemas.repair_schema_for(signature)
        if schema.digest != compiled.schema_digest:
            raise RuntimeError("compiled repair/schema digest mismatch")
        payload, evidence = self._invoke(
            signature, compiled, schema, policy, attempt=2
        )
        try:
            patch = ContractPatch(
                stage=Stage(str(payload["stage"])),
                draft_digest=str(payload["draft_digest"]),
                repair_scope=tuple(payload["repair_scope"]),
                values=dict(payload["values"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("provider returned an invalid ContractPatch") from exc
        repair_budget.consume(violations, patch)
        return patch, evidence

    def _require_native_schema_capability(self) -> None:
        """This adapter has no non-native transport; reject before model I/O."""

        if not self._capabilities.native_json_schema:
            raise CapabilityUnsupportedError(
                "CAPABILITY_UNSUPPORTED: provider lacks native JSON Schema transport"
            )

    def _invoke(
        self,
        signature: StageSignature,
        compiled: Any,
        schema: DraftSchema,
        policy: GenerationPolicy,
        *,
        attempt: int,
    ) -> tuple[Mapping[str, Any], TextCallEvidence]:
        request = StructuredTransportRequest(
            executable=self._executable,
            requested_model=policy.requested_model,
            system_message=compiled.system_message,
            user_message=compiled.user_message,
            json_schema=schema.document,
            temperature=policy.temperature,
            max_output_tokens=policy.max_output_tokens,
        )
        started = time.monotonic()
        response = self._runner(request)
        latency_ms = int((time.monotonic() - started) * 1000)
        payload, resolved_model, usage = self._decode_response(response, policy.requested_model)
        _validate_draft_against_schema(payload, schema.document)
        response_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        evidence = TextCallEvidence(
            provider=self._provider_name,
            requested_model=policy.requested_model,
            resolved_model=resolved_model,
            stage=signature.stage,
            signature_version=signature.version,
            schema_digest=schema.digest,
            approved_input_digest=compiled.approved_input_digest,
            request_digest=_sha256_text(compiled.prompt_text + schema.canonical_json),
            response_digest=_sha256_text(response_text),
            prompt_characters=compiled.character_count,
            schema_characters=schema.character_count,
            response_characters=len(response_text),
            latency_ms=latency_ms,
            attempt=attempt,
            accepted=True,
            rejection_code=None,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            cache_hit=usage.get("cache_hit"),
        )
        return payload, evidence

    @staticmethod
    def _decode_response(
        response: Mapping[str, Any] | str, requested_model: str
    ) -> tuple[Mapping[str, Any], str, Mapping[str, Any]]:
        if isinstance(response, str):
            try:
                decoded: Any = json.loads(response)
            except json.JSONDecodeError as exc:
                raise ValueError("provider returned non-JSON Draft") from exc
        else:
            decoded = dict(response)
        if not isinstance(decoded, Mapping):
            raise ValueError("provider Draft must be a JSON object")
        if "payload" in decoded:
            payload = decoded["payload"]
            if not isinstance(payload, Mapping):
                raise ValueError("provider payload must be an object")
            resolved_model = str(decoded.get("resolved_model") or requested_model)
            usage = decoded.get("usage", {})
            return dict(payload), resolved_model, dict(usage) if isinstance(usage, Mapping) else {}
        return dict(decoded), requested_model, {}


def _validate_draft_against_schema(
    value: Any, schema: Mapping[str, Any], path: str = "$"
) -> None:
    """Strict local decoding for the compact Draft-schema subset we emit.

    It intentionally validates only the JSON Schema vocabulary declared by
    ``DraftSchemaRegistry``.  Any unsupported schema keyword would be a
    registry defect rather than a reason to weaken local decoding.
    """

    if "anyOf" in schema:
        branches = schema["anyOf"]
        if not isinstance(branches, list) or not branches:
            raise ValueError(f"draft schema violation at {path}: invalid anyOf")
        failures: list[ValueError] = []
        for branch in branches:
            if not isinstance(branch, Mapping):
                raise ValueError(f"draft schema violation at {path}: invalid anyOf branch")
            try:
                _validate_draft_against_schema(value, branch, path)
            except ValueError as exc:
                failures.append(exc)
            else:
                return
        raise ValueError(f"draft schema violation at {path}: no anyOf branch matched") from failures[-1]
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"draft schema violation at {path}: value is outside enum")
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, Mapping):
            raise ValueError(f"draft schema violation at {path}: expected object")
        properties = schema.get("properties", {})
        additional_properties = schema.get("additionalProperties", True)
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"draft schema violation at {path}: object keys must be strings")
            if key in properties:
                continue
            if additional_properties is False:
                raise ValueError(
                    f"draft schema violation at {path}: unexpected field {key}"
                )
            if isinstance(additional_properties, Mapping):
                _validate_draft_against_schema(
                    item, additional_properties, f"{path}.{key}"
                )
        for key in schema.get("required", ()):
            if key not in value:
                raise ValueError(
                    f"draft schema violation at {path}: missing required field {key}"
                )
        for key, nested_schema in properties.items():
            if key in value:
                _validate_draft_against_schema(value[key], nested_schema, f"{path}.{key}")
        return
    if expected == "array":
        if not isinstance(value, list):
            raise ValueError(f"draft schema violation at {path}: expected array")
        if len(value) < schema.get("minItems", 0):
            raise ValueError(f"draft schema violation at {path}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValueError(f"draft schema violation at {path}: too many items")
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _validate_draft_against_schema(item, item_schema, f"{path}[{index}]")
        return
    if expected == "string":
        if not isinstance(value, str):
            raise ValueError(f"draft schema violation at {path}: expected string")
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValueError(f"draft schema violation at {path}: string is too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValueError(f"draft schema violation at {path}: string exceeds maxLength")
        if "pattern" in schema:
            pattern = schema["pattern"]
            if not isinstance(pattern, str) or re.fullmatch(pattern, value) is None:
                raise ValueError(f"draft schema violation at {path}: string does not match pattern")
        return
    if expected == "null":
        if value is not None:
            raise ValueError(f"draft schema violation at {path}: expected null")
        return
    if expected == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"draft schema violation at {path}: expected integer")
    elif expected == "number":
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"draft schema violation at {path}: expected number")
    else:
        return
    if "minimum" in schema and value < schema["minimum"]:
        raise ValueError(f"draft schema violation at {path}: below minimum")
    if "maximum" in schema and value > schema["maximum"]:
        raise ValueError(f"draft schema violation at {path}: above maximum")
    if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
        raise ValueError(f"draft schema violation at {path}: below exclusive minimum")
