"""Engineering-only command line interface for MODE:P vNext.

The CLI deliberately exposes only deterministic runtime operations while the
rebuild controller is in its repair phase: persistent session management and
an isolated structural Shadow run.  It never calls a Director/DP, v4, a
provider, or an external generation platform.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from . import __version__
from .canonical_serialization import canonical_json_dumps
from .session_state import (
    InvalidStateTransition,
    PersistentSession,
    SessionStateError,
)
from .shadow_entry import ShadowConfig, ShadowError, run_shadow


def _emit(value: Mapping[str, Any], stream: Any = sys.stdout) -> None:
    stream.write(canonical_json_dumps(dict(value)) + "\n")


def _parse_hashes(items: Optional[Iterable[str]]) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for item in items or ():
        if "=" not in item:
            raise SessionStateError(
                "artifact hash must use NAME=64-character-sha256 syntax"
            )
        name, digest = item.split("=", 1)
        if not name or not digest:
            raise SessionStateError("artifact hash name and digest are required")
        parsed[name] = digest
    return parsed


def _snapshot_response(snapshot: Any) -> Dict[str, Any]:
    return {"status": "OK", "session": snapshot.to_dict()}


def _session_init(args: argparse.Namespace) -> Dict[str, Any]:
    session = PersistentSession.create(
        Path(args.session_dir),
        args.episode_id,
        args.scene_id or "",
        scope=args.scope,
        owner=args.actor,
        initial_state=args.initial_state,
        correlation_id=args.correlation_id,
        artifact_hashes=_parse_hashes(args.artifact_hash),
    )
    return _snapshot_response(session.status(owner=args.actor))


def _session_status(args: argparse.Namespace) -> Dict[str, Any]:
    session = PersistentSession.open(Path(args.session_dir), owner=args.actor)
    return _snapshot_response(session.status(owner=args.actor))


def _session_transition(args: argparse.Namespace) -> Dict[str, Any]:
    session = PersistentSession.open(Path(args.session_dir), owner=args.actor)
    snapshot = session.transition(
        args.to,
        actor=args.actor,
        reason_code=args.reason_code,
        input_commit_id=args.input_commit_id,
        output_commit_id=args.output_commit_id,
        correlation_id=args.correlation_id,
        artifact_hashes=_parse_hashes(args.artifact_hash)
        if args.artifact_hash
        else None,
    )
    return _snapshot_response(snapshot)


def _shadow(args: argparse.Namespace) -> Dict[str, Any]:
    result = run_shadow(
        ShadowConfig(
            episode_script_path=args.script,
            session_dir=args.session_dir,
            episode_id=args.episode_id or "",
            run_id=args.run_id or "",
        )
    )
    return {"status": "OK", "shadow": result.to_dict()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m mode_p_vnext",
        description=(
            "MODE:P vNext engineering CLI.  Persistent sessions and isolated "
            "structural Shadow only; no production delivery or model submission."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    session = commands.add_parser("session", help="create, inspect, or explicitly transition a vNext session")
    session_commands = session.add_subparsers(dest="session_command", required=True)

    init = session_commands.add_parser("init", help="initialize an idempotent persistent session")
    init.add_argument("--session-dir", required=True)
    init.add_argument("--episode-id", required=True)
    init.add_argument("--scene-id", default="")
    init.add_argument("--scope", choices=("episode", "scene"), required=True)
    init.add_argument("--initial-state", default=None)
    init.add_argument("--actor", default="cli")
    init.add_argument("--correlation-id", default="cli-session-init")
    init.add_argument("--artifact-hash", action="append", default=[])
    init.set_defaults(handler=_session_init)

    status = session_commands.add_parser("status", help="read a persistent session's authoritative state")
    status.add_argument("--session-dir", required=True)
    status.add_argument("--actor", default="cli")
    status.set_defaults(handler=_session_status)

    transition = session_commands.add_parser("transition", help="append one explicit, audited session transition")
    transition.add_argument("--session-dir", required=True)
    transition.add_argument("--to", required=True)
    transition.add_argument("--reason-code", required=True)
    transition.add_argument("--actor", default="cli")
    transition.add_argument("--input-commit-id", default="")
    transition.add_argument("--output-commit-id", default="")
    transition.add_argument("--correlation-id", default="cli-session-transition")
    transition.add_argument("--artifact-hash", action="append", default=[])
    transition.set_defaults(handler=_session_transition)

    shadow = commands.add_parser("shadow", help="run an isolated vNext structural Shadow; never submits media")
    shadow.add_argument("--script", required=True)
    shadow.add_argument("--session-dir", required=True)
    shadow.add_argument("--episode-id", default="")
    shadow.add_argument("--run-id", default="")
    shadow.set_defaults(handler=_shadow)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        response = args.handler(args)
    except (SessionStateError, InvalidStateTransition, ShadowError, OSError, ValueError) as exc:
        _emit(
            {
                "status": "ERROR",
                "error_type": type(exc).__name__,
                "message": str(exc),
            },
            stream=sys.stderr,
        )
        return 2
    _emit(response)
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry delegates here
    raise SystemExit(main())
