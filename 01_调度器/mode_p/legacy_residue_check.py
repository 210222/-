"""Legacy residue check — scan active entry points for forbidden patterns.

Detects references to decommissioned MODE:P patterns that must not appear
in active code paths: old Agent chains, Seko packaging, YAML protocols,
TIME_SKELETON, Gate reports, and rule-ID proofs.

Usage:
    python -m legacy_residue_check [paths...]
    python -m legacy_residue_check --json [paths...]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


# Patterns that must NOT appear in active code paths
# Each entry: (pattern, severity, category, description)
_FORBIDDEN_PATTERNS: list[tuple[str, str, str, str]] = [
    # Seko platform
    (r"@图片\d+", "high", "seko", "Seko image placeholder syntax"),
    (r"[Ss]eko\s*(平台|包装|输出|格式)", "high", "seko", "Seko platform packaging"),
    (r"seko_packag", "high", "seko", "Seko packaging module reference"),

    # Old Agent chains
    (r"specialist.*[Aa]gent.*chain", "high", "old_agent", "Specialist design agent chain"),
    (r"(Shot|Movement|Composition|Lighting|Transition)Agent", "high", "old_agent",
     "Domain-specific design agent"),
    (r"domain_agent|specialist_agent|design_agent", "high", "old_agent",
     "Old agent architecture references"),

    # YAML Agent protocols
    (r"YAML\s*[Aa]gent\s*[Pp]rotocol", "high", "yaml_agent", "YAML agent protocol"),
    (r"agent_protocol\.ya?ml", "high", "yaml_agent", "Agent protocol YAML file"),
    (r"AGENT_PROTOCOL", "high", "yaml_agent", "Agent protocol constant"),

    # TIME_SKELETON
    (r"TIME_SKELETON", "high", "time_skeleton", "Time skeleton reference"),
    (r"time_skeleton\.(md|json|ya?ml)", "high", "time_skeleton", "Time skeleton file"),

    # Gate reports
    (r"Gate\s*[Rr]eport", "high", "gate", "Gate report reference"),
    (r"GATE_REPORT|gate_report", "high", "gate", "Gate report constant/file"),
    (r"gate_\d+_report", "high", "gate", "Numbered gate report"),

    # Rule ID proofs
    (r"rule[-_]?[Ii][Dd]\s*:?\s*[A-Z]+-\d+", "medium", "rule_id", "Rule ID proof syntax"),
    (r"RULE_ID|rule_id_proof", "medium", "rule_id", "Rule ID proof constant"),
    (r"rule[-_]?audit", "medium", "rule_id", "Rule audit reference"),

    # PLAN documents
    (r"\bPLAN\.md\b", "medium", "plan", "PLAN.md document reference"),
    (r"design_plan\.md", "medium", "plan", "Design plan document"),

    # Legacy mode_p
    (r"legacy_mode_p", "high", "legacy", "Legacy mode_p directory reference"),
    (r"from legacy_mode_p", "high", "legacy", "Legacy mode_p import"),

    # Old audit/score
    (r"audit_score|audit_report|complexity_score", "medium", "audit",
     "Old audit/score system"),
    (r"complexity_agent|complexity_router", "high", "audit",
     "Complexity routing agent"),
]

# Paths to exclude from scanning
_EXCLUDE_GLOBS = [
    "**/__pycache__/**",
    "**/.git/**",
    "**/.claude/worktrees/**",
    "**/legacy_mode_p/**",
    "**/05_项目经验/**",
    "**/*.pyc",
    "**/runtime_cache/**",
    "**/staging/**",
    "**/telemetry/**",
    "**/node_modules/**",
]

# Files that are allowed to reference legacy concepts (documentation only)
_ALLOWED_REFERENCES = [
    "MODE_P_REDESIGN_PROJECT/IMPLEMENTATION_PLAN.md",
    "MODE_P_REDESIGN_PROJECT/PROGRESS.md",
    "MODE_P_REDESIGN_PROJECT/LOOP_SPEC.md",
    "CLAUDE.md",
    "01_调度器/mode_p/legacy_residue_check.py",
    "01_调度器/mode_p/test_legacy_residue_check.py",
]


@dataclass
class ResidueMatch:
    file: str
    line: int
    severity: str  # high / medium
    category: str
    description: str
    matched_text: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("to_dict", None)
        return d


@dataclass
class ResidueReport:
    findings: list[ResidueMatch] = field(default_factory=list)
    files_scanned: int = 0
    lines_scanned: int = 0
    high_count: int = 0
    medium_count: int = 0

    @property
    def ok(self) -> bool:
        return self.high_count == 0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "files_scanned": self.files_scanned,
            "lines_scanned": self.lines_scanned,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "total_findings": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
        }


def _is_excluded(path: Path, root: Path) -> bool:
    """Check if a path should be excluded from scanning."""
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    rel_str = str(rel).replace("\\", "/")
    for glob in _EXCLUDE_GLOBS:
        if path.match(glob) or Path(rel_str).match(glob):
            return True
    return False


def _is_allowed(path: Path, root: Path) -> bool:
    """Check if a file is in the allowed-reference list."""
    try:
        rel = str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return False
    for allowed in _ALLOWED_REFERENCES:
        if rel == allowed.replace("\\", "/"):
            return True
    return False


def scan_file(path: Path, root: Path) -> list[ResidueMatch]:
    """Scan a single file for legacy residue."""
    findings: list[ResidueMatch] = []
    is_allowed = _is_allowed(path, root)
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return findings
    lines = content.split("\n")
    for i, line in enumerate(lines, start=1):
        for pattern, severity, category, description in _FORBIDDEN_PATTERNS:
            match = re.search(pattern, line)
            if match:
                if is_allowed and severity == "high":
                    continue  # Allow documentation references
                findings.append(ResidueMatch(
                    file=str(path.resolve().relative_to(root.resolve())),
                    line=i,
                    severity=severity,
                    category=category,
                    description=description,
                    matched_text=match.group(0),
                ))
    return findings


def scan_paths(paths: Iterable[Path], root: Path | None = None) -> ResidueReport:
    """Scan one or more paths for legacy residue."""
    if root is None:
        root = Path.cwd()
    report = ResidueReport()
    seen: set[Path] = set()

    for target in paths:
        target = Path(target)
        if not target.exists():
            continue
        files = [target] if target.is_file() else [
            f for f in target.rglob("*")
            if f.is_file() and not f.is_symlink() and f.suffix in
            (".py", ".md", ".json", ".ya?ml", ".txt", ".js", ".ts")
        ]
        for file_path in files:
            resolved = file_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if _is_excluded(file_path, root):
                continue
            findings = scan_file(file_path, root)
            report.findings.extend(findings)
            report.files_scanned += 1
            report.lines_scanned += 1  # approximate; detailed count is expensive

    report.high_count = sum(1 for f in report.findings if f.severity == "high")
    report.medium_count = sum(1 for f in report.findings if f.severity == "medium")
    return report


def scan_active_entrypoints(root: Path | None = None) -> ResidueReport:
    """Scan all active entry points for legacy residue."""
    if root is None:
        root = Path.cwd()
    targets = [
        root / "01_调度器",
        root / ".claude",
        root / "CLAUDE.md",
    ]
    existing = [t for t in targets if t.exists()]
    return scan_paths(existing, root)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan for legacy MODE:P residue in active code paths."
    )
    parser.add_argument(
        "paths", nargs="*", type=Path,
        help="Paths to scan (default: active entry points)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(),
        help="Project root for relative paths",
    )
    args = parser.parse_args()

    if args.paths:
        report = scan_paths(args.paths, args.root)
    else:
        report = scan_active_entrypoints(args.root)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        if not report.findings:
            print("No legacy residue found.")
            return 0
        for f in report.findings:
            print(f"[{f.severity.upper()}] {f.file}:{f.line} — {f.description}")
            print(f"  matched: {f.matched_text}")
        print(f"\n{report.high_count} high, {report.medium_count} medium "
              f"in {report.files_scanned} files")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
