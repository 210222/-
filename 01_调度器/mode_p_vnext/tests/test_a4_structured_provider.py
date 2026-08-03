"""A4 acceptance tests for declarative prompts and structured text transport."""

from __future__ import annotations

import json
import subprocess
from dataclasses import fields

import pytest

from mode_p_vnext.adapters.model.claude_deepseek import (
    ClaudeDeepSeekStructuredAdapter,
    ClaudeCodeNativeRunner,
    ProviderCapabilities,
    StructuredTransportRequest,
    resolve_windows_claude_binary,
)
from mode_p_vnext.ports.structured_text import (
    CapabilityUnsupportedError,
    ContractPatch,
    GenerationPolicy,
    RepairBudget,
    Violation,
    ViolationSet,
)
from mode_p_vnext.prompts.budgets import BudgetReport, PromptBudgetExceeded, PromptBudgetGate
from mode_p_vnext.prompts.compiler import CompiledPrompt, PromptCompiler
from mode_p_vnext.prompts.schema_registry import DraftSchemaRegistry
from mode_p_vnext.prompts.signatures import Stage, stage_signatures


def _assert_schema_node_matches_dataclass(schema: dict, draft_type: type) -> None:
    expected = {field.name for field in fields(draft_type)}
    assert set(schema["properties"]) == expected
    assert set(schema["required"]) == expected


def _b1_payload() -> dict:
    return {
        "curve_points": [
            {"dramatic_beat_ordinal": 1, "intensity": 56, "explanation": "The offer lands."}
        ],
        "decisions": [
            {
                "scope": "attention",
                "basis": "choice",
                "locked_by": [],
                "options": ["the hand", "the face"],
                "selected_index": 0,
                "rationale": "The hand carries the offer.",
                "tradeoff": "The reaction is held for the next beat.",
            }
        ],
        "shots": [
            {
                "shot_ordinal": 1,
                "blocking_beat_ordinal": 1,
                "duration_intent": "standard",
                "generation_mode": "text_only",
                "composition": "medium two-shot",
                "camera": "still at eye line",
                "lighting": "soft side light",
                "performance": "a restrained pause",
                "visual_beats": [
                    {
                        "visual_beat_ordinal": 1,
                        "phase": "action",
                        "subject_state": "the envelope is held out",
                        "attention": "the offering hand",
                        "storyboard_role": "required",
                    }
                ],
                "reference_binding_intents": [
                    {
                        "shot_ordinal": 1,
                        "visual_beat_ordinal": None,
                        "fact_handle": "fh:" + "a" * 64,
                        "responsibility": "prop_identity",
                    }
                ],
                "dialogue_binding_intents": [
                    {
                        "shot_ordinal": 1,
                        "visual_beat_ordinal": 1,
                        "fact_handle": "fh:" + "b" * 64,
                        "placement_phase": "middle",
                    }
                ],
                "creative_notes": "Keep the reveal quiet.",
            }
        ],
        "transition_intents": ["hold through the cut"],
        "handoff_intent": "cut to the response",
    }


def test_stage_signatures_declare_creative_stages_and_internal_i0_ingest() -> None:
    signatures = stage_signatures()
    assert set(signatures) == {Stage.I0, Stage.E0, Stage.S1, Stage.B0, Stage.B1}
    i0 = signatures[Stage.I0]
    assert i0.contract_name == "FactExtractionDraft"
    assert i0.prompt_budget == 6_000
    assert i0.schema_budget == 2_500
    assert "fact IDs" in i0.output_exclusions
    assert "creative decisions" in i0.output_exclusions
    assert signatures[Stage.E0].prompt_budget == 6_000
    assert signatures[Stage.S1].schema_budget == 3_500
    assert signatures[Stage.B0].prompt_budget == 10_000
    b1 = signatures[Stage.B1]
    assert b1.prompt_budget == 12_000
    assert b1.schema_budget == 4_500
    assert "final VEC" in b1.output_exclusions
    assert "absolute ticks" in b1.output_exclusions


