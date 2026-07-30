"""MODE:P vNext — Canonical Serialization Layer (V0.3).

Provides deterministic, platform-independent serialization primitives:

- UTF-8 encoding with LF line endings (never CRLF, never code-page dependent)
- Canonical JSON: sorted keys, compact representation, no whitespace variation
- Stable SHA-256 hashing: same logical content → same hash, always

All file I/O is explicit UTF-8. No implicit code-page behaviour, no CRLF
normalization surprises, no non-deterministic JSON output.

Spec references: LOOP §21.2; Omission P1-15.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Union


# ---------------------------------------------------------------------------
# UTF-8 / LF text utilities
# ---------------------------------------------------------------------------

def ensure_utf8_lf(text: str) -> str:
    """Normalize any line endings to LF and return the string unchanged.

    This does NOT re-encode — Python str has no encoding.  The caller is
    responsible for encoding to UTF-8 bytes at the I/O boundary.
    """
    # Normalize Windows CRLF and legacy bare CR to LF
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    return text


def write_text_utf8_lf(path: Union[str, Path], content: str) -> None:
    """Write *content* to *path* as UTF-8 with LF line endings.

    The file is opened in binary mode so no platform-level newline
    translation can occur (``\n`` stays ``\n`` on Windows).
    """
    normalized = ensure_utf8_lf(content)
    data = normalized.encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(data)


def read_text_utf8_lf(path: Union[str, Path]) -> str:
    """Read *path* as UTF-8 and normalize line endings to LF."""
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    return ensure_utf8_lf(text)


# ---------------------------------------------------------------------------
# Canonical JSON
# ---------------------------------------------------------------------------

def canonical_json_dumps(obj: Any) -> str:
    """Serialize *obj* to a canonical JSON string.

    Guarantees:
    - Object keys are sorted lexicographically (recursively).
    - No insignificant whitespace (compact representation).
    - No trailing whitespace or newline.
    - ``ensure_ascii=False`` so Unicode characters are preserved.
    - ``sort_keys=True`` for top-level keys.
    - Deterministic output for the same Python object.

    NOTE: Python's ``json.dumps(sort_keys=True)`` only sorts top-level keys.
    For deeply canonical output we post-process by parsing through
    ``json.dumps`` with a custom key-sorting approach using an OrderedDict
    round-trip or by implementing a recursive key sort on the object first.
    """
    # Recursively sort all dict keys before serializing
    sorted_obj = _recursive_sort_keys(obj)
    return json.dumps(
        sorted_obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_json_dump(path: Union[str, Path], obj: Any) -> None:
    """Write *obj* as canonical JSON to *path* (UTF-8, LF, no trailing NL)."""
    text = canonical_json_dumps(obj)
    # canonical_json_dumps produces no trailing newline; write exactly that
    write_text_utf8_lf(path, text)


def _recursive_sort_keys(obj: Any) -> Any:
    """Recursively sort all dict keys for canonical output."""
    if isinstance(obj, dict):
        return {k: _recursive_sort_keys(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_recursive_sort_keys(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Stable SHA-256 hashing
# ---------------------------------------------------------------------------

def stable_hash_sha256(data: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()


def stable_hash_file(path: Union[str, Path]) -> str:
    """Return the lowercase hex SHA-256 digest of the file at *path*.

    The file is read as raw bytes — no encoding normalization is applied.
    For text files, call ``write_text_utf8_lf`` first to ensure consistent
    line endings before hashing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return stable_hash_sha256(path.read_bytes())
