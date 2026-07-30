"""DDO-0: the Director vNext.1 queue is isolated and fail-closed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mode_p_vnext.director_vnext1.control import DirectorDdoControl
from mode_p_vnext.feature_gate import FeatureGate


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TASKS_PATH = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_DIRECTOR_V1_1_TASKS.json"
STATE_PATH = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_DIRECTOR_V1_1_STATE.json"
PLAN_PATH = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN_V1.1.md"
)
GOAL_LOCK_PATH = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "DIRECTOR_REFACTOR_GOAL_LOCK_V1.1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_director_queue_is_independent_and_dependency_ordered():
    control = DirectorDdoControl(PROJECT_ROOT)
    assert control.audit() == []
    tasks = _load(TASKS_PATH)
    assert tasks["queue_id"] == "mode_p_vnext_director_v1_1_2026_07_30"
    assert [task["task_id"] for task in tasks["tasks"]] == [
        "DDO-0", "DDO-1", "DDO-2", "DDO-3", "DDO-4", "DDO-5", "DDO-6"
    ]
    assert tasks["status_after_all"] == "DIRECTOR_TEXT_PIPELINE_IMPLEMENTED"
    assert tasks["terminal_claim_ceiling"] == "PLANNED_PREVIEW"


def test_goal_lock_and_construction_plan_remain_the_authority():
    lock = _load(GOAL_LOCK_PATH)
    assert lock["status"] == "FROZEN_PRECONSTRUCTION_V1_1"
    assert hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest() == lock["construction_plan"]["sha256"]
    assert lock["activation_guard"]["director_vnext_runtime_may_start_before_r3_2"] is False
    assert lock["single_creative_source"]["artifact"] == "VisualExecutionContract"
    assert lock["removed_legacy_dependencies"]["master_continuity_board"] is True


def test_queue_and_live_state_do_not_activate_vnext_or_production():
    state = _load(STATE_PATH)
    assert state["production_entry"] == "v4_unchanged"
    assert state["director_runtime_started"] is False
    assert state["external_submission"] is False
    assert state["media_visual_acceptance"] is False
    gate = FeatureGate(PROJECT_ROOT)
    assert gate.status().vnext_invocation_allowed is False
    assert gate.status().external_submission_allowed is False
