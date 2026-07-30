"""DDO-2: persistent Director, bounded S1, K1 and content-addressed cache."""

from __future__ import annotations

import pytest

from mode_p_vnext.director_vnext1.agent import DirectorAgent
from mode_p_vnext.director_vnext1.cache import ContentAddressedCache, content_address
from mode_p_vnext.director_vnext1.contracts import (
    DirectorContractError,
    DirectorProblem,
    DirectorProblemSet,
    EpisodeDirectionState,
    EpisodeRequest,
    KnowledgeCapsule,
    PhaseAResult,
    SceneInput,
    SceneIntentBeat,
    SceneIntentContract,
)


HASH = "b" * 64


def _capsule() -> KnowledgeCapsule:
    return KnowledgeCapsule(
        capsule_id="K-power", source_locator="capsule/power", source_sha256=HASH,
        primary_type="dramatic", tags=("power",),
        director_problem="How does attention move?", dramatic_function="make status legible",
        triggers=("power",), contraindications=(), required_context=(),
        execution_rules=("preserve approved relation",), expected_effect="the shift is readable",
        tradeoffs=(), alternatives=(), confidence_level="high", review_status="approved",
        allowed_uses=("attention",),
    )


class FixtureDirector:
    def __init__(self, *, bad_phase_a: bool = False) -> None:
        self.episode_calls = 0
        self.phase_a_calls = 0
        self.bad_phase_a = bad_phase_a

    def create_episode_direction(self, request: EpisodeRequest) -> EpisodeDirectionState:
        self.episode_calls += 1
        return EpisodeDirectionState(
            episode_id=request.episode_id, director_id="DIRECTOR-EP35",
            thematic_axis="professional faith meets personal cost",
            character_arc=("Zhou shifts from certainty to hesitation",),
            information_priorities=("the cost of the decision",),
            visual_development_goal="the environment increasingly presses on the character",
        )

    def analyse_scene_phase_a(self, scene: SceneInput, episode: EpisodeDirectionState) -> PhaseAResult:
        self.phase_a_calls += 1
        intent = SceneIntentContract(
            scene_id=scene.scene_id,
            scene_priority="make the power imbalance readable",
            dramatic_turn="the invitation changes certainty into obligation",
            relationship_state="the senior doctor holds moral authority",
            performance_question="when does Zhou stop resisting the invitation",
            information_goal=("camera shot" if self.bad_phase_a else "the offer has a hidden cost"),
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
        )
        return PhaseAResult(
            scene_intent=intent,
            problem_set=DirectorProblemSet(
                scene_id=scene.scene_id,
                problems=(DirectorProblem("P-power", "power", "How does authority shift?", ("power",)),),
            ),
        )


def _request() -> EpisodeRequest:
    return EpisodeRequest("EP35", "A doctor must choose professional risk over safety.", ("hospital exterior",))


def _scene() -> SceneInput:
    return SceneInput(
        scene_id="EP35-S2", episode_id="EP35", script_excerpt="An invitation turns a routine meeting into a test.",
        scene_context="hospital exterior at night", character_state=("Zhou is guarded",),
        scene_tags=("power",), approved_context=(),
    )


def test_persistent_director_e0_s1_k1_and_hot_cache_are_repeatable():
    provider = FixtureDirector()
    agent = DirectorAgent(provider, director_id="DIRECTOR-EP35", catalog=(_capsule(),))
    first = agent.plan_phase_a(_request(), _scene())
    second = agent.plan_phase_a(_request(), _scene())
    assert first.episode_direction.director_id == agent.director_id == "DIRECTOR-EP35"
    assert provider.episode_calls == 1
    assert provider.phase_a_calls == 1
    assert first.phase_a_cache_key == second.phase_a_cache_key
    assert first.k1_packet.stage == "K1"
    assert first.k1_packet.blocking_commit_id == ""
    assert [item.capsule_id for item in first.k1_packet.primary_capsules] == ["K-power"]
    assert agent.cache.stats["hits"] >= 2


def test_phase_a_rejects_a_camera_answer_before_later_execution_phases():
    provider = FixtureDirector(bad_phase_a=True)
    agent = DirectorAgent(provider, director_id="DIRECTOR-EP35", catalog=(_capsule(),))
    with pytest.raises(DirectorContractError, match="camera/edit execution"):
        agent.plan_phase_a(_request(), _scene())


def test_content_address_uses_only_canonical_content_not_mapping_order_or_time():
    first = content_address("director-vnext1/test", {"b": ["two"], "a": "one"})
    second = content_address("director-vnext1/test", {"a": "one", "b": ["two"]})
    assert first == second
    cache = ContentAddressedCache()
    cache.put(first, "approved-result")
    assert cache.get(second) == "approved-result"
