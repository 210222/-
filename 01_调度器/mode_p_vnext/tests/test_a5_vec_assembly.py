"""A5 acceptance tests: deterministic Blocking, Timeline, and VEC assembly.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §5.3–§5.5 / §14 A5.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from mode_p_vnext.domain.artifact import (
    DomainValidationError,
    SourceRef,
)
from mode_p_vnext.domain.blocking import (
    BlockingBeat,
    BlockingBeatDraft,
    BlockingCommit,
    BlockingDraft,
)
from mode_p_vnext.domain.decisions import (
    DecisionBasis,
    DecisionDraft,
    VisualCurvePointDraft,
)
from mode_p_vnext.domain.facts import FactKind, FactRegistry, ScriptFact
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.time import (
    TICKS_PER_SECOND,
    TickRange,
)
from mode_p_vnext.domain.vec import (
    StoryboardRole,
    VisualBeatPhase,
    VisualBeatDraft,
    ExecutionDesignDraft,
    ShotDesignDraft,
    VisualExecutionContract,
)
from mode_p_vnext.services.blocking_assembler import assemble_blocking_commit
from mode_p_vnext.services.timeline_allocator import (
    MAX_SHOT_TICKS,
    allocate_shot_ticks,
)
from mode_p_vnext.services.vec_assembler import assemble_vec


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

PROGRAM_VERSION = "mode-p-vnext-a5-test"
SCHEMA_VERSION = "2.1"
EPISODE_ID = "EP35"
SCENE_ID = "EP35-S2"


@pytest.fixture
def id_factory() -> IdFactory:
    return IdFactory(program_version=PROGRAM_VERSION)


@pytest.fixture
def blocking_draft() -> BlockingDraft:
    return BlockingDraft(
        beats=(
            BlockingBeatDraft(
                ordinal=1,
                dramatic_action="He arrives at the shooting range.",
                character_states=(
                    {"character_id": "chen", "posture": "tense"},
                ),
                prop_states=(),
                gaze_relations=(),
                action_paths=("enter the range",),
                continuity_effect="Establishes the space.",
            ),
            BlockingBeatDraft(
                ordinal=2,
                dramatic_action="He loads the pistol.",
                character_states=(
                    {"character_id": "chen", "posture": "focused"},
                ),
                prop_states=({"prop_id": "pistol", "state": "loaded"},),
                gaze_relations=("chen -> pistol",),
                action_paths=("load weapon",),
                continuity_effect="The weapon is now live.",
            ),
        )
    )


@pytest.fixture
def blocking_commit(id_factory: IdFactory, blocking_draft: BlockingDraft) -> BlockingCommit:
    return assemble_blocking_commit(
        draft=blocking_draft,
        episode_id=EPISODE_ID,
        scene_id=SCENE_ID,
        id_factory=id_factory,
        program_version=PROGRAM_VERSION,
        schema_version=SCHEMA_VERSION,
    )


@pytest.fixture
def execution_design_draft() -> ExecutionDesignDraft:
    return ExecutionDesignDraft(
        curve_points=(
            VisualCurvePointDraft(
                dramatic_beat_ordinal=1,
                intensity=60,
                explanation="arrival tension",
            ),
            VisualCurvePointDraft(
                dramatic_beat_ordinal=2,
                intensity=85,
                explanation="weapon escalation",
            ),
        ),
        decisions=(
            DecisionDraft(
                scope="camera distance for the loading shot",
                basis=DecisionBasis.CHOICE,
                locked_by=(),
                options=("extreme close-up on hands", "medium shot with face"),
                selected_index=0,
                rationale="weapon detail sells the threat",
                tradeoff="sacrifice facial reaction in this beat",
            ),
        ),
        shots=(
            ShotDesignDraft(
                blocking_beat_ordinal=1,
                dramatic_function="introduce the range and the protagonist's state",
                attention_target="chen entering the space",
                information_action="the range is empty, chen is alone",
                framing_intent="wide establishing",
                camera_pose="eye level",
                camera_motion="static",
                composition="depth layering with targets in background",
                lighting="harsh overhead fluorescents",
                performance="controlled breathing, deliberate steps",
                duration_weight=4,
                visual_beats=(
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ENTRY,
                        subject_state="chen at doorway, surveying",
                        attention="the empty range",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ACTION,
                        subject_state="chen steps forward",
                        attention="the shooting lane",
                        storyboard_role=StoryboardRole.OPTIONAL,
                    ),
                ),
            ),
            ShotDesignDraft(
                blocking_beat_ordinal=2,
                dramatic_function="weapon preparation as threat escalation",
                attention_target="hands loading the pistol",
                information_action="the pistol is ready to fire",
                framing_intent="extreme close-up on hands and weapon",
                camera_pose="overhead angle",
                camera_motion="slow push-in",
                composition="hands dominate frame, face out of focus",
                lighting="single practical above the bench",
                performance="precise, ritualistic movements",
                duration_weight=6,
                visual_beats=(
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ENTRY,
                        subject_state="hands reach for the case",
                        attention="the pistol case",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.ACTION,
                        subject_state="magazine slides in",
                        attention="the click of the magazine seating",
                        storyboard_role=StoryboardRole.REQUIRED,
                    ),
                    VisualBeatDraft(
                        phase=VisualBeatPhase.REACTION,
                        subject_state="chen's breath steadies",
                        attention="the now-live weapon",
                        storyboard_role=StoryboardRole.OMIT,
                    ),
                ),
            ),
        ),
        transition_intents=("hard cut on the magazine click",),
        audio_intents=("mechanical click of magazine",),
        reference_intents=("pistol prop reference",),
        handoff_intent="cut to the target paper, hold 12 frames",
    )


@pytest.fixture
def fact_registry() -> FactRegistry:
    return FactRegistry(
        facts=(
            ScriptFact(
                fact_id="char_chen",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Chen is the protagonist, wearing a black tactical jacket.",
                source_ref=SourceRef(source_id="ep35_script", digest="a" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="prop_pistol",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="A standard-issue 9mm pistol sits in a foam case.",
                source_ref=SourceRef(source_id="ep35_script", digest="b" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="costume_tactical_jacket",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Black tactical jacket with worn leather patches on the elbows.",
                source_ref=SourceRef(source_id="ep35_script", digest="c" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="scene_shooting_range",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Indoor shooting range, fluorescent lighting, sound-dampening panels.",
                source_ref=SourceRef(source_id="ep35_script", digest="d" * 64, locator="S2"),
            ),
            ScriptFact(
                fact_id="dialogue_chen_muttering",
                scene_id=SCENE_ID,
                kind=FactKind.SCRIPT,
                statement="Chen: This time I won't miss.",
                source_ref=SourceRef(source_id="ep35_script", digest="e" * 64, locator="S2"),
            ),
        )
    )


# ===================================================================
# BlockingAssembler
# ===================================================================

class TestBlockingAssembler:
    """Architecture §5.3 B0: model outputs only creative fields."""

    def test_draft_to_commit_produces_local_ids(
        self, id_factory: IdFactory, blocking_draft: BlockingDraft
    ) -> None:
        commit = assemble_blocking_commit(
            draft=blocking_draft,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )

        assert commit.commit_id.startswith("blocking_commit:0000:")
        assert len(commit.beats) == 2
        for beat in commit.beats:
            assert beat.beat_id.startswith("blocking_commit:")
            assert beat.entry_state_id.startswith("blocking_commit:")
            assert beat.exit_state_id.startswith("blocking_commit:")
            # Model must not know these IDs.
            assert beat.beat_id != ""
            assert beat.entry_state_id != beat.exit_state_id

    def test_commit_state_chain_is_contiguous(
        self, id_factory: IdFactory, blocking_draft: BlockingDraft
    ) -> None:
        commit = assemble_blocking_commit(
            draft=blocking_draft,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )

        assert commit.entry_state_id == commit.beats[0].entry_state_id
        assert commit.exit_state_id == commit.beats[-1].exit_state_id
        for left, right in zip(commit.beats, commit.beats[1:]):
            assert left.exit_state_id == right.entry_state_id

    def test_identical_inputs_yield_identical_commit(
        self, id_factory: IdFactory, blocking_draft: BlockingDraft
    ) -> None:
        a = assemble_blocking_commit(
            draft=blocking_draft,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        b = assemble_blocking_commit(
            draft=blocking_draft,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        assert a.commit_id == b.commit_id
        assert a.entry_state_id == b.entry_state_id
        assert a.exit_state_id == b.exit_state_id
        for ba, bb in zip(a.beats, b.beats):
            assert ba.beat_id == bb.beat_id

    def test_creative_fields_are_preserved(
        self, id_factory: IdFactory, blocking_draft: BlockingDraft
    ) -> None:
        commit = assemble_blocking_commit(
            draft=blocking_draft,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        for draft_beat, commit_beat in zip(blocking_draft.beats, commit.beats):
            assert commit_beat.dramatic_action == draft_beat.dramatic_action
            assert commit_beat.action_paths == draft_beat.action_paths
            assert commit_beat.continuity_effect == draft_beat.continuity_effect


# ===================================================================
# TimelineAllocator
# ===================================================================

class TestTimelineAllocator:
    """Architecture §5.2 / §5.4: local tick allocation from weight hints."""

    def test_proportional_allocation_sums_to_segment_duration(self) -> None:
        weights = (4, 6)
        timeline, ranges = allocate_shot_ticks(weights)

        assert timeline.duration_ticks == sum(r.duration_ticks for r in ranges)
        assert timeline.duration_ticks > 0

    def test_shot_ranges_are_adjacent_and_cover_segment(self) -> None:
        weights = (4, 6)
        timeline, ranges = allocate_shot_ticks(weights)

        assert ranges[0].start_tick == 0
        for left, right in zip(ranges, ranges[1:]):
            assert left.end_tick == right.start_tick
        assert ranges[-1].end_tick == timeline.duration_ticks

    def test_no_shot_exceeds_max_15_seconds(self) -> None:
        weights = (1, 100, 1)
        _, ranges = allocate_shot_ticks(weights)
        for r in ranges:
            assert r.duration_ticks <= MAX_SHOT_TICKS

    def test_every_shot_gets_at_least_one_tick(self) -> None:
        weights = (1, 1, 1)
        _, ranges = allocate_shot_ticks(weights)
        for r in ranges:
            assert r.duration_ticks >= 1

    def test_deterministic_output(self) -> None:
        a_timeline, a_ranges = allocate_shot_ticks((3, 7))
        b_timeline, b_ranges = allocate_shot_ticks((3, 7))
        assert a_timeline.duration_ticks == b_timeline.duration_ticks
        for ra, rb in zip(a_ranges, b_ranges):
            assert ra.start_tick == rb.start_tick
            assert ra.end_tick == rb.end_tick

    def test_empty_weights_rejected(self) -> None:
        with pytest.raises(DomainValidationError, match="at least one"):
            allocate_shot_ticks(())

    def test_negative_weight_rejected(self) -> None:
        with pytest.raises(DomainValidationError, match="positive integer"):
            allocate_shot_ticks((-1, 5))  # type: ignore[arg-type]


# ===================================================================
# VECAssembler
# ===================================================================

class TestVECAssembler:
    """Architecture §5.3–§5.5: deterministic VEC from creative drafts."""

    def test_full_assembly_produces_valid_vec(
        self,
        id_factory: IdFactory,
        blocking_commit: BlockingCommit,
        execution_design_draft: ExecutionDesignDraft,
        fact_registry: FactRegistry,
    ) -> None:
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )

        assert vec.contract_id.startswith("visual_execution_contract:0000:")
        assert vec.scene_id == SCENE_ID
        assert vec.handoff_intent == execution_design_draft.handoff_intent

    def test_contract_has_exactly_one_segment(self, id_factory, blocking_commit, execution_design_draft, fact_registry):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        assert len(vec.segments) == 1

    def test_shots_are_covered_by_segment(self, id_factory, blocking_commit, execution_design_draft, fact_registry):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        segment = vec.segments[0]
        assert set(segment.shot_ids) == {s.shot_id for s in vec.shots}

    def test_boundaries_cover_every_adjacent_shot_pair(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        # 2 shots → 1 boundary
        assert len(vec.boundaries) == 1
        assert vec.boundaries[0].from_shot_id == vec.shots[0].shot_id
        assert vec.boundaries[0].to_shot_id == vec.shots[1].shot_id

    def test_curve_points_resolve_to_blocking_beats(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        beat_ids = {b.beat_id for b in blocking_commit.beats}
        for cp in vec.curve_points:
            assert cp.blocking_beat_id in beat_ids

    def test_every_shot_carries_visual_beats(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        for shot in vec.shots:
            assert len(shot.visual_beats) >= 1
            for beat in shot.visual_beats:
                assert beat.shot_id == shot.shot_id

    def test_visual_beat_intervals_are_adjacent_and_cover_shot(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        for shot in vec.shots:
            beats = shot.visual_beats
            assert beats[0].interval.start_tick == shot.interval.start_tick
            assert beats[-1].interval.end_tick == shot.interval.end_tick
            for left, right in zip(beats, beats[1:]):
                assert left.interval.end_tick == right.interval.start_tick

    def test_safety_constant_mirror_flip_is_enforced(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        for shot in vec.shots:
            assert shot.mirror_flip_forbidden is True

    def test_reference_requirements_derived_from_facts(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        # char_chen, prop_pistol, costume_tactical_jacket, scene_shooting_range → 4 refs
        assert len(vec.reference_requirements) == 4
        roles = {r.role for r in vec.reference_requirements}
        assert roles == {"character", "prop", "costume", "scene"}

    def test_audio_events_generated_from_dialogue_facts(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        vec = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        assert len(vec.audio_events) == 1
        assert len(vec.voice_requirements) == 1
        assert vec.voice_requirements[0].audio_event_id == vec.audio_events[0].event_id

    def test_deterministic_vec_rebuild(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        a = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        b = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        assert a.contract_id == b.contract_id
        assert len(a.shots) == len(b.shots)
        for sa, sb in zip(a.shots, b.shots):
            assert sa.shot_id == sb.shot_id

    def test_b1_ordinal_not_in_blocking_commit_is_rejected(
        self, id_factory, blocking_commit, execution_design_draft, fact_registry
    ):
        from mode_p_vnext.domain.vec import ShotDesignDraft

        bad_draft = ExecutionDesignDraft(
            curve_points=execution_design_draft.curve_points,
            decisions=execution_design_draft.decisions,
            shots=(
                ShotDesignDraft(
                    blocking_beat_ordinal=99,  # does not exist
                    dramatic_function="test",
                    attention_target="test",
                    information_action="test",
                    framing_intent="test",
                    camera_pose="test",
                    camera_motion="test",
                    composition="test",
                    lighting="test",
                    performance="test",
                    duration_weight=5,
                    visual_beats=(
                        VisualBeatDraft(
                            phase=VisualBeatPhase.ENTRY,
                            subject_state="test",
                            attention="test",
                            storyboard_role=StoryboardRole.REQUIRED,
                        ),
                    ),
                ),
            ),
            transition_intents=(),
            audio_intents=(),
            reference_intents=(),
            handoff_intent="test handoff",
        )
        with pytest.raises(DomainValidationError, match="blocking ordinal"):
            assemble_vec(
                draft=bad_draft,
                blocking_commit=blocking_commit,
                facts=fact_registry,
                episode_id=EPISODE_ID,
                scene_id=SCENE_ID,
                id_factory=id_factory,
                program_version=PROGRAM_VERSION,
            )


# ===================================================================
# Cross-cutting invariants (architecture §14 A5)
# ===================================================================

class TestModelOutputPurity:
    """The model must not produce final VEC fields, IDs, or hashes."""

    def test_blocking_draft_has_no_machine_fields(self) -> None:
        """BlockingDraft carries only creative fields, no local IDs."""
        # Verify by construction: BlockingDraft.__init__ accepts no ID fields.
        draft = BlockingDraft(
            beats=(
                BlockingBeatDraft(
                    ordinal=1,
                    dramatic_action="Enter.",
                    character_states=({"character_id": "a", "state": "ready"},),
                    prop_states=(),
                    gaze_relations=(),
                    action_paths=("walk",),
                    continuity_effect="none",
                ),
            )
        )
        # The domain model itself rejects machine fields in the draft.
        assert not hasattr(draft, "commit_id")
        assert not hasattr(draft, "fingerprint")

    def test_execution_design_draft_has_no_final_vec_fields(self) -> None:
        """B1 draft must not contain final VEC fields like absolute ticks."""
        draft = ExecutionDesignDraft(
            curve_points=(
                VisualCurvePointDraft(
                    dramatic_beat_ordinal=1, intensity=50, explanation="test"
                ),
            ),
            decisions=(
                DecisionDraft(
                    scope="test",
                    basis=DecisionBasis.LOCKED,
                    locked_by=("rule",),
                    options=("single option",),
                    selected_index=0,
                    rationale="test",
                    tradeoff="none",
                ),
            ),
            shots=(
                ShotDesignDraft(
                    blocking_beat_ordinal=1,
                    dramatic_function="test",
                    attention_target="test",
                    information_action="test",
                    framing_intent="test",
                    camera_pose="test",
                    camera_motion="test",
                    composition="test",
                    lighting="test",
                    performance="test",
                    duration_weight=3,
                    visual_beats=(
                        VisualBeatDraft(
                            phase=VisualBeatPhase.ENTRY,
                            subject_state="test",
                            attention="test",
                            storyboard_role=StoryboardRole.REQUIRED,
                        ),
                    ),
                ),
            ),
            transition_intents=(),
            audio_intents=(),
            reference_intents=(),
            handoff_intent="test",
        )
        # B1 draft must not expose absolute ticks, contract IDs, or hashes.
        assert not hasattr(draft, "contract_id")
        assert not hasattr(draft, "source_fact_hashes")
        assert not hasattr(draft, "phase_a_fingerprint")
        assert not hasattr(draft, "blocking_commit")
        assert not hasattr(draft, "mirror_flip_forbidden")


class TestDeterministicRebuild:
    """Same inputs → same VEC (architecture invariant)."""

    def test_rebuild_with_no_facts_still_deterministic(
        self, id_factory, blocking_commit, execution_design_draft
    ):
        empty_facts = FactRegistry(
            facts=(
                ScriptFact(
                    fact_id="char_x",
                    scene_id=SCENE_ID,
                    kind=FactKind.SCRIPT,
                    statement="placeholder",
                    source_ref=SourceRef(source_id="s", digest="f" * 64),
                ),
            )
        )
        a = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=empty_facts,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        b = assemble_vec(
            draft=execution_design_draft,
            blocking_commit=blocking_commit,
            facts=empty_facts,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        assert a.contract_id == b.contract_id

    def test_different_model_drafts_produce_different_vec_ids(
        self, id_factory, blocking_commit, fact_registry
    ):
        draft_a = ExecutionDesignDraft(
            curve_points=(
                VisualCurvePointDraft(
                    dramatic_beat_ordinal=1, intensity=10, explanation="low"
                ),
            ),
            decisions=(
                DecisionDraft(
                    scope="a",
                    basis=DecisionBasis.LOCKED,
                    locked_by=("x",),
                    options=("one",),
                    selected_index=0,
                    rationale="r",
                    tradeoff="t",
                ),
            ),
            shots=(
                ShotDesignDraft(
                    blocking_beat_ordinal=1,
                    dramatic_function="a",
                    attention_target="a",
                    information_action="a",
                    framing_intent="a",
                    camera_pose="a",
                    camera_motion="a",
                    composition="a",
                    lighting="a",
                    performance="a",
                    duration_weight=1,
                    visual_beats=(
                        VisualBeatDraft(
                            phase=VisualBeatPhase.ENTRY,
                            subject_state="a",
                            attention="a",
                            storyboard_role=StoryboardRole.REQUIRED,
                        ),
                    ),
                ),
            ),
            transition_intents=(),
            audio_intents=(),
            reference_intents=(),
            handoff_intent="a",
        )
        draft_b = ExecutionDesignDraft(
            curve_points=(
                VisualCurvePointDraft(
                    dramatic_beat_ordinal=1, intensity=90, explanation="high"
                ),
            ),
            decisions=(
                DecisionDraft(
                    scope="b",
                    basis=DecisionBasis.LOCKED,
                    locked_by=("y",),
                    options=("two",),
                    selected_index=0,
                    rationale="r",
                    tradeoff="t",
                ),
            ),
            shots=(
                ShotDesignDraft(
                    blocking_beat_ordinal=1,
                    dramatic_function="b",
                    attention_target="b",
                    information_action="b",
                    framing_intent="b",
                    camera_pose="b",
                    camera_motion="b",
                    composition="b",
                    lighting="b",
                    performance="b",
                    duration_weight=2,
                    visual_beats=(
                        VisualBeatDraft(
                            phase=VisualBeatPhase.ENTRY,
                            subject_state="b",
                            attention="b",
                            storyboard_role=StoryboardRole.REQUIRED,
                        ),
                    ),
                ),
            ),
            transition_intents=(),
            audio_intents=(),
            reference_intents=(),
            handoff_intent="b",
        )
        vec_a = assemble_vec(
            draft=draft_a,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        vec_b = assemble_vec(
            draft=draft_b,
            blocking_commit=blocking_commit,
            facts=fact_registry,
            episode_id=EPISODE_ID,
            scene_id=SCENE_ID,
            id_factory=id_factory,
            program_version=PROGRAM_VERSION,
        )
        assert vec_a.contract_id != vec_b.contract_id