def test_i0_fact_extraction_is_schema_separated_and_not_a_director_call() -> None:
    compiler = PromptCompiler()
    registry = DraftSchemaRegistry()
    signature = stage_signatures()[Stage.I0]
    compiled = compiler.compile(
        signature,
        {
            "normalized_source": "周从文把手机放在桌上。",
            "source_digest": "a" * 64,
            "source_start": 0,
            "source_end": 12,
        },
    )
    schema = registry.schema_for(signature)
    fact = schema.document["properties"]["facts"]["items"]

    assert schema.document["title"] == "FactExtractionDraft"
    assert schema.character_count <= signature.schema_budget
    assert set(fact["properties"]) == {
        "source_start", "source_end", "semantic_type", "statement",
        "subject_id", "spoken_text",
    }
    assert set(fact["required"]) == {
        "source_start", "source_end", "semantic_type", "statement",
    }
    assert "fact_id" not in fact["properties"]
    assert "scene_hint" not in fact["properties"]
    assert schema.canonical_json not in compiled.prompt_text
    assert "MODE:P Director" not in compiled.system_message
    assert "creative decisions" in compiled.system_message
    assert "local scene partition" in compiled.system_message
    assert "optional scene hints" not in compiled.user_message
    assert "scene or partition identifiers" in signature.output_exclusions


def test_prompt_transports_only_contract_identity_while_schema_stays_separate() -> None:
    compiler = PromptCompiler()
    registry = DraftSchemaRegistry()
    signature = stage_signatures()[Stage.B1]
    compiled = compiler.compile(
        signature,
        {
            "scene_id": "EP35-S2",
            "blocking_summary": "The invitation changes the relationship.",
            "knowledge_view": [{"question": "Where should attention land?"}],
        },
    )
    schema = registry.schema_for(signature)

    assert schema.digest == compiled.schema_digest
    assert schema.canonical_json not in compiled.system_message
    assert schema.canonical_json not in compiled.user_message
    assert "schema_digest" in compiled.user_message
    assert "exact_output_shape_lock" not in compiled.prompt_text
    assert "final VEC" not in compiled.prompt_text
    assert json.loads(schema.canonical_json)["title"] == "ExecutionDesignDraft"


def test_b1_prompt_and_schema_are_preflight_budgeted() -> None:
    compiler = PromptCompiler()
    registry = DraftSchemaRegistry()
    signature = stage_signatures()[Stage.B1]
    compact = compiler.compile(signature, {"scene_id": "EP35-S2"})
    schema = registry.schema_for(signature)

    assert compact.character_count < 12_000
    assert schema.character_count < 4_500
    with pytest.raises(PromptBudgetExceeded, match="B1 prompt"):
        compiler.compile(signature, {"scene_id": "EP35-S2", "scene_intent": "x" * 12_000})


def test_b1_hard_budget_is_an_unreachable_ceiling() -> None:
    """v3.1 §6 requires the B1 prompt body to be `< 12000` and schema `< 4500`.

    Reaching the declared limit must fail closed, so the boundary values
    12000 and 4500 themselves are rejected rather than accepted.
    """

    signature = stage_signatures()[Stage.B1]
    PromptBudgetGate.validate_prompt(signature, "x" * 11_999)
    with pytest.raises(PromptBudgetExceeded, match="B1 prompt"):
        PromptBudgetGate.validate_prompt(signature, "x" * 12_000)
    PromptBudgetGate.validate_schema(signature, "x" * 4_499)
    with pytest.raises(PromptBudgetExceeded, match="B1 schema"):
        PromptBudgetGate.validate_schema(signature, "x" * 4_500)


def test_all_stage_signatures_bind_the_v31_authority_version() -> None:
    """TextCallEvidence.signature_version audits the bound authority version.

    No signature may silently fall back to a pre-v3.1 version.
    """

    assert {sig.stage for sig in stage_signatures().values()} == {
        Stage.I0, Stage.E0, Stage.S1, Stage.B0, Stage.B1,
    }
    for signature in stage_signatures().values():
        assert signature.version == "3.1"


def test_text_call_evidence_records_v31_signature_version() -> None:
    requests = []
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: requests.append(request) or {
            "payload": {
                "dramatic_promise": "Responsibility makes certainty fracture under pressure.",
                "audience_contract": "Each scene reveals a concrete emotional cost.",
                "tension_curve": ["confidence", "pressure"],
                "visual_principles": ["preserve readable action"],
                "continuity_priorities": ["preserve the established screen direction"],
                "unresolved_questions": [],
            },
            "resolved_model": "deepseek-v4-pro",
        },
        executable="claude.exe",
    )
    _, evidence = adapter.generate(
        stage_signatures()[Stage.E0],
        {"episode_id": "EP35"},
        GenerationPolicy(requested_model="deepseek-v4-pro"),
    )
    assert evidence.signature_version == "3.1"


