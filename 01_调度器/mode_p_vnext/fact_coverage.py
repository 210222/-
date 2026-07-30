"""MODE:P vNext — Fact Coverage Checker (V1.5).

Ensures every critical script fact has an explicit render-policy mapping.
No silent drops — facts classified as audio_only, narrative_only, or
not_in_segment must be declared; omissions require user approval.

Spec references: LOOP §7.9, §12.8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional, Sequence

from mode_p_vnext.schema.fact_registry import (
    FactRegistry,
    VISIBILITY_CLASSIFICATIONS,
)


# ---------------------------------------------------------------------------
# FactBinding
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FactBinding:
    """Maps a fact_id to a render policy within a segment.

    If a critical fact is deliberately omitted from visual rendering,
    ``user_approval_omission`` must record the user's explicit approval.
    """

    fact_id: str
    render_policy: str
    segment_id: str
    user_approval_omission: Optional[str] = None

    def __post_init__(self) -> None:
        if self.render_policy not in VISIBILITY_CLASSIFICATIONS:
            raise ValueError(
                f"Invalid render_policy '{self.render_policy}'. "
                f"Must be one of: {sorted(VISIBILITY_CLASSIFICATIONS)}"
            )


# ---------------------------------------------------------------------------
# CoverageResult
# ---------------------------------------------------------------------------

@dataclass
class CoverageResult:
    """Result of a fact coverage check."""

    missing_facts: List[str] = field(default_factory=list)
    phantom_bindings: List[str] = field(default_factory=list)
    duplicate_bindings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_covered(self) -> bool:
        return (
            len(self.missing_facts) == 0
            and len(self.phantom_bindings) == 0
            and len(self.duplicate_bindings) == 0
        )


@dataclass
class DropResult:
    """Result of a silent-drop check on all registry facts."""

    unbound_facts: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Coverage check
# ---------------------------------------------------------------------------

def check_fact_coverage(
    registry: FactRegistry,
    bindings: Sequence[FactBinding],
) -> CoverageResult:
    """Verify every critical fact in *registry* has a binding.

    Critical facts without a binding are ``missing_facts``.
    Bindings referencing non-existent fact_ids are ``phantom_bindings``.
    Multiple bindings for the same fact_id are ``duplicate_bindings``.
    Contextual facts without bindings produce warnings but do not block.
    """
    result = CoverageResult()

    registry_ids = {f.fact_id for f in registry}
    critical_ids = {f.fact_id for f in registry if f.is_critical}
    binding_ids: dict[str, int] = {}  # fact_id → count

    for b in bindings:
        binding_ids[b.fact_id] = binding_ids.get(b.fact_id, 0) + 1
        if b.fact_id not in registry_ids:
            result.phantom_bindings.append(b.fact_id)

    # Phantom check
    if result.phantom_bindings:
        result.warnings.append(
            f"Bindings reference {len(result.phantom_bindings)} non-existent "
            f"fact_ids: {', '.join(result.phantom_bindings)}"
        )

    # Duplicate check
    for fid, count in binding_ids.items():
        if count > 1:
            result.duplicate_bindings.append(fid)
    if result.duplicate_bindings:
        result.warnings.append(
            f"Duplicate bindings for: {', '.join(result.duplicate_bindings)}"
        )

    # Missing critical facts
    for fid in sorted(critical_ids):
        if fid not in binding_ids:
            result.missing_facts.append(fid)
    if result.missing_facts:
        result.warnings.append(
            f"Critical facts missing bindings: {', '.join(result.missing_facts)}"
        )

    # Contextual facts without bindings (warning only)
    contextual_unbound = [
        f.fact_id for f in registry
        if not f.is_critical and f.fact_id not in binding_ids
    ]
    if contextual_unbound:
        result.warnings.append(
            f"Contextual facts without bindings (OK if intentional): "
            f"{', '.join(contextual_unbound)}"
        )

    return result


def check_silent_drops(
    registry: FactRegistry,
    bindings: Sequence[FactBinding],
) -> DropResult:
    """Return all registry facts that have no binding at all.

    Unlike ``check_fact_coverage``, this checks ALL facts, not just critical ones.
    """
    binding_ids = {b.fact_id for b in bindings}
    unbound = [f.fact_id for f in registry if f.fact_id not in binding_ids]
    return DropResult(unbound_facts=sorted(unbound))
