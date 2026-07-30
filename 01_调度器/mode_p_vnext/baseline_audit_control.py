"""Independent, fail-closed controller for the R3.2 baseline audit.

This controller is deliberately separate from the historical R0--R3 repair
queue.  It can certify only ``BASELINE_REPAIR_AUDITED``: repaired source,
current regression evidence, and the 70-row ledger are coherent.  It never
starts Director, Shadow, external generation, production, or media approval.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Sequence


STATE_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_BASELINE_AUDIT_STATE.json")
CONTRACT_REL = Path(
    "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
    "R3.2_BASELINE_AUDIT_CONTRACT_002.json"
)
LEDGER_REL = Path(
    "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/task_evidence_ledger_v2.json"
)
SOURCE_LEDGER_REL = Path(
    "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R0.3_reconciliation_ledger.json"
)
REPAIR_STATE_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD_STATE.json")

STATUS_REQUIRED = "BASELINE_AUDIT_REQUIRED"
STATUS_IN_PROGRESS = "BASELINE_AUDIT_IN_PROGRESS"
STATUS_AUDITED = "BASELINE_REPAIR_AUDITED"
STATUS_FAILED = "BASELINE_AUDIT_FAILED"
PENDING_DISPOSITION = "PENDING_MACHINE_AUDIT"

NON_ACTIVATION_FLAGS = (
    "director_runtime_started",
    "shadow_started",
    "external_generation_invoked",
    "production_entry_changed",
    "media_visual_acceptance_claimed",
)


class BaselineAuditError(RuntimeError):
    """The baseline audit cannot establish its restricted terminal state."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(_canonical_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BaselineAuditError(f"required audit artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BaselineAuditError(f"invalid JSON in audit artifact {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BaselineAuditError(f"audit artifact root must be an object: {path}")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_relative(raw: str) -> Path:
    normalized = raw.replace("\\", "/").strip()
    candidate = PurePosixPath(normalized)
    if not normalized or candidate.is_absolute() or ".." in candidate.parts:
        raise BaselineAuditError(f"unsafe relative path in baseline contract: {raw!r}")
    return Path(*candidate.parts)


class BaselineAuditControl:
    """One-shot baseline-audit state machine for the new controller generation."""

    def __init__(self, project_root: Path):
        self.root = project_root.resolve()
        self.state_path = self.root / STATE_REL
        self.contract_path = self.root / CONTRACT_REL
        self.ledger_path = self.root / LEDGER_REL
        self.source_ledger_path = self.root / SOURCE_LEDGER_REL
        self.repair_state_path = self.root / REPAIR_STATE_REL

    @classmethod
    def default(cls) -> "BaselineAuditControl":
        return cls(Path(__file__).resolve().parents[2])

    def load_contract(self) -> Dict[str, Any]:
        return _read_json(self.contract_path)

    def load_state(self) -> Dict[str, Any]:
        return _read_json(self.state_path)

    def load_ledger(self) -> Dict[str, Any]:
        return _read_json(self.ledger_path)

    def _guarded_input_hashes(self, contract: Mapping[str, Any]) -> Dict[str, str]:
        raw_paths = contract.get("guarded_inputs")
        if not isinstance(raw_paths, list) or not raw_paths:
            raise BaselineAuditError("baseline contract must name guarded_inputs")
        result: Dict[str, str] = {}
        for raw_path in raw_paths:
            if not isinstance(raw_path, str):
                raise BaselineAuditError("guarded input path must be a string")
            relative = _safe_relative(raw_path)
            resolved = (self.root / relative).resolve()
            try:
                resolved.relative_to(self.root)
            except ValueError as exc:
                raise BaselineAuditError(
                    f"guarded input resolves outside project: {raw_path}"
                ) from exc
            if not resolved.is_file():
                raise BaselineAuditError(f"guarded input missing: {raw_path}")
            result[relative.as_posix()] = _sha256_file(resolved)
        return result

    @staticmethod
    def _v10_6(ledger: Mapping[str, Any]) -> Dict[str, Any]:
        tasks = ledger.get("tasks")
        if not isinstance(tasks, list):
            raise BaselineAuditError("evidence ledger must contain tasks")
        matches = [row for row in tasks if isinstance(row, dict) and row.get("task_id") == "V10.6"]
        if len(matches) != 1:
            raise BaselineAuditError("evidence ledger must contain exactly one V10.6 row")
        return matches[0]

    @staticmethod
    def _non_activation_issues(source: Mapping[str, Any]) -> List[str]:
        issues: List[str] = []
        for field in NON_ACTIVATION_FLAGS:
            if source.get(field) is not False:
                issues.append(f"non-activation field must be false: {field}")
        return issues

    def _validate_contract(self, contract: Mapping[str, Any]) -> List[str]:
        issues: List[str] = []
        if contract.get("status") != "AUTHORIZED_BASELINE_AUDIT_GENERATION":
            issues.append("baseline contract is not an authorized audit generation")
        if contract.get("terminal_state") != STATUS_AUDITED:
            issues.append("baseline contract terminal_state is not BASELINE_REPAIR_AUDITED")
        if contract.get("replaces_LOCAL_VNEXT_READY") is not False:
            issues.append("baseline contract must not replace or emit LOCAL_VNEXT_READY")
        if contract.get("historical_r0_to_r3_evidence_rewritten") is not False:
            issues.append("baseline contract must preserve historical R0-R3 evidence")
        issues.extend(self._non_activation_issues(contract.get("non_activation", {})))
        commands = contract.get("verification_commands")
        if not isinstance(commands, list) or {item.get("name") for item in commands if isinstance(item, dict)} != {
            "vnext_full",
            "v4_full",
        }:
            issues.append("baseline contract must define exactly vnext_full and v4_full")
        return issues

    def audit(self) -> List[str]:
        """Return every detected inconsistency without changing any artifact."""

        issues: List[str] = []
        try:
            contract = self.load_contract()
            state = self.load_state()
            ledger = self.load_ledger()
            issues.extend(self._validate_contract(contract))
            state_status = state.get("status")
            if state_status not in {STATUS_REQUIRED, STATUS_IN_PROGRESS, STATUS_AUDITED, STATUS_FAILED}:
                issues.append(f"unknown baseline audit state: {state_status!r}")
                return issues
            if state.get("controller_generation") != contract.get("controller_generation"):
                issues.append("state/controller generation mismatch")
            if state.get("production_entry") != "v4_unchanged":
                issues.append("baseline audit state must retain v4_unchanged production entry")
            issues.extend(self._non_activation_issues(state))

            source = _read_json(self.source_ledger_path)
            source_ref = ledger.get("source_ledger", {})
            if source_ref.get("task_count") != 70:
                issues.append("evidence ledger source task count is not 70")
            if source_ref.get("sha256") != _sha256_file(self.source_ledger_path):
                issues.append("evidence ledger source hash drift")
            if len(source.get("tasks", [])) != 70:
                issues.append("immutable source ledger no longer has 70 tasks")

            v10_6 = self._v10_6(ledger)
            summary = ledger.get("summary", {})
            if state_status in {STATUS_REQUIRED, STATUS_IN_PROGRESS, STATUS_FAILED}:
                if v10_6.get("disposition") != PENDING_DISPOSITION:
                    issues.append("V10.6 must remain PENDING_MACHINE_AUDIT before final state")
                if summary.get("all_70_evidenced") is not False:
                    issues.append("all_70_evidenced cannot be true before terminal baseline state")
            elif state_status == STATUS_AUDITED:
                if v10_6.get("disposition") != "VERIFIED_IMPLEMENTED":
                    issues.append("V10.6 is not verified in terminal baseline state")
                if summary.get("all_70_evidenced") is not True:
                    issues.append("terminal baseline state requires all_70_evidenced=true")
                evidence_ref = v10_6.get("baseline_audit_evidence")
                if not isinstance(evidence_ref, str):
                    issues.append("V10.6 terminal evidence path is missing")
                else:
                    evidence_path = self.root / _safe_relative(evidence_ref)
                    evidence = _read_json(evidence_path)
                    if evidence.get("status") != STATUS_AUDITED:
                        issues.append("baseline evidence does not carry audited status")
                    if evidence.get("ledger_sha256") != _sha256_file(self.ledger_path):
                        issues.append("baseline evidence ledger hash mismatch")
                    if state.get("audit_evidence_sha256") != _sha256_file(evidence_path):
                        issues.append("state baseline evidence hash mismatch")
                    results = evidence.get("verification_results", [])
                    if not isinstance(results, list) or len(results) != 2:
                        issues.append("baseline evidence must retain two verification results")
                    else:
                        for result in results:
                            if result.get("exit_code") != 0:
                                issues.append("terminal baseline evidence has failed verification")
                            if "skipped" in str(result.get("stdout_tail", "")).lower():
                                issues.append("terminal baseline evidence contains skipped tests")
                    if evidence.get("guarded_input_hashes") != state.get("guarded_input_hashes"):
                        issues.append("state/evidence guarded input hashes differ")
                current_hashes = self._guarded_input_hashes(contract)
                if current_hashes != state.get("guarded_input_hashes"):
                    issues.append("guarded input drift after baseline audit")

            repair_state = _read_json(self.repair_state_path)
            if repair_state.get("production_entry") != "v4_unchanged":
                issues.append("historical repair state does not retain v4_unchanged entry")
        except BaselineAuditError as exc:
            issues.append(str(exc))
        return issues

    def _run_command(self, command: Mapping[str, Any]) -> Dict[str, Any]:
        name = command.get("name")
        raw_argv = command.get("argv")
        raw_cwd = command.get("cwd")
        timeout_seconds = command.get("timeout_seconds")
        if not isinstance(name, str) or not isinstance(raw_argv, list) or not isinstance(raw_cwd, str):
            raise BaselineAuditError("malformed baseline verification command")
        if not isinstance(timeout_seconds, int) or timeout_seconds < 1 or timeout_seconds > 3600:
            raise BaselineAuditError("baseline verification timeout must be 1..3600 seconds")
        argv = [sys.executable if value == "{python}" else value for value in raw_argv]
        if not all(isinstance(value, str) and value for value in argv):
            raise BaselineAuditError("baseline verification argv must be non-empty strings")
        cwd = (self.root / _safe_relative(raw_cwd)).resolve()
        try:
            cwd.relative_to(self.root)
        except ValueError as exc:
            raise BaselineAuditError("baseline verification cwd escapes project") from exc
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise BaselineAuditError(f"baseline verification timed out: {name}") from exc
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        return {
            "name": name,
            "argv": argv,
            "cwd": raw_cwd,
            "exit_code": completed.returncode,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
            "stdout_tail": stdout[-2000:],
            "stderr_tail": stderr[-2000:],
        }

    def _write_failure(self, state: Mapping[str, Any], reason: str, results: Sequence[Mapping[str, Any]]) -> None:
        failed = dict(state)
        failed.update(
            {
                "status": STATUS_FAILED,
                "failed_at": _utc_now(),
                "failure_reason": reason,
                "verification_results": list(results),
            }
        )
        _atomic_write_json(self.state_path, failed)

    def invalidate(self, *, reason: str) -> Dict[str, Any]:
        """Reopen the terminal audit after guarded source or test drift.

        This is deliberately a controller transition, not an edit of the
        terminal label.  The prior evidence file is retained and referenced
        in ``invalidated_runs``; V10.6 returns to pending until a fresh full
        execution creates a new terminal record.
        """

        if not reason.strip():
            raise BaselineAuditError("baseline audit invalidation requires a non-empty reason")
        contract = self.load_contract()
        contract_issues = self._validate_contract(contract)
        if contract_issues:
            raise BaselineAuditError("baseline contract invalid: " + "; ".join(contract_issues))
        state = self.load_state()
        if state.get("status") not in {STATUS_AUDITED, STATUS_FAILED}:
            raise BaselineAuditError(
                "baseline audit can be invalidated only from terminal or failed state"
            )
        ledger = self.load_ledger()
        v10_6 = self._v10_6(ledger)
        prior = {
            "run_id": state.get("run_id"),
            "status": state.get("status"),
            "audit_evidence": state.get("audit_evidence"),
            "audit_evidence_sha256": state.get("audit_evidence_sha256"),
            "invalidated_at": _utc_now(),
            "reason": reason,
        }
        history = list(state.get("invalidated_runs", []))
        history.append(prior)

        v10_6.update(
            {
                "disposition": PENDING_DISPOSITION,
                "reason": "A prior machine audit was invalidated by guarded input drift. A fresh independent R3.2 baseline audit is required before this row can be current evidence.",
                "required_terminal_state": STATUS_AUDITED,
            }
        )
        for field in (
            "current_test_file",
            "current_test_run",
            "source_task_dependency_closure",
            "baseline_audit_evidence",
            "machine_terminal_state",
        ):
            v10_6.pop(field, None)
        summary = ledger["summary"]
        summary.update(
            {
                "verified_implemented": 69,
                "not_currently_verified": 0,
                "blocked_invalid_dependency": 0,
                "historical_reversion_unverified": 0,
                "pending_machine_audit": 1,
                "approved_waiver": 0,
                "retired": 0,
                "all_70_reconciled": True,
                "all_70_evidenced": False,
                "unresolved_task_ids": ["V10.6"],
            }
        )
        ledger["status"] = "BASELINE_AUDIT_REQUIRED_V10_6_PENDING_MACHINE_AUDIT"
        ledger["verification_run"] = {
            "id": "R3_2_BASELINE_AUDIT_INVALIDATED",
            "scope": "A guarded input drifted after the prior terminal state; V10.6 is pending a fresh full-suite controller execution.",
            "must_have_zero_skips": True,
        }
        ledger["evidence_contract"]["all_70_evidenced"] = False
        ledger["evidence_contract"]["terminal_state"] = None
        _atomic_write_json(self.ledger_path, ledger)

        reopened = dict(state)
        reopened.update(
            {
                "status": STATUS_REQUIRED,
                "run_id": None,
                "started_at": None,
                "completed_at": None,
                "failure_reason": None,
                "guarded_input_hashes": {},
                "verification_results": [],
                "audit_evidence": None,
                "audit_evidence_sha256": None,
                "ledger_sha256": None,
                "invalidated_runs": history,
            }
        )
        _atomic_write_json(self.state_path, reopened)
        issues = self.audit()
        if issues:
            raise BaselineAuditError("invalidated baseline state is inconsistent: " + "; ".join(issues))
        return reopened

    def execute(self) -> Dict[str, Any]:
        """Run fresh complete suites and atomically produce the restricted terminal state."""

        if self.audit():
            raise BaselineAuditError("baseline audit precondition failed: " + "; ".join(self.audit()))
        contract = self.load_contract()
        state = self.load_state()
        ledger = self.load_ledger()
        if state.get("status") != STATUS_REQUIRED:
            raise BaselineAuditError(
                f"baseline audit can start only from {STATUS_REQUIRED}, got {state.get('status')!r}"
            )
        if self._v10_6(ledger).get("disposition") != PENDING_DISPOSITION:
            raise BaselineAuditError("V10.6 must be pending before baseline execution")

        guarded_hashes = self._guarded_input_hashes(contract)
        run_id = f"R3.2_BASELINE_AUDIT_{uuid.uuid4().hex}"
        in_progress = dict(state)
        in_progress.update(
            {
                "status": STATUS_IN_PROGRESS,
                "run_id": run_id,
                "started_at": _utc_now(),
                "guarded_input_hashes": guarded_hashes,
                "verification_results": [],
                "failure_reason": None,
            }
        )
        _atomic_write_json(self.state_path, in_progress)

        results: List[Dict[str, Any]] = []
        try:
            for command in contract["verification_commands"]:
                result = self._run_command(command)
                results.append(result)
                if result["exit_code"] != 0:
                    raise BaselineAuditError(
                        f"baseline verification failed: {result['name']}\n{result['stdout_tail']}\n{result['stderr_tail']}"
                    )
                if "skipped" in result["stdout_tail"].lower():
                    raise BaselineAuditError(
                        f"baseline verification has skipped tests: {result['name']}"
                    )
            if self._guarded_input_hashes(contract) != guarded_hashes:
                raise BaselineAuditError("guarded input drift during baseline verification")
        except BaselineAuditError as exc:
            self._write_failure(in_progress, str(exc), results)
            raise

        finalized_ledger = copy.deepcopy(ledger)
        finalized_v10_6 = self._v10_6(finalized_ledger)
        evidence_rel = (
            "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
            "R3.2_BASELINE_REPAIR_AUDIT_005.json"
        )
        finalized_v10_6.update(
            {
                "disposition": "VERIFIED_IMPLEMENTED",
                "current_test_file": "mode_p_vnext/tests/test_r3_2_baseline_audit_control.py",
                "current_test_run": "R3.2 baseline audit full-suite execution",
                "source_task_dependency_closure": "V0.1-V10.5 current verification closure",
                "baseline_audit_evidence": evidence_rel,
                "machine_terminal_state": STATUS_AUDITED,
            }
        )
        finalized_v10_6.pop("reason", None)
        summary = finalized_ledger["summary"]
        summary.update(
            {
                "verified_implemented": 70,
                "not_currently_verified": 0,
                "blocked_invalid_dependency": 0,
                "historical_reversion_unverified": 0,
                "pending_machine_audit": 0,
                "approved_waiver": 0,
                "retired": 0,
                "all_70_reconciled": True,
                "all_70_evidenced": True,
                "unresolved_task_ids": [],
            }
        )
        finalized_ledger["status"] = "BASELINE_REPAIR_AUDITED_CURRENT_TASK_COVERAGE"
        finalized_ledger["verification_run"] = {
            "id": run_id,
            "scope": "Fresh vNext and v4 full-suite execution under the independent R3.2 baseline-audit controller.",
            "must_have_zero_skips": True,
        }
        finalized_ledger["evidence_contract"]["all_70_evidenced"] = True
        finalized_ledger["evidence_contract"]["terminal_state"] = STATUS_AUDITED
        ledger_sha256 = hashlib.sha256(_canonical_json_bytes(finalized_ledger)).hexdigest()

        evidence = {
            "schema_version": "1.0",
            "record_id": "R3.2_BASELINE_REPAIR_AUDIT_005",
            "record_type": "mode_p_vnext_independent_baseline_audit",
            "created_at": _utc_now(),
            "status": STATUS_AUDITED,
            "run_id": run_id,
            "authorization": "User authorized controlled invalidation/revalidation and terminal-contract rebase; settings.local.json must remain preserved.",
            "historical_records_preserved": [
                "R3.2_TERMINAL_STATE_CONTRACT_001.json",
                "R3.2_AUDIT_FAILURE_004.json",
            ],
            "verification_results": results,
            "guarded_input_hashes": guarded_hashes,
            "ledger_path": LEDGER_REL.as_posix(),
            "ledger_sha256": ledger_sha256,
            "terminal_state": STATUS_AUDITED,
            "non_activation": {field: False for field in NON_ACTIVATION_FLAGS},
            "claims_not_granted": [
                "LOCAL_VNEXT_READY",
                "DIRECTOR_SHADOW_READY",
                "PRODUCTION_READY",
                "STORYBOARD_VIDEO_VISUAL_ACCEPTANCE",
            ],
        }
        evidence_path = self.root / evidence_rel
        _atomic_write_json(evidence_path, evidence)
        _atomic_write_json(self.ledger_path, finalized_ledger)
        final_state = dict(in_progress)
        final_state.update(
            {
                "status": STATUS_AUDITED,
                "completed_at": _utc_now(),
                "audit_evidence": evidence_rel,
                "audit_evidence_sha256": _sha256_file(evidence_path),
                "ledger_sha256": ledger_sha256,
                "verification_results": results,
                "failure_reason": None,
            }
        )
        _atomic_write_json(self.state_path, final_state)
        issues = self.audit()
        if issues:
            raise BaselineAuditError("terminal baseline audit is inconsistent: " + "; ".join(issues))
        return final_state


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MODE:P vNext R3.2 baseline-audit controller")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("command", choices=("audit", "execute", "invalidate"))
    parser.add_argument("--reason", default="")
    args = parser.parse_args(argv)
    control = BaselineAuditControl(
        Path(args.project_root) if args.project_root else Path(__file__).resolve().parents[2]
    )
    try:
        if args.command == "audit":
            issues = control.audit()
            print(json.dumps({"ok": not issues, "issues": issues}, ensure_ascii=False))
            return 0 if not issues else 1
        if args.command == "invalidate":
            print(json.dumps(control.invalidate(reason=args.reason), ensure_ascii=False))
            return 0
        print(json.dumps(control.execute(), ensure_ascii=False))
        return 0
    except BaselineAuditError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
