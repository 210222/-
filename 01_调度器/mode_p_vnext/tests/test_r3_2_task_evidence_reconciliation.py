"""Fail-closed reconciliation checks for the 70 historical vNext tasks.

It distinguishes a pending machine audit from a terminal baseline audit.
V10.6 may become verified only when the independent controller has emitted
the restricted ``BASELINE_REPAIR_AUDITED`` state and its evidence is current.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCHEDULER_ROOT = PROJECT_ROOT / "01_调度器"
SOURCE_LEDGER = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "R0.3_reconciliation_ledger.json"
)
EVIDENCE_LEDGER = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "task_evidence_ledger_v2.json"
)
BASELINE_STATE = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "MODE_P_VNEXT_BASELINE_AUDIT_STATE.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(ledger: dict, source: dict) -> None:
    """Validate every task against the immutable R0.3 task set."""
    assert ledger["source_ledger"]["task_count"] == 70
    assert hashlib.sha256(SOURCE_LEDGER.read_bytes()).hexdigest() == ledger["source_ledger"]["sha256"]

    source_by_id = {row["task_id"]: row for row in source["tasks"]}
    rows = ledger["tasks"]
    by_id = {row["task_id"]: row for row in rows}
    assert len(rows) == len(by_id) == len(source_by_id) == 70
    assert set(by_id) == set(source_by_id)

    allowed = set(ledger["disposition_vocabulary"])
    for task_id, row in by_id.items():
        assert row["disposition"] in allowed, task_id
        source_row = source_by_id[task_id]
        if row["disposition"] == "VERIFIED_IMPLEMENTED":
            test_file = row.get("current_test_file")
            assert isinstance(test_file, str) and test_file
            assert (SCHEDULER_ROOT / test_file).is_file(), f"{task_id}: {test_file} missing"
            for dep in source_row["depends_on"]:
                if dep.startswith("V"):
                    assert by_id[dep]["disposition"] == "VERIFIED_IMPLEMENTED", (
                        f"{task_id} claimed verified while dependency {dep} is {by_id[dep]['disposition']}"
                    )
        elif row["disposition"] == "BLOCKED_INVALID_DEP":
            unresolved = row.get("unresolved_dependencies", [])
            assert unresolved, f"{task_id} blocked without naming a dependency"
            for dep in unresolved:
                assert by_id[dep]["disposition"] != "VERIFIED_IMPLEMENTED", (
                    f"{task_id} claims blocked by verified dependency {dep}"
                )
        elif row["disposition"] == "NOT_CURRENTLY_VERIFIED":
            assert source_row["checkbox"] == "[ ]", f"{task_id} needs a stronger disposition"
            assert row.get("reason")
        elif row["disposition"] == "HISTORICAL_REVERSION_UNVERIFIED":
            assert task_id == "V10.6"
            assert "reversion" in row.get("reason", "").lower()
        elif row["disposition"] == "PENDING_MACHINE_AUDIT":
            assert task_id == "V10.6"
            assert row.get("required_terminal_state") == "BASELINE_REPAIR_AUDITED"
            assert row.get("reason")
            assert ledger["summary"]["all_70_evidenced"] is False

        if task_id == "V10.6" and row["disposition"] == "VERIFIED_IMPLEMENTED":
            evidence_rel = row.get("baseline_audit_evidence")
            assert isinstance(evidence_rel, str) and evidence_rel
            evidence_path = PROJECT_ROOT / evidence_rel
            assert evidence_path.is_file()
            evidence = _load(evidence_path)
            state = _load(BASELINE_STATE)
            assert evidence["status"] == "BASELINE_REPAIR_AUDITED"
            assert state["status"] == "BASELINE_REPAIR_AUDITED"
            assert evidence["ledger_sha256"] == hashlib.sha256(EVIDENCE_LEDGER.read_bytes()).hexdigest()
            assert state["audit_evidence_sha256"] == hashlib.sha256(evidence_path.read_bytes()).hexdigest()

    counts = Counter(row["disposition"] for row in rows)
    summary = ledger["summary"]
    assert counts["VERIFIED_IMPLEMENTED"] == summary["verified_implemented"]
    assert counts["NOT_CURRENTLY_VERIFIED"] == summary["not_currently_verified"]
    assert counts["BLOCKED_INVALID_DEP"] == summary["blocked_invalid_dependency"]
    assert counts["HISTORICAL_REVERSION_UNVERIFIED"] == summary["historical_reversion_unverified"]
    assert counts["PENDING_MACHINE_AUDIT"] == summary.get("pending_machine_audit", 0)
    assert summary["all_70_reconciled"] is True
    unresolved = {row["task_id"] for row in rows if row["disposition"] != "VERIFIED_IMPLEMENTED"}
    assert unresolved == set(summary["unresolved_task_ids"])
    assert summary["all_70_evidenced"] is (not unresolved)
    assert ledger["evidence_contract"]["all_70_evidenced"] is summary["all_70_evidenced"]


def test_all_70_rows_have_truthful_current_dispositions():
    _validate(_load(EVIDENCE_LEDGER), _load(SOURCE_LEDGER))


def test_verified_rows_are_currently_executable_without_skips():
    ledger = _load(EVIDENCE_LEDGER)
    files = [
        row["current_test_file"]
        for row in ledger["tasks"]
        if row["disposition"] == "VERIFIED_IMPLEMENTED"
    ]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider"],
        cwd=SCHEDULER_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "skipped" not in result.stdout.lower(), result.stdout


def test_tampered_summary_or_dependency_cannot_pass():
    ledger = _load(EVIDENCE_LEDGER)
    source = _load(SOURCE_LEDGER)
    bad_summary = copy.deepcopy(ledger)
    current_verified = bad_summary["summary"]["verified_implemented"]
    bad_summary["summary"]["verified_implemented"] = (
        current_verified - 1 if current_verified else 1
    )
    with pytest.raises(AssertionError):
        _validate(bad_summary, source)

    bad_dependency = copy.deepcopy(ledger)
    by_id = {row["task_id"]: row for row in bad_dependency["tasks"]}
    by_id["V10.6"]["disposition"] = "VERIFIED_IMPLEMENTED"
    by_id["V10.6"]["current_test_file"] = "mode_p_vnext/tests/test_r3_2_task_evidence_reconciliation.py"
    by_id["V10.6"].pop("baseline_audit_evidence", None)
    with pytest.raises(AssertionError):
        _validate(bad_dependency, source)