def test_schema_digest_mismatch_fails_before_any_provider_call() -> None:
    """A compiled schema digest that cannot be re-verified is a local failure."""

    calls: list[object] = []
    signature = stage_signatures()[Stage.E0]

    class _TamperedCompiler:
        def compile(self, _signature, _approved_input):
            return CompiledPrompt(
                signature=signature,
                system_message="system",
                user_message="user",
                schema_digest="a" * 64,
                approved_input_digest="b" * 64,
                budget_report=BudgetReport(
                    stage="E0", kind="prompt", character_count=10,
                    hard_limit=signature.prompt_budget, soft_warning=False,
                ),
            )

    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: calls.append(request),
        executable="claude.exe",
        compiler=_TamperedCompiler(),
    )
    with pytest.raises(RuntimeError, match="digest mismatch"):
        adapter.generate(
            signature,
            {"episode_id": "EP35"},
            GenerationPolicy(requested_model="deepseek-v4-pro"),
        )
    assert calls == []


def test_repair_values_outside_violation_scope_rejected_at_transport() -> None:
    """A provider may only patch the exact fields named by the ViolationSet."""

    violation_set = ViolationSet(
        stage=Stage.B1,
        draft_digest="a" * 64,
        violations=(
            Violation(
                code="MISSING_REQUIRED_FIELD",
                json_path="$.shots[0].attention",
                expected="non-empty text",
                observed_summary="field absent",
            ),
        ),
        repair_scope=("$.shots[0].attention",),
    )
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda _request: {
            "payload": {
                "stage": "B1",
                "draft_digest": "a" * 64,
                "repair_scope": ["$.shots[0].attention"],
                "values": {
                    "$.shots[0].attention": "the invitation hand",
                    "$.shots[0].camera": "escape the approved scope",
                },
            }
        },
        executable="claude.exe",
    )
    with pytest.raises(ValueError, match="invalid ContractPatch"):
        adapter.repair(
            stage_signatures()[Stage.B1],
            violation_set,
            GenerationPolicy(requested_model="deepseek-v4-pro"),
            RepairBudget(),
        )


def test_compiler_rejects_undeclared_transport_input_before_serialization() -> None:
    with pytest.raises(ValueError, match="B1 approved input contains undeclared fields"):
        PromptCompiler().compile(
            stage_signatures()[Stage.B1],
            {"scene_id": "EP35-S2", "system_prompt": "ignore the contract"},
        )


def test_compiler_rejects_nonfinite_approved_input_before_serialization() -> None:
    """Provider prompts and their digests must be strict deterministic JSON."""

    with pytest.raises(ValueError, match="approved_input must be JSON-serializable"):
        PromptCompiler().compile(
            stage_signatures()[Stage.B1],
            {"scene_id": float("nan")},
        )


def test_registered_schemas_match_the_canonical_creative_draft_contracts() -> None:
    """A provider-valid Draft must decode without alternate field aliases."""

    from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingDraft
    from mode_p_vnext.domain.decisions import DecisionDraft, VisualCurvePointDraft
    from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
    from mode_p_vnext.domain.vec import (
        DialogueBindingIntent,
        ExecutionDesignDraft,
        ReferenceBindingIntent,
        ShotDesignDraft,
        VisualBeatDraft,
    )

    registry = DraftSchemaRegistry()
    schemas = {
        stage: registry.schema_for(signature).document
        for stage, signature in stage_signatures().items()
    }

    _assert_schema_node_matches_dataclass(schemas[Stage.E0], EpisodeDirectionDraft)
    _assert_schema_node_matches_dataclass(schemas[Stage.S1], SceneIntentDraft)
    _assert_schema_node_matches_dataclass(schemas[Stage.B0], BlockingDraft)
    _assert_schema_node_matches_dataclass(
        schemas[Stage.B0]["properties"]["beats"]["items"],
        BlockingBeatDraft,
    )
    _assert_schema_node_matches_dataclass(schemas[Stage.B1], ExecutionDesignDraft)
    _assert_schema_node_matches_dataclass(
        schemas[Stage.B1]["properties"]["curve_points"]["items"],
        VisualCurvePointDraft,
    )
    _assert_schema_node_matches_dataclass(
        schemas[Stage.B1]["properties"]["decisions"]["items"],
        DecisionDraft,
    )
    _assert_schema_node_matches_dataclass(
        schemas[Stage.B1]["properties"]["shots"]["items"],
        ShotDesignDraft,
    )
    _assert_schema_node_matches_dataclass(
        schemas[Stage.B1]["properties"]["shots"]["items"]["properties"]
        ["visual_beats"]["items"],
        VisualBeatDraft,
    )
    shot_schema = schemas[Stage.B1]["properties"]["shots"]["items"]
    _assert_schema_node_matches_dataclass(
        shot_schema["properties"]["reference_binding_intents"]["items"],
        ReferenceBindingIntent,
    )
    _assert_schema_node_matches_dataclass(
        shot_schema["properties"]["dialogue_binding_intents"]["items"],
        DialogueBindingIntent,
    )
    assert "audio_intents" not in schemas[Stage.B1]["properties"]
    assert "reference_intents" not in schemas[Stage.B1]["properties"]
    assert "start_tick" not in shot_schema["properties"]
    i0_fact = schemas[Stage.I0]["properties"]["facts"]["items"]
    assert i0_fact["additionalProperties"] is False
    assert i0_fact["properties"]["semantic_type"]["enum"] == [
        "narrative", "character", "wardrobe", "prop", "setting",
        "dialogue", "continuity", "asset",
    ]


