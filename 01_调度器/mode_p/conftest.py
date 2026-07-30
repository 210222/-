"""pytest configuration — ensure subprocess CLI tests can find local modules."""
from __future__ import annotations

import os
from pathlib import Path

_MODULE_DIR = str(Path(__file__).parent.resolve())
_existing = os.environ.get("PYTHONPATH", "")
if _existing:
    os.environ["PYTHONPATH"] = f"{_MODULE_DIR}{os.pathsep}{_existing}"
else:
    os.environ["PYTHONPATH"] = _MODULE_DIR
