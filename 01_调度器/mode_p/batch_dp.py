"""Evidence-bound fresh-DP review for one scheduled MODE:P batch.

The LLM call remains owned by Claude Code. This module prepares the exact input
packet, validates one response against the union of Shot IDs, routes issues to
the affected scene Masters, and commits READY scenes without creative work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from batch_state_machine import BatchStage, StateMachineError, load_state
from dp_contract import (
    DP_READY_FORMAT,
    DP_VALID_FIELDS,
    DpContractError,
    manifest_shot_ids,
    parse_dp_feedback,
    validate_dp_contract,
)
from run_mode_p import submit as submit_scene
from scene_bridge import (
    BridgeError,
    commit_batch_state,
    load_batch_manifest,
    validate_batch_commit_inputs,
    validate_scene_commit_input,
)
from session_lock import LockError, session_lock, verify_commit
from pipeline_telemetry import files_byte_size, record_event
from model_acceptance_guard import (
    AcceptanceGuardError,
    require_acceptance_dp_provenance,
)
from cache_manager import CacheKey, lookup_cache, restore_cache, store_in_cache
from asset_card_registry import AssetCardError, select_verified_cards


SCHEMA_VERSION = "1.0"
_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parents[1]
_DEFAULT_DP_CACHE = _MODULE_DIR / "runtime_cache" / "dp"


class BatchDpError(ValueError):
    """Raised when batch review evidence is missing, stale, or malformed."""


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise BatchDpError(f"cannot hash required file {path}: {exc}") from exc


def _object_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _batch_spec(manifest: dict[str, Any], batch_index: int) -> dict[str, Any]:
    if not 1 <= batch_index <= len(manifest["batches"]):
        raise BatchDpError(
            f"batch {batch_index} is outside 1-{len(manifest['batches'])}"
        )
    return manifest["batches"][batch_index - 1]


def _require_mapping(expected: list[int], sessions: dict[int, Path]) -> None:
    if sorted(sessions) != expected:
        raise BatchDpError(
            f"batch requires scene sessions {expected}; got {sorted(sessions)}"
        )


def _dependency(path: Path, label: str) -> dict[str, str]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise BatchDpError(f"missing {label}: {resolved}")
    return {
        "label": label,
        "path": str(resolved),
        "sha256": _sha256(resolved),
    }


def _scene_packet(scene_index: int, session: Path) -> dict[str, Any]:
    session = session.resolve()
    try:
        state = load_state(session)
    except StateMachineError as exc:
        raise BatchDpError(f"scene {scene_index} state is invalid: {exc}") from exc
    if state.stage != BatchStage.DP_BATCH.value:
        raise BatchDpError(
            f"scene {scene_index} must be at dp_batch, got {state.stage}"
        )
    ok, issues = verify_commit(session, "working")
    if not ok:
        raise BatchDpError(
            f"scene {scene_index} working commit is invalid: {'; '.join(issues)}"
        )
    try:
        validate_scene_commit_input(scene_index, session)
    except BridgeError as exc:
        raise BatchDpError(f"scene {scene_index} is not commit-ready: {exc}") from exc

    master = session / "DIRECTOR_MASTER.md"
    manifest = session / "working" / "SHOT_MANIFEST.json"
    storyboard = session / "working" / "STORYBOARD.md"
    video = session / "working" / "VIDEO_PROMPT.md"
    context = session / "SCENE_CONTEXT.md"
    files = {
        "master": _dependency(master, f"scene {scene_index} Master"),
        "manifest": _dependency(manifest, f"scene {scene_index} Manifest"),
        "storyboard": _dependency(storyboard, f"scene {scene_index} Storyboard"),
        "video_prompt": _dependency(video, f"scene {scene_index} Video Prompt"),
        "scene_context": _dependency(context, f"scene {scene_index} context"),
    }
    knowledge = session / "KNOWLEDGE_CONTEXT.md"
    if knowledge.is_file():
        files["knowledge_context"] = _dependency(
            knowledge, f"scene {scene_index} knowledge context"
        )
    shot_ids = sorted(manifest_shot_ids(manifest))
    return {
        "scene_index": scene_index,
        "session_path": str(session),
        "artifact_generation": state.artifact_generation,
        "shot_ids": shot_ids,
        "files": files,
    }


def _without_provenance_comments(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith("<!--")
    ).strip()


def _exact_script_excerpt(context_path: Path) -> str:
    text = context_path.read_text(encoding="utf-8")
    marker = "## Exact Script Excerpt"
    if marker in text:
        return _without_provenance_comments(text.split(marker, 1)[1])
    return _without_provenance_comments(text)


def _render_scene_model_evidence(
    scene: dict[str, Any], shared_dependencies: list[dict[str, str]],
    asset_card_evidence: str,
) -> str:
    continuity = next(
        (
            item for item in shared_dependencies
            if item["label"] == "EPISODE_CONTINUITY_LEDGER.md"
        ),
        None,
    )
    continuity_text = "No committed episode continuity beyond the current excerpt."
    if continuity is not None:
        continuity_text = _without_provenance_comments(
            Path(continuity["path"]).read_text(encoding="utf-8")
        )
    # The ledger is supporting context, not a second script. Keep this packet compact.
    if len(continuity_text) > 6000:
        continuity_text = continuity_text[:6000].rstrip() + "\n[continuity digest truncated]"
    return "\n".join([
        f"# DP Evidence - Scene {scene['scene_index']}",
        "",
        "## Current Episode Excerpt",
        "",
        _exact_script_excerpt(Path(scene["files"]["scene_context"]["path"])),
        "",
        "## Committed Continuity Digest",
        "",
        continuity_text,
        "",
        "## Verified Text Asset-Card Evidence Used",
        "",
        asset_card_evidence.strip() or "None. This scene uses text_only generation.",
        "",
    ])


def prepare_batch_dp(
    batch_index: int,
    batch_manifest_path: Path,
    scene_session_dirs: dict[int, Path],
    batch_review_dir: Path,
    *,
    capability_path: Path | None = None,
    asset_index_path: Path | None = None,
    asset_card_index_path: Path | None = None,
    dp_model: str = "inherit",
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    """Create a source-bound packet for exactly one new DP Agent call."""
    try:
        manifest = load_batch_manifest(batch_manifest_path)
    except BridgeError as exc:
        raise BatchDpError(str(exc)) from exc
    batch = _batch_spec(manifest, batch_index)
    expected = batch["scene_indices"]
    _require_mapping(expected, scene_session_dirs)

    session_root = batch_manifest_path.resolve().parent
    shared = [
        _dependency(session_root / name, name)
        for name in manifest["shared_documents"]
    ]
    runtime_evidence = [
        _dependency(
            capability_path or (_MODULE_DIR / "sd2_capability_profile.json"),
            "SD2 capability profile",
        ),
        _dependency(
            asset_index_path or (_PROJECT_ROOT / "ASSET_INDEX.json"),
            "asset index",
        ),
        _dependency(
            asset_card_index_path or (_PROJECT_ROOT / "ASSET_CARD_INDEX.json"),
            "text asset-card index",
        ),
        _dependency(
            _MODULE_DIR / "knowledge" / "knowledge_index.json",
            "knowledge index",
        ),
        _dependency(
            _PROJECT_ROOT / ".claude" / "agents" / "mode-p-dp.md",
            "Claude DP agent contract",
        ),
        _dependency(
            _PROJECT_ROOT / "02_Agent" / "dp_agent.md",
            "canonical DP contract",
        ),
        _dependency(_MODULE_DIR / "dp_contract.py", "DP parser contract"),
    ]
    scenes = [
        _scene_packet(index, scene_session_dirs[index]) for index in expected
    ]
    card_budget_remaining = 2000
    for scene in scenes:
        scene_manifest = json.loads(
            Path(scene["files"]["manifest"]["path"]).read_text(encoding="utf-8")
        )
        references: list[dict[str, str]] = []
        seen_refs: set[tuple[str, str]] = set()
        for shot in scene_manifest["shots"]:
            for reference in shot["reference_assets"]:
                key = (reference["asset_id"], reference["responsibility"])
                if key not in seen_refs:
                    references.append(reference)
                    seen_refs.add(key)
        try:
            card_evidence = select_verified_cards(
                references,
                card_index_path=(
                    asset_card_index_path or (_PROJECT_ROOT / "ASSET_CARD_INDEX.json")
                ),
                asset_index_path=(
                    asset_index_path or (_PROJECT_ROOT / "ASSET_INDEX.json")
                ),
                max_chars=card_budget_remaining,
            ) if references else ""
        except AssetCardError as exc:
            raise BatchDpError(
                f"scene {scene['scene_index']} asset-card evidence: {exc}"
            ) from exc
        card_budget_remaining -= len(card_evidence)
        evidence_path = (
            batch_review_dir
            / f"DP_EVIDENCE_SCENE_{scene['scene_index']:03d}.md"
        )
        _atomic_text(
            evidence_path,
            _render_scene_model_evidence(scene, shared, card_evidence),
        )
        scene["files"]["dp_evidence"] = _dependency(
            evidence_path, f"scene {scene['scene_index']} episode evidence"
        )
    shot_ids = [shot for scene in scenes for shot in scene["shot_ids"]]
    if len(shot_ids) != len(set(shot_ids)):
        raise BatchDpError("Shot IDs overlap across scene Manifests")

    content_identity = {
        "script_source_hash": manifest["script_source_hash"],
        "dp_model": dp_model,
        "shared": [(item["label"], item["sha256"]) for item in shared],
        "runtime": [(item["label"], item["sha256"]) for item in runtime_evidence],
        "scenes": [{
            "scene_index": scene["scene_index"],
            "shot_ids": scene["shot_ids"],
            "files": [
                (name, item["sha256"])
                for name, item in sorted(scene["files"].items())
            ],
        } for scene in scenes],
    }
    review_content_sha256 = _object_hash(content_identity)
    cache_root = (cache_dir or _DEFAULT_DP_CACHE).resolve()
    unsigned = {
        "schema_version": SCHEMA_VERSION,
        "batch_index": batch_index,
        "total_batches": manifest["total_batches"],
        "script_source_hash": manifest["script_source_hash"],
        "batch_manifest": _dependency(batch_manifest_path, "batch manifest"),
        "shared_dependencies": shared,
        "runtime_dependencies": runtime_evidence,
        "scenes": scenes,
        "shot_ids": shot_ids,
        "dp_model": dp_model,
        "review_content_sha256": review_content_sha256,
        "cache_dir": str(cache_root),
    }
    packet = dict(unsigned)
    packet["packet_sha256"] = _object_hash(unsigned)

    with session_lock(batch_review_dir):
        _atomic_json(batch_review_dir / "DP_PACKET.json", packet)
        _atomic_text(batch_review_dir / "DP_PACKET.md", _render_packet(packet))
        cache_entry = lookup_cache(
            cache_root, _dp_cache_key(packet), telemetry_session=session_root
        )
        cached_path = batch_review_dir / "CACHED_DP_RESPONSE.md"
        cached_path.unlink(missing_ok=True)
        if cache_entry is not None:
            restore_cache(cache_root, cache_entry, batch_review_dir)
        _atomic_json(batch_review_dir / "DP_STATE.json", {
            "schema_version": SCHEMA_VERSION,
            "status": "cached_dp_available" if cache_entry else "awaiting_fresh_dp",
            "packet_sha256": packet["packet_sha256"],
            "feedback_sha256": "",
            "affected_scenes": [],
            "cached_response_path": str(cached_path.resolve()) if cache_entry else "",
        })
    return packet


def _render_packet(packet: dict[str, Any]) -> str:
    lines = [
        "# MODE:P Fresh DP Batch Packet",
        "",
        f"Batch: {packet['batch_index']}/{packet['total_batches']}",
        f"DP model assignment: `{packet['dp_model']}`",
        "",
        "Read only the files under Model-Visible Evidence. Review the supplied "
        "episode evidence and final views; do not seek Master, Manifest, knowledge, "
        "runtime code, prior feedback, or Director reasoning.",
        "",
        "## Response Contract",
        "",
        "If every scene passes, write exactly one scene-specific evidence line "
        "for each reviewed scene and no other text:",
        f"`{DP_READY_FORMAT}`",
        "Each READY detail must be 18-240 characters, cite at least one current "
        "Shot ID, and state one concrete observed spatial, boundary, light, action, "
        "composition, reference, mode, or duration fact. Do not write per-Shot "
        "verdicts, a preface, summary, heading, or explanation outside these lines.",
        "",
        "If any issue exists, write only issue lines and no READY lines:",
        "`<Shot ID>: <field> — <concrete problem, at most 240 characters>`",
        "",
        "Allowed fields: " + ", ".join(sorted(DP_VALID_FIELDS)),
        "",
        "## Model-Visible Evidence",
        "",
    ]
    for scene in packet["scenes"]:
        lines.extend(["", f"## Scene {scene['scene_index']}", ""])
        lines.append("Shot IDs: " + ", ".join(scene["shot_ids"]))
        for name in ("dp_evidence", "storyboard", "video_prompt"):
            item = scene["files"][name]
            lines.append(f"- {item['label']}: `{item['path']}`")
        manifest = json.loads(Path(scene["files"]["manifest"]["path"]).read_text(
            encoding="utf-8"
        ))
        modes = sorted({
            (
                shot["scene_expression"], shot["timing_mode"],
                shot["generation_mode"], shot["transition_execution"],
            )
            for shot in manifest["shots"]
        })
        lines.append("- Used capability digest:")
        for expression, timing, generation, transition in modes:
            lines.append(
                f"  - profile={expression}; timing={timing}; "
                f"generation={generation}; transition={transition}"
            )
        references = [
            f"{asset['asset_id']}|{asset['responsibility']}"
            for shot in manifest["shots"]
            for asset in shot["reference_assets"]
        ]
        lines.append(
            "- Used verified asset-card digest: "
            + (", ".join(sorted(set(references))) if references else "none (text_only)")
        )
    lines.append("")
    return "\n".join(lines)


def _dp_cache_key(packet: dict[str, Any]) -> CacheKey:
    return CacheKey("dp", {
        "review_content": packet["review_content_sha256"],
        "model_assignment": _text_hash(packet["dp_model"]),
        "cache_contract": _text_hash("batch_dp_response_cache_v1.0"),
    })


def cache_dp_response(packet: dict[str, Any], feedback_path: Path,
                      telemetry_session: Path) -> None:
    """Store only a contract-valid response from a proven actual DP call."""
    try:
        text = feedback_path.read_text(encoding="utf-8").lstrip("\ufeff")
    except (OSError, UnicodeError) as exc:
        raise BatchDpError(f"cannot cache DP feedback: {exc}") from exc
    parsed = parse_dp_feedback(text)
    valid, problems = validate_dp_contract(parsed, set(packet["shot_ids"]))
    if not valid:
        raise BatchDpError("cannot cache invalid DP feedback: " + "; ".join(problems))
    store_in_cache(
        Path(packet["cache_dir"]),
        _dp_cache_key(packet),
        {"CACHED_DP_RESPONSE.md": feedback_path},
        telemetry_session=telemetry_session,
    )


def _load_packet(batch_review_dir: Path) -> dict[str, Any]:
    path = batch_review_dir / "DP_PACKET.json"
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BatchDpError(f"cannot read DP packet: {exc}") from exc
    supplied = packet.get("packet_sha256")
    unsigned = dict(packet)
    unsigned.pop("packet_sha256", None)
    if packet.get("schema_version") != SCHEMA_VERSION or supplied != _object_hash(unsigned):
        raise BatchDpError("DP packet schema or self-hash is invalid")
    return packet


def _verify_packet_current(packet: dict[str, Any]) -> None:
    dependencies = [packet["batch_manifest"]]
    dependencies.extend(packet["shared_dependencies"])
    dependencies.extend(packet["runtime_dependencies"])
    for scene in packet["scenes"]:
        dependencies.extend(scene["files"].values())
    for item in dependencies:
        path = Path(item["path"])
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise BatchDpError(f"DP input changed after packet creation: {item['label']}")


def submit_batch_dp(
    batch_review_dir: Path,
    feedback_path: Path,
    *,
    failpoint_after_scene: int | None = None,
) -> dict[str, Any]:
    """Route one bound DP result; READY commits all scenes in the packet."""
    with session_lock(batch_review_dir):
        packet = _load_packet(batch_review_dir)
        _verify_packet_current(packet)
        try:
            text = feedback_path.read_text(encoding="utf-8").lstrip("\ufeff")
        except (OSError, UnicodeError) as exc:
            raise BatchDpError(f"cannot read DP feedback: {exc}") from exc
        parsed = parse_dp_feedback(text)
        valid, problems = validate_dp_contract(parsed, set(packet["shot_ids"]))
        if not valid:
            raise BatchDpError("invalid DP feedback: " + "; ".join(problems))

        feedback_copy = batch_review_dir / "DP_FEEDBACK.md"
        _atomic_text(feedback_copy, text.strip() + "\n")
        feedback_hash = _sha256(feedback_copy)
        if parsed.status == "blocked":
            state = {
                "schema_version": SCHEMA_VERSION,
                "status": "input_blocked",
                "packet_sha256": packet["packet_sha256"],
                "feedback_sha256": feedback_hash,
                "reason": parsed.block_reason,
                "committed_scenes": [],
            }
            _atomic_json(batch_review_dir / "DP_STATE.json", state)
            return state

        shot_to_scene = {
            shot_id: scene["scene_index"]
            for scene in packet["scenes"]
            for shot_id in scene["shot_ids"]
        }
        scene_by_index = {
            scene["scene_index"]: scene for scene in packet["scenes"]
        }

        if parsed.status == "issues":
            grouped: dict[int, list[str]] = {}
            for issue in parsed.issues:
                grouped.setdefault(shot_to_scene[issue.shot_id], []).append(
                    f"{issue.shot_id}: {issue.field} — {issue.detail}"
                )
            blocked = False
            for scene_index, lines in sorted(grouped.items()):
                scene = scene_by_index[scene_index]
                split_path = batch_review_dir / "routed" / f"scene-{scene_index:03d}.md"
                _atomic_text(split_path, "\n".join(lines) + "\n")
                session = Path(scene["session_path"])
                result = submit_scene(
                    session,
                    Path(scene["files"]["storyboard"]["path"]),
                    Path(scene["files"]["video_prompt"]["path"]),
                    split_path,
                    Path(scene["files"]["master"]["path"]),
                )
                if result == 3:
                    blocked = True
                elif result != 1:
                    raise BatchDpError(
                        f"scene {scene_index} did not enter Director revision (code {result})"
                    )
            state = {
                "schema_version": SCHEMA_VERSION,
                "status": "blocked" if blocked else "revision_required",
                "packet_sha256": packet["packet_sha256"],
                "feedback_sha256": feedback_hash,
                "affected_scenes": sorted(grouped),
            }
            _atomic_json(batch_review_dir / "DP_STATE.json", state)
            return state

        ready_by_scene = {
            item.scene_id: item for item in parsed.ready_evidence
        }
        manifest_path = Path(packet["batch_manifest"]["path"])
        ledger = next(
            Path(item["path"])
            for item in packet["shared_dependencies"]
            if item["label"] == "EPISODE_CONTINUITY_LEDGER.md"
        )
        scene_sessions = {
            scene["scene_index"]: Path(scene["session_path"])
            for scene in packet["scenes"]
        }
        try:
            validate_batch_commit_inputs(
                packet["batch_index"], manifest_path, ledger, scene_sessions
            )
        except BridgeError as exc:
            raise BatchDpError(
                f"batch cannot commit any scene: {exc}"
            ) from exc
        committed: list[int] = []
        for scene in packet["scenes"]:
            session = Path(scene["session_path"])
            current = load_state(session)
            if current.stage == BatchStage.BATCH_COMMIT.value:
                committed.append(scene["scene_index"])
                continue
            if current.stage != BatchStage.DP_BATCH.value:
                raise BatchDpError(
                    f"scene {scene['scene_index']} cannot accept READY from {current.stage}"
                )
            scene_ids = {shot_id.rsplit("-", 1)[0] for shot_id in scene["shot_ids"]}
            if len(scene_ids) != 1:
                raise BatchDpError(
                    f"scene {scene['scene_index']} has inconsistent Shot scene IDs"
                )
            scene_id = next(iter(scene_ids))
            evidence = ready_by_scene.get(scene_id)
            if evidence is None:
                raise BatchDpError(
                    f"scene {scene['scene_index']} lacks bound READY evidence"
                )
            scene_ready = (
                batch_review_dir / "routed" /
                f"ready-scene-{scene['scene_index']:03d}.md"
            )
            _atomic_text(
                scene_ready,
                f"READY {evidence.scene_id}: {evidence.detail}\n",
            )
            result = submit_scene(
                session,
                Path(scene["files"]["storyboard"]["path"]),
                Path(scene["files"]["video_prompt"]["path"]),
                scene_ready,
                Path(scene["files"]["master"]["path"]),
            )
            if result != 0:
                raise BatchDpError(
                    f"scene {scene['scene_index']} READY commit failed (code {result})"
                )
            committed.append(scene["scene_index"])
            if failpoint_after_scene == scene["scene_index"]:
                raise BatchDpError(
                    f"simulated interruption after scene {scene['scene_index']} commit"
                )

        commit_path = batch_review_dir / "LEDGER_COMMIT.json"
        commit_batch_state(
            packet["batch_index"],
            manifest_path,
            ledger,
            scene_sessions,
            commit_path,
        )
        state = {
            "schema_version": SCHEMA_VERSION,
            "status": "committed",
            "packet_sha256": packet["packet_sha256"],
            "feedback_sha256": feedback_hash,
            "affected_scenes": [],
            "committed_scenes": committed,
            "ledger_commit_sha256": _sha256(commit_path),
        }
        _atomic_json(batch_review_dir / "DP_STATE.json", state)
        return state


def _parse_scene_sessions(values: list[str]) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for value in values:
        try:
            raw_index, raw_path = value.split("=", 1)
            index = int(raw_index)
        except (ValueError, TypeError) as exc:
            raise BatchDpError("scene session must be INDEX=PATH") from exc
        if index < 1 or index in result or not raw_path.strip():
            raise BatchDpError(f"invalid or duplicate scene session mapping: {value}")
        result[index] = Path(raw_path)
    return result


_prepare_batch_dp_impl = prepare_batch_dp
_submit_batch_dp_impl = submit_batch_dp


def prepare_batch_dp(
    batch_index: int,
    batch_manifest_path: Path,
    scene_session_dirs: dict[int, Path],
    batch_review_dir: Path,
    *,
    capability_path: Path | None = None,
    asset_index_path: Path | None = None,
    asset_card_index_path: Path | None = None,
    dp_model: str = "inherit",
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    root = batch_manifest_path.resolve().parent
    try:
        packet = _prepare_batch_dp_impl(
            batch_index,
            batch_manifest_path,
            scene_session_dirs,
            batch_review_dir,
            capability_path=capability_path,
            asset_index_path=asset_index_path,
            asset_card_index_path=asset_card_index_path,
            dp_model=dp_model,
            cache_dir=cache_dir,
        )
    except Exception as exc:
        record_event(
            root, event_type="local", stage="batch_dp_prepare", status="failed",
            elapsed_s=time.monotonic() - started,
            input_bytes=files_byte_size([batch_manifest_path]),
            result_code=1, error_code=type(exc).__name__,
        )
        raise
    record_event(
        root, event_type="local", stage="batch_dp_prepare",
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([
            batch_manifest_path,
            *[Path(item["path"]) for item in packet["shared_dependencies"]],
            *[Path(item["path"]) for item in packet["runtime_dependencies"]],
            *[
                Path(item["path"])
                for scene in packet["scenes"] for item in scene["files"].values()
            ],
        ]),
        output_bytes=files_byte_size([
            batch_review_dir / "DP_PACKET.json",
            batch_review_dir / "DP_PACKET.md",
            batch_review_dir / "DP_STATE.json",
        ]),
    )
    return packet


def submit_batch_dp(
    batch_review_dir: Path,
    feedback_path: Path,
    *,
    model_name: str = "",
    model_call_id: str = "",
    model_elapsed_s: float = 0.0,
    failpoint_after_scene: int | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    if bool(model_name) != bool(model_call_id):
        raise BatchDpError("model_name and model_call_id must be supplied together")
    if model_elapsed_s < 0:
        raise BatchDpError("model_elapsed_s cannot be negative")
    try:
        require_acceptance_dp_provenance(
            batch_review_dir,
            model_call_id,
            model_name,
            feedback_path,
        )
    except AcceptanceGuardError as exc:
        raise BatchDpError(str(exc)) from exc
    try:
        packet = _load_packet(batch_review_dir)
        root = Path(packet["batch_manifest"]["path"]).resolve().parent
    except Exception:
        root = batch_review_dir.resolve()
    try:
        state = _submit_batch_dp_impl(
            batch_review_dir,
            feedback_path,
            failpoint_after_scene=failpoint_after_scene,
        )
    except Exception as exc:
        record_event(
            root, event_type="local", stage="batch_dp_submit", status="failed",
            elapsed_s=time.monotonic() - started,
            input_bytes=files_byte_size([feedback_path]),
            result_code=1, error_code=type(exc).__name__,
        )
        raise
    record_event(
        root,
        event_type="local",
        stage="batch_dp_submit",
        status=(
            "revision_required" if state["status"] == "revision_required"
            else "blocked" if state["status"] == "blocked" else "completed"
        ),
        elapsed_s=time.monotonic() - started,
        input_bytes=files_byte_size([
            batch_review_dir / "DP_PACKET.json", feedback_path
        ]),
        output_bytes=files_byte_size([
            batch_review_dir / "DP_FEEDBACK.md",
            batch_review_dir / "DP_STATE.json",
            batch_review_dir / "LEDGER_COMMIT.json",
        ]),
        result_code=0,
    )
    if model_name and model_call_id:
        record_event(
            root,
            event_type="model",
            stage="fresh_dp_batch",
            status=(
                "revision_required" if state["status"] == "revision_required"
                else "blocked" if state["status"] == "blocked" else "completed"
            ),
            elapsed_s=model_elapsed_s,
            input_bytes=files_byte_size([batch_review_dir / "DP_PACKET.md"]),
            output_bytes=files_byte_size([feedback_path]),
            model_role="dp",
            model_name=model_name,
            model_call_id=model_call_id,
        )
        cache_dp_response(packet, feedback_path, root)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Operate one fresh-DP batch review")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("batch_index", type=int)
    prepare.add_argument("batch_manifest", type=Path)
    prepare.add_argument("review_dir", type=Path)
    prepare.add_argument("--scene-session", action="append", default=[])
    prepare.add_argument("--capability", type=Path)
    prepare.add_argument("--assets", type=Path)
    prepare.add_argument("--asset-cards", type=Path)
    prepare.add_argument("--dp-model", default="inherit")
    prepare.add_argument("--cache-dir", type=Path)
    submit = sub.add_parser("submit")
    submit.add_argument("review_dir", type=Path)
    submit.add_argument("feedback", type=Path)
    submit.add_argument("--model-name", default="")
    submit.add_argument("--model-call-id", default="")
    submit.add_argument("--model-elapsed", type=float, default=0.0)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            packet = prepare_batch_dp(
                args.batch_index,
                args.batch_manifest,
                _parse_scene_sessions(args.scene_session),
                args.review_dir,
                capability_path=args.capability,
                asset_index_path=args.assets,
                asset_card_index_path=args.asset_cards,
                dp_model=args.dp_model,
                cache_dir=args.cache_dir,
            )
            print(f"Fresh DP packet -> {args.review_dir / 'DP_PACKET.md'}")
            print(f"Packet SHA-256: {packet['packet_sha256']}")
        else:
            state = submit_batch_dp(
                args.review_dir,
                args.feedback,
                model_name=args.model_name,
                model_call_id=args.model_call_id,
                model_elapsed_s=args.model_elapsed,
            )
            print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0
    except (
        BatchDpError, DpContractError, BridgeError, LockError,
        StateMachineError, OSError, ValueError,
    ) as exc:
        print(f"Batch DP error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
