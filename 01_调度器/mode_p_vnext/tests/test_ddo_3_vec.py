"""DDO-3: Phase B must commit blocking before a single-source VEC exists."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mode_p_vnext.director_vnext1.agent import DirectorAgent, _phase_a_fingerprint
from mode_p_vnext.director_vnext1.contracts import (
    BlockingBeat,
    BlockingCommit,
    CharacterBlockingState,
    DecisionCandidate,
    DialogueEvent,
    DirectorContractError,
    DirectorDecisionRecord,
    DirectorProblem,
    DirectorProblemSet,
    EpisodeDirectionState,
    EpisodeRequest,
    GenerationSegment,
    PhaseAResult,
    PhaseBResult,
    PropBlockingState,
    RejectedOption,
    ReferenceBindingRequirement,
    SceneInput,
    SceneIntentBeat,
    SceneIntentContract,
    SceneVisualCurve,
    VisualCurvePoint,
    VisualExecutionContract,
    VisualShot,
)


FACT_HASH = "c" * 64


def _phase_a() -> PhaseAResult:
    return PhaseAResult(
        SceneIntentContract(
            scene_id="S2", scene_priority="make obligation visible",
            dramatic_turn="an invitation becomes a demand",
            relationship_state="Chen holds authority over Zhou",
            performance_question="when does Zhou yield", information_goal="the offer carries risk",
            scene_objective="make Zhou weigh the cost of acceptance",
            dramatic_action="an invitation becomes a moral demand",
            entry_state="Zhou keeps distance from the offer",
            exit_state="Zhou accepts the weight of the choice",
            power_curve="Chen's authority transfers pressure to Zhou",
            character_actions=("Chen holds the demand", "Zhou yields attention"),
            beats=(SceneIntentBeat("S2-B1", ("fact:S2-1",), "authority becomes explicit"),),
            attention_trajectory="Chen's demand to Zhou's decision",
            audience_knowledge_delta="the offer carries a professional cost",
            character_knowledge_delta="Zhou understands the cost of refusal",
            risk_flags=("do not turn yielding into an unmotivated action",),
            must_preserve=("Zhou remains guarded before accepting",),
            avoid_list=("unmotivated emotional reversal",),
        ),
        DirectorProblemSet("S2", (DirectorProblem("P1", "power", "Who controls the choice?", ("power",)),)),
    )


def _blocking(phase_a: PhaseAResult | None = None) -> BlockingCommit:
    return BlockingCommit(
        commit_id="B-S2", scene_id="S2",
        phase_a_fingerprint=_phase_a_fingerprint(phase_a) if phase_a else "phase-a-fixture",
        beats=(
            BlockingBeat(
                beat_id="BEAT-1", dramatic_function="authority presses on Zhou",
                character_states=(
                    CharacterBlockingState("CHEN", "entry steps", "screen_left", "faces right", "faces Zhou", "Zhou", "hold", ("head", "torso", "right_hand"), "chen-w1"),
                    CharacterBlockingState("ZHOU", "entry steps", "screen_right", "faces left", "faces Chen", "Chen", "hold", ("head", "torso", "right_hand"), "zhou-w1"),
                ),
                prop_states=(
                    PropBlockingState("PHONE-1", "phone", "ZHOU", "right", "secure", "screen outward", "toward camera", "front plane", "toward Chen", "closed", "ZHOU"),
                ),
                action_paths=("Chen holds the threshold while Zhou yields one step",),
                space_control="Chen controls the exit route", entry_state_id="S2-entry", exit_state_id="S2-pressured",
                dramatic_reason="the invitation must be motivated by spatial authority", constraint_refs=("fact:S2-1",),
            ),
        ),
        entry_state_id="S2-entry", exit_state_id="S2-pressured",
        dramatic_reason="authority shifts before the invitation is accepted", constraint_refs=("fact:S2-1",),
    )


def _phase_b(blocking: BlockingCommit | None = None, phase_a: PhaseAResult | None = None) -> PhaseBResult:
    blocking = blocking or _blocking(phase_a)
    curve = SceneVisualCurve(
        "S2", blocking.fingerprint,
        (VisualCurvePoint("BEAT-1", "Chen to Zhou", "the demand becomes explicit", "constrained", "focused", "restraint", "continue until the decision is voiced"),),
    )
    candidates = (
        DecisionCandidate("OPT-HOLD", "D-S2", "shot_topology", "hold-authority", "hold the relation while the pressure changes", ("fact:S2-1",), "protect the relation", "less coverage", "low", ("identity", "screen_order")),
        DecisionCandidate("OPT-SPLIT", "D-S2", "shot_topology", "split-reaction", "divide the reaction after the demand", ("fact:S2-1",), "isolate hesitation", "may weaken spatial pressure", "medium", ("identity", "screen_order")),
    )
    decision = DirectorDecisionRecord(
        decision_id="D-S2", scope="S2", decision_kind="shot_topology", problem_ids=("P1",),
        blocking_commit_fingerprint=blocking.fingerprint, selected_option_id="OPT-HOLD", constraint_locked=True,
        selected_capsule_ids=(), evidence_refs=("fact:S2-1",),
        decision_summary="keep authority and hesitation in one readable relation", tradeoff_summary="coverage is intentionally restrained",
        rejected_options=(RejectedOption("OPT-SPLIT", "WRONG_PACE", "separation releases the pressure too early"),),
        risk_flags=("model may over-separate the pair",), freedom_corridor=("minor facial timing",),
        influenced_vec_field_ids=("shot:SH-1:composition",),
    )
    segment = GenerationSegment("SEG-1", 0, 100, ("SH-1",))
    dialogue = DialogueEvent("DIALOGUE-1", "SEG-1", "CHEN", "voice-chen", 10, 30, "Come with me.")
    shot = VisualShot(
        shot_id="SH-1", segment_id="SEG-1", start_tick=0, end_tick=100,
        dramatic_function="hold authority against hesitation", attention_target="the relation", information_action="reveal the demand",
        blocking_beat_id="BEAT-1", axis_id="AX-1", camera_side="A", screen_order=("CHEN-left", "ZHOU-right"),
        shot_size="two-shot", focal_intent="relation priority", camera_pose="entry-side observation", camera_motion="restrained hold",
        composition="paired relation", lighting="hospital threshold contrast", performance="Chen holds; Zhou yields", gaze_targets=("CHEN->ZHOU", "ZHOU->CHEN"),
        prop_state_ids=("PHONE-1",), dialogue_event_ids=("DIALOGUE-1",),
        start_state_id="S2-entry", end_state_id="S2-pressured", cut_in_reason="enter on authority", cut_out_reason="leave after demand",
        selected_capsule_ids=(), freedom_corridor=("minor facial timing",), decision_id="D-S2",
    )
    vec = VisualExecutionContract(
        contract_id="VEC-S2", schema_version="1.1", scene_id="S2", source_fact_hashes=(FACT_HASH,),
        phase_a_fingerprint=blocking.phase_a_fingerprint, blocking_commit=blocking, visual_curve=curve,
        decisions=(decision,), segments=(segment,), shots=(shot,), boundaries=(), dialogue_events=(dialogue,),
        reference_binding_requirements=(
            ReferenceBindingRequirement("REQ-chen-id", "character_identity", "character", "CHEN", 100),
            ReferenceBindingRequirement("REQ-chen-wardrobe", "wardrobe", "character", "CHEN", 100),
            ReferenceBindingRequirement("REQ-zhou-id", "character_identity", "character", "ZHOU", 100),
            ReferenceBindingRequirement("REQ-zhou-wardrobe", "wardrobe", "character", "ZHOU", 100),
            ReferenceBindingRequirement("REQ-phone", "prop_geometry", "prop", "phone", 80),
            ReferenceBindingRequirement("REQ-scene", "scene_layout", "scene", "S2", 70),
        ),
        final_handoff="review the held relation before rendering",
    )
    return PhaseBResult(blocking, curve, candidates, (decision,), vec)


def test_blocking_commit_precedes_k2_and_any_vec_camera_choice():
    phase_a = _phase_a()
    provider = _PhaseBFixtureDirector()
    agent = DirectorAgent(provider, director_id="DIRECTOR-S2", catalog=())
    result = agent.plan_phase_b(_request(), _scene())
    assert provider.order == ["E0", "S1", "B0", "B1"]
    assert result.k2_packet.stage == "K2"
    assert result.k2_packet.blocking_commit_id == "B-S2"
    assert result.phase_b.visual_execution_contract.blocking_commit.fingerprint == result.blocking_commit.fingerprint
    bad_decision = replace(result.phase_b.decisions[0], blocking_commit_fingerprint="wrong")
    with pytest.raises(DirectorContractError, match="camera/execution decision"):
        replace(result.phase_b.visual_execution_contract, decisions=(bad_decision,))


def test_candidate_record_requires_real_distinct_options_and_auditable_provenance():
    valid = _phase_b()
    assert valid.decisions[0].selected_option_id == "OPT-HOLD"
    assert valid.decisions[0].rejected_options[0].rejection_code == "WRONG_PACE"
    duplicate_candidate = replace(valid.candidates[1], proposal_signature="hold-authority")
    with pytest.raises(DirectorContractError, match="genuinely distinct"):
        PhaseBResult(valid.blocking_commit, valid.visual_curve, (valid.candidates[0], duplicate_candidate), valid.decisions, valid.visual_execution_contract)


def test_vec_fails_closed_for_missing_spatial_prop_or_mirror_invariants():
    valid = _phase_b()
    invalid_prop_shot = replace(valid.visual_execution_contract.shots[0], prop_state_ids=("PHONE-UNKNOWN",))
    with pytest.raises(DirectorContractError, match="prop state"):
        replace(valid.visual_execution_contract, shots=(invalid_prop_shot,))
    with pytest.raises(DirectorContractError, match="mirror"):
        replace(valid.visual_execution_contract.shots[0], mirror_flip_forbidden=False)


def _request() -> EpisodeRequest:
    return EpisodeRequest("EP35", "A doctor must choose risk over safety.", ("hospital entrance",))


def _scene() -> SceneInput:
    return SceneInput("S2", "EP35", "Chen makes an invitation that becomes a demand.", "hospital entrance", ("Zhou is guarded",), ("power",), ())


class _PhaseBFixtureDirector:
    def __init__(self) -> None:
        self.order: list[str] = []
        self._phase_a: PhaseAResult | None = None
        self._blocking: BlockingCommit | None = None

    def create_episode_direction(self, request: EpisodeRequest) -> EpisodeDirectionState:
        self.order.append("E0")
        return EpisodeDirectionState(request.episode_id, "DIRECTOR-S2", "duty meets cost", ("Zhou yields under pressure",), ("the demand",), "pressure builds around the relation")

    def analyse_scene_phase_a(self, scene: SceneInput, episode: EpisodeDirectionState) -> PhaseAResult:
        self.order.append("S1")
        self._phase_a = _phase_a()
        return self._phase_a

    def create_blocking_commit(self, scene: SceneInput, phase_a: PhaseAResult, k1_packet):
        self.order.append("B0")
        self._blocking = _blocking(phase_a)
        return self._blocking

    def design_phase_b(self, scene: SceneInput, phase_a: PhaseAResult, blocking_commit: BlockingCommit, k1_packet, k2_packet):
        self.order.append("B1")
        assert k2_packet.blocking_commit_id == blocking_commit.commit_id
        return _phase_b(blocking_commit, phase_a)
