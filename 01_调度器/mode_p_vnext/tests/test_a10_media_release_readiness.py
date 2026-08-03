"""A10 evidence readiness checks.

These checks deliberately validate *physical external evidence*, not visual
quality.  With no A10 evidence packet they issue an auditable skip; a passing
unit test must never be read as media acceptance or owner approval.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import pytest


ARCHITECTURE_SHA256 = "d5616edc209dcaba3d82a1defe5e11187145399c30143bad6e4e685eb5c4c903"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
A10_RUNS_ROOT = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "vnext_release_runs" / "A10"
MEDIA_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv", ".png", ".jpg", ".jpeg", ".webp"}
FRAME_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class MediaEvidenceError(AssertionError):
    """An A10 packet is structurally incapable of proving real-media readiness."""


def _require_mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MediaEvidenceError(f"{field} must be an object")
    return value


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MediaEvidenceError(f"{field} must be non-empty text")
    return value


def _require_sha256(value: object, field: str) -> str:
    text = _require_text(value, field)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise MediaEvidenceError(f"{field} must be a lowercase SHA256")
    return text


def _require_list(value: object, field: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise MediaEvidenceError(f"{field} must be a non-empty list")
    return value


def _parse_timestamp(value: object, field: str) -> datetime:
    text = _require_text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MediaEvidenceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise MediaEvidenceError(f"{field} must include a timezone")
    return parsed


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file(root: Path, raw_path: object, field: str, suffixes: set[str]) -> Path:
    text = _require_text(raw_path, field)
    candidate = (root / text).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise MediaEvidenceError(f"{field} escapes the A10 run root") from exc
    if not candidate.is_file():
        raise MediaEvidenceError(f"{field} does not name a real file")
    if candidate.stat().st_size < 64:
        raise MediaEvidenceError(f"{field} is too small to be reviewable media")
    if candidate.suffix.casefold() not in suffixes:
        raise MediaEvidenceError(f"{field} has an unsupported media extension")
    return candidate


def _assert_recognised_media(path: Path, field: str) -> None:
    header = path.read_bytes()[:32]
    suffix = path.suffix.casefold()
    valid = (
        (suffix == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n"))
        or (suffix in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff"))
        or (suffix == ".webp" and header.startswith(b"RIFF") and header[8:12] == b"WEBP")
        or (suffix in {".mp4", ".mov"} and len(header) >= 12 and header[4:8] == b"ftyp")
        or (suffix in {".webm", ".mkv"} and header.startswith(b"\x1a\x45\xdf\xa3"))
    )
    if not valid:
        raise MediaEvidenceError(f"{field} is not a recognised image/video binary")


def _validate_file_hash(
    root: Path,
    item: Mapping[str, Any],
    *,
    path_field: str,
    hash_field: str,
    suffixes: set[str],
) -> Path:
    path = _safe_file(root, item.get(path_field), path_field, suffixes)
    expected = _require_sha256(item.get(hash_field), hash_field)
    actual = _sha256_file(path)
    if actual != expected:
        raise MediaEvidenceError(f"{hash_field} does not match {path_field}")
    _assert_recognised_media(path, path_field)
    return path


def _validate_attribution(value: object, field: str) -> None:
    attribution = _require_mapping(value, field)
    _require_text(attribution.get("layer"), f"{field}.layer")
    _require_text(attribution.get("cause"), f"{field}.cause")
    refs = _require_list(attribution.get("artifact_or_capability_refs"), f"{field}.artifact_or_capability_refs")
    for index, ref in enumerate(refs):
        _require_text(ref, f"{field}.artifact_or_capability_refs[{index}]")


def _validate_record_binding(root: Path, binding: Mapping[str, Any], path_field: str) -> None:
    record_path = _safe_file(root, binding.get(path_field), path_field, {".json"})
    expected = _require_sha256(binding.get(f"{path_field}_sha256"), f"{path_field}_sha256")
    if _sha256_file(record_path) != expected:
        raise MediaEvidenceError(f"{path_field}_sha256 does not match {path_field}")
    try:
        decoded = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MediaEvidenceError(f"{path_field} is not readable UTF-8 JSON") from exc
    if not isinstance(decoded, Mapping):
        raise MediaEvidenceError(f"{path_field} must contain a JSON object")


def validate_real_media_packet(payload: object, *, runs_root: Path = A10_RUNS_ROOT) -> None:
    """Validate reproducible A10 evidence without judging the imagery itself."""

    evidence = _require_mapping(payload, "evidence")
    if evidence.get("kind") != "MEDIA_VISUAL_ACCEPTANCE":
        raise MediaEvidenceError("kind must be MEDIA_VISUAL_ACCEPTANCE")
    if evidence.get("accepted") is not True:
        raise MediaEvidenceError("accepted must be true only after media review")
    if evidence.get("evidence_mode") != "EXTERNAL_REAL_MEDIA":
        raise MediaEvidenceError("evidence_mode must be EXTERNAL_REAL_MEDIA")
    if evidence.get("architecture_authority_sha256") != ARCHITECTURE_SHA256:
        raise MediaEvidenceError("architecture authority hash does not match frozen v3.1")
    if evidence.get("production_switch_authorized") is not False:
        raise MediaEvidenceError("A10 evidence must keep production switching false")
    if "owner_preview_approval" in evidence or "owner_production_approval" in evidence:
        raise MediaEvidenceError("media evidence cannot stand in for independent owner approval")

    runs = _require_list(evidence.get("media_runs"), "media_runs")
    runs_by_id: dict[str, Mapping[str, Any]] = {}
    for index, raw_run in enumerate(runs):
        run = _require_mapping(raw_run, f"media_runs[{index}]")
        run_id = _require_text(run.get("run_id"), f"media_runs[{index}].run_id")
        if run_id in runs_by_id:
            raise MediaEvidenceError("media_runs run_id values must be unique")
        if run.get("track") not in {"v4", "vnext"}:
            raise MediaEvidenceError(f"media_runs[{index}].track must be v4 or vnext")
        _require_text(run.get("provider"), f"media_runs[{index}].provider")
        _require_sha256(run.get("scene_digest"), f"media_runs[{index}].scene_digest")
        started = _parse_timestamp(run.get("started_at"), f"media_runs[{index}].started_at")
        completed = _parse_timestamp(run.get("completed_at"), f"media_runs[{index}].completed_at")
        if completed < started:
            raise MediaEvidenceError(f"media_runs[{index}] completed before it started")
        _require_text(run.get("media_kind"), f"media_runs[{index}].media_kind")
        _validate_file_hash(
            runs_root,
            run,
            path_field="media_path",
            hash_field="media_sha256",
            suffixes=MEDIA_SUFFIXES,
        )
        _validate_record_binding(runs_root, run, "source_run_record_path")
        inputs = _require_list(run.get("input_artifact_refs"), f"media_runs[{index}].input_artifact_refs")
        for ref_index, ref in enumerate(inputs):
            _require_text(ref, f"media_runs[{index}].input_artifact_refs[{ref_index}]")
        _validate_attribution(run.get("attribution"), f"media_runs[{index}].attribution")
        runs_by_id[run_id] = run

    frames = _require_list(evidence.get("frame_evidence"), "frame_evidence")
    frames_by_id: dict[str, Mapping[str, Any]] = {}
    seen_frame_coordinates: set[tuple[str, int]] = set()
    for index, raw_frame in enumerate(frames):
        frame = _require_mapping(raw_frame, f"frame_evidence[{index}]")
        evidence_id = _require_text(frame.get("evidence_id"), f"frame_evidence[{index}].evidence_id")
        if evidence_id in frames_by_id:
            raise MediaEvidenceError("frame evidence_id values must be unique")
        run_id = _require_text(frame.get("media_run_id"), f"frame_evidence[{index}].media_run_id")
        if run_id not in runs_by_id:
            raise MediaEvidenceError("frame evidence refers to an unknown media run")
        frame_index = frame.get("frame_index")
        if isinstance(frame_index, bool) or not isinstance(frame_index, int) or frame_index < 0:
            raise MediaEvidenceError("frame_index must be a non-negative integer")
        coordinate = (run_id, frame_index)
        if coordinate in seen_frame_coordinates:
            raise MediaEvidenceError("frame evidence cannot duplicate a run/frame_index coordinate")
        seen_frame_coordinates.add(coordinate)
        timestamp_ms = frame.get("timestamp_ms")
        if isinstance(timestamp_ms, bool) or not isinstance(timestamp_ms, int) or timestamp_ms < 0:
            raise MediaEvidenceError("timestamp_ms must be a non-negative integer")
        _validate_file_hash(
            runs_root,
            frame,
            path_field="frame_path",
            hash_field="frame_sha256",
            suffixes=FRAME_SUFFIXES,
        )
        checks = _require_list(frame.get("review_checks"), f"frame_evidence[{index}].review_checks")
        for check_index, check in enumerate(checks):
            _require_text(check, f"frame_evidence[{index}].review_checks[{check_index}]")
        _validate_attribution(frame.get("attribution"), f"frame_evidence[{index}].attribution")
        frames_by_id[evidence_id] = frame

    comparison = _require_mapping(evidence.get("v4_vnext_comparison"), "v4_vnext_comparison")
    comparison_scene = _require_sha256(comparison.get("same_scene_digest"), "v4_vnext_comparison.same_scene_digest")
    v4_run_id = _require_text(comparison.get("v4_media_run_id"), "v4_vnext_comparison.v4_media_run_id")
    vnext_run_id = _require_text(comparison.get("vnext_media_run_id"), "v4_vnext_comparison.vnext_media_run_id")
    if v4_run_id == vnext_run_id or v4_run_id not in runs_by_id or vnext_run_id not in runs_by_id:
        raise MediaEvidenceError("comparison must bind two distinct known media runs")
    if runs_by_id[v4_run_id].get("track") != "v4" or runs_by_id[vnext_run_id].get("track") != "vnext":
        raise MediaEvidenceError("comparison must bind v4 and vnext tracks respectively")
    if {runs_by_id[v4_run_id].get("scene_digest"), runs_by_id[vnext_run_id].get("scene_digest")} != {comparison_scene}:
        raise MediaEvidenceError("v4 and vnext runs do not share the comparison scene digest")
    pairs = _require_list(comparison.get("frame_pairs"), "v4_vnext_comparison.frame_pairs")
    for index, raw_pair in enumerate(pairs):
        pair = _require_mapping(raw_pair, f"v4_vnext_comparison.frame_pairs[{index}]")
        v4_frame = _require_text(pair.get("v4_frame_evidence_id"), f"frame_pairs[{index}].v4_frame_evidence_id")
        vnext_frame = _require_text(pair.get("vnext_frame_evidence_id"), f"frame_pairs[{index}].vnext_frame_evidence_id")
        if v4_frame not in frames_by_id or vnext_frame not in frames_by_id:
            raise MediaEvidenceError("comparison frame pair refers to unknown frame evidence")
        if frames_by_id[v4_frame].get("media_run_id") != v4_run_id or frames_by_id[vnext_frame].get("media_run_id") != vnext_run_id:
            raise MediaEvidenceError("comparison frame pair does not preserve track attribution")
    observations = _require_list(comparison.get("reviewer_observations"), "v4_vnext_comparison.reviewer_observations")
    for index, observation in enumerate(observations):
        _require_text(observation, f"v4_vnext_comparison.reviewer_observations[{index}]")

    binding = _require_mapping(evidence.get("vnext_runtime_binding"), "vnext_runtime_binding")
    _require_text(binding.get("vec_artifact_id"), "vnext_runtime_binding.vec_artifact_id")
    _require_text(binding.get("projection_artifact_id"), "vnext_runtime_binding.projection_artifact_id")
    _validate_record_binding(runs_root, binding, "vec_record_path")
    _validate_record_binding(runs_root, binding, "projection_record_path")
    _validate_record_binding(runs_root, binding, "run_record_path")
    _validate_record_binding(runs_root, binding, "result_record_path")

    rollback = _require_mapping(evidence.get("rollback_drill"), "rollback_drill")
    _parse_timestamp(rollback.get("performed_at"), "rollback_drill.performed_at")
    _require_text(rollback.get("operator"), "rollback_drill.operator")
    _validate_record_binding(runs_root, rollback, "record_path")
    if rollback.get("production_entry_before") != "v4_unchanged" or rollback.get("production_entry_after") != "v4_unchanged":
        raise MediaEvidenceError("rollback drill must leave v4 as the production entry")
    if rollback.get("production_switch_authorized") is not False:
        raise MediaEvidenceError("rollback drill cannot authorize production switching")
    if rollback.get("result") != "v4_unchanged":
        raise MediaEvidenceError("rollback drill result must be v4_unchanged")


def _candidate_packet() -> Path | None:
    raw = os.environ.get("MODE_P_A10_MEDIA_EVIDENCE", "").strip()
    if raw:
        path = Path(raw).expanduser().resolve()
        try:
            path.relative_to(A10_RUNS_ROOT.resolve())
        except ValueError as exc:
            raise MediaEvidenceError("MODE_P_A10_MEDIA_EVIDENCE must stay inside A10 runs") from exc
        return path
    if not A10_RUNS_ROOT.is_dir():
        return None
    candidates = sorted(A10_RUNS_ROOT.rglob("MEDIA_VISUAL_ACCEPTANCE.json"))
    if not candidates:
        return None
    if len(candidates) != 1:
        raise MediaEvidenceError("set MODE_P_A10_MEDIA_EVIDENCE when multiple A10 packets exist")
    return candidates[0]


def test_validator_rejects_controller_minimum_shape(tmp_path: Path) -> None:
    """A non-empty controller-shaped JSON object is never enough for A10."""

    packet = {
        "kind": "MEDIA_VISUAL_ACCEPTANCE",
        "accepted": True,
        "evidence_mode": "EXTERNAL_REAL_MEDIA",
        "architecture_authority_sha256": ARCHITECTURE_SHA256,
        "production_switch_authorized": False,
        "media_runs": [{}],
        "frame_evidence": [{}],
        "v4_vnext_comparison": {"same_scene_digest": "0" * 64},
        "vnext_runtime_binding": {},
        "rollback_drill": {},
    }
    with pytest.raises(MediaEvidenceError, match=r"media_runs\[0\].run_id"):
        validate_real_media_packet(packet, runs_root=tmp_path)


def test_external_packet_is_physically_reviewable_without_claiming_visual_quality() -> None:
    packet_path = _candidate_packet()
    if packet_path is None:
        pytest.skip(
            "A10 external-real-media packet is absent; this is not visual acceptance and keeps the release gate closed"
        )
    try:
        payload = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MediaEvidenceError("A10 evidence packet is not readable UTF-8 JSON") from exc
    validate_real_media_packet(payload)
