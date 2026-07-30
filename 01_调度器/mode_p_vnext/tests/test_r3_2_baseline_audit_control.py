"""Behavioral checks for the independent R3.2 baseline-audit controller."""

from __future__ import annotations

import json
from pathlib import Path

from mode_p_vnext.baseline_audit_control import (
    NON_ACTIVATION_FLAGS,
    STATUS_AUDITED,
    STATUS_IN_PROGRESS,
    STATUS_REQUIRED,
    BaselineAuditControl,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STATE_PATH = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_BASELINE_AUDIT_STATE.json"
CONTRACT_PATH = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "R3.2_BASELINE_AUDIT_CONTRACT_002.json"
)
LEDGER_PATH = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "task_evidence_ledger_v2.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_baseline_audit_controller_has_a_valid_current_state():
    control = BaselineAuditControl(PROJECT_ROOT)
    assert control.audit() == []
    state = control.load_state()
    assert state["status"] in {STATUS_REQUIRED, STATUS_IN_PROGRESS, STATUS_AUDITED}


def test_only_restricted_terminal_state_can_close_the_pending_v10_6_row():
    state = _load(STATE_PATH)
    ledger = _load(LEDGER_PATH)
    v10_6 = next(row for row in ledger["tasks"] if row["task_id"] == "V10.6")
    if state["status"] == STATUS_AUDITED:
        assert v10_6["machine_terminal_state"] == STATUS_AUDITED
        assert v10_6["baseline_audit_evidence"].endswith("R3.2_BASELINE_REPAIR_AUDIT_005.json")
    else:
        assert v10_6["disposition"] == "PENDING_MACHINE_AUDIT"
        assert v10_6["required_terminal_state"] == STATUS_AUDITED


def test_contract_does_not_use_a_readiness_or_activation_label():
    contract = _load(CONTRACT_PATH)
    state = _load(STATE_PATH)
    serialized = json.dumps(contract, ensure_ascii=False, sort_keys=True)
    assert "LOCAL_VNEXT_READY" not in contract["terminal_state"]
    assert "DIRECTOR_SHADOW_READY" not in contract["terminal_state"]
    assert "PRODUCTION_READY" not in contract["terminal_state"]
    for source in (contract["non_activation"], state):
        for field in NON_ACTIVATION_FLAGS:
            assert source[field] is False
