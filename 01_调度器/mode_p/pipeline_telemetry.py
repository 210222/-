"""Pipeline telemetry — instrument MODE:P calls with timing and cache metrics.

Records: wall-clock time per stage, input/output byte sizes, cache hit/miss,
and invalidation scope. Data is lightweight and never includes creative content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


EVENT_SCHEMA_VERSION = "2.0"
_EVENT_TYPES = {"local", "model", "cache", "invalidation"}
_STATUSES = {"completed", "failed", "revision_required", "blocked"}
_CACHE_STATUSES = {"none", "hit", "miss", "store"}


@dataclass
class StageRecord:
    stage: str
    started_at: str
    elapsed_s: float = 0.0
    input_bytes: int = 0
    output_bytes: int = 0
    cache_hit: bool = False
    cache_miss: bool = False
    error: str = ""


@dataclass
class TelemetrySession:
    session_id: str
    script_sha256: str = ""
    bootstrap_sha256: str = ""
    stages: list[StageRecord] = field(default_factory=list)
    total_elapsed_s: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    invalidation_reason: str = ""


class Telemetry:
    """Context manager for pipeline stage timing."""

    def __init__(self, session: TelemetrySession):
        self.session = session
        self._start = 0.0
        self._stage: StageRecord | None = None

    def start_stage(self, stage: str):
        self._stage = StageRecord(
            stage=stage,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._start = time.monotonic()

    def end_stage(self, input_bytes: int = 0, output_bytes: int = 0,
                  cache_hit: bool = False, cache_miss: bool = False,
                  error: str = ""):
        if self._stage is None:
            return
        self._stage.elapsed_s = round(time.monotonic() - self._start, 4)
        self._stage.input_bytes = input_bytes
        self._stage.output_bytes = output_bytes
        self._stage.cache_hit = cache_hit
        self._stage.cache_miss = cache_miss
        self._stage.error = error
        self.session.stages.append(self._stage)
        if cache_hit:
            self.session.cache_hits += 1
        if cache_miss:
            self.session.cache_misses += 1
        self._stage = None

    def finish(self):
        self.session.total_elapsed_s = round(
            sum(s.elapsed_s for s in self.session.stages), 4)

    def write_report(self, output_path: Path):
        self.finish()
        data = asdict(self.session)
        data["stages"] = [asdict(s) for s in self.session.stages]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

    @staticmethod
    def load(path: Path) -> TelemetrySession:
        data = json.loads(path.read_text(encoding="utf-8"))
        session = TelemetrySession(
            session_id=data.get("session_id", ""),
            script_sha256=data.get("script_sha256", ""),
            bootstrap_sha256=data.get("bootstrap_sha256", ""),
            cache_hits=data.get("cache_hits", 0),
            cache_misses=data.get("cache_misses", 0),
            total_elapsed_s=data.get("total_elapsed_s", 0),
            invalidation_reason=data.get("invalidation_reason", ""),
        )
        for s in data.get("stages", []):
            session.stages.append(StageRecord(**s))
        return session


def files_byte_size(paths: Iterable[Path]) -> int:
    """Count current regular-file bytes without reading or recording content."""
    total = 0
    seen: set[Path] = set()
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else [
            item for item in path.rglob("*") if item.is_file() and not item.is_symlink()
        ]
        for item in candidates:
            resolved = item.resolve()
            if resolved not in seen:
                total += item.stat().st_size
                seen.add(resolved)
    return total


def telemetry_root_for_scene(scene_session: Path) -> Path:
    """Map scenes/scene_NNN to its episode root; keep standalone tests local."""
    resolved = scene_session.resolve()
    if resolved.parent.name == "scenes":
        return resolved.parent.parent
    return resolved


def record_event(
    session_dir: Path,
    *,
    event_type: str,
    stage: str,
    status: str = "completed",
    elapsed_s: float = 0.0,
    input_bytes: int = 0,
    output_bytes: int = 0,
    model_role: str = "",
    model_name: str = "",
    model_call_id: str = "",
    cache_status: str = "none",
    invalidation_scope: Iterable[str] = (),
    result_code: int = 0,
    error_code: str = "",
) -> dict[str, Any]:
    """Write one immutable telemetry event without creative payloads."""
    if event_type not in _EVENT_TYPES:
        raise ValueError(f"invalid telemetry event_type: {event_type}")
    if status not in _STATUSES:
        raise ValueError(f"invalid telemetry status: {status}")
    if cache_status not in _CACHE_STATUSES:
        raise ValueError(f"invalid telemetry cache_status: {cache_status}")
    if not isinstance(stage, str) or not stage.strip():
        raise ValueError("telemetry stage is required")
    if elapsed_s < 0 or input_bytes < 0 or output_bytes < 0:
        raise ValueError("telemetry measurements cannot be negative")
    if event_type == "model" and (
        model_role not in {"director", "dp"}
        or not model_name.strip()
        or not model_call_id.strip()
    ):
        raise ValueError("model telemetry requires role, model, and call ID")
    scope = sorted(set(str(item).strip() for item in invalidation_scope if str(item).strip()))
    event = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": uuid.uuid4().hex,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "stage": stage.strip(),
        "status": status,
        "elapsed_s": round(float(elapsed_s), 6),
        "input_bytes": int(input_bytes),
        "output_bytes": int(output_bytes),
        "model_role": model_role,
        "model_name": model_name,
        "model_call_id_sha256": (
            hashlib.sha256(model_call_id.encode("utf-8")).hexdigest()
            if model_call_id else ""
        ),
        "cache_status": cache_status,
        "invalidation_scope": scope,
        "result_code": int(result_code),
        "error_code": error_code.strip(),
    }
    event_dir = session_dir.resolve() / "telemetry" / "events"
    event_dir.mkdir(parents=True, exist_ok=True)
    name = f"{time.time_ns()}-{os.getpid()}-{event['event_id']}.json"
    target = event_dir / name
    descriptor = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        payload = (
            json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return event


def load_events(session_dir: Path) -> list[dict[str, Any]]:
    event_dir = session_dir.resolve() / "telemetry" / "events"
    if not event_dir.is_dir():
        return []
    events: list[dict[str, Any]] = []
    for path in sorted(event_dir.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid telemetry event {path.name}: {exc}") from exc
        if (
            not isinstance(value, dict)
            or value.get("schema_version") != EVENT_SCHEMA_VERSION
            or value.get("event_type") not in _EVENT_TYPES
        ):
            raise ValueError(f"invalid telemetry event schema: {path.name}")
        events.append(value)
    return events


def summarize_events(session_dir: Path) -> dict[str, Any]:
    events = load_events(session_dir)
    by_stage: dict[str, dict[str, Any]] = {}
    model_calls = {"director": 0, "dp": 0}
    model_ids: set[str] = set()
    cache = {"hit": 0, "miss": 0, "store": 0}
    invalidation_scope: set[str] = set()
    for event in events:
        stage = event["stage"]
        aggregate = by_stage.setdefault(stage, {
            "events": 0, "elapsed_s": 0.0, "input_bytes": 0,
            "output_bytes": 0, "failures": 0,
        })
        aggregate["events"] += 1
        aggregate["elapsed_s"] = round(
            aggregate["elapsed_s"] + float(event["elapsed_s"]), 6
        )
        aggregate["input_bytes"] += int(event["input_bytes"])
        aggregate["output_bytes"] += int(event["output_bytes"])
        if event["status"] in {"failed", "blocked"}:
            aggregate["failures"] += 1
        if event["event_type"] == "model":
            call_hash = event["model_call_id_sha256"]
            if call_hash and call_hash not in model_ids:
                model_calls[event["model_role"]] += 1
                model_ids.add(call_hash)
        if event["cache_status"] in cache:
            cache[event["cache_status"]] += 1
        invalidation_scope.update(event["invalidation_scope"])
    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_count": len(events),
        "total_elapsed_s": round(sum(float(e["elapsed_s"]) for e in events), 6),
        "total_input_bytes": sum(int(e["input_bytes"]) for e in events),
        "total_output_bytes": sum(int(e["output_bytes"]) for e in events),
        "model_calls": model_calls,
        "cache": cache,
        "invalidation_scope": sorted(invalidation_scope),
        "stages": dict(sorted(by_stage.items())),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="MODE:P pipeline telemetry.")
    sub = parser.add_subparsers(dest="command", required=True)

    summ = sub.add_parser("summary", help="Print telemetry summary")
    summ.add_argument("report", type=Path)

    events = sub.add_parser("event-summary", help="Summarize immutable runtime events")
    events.add_argument("session", type=Path)

    model = sub.add_parser("record-model", help="Record one actual Director or DP call")
    model.add_argument("session", type=Path)
    model.add_argument("--stage", required=True)
    model.add_argument("--role", choices=("director", "dp"), required=True)
    model.add_argument("--model", required=True)
    model.add_argument("--call-id", required=True)
    model.add_argument("--elapsed", type=float, default=0.0)
    model.add_argument("--input", type=Path, action="append", default=[])
    model.add_argument("--output", type=Path, action="append", default=[])

    invalidation = sub.add_parser("record-invalidation")
    invalidation.add_argument("session", type=Path)
    invalidation.add_argument("--stage", default="dependency_invalidation")
    invalidation.add_argument("--scope", action="append", default=[])

    args = parser.parse_args()

    if args.command == "summary":
        session = Telemetry.load(args.report)
        print(f"Session: {session.session_id}")
        print(f"Total elapsed: {session.total_elapsed_s:.2f}s")
        print(f"Stages: {len(session.stages)}")
        print(f"Cache: {session.cache_hits} hits, {session.cache_misses} misses")
        for s in session.stages:
            cache = " [HIT]" if s.cache_hit else " [MISS]" if s.cache_miss else ""
            err = f" ERROR: {s.error}" if s.error else ""
            print(f"  {s.stage}: {s.elapsed_s:.3f}s "
                  f"in={s.input_bytes}b out={s.output_bytes}b{cache}{err}")
        return 0
    if args.command == "event-summary":
        print(json.dumps(summarize_events(args.session), ensure_ascii=False, indent=2))
        return 0
    if args.command == "record-model":
        record_event(
            args.session,
            event_type="model",
            stage=args.stage,
            elapsed_s=args.elapsed,
            input_bytes=files_byte_size(args.input),
            output_bytes=files_byte_size(args.output),
            model_role=args.role,
            model_name=args.model,
            model_call_id=args.call_id,
        )
        return 0
    if args.command == "record-invalidation":
        record_event(
            args.session,
            event_type="invalidation",
            stage=args.stage,
            invalidation_scope=args.scope,
        )
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
