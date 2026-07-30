"""DP cache keys, fresh-invocation tracking and anti-idle protection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set

from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256


def _hash(value: object) -> str:
    return stable_hash_sha256(canonical_json_dumps(value).encode("utf-8"))


def compute_dp_cache_key(
    dp_view_hash: str,
    capability_hash: str,
    asset_hash: str,
    implementation_version: str,
) -> str:
    """Key for identical review evidence; it intentionally excludes context ID."""
    return _hash({
        "dp_view_hash": dp_view_hash,
        "capability_hash": capability_hash,
        "asset_hash": asset_hash,
        "implementation_version": implementation_version,
    })


def compute_dp_invocation_key(
    cache_key: str,
    context_id: str,
    revision_id: str = "",
) -> str:
    """Trace a specific fresh invocation without letting it defeat anti-idle."""
    if not cache_key or not context_id:
        raise ValueError("cache_key and fresh context_id are required")
    return _hash({
        "cache_key": cache_key,
        "context_id": context_id,
        "revision_id": revision_id,
    })


@dataclass(frozen=True)
class DPReviewRecord:
    cache_key: str
    invocation_key: str
    context_id: str
    verdict: str
    revision_id: str = ""


class DPCache:
    """Tracks both duplicate evidence and one-use DP context identities."""

    def __init__(self) -> None:
        self._seen: Set[str] = set()
        self._context_ids: Set[str] = set()
        self._records: Dict[str, DPReviewRecord] = {}

    def record(
        self,
        cache_key: str,
        verdict: str,
        *,
        context_id: str = "",
        revision_id: str = "",
    ) -> DPReviewRecord | None:
        """Record a review; a supplied context ID may be used exactly once."""
        self._seen.add(cache_key)
        if not context_id:
            return None
        if context_id in self._context_ids:
            raise ValueError(f"DP context already used: {context_id}")
        self._context_ids.add(context_id)
        invocation_key = compute_dp_invocation_key(cache_key, context_id, revision_id)
        record = DPReviewRecord(
            cache_key=cache_key,
            invocation_key=invocation_key,
            context_id=context_id,
            verdict=verdict,
            revision_id=revision_id,
        )
        self._records[invocation_key] = record
        return record

    def is_duplicate_question(self, cache_key: str) -> bool:
        """True means unchanged evidence must not trigger an idle repeat review."""
        return cache_key in self._seen

    def review_record(self, invocation_key: str) -> DPReviewRecord | None:
        return self._records.get(invocation_key)
