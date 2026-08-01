"""Deterministic local assembly of VisualExecutionContract from model drafts.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §5.3–§5.5 / §14 A5.

The model produces only an ExecutionDesignDraft (B1).  This assembler performs
every machine step — IDs, hashes, ticks, boundaries, reference derivation,
audio synthesis, safety constants, and invariant validation — so the final
VisualExecutionContract carries zero model-generated machine fields.
"""

from __future__ import annotations

from mode_p_vnext.domain.artifact import (
    ArtifactKind,
    DomainValidationError,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingCommit
from mode_p_vnext.domain.decisions import (
    DecisionDraft,
    DirectorDecision,
    VisualCurvePoint,
    VisualCurvePointDraft,
)
from mode_p_vnext.domain.facts import FactRegistry, ScriptFact
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.time import CanonicalTimeline, TickRange
from mode_p_vnext.domain.vec import (
    AudioEvent,
    ExecutionDesignDraft,
    GenerationSegment,
    ReferenceRequirement,
    ShotBoundary,
    ShotDesignDraft,
    StoryboardRole,
    VisualBeat,
    VisualBeatDraft,
    VisualBeatPhase,
    VisualExecutionContract,
    VisualShot,
    VoiceRequirement,
)
from mode_p_vnext.services.timeline_allocator import allocate_shot_ticks


# ---------------------------------------------------------------------------
# Fact categorisation (deterministic, convention-based)
# ---------------------------------------------------------------------------

def _fact_scope_kind(fact: ScriptFact) -> str | None:
    """Return 'character' | 'prop' | 'costume' | 'scene' | None.

    Uses the fact_id prefix convention:
        char_*     → character
        prop_*     → prop
        costume_*  → costume
        scene_*    → scene / setting
    """
    prefixes = {
        "char_": "character",
        "prop_": "prop",
        "costume_": "costume",
        "scene_": "scene",
    }
    for prefix, kind in prefixes.items():
        if fact.fact_id.startswith(prefix):
            return kind
    return None


def _is_dialogue_fact(fact: ScriptFact) -> bool:
    """Return True when the fact carries script dialogue."""
    return fact.fact_id.startswith("dialogue_")


def _speaker_from_dialogue(fact: ScriptFact) -> str:
    """Extract a speaker label from a dialogue fact's statement.

    Expects statements like 'CHAR_NAME: ...' or '角色名：...'.
    """
    statement = fact.statement
    for sep in (":", "：", "—"):
        if sep in statement:
            return statement.split(sep, 1)[0].strip()
    return "unknown"


def _dialogue_text(fact: ScriptFact) -> str:
    """Extract the spoken text from a dialogue fact's statement."""
    statement = fact.statement
    for sep in (":", "：", "—"):
        if sep in statement:
            return statement.split(sep, 1)[1].strip()
    return statement


# ---------------------------------------------------------------------------
# VEC assembly
# ---------------------------------------------------------------------------

def assemble_vec(
    *,
    draft: ExecutionDesignDraft,
    blocking_commit: BlockingCommit,
    facts: FactRegistry,
    episode_id: str,
    scene_id: str,
    id_factory: IdFactory,
    program_version: str,
    schema_version: str = "2.1",
    execution_design_artifact_id: str = "",
    blocking_commit_artifact_id: str = "",
) -> VisualExecutionContract:
    """Produce the sole machine-readable creative authority for both projections.

    The model's ExecutionDesignDraft supplies creative choices only.
    Everything else — IDs, ticks, boundaries, references, audio, safety
    constants — is assembled deterministically here so that identical
    inputs always produce an identical VisualExecutionContract.
    """

    # -- 0.  stable input digest for rebuild determinism ----------------------
    input_digest = canonical_sha256(
        {
            "draft_payload": draft,
            "blocking_commit_payload": blocking_commit,
            "facts_payload": facts,
            "episode_id": episode_id,
            "scene_id": scene_id,
            "program_version": program_version,
            "schema_version": schema_version,
        }
    )

    # -- 1.  contract and dependency artifact identities ----------------------
    contract_id = id_factory.create(
        artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="B1:vec",
        input_digest=input_digest,
        ordinal=0,
    )

    if not execution_design_artifact_id:
        execution_design_artifact_id = id_factory.create(
            artifact_kind=ArtifactKind.EXECUTION_DESIGN_DRAFT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1",
            input_digest=input_digest,
            ordinal=0,
        )

    if not blocking_commit_artifact_id:
        blocking_commit_artifact_id = id_factory.create(
            artifact_kind=ArtifactKind.BLOCKING_COMMIT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B0",
            input_digest=canonical_sha256(blocking_commit),
            ordinal=0,
        )

    # -- 2.  resolve blocking beat ordinals → IDs -----------------------------
    beat_by_ordinal: dict[int, str] = {
        beat.source_ordinal: beat.beat_id for beat in blocking_commit.beats
    }

    def _resolve_beat(ordinal: int) -> str:
        if ordinal not in beat_by_ordinal:
            raise DomainValidationError(
                f"B1 shot references blocking ordinal {ordinal} "
                f"which does not exist in the BlockingCommit"
            )
        return beat_by_ordinal[ordinal]

    # -- 3.  curve points -----------------------------------------------------
    curve_points = _assemble_curve_points(
        draft.curve_points,
        beat_by_ordinal,
        id_factory,
        episode_id,
        scene_id,
        input_digest,
    )

    # -- 4.  decisions --------------------------------------------------------
    decisions = _assemble_decisions(
        draft.decisions,
        id_factory,
        episode_id,
        scene_id,
        input_digest,
    )

    # -- 5.  timeline allocation ----------------------------------------------
    weights = tuple(shot.duration_weight for shot in draft.shots)
    segment_timeline, shot_ranges = allocate_shot_ticks(weights)

    # -- 6.  one generation segment per scene ---------------------------------
    segment_id = id_factory.create(
        artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="B1:segment",
        input_digest=input_digest,
        ordinal=1,
    )

    # -- 7.  visual shots -----------------------------------------------------
    shots, shot_ids = _assemble_shots(
        draft.shots,
        shot_ranges,
        beat_by_ordinal,
        segment_id,
        decisions,
        id_factory,
        episode_id,
        scene_id,
        input_digest,
    )

    segment = GenerationSegment(
        segment_id=segment_id,
        timeline=segment_timeline,
        shot_ids=shot_ids,
    )

    # -- 8.  shot boundaries (N shots → N-1 boundaries) -----------------------
    boundaries = _assemble_boundaries(
        draft.transition_intents,
        shots,
        segment_id,
        decisions,
        id_factory,
        episode_id,
        scene_id,
        input_digest,
    )

    # -- 9.  reference requirements -------------------------------------------
    reference_requirements = _derive_references(
        facts,
        id_factory,
        episode_id,
        scene_id,
        input_digest,
    )

    # -- 10.  audio events + voice requirements -------------------------------
    audio_events, voice_requirements = _derive_audio(
        facts,
        segment_id,
        id_factory,
        episode_id,
        scene_id,
        input_digest,
    )

    # -- 11.  handoff ---------------------------------------------------------
    handoff_intent = draft.handoff_intent

    # -- 12.  source fact ids -------------------------------------------------
    source_fact_ids = tuple(fact.fact_id for fact in facts.facts)

    # -- 13.  publish (domain __post_init__ runs full invariant validation) ---
    return VisualExecutionContract(
        contract_id=contract_id,
        scene_id=scene_id,
        execution_design_artifact_id=execution_design_artifact_id,
        blocking_commit_artifact_id=blocking_commit_artifact_id,
        source_fact_ids=source_fact_ids,
        timeline=CanonicalTimeline(),
        curve_points=curve_points,
        decisions=decisions,
        segments=(segment,),
        shots=shots,
        boundaries=boundaries,
        audio_events=audio_events,
        voice_requirements=voice_requirements,
        reference_requirements=reference_requirements,
        handoff_intent=handoff_intent,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assemble_curve_points(
    drafts: tuple[VisualCurvePointDraft, ...],
    beat_by_ordinal: dict[int, str],
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    input_digest: str,
) -> tuple[VisualCurvePoint, ...]:
    points: list[VisualCurvePoint] = []
    for i, d in enumerate(drafts, start=1):
        blocking_beat_id = beat_by_ordinal.get(d.dramatic_beat_ordinal)
        if blocking_beat_id is None:
            raise DomainValidationError(
                f"curve point {i} references blocking ordinal "
                f"{d.dramatic_beat_ordinal} which does not exist"
            )
        point_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:curve",
            input_digest=input_digest,
            ordinal=i,
        )
        points.append(
            VisualCurvePoint(
                point_id=point_id,
                source_curve_ordinal=i,
                blocking_beat_id=blocking_beat_id,
                intensity=d.intensity,
                explanation=d.explanation,
            )
        )
    return tuple(points)


def _assemble_decisions(
    drafts: tuple[DecisionDraft, ...],
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    input_digest: str,
) -> tuple[DirectorDecision, ...]:
    decisions: list[DirectorDecision] = []
    for i, d in enumerate(drafts, start=1):
        decision_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:decision",
            input_digest=input_digest,
            ordinal=i,
        )
        decisions.append(
            DirectorDecision(
                decision_id=decision_id,
                source_decision_ordinal=i,
                scope=d.scope,
                basis=d.basis,
                locked_by=d.locked_by,
                options=d.options,
                selected_index=d.selected_index,
                rationale=d.rationale,
                tradeoff=d.tradeoff,
            )
        )
    return tuple(decisions)


