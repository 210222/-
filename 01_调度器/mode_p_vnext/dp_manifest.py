"""Fresh-context manifests for independent DP review packets.

Every DP invocation receives a newly issued context identifier and a sealed
hash of its deterministic whitelist view.  A manifest is evidence of the
review boundary, not an instruction for creative rewriting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Set
from uuid import uuid4

from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256
from mode_p_vnext.dp_view_compiler import DP_VIEW_WHITELIST, DPView, compile_dp_view


def _hash(value: object) -> str:
    return stable_hash_sha256(canonical_json_dumps(value).encode("utf-8"))


class DPContextReuseError(ValueError):
    """A DP context identifier was reused instead of creating a fresh review."""


def new_dp_context_id(prefix: str = "DPCTX") -> str:
    """Create an opaque fresh context ID; it intentionally carries no scene data."""
    if not prefix:
        raise ValueError("context prefix is required")
    return f"{prefix}-{uuid4().hex}"


@dataclass
class DPPacketManifest:
    manifest_id: str
    context_id: str
    whitelist_fields: list[str] = field(default_factory=list)
    field_hashes: Dict[str, str] = field(default_factory=dict)
    is_fresh_context: bool = True
    parent_context_id: str = ""
    revision_id: str = ""
    content_sha256: str = ""

    def _payload(self) -> Dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "context_id": self.context_id,
            "whitelist_fields": sorted(self.whitelist_fields),
            "field_hashes": dict(sorted(self.field_hashes.items())),
            "is_fresh_context": self.is_fresh_context,
            "parent_context_id": self.parent_context_id,
            "revision_id": self.revision_id,
        }

    def __post_init__(self) -> None:
        if not self.manifest_id or not self.context_id:
            raise ValueError("manifest_id and context_id are required")
        if not self.is_fresh_context:
            raise ValueError("DP packet must declare a fresh context")
        if len(self.whitelist_fields) != len(set(self.whitelist_fields)):
            raise ValueError("whitelist_fields contains duplicates")
        extra_hashes = sorted(set(self.field_hashes) - set(self.whitelist_fields))
        if extra_hashes:
            raise ValueError("field hashes outside whitelist: " + ", ".join(extra_hashes))
        if not self.content_sha256:
            self.content_sha256 = _hash(self._payload())

    def verify_integrity(self) -> bool:
        return self.content_sha256 == _hash(self._payload())

    def validate_for_invocation(self) -> None:
        """Apply strict whitelist/hash checks at the actual DP boundary.

        Direct construction stays compatible with older evidence readers; a
        manifest cannot be registered for a live review unless every listed
        field is an approved projection with a full SHA-256 hash.
        """
        unknown = sorted(set(self.whitelist_fields) - DP_VIEW_WHITELIST)
        if unknown:
            raise ValueError("non-whitelisted DP fields: " + ", ".join(unknown))
        missing = sorted(set(self.whitelist_fields) - set(self.field_hashes))
        if missing:
            raise ValueError("DP field hashes missing: " + ", ".join(missing))
        malformed = sorted(
            key for key, value in self.field_hashes.items()
            if len(value) != 64 or any(char not in "0123456789abcdef" for char in value.lower())
        )
        if malformed:
            raise ValueError("DP field hashes must be SHA-256: " + ", ".join(malformed))
        if not self.verify_integrity():
            raise ValueError("DP manifest integrity check failed")

    def to_dict(self) -> Dict[str, Any]:
        payload = self._payload()
        payload["content_sha256"] = self.content_sha256
        return payload


class FreshDPContextRegistry:
    """Process-local guard against reusing a DP review context or packet ID."""

    def __init__(self) -> None:
        self._context_ids: Set[str] = set()
        self._manifest_ids: Set[str] = set()

    def register(self, manifest: DPPacketManifest) -> None:
        try:
            manifest.validate_for_invocation()
        except ValueError as exc:
            raise DPContextReuseError(str(exc)) from exc
        if manifest.context_id in self._context_ids:
            raise DPContextReuseError(f"DP context already used: {manifest.context_id}")
        if manifest.manifest_id in self._manifest_ids:
            raise DPContextReuseError(f"DP manifest already used: {manifest.manifest_id}")
        if manifest.parent_context_id and manifest.parent_context_id == manifest.context_id:
            raise DPContextReuseError("fresh DP context cannot equal parent context")
        self._context_ids.add(manifest.context_id)
        self._manifest_ids.add(manifest.manifest_id)


def create_dp_packet_manifest(
    manifest_id: str,
    sources: Mapping[str, Any],
    *,
    context_id: str = "",
    parent_context_id: str = "",
    revision_id: str = "",
    registry: Optional[FreshDPContextRegistry] = None,
) -> DPPacketManifest:
    """Compile a strict DP view and seal it into a new-context manifest."""
    view = DPView.from_sources(sources, strict=True)
    if not view.verify_integrity():
        raise ValueError("DP view integrity check failed")
    fields = sorted(view.fields)
    manifest = DPPacketManifest(
        manifest_id=manifest_id,
        context_id=context_id or new_dp_context_id(),
        whitelist_fields=fields,
        field_hashes={key: _hash(value) for key, value in view.fields.items()},
        parent_context_id=parent_context_id,
        revision_id=revision_id,
    )
    if registry:
        registry.register(manifest)
    return manifest
