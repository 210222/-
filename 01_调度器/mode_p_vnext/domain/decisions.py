"""Bounded decision drafts owned by the Director loop."""

from __future__ import annotations

from dataclasses import dataclass

from .artifact import DomainValidationError


DOMAIN_SCHEMA_VERSION = "2.1"
CANONICAL_DOMAIN_TYPES = ("DecisionDraft", "DecisionOptionDraft", "VisualCurvePointDraft")


@dataclass(frozen=True)
class DecisionOptionDraft:
    option: str
    rationale: str
    tradeoff: str

    def __post_init__(self) -> None:
        if any(not getattr(self, field_name).strip() for field_name in ("option", "rationale", "tradeoff")):
            raise DomainValidationError("decision option fields must be non-empty")


@dataclass(frozen=True)
class DecisionDraft:
    decision_question: str
    options: tuple[DecisionOptionDraft, ...]
    selected_option_index: int

    def __post_init__(self) -> None:
        if not self.decision_question.strip():
            raise DomainValidationError("decision_question must be non-empty")
        options = tuple(self.options)
        if len(options) not in {1, 2} or not all(isinstance(item, DecisionOptionDraft) for item in options):
            raise DomainValidationError("Director decisions must contain one or two options")
        if isinstance(self.selected_option_index, bool) or self.selected_option_index not in range(len(options)):
            raise DomainValidationError("selected_option_index must select an available option")
        object.__setattr__(self, "options", options)


@dataclass(frozen=True)
class VisualCurvePointDraft:
    dramatic_beat_ordinal: int
    intensity: int
    explanation: str

    def __post_init__(self) -> None:
        if isinstance(self.dramatic_beat_ordinal, bool) or self.dramatic_beat_ordinal < 1:
            raise DomainValidationError("dramatic_beat_ordinal must be positive")
        if isinstance(self.intensity, bool) or not 0 <= self.intensity <= 100:
            raise DomainValidationError("intensity must be an integer from zero to one hundred")
        if not self.explanation.strip():
            raise DomainValidationError("explanation must be non-empty")
