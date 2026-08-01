"""Model-produced dramatic direction drafts, without execution authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .artifact import DOMAIN_SCHEMA_VERSION, ArtifactKind, DomainValidationError
CANONICAL_DOMAIN_TYPES = ("EpisodeDirectionDraft", "SceneIntentDraft")


def _texts(value: tuple[str, ...], field_name: str, *, require_items: bool) -> tuple[str, ...]:
    values = tuple(value)
    if (require_items and not values) or any(not isinstance(item, str) or not item.strip() for item in values):
        raise DomainValidationError(f"{field_name} must contain only non-empty text")
    return values


@dataclass(frozen=True)
class EpisodeDirectionDraft:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.EPISODE_DIRECTION_DRAFT

    dramatic_promise: str
    audience_contract: str
    tension_curve: tuple[str, ...]
    visual_principles: tuple[str, ...]
    continuity_priorities: tuple[str, ...]
    unresolved_questions: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.dramatic_promise, str)
            or not self.dramatic_promise.strip()
            or not isinstance(self.audience_contract, str)
            or not self.audience_contract.strip()
        ):
            raise DomainValidationError("dramatic_promise and audience_contract must be non-empty")
        for field_name in ("tension_curve", "visual_principles", "continuity_priorities"):
            object.__setattr__(self, field_name, _texts(getattr(self, field_name), field_name, require_items=True))
        object.__setattr__(
            self,
            "unresolved_questions",
            _texts(self.unresolved_questions, "unresolved_questions", require_items=False),
        )


@dataclass(frozen=True)
class SceneIntentDraft:
    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.SCENE_INTENT_DRAFT

    scene_purpose: str
    state_change: str
    audience_information: tuple[str, ...]
    character_knowledge: tuple[str, ...]
    performance_questions: tuple[str, ...]
    director_problems: tuple[str, ...]
    continuity_effects: tuple[str, ...]
    unresolved_questions: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.scene_purpose, str)
            or not self.scene_purpose.strip()
            or not isinstance(self.state_change, str)
            or not self.state_change.strip()
        ):
            raise DomainValidationError("scene_purpose and state_change must be non-empty")
        for field_name in (
            "audience_information",
            "character_knowledge",
            "performance_questions",
            "director_problems",
            "continuity_effects",
            "unresolved_questions",
        ):
            object.__setattr__(self, field_name, _texts(getattr(self, field_name), field_name, require_items=False))
