"""Strict text-only DeepSeek adapter for the Director vNext.1 contracts.

Importing this module never performs network I/O.  The HTTP client requires an
explicit API key and the provider records hashes/usage, never prompts, model
reasoning, credentials, or raw responses.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import MISSING, asdict, dataclass, fields, is_dataclass
from types import UnionType
from typing import (
    Any,
    Callable,
    Literal,
    Mapping,
    Protocol,
    Tuple,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from .agent import DirectorProvider, _phase_a_fingerprint
from .contracts import (
    BlockingCommit,
    DecisionPacket,
    DirectorContractError,
    EpisodeDirectionState,
    EpisodeRequest,
    PhaseAResult,
    PhaseBExecutionDraft,
    PhaseBResult,
    SceneInput,
    materialize_phase_b_result,
)
from .provider_prompts import build_stage_messages, strict_json_schema


DEFAULT_DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"
TEXT_VALIDATED = "TEXT_VALIDATED"
CLI_NATIVE_JSON_SCHEMA_MAX_CHARS = 12000


class DeepSeekProviderError(DirectorContractError):
    """Fail-closed provider, transport, model provenance, or JSON error."""


def _runtime_packet_payload(packet: DecisionPacket) -> Mapping[str, Any]:
    """Expose only the bounded runtime view of a knowledge packet to the model.

    Runtime packets previously used ``asdict(packet)``.  That repeated source
    provenance and normalization-only fields in B0/B1 prompts even though the
    Director only needs approved application rules.  The compact view keeps
    the selected capsules, their allowed execution guidance, conflict status,
    and applicability records, while leaving full source evidence offline.
    """

    def capsule_payload(capsule: Any) -> Mapping[str, Any]:
        # ``KnowledgeCapsule.runtime_metadata`` is intentionally rich for
        # local audit.  A model-stage packet must be smaller: source hashes,
        # field provenance, related IDs and fingerprint data do not alter the
        # Director's current choice and needlessly consume reasoning context.
        common = {
            "capsule_id": capsule.capsule_id,
            "director_problem": capsule.director_problem,
            "dramatic_function": capsule.dramatic_function,
            "triggers": capsule.triggers,
            "contraindications": capsule.contraindications,
            "required_context": capsule.required_context,
            "execution_rules": capsule.execution_rules,
            "expected_effect": capsule.expected_effect,
            "confidence_level": capsule.confidence_level,
            "allowed_uses": capsule.allowed_uses,
        }
        if packet.stage == "K1":
            # K1 supplies selected planning/blocking knowledge. Candidate
            # alternatives and source taxonomy were resolved by retrieval and
            # do not need to be re-litigated in B0.
            return common
        return {
            **common,
            "primary_type": capsule.primary_type,
            "tags": capsule.tags,
            "secondary_tags": capsule.secondary_tags,
            "decision_level": capsule.decision_level,
            "tradeoffs": capsule.tradeoffs,
            "alternatives": capsule.alternatives,
            "anti_pattern_tags": capsule.anti_pattern_tags,
        }

    return {
        "packet_id": packet.packet_id,
        "scene_id": packet.scene_id,
        "stage": packet.stage,
        "blocking_commit_id": packet.blocking_commit_id,
        "no_match": packet.no_match,
        "primary_capsules": [
            capsule_payload(capsule) for capsule in packet.primary_capsules
        ],
        "conflict_capsule": (
            capsule_payload(packet.conflict_capsule)
            if packet.conflict_capsule
            else None
        ),
        "anti_pattern_capsule": (
            capsule_payload(packet.anti_pattern_capsule)
            if packet.anti_pattern_capsule
            else None
        ),
        "application_records": [
            asdict(record) for record in packet.application_records
        ],
        "conflict_decision": (
            asdict(packet.conflict_decision)
            if packet.conflict_decision
            else None
        ),
    }


def _blocking_phase_a_payload(phase_a: PhaseAResult) -> Mapping[str, Any]:
    """Project Phase A into the exact facts B0 needs to freeze blocking.

    The full Phase-A object remains the immutable, fingerprinted source.  B0
    receives its action, entry/exit, beat, and preservation fields plus the
    relevant Director questions.  This is an information-scope reduction, not
    a second interpretation or a truncation of any selected field.
    """

    intent = phase_a.scene_intent
    return {
        "scene_id": intent.scene_id,
        "dramatic_action": intent.dramatic_action,
        "entry_state": intent.entry_state,
        "exit_state": intent.exit_state,
        "character_actions": intent.character_actions,
        "beats": [asdict(beat) for beat in intent.beats],
        "risk_flags": intent.risk_flags,
        "must_preserve": intent.must_preserve,
        "avoid_list": intent.avoid_list,
        # K1 carries the problem-to-capsule mapping and problem rationale. B0
        # only needs the stable identifiers to cite the blocking it resolves.
        "director_problem_ids": [
            problem.problem_id for problem in phase_a.problem_set.problems
        ],
    }


def _execution_phase_a_payload(phase_a: PhaseAResult) -> Mapping[str, Any]:
    """Project only execution-relevant Phase-A facts into B1.

    B1 has the validated BlockingCommit and K2 packet; audience and character
    knowledge prose is intentionally not repeated when it adds no executable
    field beyond the already-approved scene objective and information goal.
    """

    intent = phase_a.scene_intent
    return {
        "scene_id": intent.scene_id,
        "dramatic_turn": intent.dramatic_turn,
        "relationship_state": intent.relationship_state,
        "performance_question": intent.performance_question,
        "information_goal": intent.information_goal,
        "scene_objective": intent.scene_objective,
        "dramatic_action": intent.dramatic_action,
        "entry_state": intent.entry_state,
        "exit_state": intent.exit_state,
        "power_curve": intent.power_curve,
        "character_actions": intent.character_actions,
        "beats": [asdict(beat) for beat in intent.beats],
        "attention_trajectory": intent.attention_trajectory,
        "risk_flags": intent.risk_flags,
        "must_preserve": intent.must_preserve,
        "avoid_list": intent.avoid_list,
        "director_problem_ids": [
            problem.problem_id for problem in phase_a.problem_set.problems
        ],
    }


def _b1_k1_packet_payload(packet: DecisionPacket) -> Mapping[str, Any]:
    """Give B1 K1 lineage without repeating B0-resolved planning prose."""

    return {
        "packet_id": packet.packet_id,
        "scene_id": packet.scene_id,
        "stage": packet.stage,
        "selected_capsule_ids": [
            capsule.capsule_id for capsule in packet.primary_capsules
        ],
        "application_records": [
            {
                "capsule_id": record.capsule_id,
                "problem_ids": record.problem_ids,
                "allowed_use": record.allowed_use,
                "influenced_fields": record.influenced_fields,
            }
            for record in packet.application_records
        ],
        "no_match": packet.no_match,
    }


def _required_vec_reference_bindings(
    scene: SceneInput,
    blocking_commit: BlockingCommit,
) -> tuple[Mapping[str, Any], ...]:
    """Derive non-negotiable B1 asset bindings from accepted B0 locally."""

    character_ids = sorted(
        {
            state.character_id
            for beat in blocking_commit.beats
            for state in beat.character_states
        }
    )
    prop_ids = sorted(
        {
            prop.prop_id
            for beat in blocking_commit.beats
            for prop in beat.prop_states
        }
    )
    requirements: list[Mapping[str, Any]] = []
    for character_id in character_ids:
        requirements.extend(
            (
                {
                    "role": "character_identity",
                    "scope_kind": "character",
                    "scope_id": character_id,
                    "minimum_priority": 100,
                },
                {
                    "role": "wardrobe",
                    "scope_kind": "character",
                    "scope_id": character_id,
                    "minimum_priority": 100,
                },
            )
        )
    requirements.extend(
        {
            "role": "prop_geometry",
            "scope_kind": "prop",
            "scope_id": prop_id,
            "minimum_priority": 80,
        }
        for prop_id in prop_ids
    )
    requirements.append(
        {
            "role": "scene_layout",
            "scope_kind": "scene",
            "scope_id": scene.scene_id,
            "minimum_priority": 70,
        }
    )
    return tuple(requirements)


def _repair_instruction(stage: str, violation: str) -> str:
    """Give one bounded, stage-specific repair instruction without raw output."""

    stage_guardrail = ""
    if stage == "B0":
        stage_guardrail = (
            " For B0 specifically: every beats[i].action_paths must be a "
            "non-empty JSON array; each item must state 'character: motivation "
            "-> physical action -> spatial/result state'. Do not use [] or "
            "camera/edit language."
        )
    return (
        "The preceding contract attempt was rejected. Correct this exact "
        f"violation: {violation}.{stage_guardrail} Return the complete "
        "replacement JSON object only; do not explain, preserve approved facts, "
        "and do not introduce visual-media verification claims."
    )


def _iter_contract_text(value: Any, path: str = "$"):
    if isinstance(value, str):
        yield path, value
        return
    if is_dataclass(value):
        for field in fields(value):
            yield from _iter_contract_text(
                getattr(value, field.name),
                f"{path}.{field.name}",
            )
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            yield from _iter_contract_text(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield from _iter_contract_text(item, f"{path}.{key}")


def _assert_stage_output_budget(stage: str, result: Any) -> None:
    """Keep externally serialized contracts compact without limiting reasoning."""

    max_chars = {
        "E0": 180,
        "S1": 180,
        "B0": 180,
        "B1": 240,
    }.get(stage)
    if max_chars is None:
        return
    over_budget = next(
        (
            (path, len(text))
            for path, text in _iter_contract_text(result)
            if len(text) > max_chars
        ),
        None,
    )
    if over_budget is not None:
        path, length = over_budget
        raise DeepSeekProviderError(
            f"{stage} text budget exceeds {max_chars} characters at {path} ({length})"
        )


@dataclass(frozen=True)
class TextModelResponse:
    content: str
    resolved_model: str
    request_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_tokens: int = 0
    transport_normalization: str = ""


class TextCompletionClient(Protocol):
    def complete(
        self,
        *,
        model: str,
        messages: Tuple[Mapping[str, str], ...],
        temperature: float,
        max_tokens: int,
        thinking_enabled: bool,
        json_schema: Mapping[str, Any] | None = None,
        effort: str = "max",
    ) -> TextModelResponse:
        """Return a text response from the exact requested model."""


@dataclass(frozen=True)
class ProviderCallRecord:
    stage: str
    model: str
    request_id: str
    request_sha256: str
    response_sha256: str
    duration_ms: int
    input_tokens: int
    output_tokens: int
    cache_hit_tokens: int
    validation_status: str = TEXT_VALIDATED
    media_inspection_performed: bool = False
    visual_acceptance_claimed: bool = False
    transport_normalization: str = ""
    prompt_chars: int = 0
    schema_chars: int = 0
    schema_transport: str = ""
    attempt: int = 1
    accepted: bool = True
    rejection_reason: str = ""


class DeepSeekOpenAITextClient:
    """Minimal OpenAI-compatible HTTP client with no implicit credentials."""

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = DEFAULT_DEEPSEEK_ENDPOINT,
        timeout_seconds: int = 180,
    ) -> None:
        if not api_key or not api_key.strip():
            raise DeepSeekProviderError("DEEPSEEK_API_KEY is required")
        if not endpoint.startswith("https://"):
            raise DeepSeekProviderError("DeepSeek endpoint must use HTTPS")
        if timeout_seconds < 1 or timeout_seconds > 600:
            raise DeepSeekProviderError("DeepSeek timeout must be 1..600 seconds")
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(cls) -> "DeepSeekOpenAITextClient":
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        return cls(api_key=api_key)

    def complete(
        self,
        *,
        model: str,
        messages: Tuple[Mapping[str, str], ...],
        temperature: float,
        max_tokens: int,
        thinking_enabled: bool,
        json_schema: Mapping[str, Any] | None = None,
        effort: str = "max",
    ) -> TextModelResponse:
        body: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        del json_schema, effort  # The HTTP transport only requests a JSON object.
        if thinking_enabled:
            body["thinking"] = {"type": "enabled"}
        request = urllib.request.Request(
            self._endpoint,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self._timeout_seconds,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise DeepSeekProviderError(
                f"DeepSeek text request failed: {type(exc).__name__}"
            ) from exc
        try:
            choice = payload["choices"][0]
            content = choice["message"]["content"]
            resolved_model = payload.get("model", model)
        except (KeyError, IndexError, TypeError) as exc:
            raise DeepSeekProviderError("DeepSeek response envelope is invalid") from exc
        if not isinstance(content, str) or not content.strip():
            raise DeepSeekProviderError("DeepSeek response content is empty")
        usage = payload.get("usage") or {}
        details = usage.get("prompt_tokens_details") or {}
        return TextModelResponse(
            content=content,
            resolved_model=str(resolved_model),
            request_id=str(payload.get("id", "")),
            input_tokens=int(usage.get("prompt_tokens", 0) or 0),
            output_tokens=int(usage.get("completion_tokens", 0) or 0),
            cache_hit_tokens=int(
                details.get(
                    "cache_read_tokens",
                    usage.get("prompt_cache_hit_tokens", 0),
                )
                or 0
            ),
        )


class ClaudeCodeDeepSeekTextClient:
    """Use the user's authenticated Claude Code CLI as a text-only transport.

    No credential is read by this class.  It intentionally passes neither
    files nor tool permissions to the CLI, so a Director call cannot upload
    media, inspect a local storyboard, or edit the project.
    """

    uses_native_json_schema = True
    # Windows passes `--json-schema` as an argv element.  Keep a conservative
    # headroom below CreateProcess' command-line limit; larger schemas travel
    # in the prompt and remain fail-closed in the local decoder.
    native_json_schema_max_chars = CLI_NATIVE_JSON_SCHEMA_MAX_CHARS

    def __init__(
        self,
        *,
        executable: str = "claude",
        cwd: str | None = None,
        timeout_seconds: int = 600,
        runner: Any = subprocess.run,
    ) -> None:
        if not executable.strip():
            raise DeepSeekProviderError("Claude Code executable is required")
        if timeout_seconds < 1 or timeout_seconds > 1800:
            raise DeepSeekProviderError("Claude Code timeout must be 1..1800 seconds")
        self._executable = executable
        self._cwd = cwd
        self._timeout_seconds = timeout_seconds
        self._runner = runner

    def _resolved_executable(self) -> str:
        """Resolve npm's Windows ``claude.cmd`` without invoking a shell."""

        found = shutil.which(self._executable)
        if found:
            return found
        if os.name == "nt" and self._executable == "claude":
            app_data = os.environ.get("APPDATA", "")
            candidate = os.path.join(app_data, "npm", "claude.cmd")
            if app_data and os.path.isfile(candidate):
                return candidate
        return self._executable

    @staticmethod
    def _unwrap_standalone_json_fence(content: str) -> tuple[str, str]:
        """Normalize only known Claude/DeepSeek presentation wrappers.

        This is intentionally narrower than Markdown parsing: a fence is
        accepted only when it contains one object and has no surrounding prose.
        A leading DeepSeek ``<think>`` block is discarded only when it is
        followed by one object and no other presentation text.  Any other
        explanation remains invalid at the Director contract layer and the
        discarded thought content is never persisted.
        """

        match = re.fullmatch(
            r"\s*```json\s*(\{.*\})\s*```\s*",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if match is None:
            think_match = re.fullmatch(
                r"\s*<think>.*?</think>\s*(\{.*\})\s*",
                content,
                flags=re.DOTALL | re.IGNORECASE,
            )
            if think_match is None:
                return content, ""
            return think_match.group(1), "cli_leading_think_block_discarded"
        return match.group(1), "cli_standalone_json_fence"

    @staticmethod
    def _classify_nonzero_cli_output(stdout: str) -> str:
        """Expose a stable transport category without persisting raw output."""

        # Claude's JSON envelope carries an HTTP-like API status.  It is more
        # reliable than searching its human error message: the latter can say
        # "permission" for a payment/credit refusal and previously made CPL-2
        # misdiagnose HTTP 402 as a local permission-gate failure.
        try:
            envelope = json.loads(stdout)
            api_status = envelope.get("api_error_status") if isinstance(envelope, Mapping) else None
        except json.JSONDecodeError:
            api_status = None
        status_classes = {
            400: "request_rejected",
            401: "authentication_failed",
            402: "billing_or_credit_required",
            403: "authorization_denied",
            408: "transport_timeout",
            413: "prompt_too_large",
            429: "rate_limited",
            500: "provider_unavailable",
            502: "provider_unavailable",
            503: "provider_unavailable",
            504: "transport_timeout",
        }
        if isinstance(api_status, int) and api_status in status_classes:
            return status_classes[api_status]
        lowered = stdout.lower()
        if "command line is too long" in lowered:
            return "command_line_too_long"
        if "json schema" in lowered or "schema" in lowered:
            return "schema_rejected"
        if "rate limit" in lowered or "too many requests" in lowered:
            return "rate_limited"
        if "authentication" in lowered or "unauthorized" in lowered:
            return "authentication_failed"
        if "timeout" in lowered or "timed out" in lowered:
            return "transport_timeout"
        if "overloaded" in lowered or "unavailable" in lowered:
            return "provider_unavailable"
        if "context" in lowered and ("limit" in lowered or "long" in lowered):
            return "context_limit"
        if "prompt" in lowered and ("limit" in lowered or "large" in lowered):
            return "prompt_too_large"
        if "permission" in lowered or "forbidden" in lowered:
            return "permission_rejected"
        if "invalid" in lowered or "bad request" in lowered:
            return "request_rejected"
        if "error" in lowered:
            return "cli_reported_error"
        return "cli_unspecified"

    @staticmethod
    def _nonzero_stdout_shape(stdout: str) -> str:
        """Return non-sensitive diagnostics for a failed CLI envelope."""

        try:
            envelope = json.loads(stdout)
        except json.JSONDecodeError:
            return f"text_chars={len(stdout)}"
        if not isinstance(envelope, Mapping):
            return "json_non_object"
        result = envelope.get("result")
        api_status = envelope.get("api_error_status")
        message_type = envelope.get("type")
        subtype = envelope.get("subtype")
        terminal_reason = envelope.get("terminal_reason")
        return (
            "json_keys=" + ",".join(sorted(str(key) for key in envelope))
            + f";is_error={bool(envelope.get('is_error'))}"
            + f";api_error_status={api_status if isinstance(api_status, int) else 'none'}"
            + f";type={message_type if isinstance(message_type, str) else 'none'}"
            + f";subtype={subtype if isinstance(subtype, str) else 'none'}"
            + f";terminal_reason={terminal_reason if isinstance(terminal_reason, str) else 'none'}"
            + f";result_type={type(result).__name__}"
            + f";result_chars={len(result) if isinstance(result, str) else 0}"
        )

    def complete(
        self,
        *,
        model: str,
        messages: Tuple[Mapping[str, str], ...],
        temperature: float,
        max_tokens: int,
        thinking_enabled: bool,
        json_schema: Mapping[str, Any] | None = None,
        effort: str = "max",
    ) -> TextModelResponse:
        del temperature, max_tokens  # Claude Code controls its supported range.
        if effort not in {"low", "medium", "high", "xhigh", "max"}:
            raise DeepSeekProviderError("unsupported Claude Code effort")
        # Claude Code otherwise keeps its default *agent* system prompt even
        # when the user payload says "text only".  That default can make the
        # model enter tool/permission handling before it answers.  Put the
        # Director contract in Claude's actual system-prompt slot and keep the
        # stdin payload limited to the request data.
        system_contents = [
            message["content"]
            for message in messages
            if message["role"] == "system"
        ]
        if not system_contents:
            raise DeepSeekProviderError(
                "Claude Code text transport requires a system contract"
            )
        prompt_parts = [
            f"[{message['role'].upper()}]\n{message['content']}"
            for message in messages
            if message["role"] != "system"
        ]
        if not prompt_parts:
            raise DeepSeekProviderError(
                "Claude Code text transport requires a non-system request"
            )
        system_prompt = "\n\n".join(system_contents)
        prompt = "\n\n".join(prompt_parts)
        argv = [
            self._resolved_executable(),
            "-p",
            "--model",
            model,
            "--effort",
            effort if thinking_enabled else "high",
            "--permission-mode",
            # Claude Code can deny its own confirmation action even with no
            # tools in `plan` or `auto` mode. This bypass applies only to that
            # empty-tool session: no file, shell, browser, media, or MCP tool
            # is present for the model to exercise.
            "bypassPermissions",
            # A text-only Director must never attempt CLI tools. This prevents
            # intermittent permission denials without granting read/write
            # access to the workspace or media assets.
            "--tools",
            "",
            # Eliminate the remaining agentic paths.  ``-p`` is Claude Code's
            # one-print completion mode; safe mode additionally blocks local
            # hooks, plugins, agents, and project customizations.
            "--disable-slash-commands",
            "--safe-mode",
            "--no-session-persistence",
            "--system-prompt",
            system_prompt,
            "--no-chrome",
            "--output-format",
            "json",
        ]
        if json_schema is not None:
            argv.extend(
                [
                    "--json-schema",
                    json.dumps(
                        json_schema,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ]
            )
        try:
            completed = self._runner(
                argv,
                input=prompt,
                cwd=self._cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DeepSeekProviderError(
                f"Claude Code text transport failed: {type(exc).__name__}"
            ) from exc
        if completed.returncode != 0:
            stderr = completed.stderr or ""
            stdout = completed.stdout or ""
            stderr_hash = hashlib.sha256(stderr.encode("utf-8")).hexdigest()
            stdout_hash = hashlib.sha256(stdout.encode("utf-8")).hexdigest()
            safe_tail = re.sub(r"\s+", " ", stderr)[-480:]
            raise DeepSeekProviderError(
                "Claude Code text transport failed with exit "
                f"{completed.returncode}; stderr_sha256={stderr_hash}; "
                f"stdout_sha256={stdout_hash}; "
                f"cli_error_class={self._classify_nonzero_cli_output(stdout)}; "
                f"stdout_shape={self._nonzero_stdout_shape(stdout)}; "
                f"stderr_tail={safe_tail!r}"
            )
        raw_stdout = completed.stdout or ""
        stdout_candidate, stdout_normalization = self._unwrap_standalone_json_fence(
            raw_stdout
        )
        try:
            envelope = json.loads(stdout_candidate)
            if not isinstance(envelope, Mapping):
                raise TypeError("Claude Code JSON output must be an object")
            if "result" in envelope:
                content = envelope["result"]
                model_usage = envelope.get("modelUsage") or {}
                model_record = model_usage.get(model) or {}
                resolved_model = str(
                    model_record.get("canonicalModel", model)
                )
                usage = envelope.get("usage") or {}
                direct_contract_json = False
            else:
                # Some installed Claude Code builds emit a direct JSON object
                # when the model itself produces structured JSON, rather than
                # wrapping it in the documented result envelope.  It is safe
                # to accept only a plain object with none of Claude's envelope
                # control fields; the stage decoder still validates every
                # contract field locally and fail-closed.
                envelope_fields = {
                    "api_error_status",
                    "is_error",
                    "modelUsage",
                    "permission_denials",
                    "result",
                    "session_id",
                    "stop_reason",
                    "subtype",
                    "terminal_reason",
                    "type",
                    "usage",
                }
                if any(field in envelope for field in envelope_fields):
                    raise KeyError("Claude Code result envelope has no result")
                content = json.dumps(
                    envelope,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                resolved_model = model
                usage = {}
                direct_contract_json = True
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise DeepSeekProviderError(
                "Claude Code did not return a valid JSON result envelope; "
                f"stdout_sha256={hashlib.sha256(raw_stdout.encode('utf-8')).hexdigest()}; "
                f"stdout_shape={self._nonzero_stdout_shape(raw_stdout)}"
            ) from exc
        if (
            not direct_contract_json
            and envelope.get("is_error")
        ) or not isinstance(content, str) or not content.strip():
            raise DeepSeekProviderError("Claude Code reported an unsuccessful text result")
        normalized_content, normalization = self._unwrap_standalone_json_fence(content)
        normalizations = [
            marker for marker in (stdout_normalization, normalization) if marker
        ]
        if direct_contract_json:
            normalizations.insert(0, "cli_direct_contract_json")
        normalization = "+".join(dict.fromkeys(normalizations))
        return TextModelResponse(
            content=normalized_content,
            resolved_model=resolved_model,
            request_id="" if direct_contract_json else str(envelope.get("session_id", "")),
            input_tokens=int(usage.get("input_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            cache_hit_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
            transport_normalization=normalization,
        )


_VISUAL_CLAIM_PATTERN = re.compile(
    r"(?:visually\s+(?:verified|inspected)|image\s+inspected|video\s+inspected|"
    r"no\s+mirror\s+flip\s+observed|(?:已|经)(?:视觉|画面|视频|图像)(?:核验|验证|检查)|"
    r"(?:镜像|手部|眼神|站位|道具方向).{0,12}(?:画面)?(?:通过|正确|无误))",
    re.IGNORECASE,
)


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _decode_value(annotation: Any, value: Any, path: str) -> Any:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if is_dataclass(annotation):
        return _decode_dataclass(annotation, value, path)
    if origin in {tuple, Tuple}:
        if not isinstance(value, list):
            raise DeepSeekProviderError(f"{path} must be a JSON array")
        item_type = args[0] if args else Any
        return tuple(
            _decode_value(item_type, item, f"{path}[{index}]")
            for index, item in enumerate(value)
        )
    if origin is list:
        if not isinstance(value, list):
            raise DeepSeekProviderError(f"{path} must be a JSON array")
        item_type = args[0] if args else Any
        return [
            _decode_value(item_type, item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if origin in {dict, Mapping}:
        if not isinstance(value, dict):
            raise DeepSeekProviderError(f"{path} must be a JSON object")
        value_type = args[1] if len(args) > 1 else Any
        return {
            str(key): _decode_value(value_type, item, f"{path}.{key}")
            for key, item in value.items()
        }
    if origin in {Union, UnionType}:
        if value is None and type(None) in args:
            return None
        errors = []
        for candidate in (item for item in args if item is not type(None)):
            try:
                return _decode_value(candidate, value, path)
            except DeepSeekProviderError as exc:
                errors.append(str(exc))
        raise DeepSeekProviderError(
            f"{path} does not match its allowed JSON type"
        )
    if origin is Literal:
        if value not in args:
            allowed = ", ".join(repr(item) for item in args)
            raise DeepSeekProviderError(f"{path} must equal one of: {allowed}")
        return value
    if annotation is Any:
        return value
    if annotation is bool:
        if type(value) is not bool:
            raise DeepSeekProviderError(f"{path} must be a boolean")
        return value
    if annotation is int:
        if type(value) is not int:
            raise DeepSeekProviderError(f"{path} must be an integer")
        return value
    if annotation is float:
        if type(value) not in {int, float}:
            raise DeepSeekProviderError(f"{path} must be a number")
        return float(value)
    if annotation is str:
        if not isinstance(value, str):
            raise DeepSeekProviderError(f"{path} must be a string")
        return value
    return value


def _decode_dataclass(contract_type: type, value: Any, path: str = "$") -> Any:
    if not isinstance(value, dict):
        raise DeepSeekProviderError(f"{path} must be a JSON object")
    contract_fields = {field.name: field for field in fields(contract_type)}
    unknown = sorted(set(value) - set(contract_fields))
    if unknown:
        raise DeepSeekProviderError(
            f"{path} contains unknown contract fields: {unknown}"
        )
    hints = get_type_hints(contract_type)
    decoded: dict[str, Any] = {}
    for name, contract_field in contract_fields.items():
        if name not in value:
            if (
                contract_field.default is MISSING
                and contract_field.default_factory is MISSING
            ):
                raise DeepSeekProviderError(f"{path}.{name} is required")
            continue
        decoded[name] = _decode_value(
            hints[name],
            value[name],
            f"{path}.{name}",
        )
    try:
        return contract_type(**decoded)
    except (TypeError, ValueError) as exc:
        raise DeepSeekProviderError(
            f"{path} violates {contract_type.__name__}: {exc}"
        ) from exc


class DeepSeekDirectorProvider(DirectorProvider):
    """Persistent text Director; all four stages are contract-decoded."""

    def __init__(
        self,
        client: TextCompletionClient,
        *,
        director_id: str,
        model: str = DEFAULT_DEEPSEEK_MODEL,
        max_tokens: int = 24000,
        max_contract_repairs: int = 1,
    ) -> None:
        if not director_id.strip():
            raise DeepSeekProviderError("director_id is required")
        if model != DEFAULT_DEEPSEEK_MODEL:
            raise DeepSeekProviderError(
                f"Director model must be exactly {DEFAULT_DEEPSEEK_MODEL}"
            )
        self._client = client
        self._director_id = director_id
        self._model = model
        self._max_tokens = max_tokens
        if max_contract_repairs < 0 or max_contract_repairs > 2:
            raise DeepSeekProviderError("max_contract_repairs must be 0..2")
        self._max_contract_repairs = max_contract_repairs
        self._records: list[ProviderCallRecord] = []

    @property
    def call_records(self) -> Tuple[ProviderCallRecord, ...]:
        return tuple(self._records)

    def _call(
        self,
        *,
        stage: str,
        contract_type: type,
        approved_input: Mapping[str, Any],
        output_transform: Callable[[Any], Any] | None = None,
    ) -> Any:
        correction = ""
        contract_attempt = 1
        native_schema_fallback_used = False
        while contract_attempt <= self._max_contract_repairs + 1:
            # Local decoding and budget checks remain authoritative.  Native
            # CLI schema is a transport assist, so omit only maxLength there
            # when it would otherwise force a large B1 schema back into the
            # prompt/argv failure path.
            validation_schema = strict_json_schema(
                contract_type,
                max_string_length={
                    "E0": 180,
                    "S1": 180,
                    "B0": 180,
                    "B1": 240,
                }.get(stage),
            )
            native_transport_schema = strict_json_schema(contract_type)
            serialized_schema = json.dumps(
                validation_schema,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            serialized_native_schema = json.dumps(
                native_transport_schema,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            native_limit = getattr(
                self._client,
                "native_json_schema_max_chars",
                None,
            )
            use_native_schema = not native_schema_fallback_used and bool(
                getattr(self._client, "uses_native_json_schema", False)
            ) and (
                native_limit is None
                or len(serialized_native_schema) <= int(native_limit)
            )
            messages = build_stage_messages(
                stage=stage,
                contract_type=contract_type,
                approved_input=approved_input,
                include_contract_shape=not use_native_schema,
            )
            if correction:
                messages = (
                    *messages,
                    {
                        "role": "user",
                        "content": _repair_instruction(stage, correction),
                    },
                )
            started = time.monotonic()
            request_sha256 = _sha256_json(messages)
            prompt_chars = sum(len(message["content"]) for message in messages)
            schema_transport = (
                "native_argv" if use_native_schema else "stdin_contract_shape"
            )
            try:
                response = self._client.complete(
                    model=self._model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=self._max_tokens,
                    thinking_enabled=True,
                    json_schema=(
                        native_transport_schema if use_native_schema else None
                    ),
                    # The Director policy is deliberately uniform: no stage may
                    # silently downgrade the requested maximum reasoning effort.
                    effort="max",
                )
            except DeepSeekProviderError as exc:
                duration_ms = round((time.monotonic() - started) * 1000)
                # A transport failure has no trustworthy response to repair.
                # The sole exception is a fast native-schema CLI
                # incompatibility: retry it once through stdin contract shape,
                # which avoids an argv/schema compatibility failure without
                # spending a model contract-repair attempt. Timeouts and late
                # failures stop.
                self._records.append(
                    ProviderCallRecord(
                        stage=stage,
                        model=self._model,
                        request_id="",
                        request_sha256=request_sha256,
                        response_sha256="",
                        duration_ms=duration_ms,
                        input_tokens=0,
                        output_tokens=0,
                        cache_hit_tokens=0,
                        prompt_chars=prompt_chars,
                        schema_chars=len(serialized_schema),
                        schema_transport=schema_transport,
                        attempt=contract_attempt,
                        accepted=False,
                        rejection_reason=str(exc),
                    )
                )
                native_schema_incompatibility = (
                    "text transport failed with exit 1" in str(exc)
                    or "did not return a valid JSON result envelope" in str(exc)
                )
                if (
                    use_native_schema
                    and not native_schema_fallback_used
                    and duration_ms <= 60_000
                    and native_schema_incompatibility
                ):
                    native_schema_fallback_used = True
                    continue
                raise
            duration_ms = round((time.monotonic() - started) * 1000)
            response_sha256 = hashlib.sha256(
                response.content.encode("utf-8")
            ).hexdigest()
            try:
                if response.resolved_model != self._model:
                    raise DeepSeekProviderError(
                        "DeepSeek resolved model does not match the requested Director model"
                    )
                if _VISUAL_CLAIM_PATTERN.search(response.content):
                    raise DeepSeekProviderError(
                        "text-only Director attempted to claim visual media verification"
                    )
                try:
                    raw = json.loads(response.content)
                except json.JSONDecodeError as exc:
                    raise DeepSeekProviderError(
                        "DeepSeek must return one strict JSON object without Markdown"
                    ) from exc
                result = _decode_dataclass(contract_type, raw)
                if output_transform is not None:
                    result = output_transform(result)
                _assert_stage_output_budget(stage, result)
            except (DeepSeekProviderError, DirectorContractError) as exc:
                failure = (
                    exc
                    if isinstance(exc, DeepSeekProviderError)
                    else DeepSeekProviderError(str(exc))
                )
                self._records.append(
                    ProviderCallRecord(
                        stage=stage,
                        model=self._model,
                        request_id=response.request_id,
                        request_sha256=request_sha256,
                        response_sha256=response_sha256,
                        duration_ms=duration_ms,
                        input_tokens=response.input_tokens,
                        output_tokens=response.output_tokens,
                        cache_hit_tokens=response.cache_hit_tokens,
                        transport_normalization=response.transport_normalization,
                        prompt_chars=prompt_chars,
                        schema_chars=len(serialized_schema),
                        schema_transport=schema_transport,
                        attempt=contract_attempt,
                        accepted=False,
                        rejection_reason=str(failure),
                    )
                )
                if contract_attempt > self._max_contract_repairs:
                    raise failure
                correction = str(failure)
                contract_attempt += 1
                continue
            self._records.append(
                ProviderCallRecord(
                    stage=stage,
                    model=self._model,
                    request_id=response.request_id,
                    request_sha256=request_sha256,
                    response_sha256=response_sha256,
                    duration_ms=duration_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    cache_hit_tokens=response.cache_hit_tokens,
                    transport_normalization=response.transport_normalization,
                    prompt_chars=prompt_chars,
                    schema_chars=len(serialized_schema),
                    schema_transport=schema_transport,
                    attempt=contract_attempt,
                )
            )
            return result
        raise AssertionError("unreachable bounded Director repair loop")

    def create_episode_direction(
        self,
        request: EpisodeRequest,
    ) -> EpisodeDirectionState:
        return self._call(
            stage="E0",
            contract_type=EpisodeDirectionState,
            approved_input={
                "director_id": self._director_id,
                "episode_request": asdict(request),
            },
        )

    def analyse_scene_phase_a(
        self,
        scene: SceneInput,
        episode_direction: EpisodeDirectionState,
    ) -> PhaseAResult:
        return self._call(
            stage="S1",
            contract_type=PhaseAResult,
            approved_input={
                "scene": asdict(scene),
                "episode_direction": asdict(episode_direction),
            },
        )

    def create_blocking_commit(
        self,
        scene: SceneInput,
        phase_a: PhaseAResult,
        k1_packet: DecisionPacket,
    ) -> BlockingCommit:
        return self._call(
            stage="B0",
            contract_type=BlockingCommit,
            approved_input={
                "scene": asdict(scene),
                "phase_a_blocking_scope": _blocking_phase_a_payload(phase_a),
                "expected_phase_a_fingerprint": _phase_a_fingerprint(phase_a),
                "k1_packet": _runtime_packet_payload(k1_packet),
            },
        )

    def design_phase_b(
        self,
        scene: SceneInput,
        phase_a: PhaseAResult,
        blocking_commit: BlockingCommit,
        k1_packet: DecisionPacket,
        k2_packet: DecisionPacket,
    ) -> PhaseBResult:
        execution_draft = self._call(
            stage="B1",
            contract_type=PhaseBExecutionDraft,
            approved_input={
                "scene": asdict(scene),
                "phase_a_execution_scope": _execution_phase_a_payload(phase_a),
                "phase_a_fingerprint": _phase_a_fingerprint(phase_a),
                "blocking_commit": asdict(blocking_commit),
                "blocking_commit_fingerprint": blocking_commit.fingerprint,
                "required_reference_bindings": _required_vec_reference_bindings(
                    scene,
                    blocking_commit,
                ),
                "k1_packet_lineage": _b1_k1_packet_payload(k1_packet),
                "k2_packet": _runtime_packet_payload(k2_packet),
                "approved_source_fact_hashes": (
                    _sha256_json(scene.cache_payload),
                    *(
                        hashlib.sha256(item.encode("utf-8")).hexdigest()
                        for item in scene.approved_context
                    ),
                ),
            },
            output_transform=lambda draft: materialize_phase_b_result(
                blocking_commit=blocking_commit,
                execution_draft=draft,
            ),
        )
        if not isinstance(execution_draft, PhaseBResult):
            raise AssertionError("B1 materialization did not return PhaseBResult")
        return execution_draft


__all__ = [
    "DEFAULT_DEEPSEEK_ENDPOINT",
    "DEFAULT_DEEPSEEK_MODEL",
    "DeepSeekDirectorProvider",
    "ClaudeCodeDeepSeekTextClient",
    "DeepSeekOpenAITextClient",
    "DeepSeekProviderError",
    "ProviderCallRecord",
    "TEXT_VALIDATED",
    "TextCompletionClient",
    "TextModelResponse",
]
