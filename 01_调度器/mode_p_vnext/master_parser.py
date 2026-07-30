"""MODE:P vNext — Master Parser & Validator (V4.5).

Parses a vNext DIRECTOR_MASTER JSON structure into validated objects.
Fail-closed: any structural violation raises MasterParseError.
Never guesses natural language or modifies shots for the Director.

Spec references: LOOP §8, §12.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from mode_p_vnext.schema.canonical_timeline import TimeInterval
from mode_p_vnext.schema.generation_segment import GenerationSegment, CinematicShot

SHOT_REQUIRED = frozenset({
    "shot_id", "segment_id", "start_tick", "end_tick",
    "narrative_job", "camera_position", "shot_size",
    "focal_intent", "camera_motion", "composition",
    "lighting", "performance",
})


class MasterParseError(Exception):
    """Raised when master JSON fails structural validation."""
    pass


@dataclass
class DirectorMaster:
    """Parsed and validated Director Master."""
    master_id: str
    episode_id: str
    schema_version: str
    diagnosis_artifact_id: str = ""
    segments: List[GenerationSegment] = field(default_factory=list)
    fidelity_contract_id: str = ""
    knowledge_snapshot_id: str = ""


def parse_master(data: Dict[str, Any]) -> DirectorMaster:
    """Parse a master dict into a DirectorMaster. Raises on any violation."""
    if "master_id" not in data:
        raise MasterParseError("Missing required field: master_id")
    if "episode_id" not in data:
        raise MasterParseError("Missing required field: episode_id")
    if "segments" not in data:
        raise MasterParseError("Missing required field: segments")

    segments: List[GenerationSegment] = []
    for seg_data in data["segments"]:
        seg = _parse_segment(seg_data)
        segments.append(seg)

    return DirectorMaster(
        master_id=data["master_id"],
        episode_id=data["episode_id"],
        schema_version=data.get("schema_version", "4.0"),
        diagnosis_artifact_id=data.get("diagnosis_artifact_id", ""),
        segments=segments,
        fidelity_contract_id=data.get("fidelity_contract_id", ""),
        knowledge_snapshot_id=data.get("knowledge_snapshot_id", ""),
    )


def _parse_segment(data: Dict[str, Any]) -> GenerationSegment:
    seg_id = data.get("segment_id")
    if not seg_id:
        raise MasterParseError("segment missing segment_id")
    seg_iv = TimeInterval(
        start_tick=data["start_tick"],
        end_tick=data["end_tick"],
    )
    shots: List[CinematicShot] = []
    prev_end = seg_iv.start_tick
    for sdata in data.get("shots", []):
        shot = _parse_shot(sdata)
        if shot.time_range.start_tick < seg_iv.start_tick or \
           shot.time_range.end_tick > seg_iv.end_tick:
            raise MasterParseError(
                f"Shot '{shot.shot_id}' [{shot.time_range.start_tick},"
                f"{shot.time_range.end_tick}) outside segment '{seg_id}' "
                f"[{seg_iv.start_tick},{seg_iv.end_tick})"
            )
        if shot.time_range.start_tick != prev_end:
            raise MasterParseError(
                f"Shot '{shot.shot_id}' gap: expected start_tick={prev_end}, "
                f"got {shot.time_range.start_tick}"
            )
        prev_end = shot.time_range.end_tick
        shots.append(shot)

    if prev_end != seg_iv.end_tick:
        raise MasterParseError(
            f"Segment '{seg_id}': last shot ends at {prev_end}, "
            f"segment ends at {seg_iv.end_tick}"
        )

    return GenerationSegment(
        segment_id=seg_id,
        time_range=seg_iv,
        shots=shots,
        scene_id=data.get("scene_id", ""),
        narrative_summary=data.get("narrative_summary", ""),
        fact_bindings=data.get("fact_bindings", []),
        final_handoff_state_id=data.get("final_handoff_state_id", ""),
        knowledge_snapshot_id=data.get("knowledge_snapshot_id", ""),
    )


def _parse_shot(data: Dict[str, Any]) -> CinematicShot:
    missing = SHOT_REQUIRED - set(data.keys())
    if missing:
        raise MasterParseError(
            f"Shot missing required fields: {sorted(missing)}"
        )
    return CinematicShot(
        shot_id=data["shot_id"],
        segment_id=data["segment_id"],
        time_range=TimeInterval(data["start_tick"], data["end_tick"]),
        narrative_job=data["narrative_job"],
        camera_position=data["camera_position"],
        shot_size=data["shot_size"],
        focal_intent=data["focal_intent"],
        camera_motion=data["camera_motion"],
        composition=data["composition"],
        lighting=data["lighting"],
        performance=data["performance"],
        fact_ids=data.get("fact_ids", []),
        visibility_state_id=data.get("visibility_state_id", ""),
        entry_state_id=data.get("entry_state_id", ""),
        exit_state_id=data.get("exit_state_id", ""),
    )


def validate_master(master: DirectorMaster) -> List[str]:
    """Run post-parse validation. Returns structural violations only."""
    violations: List[str] = []
    if not master.segments:
        violations.append("Master has no segments")
    for seg in master.segments:
        if not seg.shots:
            violations.append(f"Segment '{seg.segment_id}' has no shots")
    return violations
