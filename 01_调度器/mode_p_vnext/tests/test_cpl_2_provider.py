"""CPL-2 verifies the strict, text-only DeepSeek Director adapter."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict

import pytest

from mode_p_vnext.director_vnext1.agent import _phase_a_fingerprint
from mode_p_vnext.director_vnext1.contracts import (
    BlockingBeat,
    BlockingCommit,
    CharacterBlockingState,
    DecisionPacket,
    DecisionCandidate,
    DialogueEvent,
    DirectorDecisionRecord,
    DirectorProblem,
    DirectorProblemSet,
    EpisodeDirectionState,
    GenerationSegment,
    PhaseAResult,
    PhaseBExecutionDraft,
    PhaseBResult,
    PropBlockingState,
    ReferenceBindingRequirement,
    RejectedOption,
    SceneIntentBeat,
    SceneIntentContract,
    SceneVisualCurve,
    VisualCurvePoint,
    VisualExecutionContract,
    VisualShot,
)
from mode_p_vnext.director_vnext1.provider_deepseek import (
    ClaudeCodeDeepSeekTextClient,
    DEFAULT_DEEPSEEK_MODEL,
    DeepSeekDirectorProvider,
    DeepSeekProviderError,
    TextModelResponse,
)
from mode_p_vnext.director_vnext1.provider_prompts import (
    build_stage_messages,
    strict_json_schema,
)
from mode_p_vnext.director_vnext1.shadow_run import (
    UNKNOWN_SCRIPT_CASE_ID,
    run_unknown_script_text_shadow,
    unknown_script_case,
)


class FixtureTextClient:
    def __init__(self, responses, *, resolved_model=DEFAULT_DEEPSEEK_MODEL):
        self._responses = list(responses)
        self._resolved_model = resolved_model
        self.requests = []

    def complete(
        self,
        *,
        model,
        messages,
        temperature,
        max_tokens,
        thinking_enabled,
        json_schema=None,
        effort="max",
    ):
        self.requests.append(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "thinking_enabled": thinking_enabled,
                "json_schema": json_schema,
                "effort": effort,
            }
        )
        return TextModelResponse(
            content=self._responses.pop(0),
            resolved_model=self._resolved_model,
            request_id=f"text-{len(self.requests)}",
            input_tokens=100,
            output_tokens=50,
            cache_hit_tokens=10,
        )


class FailingTextClient:
    def __init__(self):
        self.calls = 0

    def complete(self, **_kwargs):
        self.calls += 1
        raise DeepSeekProviderError("synthetic transport timeout")


class NativeSchemaFallbackClient:
    uses_native_json_schema = True
    native_json_schema_max_chars = 12000

    def __init__(self, response, native_failure="Claude Code text transport failed with exit 1"):
        self.response = response
        self.native_failure = native_failure
        self.requests = []

    def complete(self, **kwargs):
        self.requests.append(kwargs)
        if kwargs["json_schema"] is not None:
            raise DeepSeekProviderError(self.native_failure)
        return TextModelResponse(
            content=self.response,
            resolved_model=DEFAULT_DEEPSEEK_MODEL,
            request_id="fallback-ok",
        )


def _outputs():
    episode, scene = unknown_script_case()
    direction = EpisodeDirectionState(
        episode_id=episode.episode_id,
        director_id="director-vnext1-deepseek",
        thematic_axis="responsibility becomes visible when authority withdraws",
        character_arc=("Lin Lan moves from waiting to accepting responsibility",),
        information_priorities=("the key transfers responsibility",),
        visual_development_goal="the remaining choice increasingly dominates attention",
    )
    phase_a = PhaseAResult(
        scene_intent=SceneIntentContract(
            scene_id=scene.scene_id,
            scene_priority="make the transfer of responsibility legible",
            dramatic_turn="the mentor leaves the decision with Lin Lan",
            relationship_state="authority withdraws and leaves pressure behind",
            performance_question="when does Lin Lan stop waiting for permission",
            information_goal="the key now carries a personal decision",
            scene_objective="make the audience feel the pause before action",
            dramatic_action="a transfer becomes a private burden",
            entry_state="Lin Lan watches the mentor control the choice",
            exit_state="Lin Lan focuses on the key without acting yet",
            power_curve="Zhao relinquishes authority and Lin inherits its weight",
            character_actions=("Zhao places the key and leaves", "Lin absorbs the silence"),
            beats=(
                SceneIntentBeat(
                    "BEAT-TRANSFER",
                    ("fact:key-transfer",),
                    "responsibility becomes explicit",
                ),
            ),
            attention_trajectory="mentor departure to the key and Lin's decision",
            audience_knowledge_delta="the exit choice belongs to Lin Lan",
            character_knowledge_delta="Lin Lan understands she cannot wait for instruction",
            risk_flags=("do not make Lin act before the pause",),
            must_preserve=("the key remains on the table",),
            avoid_list=("unmotivated emotional reversal",),
        ),
        problem_set=DirectorProblemSet(
            scene.scene_id,
            (
                DirectorProblem(
                    "P-TRANSFER",
                    "power",
                    "Who now carries the decision?",
                    ("power", "departure"),
                ),
            ),
        ),
    )
    blocking = BlockingCommit(
        commit_id="BLOCK-TRANSFER",
        scene_id=scene.scene_id,
        phase_a_fingerprint=_phase_a_fingerprint(phase_a),
        beats=(
            BlockingBeat(
                beat_id="BEAT-TRANSFER",
                dramatic_function="responsibility remains with Lin after Zhao exits",
                character_states=(
                    CharacterBlockingState(
                        "LIN", "table", "screen_right", "faces table", "faces key",
                        "emergency key", "hold", ("head", "torso", "right_hand"), "lin-w1",
                    ),
                    CharacterBlockingState(
                        "ZHAO", "exit door", "screen_left", "faces exit", "faces exit",
                        "exit", "depart", ("head", "torso", "left_hand"), "zhao-w1",
                    ),
                ),
                prop_states=(
                    PropBlockingState(
                        "KEY-ON-TABLE", "emergency_key", "none", "none", "flat",
                        "key bow upward", "toward exit", "table plane", "toward Lin",
                        "closed", "LIN",
                    ),
                ),
                action_paths=("Zhao places the key, exits left, Lin holds beside the table",),
                space_control="the exit opens the empty space beside Lin",
                entry_state_id="STATE-ENTRY",
                exit_state_id="STATE-KEY-FOCUS",
                dramatic_reason="the transfer must be readable before any action",
                constraint_refs=("fact:key-transfer", "fact:night-theatre"),
            ),
        ),
        entry_state_id="STATE-ENTRY",
        exit_state_id="STATE-KEY-FOCUS",
        dramatic_reason="authority leaves and responsibility remains",
        constraint_refs=("fact:key-transfer",),
    )
    curve = SceneVisualCurve(
        scene.scene_id,
        blocking.fingerprint,
        (
            VisualCurvePoint(
                "BEAT-TRANSFER", "mentor departure to key", "the choice is now Lin's",
                "opening space", "focused", "restraint", "cut only after the departure settles",
            ),
        ),
    )
    candidates = (
        DecisionCandidate(
            "OPT-RELATION", "DEC-TRANSFER", "attention_topology", "departure-to-key",
            "hold departure before shifting attention to the key", ("fact:key-transfer",),
            "protect the transfer", "restrained coverage", "low", ("actor timing",),
        ),
        DecisionCandidate(
            "OPT-ISOLATE", "DEC-TRANSFER", "attention_topology", "instant-key-close",
            "isolate the key immediately", ("fact:key-transfer",),
            "make the prop immediate", "loses the departure", "medium", ("prop emphasis",),
        ),
    )
    decision = DirectorDecisionRecord(
        decision_id="DEC-TRANSFER",
        scope=scene.scene_id,
        decision_kind="attention_topology",
        problem_ids=("P-TRANSFER",),
        blocking_commit_fingerprint=blocking.fingerprint,
        selected_option_id="OPT-RELATION",
        constraint_locked=True,
        selected_capsule_ids=("K-DIR-NARRATIVE-FIRST-001",),
        evidence_refs=("fact:key-transfer",),
        decision_summary="show the withdrawal before the key becomes the attention target",
        tradeoff_summary="the prop is not isolated at the first instant",
        rejected_options=(
            RejectedOption(
                "OPT-ISOLATE", "REVEALS_HIDDEN_INFORMATION",
                "an immediate key isolation skips the transfer of responsibility",
            ),
        ),
        risk_flags=("do not make the key change hands",),
        freedom_corridor=("minor facial timing",),
        influenced_vec_field_ids=("shot:SHOT-1:attention_target",),
    )
    segment = GenerationSegment("SEG-1", 0, 90, ("SHOT-1",))
    dialogue = DialogueEvent(
        "DIALOGUE-1", "SEG-1", "ZHAO", "voice-zhao", 10, 30, "这次你决定。"
    )
    shot = VisualShot(
        shot_id="SHOT-1", segment_id="SEG-1", start_tick=0, end_tick=90,
        dramatic_function="make responsibility remain after authority exits",
        attention_target="Zhao departure then the key near Lin",
        information_action="reveal transfer without changing the key state",
        blocking_beat_id="BEAT-TRANSFER", axis_id="AX-TRANSFER", camera_side="A",
        screen_order=("ZHAO-left", "LIN-right", "KEY-right"),
        shot_size="two-person medium", focal_intent="relation before object", camera_pose="table-side",
        camera_motion="restrained hold", composition="departure leaves negative space beside Lin",
        lighting="motivated emergency light", performance="Zhao exits; Lin delays action and looks to key",
        gaze_targets=("ZHAO->exit", "LIN->emergency_key"), prop_state_ids=("KEY-ON-TABLE",),
        dialogue_event_ids=("DIALOGUE-1",), start_state_id="STATE-ENTRY", end_state_id="STATE-KEY-FOCUS",
        cut_in_reason="enter on transferred responsibility", cut_out_reason="leave after the pause settles",
        selected_capsule_ids=("K-DIR-NARRATIVE-FIRST-001",), freedom_corridor=("minor facial timing",),
        decision_id="DEC-TRANSFER",
    )
    vec = VisualExecutionContract(
        contract_id="VEC-TRANSFER", schema_version="1.1", scene_id=scene.scene_id,
        source_fact_hashes=("c" * 64,), phase_a_fingerprint=blocking.phase_a_fingerprint,
        blocking_commit=blocking, visual_curve=curve, decisions=(decision,), segments=(segment,),
        shots=(shot,), boundaries=(), dialogue_events=(dialogue,),
        reference_binding_requirements=(
            ReferenceBindingRequirement("REQ-LIN-ID", "character_identity", "character", "LIN", 100),
            ReferenceBindingRequirement("REQ-LIN-WARDROBE", "wardrobe", "character", "LIN", 100),
            ReferenceBindingRequirement("REQ-ZHAO-ID", "character_identity", "character", "ZHAO", 100),
            ReferenceBindingRequirement("REQ-ZHAO-WARDROBE", "wardrobe", "character", "ZHAO", 100),
            ReferenceBindingRequirement("REQ-KEY", "prop_geometry", "prop", "emergency_key", 80),
            ReferenceBindingRequirement("REQ-SCENE", "scene_layout", "scene", scene.scene_id, 70),
        ),
        final_handoff="text contract requires media validation before acceptance",
    )
    return direction, phase_a, blocking, PhaseBResult(blocking, curve, candidates, (decision,), vec)


def _provider(*, resolved_model=DEFAULT_DEEPSEEK_MODEL):
    direction, phase_a, blocking, phase_b = _outputs()
    responses = [
        json.dumps(asdict(direction), ensure_ascii=False),
        json.dumps(asdict(phase_a), ensure_ascii=False),
        json.dumps(asdict(blocking), ensure_ascii=False),
        json.dumps(_phase_b_execution_wire(phase_b), ensure_ascii=False),
    ]
    client = FixtureTextClient(responses, resolved_model=resolved_model)
    return DeepSeekDirectorProvider(
        client,
        director_id="director-vnext1-deepseek",
    ), client


def _phase_b_execution_wire(phase_b: PhaseBResult):
    """Serialize only the B1-owned fields; B0 is locally materialized."""

    value = asdict(phase_b)
    visual_execution_draft = dict(value["visual_execution_contract"])
    visual_execution_draft.pop("blocking_commit")
    return {
        "visual_curve": value["visual_curve"],
        "candidates": value["candidates"],
        "decisions": value["decisions"],
        "visual_execution_draft": visual_execution_draft,
    }


def test_unknown_script_shadow_runs_e0_through_b1_as_text_only(tmp_path):
    provider, client = _provider()
    evidence = run_unknown_script_text_shadow(
        provider=provider,
        output_root=tmp_path,
        run_id="shadow-unknown-001",
    )
    assert evidence["case_id"] == UNKNOWN_SCRIPT_CASE_ID
    assert evidence["claim_ceiling"] == "TEXT_VALIDATED"
    assert [item["stage"] for item in evidence["model_calls"]] == ["E0", "S1", "B0", "B1"]
    assert evidence["media"]["frames_inspected_by_deepseek"] == 0
    assert evidence["media"]["visual_acceptance"] is False
    assert client.requests and all(item["thinking_enabled"] for item in client.requests)
    assert (tmp_path / "shadow-unknown-001" / "TEXT_SHADOW_EVIDENCE.json").is_file()


def test_shadow_persists_e0_s1_and_b0_checkpoints_when_b1_fails(tmp_path):
    direction, phase_a, blocking, _ = _outputs()
    provider = DeepSeekDirectorProvider(
        FixtureTextClient(
            [
                json.dumps(asdict(direction)),
                json.dumps(asdict(phase_a)),
                json.dumps(asdict(blocking)),
                json.dumps({"bad": "B1 output"}),
            ]
        ),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    with pytest.raises(DeepSeekProviderError):
        run_unknown_script_text_shadow(
            provider=provider,
            output_root=tmp_path,
            run_id="shadow-failed-b1",
        )
    run_dir = tmp_path / "shadow-failed-b1"
    assert (run_dir / "CHECKPOINT_E0_S1.json").is_file()
    assert (run_dir / "CHECKPOINT_B0_K2.json").is_file()
    b0_checkpoint = json.loads((run_dir / "CHECKPOINT_B0_K2.json").read_text())
    assert b0_checkpoint["blocking_commit"]["beats"]
    failure = json.loads((run_dir / "FAILED_TEXT_SHADOW.json").read_text())
    assert failure["status"] == "FAILED_TEXT_ONLY"
    assert failure["media_visual_acceptance"] is False


def test_provider_rejects_wrong_model_unknown_fields_and_visual_claims():
    direction, *_ = _outputs()
    bad_payload = asdict(direction) | {"chain_of_thought": "hidden"}
    provider = DeepSeekDirectorProvider(
        FixtureTextClient([json.dumps(bad_payload)]),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    episode, _ = unknown_script_case()
    with pytest.raises(DeepSeekProviderError, match="unknown contract fields"):
        provider.create_episode_direction(episode)

    visual_provider = DeepSeekDirectorProvider(
        FixtureTextClient([json.dumps(asdict(direction)) + " visually verified" ]),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    with pytest.raises(DeepSeekProviderError, match="visual media verification"):
        visual_provider.create_episode_direction(episode)

    model_provider = DeepSeekDirectorProvider(
        FixtureTextClient([json.dumps(asdict(direction))], resolved_model="other-model"),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    with pytest.raises(DeepSeekProviderError, match="resolved model"):
        model_provider.create_episode_direction(episode)


def test_provider_records_one_bounded_contract_repair_without_raw_output():
    direction, *_ = _outputs()
    invalid = asdict(direction) | {"unknown": "not allowed"}
    provider = DeepSeekDirectorProvider(
        FixtureTextClient([json.dumps(invalid), json.dumps(asdict(direction))]),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=1,
    )
    episode, _ = unknown_script_case()
    assert provider.create_episode_direction(episode) == direction
    records = provider.call_records
    assert [(item.attempt, item.accepted) for item in records] == [(1, False), (2, True)]
    assert records[0].rejection_reason.startswith("$ contains unknown")
    assert "unknown" not in records[0].response_sha256
    assert records[0].prompt_chars > 0
    assert records[0].schema_chars > 0
    assert records[0].schema_transport == "stdin_contract_shape"


def test_stage_messages_lock_exact_top_level_contract_fields():
    episode, _ = unknown_script_case()
    messages = build_stage_messages(
        stage="E0",
        contract_type=EpisodeDirectionState,
        approved_input={
            "director_id": "director-vnext1-deepseek",
            "episode_request": asdict(episode),
        },
        include_contract_shape=True,
    )
    payload = json.loads(messages[1]["content"])
    expected = [
        "character_arc",
        "director_id",
        "episode_id",
        "information_priorities",
        "thematic_axis",
        "visual_development_goal",
    ]
    assert payload["exact_output_field_lock"] == {
        "allowed_top_level_fields": expected,
        "required_top_level_fields": expected,
        "additional_top_level_fields_forbidden": True,
        "top_level_json_types": {
            "character_arc": "array",
            "director_id": "string",
            "episode_id": "string",
            "information_priorities": "array",
            "thematic_axis": "string",
            "visual_development_goal": "string",
        },
    }
    assert sorted(payload["exact_output_shape_lock"]) == expected
    assert payload["required_output_shape"] == {
        "source": "exact_output_shape_lock",
        "locally_enforced": True,
    }

    b0_messages = build_stage_messages(
        stage="B0",
        contract_type=BlockingCommit,
        approved_input={},
        include_contract_shape=False,
    )
    b0_payload = json.loads(b0_messages[1]["content"])
    assert b0_payload["exact_output_enum_lock"][
        "$.beats[].character_states[].screen_position"
    ] == ["offscreen", "screen_center", "screen_left", "screen_right"]
    assert b0_payload["exact_output_enum_lock"]["$.beats[].prop_states[].holder_hand"] == [
        "both",
        "left",
        "none",
        "right",
    ]
    assert "$.beats[].prop_states[].holder_character_id" in b0_payload[
        "exact_identifier_lock"
    ]
    assert b0_payload["exact_cross_field_lock"] == [
        "$.beats[].prop_states[]: holder_hand='none' => holder_character_id='none'",
        "$.beats[].prop_states[]: holder_hand!='none' => holder_character_id equals a $.beats[].character_states[].character_id in the same beat",
    ]

    b1_messages = build_stage_messages(
        stage="B1",
        contract_type=PhaseBExecutionDraft,
        approved_input={},
        include_contract_shape=False,
    )
    b1_payload = json.loads(b1_messages[1]["content"])
    assert b1_payload["exact_cross_field_lock"][0] == (
        "$.visual_execution_draft.segments[].start_tick = 0"
    )
    assert "$.visual_execution_draft.shots[].mirror_flip_forbidden = true" in b1_payload[
        "exact_cross_field_lock"
    ]


def test_b0_repair_names_nonempty_motivated_action_paths():
    _, phase_a, blocking, _ = _outputs()
    _, scene = unknown_script_case()
    invalid = asdict(blocking)
    invalid["beats"][0]["action_paths"] = []
    k1 = DecisionPacket(
        packet_id="K1-test",
        scene_id=scene.scene_id,
        stage="K1",
        primary_capsules=(),
        application_records=(),
        no_match=True,
    )
    client = FixtureTextClient(
        [json.dumps(invalid), json.dumps(asdict(blocking))]
    )
    provider = DeepSeekDirectorProvider(
        client,
        director_id="director-vnext1-deepseek",
        max_contract_repairs=1,
    )
    assert provider.create_blocking_commit(scene, phase_a, k1) == blocking
    assert "action_paths must be a non-empty JSON array" in client.requests[1]["messages"][-1]["content"]
    assert "motivation -> physical action -> spatial/result state" in client.requests[1]["messages"][-1]["content"]
    initial_payload = json.loads(client.requests[0]["messages"][1]["content"])
    assert "phase_a_blocking_scope" in initial_payload["approved_input"]
    assert "phase_a" not in initial_payload["approved_input"]
    assert initial_payload["approved_input"]["phase_a_blocking_scope"]["must_preserve"]
    action_schema = strict_json_schema(
        BlockingCommit,
        max_string_length=180,
    )["properties"]["beats"]["items"]["properties"]["action_paths"]["items"]
    assert action_schema["maxLength"] == 180


def test_b0_rejects_overlong_serialized_text_before_acceptance():
    _, phase_a, blocking, _ = _outputs()
    _, scene = unknown_script_case()
    invalid = asdict(blocking)
    invalid["beats"][0]["dramatic_reason"] = "x" * 181
    k1 = DecisionPacket(
        packet_id="K1-budget",
        scene_id=scene.scene_id,
        stage="K1",
        primary_capsules=(),
        application_records=(),
        no_match=True,
    )
    provider = DeepSeekDirectorProvider(
        FixtureTextClient([json.dumps(invalid)]),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    with pytest.raises(DeepSeekProviderError, match="B0 text budget exceeds 180"):
        provider.create_blocking_commit(scene, phase_a, k1)


def test_e0_and_s1_reject_overlong_serialized_text_before_acceptance():
    direction, phase_a, _, _ = _outputs()
    episode, scene = unknown_script_case()
    long_direction = asdict(direction)
    long_direction["thematic_axis"] = "x" * 181
    e0_provider = DeepSeekDirectorProvider(
        FixtureTextClient([json.dumps(long_direction)]),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    with pytest.raises(DeepSeekProviderError, match="E0 text budget exceeds 180"):
        e0_provider.create_episode_direction(episode)

    long_phase_a = asdict(phase_a)
    long_phase_a["scene_intent"]["scene_objective"] = "x" * 181
    s1_provider = DeepSeekDirectorProvider(
        FixtureTextClient([json.dumps(long_phase_a)]),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    # Invoke S1 directly to prove the stage budget, without accepting a
    # fabricated EpisodeDirection through another call.
    with pytest.raises(DeepSeekProviderError, match="S1 text budget exceeds 180"):
        s1_provider.analyse_scene_phase_a(scene, direction)


def test_shadow_resumes_from_accepted_e0_s1_without_repeating_model_calls(tmp_path):
    direction, phase_a, blocking, phase_b = _outputs()
    invalid_blocking = asdict(blocking)
    invalid_blocking["beats"][0]["action_paths"] = []
    first_provider = DeepSeekDirectorProvider(
        FixtureTextClient(
            [
                json.dumps(asdict(direction)),
                json.dumps(asdict(phase_a)),
                json.dumps(invalid_blocking),
            ]
        ),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    with pytest.raises(DeepSeekProviderError, match="motivated action paths"):
        run_unknown_script_text_shadow(
            provider=first_provider,
            output_root=tmp_path,
            run_id="shadow-resume-b0",
        )
    checkpoint = json.loads(
        (tmp_path / "shadow-resume-b0" / "CHECKPOINT_E0_S1.json").read_text()
    )
    assert checkpoint["phase_a"]["problem_set"]["problems"]

    resumed_client = FixtureTextClient(
        [json.dumps(asdict(blocking)), json.dumps(_phase_b_execution_wire(phase_b))]
    )
    resumed_provider = DeepSeekDirectorProvider(
        resumed_client,
        director_id="director-vnext1-deepseek",
    )
    evidence = run_unknown_script_text_shadow(
        provider=resumed_provider,
        output_root=tmp_path,
        run_id="shadow-resume-b0",
        resume=True,
    )
    stages = [
        json.loads(request["messages"][1]["content"])["stage"]
        for request in resumed_client.requests
    ]
    assert stages == ["B0", "B1"]
    assert evidence["accepted_stage_sequence"] == ["E0", "S1", "B0", "B1"]
    assert any(
        call["stage"] == "B0" and not call["accepted"]
        for call in evidence["model_calls"]
    )


def test_shadow_resumes_from_e0_checkpoint_without_repeating_e0(tmp_path):
    direction, phase_a, blocking, phase_b = _outputs()
    first_provider = DeepSeekDirectorProvider(
        FixtureTextClient(
            [
                json.dumps(asdict(direction)),
                json.dumps({"bad": "S1 output"}),
            ]
        ),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    with pytest.raises(DeepSeekProviderError):
        run_unknown_script_text_shadow(
            provider=first_provider,
            output_root=tmp_path,
            run_id="shadow-resume-s1",
        )
    run_dir = tmp_path / "shadow-resume-s1"
    assert (run_dir / "CHECKPOINT_E0.json").is_file()
    assert not (run_dir / "CHECKPOINT_E0_S1.json").exists()

    resumed_client = FixtureTextClient(
        [
            json.dumps(asdict(phase_a)),
            json.dumps(asdict(blocking)),
            json.dumps(_phase_b_execution_wire(phase_b)),
        ]
    )
    evidence = run_unknown_script_text_shadow(
        provider=DeepSeekDirectorProvider(
            resumed_client,
            director_id="director-vnext1-deepseek",
        ),
        output_root=tmp_path,
        run_id="shadow-resume-s1",
        resume=True,
    )
    stages = [
        json.loads(request["messages"][1]["content"])["stage"]
        for request in resumed_client.requests
    ]
    assert stages == ["S1", "B0", "B1"]
    assert evidence["accepted_stage_sequence"] == ["E0", "S1", "B0", "B1"]


def test_shadow_resumes_from_b0_k2_checkpoint_with_b1_only(tmp_path):
    direction, phase_a, blocking, phase_b = _outputs()
    first_provider = DeepSeekDirectorProvider(
        FixtureTextClient(
            [
                json.dumps(asdict(direction)),
                json.dumps(asdict(phase_a)),
                json.dumps(asdict(blocking)),
                json.dumps({"bad": "B1 output"}),
            ]
        ),
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    with pytest.raises(DeepSeekProviderError):
        run_unknown_script_text_shadow(
            provider=first_provider,
            output_root=tmp_path,
            run_id="shadow-resume-b1",
        )
    resumed_client = FixtureTextClient([json.dumps(_phase_b_execution_wire(phase_b))])
    evidence = run_unknown_script_text_shadow(
        provider=DeepSeekDirectorProvider(
            resumed_client,
            director_id="director-vnext1-deepseek",
        ),
        output_root=tmp_path,
        run_id="shadow-resume-b1",
        resume=True,
    )
    stages = [
        json.loads(request["messages"][1]["content"])["stage"]
        for request in resumed_client.requests
    ]
    assert stages == ["B1"]
    assert evidence["accepted_stage_sequence"] == ["E0", "S1", "B0", "B1"]


def test_transport_timeout_is_recorded_once_and_never_spends_a_contract_repair():
    client = FailingTextClient()
    provider = DeepSeekDirectorProvider(
        client,
        director_id="director-vnext1-deepseek",
        max_contract_repairs=1,
    )
    episode, _ = unknown_script_case()
    with pytest.raises(DeepSeekProviderError, match="synthetic transport timeout"):
        provider.create_episode_direction(episode)
    assert client.calls == 1
    record = provider.call_records[0]
    assert record.stage == "E0" and record.accepted is False
    assert record.response_sha256 == ""


def test_fast_native_schema_exit_retries_once_with_stdin_contract_shape():
    direction, *_ = _outputs()
    client = NativeSchemaFallbackClient(json.dumps(asdict(direction)))
    provider = DeepSeekDirectorProvider(
        client,
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    episode, _ = unknown_script_case()
    assert provider.create_episode_direction(episode) == direction
    assert [request["json_schema"] is None for request in client.requests] == [False, True]
    assert [(record.attempt, record.accepted) for record in provider.call_records] == [(1, False), (1, True)]


def test_fast_native_schema_nonstandard_envelope_retries_once_with_stdin_contract_shape():
    direction, *_ = _outputs()
    client = NativeSchemaFallbackClient(
        json.dumps(asdict(direction)),
        native_failure="Claude Code did not return a valid JSON result envelope; stdout_shape=text_chars=1028",
    )
    provider = DeepSeekDirectorProvider(
        client,
        director_id="director-vnext1-deepseek",
        max_contract_repairs=0,
    )
    episode, _ = unknown_script_case()
    assert provider.create_episode_direction(episode) == direction
    assert [request["json_schema"] is None for request in client.requests] == [False, True]
    assert [(record.attempt, record.accepted) for record in provider.call_records] == [(1, False), (1, True)]


def test_claude_code_transport_locks_model_and_transmits_text_only():
    direction, *_ = _outputs()
    calls = []

    def _runner(argv, **kwargs):
        calls.append((argv, kwargs))
        payload = {
            "is_error": False,
            "session_id": "cli-session-1",
            "result": json.dumps(asdict(direction)),
            "usage": {
                "input_tokens": 12,
                "output_tokens": 8,
                "cache_read_input_tokens": 4,
            },
            "modelUsage": {
                "deepseek-v4-pro": {
                    "canonicalModel": "deepseek-v4-pro"
                }
            },
        }
        return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

    provider = DeepSeekDirectorProvider(
        ClaudeCodeDeepSeekTextClient(
            executable="claude",
            cwd="D:/tsc/导演系统_v5/01_调度器",
            runner=_runner,
        ),
        director_id="director-vnext1-deepseek",
    )
    episode, _ = unknown_script_case()
    result = provider.create_episode_direction(episode)
    assert result == direction
    argv, kwargs = calls[0]
    assert "--model" in argv and argv[argv.index("--model") + 1] == "deepseek-v4-pro"
    assert "--permission-mode" in argv and argv[argv.index("--permission-mode") + 1] == "bypassPermissions"
    assert "--tools" in argv and argv[argv.index("--tools") + 1] == ""
    assert "--disable-slash-commands" in argv
    assert "--safe-mode" in argv
    assert "--no-session-persistence" in argv
    assert "--system-prompt" in argv
    assert "You have no tools" in argv[argv.index("--system-prompt") + 1]
    assert "--file" not in argv
    assert "--no-chrome" in argv
    assert "--json-schema" in argv
    assert kwargs["input"].startswith("[USER]")
    assert "[SYSTEM]" not in kwargs["input"]


def test_claude_code_transport_only_unwraps_a_standalone_json_fence():
    direction, *_ = _outputs()

    def _runner(argv, **_kwargs):
        payload = {
            "is_error": False,
            "session_id": "cli-session-2",
            "result": "```json\n" + json.dumps(asdict(direction)) + "\n```",
            "usage": {},
            "modelUsage": {
                "deepseek-v4-pro": {"canonicalModel": "deepseek-v4-pro"}
            },
        }
        return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

    client = ClaudeCodeDeepSeekTextClient(runner=_runner)
    response = client.complete(
        model="deepseek-v4-pro",
        messages=({"role": "system", "content": "s"}, {"role": "user", "content": "u"}),
        temperature=0.1,
        max_tokens=100,
        thinking_enabled=True,
    )
    assert json.loads(response.content)["episode_id"] == "UNK-E01"
    assert response.transport_normalization == "cli_standalone_json_fence"
    raw, marker = client._unwrap_standalone_json_fence("text ```json {} ```")
    assert raw == "text ```json {} ```" and marker == ""
    raw, marker = client._unwrap_standalone_json_fence(
        "<think>private reasoning</think>\n{\"episode_id\":\"UNK-E01\"}"
    )
    assert raw == '{"episode_id":"UNK-E01"}'
    assert marker == "cli_leading_think_block_discarded"
    raw, marker = client._unwrap_standalone_json_fence(
        "before <think>private reasoning</think>\n{\"episode_id\":\"UNK-E01\"}"
    )
    assert raw.startswith("before ") and marker == ""
    assert client._classify_nonzero_cli_output("server rate limit") == "rate_limited"
    assert client._classify_nonzero_cli_output("invalid JSON Schema") == "schema_rejected"
    assert client._classify_nonzero_cli_output(
        '{"api_error_status":402,"result":"permission wording"}'
    ) == "billing_or_credit_required"
    assert "api_error_status=402" in client._nonzero_stdout_shape(
        '{"api_error_status":402,"is_error":true,"result":"denied"}'
    )
    assert "type=result" in client._nonzero_stdout_shape(
        '{"is_error":false,"type":"result","subtype":"success","result":"{}"}'
    )


def test_claude_code_transport_accepts_plain_direct_contract_json_only():
    direction, *_ = _outputs()

    def _runner(argv, **_kwargs):
        return subprocess.CompletedProcess(
            argv,
            0,
            json.dumps(asdict(direction)),
            "",
        )

    client = ClaudeCodeDeepSeekTextClient(runner=_runner)
    response = client.complete(
        model="deepseek-v4-pro",
        messages=(
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
        ),
        temperature=0.1,
        max_tokens=100,
        thinking_enabled=True,
    )
    assert json.loads(response.content) == json.loads(json.dumps(asdict(direction)))
    assert response.resolved_model == "deepseek-v4-pro"
    assert response.transport_normalization == "cli_direct_contract_json"


def test_claude_code_transport_accepts_only_a_standalone_fenced_direct_contract():
    direction, *_ = _outputs()

    def _runner(argv, **_kwargs):
        return subprocess.CompletedProcess(
            argv,
            0,
            "```json\n" + json.dumps(asdict(direction)) + "\n```",
            "",
        )

    client = ClaudeCodeDeepSeekTextClient(runner=_runner)
    response = client.complete(
        model="deepseek-v4-pro",
        messages=(
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
        ),
        temperature=0.1,
        max_tokens=100,
        thinking_enabled=True,
    )
    assert json.loads(response.content) == json.loads(json.dumps(asdict(direction)))
    assert response.transport_normalization == (
        "cli_direct_contract_json+cli_standalone_json_fence"
    )


def test_decoupled_b1_schema_uses_compact_native_transport_schema():
    _, phase_a, blocking, phase_b = _outputs()
    _, scene = unknown_script_case()
    calls = []

    def _runner(argv, **kwargs):
        calls.append((argv, kwargs))
        payload = {
            "is_error": False,
            "session_id": "cli-session-b1",
            "result": json.dumps(_phase_b_execution_wire(phase_b)),
            "usage": {},
            "modelUsage": {
                "deepseek-v4-pro": {"canonicalModel": "deepseek-v4-pro"}
            },
        }
        return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

    k1 = DecisionPacket(
        packet_id="K1-large",
        scene_id=scene.scene_id,
        stage="K1",
        primary_capsules=(),
        application_records=(),
        no_match=True,
    )
    k2 = DecisionPacket(
        packet_id="K2-large",
        scene_id=scene.scene_id,
        stage="K2",
        primary_capsules=(),
        application_records=(),
        blocking_commit_id=blocking.commit_id,
        no_match=True,
    )
    provider = DeepSeekDirectorProvider(
        ClaudeCodeDeepSeekTextClient(runner=_runner),
        director_id="director-vnext1-deepseek",
    )
    assert provider.design_phase_b(scene, phase_a, blocking, k1, k2) == phase_b
    argv, kwargs = calls[0]
    assert "--json-schema" in argv
    native_schema = json.loads(argv[argv.index("--json-schema") + 1])
    assert "blocking_commit" not in native_schema["properties"]
    assert "blocking_commit" not in native_schema["properties"]["visual_execution_draft"]["properties"]
    assert '"exact_output_shape_lock"' in kwargs["input"]
    assert '"required_output_shape"' not in kwargs["input"]
    payload = json.loads(kwargs["input"].split("\n", 1)[1])
    required_bindings = payload["approved_input"]["required_reference_bindings"]
    assert {item["role"] for item in required_bindings} >= {
        "character_identity",
        "wardrobe",
        "prop_geometry",
        "scene_layout",
    }
    assert provider.call_records[0].schema_transport == "native_argv"


def test_native_schema_carries_contract_enums_not_just_json_types():
    schema = strict_json_schema(PhaseAResult)
    priority = schema["properties"]["problem_set"]["properties"]["problems"]["items"]["properties"]["priority"]
    assert priority["enum"] == ["normal", "high"]


def test_native_b1_schema_locks_every_shot_to_no_mirror_flip():
    schema = strict_json_schema(PhaseBExecutionDraft)
    mirror_lock = schema["properties"]["visual_execution_draft"]["properties"][
        "shots"
    ]["items"]["properties"]["mirror_flip_forbidden"]
    assert mirror_lock == {"enum": [True]}


def test_native_schema_rejects_empty_required_b0_collections_before_local_decode():
    schema = strict_json_schema(BlockingCommit)
    beat = schema["properties"]["beats"]["items"]
    assert schema["properties"]["beats"]["minItems"] == 1
    assert beat["properties"]["action_paths"]["minItems"] == 1
    assert beat["properties"]["character_states"]["minItems"] == 1
    assert beat["properties"]["constraint_refs"]["minItems"] == 1
