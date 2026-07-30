"""MODE:P vNext — Render Payload Manifest (V5.7).

Records included/excluded field IDs, negative route, asset slots,
capability snapshot, serialization version, and content hash.

Spec references: LOOP §21.4a.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256
from mode_p_vnext.payload_compiler import RenderPayload
from mode_p_vnext.schema.visibility_contract import VisibilityContract


@dataclass
class PayloadManifest:
    manifest_id: str
    segment_id: str
    schema_version: str = "5.7"
    included_field_ids: List[str] = field(default_factory=list)
    excluded_field_ids: List[str] = field(default_factory=list)
    negative_route: str = ""
    asset_slots_used: int = 0
    capability_profile_hash: str = ""
    content_sha256: str = ""


def create_payload_manifest(
    payload: RenderPayload,
    contract: VisibilityContract,
    manifest_id: str = "",
) -> PayloadManifest:
    """Create a manifest from a compiled payload and visibility contract."""
    m = PayloadManifest(
        manifest_id=manifest_id or f"MANIFEST_{payload.segment_id}",
        segment_id=payload.segment_id,
        included_field_ids=sorted(payload.fields.keys()),
        excluded_field_ids=sorted(str(e) for e in payload.excluded_fields),
        negative_route=contract.negative_route,
        asset_slots_used=len(payload.fields.get("reference_images", [])),
    )
    # Hash the payload content
    payload_json = canonical_json_dumps(payload.fields)
    m.content_sha256 = stable_hash_sha256(payload_json.encode("utf-8"))
    return m
