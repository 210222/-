"""Retired pre-v3 fact registry schema; historical evidence only."""

from __future__ import annotations

from typing import Mapping

from mode_p_vnext.compat.retired_authority import (
    LegacyAuthorityObservation,
    observe_legacy_payload as _observe,
    reject_legacy_construction,
)

MIGRATION_DISPOSITION = "HISTORICAL_READ_ONLY"
PERSISTENT_CONSTRUCTION_AUTHORIZED = False
HISTORICAL_GIT_BLOB_OID = "3088208dfdad2b73bbb7d42fcf3d04a4f8f5cc99"
CANONICAL_REPLACEMENT_MODULES = (
    "mode_p_vnext.domain.facts",
    "mode_p_vnext.services.fact_assembler",
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
