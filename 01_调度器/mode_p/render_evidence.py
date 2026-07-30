"""Render evidence schema — manage external real-render evidence for MODE:P learning.

MODE:P does NOT render. This module defines the data structures and validation
for external Jimeng SD2.0 render results, user observations, and their
correlation with Master/asset versions.

Evidence flows through the experience pipeline:
    render_case -> candidate -> repeated -> validated -> knowledge
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVIDENCE_SCHEMA_VERSION = "1.0"
EXPERIENCE_DIR = Path(__file__).resolve().parent.parent.parent / "05_项目经验"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class RenderEvidence:
    """One external render result with its generation context."""
    evidence_id: str
    master_sha256: str
    master_version: int
    scene_id: str
    shot_ids: list[str] = field(default_factory=list)
    generation_mode: str = ""          # pure_prompt | keyframes | omni_reference
    reference_assets: list[str] = field(default_factory=list)  # asset_ids
    asset_versions: dict[str, str] = field(default_factory=dict)  # asset_id -> content hash/version
    prompt_text: str = ""
    render_output_path: str = ""       # path to render result (image/video)
    sd2_capability_version: str = ""
    recorded_at: str = ""

    def __post_init__(self):
        if not self.recorded_at:
            self.recorded_at = datetime.now(timezone.utc).isoformat()


@dataclass
class UserObservation:
    """Human observation about a render result."""
    observation_id: str
    evidence_id: str
    what_worked: str = ""
    what_failed: str = ""
    root_cause: str = ""
    suggestion: str = ""
    confidence: str = ""  # high / medium / low / uncertain
    observer: str = ""
    observed_at: str = ""

    def __post_init__(self):
        if not self.observed_at:
            self.observed_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ExperienceCandidate:
    """A candidate experience extracted from render evidence."""
    candidate_id: str
    title: str
    description: str
    evidence_ids: list[str] = field(default_factory=list)
    observation_ids: list[str] = field(default_factory=list)
    applicability: str = ""           # when this experience applies
    non_applicability: str = ""       # when it does NOT apply
    invariants: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    generation_mode: str = ""
    reference_pattern: str = ""       # asset_id:responsibility combinations observed
    master_version: int = 0
    asset_versions: dict[str, str] = field(default_factory=dict)  # asset_id -> hash
    status: str = "candidate"         # candidate | repeated | validated | rejected
    rejection_reason: str = ""
    promotion_log: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_evidence(evidence: RenderEvidence) -> list[str]:
    """Validate that render evidence is real and complete. Returns error list."""
    errors: list[str] = []
    if not evidence.evidence_id.strip():
        errors.append("evidence_id is required")
    if len(evidence.master_sha256) != 64:
        errors.append("master_sha256 must be 64 hex chars")
    if not evidence.scene_id.strip():
        errors.append("scene_id is required")
    if evidence.generation_mode not in ("pure_prompt", "keyframes", "omni_reference"):
        errors.append(f"unknown generation_mode: {evidence.generation_mode}")
    if not evidence.render_output_path.strip():
        errors.append("render_output_path is required (real render evidence)")
    output = Path(evidence.render_output_path)
    if not output.exists():
        errors.append(f"render_output_path does not exist: {evidence.render_output_path}")
    missing_asset_versions = [
        asset_id for asset_id in evidence.reference_assets
        if not str(evidence.asset_versions.get(asset_id, "")).strip()
    ]
    if missing_asset_versions:
        errors.append(
            "asset_versions missing for reference_assets: "
            + ", ".join(sorted(missing_asset_versions))
        )
    return errors


def validate_candidate(candidate: ExperienceCandidate) -> list[str]:
    """Validate a candidate experience. Returns error list."""
    errors: list[str] = []
    if not candidate.candidate_id.strip():
        errors.append("candidate_id is required")
    if not candidate.title.strip():
        errors.append("title is required")
    if not candidate.description.strip():
        errors.append("description is required")
    if not candidate.evidence_ids:
        errors.append("at least one evidence_id is required (no real render evidence)")
    if not candidate.applicability.strip():
        errors.append("applicability conditions are required")
    if candidate.status not in ("candidate", "repeated", "validated", "rejected"):
        errors.append(f"invalid status: {candidate.status}")
    unique_evidence = set(candidate.evidence_ids)
    unique_observations = set(candidate.observation_ids)
    if candidate.status in ("repeated", "validated"):
        if len(unique_evidence) < 2:
            errors.append(
                f"{candidate.status} requires at least two independent evidence_ids"
            )
        if len(unique_observations) < 2:
            errors.append(
                f"{candidate.status} requires at least two user observations"
            )
    if candidate.status == "validated":
        validation_logs = [
            entry for entry in candidate.promotion_log
            if entry.get("to_status") == "validated"
        ]
        if not validation_logs:
            errors.append("validated status requires a promotion log entry")
        else:
            latest = validation_logs[-1]
            if not str(latest.get("approved_by", "")).strip():
                errors.append("validated promotion requires approved_by")
            regression = latest.get("regression_report")
            if not isinstance(regression, dict) or not regression.get("passed"):
                errors.append("validated promotion requires a passed regression_report")
            elif not str(regression.get("command", "")).strip():
                errors.append("validated regression_report requires command")
    if candidate.status == "rejected" and not candidate.rejection_reason.strip():
        errors.append("rejection_reason is required for rejected candidates")
    return errors


def validate_candidate_evidence(
    candidate: ExperienceCandidate,
    base_dir: Path | None = None,
) -> tuple[list[str], set[str]]:
    """Validate that candidate evidence points to real render cases.

    This check is intentionally separate from ``validate_candidate`` so draft
    candidates can be edited or imported before all referenced cases exist.
    Promotion and export must call this stricter check.
    """
    if base_dir is None:
        base_dir = EXPERIENCE_DIR

    errors: list[str] = []
    scene_ids: set[str] = set()
    known_observation_ids: set[str] = set()
    observation_ids_by_evidence: dict[str, set[str]] = {}

    for evidence_id in sorted(set(candidate.evidence_ids)):
        try:
            evidence, observations = load_render_case(evidence_id, base_dir)
        except FileNotFoundError:
            errors.append(f"referenced render case not found: {evidence_id}")
            continue

        evidence_errors = validate_evidence(evidence)
        if evidence_errors:
            errors.extend(
                f"{evidence_id}: {error}" for error in evidence_errors
            )
        scene_ids.add(evidence.scene_id)

        case_observation_ids = {
            observation.observation_id for observation in observations
            if observation.evidence_id == evidence_id
        }
        observation_ids_by_evidence[evidence_id] = case_observation_ids
        known_observation_ids.update(case_observation_ids)

        if not case_observation_ids:
            errors.append(f"{evidence_id}: at least one user observation is required")

    missing_observations = sorted(set(candidate.observation_ids) - known_observation_ids)
    if missing_observations:
        errors.append(
            "observation_ids are not present in referenced render cases: "
            + ", ".join(missing_observations)
        )

    candidate_observations = set(candidate.observation_ids)
    for evidence_id, case_observation_ids in observation_ids_by_evidence.items():
        if not (case_observation_ids & candidate_observations):
            errors.append(
                f"{evidence_id}: candidate must cite at least one observation "
                "from this render case"
            )

    return errors, scene_ids


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    _ensure_dir(path.parent)
    descriptor = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        payload = (
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def save_render_case(evidence: RenderEvidence, observations: list[UserObservation],
                     base_dir: Path | None = None) -> Path:
    """Save a render case (evidence + observations) atomically."""
    if base_dir is None:
        base_dir = EXPERIENCE_DIR
    case_dir = base_dir / "render_cases" / evidence.evidence_id
    _ensure_dir(case_dir)

    errors = validate_evidence(evidence)
    if errors:
        raise ValueError(f"Invalid render evidence: {'; '.join(errors)}")

    # Write evidence manifest
    evidence_data = asdict(evidence)
    evidence_data["schema_version"] = EVIDENCE_SCHEMA_VERSION
    _write_json(case_dir / "evidence.json", evidence_data)

    # Write observations
    obs_list = []
    for obs in observations:
        if obs.evidence_id != evidence.evidence_id:
            raise ValueError(
                f"Observation {obs.observation_id} references wrong evidence_id"
            )
        obs_list.append(asdict(obs))
    _write_json(case_dir / "observations.json", {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "observations": obs_list,
    })

    return case_dir


def load_render_case(evidence_id: str, base_dir: Path | None = None
                     ) -> tuple[RenderEvidence, list[UserObservation]]:
    """Load a render case from disk."""
    if base_dir is None:
        base_dir = EXPERIENCE_DIR
    case_dir = base_dir / "render_cases" / evidence_id
    if not case_dir.is_dir():
        raise FileNotFoundError(f"Render case not found: {evidence_id}")

    ev_data = json.loads((case_dir / "evidence.json").read_text(encoding="utf-8"))
    evidence = RenderEvidence(**{k: v for k, v in ev_data.items()
                                  if k != "schema_version"})

    obs_path = case_dir / "observations.json"
    observations: list[UserObservation] = []
    if obs_path.exists():
        obs_data = json.loads(obs_path.read_text(encoding="utf-8"))
        for o in obs_data.get("observations", []):
            observations.append(UserObservation(**{k: v for k, v in o.items()
                                                    if k != "schema_version"}))

    return evidence, observations


def save_candidate(candidate: ExperienceCandidate, base_dir: Path | None = None) -> Path:
    """Save a candidate experience."""
    if base_dir is None:
        base_dir = EXPERIENCE_DIR
    errors = validate_candidate(candidate)
    if errors:
        raise ValueError(f"Invalid candidate: {'; '.join(errors)}")

    target = _candidate_path(base_dir, candidate.status, candidate.candidate_id)
    data = asdict(candidate)
    data["schema_version"] = EVIDENCE_SCHEMA_VERSION
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def load_candidate(candidate_id: str, base_dir: Path | None = None
                   ) -> ExperienceCandidate | None:
    """Load a candidate from any status directory."""
    if base_dir is None:
        base_dir = EXPERIENCE_DIR
    for status in ("candidates", "repeated", "validated", "rejected"):
        path = base_dir / status / f"{candidate_id}.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return ExperienceCandidate(**{k: v for k, v in data.items()
                                           if k != "schema_version"})
    return None


def list_candidates(status: str = "candidate", base_dir: Path | None = None
                    ) -> list[str]:
    """List candidate IDs in a given status directory."""
    if base_dir is None:
        base_dir = EXPERIENCE_DIR
    target = base_dir / _status_dir(status)
    if not target.is_dir():
        return []
    return sorted(
        p.stem for p in target.glob("*.json")
        if p.stem != "README"
    )


def promote_candidate(
    candidate_id: str,
    new_status: str,
    base_dir: Path | None = None,
    *,
    approved_by: str = "",
    regression_report: dict[str, Any] | None = None,
    rejection_reason: str = "",
) -> ExperienceCandidate:
    """Promote a candidate to a new status with enforced evidence rules."""
    if base_dir is None:
        base_dir = EXPERIENCE_DIR
    candidate = load_candidate(candidate_id, base_dir)
    if candidate is None:
        raise FileNotFoundError(f"Candidate not found: {candidate_id}")

    valid_transitions = {
        "candidate": ("repeated", "rejected"),
        "repeated": ("validated", "rejected"),
        "validated": ("rejected",),
        "rejected": ("candidate",),  # can reopen
    }
    allowed = valid_transitions.get(candidate.status, ())
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from '{candidate.status}' to '{new_status}'. "
            f"Allowed: {allowed}"
        )

    old_status = candidate.status
    updated = ExperienceCandidate(**asdict(candidate))
    updated.status = new_status
    updated.updated_at = datetime.now(timezone.utc).isoformat()
    if new_status == "rejected":
        updated.rejection_reason = rejection_reason or updated.rejection_reason
    elif new_status == "candidate":
        updated.rejection_reason = ""
    elif new_status == "validated":
        if not approved_by.strip():
            raise ValueError("validated promotion requires --approved-by")
        if not regression_report or not regression_report.get("passed"):
            raise ValueError("validated promotion requires a passed regression report")
        if not str(regression_report.get("command", "")).strip():
            raise ValueError("validated regression report requires command")

    updated.promotion_log.append({
        "at": updated.updated_at,
        "from_status": old_status,
        "to_status": new_status,
        "approved_by": approved_by.strip(),
        "regression_report": regression_report or {},
        "evidence_ids": sorted(set(updated.evidence_ids)),
        "observation_ids": sorted(set(updated.observation_ids)),
    })

    errors = validate_candidate(updated)
    if errors:
        raise ValueError(f"Invalid promotion: {'; '.join(errors)}")
    if new_status in ("repeated", "validated"):
        evidence_errors, scene_ids = validate_candidate_evidence(updated, base_dir)
        if new_status == "validated" and len(scene_ids) < 2:
            evidence_errors.append(
                "validated promotion requires evidence from at least two different scenes"
            )
        if evidence_errors:
            raise ValueError(f"Invalid promotion evidence: {'; '.join(evidence_errors)}")

    _save_rollback_snapshot(candidate, base_dir, new_status)
    old_path = _candidate_path(base_dir, old_status, candidate_id)
    if old_path.is_file():
        old_path.unlink()
    return save_candidate(updated, base_dir)


def rollback_promotion(candidate_id: str,
                       base_dir: Path | None = None) -> ExperienceCandidate:
    """Restore the latest pre-promotion snapshot for a candidate."""
    if base_dir is None:
        base_dir = EXPERIENCE_DIR
    history_dir = base_dir / ".promotion_history" / candidate_id
    snapshots = sorted(history_dir.glob("*.json"))
    if not snapshots:
        raise FileNotFoundError(f"No rollback snapshot found for {candidate_id}")
    latest = snapshots[-1]
    data = json.loads(latest.read_text(encoding="utf-8"))
    candidate_data = data["candidate"]
    restored = ExperienceCandidate(**{
        key: value for key, value in candidate_data.items()
        if key != "schema_version"
    })
    current = load_candidate(candidate_id, base_dir)
    if current is not None:
        current_path = _candidate_path(base_dir, current.status, candidate_id)
        if current_path.is_file():
            current_path.unlink()
    save_candidate(restored, base_dir)
    return restored


def _status_dir(status: str) -> str:
    return {
        "candidate": "candidates",
        "repeated": "repeated",
        "validated": "validated",
        "rejected": "rejected",
    }.get(status, "candidates")


def _candidate_path(base_dir: Path, status: str, candidate_id: str) -> Path:
    return base_dir / _status_dir(status) / f"{candidate_id}.json"


def _save_rollback_snapshot(
    candidate: ExperienceCandidate,
    base_dir: Path,
    target_status: str,
) -> Path:
    snapshot_dir = base_dir / ".promotion_history" / candidate.candidate_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = (
        snapshot_dir /
        f"{stamp}_{candidate.status}_to_{target_status}_{uuid.uuid4().hex[:8]}.json"
    )
    payload = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "snapshot_type": "pre_promotion",
        "candidate": asdict(candidate),
    }
    _write_json(path, payload)
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage MODE:P render evidence and experience candidates."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    list_p = sub.add_parser("list", help="List candidates by status")
    list_p.add_argument("--status", default="candidate",
                        choices=("candidate", "repeated", "validated", "rejected"))

    # validate
    validate_p = sub.add_parser("validate", help="Validate a candidate")
    validate_p.add_argument("candidate_id")

    # promote
    promote_p = sub.add_parser("promote", help="Promote a candidate to a new status")
    promote_p.add_argument("candidate_id")
    promote_p.add_argument("new_status",
                           choices=("repeated", "validated", "rejected", "candidate"))
    promote_p.add_argument("--approved-by", default="",
                           help="Required for validated promotion")
    promote_p.add_argument("--regression-command", default="",
                           help="Command that passed before validated promotion")
    promote_p.add_argument("--regression-passed", action="store_true",
                           help="Declare that the regression command passed")
    promote_p.add_argument("--rejection-reason", default="",
                           help="Required when promoting to rejected")

    rollback_p = sub.add_parser("rollback", help="Rollback the latest promotion")
    rollback_p.add_argument("candidate_id")

    args = parser.parse_args()

    if args.command == "list":
        ids = list_candidates(args.status)
        if ids:
            for cid in ids:
                print(cid)
        else:
            print(f"(no {args.status} candidates)")
        return 0

    if args.command == "validate":
        candidate = load_candidate(args.candidate_id)
        if candidate is None:
            print(f"Candidate not found: {args.candidate_id}")
            return 1
        errors = validate_candidate(candidate)
        if errors:
            for e in errors:
                print(f"ERROR: {e}")
            return 1
        print(f"Candidate {args.candidate_id} is valid (status: {candidate.status})")
        return 0

    if args.command == "promote":
        try:
            regression_report = None
            if args.new_status == "validated":
                regression_report = {
                    "command": args.regression_command,
                    "passed": args.regression_passed,
                }
            promote_candidate(
                args.candidate_id,
                args.new_status,
                approved_by=args.approved_by,
                regression_report=regression_report,
                rejection_reason=args.rejection_reason,
            )
            print(f"Promoted {args.candidate_id} -> {args.new_status}")
            return 0
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return 1

    if args.command == "rollback":
        try:
            restored = rollback_promotion(args.candidate_id)
            print(f"Rolled back {args.candidate_id} -> {restored.status}")
            return 0
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
