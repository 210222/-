"""v3.0 zero-model Gate 0 over the canonical VEC and ProjectionAST.

Architecture authority: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0 sections
3-4, 13, 15 A7, and 16.  Gate 0 never makes a creative or visual-quality
judgement.  It only proves deterministic structure, identity, timing,
binding, projection, prompt-budget, and text-claim invariants before an
independent DP session may start.
"""

from __future__ import annotations

import dataclasses
import json

from mode_p_vnext.domain.artifact import (
    DOMAIN_SCHEMA_VERSION,
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    canonical_sha256,
)
from mode_p_vnext.domain.evidence import DeterministicGateResult
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.projection import ProjectionAST, ProjectionManifest
from mode_p_vnext.domain.vec import StoryboardRole, VisualExecutionContract
from mode_p_vnext.prompts.compiler import CompiledPrompt
from mode_p_vnext.services.projection_compiler import (
    StoryboardProjection,
    VideoProjection,
    node_attribute,
    projection_nodes,
)


TEXT_VALIDATED = "TEXT_VALIDATED"

SCHEMA_INTEGRITY = "schema_integrity"
DIGEST_INTEGRITY = "digest_integrity"
ID_INTEGRITY = "id_integrity"
TICK_INTEGRITY = "tick_integrity"
BOUNDARY_INTEGRITY = "n_plus_one_boundary_integrity"
TYPED_BINDING_INTEGRITY = "typed_binding_integrity"
PROJECTION_IDENTITY = "single_projection_identity"
PROMPT_BUDGET = "prompt_budget"
SAFETY_BOUNDARY = "safety_boundary"
CLAIM_CEILING = "text_claim_ceiling"

GATE0_CHECK_IDS = (
    SCHEMA_INTEGRITY,
    DIGEST_INTEGRITY,
    ID_INTEGRITY,
    TICK_INTEGRITY,
    BOUNDARY_INTEGRITY,
    TYPED_BINDING_INTEGRITY,
    PROJECTION_IDENTITY,
    PROMPT_BUDGET,
    SAFETY_BOUNDARY,
    CLAIM_CEILING,
)

_FORBIDDEN_PROMPT_KEYS = frozenset(
    {
        "private_reasoning",
        "chain_of_thought",
        "dp_history",
        "runtime_code",
        "telemetry",
        "cache",
        "golden",
        "holdout",
    }
)
_HEX = frozenset("0123456789abcdef")


def _fail(failed: set[str], check_id: str, condition: bool) -> None:
    if not condition:
        failed.add(check_id)


def _vec_output_digest(vec: VisualExecutionContract) -> str:
    fields = {
        item.name: getattr(vec, item.name)
        for item in dataclasses.fields(vec)
        if item.name != "canonical_output_sha256"
    }
    return canonical_sha256(fields)


def _vec_ids(vec: VisualExecutionContract) -> tuple[str, ...]:
    return (
        vec.contract_id,
        *(item.point_id for item in vec.curve_points),
        *(item.decision_id for item in vec.decisions),
        *(item.unit_id for item in vec.generation_units),
        *(item.shot_id for item in vec.shots),
        *(beat.beat_id for shot in vec.shots for beat in shot.visual_beats),
        *(item.boundary_id for item in vec.boundaries),
        *(item.event_id for item in vec.audio_events),
        *(item.requirement_id for item in vec.voice_requirements),
        *(item.requirement_id for item in vec.reference_requirements),
    )


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(item in _HEX for item in value)
    )


def _is_machine_id(value: object) -> bool:
    return isinstance(value, str) and value.startswith("id:") and _is_sha256(value[3:])


def _all_bound_ids(vec: VisualExecutionContract, ast: ProjectionAST) -> tuple[str, ...]:
    return (
        vec.contract_id,
        vec.execution_design_artifact_id,
        vec.blocking_commit_artifact_id,
        *vec.source_fact_ids,
        *(item.point_id for item in vec.curve_points),
        *(item.decision_id for item in vec.decisions),
        *(item.unit_id for item in vec.generation_units),
        *(item.shot_id for item in vec.shots),
        *(item.generation_unit_id for item in vec.shots),
        *(item.blocking_beat_id for item in vec.shots),
        *(item_id for item in vec.shots for item_id in item.decision_ids),
        *(beat.beat_id for shot in vec.shots for beat in shot.visual_beats),
        *(beat.start_state_id for shot in vec.shots for beat in shot.visual_beats),
        *(beat.end_state_id for shot in vec.shots for beat in shot.visual_beats),
        *(item.boundary_id for item in vec.boundaries),
        *(item_id for item in vec.boundaries for item_id in item.decision_ids),
        *(item.before_state_id for item in vec.boundaries),
        *(item.after_state_id for item in vec.boundaries),
        *(item.event_id for item in vec.audio_events),
        *(item.visual_beat_id for item in vec.audio_events),
        *(item.requirement_id for item in vec.voice_requirements),
        *(item.requirement_id for item in vec.reference_requirements),
        ast.projection_id,
        ast.source_vec_artifact_id,
        *(item.node_id for item in projection_nodes(ast)),
        *(item.source_beat_id for item in projection_nodes(ast)),
        *(item.source_shot_id for item in projection_nodes(ast)),
        *(item.start_state_id for item in projection_nodes(ast)),
        *(item.end_state_id for item in projection_nodes(ast)),
        *(item_id for item in projection_nodes(ast) for item_id in item.decision_ids),
    )


