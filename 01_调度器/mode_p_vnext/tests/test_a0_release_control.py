"""A0 freezes one architecture-v3.0 construction ledger and v4 safety."""

from __future__ import annotations

import fnmatch
import hashlib
import json

import pytest

from mode_p_vnext.director_vnext1.completion_control import CompletionControl
from mode_p_vnext.director_vnext1.control import DirectorDdoControl
from mode_p_vnext.feature_gate import FeatureGate
from mode_p_vnext.rebuild_control import (
    ControlError,
    RebuildControl,
    _sha256_file,
)
from mode_p_vnext.release_control import (
    ReleaseControl,
    _claim_summary,
    _patterns_overlap,
)


ARCHITECTURE_REL = (
    "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
    "MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0.md"
)
ARCHITECTURE_BUNDLE = {ARCHITECTURE_REL}
AUTHORITY_MARKER = "MODE_P_VNEXT_AUTHORITY: architecture-v3.0"


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def test_release_ledger_is_the_single_v3_task_selector():
    control = ReleaseControl.default()
    tasks = control.load_tasks()
    assert [task.task_id for task in tasks] == [
        "A0",
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
        "A8",
        "A9",
        "A10",
    ]
    assert tasks[0].depends_on == ()
    for previous, current in zip(tasks, tasks[1:]):
        assert current.depends_on == (previous.task_id,)

    assert control.tasks_path != RebuildControl.default().tasks_path
    assert control.tasks_path != DirectorDdoControl.default().tasks_path
    assert control.tasks_path != CompletionControl.default().tasks_path
    assert control.state_path != RebuildControl.default().state_path
    assert control.state_path != DirectorDdoControl.default().state_path
    assert control.state_path != CompletionControl.default().state_path
    assert control.lock_path != RebuildControl.default().lock_path
    assert control.lock_path != DirectorDdoControl.default().lock_path
    assert control.lock_path != CompletionControl.default().lock_path


