"""MODE:P vNext — Knowledge Source Auditor (V3.1).

Inventories all 24 knowledge files from the V0.1 baseline, cross-references
hashes, records dispositions, and flags E0 isolation gaps.

Spec references: LOOP §5; Knowledge Audit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


class RuntimeKnowledgeIsolationError(ValueError):
    """A runtime component attempted to use an archived/raw knowledge source."""


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _load_baseline_manifest() -> Dict[str, Any]:
    path = (_get_project_root() / "MODE_P_REDESIGN_PROJECT"
            / "vnext_baseline" / "V0.1_FREEZE_MANIFEST.json")
    return json.loads(path.read_text(encoding="utf-8"))


# Extended metadata beyond what the baseline manifest records
_KNOWLEDGE_META: Dict[str, Dict[str, Any]] = {
    "03_知识库/03_导演知识库_v4.0.md": {
        "license_status": "internal_archive",
        "e0_isolated": True,
        "disposition": "archived; forbidden for independent retrieval",
    },
    "03_知识库/03_导演知识库_v5.0.md": {
        "license_status": "internal",
        "e0_isolated": True,
        "disposition": "largest director rule source; extraction candidate only",
    },
    "03_知识库/04_编剧知识库_v1.1.md": {
        "license_status": "internal",
        "e0_isolated": True,
        "disposition": "diagnosis source; script-rewriting sections isolated",
    },
    "03_知识库/04_构图思维_导演用.md": {
        "license_status": "internal",
        "e0_isolated": True,
        "disposition": "composition candidate; intent-to-technique mapping must be softened",
    },
    "03_知识库/运镜思维_导演可用运动思维.md": {
        "license_status": "internal",
        "e0_isolated": True,
        "disposition": "camera movement candidate; must not output direct shot answers",
    },
    "03_知识库/导演手册_视觉叙事决策框架.md": {
        "license_status": "internal",
        "e0_isolated": True,
        "disposition": "diagnosis workflow candidate",
    },
    "03_知识库/PERFORMANCE_KB.md": {
        "license_status": "internal",
        "e0_isolated": True,
        "disposition": "performance visibility candidate; fixed psych mappings isolated",
    },
    "03_知识库/sd2_model_capability.md": {
        "license_status": "internal",
        "e0_isolated": True,
        "disposition": "historical capability claim; NOT current permanent fact",
    },
    "03_知识库/sd2_storyboard_prompt_quality_standard.md": {
        "license_status": "internal",
        "e0_isolated": True,
        "disposition": "storyboard/video prompt quality candidate",
    },
    "03_知识库/distillation_engine_v1.0.md": {
        "license_status": "internal_archive",
        "e0_isolated": True,
        "disposition": "legacy distillation reference; do not restore old thresholds",
    },
}


def _default_meta(source_group: str) -> Dict[str, Any]:
    if source_group == "runtime_core":
        return {"license_status": "internal", "e0_isolated": False,
                "disposition": "K1 candidate baseline — to be audited for vNext migration"}
    elif source_group == "runtime_capsule":
        return {"license_status": "internal", "e0_isolated": False,
                "disposition": "K2 migration candidate"}
    elif source_group == "runtime_index":
        return {"license_status": "internal", "e0_isolated": False,
                "disposition": "tooling metadata; rebuild index for vNext"}
    return {"license_status": "unknown", "e0_isolated": False,
            "disposition": "pending"}


def load_knowledge_inventory() -> List[Dict[str, Any]]:
    """Return the full 24-file knowledge inventory with metadata."""
    manifest = _load_baseline_manifest()
    inventory: List[Dict[str, Any]] = []

    for entry in manifest["knowledge_files"]:
        meta = _KNOWLEDGE_META.get(entry["path"],
                                   _default_meta(entry["source_group"]))
        inventory.append({
            "path": entry["path"],
            "sha256": entry["sha256"],
            "bytes": entry["bytes"],
            "source_group": entry["source_group"],
            "disposition": meta["disposition"],
            "license_status": meta["license_status"],
            "e0_isolated": meta["e0_isolated"],
        })

    return inventory


def audit_knowledge_sources() -> Dict[str, Any]:
    """Run a full audit and return a summary report."""
    inventory = load_knowledge_inventory()
    by_group: Dict[str, int] = {}
    disposition_summary: Dict[str, int] = {}
    e0_isolated_count = 0

    for entry in inventory:
        g = entry["source_group"]
        by_group[g] = by_group.get(g, 0) + 1
        d = entry["disposition"]
        disposition_summary[d] = disposition_summary.get(d, 0) + 1
        if entry["e0_isolated"]:
            e0_isolated_count += 1

    return {
        "total_files": len(inventory),
        "by_group": by_group,
        "disposition_summary": disposition_summary,
        "e0_isolated_count": e0_isolated_count,
        "e0_not_isolated_count": len(inventory) - e0_isolated_count,
    }


# Runtime retrieval is intentionally more restrictive than the audit process:
# the auditor may read the frozen manifest, while a generation run may consume
# only an already-reviewed metadata catalog.  In particular it may not read a
# K0 markdown/book passage or reactivate the v4 archive.
_RAW_SOURCE_GROUPS = frozenset({"offline_source"})
_METADATA_OPERATIONS = frozenset({"metadata_index", "hash_reference", "snapshot_reference"})


def runtime_source_policy(
    source_group: str,
    *,
    operation: str = "metadata_index",
    source_path: str = "",
) -> Dict[str, Any]:
    """Return an explicit fail-closed decision for runtime knowledge access."""
    lowered_path = source_path.replace("\\", "/").lower()
    is_v4_archive = "/v4" in lowered_path or "director_system_v4" in lowered_path
    if operation not in _METADATA_OPERATIONS:
        return {
            "allowed": False,
            "reason": "runtime_may_not_load_raw_knowledge_text",
            "source_group": source_group,
        }
    if source_group in _RAW_SOURCE_GROUPS or is_v4_archive:
        return {
            "allowed": False,
            "reason": "k0_or_v4_archive_is_read_only_outside_runtime",
            "source_group": source_group,
        }
    return {
        "allowed": True,
        "reason": "prebuilt_metadata_only",
        "source_group": source_group,
    }


def assert_runtime_source_allowed(
    source_group: str,
    *,
    operation: str = "metadata_index",
    source_path: str = "",
) -> None:
    """Raise rather than silently falling back to a raw knowledge read."""
    policy = runtime_source_policy(
        source_group,
        operation=operation,
        source_path=source_path,
    )
    if not policy["allowed"]:
        raise RuntimeKnowledgeIsolationError(str(policy["reason"]))


def build_runtime_metadata_index(
    entries: Iterable[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Create a hash/path-only catalog without loading any source contents.

    This routine deliberately accepts already-provided inventory metadata.  It
    does not accept a source loader or filesystem path, preventing accidental
    full-library loading in the retrieval path.
    """
    index: List[Dict[str, Any]] = []
    for entry in entries:
        source_group = str(entry.get("source_group", "unknown"))
        source_path = str(entry.get("path", ""))
        policy = runtime_source_policy(
            source_group,
            operation="metadata_index",
            source_path=source_path,
        )
        index.append({
            "path": source_path,
            "sha256": str(entry.get("sha256", "")),
            "source_group": source_group,
            "runtime_allowed": bool(policy["allowed"]),
            "runtime_reason": str(policy["reason"]),
        })
    return index
