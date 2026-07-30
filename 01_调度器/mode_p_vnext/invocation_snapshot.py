"""MODE:P vNext — Model Invocation Snapshot (V6.5).

Records model/product version, parameters, full input hash, output hash,
invocation ID, retries, and replay semantics.

Spec references: LOOP §21.5, §22; Omission P0-13.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class InvocationSnapshot:
    invocation_id: str
    model: str
    provider_version: str
    input_sha256: str
    output_sha256: str
    sampling_params: Dict[str, Any] = field(default_factory=dict)
    finish_reason: str = "stop"
    retry_count: int = 0
    allow_replay_compile: bool = True     # deterministic re-compile from saved response
    allow_reinvoke: bool = False           # re-call model with same input (new branch)
    allow_regenerate: bool = False         # re-call model with new parameters

    @property
    def truncated(self) -> bool:
        return self.finish_reason == "length"
