"""Retired vNext.1 persistent contracts; historical evidence only.

The executable source before v3 convergence is retained by Git blob OID.
Canonical construction must use :mod:`mode_p_vnext.domain`.
"""

from __future__ import annotations

from typing import Mapping

from mode_p_vnext.compat.retired_authority import (
    LegacyAuthorityObservation,
    observe_legacy_payload as _observe,
    reject_legacy_construction,
)

MIGRATION_DISPOSITION = "HISTORICAL_READ_ONLY"
PERSISTENT_CONSTRUCTION_AUTHORIZED = False
HISTORICAL_GIT_BLOB_OID = "5002e9b9b2a12afaaba25591d1668c4d60864a24"
CANONICAL_REPLACEMENT_MODULES = (
    "mode_p_vnext.domain.blocking",
    "mode_p_vnext.domain.decisions",
    "mode_p_vnext.domain.direction",
    "mode_p_vnext.domain.vec",
)


def observe_legacy_payload(payload: Mapping[str, object]) -> LegacyAuthorityObservation:
    return _observe(
        payload,
        source_module=__name__,
        historical_git_blob_oid=HISTORICAL_GIT_BLOB_OID,
    )


def construct_legacy_authority(*_args: object, **_kwargs: object) -> None:
    reject_legacy_construction(__name__)


def __getattr__(name: str) -> object:
    if name.startswith("__"):
        raise AttributeError(name)
    reject_legacy_construction(f"{__name__}.{name}")
