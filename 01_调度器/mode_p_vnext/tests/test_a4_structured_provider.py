"""A4 acceptance tests for declarative prompts and structured text transport."""

from __future__ import annotations

import json
import subprocess

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
from mode_p_vnext.prompts.budgets import PromptBudgetExceeded
from mode_p_vnext.prompts.compiler import PromptCompiler
from mode_p_vnext.prompts.schema_registry import DraftSchemaRegistry
from mode_p_vnext.prompts.signatures import Stage, stage_signatures


def test_stage_signatures_declare_the_only_four_model_stages() -> None:
    signatures = stage_signatures()
    assert set(signatures) == {Stage.E0, Stage.S1, Stage.B0, Stage.B1}
    assert signatures[Stage.E0].prompt_budget == 6_000
    assert signatures[Stage.S1].schema_budget == 3_500
    assert signatures[Stage.B0].prompt_budget == 10_000
    b1 = signatures[Stage.B1]
    assert b1.prompt_budget == 12_000
    assert b1.schema_budget == 4_500
    assert "final VEC" in b1.output_exclusions
    assert "absolute ticks" in b1.output_exclusions


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

    assert compact.character_count <= 12_000
    assert schema.character_count <= 4_500
    with pytest.raises(PromptBudgetExceeded, match="B1 prompt"):
        compiler.compile(signature, {"scene_id": "EP35-S2", "oversized": "x" * 12_000})


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


def test_schema_is_a_dedicated_transport_field_not_prompt_text() -> None:
    requests = []
    adapter = ClaudeDeepSeekStructuredAdapter(
        runner=lambda request: requests.append(request) or {
            "payload": {
                "thematic_axis": "responsibility",
                "dramatic_direction": "certainty fractures under pressure",
                "visual_principles": ["preserve readable action"],
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
    patch = ContractPatch(
        stage=Stage.B1,
        draft_digest="a" * 64,
        repair_scope=("$.handoff_intent",),
        values={"$.handoff_intent": "hold on the decision"},
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
            patch,
            GenerationPolicy(requested_model="deepseek-v4-pro"),
            budget,
        )
    assert budget.used == 0
