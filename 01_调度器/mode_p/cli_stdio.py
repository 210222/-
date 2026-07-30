"""Stable UTF-8 stdio contract for MODE:P command-line entry points."""

from __future__ import annotations

import sys
from typing import TextIO


def _reconfigure_utf8(stream: TextIO) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="strict")
    except (OSError, ValueError):
        # Embedded/captured streams may already be detached or immutable.  Their
        # owner controls the encoding, so leave them untouched.
        return


def configure_utf8_stdio() -> None:
    """Make CLI pipe output deterministic across Windows code pages."""

    _reconfigure_utf8(sys.stdout)
    _reconfigure_utf8(sys.stderr)
