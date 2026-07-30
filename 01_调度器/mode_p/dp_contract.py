"""Natural-language DP issue lines and Master-bound anti-stall identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


DP_READY_SENTENCE = (
    "READY S1: Shot S1-1 的机位位于已定义空间内，入口边界与0秒人物位置一致。"
)
DP_READY_FORMAT = "READY <scene_id>: <cite current Shot ID(s) and one concrete observed reason>"
DP_VALID_FIELDS = {
    "story_fidelity",
    "shot_intent",
    "camera_position",
    "camera_path",
    "spatial_feasibility",
    "axis_eyeline",
    "screen_direction",
    "action_continuity",
    "performance_visibility",
    "composition_focus",
    "depth_layering",
    "light_source",
    "light_continuity",
    "transition_motivation",
    "transition_execution",
    "duration",
    "prompt_visibility",
    "reference_conflict",
    "reference_missing",
    "mode_capability",
    "boundary_continuity",
    "view_sync",
}
_SHOT_ID_RE = re.compile(r"^[A-Za-z0-9_-]+-\d+$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_ISSUE_LINE_RE = re.compile(
    r"^(?:[-*]\s*)?(?:Shot\s+)?(?P<id>[A-Za-z0-9_-]+-\d+)\s*:\s*"
    r"(?P<field>[a-z_]+)\s*(?:—|–|-)\s*(?P<detail>\S.*)$"
)
_READY_LINE_RE = re.compile(
    r"^READY\s+(?P<scene_id>[A-Za-z0-9_-]+)\s*:\s*(?P<detail>\S.*)$"
)
_INPUT_BLOCKED_RE = re.compile(r"^DP_INPUT_BLOCKED\s*:\s*(?P<reason>\S.*)$")
_SHOT_MENTION_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?P<id>[A-Za-z0-9_-]+-\d+)(?![A-Za-z0-9_.-])"
)
_MAX_DETAIL_CHARS = 240
_MIN_READY_DETAIL_CHARS = 18
_READY_EVIDENCE_TERMS = (
    "位置", "路径", "空间", "关系线", "视线", "方向", "动作", "边界", "切点",
    "机位", "运镜", "轴线", "连续", "同步", "状态", "时间线", "表演", "景别",
    "光", "光源", "光向", "光比", "色温", "锚点", "构图", "景深", "焦段",
    "参考", "模式", "时长",
    "position", "path", "space", "axis", "eyeline", "direction", "action",
    "camera", "movement", "continuity", "sync", "state", "timeline", "performance",
    "boundary", "cut", "light", "anchor", "composition", "depth", "lens",
    "reference", "mode", "duration",
)


class DpContractError(ValueError):
    """Raised when feedback cannot safely control the loop."""


@dataclass(frozen=True)
class DpIssue:
    shot_id: str
    field: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"shot_id": self.shot_id, "field": self.field, "detail": self.detail}

    def identity(self) -> dict[str, str]:
        return {"shot_id": self.shot_id, "field": self.field}


@dataclass(frozen=True)
class DpReadyEvidence:
    scene_id: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"scene_id": self.scene_id, "detail": self.detail}


@dataclass
class DpFeedback:
    status: str
    issues: list[DpIssue] = field(default_factory=list)
    raw_text: str = ""
    parse_errors: list[str] = field(default_factory=list)
    ready_evidence: list[DpReadyEvidence] = field(default_factory=list)
    block_reason: str = ""

    @property
    def is_ready(self) -> bool:
        return (
            self.status == "ready" and bool(self.ready_evidence)
            and not self.issues and not self.parse_errors
        )

    def fingerprint(self, master_sha256: str) -> str:
        """Hash only stable issue identity and the exact reviewed Master."""
        if not _HASH_RE.fullmatch(master_sha256):
            raise DpContractError("current Master SHA-256 is required for a DP fingerprint")
        valid, problems = validate_dp_contract(self)
        if not valid or self.status != "issues":
            raise DpContractError(
                "only valid issue feedback has an anti-stall fingerprint: "
                + "; ".join(problems or [self.status])
            )
        identities = sorted(
            (issue.identity() for issue in self.issues),
            key=lambda item: (item["shot_id"], item["field"]),
        )
        payload = {
            "master_sha256": master_sha256,
            "issues": identities,
        }
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def parse_dp_feedback(text: str) -> DpFeedback:
    """Parse scene-bound READY evidence or one natural issue per line."""
    if not isinstance(text, str):
        return DpFeedback("invalid", parse_errors=["feedback must be text"])
    stripped = text.strip()
    if not stripped:
        return DpFeedback("invalid", raw_text=text, parse_errors=["DP feedback is empty"])
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    blocked_matches = [_INPUT_BLOCKED_RE.fullmatch(line) for line in lines]
    if len(lines) == 1 and blocked_matches[0] is not None:
        return DpFeedback(
            "blocked",
            raw_text=text,
            block_reason=blocked_matches[0].group("reason").strip(),
        )
    if any(match is not None for match in blocked_matches):
        return DpFeedback(
            "invalid", raw_text=text,
            parse_errors=["DP_INPUT_BLOCKED must be the only feedback line"],
        )
    ready_matches = [_READY_LINE_RE.fullmatch(line) for line in lines]
    if lines and all(match is not None for match in ready_matches):
        return DpFeedback(
            "ready",
            raw_text=text,
            ready_evidence=[
                DpReadyEvidence(match.group("scene_id"), match.group("detail").strip())
                for match in ready_matches if match is not None
            ],
        )
    if any(match is not None for match in ready_matches):
        return DpFeedback(
            "invalid", raw_text=text,
            parse_errors=["READY evidence cannot be mixed with issues or free text"],
        )

    issues: list[DpIssue] = []
    errors: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        match = _ISSUE_LINE_RE.fullmatch(line)
        if not match:
            errors.append(f"line {line_number} does not match the DP issue contract")
            continue
        issues.append(DpIssue(
            shot_id=match.group("id"),
            field=match.group("field"),
            detail=match.group("detail").strip(),
        ))
    status = "issues" if issues and not errors else "invalid"
    return DpFeedback(status, issues, text, errors)


def validate_dp_contract(
    feedback: DpFeedback,
    valid_shot_ids: set[str] | None = None,
) -> tuple[bool, list[str]]:
    """Validate shape and, when supplied, bind every issue to the Manifest."""
    problems = list(feedback.parse_errors)
    if feedback.status not in {"ready", "issues", "blocked", "invalid"}:
        problems.append(f"invalid DP status: {feedback.status}")
    if feedback.status == "blocked":
        reason = feedback.block_reason.strip()
        if len(reason) < 8:
            problems.append("DP_INPUT_BLOCKED requires a concrete missing-input reason")
        if len(reason) > _MAX_DETAIL_CHARS:
            problems.append(
                f"DP_INPUT_BLOCKED reason exceeds {_MAX_DETAIL_CHARS} characters"
            )
        if feedback.issues or feedback.ready_evidence:
            problems.append("DP_INPUT_BLOCKED cannot contain READY evidence or issues")
        return not problems, problems
    if feedback.status == "ready":
        if feedback.issues:
            problems.append("READY feedback cannot contain issues")
        if not feedback.ready_evidence:
            problems.append("READY requires scene-specific evidence")
            return False, problems
        seen_scenes: set[str] = set()
        expected_scenes = (
            {_scene_id_from_shot(item) for item in valid_shot_ids}
            if valid_shot_ids is not None else None
        )
        for evidence in feedback.ready_evidence:
            if evidence.scene_id in seen_scenes:
                problems.append(f"duplicate READY scene: {evidence.scene_id}")
            seen_scenes.add(evidence.scene_id)
            detail = evidence.detail.strip()
            if len(detail) < _MIN_READY_DETAIL_CHARS:
                problems.append(
                    f"READY evidence is too short for scene {evidence.scene_id}"
                )
            elif len(detail) > _MAX_DETAIL_CHARS:
                problems.append(
                    f"READY evidence exceeds {_MAX_DETAIL_CHARS} characters for "
                    f"scene {evidence.scene_id}"
                )
            if not any(term.casefold() in detail.casefold() for term in _READY_EVIDENCE_TERMS):
                problems.append(
                    f"READY evidence for {evidence.scene_id} names no observable review dimension"
                )
            mentioned = {match.group("id") for match in _SHOT_MENTION_RE.finditer(detail)}
            if not mentioned:
                problems.append(
                    f"READY evidence for {evidence.scene_id} must cite a current Shot ID"
                )
            elif any(_scene_id_from_shot(item) != evidence.scene_id for item in mentioned):
                problems.append(
                    f"READY evidence for {evidence.scene_id} cites a Shot from another scene"
                )
            if valid_shot_ids is not None and any(
                item not in valid_shot_ids for item in mentioned
            ):
                problems.append(
                    f"READY evidence for {evidence.scene_id} cites a Shot absent from current Manifests"
                )
        if expected_scenes is not None and seen_scenes != expected_scenes:
            problems.append(
                "READY evidence must cover every reviewed scene exactly once: "
                f"expected {sorted(expected_scenes)}, got {sorted(seen_scenes)}"
            )
        return not problems, problems
    if feedback.status != "issues" or not feedback.issues:
        problems.append("DP issue feedback must contain at least one valid issue line")
        return False, problems

    seen: set[tuple[str, str]] = set()
    for issue in feedback.issues:
        identity = (issue.shot_id, issue.field)
        if not _SHOT_ID_RE.fullmatch(issue.shot_id):
            problems.append(f"invalid Shot ID: {issue.shot_id}")
        elif valid_shot_ids is not None and issue.shot_id not in valid_shot_ids:
            problems.append(f"Shot ID is absent from current Manifest: {issue.shot_id}")
        if issue.field not in DP_VALID_FIELDS:
            problems.append(f"invalid issue field '{issue.field}' for {issue.shot_id}")
        if not issue.detail.strip():
            problems.append(f"empty detail for {issue.shot_id}.{issue.field}")
        elif len(issue.detail) > _MAX_DETAIL_CHARS:
            problems.append(
                f"detail exceeds {_MAX_DETAIL_CHARS} characters for "
                f"{issue.shot_id}.{issue.field}"
            )
        if identity in seen:
            problems.append(f"duplicate issue identity: {issue.shot_id}.{issue.field}")
        seen.add(identity)
    return not problems, problems


def _scene_id_from_shot(shot_id: str) -> str:
    return shot_id.rsplit("-", 1)[0]


def detect_stall(previous_fingerprints: list[str], current_fingerprint: str) -> bool:
    if not _HASH_RE.fullmatch(current_fingerprint):
        raise DpContractError("current fingerprint is invalid")
    if any(not _HASH_RE.fullmatch(item) for item in previous_fingerprints):
        raise DpContractError("fingerprint history is malformed")
    return current_fingerprint in previous_fingerprints


def manifest_shot_ids(manifest_path: Path) -> set[str]:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DpContractError(f"cannot read current Manifest: {exc}") from exc
    shots = data.get("shots") if isinstance(data, dict) else None
    if not isinstance(shots, list) or not shots:
        raise DpContractError("current Manifest contains no shots")
    ids = [shot.get("shot_id") for shot in shots if isinstance(shot, dict)]
    if len(ids) != len(shots) or any(not isinstance(item, str) for item in ids):
        raise DpContractError("current Manifest Shot IDs are malformed")
    if len(ids) != len(set(ids)):
        raise DpContractError("current Manifest contains duplicate Shot IDs")
    return set(ids)


def manifest_shot_ids_many(manifest_paths: list[Path]) -> set[str]:
    """Return the disjoint Shot-ID union for one DP batch."""
    if not manifest_paths:
        raise DpContractError("at least one current Manifest is required")
    union: set[str] = set()
    for path in manifest_paths:
        current = manifest_shot_ids(path)
        overlap = union & current
        if overlap:
            raise DpContractError(
                f"duplicate Shot IDs across current Manifests: {sorted(overlap)}"
            )
        union.update(current)
    return union


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Master-bound DP feedback.")
    parser.add_argument("feedback", type=Path)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--master-sha256")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        feedback = parse_dp_feedback(args.feedback.read_text(encoding="utf-8"))
        valid, problems = validate_dp_contract(
            feedback, manifest_shot_ids_many(args.manifest)
        )
        fingerprint = (
            feedback.fingerprint(args.master_sha256)
            if valid and feedback.status == "issues" and args.master_sha256 else None
        )
        if args.json:
            print(json.dumps({
                "valid": valid,
                "status": feedback.status,
                "issues": [issue.to_dict() for issue in feedback.issues],
                "ready_evidence": [
                    item.to_dict() for item in feedback.ready_evidence
                ],
                "fingerprint": fingerprint,
                "problems": problems,
            }, ensure_ascii=False, indent=2))
        elif valid:
            print("DP feedback contract valid.")
        else:
            print("\n".join(problems), file=sys.stderr)
        return 0 if valid else 1
    except (OSError, UnicodeError, DpContractError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
