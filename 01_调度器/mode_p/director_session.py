"""Bind one observable Director Agent identity to an entire episode session."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


STATE_NAME = "DIRECTOR_SESSION.json"
SCHEMA_VERSION = "1.0"


class DirectorSessionError(ValueError):
    """Raised when an orchestrator attempts to replace the episode Director."""


def bind_director(
    episode_session: Path,
    agent_id: str,
    resolved_model: str,
    *,
    now: datetime | None = None,
) -> dict:
    episode_session = episode_session.resolve()
    if not episode_session.is_dir():
        raise DirectorSessionError(f"episode session does not exist: {episode_session}")
    agent_id = agent_id.strip()
    resolved_model = resolved_model.strip()
    if not agent_id or not resolved_model:
        raise DirectorSessionError("agent_id and resolved_model are required")
    path = episode_session / STATE_NAME
    if path.exists():
        state = _load(path)
        _require_identity(state, agent_id, resolved_model)
        return state
    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    state = {
        "schema_version": SCHEMA_VERSION,
        "episode_session_id": episode_session.name,
        "director_agent_id": agent_id,
        "resolved_model": resolved_model,
        "bound_at": timestamp,
        "resume_events": [],
    }
    _atomic_json(path, state)
    return state


def record_resume(
    episode_session: Path,
    agent_id: str,
    resolved_model: str,
    event_id: str,
    *,
    now: datetime | None = None,
) -> dict:
    path = episode_session.resolve() / STATE_NAME
    state = _load(path)
    _require_identity(state, agent_id.strip(), resolved_model.strip())
    event_id = event_id.strip()
    if not event_id:
        raise DirectorSessionError("resume event_id is required")
    events = state["resume_events"]
    if any(item["event_id"] == event_id for item in events):
        raise DirectorSessionError(f"resume event_id already recorded: {event_id}")
    events.append({
        "sequence": len(events) + 1,
        "event_id": event_id,
        "recorded_at": (now or datetime.now(timezone.utc)).isoformat(),
    })
    _atomic_json(path, state)
    return state


def verify_director(
    episode_session: Path,
    agent_id: str,
    resolved_model: str,
) -> dict:
    state = _load(episode_session.resolve() / STATE_NAME)
    _require_identity(state, agent_id.strip(), resolved_model.strip())
    return state


def _load(path: Path) -> dict:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DirectorSessionError(f"cannot read Director session binding: {exc}") from exc
    expected = {
        "schema_version", "episode_session_id", "director_agent_id",
        "resolved_model", "bound_at", "resume_events",
    }
    if not isinstance(state, dict) or set(state) != expected:
        raise DirectorSessionError("Director session binding fields are malformed")
    if state["schema_version"] != SCHEMA_VERSION:
        raise DirectorSessionError("unsupported Director session binding version")
    if not isinstance(state["resume_events"], list):
        raise DirectorSessionError("Director resume_events must be a list")
    return state


def _require_identity(state: dict, agent_id: str, resolved_model: str) -> None:
    if state["director_agent_id"] != agent_id:
        raise DirectorSessionError(
            "episode Director replacement rejected: resume the originally bound Agent ID"
        )
    if state["resolved_model"] != resolved_model:
        raise DirectorSessionError(
            "episode Director model changed during the same session"
        )


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("bind", "verify"):
        command = sub.add_parser(name)
        command.add_argument("episode_session", type=Path)
        command.add_argument("--agent-id", required=True)
        command.add_argument("--model-name", required=True)
    resume = sub.add_parser("resume")
    resume.add_argument("episode_session", type=Path)
    resume.add_argument("--agent-id", required=True)
    resume.add_argument("--model-name", required=True)
    resume.add_argument("--event-id", required=True)
    args = parser.parse_args()
    try:
        if args.command == "bind":
            state = bind_director(
                args.episode_session, args.agent_id, args.model_name
            )
        elif args.command == "resume":
            state = record_resume(
                args.episode_session, args.agent_id, args.model_name, args.event_id
            )
        else:
            state = verify_director(
                args.episode_session, args.agent_id, args.model_name
            )
        print(json.dumps(state, ensure_ascii=False, sort_keys=True))
        return 0
    except DirectorSessionError as exc:
        print(f"DIRECTOR_SESSION_BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
