"""Isolated text-only Shadow runner for an unknown-script Director case."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .agent import (
    DirectorAgent,
    PhaseAPlanningResult,
    PhaseBPlanningResult,
    _phase_a_fingerprint,
)
from .cache import content_address
from .capsules import RetrievalContext, retrieve_k1, retrieve_k2
from .contracts import (
    BlockingBeat,
    BlockingCommit,
    CharacterBlockingState,
    DirectorContractError,
    DirectorProblem,
    DirectorProblemSet,
    EpisodeDirectionState,
    EpisodeRequest,
    PhaseAResult,
    PropBlockingState,
    SceneInput,
    SceneIntentBeat,
    SceneIntentContract,
)
from .knowledge_catalog import load_actual_catalog
from .provider_deepseek import DeepSeekDirectorProvider, TEXT_VALIDATED


UNKNOWN_SCRIPT_CASE_ID = "DIRECTOR-UNKNOWN-TEXT-001"


def unknown_script_case() -> tuple[EpisodeRequest, SceneInput]:
    """A fixture not derived from the EP35 continuity examples."""

    episode = EpisodeRequest(
        episode_id="UNK-E01",
        episode_premise=(
            "A theatre stage manager must decide whether to open an emergency "
            "exit after a blackout reveals that her mentor no longer controls "
            "the decision."
        ),
        approved_story_facts=(
            "The scene is backstage at an old theatre at night.",
            "Only emergency lighting is active.",
            "Lin Lan and Zhao Heng are the only visible characters.",
            "A metal emergency key is the only handled prop.",
        ),
    )
    scene = SceneInput(
        scene_id="UNK-E01-S03",
        episode_id=episode.episode_id,
        script_excerpt=(
            "停电后应急灯亮起。赵衡把唯一的应急门钥匙放在桌面，"
            "对林岚说：‘这次你决定。’他退到门外。林岚没有马上拿钥匙，"
            "只听着观众席传来的敲门声，随后把视线落向钥匙。"
        ),
        scene_context=(
            "The mentor transfers responsibility and leaves; the remaining "
            "character must absorb the decision before acting."
        ),
        character_state=(
            "Lin Lan: alert, initially subordinate, left alone with the choice",
            "Zhao Heng: controlled, relinquishes authority, exits",
        ),
        scene_tags=(
            "power",
            "relationship",
            "departure",
            "gaze",
            "dialogue",
            "reveal",
            "blocking",
            "composition",
            "screen_direction",
        ),
        approved_context=(
            "location_layout_approved",
            "wardrobe_locked",
            "voice_assets_locked",
            "blocking_verified",
        ),
        impact_level="high",
    )
    return episode, scene


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _checkpoint(
    run_dir: Path,
    *,
    name: str,
    provider: DeepSeekDirectorProvider,
    payload: Mapping[str, Any],
    prior_model_calls: tuple[Mapping[str, Any], ...] = (),
) -> None:
    _write_json_atomic(
        run_dir / name,
        {
            "schema_version": "director-text-shadow-checkpoint-v1",
            "checkpoint": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model_calls": [
                *prior_model_calls,
                *(asdict(item) for item in provider.call_records),
            ],
            "media_visual_acceptance": False,
            "production_entry_changed": False,
            **payload,
        },
    )


def _next_failure_checkpoint_name(run_dir: Path) -> str:
    """Preserve every failed resume attempt instead of overwriting evidence."""

    primary = run_dir / "FAILED_TEXT_SHADOW.json"
    if not primary.exists():
        return primary.name
    index = 2
    while (run_dir / f"FAILED_TEXT_SHADOW_{index:03}.json").exists():
        index += 1
    return f"FAILED_TEXT_SHADOW_{index:03}.json"


def _restore_phase_a_checkpoint(
    *,
    checkpoint_path: Path,
    scene: SceneInput,
    catalog: tuple[Any, ...],
) -> tuple[PhaseAPlanningResult, tuple[Mapping[str, Any], ...]]:
    """Restore only a previously accepted E0/S1 checkpoint.

    The restoration repeats deterministic K1 retrieval and verifies its stored
    fingerprint.  It never trusts an opaque previous model response or resumes
    from a partial B0/B1 artifact.
    """

    try:
        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        raw_phase_a = payload["phase_a"]
        raw_intent = raw_phase_a["scene_intent"]
        intent = SceneIntentContract(
            **{
                **raw_intent,
                "beats": tuple(
                    SceneIntentBeat(**beat) for beat in raw_intent["beats"]
                ),
            }
        )
        raw_problem_set = raw_phase_a["problem_set"]
        phase_a = PhaseAResult(
            scene_intent=intent,
            problem_set=DirectorProblemSet(
                scene_id=raw_problem_set["scene_id"],
                problems=tuple(
                    DirectorProblem(**problem)
                    for problem in raw_problem_set["problems"]
                ),
            ),
        )
        direction = EpisodeDirectionState(**payload["episode_direction"])
        prior_calls = tuple(payload["model_calls"])
        expected_k1 = str(payload["k1_packet_sha256"])
    except (KeyError, TypeError, json.JSONDecodeError, DirectorContractError) as exc:
        raise DirectorContractError(
            "E0/S1 checkpoint is not safely recoverable"
        ) from exc
    if direction.episode_id != scene.episode_id or direction.director_id != "director-vnext1-deepseek":
        raise DirectorContractError("E0/S1 checkpoint identity does not match the Shadow case")
    if phase_a.scene_intent.scene_id != scene.scene_id:
        raise DirectorContractError("E0/S1 checkpoint scene does not match the Shadow case")
    k1_packet = retrieve_k1(
        packet_id=f"K1-{scene.scene_id}",
        problems=phase_a.problem_set,
        catalog=catalog,
        context=RetrievalContext(
            scene_tags=scene.scene_tags,
            approved_context=scene.approved_context,
            impact_level=scene.impact_level,
        ),
    )
    if k1_packet.fingerprint != expected_k1:
        raise DirectorContractError("E0/S1 checkpoint K1 fingerprint no longer matches")
    # A previous failed attempt may have recorded later rejected calls. Preserve
    # those hashes/timings in the next evidence record without treating them as
    # accepted stage state. The latest failure is authoritative because each
    # resumed failure contains all earlier call records.
    failure_files = sorted(run_dir for run_dir in checkpoint_path.parent.glob("FAILED_TEXT_SHADOW*.json"))
    if failure_files:
        try:
            failure_payload = json.loads(failure_files[-1].read_text(encoding="utf-8"))
            failure_calls = tuple(failure_payload.get("model_calls", ()))
            if failure_calls[: len(prior_calls)] == prior_calls:
                prior_calls = failure_calls
        except (OSError, TypeError, json.JSONDecodeError):
            # The typed E0/S1 checkpoint remains the recovery authority; an
            # unreadable failure log must not silently block safe recovery.
            pass
    return (
        PhaseAPlanningResult(
            episode_direction=direction,
            phase_a=phase_a,
            k1_packet=k1_packet,
            episode_cache_key="recovered-e0",
            phase_a_cache_key="recovered-s1",
        ),
        prior_calls,
    )


def _restore_e0_checkpoint(
    *,
    checkpoint_path: Path,
    episode: EpisodeRequest,
) -> tuple[EpisodeDirectionState, tuple[Mapping[str, Any], ...]]:
    """Restore an accepted E0 without treating an incomplete S1 as valid.

    E0 is an independently validated, expensive text decision.  Persisting it
    lets an S1 transport or contract failure resume at S1, while S1 itself is
    still required to complete before a Phase-A checkpoint exists.
    """

    try:
        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        direction = EpisodeDirectionState(**payload["episode_direction"])
        prior_calls = tuple(payload["model_calls"])
        expected_episode_input = str(payload["episode_input_sha256"])
    except (KeyError, TypeError, json.JSONDecodeError, DirectorContractError) as exc:
        raise DirectorContractError("E0 checkpoint is not safely recoverable") from exc
    if expected_episode_input != _canonical_hash(asdict(episode)):
        raise DirectorContractError("E0 checkpoint input does not match the Shadow case")
    if (
        direction.episode_id != episode.episode_id
        or direction.director_id != "director-vnext1-deepseek"
    ):
        raise DirectorContractError("E0 checkpoint identity does not match the Shadow case")
    failure_files = sorted(checkpoint_path.parent.glob("FAILED_TEXT_SHADOW*.json"))
    if failure_files:
        try:
            failure_payload = json.loads(failure_files[-1].read_text(encoding="utf-8"))
            failure_calls = tuple(failure_payload.get("model_calls", ()))
            if failure_calls[: len(prior_calls)] == prior_calls:
                prior_calls = failure_calls
        except (OSError, TypeError, json.JSONDecodeError):
            # The typed E0 checkpoint remains authoritative if a failure log
            # is unreadable; an incomplete failure log must not fabricate S1.
            pass
    return direction, prior_calls


def _resume_phase_a_after_e0(
    *,
    provider: DeepSeekDirectorProvider,
    episode: EpisodeRequest,
    scene: SceneInput,
    direction: EpisodeDirectionState,
    catalog: tuple[Any, ...],
) -> PhaseAPlanningResult:
    """Run and validate S1 from a restored E0 without reissuing E0."""

    if episode.episode_id != scene.episode_id:
        raise DirectorContractError("scene must be planned by its own episode direction")
    phase_a = provider.analyse_scene_phase_a(scene, direction)
    if phase_a.scene_intent.scene_id != scene.scene_id:
        raise DirectorContractError("S1 output scene does not match its request")
    k1_packet = retrieve_k1(
        packet_id=f"K1-{scene.scene_id}",
        problems=phase_a.problem_set,
        catalog=catalog,
        context=RetrievalContext(
            scene_tags=scene.scene_tags,
            approved_context=scene.approved_context,
            impact_level=scene.impact_level,
        ),
    )
    return PhaseAPlanningResult(
        episode_direction=direction,
        phase_a=phase_a,
        k1_packet=k1_packet,
        episode_cache_key=content_address("director-vnext1/e0", episode.cache_payload),
        phase_a_cache_key=content_address(
            "director-vnext1/s1",
            {"scene": scene.cache_payload, "episode_direction": direction},
        ),
    )


def _restore_b0_k2_checkpoint(
    *,
    checkpoint_path: Path,
    scene: SceneInput,
    phase_a: PhaseAResult,
    catalog: tuple[Any, ...],
) -> tuple[BlockingCommit, Any]:
    """Restore a validated B0 state and deterministically rebuild K2."""

    try:
        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        raw_commit = payload["blocking_commit"]
        beats = tuple(
            BlockingBeat(
                **{
                    **raw_beat,
                    "character_states": tuple(
                        CharacterBlockingState(**state)
                        for state in raw_beat["character_states"]
                    ),
                    "prop_states": tuple(
                        PropBlockingState(**state)
                        for state in raw_beat["prop_states"]
                    ),
                }
            )
            for raw_beat in raw_commit["beats"]
        )
        blocking = BlockingCommit(**{**raw_commit, "beats": beats})
        expected_k2 = str(payload["k2_packet_sha256"])
    except (KeyError, TypeError, json.JSONDecodeError, DirectorContractError) as exc:
        raise DirectorContractError(
            "B0/K2 checkpoint is not safely recoverable"
        ) from exc
    if blocking.scene_id != scene.scene_id:
        raise DirectorContractError("B0/K2 checkpoint scene does not match the Shadow case")
    if blocking.phase_a_fingerprint != _phase_a_fingerprint(phase_a):
        raise DirectorContractError("B0/K2 checkpoint does not match the accepted Phase A")
    k2_packet = retrieve_k2(
        packet_id=f"K2-{scene.scene_id}-{blocking.commit_id}",
        problems=phase_a.problem_set,
        catalog=catalog,
        context=RetrievalContext(
            scene_tags=scene.scene_tags,
            approved_context=scene.approved_context,
            impact_level=scene.impact_level,
        ),
        blocking_commit_id=blocking.commit_id,
    )
    if k2_packet.fingerprint != expected_k2:
        raise DirectorContractError("B0/K2 checkpoint K2 fingerprint no longer matches")
    return blocking, k2_packet


def run_unknown_script_text_shadow(
    *,
    provider: DeepSeekDirectorProvider,
    output_root: Path,
    run_id: str | None = None,
    resume: bool = False,
) -> Mapping[str, Any]:
    """Run E0/S1/B0/B1 and persist text evidence; never accept media."""

    episode, scene = unknown_script_case()
    effective_run_id = run_id or (
        f"{UNKNOWN_SCRIPT_CASE_ID}-{uuid.uuid4().hex[:12]}"
    )
    run_dir = output_root / effective_run_id
    if resume:
        if not run_dir.is_dir():
            raise DirectorContractError("resume requires an existing Shadow run directory")
        if (run_dir / "TEXT_SHADOW_EVIDENCE.json").exists():
            raise DirectorContractError("a completed Shadow run cannot be resumed")
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
    catalog = load_actual_catalog()
    agent = DirectorAgent(
        provider,
        director_id="director-vnext1-deepseek",
        catalog=catalog,
    )
    prior_model_calls: tuple[Mapping[str, Any], ...] = ()
    try:
        if resume:
            phase_a_checkpoint = run_dir / "CHECKPOINT_E0_S1.json"
            if phase_a_checkpoint.exists():
                phase_a_result, prior_model_calls = _restore_phase_a_checkpoint(
                    checkpoint_path=phase_a_checkpoint,
                    scene=scene,
                    catalog=tuple(catalog),
                )
            else:
                direction, prior_model_calls = _restore_e0_checkpoint(
                    checkpoint_path=run_dir / "CHECKPOINT_E0.json",
                    episode=episode,
                )
                phase_a_result = _resume_phase_a_after_e0(
                    provider=provider,
                    episode=episode,
                    scene=scene,
                    direction=direction,
                    catalog=tuple(catalog),
                )
                _checkpoint(
                    run_dir,
                    name="CHECKPOINT_E0_S1.json",
                    provider=provider,
                    payload={
                        "episode_direction": asdict(phase_a_result.episode_direction),
                        "phase_a": asdict(phase_a_result.phase_a),
                        "k1_packet_sha256": phase_a_result.k1_packet.fingerprint,
                    },
                    prior_model_calls=prior_model_calls,
                )
        else:
            direction, _ = agent.episode_direction(episode)
            _checkpoint(
                run_dir,
                name="CHECKPOINT_E0.json",
                provider=provider,
                payload={
                    "episode_direction": asdict(direction),
                    "episode_input_sha256": _canonical_hash(asdict(episode)),
                },
            )
            phase_a_result = agent.plan_phase_a(episode, scene)
            _checkpoint(
                run_dir,
                name="CHECKPOINT_E0_S1.json",
                provider=provider,
                payload={
                    "episode_direction": asdict(phase_a_result.episode_direction),
                    "phase_a": asdict(phase_a_result.phase_a),
                    "k1_packet_sha256": phase_a_result.k1_packet.fingerprint,
                },
            )
        b0_checkpoint = run_dir / "CHECKPOINT_B0_K2.json"
        if resume and b0_checkpoint.exists():
            blocking, k2_packet = _restore_b0_k2_checkpoint(
                checkpoint_path=b0_checkpoint,
                scene=scene,
                phase_a=phase_a_result.phase_a,
                catalog=tuple(catalog),
            )
        else:
            blocking = provider.create_blocking_commit(
                scene,
                phase_a_result.phase_a,
                phase_a_result.k1_packet,
            )
            if blocking.scene_id != scene.scene_id:
                raise DirectorContractError("BlockingCommit scene does not match its request")
            if blocking.phase_a_fingerprint != _phase_a_fingerprint(phase_a_result.phase_a):
                raise DirectorContractError("BlockingCommit must cite the exact Phase A result")
            k2_packet = retrieve_k2(
                packet_id=f"K2-{scene.scene_id}-{blocking.commit_id}",
                problems=phase_a_result.phase_a.problem_set,
                catalog=catalog,
                context=RetrievalContext(
                    scene_tags=scene.scene_tags,
                    approved_context=scene.approved_context,
                    impact_level=scene.impact_level,
                ),
                blocking_commit_id=blocking.commit_id,
            )
            _checkpoint(
                run_dir,
                name="CHECKPOINT_B0_K2.json",
                provider=provider,
                payload={
                    "blocking_commit": asdict(blocking),
                    "blocking_commit_sha256": blocking.fingerprint,
                    "k2_packet_sha256": k2_packet.fingerprint,
                },
                prior_model_calls=prior_model_calls,
            )
        phase_b = provider.design_phase_b(
            scene,
            phase_a_result.phase_a,
            blocking,
            phase_a_result.k1_packet,
            k2_packet,
        )
        result = PhaseBPlanningResult(
            phase_a_result=phase_a_result,
            blocking_commit=blocking,
            k2_packet=k2_packet,
            phase_b=phase_b,
        )
    except Exception as exc:
        _checkpoint(
            run_dir,
            name=_next_failure_checkpoint_name(run_dir),
            provider=provider,
            payload={
                "status": "FAILED_TEXT_ONLY",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "claim_ceiling": "TEXT_VALIDATED",
            },
            prior_model_calls=prior_model_calls,
        )
        raise
    current_records = tuple(asdict(item) for item in provider.call_records)
    records = (*prior_model_calls, *current_records)
    accepted_records = tuple(record for record in records if record["accepted"])
    if [record["stage"] for record in accepted_records] != ["E0", "S1", "B0", "B1"]:
        raise RuntimeError(
            "unknown-script Shadow must accept E0/S1/B0/B1 in order"
        )
    if any(int(record["attempt"]) > 2 for record in records):
        raise RuntimeError("unknown-script Shadow exceeded its one-repair limit")
    if any(
        record["media_inspection_performed"] or record["visual_acceptance_claimed"]
        for record in records
    ):
        raise RuntimeError("text-only Shadow cannot contain media acceptance")

    record = {
        "schema_version": "director-text-shadow-v1",
        "run_id": effective_run_id,
        "case_id": UNKNOWN_SCRIPT_CASE_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "director_id": agent.director_id,
        "model": accepted_records[-1]["model"],
        "validation_status": TEXT_VALIDATED,
        "claim_ceiling": "TEXT_VALIDATED",
        "episode_input_sha256": _canonical_hash(asdict(episode)),
        "scene_input_sha256": _canonical_hash(asdict(scene)),
        "episode_direction": asdict(
            result.phase_a_result.episode_direction
        ),
        "scene_intent": asdict(
            result.phase_a_result.phase_a.scene_intent
        ),
        "blocking_commit_sha256": result.blocking_commit.fingerprint,
        "vec_sha256": result.phase_b.visual_execution_contract.fingerprint,
        "model_calls": list(records),
        "accepted_stage_sequence": [item["stage"] for item in accepted_records],
        "knowledge": {
            "k1_packet_sha256": result.phase_a_result.k1_packet.fingerprint,
            "k2_packet_sha256": result.k2_packet.fingerprint,
            "runtime_full_sources_loaded": False,
        },
        "media": {
            "images_supplied_to_deepseek": 0,
            "videos_supplied_to_deepseek": 0,
            "frames_inspected_by_deepseek": 0,
            "visual_acceptance": False,
            "visual_acceptance_owner": "CPL-5",
        },
        "production_entry_changed": False,
    }
    _write_json_atomic(run_dir / "TEXT_SHADOW_EVIDENCE.json", record)
    return record


__all__ = [
    "UNKNOWN_SCRIPT_CASE_ID",
    "run_unknown_script_text_shadow",
    "unknown_script_case",
]
