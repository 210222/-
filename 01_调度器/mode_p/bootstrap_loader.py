"""Metadata-only MODE:P bootstrap and stable runtime fingerprints.

The bootstrap reads the four small Core documents and runtime instructions.
For capsules and reference media it reads only validated indexes and filesystem
metadata.  It never preloads capsule text, legacy material, render cases, or
media bodies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from asset_indexer import AssetIndexError, load_asset_index_metadata
from asset_card_registry import AssetCardError, load_card_index_metadata
from knowledge_indexer import load_index_metadata
from pipeline_telemetry import files_byte_size, record_event
from sd2_capability_manager import CapabilityProfileError, load_profile


BOOTSTRAP_SCHEMA_VERSION = "2.0"
_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parents[1]
_KNOWLEDGE_INDEX = _MODULE_DIR / "knowledge" / "knowledge_index.json"
_CAPABILITY_PROFILE = _MODULE_DIR / "sd2_capability_profile.json"
_ASSET_INDEX = _PROJECT_ROOT / "ASSET_INDEX.json"
_ASSET_CARD_INDEX = _PROJECT_ROOT / "ASSET_CARD_INDEX.json"

_RUNTIME_FILES = (
    "CLAUDE.md",
    ".claude/commands/mode-p-pilot.md",
    ".claude/agents/mode-p-director.md",
    ".claude/agents/mode-p-dp.md",
    "02_Agent/director_agent.md",
    "02_Agent/dp_agent.md",
    "01_调度器/mode_p/director_agent.md",
    "01_调度器/mode_p/dp_agent.md",
    "01_调度器/mode_p/director_runtime_contract.md",
    "01_调度器/mode_p/director_master_template.md",
    "01_调度器/mode_p/shot_manifest_schema.json",
)
_CHECKER_FILES = (
    "project_context.py",
    "asset_card_registry.py",
    "script_ingest.py",
    "context_retriever.py",
    "master_compiler.py",
    "view_deriver.py",
    "master_sync_check.py",
    "boundary_check.py",
    "reference_plan_check.py",
    "sd2_preflight.py",
    "structural_precheck.py",
    "batch_state_machine.py",
    "session_lock.py",
)


@dataclass
class BootstrapManifest:
    schema_version: str = BOOTSTRAP_SCHEMA_VERSION
    knowledge_index: dict[str, Any] = field(default_factory=dict)
    core_documents: list[dict[str, Any]] = field(default_factory=list)
    knowledge_file_metadata_sha256: str = ""
    capability_profile: dict[str, Any] = field(default_factory=dict)
    asset_index: dict[str, Any] = field(default_factory=dict)
    asset_metadata_sha256: str = ""
    asset_card_index: dict[str, Any] = field(default_factory=dict)
    asset_card_metadata_sha256: str = ""
    runtime_fingerprints: dict[str, str] = field(default_factory=dict)
    checker_fingerprints: dict[str, str] = field(default_factory=dict)
    compiler_version: str = ""
    manifest_sha256: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    # Compatibility accessors used by earlier callers.
    @property
    def knowledge_index_sha256(self) -> str:
        return str(self.knowledge_index.get("content_sha256", ""))

    @property
    def knowledge_core_count(self) -> int:
        return int(self.knowledge_index.get("core_count", 0))

    @property
    def knowledge_capsule_count(self) -> int:
        return int(self.knowledge_index.get("capsule_count", 0))

    @property
    def capability_profile_sha256(self) -> str:
        return str(self.capability_profile.get("content_sha256", ""))

    @property
    def capability_modes(self) -> list[str]:
        modes = self.capability_profile.get("modes", [])
        return list(modes) if isinstance(modes, list) else []

    @property
    def asset_index_sha256(self) -> str:
        return str(self.asset_index.get("content_sha256", ""))

    @property
    def asset_count(self) -> int:
        return int(self.asset_index.get("asset_count", 0))

    @property
    def asset_card_count(self) -> int:
        return int(self.asset_card_index.get("card_count", 0))


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_hash(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _portable_label(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return f"external/{path.name}"


def _stable_payload(manifest: BootstrapManifest) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "knowledge_index": manifest.knowledge_index,
        "core_documents": manifest.core_documents,
        "knowledge_file_metadata_sha256": manifest.knowledge_file_metadata_sha256,
        "capability_profile": manifest.capability_profile,
        "asset_index": manifest.asset_index,
        "asset_metadata_sha256": manifest.asset_metadata_sha256,
        "asset_card_index": manifest.asset_card_index,
        "asset_card_metadata_sha256": manifest.asset_card_metadata_sha256,
        "runtime_fingerprints": manifest.runtime_fingerprints,
        "checker_fingerprints": manifest.checker_fingerprints,
        "compiler_version": manifest.compiler_version,
    }


def _knowledge_metadata(
    manifest: BootstrapManifest, index_path: Path, project_root: Path
) -> None:
    raw = index_path.read_bytes()
    data = load_index_metadata(index_path)
    core = data["core"]
    capsules = data["capsules"]
    manifest.knowledge_index = {
        "path": _portable_label(index_path, project_root),
        "schema_version": data["schema_version"],
        "content_sha256": _sha256_bytes(raw),
        "core_count": len(core),
        "capsule_count": len(capsules),
        "index_updated_at": data.get("index_updated_at", ""),
    }
    file_stats: list[dict[str, Any]] = []
    for section, entries in (("core", core), ("capsule", capsules)):
        for entry in entries:
            path = (index_path.parent / entry["path"]).resolve()
            try:
                path.relative_to(index_path.parent.resolve())
            except ValueError as exc:
                raise ValueError(f"knowledge path escapes index: {entry['path']}") from exc
            stat = path.stat()
            file_stats.append({
                "section": section,
                "path": entry["path"],
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            })
            if section != "core":
                continue
            content = path.read_bytes()
            digest = _sha256_bytes(content)
            if digest != entry["content_sha256"] or len(content) != entry["byte_size"]:
                raise ValueError(f"Core content does not match knowledge index: {entry['path']}")
            manifest.core_documents.append({
                "path": entry["path"],
                "content_sha256": digest,
                "byte_size": len(content),
            })
    manifest.core_documents.sort(key=lambda item: item["path"])
    manifest.knowledge_file_metadata_sha256 = _json_hash(file_stats)


def _capability_metadata(
    manifest: BootstrapManifest, profile_path: Path, project_root: Path
) -> None:
    raw = profile_path.read_bytes()
    data = load_profile(profile_path)
    manifest.capability_profile = {
        "path": _portable_label(profile_path, project_root),
        "schema_version": data["schema_version"],
        "profile_id": data["profile_id"],
        "content_sha256": _sha256_bytes(raw),
        "modes": sorted(data["modes"]),
    }


def _asset_metadata(
    manifest: BootstrapManifest, index_path: Path, project_root: Path
) -> None:
    raw = index_path.read_bytes()
    data = load_asset_index_metadata(index_path)
    manifest.asset_index = {
        "path": _portable_label(index_path, project_root),
        "schema_version": data["schema_version"],
        "content_sha256": _sha256_bytes(raw),
        "asset_count": data["asset_count"],
    }
    asset_root = (index_path.parent / data["asset_root"]).resolve()
    metadata: list[dict[str, Any]] = []
    for asset in data["assets"]:
        path = (asset_root / Path(*Path(asset["path"]).parts)).resolve()
        try:
            path.relative_to(asset_root)
        except ValueError as exc:
            raise AssetIndexError(f"asset path escapes root: {asset['path']}") from exc
        exists = path.is_file()
        if asset["status"] == "available" and not exists:
            raise AssetIndexError(f"available asset is missing: {asset['asset_id']}")
        stat = path.stat() if exists else None
        metadata.append({
            "asset_id": asset["asset_id"],
            "path": asset["path"],
            "media_type": asset["media_type"],
            "status": asset["status"],
            "indexed_content_sha256": asset["content_sha256"],
            "indexed_byte_size": asset["byte_size"],
            "actual_byte_size": stat.st_size if stat else None,
            "mtime_ns": stat.st_mtime_ns if stat else None,
        })
    manifest.asset_metadata_sha256 = _json_hash(metadata)


def _asset_card_metadata(
    manifest: BootstrapManifest, index_path: Path, project_root: Path
) -> None:
    raw = index_path.read_bytes()
    data = load_card_index_metadata(index_path)
    manifest.asset_card_index = {
        "path": _portable_label(index_path, project_root),
        "schema_version": data["schema_version"],
        "content_sha256": _sha256_bytes(raw),
        "card_count": data["card_count"],
    }
    metadata: list[dict[str, Any]] = []
    for card in data["cards"]:
        path = (index_path.parent / Path(*card["card_path"].split("/"))).resolve()
        try:
            path.relative_to(index_path.parent.resolve())
        except ValueError as exc:
            raise AssetCardError(f"asset card path escapes root: {card['card_path']}") from exc
        stat = path.stat() if path.is_file() else None
        metadata.append({
            "asset_id": card["asset_id"],
            "media_sha256": card["media_sha256"],
            "card_sha256": card["card_sha256"],
            "status": card["status"],
            "byte_size": stat.st_size if stat else None,
            "mtime_ns": stat.st_mtime_ns if stat else None,
        })
    manifest.asset_card_metadata_sha256 = _json_hash(metadata)


def _runtime_metadata(
    manifest: BootstrapManifest, project_root: Path, module_dir: Path
) -> None:
    for relative in _RUNTIME_FILES:
        path = project_root.joinpath(*relative.split("/"))
        if not path.is_file():
            raise FileNotFoundError(f"runtime instruction/template missing: {relative}")
        manifest.runtime_fingerprints[relative] = _file_hash(path)
    for filename in _CHECKER_FILES:
        path = module_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"local checker missing: {filename}")
        manifest.checker_fingerprints[filename] = _file_hash(path)
    from master_compiler import COMPILER_VERSION

    manifest.compiler_version = COMPILER_VERSION


def load_bootstrap(
    knowledge_index_path: Path | None = None,
    capability_path: Path | None = None,
    asset_index_path: Path | None = None,
    *,
    asset_card_index_path: Path | None = None,
    project_root: Path | None = None,
) -> BootstrapManifest:
    """Build a stable bootstrap manifest without reading capsules or media."""
    manifest = BootstrapManifest()
    root = (project_root or _PROJECT_ROOT).resolve()
    index_path = (knowledge_index_path or _KNOWLEDGE_INDEX).resolve()
    profile_path = (capability_path or _CAPABILITY_PROFILE).resolve()
    assets_path = (asset_index_path or (root / "ASSET_INDEX.json")).resolve()
    cards_path = (asset_card_index_path or (root / "ASSET_CARD_INDEX.json")).resolve()
    operations = (
        ("knowledge_index", lambda: _knowledge_metadata(manifest, index_path, root)),
        ("capability_profile", lambda: _capability_metadata(manifest, profile_path, root)),
        ("asset_index", lambda: _asset_metadata(manifest, assets_path, root)),
        ("asset_card_index", lambda: _asset_card_metadata(manifest, cards_path, root)),
        ("runtime", lambda: _runtime_metadata(manifest, root, _MODULE_DIR)),
    )
    for label, operation in operations:
        try:
            operation()
        except (
            OSError, UnicodeError, ValueError, AssetIndexError, AssetCardError,
            CapabilityProfileError,
        ) as exc:
            manifest.errors.append(f"{label}: {exc}")
    if manifest.ok:
        manifest.manifest_sha256 = _json_hash(_stable_payload(manifest))
    return manifest


def compute_cache_key(
    bootstrap: BootstrapManifest, script_hash: str, scene_indices: list[int]
) -> str:
    """Build the bootstrap/script scope key; detailed stage keys live elsewhere."""
    if not bootstrap.ok or not bootstrap.manifest_sha256:
        raise ValueError("an invalid bootstrap manifest cannot authorize a cache key")
    if not isinstance(script_hash, str) or not script_hash:
        raise ValueError("script_hash cannot be empty")
    if (
        not isinstance(scene_indices, list) or not scene_indices
        or any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in scene_indices)
        or len(scene_indices) != len(set(scene_indices))
    ):
        raise ValueError("scene_indices must be unique positive integers")
    return _json_hash({
        "bootstrap_manifest_sha256": bootstrap.manifest_sha256,
        "script_hash": script_hash,
        "scene_indices": sorted(scene_indices),
    })


def write_bootstrap_manifest(path: Path, manifest: BootstrapManifest) -> None:
    if not manifest.ok or not manifest.manifest_sha256:
        raise ValueError("cannot persist an invalid bootstrap manifest")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    try:
        temporary.write_text(
            json.dumps(asdict(manifest), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Load MODE:P bootstrap metadata.")
    parser.add_argument("--knowledge-index", type=Path)
    parser.add_argument("--capability", type=Path)
    parser.add_argument("--assets", type=Path)
    parser.add_argument("--asset-cards", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--telemetry-session", type=Path, default=None)
    args = parser.parse_args()
    t_started = time.monotonic()
    manifest = load_bootstrap(
        args.knowledge_index, args.capability, args.assets,
        asset_card_index_path=args.asset_cards,
    )
    if args.output and manifest.ok:
        write_bootstrap_manifest(args.output, manifest)
    if args.json:
        print(json.dumps(asdict(manifest), ensure_ascii=False, indent=2))
    elif manifest.ok:
        print(
            f"Bootstrap {manifest.manifest_sha256[:12]}: "
            f"{manifest.knowledge_core_count} Core, "
            f"{manifest.knowledge_capsule_count} capsule metadata, "
            f"{manifest.asset_count} asset metadata, "
            f"{manifest.asset_card_count} text asset cards"
        )
    else:
        for error in manifest.errors:
            print(f"ERROR: {error}", file=sys.stderr)
    result_code = 0 if manifest.ok else 1
    if args.telemetry_session:
        input_paths: list[Path] = []
        for p in (
            args.knowledge_index, args.capability, args.assets, args.asset_cards
        ):
            if p is not None:
                input_paths.append(p)
        if not input_paths:
            input_paths = [
                _KNOWLEDGE_INDEX, _CAPABILITY_PROFILE, _ASSET_INDEX,
                _ASSET_CARD_INDEX,
            ]
        output_paths: list[Path] = []
        if args.output:
            output_paths.append(args.output)
        record_event(
            args.telemetry_session,
            event_type="local",
            stage="bootstrap",
            status="completed" if result_code == 0 else "failed",
            elapsed_s=time.monotonic() - t_started,
            input_bytes=files_byte_size(input_paths),
            output_bytes=files_byte_size(output_paths),
            result_code=result_code,
            error_code="" if result_code == 0 else f"return_{result_code}",
        )
    return result_code


if __name__ == "__main__":
    from cli_stdio import configure_utf8_stdio

    configure_utf8_stdio()
    raise SystemExit(main())
