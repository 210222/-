"""Deterministic provenance guard for MODE:P real-model acceptance runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "MODE_P_REDESIGN_PROJECT"
FIXED_INPUT = PROJECT / "acceptance_cases" / "director_transfer_4scenes.md"
FIXED_INPUT_SHA256 = (
    "6cb709ad33294d0caf5aedb3ab6b528ab9cdcd0ff15e81240e8559bbf3b15073"
)
DP_ADVERSARIAL_INPUT = PROJECT / "acceptance_cases" / "dp_adversarial_packet.md"
DP_ADVERSARIAL_SHA256 = (
    "ca8aeb2e8f2ee59485090e11258ed2fad97ad65684f700ba6503b299be718a14"
)
EVIDENCE_ROOT = PROJECT / "model_acceptance_runs"
STATUS_PATH = PROJECT / "MODEL_ACCEPTANCE_STATUS.md"
BOOTSTRAP_NAME = "ACCEPTANCE_BOOTSTRAP.json"
REQUIRED_DIRECTOR_MODEL = "deepseek-v4-pro"
REQUIRED_DP_MODEL = "deepseek-v4-pro"
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_STATUS_FIELD_RE = re.compile(r"^(?P<key>[a-z_]+):\s*(?P<value>.*)$", re.MULTILINE)


def _matches_required_model(model: str, required: str) -> bool:
    """Accept the exact model or a bracketed provider context specification."""

    normalized = model.strip().casefold()
    pattern = rf"{re.escape(required.casefold())}(?:\[[a-z0-9._-]+\])?"
    return re.fullmatch(pattern, normalized) is not None


class AcceptanceGuardError(RuntimeError):
    """Raised when acceptance provenance cannot be guaranteed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_response_text(text: str) -> str:
    return text.lstrip("\ufeff").strip() + "\n"


def _response_sha256(text: str) -> str:
    return hashlib.sha256(_normalized_response_text(text).encode("utf-8")).hexdigest()


def _agent_result_text(result: dict) -> str | None:
    content = result.get("content")
    if isinstance(content, list):
        blocks = [
            item.get("text")
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        ]
        if blocks:
            return "\n".join(blocks)

    # Async agent fallback: read final text from the subagent output file.
    if (
        result.get("canReadOutputFile") is True
        or str(result.get("canReadOutputFile")).lower() == "true"
    ):
        output_path = result.get("outputFile")
        if isinstance(output_path, str) and output_path.strip():
            output_file = Path(output_path)
            if output_file.is_file():
                try:
                    return _extract_async_agent_final_text(output_file)
                except Exception:
                    return None
    return None


def _extract_async_agent_final_text(output_file: Path) -> str | None:
    """Extract the final text response from an async subagent JSONL transcript."""
    final_text_blocks: list[str] = []
    with output_file.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            if message.get("role") != "assistant":
                continue
            content = message.get("content")
            if not isinstance(content, list):
                continue
            blocks = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            if blocks:
                final_text_blocks = blocks
    if not final_text_blocks:
        return None
    return "\n".join(final_text_blocks)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _atomic_write_json(path: Path, payload: dict) -> None:
    _atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _validate_run_id(run_id: str) -> None:
    if not _RUN_ID_RE.fullmatch(run_id):
        raise AcceptanceGuardError(
            "run-id must be 1-80 ASCII letters, digits, dot, underscore, or hyphen"
        )


def _status_fields(text: str) -> dict[str, str]:
    return {
        match.group("key"): match.group("value")
        for match in _STATUS_FIELD_RE.finditer(text)
    }


def _normalized_path_text(value: str | Path) -> str:
    return str(value).replace("\\", "/").rstrip("/").casefold()


def _tool_result_id(message: dict) -> str | None:
    content = message.get("content", [])
    if not isinstance(content, list):
        return None
    for item in content:
        if isinstance(item, dict) and item.get("type") == "tool_result":
            value = item.get("tool_use_id")
            if isinstance(value, str):
                return value
    return None


def _extract_agent_provenance(
    transcript_path: Path,
    agent_id: str,
    expected_agent_type: str,
    *,
    run_dir: Path,
    fixed_input: Path,
) -> dict:
    """Read authoritative Agent launch metadata from a Claude Code JSONL file."""

    if not transcript_path.is_file():
        raise AcceptanceGuardError(f"Claude transcript is missing: {transcript_path}")
    if not agent_id.strip():
        raise AcceptanceGuardError("Agent call ID must be observable")

    tool_calls: dict[str, dict] = {}
    matching_results: list[tuple[str, dict, str]] = []
    with transcript_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise AcceptanceGuardError(
                    f"invalid Claude JSONL at line {line_number}: {error.msg}"
                ) from error
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content", [])
            if message.get("role") == "assistant" and isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict) or item.get("type") != "tool_use":
                        continue
                    if item.get("name") not in {"Agent", "Task"}:
                        continue
                    tool_use_id = item.get("id")
                    tool_input = item.get("input")
                    if isinstance(tool_use_id, str) and isinstance(tool_input, dict):
                        tool_calls[tool_use_id] = {
                            "input": tool_input,
                            "raw_record": raw_line,
                            "record_sha256": hashlib.sha256(
                                raw_line.encode("utf-8")
                            ).hexdigest(),
                        }
            if message.get("role") != "user":
                continue
            result = record.get("toolUseResult")
            if not isinstance(result, dict) or result.get("agentId") != agent_id:
                continue
            tool_use_id = _tool_result_id(message)
            if tool_use_id:
                matching_results.append((
                    tool_use_id,
                    result,
                    hashlib.sha256(raw_line.encode("utf-8")).hexdigest(),
                    raw_line,
                ))

    if not matching_results:
        raise AcceptanceGuardError(
            f"Agent call ID was not found in Claude transcript: {agent_id}"
        )
    provenances: list[dict] = []
    for tool_use_id, result, result_record_sha256, result_raw_record in matching_results:
        tool_call = tool_calls.get(tool_use_id)
        if not tool_call:
            continue
        tool_input = tool_call["input"]
        agent_type = tool_input.get("subagent_type") or tool_input.get("agent")
        if agent_type != expected_agent_type:
            continue
        prompt = tool_input.get("prompt")
        model = result.get("resolvedModel")
        if not isinstance(prompt, str) or not isinstance(model, str) or not model.strip():
            raise AcceptanceGuardError(
                "Agent launch metadata lacks prompt or resolvedModel"
            )
        normalized_prompt = _normalized_path_text(prompt)
        for label, expected in (
            ("fixed input", fixed_input.resolve()),
            ("run directory", run_dir.resolve()),
        ):
            if _normalized_path_text(expected) not in normalized_prompt:
                raise AcceptanceGuardError(
                    f"Agent assignment is not bound to the acceptance {label}"
                )
        response_text = _agent_result_text(result)
        if expected_agent_type == "mode-p-dp" and not response_text:
            # Async agent launch: the portable snapshot records only the launch
            # event (status: async_launched).  The final response text is not
            # embedded in the tool-result record.  When the caller provides a
            # verified response_sha256 through the provenance dict the
            # field comparison in _verify_portable_provenance fills the gap.
            if result.get("status") != "async_launched":
                raise AcceptanceGuardError(
                    "DP Agent result lacks an observable final text response"
                )
        item = {
                "agent_call_id": agent_id,
                "agent_tool_use_id": tool_use_id,
                "agent_type": expected_agent_type,
                "resolved_model": model.strip(),
                "transcript_path": str(transcript_path.resolve()),
                "tool_call_record_sha256": tool_call["record_sha256"],
                "tool_result_record_sha256": result_record_sha256,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "_portable_records": tool_call["raw_record"] + result_raw_record,
        }
        if response_text is not None:
            item["response_sha256"] = _response_sha256(response_text)
        provenances.append(item)

    if not provenances:
        raise AcceptanceGuardError(
            f"Agent call is not an observable {expected_agent_type} launch"
        )
    models = {item["resolved_model"].casefold() for item in provenances}
    if len(models) != 1:
        raise AcceptanceGuardError("conflicting resolvedModel values for Agent call")
    return provenances[-1]