def test_release_registry_matches_architecture_work_packages_and_phases():
    control = ReleaseControl.default()
    document = _read_json(control.tasks_path)
    assert document["schema_version"] == "2.0"
    assert document["architecture_version"] == "3.0"
    assert document["authority"] == "SOLE_VNEXT_CONSTRUCTION_LEDGER"
    assert document["terminal_claim_ceiling"] == "OWNER_APPROVED_PREVIEW"
    assert document["status_after_all"] == "PRODUCTION_SWITCH_PROPOSAL_ELIGIBLE"

    phases = {task["task_id"]: task["phase"] for task in document["tasks"]}
    assert phases == {
        "A0": "BASELINE_REPAIR",
        "A1": "ARCHITECTURE_MIGRATION",
        "A2": "ARCHITECTURE_MIGRATION",
        "A3": "ARCHITECTURE_MIGRATION",
        "A4": "ARCHITECTURE_MIGRATION",
        "A5": "ARCHITECTURE_MIGRATION",
        "A6": "ARCHITECTURE_MIGRATION",
        "A7": "ARCHITECTURE_MIGRATION",
        "A8": "TEXT_SHADOW",
        "A9": "HOLDOUT_EVALUATION",
        "A10": "MEDIA_EVIDENCE",
    }
    assert set(document["locked_verification_inputs"]) == ARCHITECTURE_BUNDLE
    assert all(
        set(task.locked_verification_inputs) == ARCHITECTURE_BUNDLE
        for task in control.load_tasks()
    )
    assert all(
        not ARCHITECTURE_BUNDLE.intersection(task["allowed_paths"])
        for task in document["tasks"]
    )

    pending = {task["task_id"]: task["pending_status"] for task in document["tasks"]}
    assert pending["A0"] == "BASELINE_REPAIR_REQUIRED"
    assert all(
        pending[task_id] == "ARCHITECTURE_MIGRATION_REQUIRED"
        for task_id in ("A1", "A2", "A3", "A4", "A5", "A6", "A7")
    )
    assert pending["A8"] == "TEXT_SHADOW_REQUIRED"
    assert pending["A9"] == "HOLDOUT_EVALUATION_REQUIRED"
    assert pending["A10"] == "MEDIA_EVIDENCE_REQUIRED"

    a4 = next(task for task in document["tasks"] if task["task_id"] == "A4")
    assert "b1_prompt_under_12000_chars" in a4["required_checks"]
    assert "b1_schema_under_4500_chars" in a4["required_checks"]
    assert "i0_fact_extraction_signature" in a4["required_checks"]
    assert "model_does_not_mint_ids_or_ticks" in a4["required_checks"]
    assert "typed_binding_intents_in_b1_schema" in a4["required_checks"]
    assert "free_text_not_binding_transport" in a4["required_checks"]
    a5 = next(task for task in document["tasks"] if task["task_id"] == "A5")
    assert "drafts_contain_creative_choices_only" in a5["required_checks"]
    assert "deterministic_vec_rebuild" in a5["required_checks"]
    assert "typed_reference_binding" in a5["required_checks"]
    assert "typed_dialogue_audio_binding" in a5["required_checks"]
    assert "no_fact_id_or_statement_parsing" in a5["required_checks"]
    assert "per_shot_generation_cap" in a5["required_checks"]
    assert "scene_duration_not_capped_at_15s" in a5["required_checks"]
    assert "dialogue_phase_tick_placement" in a5["required_checks"]
    assert "source_span_never_used_as_timing" in a5["required_checks"]
    assert "requirements_bound_to_shot_or_beat" in a5["required_checks"]
    assert "free_text_intents_not_bound" in a5["required_checks"]

    a1 = next(task for task in document["tasks"] if task["task_id"] == "A1")
    assert {
        "normalized_source_contract",
        "local_fact_assembler_ownership",
        "typed_fact_semantics",
        "opaque_fact_handles_and_ids",
        "source_span_provenance_only",
        "generation_capability_profile",
        "duration_intent_not_raw_ticks",
        "typed_reference_binding_intent",
        "typed_dialogue_binding_intent",
    }.issubset(a1["required_checks"])
    assert {
        "01_调度器/mode_p_vnext/services/source_normalizer.py",
        "01_调度器/mode_p_vnext/services/fact_assembler.py",
    }.issubset(a1["allowed_paths"])

    a0 = next(task for task in document["tasks"] if task["task_id"] == "A0")
    assert "single_architecture_document_locked" in a0["required_checks"]
    assert "v23_rejected_as_historical" in a0["required_checks"]
    assert "active_guidance_version_converged" in a0["required_checks"]
    assert "architecture_drift_blocks_claim" in a0["required_checks"]
    assert "01_调度器/mode_p/test_ep35_s1_pipeline.py" in a0["allowed_paths"]

    a6 = next(task for task in document["tasks"] if task["task_id"] == "A6")
    assert {
        "canonical_projection_type_identity",
        "projection_envelope_roundtrip",
        "no_duplicate_projection_authority",
    }.issubset(a6["required_checks"])
    assert [item["name"] for item in a6["verification_commands"]] == [
        "a6_projection_compiler",
        "a6_v4_isolation",
    ]

    a7 = next(task for task in document["tasks"] if task["task_id"] == "A7")
    assert "canonical_projection_and_evidence_consumption" in a7["required_checks"]
    assert [item["name"] for item in a7["verification_commands"]] == [
        "a7_dual_loop",
        "a7_v4_isolation",
    ]

    a8 = next(task for task in document["tasks"] if task["task_id"] == "A8")
    assert {
        "raw_source_to_fact_registry",
        "canonical_ingest_to_projection",
        "typed_ingest_provenance",
        "complete_v30_state_graph",
        "run_record_digest_tamper_rejected",
        "no_v4_write_or_external_media",
    }.issubset(a8["required_checks"])


def test_a3_exclusively_owns_legacy_knowledge_adapter_migration():
    """The A3 migration owns every legacy source that can mint a K1/K2 snapshot."""
    tasks = ReleaseControl.default().load_tasks()
    a3 = next(task for task in tasks if task.task_id == "A3")

    assert {
        "01_调度器/mode_p_vnext/services/knowledge_retriever.py",
        "01_调度器/mode_p_vnext/knowledge_flow.py",
        "01_调度器/mode_p_vnext/knowledge_snapshot.py",
    }.issubset(a3.allowed_paths)


