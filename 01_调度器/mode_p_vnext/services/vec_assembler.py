"""Assemble the v3.1 Visual Execution Contract from typed creative Drafts.

The director Draft is deliberately non-executable: it contains creative
choices, duration intents, and opaque typed binding handles only.  This module
is the sole authority that creates local IDs, hashes, ticks, placements,
boundaries, resolved fact bindings, and the final VEC graph.
"""

from __future__ import annotations

from mode_p_vnext.domain.artifact import ArtifactKind, DomainValidationError, canonical_sha256
from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingCommit, BlockingDraft
from mode_p_vnext.domain.decisions import DirectorDecision, VisualCurvePoint
from mode_p_vnext.domain.facts import FactRegistry, FactSemantic, ScriptFact
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.time import (
    CanonicalTimeline,
    GenerationCapabilityProfile,
    TickMarker,
    TickRange,
)
from mode_p_vnext.domain.vec import (
    AudioEvent,
    ExecutionDesignDraft,
    GenerationUnit,
    PlacementPhase,
    ReferenceRequirement,
    ReferenceResponsibility,
    ShotBoundary,
    VisualBeat,
    VisualExecutionContract,
    VisualShot,
    VoiceRequirement,
)
from mode_p_vnext.services.blocking_assembler import assemble_blocking_commit
from mode_p_vnext.services.timeline_allocator import allocate_shot_timelines


_REFERENCE_SEMANTICS: dict[ReferenceResponsibility, frozenset[FactSemantic]] = {
    ReferenceResponsibility.CHARACTER_IDENTITY: frozenset({FactSemantic.CHARACTER}),
    ReferenceResponsibility.WARDROBE_CONTINUITY: frozenset({FactSemantic.WARDROBE}),
    ReferenceResponsibility.PROP_IDENTITY: frozenset({FactSemantic.PROP}),
    ReferenceResponsibility.SETTING_CONTINUITY: frozenset({FactSemantic.SETTING}),
    ReferenceResponsibility.FIRST_FRAME: frozenset(
        {
            FactSemantic.CHARACTER,
            FactSemantic.WARDROBE,
            FactSemantic.PROP,
            FactSemantic.SETTING,
            FactSemantic.ASSET,
        }
    ),
    ReferenceResponsibility.LAST_FRAME: frozenset(
        {
            FactSemantic.CHARACTER,
            FactSemantic.WARDROBE,
            FactSemantic.PROP,
            FactSemantic.SETTING,
            FactSemantic.ASSET,
        }
    ),
}


def _local_id(
    factory: IdFactory,
    *,
    episode_id: str,
    scene_id: str,
    stage: str,
    input_digest: str,
    ordinal: int,
) -> str:
    return factory.create(
        artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage=stage,
        input_digest=input_digest,
        ordinal=ordinal,
    )


