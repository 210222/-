"""MODE:P vNext — Reference/Asset Binding (V2.4).

Binds asset references to content hashes, platform slots, responsibilities,
authorization status, time ranges, and project scope. Detects slot conflicts.

Spec references: LOOP §7.7, §11.2, §28.7; Omission P0-12/P1-14.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from mode_p_vnext.knowledge_security import assert_untrusted_text_safe
from mode_p_vnext.schema.canonical_timeline import TimeInterval


@dataclass(frozen=True)
class AssetBinding:
    """A verified binding between an asset reference and its concrete identity.

    Every ``@图片1``-style reference in the Director's output must be bound
    to a content hash, platform slot, and declared responsibility.
    """

    asset_id: str                        # e.g. "@图片1", "@角色名"
    content_sha256: str                  # full SHA-256 of the asset file
    version: str                         # asset version
    platform_slot: str                   # e.g. "reference_image_0"
    responsibility: str                  # e.g. "storyboard_reference", "video_reference"
    authorized: bool = True              # user-confirmed usage authorization
    project_id: str = ""                 # scoped to project (empty = current)
    crop: str = ""                       # e.g. "16:9→9:16 center"
    valid_time_range: Optional[TimeInterval] = None
    conflict_priority: int = 0           # higher = wins in conflict resolution
    notes: str = ""

    def __post_init__(self) -> None:
        if self.notes:
            assert_untrusted_text_safe(
                source_id=self.asset_id,
                source_kind="asset_metadata",
                project_id=self.project_id or "asset_binding",
                content=self.notes,
            )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "asset_id": self.asset_id,
            "content_sha256": self.content_sha256,
            "version": self.version,
            "platform_slot": self.platform_slot,
            "responsibility": self.responsibility,
            "authorized": self.authorized,
        }
        if self.project_id:
            d["project_id"] = self.project_id
        if self.crop:
            d["crop"] = self.crop
        if self.valid_time_range is not None:
            d["valid_time_range"] = self.valid_time_range.to_dict()
        return d

    def to_runtime_metadata(self) -> Dict[str, Any]:
        """Return runtime-safe asset metadata without free-form notes."""
        d = self.to_dict()
        if self.notes:
            envelope = assert_untrusted_text_safe(
                source_id=self.asset_id,
                source_kind="asset_metadata",
                project_id=self.project_id or "asset_binding",
                content=self.notes,
            )
            d["notes_sha256"] = envelope.content_sha256
            d["notes_role"] = "untrusted_data"
        return d


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def check_asset_conflicts(
    bindings: Sequence[AssetBinding],
) -> List[str]:
    """Return conflicts where multiple assets claim the same platform slot."""
    conflicts: List[str] = []
    slot_map: Dict[str, List[AssetBinding]] = {}
    for b in bindings:
        slot_map.setdefault(b.platform_slot, []).append(b)

    for slot, items in slot_map.items():
        if len(items) > 1:
            ids = [b.asset_id for b in items]
            # Check if conflict can be resolved by priority
            priorities = [b.conflict_priority for b in items]
            if len(set(priorities)) == 1:
                conflicts.append(
                    f"Slot '{slot}' has {len(items)} assets with same priority: "
                    f"{', '.join(ids)} — manual resolution required"
                )
            else:
                winner = max(items, key=lambda b: b.conflict_priority)
                conflicts.append(
                    f"Slot '{slot}' conflict: {', '.join(ids)} → "
                    f"'{winner.asset_id}' wins by priority {winner.conflict_priority}"
                )
    return conflicts


def check_asset_authorization(
    bindings: Sequence[AssetBinding],
) -> List[str]:
    """Return violations for unauthorized assets."""
    violations: List[str] = []
    for b in bindings:
        if not b.authorized:
            violations.append(
                f"Asset '{b.asset_id}' (slot '{b.platform_slot}') "
                f"is not authorized for use"
            )
    return violations


def check_asset_project_scope(
    bindings: Sequence[AssetBinding],
    project_id: str,
) -> List[str]:
    """Return violations for missing or mismatched project scope."""
    violations: List[str] = []
    for b in bindings:
        if not b.project_id:
            violations.append(
                f"Asset '{b.asset_id}' (slot '{b.platform_slot}') has no project scope"
            )
        elif b.project_id != project_id:
            violations.append(
                f"Asset '{b.asset_id}' belongs to project '{b.project_id}', "
                f"not '{project_id}'"
            )
    return violations
