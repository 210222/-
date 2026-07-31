"""Small, data-triggered prompt fragments; none contain a recursive schema."""

from __future__ import annotations

from typing import Mapping


DIRECTOR_CORE = (
    "You are the MODE:P Director for one bounded creative stage. Use only approved "
    "facts and the compact knowledge view supplied for this call. Choose creative "
    "draft content only; do not invent story facts, deterministic identifiers, hashes, "
    "or rendered delivery text. Keep private reasoning private. Return one "
    "JSON object that satisfies the separately transported contract."
)

_CONDITIONAL_FRAGMENTS: Mapping[str, str] = {
    "continuity": (
        "Continuity facts are constraints, not instructions to repeat an earlier "
        "camera or composition. Preserve the stated incoming state."
    ),
    "dialogue": (
        "Dialogue remains an approved narrative fact. Choose only timing or emphasis "
        "intent needed by this stage; do not rewrite or duplicate dialogue."
    ),
    "references": (
        "Reference requirements identify identity, wardrobe, prop geometry, and scene "
        "layout obligations. Do not invent image slots or binding IDs."
    ),
    "conflict": (
        "A knowledge conflict is unresolved. Preserve materially different options and "
        "state the creative tradeoff instead of silently choosing on behalf of review."
    ),
}


def conditional_fragments(approved_input: Mapping[str, object]) -> tuple[str, ...]:
    """Select only fragments whose compact input has the matching feature."""

    selected: list[str] = []
    if approved_input.get("continuity_state"):
        selected.append(_CONDITIONAL_FRAGMENTS["continuity"])
    if approved_input.get("dialogue") or approved_input.get("audio_facts"):
        selected.append(_CONDITIONAL_FRAGMENTS["dialogue"])
    if approved_input.get("reference_requirements"):
        selected.append(_CONDITIONAL_FRAGMENTS["references"])
    if approved_input.get("knowledge_conflicts"):
        selected.append(_CONDITIONAL_FRAGMENTS["conflict"])
    return tuple(selected)