def _check_ticks(vec: VisualExecutionContract) -> bool:
    units = {item.unit_id: item for item in vec.generation_units}
    if len(units) != len(vec.shots):
        return False
    placements = tuple(vec.scene_timeline.generation_unit_placements)
    if len(placements) != len(vec.generation_units):
        return False
    if placements[0].interval.start_tick != vec.scene_timeline.interval.start_tick:
        return False
    if placements[-1].interval.end_tick != vec.scene_timeline.interval.end_tick:
        return False
    if any(
        left.interval.end_tick != right.interval.start_tick
        for left, right in zip(placements, placements[1:])
    ):
        return False
    for shot in vec.shots:
        unit = units.get(shot.generation_unit_id)
        if unit is None or unit.shot_id != shot.shot_id:
            return False
        if shot.interval.start_tick != 0 or shot.interval != unit.timeline.interval:
            return False
        if shot.interval.end_tick > vec.capability_profile.max_generation_ticks:
            return False
        beats = shot.visual_beats
        if beats[0].interval.start_tick != 0 or beats[-1].interval.end_tick != shot.interval.end_tick:
            return False
        if any(
            left.interval.end_tick != right.interval.start_tick
            or left.end_state_id != right.start_state_id
            for left, right in zip(beats, beats[1:])
        ):
            return False
    return True


def _check_boundaries(vec: VisualExecutionContract) -> bool:
    if len(vec.boundaries) != len(vec.shots) + 1:
        return False
    if tuple(item.boundary_ordinal for item in vec.boundaries) != tuple(
        range(len(vec.shots) + 1)
    ):
        return False
    units = {item.unit_id: item for item in vec.generation_units}
    for index, boundary in enumerate(vec.boundaries):
        expected_from = None if index == 0 else vec.shots[index - 1].shot_id
        expected_to = None if index == len(vec.shots) else vec.shots[index].shot_id
        expected_tick = (
            units[vec.shots[0].generation_unit_id].scene_placement.interval.start_tick
            if index == 0
            else units[vec.shots[-1].generation_unit_id].scene_placement.interval.end_tick
            if index == len(vec.shots)
            else units[vec.shots[index - 1].generation_unit_id].scene_placement.interval.end_tick
        )
        if (
            boundary.from_shot_id != expected_from
            or boundary.to_shot_id != expected_to
            or boundary.scene_tick != expected_tick
        ):
            return False
    return True


def _check_bindings(vec: VisualExecutionContract) -> bool:
    approved_ids = set(vec.source_fact_ids)
    approved_handles = set(vec.approved_fact_handles)
    shots = {item.shot_id: item for item in vec.shots}
    beats = {item.beat_id: item for shot in vec.shots for item in shot.visual_beats}
    references = {item.requirement_id: item for item in vec.reference_requirements}
    audio = {item.event_id: item for item in vec.audio_events}
    if any(
        item.source_fact_id not in approved_ids
        or item.source_fact_handle not in approved_handles
        or item.shot_id not in shots
        or item.requirement_id not in shots[item.shot_id].reference_requirement_ids
        or (
            item.visual_beat_id is not None
            and (
                item.visual_beat_id not in beats
                or beats[item.visual_beat_id].shot_id != item.shot_id
                or item.requirement_id not in beats[item.visual_beat_id].reference_requirement_ids
            )
        )
        for item in vec.reference_requirements
    ):
        return False
    if any(
        item.source_fact_id not in approved_ids
        or item.source_fact_handle not in approved_handles
        or item.shot_id not in shots
        or item.visual_beat_id not in beats
        or beats[item.visual_beat_id].shot_id != item.shot_id
        or item.event_id not in shots[item.shot_id].audio_event_ids
        or item.event_id not in beats[item.visual_beat_id].audio_event_ids
        or not beats[item.visual_beat_id].interval.contains(item.marker.tick)
        for item in vec.audio_events
    ):
        return False
    for shot in vec.shots:
        if any(
            item_id not in references or references[item_id].shot_id != shot.shot_id
            for item_id in shot.reference_requirement_ids
        ):
            return False
        if any(
            item_id not in audio or audio[item_id].shot_id != shot.shot_id
            for item_id in shot.audio_event_ids
        ):
            return False
        for beat in shot.visual_beats:
            if any(
                item_id not in references
                or references[item_id].visual_beat_id != beat.beat_id
                for item_id in beat.reference_requirement_ids
            ):
                return False
            if any(
                item_id not in audio or audio[item_id].visual_beat_id != beat.beat_id
                for item_id in beat.audio_event_ids
            ):
                return False
    voice_by_event = {item.audio_event_id: item for item in vec.voice_requirements}
    return set(voice_by_event) == set(audio) and all(
        voice_by_event[event_id].shot_id == event.shot_id
        and voice_by_event[event_id].visual_beat_id == event.visual_beat_id
        and voice_by_event[event_id].character_label == event.character_label
        for event_id, event in audio.items()
    )


