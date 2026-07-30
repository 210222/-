"""Deterministic, least-privilege DP_VIEW compiler.

DP is an independent reviewer, not a second Director.  It receives only
observable evidence and derived views; master internals, knowledge packets,
reasoning traces and old DP feedback are structurally excluded before a packet
is made.  The compiler does not infer or add creative content.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterable, Mapping

from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256


DP_VIEW_WHITELIST: FrozenSet[str] = frozenset({
    "script_facts",
    "episode_continuity",
    "storyboard_view",
    "video_prompt_view",
    "used_capabilities",
    "asset_text_evidence",
    "user_visual_constraints",
    "correction_impact",
    "fidelity_view",
    "visibility_view",
    "handoff_view",
    "timeline_view",
    "reference_responsibilities",
})

DP_VIEW_FORBIDDEN: FrozenSet[str] = frozenset({
    "master",
    "knowledge_packet",
    "director_reasoning",
    "historical_dp_feedback",
    "scene_diagnosis",
    "fact_registry_internal",
    "fidelity_contract_internal",
    "knowledge_snapshot",
})


class DPViewViolation(ValueError):
    """A caller attempted to pass non-reviewable context to DP."""


def _hash(value: object) -> str:
    return stable_hash_sha256(canonical_json_dumps(value).encode("utf-8"))


def _find_forbidden_keys(value: object, *, path: str = "") -> list[str]:
    """Find forbidden structural keys without scanning ordinary text values."""
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if path else key_text
            if key_text in DP_VIEW_FORBIDDEN:
                found.append(child_path)
            found.extend(_find_forbidden_keys(child, path=child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_find_forbidden_keys(child, path=f"{path}[{index}]"))
    return found


def validate_dp_view(view: Mapping[str, Any]) -> list[str]:
    """Return structural boundary violations; no natural-language inspection."""
    violations: list[str] = []
    for key in view:
        if key not in DP_VIEW_WHITELIST:
            violations.append(f"non_whitelisted_field:{key}")
        if key in DP_VIEW_FORBIDDEN:
            violations.append(f"forbidden_field:{key}")
    for key, value in view.items():
        for path in _find_forbidden_keys(value, path=str(key)):
            violations.append(f"nested_forbidden_field:{path}")
    return sorted(set(violations))


@dataclass(frozen=True)
class DPView:
    """A sealed derived view suitable for a fresh DP invocation."""

    fields: Mapping[str, Any]
    content_sha256: str

    @classmethod
    def from_sources(cls, sources: Mapping[str, Any], *, strict: bool = True) -> "DPView":
        fields = compile_dp_view(dict(sources), strict=strict)
        return cls(fields=fields, content_sha256=_hash(fields))

    def verify_integrity(self) -> bool:
        """Detect mutation of a derived view before it is put in a DP packet."""
        return self.content_sha256 == _hash(self.fields)


def compile_dp_view(sources: Dict[str, Any], *, strict: bool = False) -> Dict[str, Any]:
    """Return a deep-copied whitelist projection of ``sources``.

    ``strict`` is used by a real DP invocation: forbidden or nested internal
    fields become a blocking error instead of a silent drop.  The legacy
    default remains a safe filtering projection for existing callers.
    """
    if not isinstance(sources, Mapping):
        raise TypeError("DP sources must be a mapping")
    if strict:
        excluded = sorted(set(sources) - DP_VIEW_WHITELIST)
        if excluded:
            raise DPViewViolation("non-whitelisted DP source fields: " + ", ".join(excluded))
    result: Dict[str, Any] = {
        key: deepcopy(sources[key]) for key in DP_VIEW_WHITELIST if key in sources
    }
    violations = validate_dp_view(result)
    if violations:
        raise DPViewViolation("invalid DP view: " + "; ".join(violations))
    return result
