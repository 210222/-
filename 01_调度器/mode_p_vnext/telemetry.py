"""MODE:P vNext — Telemetry, SLO & Error Classification (V9.6).

Records stage timing, budget, cache, failure type, approval status, and
recovery results. Does NOT log private reasoning or media content.

Spec references: LOOP §26-§28; Audit P0-05/P1-05.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StageEvent:
    stage: str
    duration_ms: int
    budget_remaining: int = 0
    cache_hit: bool = False
    # Explicitly NO: director_reasoning, media_content, prompt_text


@dataclass
class ErrorEvent:
    error_type: str
    stage: str
    message: str
    recoverable: bool = False
    # Explicitly NO: private data, stack traces with sensitive info


@dataclass
class ApprovalEvent:
    episode_id: str
    status: str     # approved | clarification_requested | revision_requested
    duration_since_storyboard_ready_ms: int = 0


@dataclass
class RecoveryEvent:
    episode_id: str
    from_state: str
    to_state: str
    success: bool
