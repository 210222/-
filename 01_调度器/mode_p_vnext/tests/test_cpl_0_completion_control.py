"""CPL-0 freezes an honest completion audit without changing runtime."""

from __future__ import annotations

import json

from mode_p_vnext.director_vnext1.completion_control import CompletionControl
from mode_p_vnext.director_vnext1.control import DirectorDdoControl
from mode_p_vnext.feature_gate import FeatureGate


def test_completion_queue_is_independent_and_preserves_text_pipeline_history():
    control = CompletionControl.default()
    tasks = control.load_tasks()
    assert [task.task_id for task in tasks] == [f"CPL-{index}" for index in range(6)]
    assert control.tasks_path != DirectorDdoControl.default().tasks_path
    assert control.state_path != DirectorDdoControl.default().state_path
    assert control.lock_path != DirectorDdoControl.default().lock_path
    assert DirectorDdoControl.default().load_state()["status"] == "DIRECTOR_TEXT_PIPELINE_IMPLEMENTED"


def test_completion_matrix_records_unfinished_real_director_media_and_approval():
    root = CompletionControl.default().root
    matrix = (
        root
        / "MODE_P_REDESIGN_PROJECT"
        / "vnext_repair_evidence"
        / "DIRECTOR_DECISION_REFACTOR_COMPLETION_MATRIX_002.md"
    ).read_text(encoding="utf-8")
    assert "真实 Director 在未知剧本" in matrix
    assert "DeepSeek 是文本模型" in matrix
    assert "实际故事板与视频" in matrix
    assert "用户明确批准" in matrix
    assert "PLANNED_PREVIEW" in matrix


def test_completion_queue_cannot_enable_external_or_production_entry():
    control = CompletionControl.default()
    state = control.load_state()
    assert state["external_submission"] is False
    assert state["director_runtime_started"] is False
    assert state["media_visual_acceptance"] is False
    assert state["owner_production_approval"] is False
    assert state["production_entry"] == "v4_unchanged"
    tasks_doc = json.loads(control.tasks_path.read_text(encoding="utf-8"))
    assert tasks_doc["terminal_claim_ceiling"] == "PLANNED_PREVIEW"
    # Existing vNext feature gate remains fail-closed for release activity.
    gate = FeatureGate(control.root)
    status = gate.status()
    assert gate.production_enabled is False
    assert gate.can_enable_in_rebuild("production") is False
    assert status.effective_mode == "current"
    assert status.vnext_invocation_allowed is False
    assert status.external_submission_allowed is False