def _check_projection(
    vec: VisualExecutionContract,
    ast: ProjectionAST,
    storyboard: StoryboardProjection,
    video: VideoProjection,
) -> bool:
    if storyboard.ast is not ast or video.ast is not ast:
        return False
    nodes = projection_nodes(ast)
    if ast.source_vec_artifact_id != vec.contract_id:
        return False
    if tuple(video.nodes) != nodes or any(
        actual is not expected for actual, expected in zip(video.nodes, nodes)
    ):
        return False
    node_by_id = {item.node_id: item for item in nodes}
    if any(node_by_id.get(item.node_id) is not item for item in storyboard.nodes):
        return False
    selected = tuple(item.node_id for item in storyboard.nodes)
    if selected != tuple(item.node_id for item in nodes if item.node_id in set(selected)):
        return False
    if any(
        node_attribute(item, "storyboard_role", str) == StoryboardRole.OMIT.value
        for item in storyboard.nodes
    ):
        return False
    required_ids = {
        item.node_id
        for item in nodes
        if node_attribute(item, "storyboard_role", str) == StoryboardRole.REQUIRED.value
    }
    if not required_ids.issubset(selected):
        return False

    vec_digest = canonical_sha256(vec)
    ast_digest = canonical_sha256(ast)
    capability_digest = canonical_sha256(vec.capability_profile)
    reference_digest = canonical_sha256(vec.reference_requirements)
    audio_digest = canonical_sha256(
        {"audio_events": vec.audio_events, "voice_requirements": vec.voice_requirements}
    )
    for manifest in (storyboard.manifest, video.manifest):
        if type(manifest) is not ProjectionManifest:
            return False
        if (
            manifest.vec_digest != vec_digest
            or manifest.projection_ast_digest != ast_digest
            or manifest.source_node_ids != tuple(item.node_id for item in nodes)
            or manifest.capability_profile_digest != capability_digest
            or manifest.reference_binding_digest != reference_digest
            or manifest.audio_binding_digest != audio_digest
        ):
            return False
    shots = {item.shot_id: item for item in vec.shots}
    beats = {item.beat_id: item for shot in vec.shots for item in shot.visual_beats}
    units = {item.shot_id: item for item in vec.generation_units}
    for node in nodes:
        shot = shots.get(node.source_shot_id)
        beat = beats.get(node.source_beat_id)
        if shot is None or beat is None or beat.shot_id != shot.shot_id:
            return False
        placement = units[shot.shot_id].scene_placement.interval
        if (
            node.interval.start_tick != placement.start_tick + beat.interval.start_tick
            or node.interval.end_tick != placement.start_tick + beat.interval.end_tick
            or node.start_state_id != beat.start_state_id
            or node.end_state_id != beat.end_state_id
            or node.decision_ids != beat.decision_ids
            or node_attribute(node, "vec_digest", str) != vec_digest
            or node_attribute(node, "capability_profile_digest", str) != capability_digest
        ):
            return False
    return True