def _assemble_shots(
    shot_drafts: tuple[ShotDesignDraft, ...],
    shot_ranges: tuple[TickRange, ...],
    beat_by_ordinal: dict[int, str],
    segment_id: str,
    decisions: tuple[DirectorDecision, ...],
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    input_digest: str,
) -> tuple[tuple[VisualShot, ...], tuple[str, ...]]:
    decision_ids = tuple(d.decision_id for d in decisions)

    shots: list[VisualShot] = []
    shot_ids: list[str] = []

    for i, (draft, tick_range) in enumerate(zip(shot_drafts, shot_ranges), start=1):
        shot_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:shot",
            input_digest=input_digest,
            ordinal=i,
        )

        blocking_beat_id = beat_by_ordinal.get(draft.blocking_beat_ordinal)
        if blocking_beat_id is None:
            raise DomainValidationError(
                f"shot {i} references blocking ordinal "
                f"{draft.blocking_beat_ordinal} which does not exist"
            )

        visual_beats = _assemble_visual_beats(
            draft.visual_beats,
            shot_id,
            tick_range,
            id_factory,
            episode_id,
            scene_id,
            input_digest,
            i,
        )

        shots.append(
            VisualShot(
                shot_id=shot_id,
                segment_id=segment_id,
                source_shot_ordinal=i,
                blocking_beat_id=blocking_beat_id,
                interval=tick_range,
                dramatic_function=draft.dramatic_function,
                attention_target=draft.attention_target,
                information_action=draft.information_action,
                framing_intent=draft.framing_intent,
                camera_pose=draft.camera_pose,
                camera_motion=draft.camera_motion,
                composition=draft.composition,
                lighting=draft.lighting,
                performance=draft.performance,
                visual_beats=visual_beats,
                decision_ids=decision_ids,
                reference_requirement_ids=(),
                audio_event_ids=(),
            )
        )
        shot_ids.append(shot_id)

    return tuple(shots), tuple(shot_ids)