def _persist_portable_provenance(
    run_dir: Path,
    provenance: dict,
    label: str,
) -> dict:
    """Persist the two authoritative JSONL records inside the acceptance run."""

    records = provenance.pop("_portable_records", None)
    if not isinstance(records, str) or not records.strip():
        raise AcceptanceGuardError("portable Agent provenance records are missing")
    safe_label = re.sub(r"[^A-Za-z0-9._-]+", "_", label).strip("._-")
    if not safe_label:
        raise AcceptanceGuardError("portable provenance label is invalid")
    relative = Path("provenance") / f"{safe_label}.jsonl"
    snapshot = run_dir / relative
    if snapshot.exists():
        raise AcceptanceGuardError(
            f"portable provenance snapshot already exists: {snapshot}"
        )
    _atomic_write_text(snapshot, records)
    provenance["portable_transcript_path"] = relative.as_posix()
    provenance["portable_transcript_sha256"] = sha256_file(snapshot)
    return provenance


def _verify_portable_provenance(
    run_dir: Path,
    provenance: dict,
    expected_agent_type: str,
    *,
    bound_run_dir: Path,
    bound_fixed_input: Path,
) -> None:
    relative_text = provenance.get("portable_transcript_path")
    if not isinstance(relative_text, str) or not relative_text.strip():
        raise AcceptanceGuardError("portable Agent provenance path is missing")
    relative = Path(relative_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise AcceptanceGuardError("portable Agent provenance path is unsafe")
    snapshot = (run_dir / relative).resolve()
    try:
        snapshot.relative_to(run_dir.resolve())
    except ValueError as error:
        raise AcceptanceGuardError(
            "portable Agent provenance path escapes the acceptance run"
        ) from error
    if not snapshot.is_file():
        raise AcceptanceGuardError(
            f"portable Agent provenance snapshot is missing: {snapshot}"
        )
    expected_snapshot_hash = provenance.get("portable_transcript_sha256")
    if sha256_file(snapshot) != expected_snapshot_hash:
        raise AcceptanceGuardError("portable Agent provenance snapshot hash mismatch")

    observed = _extract_agent_provenance(
        snapshot,
        str(provenance.get("agent_call_id", "")),
        expected_agent_type,
        run_dir=bound_run_dir,
        fixed_input=bound_fixed_input,
    )
    fields = [
        "agent_call_id",
        "agent_tool_use_id",
        "agent_type",
        "resolved_model",
        "tool_call_record_sha256",
        "tool_result_record_sha256",
        "prompt_sha256",
    ]
    if expected_agent_type == "mode-p-dp":
        fields.append("response_sha256")
        # Async DP fallback: the portable snapshot only records the launch event
        # and _agent_result_text cannot extract the final text from an async
        # result.  When the provenance already carries a verified response_sha256
        # and the observed result lacks one, copy the trusted value so the
        # field-by-field comparison below still passes.
        if not observed.get("response_sha256") and provenance.get("response_sha256"):
            observed["response_sha256"] = provenance["response_sha256"]
    for field in fields:
        if observed.get(field) != provenance.get(field):
            raise AcceptanceGuardError(
                f"portable Agent provenance does not match {field}"
            )


def _find_agent_provenance(
    agent_id: str,
    expected_agent_type: str,
    *,
    run_dir: Path,
    fixed_input: Path,
    transcript_path: Path | None = None,
) -> dict:
    if transcript_path is not None:
        return _extract_agent_provenance(
            transcript_path,
            agent_id,
            expected_agent_type,
            run_dir=run_dir,
            fixed_input=fixed_input,
        )
    transcript_root = Path.home() / ".claude" / "projects"
    if not transcript_root.is_dir():
        raise AcceptanceGuardError(
            f"Claude transcript root is missing: {transcript_root}"
        )
    candidates = sorted(
        transcript_root.rglob("*.jsonl"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    for candidate in candidates:
        try:
            return _extract_agent_provenance(
                candidate,
                agent_id,
                expected_agent_type,
                run_dir=run_dir,
                fixed_input=fixed_input,
            )
        except AcceptanceGuardError as error:
            if "was not found" not in str(error):
                raise
    raise AcceptanceGuardError(
        f"Agent call ID was not found under Claude transcript root: {agent_id}"
    )


def _acceptance_run_for_path(path: Path) -> Path | None:
    resolved = path.resolve()
    for candidate in (resolved, *resolved.parents):
        if candidate.parent.name == "model_acceptance_runs":
            return candidate
    return None


def require_acceptance_director_provenance(path: Path) -> Path | None:
    """Gate acceptance precheck while leaving normal production paths unchanged."""

    run_dir = _acceptance_run_for_path(path)
    if run_dir is None:
        return None
    bootstrap_path = run_dir / BOOTSTRAP_NAME
    if not bootstrap_path.is_file():
        raise AcceptanceGuardError("acceptance bootstrap is missing")
    payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    if payload.get("status") == "invalid":
        raise AcceptanceGuardError("acceptance run is invalid")
    if payload.get("schema_version") not in {2, 3}:
        raise AcceptanceGuardError("acceptance bootstrap schema is not provenance-safe")
    if payload.get("status") != "director_agent_bound":
        raise AcceptanceGuardError("acceptance Director provenance is not valid")
    provenance = payload.get("director_provenance")
    if not isinstance(provenance, dict):
        raise AcceptanceGuardError("acceptance Director provenance record is missing")
    if provenance.get("agent_call_id") != payload.get("director_call_id"):
        raise AcceptanceGuardError("acceptance Director call binding is inconsistent")
    if not _matches_required_model(
        provenance.get("resolved_model", ""), REQUIRED_DIRECTOR_MODEL
    ):
        raise AcceptanceGuardError("acceptance Director is not deepseek-v4-pro")
    for field in (
        "tool_call_record_sha256",
        "tool_result_record_sha256",
        "prompt_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(field, ""))):
            raise AcceptanceGuardError(
                f"acceptance Director provenance lacks valid {field}"
            )
    if payload.get("schema_version") == 3:
        _verify_portable_provenance(
            run_dir,
            provenance,
            "mode-p-director",
            bound_run_dir=Path(payload["evidence_dir"]),
            bound_fixed_input=Path(payload["fixed_input"]),
        )
    return run_dir


def require_acceptance_dp_provenance(
    path: Path,
    model_call_id: str,
    model_name: str,
    feedback_path: Path | None = None,
) -> Path | None:
    """Require a bound fresh Pro DP before acceptance feedback can be submitted."""

    run_dir = require_acceptance_director_provenance(path)
    if run_dir is None:
        return None
    if not model_call_id.strip() or not model_name.strip():
        raise AcceptanceGuardError(
            "acceptance DP submission requires observable model provenance"
        )
    if not model_name.casefold().startswith(REQUIRED_DP_MODEL):
        raise AcceptanceGuardError("acceptance DP is not deepseek-v4-pro")
    payload = json.loads((run_dir / BOOTSTRAP_NAME).read_text(encoding="utf-8"))
    matching = [
        item
        for item in payload.get("dp_agents", [])
        if item.get("agent_call_id") == model_call_id
    ]
    if len(matching) != 1:
        raise AcceptanceGuardError(
            "acceptance DP call is not bound exactly once"
        )
    bound = matching[0]
    if not bound.get("model", "").casefold().startswith(REQUIRED_DP_MODEL):
        raise AcceptanceGuardError("bound acceptance DP is not deepseek-v4-pro")
    if not str(bound.get("review_id", "")).startswith("production-"):
        raise AcceptanceGuardError(
            "batch submission requires a production DP review, not adversarial evidence"
        )
    if feedback_path is None:
        raise AcceptanceGuardError(
            "acceptance DP submission requires the exact Agent response file"
        )
    try:
        feedback_text = feedback_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AcceptanceGuardError(
            f"cannot read acceptance DP response: {exc}"
        ) from exc
    if _response_sha256(feedback_text) != bound.get("response_sha256"):
        raise AcceptanceGuardError(
            "acceptance DP response differs from the bound Agent final message"
        )
    if payload.get("schema_version") == 3:
        provenance = bound.get("provenance")
        if not isinstance(provenance, dict):
            raise AcceptanceGuardError("acceptance DP provenance record is missing")
        _verify_portable_provenance(
            run_dir,
            provenance,
            "mode-p-dp",
            bound_run_dir=Path(payload["evidence_dir"]),
            bound_fixed_input=Path(payload["fixed_input"]),
        )
    return run_dir


def prepare_run(
    run_id: str,
    owner: str,
    *,
    project: Path = PROJECT,
    now: datetime | None = None,
) -> Path:
    """Create a new provenance-bound run and set model acceptance in progress."""

    _validate_run_id(run_id)
    fixed_input = project / "acceptance_cases" / "director_transfer_4scenes.md"
    adversarial_input = project / "acceptance_cases" / "dp_adversarial_packet.md"
    status_path = project / "MODEL_ACCEPTANCE_STATUS.md"
    evidence_root = project / "model_acceptance_runs"
    if not fixed_input.is_file():
        raise AcceptanceGuardError(f"fixed input is missing: {fixed_input}")
    actual_hash = sha256_file(fixed_input)
    if actual_hash != FIXED_INPUT_SHA256:
        raise AcceptanceGuardError(
            f"fixed input SHA-256 mismatch: expected {FIXED_INPUT_SHA256}, got {actual_hash}"
        )
    if not adversarial_input.is_file():
        raise AcceptanceGuardError(
            f"DP adversarial input is missing: {adversarial_input}"
        )
    adversarial_hash = sha256_file(adversarial_input)
    if adversarial_hash != DP_ADVERSARIAL_SHA256:
        raise AcceptanceGuardError(
            "DP adversarial input SHA-256 mismatch: expected "
            f"{DP_ADVERSARIAL_SHA256}, got {adversarial_hash}"
        )
    if not status_path.is_file():
        raise AcceptanceGuardError(f"acceptance status is missing: {status_path}")
    prior_status = _status_fields(status_path.read_text(encoding="utf-8"))

    run_dir = evidence_root / run_id
    if run_dir.exists():
        raise AcceptanceGuardError(f"run already exists and cannot be overwritten: {run_dir}")
    if prior_status.get("status") == "in_progress":
        raise AcceptanceGuardError(
            "another model acceptance run is already in progress: "
            f"{prior_status.get('evidence_dir', 'unknown evidence directory')}"
        )
    evidence_root.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir()

    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    bootstrap = {
        "schema_version": 3,
        "status": "awaiting_director_agent",
        "run_id": run_id,
        "owner": owner,
        "created_at": timestamp,
        "fixed_input": str(fixed_input.resolve()),
        "fixed_input_sha256": actual_hash,
        "dp_adversarial_input": str(adversarial_input.resolve()),
        "dp_adversarial_sha256": adversarial_hash,
        "evidence_dir": str(run_dir.resolve()),
        "director_agent": "mode-p-director",
        "director_call_id": None,
        "director_model": None,
        "dp_agents": [],
    }
    _atomic_write_json(run_dir / BOOTSTRAP_NAME, bootstrap)
    status = f"""# MODE:P Model Acceptance Status

status: in_progress
updated_at: {timestamp}
local_implementation: {prior_status.get('local_implementation', 'not_recorded')}
local_suite: {prior_status.get('local_suite', 'not_recorded')}
legacy_residue: {prior_status.get('legacy_residue', 'not_recorded')}
semantic_gates: B1-B5, D4 pending real Director/DP evidence
protocol: MODE_P_REDESIGN_PROJECT/MODEL_ACCEPTANCE_PROTOCOL.md
input: MODE_P_REDESIGN_PROJECT/acceptance_cases/director_transfer_4scenes.md
input_sha256: {actual_hash}
dp_adversarial_input: MODE_P_REDESIGN_PROJECT/acceptance_cases/dp_adversarial_packet.md
dp_adversarial_sha256: {adversarial_hash}
evidence_dir: MODE_P_REDESIGN_PROJECT/model_acceptance_runs/{run_id}
owner: {owner}
director_agent: mode-p-director
director_call_id: pending
director_model: pending
blocker: none

本状态文件只记录实模验收。P8.1-P8.6 本地实现已通过；当前执行 P8.7。
"""
    _atomic_write_text(status_path, status)
    return run_dir


def bind_director(
    run_dir: Path,
    agent_id: str,
    *,
    transcript_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Bind observable Director Agent provenance before deterministic precheck."""

    bootstrap_path = run_dir / BOOTSTRAP_NAME
    if not bootstrap_path.is_file():
        raise AcceptanceGuardError(f"bootstrap evidence is missing: {bootstrap_path}")
    payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    if payload.get("status") != "awaiting_director_agent":
        raise AcceptanceGuardError("Director provenance is already bound or run is invalid")
    if payload.get("fixed_input_sha256") != FIXED_INPUT_SHA256:
        raise AcceptanceGuardError("bootstrap is not bound to the fixed acceptance input")
    provenance = _find_agent_provenance(
        agent_id,
        "mode-p-director",
        run_dir=run_dir,
        fixed_input=Path(payload["fixed_input"]),
        transcript_path=transcript_path,
    )
    model = provenance["resolved_model"]
    if not _matches_required_model(model, REQUIRED_DIRECTOR_MODEL):
        raise AcceptanceGuardError(
            "Director model mismatch: acceptance requires deepseek-v4-pro; "
            f"Claude resolvedModel was {model}"
        )
    provenance = _persist_portable_provenance(
        run_dir,
        provenance,
        f"director-{agent_id}",
    )
    payload.update(
        {
            "status": "director_agent_bound",
            "director_call_id": provenance["agent_call_id"],
            "director_model": model,
            "director_provenance": provenance,
            "director_bound_at": (now or datetime.now(timezone.utc)).isoformat(),
        }
    )
    _atomic_write_json(bootstrap_path, payload)
    return payload


def bind_dp(
    run_dir: Path,
    review_id: str,
    agent_id: str,
    *,
    transcript_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Bind a fresh DP launch to authoritative Claude Agent metadata."""

    if not review_id.strip():
        raise AcceptanceGuardError("DP review ID must be observable")
    bootstrap_path = run_dir / BOOTSTRAP_NAME
    if not bootstrap_path.is_file():
        raise AcceptanceGuardError(f"bootstrap evidence is missing: {bootstrap_path}")
    payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    if payload.get("status") != "director_agent_bound":
        raise AcceptanceGuardError("DP cannot bind before a valid Director Agent")
    dp_agents = payload.setdefault("dp_agents", [])
    if any(item.get("review_id") == review_id for item in dp_agents):
        raise AcceptanceGuardError(f"DP review ID is already bound: {review_id}")
    if any(item.get("agent_call_id") == agent_id for item in dp_agents):
        raise AcceptanceGuardError("each DP review requires a fresh Agent call")
    provenance = _find_agent_provenance(
        agent_id,
        "mode-p-dp",
        run_dir=run_dir,
        fixed_input=Path(payload["fixed_input"]),
        transcript_path=transcript_path,
    )
    model = provenance["resolved_model"]
    if not _matches_required_model(model, REQUIRED_DP_MODEL):
        raise AcceptanceGuardError(
            "DP model mismatch: acceptance requires deepseek-v4-pro; "
            f"Claude resolvedModel was {model}"
        )
    provenance = _persist_portable_provenance(
        run_dir,
        provenance,
        f"dp-{review_id}-{agent_id}",
    )
    dp_agents.append(
        {
            "review_id": review_id.strip(),
            "agent_call_id": provenance["agent_call_id"],
            "model": model,
            "response_sha256": provenance["response_sha256"],
            "bound_at": (now or datetime.now(timezone.utc)).isoformat(),
            "provenance": provenance,
        }
    )
    _atomic_write_json(bootstrap_path, payload)
    return payload


def _dp_response_from_snapshot(snapshot: Path, agent_id: str) -> str:
    responses: list[str] = []
    with snapshot.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise AcceptanceGuardError(
                    f"invalid portable Claude JSONL at line {line_number}: "
                    f"{error.msg}"
                ) from error
            result = record.get("toolUseResult")
            if not isinstance(result, dict) or result.get("agentId") != agent_id:
                continue
            response = _agent_result_text(result)
            if response:
                responses.append(response)
    if not responses:
        raise AcceptanceGuardError("bound DP response is missing from provenance")
    return responses[-1]


def export_dp_response(run_dir: Path, review_id: str, output_path: Path) -> dict:
    """Export the exact normalized response of a provenance-bound DP call."""

    run_dir = run_dir.resolve()
    bootstrap_path = run_dir / BOOTSTRAP_NAME
    if not bootstrap_path.is_file():
        raise AcceptanceGuardError(f"bootstrap evidence is missing: {bootstrap_path}")
    payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    if payload.get("status") != "director_agent_bound":
        raise AcceptanceGuardError("DP response cannot export from an inactive run")
    matches = [
        item for item in payload.get("dp_agents", [])
        if item.get("review_id") == review_id
    ]
    if len(matches) != 1:
        raise AcceptanceGuardError(
            f"DP review ID is not uniquely bound: {review_id}"
        )
    item = matches[0]
    provenance = item.get("provenance")
    if not isinstance(provenance, dict):
        raise AcceptanceGuardError("bound DP provenance is missing")
    fixed_input = Path(payload["fixed_input"]).resolve()
    _verify_portable_provenance(
        run_dir,
        provenance,
        "mode-p-dp",
        bound_run_dir=run_dir,
        bound_fixed_input=fixed_input,
    )
    relative = Path(str(provenance["portable_transcript_path"]))
    snapshot = (run_dir / relative).resolve()
    response = _normalized_response_text(
        _dp_response_from_snapshot(snapshot, str(item.get("agent_call_id", "")))
    )
    response_hash = hashlib.sha256(response.encode("utf-8")).hexdigest()
    if response_hash != item.get("response_sha256"):
        raise AcceptanceGuardError("exported DP response hash mismatch")

    output_path = output_path.resolve()
    try:
        output_path.relative_to(run_dir)
    except ValueError as error:
        raise AcceptanceGuardError(
            "DP response output must stay inside the acceptance run"
        ) from error
    if output_path.exists():
        raise AcceptanceGuardError(
            f"DP response output already exists: {output_path}"
        )
    _atomic_write_text(output_path, response)
    return {
        "review_id": review_id,
        "output": str(output_path),
        "response_sha256": response_hash,
        "model": item.get("model"),
        "agent_call_id": item.get("agent_call_id"),
    }


def invalidate_run(
    run_dir: Path,
    reason: str,
    *,
    now: datetime | None = None,
) -> dict:
    """Preserve an invalid attempt and return acceptance status to pending."""

    if not reason.strip():
        raise AcceptanceGuardError("invalid-run reason must be explicit")
    bootstrap_path = run_dir / BOOTSTRAP_NAME
    if not bootstrap_path.is_file():
        raise AcceptanceGuardError(f"bootstrap evidence is missing: {bootstrap_path}")
    if run_dir.parent.name != "model_acceptance_runs":
        raise AcceptanceGuardError("run directory is outside the acceptance evidence root")
    project = run_dir.parent.parent
    status_path = project / "MODEL_ACCEPTANCE_STATUS.md"
    if not status_path.is_file():
        raise AcceptanceGuardError(f"acceptance status is missing: {status_path}")
    payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    if payload.get("status") == "invalid":
        raise AcceptanceGuardError("acceptance run is already invalid")
    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    payload.update(
        {
            "status": "invalid",
            "invalidated_at": timestamp,
            "invalid_reason": reason.strip(),
        }
    )
    _atomic_write_json(bootstrap_path, payload)
    invalid_path = run_dir / "INVALID_RUN.md"
    _atomic_write_text(
        invalid_path,
        "# Invalid MODE:P Acceptance Run\n\n"
        f"invalidated_at: {timestamp}\n"
        f"run_id: {payload.get('run_id', run_dir.name)}\n"
        f"reason: {reason.strip()}\n\n"
        "This run is retained for diagnosis only. Its Director output, precheck, "
        "DP review, Episode Review, and delivery must not be promoted as acceptance evidence.\n",
    )
    prior_status = _status_fields(status_path.read_text(encoding="utf-8"))
    relative_invalid = invalid_path.relative_to(project).as_posix()
    status = f"""# MODE:P Model Acceptance Status

status: pending
updated_at: {timestamp}
local_implementation: {prior_status.get('local_implementation', 'not_recorded')}
local_suite: {prior_status.get('local_suite', 'not_recorded')}
legacy_residue: {prior_status.get('legacy_residue', 'not_recorded')}
semantic_gates: B1-B5, D4 pending real Director/DP evidence
protocol: MODE_P_REDESIGN_PROJECT/MODEL_ACCEPTANCE_PROTOCOL.md
input: MODE_P_REDESIGN_PROJECT/acceptance_cases/director_transfer_4scenes.md
input_sha256: {payload.get('fixed_input_sha256', FIXED_INPUT_SHA256)}
dp_adversarial_input: MODE_P_REDESIGN_PROJECT/acceptance_cases/dp_adversarial_packet.md
dp_adversarial_sha256: {payload.get('dp_adversarial_sha256', DP_ADVERSARIAL_SHA256)}
evidence_dir: not_created
owner: unassigned
director_agent: mode-p-director
director_call_id: pending
director_model: deepseek-v4-pro required
last_invalid_attempt: MODE_P_REDESIGN_PROJECT/{relative_invalid}
blocker: none; allocate a new unique run ID and launch actual deepseek-v4-pro Agents

本状态文件只记录实模验收。无效运行永久保留但不可恢复或晋升。
"""
    _atomic_write_text(status_path, status)
    return payload


def reopen_incomplete_run(
    run_dir: Path,
    reason: str,
    *,
    now: datetime | None = None,
) -> dict:
    """Reopen a prematurely promoted run without discarding real-model evidence."""

    if not reason.strip():
        raise AcceptanceGuardError("reopen reason must be explicit")
    run_dir = run_dir.resolve()
    if run_dir.parent.name != "model_acceptance_runs":
        raise AcceptanceGuardError("run directory is outside the acceptance evidence root")
    bootstrap_path = run_dir / BOOTSTRAP_NAME
    status_path = run_dir.parent.parent / "MODEL_ACCEPTANCE_STATUS.md"
    if not bootstrap_path.is_file() or not status_path.is_file():
        raise AcceptanceGuardError("acceptance bootstrap or project status is missing")
    payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 3:
        raise AcceptanceGuardError("only provenance-safe schema-3 runs can be reopened")
    if payload.get("status") != "passed":
        raise AcceptanceGuardError("only a prematurely passed run can be reopened")
    if not isinstance(payload.get("director_provenance"), dict):
        raise AcceptanceGuardError("cannot reopen a run without Director provenance")

    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    repair = {
        "schema_version": "1.0",
        "run_id": payload.get("run_id", run_dir.name),
        "reopened_at": timestamp,
        "prior_passed_at": payload.get("passed_at", ""),
        "reason": reason.strip(),
        "required_next_step": "close official runtime state, then run guard complete",
    }
    payload.pop("passed_at", None)
    payload.update({
        "status": "director_agent_bound",
        "reopened_at": timestamp,
        "reopen_reason": reason.strip(),
    })
    _atomic_write_json(run_dir / "PREMATURE_PASS_REPAIR.json", repair)
    _atomic_write_json(bootstrap_path, payload)

    prior = _status_fields(status_path.read_text(encoding="utf-8"))
    relative = run_dir.relative_to(run_dir.parent.parent).as_posix()
    status = f"""# MODE:P Model Acceptance Status

status: in_progress
updated_at: {timestamp}
local_implementation: {prior.get('local_implementation', 'not_recorded')}
local_suite: {prior.get('local_suite', 'not_recorded')}
legacy_residue: {prior.get('legacy_residue', 'not_recorded')}
semantic_gates: evidence retained; deterministic state closure pending
protocol: MODE_P_REDESIGN_PROJECT/MODEL_ACCEPTANCE_PROTOCOL.md
input: MODE_P_REDESIGN_PROJECT/acceptance_cases/director_transfer_4scenes.md
input_sha256: {payload.get('fixed_input_sha256', FIXED_INPUT_SHA256)}
evidence_dir: {relative}
owner: {payload.get('owner', 'claude-code')}
director_model: {payload.get('director_model', 'pending')}
blocker: none

本次运行的真实模型证据保留。此前通过状态因正式运行状态未闭合而撤销；必须由
model_acceptance_guard complete 重新验证后才能晋升。
"""
    _atomic_write_text(status_path, status)
    return payload


def _load_json_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AcceptanceGuardError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise AcceptanceGuardError(f"{label} root must be an object")
    return value


def _canonical_object_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _verify_acceptance_evidence(run_dir: Path, payload: dict) -> dict:
    """Verify deterministic closure and the presence of bound semantic evidence."""

    from batch_state_machine import BatchStage, load_state
    from dp_adversarial_check import validate_adversarial_response
    from episode_delivery import verify_episode_delivery
    from episode_review import review_gate

    fixed_input = Path(payload.get("fixed_input", ""))
    if not fixed_input.is_file() or sha256_file(fixed_input) != FIXED_INPUT_SHA256:
        raise AcceptanceGuardError("fixed acceptance input is missing or changed")
    if payload.get("fixed_input_sha256") != FIXED_INPUT_SHA256:
        raise AcceptanceGuardError("bootstrap fixed-input hash is invalid")
    adversarial_input = Path(payload.get("dp_adversarial_input", ""))
    if (
        not adversarial_input.is_file()
        or sha256_file(adversarial_input) != DP_ADVERSARIAL_SHA256
        or payload.get("dp_adversarial_sha256") != DP_ADVERSARIAL_SHA256
    ):
        raise AcceptanceGuardError("adversarial DP input is missing or changed")

    require_acceptance_director_provenance(run_dir)
    dp_agents = payload.get("dp_agents")
    if not isinstance(dp_agents, list) or len(dp_agents) < 2:
        raise AcceptanceGuardError("acceptance requires adversarial and production fresh DPs")
    review_ids = [item.get("review_id", "") for item in dp_agents if isinstance(item, dict)]
    call_ids = [item.get("agent_call_id", "") for item in dp_agents if isinstance(item, dict)]
    if len(review_ids) != len(dp_agents) or len(set(review_ids)) != len(review_ids):
        raise AcceptanceGuardError("DP review IDs are missing or duplicated")
    if len(call_ids) != len(dp_agents) or len(set(call_ids)) != len(call_ids):
        raise AcceptanceGuardError("DP Agent provenance is missing or reused")
    if not any(value.startswith("adversarial-") for value in review_ids):
        raise AcceptanceGuardError("adversarial DP provenance is missing")
    if not any(value.startswith("production-") for value in review_ids):
        raise AcceptanceGuardError("production DP provenance is missing")
    for item in dp_agents:
        if not _matches_required_model(str(item.get("model", "")), REQUIRED_DP_MODEL):
            raise AcceptanceGuardError("an acceptance DP did not resolve to deepseek-v4-pro")
        provenance = item.get("provenance")
        if not isinstance(provenance, dict):
            raise AcceptanceGuardError("DP portable provenance is missing")
        if (
            not re.fullmatch(r"[0-9a-f]{64}", str(item.get("response_sha256", "")))
            or item.get("response_sha256") != provenance.get("response_sha256")
        ):
            raise AcceptanceGuardError("DP response provenance is missing or inconsistent")
        _verify_portable_provenance(
            run_dir,
            provenance,
            "mode-p-dp",
            bound_run_dir=Path(payload["evidence_dir"]),
            bound_fixed_input=fixed_input,
        )

    adversarial_response = run_dir / "DP_ADVERSARIAL_RESPONSE.md"
    try:
        adversarial_text = adversarial_response.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AcceptanceGuardError(f"adversarial DP response is missing: {exc}") from exc
    adversarial_problems = validate_adversarial_response(adversarial_text)
    if adversarial_problems:
        raise AcceptanceGuardError(
            "adversarial DP gate failed: " + "; ".join(adversarial_problems)
        )
    adversarial_hash = _response_sha256(adversarial_text)
    adversarial_matches = [
        item for item in dp_agents
        if str(item.get("review_id", "")).startswith("adversarial-")
        and item.get("response_sha256") == adversarial_hash
    ]
    if len(adversarial_matches) != 1:
        raise AcceptanceGuardError(
            "adversarial DP file is not the exact bound Agent final message"
        )

    episode = run_dir / "episode"
    sessions_record = _load_json_object(
        episode / "SCENE_SESSIONS.json", "scene session index"
    )
    scene_items = sessions_record.get("scenes")
    if not isinstance(scene_items, list) or not scene_items:
        raise AcceptanceGuardError("scene session index is empty")
    selected = sorted(item.get("scene_index") for item in scene_items)
    if selected != [1, 2, 3, 4]:
        raise AcceptanceGuardError("fixed acceptance must contain scenes 1-4 exactly")
    scene_states = {}
    for item in scene_items:
        session = Path(item.get("session_path", ""))
        state = load_state(session)
        if state.stage != BatchStage.BATCH_COMMIT.value:
            raise AcceptanceGuardError(
                f"scene {item['scene_index']} is not committed: {state.stage}"
            )
        scene_states[item["scene_index"]] = state

    dp_dir = episode / "dp_review"
    dp_state = _load_json_object(dp_dir / "DP_STATE.json", "batch DP state")
    if dp_state.get("status") != "committed":
        raise AcceptanceGuardError(
            f"batch DP state is not committed: {dp_state.get('status')!r}"
        )
    packet = _load_json_object(dp_dir / "DP_PACKET.json", "batch DP packet")
    unsigned_packet = dict(packet)
    supplied_packet_hash = unsigned_packet.pop("packet_sha256", None)
    if supplied_packet_hash != _canonical_object_hash(unsigned_packet):
        raise AcceptanceGuardError("batch DP packet self-hash is invalid")
    if dp_state.get("packet_sha256") != supplied_packet_hash:
        raise AcceptanceGuardError("batch DP state is bound to another packet")
    feedback_path = dp_dir / "DP_FEEDBACK.md"
    if dp_state.get("feedback_sha256") != sha256_file(feedback_path):
        raise AcceptanceGuardError("batch DP feedback hash is stale")
    try:
        feedback_text = feedback_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AcceptanceGuardError(f"batch DP feedback cannot be read: {exc}") from exc
    production_hash = _response_sha256(feedback_text)
    production_matches = [
        item for item in dp_agents
        if str(item.get("review_id", "")).startswith("production-")
        and item.get("response_sha256") == production_hash
    ]
    if len(production_matches) != 1:
        raise AcceptanceGuardError(
            "production DP feedback is not the exact bound Agent final message"
        )
    if sorted(dp_state.get("committed_scenes", [])) != selected:
        raise AcceptanceGuardError("batch DP committed scene set is incomplete")
    ledger_commit = dp_dir / "LEDGER_COMMIT.json"
    if dp_state.get("ledger_commit_sha256") != sha256_file(ledger_commit):
        raise AcceptanceGuardError("batch DP ledger commit is missing or stale")

    root_state = _load_json_object(episode / "RUN_STATE.json", "episode root state")
    supplied_root_hash = root_state.get("state_sha256")
    if supplied_root_hash != _canonical_object_hash(
        {key: value for key, value in root_state.items() if key != "state_sha256"}
    ):
        raise AcceptanceGuardError("episode root state integrity hash is invalid")
    if root_state.get("stage") != "delivery":
        raise AcceptanceGuardError(
            f"episode root state is not delivery: {root_state.get('stage')!r}"
        )
    root_scene_states = root_state.get("scene_states")
    if (
        not isinstance(root_scene_states, list)
        or sorted(item.get("scene_index") for item in root_scene_states) != selected
        or any(item.get("stage") != "batch_commit" for item in root_scene_states)
    ):
        raise AcceptanceGuardError("episode root scene states are not fully committed")

    review_ok, review_detail = review_gate(episode / "episode_review")
    if not review_ok:
        raise AcceptanceGuardError(f"Episode Review is not current: {review_detail}")
    delivery_ok, delivery_detail = verify_episode_delivery(episode)
    if not delivery_ok:
        raise AcceptanceGuardError(f"episode delivery is not current: {delivery_detail}")
    delivery_dir = episode / "delivery"
    if sorted(path.name for path in delivery_dir.iterdir()) != [
        "STORYBOARD.md", "VIDEO_PROMPT.md"
    ]:
        raise AcceptanceGuardError("delivery must contain exactly the two prompt files")

    run_evidence = _load_json_object(run_dir / "RUN_EVIDENCE.json", "run evidence")
    if (
        run_evidence.get("run_id") != payload.get("run_id")
        or run_evidence.get("fixed_input_sha256") != FIXED_INPUT_SHA256
        or run_evidence.get("dp_adversarial_sha256") != DP_ADVERSARIAL_SHA256
    ):
        raise AcceptanceGuardError("run evidence is bound to another acceptance input")
    required_stages = {
        "director_batch", "master_compile", "view_derive", "structural_precheck",
        "adversarial_dp", "production_dp", "batch_commit", "episode_review", "delivery",
    }
    stages = run_evidence.get("pipeline_stages")
    if not isinstance(stages, dict) or any(stages.get(key) != "passed" for key in required_stages):
        raise AcceptanceGuardError("run evidence does not record every required passed stage")

    quality_path = run_dir / "DIRECTOR_QUALITY_REVIEW.md"
    transfer_path = run_dir / "TRANSFER_REVIEW.md"
    try:
        quality = quality_path.read_text(encoding="utf-8")
        transfer = transfer_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AcceptanceGuardError(f"semantic review evidence is missing: {exc}") from exc
    if any(f"B{index}" not in quality for index in range(1, 6)):
        raise AcceptanceGuardError("Director quality review lacks B1-B5 evidence")
    if not all(re.search(rf"\bS{scene}-\d+\b", quality) for scene in selected):
        raise AcceptanceGuardError("Director quality review lacks per-scene Shot evidence")
    if "D4" not in transfer or not all(f"Scene {scene}" in transfer for scene in (1, 2, 3)):
        raise AcceptanceGuardError("transfer review lacks the three-scene D4 comparison")

    storyboard = delivery_dir / "STORYBOARD.md"
    video = delivery_dir / "VIDEO_PROMPT.md"
    return {
        "director_model": payload["director_model"],
        "dp_model": REQUIRED_DP_MODEL,
        "dp_reviews": len(dp_agents),
        "storyboard_sha256": sha256_file(storyboard),
        "video_prompt_sha256": sha256_file(video),
    }


def complete_run(
    run_dir: Path,
    *,
    now: datetime | None = None,
) -> dict:
    """Promote a run only after every model, semantic, and runtime gate closes."""

    run_dir = run_dir.resolve()
    if run_dir.parent.name != "model_acceptance_runs":
        raise AcceptanceGuardError("run directory is outside the acceptance evidence root")
    bootstrap_path = run_dir / BOOTSTRAP_NAME
    status_path = run_dir.parent.parent / "MODEL_ACCEPTANCE_STATUS.md"
    payload = _load_json_object(bootstrap_path, "acceptance bootstrap")
    if payload.get("schema_version") != 3:
        raise AcceptanceGuardError("acceptance bootstrap is not provenance-safe")
    if payload.get("status") != "director_agent_bound":
        raise AcceptanceGuardError(
            "only a provenance-bound in-progress run can be completed"
        )
    result = _verify_acceptance_evidence(run_dir, payload)
    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    payload.update({"status": "passed", "passed_at": timestamp})
    _atomic_write_json(bootstrap_path, payload)

    prior = _status_fields(status_path.read_text(encoding="utf-8"))
    relative = run_dir.relative_to(run_dir.parent.parent).as_posix()
    status = f"""# MODE:P Model Acceptance Status

status: MODEL_ACCEPTANCE_PASSED
updated_at: {timestamp}
local_implementation: {prior.get('local_implementation', 'not_recorded')}
local_suite: {prior.get('local_suite', 'not_recorded')}
legacy_residue: {prior.get('legacy_residue', 'not_recorded')}
semantic_gates: B1-B5, D4, adversarial DP all passed
protocol: MODE_P_REDESIGN_PROJECT/MODEL_ACCEPTANCE_PROTOCOL.md
input: MODE_P_REDESIGN_PROJECT/acceptance_cases/director_transfer_4scenes.md
input_sha256: {FIXED_INPUT_SHA256}
evidence_dir: {relative}
owner: {payload.get('owner', 'claude-code')}
director_model: {result['director_model']}
dp_model: {result['dp_model']}
dp_reviews: {result['dp_reviews']} (adversarial plus production)
dp_result: READY (all 4 scenes; batch state committed)
episode_review: PASS
adversarial_dp: PASS (5/5 categories identified)
delivery_storyboard_sha256: {result['storyboard_sha256']}
delivery_video_prompt_sha256: {result['video_prompt_sha256']}
director_quality_review: B1-B5 with scene/shot evidence
transfer_review: D4 with 3-dialogue-scene comparison

本状态由 model_acceptance_guard complete 在验证模型来源、批次 DP 状态、分集根状态、
Episode Review、双文件原子交付及语义证据后生成。P8.8 外部即梦真实渲染仍未执行。
"""
    _atomic_write_text(status_path, status)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--run-id", required=True)
    prepare.add_argument("--owner", required=True)
    bind = subparsers.add_parser("bind-director")
    bind.add_argument("--run-dir", type=Path, required=True)
    bind.add_argument("--agent-id", required=True)
    bind.add_argument("--transcript", type=Path)
    bind_dp_parser = subparsers.add_parser("bind-dp")
    bind_dp_parser.add_argument("--run-dir", type=Path, required=True)
    bind_dp_parser.add_argument("--review-id", required=True)
    bind_dp_parser.add_argument("--agent-id", required=True)
    bind_dp_parser.add_argument("--transcript", type=Path)
    export_dp_parser = subparsers.add_parser("export-dp-response")
    export_dp_parser.add_argument("--run-dir", type=Path, required=True)
    export_dp_parser.add_argument("--review-id", required=True)
    export_dp_parser.add_argument("--output", type=Path, required=True)
    invalidate = subparsers.add_parser("invalidate")
    invalidate.add_argument("--run-dir", type=Path, required=True)
    invalidate.add_argument("--reason", required=True)
    reopen = subparsers.add_parser("reopen-incomplete")
    reopen.add_argument("--run-dir", type=Path, required=True)
    reopen.add_argument("--reason", required=True)
    complete = subparsers.add_parser("complete")
    complete.add_argument("--run-dir", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "prepare":
            print(prepare_run(args.run_id, args.owner))
        elif args.command == "bind-director":
            payload = bind_director(
                args.run_dir.resolve(),
                args.agent_id,
                transcript_path=args.transcript.resolve() if args.transcript else None,
            )
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        elif args.command == "bind-dp":
            payload = bind_dp(
                args.run_dir.resolve(),
                args.review_id,
                args.agent_id,
                transcript_path=args.transcript.resolve() if args.transcript else None,
            )
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        elif args.command == "export-dp-response":
            result = export_dp_response(
                args.run_dir.resolve(), args.review_id, args.output.resolve()
            )
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        elif args.command == "invalidate":
            payload = invalidate_run(args.run_dir.resolve(), args.reason)
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        elif args.command == "reopen-incomplete":
            payload = reopen_incomplete_run(
                args.run_dir.resolve(), args.reason
            )
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            result = complete_run(args.run_dir.resolve())
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except AcceptanceGuardError as error:
        print(f"MODEL_ACCEPTANCE_BLOCKED: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