def test_architecture_bundle_hashes_are_locked_and_current():
    control = ReleaseControl.default()
    document = _read_json(control.tasks_path)
    expected = document["locked_verification_inputs"]
    actual = {
        rel_path: _sha256_file(control.root / rel_path)
        for rel_path in ARCHITECTURE_BUNDLE
    }
    assert expected == actual

    state = control.load_state()
    assert state["architecture_version"] == "3.0"
    assert state["architecture_documents"] == [
        {"path": item["path"], "sha256": item["sha256"]}
        for item in document["architecture_documents"]
    ]
    assert state["architecture_document"] == state["architecture_documents"][-1]


def test_v30_root_contracts_are_explicit_and_fail_closed():
    root = ReleaseControl.default().root
    architecture = (root / ARCHITECTURE_REL).read_text(encoding="utf-8")

    for marker in (
        "NORMATIVE_SINGLE_AUTHORITY",
        "REJECTED_BY_WHOLE_SYSTEM_AUDIT",
        "NormalizedSource",
        "local FactAssembler",
        "FactRegistry",
        "TICKS_PER_SECOND = 24000",
        "一个 `GenerationUnit` 对应一个 `CinematicShot`",
        "Scene/Episode 总时长",
        "MUST NOT 被 15 秒封顶",
        "source_start/source_end",
        "MUST NOT 用于计算 screen time",
        "DialogueBindingIntent",
        "ReferenceBindingIntent",
        "唯一机器绑定输入",
        "每个生成的 ReferenceRequirement/AudioEvent 必须绑定",
        "B1 运行 prompt（不含 schema）必须 `< 12000`",
        "VEC -> ProjectionAST -> StoryboardProjection / VideoProjection",
        "production_entry=v4_unchanged",
    ):
        assert marker in architecture


def test_v23_is_registered_as_rejected_history_not_active_authority():
    control = ReleaseControl.default()
    document = _read_json(control.tasks_path)
    historical = {
        item["version"]: item for item in document["historical_architecture_documents"]
    }
    assert historical["2.3"]["disposition"] == (
        "REJECTED_BY_WHOLE_SYSTEM_AUDIT"
    )
    assert all(
        historical[version]["disposition"] == "HISTORICAL_READ_ONLY"
        for version in ("2.0", "2.1", "2.2")
    )
    assert all(
        "V2." not in item["path"]
        for item in document["architecture_documents"]
    )


def test_legacy_queues_are_imported_as_history_not_completion():
    state = ReleaseControl.default().load_state()
    imports = state["legacy_imports"]
    assert [item["queue_id"] for item in imports] == [
        "mode_p_vnext_loop_repair_2026_07_22",
        "mode_p_vnext_director_v1_1_2026_07_30",
        "mode_p_vnext_completion_2026_07_30",
    ]
    assert all(item["disposition"] == "HISTORICAL_READ_ONLY" for item in imports)
    assert all(item["grants_v2_completion"] is False for item in imports)
    assert imports[0]["imported_next_task"] == "R0.2"
    assert imports[1]["imported_completed_tasks"] == [
        "DDO-0",
        "DDO-1",
        "DDO-2",
        "DDO-3",
        "DDO-4",
        "DDO-5",
        "DDO-6",
    ]
    assert imports[2]["imported_next_task"] == "CPL-2"
    assert (
        imports[2]["failure_evidence"]["classification"]
        == "ARCHITECTURE_BOUNDARY_FAILURE"
    )


def test_legacy_controllers_cannot_select_or_advance_release_work():
    for control in (
        RebuildControl.default(),
        DirectorDdoControl.default(),
        CompletionControl.default(),
    ):
        with pytest.raises(ControlError, match="historical read-only"):
            control.next_task()
        with pytest.raises(ControlError, match="historical read-only"):
            control.claim("not-a-release-task", "test-owner")
        assert isinstance(control.load_state(), dict)


