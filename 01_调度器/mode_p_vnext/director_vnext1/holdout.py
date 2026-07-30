"""Frozen, isolated holdout registry for Director vNext.1 evaluation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from typing import Sequence, Tuple

from .contracts import DirectorContractError


def _hash_payload(payload: object) -> str:
    if is_dataclass(payload) and not isinstance(payload, type):
        payload = asdict(payload)
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=asdict).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class HoldoutCase:
    case_id: str
    script_sha256: str
    evaluation_tags: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.script_sha256.strip() or not self.evaluation_tags:
            raise DirectorContractError("holdout case needs an ID, script hash, and evaluation tags")
        if len(self.script_sha256) != 64 or any(char not in "0123456789abcdef" for char in self.script_sha256):
            raise DirectorContractError("holdout script hash must be a lowercase SHA-256")


@dataclass(frozen=True)
class FrozenHoldoutSet:
    """No script text, answer, capsule, prompt, or Golden case enters this registry."""

    set_id: str
    golden_case_ids: Tuple[str, ...]
    cases: Tuple[HoldoutCase, ...]
    frozen: bool = True

    def __post_init__(self) -> None:
        if not self.set_id.strip() or not self.cases or not self.frozen:
            raise DirectorContractError("holdout set must be named, non-empty, and frozen")
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise DirectorContractError("holdout case IDs must be unique")
        overlap = set(ids) & set(self.golden_case_ids)
        if overlap:
            raise DirectorContractError("Golden and Holdout cases must remain disjoint")

    @property
    def fingerprint(self) -> str:
        return _hash_payload(
            {
                "set_id": self.set_id,
                "golden_case_ids": self.golden_case_ids,
                "cases": self.cases,
                "frozen": self.frozen,
            }
        )

    def assert_case_is_held_out(self, case_id: str) -> HoldoutCase:
        for case in self.cases:
            if case.case_id == case_id:
                return case
        raise DirectorContractError("requested evaluation case is not in the frozen Holdout set")
