"""MODE:P Director vNext.1.

This namespace implements the separately controlled Director construction
chain.  Importing it never enables Shadow, external submission, or production.
"""

from __future__ import annotations

__all__ = ["DirectorDdoControl"]

from .control import DirectorDdoControl
