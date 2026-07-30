"""Layered, content-addressed cache keys for the MODE:P pipeline.

Each stage key names its real inputs.  No hard-coded implementation version is
accepted: source files and runtime instructions are represented by content
fingerprints from the bootstrap manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from asset_indexer import load_asset_index_metadata
from bootstrap_loader import BootstrapManifest, load_bootstrap
from session_lock import session_lock
from pipeline_telemetry import files_byte_size, record_event


CACHE_SCHEMA_VERSION = "2.0"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_STAGES = {
    "core_bundle", "script", "visual_bible", "scene_context",
    "knowledge_context", "capability", "asset", "master", "views", "dp",
    "check",
}


class CacheError(ValueError):
    """Raised when a key, cache manifest, or cached object is invalid."""


@dataclass(frozen=True)
class CacheKey:
    stage: str
    dependencies: dict[str, str]
    schema_version: str = CACHE_SCHEMA_VERSION

    def compute(self) -> str:
        _validate_key(self)
        return _json_hash({
            "schema_version": self.schema_version,
            "stage": self.stage,
            "dependencies": dict(sorted(self.dependencies.items())),
        })


@dataclass(frozen=True)
class CacheOutput:
    path: str
    sha256: str
    byte_size: int


@dataclass
class CacheEntry:
    key: str
    stage: str
    dependencies: dict[str, str]
    created_at: str
    object_root: str
    outputs: list[CacheOutput] = field(default_factory=list)


@dataclass
class CacheManifest:
    schema_version: str = CACHE_SCHEMA_VERSION
    entries: list[CacheEntry] = field(default_factory=list)
    manifest_sha256: str = ""

    def find(self, key: str) -> CacheEntry | None:
        return next((entry for entry in self.entries if entry.key == key), None)

    def store(self, entry: CacheEntry) -> None:
        self.entries = [item for item in self.entries if item.key != entry.key]
        self.entries.append(entry)
        self.entries.sort(key=lambda item: item.key)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256(encoded)


def _content_hash(value: str | bytes | Path, label: str) -> str:
    if isinstance(value, Path):
        if not value.is_file():
            raise CacheError(f"{label} file not found: {value}")
        content = value.read_bytes()
    elif isinstance(value, str):
        content = value.encode("utf-8")
    elif isinstance(value, bytes):
        content = value
    else:
        raise CacheError(f"{label} must be text, bytes, or a file path")
    return _sha256(content)


def _require_hash(value: str, label: str) -> str:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise CacheError(f"{label} must be a lowercase SHA-256")
    return value


def _key_hash(key: CacheKey, expected_stage: str, label: str) -> str:
    if key.stage != expected_stage:
        raise CacheError(f"{label} must be a {expected_stage} cache key")
    return key.compute()


def _validate_key(key: CacheKey) -> None:
    if key.schema_version != CACHE_SCHEMA_VERSION:
        raise CacheError("unsupported cache key schema_version")
    if key.stage not in _STAGES:
        raise CacheError(f"unsupported cache stage: {key.stage}")
    if not isinstance(key.dependencies, dict) or not key.dependencies:
        raise CacheError("cache key dependencies cannot be empty")
    for name, digest in key.dependencies.items():
        if not isinstance(name, str) or not name:
            raise CacheError("cache dependency names must be non-empty strings")
        _require_hash(digest, f"dependency {name}")


def _bootstrap_ready(bootstrap: BootstrapManifest) -> None:
    if not bootstrap.ok or not bootstrap.manifest_sha256:
        raise CacheError("invalid bootstrap cannot authorize cache keys")


def _fingerprint_subset(values: Mapping[str, str], predicate: Any) -> str:
    selected = {key: value for key, value in values.items() if predicate(key)}
    if not selected:
        raise CacheError("required implementation fingerprints are missing")
    for key, value in selected.items():
        _require_hash(value, key)
    return _json_hash(selected)


def build_core_bundle_key(bootstrap: BootstrapManifest) -> CacheKey:
    _bootstrap_ready(bootstrap)
    core_hash = _json_hash(bootstrap.core_documents)
    instruction_hash = _fingerprint_subset(
        bootstrap.runtime_fingerprints,
        lambda path: path.endswith(("director_agent.md", "dp_agent.md", "mode-p-director.md", "mode-p-dp.md")),
    )
    template_hash = _fingerprint_subset(
        bootstrap.runtime_fingerprints,
        lambda path: path.endswith(("director_master_template.md", "shot_manifest_schema.json")),
    )
    view_implementation = bootstrap.checker_fingerprints.get("view_deriver.py", "")
    return CacheKey("core_bundle", {
        "core_documents": core_hash,
        "director_dp_instructions": instruction_hash,
        "master_templates": template_hash,
        "view_deriver": _require_hash(view_implementation, "view_deriver fingerprint"),
    })


def build_script_key(script: str | bytes | Path, bootstrap: BootstrapManifest) -> CacheKey:
    _bootstrap_ready(bootstrap)
    parser = bootstrap.checker_fingerprints.get("script_ingest.py", "")
    return CacheKey("script", {
        "script_content": _content_hash(script, "script"),
        "script_parser": _require_hash(parser, "script parser fingerprint"),
    })


def build_visual_bible_key(
    script_key: CacheKey,
    core_bundle_key: CacheKey,
    user_visual_constraints: str | bytes | Path,
    project_continuity: str | bytes | Path,
) -> CacheKey:
    return CacheKey("visual_bible", {
        "script_key": _key_hash(script_key, "script", "script_key"),
        "core_bundle_key": _key_hash(core_bundle_key, "core_bundle", "core_bundle_key"),
        "user_visual_constraints": _content_hash(user_visual_constraints, "user constraints"),
        "project_continuity": _content_hash(project_continuity, "project continuity"),
    })


def build_scene_context_key(
    scene_source: str | bytes | Path,
    adjacent_continuity: str | bytes | Path,
    visual_bible_excerpt: str | bytes | Path,
) -> CacheKey:
    return CacheKey("scene_context", {
        "scene_source": _content_hash(scene_source, "scene source"),
        "adjacent_continuity": _content_hash(adjacent_continuity, "adjacent continuity"),
        "visual_bible_excerpt": _content_hash(visual_bible_excerpt, "Visual Bible excerpt"),
    })


def build_knowledge_context_key(
    bootstrap: BootstrapManifest,
    selected_capsules: Mapping[str, Path],
    validated_experiences: Mapping[str, Path],
) -> CacheKey:
    _bootstrap_ready(bootstrap)
    retriever = bootstrap.checker_fingerprints.get("context_retriever.py", "")
    capsule_hashes = {
        name: _content_hash(path, f"capsule {name}")
        for name, path in sorted(selected_capsules.items())
    }
    experience_hashes = {
        name: _content_hash(path, f"validated experience {name}")
        for name, path in sorted(validated_experiences.items())
    }
    return CacheKey("knowledge_context", {
        "retriever": _require_hash(retriever, "context retriever fingerprint"),
        "selected_capsules": _json_hash(capsule_hashes),
        "validated_experiences": _json_hash(experience_hashes),
    })


def build_capability_key(bootstrap: BootstrapManifest) -> CacheKey:
    _bootstrap_ready(bootstrap)
    return CacheKey("capability", {
        "profile_content": _require_hash(
            bootstrap.capability_profile_sha256, "capability profile hash"
        ),
        "profile_identity": _json_hash({
            "schema_version": bootstrap.capability_profile.get("schema_version"),
            "profile_id": bootstrap.capability_profile.get("profile_id"),
        }),
    })


def build_asset_key(asset_index_path: Path, selected_asset_ids: list[str]) -> CacheKey:
    if len(selected_asset_ids) != len(set(selected_asset_ids)):
        raise CacheError("selected asset IDs must be unique")
    data = load_asset_index_metadata(asset_index_path)
    indexed = {item["asset_id"]: item for item in data["assets"]}
    missing = sorted(set(selected_asset_ids) - set(indexed))
    if missing:
        raise CacheError(f"selected assets are absent from ASSET_INDEX: {missing}")
    selected = {
        asset_id: {
            "content_sha256": indexed[asset_id]["content_sha256"],
            "status": indexed[asset_id]["status"],
            "media_type": indexed[asset_id]["media_type"],
            "responsibilities": indexed[asset_id]["responsibilities"],
        }
        for asset_id in sorted(selected_asset_ids)
    }
    return CacheKey("asset", {
        "selected_asset_records": _json_hash(selected),
        "asset_index_schema": _json_hash(data["schema_version"]),
    })


def build_master_key(
    scene_context_key: CacheKey,
    knowledge_context_key: CacheKey,
    capability_key: CacheKey,
    asset_key: CacheKey,
    bootstrap: BootstrapManifest,
) -> CacheKey:
    _bootstrap_ready(bootstrap)
    director = _fingerprint_subset(
        bootstrap.runtime_fingerprints,
        lambda path: path.endswith(("director_agent.md", "mode-p-director.md")),
    )
    return CacheKey("master", {
        "scene_context_key": _key_hash(scene_context_key, "scene_context", "scene context"),
        "knowledge_context_key": _key_hash(knowledge_context_key, "knowledge_context", "knowledge context"),
        "capability_key": _key_hash(capability_key, "capability", "capability"),
        "asset_key": _key_hash(asset_key, "asset", "asset"),
        "director_instructions": director,
    })


def build_views_key(master: str | bytes | Path, bootstrap: BootstrapManifest) -> CacheKey:
    _bootstrap_ready(bootstrap)
    director = _fingerprint_subset(
        bootstrap.runtime_fingerprints,
        lambda path: path.endswith(("director_agent.md", "mode-p-director.md")),
    )
    return CacheKey("views", {
        "master_content": _content_hash(master, "Master"),
        "director_instructions": director,
        "view_deriver": _require_hash(
            bootstrap.checker_fingerprints.get("view_deriver.py", ""),
            "view deriver fingerprint",
        ),
    })


def build_dp_key(
    *,
    script_facts: str | bytes | Path,
    scene_context: str | bytes | Path,
    visual_bible_excerpt: str | bytes | Path,
    master: str | bytes | Path,
    storyboard: str | bytes | Path,
    video_prompt: str | bytes | Path,
    reference_plan: str | bytes | Path,
    capability_key: CacheKey,
    bootstrap: BootstrapManifest,
) -> CacheKey:
    _bootstrap_ready(bootstrap)
    dp_instructions = _fingerprint_subset(
        bootstrap.runtime_fingerprints,
        lambda path: path.endswith(("dp_agent.md", "mode-p-dp.md")),
    )
    return CacheKey("dp", {
        "script_facts": _content_hash(script_facts, "Script Facts"),
        "scene_context": _content_hash(scene_context, "scene context"),
        "visual_bible_excerpt": _content_hash(visual_bible_excerpt, "Visual Bible excerpt"),
        "master": _content_hash(master, "Master"),
        "storyboard": _content_hash(storyboard, "Storyboard"),
        "video_prompt": _content_hash(video_prompt, "Video Prompt"),
        "reference_plan": _content_hash(reference_plan, "reference plan"),
        "capability_key": _key_hash(capability_key, "capability", "capability"),
        "dp_instructions": dp_instructions,
    })


def build_check_key(
    *,
    master: str | bytes | Path,
    manifest: str | bytes | Path,
    storyboard: str | bytes | Path,
    video_prompt: str | bytes | Path,
    capability_key: CacheKey,
    asset_key: CacheKey,
    checker_names: list[str],
    bootstrap: BootstrapManifest,
) -> CacheKey:
    _bootstrap_ready(bootstrap)
    if not checker_names or len(checker_names) != len(set(checker_names)):
        raise CacheError("checker_names must contain unique checker source names")
    implementations: dict[str, str] = {}
    for name in sorted(checker_names):
        digest = bootstrap.checker_fingerprints.get(name, "")
        implementations[name] = _require_hash(digest, f"checker {name}")
    return CacheKey("check", {
        "master": _content_hash(master, "Master"),
        "manifest": _content_hash(manifest, "Manifest"),
        "storyboard": _content_hash(storyboard, "Storyboard"),
        "video_prompt": _content_hash(video_prompt, "Video Prompt"),
        "capability_key": _key_hash(capability_key, "capability", "capability"),
        "asset_key": _key_hash(asset_key, "asset", "asset"),
        "checker_implementations": _json_hash(implementations),
    })


def _safe_relative(raw: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise CacheError("cache output paths must be portable and relative")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CacheError(f"cache output path escapes object root: {raw}")
    return path


def _manifest_hash(data: dict[str, Any]) -> str:
    return _json_hash({key: value for key, value in data.items() if key != "manifest_sha256"})


def _validate_manifest(data: Any) -> CacheManifest:
    expected = {"schema_version", "entries", "manifest_sha256"}
    if not isinstance(data, dict) or set(data) != expected:
        raise CacheError("cache manifest fields do not match schema")
    if data["schema_version"] != CACHE_SCHEMA_VERSION:
        raise CacheError("unsupported cache manifest schema_version")
    if data["manifest_sha256"] != _manifest_hash(data):
        raise CacheError("cache manifest integrity hash mismatch")
    if not isinstance(data["entries"], list):
        raise CacheError("cache manifest entries must be an array")
    entries: list[CacheEntry] = []
    keys: set[str] = set()
    for raw in data["entries"]:
        required = {"key", "stage", "dependencies", "created_at", "object_root", "outputs"}
        if not isinstance(raw, dict) or set(raw) != required:
            raise CacheError("cache entry fields do not match schema")
        _require_hash(raw["key"], "cache entry key")
        key = CacheKey(raw["stage"], raw["dependencies"])
        if key.compute() != raw["key"]:
            raise CacheError("cache entry key does not match dependencies")
        if raw["key"] in keys:
            raise CacheError("cache manifest contains duplicate keys")
        keys.add(raw["key"])
        try:
            datetime.fromisoformat(raw["created_at"])
        except (TypeError, ValueError) as exc:
            raise CacheError("cache entry created_at is invalid") from exc
        _safe_relative(raw["object_root"])
        if not isinstance(raw["outputs"], list) or not raw["outputs"]:
            raise CacheError("cache entry outputs are empty")
        outputs: list[CacheOutput] = []
        seen: set[str] = set()
        for output in raw["outputs"]:
            if not isinstance(output, dict) or set(output) != {"path", "sha256", "byte_size"}:
                raise CacheError("cache output fields are invalid")
            path = _safe_relative(output["path"]).as_posix()
            if path.casefold() in seen:
                raise CacheError("cache output paths are duplicated")
            seen.add(path.casefold())
            _require_hash(output["sha256"], "cache output hash")
            size = output["byte_size"]
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                raise CacheError("cache output byte_size is invalid")
            outputs.append(CacheOutput(path, output["sha256"], size))
        entries.append(CacheEntry(
            key=raw["key"], stage=raw["stage"], dependencies=raw["dependencies"],
            created_at=raw["created_at"], object_root=raw["object_root"], outputs=outputs,
        ))
    return CacheManifest(CACHE_SCHEMA_VERSION, entries, data["manifest_sha256"])


def _manifest_data(manifest: CacheManifest) -> dict[str, Any]:
    data = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "entries": [asdict(entry) for entry in manifest.entries],
        "manifest_sha256": "",
    }
    data["manifest_sha256"] = _manifest_hash(data)
    manifest.manifest_sha256 = data["manifest_sha256"]
    return data


def load_cache_manifest(cache_dir: Path) -> CacheManifest:
    path = cache_dir / "CACHE_MANIFEST.json"
    if not path.is_file():
        empty = CacheManifest()
        _manifest_data(empty)
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CacheError(f"cannot read cache manifest: {exc}") from exc
    return _validate_manifest(data)


def _save_cache_manifest_unlocked(cache_dir: Path, manifest: CacheManifest) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "CACHE_MANIFEST.json"
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    try:
        temporary.write_text(
            json.dumps(_manifest_data(manifest), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def save_cache_manifest(cache_dir: Path, manifest: CacheManifest) -> None:
    with session_lock(cache_dir):
        _save_cache_manifest_unlocked(cache_dir, manifest)


def store_in_cache(
    cache_dir: Path,
    key: CacheKey,
    output_files: Mapping[str, Path],
) -> CacheEntry:
    _validate_key(key)
    if not output_files:
        raise CacheError("cannot cache an empty output set")
    computed = key.compute()
    normalized: list[tuple[PurePosixPath, Path]] = []
    seen: set[str] = set()
    for raw, source in output_files.items():
        relative = _safe_relative(raw)
        if relative.as_posix().casefold() in seen:
            raise CacheError("cache output paths are duplicated")
        seen.add(relative.as_posix().casefold())
        source = Path(source)
        if not source.is_file():
            raise CacheError(f"cache source is not a file: {source}")
        normalized.append((relative, source))
    with session_lock(cache_dir):
        object_root = Path("objects") / computed[:2] / computed
        destination = cache_dir / object_root
        temporary = cache_dir / "objects" / f".tmp-{computed}-{os.getpid()}-{time.time_ns()}"
        temporary.mkdir(parents=True)
        outputs: list[CacheOutput] = []
        try:
            for relative, source in normalized:
                target = temporary.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                outputs.append(CacheOutput(
                    relative.as_posix(), _content_hash(target, "cached output"), target.stat().st_size
                ))
            if destination.exists():
                shutil.rmtree(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary.replace(destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        entry = CacheEntry(
            key=computed,
            stage=key.stage,
            dependencies=dict(sorted(key.dependencies.items())),
            created_at=datetime.now(timezone.utc).isoformat(),
            object_root=object_root.as_posix(),
            outputs=sorted(outputs, key=lambda item: item.path.casefold()),
        )
        manifest = load_cache_manifest(cache_dir)
        manifest.store(entry)
        _save_cache_manifest_unlocked(cache_dir, manifest)
        return entry


def _entry_current(cache_dir: Path, entry: CacheEntry) -> bool:
    root = cache_dir.joinpath(*PurePosixPath(entry.object_root).parts)
    if not root.is_dir():
        return False
    expected = {item.path: item for item in entry.outputs}
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*") if path.is_file() and not path.is_symlink()
    }
    if actual != set(expected):
        return False
    for relative, output in expected.items():
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.stat().st_size != output.byte_size or _content_hash(path, "cached output") != output.sha256:
            return False
    return True


def lookup_cache(cache_dir: Path, key: CacheKey) -> CacheEntry | None:
    """Return only a fully verified hit; malformed or damaged cache is a miss."""
    try:
        manifest = load_cache_manifest(cache_dir)
        entry = manifest.find(key.compute())
        if entry is None or entry.stage != key.stage or entry.dependencies != key.dependencies:
            return None
        return entry if _entry_current(cache_dir, entry) else None
    except (CacheError, OSError, UnicodeError):
        return None


def restore_cache(
    cache_dir: Path,
    entry: CacheEntry,
    destination_root: Path,
) -> dict[str, Path]:
    """Restore verified cache outputs with per-file atomic replacement."""
    if not _entry_current(cache_dir, entry):
        raise CacheError("cache entry is missing or damaged")
    object_root = cache_dir.joinpath(*PurePosixPath(entry.object_root).parts)
    restored: dict[str, Path] = {}
    staged: list[tuple[Path, Path, CacheOutput]] = []
    try:
        for output in entry.outputs:
            relative = _safe_relative(output.path)
            source = object_root.joinpath(*relative.parts)
            target = destination_root.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(
                f".{target.name}.cache-{uuid.uuid4().hex}.tmp"
            )
            shutil.copy2(source, temporary)
            if (
                temporary.stat().st_size != output.byte_size
                or _content_hash(temporary, "restored cache output") != output.sha256
            ):
                raise CacheError(f"restored cache output failed hash check: {output.path}")
            staged.append((temporary, target, output))
        for temporary, target, output in staged:
            temporary.replace(target)
            restored[output.path] = target
        return restored
    finally:
        for temporary, _, _ in staged:
            temporary.unlink(missing_ok=True)


_store_in_cache_impl = store_in_cache
_lookup_cache_impl = lookup_cache


def _telemetry_session(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    raw = os.environ.get("MODE_P_TELEMETRY_SESSION", "").strip()
    return Path(raw) if raw else None


def store_in_cache(
    cache_dir: Path,
    key: CacheKey,
    output_files: Mapping[str, Path],
    *,
    telemetry_session: Path | None = None,
) -> CacheEntry:
    started = time.monotonic()
    entry = _store_in_cache_impl(cache_dir, key, output_files)
    root = _telemetry_session(telemetry_session)
    if root is not None:
        record_event(
            root, event_type="cache", stage=key.stage,
            elapsed_s=time.monotonic() - started,
            input_bytes=files_byte_size(output_files.values()),
            output_bytes=sum(item.byte_size for item in entry.outputs),
            cache_status="store",
        )
    return entry


def lookup_cache(
    cache_dir: Path,
    key: CacheKey,
    *,
    telemetry_session: Path | None = None,
) -> CacheEntry | None:
    started = time.monotonic()
    entry = _lookup_cache_impl(cache_dir, key)
    root = _telemetry_session(telemetry_session)
    if root is not None:
        record_event(
            root, event_type="cache", stage=key.stage,
            elapsed_s=time.monotonic() - started,
            output_bytes=(sum(item.byte_size for item in entry.outputs) if entry else 0),
            cache_status="hit" if entry else "miss",
        )
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a MODE:P script cache key.")
    parser.add_argument("script", type=Path)
    args = parser.parse_args()
    try:
        key = build_script_key(args.script, load_bootstrap())
        print(key.compute())
        return 0
    except (CacheError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
