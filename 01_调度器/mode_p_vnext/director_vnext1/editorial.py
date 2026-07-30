"""Text-only editorial review for a frozen VisualExecutionContract.

This module may identify an observable contract problem and its smallest
affected scope.  It is intentionally unable to prescribe a new shot, camera,
or edit; those choices stay with the persistent Director in a later revision.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple

from .contracts import DirectorContractError, VisualExecutionContract


MUTE_VISUAL_LOGIC = "MUTE_VISUAL_LOGIC"
DIALOGUE_REDUNDANCY = "DIALOGUE_REDUNDANCY"
REVIEW_MODES = frozenset({MUTE_VISUAL_LOGIC, DIALOGUE_REDUNDANCY})
TEXT_VALIDATED = "TEXT_VALIDATED"
TEXT_REVIEW_FAILED = "TEXT_REVIEW_FAILED"

# An observation names a failed contract condition, not its creative remedy.
_TAKEOVER_LANGUAGE = re.compile(
    r"(?:镜头|运镜|焦段|机位|剪辑|转场|\bcamera\b|\blens\b|\bshot\b|\bcut\b|\bedit\b)",
    re.IGNORECASE,
)


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise DirectorContractError(f"{field_name} is required")


@dataclass(frozen=True)
class EditorialIssue:
    issue_id: str
    issue_code: str
    severity: str
    contract_refs: Tuple[str, ...]
    observation: str
    affected_node_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("issue_id", self.issue_id),
            ("issue_code", self.issue_code),
            ("observation", self.observation),
        ):
            _require_text(value, field_name)
        if self.severity not in {"warning", "blocking"}:
            raise DirectorContractError("editorial issue severity is invalid")
        if not self.contract_refs or not self.affected_node_ids:
            raise DirectorContractError("editorial issue requires contract refs and an affected scope")
        if _TAKEOVER_LANGUAGE.search(self.observation):
            raise DirectorContractError("editorial review cannot prescribe an execution solution")


@dataclass(frozen=True)
class EditorialReviewRecord:
    review_id: str
    mode: str
    contract_fingerprint: str
    observed_contract_refs: Tuple[str, ...]
    issues: Tuple[EditorialIssue, ...]
    status: str
    scope: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("review_id", self.review_id),
            ("contract_fingerprint", self.contract_fingerprint),
            ("scope", self.scope),
        ):
            _require_text(value, field_name)
        if self.mode not in REVIEW_MODES:
            raise DirectorContractError("editorial review mode is invalid")
        if not self.observed_contract_refs:
            raise DirectorContractError("editorial review must identify observed contract fields")
        if self.status not in {TEXT_VALIDATED, TEXT_REVIEW_FAILED}:
            raise DirectorContractError("text review cannot claim visual realization or production acceptance")
        has_blocker = any(issue.severity == "blocking" for issue in self.issues)
        if (self.status == TEXT_VALIDATED) == has_blocker:
            raise DirectorContractError("text review status must reflect blocking observations")
        issue_ids = [issue.issue_id for issue in self.issues]
        if len(issue_ids) != len(set(issue_ids)):
            raise DirectorContractError("editorial issue IDs must be unique")


@dataclass(frozen=True)
class EditorialReviewBundle:
    mute_visual_logic: EditorialReviewRecord
    dialogue_redundancy: EditorialReviewRecord

    @property
    def status(self) -> str:
        if TEXT_REVIEW_FAILED in {self.mute_visual_logic.status, self.dialogue_redundancy.status}:
            return TEXT_REVIEW_FAILED
        return TEXT_VALIDATED


def review_vec_text(vec: VisualExecutionContract, mode: str) -> EditorialReviewRecord:
    """Review structural evidence only; no media/pixel claim is possible here."""

    if mode not in REVIEW_MODES:
        raise DirectorContractError("requested editorial mode is invalid")
    if mode == MUTE_VISUAL_LOGIC:
        return _review_mute_visual_logic(vec)
    return _review_dialogue_redundancy(vec)


def review_both_modes(vec: VisualExecutionContract) -> EditorialReviewBundle:
    return EditorialReviewBundle(
        mute_visual_logic=review_vec_text(vec, MUTE_VISUAL_LOGIC),
        dialogue_redundancy=review_vec_text(vec, DIALOGUE_REDUNDANCY),
    )


def _review_mute_visual_logic(vec: VisualExecutionContract) -> EditorialReviewRecord:
    refs: list[str] = []
    issues: list[EditorialIssue] = []
    for item in vec.visual_curve.points:
        refs.append(f"curve:{item.beat_id}")
        if item.attention_change == item.information_release:
            issues.append(
                EditorialIssue(
                    issue_id=f"MUTE-{item.beat_id}", issue_code="MUTE_LOGIC_UNSEPARATED",
                    severity="warning", contract_refs=(f"curve:{item.beat_id}",),
                    observation="attention change and information release use the same unresolved statement",
                    affected_node_ids=(f"curve:{item.beat_id}",),
                )
            )
    for item in vec.shots:
        refs.append(f"shot:{item.shot_id}:dramatic_function")
        if item.attention_target == item.information_action:
            issues.append(
                EditorialIssue(
                    issue_id=f"MUTE-SHOT-{item.shot_id}", issue_code="MUTE_ATTENTION_UNSEPARATED",
                    severity="warning", contract_refs=(f"shot:{item.shot_id}:attention_target",),
                    observation="attention target and information action are not separately stated",
                    affected_node_ids=(f"shot:{item.shot_id}",),
                )
            )
    return EditorialReviewRecord(
        review_id=f"ER-MUTE-{vec.contract_id}", mode=MUTE_VISUAL_LOGIC,
        contract_fingerprint=vec.fingerprint, observed_contract_refs=tuple(refs), issues=tuple(issues),
        status=TEXT_VALIDATED, scope=vec.scene_id,
    )


def _review_dialogue_redundancy(vec: VisualExecutionContract) -> EditorialReviewRecord:
    refs = [f"dialogue:{event.event_id}" for event in vec.dialogue_events]
    issues: list[EditorialIssue] = []
    seen: dict[str, str] = {}
    for event in vec.dialogue_events:
        normalized = " ".join(event.text.lower().split())
        earlier = seen.get(normalized)
        if earlier is not None:
            issues.append(
                EditorialIssue(
                    issue_id=f"DIALOGUE-{event.event_id}", issue_code="DIALOGUE_TEXT_REPEATED",
                    severity="blocking", contract_refs=(f"dialogue:{earlier}", f"dialogue:{event.event_id}"),
                    observation="the same dialogue text is assigned more than once in this contract",
                    affected_node_ids=(f"dialogue:{earlier}", f"dialogue:{event.event_id}"),
                )
            )
        else:
            seen[normalized] = event.event_id
    return EditorialReviewRecord(
        review_id=f"ER-DIALOGUE-{vec.contract_id}", mode=DIALOGUE_REDUNDANCY,
        contract_fingerprint=vec.fingerprint, observed_contract_refs=tuple(refs), issues=tuple(issues),
        status=TEXT_REVIEW_FAILED if issues else TEXT_VALIDATED, scope=vec.scene_id,
    )