def test_release_control_has_one_legal_next_task_and_at_most_one_matching_lock():
    control = ReleaseControl.default()
    assert control.audit() == []
    state = control.load_state()
    completed = set(state["completed_tasks"])
    expected = next(
        (task for task in control.load_tasks() if task.task_id not in completed),
        None,
    )

    if state["status"] == "IN_PROGRESS":
        assert expected is not None
        assert control.next_task().task_id == expected.task_id
        assert state["current_task"] == expected.task_id
        assert state["current_owner"]
        assert state["lock_token"]
        lock = _read_json(control.lock_path)
        assert lock["task_id"] == state["current_task"]
        assert lock["owner"] == state["current_owner"]
        assert lock["token"] == state["lock_token"]
    else:
        actual = control.next_task()
        if expected is not None:
            assert actual is not None
            assert actual.task_id == expected.task_id
            assert state["status"] == expected.pending_status
            assert state["next_task"] == expected.task_id
        else:
            assert actual is None
            assert state["next_task"] is None
        assert state["current_task"] is None
        assert state["current_owner"] is None
        assert state["lock_token"] is None
        assert not control.lock_path.exists()

    historical_locks = [
        RebuildControl.default().lock_path,
        DirectorDdoControl.default().lock_path,
        CompletionControl.default().lock_path,
    ]
    assert all(not path.exists() for path in historical_locks)


def test_construction_entry_and_readme_route_only_to_release_control():
    root = ReleaseControl.default().root
    command = (
        root / ".claude" / "commands" / "mode-p-vnext-rebuild.md"
    ).read_text(encoding="utf-8")
    readme = (
        root / "MODE_P_REDESIGN_PROJECT" / "README.md"
    ).read_text(encoding="utf-8")
    construction = (
        root
        / "MODE_P_REDESIGN_PROJECT"
        / "MODE_P_VNEXT_CONSTRUCTION_V3.md"
    ).read_text(encoding="utf-8")

    assert "python -m mode_p_vnext.release_control" in command
    assert "MODE_P_VNEXT_RELEASE_TASKS.json" in command
    assert "MODE_P_VNEXT_RELEASE_STATE.json" in command
    assert "historical evidence only" in command
    assert "v2.3 is rejected" in command
    assert "python -m mode_p_vnext.rebuild_control claim" not in command
    assert "Never call `record-owner-approval` for the user." in command

    assert "MODE_P_VNEXT_CONSTRUCTION_V3.md" in readme
    assert "MODE_P_VNEXT_RELEASE_TASKS.json" in readme
    assert "python -m mode_p_vnext.release_control" in readme
    assert "v2.3 已正式否决" in construction
    assert "一轮只完成一个 A 包" in construction
    assert "独占写入所有权" in construction

    root_guidance = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert "architecture-v3.0 ReleaseLedger" in root_guidance
    assert "mode_p_vnext.release_control" in root_guidance
    assert "mode_p_vnext.rebuild_control\naudit/status" not in root_guidance

    registry = _read_json(ReleaseControl.default().tasks_path)
    assert {item["path"] for item in registry["active_guidance"]} == {
        "CLAUDE.md",
        ".claude/commands/mode-p-vnext-rebuild.md",
        "MODE_P_REDESIGN_PROJECT/README.md",
        "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_CONSTRUCTION_V3.md",
        "01_调度器/mode_p_vnext/README.md",
    }
    for item in registry["active_guidance"]:
        content = (root / item["path"]).read_text(encoding="utf-8")
        assert item["marker"] == AUTHORITY_MARKER
        assert AUTHORITY_MARKER in content

    historical_construction = (
        root
        / "MODE_P_REDESIGN_PROJECT"
        / "MODE_P_VNEXT_CONSTRUCTION_V2.md"
    ).read_text(encoding="utf-8")
    assert "HISTORICAL_READ_ONLY" in historical_construction
    assert "REJECTED_BY_WHOLE_SYSTEM_AUDIT" in historical_construction