def test_i0_schema_rejects_non_fact_fields_and_empty_source_statements() -> None:
    from mode_p_vnext.adapters.model.claude_deepseek import (
        _validate_draft_against_schema,
    )

    schema = DraftSchemaRegistry().schema_for(
        stage_signatures()[Stage.I0]
    ).document
    payload = {
        "facts": [
            {
                "source_start": 0,
                "source_end": 7,
                "semantic_type": "prop",
                "statement": "手机在桌上。",
                "subject_id": "prop:phone",
            }
        ]
    }
    _validate_draft_against_schema(payload, schema)

    payload["facts"][0]["fact_id"] = "forbidden"
    with pytest.raises(ValueError, match="unexpected field.*fact_id"):
        _validate_draft_against_schema(payload, schema)
    del payload["facts"][0]["fact_id"]
    payload["facts"][0]["scene_hint"] = "雨后站台"
    with pytest.raises(ValueError, match="unexpected field.*scene_hint"):
        _validate_draft_against_schema(payload, schema)
    del payload["facts"][0]["scene_hint"]
    payload["facts"][0]["statement"] = ""
    with pytest.raises(ValueError, match="too short"):
        _validate_draft_against_schema(payload, schema)


def test_b0_state_maps_reject_values_outside_the_domain_safe_transport_shape() -> None:
    from mode_p_vnext.adapters.model.claude_deepseek import (
        _validate_draft_against_schema,
    )

    schema = DraftSchemaRegistry().schema_for(
        stage_signatures()[Stage.B0]
    ).document
    payload = {
        "beats": [
            {
                "ordinal": 1,
                "dramatic_action": "He holds at the doorway.",
                "character_states": [{"character_id": "chen", "posture": "still"}],
                "prop_states": [],
                "gaze_relations": ["chen -> zhou"],
                "action_paths": ["hold position"],
                "continuity_effect": "The exit direction stays locked.",
            }
        ]
    }
    _validate_draft_against_schema(payload, schema)

    payload["beats"][0]["character_states"][0]["character_id"] = 7
    with pytest.raises(ValueError, match="expected string"):
        _validate_draft_against_schema(payload, schema)


def test_b1_schema_rejects_model_ticks_legacy_text_bindings_and_invalid_handles() -> None:
    from mode_p_vnext.adapters.model.claude_deepseek import (
        _validate_draft_against_schema,
    )

    schema = DraftSchemaRegistry().schema_for(
        stage_signatures()[Stage.B1]
    ).document
    payload = _b1_payload()
    _validate_draft_against_schema(payload, schema)

    with_ticks = json.loads(json.dumps(payload))
    with_ticks["shots"][0]["start_tick"] = 0
    with pytest.raises(ValueError, match="unexpected field.*start_tick"):
        _validate_draft_against_schema(with_ticks, schema)

    legacy_bindings = json.loads(json.dumps(payload))
    legacy_bindings["reference_intents"] = ["bind the envelope"]
    with pytest.raises(ValueError, match="unexpected field.*reference_intents"):
        _validate_draft_against_schema(legacy_bindings, schema)

    invalid_handle = json.loads(json.dumps(payload))
    invalid_handle["shots"][0]["reference_binding_intents"][0]["fact_handle"] = "envelope"
    with pytest.raises(ValueError, match="does not match pattern"):
        _validate_draft_against_schema(invalid_handle, schema)


