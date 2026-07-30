"""R3.2 terminal-state contract is a restricted baseline audit, not readiness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mode_p_vnext.baseline_audit_control import (
    STATUS_AUDITED,
    STATUS_IN_PROGRESS,
    STATUS_REQUIRED,
    BaselineAuditControl,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HISTORICAL_CONTRACT = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "R3.2_TERMINAL_STATE_CONTRACT_001.json"
)
ACTIVE_CONTRACT = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "R3.2_BASELINE_AUDIT_CONTRACT_002.json"
)
STATE_PATH = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_BASELINE_AUDIT_STATE.json"
LEDGER_PATH = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "task_evidence_ledger_v2.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_historical_mismatch_record_is_preserved_not_rewritten():
    historical = _load(HISTORICAL_CONTRACT)
    assert historical["status"] == "CONTRACT_MISMATCH_CONFIRMED_NOT_RESOLVED"
    assert historical["controller_fact"]["controller_emits_LOCAL_VNEXT_READY"] is False
    assert historical["truthful_interpretation"]["may_complete_r3_2_now"] is False


def test_authorized_baseline_generation_is_fail_closed_during_and_after_execution():
    contract = _load(ACTIVE_CONTRACT)
    state = _load(STATE_PATH)
    ledger = _load(LEDGER_PATH)
    control = BaselineAuditControl(PROJECT_ROOT)

    assert contract["status"] == "AUTHORIZED_BASELINE_AUDIT_GENERATION"
    assert contract["terminal_state"] == STATUS_AUDITED
    assert contract["replaces_LOCAL_VNEXT_READY"] is False
    assert control.audit() == []
    assert state["status"] in {STATUS_REQUIRED, STATUS_IN_PROGRESS, STATUS_AUDITED}

    v10_6 = next(row for row in ledger["tasks"] if row["task_id"] == "V10.6")
    if state["status"] == STATUS_AUDITED:
        evidence_path = PROJECT_ROOT / v10_6["baseline_audit_evidence"]
        assert v10_6["disposition"] == "VERIFIED_IMPLEMENTED"
        assert ledger["summary"]["all_70_evidenced"] is True
        assert hashlib.sha256(evidence_path.read_bytes()).hexdigest() == state["audit_evidence_sha256"]
    else:
        assert v10_6["disposition"] == "PENDING_MACHINE_AUDIT"
        assert ledger["summary"]["all_70_evidenced"] is False


def test_baseline_terminal_state_grants_no_runtime_or_media_authority():
    contract = _load(ACTIVE_CONTRACT)
    state = _load(STATE_PATH)
    for source in (contract["non_activation"], state):
        assert source["director_runtime_started"] is False
        assert source["shadow_started"] is False
        assert source["external_generation_invoked"] is False
        assert source["production_entry_changed"] is False
        assert source["media_visual_acceptance_claimed"] is False
    assert "LOCAL_VNEXT_READY" in contract["claims_not_granted"]
    assert "DIRECTOR_SHADOW_READY" in contract["claims_not_granted"]
    assert "PRODUCTION_READY" in contract["claims_not_granted"]
