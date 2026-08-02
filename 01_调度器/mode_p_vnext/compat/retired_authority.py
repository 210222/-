"""Fail-closed observation boundary for pre-v3 persistent authorities.

Retired modules may expose their raw records only as immutable, non-persistent
observations.  They cannot construct a canonical artifact, mint an ID, write a
checkpoint, or provide an executable compatibility schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from mode_p_vnext.domain.artifact import DomainValidationError


class RetiredAuthorityError(RuntimeError):
    """Raised whenever rejected historical code attempts construction."""


def _require_git_blob_oid(value: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise DomainValidationError("historical_git_blob_oid must be a Git SHA-1 OID")
    return value


def _freeze_legacy_value(value: object) -> object:
    if isinstance(value, Mapping):
        frozen = {
            str(key): _freeze_legacy_value(item)
            for key, item in value.items()
        }
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_legacy_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_legacy_value(item) for item in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise DomainValidationError(
        "legacy observation accepts only JSON-compatible scalar/container values"
    )


@dataclass(frozen=True)
class LegacyAuthorityObservation:
    """Non-persistent view of one rejected historical payload."""

    source_module: str
    historical_git_blob_oid: str
    raw_payload: Mapping[str, object]
    requires_reingest: bool = True
    persistent_write_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.source_module, str) or not self.source_module.strip():
            raise DomainValidationError("source_module must be non-empty")
        _require_git_blob_oid(self.historical_git_blob_oid)
        if not isinstance(self.raw_payload, Mapping):
            raise DomainValidationError("raw_payload must be a mapping")
        object.__setattr__(
            self,
            "raw_payload",
            _freeze_legacy_value(self.raw_payload),
        )
        if self.requires_reingest is not True:
            raise DomainValidationError("legacy authority observations require reingest")
        if self.persistent_write_authorized is not False:
            raise DomainValidationError("legacy authority observations cannot authorize writes")


def observe_legacy_payload(
    payload: Mapping[str, object],
    *,
    source_module: str,
    historical_git_blob_oid: str,
) -> LegacyAuthorityObservation:
    """Return an immutable observation without granting v3 authority."""

    return LegacyAuthorityObservation(
        source_module=source_module,
        historical_git_blob_oid=historical_git_blob_oid,
        raw_payload=payload,
    )


def reject_legacy_construction(source_module: str) -> None:
    """Reject every attempt to execute a retired persistent constructor."""

    raise RetiredAuthorityError(
        f"{source_module} persistent authority is retired; reingest through canonical v3 services"
    )
