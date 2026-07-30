"""Bounded DP review responses.

DP may signal READY, a directed question, or an input block.  It cannot issue
a new scene design, choose a camera solution, replace the Director, or request
an unrestricted rewrite.  Every non-ready issue is attached to an existing
review object so the following revision can stay local.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import FrozenSet, List, Sequence, Tuple


VALID_VERDICTS: FrozenSet[str] = frozenset({
    "READY",
    "DIRECTED_QUESTION",
    "INPUT_BLOCK",
})
VALID_FIDELITY_CLASSES: FrozenSet[str] = frozenset({
    "LOCKED", "ELASTIC", "OPTIMIZABLE", "FORBIDDEN", "NOT_APPLICABLE",
})


class DPResponseViolation(ValueError):
    """The reviewer response attempted to exceed its evidence/revision role."""


_REDIRECTION_MARKERS: Tuple[str, ...] = (
    "rewrite the whole scene", "rewrite entire scene", "replace the director",
    "start over", "all shots", "entire master", "must use 35mm", "must use 50mm",
    "must use 85mm", "use a hard cut", "three shots", "cut to closeup",
    "全场重写", "整场重写", "替换导演", "重新导演", "必须使用35mm", "必须使用50mm",
    "必须使用85mm", "必须硬切", "三个镜头", "切到近景",
)


def _contains_redirection(text: str) -> bool:
    lowered = " ".join(text.lower().split())
    if any(marker in lowered for marker in _REDIRECTION_MARKERS):
        return True
    # DP may name the observed problem but must not prescribe a lens, motion,
    # cut topology or shot count as its correction. Those remain Director work.
    return bool(re.search(
        r"\b(?:35|50|85)\s*mm\b|\bhard\s+cut\b|\bpush(?:-|\s)+in\b|\bdolly\b|\bthree\s+shots?\b|"
        r"(?:硬切|推镜|摇镜|跟拍|三个镜头|三镜头)",
        lowered,
    ))


@dataclass
class DPIssue:
    issue_id: str
    question: str
    bound_to_segment: str = ""
    bound_to_shot: str = ""
    bound_to_beat: str = ""
    bound_to_panel: int = 0
    bound_to_fidelity: str = ""
    affected_boundaries: List[str] = field(default_factory=list)
    fidelity_class: str = "LOCKED"
    issue_code: str = ""
    observed_evidence: str = ""
    required_correction_domain: str = ""

    def __post_init__(self) -> None:
        if not self.issue_id or not self.question.strip():
            raise DPResponseViolation("DP issue requires issue_id and a directed question")
        if self.fidelity_class not in VALID_FIDELITY_CLASSES:
            raise DPResponseViolation(f"invalid fidelity class: {self.fidelity_class}")
        if _contains_redirection(self.question):
            raise DPResponseViolation("DP may identify a local problem, not direct a creative rewrite")
        if not self.binding_keys:
            raise DPResponseViolation("DP issue must bind to segment, shot, beat, panel or fidelity")
        if any(not boundary.strip() for boundary in self.affected_boundaries):
            raise DPResponseViolation("affected boundary IDs must be non-empty")

    @property
    def binding_keys(self) -> Tuple[str, ...]:
        keys: List[str] = []
        if self.bound_to_segment:
            keys.append(f"segment:{self.bound_to_segment}")
        if self.bound_to_shot:
            keys.append(f"shot:{self.bound_to_shot}")
        if self.bound_to_beat:
            keys.append(f"beat:{self.bound_to_beat}")
        if self.bound_to_panel:
            keys.append(f"panel:{self.bound_to_panel}")
        if self.bound_to_fidelity:
            keys.append(f"fidelity:{self.bound_to_fidelity}")
        return tuple(keys)


@dataclass
class DPResponse:
    response_id: str
    verdict: str
    issues: List[DPIssue] = field(default_factory=list)
    context_id: str = ""
    manifest_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.response_id:
            raise DPResponseViolation("DP response requires response_id")
        if self.verdict not in VALID_VERDICTS:
            raise ValueError(
                f"Invalid DP verdict '{self.verdict}'. Must be one of: {sorted(VALID_VERDICTS)}"
            )
        issue_ids = [issue.issue_id for issue in self.issues]
        if len(issue_ids) != len(set(issue_ids)):
            raise DPResponseViolation("duplicate DP issue_id")
        if self.verdict == "READY" and self.issues:
            raise DPResponseViolation("READY cannot carry revision issues")
        if self.verdict != "READY" and not self.issues:
            raise DPResponseViolation(f"{self.verdict} requires at least one bound issue")

    @property
    def is_ready(self) -> bool:
        return self.verdict == "READY" and len(self.issues) == 0

    @property
    def revision_scope_keys(self) -> Tuple[str, ...]:
        keys: List[str] = []
        for issue in self.issues:
            keys.extend(issue.binding_keys)
        return tuple(sorted(set(keys)))

    def validate_against_manifest(
        self,
        manifest: object,
        *,
        available_scope_keys: Sequence[str] = (),
    ) -> None:
        """Bind a production DP response to its fresh, sealed input packet.

        This is intentionally opt-in for legacy in-memory fixtures.  Runtime
        callers must use it before routing a response into a revision.
        """
        manifest_context = getattr(manifest, "context_id", "")
        manifest_hash = getattr(manifest, "content_sha256", "")
        verify = getattr(manifest, "verify_integrity", None)
        if not self.context_id or not self.manifest_sha256:
            raise DPResponseViolation("production DP response requires context_id and manifest_sha256")
        if not manifest_context or not manifest_hash or self.context_id != manifest_context:
            raise DPResponseViolation("DP response context does not match packet manifest")
        if self.manifest_sha256 != manifest_hash:
            raise DPResponseViolation("DP response manifest hash does not match packet manifest")
        if callable(verify) and not verify():
            raise DPResponseViolation("DP packet manifest integrity check failed")
        known = set(available_scope_keys)
        if known:
            unknown = sorted(set(self.revision_scope_keys) - known)
            if unknown:
                raise DPResponseViolation("DP issue binds unknown review objects: " + ", ".join(unknown))
