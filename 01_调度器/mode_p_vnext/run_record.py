"""MODE:P vNext — Storyboard / Render Run Record (V8.6).

Binds submitted text, actual assets, platform parameters, task ID, version,
and output hash. No run record → cannot promote to validated evidence.

Spec references: LOOP §9 Step 15, §21.7; Omission P0-12.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StoryboardRunRecord:
    record_id: str
    submitted_prompt_hash: str
    storyboard_image_hash: str
    task_id: str
    platform: str
    platform_version: str = ""
    can_promote_to_validated: bool = True


@dataclass
class RenderRunRecord:
    record_id: str
    submitted_payload_hash: str
    video_output_hash: str
    task_id: str
    platform: str
    platform_version: str = ""
    can_promote_to_validated: bool = True


def RunRecord() -> None:
    """No run record exists yet — returns None to signal missing evidence."""
    return None