def test_a0_cannot_enable_external_media_or_production():
    state = ReleaseControl.default().load_state()
    assert state["production_entry"] == "v4_unchanged"
    assert state["director_runtime_started"] is False
    assert state["external_submission"] is False
    assert state["media_visual_acceptance"] is False
    assert state["owner_production_approval"] is False
    assert state["production_switch_authorized"] is False

    gate = FeatureGate(ReleaseControl.default().root)
    status = gate.status()
    assert gate.production_enabled is False
    assert gate.can_enable_in_rebuild("production") is False
    assert status.effective_mode == "current"
    assert status.vnext_invocation_allowed is False
    assert status.external_submission_allowed is False


def test_task_path_ownership_and_evidence_patterns_are_disjoint():
    tasks = ReleaseControl.default().load_tasks()
    for index, left in enumerate(tasks):
        for right in tasks[index + 1 :]:
            overlaps = [
                (left_pattern, right_pattern)
                for left_pattern in left.allowed_paths
                for right_pattern in right.allowed_paths
                if _patterns_overlap(left_pattern, right_pattern)
            ]
            assert overlaps == [], f"{left.task_id}/{right.task_id}: {overlaps}"

            left_sample = (
                "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
                f"{left.task_id}_SAMPLE.json"
            )
            right_sample = (
                "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
                f"{right.task_id}_SAMPLE.json"
            )
            assert not any(
                fnmatch.fnmatchcase(right_sample, pattern)
                for pattern in left.allowed_paths
            )
            assert not any(
                fnmatch.fnmatchcase(left_sample, pattern)
                for pattern in right.allowed_paths
            )

    a10 = next(task for task in tasks if task.task_id == "A10")
    assert a10.manual_gates == (
        "media_visual_acceptance",
        "owner_production_approval",
    )
    assert all(
        not path.startswith("01_调度器/mode_p_vnext/")
        or "/tests/" in path
        for path in a10.allowed_paths
    )


def _minimal_release_task(task_id, depends_on, pending_status):
    return {
        "task_id": task_id,
        "title": task_id,
        "phase": pending_status.removesuffix("_REQUIRED"),
        "pending_status": pending_status,
        "depends_on": depends_on,
        "spec_refs": [],
        "allowed_paths": [
            "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
            f"{task_id}_*.json"
        ],
        "required_checks": ["ok"],
        "verification_commands": [
            {
                "name": f"{task_id.lower()}_verification",
                "argv": ["{python}", "-c", "raise SystemExit(0)"],
                "cwd": ".",
                "timeout_seconds": 30,
            }
        ],
        "locked_verification_inputs": {},
    }


def _minimal_release_state():
    return {
        "schema_version": "2.0",
        "queue_id": "test-release",
        "architecture_version": "2.1",
        "architecture_documents": [],
        "authority": "SOLE_VNEXT_CONSTRUCTION_LEDGER",
        "status": "BASELINE_REPAIR_REQUIRED",
        "completed_tasks": [],
        "current_task": None,
        "current_owner": None,
        "lock_token": None,
        "next_task": "A0",
        "evidence_records": {},
        "invalidated_records": [],
        "release_gate_evidence": {},
        "production_entry": "v4_unchanged",
        "media_visual_acceptance": False,
        "owner_production_approval": False,
        "production_switch_authorized": False,
    }


