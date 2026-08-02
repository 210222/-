"""A5 acceptance tests for the frozen v3.0 VEC assembly invariant set."""

from __future__ import annotations

from dataclasses import replace
import inspect

import pytest

from mode_p_vnext.domain.artifact import DomainValidationError, SourceRef
from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingDraft
from mode_p_vnext.domain.decisions import (
    DecisionBasis,
    DecisionDraft,
    VisualCurvePointDraft,
)
from mode_p_vnext.domain.facts import (
    FactConfidence,
    FactKind,
    FactQualifiers,
    FactRegistry,
    FactSemantic,
    ScriptFact,
    SourceSpan,
)
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.time import DurationIntent, GenerationCapabilityProfile
from mode_p_vnext.domain.vec import (
    DialogueBindingIntent,
    ExecutionDesignDraft,
    GenerationMode,
    PlacementPhase,
    ReferenceBindingIntent,
    ReferenceResponsibility,
    ShotDesignDraft,
    StoryboardRole,
    VisualBeatDraft,
    VisualBeatPhase,
)
from mode_p_vnext.services import vec_assembler
from mode_p_vnext.services.blocking_assembler import assemble_blocking_commit
from mode_p_vnext.services.timeline_allocator import allocate_shot_timelines
from mode_p_vnext.services.vec_assembler import assemble_vec


PROGRAM_VERSION = "mode-p-vnext-a5-test"
EPISODE_ID = "EP35"
SCENE_ID = "EP35-S2"
SOURCE_REF = SourceRef(source_id="a5-fixture", digest="f" * 64)


def _opaque_id(character: str) -> str:
    return f"id:{character * 64}"


def _opaque_handle(character: str) -> str:
    return f"fh:{character * 64}"


def _fact(
    *,
    ordinal: int,
    character: str,
    semantic: FactSemantic,
    span_start: int,
    subject_label: str | None = None,
    spoken_text: str | None = None,
) -> ScriptFact:
    return ScriptFact(
        fact_id=_opaque_id(character),
        fact_handle=_opaque_handle(character),
        kind=FactKind.SCRIPT,
        semantic=semantic,
        statement=f"fixture-{semantic.value}-{ordinal}",
        confidence=FactConfidence.EXPLICIT,
        qualifiers=FactQualifiers(
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            subject_label=subject_label,
            spoken_text=spoken_text,
        ),
        provenance=(
            SourceSpan(
                source_ref=SOURCE_REF,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                source_start=span_start,
                source_end=span_start + 1,
            ),
        ),
        ordinal=ordinal,
    )


def make_facts(*, dialogue_span_start: int = 30) -> FactRegistry:
    return FactRegistry(
        source_ref=SOURCE_REF,
        facts=(
            _fact(
                ordinal=1,
                character="a",
                semantic=FactSemantic.CHARACTER,
                span_start=10,
                subject_label="Mira",
            ),
            _fact(
                ordinal=2,
                character="b",
                semantic=FactSemantic.PROP,
                span_start=20,
                subject_label="service pistol",
            ),
            _fact(
                ordinal=3,
                character="c",
                semantic=FactSemantic.DIALOGUE,
                span_start=dialogue_span_start,
                subject_label="Mira",
                spoken_text="Don't move.",
            ),
            _fact(
                ordinal=4,
                character="d",
                semantic=FactSemantic.SETTING,
                span_start=40,
                subject_label="range",
            ),
        ),
    )


def make_blocking_draft() -> BlockingDraft:
    return BlockingDraft(
        beats=(
            BlockingBeatDraft(
                ordinal=1,
                dramatic_action="Mira enters the quiet range.",
                character_states=({"character": "Mira", "posture": "guarded"},),
                prop_states=(),
                gaze_relations=(),
                action_paths=("enter",),
                continuity_effect="The range is established.",
            ),
            BlockingBeatDraft(
                ordinal=2,
                dramatic_action="Mira confronts the pistol.",
                character_states=({"character": "Mira", "posture": "ready"},),
                prop_states=({"prop": "pistol", "state": "visible"},),
                gaze_relations=("Mira -> pistol",),
                action_paths=("raise focus",),
                continuity_effect="The threat escalates.",
            ),
        )
    )