def _assemble_visual_beats(
    beat_drafts: tuple[VisualBeatDraft, ...],
    shot_id: str,
    shot_range: TickRange,
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    input_digest: str,
    shot_ordinal: int,
) -> tuple[VisualBeat, ...]:
    total_duration = shot_range.duration_ticks
    beat_count = len(beat_drafts)

    beats: list[VisualBeat] = []
    cursor = shot_range.start_tick

    for j, draft in enumerate(beat_drafts):
        # Divide remaining ticks equally among remaining beats.
        remaining_beats = beat_count - j
        beat_duration = max(1, (shot_range.end_tick - cursor) // remaining_beats)
        beat_end = cursor + beat_duration
        if j == beat_count - 1:
            # Last beat consumes the rest.
            beat_end = shot_range.end_tick

        beat_interval = TickRange(start_tick=cursor, end_tick=beat_end)

        beat_ordinal = shot_ordinal * 100 + j
        beat_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:visual_beat",
            input_digest=input_digest,
            ordinal=beat_ordinal,
        )

        start_state_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:beat_state",
            input_digest=input_digest,
            ordinal=beat_ordinal * 2,
        )
        end_state_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:beat_state",
            input_digest=input_digest,
            ordinal=beat_ordinal * 2 + 1,
        )

        beats.append(
            VisualBeat(
                beat_id=beat_id,
                shot_id=shot_id,
                phase=draft.phase,
                interval=beat_interval,
                subject_state=draft.subject_state,
                attention=draft.attention,
                storyboard_role=draft.storyboard_role,
                start_state_id=start_state_id,
                end_state_id=end_state_id,
                decision_ids=(),
            )
        )
        cursor = beat_end

    # Chain state adjacency so domain validation passes.
    chained: list[VisualBeat] = []
    for k, beat in enumerate(beats):
        if k == 0:
            chained.append(beat)
        else:
            prev_end = chained[k - 1].end_state_id
            chained.append(
                VisualBeat(
                    beat_id=beat.beat_id,
                    shot_id=beat.shot_id,
                    phase=beat.phase,
                    interval=beat.interval,
                    subject_state=beat.subject_state,
                    attention=beat.attention,
                    storyboard_role=beat.storyboard_role,
                    start_state_id=prev_end,
                    end_state_id=beat.end_state_id,
                    decision_ids=beat.decision_ids,
                )
            )

    return tuple(chained)