def test_phase_status_progression_uses_the_next_work_package(tmp_path):
    work_packages = ["A0", "A1", "A2", "A3", "A4"]
    tasks = {
        "schema_version": "2.0",
        "architecture_version": "2.1",
        "architecture_documents": [],
        "authority": "SOLE_VNEXT_CONSTRUCTION_LEDGER",
        "status_after_all": "DONE",
        "tasks": [
            _minimal_release_task("A0", [], "BASELINE_REPAIR_REQUIRED"),
            *(
                _minimal_release_task(
                    task_id,
                    [work_packages[index - 1]],
                    "ARCHITECTURE_MIGRATION_REQUIRED",
                )
                for index, task_id in enumerate(work_packages[1:], start=1)
            ),
        ],
    }
    control = ReleaseControl(tmp_path)
    _write_json(control.tasks_path, tasks)
    _write_json(control.state_path, _minimal_release_state())

    for index, task_id in enumerate(work_packages[:-1]):
        claim = control.claim(task_id, "phase-test")
        evidence = (
            tmp_path
            / "MODE_P_REDESIGN_PROJECT"
            / "vnext_repair_evidence"
            / f"{task_id}_PHASE.json"
        )
        _write_json(
            evidence,
            {
                "task_id": task_id,
                "changed_paths": [],
                "checks": [{"name": "ok", "exit_code": 0}],
            },
        )
        state = control.complete(task_id, "phase-test", claim["token"], evidence)
        expected = work_packages[index + 1]
        assert state["status"] == "ARCHITECTURE_MIGRATION_REQUIRED"
        assert state["next_task"] == expected
        assert control.next_task().task_id == expected

    claim = control.claim("A4", "phase-test")
    state = control.fail("A4", "phase-test", claim["token"], None)
    assert state["status"] == "ARCHITECTURE_MIGRATION_REQUIRED"
    assert state["next_task"] == "A4"


def test_claim_cli_summary_is_bounded():
    lock = {
        "task_id": "A0",
        "owner": "owner",
        "token": "token",
        "acquired_at": "now",
        "manifest_file_count": 1556,
        "manifest_sha256": "a" * 64,
        "claim_manifest": {f"path-{index}": "b" * 64 for index in range(2000)},
    }
    summary = _claim_summary(lock)
    assert set(summary) == {
        "task_id",
        "owner",
        "token",
        "acquired_at",
        "manifest_file_count",
        "manifest_sha256",
    }
    assert "claim_manifest" not in summary
    assert len(json.dumps(summary)) < 512


def test_v3_active_guidance_drift_blocks_next_and_claim(tmp_path):
    architecture = (
        tmp_path
        / "MODE_P_REDESIGN_PROJECT"
        / "vnext_repair_evidence"
        / "MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0.md"
    )
    architecture.parent.mkdir(parents=True, exist_ok=True)
    architecture.write_text("single v3 authority\n", encoding="utf-8")
    architecture_hash = _sha256_file(architecture)
    architecture_rel = architecture.relative_to(tmp_path).as_posix()

    guidance = tmp_path / "CLAUDE.md"
    guidance.write_text(AUTHORITY_MARKER + "\n", encoding="utf-8")
    task = _minimal_release_task("A0", [], "BASELINE_REPAIR_REQUIRED")
    tasks = {
        "schema_version": "2.0",
        "queue_id": "test-v3",
        "architecture_version": "3.0",
        "architecture_documents": [
            {
                "path": architecture_rel,
                "sha256": architecture_hash,
                "role": "SOLE_NORMATIVE_BASELINE",
            }
        ],
        "historical_architecture_documents": [
            {
                "version": version,
                "path": f"historical-v{version}.md",
                "disposition": (
                    "REJECTED_BY_WHOLE_SYSTEM_AUDIT"
                    if version == "2.3"
                    else "HISTORICAL_READ_ONLY"
                ),
            }
            for version in ("2.0", "2.1", "2.2", "2.3")
        ],
        "active_guidance": [
            {"path": "CLAUDE.md", "marker": AUTHORITY_MARKER}
        ],
        "locked_verification_inputs": {architecture_rel: architecture_hash},
        "authority": "SOLE_VNEXT_CONSTRUCTION_LEDGER",
        "status_after_all": "DONE",
        "tasks": [task],
    }
    state = _minimal_release_state()
    state.update(
        {
            "architecture_version": "3.0",
            "architecture_documents": [
                {"path": architecture_rel, "sha256": architecture_hash}
            ],
        }
    )
    control = ReleaseControl(tmp_path)
    _write_json(control.tasks_path, tasks)
    _write_json(control.state_path, state)

    assert control.next_task().task_id == "A0"
    guidance.write_text("stale architecture-v2.2 guidance\n", encoding="utf-8")
    with pytest.raises(ControlError, match="active guidance authority marker drift"):
        control.next_task()
    with pytest.raises(ControlError, match="active guidance authority marker drift"):
        control.claim("A0", "drift-test")