def _prompt_payload(prompt: CompiledPrompt) -> dict[str, object] | None:
    try:
        payload = json.loads(prompt.user_message)
    except (TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _contains_forbidden_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in _FORBIDDEN_PROMPT_KEYS
            or _contains_forbidden_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _check_prompts(prompts: tuple[CompiledPrompt, ...]) -> tuple[bool, bool]:
    if not prompts or not all(type(item) is CompiledPrompt for item in prompts):
        return False, False
    budget_ok = True
    safety_ok = True
    for prompt in prompts:
        signature = prompt.signature
        report = prompt.budget_report
        payload = _prompt_payload(prompt)
        budget_ok = budget_ok and (
            report.kind == "prompt"
            and report.stage == signature.stage.value
            and report.character_count == len(prompt.prompt_text)
            and report.hard_limit == signature.prompt_budget
            and report.character_count <= signature.prompt_budget
            and _is_sha256(prompt.schema_digest)
            and _is_sha256(prompt.approved_input_digest)
        )
        approved_input = payload.get("approved_input") if payload is not None else None
        safety_ok = safety_ok and (
            signature.version == "3.0"
            and isinstance(approved_input, dict)
            and set(approved_input).issubset(signature.approved_input_keys)
            and not _contains_forbidden_key(payload)
        )
    return budget_ok, safety_ok


def run_gate0(
    *,
    vec: VisualExecutionContract,
    ast: ProjectionAST,
    storyboard: StoryboardProjection,
    video: VideoProjection,
    compiled_prompts: tuple[CompiledPrompt, ...],
    claim_ceiling: str,
    id_factory: IdFactory,
    program_version: str,
) -> DeterministicGateResult:
    """Return the sole canonical ``DeterministicGateResult`` authority."""

    if type(vec) is not VisualExecutionContract:
        raise DomainValidationError("vec must be the exact canonical VisualExecutionContract")
    if type(ast) is not ProjectionAST:
        raise DomainValidationError("ast must be the exact canonical ProjectionAST")
    if type(storyboard) is not StoryboardProjection or type(video) is not VideoProjection:
        raise DomainValidationError("projection views must be exact v3 delivery views")
    if not isinstance(id_factory, IdFactory) or id_factory.program_version != program_version:
        raise DomainValidationError("IdFactory must match program_version")

    failed: set[str] = set()
    _fail(failed, SCHEMA_INTEGRITY, DOMAIN_SCHEMA_VERSION == "3.0")
    _fail(failed, DIGEST_INTEGRITY, vec.canonical_output_sha256 == _vec_output_digest(vec))

    all_ids = (*_vec_ids(vec), ast.projection_id, *(item.node_id for item in projection_nodes(ast)))
    _fail(
        failed,
        ID_INTEGRITY,
        len(all_ids) == len(set(all_ids))
        and all(_is_machine_id(item) for item in _all_bound_ids(vec, ast)),
    )
    _fail(failed, TICK_INTEGRITY, _check_ticks(vec))
    _fail(failed, BOUNDARY_INTEGRITY, _check_boundaries(vec))
    _fail(failed, TYPED_BINDING_INTEGRITY, _check_bindings(vec))
    try:
        projection_ok = _check_projection(vec, ast, storyboard, video)
    except (DomainValidationError, KeyError, TypeError, ValueError):
        projection_ok = False
    _fail(failed, PROJECTION_IDENTITY, projection_ok)
    budget_ok, safety_ok = _check_prompts(tuple(compiled_prompts))
    _fail(failed, PROMPT_BUDGET, budget_ok)
    _fail(failed, SAFETY_BOUNDARY, safety_ok)
    _fail(failed, CLAIM_CEILING, claim_ceiling == TEXT_VALIDATED)

    evidence_refs = (
        SourceRef(source_id=vec.contract_id, digest=canonical_sha256(vec)),
        SourceRef(source_id=ast.projection_id, digest=canonical_sha256(ast)),
        SourceRef(
            source_id=f"storyboard-manifest:{ast.projection_id}",
            digest=canonical_sha256(storyboard.manifest),
        ),
        SourceRef(
            source_id=f"video-manifest:{ast.projection_id}",
            digest=canonical_sha256(video.manifest),
        ),
        *(SourceRef(
            source_id=f"compiled-prompt:{ordinal}:{item.signature.stage.value}",
            digest=canonical_sha256(item),
        ) for ordinal, item in enumerate(compiled_prompts)),
    )
    failed_check_ids = tuple(item for item in GATE0_CHECK_IDS if item in failed)
    target_artifact_ids = tuple(dict.fromkeys((vec.contract_id, ast.projection_id)))
    result_input_digest = canonical_sha256(
        {
            "target_artifact_ids": target_artifact_ids,
            "checks": GATE0_CHECK_IDS,
            "failed": failed_check_ids,
            "evidence": evidence_refs,
            "claim_ceiling": claim_ceiling,
        }
    )
    result_id = id_factory.create(
        artifact_kind=ArtifactKind.GATE0_RESULT,
        episode_id=vec.episode_id,
        scene_id=vec.scene_id,
        stage="gate0",
        input_digest=result_input_digest,
        ordinal=0,
    )
    return DeterministicGateResult(
        result_id=result_id,
        target_artifact_ids=target_artifact_ids,
        check_ids=GATE0_CHECK_IDS,
        failed_check_ids=failed_check_ids,
        evidence_refs=evidence_refs,
        passed=not failed_check_ids,
    )


__all__ = [
    "GATE0_CHECK_IDS",
    "TEXT_VALIDATED",
    "run_gate0",
]
