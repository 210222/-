"""MODE:P vNext — Dependency Invalidation (V6.3).

Computes minimal approval invalidation scope when facts, timeline,
storyboard corrections, capabilities, assets, adapters, or field routes
change.

Spec references: LOOP §23-§25.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set


class DependencyGraph:
    def __init__(self):
        self._nodes: Dict[str, str] = {}           # id → type
        self._deps: Dict[str, Set[str]] = defaultdict(set)   # id → {dep_ids}
        self._dependents: Dict[str, Set[str]] = defaultdict(set)  # id → {dependent_ids}

    def add(self, node_id: str, node_type: str,
            depends_on: List[str] | None = None) -> None:
        self._nodes[node_id] = node_type
        for dep_id in (depends_on or []):
            self._deps[node_id].add(dep_id)
            self._dependents[dep_id].add(node_id)

    def invalidate(self, changed_id: str) -> List[str]:
        """Return all node IDs transitively invalidated by changing *changed_id*."""
        invalidated: List[str] = []
        visited: Set[str] = set()
        stack = [changed_id]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for dep in self._dependents.get(current, set()):
                if dep not in visited:
                    invalidated.append(dep)
                    stack.append(dep)
        return invalidated