def _require_text(value: str | None, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")
    return value


def _require_fact_scope(facts: FactRegistry, *, episode_id: str, scene_id: str) -> None:
    for fact in facts.facts:
        if (
            fact.qualifiers.episode_id != episode_id
            or fact.qualifiers.scene_id != scene_id
        ):
            raise DomainValidationError("every resolved fact must belong to the VEC episode and scene")


def _reconstruct_blocking_draft(commit: BlockingCommit) -> BlockingDraft:
    """Recover the exact creative B0 Draft represented by a canonical commit.

    ``BlockingCommit`` carries the complete creative beat content but no model
    authority.  Reconstructing its Draft lets the VEC boundary prove that the
    supplied commit is the deterministic output of the active local B0
    compiler, instead of trusting an opaque ID or an external envelope.
    """

    return BlockingDraft(
        beats=tuple(
            BlockingBeatDraft(
                ordinal=beat.source_ordinal,
                dramatic_action=beat.dramatic_action,
                character_states=beat.character_states,
                prop_states=beat.prop_states,
                gaze_relations=beat.gaze_relations,
                action_paths=beat.action_paths,
                continuity_effect=beat.continuity_effect,
            )
            for beat in commit.beats
        )
    )


def _require_current_blocking_authority(
    commit: BlockingCommit,
    *,
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    program_version: str,
) -> None:
    """Fail closed unless B0 is reproducible under the current local authority."""

    expected = assemble_blocking_commit(
        draft=_reconstruct_blocking_draft(commit),
        episode_id=episode_id,
        scene_id=scene_id,
        id_factory=id_factory,
        program_version=program_version,
    )
    if expected != commit:
        raise DomainValidationError(
            "blocking_commit is not rebuildable by the current local B0 compiler"
        )


def _resolve_reference_fact(
    facts: FactRegistry,
    *,
    fact_handle: str,
    responsibility: ReferenceResponsibility,
) -> ScriptFact:
    fact = facts.by_handle(fact_handle)
    if fact.semantic not in _REFERENCE_SEMANTICS[responsibility]:
        raise DomainValidationError(
            "typed reference responsibility is incompatible with the resolved fact semantic"
        )
    return fact


def _resolve_dialogue_fact(facts: FactRegistry, *, fact_handle: str) -> ScriptFact:
    fact = facts.by_handle(fact_handle)
    if fact.semantic is not FactSemantic.DIALOGUE:
        raise DomainValidationError("DialogueBindingIntent must resolve a dialogue fact")
    _require_text(fact.qualifiers.subject_label, "dialogue subject_label")
    _require_text(fact.qualifiers.spoken_text, "dialogue spoken_text")
    return fact


def _marker_for(phase: PlacementPhase, interval: TickRange) -> TickMarker:
    """Place dialogue only from the target VisualBeat's local tick interval."""

    duration = interval.duration_ticks
    offsets = {
        PlacementPhase.OPENING: 0,
        PlacementPhase.EARLY: duration // 4,
        PlacementPhase.MIDDLE: duration // 2,
        PlacementPhase.LATE: (duration * 3) // 4,
        PlacementPhase.CLOSING: duration - 1,
    }
    return TickMarker(interval.start_tick + offsets[phase])


def _partition_visual_beats(duration_ticks: int, beat_count: int) -> tuple[TickRange, ...]:
    if beat_count < 1 or beat_count > duration_ticks:
        raise DomainValidationError("VisualBeats must fit as non-empty local tick intervals")
    base, remainder = divmod(duration_ticks, beat_count)
    cursor = 0
    intervals: list[TickRange] = []
    for index in range(beat_count):
        size = base + (1 if index < remainder else 0)
        intervals.append(TickRange(cursor, cursor + size))
        cursor += size
    return tuple(intervals)


def _vec_output_digest(**fields: object) -> str:
    """Hash the complete final VEC projection excluding this digest itself.

    Excluding only ``canonical_output_sha256`` avoids a self-referential hash
    while preserving a reproducible digest of every other final contract field.
    """

    return canonical_sha256(fields)


def assemble_vec(
    *,
    draft: ExecutionDesignDraft,
    blocking_commit: BlockingCommit,
    facts: FactRegistry,
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    program_version: str,
    capability_profile: GenerationCapabilityProfile | None = None,
) -> VisualExecutionContract:
    """Create the sole local executable authority from approved typed inputs.

    No legacy compatibility surface is retained.  Callers must supply v3
    domain values; invalid scope, handle, semantic, or graph relationships fail
    before a VEC is emitted.
    """

    if not isinstance(draft, ExecutionDesignDraft):
        raise DomainValidationError("draft must be an ExecutionDesignDraft")
    if not isinstance(blocking_commit, BlockingCommit):
        raise DomainValidationError("blocking_commit must be a BlockingCommit")
    if not isinstance(facts, FactRegistry):
        raise DomainValidationError("facts must be a FactRegistry")
    if not isinstance(id_factory, IdFactory):
        raise DomainValidationError("id_factory must be an IdFactory")
    _require_text(episode_id, "episode_id")
    _require_text(scene_id, "scene_id")
    _require_text(program_version, "program_version")
    if id_factory.program_version != program_version:
        raise DomainValidationError("id_factory program_version must match the approved VEC program_version")
    if blocking_commit.scene_id != scene_id:
        raise DomainValidationError("blocking_commit scene_id must match the VEC scene")
    _require_current_blocking_authority(
        blocking_commit,
        episode_id=episode_id,
        scene_id=scene_id,
        id_factory=id_factory,
        program_version=program_version,
    )
    _require_fact_scope(facts, episode_id=episode_id, scene_id=scene_id)
    expected_transition_count = len(draft.shots) - 1
    if len(draft.transition_intents) != expected_transition_count:
        raise DomainValidationError(
            "ExecutionDesignDraft must declare exactly one transition intent per interior boundary"
        )

    profile = capability_profile or GenerationCapabilityProfile.sd20_default()
    if not isinstance(profile, GenerationCapabilityProfile):
        raise DomainValidationError("capability_profile must be canonical")

    input_digest = canonical_sha256(
        {
            "draft": draft,
            "blocking_commit": blocking_commit,
            "facts": facts,
            "episode_id": episode_id,
            "scene_id": scene_id,
            "program_version": program_version,
            "capability_profile": profile,
        }
    )
    execution_id = _local_id(
        id_factory,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="B1:execution-design",
        input_digest=input_digest,
        ordinal=0,
    )
    blocking_id = blocking_commit.commit_id
    contract_id = _local_id(
        id_factory,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="B1:vec",
        input_digest=input_digest,
        ordinal=0,
    )

    blocking_by_ordinal = {beat.source_ordinal: beat for beat in blocking_commit.beats}
    curve_points: list[VisualCurvePoint] = []
    for ordinal, point in enumerate(draft.curve_points, start=1):
        try:
            blocking_beat = blocking_by_ordinal[point.dramatic_beat_ordinal]
        except KeyError as exc:
            raise DomainValidationError("VisualCurvePointDraft references an unknown BlockingBeat") from exc
        curve_points.append(
            VisualCurvePoint(
                point_id=_local_id(
                    id_factory,
                    episode_id=episode_id,
                    scene_id=scene_id,
                    stage="B1:curve-point",
                    input_digest=input_digest,
                    ordinal=ordinal,
                ),
                source_curve_ordinal=ordinal,
                blocking_beat_id=blocking_beat.beat_id,
                intensity=point.intensity,
                explanation=point.explanation,
            )
        )

    decisions: list[DirectorDecision] = []
    for ordinal, decision in enumerate(draft.decisions, start=1):
        decisions.append(
            DirectorDecision(
                decision_id=_local_id(
                    id_factory,
                    episode_id=episode_id,
                    scene_id=scene_id,
                    stage="B1:decision",
                    input_digest=input_digest,
                    ordinal=ordinal,
                ),
                source_decision_ordinal=ordinal,
                scope=decision.scope,
                basis=decision.basis,
                locked_by=decision.locked_by,
                options=decision.options,
                selected_index=decision.selected_index,
                rationale=decision.rationale,
                tradeoff=decision.tradeoff,
            )
        )
    decision_ids = tuple(item.decision_id for item in decisions)

    shot_ids = tuple(
        _local_id(
            id_factory,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:shot",
            input_digest=input_digest,
            ordinal=shot.shot_ordinal,
        )
        for shot in draft.shots
    )
    unit_ids = tuple(
        _local_id(
            id_factory,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:generation-unit",
            input_digest=input_digest,
            ordinal=shot.shot_ordinal,
        )
        for shot in draft.shots
    )
    scene_timeline, unit_timelines = allocate_shot_timelines(
        scene_id=scene_id,
        generation_unit_ids=unit_ids,
        duration_intents=tuple(shot.duration_intent for shot in draft.shots),
        capability_profile=profile,
    )
    placement_by_unit = {
        placement.scope_id: placement
        for placement in scene_timeline.generation_unit_placements
    }
    generation_units = tuple(
        GenerationUnit(
            unit_id=unit_id,
            shot_id=shot_id,
            generation_mode=shot.generation_mode,
            timeline=unit_timeline,
            scene_placement=placement_by_unit[unit_id],
        )
        for shot_id, unit_id, shot, unit_timeline in zip(
            shot_ids, unit_ids, draft.shots, unit_timelines
        )
    )

    shots: list[VisualShot] = []
    audio_events: list[AudioEvent] = []
    voice_requirements: list[VoiceRequirement] = []
    reference_requirements: list[ReferenceRequirement] = []
    for shot_draft, shot_id, unit_id, unit_timeline in zip(
        draft.shots, shot_ids, unit_ids, unit_timelines
    ):
        try:
            blocking_beat = blocking_by_ordinal[shot_draft.blocking_beat_ordinal]
        except KeyError as exc:
            raise DomainValidationError("ShotDesignDraft references an unknown BlockingBeat") from exc

        intervals = _partition_visual_beats(
            unit_timeline.duration_ticks, len(shot_draft.visual_beats)
        )
        beat_ids = tuple(
            _local_id(
                id_factory,
                episode_id=episode_id,
                scene_id=scene_id,
                stage=f"B1:shot-{shot_draft.shot_ordinal}:visual-beat",
                input_digest=input_digest,
                ordinal=beat_draft.visual_beat_ordinal,
            )
            for beat_draft in shot_draft.visual_beats
        )
        state_ids = tuple(
            _local_id(
                id_factory,
                episode_id=episode_id,
                scene_id=scene_id,
                stage=f"B1:shot-{shot_draft.shot_ordinal}:state",
                input_digest=input_digest,
                ordinal=ordinal,
            )
            for ordinal in range(0, len(shot_draft.visual_beats) + 1)
        )
        reference_ids_by_beat: dict[str, list[str]] = {beat_id: [] for beat_id in beat_ids}
        audio_ids_by_beat: dict[str, list[str]] = {beat_id: [] for beat_id in beat_ids}
        shot_reference_ids: list[str] = []
        shot_audio_ids: list[str] = []

        for ordinal, intent in enumerate(shot_draft.reference_binding_intents, start=1):
            fact = _resolve_reference_fact(
                facts,
                fact_handle=intent.fact_handle,
                responsibility=intent.responsibility,
            )
            target_beat_id = (
                None
                if intent.visual_beat_ordinal is None
                else beat_ids[intent.visual_beat_ordinal - 1]
            )
            requirement_id = _local_id(
                id_factory,
                episode_id=episode_id,
                scene_id=scene_id,
                stage=f"B1:shot-{shot_draft.shot_ordinal}:reference",
                input_digest=input_digest,
                ordinal=ordinal,
            )
            reference_requirements.append(
                ReferenceRequirement(
                    requirement_id=requirement_id,
                    responsibility=intent.responsibility,
                    source_fact_id=fact.fact_id,
                    source_fact_handle=fact.fact_handle,
                    shot_id=shot_id,
                    visual_beat_id=target_beat_id,
                )
            )
            shot_reference_ids.append(requirement_id)
            if target_beat_id is not None:
                reference_ids_by_beat[target_beat_id].append(requirement_id)

        for ordinal, intent in enumerate(shot_draft.dialogue_binding_intents, start=1):
            fact = _resolve_dialogue_fact(facts, fact_handle=intent.fact_handle)
            target_beat_id = beat_ids[intent.visual_beat_ordinal - 1]
            target_interval = intervals[intent.visual_beat_ordinal - 1]
            event_id = _local_id(
                id_factory,
                episode_id=episode_id,
                scene_id=scene_id,
                stage=f"B1:shot-{shot_draft.shot_ordinal}:audio-event",
                input_digest=input_digest,
                ordinal=ordinal,
            )
            audio_events.append(
                AudioEvent(
                    event_id=event_id,
                    source_fact_id=fact.fact_id,
                    source_fact_handle=fact.fact_handle,
                    shot_id=shot_id,
                    visual_beat_id=target_beat_id,
                    marker=_marker_for(intent.placement_phase, target_interval),
                    placement_phase=intent.placement_phase,
                    character_label=_require_text(fact.qualifiers.subject_label, "dialogue subject_label"),
                    text=_require_text(fact.qualifiers.spoken_text, "dialogue spoken_text"),
                )
            )
            voice_requirements.append(
                VoiceRequirement(
                    requirement_id=_local_id(
                        id_factory,
                        episode_id=episode_id,
                        scene_id=scene_id,
                        stage=f"B1:shot-{shot_draft.shot_ordinal}:voice-requirement",
                        input_digest=input_digest,
                        ordinal=ordinal,
                    ),
                    audio_event_id=event_id,
                    character_label=_require_text(fact.qualifiers.subject_label, "dialogue subject_label"),
                    shot_id=shot_id,
                    visual_beat_id=target_beat_id,
                )
            )
            shot_audio_ids.append(event_id)
            audio_ids_by_beat[target_beat_id].append(event_id)

        visual_beats = tuple(
            VisualBeat(
                beat_id=beat_id,
                shot_id=shot_id,
                source_visual_beat_ordinal=beat_draft.visual_beat_ordinal,
                phase=beat_draft.phase,
                interval=interval,
                subject_state=beat_draft.subject_state,
                attention=beat_draft.attention,
                storyboard_role=beat_draft.storyboard_role,
                start_state_id=state_ids[index],
                end_state_id=state_ids[index + 1],
                decision_ids=decision_ids,
                reference_requirement_ids=tuple(reference_ids_by_beat[beat_id]),
                audio_event_ids=tuple(audio_ids_by_beat[beat_id]),
            )
            for index, (beat_draft, beat_id, interval) in enumerate(
                zip(shot_draft.visual_beats, beat_ids, intervals)
            )
        )
        shots.append(
            VisualShot(
                shot_id=shot_id,
                generation_unit_id=unit_id,
                source_shot_ordinal=shot_draft.shot_ordinal,
                blocking_beat_id=blocking_beat.beat_id,
                generation_mode=shot_draft.generation_mode,
                interval=unit_timeline.interval,
                composition=shot_draft.composition,
                camera=shot_draft.camera,
                lighting=shot_draft.lighting,
                performance=shot_draft.performance,
                creative_notes=shot_draft.creative_notes,
                visual_beats=visual_beats,
                decision_ids=decision_ids,
                reference_requirement_ids=tuple(shot_reference_ids),
                audio_event_ids=tuple(shot_audio_ids),
            )
        )

    boundaries: list[ShotBoundary] = []
    for ordinal in range(0, len(shots) + 1):
        if ordinal == 0:
            from_shot_id = None
            to_shot_id = shots[0].shot_id
            scene_tick = generation_units[0].scene_placement.interval.start_tick
            before_state_id = blocking_commit.entry_state_id
            after_state_id = shots[0].visual_beats[0].start_state_id
            transition_intent = "scene entrance"
        elif ordinal == len(shots):
            from_shot_id = shots[-1].shot_id
            to_shot_id = None
            scene_tick = generation_units[-1].scene_placement.interval.end_tick
            before_state_id = shots[-1].visual_beats[-1].end_state_id
            after_state_id = blocking_commit.exit_state_id
            transition_intent = "scene exit"
        else:
            from_shot_id = shots[ordinal - 1].shot_id
            to_shot_id = shots[ordinal].shot_id
            scene_tick = generation_units[ordinal - 1].scene_placement.interval.end_tick
            before_state_id = shots[ordinal - 1].visual_beats[-1].end_state_id
            after_state_id = shots[ordinal].visual_beats[0].start_state_id
            transition_intent = draft.transition_intents[ordinal - 1]
        boundaries.append(
            ShotBoundary(
                boundary_id=_local_id(
                    id_factory,
                    episode_id=episode_id,
                    scene_id=scene_id,
                    stage="B1:boundary",
                    input_digest=input_digest,
                    ordinal=ordinal,
                ),
                boundary_ordinal=ordinal,
                scene_tick=scene_tick,
                from_shot_id=from_shot_id,
                to_shot_id=to_shot_id,
                before_state_id=before_state_id,
                after_state_id=after_state_id,
                transition_intent=transition_intent,
                decision_ids=decision_ids,
            )
        )

    final_fields = {
        "contract_id": contract_id,
        "episode_id": episode_id,
        "scene_id": scene_id,
        "execution_design_artifact_id": execution_id,
        "blocking_commit_artifact_id": blocking_id,
        "source_fact_ids": tuple(fact.fact_id for fact in facts.facts),
        "approved_fact_handles": tuple(fact.fact_handle for fact in facts.facts),
        "timeline": CanonicalTimeline(),
        "scene_timeline": scene_timeline,
        "capability_profile": profile,
        "curve_points": tuple(curve_points),
        "decisions": tuple(decisions),
        "generation_units": generation_units,
        "shots": tuple(shots),
        "boundaries": tuple(boundaries),
        "audio_events": tuple(audio_events),
        "voice_requirements": tuple(voice_requirements),
        "reference_requirements": tuple(reference_requirements),
        "handoff_intent": draft.handoff_intent,
        "canonical_input_sha256": input_digest,
    }
    return VisualExecutionContract(
        **final_fields,
        canonical_output_sha256=_vec_output_digest(**final_fields),
    )
