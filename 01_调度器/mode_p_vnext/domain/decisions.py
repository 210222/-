"""Bounded creative decisions and their locally identified VEC records."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import ClassVar

from .artifact import DOMAIN_SCHEMA_VERSION, ArtifactKind, DomainValidationError
CANONICAL_DOMAIN_TYPES = (
    "DecisionBasis",
    "DecisionDraft",
    "DirectorDecision",
    "VisualCurvePoint",
    "VisualCurvePointDraft",
)


class DecisionBasis(str, enum.Enum):
    LOCKED = "locked"
    CHOICE = "choice"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty")


def _text_tuple(
    value: tuple[str, ...], field_name: str, *, require_items: bool
) -> tuple[str, ...]:
    values = tuple(value)
    if (require_items and not values) or any(
        not isinstance(item, str) or not item.strip() for item in values
    ):
        raise DomainValidationError(
            f"{field_name} must contain only non-empty text"
        )
    return values


def _normalised_option(value: str) -> str:
    return " ".join(value.casefold().split())


def _validate_decision_content(
    *,
    basis: DecisionBasis,
    locked_by: tuple[str, ...],
    options: tuple[str, ...],
    selected_index: int,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not isinstance(basis, DecisionBasis):
        raise DomainValidationError("basis must be locked or choice")
    locked = _text_tuple(
        locked_by,
        "locked_by",
        require_items=basis is DecisionBasis.LOCKED,
    )
    choices = _text_tuple(options, "options", require_items=True)
    if len(choices) > 2:
        raise DomainValidationError("options may contain at most two choices")
    if len({_normalised_option(item) for item in choices}) != len(choices):
        raise DomainValidationError("decision options must be substantively distinct")
    if basis is DecisionBasis.CHOICE:
        if locked:
            raise DomainValidationError("choice decisions cannot carry locked_by")
        if len(choices) != 2:
            raise DomainValidationError(
                "choice decisions require exactly two options"
            )
    elif len(choices) != 1:
        raise DomainValidationError(
            "locked decisions require exactly one resolved option"
        )
    if (
        isinstance(selected_index, bool)
        or not isinstance(selected_index, int)
        or selected_index not in range(len(choices))
    ):
        raise DomainValidationError(
            "selected_index must select an available option"
        )
    return locked, choices


@dataclass(frozen=True)
class DecisionDraft:
    """The exact B1 decision shape; it carries no machine-generated ID."""

    ARTIFACT_KIND: ClassVar[ArtifactKind] = ArtifactKind.DECISION_DRAFT

    scope: str
    basis: DecisionBasis
    locked_by: tuple[str, ...]
    options: tuple[str, ...]
    selected_index: int
    rationale: str
    tradeoff: str

    def __post_init__(self) -> None:
        for field_name in ("scope", "rationale", "tradeoff"):
            _require_text(getattr(self, field_name), field_name)
        locked, options = _validate_decision_content(
            basis=self.basis,
            locked_by=self.locked_by,
            options=self.options,
            selected_index=self.selected_index,
        )
        object.__setattr__(self, "locked_by", locked)
        object.__setattr__(self, "options", options)


@dataclass(frozen=True)
class DirectorDecision:
    """A locally identified decision record embedded in the final VEC."""

    decision_id: str
    source_decision_ordinal: int
    scope: str
    basis: DecisionBasis
    locked_by: tuple[str, ...]
    options: tuple[str, ...]
    selected_index: int
    rationale: str
    tradeoff: str

    def __post_init__(self) -> None:
        for field_name in ("decision_id", "scope", "rationale", "tradeoff"):
            _require_text(getattr(self, field_name), field_name)
        if (
            isinstance(self.source_decision_ordinal, bool)
            or not isinstance(self.source_decision_ordinal, int)
            or self.source_decision_ordinal < 1
        ):
            raise DomainValidationError(
                "source_decision_ordinal must be a positive integer"
            )
        locked, options = _validate_decision_content(
            basis=self.basis,
            locked_by=self.locked_by,
            options=self.options,
            selected_index=self.selected_index,
        )
        object.__setattr__(self, "locked_by", locked)
        object.__setattr__(self, "options", options)


@dataclass(frozen=True)
class VisualCurvePointDraft:
    dramatic_beat_ordinal: int
    intensity: int
    explanation: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.dramatic_beat_ordinal, bool)
            or not isinstance(self.dramatic_beat_ordinal, int)
            or self.dramatic_beat_ordinal < 1
        ):
            raise DomainValidationError(
                "dramatic_beat_ordinal must be a positive integer"
            )
        if (
            isinstance(self.intensity, bool)
            or not isinstance(self.intensity, int)
            or not 0 <= self.intensity <= 100
        ):
            raise DomainValidationError(
                "intensity must be an integer from zero to one hundred"
            )
        _require_text(self.explanation, "explanation")


@dataclass(frozen=True)
class VisualCurvePoint:
    point_id: str
    source_curve_ordinal: int
    blocking_beat_id: str
    intensity: int
    explanation: str

    def __post_init__(self) -> None:
        for field_name in ("point_id", "blocking_beat_id", "explanation"):
            _require_text(getattr(self, field_name), field_name)
        if (
            isinstance(self.source_curve_ordinal, bool)
            or not isinstance(self.source_curve_ordinal, int)
            or self.source_curve_ordinal < 1
        ):
            raise DomainValidationError(
                "source_curve_ordinal must be a positive integer"
            )
        if (
            isinstance(self.intensity, bool)
            or not isinstance(self.intensity, int)
            or not 0 <= self.intensity <= 100
        ):
            raise DomainValidationError(
                "intensity must be an integer from zero to one hundred"
            )
