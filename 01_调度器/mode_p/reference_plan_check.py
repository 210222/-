"""Check generation mode and reference asset plan from SHOT_MANIFEST.json.

This is a deterministic local checker. It verifies:
- Generation mode is valid and consistent with asset list
- Asset IDs are unique within a shot
- Responsibilities are valid and non-conflicting
- Optional: asset files exist (when ASSET_INDEX is provided)

It MUST NOT judge whether the Director chose the right mode or assets.
It MUST NOT evaluate whether assets are aesthetically suitable.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import jsonschema

from asset_indexer import AssetIndexError, load_asset_index
from sd2_capability_manager import CapabilityProfileError, load_profile


SCHEMA_PATH = Path(__file__).with_name("shot_manifest_schema.json")
DEFAULT_CAPABILITY_PROFILE = Path(__file__).with_name("sd2_capability_profile.json")
with open(SCHEMA_PATH, encoding="utf-8") as _schema_file:
    _SCHEMA = json.load(_schema_file)

VALID_RESPONSIBILITIES = frozenset({
    "identity", "wardrobe", "location", "continuity",
    "action", "camera", "style", "audio", "first_frame", "last_frame",
})

# Mode requirements
TEXT_ONLY = "text_only"
FIRST_LAST_FRAME = "first_last_frame"
OMNI_REFERENCE = "omni_reference"


@dataclass
class RefIssue:
    shot_id: str
    category: str  # "mode", "asset_count", "responsibility", "duplicate", "file", "conflict"
    detail: str


@dataclass
class RefReport:
    issues: list[RefIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------

def check_references(manifest_path: Path, asset_index_path: Path | None = None,
                     capability_profile_path: Path | None = None) -> RefReport:
    """Check facts from Manifest, capability profile, and optional asset index."""
    report = RefReport()

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        jsonschema.validate(manifest, _SCHEMA)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError,
            jsonschema.ValidationError) as exc:
        report.issues.append(RefIssue("MANIFEST", "manifest", str(exc)))
        return report

    profile_path = capability_profile_path or DEFAULT_CAPABILITY_PROFILE
    try:
        capability_profile = load_profile(profile_path)
        mode_capabilities = capability_profile["modes"]
    except (CapabilityProfileError, OSError, UnicodeDecodeError,
            json.JSONDecodeError, KeyError, TypeError) as exc:
        report.issues.append(RefIssue("CONFIG", "capability", str(exc)))
        return report

    asset_entries: dict[str, dict] = {}
    asset_root: Path | None = None
    asset_index_loaded = asset_index_path is not None
    if asset_index_path is not None:
        try:
            asset_index = load_asset_index(asset_index_path)
            asset_entries = {entry["asset_id"]: entry for entry in asset_index["assets"]}
            asset_root = (asset_index_path.parent / asset_index["asset_root"]).resolve()
        except (AssetIndexError, OSError, UnicodeDecodeError,
                json.JSONDecodeError, KeyError, TypeError) as exc:
            report.issues.append(RefIssue("ASSET_INDEX", "index", str(exc)))
            return report

    for shot in manifest["shots"]:
        _check_shot_references(
            shot, capability_profile, mode_capabilities, asset_entries, asset_index_path,
            asset_root, asset_index_loaded, report,
        )

    return report


# ---------------------------------------------------------------------------
# per-shot checks
# ---------------------------------------------------------------------------

def _check_shot_references(shot: dict, capability_profile: dict,
                           mode_capabilities: dict,
                           asset_entries: dict[str, dict],
                           asset_index_path: Path | None,
                           asset_root: Path | None,
                           asset_index_loaded: bool,
                           report: RefReport) -> None:
    shot_id = shot["shot_id"]
    mode = shot["generation_mode"]
    assets: list[dict] = shot.get("reference_assets", [])

    # 1. Mode capability is configuration truth, not a hard-coded guess.
    capability = mode_capabilities.get(mode)
    if not isinstance(capability, dict):
        report.issues.append(RefIssue(
            shot_id, "mode", f"Mode '{mode}' is absent from capability profile"
        ))
        return

    # 2. Verify the Director-selected mode; never choose a mode here.
    count_spec = capability["asset_count"]
    minimum = count_spec["min"]
    maximum = count_spec["max"]
    if count_spec["enforcement"] == "hard" and not minimum <= len(assets) <= maximum:
        report.issues.append(RefIssue(
            shot_id, "asset_count",
            f"Mode '{mode}' allows {minimum}..{maximum} assets, got {len(assets)}",
        ))

    actual_responsibilities = [asset["responsibility"] for asset in assets]
    for responsibility in capability["required_responsibilities"]:
        if actual_responsibilities.count(responsibility) != 1:
            report.issues.append(RefIssue(
                shot_id, "responsibility",
                f"Mode '{mode}' requires exactly one '{responsibility}' asset",
            ))

    # 4. Valid responsibilities
    for a in assets:
        resp = a.get("responsibility", "")
        if resp not in VALID_RESPONSIBILITIES:
            report.issues.append(RefIssue(
                shot_id, "responsibility",
                f"Asset '{a['asset_id']}' has invalid responsibility '{resp}'; "
                f"must be one of {sorted(VALID_RESPONSIBILITIES)}",
            ))

    # 5. Asset-index facts (when provided). Multiple assets may share a
    # responsibility, and one asset may have explicit multiple bindings.
    if asset_index_loaded:
        media_spec = capability["allowed_media_types"]
        allowed_media = set(media_spec["values"])
        media_counts: dict[str, int] = {}
        for a in assets:
            aid = a["asset_id"]
            entry = asset_entries.get(aid)
            if entry is None:
                report.issues.append(RefIssue(
                    shot_id, "file",
                    f"Asset '{aid}' not found in ASSET_INDEX",
                ))
                continue
            if entry["status"] != "available":
                report.issues.append(RefIssue(
                    shot_id, "file",
                    f"Asset '{aid}' is not available (status: {entry['status']})",
                ))
                continue
            media_type = entry.get("media_type")
            if media_spec["enforcement"] == "hard" and media_type not in allowed_media:
                report.issues.append(RefIssue(
                    shot_id, "capability",
                    f"Asset '{aid}' media_type '{media_type}' is not allowed for '{mode}'",
                ))
            if isinstance(media_type, str):
                media_counts[media_type] = media_counts.get(media_type, 0) + 1
            supported = entry.get("responsibilities")
            if isinstance(supported, list) and a["responsibility"] not in supported:
                report.issues.append(RefIssue(
                    shot_id, "responsibility",
                    f"Asset '{aid}' does not support '{a['responsibility']}'",
                ))
            raw_path = entry.get("path")
            if not isinstance(raw_path, str) or not raw_path.strip():
                report.issues.append(RefIssue(
                    shot_id, "file", f"Asset '{aid}' has no usable path",
                ))
                continue
            file_path = asset_root / Path(*PurePosixPath(raw_path).parts) if asset_root else Path(raw_path)
            if not file_path.is_file():
                report.issues.append(RefIssue(
                    shot_id, "file", f"Asset file missing: {file_path}",
                ))

        if mode == OMNI_REFERENCE:
            limits = capability_profile["model_capabilities"]["multimodal_reference_limits"]
            if limits["enforcement"] == "hard":
                for media_type in ("image", "video", "audio"):
                    if media_counts.get(media_type, 0) > limits[media_type]:
                        report.issues.append(RefIssue(
                            shot_id, "asset_count",
                            f"Mode '{mode}' allows at most {limits[media_type]} "
                            f"{media_type} assets, got {media_counts[media_type]}",
                        ))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check generation mode and reference asset plan."
    )
    parser.add_argument("manifest", type=Path, help="Path to SHOT_MANIFEST.json")
    parser.add_argument("--assets", type=Path, default=None,
                        help="Optional path to ASSET_INDEX.json for file existence check")
    parser.add_argument("--capabilities", type=Path, default=None,
                        help="Path to SD2 capability profile (default: bundled profile)")
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"File not found: {args.manifest}", file=sys.stderr)
        return 2

    report = check_references(args.manifest, args.assets, args.capabilities)

    if report.ok:
        print("Reference plan check passed.")
        return 0

    for issue in report.issues:
        print(f"[{issue.shot_id}] {issue.category}: {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
