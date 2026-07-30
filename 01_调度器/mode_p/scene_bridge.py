"""Committed cross-batch continuity state for MODE:P.

The module never invents continuity.  It records canonical opening/closing
state from already delivered scene manifests, carries that committed state into
the next batch, and checks the next batch's first opening state when the
Director declares a continuous handoff.  Elliptical and scene-reset handoffs
remain semantic DP decisions but still require the prior commit in context.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import jsonschema
from pipeline_telemetry import files_byte_size, record_event


_SCHEMA_PATH = Path(__file__).with_name("shot_manifest_schema.json")
_SHOT_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_PLACEHOLDER_RE = re.compile(r"\[Director:|<Name>|<N>", re.IGNORECASE)
_PRIOR_COMMIT_RE = re.compile(
    r"<!--\s*prior_commit_sha256:\s*([0-9a-f]{64})\s*-->")
_SOURCE_HASH_RE = re.compile(
    r"<!--\s*source_sha256:\s*([0-9a-f]{64})\s*-->")
_CONTINUITY_MODES = {"continuous", "elliptical", "scene_reset"}


class BridgeError(Exception):
    """Raised when commit provenance or bridge structure is invalid."""


@dataclass
class HandoffCheck:
    batch_from: int
    batch_to: int
    scene_from: int
    scene_to: int
    status: str = "pending"  # pending | ok | mismatch
    detail: str = ""


@dataclass
class BridgeReport:
    handoffs: list[HandoffCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(handoff.status == "ok" for handoff in self.handoffs)

    @property
    def pending(self) -> bool:
        return all(handoff.status in ("ok", "pending")
                   for handoff in self.handoffs)


def compute_handoffs(batch_manifest_path: Path) -> BridgeReport:
    """Return every edge between adjacent batches after validating the manifest."""
    manifest = _load_batch_manifest(batch_manifest_path)
    report = BridgeReport()
    for left, right in zip(manifest["batches"], manifest["batches"][1:]):
        report.handoffs.append(HandoffCheck(
            batch_from=left["batch_index"],
            batch_to=right["batch_index"],
            scene_from=left["scene_indices"][-1],
            scene_to=right["scene_indices"][0],
        ))
    return report


def commit_batch_state(batch_index: int, batch_manifest_path: Path,
                       episode_ledger_path: Path,
                       scene_session_dirs: dict[int, Path],
                       output_path: Path | None = None) -> dict:
    """Commit canonical scene states only after every scene is delivered."""
    manifest = _load_batch_manifest(batch_manifest_path)
    batch = _get_batch(manifest, batch_index)
    expected = batch["scene_indices"]
    if sorted(scene_session_dirs) != expected:
        raise BridgeError(
            f"Batch {batch_index} requires scene sessions {expected}; got "
            f"{sorted(scene_session_dirs)}")

    ledger_text = _read_text(episode_ledger_path, "episode continuity ledger")
    if "# EPISODE_CONTINUITY_LEDGER" not in ledger_text:
        raise BridgeError("Episode continuity ledger has the wrong document type")
    if _PLACEHOLDER_RE.search(ledger_text):
        raise BridgeError("Episode continuity ledger still contains Director placeholders")

    validate_batch_commit_inputs(
        batch_index,
        batch_manifest_path,
        episode_ledger_path,
        scene_session_dirs,
    )

    scene_states: list[dict] = []
    for scene_index in expected:
        session = scene_session_dirs[scene_index]
        scene_states.append(_delivered_scene_state(scene_index, session))

    payload = {
        "schema_version": "1.0",
        "status": "committed",
        "batch_index": batch_index,
        "script_source_hash": manifest["script_source_hash"],
        "batch_manifest_sha256": _file_hash(batch_manifest_path),
        "episode_ledger_sha256": _file_hash(episode_ledger_path),
        "scene_states": scene_states,
        "outgoing_scene_index": scene_states[-1]["scene_index"],
        "outgoing_scene_id": scene_states[-1]["scene_id"],
        "outgoing_state": scene_states[-1]["closing_state_keys"],
    }
    payload["commit_sha256"] = _object_hash(payload)
    if output_path is not None:
        _atomic_write_json(output_path, payload)
    return payload


def validate_batch_commit_inputs(batch_index: int, batch_manifest_path: Path,
                                 episode_ledger_path: Path,
                                 scene_session_dirs: dict[int, Path]) -> list[dict]:
    """Validate every immutable commit input before any scene is delivered."""
    manifest = _load_batch_manifest(batch_manifest_path)
    batch = _get_batch(manifest, batch_index)
    expected = batch["scene_indices"]
    if sorted(scene_session_dirs) != expected:
        raise BridgeError(
            f"Batch {batch_index} requires scene sessions {expected}; got "
            f"{sorted(scene_session_dirs)}")

    ledger_text = _read_text(episode_ledger_path, "episode continuity ledger")
    if "# EPISODE_CONTINUITY_LEDGER" not in ledger_text:
        raise BridgeError("Episode continuity ledger has the wrong document type")
    if _PLACEHOLDER_RE.search(ledger_text):
        raise BridgeError("Episode continuity ledger still contains Director placeholders")

    return [
        validate_scene_commit_input(scene_index, scene_session_dirs[scene_index])
        for scene_index in expected
    ]


def validate_scene_commit_input(scene_index: int, session: Path) -> dict:
    """Validate the current Master/Manifest pair without requiring delivery."""
    manifest = _load_current_manifest(session)
    master_path = session / "DIRECTOR_MASTER.md"
    master_text = _read_text(master_path, f"scene {scene_index} Director Master")
    master_hash = hashlib.sha256(master_text.encode("utf-8")).hexdigest()
    if master_hash != manifest["master_content_hash"]:
        raise BridgeError(
            f"Scene {scene_index} Master does not match its current Manifest")
    _validate_scene_boundary_contract(scene_index, manifest)
    first, last = manifest["shots"][0], manifest["shots"][-1]
    return {
        "scene_index": scene_index,
        "scene_id": manifest["scene_id"],
        "manifest_sha256": _file_hash(_manifest_path(session)),
        "master_content_hash": manifest["master_content_hash"],
        "opening_state_keys": first["opening_state_keys"],
        "closing_state_keys": last["closing_state_keys"],
    }


def generate_ledger_snapshot(batch_index: int,
                             batch_manifest_path: Path,
                             ledger_template_path: Path,
                             output_path: Path | None = None,
                             prior_commit_path: Path | None = None) -> str:
    """Create the exact committed continuity context read by one batch."""
    manifest = _load_batch_manifest(batch_manifest_path)
    batch = _get_batch(manifest, batch_index)
    ledger_text = _read_text(ledger_template_path, "episode continuity ledger")
    if "# EPISODE_CONTINUITY_LEDGER" not in ledger_text:
        raise BridgeError("Episode continuity ledger has the wrong document type")
    if _PLACEHOLDER_RE.search(ledger_text):
        raise BridgeError("Episode continuity ledger still contains Director placeholders")

    prior_commit: dict | None = None
    if batch_index > 1:
        if prior_commit_path is None:
            raise BridgeError("A prior committed Ledger state is required after batch 1")
        prior_commit = _load_commit(prior_commit_path)
        _verify_prior_commit(
            prior_commit, batch_index, manifest, batch_manifest_path,
            ledger_template_path)
    elif prior_commit_path is not None:
        raise BridgeError("Batch 1 must not inherit a prior commit")

    lines = [
        f"# Ledger Snapshot - Batch {batch_index} ({batch['label']})",
        "",
        "<!-- contract: ledger_snapshot v1.0 -->",
        f"<!-- source_sha256: {manifest['script_source_hash']} -->",
        f"<!-- batch_manifest_sha256: {_file_hash(batch_manifest_path)} -->",
        f"<!-- episode_ledger_sha256: {_file_hash(ledger_template_path)} -->",
    ]
    if prior_commit is not None:
        lines.append(
            f"<!-- prior_commit_sha256: {prior_commit['commit_sha256']} -->")
    lines.extend([
        "",
        "## Current Batch",
        "Scenes: " + ", ".join(str(index) for index in batch["scene_indices"]),
        "",
        "## Inherited Committed State",
    ])
    if prior_commit is None:
        lines.append("Opening batch: no prior batch state.")
    else:
        lines.append(
            f"Committed from batch {prior_commit['batch_index']}, scene "
            f"{prior_commit['outgoing_scene_index']} "
            f"({prior_commit['outgoing_scene_id']}).")
        lines.extend(_render_state(prior_commit["outgoing_state"]))
    lines.extend([
        "",
        "## Global Ledger Binding",
        "This snapshot is bound to the completed episode Continuity Ledger by "
        "the hash above. The Director reads that Ledger together with this "
        "canonical inherited state.",
        "",
    ])
    text = "\n".join(lines)
    if output_path is not None:
        try:
            output_path.write_text(text, encoding="utf-8")
        except OSError as exc:
            raise BridgeError(f"Cannot write Ledger snapshot {output_path}: {exc}") from exc
    return text


def validate_handoff(batch_index: int,
                     batch_manifest_path: Path,
                     prior_ledger_path: Path,
                     current_master_dir: Path,
                     continuity_mode: str = "continuous") -> BridgeReport:
    """Validate provenance and, for continuous bridges, exact canonical state."""
    if continuity_mode not in _CONTINUITY_MODES:
        raise BridgeError(
            f"continuity_mode must be one of {sorted(_CONTINUITY_MODES)}")
    manifest = _load_batch_manifest(batch_manifest_path)
    if batch_index == 1:
        return BridgeReport()
    batch = _get_batch(manifest, batch_index)
    previous = _get_batch(manifest, batch_index - 1)
    previous_scene = previous["scene_indices"][-1]
    current_scene = batch["scene_indices"][0]
    check = HandoffCheck(
        batch_from=batch_index - 1,
        batch_to=batch_index,
        scene_from=previous_scene,
        scene_to=current_scene,
    )
    report = BridgeReport([check])

    try:
        commit = _load_commit(prior_ledger_path)
        _verify_prior_commit(
            commit, batch_index, manifest, batch_manifest_path, None)
        snapshot_path = current_master_dir / "LEDGER_SNAPSHOT.md"
        snapshot = _read_text(snapshot_path, "current batch Ledger snapshot")
        commit_refs = _PRIOR_COMMIT_RE.findall(snapshot)
        source_refs = _SOURCE_HASH_RE.findall(snapshot)
        if commit_refs != [commit["commit_sha256"]]:
            raise BridgeError("Current batch snapshot does not bind the prior commit")
        if source_refs != [manifest["script_source_hash"]]:
            raise BridgeError("Current batch snapshot has a stale script source hash")
        current_manifest = _load_current_manifest(current_master_dir)
    except BridgeError as exc:
        check.status = "mismatch"
        check.detail = str(exc)
        return report

    opening = current_manifest["shots"][0]["opening_state_keys"]
    inherited = commit["outgoing_state"]
    if continuity_mode == "continuous":
        differences = _state_differences(inherited, opening)
        if differences:
            check.status = "mismatch"
            check.detail = "Continuous bridge state mismatch: " + "; ".join(differences)
            return report
        check.status = "ok"
        check.detail = "Prior committed state is loaded and exactly matches the opening state"
    else:
        check.status = "ok"
        check.detail = (
            f"Prior committed state is loaded; {continuity_mode} state changes require "
            "fresh DP semantic review")
    return report


def _load_batch_manifest(path: Path) -> dict:
    manifest = _read_json(path, "batch manifest")
    required = {
        "schema_version", "script_source_hash", "mode", "total_scenes",
        "selected_scenes", "total_batches", "batches", "shared_documents",
    }
    missing = required - set(manifest)
    if missing:
        raise BridgeError(f"Batch manifest missing fields: {sorted(missing)}")
    if manifest["schema_version"] not in {"1.0", "1.1"}:
        raise BridgeError("Unsupported batch manifest schema_version")
    if manifest["schema_version"] == "1.1":
        if manifest.get("director_scope") != "episode":
            raise BridgeError("Batch manifest v1.1 must bind Director scope to episode")
        if manifest.get("director_resume_required") is not True:
            raise BridgeError("Batch manifest v1.1 must require Director resume")
    if not re.fullmatch(r"[0-9a-f]{64}", manifest["script_source_hash"]):
        raise BridgeError("Batch manifest has invalid script_source_hash")
    batches = manifest["batches"]
    if not isinstance(batches, list) or not batches:
        raise BridgeError("Batch manifest must contain at least one batch")
    if manifest["total_batches"] != len(batches):
        raise BridgeError("Batch manifest total_batches mismatch")
    flattened: list[int] = []
    for expected_index, batch in enumerate(batches, 1):
        if batch.get("batch_index") != expected_index:
            raise BridgeError("Batch indexes must be consecutive from 1")
        scenes = batch.get("scene_indices")
        if not isinstance(scenes, list) or not scenes or not all(
                isinstance(index, int) for index in scenes):
            raise BridgeError(f"Batch {expected_index} has invalid scene_indices")
        flattened.extend(scenes)
    if flattened != manifest["selected_scenes"]:
        raise BridgeError("Batch scene order does not match selected_scenes")
    if flattened != sorted(set(flattened)):
        raise BridgeError("Selected scenes must be unique and ascending")
    if any(index < 1 or index > manifest["total_scenes"] for index in flattened):
        raise BridgeError("Selected scene index is outside total_scenes")
    required_shared = {"SCRIPT_FACTS.md", "EPISODE_VISUAL_BIBLE.md",
                       "EPISODE_CONTINUITY_LEDGER.md"}
    if not required_shared.issubset(set(manifest["shared_documents"])):
        raise BridgeError("Batch manifest omits required shared episode documents")
    return manifest


def _get_batch(manifest: dict, batch_index: int) -> dict:
    if not 1 <= batch_index <= len(manifest["batches"]):
        raise BridgeError(
            f"Batch {batch_index} out of range (1-{len(manifest['batches'])})")
    return manifest["batches"][batch_index - 1]


def _delivered_scene_state(scene_index: int, session: Path) -> dict:
    status = _read_text(session / "STATUS.md", f"scene {scene_index} status")
    if "状态：已交付。" not in status:
        raise BridgeError(f"Scene {scene_index} has not reached delivered status")
    delivery = session / "delivery"
    if not delivery.is_dir():
        raise BridgeError(f"Scene {scene_index} delivery directory is missing")
    delivered_files = sorted(path.name for path in delivery.iterdir() if path.is_file())
    if delivered_files != ["STORYBOARD.md", "VIDEO_PROMPT.md"]:
        raise BridgeError(
            f"Scene {scene_index} delivery must contain exactly STORYBOARD.md and "
            "VIDEO_PROMPT.md")
    state = validate_scene_commit_input(scene_index, session)
    return {
        **state,
        "storyboard_sha256": _file_hash(delivery / "STORYBOARD.md"),
        "video_prompt_sha256": _file_hash(delivery / "VIDEO_PROMPT.md"),
    }


def _validate_scene_boundary_contract(scene_index: int, manifest: dict) -> None:
    """Validate legacy Shot links or active v4 shared-Boundary ownership."""
    shots = manifest["shots"]
    first, last = shots[0], shots[-1]
    boundaries = manifest.get("boundaries")
    if boundaries is None:
        if first["entry_boundary_id"] != "SCENE_ENTRY":
            raise BridgeError(f"Scene {scene_index} first shot is not SCENE_ENTRY")
        if (last["exit_boundary_id"] != "SCENE_EXIT" or
                last["boundary_continuity"] != "scene_exit"):
            raise BridgeError(f"Scene {scene_index} last shot is not a scene_exit")
        return

    if len(boundaries) != len(shots) + 1:
        raise BridgeError(
            f"Scene {scene_index} shared Boundary count does not equal Shot count + 1")
    opening = boundaries[0]
    closing = boundaries[-1]
    if (
        opening.get("from_ref") != "SCENE_ENTRY"
        or opening.get("to_ref") != first["shot_id"]
        or opening.get("relation") != "scene_entry"
        or first["entry_boundary_id"] != opening.get("boundary_id")
    ):
        raise BridgeError(
            f"Scene {scene_index} B0 does not connect SCENE_ENTRY to its first Shot")
    if (
        closing.get("from_ref") != last["shot_id"]
        or closing.get("to_ref") != "SCENE_EXIT"
        or closing.get("relation") != "scene_exit"
        or last["exit_boundary_id"] != closing.get("boundary_id")
        or last["boundary_continuity"] != "scene_exit"
    ):
        raise BridgeError(
            f"Scene {scene_index} final Boundary does not connect its last Shot to SCENE_EXIT")


def _manifest_path(directory: Path) -> Path:
    candidates = (
        directory / "working" / "SHOT_MANIFEST.json",
        directory / "SHOT_MANIFEST.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise BridgeError(f"No SHOT_MANIFEST.json found under {directory}")


def _load_current_manifest(directory: Path) -> dict:
    path = _manifest_path(directory)
    manifest = _read_json(path, "shot manifest")
    try:
        jsonschema.validate(manifest, _SHOT_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise BridgeError(f"Shot manifest schema error: {exc.message}") from exc
    return manifest


def _load_commit(path: Path) -> dict:
    commit = _read_json(path, "Ledger commit")
    required = {
        "schema_version", "status", "batch_index", "script_source_hash",
        "batch_manifest_sha256", "episode_ledger_sha256", "scene_states",
        "outgoing_scene_index", "outgoing_scene_id", "outgoing_state",
        "commit_sha256",
    }
    missing = required - set(commit)
    if missing:
        raise BridgeError(f"Ledger commit missing fields: {sorted(missing)}")
    if commit["schema_version"] != "1.0" or commit["status"] != "committed":
        raise BridgeError("Ledger commit is not a supported committed record")
    supplied = commit["commit_sha256"]
    unsigned = dict(commit)
    unsigned.pop("commit_sha256", None)
    if supplied != _object_hash(unsigned):
        raise BridgeError("Ledger commit self-hash mismatch")
    return commit


def _verify_prior_commit(commit: dict, batch_index: int, manifest: dict,
                         manifest_path: Path,
                         ledger_path: Path | None) -> None:
    if commit["batch_index"] != batch_index - 1:
        raise BridgeError("Prior commit belongs to the wrong batch")
    if commit["script_source_hash"] != manifest["script_source_hash"]:
        raise BridgeError("Prior commit belongs to a different script version")
    if commit["batch_manifest_sha256"] != _file_hash(manifest_path):
        raise BridgeError("Prior commit belongs to a different batch manifest")
    previous = _get_batch(manifest, batch_index - 1)
    if commit["outgoing_scene_index"] != previous["scene_indices"][-1]:
        raise BridgeError("Prior commit outgoing scene does not match previous batch")
    if ledger_path is not None and (
            commit["episode_ledger_sha256"] != _file_hash(ledger_path)):
        raise BridgeError("Prior commit belongs to a different episode Ledger version")


def _normalise_state(state: dict) -> dict:
    normal = {
        "characters": sorted(state["characters"], key=lambda item: item["entity_id"]),
        "props": sorted(state["props"], key=lambda item: item["prop_id"]),
        "light_main": state["light_main"],
        "action_phase": state["action_phase"],
    }
    for key in ("story_time", "weather", "environment"):
        if key in state:
            normal[key] = state[key]
    return normal


def _state_differences(left: dict, right: dict) -> list[str]:
    left = _normalise_state(left)
    right = _normalise_state(right)
    differences: list[str] = []
    for key in sorted(set(left) | set(right)):
        if left.get(key) != right.get(key):
            differences.append(key)
    return differences


def _render_state(state: dict) -> list[str]:
    normal = _normalise_state(state)
    lines = ["", "### Characters"]
    if normal["characters"]:
        for character in normal["characters"]:
            detail = (
                f"- {character['entity_id']}: position={character['position']}; "
                f"facing={character['facing']}; "
                f"screen_direction={character['screen_direction']}; "
                f"posture={character['posture']}")
            if "wardrobe" in character:
                detail += f"; wardrobe={character['wardrobe']}"
            if "injury" in character:
                detail += f"; injury={character['injury']}"
            lines.append(detail)
    else:
        lines.append("- None")
    lines.append("### Props")
    if normal["props"]:
        for prop in normal["props"]:
            lines.append(
                f"- {prop['prop_id']}: held_by={prop['held_by']}; "
                f"location={prop['location']}")
    else:
        lines.append("- None")
    light = normal["light_main"]
    lines.extend([
        "### Light and Action",
        f"- Main light: direction={light['direction']}; "
        f"color_temp_k={light['color_temp_k']}; ratio={light['ratio']}",
        f"- Action phase: {normal['action_phase']}",
    ])
    for key, label in (
        ("story_time", "Story time"),
        ("weather", "Weather"),
        ("environment", "Environment"),
    ):
        if key in normal:
            lines.append(f"- {label}: {normal[key]}")
    return lines


def _read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BridgeError(f"Cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BridgeError(f"{label} root must be an object")
    return value


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise BridgeError(f"Cannot read {label} {path}: {exc}") from exc


def _file_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise BridgeError(f"Cannot hash {path}: {exc}") from exc


def _object_hash(value: dict) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _atomic_write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise BridgeError(f"Cannot commit Ledger state to {path}: {exc}") from exc


def _parse_scene_sessions(values: list[str]) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for value in values:
        try:
            raw_index, raw_path = value.split("=", 1)
            index = int(raw_index)
        except (ValueError, TypeError) as exc:
            raise BridgeError(
                f"Invalid --scene-session {value!r}; expected INDEX=PATH") from exc
        if index in result:
            raise BridgeError(f"Duplicate scene session index: {index}")
        result[index] = Path(raw_path)
    return result


def load_batch_manifest(path: Path) -> dict:
    """Public validated loader used by episode-level orchestration."""
    return _load_batch_manifest(path)


def delivered_scene_state(scene_index: int, session: Path) -> dict:
    """Public delivered-state verifier used by episode review."""
    return _delivered_scene_state(scene_index, session)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Committed cross-batch continuity state management")
    sub = parser.add_subparsers(dest="command", required=True)

    handoffs = sub.add_parser("handoffs")
    handoffs.add_argument("batch_manifest", type=Path)
    handoffs.add_argument("--telemetry-session", type=Path, default=None)

    commit = sub.add_parser("commit")
    commit.add_argument("batch_index", type=int)
    commit.add_argument("batch_manifest", type=Path)
    commit.add_argument("episode_ledger", type=Path)
    commit.add_argument("-o", "--output", type=Path, required=True)
    commit.add_argument("--scene-session", action="append", default=[],
                        help="Delivered scene mapping INDEX=SESSION_PATH; repeat per scene")
    commit.add_argument("--telemetry-session", type=Path, default=None)

    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("batch_index", type=int)
    snapshot.add_argument("batch_manifest", type=Path)
    snapshot.add_argument("episode_ledger", type=Path)
    snapshot.add_argument("-o", "--output", type=Path, default=None)
    snapshot.add_argument("--prior-commit", type=Path, default=None)
    snapshot.add_argument("--telemetry-session", type=Path, default=None)

    validate = sub.add_parser("validate")
    validate.add_argument("batch_index", type=int)
    validate.add_argument("batch_manifest", type=Path)
    validate.add_argument("prior_commit", type=Path)
    validate.add_argument("current_batch_dir", type=Path)
    validate.add_argument("--continuity-mode", choices=sorted(_CONTINUITY_MODES),
                          default="continuous")
    validate.add_argument("--telemetry-session", type=Path, default=None)
    args = parser.parse_args()

    t_started = time.monotonic()
    telemetry = getattr(args, "telemetry_session", None)
    result_code = 1
    try:
        if args.command == "handoffs":
            report = compute_handoffs(args.batch_manifest)
            output_text = json.dumps([asdict(item) for item in report.handoffs],
                                     ensure_ascii=False, indent=2)
            print(output_text)
            result_code = 0
            return result_code
        if args.command == "commit":
            value = commit_batch_state(
                args.batch_index, args.batch_manifest, args.episode_ledger,
                _parse_scene_sessions(args.scene_session), args.output)
            print(f"Ledger commit {value['commit_sha256']} -> {args.output}")
            result_code = 0
            return result_code
        if args.command == "snapshot":
            text = generate_ledger_snapshot(
                args.batch_index, args.batch_manifest, args.episode_ledger,
                args.output, args.prior_commit)
            if args.output is None:
                print(text)
            else:
                print(f"Ledger snapshot -> {args.output}")
            result_code = 0
            return result_code
        report = validate_handoff(
            args.batch_index, args.batch_manifest, args.prior_commit,
            args.current_batch_dir, args.continuity_mode)
        output_text = json.dumps([asdict(item) for item in report.handoffs],
                                 ensure_ascii=False, indent=2)
        print(output_text)
        result_code = 0 if report.ok else 1
        return result_code
    except BridgeError as exc:
        print(f"Scene bridge error: {exc}", file=sys.stderr)
        result_code = 1
        return result_code
    finally:
        if telemetry is not None:
            stage = f"scene_bridge_{args.command}"
            status = "completed" if result_code == 0 else "failed"
            input_paths: list[Path] = []
            if args.command == "handoffs":
                input_paths = [args.batch_manifest]
            elif args.command == "commit":
                input_paths = [args.batch_manifest, args.episode_ledger]
                if args.output:
                    input_paths.append(args.output)
            elif args.command == "snapshot":
                input_paths = [args.batch_manifest, args.episode_ledger]
                if args.prior_commit:
                    input_paths.append(args.prior_commit)
            elif args.command == "validate":
                input_paths = [args.batch_manifest, args.prior_commit, args.current_batch_dir]
            record_event(
                telemetry,
                event_type="local",
                stage=stage,
                status=status,
                elapsed_s=time.monotonic() - t_started,
                input_bytes=files_byte_size([p for p in input_paths if p.exists()]),
                output_bytes=files_byte_size(
                    [args.output] if hasattr(args, "output") and args.output and Path(args.output).exists() else []
                ),
                result_code=result_code,
                error_code="" if result_code == 0 else f"return_{result_code}",
            )


if __name__ == "__main__":
    raise SystemExit(main())