def test_windows_resolution_prefers_native_executable_over_cmd_shim() -> None:
    resolved = resolve_windows_claude_binary(
        (
            r"C:\\Users\\JT\\AppData\\Roaming\\npm\\claude.cmd",
            r"C:\\Program Files\\Claude\\claude.exe",
        ),
        is_windows=True,
    )
    assert resolved.endswith("claude.exe")
    with pytest.raises(CapabilityUnsupportedError, match="native claude.exe"):
        resolve_windows_claude_binary((r"C:\\npm\\claude.cmd",), is_windows=True)


def test_missing_structured_capability_fails_before_any_model_call() -> None:
    calls: list[object] = []
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: calls.append(request),
        executable="claude.exe",
        capabilities=ProviderCapabilities(native_json_schema=False),
    )
    with pytest.raises(CapabilityUnsupportedError, match="CAPABILITY_UNSUPPORTED"):
        adapter.generate(
            stage_signatures()[Stage.E0],
            {"episode_id": "EP35"},
            GenerationPolicy(requested_model="deepseek-v4-pro"),
        )
    assert calls == []


def test_native_only_adapter_cannot_bypass_schema_requirement_by_policy_flag() -> None:
    """A native-only adapter must fail closed; it has no safe fallback transport."""

    calls: list[object] = []
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: calls.append(request),
        executable="claude.exe",
        capabilities=ProviderCapabilities(native_json_schema=False),
    )
    with pytest.raises(CapabilityUnsupportedError, match="CAPABILITY_UNSUPPORTED"):
        adapter.generate(
            stage_signatures()[Stage.E0],
            {"episode_id": "EP35"},
            GenerationPolicy(
                requested_model="deepseek-v4-pro", require_native_schema=False
            ),
        )
    assert calls == []


def test_schema_is_a_dedicated_transport_field_not_prompt_text() -> None:
    requests = []
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: requests.append(request) or {
            "payload": {
                "dramatic_promise": "Responsibility makes certainty fracture under pressure.",
                "audience_contract": "Each scene reveals a concrete emotional cost.",
                "tension_curve": ["confidence", "pressure"],
                "visual_principles": ["preserve readable action"],
                "continuity_priorities": ["preserve the established screen direction"],
                "unresolved_questions": [],
            },
            "resolved_model": "deepseek-v4-pro",
        },
        executable="claude.exe",
    )
    draft, evidence = adapter.generate(
        stage_signatures()[Stage.E0],
        {"episode_id": "EP35"},
        GenerationPolicy(requested_model="deepseek-v4-pro"),
    )
    request = requests[0]
    assert draft.contract_name == "EpisodeDirectionDraft"
    assert evidence.schema_digest
    assert request.json_schema["title"] == "EpisodeDirectionDraft"
    assert json.dumps(request.json_schema, sort_keys=True) not in request.user_message
    assert request.system_message != request.user_message