def test_architecture_rebase_rejects_an_amendment_stack(tmp_path):
    control = ReleaseControl(tmp_path)
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    with pytest.raises(ControlError, match="one complete normative document"):
        control.rebase_architecture("3.1", [first, second])


def test_artifact_hashes_are_portable_across_git_line_endings(tmp_path):
    text_path = tmp_path / "artifact.txt"
    text_path.write_bytes("第一行\nsecond\n".encode("utf-8"))
    lf_hash = _sha256_file(text_path)
    text_path.write_bytes("第一行\r\nsecond\r\n".encode("utf-8"))
    assert _sha256_file(text_path) == lf_hash

    binary_path = tmp_path / "artifact.bin"
    binary_path.write_bytes(b"\x00a\n")
    binary_lf_hash = _sha256_file(binary_path)
    binary_path.write_bytes(b"\x00a\r\n")
    assert _sha256_file(binary_path) != binary_lf_hash


def test_a10_requires_hash_bound_media_and_owner_gates(tmp_path):
    task = _minimal_release_task("A10", [], "MEDIA_EVIDENCE_REQUIRED")
    task["allowed_paths"].insert(
        0, "MODE_P_REDESIGN_PROJECT/vnext_release_runs/A10/**"
    )
    task["manual_gates"] = [
        "media_visual_acceptance",
        "owner_production_approval",
    ]
    tasks = {
        "schema_version": "2.0",
        "architecture_version": "2.1",
        "architecture_documents": [],
        "authority": "SOLE_VNEXT_CONSTRUCTION_LEDGER",
        "status_after_all": "PRODUCTION_SWITCH_PROPOSAL_ELIGIBLE",
        "tasks": [task],
    }
    state = _minimal_release_state()
    state.update(
        {
            "status": "MEDIA_EVIDENCE_REQUIRED",
            "next_task": "A10",
        }
    )
    control = ReleaseControl(tmp_path)
    _write_json(control.tasks_path, tasks)
    _write_json(control.state_path, state)
    claim = control.claim("A10", "a10-test")

    unsafe_state = control.load_state()
    unsafe_state["production_entry"] = "vnext"
    _write_json(control.state_path, unsafe_state)
    with pytest.raises(ControlError, match="cannot change the production entry"):
        control.complete(
            "A10",
            "a10-test",
            claim["token"],
            tmp_path / "does-not-exist.json",
        )
    assert control.lock_path.is_file()
    unsafe_state["production_entry"] = "v4_unchanged"
    _write_json(control.state_path, unsafe_state)

    media_path = (
        tmp_path
        / "MODE_P_REDESIGN_PROJECT"
        / "vnext_release_runs"
        / "A10"
        / "media_acceptance.json"
    )
    media_payload = {
        "kind": "MEDIA_VISUAL_ACCEPTANCE",
        "accepted": True,
        "media_runs": ["run-001"],
        "frame_evidence": ["frame-001"],
        "v4_vnext_comparison": {"result": "accepted"},
        "production_switch_authorized": False,
    }
    _write_json(media_path, media_payload)
    control.record_media_acceptance("a10-test", claim["token"], media_path)
    with pytest.raises(ControlError, match="owner preview approval"):
        control._assert_a10_gates()

    media_sha = hashlib.sha256(media_path.read_bytes()).hexdigest()
    owner_path = (
        tmp_path
        / "MODE_P_REDESIGN_PROJECT"
        / "vnext_owner_approvals"
        / "owner-001.json"
    )
    _write_json(
        owner_path,
        {
            "kind": "OWNER_PREVIEW_APPROVAL",
            "approved": True,
            "approved_by": "test-user",
            "scope": "OWNER_APPROVED_PREVIEW",
            "media_evidence_sha256": media_sha,
            "production_switch_authorized": False,
        },
    )
    control.record_owner_approval("test-user", owner_path)
    control._assert_a10_gates()

    media_payload["frame_evidence"].append("changed-after-approval")
    _write_json(media_path, media_payload)
    assert any("hash drift" in issue for issue in control.audit())
    with pytest.raises(ControlError, match="release gates failed"):
        control._assert_a10_gates()
