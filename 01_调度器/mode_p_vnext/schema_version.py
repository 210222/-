"""MODE:P vNext — Schema Version & Migration Strategy (V4.6).

Explicit schema version with compatibility window rules. Major version
changes invalidate prior approvals. Migration is read-only — vNext never
writes back to old-schema sessions.

Spec references: LOOP §24, §25.
"""

from __future__ import annotations

CURRENT_SCHEMA_VERSION = "4.0"
COMPATIBLE_MAJOR = 4
MIGRATION_READ_ONLY = True


def parse_version(v: str) -> tuple[int, int]:
    major, _, minor = v.partition(".")
    return int(major), int(minor)


def is_compatible(producer_version: str, consumer_version: str) -> bool:
    """Return True if *consumer* can read artifacts from *producer*.

    Compatible when same major version and consumer minor >= producer minor.
    """
    pmaj, pmin = parse_version(producer_version)
    cmaj, cmin = parse_version(consumer_version)
    if pmaj != cmaj:
        return False
    return cmin >= pmin


def major_change_invalidates(old_version: str, new_version: str) -> bool:
    """Return True if upgrading from old to new invalidates prior approvals."""
    omaj, _ = parse_version(old_version)
    nmaj, _ = parse_version(new_version)
    return nmaj > omaj