def _assemble_boundaries(
    transition_intents: tuple[str, ...],
    shots: tuple[VisualShot, ...],
    segment_id: str,
    decisions: tuple[DirectorDecision, ...],
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    input_digest: str,
) -> tuple[ShotBoundary, ...]:
    if len(shots) < 2:
        return ()

    decision_ids = tuple(d.decision_id for d in decisions)
    boundaries: list[ShotBoundary] = []

    for i, (left, right) in enumerate(zip(shots, shots[1:]), start=1):
        boundary_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:boundary",
            input_digest=input_digest,
            ordinal=i,
        )
        intent = (
            transition_intents[i - 1]
            if i - 1 < len(transition_intents)
            else "cut"
        )
        boundaries.append(
            ShotBoundary(
                boundary_id=boundary_id,
                segment_id=segment_id,
                from_shot_id=left.shot_id,
                to_shot_id=right.shot_id,
                transition_intent=intent,
                decision_ids=decision_ids,
            )
        )

    return tuple(boundaries)


def _derive_references(
    facts: FactRegistry,
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    input_digest: str,
) -> tuple[ReferenceRequirement, ...]:
    """Derive ReferenceRequirements from character/prop/costume/scene facts."""
    refs: list[ReferenceRequirement] = []
    ordinal = 0

    for fact in facts.facts:
        scope_kind = _fact_scope_kind(fact)
        if scope_kind is None:
            continue
        ordinal += 1
        req_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:reference",
            input_digest=input_digest,
            ordinal=ordinal,
        )
        refs.append(
            ReferenceRequirement(
                requirement_id=req_id,
                role=scope_kind,
                scope_kind=scope_kind,
                scope_id=fact.fact_id,
                source_fact_ids=(fact.fact_id,),
            )
        )

    return tuple(refs)


def _derive_audio(
    facts: FactRegistry,
    segment_id: str,
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    input_digest: str,
) -> tuple[tuple[AudioEvent, ...], tuple[VoiceRequirement, ...]]:
    """Generate AudioEvents from dialogue facts, each with a VoiceRequirement."""
    audio_events: list[AudioEvent] = []
    voice_reqs: list[VoiceRequirement] = []
    ordinal = 0

    for fact in facts.facts:
        if not _is_dialogue_fact(fact):
            continue
        ordinal += 1
        character_id = _speaker_from_dialogue(fact)
        text = _dialogue_text(fact)

        event_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:audio_event",
            input_digest=input_digest,
            ordinal=ordinal,
        )
        # Dialogue events span a nominal range; the exact placement is
        # refined by the projection layer.
        audio_events.append(
            AudioEvent(
                event_id=event_id,
                segment_id=segment_id,
                interval=TickRange(start_tick=0, end_tick=1),
                source_fact_id=fact.fact_id,
                character_id=character_id,
                text=text,
            )
        )

        voice_id = id_factory.create(
            artifact_kind=ArtifactKind.VISUAL_EXECUTION_CONTRACT,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="B1:voice",
            input_digest=input_digest,
            ordinal=ordinal,
        )
        voice_reqs.append(
            VoiceRequirement(
                requirement_id=voice_id,
                audio_event_id=event_id,
                character_id=character_id,
            )
        )

    return tuple(audio_events), tuple(voice_reqs)
