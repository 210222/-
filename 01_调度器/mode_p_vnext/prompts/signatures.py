"""Frozen declarative model-stage signatures for the v3.0 architecture."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class Stage(str, Enum):
    I0 = "I0"
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
    approved_input_keys: tuple[str, ...] = ()

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
        input_keys = tuple(self.approved_input_keys)
        if not input_keys or any(
            not isinstance(item, str) or not item or not item.isidentifier()
            for item in input_keys
        ):
            raise ValueError("approved_input_keys must contain non-empty identifier keys")
        if len(input_keys) != len(set(input_keys)):
            raise ValueError("approved_input_keys must not contain duplicates")
        object.__setattr__(self, "approved_input_keys", input_keys)

    def assert_approved_input(self, approved_input: Mapping[str, object]) -> None:
        """Reject undeclared transport fields before any provider invocation."""

        if not isinstance(approved_input, Mapping):
            raise TypeError("approved_input must be a mapping")
        unexpected = set(approved_input) - set(self.approved_input_keys)
        if unexpected:
            raise ValueError(
                f"{self.stage.value} approved input contains undeclared fields: "
                + ",".join(sorted(str(item) for item in unexpected))
            )


_STAGE_SIGNATURES: Mapping[Stage, StageSignature] = MappingProxyType({
    Stage.I0: StageSignature(
        stage=Stage.I0,
        version="3.0",
        contract_name="FactExtractionDraft",
        semantic_goal=(
            "Extract only source-anchored script facts for deterministic local "
            "assembly; make no narrative or visual design decisions."
        ),
        approved_input_fields=(
            "normalized source document",
            "source digest",
            "source segment bounds",
        ),
        output_semantics=(
            "source spans",
            "fact semantics",
            "source-supported statements",
            "optional subject identifiers",
            "optional dialogue text",
        ),
        output_exclusions=(
            "fact IDs",
            "artifact IDs",
            "scene or partition identifiers",
            "hashes",
            "validation status",
            "creative decisions",
            "camera, composition, movement, performance, and editing",
            "reference bindings, audio files, VEC, projections, and delivery prompts",
            "Golden, Holdout, historical outputs, and task records",
        ),
        # I0 is deliberately bounded like the smaller E0 transport. A8 must
        # split independent normalized-source windows rather than truncate facts.
        prompt_budget=6_000,
        schema_budget=2_500,
        approved_input_keys=(
            "normalized_source",
            "source_digest",
            "source_start",
            "source_end",
        ),
    ),
    Stage.E0: StageSignature(
        stage=Stage.E0,
        version="3.0",
        contract_name="EpisodeDirectionDraft",
        semantic_goal="Choose stable episode-level dramatic direction from approved episode facts.",
        approved_input_fields=("episode facts", "episode constraints"),
        output_semantics=("dramatic promise", "audience contract", "tension curve", "visual principles", "continuity priorities", "unresolved questions"),
        output_exclusions=("shots", "lenses", "camera movement", "final VEC", "IDs and hashes"),
        prompt_budget=6_000,
        schema_budget=2_500,
        approved_input_keys=(
            "episode_id",
            "episode_facts",
            "episode_constraints",
            "continuity_state",
        ),
    ),
    Stage.S1: StageSignature(
        stage=Stage.S1,
        version="3.0",
        contract_name="SceneIntentDraft",
        semantic_goal="Diagnose scene change, information strategy, and Director questions.",
        approved_input_fields=("scene facts", "episode direction", "continuity state"),
        output_semantics=("scene purpose", "state change", "audience information", "character knowledge", "performance questions", "director problems", "continuity effects", "unresolved questions"),
        output_exclusions=("shots", "lenses", "camera movement", "final VEC", "IDs and hashes"),
        prompt_budget=8_000,
        schema_budget=3_500,
        approved_input_keys=(
            "scene_id",
            "scene_facts",
            "episode_direction",
            "continuity_state",
            "knowledge_view",
        ),
    ),
    Stage.B0: StageSignature(
        stage=Stage.B0,
        version="3.0",
        contract_name="BlockingDraft",
        semantic_goal="Choose motivated character, prop, gaze, and spatial states before execution design.",
        approved_input_fields=("scene intent", "K1 decision view", "continuity state"),
        output_semantics=("blocking beats", "dramatic actions", "character and prop states", "gaze relations", "causal action paths", "continuity effects"),
        output_exclusions=("shots", "lenses", "camera movement", "final VEC", "IDs and hashes"),
        prompt_budget=10_000,
        schema_budget=4_500,
        approved_input_keys=(
            "scene_id",
            "scene_intent",
            "knowledge_view",
            "continuity_state",
            "blocking_constraints",
        ),
    ),
    Stage.B1: StageSignature(
        stage=Stage.B1,
        version="3.0",
        contract_name="ExecutionDesignDraft",
        semantic_goal=(
            "Choose creative Shot and VisualBeat intent after approved blocking; "
            "machine bindings may use only approved opaque handles."
        ),
        approved_input_fields=(
            "compact scene intent",
            "approved blocking summary",
            "screened K2 decision view",
            "capability profile",
            "approved opaque fact handles",
        ),
        output_semantics=(
            "visual curve points",
            "director decisions",
            "shot designs",
            "duration intents",
            "generation modes",
            "visual beats",
            "typed reference binding intents",
            "typed dialogue binding intents",
            "transition intents",
            "handoff intent",
        ),
        output_exclusions=(
            "final VEC",
            "canonical IDs and hashes",
            "absolute ticks",
            "final timeline",
            "source fact hashes and source-span timing",
            "blocking commit copy",
            "free-text reference or audio machine bindings",
            "contract IDs, shot IDs, boundary IDs, and requirements",
        ),
        prompt_budget=12_000,
        schema_budget=4_500,
        soft_prompt_target=9_000,
        approved_input_keys=(
            "scene_id",
            "scene_intent",
            "blocking_summary",
            "blocking_commit",
            "knowledge_view",
            "capability_profile",
            "approved_fact_handles",
            "reference_requirements",
            "dialogue",
            "audio_facts",
            "continuity_state",
            "knowledge_conflicts",
        ),
    ),
})


def stage_signatures() -> Mapping[Stage, StageSignature]:
    """Return the immutable-by-convention registry of all model stages."""

    return _STAGE_SIGNATURES
