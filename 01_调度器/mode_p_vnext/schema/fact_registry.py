"""MODE:P vNext — Fact Registry Schema (V1.4).

Structured narrative facts extracted from the script.
- Each fact has a stable fact_id, source line, type, criticality, and visibility classification.
- Program validates structure and coverage; it NEVER authors facts.
- Facts are the Director's input; validation only checks completeness and consistency.

Spec references: LOOP §7.9, §9 Step 1; Omission P0-10.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Iterator, List, Optional

from mode_p_vnext.knowledge_security import assert_untrusted_text_safe


# ---------------------------------------------------------------------------
# Valid constants
# ---------------------------------------------------------------------------

FACT_TYPES: FrozenSet[str] = frozenset({
    "event",         # 事件
    "dialogue",      # 对白
    "continuity",    # 连续性入口
    "character",     # 角色事实
    "prop",          # 道具事实
    "spatial",       # 空间事实
    "uncertain",     # 未确定项（类型层面）
})

CRITICALITY_LEVELS: FrozenSet[str] = frozenset({
    "critical",      # 关键事实——不可降级
    "important",     # 重要事实
    "contextual",     # 背景事实
})

VISIBILITY_CLASSIFICATIONS: FrozenSet[str] = frozenset({
    "visible",           # 当前镜头可见
    "audio_only",        # 只在声音时间线
    "narrative_only",    # 叙事层成立但不可见
    "not_in_segment",    # 不在当前段
    "locked_execution",  # 执行约束但不影响可见性
})


# ---------------------------------------------------------------------------
# ScriptFact
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScriptFact:
    """A single structured fact from the script.

    Equality and hashing are by ``fact_id`` only — two facts with the same ID
    are the same fact regardless of other field differences.
    """

    fact_id: str
    source_line: int
    fact_type: str
    summary: str
    criticality: str
    visibility: str
    uncertain: bool = False
    character_ids: List[str] = field(default_factory=list)
    prop_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.fact_id.strip():
            raise ValueError("fact_id must not be empty")
        assert_untrusted_text_safe(
            source_id=self.fact_id,
            source_kind="script_fact",
            project_id="fact_registry",
            content=self.summary,
        )
        if self.fact_type not in FACT_TYPES:
            raise ValueError(
                f"Invalid fact_type '{self.fact_type}'. "
                f"Must be one of: {sorted(FACT_TYPES)}"
            )
        if self.criticality not in CRITICALITY_LEVELS:
            raise ValueError(
                f"Invalid criticality '{self.criticality}'. "
                f"Must be one of: {sorted(CRITICALITY_LEVELS)}"
            )
        if self.visibility not in VISIBILITY_CLASSIFICATIONS:
            raise ValueError(
                f"Invalid visibility '{self.visibility}'. "
                f"Must be one of: {sorted(VISIBILITY_CLASSIFICATIONS)}"
            )
        if self.source_line < 1:
            raise ValueError(f"source_line must be >= 1, got {self.source_line}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScriptFact):
            return NotImplemented
        return self.fact_id == other.fact_id

    def __hash__(self) -> int:
        return hash(self.fact_id)

    @property
    def is_critical(self) -> bool:
        return self.criticality == "critical"

    @property
    def is_visible(self) -> bool:
        return self.visibility == "visible"

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "fact_id": self.fact_id,
            "source_line": self.source_line,
            "fact_type": self.fact_type,
            "summary": self.summary,
            "criticality": self.criticality,
            "visibility": self.visibility,
            "uncertain": self.uncertain,
        }
        if self.character_ids:
            d["character_ids"] = self.character_ids
        if self.prop_ids:
            d["prop_ids"] = self.prop_ids
        return d

    def to_runtime_metadata(self) -> Dict[str, Any]:
        """Return runtime-safe provenance without raw script prose."""
        envelope = assert_untrusted_text_safe(
            source_id=self.fact_id,
            source_kind="script_fact",
            project_id="fact_registry",
            content=self.summary,
        )
        return {
            "fact_id": self.fact_id,
            "source_line": self.source_line,
            "fact_type": self.fact_type,
            "criticality": self.criticality,
            "visibility": self.visibility,
            "summary_sha256": envelope.content_sha256,
            "role": "untrusted_data",
        }


# ---------------------------------------------------------------------------
# FactRegistry — container
# ---------------------------------------------------------------------------

class FactRegistry:
    """A validated collection of ScriptFacts.

    The registry enforces uniqueness by fact_id. It is a container only —
    the Director authors facts; this class validates structure and provides
    lookup/filter helpers.
    """

    def __init__(self) -> None:
        self._facts: Dict[str, ScriptFact] = {}

    def add(self, fact: ScriptFact) -> None:
        """Add a fact. Raises ValueError if fact_id already exists."""
        if fact.fact_id in self._facts:
            raise ValueError(
                f"Duplicate fact_id '{fact.fact_id}' — facts must have unique IDs"
            )
        self._facts[fact.fact_id] = fact

    def get(self, fact_id: str) -> Optional[ScriptFact]:
        """Look up a fact by ID. Returns None if not found."""
        return self._facts.get(fact_id)

    def __len__(self) -> int:
        return len(self._facts)

    def __iter__(self) -> Iterator[ScriptFact]:
        return iter(self._facts.values())

    def __contains__(self, fact_id: str) -> bool:
        return fact_id in self._facts

    def critical_facts(self) -> Iterator[ScriptFact]:
        """Iterate over facts marked as critical."""
        for f in self._facts.values():
            if f.is_critical:
                yield f

    def uncertain_facts(self) -> Iterator[ScriptFact]:
        """Iterate over facts marked as uncertain."""
        for f in self._facts.values():
            if f.uncertain:
                yield f

    def visible_facts(self) -> Iterator[ScriptFact]:
        """Iterate over facts classified as visible."""
        for f in self._facts.values():
            if f.is_visible:
                yield f

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "fact_registry",
            "version": "1.4",
            "fact_count": len(self._facts),
            "facts": [f.to_dict() for f in self._facts.values()],
        }


# ---------------------------------------------------------------------------
# Validation — structural only, no creative judgment
# ---------------------------------------------------------------------------

def validate_registry(registry: FactRegistry) -> List[str]:
    """Validate the registry structure. Returns list of violation strings.

    Checks:
    - Each fact_id is unique (enforced by add(), but re-check here for safety)
    - No critical fact is missing a source line
    - Warn if multiple facts cite the same source_line (may be intentional)
    """
    violations: List[str] = []
    seen_lines: Dict[int, List[str]] = {}
    seen_ids: set[str] = set()
    critical_missing_line: List[str] = []

    for fact in registry:
        # Duplicate ID check (belt-and-suspenders)
        if fact.fact_id in seen_ids:
            violations.append(f"Duplicate fact_id: {fact.fact_id}")
        seen_ids.add(fact.fact_id)

        # Track source lines for overlap detection
        if fact.source_line not in seen_lines:
            seen_lines[fact.source_line] = []
        seen_lines[fact.source_line].append(fact.fact_id)

    # Multiple facts from same source line (review item, not necessarily error)
    for line_no, ids in seen_lines.items():
        if len(ids) > 1:
            violations.append(
                f"Multiple facts from line {line_no}: {', '.join(ids)} "
                f"— verify this is intentional"
            )

    return violations
