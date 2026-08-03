"""Small, data-triggered prompt fragments; none contain a recursive schema."""

from __future__ import annotations

from typing import Mapping

from .signatures import Stage, StageSignature


DIRECTOR_CORE = (
    "You are the MODE:P Director for one bounded creative stage. Use only approved "
    "facts and the compact knowledge view supplied for this call. Choose creative "
    "draft content only; do not invent story facts, deterministic identifiers, hashes, "
    "or rendered delivery text. When a contract supports bindings, select only "
    "approved opaque handles through its typed binding fields; free text never "
    "creates a machine binding. Keep private reasoning private. Return one "
    "JSON object that satisfies the separately transported contract."
)

FACT_EXTRACTION_CORE = (
    "You extract only source-anchored MODE:P script facts for one bounded ingest "
    "window. Use only the normalized source supplied for this call. Do not make "
    "creative decisions, rewrite narrative, invent facts, identifiers, hashes, "
    "validation status, or fields that name or select a local scene partition. "
    "For every fact, `statement` must be transcribed verbatim from the "
    "normalized source, exactly the text between its own `source_start` and "
    "`source_end` character offsets (punctuation included): never paraphrase, "
    "summarize, add an explanation or subject, or drop trailing punctuation. "
    "Return one JSON object that satisfies the separately "
    "transported contract."
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


def core_for_signature(signature: StageSignature) -> str:
    """I0 is a fact extractor, not a Director creative call."""

    return FACT_EXTRACTION_CORE if signature.stage is Stage.I0 else DIRECTOR_CORE


def conditional_fragments(
    approved_input: Mapping[str, object], *, stage: Stage | None = None
) -> tuple[str, ...]:
    """Select only fragments whose compact input has the matching feature."""

    if stage is Stage.I0:
        return ()

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
