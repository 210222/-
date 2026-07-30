"""Validate a small, Director-selected knowledge packet for a scene.

The caller supplies Director-authored scene metadata and zero-to-three explicit
capsule paths. This module does not read a script, infer dramatic intent, choose
a capsule from keywords, or choose an SD2 generation mode. Scene metadata only
filters validated experience records. With no explicit capsule request, the
knowledge packet contains Core only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

from knowledge_indexer import validate_index


_DEFAULT_INDEX = Path(__file__).with_name("knowledge") / "knowledge_index.json"
_EXPERIENCE_DIR = Path(__file__).parent.parent.parent / "05_项目经验" / "validated"
_QUERY_FIELDS = {
    "scene_types", "drama_intents", "space_conditions", "character_count",
    "motion_complexity", "requested_capsules",
}
_MOTION_LEVELS = {"minimal", "low", "medium", "high", "variable"}


class RetrievalError(ValueError):
    """Raised when retrieval inputs or indexed content fail closed."""


def _string_array(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if value is None and allow_empty:
        return []
    if not isinstance(value, list) or (not value and not allow_empty):
        raise RetrievalError(f"{field} must be a string array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise RetrievalError(f"{field} contains an empty or non-string value")
    normalized = list(dict.fromkeys(item.strip() for item in value))
    if len(normalized) != len(value):
        raise RetrievalError(f"{field} contains duplicate values")
    return normalized


def normalize_query(query: dict[str, Any]) -> dict[str, Any]:
    """Validate explicit Director-authored retrieval metadata."""
    if not isinstance(query, dict):
        raise RetrievalError("query must be an object")
    unknown = set(query) - _QUERY_FIELDS
    if unknown:
        raise RetrievalError(f"unknown query fields: {sorted(unknown)}")

    normalized: dict[str, Any] = {}
    for field in ("scene_types", "drama_intents", "space_conditions", "requested_capsules"):
        normalized[field] = _string_array(query.get(field), field)

    count = query.get("character_count")
    if count is not None and (
        isinstance(count, bool) or not isinstance(count, int) or count < 0
    ):
        raise RetrievalError("character_count must be a non-negative integer")
    normalized["character_count"] = count

    motion = query.get("motion_complexity")
    if motion is not None and motion not in _MOTION_LEVELS:
        raise RetrievalError(f"motion_complexity must be one of {sorted(_MOTION_LEVELS)}")
    normalized["motion_complexity"] = motion

    if len(normalized["requested_capsules"]) > 3:
        raise RetrievalError("requested_capsules may contain at most three paths")
    return normalized


def _range_contains(count_range: dict[str, Any], value: int | None) -> bool:
    if value is None:
        return False
    minimum = count_range["min"]
    maximum = count_range["max"]
    return value >= minimum and (maximum is None or value <= maximum)


def relevance(entry: dict[str, Any], query: dict[str, Any]) -> tuple[int, list[str]]:
    """Score indexed applicability; weak numeric matches cannot select alone."""
    score = 0
    reasons: list[str] = []
    path = entry["path"]
    if path in query["requested_capsules"]:
        score += 100
        reasons.append("director_requested")

    for field, weight in (
        ("scene_types", 4),
        ("drama_intents", 4),
        ("space_conditions", 2),
    ):
        matches = sorted(set(query[field]) & set(entry[field]))
        if matches:
            score += weight * len(matches)
            reasons.extend(f"{field}:{item}" for item in matches)

    has_strong_match = any(
        reason == "director_requested"
        or reason.startswith("scene_types:")
        or reason.startswith("drama_intents:")
        for reason in reasons
    )
    if not has_strong_match:
        return 0, []

    if _range_contains(entry["character_count_range"], query["character_count"]):
        score += 1
        reasons.append("character_count")
    if query["motion_complexity"] == entry["motion_complexity"]:
        score += 1
        reasons.append("motion_complexity")
    return score, reasons


def _safe_content_path(root: Path, raw: Any) -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise RetrievalError("experience content_path must be a portable relative path")
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts:
        raise RetrievalError("experience content_path escapes the validated directory")
    candidate = (root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RetrievalError("experience content_path escapes the validated directory") from exc
    return candidate


def _validated_experiences(
    experience_dir: Path, query: dict[str, Any]
) -> list[dict[str, Any]]:
    if not experience_dir.is_dir():
        return []

    selected: list[tuple[int, str, dict[str, Any]]] = []
    for record_path in sorted(experience_dir.glob("*.experience.json")):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RetrievalError(f"invalid experience record {record_path.name}: {exc}") from exc
        required = {
            "schema_version", "experience_id", "status", "content_path",
            "content_sha256", "verified_count", "render_evidence", "applicability",
        }
        if not isinstance(record, dict) or set(record) != required:
            raise RetrievalError(f"invalid experience record shape: {record_path.name}")
        if record["schema_version"] != "1.0" or record["status"] != "validated":
            raise RetrievalError(f"experience is not validated: {record_path.name}")
        if (
            not isinstance(record["experience_id"], str)
            or not record["experience_id"].strip()
            or isinstance(record["verified_count"], bool)
            or not isinstance(record["verified_count"], int)
            or record["verified_count"] < 2
        ):
            raise RetrievalError(f"experience lacks repeated verification: {record_path.name}")
        evidence = _string_array(record["render_evidence"], "render_evidence", allow_empty=False)
        if not evidence:
            raise RetrievalError(f"experience lacks render evidence: {record_path.name}")

        digest = record["content_sha256"]
        if not isinstance(digest, str) or len(digest) != 64:
            raise RetrievalError(f"invalid experience hash: {record_path.name}")
        content_path = _safe_content_path(experience_dir, record["content_path"])
        if not content_path.is_file():
            raise RetrievalError(f"missing experience content: {record['content_path']}")
        actual = hashlib.sha256(content_path.read_bytes()).hexdigest()
        if actual != digest:
            raise RetrievalError(f"stale experience content: {record['content_path']}")

        applicability = record["applicability"]
        if not isinstance(applicability, dict):
            raise RetrievalError(f"invalid experience applicability: {record_path.name}")
        pseudo_entry = {
            "path": record["content_path"],
            "scene_types": _string_array(applicability.get("scene_types"), "scene_types"),
            "drama_intents": _string_array(applicability.get("drama_intents"), "drama_intents"),
            "space_conditions": _string_array(applicability.get("space_conditions"), "space_conditions"),
            "character_count_range": applicability.get("character_count_range"),
            "motion_complexity": applicability.get("motion_complexity"),
        }
        count_range = pseudo_entry["character_count_range"]
        if (
            not isinstance(count_range, dict)
            or set(count_range) != {"min", "max"}
            or isinstance(count_range.get("min"), bool)
            or not isinstance(count_range.get("min"), int)
            or count_range["min"] < 0
            or (
                count_range["max"] is not None
                and (
                    isinstance(count_range["max"], bool)
                    or not isinstance(count_range["max"], int)
                    or count_range["max"] < count_range["min"]
                )
            )
            or pseudo_entry["motion_complexity"] not in _MOTION_LEVELS
        ):
            raise RetrievalError(f"invalid experience applicability: {record_path.name}")
        score, reasons = relevance(pseudo_entry, {**query, "requested_capsules": []})
        if score:
            selected.append((score, record["experience_id"], {
                "experience_id": record["experience_id"],
                "path": str(content_path),
                "content_sha256": digest,
                "score": score,
                "matched_on": reasons,
            }))

    selected.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in selected[:3]]


def retrieve_context(
    query: dict[str, Any],
    index_path: Path = _DEFAULT_INDEX,
    experience_dir: Path | None = None,
) -> dict[str, Any]:
    """Return Core, zero-to-three matched capsules, and validated experience."""
    normalized = normalize_query(query)
    ok, issues = validate_index(index_path)
    if not ok:
        raise RetrievalError("knowledge index failed closed: " + "; ".join(issues))
    index_bytes = index_path.read_bytes()
    index = json.loads(index_bytes.decode("utf-8"))

    indexed_paths = {entry["path"] for entry in index["capsules"]}
    unknown_requested = set(normalized["requested_capsules"]) - indexed_paths
    if unknown_requested:
        raise RetrievalError(f"requested capsule is not indexed: {sorted(unknown_requested)}")

    capsule_by_path = {entry["path"]: entry for entry in index["capsules"]}
    capsules = list(normalized["requested_capsules"])
    selected = [capsule_by_path[path] for path in capsules]

    core = [entry["path"] for entry in index["core"]]
    content_hashes = {
        entry["path"]: entry["content_sha256"]
        for entry in (*index["core"], *selected)
    }
    experiences = _validated_experiences(experience_dir or _EXPERIENCE_DIR, normalized)
    return {
        "schema_version": "1.0",
        "query": normalized,
        "knowledge_index_sha256": hashlib.sha256(index_bytes).hexdigest(),
        "core": core,
        "capsules": capsules,
        "experiences": experiences,
        "content_hashes": content_hashes,
        "selection_reasons": {path: ["director_requested"] for path in capsules},
        "no_capsule_match": not capsules,
        "historical_fallback_used": False,
    }


def write_context_md(summary: dict[str, Any], output_path: Path) -> None:
    """Write an auditable manifest; agents load only the listed source files."""
    lines = [
        "# KNOWLEDGE_CONTEXT",
        "",
        f"Knowledge index SHA-256: `{summary['knowledge_index_sha256']}`",
        "",
        "## Core",
    ]
    for path in summary["core"]:
        lines.append(f"- `knowledge/{path}` | `{summary['content_hashes'][path]}`")
    lines.extend(["", "## Scene Capsules"])
    if summary["capsules"]:
        for path in summary["capsules"]:
            reasons = ", ".join(summary["selection_reasons"][path])
            lines.append(
                f"- `knowledge/{path}` | `{summary['content_hashes'][path]}` | {reasons}"
            )
    else:
        lines.append("- None. Director uses Core and current script facts; no historical fallback.")
    lines.extend(["", "## Validated Experiences"])
    if summary["experiences"]:
        for item in summary["experiences"]:
            lines.append(f"- `{item['path']}` | `{item['content_sha256']}`")
    else:
        lines.append("- None.")
    lines.extend(["", "Historical fallback used: `false`", ""])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.tmp-{os.getpid()}")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieve scene-relevant Director knowledge.")
    parser.add_argument("--scene-type", action="append", dest="scene_types", default=[])
    parser.add_argument("--drama-intent", action="append", dest="drama_intents", default=[])
    parser.add_argument("--space-condition", action="append", dest="space_conditions", default=[])
    parser.add_argument("--character-count", type=int)
    parser.add_argument("--motion-complexity", choices=sorted(_MOTION_LEVELS))
    parser.add_argument("--request-capsule", action="append", dest="requested_capsules", default=[])
    parser.add_argument("--index", type=Path, default=_DEFAULT_INDEX)
    parser.add_argument("--experience-dir", type=Path, default=None)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    query = {field: getattr(args, field) for field in _QUERY_FIELDS}
    try:
        summary = retrieve_context(query, args.index, args.experience_dir)
        if args.output:
            write_context_md(summary, args.output)
            print(f"KNOWLEDGE_CONTEXT -> {args.output}")
        else:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except (RetrievalError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Context retrieval failed: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
