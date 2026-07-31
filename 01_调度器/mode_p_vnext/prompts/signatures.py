"""The four declarative model-stage signatures required by architecture v2.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class Stage(str, Enum):
    E0 = "E0"
    S1 = "S1"
    B0 = "B0"
    B1 = "B1"


@dataclass(frozen=True)
class StageSignature:
    """A compact declaration of one creative Draft call.

    This is deliberately not a runtime transcript, project rulebook, or
    recursive output contract.  Schema shape travels through the structured
    transport channel and deterministic assembly belongs to later services.
    """

    stage: Stage
    version: str
    contract_name: str
    semantic_goal: str
    approved_input_fields: tuple[str, ...]
    output_semantics: tuple[str, ...]
    output_exclusions: tuple[str, ...]
    prompt_budget: int
    schema_budget: int
    soft_prompt_target: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stage, Stage):
            raise TypeError("stage must be a Stage")
        for field_name in ("version", "contract_name", "semantic_goal"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")
        for field_name in (
            "approved_input_fields",
            "output_semantics",
            "output_exclusions",
        ):
            values = tuple(getattr(self, field_name))
            if not values or any(not item.strip() for item in values):
                raise ValueError(f"{field_name} must contain non-empty values")
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
            object.__setattr__(self, field_name, values)
        if self.prompt_budget <= 0 or self.schema_budget <= 0:
            raise ValueError("prompt and schema budgets must be positive")
        if self.soft_prompt_target is not None and not 0 < self.soft_prompt_target <= self.prompt_budget:
            raise ValueError("soft prompt target must fit within hard prompt budget")


_STAGE_SIGNATURES: Mapping[Stage, StageSignature] = MappingProxyType({
    Stage.E0: StageSignature(
        stage=Stage.E0,
        version="1.0",
        contract_name="EpisodeDirectionDraft",
        semantic_goal="Choose stable episode-level dramatic direction from approved episode facts.",
        approved_input_fields=("episode facts", "episode constraints"),
        output_semantics=("dramatic direction", "visual principles", "guardrails"),
        output_exclusions=("shots", "lenses", "camera movement", "final VEC", "IDs and hashes"),
        prompt_budget=6_000,
        schema_budget=2_500,
    ),
    Stage.S1: StageSignature(
        stage=Stage.S1,
        version="1.0",
        contract_name="SceneIntentDraft",
        semantic_goal="Diagnose scene change, information strategy, and Director questions.",
        approved_input_fields=("scene facts", "episode direction", "continuity state"),
        output_semantics=("scene intent", "dramatic turn", "problem set"),
        output_exclusions=("shots", "lenses", "camera movement", "final VEC", "IDs and hashes"),
        prompt_budget=8_000,
        schema_budget=3_500,
    ),
    Stage.B0: StageSignature(
        stage=Stage.B0,
        version="1.0",
        contract_name="BlockingDraft",
        semantic_goal="Choose motivated character, prop, gaze, and spatial states before execution design.",
        approved_input_fields=("scene intent", "K1 decision view", "continuity state"),
        output_semantics=("blocking beats", "causal action paths", "entry and exit state"),
        output_exclusions=("shots", "lenses", "camera movement", "final VEC", "IDs and hashes"),
        prompt_budget=10_000,
        schema_budget=4_500,
    ),
    Stage.B1: StageSignature(
        stage=Stage.B1,
        version="1.0",
        contract_name="ExecutionDesignDraft",
        semantic_goal="Choose executable visual beats, alternatives, transitions, audio, references, and handoff intent after approved blocking.",
        approved_input_fields=("compact scene intent", "blocking summary", "K2 decision view", "reference requirements"),
        output_semantics=("curve points", "decisions", "shot intents", "transition intents", "audio intents", "reference intents", "handoff intent"),
        output_exclusions=("final VEC", "absolute ticks", "source fact hashes", "phase A fingerprint", "blocking commit copy", "contract IDs", "shot IDs", "mirror safety constants"),
        prompt_budget=12_000,
        schema_budget=4_500,
        soft_prompt_target=9_000,
    ),
})


def stage_signatures() -> Mapping[Stage, StageSignature]:
    """Return the immutable-by-convention registry of all model stages."""

    return _STAGE_SIGNATURES