def make_draft(*, include_bindings: bool = True) -> ExecutionDesignDraft:
    references_one = (
        ReferenceBindingIntent(
            shot_ordinal=1,
            visual_beat_ordinal=None,
            fact_handle=_opaque_handle("a"),
            responsibility=ReferenceResponsibility.CHARACTER_IDENTITY,
        ),
    ) if include_bindings else ()
    references_two = (
        ReferenceBindingIntent(
            shot_ordinal=2,
            visual_beat_ordinal=1,
            fact_handle=_opaque_handle("b"),
            responsibility=ReferenceResponsibility.PROP_IDENTITY,
        ),
    ) if include_bindings else ()
    dialogue_two = (
        DialogueBindingIntent(
            shot_ordinal=2,
            visual_beat_ordinal=2,
            fact_handle=_opaque_handle("c"),
            placement_phase=PlacementPhase.MIDDLE,
        ),
    ) if include_bindings else ()
    return ExecutionDesignDraft(
        curve_points=(
            VisualCurvePointDraft(1, 60, "arrival tension"),
            VisualCurvePointDraft(2, 85, "threat escalation"),
        ),
        decisions=(
            DecisionDraft(
                scope="coverage",
                basis=DecisionBasis.CHOICE,
                locked_by=(),
                options=("wide", "close"),
                selected_index=1,
                rationale="preserve the reveal",
                tradeoff="less environment detail",
            ),
        ),
        shots=(
            ShotDesignDraft(
                shot_ordinal=1,
                blocking_beat_ordinal=1,
                duration_intent=DurationIntent.STANDARD,
                generation_mode=GenerationMode.TEXT_ONLY,
                composition="wide entrance",
                camera="slow push",
                lighting="cold practicals",
                performance="guarded scan",
                visual_beats=(
                    VisualBeatDraft(1, VisualBeatPhase.ENTRY, "at door", "room", StoryboardRole.REQUIRED),
                    VisualBeatDraft(2, VisualBeatPhase.ACTION, "steps in", "Mira", StoryboardRole.OPTIONAL),
                ),
                reference_binding_intents=references_one,
                dialogue_binding_intents=(),
                creative_notes="hold the silence",
            ),
            ShotDesignDraft(
                shot_ordinal=2,
                blocking_beat_ordinal=2,
                duration_intent=DurationIntent.EXTENDED,
                generation_mode=GenerationMode.OMNI_REFERENCE,
                composition="waist-up confrontation",
                camera="controlled settle",
                lighting="hard side key",
                performance="breath held",
                visual_beats=(
                    VisualBeatDraft(1, VisualBeatPhase.ACTION, "pistol revealed", "pistol", StoryboardRole.REQUIRED),
                    VisualBeatDraft(2, VisualBeatPhase.REACTION, "eyes lock", "Mira", StoryboardRole.REQUIRED),
                ),
                reference_binding_intents=references_two,
                dialogue_binding_intents=dialogue_two,
                creative_notes="do not rush the line",
            ),
        ),
        transition_intents=("hard cut",),
        handoff_intent="leave on the confrontation",
    )


@pytest.fixture
def id_factory() -> IdFactory:
    return IdFactory(program_version=PROGRAM_VERSION)


