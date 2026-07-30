"""MODE:P vNext — v4/vNext Contamination Scanner (V0.4).

Enforces the isolation boundary between v4 (read-only black-box) and vNext:

1. **Write safety**: vNext code must never write into v4 Session, delivery,
   cache, or knowledge directories.  Attempts raise ``ContaminationError``.

2. **Import scan**: v4 active entry-point files must not import unapproved
   vNext modules.  A baseline scan returns zero violations.

3. **Allowed cross-refs**: Explicit read-only paths (e.g. the V0.1 baseline
   manifest) are permitted for both sides to reference.

Spec references: LOOP §15.1, §24, §27.
"""

from pathlib import Path
from typing import List, Set, Union


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class ContaminationError(Exception):
    """Raised when vNext attempts to write into v4-protected territory."""
    pass


# ---------------------------------------------------------------------------
# v4 protected territory (paths vNext MUST NOT write to)
# ---------------------------------------------------------------------------

# Resolved lazily via _get_project_root()
_V4_PROTECTED_SUBDIRS: List[str] = []


def _get_project_root() -> Path:
    """Return the project root (parent of mode_p_vnext's parent)."""
    this_file = Path(__file__).resolve()
    # mode_p_vnext / contamination_scanner.py → parent → parent
    return this_file.parent.parent.parent


def _get_mode_p_root() -> Path:
    return _get_project_root() / "01_调度器" / "mode_p"


def _get_v4_protected_paths() -> List[Path]:
    """Return absolute paths that vNext must not write to."""
    mode_p = _get_mode_p_root()
    return [
        mode_p,                          # entire v4 runtime directory
        mode_p / "knowledge",            # v4 knowledge files
        mode_p / "sessions",             # v4 session data
        mode_p / "delivery",             # v4 delivery output
        mode_p / ".cache",               # v4 cache
        mode_p / "__pycache__",          # v4 bytecode (shouldn't write here anyway)
    ]


# ---------------------------------------------------------------------------
# Allowed cross-references
# ---------------------------------------------------------------------------

ALLOWED_VNEXT_REFS_FROM_V4: Set[str] = {
    "MODE_P_REDESIGN_PROJECT/vnext_baseline/",
}

# These are the v4 files considered "active entrypoints" — any vNext import
# in them is a violation unless explicitly whitelisted.
V4_ACTIVE_ENTRYPOINT_PATTERNS = [
    "01_调度器/mode_p/*.py",
]


# ---------------------------------------------------------------------------
# Write safety check
# ---------------------------------------------------------------------------

def check_vnext_write_safe(target: Union[str, Path]) -> None:
    """Raise ``ContaminationError`` if *target* is inside v4 protected territory.

    vNext code must call this before writing any file outside its own package
    directory, especially when a future task might generate output into
    shared project paths.

    Parameters
    ----------
    target : str or Path
        The absolute or relative path the caller intends to write to.

    Raises
    ------
    ContaminationError
        If *target* resolves inside v4 protected territory.
    """
    target = Path(target).resolve()
    for protected in _get_v4_protected_paths():
        try:
            target.relative_to(protected)
            # If we get here, target is inside the protected path
            raise ContaminationError(
                f"vNext write blocked: {target} is inside v4 protected "
                f"territory ({protected}). vNext must not write to v4 "
                f"Session, delivery, cache, or knowledge directories."
            )
        except ValueError:
            # target is NOT under this protected path — continue checking
            continue


# ---------------------------------------------------------------------------
# v4 import scan
# ---------------------------------------------------------------------------

def scan_v4_for_vnext_imports() -> List[str]:
    """Scan v4 active entrypoint files for unapproved vNext imports.

    Returns a list of human-readable violation strings. An empty list
    means no contamination detected.

    This is a mechanical check — it looks for literal ``import mode_p_vnext``
    or ``from mode_p_vnext`` statements in v4 Python source files.
    """
    violations: List[str] = []
    mode_p_root = _get_mode_p_root()
    if not mode_p_root.is_dir():
        return violations

    for py_file in mode_p_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        file_violations = _scan_file_for_vnext_imports(py_file)
        violations.extend(file_violations)

    return violations


def _scan_file_for_vnext_imports(file_path: Path) -> List[str]:
    """Scan a single Python file for vNext import statements."""
    violations: List[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return violations

    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("import mode_p_vnext", "from mode_p_vnext")):
            violations.append(f"{file_path}:{lineno}: {stripped}")
    return violations


# ---------------------------------------------------------------------------
# Read-only cross-reference whitelist
# ---------------------------------------------------------------------------

def is_allowed_readonly_ref(target: Union[str, Path]) -> bool:
    """Return True if *target* is an explicitly allowed read-only cross-ref.

    Both v4 and vNext are permitted to read from these paths, but neither
    side may write to them through the other's runtime.
    """
    target = Path(target).resolve()
    project_root = _get_project_root()

    for allowed_rel in ALLOWED_VNEXT_REFS_FROM_V4:
        allowed_abs = (project_root / allowed_rel).resolve()
        try:
            target.relative_to(allowed_abs)
            return True
        except ValueError:
            continue
    return False