def test_schema_contract_is_deeply_immutable_at_registry_and_transport_boundaries() -> None:
    """A runner must not alter the schema whose digest seals the text call."""

    schema = DraftSchemaRegistry().schema_for(stage_signatures()[Stage.E0])
    original_additional_properties = schema.document["additionalProperties"]
    try:
        with pytest.raises(TypeError, match="immutable"):
            schema.document["additionalProperties"] = True
        with pytest.raises(TypeError, match="immutable"):
            schema.document["properties"]["final_vec"] = {"type": "object"}
    finally:
        # The pre-repair registry is mutable.  Restore it even when the new
        # assertions intentionally fail so this regression cannot taint peers.
        try:
            schema.document["additionalProperties"] = original_additional_properties
            schema.document["properties"].pop("final_vec", None)
        except TypeError:
            pass

    repair_schema = DraftSchemaRegistry().repair_schema_for(
        stage_signatures()[Stage.I0]
    )
    with pytest.raises(TypeError, match="immutable"):
        repair_schema.document["properties"]["values"][
            "additionalProperties"
        ] = False

    mutation_blocked: list[bool] = []

    def runner(request: StructuredTransportRequest) -> dict:
        original = request.json_schema["additionalProperties"]
        try:
            request.json_schema["additionalProperties"] = True
        except TypeError:
            mutation_blocked.append(True)
        else:
            mutation_blocked.append(False)
            request.json_schema["additionalProperties"] = original
        return {
            "payload": {
                "dramatic_promise": "Responsibility makes certainty fracture under pressure.",
                "audience_contract": "Each scene reveals a concrete emotional cost.",
                "tension_curve": ["confidence", "pressure"],
                "visual_principles": ["preserve readable action"],
                "continuity_priorities": ["preserve screen direction"],
                "unresolved_questions": [],
            }
        }

    adapter = ClaudeDeepSeekStructuredAdapter(runner=runner, executable="claude.exe")
    draft, evidence = adapter.generate(
        stage_signatures()[Stage.E0],
        {"episode_id": "EP35"},
        GenerationPolicy(requested_model="deepseek-v4-pro"),
    )

    assert mutation_blocked == [True]
    assert draft.contract_name == "EpisodeDirectionDraft"
    assert evidence.schema_digest == schema.digest


def test_i0_uses_the_same_structured_port_without_creative_fields() -> None:
    requests = []
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: requests.append(request) or {
            "payload": {
                "facts": [
                    {
                        "source_start": 0,
                        "source_end": 7,
                        "semantic_type": "prop",
                        "statement": "手机在桌上。",
                        "subject_id": "prop:phone",
                    }
                ]
            },
            "resolved_model": "deepseek-v4-pro",
        },
        executable="claude.exe",
    )
    draft, evidence = adapter.generate(
        stage_signatures()[Stage.I0],
        {"normalized_source": "手机在桌上。", "source_digest": "a" * 64},
        GenerationPolicy(requested_model="deepseek-v4-pro"),
    )

    assert draft.stage is Stage.I0
    assert draft.contract_name == "FactExtractionDraft"
    assert requests[0].json_schema["title"] == "FactExtractionDraft"
    assert evidence.stage is Stage.I0


def test_i0_structured_provider_rejects_model_authored_scene_partition_fields() -> None:
    """Only the local caller may attach an I0 fact to its source partition."""

    requests = []
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: requests.append(request) or {
            "payload": {
                "facts": [
                    {
                        "source_start": 0,
                        "source_end": 7,
                        "semantic_type": "prop",
                        "statement": "手机在桌上。",
                        "subject_id": "prop:phone",
                        "scene_hint": "雨后站台",
                    }
                ]
            }
        },
        executable="claude.exe",
    )

    with pytest.raises(ValueError, match="unexpected field.*scene_hint"):
        adapter.generate(
            stage_signatures()[Stage.I0],
            {"normalized_source": "手机在桌上。", "source_digest": "a" * 64},
            GenerationPolicy(requested_model="deepseek-v4-pro"),
        )

    fact_schema = requests[0].json_schema["properties"]["facts"]["items"]
    assert "scene_hint" not in fact_schema["properties"]


def test_adapter_rejects_non_draft_fields_after_structured_transport() -> None:
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda _request: {"payload": {"final_vec": {"forbidden": True}}},
        executable="claude.exe",
    )
    with pytest.raises(ValueError, match="unexpected field.*final_vec"):
        adapter.generate(
            stage_signatures()[Stage.E0],
            {"episode_id": "EP35"},
            GenerationPolicy(requested_model="deepseek-v4-pro"),
        )