@pytest.fixture
def blocking_commit(id_factory: IdFactory):
    return assemble_blocking_commit(
        draft=make_blocking_draft(),
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


def build_vec(id_factory: IdFactory, blocking_commit, *, facts: FactRegistry | None = None, draft: ExecutionDesignDraft | None = None):
    return assemble_vec(
        draft=draft or make_draft(),
        blocking_commit=blocking_commit,
        facts=facts or make_facts(),
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
    )


def test_duration_intents_map_to_local_generation_units_not_a_scene_cap() -> None:
    profile = GenerationCapabilityProfile.sd20_default()
    scene_timeline, unit_timelines = allocate_shot_timelines(
        scene_id=SCENE_ID,
        generation_unit_ids=("id:" + "1" * 64, "id:" + "2" * 64),
        duration_intents=(DurationIntent.EXTENDED, DurationIntent.EXTENDED),
        capability_profile=profile,
    )

    assert all(timeline.duration_ticks == 312_000 for timeline in unit_timelines)
    assert all(timeline.duration_ticks <= profile.max_generation_ticks for timeline in unit_timelines)
    assert all(timeline.interval.start_tick == 0 for timeline in unit_timelines)
    assert scene_timeline.interval.duration_ticks == 624_000
    assert scene_timeline.interval.duration_ticks > profile.max_generation_ticks
    placements = scene_timeline.generation_unit_placements
    assert placements[0].interval.end_tick == placements[1].interval.start_tick


def test_blocking_and_vec_are_deterministic_local_authority(id_factory, blocking_commit) -> None:
    first = build_vec(id_factory, blocking_commit)
    second = build_vec(id_factory, blocking_commit)

    assert first == second
    assert first.contract_id.startswith("id:")
    assert first.execution_design_artifact_id.startswith("id:")
    assert first.blocking_commit_artifact_id == blocking_commit.commit_id
    assert first.canonical_input_sha256 != first.canonical_output_sha256
    final_fields = {
        name: getattr(first, name)
        for name in first.__dataclass_fields__
        if name not in {"ARTIFACT_KIND", "canonical_output_sha256"}
    }
    assert first.canonical_output_sha256 == vec_assembler._vec_output_digest(**final_fields)
    assert all(unit.unit_id.startswith("id:") for unit in first.generation_units)
    assert all(shot.shot_id.startswith("id:") for shot in first.shots)
    assert len(first.generation_units) == len(first.shots) == 2
    assert all(unit.timeline.interval == shot.interval for unit, shot in zip(first.generation_units, first.shots))


def test_n_plus_one_boundaries_use_placement_cut_points_and_state_chain(id_factory, blocking_commit) -> None:
    vec = build_vec(id_factory, blocking_commit)

    assert len(vec.boundaries) == len(vec.shots) + 1
    assert [boundary.boundary_ordinal for boundary in vec.boundaries] == [0, 1, 2]
    assert vec.boundaries[0].before_state_id == blocking_commit.entry_state_id
    assert vec.boundaries[-1].after_state_id == blocking_commit.exit_state_id
    assert vec.boundaries[1].scene_tick == vec.generation_units[0].scene_placement.interval.end_tick
    assert vec.boundaries[1].scene_tick == vec.generation_units[1].scene_placement.interval.start_tick
    assert vec.boundaries[1].before_state_id == vec.shots[0].visual_beats[-1].end_state_id
    assert vec.boundaries[1].after_state_id == vec.shots[1].visual_beats[0].start_state_id


def test_explicit_visual_beats_cover_each_local_shot_timeline(id_factory, blocking_commit) -> None:
    vec = build_vec(id_factory, blocking_commit)

    for shot in vec.shots:
        assert shot.visual_beats[0].interval.start_tick == 0
        assert shot.visual_beats[-1].interval.end_tick == shot.interval.end_tick
        assert all(
            left.interval.end_tick == right.interval.start_tick
            and left.end_state_id == right.start_state_id
            for left, right in zip(shot.visual_beats, shot.visual_beats[1:])
        )


def test_typed_reference_and_dialogue_bindings_are_exact_and_bidirectional(id_factory, blocking_commit) -> None:
    vec = build_vec(id_factory, blocking_commit)

    assert len(vec.reference_requirements) == 2
    assert len(vec.audio_events) == len(vec.voice_requirements) == 1
    character_reference, prop_reference = vec.reference_requirements
    assert character_reference.source_fact_handle == _opaque_handle("a")
    assert character_reference.visual_beat_id is None
    assert prop_reference.source_fact_handle == _opaque_handle("b")
    assert prop_reference.visual_beat_id == vec.shots[1].visual_beats[0].beat_id
    event = vec.audio_events[0]
    dialogue_beat = vec.shots[1].visual_beats[1]
    assert event.source_fact_handle == _opaque_handle("c")
    assert event.shot_id == vec.shots[1].shot_id
    assert event.visual_beat_id == dialogue_beat.beat_id
    assert dialogue_beat.interval.contains(event.marker.tick)
    assert event.marker.tick == dialogue_beat.interval.start_tick + dialogue_beat.interval.duration_ticks // 2
    assert event.event_id in vec.shots[1].audio_event_ids
    assert event.event_id in dialogue_beat.audio_event_ids
    assert prop_reference.requirement_id in dialogue_beat.reference_requirement_ids or prop_reference.requirement_id in vec.shots[1].visual_beats[0].reference_requirement_ids
    assert vec.voice_requirements[0].audio_event_id == event.event_id


def test_no_automatic_fact_binding_and_no_free_text_binding_surface(id_factory, blocking_commit) -> None:
    vec = build_vec(id_factory, blocking_commit, draft=make_draft(include_bindings=False))

    assert vec.reference_requirements == ()
    assert vec.audio_events == ()
    assert vec.voice_requirements == ()
    fields = set(ShotDesignDraft.__dataclass_fields__)
    assert "reference_binding_intents" in fields
    assert "dialogue_binding_intents" in fields
    assert "reference_intents" not in fields
    assert "audio_intents" not in fields


@pytest.mark.parametrize(
    "intent",
    (
        ReferenceBindingIntent(
            shot_ordinal=1,
            visual_beat_ordinal=1,
            fact_handle=_opaque_handle("b"),
            responsibility=ReferenceResponsibility.CHARACTER_IDENTITY,
        ),
        ReferenceBindingIntent(
            shot_ordinal=1,
            visual_beat_ordinal=1,
            fact_handle=_opaque_handle("e"),
            responsibility=ReferenceResponsibility.CHARACTER_IDENTITY,
        ),
    ),
)
def test_reference_semantic_mismatch_or_unknown_handle_fails_closed(id_factory, blocking_commit, intent) -> None:
    draft = make_draft()
    first = replace(draft.shots[0], reference_binding_intents=(intent,))
    bad_draft = replace(draft, shots=(first, draft.shots[1]))

    with pytest.raises(DomainValidationError):
        build_vec(id_factory, blocking_commit, draft=bad_draft)


def test_dialogue_marker_is_independent_of_provenance_positions(id_factory, blocking_commit) -> None:
    early_provenance = build_vec(id_factory, blocking_commit, facts=make_facts(dialogue_span_start=30))
    late_provenance = build_vec(id_factory, blocking_commit, facts=make_facts(dialogue_span_start=90_000))

    assert early_provenance.audio_events[0].marker == late_provenance.audio_events[0].marker
    assert early_provenance.audio_events[0].marker.tick == (
        early_provenance.shots[1].visual_beats[1].interval.start_tick
        + early_provenance.shots[1].visual_beats[1].interval.duration_ticks // 2
    )


def test_invalid_blocking_ordinal_and_wrong_dialogue_semantic_fail_closed(id_factory, blocking_commit) -> None:
    draft = make_draft()
    invalid_shot = replace(draft.shots[0], blocking_beat_ordinal=99)
    with pytest.raises(DomainValidationError):
        build_vec(id_factory, blocking_commit, draft=replace(draft, shots=(invalid_shot, draft.shots[1])))

    character_as_dialogue = DialogueBindingIntent(
        shot_ordinal=2,
        visual_beat_ordinal=2,
        fact_handle=_opaque_handle("a"),
        placement_phase=PlacementPhase.MIDDLE,
    )
    second = replace(draft.shots[1], dialogue_binding_intents=(character_as_dialogue,))
    with pytest.raises(DomainValidationError):
        build_vec(id_factory, blocking_commit, draft=replace(draft, shots=(draft.shots[0], second)))

    with pytest.raises(DomainValidationError):
        assemble_vec(
            draft=draft,
            blocking_commit=blocking_commit,
            facts=make_facts(),
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=IdFactory(program_version="different-approved-program"),
            program_version=PROGRAM_VERSION,
        )


def test_blocking_commit_rejects_mismatched_program_identity() -> None:
    with pytest.raises(DomainValidationError, match="Blocking program_version"):
        assemble_blocking_commit(
            draft=make_blocking_draft(),
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=IdFactory(program_version="other-approved-program"),
            program_version=PROGRAM_VERSION,
        )


def test_blocking_commit_rejects_noncanonical_schema_identity(id_factory) -> None:
    with pytest.raises(DomainValidationError, match="schema_version must match canonical domain schema"):
        assemble_blocking_commit(
            draft=make_blocking_draft(),
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
            schema_version="foreign-schema-version",
        )


@pytest.mark.parametrize(
    ("foreign_episode_id", "foreign_program_version"),
    (
        (EPISODE_ID, "foreign-approved-program"),
        ("EP35-foreign", PROGRAM_VERSION),
    ),
)
def test_vec_rejects_blocking_commit_not_rebuildable_by_current_program(
    id_factory,
    foreign_episode_id: str,
    foreign_program_version: str,
) -> None:
    foreign_commit = assemble_blocking_commit(
        draft=make_blocking_draft(),
        episode_id=foreign_episode_id,
        scene_id=SCENE_ID,
        id_factory=IdFactory(program_version=foreign_program_version),
        program_version=foreign_program_version,
    )

    with pytest.raises(DomainValidationError, match="rebuildable by the current local B0 compiler"):
        build_vec(id_factory, foreign_commit)


@pytest.mark.parametrize(
    "transition_intents",
    (
        (),
        ("hard cut", "unconsumed transition"),
    ),
)
def test_vec_rejects_incomplete_or_unconsumed_transition_intents(
    id_factory, blocking_commit, transition_intents
) -> None:
    with pytest.raises(DomainValidationError, match="exactly one transition intent"):
        build_vec(
            id_factory,
            blocking_commit,
            draft=replace(make_draft(), transition_intents=transition_intents),
        )


def test_vec_exposes_no_caller_override_for_local_artifact_identities() -> None:
    parameters = inspect.signature(assemble_vec).parameters

    assert "execution_design_artifact_id" not in parameters
    assert "blocking_commit_artifact_id" not in parameters


def test_assembler_has_no_legacy_fact_or_timing_inference_path() -> None:
    assembler_source = inspect.getsource(vec_assembler)
    allocator_source = inspect.getsource(allocate_shot_timelines)

    assert ".statement" not in assembler_source
    assert ".source_start" not in assembler_source
    assert ".source_end" not in assembler_source
    assert "duration_weight" not in allocator_source
    assert "allocate_shot_ticks" not in allocator_source
