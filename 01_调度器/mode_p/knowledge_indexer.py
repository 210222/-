"""Validate and hash the metadata-only MODE:P knowledge index.

The index is an allowlist for context retrieval.  It never chooses a creative
answer or an SD2 generation mode; it only describes which knowledge may be
considered for a Director-authored scene.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


_DEFAULT_INDEX = Path(__file__).with_name("knowledge") / "knowledge_index.json"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_TOP_FIELDS = {
    "schema_version", "description", "core", "capsules",
    "index_updated_at", "index_statistics",
}
_CORE_FIELDS = {
    "path", "always_load", "topics", "content_sha256", "byte_size",
}
_CAPSULE_FIELDS = {
    "path", "scene_types", "drama_intents", "space_conditions",
    "character_count_range", "motion_complexity", "sd2_risk_tags",
    "verified_count", "experience_status", "content_sha256", "byte_size",
}
_MOTION_LEVELS = {"minimal", "low", "medium", "high", "variable"}
_EXPERIENCE_STATES = {"none", "candidate", "repeated", "validated", "rejected"}


def _string_list(value: Any, field: str, issues: list[str]) -> None:
    if not isinstance(value, list) or not value:
        issues.append(f"SCHEMA: {field} must be a non-empty string array")
        return
    if any(not isinstance(item, str) or not item.strip() for item in value):
        issues.append(f"SCHEMA: {field} contains an empty or non-string value")
    elif len(value) != len(set(value)):
        issues.append(f"SCHEMA: {field} contains duplicate values")


def _entry_path(index_dir: Path, raw: Any, section: str) -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ValueError("path must be a non-empty portable relative path")
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts or pure.parts[0] != section:
        raise ValueError(f"path must stay under {section}/")
    candidate = (index_dir / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(index_dir.resolve())
    except ValueError as exc:
        raise ValueError("path resolves outside the knowledge directory") from exc
    return candidate


def _validate_structure(data: Any, index_dir: Path) -> list[str]:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["SCHEMA: index root must be an object"]

    unknown = set(data) - _TOP_FIELDS
    missing = {"schema_version", "description", "core", "capsules"} - set(data)
    if unknown:
        issues.append(f"SCHEMA: unknown top-level fields: {sorted(unknown)}")
    if missing:
        issues.append(f"SCHEMA: missing top-level fields: {sorted(missing)}")
    if data.get("schema_version") != "1.1":
        issues.append("SCHEMA: schema_version must be 1.1")
    if not isinstance(data.get("description"), str) or not data.get("description", "").strip():
        issues.append("SCHEMA: description must be a non-empty string")

    all_paths: list[str] = []
    for section in ("core", "capsules"):
        entries = data.get(section)
        if not isinstance(entries, list) or not entries:
            issues.append(f"SCHEMA: {section} must be a non-empty array")
            continue
        for number, entry in enumerate(entries, 1):
            label = f"{section}[{number}]"
            if not isinstance(entry, dict):
                issues.append(f"SCHEMA: {label} must be an object")
                continue
            allowed = _CORE_FIELDS if section == "core" else _CAPSULE_FIELDS
            required = allowed - {"content_sha256", "byte_size"}
            if set(entry) - allowed:
                issues.append(f"SCHEMA: {label} has unknown fields: {sorted(set(entry) - allowed)}")
            if required - set(entry):
                issues.append(f"SCHEMA: {label} is missing fields: {sorted(required - set(entry))}")

            raw_path = entry.get("path")
            if isinstance(raw_path, str):
                all_paths.append(raw_path)
            try:
                _entry_path(index_dir, raw_path, section)
            except (ValueError, IndexError) as exc:
                issues.append(f"SCHEMA: {label}.path {exc}")

            if section == "core":
                if entry.get("always_load") is not True:
                    issues.append(f"SCHEMA: {label}.always_load must be true")
                _string_list(entry.get("topics"), f"{label}.topics", issues)
            else:
                for field in ("scene_types", "drama_intents", "space_conditions", "sd2_risk_tags"):
                    _string_list(entry.get(field), f"{label}.{field}", issues)
                count_range = entry.get("character_count_range")
                if not isinstance(count_range, dict) or set(count_range) != {"min", "max"}:
                    issues.append(f"SCHEMA: {label}.character_count_range must contain only min/max")
                else:
                    minimum, maximum = count_range.get("min"), count_range.get("max")
                    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0:
                        issues.append(f"SCHEMA: {label}.character_count_range.min must be >= 0")
                    if maximum is not None and (
                        isinstance(maximum, bool) or not isinstance(maximum, int)
                        or maximum < 0 or (isinstance(minimum, int) and maximum < minimum)
                    ):
                        issues.append(f"SCHEMA: {label}.character_count_range.max is invalid")
                if entry.get("motion_complexity") not in _MOTION_LEVELS:
                    issues.append(f"SCHEMA: {label}.motion_complexity is invalid")
                verified_count = entry.get("verified_count")
                if isinstance(verified_count, bool) or not isinstance(verified_count, int) or verified_count < 0:
                    issues.append(f"SCHEMA: {label}.verified_count must be >= 0")
                if entry.get("experience_status") not in _EXPERIENCE_STATES:
                    issues.append(f"SCHEMA: {label}.experience_status is invalid")

            digest = entry.get("content_sha256")
            if digest is not None and (not isinstance(digest, str) or not _HASH_RE.fullmatch(digest)):
                issues.append(f"SCHEMA: {label}.content_sha256 must be lowercase SHA-256")
            byte_size = entry.get("byte_size")
            if byte_size is not None and (
                isinstance(byte_size, bool) or not isinstance(byte_size, int) or byte_size < 0
            ):
                issues.append(f"SCHEMA: {label}.byte_size must be >= 0")

    if len(all_paths) != len(set(all_paths)):
        issues.append("SCHEMA: duplicate indexed paths")

    timestamp = data.get("index_updated_at")
    if timestamp is not None:
        try:
            datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            issues.append("SCHEMA: index_updated_at must be an ISO-8601 timestamp")

    stats = data.get("index_statistics")
    if stats is not None:
        if not isinstance(stats, dict) or set(stats) != {
            "total_entries", "total_bytes", "changed_since_last"
        }:
            issues.append("SCHEMA: index_statistics has an invalid shape")
        elif (
            isinstance(stats["total_entries"], bool)
            or not isinstance(stats["total_entries"], int)
            or stats["total_entries"] < 0
            or isinstance(stats["total_bytes"], bool)
            or not isinstance(stats["total_bytes"], int)
            or stats["total_bytes"] < 0
            or not isinstance(stats["changed_since_last"], list)
            or any(not isinstance(item, str) for item in stats["changed_since_last"])
        ):
            issues.append("SCHEMA: index_statistics values are invalid")
    return issues


def _read_index(index_path: Path) -> dict[str, Any]:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read knowledge index: {exc}") from exc
    issues = _validate_structure(data, index_path.parent)
    if issues:
        raise ValueError("; ".join(issues))
    return data


def load_index_metadata(index_path: Path) -> dict[str, Any]:
    """Load and structurally validate the index without reading knowledge files."""
    return _read_index(index_path)


def compute_hashes(index_path: Path, output_path: Path | None = None) -> dict:
    """Read index, compute hashes for all entries, return updated index dict."""
    index_dir = index_path.parent
    data = _read_index(index_path)
    total_entries = 0
    total_size = 0
    changed: list[str] = []

    for section in ("core", "capsules"):
        for entry in data.get(section, []):
            file_path = _entry_path(index_dir, entry["path"], section)
            if not file_path.is_file():
                raise FileNotFoundError(f"Indexed file not found: {file_path}")
            content = file_path.read_bytes()
            content.decode("utf-8")
            new_hash = hashlib.sha256(content).hexdigest()
            old_hash = entry.get("content_sha256")
            if old_hash != new_hash or entry.get("byte_size") != len(content):
                changed.append(entry["path"])
            entry["content_sha256"] = new_hash
            entry["byte_size"] = len(content)
            total_entries += 1
            total_size += entry["byte_size"]

    old_stats = data.get("index_statistics", {})
    if (
        changed
        or "index_updated_at" not in data
        or old_stats.get("total_entries") != total_entries
        or old_stats.get("total_bytes") != total_size
    ):
        data["index_updated_at"] = datetime.now(timezone.utc).isoformat()
    data["index_statistics"] = {
        "total_entries": total_entries,
        "total_bytes": total_size,
        "changed_since_last": changed,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output_path.with_name(f".{output_path.name}.tmp-{os.getpid()}")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(output_path)
    return data


def validate_index(index_path: Path) -> tuple[bool, list[str]]:
    """Check that all indexed files exist and hashes match. Returns (ok, issues)."""
    index_dir = index_path.parent
    try:
        data = _read_index(index_path)
    except ValueError as exc:
        return False, [f"INDEX: {exc}"]
    issues: list[str] = []

    for section in ("core", "capsules"):
        for entry in data.get(section, []):
            file_path = _entry_path(index_dir, entry["path"], section)
            if not file_path.is_file():
                issues.append(f"MISSING: {entry['path']}")
                continue
            try:
                content = file_path.read_bytes()
                content.decode("utf-8")
            except (OSError, UnicodeError) as exc:
                issues.append(f"UNREADABLE: {entry['path']} ({exc})")
                continue
            actual = hashlib.sha256(content).hexdigest()
            expected = entry.get("content_sha256")
            if expected and actual != expected:
                issues.append(f"HASH MISMATCH: {entry['path']} "
                              f"(expected {expected[:8]}..., got {actual[:8]}...)")
            if not expected:
                issues.append(f"NO HASH: {entry['path']} (run 'update' to compute)")
            if entry.get("byte_size") != len(content):
                issues.append(
                    f"SIZE MISMATCH: {entry['path']} "
                    f"(expected {entry.get('byte_size')}, got {len(content)})"
                )

    if "index_updated_at" not in data:
        issues.append("INDEX: missing index_updated_at timestamp")

    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage versioned knowledge index with content hashes."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    up = sub.add_parser("update", help="Compute hashes and update index")
    up.add_argument("index", type=Path, nargs="?", default=_DEFAULT_INDEX)
    up.add_argument("-o", "--output", type=Path, default=None)

    val = sub.add_parser("validate", help="Validate indexed files and hashes")
    val.add_argument("index", type=Path, nargs="?", default=_DEFAULT_INDEX)

    args = parser.parse_args()

    if args.command == "update":
        out = args.output or args.index
        try:
            data = compute_hashes(args.index, out)
        except (ValueError, FileNotFoundError, UnicodeError, OSError) as exc:
            print(f"Index update failed: {exc}", file=sys.stderr)
            return 1
        stats = data["index_statistics"]
        print(f"Index updated: {stats['total_entries']} entries, "
              f"{stats['total_bytes']} bytes, "
              f"{len(stats['changed_since_last'])} changed")
        return 0
    else:
        ok, issues = validate_index(args.index)
        if ok:
            print("Index valid — all files present and hashes match.")
            return 0
        for issue in issues:
            print(f"  {issue}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
