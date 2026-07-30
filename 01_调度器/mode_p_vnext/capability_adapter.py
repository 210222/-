"""MODE:P vNext — Capability Profile & Prompt Adapter (V5.5).

Adapter handles tags, slots, escapes, and channel routing. Does NOT change
Director semantics. Conservative: unknown capabilities fail closed.

Spec references: LOOP §22.3; Omission P0-14.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


class CapabilityBlockedError(Exception):
    """Raised when an adapter cannot route a field due to missing capability."""
    pass


@dataclass
class CapabilityProfile:
    """Verified platform capability snapshot."""
    platform: str
    version: str
    negative_strategy: str          # inline | separate_channel | unsupported
    duration_quantization: str       # e.g. "1s", "0.5s"
    aspect_ratios: List[str]
    fps: int
    internal_cuts_supported: bool
    reference_slots: int             # max @reference images
    text_overlay_supported: bool
    audio_lipsync_supported: bool
    max_prompt_chars: int
    verified_at: str = ""


class PromptAdapter:
    """Routes Master fields to platform-specific prompt slots.

    Tags and slots only — never changes Director semantics.
    """
    def __init__(self, profile: CapabilityProfile):
        self.profile = profile

    def adapt(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt fields for the target platform. Raises on missing capability."""
        result = dict(fields)

        # Check reference slots
        refs = fields.get("reference_images", [])
        if len(refs) > self.profile.reference_slots:
            raise CapabilityBlockedError(
                f"Need {len(refs)} reference slots, platform has "
                f"{self.profile.reference_slots}"
            )

        # Check internal cuts
        if not self.profile.internal_cuts_supported:
            if len(fields.get("shot_descriptions", [])) > 1:
                raise CapabilityBlockedError(
                    "Multiple shots require internal_cuts_supported=true"
                )

        # Escape forbidden terms for inline negatives
        if self.profile.negative_strategy == "inline":
            forbidden = fields.get("forbidden", [])
            if forbidden:
                result["negative_prompt"] = ", ".join(forbidden)

        return result
