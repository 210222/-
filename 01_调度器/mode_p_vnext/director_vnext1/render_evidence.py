"""Non-production Shadow plans, render records, and FFmpeg extraction plans."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence, Tuple

from .contracts import DirectorContractError, VisualExecutionContract


RENDER_STATUSES = frozenset({"PLANNED", "SUBMITTED", "RENDERED", "VISUAL_REJECTED", "VISUALLY_ACCEPTED"})
FRAME_KINDS = frozenset({"opening", "panel", "boundary_before", "boundary_after", "ending"})


def _require(value: str, name: str) -> None:
    if not value or not value.strip():
        raise DirectorContractError(f"{name} is required")


@dataclass(frozen=True)
class ShadowExecutionPlan:
    plan_id: str
    contract_fingerprint: str
    holdout_fingerprint: str
    isolated_workspace: str
    external_submission_allowed: bool = False
    production_switch_allowed: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("plan_id", self.plan_id), ("contract_fingerprint", self.contract_fingerprint),
            ("holdout_fingerprint", self.holdout_fingerprint), ("isolated_workspace", self.isolated_workspace),
        ):
            _require(value, name)
        if self.external_submission_allowed or self.production_switch_allowed:
            raise DirectorContractError("DDO-6 Shadow plan must remain isolated and non-production")


@dataclass(frozen=True)
class RenderRunRecord:
    run_id: str
    render_kind: str
    contract_fingerprint: str
    target_name: str
    status: str
    media_path: str = ""
    media_sha256: str = ""
    visual_reviewer: str = ""
    hard_invariant_result: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("run_id", self.run_id), ("render_kind", self.render_kind),
            ("contract_fingerprint", self.contract_fingerprint), ("target_name", self.target_name),
        ):
            _require(value, name)
        if self.render_kind not in {"storyboard", "video"}:
            raise DirectorContractError("render kind must be storyboard or video")
        if self.status not in RENDER_STATUSES:
            raise DirectorContractError("render status is invalid")
        artifact_statuses = {"RENDERED", "VISUAL_REJECTED", "VISUALLY_ACCEPTED"}
        if self.status in artifact_statuses:
            if not self.media_path or len(self.media_sha256) != 64:
                raise DirectorContractError("real render records require media path and SHA-256")
        if self.status == "VISUALLY_ACCEPTED":
            if not self.visual_reviewer or not self.hard_invariant_result:
                raise DirectorContractError("visual acceptance requires reviewer and hard-invariant result")


@dataclass(frozen=True)
class FrameTarget:
    target_id: str
    segment_id: str
    input_video_path: str
    kind: str
    local_tick: int
    source_refs: Tuple[str, ...]
    output_path: str

    def __post_init__(self) -> None:
        for name, value in (
            ("target_id", self.target_id), ("segment_id", self.segment_id),
            ("input_video_path", self.input_video_path), ("output_path", self.output_path),
        ):
            _require(value, name)
        if self.kind not in FRAME_KINDS or self.local_tick < 0 or not self.source_refs:
            raise DirectorContractError("frame target is incomplete")


@dataclass(frozen=True)
class FfmpegFramePlan:
    tick_rate: int
    targets: Tuple[FrameTarget, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.tick_rate, int) or self.tick_rate < 1 or not self.targets:
            raise DirectorContractError("FFmpeg plan requires positive tick rate and targets")

    def commands(self, ffmpeg_executable: str) -> Tuple[Tuple[str, ...], ...]:
        _require(ffmpeg_executable, "ffmpeg_executable")
        return tuple(
            (
                ffmpeg_executable, "-ss", f"{target.local_tick / self.tick_rate:.3f}", "-i",
                target.input_video_path, "-frames:v", "1", "-y", target.output_path,
            )
            for target in self.targets
        )


def build_ffmpeg_frame_plan(
    vec: VisualExecutionContract,
    *,
    input_video_paths: Mapping[str, str],
    output_directory: str,
    tick_rate: int = 10,
) -> FfmpegFramePlan:
    """Plan observed frames; execution is intentionally a separate user-approved step."""

    _require(output_directory, "output_directory")
    targets: list[FrameTarget] = []
    shots = {shot.shot_id: shot for shot in vec.shots}
    for segment in vec.segments:
        input_video_path = input_video_paths.get(segment.segment_id, "")
        _require(input_video_path, f"input_video_paths[{segment.segment_id}]")
        segment_shots = [shots[shot_id] for shot_id in segment.shot_ids]
        first, last = segment_shots[0], segment_shots[-1]
        targets.append(_target(segment.segment_id, input_video_path, "opening", first.start_tick, (f"shot:{first.shot_id}",), output_directory))
        for shot in segment_shots:
            targets.append(_target(segment.segment_id, input_video_path, "panel", shot.start_tick, (f"shot:{shot.shot_id}", f"beat:{shot.blocking_beat_id}"), output_directory))
        for boundary in vec.boundaries:
            if boundary.segment_id != segment.segment_id:
                continue
            before, after = shots[boundary.from_shot_id], shots[boundary.to_shot_id]
            targets.append(_target(segment.segment_id, input_video_path, "boundary_before", max(before.start_tick, before.end_tick - 1), (f"boundary:{boundary.boundary_id}",), output_directory))
            targets.append(_target(segment.segment_id, input_video_path, "boundary_after", after.start_tick, (f"boundary:{boundary.boundary_id}",), output_directory))
        targets.append(_target(segment.segment_id, input_video_path, "ending", max(last.start_tick, last.end_tick - 1), (f"shot:{last.shot_id}",), output_directory))
    return FfmpegFramePlan(tick_rate, tuple(targets))


def _target(segment_id: str, input_video_path: str, kind: str, tick: int, refs: Tuple[str, ...], output_directory: str) -> FrameTarget:
    target_id = f"{segment_id}-{kind}-{tick}"
    output_path = str(Path(output_directory) / f"{target_id}.png")
    return FrameTarget(target_id, segment_id, input_video_path, kind, tick, refs, output_path)


@dataclass(frozen=True)
class OwnerApprovalGate:
    gate_id: str
    contract_fingerprint: str
    storyboard_record: RenderRunRecord
    video_record: RenderRunRecord
    owner_approval_recorded: bool = False
    production_switch_authorized: bool = False

    def __post_init__(self) -> None:
        _require(self.gate_id, "gate_id")
        _require(self.contract_fingerprint, "contract_fingerprint")
        if self.storyboard_record.contract_fingerprint != self.contract_fingerprint or self.video_record.contract_fingerprint != self.contract_fingerprint:
            raise DirectorContractError("approval gate records must cite the same VEC")
        if self.owner_approval_recorded:
            if self.storyboard_record.status != "VISUALLY_ACCEPTED" or self.video_record.status != "VISUALLY_ACCEPTED":
                raise DirectorContractError("owner approval requires accepted storyboard and video render records")
        if self.production_switch_authorized:
            raise DirectorContractError("DDO-6 cannot authorize a production switch")
