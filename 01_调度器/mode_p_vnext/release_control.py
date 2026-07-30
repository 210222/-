"""Single construction controller for the MODE:P vNext architecture-v2 ledger.

The R, DDO, and CPL controllers remain readable as historical evidence, but
they are not valid task selectors after architecture v2 becomes the
construction baseline.  This module is the only controller used by
``/mode-p-vnext-rebuild`` for new work.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import fnmatch
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence

from mode_p_vnext.rebuild_control import (
    ControlError,
    RebuildControl,
    _atomic_write_json,
    _is_symlink_or_junction,
    _normalise_rel_path,
    _path_allowed,
    _read_json,
    _resolve_safe,
    _sha256_file,
    _utc_now,
)


RELEASE_TASKS_REL = Path(
    "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_TASKS.json"
)
RELEASE_STATE_REL = Path(
    "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_STATE.json"
)
RELEASE_LOCK_REL = Path(
    "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE.lock.json"
)
MEDIA_EVIDENCE_GLOB = "MODE_P_REDESIGN_PROJECT/vnext_release_runs/A10/**"
OWNER_APPROVAL_GLOB = "MODE_P_REDESIGN_PROJECT/vnext_owner_approvals/**"


def _patterns_overlap(left: str, right: str) -> bool:
    """Conservatively detect overlapping task-owned path patterns."""

    left = left.replace("\\", "/")
    right = right.replace("\\", "/")
    if left == right:
        return True
    for broad, narrow in ((left, right), (right, left)):
        if broad.endswith("/**"):
            prefix = broad[:-3].rstrip("/")
            if narrow == prefix or narrow.startswith(prefix + "/"):
                return True
    # This catches ambiguous sibling globs such as A1*.json vs A10_*.json.
    if fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left):
        return True
    return False


def _claim_summary(lock: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: lock[key]
        for key in (
            "task_id",
            "owner",
            "token",
            "acquired_at",
            "manifest_file_count",
            "manifest_sha256",
        )
    }


class ReleaseControl(RebuildControl):
    """Bind audited claim/evidence mechanics to the sole v2 ReleaseLedger."""

    def __init__(self, project_root: Path):
        super().__init__(
            project_root,
            tasks_rel=RELEASE_TASKS_REL,
            state_rel=RELEASE_STATE_REL,
            lock_rel=RELEASE_LOCK_REL,
        )
        # Owner approval is an external human gate, not an A10 worker artifact.
        # Keep it outside task deltas while binding its live hash in state.
        self._mutable_control_paths = frozenset(
            set(self._mutable_control_paths) | {OWNER_APPROVAL_GLOB}
        )

    @classmethod
    def default(cls) -> "ReleaseControl":
        return cls(Path(__file__).resolve().parents[2])

    def audit(self) -> List[str]:
        issues = super().audit()
        try:
            tasks = self.load_tasks()
            registry = self._load_tasks_document()
            state = self.load_state()
            if state.get("architecture_version") != registry.get(
                "architecture_version"
            ):
                issues.append(
                    "state and registry architecture_version disagree"
                )
            raw_registry_documents = registry.get("architecture_documents", [])
            if not isinstance(raw_registry_documents, list) or not all(
                isinstance(item, dict) for item in raw_registry_documents
            ):
                raise ControlError(
                    "registry architecture_documents must be a list of objects"
                )
            registry_documents = [
                {"path": item.get("path"), "sha256": item.get("sha256")}
                for item in raw_registry_documents
            ]
            if state.get("architecture_documents") != registry_documents:
                issues.append(
                    "state and registry architecture document bundle disagree"
                )
            for record in registry_documents:
                rel_path = record.get("path")
                expected_hash = record.get("sha256")
                if not isinstance(rel_path, str) or not isinstance(
                    expected_hash, str
                ):
                    issues.append("architecture document lacks path or sha256")
                    continue
                try:
                    path = _resolve_safe(self.root, rel_path)
                except ControlError as exc:
                    issues.append(str(exc))
                    continue
                if not path.is_file():
                    issues.append(f"architecture document missing: {rel_path}")
                elif _sha256_file(path) != expected_hash:
                    issues.append(f"architecture document hash drift: {rel_path}")

            phase_status = {
                "BASELINE_REPAIR": "BASELINE_REPAIR_REQUIRED",
                "ARCHITECTURE_MIGRATION": "ARCHITECTURE_MIGRATION_REQUIRED",
                "TEXT_SHADOW": "TEXT_SHADOW_REQUIRED",
                "HOLDOUT_EVALUATION": "HOLDOUT_EVALUATION_REQUIRED",
                "MEDIA_EVIDENCE": "MEDIA_EVIDENCE_REQUIRED",
            }
            for task in tasks:
                expected_status = phase_status.get(task.phase)
                if expected_status is None:
                    issues.append(f"{task.task_id}: unknown release phase {task.phase}")
                elif task.pending_status != expected_status:
                    issues.append(
                        f"{task.task_id}: pending_status does not match phase"
                    )
                expected_gates = (
                    ("media_visual_acceptance", "owner_production_approval")
                    if task.task_id == "A10"
                    else ()
                )
                if tuple(task.manual_gates) != expected_gates:
                    issues.append(
                        f"{task.task_id}: manual gate declaration is invalid"
                    )

            if state.get("status") == "IN_PROGRESS":
                if state.get("next_task") != state.get("current_task"):
                    issues.append(
                        "IN_PROGRESS next_task must equal current_task"
                    )
            elif state.get("next_task") is not None:
                task_by_id = {task.task_id: task for task in tasks}
                next_task = task_by_id.get(str(state.get("next_task")))
                if next_task is None:
                    issues.append("state next_task is unknown")
                elif state.get("status") != next_task.pending_status:
                    issues.append(
                        "state status does not match next task pending_status"
                    )
            for index, left_task in enumerate(tasks):
                for right_task in tasks[index + 1 :]:
                    for left in left_task.allowed_paths:
                        for right in right_task.allowed_paths:
                            if _patterns_overlap(left, right):
                                issues.append(
                                    "task path ownership overlap: "
                                    f"{left_task.task_id}:{left} <-> "
                                    f"{right_task.task_id}:{right}"
                                )
            for task in tasks:
                expected = (
                    "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
                    f"{task.task_id}_*.json"
                )
                evidence_patterns = [
                    path
                    for path in task.allowed_paths
                    if path.startswith(
                        "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
                    )
                    and path.endswith(".json")
                ]
                if evidence_patterns != [expected]:
                    issues.append(
                        f"{task.task_id}: evidence path must be exactly {expected}"
                    )
            issues.extend(self._gate_record_issues())
        except ControlError as exc:
            issues.append(str(exc))
        return issues

    def _gate_record_issues(self) -> List[str]:
        issues: List[str] = []
        state = self.load_state()
        records = state.get("release_gate_evidence", {})
        if not isinstance(records, dict):
            return ["release_gate_evidence must be an object"]

        media = records.get("media_visual_acceptance")
        owner = records.get("owner_production_approval")
        if bool(state.get("media_visual_acceptance")) != isinstance(media, dict):
            issues.append("media_visual_acceptance flag and evidence record disagree")
        if bool(state.get("owner_production_approval")) != isinstance(owner, dict):
            issues.append("owner_production_approval flag and evidence record disagree")
        if owner is not None and media is None:
            issues.append("owner approval exists without media acceptance")

        for name, record in (
            ("media_visual_acceptance", media),
            ("owner_production_approval", owner),
        ):
            if not isinstance(record, dict):
                continue
            raw_path = record.get("path")
            expected_hash = record.get("sha256")
            if not isinstance(raw_path, str) or not isinstance(expected_hash, str):
                issues.append(f"{name} evidence record lacks path or sha256")
                continue
            try:
                path = _resolve_safe(self.root, raw_path)
            except ControlError as exc:
                issues.append(f"{name}: {exc}")
                continue
            if not path.is_file():
                issues.append(f"{name} evidence file missing")
            elif _sha256_file(path) != expected_hash:
                issues.append(f"{name} evidence hash drift")

        if isinstance(media, dict) and isinstance(owner, dict):
            try:
                owner_payload = _read_json(
                    _resolve_safe(self.root, str(owner["path"]))
                )
            except (ControlError, KeyError):
                owner_payload = {}
            if owner_payload.get("media_evidence_sha256") != media.get("sha256"):
                issues.append("owner approval is not bound to current media evidence")
        if state.get("production_switch_authorized") is not False:
            issues.append("release ledger must not authorize production switching")
        return issues

    def rebase_architecture(
        self, version: str, document_paths: Sequence[Path]
    ) -> Dict[str, Any]:
        if self.lock_path.exists():
            raise ControlError("cannot rebase architecture while a lock exists")
        if not version.strip() or not document_paths:
            raise ControlError("architecture version and documents are required")
        state = self.load_state()
        if state.get("completed_tasks") or state.get("current_task") is not None:
            raise ControlError(
                "architecture rebase requires no completed or active release task"
            )

        documents: List[Dict[str, str]] = []
        for raw_path in document_paths:
            resolved = raw_path.resolve()
            try:
                rel_path = resolved.relative_to(self.root).as_posix()
            except ValueError as exc:
                raise ControlError(
                    "architecture documents must be stored inside project"
                ) from exc
            if not resolved.is_file() or _is_symlink_or_junction(resolved):
                raise ControlError(
                    f"architecture document must be a regular file: {rel_path}"
                )
            documents.append({"path": rel_path, "sha256": _sha256_file(resolved)})

        expected = {item["path"]: item["sha256"] for item in documents}
        registry = self._load_tasks_document()
        if str(registry.get("architecture_version")) != version:
            raise ControlError(
                "task registry architecture_version does not match rebase version"
            )
        for task in self.load_tasks():
            if dict(task.locked_verification_inputs) != expected:
                raise ControlError(
                    f"{task.task_id} does not lock the complete architecture bundle"
                )

        rebases = list(state.get("architecture_rebases", []))
        rebases.append(
            {
                "previous_version": state.get("architecture_version"),
                "new_version": version,
                "documents": documents,
                "rebased_at": _utc_now(),
            }
        )
        first_task = self.load_tasks()[0]
        state.update(
            {
                "queue_id": registry.get("queue_id", state.get("queue_id")),
                "architecture_version": version,
                "architecture_documents": documents,
                "architecture_document": documents[-1],
                "architecture_rebases": rebases,
                "status": first_task.pending_status,
                "next_task": first_task.task_id,
                "release_gate_evidence": {},
                "media_visual_acceptance": False,
                "owner_production_approval": False,
                "a10_gate_status": "MEDIA_EVIDENCE_REQUIRED",
                "external_submission": False,
                "production_switch_authorized": False,
                "updated_at": _utc_now(),
            }
        )
        _atomic_write_json(self.state_path, state)
        return state

    def record_media_acceptance(
        self, owner: str, token: str, evidence_path: Path
    ) -> Dict[str, Any]:
        state = self._require_lock("A10", owner, token)
        resolved = evidence_path.resolve()
        try:
            rel_path = resolved.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ControlError("media evidence must be stored inside project") from exc
        if not _path_allowed(rel_path, [MEDIA_EVIDENCE_GLOB]):
            raise ControlError("media evidence must be inside the A10 run directory")
        payload = _read_json(resolved)
        if payload.get("kind") != "MEDIA_VISUAL_ACCEPTANCE":
            raise ControlError("media evidence kind must be MEDIA_VISUAL_ACCEPTANCE")
        if payload.get("accepted") is not True:
            raise ControlError("media evidence must explicitly be accepted")
        for field in ("media_runs", "frame_evidence"):
            value = payload.get(field)
            if not isinstance(value, list) or not value:
                raise ControlError(f"media evidence {field} must be non-empty")
        comparison = payload.get("v4_vnext_comparison")
        if not isinstance(comparison, dict) or not comparison:
            raise ControlError("media evidence needs a v4_vnext_comparison")
        if payload.get("production_switch_authorized") is not False:
            raise ControlError("media evidence cannot authorize production switching")

        records = dict(state.get("release_gate_evidence", {}))
        records["media_visual_acceptance"] = {
            "path": rel_path,
            "sha256": _sha256_file(resolved),
            "recorded_at": _utc_now(),
            "recorded_by": owner,
        }
        records.pop("owner_production_approval", None)
        state.update(
            {
                "release_gate_evidence": records,
                "media_visual_acceptance": True,
                "owner_production_approval": False,
                "a10_gate_status": "OWNER_APPROVAL_REQUIRED",
                "external_submission": True,
                "production_switch_authorized": False,
                "updated_at": _utc_now(),
            }
        )
        _atomic_write_json(self.state_path, state)
        return state

    def record_owner_approval(
        self, approved_by: str, evidence_path: Path
    ) -> Dict[str, Any]:
        if not approved_by.strip():
            raise ControlError("approved_by must be non-empty")
        state = self.load_state()
        if state.get("status") != "IN_PROGRESS" or state.get("current_task") != "A10":
            raise ControlError("owner approval requires an active A10 claim")
        records = dict(state.get("release_gate_evidence", {}))
        media = records.get("media_visual_acceptance")
        if not state.get("media_visual_acceptance") or not isinstance(media, dict):
            raise ControlError("owner approval requires recorded media acceptance")

        resolved = evidence_path.resolve()
        try:
            rel_path = resolved.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ControlError("owner approval must be stored inside project") from exc
        if not _path_allowed(rel_path, [OWNER_APPROVAL_GLOB]):
            raise ControlError(
                "owner approval must be inside the independent approval directory"
            )
        payload = _read_json(resolved)
        if payload.get("kind") != "OWNER_PREVIEW_APPROVAL":
            raise ControlError("owner evidence kind must be OWNER_PREVIEW_APPROVAL")
        if payload.get("approved") is not True:
            raise ControlError("owner evidence must explicitly approve the preview")
        if payload.get("approved_by") != approved_by:
            raise ControlError("approved_by does not match owner evidence")
        if payload.get("scope") != "OWNER_APPROVED_PREVIEW":
            raise ControlError("owner approval scope must be OWNER_APPROVED_PREVIEW")
        if payload.get("media_evidence_sha256") != media.get("sha256"):
            raise ControlError("owner approval must bind current media evidence hash")
        if payload.get("production_switch_authorized") is not False:
            raise ControlError("owner approval cannot authorize production switching")

        records["owner_production_approval"] = {
            "path": rel_path,
            "sha256": _sha256_file(resolved),
            "recorded_at": _utc_now(),
            "approved_by": approved_by,
        }
        state.update(
            {
                "release_gate_evidence": records,
                "owner_production_approval": True,
                "a10_gate_status": "OWNER_APPROVED_PREVIEW",
                "production_switch_authorized": False,
                "updated_at": _utc_now(),
            }
        )
        _atomic_write_json(self.state_path, state)
        return state

    def _assert_a10_gates(self) -> None:
        issues = self._gate_record_issues()
        state = self.load_state()
        if not state.get("media_visual_acceptance"):
            issues.append("A10 requires media visual acceptance")
        if not state.get("owner_production_approval"):
            issues.append("A10 requires explicit owner preview approval")
        if issues:
            raise ControlError("A10 release gates failed: " + "; ".join(issues))

    def complete(
        self,
        task_id: str,
        owner: str,
        token: str,
        evidence_path: Path,
    ) -> Dict[str, Any]:
        pre_state = self._require_lock(task_id, owner, token)
        if pre_state.get("production_entry") != "v4_unchanged":
            raise ControlError("release completion cannot change the production entry")
        if pre_state.get("production_switch_authorized") is not False:
            raise ControlError("release completion cannot authorize production switching")
        if task_id == "A10":
            self._assert_a10_gates()
        state = super().complete(task_id, owner, token, evidence_path)
        return state

    def _clear_a10_gates(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state.update(
            {
                "release_gate_evidence": {},
                "media_visual_acceptance": False,
                "owner_production_approval": False,
                "a10_gate_status": "MEDIA_EVIDENCE_REQUIRED",
                "production_switch_authorized": False,
                "updated_at": _utc_now(),
            }
        )
        _atomic_write_json(self.state_path, state)
        return state

    def fail(
        self,
        task_id: str,
        owner: str,
        token: str,
        evidence_path: Optional[Path],
    ) -> Dict[str, Any]:
        state = super().fail(task_id, owner, token, evidence_path)
        return self._clear_a10_gates(state) if task_id == "A10" else state

    def invalidate(self, task_id: str, *, owner: str, reason: str) -> Dict[str, Any]:
        state = super().invalidate(task_id, owner=owner, reason=reason)
        return self._clear_a10_gates(state) if task_id == "A10" else state


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MODE:P vNext architecture-v2 release control"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="explicit project root, primarily for isolated verification",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit")
    sub.add_parser("status")
    sub.add_parser("next")

    claim = sub.add_parser("claim")
    claim.add_argument("task_id")
    claim.add_argument("--owner", required=True)

    complete = sub.add_parser("complete")
    complete.add_argument("task_id")
    complete.add_argument("--owner", required=True)
    complete.add_argument("--token", required=True)
    complete.add_argument("--evidence", required=True, type=Path)

    fail = sub.add_parser("fail")
    fail.add_argument("task_id")
    fail.add_argument("--owner", required=True)
    fail.add_argument("--token", required=True)
    fail.add_argument("--evidence", type=Path)

    recover = sub.add_parser("recover")
    recover.add_argument("--force", action="store_true")

    invalidate = sub.add_parser("invalidate")
    invalidate.add_argument("task_id")
    invalidate.add_argument("--owner", required=True)
    invalidate.add_argument("--reason", required=True)

    rebase = sub.add_parser("rebase-architecture")
    rebase.add_argument("--version", required=True)
    rebase.add_argument("--document", required=True, action="append", type=Path)

    media = sub.add_parser("record-media-acceptance")
    media.add_argument("--owner", required=True)
    media.add_argument("--token", required=True)
    media.add_argument("--evidence", required=True, type=Path)

    approval = sub.add_parser("record-owner-approval")
    approval.add_argument("--approved-by", required=True)
    approval.add_argument("--evidence", required=True, type=Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    _configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    control = (
        ReleaseControl(args.project_root)
        if args.project_root is not None
        else ReleaseControl.default()
    )
    try:
        if args.command == "audit":
            issues = control.audit()
            _print_json({"ok": not issues, "issues": issues})
            return 0 if not issues else 1
        if args.command == "status":
            _print_json(control.load_state())
            return 0
        if args.command == "next":
            task = control.next_task()
            _print_json(None if task is None else asdict(task))
            return 0
        if args.command == "claim":
            _print_json(_claim_summary(control.claim(args.task_id, args.owner)))
            return 0
        if args.command == "complete":
            _print_json(
                control.complete(
                    args.task_id,
                    args.owner,
                    args.token,
                    args.evidence,
                )
            )
            return 0
        if args.command == "fail":
            _print_json(
                control.fail(
                    args.task_id,
                    args.owner,
                    args.token,
                    args.evidence,
                )
            )
            return 0
        if args.command == "recover":
            _print_json(control.recover(force=args.force))
            return 0
        if args.command == "invalidate":
            _print_json(
                control.invalidate(
                    args.task_id,
                    owner=args.owner,
                    reason=args.reason,
                )
            )
            return 0
        if args.command == "rebase-architecture":
            _print_json(
                control.rebase_architecture(args.version, args.document)
            )
            return 0
        if args.command == "record-media-acceptance":
            _print_json(
                control.record_media_acceptance(
                    args.owner, args.token, args.evidence
                )
            )
            return 0
        if args.command == "record-owner-approval":
            _print_json(
                control.record_owner_approval(
                    args.approved_by, args.evidence
                )
            )
            return 0
    except ControlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
