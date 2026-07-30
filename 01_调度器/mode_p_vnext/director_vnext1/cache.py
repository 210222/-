"""Small deterministic cache for Director vNext.1 planning phases.

The cache is intentionally local and in-memory at this stage.  Its key is a
canonical digest of approved input content, never a wall-clock value or a model
response.  This makes a cache hit auditable and prevents a prompt-time field
from silently changing a director decision.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, TypeVar

from .contracts import DirectorContractError


T = TypeVar("T")


def _normalise(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _normalise(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _normalise(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_normalise(item) for item in value]
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise DirectorContractError(f"cache input has unsupported type: {type(value).__name__}")


def content_address(namespace: str, payload: Mapping[str, object]) -> str:
    """Return a content-only key; callers must explicitly choose a namespace."""

    if not namespace or not namespace.strip():
        raise DirectorContractError("cache namespace is required")
    canonical = json.dumps(
        {"namespace": namespace, "payload": _normalise(payload)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ContentAddressedCache:
    """Typed value cache with observable hit/miss counters for performance QA."""

    def __init__(self) -> None:
        self._values: dict[str, object] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> object | None:
        if key in self._values:
            self._hits += 1
            return self._values[key]
        self._misses += 1
        return None

    def put(self, key: str, value: T) -> T:
        if not key or not key.strip():
            raise DirectorContractError("cache key is required")
        self._values[key] = value
        return value

    @property
    def stats(self) -> Mapping[str, int]:
        return {"entries": len(self._values), "hits": self._hits, "misses": self._misses}
