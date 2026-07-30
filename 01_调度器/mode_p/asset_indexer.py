"""Build and validate the content-addressed MODE:P reference asset index."""

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


_DEFAULT_INDEX = Path(__file__).parent.parent.parent / "ASSET_INDEX.json"
_MEDIA_BY_SUFFIX = {
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".mp4": "video", ".mov": "video",
    ".mp3": "audio", ".wav": "audio",
}
VALID_MEDIA_TYPES = set(_MEDIA_BY_SUFFIX.values())
VALID_RESPONSIBILITIES = {
    "identity", "wardrobe", "location", "continuity", "action", "camera",
    "style", "audio", "first_frame", "last_frame",
}
VALID_STATUSES = {"available", "missing", "deprecated"}
_ASSET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_TOP_FIELDS = {
    "schema_version", "description", "updated_at", "asset_root",
    "asset_count", "assets",
}
_ASSET_FIELDS = {
    "asset_id", "path", "media_type", "content_sha256", "byte_size",
    "status", "responsibilities",
}


class AssetIndexError(ValueError):
    """Raised when an asset index cannot safely be used."""


def _portable_relative(raw: Any, field: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise AssetIndexError(f"{field} must be a portable relative path")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise AssetIndexError(f"{field} must not escape its root")
    return path


def _resolve_beneath(root: Path, raw: Any, field: str) -> Path:
    portable = _portable_relative(raw, field)
    candidate = (root / Path(*portable.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise AssetIndexError(f"{field} resolves outside its root") from exc
    return candidate


def _validate_structure(data: Any, index_path: Path) -> list[str]:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["index root must be an object"]
    if set(data) != _TOP_FIELDS:
        issues.append(f"top-level fields must be exactly {sorted(_TOP_FIELDS)}")
    if data.get("schema_version") != "1.1":
        issues.append("schema_version must be 1.1")
    if not isinstance(data.get("description"), str) or not data.get("description", "").strip():
        issues.append("description must be a non-empty string")
    try:
        datetime.fromisoformat(data.get("updated_at"))
    except (TypeError, ValueError):
        issues.append("updated_at must be ISO-8601")

    try:
        asset_root = _resolve_beneath(index_path.parent, data.get("asset_root"), "asset_root")
    except AssetIndexError as exc:
        issues.append(str(exc))
        asset_root = index_path.parent.resolve()

    assets = data.get("assets")
    if not isinstance(assets, list):
        issues.append("assets must be an array")
        return issues
    if data.get("asset_count") != len(assets):
        issues.append("asset_count does not match assets length")

    ids: list[str] = []
    paths: list[str] = []
    for number, asset in enumerate(assets, 1):
        label = f"assets[{number}]"
        if not isinstance(asset, dict) or set(asset) != _ASSET_FIELDS:
            issues.append(f"{label} fields must be exactly {sorted(_ASSET_FIELDS)}")
            continue
        asset_id = asset["asset_id"]
        if not isinstance(asset_id, str) or not _ASSET_ID_RE.fullmatch(asset_id):
            issues.append(f"{label}.asset_id is invalid")
        else:
            ids.append(asset_id)
        try:
            _resolve_beneath(asset_root, asset["path"], f"{label}.path")
            paths.append(asset["path"])
        except AssetIndexError as exc:
            issues.append(str(exc))
        if asset["media_type"] not in VALID_MEDIA_TYPES:
            issues.append(f"{label}.media_type is invalid")
        if asset["status"] not in VALID_STATUSES:
            issues.append(f"{label}.status is invalid")
        if not isinstance(asset["content_sha256"], str) or not _HASH_RE.fullmatch(asset["content_sha256"]):
            issues.append(f"{label}.content_sha256 is invalid")
        if (
            isinstance(asset["byte_size"], bool)
            or not isinstance(asset["byte_size"], int)
            or asset["byte_size"] < 0
        ):
            issues.append(f"{label}.byte_size is invalid")
        responsibilities = asset["responsibilities"]
        if (
            not isinstance(responsibilities, list)
            or any(item not in VALID_RESPONSIBILITIES for item in responsibilities)
            or len(responsibilities) != len(set(responsibilities))
        ):
            issues.append(f"{label}.responsibilities are invalid")
    if len(ids) != len(set(ids)):
        issues.append("asset_id values must be unique")
    if len(paths) != len(set(paths)):
        issues.append("asset paths must be unique")
    return issues


def _read_index(index_path: Path, *, verify_files: bool) -> dict[str, Any]:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AssetIndexError(f"cannot read asset index: {exc}") from exc
    issues = _validate_structure(data, index_path)
    if not issues and verify_files:
        asset_root = _resolve_beneath(index_path.parent, data["asset_root"], "asset_root")
        for asset in data["assets"]:
            if asset["status"] != "available":
                continue
            path = _resolve_beneath(asset_root, asset["path"], f"asset {asset['asset_id']} path")
            if not path.is_file():
                issues.append(f"asset {asset['asset_id']}: available file is missing")
                continue
            content = path.read_bytes()
            actual = hashlib.sha256(content).hexdigest()
            if actual != asset["content_sha256"]:
                issues.append(f"asset {asset['asset_id']}: content hash mismatch")
            if len(content) != asset["byte_size"]:
                issues.append(f"asset {asset['asset_id']}: byte_size mismatch")
    if issues:
        raise AssetIndexError("; ".join(issues))
    return data


def load_asset_index(index_path: Path = _DEFAULT_INDEX) -> dict[str, Any]:
    """Load a strict index whose available files and hashes are current."""
    return _read_index(index_path, verify_files=True)


def load_asset_index_metadata(index_path: Path = _DEFAULT_INDEX) -> dict[str, Any]:
    """Validate index metadata without reading image, video, or audio bodies."""
    return _read_index(index_path, verify_files=False)


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _new_asset_id(relative_path: str, used: set[str]) -> str:
    pure = PurePosixPath(relative_path)
    readable = re.sub(r"[^A-Za-z0-9_-]+", "_", "__".join(pure.with_suffix("").parts))
    readable = readable.strip("_")[:80] or "asset"
    suffix = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:10]
    candidate = f"{readable}-{suffix}"
    if candidate in used:
        raise AssetIndexError(f"deterministic asset_id collision for {relative_path}")
    return candidate


def scan_directory(asset_dir: Path, output_path: Path | None = None) -> dict[str, Any]:
    """Scan assets, preserve stable IDs/metadata, and atomically update the index."""
    output = output_path or _DEFAULT_INDEX
    asset_dir = asset_dir.resolve()
    if not asset_dir.is_dir():
        raise AssetIndexError(f"asset directory not found: {asset_dir}")
    output_parent = output.parent.resolve()
    try:
        root_relative = asset_dir.relative_to(output_parent).as_posix() or "."
    except ValueError as exc:
        raise AssetIndexError("asset directory must be inside the index directory") from exc

    previous: dict[str, Any] | None = None
    if output.is_file():
        previous = _read_index(output, verify_files=False)
        if previous["asset_root"] != root_relative:
            raise AssetIndexError("existing asset_root differs from the scanned directory")
    previous_by_path = {
        asset["path"]: asset for asset in previous["assets"]
    } if previous else {}
    used_ids = {asset["asset_id"] for asset in previous_by_path.values()}

    discovered: dict[str, dict[str, Any]] = {}
    for path in sorted(asset_dir.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not path.is_file() or path.suffix.lower() not in _MEDIA_BY_SUFFIX:
            continue
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(asset_dir).as_posix()
        except ValueError as exc:
            raise AssetIndexError(f"asset symlink escapes root: {path}") from exc
        content = resolved.read_bytes()
        former = previous_by_path.get(relative)
        if former:
            asset_id = former["asset_id"]
            responsibilities = former["responsibilities"]
            status = "deprecated" if former["status"] == "deprecated" else "available"
        else:
            asset_id = _new_asset_id(relative, used_ids)
            used_ids.add(asset_id)
            responsibilities = []
            status = "available"
        discovered[relative] = {
            "asset_id": asset_id,
            "path": relative,
            "media_type": _MEDIA_BY_SUFFIX[resolved.suffix.lower()],
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "byte_size": len(content),
            "status": status,
            "responsibilities": responsibilities,
        }

    for relative, former in previous_by_path.items():
        if relative not in discovered:
            retained = dict(former)
            retained["status"] = "deprecated" if former["status"] == "deprecated" else "missing"
            discovered[relative] = retained

    assets = sorted(discovered.values(), key=lambda item: item["asset_id"])
    semantic = {
        "schema_version": "1.1",
        "description": "MODE:P reference assets with stable IDs, content hashes, availability, and permitted responsibilities.",
        "asset_root": root_relative,
        "asset_count": len(assets),
        "assets": assets,
    }
    previous_semantic = None
    if previous:
        previous_semantic = {key: value for key, value in previous.items() if key != "updated_at"}
    index = {
        **semantic,
        "updated_at": (
            previous["updated_at"]
            if previous and previous_semantic == semantic
            else datetime.now(timezone.utc).isoformat()
        ),
    }
    _write_atomic(output, index)
    load_asset_index(output)
    return index


def validate_assets(index_path: Path) -> tuple[bool, list[str]]:
    try:
        load_asset_index(index_path)
        return True, []
    except AssetIndexError as exc:
        return False, [str(exc)]


def update_status(index_path: Path, asset_id: str, status: str) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise AssetIndexError(f"invalid status: {status}")
    data = _read_index(index_path, verify_files=False)
    target = next((asset for asset in data["assets"] if asset["asset_id"] == asset_id), None)
    if target is None:
        raise AssetIndexError(f"unknown asset_id: {asset_id}")
    if status == "available":
        asset_root = _resolve_beneath(index_path.parent, data["asset_root"], "asset_root")
        path = _resolve_beneath(asset_root, target["path"], "asset path")
        if not path.is_file():
            raise AssetIndexError("cannot mark a missing file available; rescan after restoring it")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != target["content_sha256"]:
            raise AssetIndexError("cannot mark changed content available; rescan to update its hash")
    if target["status"] != status:
        target["status"] = status
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_atomic(index_path, data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the MODE:P asset index.")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan")
    scan.add_argument("asset_dir", type=Path)
    scan.add_argument("-o", "--output", type=Path, default=_DEFAULT_INDEX)
    validate = sub.add_parser("validate")
    validate.add_argument("index", type=Path, nargs="?", default=_DEFAULT_INDEX)
    status_parser = sub.add_parser("status")
    status_parser.add_argument("index", type=Path)
    status_parser.add_argument("asset_id")
    status_parser.add_argument("status", choices=sorted(VALID_STATUSES))
    args = parser.parse_args()
    try:
        if args.command == "scan":
            data = scan_directory(args.asset_dir, args.output)
            print(f"Scanned {data['asset_count']} assets -> {args.output}")
        elif args.command == "validate":
            load_asset_index(args.index)
            print("Asset index valid; available files and hashes match.")
        else:
            update_status(args.index, args.asset_id, args.status)
            print(f"Asset '{args.asset_id}' status set to '{args.status}'.")
        return 0
    except (AssetIndexError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Asset index operation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