def test_native_runner_uses_native_schema_channel_and_no_tools() -> None:
    calls = []

    def fake_subprocess(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(
            argv,
            0,
            json.dumps(
                {
                    "result": json.dumps({"thematic_axis": "responsibility"}),
                    "modelUsage": {"deepseek-v4-pro": {"canonicalModel": "deepseek-v4-pro"}},
                    "usage": {"input_tokens": 7, "output_tokens": 3},
                }
            ),
            "",
        )

    runner = ClaudeCodeNativeRunner(
        executable=r"C:\\Program Files\\Claude\\claude.exe",
        subprocess_runner=fake_subprocess,
    )
    response = runner(
        StructuredTransportRequest(
            executable=r"C:\\Program Files\\Claude\\claude.exe",
            requested_model="deepseek-v4-pro",
            system_message="system contract",
            user_message="compact approved input",
            json_schema={"type": "object", "title": "EpisodeDirectionDraft"},
            temperature=0.2,
            max_output_tokens=1000,
        )
    )
    argv, kwargs = calls[0]
    assert argv[0].endswith("claude.exe")
    assert argv[argv.index("--tools") + 1] == ""
    assert argv[argv.index("--system-prompt") + 1] == "system contract"
    assert json.loads(argv[argv.index("--json-schema") + 1])["title"] == "EpisodeDirectionDraft"
    assert kwargs["input"] == "compact approved input"
    assert response["payload"]["thematic_axis"] == "responsibility"


def test_only_one_whitelisted_contract_patch_can_consume_repair_budget() -> None:
    violation_set = ViolationSet(
        stage=Stage.B1,
        draft_digest="a" * 64,
        violations=(
            Violation(
                code="MISSING_REQUIRED_FIELD",
                json_path="$.shots[0].attention",
                expected="non-empty text",
                observed_summary="field absent",
            ),
        ),
        repair_scope=("$.shots[0].attention",),
    )
    patch = ContractPatch(
        stage=Stage.B1,
        draft_digest="a" * 64,
        repair_scope=("$.shots[0].attention",),
        values={"$.shots[0].attention": "the invitation hand"},
    )
    budget = RepairBudget(maximum=1)
    assert budget.consume(violation_set, patch) == 1
    with pytest.raises(ValueError, match="repair budget exhausted"):
        budget.consume(violation_set, patch)
    with pytest.raises(ValueError, match="outside the approved repair scope"):
        ContractPatch(
            stage=Stage.B1,
            draft_digest="a" * 64,
            repair_scope=("$.shots[0].attention",),
            values={"$.shots[0].camera": "unapproved"},
        )


def test_transport_failure_does_not_consume_the_single_contract_repair() -> None:
    violation_set = ViolationSet(
        stage=Stage.B1,
        draft_digest="a" * 64,
        violations=(Violation("MISSING", "$.handoff_intent", "text", "absent"),),
        repair_scope=("$.handoff_intent",),
    )
    budget = RepairBudget()
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda _request: (_ for _ in ()).throw(ConnectionError("transport down")),
        executable="claude.exe",
    )
    with pytest.raises(ConnectionError, match="transport down"):
        adapter.repair(
            stage_signatures()[Stage.B1],
            violation_set,
            GenerationPolicy(requested_model="deepseek-v4-pro"),
            budget,
        )
    assert budget.used == 0


def test_i0_source_span_repair_uses_one_scoped_patch_transport() -> None:
    violation_set = ViolationSet(
        stage=Stage.I0,
        draft_digest="a" * 64,
        violations=(
            Violation(
                "SOURCE_SPAN_OUT_OF_RANGE",
                "$.facts[0].source_end",
                "end within normalized source",
                "end=99 beyond source length=12",
            ),
        ),
        repair_scope=("$.facts[0].source_end",),
    )
    requests = []
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: requests.append(request) or {
            "payload": {
                "stage": "I0",
                "draft_digest": "a" * 64,
                "repair_scope": ["$.facts[0].source_end"],
                "values": {"$.facts[0].source_end": 12},
            }
        },
        executable="claude.exe",
    )
    budget = RepairBudget()

    patch, evidence = adapter.repair(
        stage_signatures()[Stage.I0],
        violation_set,
        GenerationPolicy(requested_model="deepseek-v4-pro"),
        budget,
    )

    assert patch.values == {"$.facts[0].source_end": 12}
    assert evidence.attempt == 2
    assert requests[0].json_schema["title"] == "ContractPatch"
    assert "FactExtractionDraft" not in requests[0].user_message
    with pytest.raises(ValueError, match="repair budget exhausted"):
        adapter.repair(
            stage_signatures()[Stage.I0],
            violation_set,
            GenerationPolicy(requested_model="deepseek-v4-pro"),
            budget,
        )
    assert len(requests) == 1


def test_i0_contract_repair_cannot_escape_the_source_span_ceiling() -> None:
    with pytest.raises(ValueError, match="limited to source_start/source_end"):
        ViolationSet(
            stage=Stage.I0,
            draft_digest="a" * 64,
            violations=(Violation("EMPTY", "$.facts[0].statement", "text", "empty"),),
            repair_scope=("$.facts[0].statement",),
        )
