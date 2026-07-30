"""MODE:P vNext — Dedup & Conflict Graph (V3.3).

Detects same-source duplicates, near-duplicate claims, and conflicting claims.
Exposes conflicts for Director resolution — never auto-selects a creative winner.

Spec references: LOOP §5.6, §5.9.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from mode_p_vnext.schema.decision_card import DecisionCard


# ---------------------------------------------------------------------------
# Duplicate detection (exact + same-source)
# ---------------------------------------------------------------------------

def find_duplicates(cards: Sequence[DecisionCard]) -> List[Dict]:
    """Return pairs of cards with identical claim text."""
    seen: Dict[str, str] = {}
    dupes: List[Dict] = []
    for c in cards:
        key = c.claim.strip().lower()
        if key in seen:
            dupes.append({
                "type": "exact_duplicate",
                "card_ids": [seen[key], c.card_id],
                "claim": c.claim,
            })
        else:
            seen[key] = c.card_id
    return dupes


def find_same_source_duplicates(cards: Sequence[DecisionCard]) -> List[Dict]:
    """Return groups of cards derived from the same source file.

    Multiple cards from the same source isn't necessarily wrong, but it
    flags potential redundant extraction.
    """
    by_source: Dict[str, List[str]] = defaultdict(list)
    for c in cards:
        if c.source_file:
            by_source[c.source_file].append(c.card_id)

    dupes: List[Dict] = []
    for source, ids in by_source.items():
        if len(ids) > 1:
            dupes.append({
                "type": "same_source",
                "source_file": source,
                "card_ids": sorted(ids),
            })
    return dupes


# ---------------------------------------------------------------------------
# Conflict graph
# ---------------------------------------------------------------------------

@dataclass
class ConflictGraph:
    """A graph of conflicting claims.

    Each conflict entry lists the involved card_ids and the shared topic.
    The algorithm never picks a winner — the Director resolves conflicts.
    """

    conflicts: List[Dict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0


# ---------------------------------------------------------------------------
# Simple keyword-based opposite detection
# ---------------------------------------------------------------------------

# Pairs of keywords that suggest opposing stances on the same topic
_OPPOSING_PAIRS = [
    ({"推镜", "zoom"}, {"切镜", "cut"}),
    ({"横版", "landscape"}, {"竖版", "portrait"}),
    ({"保持", "keep", "维持"}, {"改变", "change", "切换"}),
    ({"硬切", "hard cut"}, {"连续", "continuous"}),
    ({"可见", "visible"}, {"不可见", "invisible", "遮挡"}),
    ({"单一", "single"}, {"多个", "multi"}),
]


def _extract_keywords(text: str) -> set:
    """Extract topic keywords from a claim."""
    # Simple: check for presence of known topic words
    found = set()
    lower = text.lower()
    for t in {"推镜", "切镜", "zoom", "cut", "硬切", "连续", "构图", "光影",
              "注意力", "可见", "不可见", "遮挡", "横版", "竖版",
              "landscape", "portrait", "单一", "多个", "single", "multi",
              "保持", "改变", "维持", "切换", "sound", "声音", "对白",
              "手机", "背面", "后壳", "界面", "UI"}:
        if t in lower:
            found.add(t)
    return found


def build_conflict_graph(cards: Sequence[DecisionCard]) -> ConflictGraph:
    """Build a conflict graph from a set of decision cards.

    Two cards conflict if they share topic keywords but appear in
    opposing keyword pairs (e.g. one says "推镜" and the other says "切镜"
    on the same topic like "注意力").
    """
    graph = ConflictGraph()

    for i in range(len(cards)):
        for j in range(i + 1, len(cards)):
            ki = _extract_keywords(cards[i].claim)
            kj = _extract_keywords(cards[j].claim)
            shared = ki & kj
            if not shared:
                continue

            # Check for opposing pairs within the shared topic area
            for opp_a, opp_b in _OPPOSING_PAIRS:
                has_a_i = bool(ki & opp_a)
                has_b_i = bool(ki & opp_b)
                has_a_j = bool(kj & opp_a)
                has_b_j = bool(kj & opp_b)
                # Conflict: card i has A, card j has B on the same topic
                if (has_a_i and has_b_j) or (has_b_i and has_a_j):
                    graph.conflicts.append({
                        "card_ids": [cards[i].card_id, cards[j].card_id],
                        "shared_topic": sorted(shared),
                        "opposing_pair": [sorted(opp_a), sorted(opp_b)],
                        "claim_a": cards[i].claim,
                        "claim_b": cards[j].claim,
                    })
                    break  # one conflict per pair is enough

    return graph
