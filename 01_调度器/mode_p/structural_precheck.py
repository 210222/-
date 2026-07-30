"""Orchestrate the full pre-DP structural check pipeline.

This is a deterministic local program. It:
1. Compiles Master → Manifest (master_compiler)
2. Derives views (view_deriver)
3. Runs master_sync_check
4. Runs boundary_check
5. Runs reference_plan_check
6. Runs the deterministic SD2.0 hard-boundary preflight

Any failure blocks the DP call. After DP READY, a separate
final hash/delivery check confirms nothing changed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    passed: bool
    output: str = ""


@dataclass
class PrecheckReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.passed for r in self.results)

    def add(self, name: str, passed: bool, output: str = "") -> None:
        self.results.append(CheckResult(name, passed, output))


def _run_module(module: str, *args: str) -> tuple[int, str]:
    """Run a Python module and return (exit_code, stdout)."""
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-m", module, *args],
        capture_output=True, text=True, encoding="utf-8", errors="strict", timeout=30,
        cwd=Path(__file__).resolve().parent,
        env=child_env,
    )
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part and part.strip()
    )
    return result.returncode, output


def run_precheck(
    master_path: Path,
    session_dir: Path,
    output_dir: Path | None = None,
) -> PrecheckReport:
    """Run the full pre-DP structural check pipeline.

    Writes Manifest and views into output_dir, or session_dir/working/ by
    default.  Runtime callers use an isolated build directory and publish it
    atomically only after every check passes.
    Returns a report; report.ok is True iff all checks pass.
    """
    report = PrecheckReport()
    working = output_dir or session_dir / "working"
    working.mkdir(parents=True, exist_ok=True)

    manifest_path = working / "SHOT_MANIFEST.json"
    storyboard_path = working / "STORYBOARD.md"
    video_path = working / "VIDEO_PROMPT.md"

    # Step 1: Compile Master → Manifest
    code, out = _run_module("master_compiler", str(master_path), str(manifest_path))
    report.add("master_compiler", code == 0, out)
    if code != 0:
        return report  # cannot continue

    # Step 2: Derive views
    code, out = _run_module(
        "view_deriver", str(master_path), str(manifest_path),
        "-s", str(storyboard_path), "-v", str(video_path),
    )
    report.add("view_deriver", code == 0, out)
    if code != 0:
        return report  # cannot continue

    # Step 3: Master sync check
    code, out = _run_module(
        "master_sync_check",
        str(master_path), str(manifest_path),
        str(storyboard_path), str(video_path),
    )
    report.add("master_sync_check", code == 0, out)

    # Step 4: Boundary check
    code, out = _run_module("boundary_check", str(manifest_path))
    report.add("boundary_check", code == 0, out)

    # Step 5: Reference plan check
    code, out = _run_module("reference_plan_check", str(manifest_path))
    report.add("reference_plan_check", code == 0, out)

    # Step 6: hard SD2.0 prompt boundaries.  Advisory quality heuristics are
    # deliberately excluded from this deterministic gate.
    code, out = _run_module("sd2_preflight", str(video_path))
    report.add("sd2_preflight", code == 0, out)

    return report


def run_final_checks(
    master_path: Path,
    session_dir: Path,
    output_dir: Path | None = None,
) -> PrecheckReport:
    """After DP READY: recompile and verify nothing changed structurally.

    This confirms the delivered views still match the Master and Manifest.
    """
    report = PrecheckReport()
    working = output_dir or session_dir / "working"
    manifest_path = working / "SHOT_MANIFEST.json"
    storyboard_path = working / "STORYBOARD.md"
    video_path = working / "VIDEO_PROMPT.md"

    # Final sync check
    code, out = _run_module(
        "master_sync_check",
        str(master_path), str(manifest_path),
        str(storyboard_path), str(video_path),
    )
    report.add("final_master_sync", code == 0, out)

    code, out = _run_module("boundary_check", str(manifest_path))
    report.add("final_boundary_check", code == 0, out)

    code, out = _run_module("reference_plan_check", str(manifest_path))
    report.add("final_reference_plan_check", code == 0, out)

    code, out = _run_module("sd2_preflight", str(video_path))
    report.add("final_sd2_preflight", code == 0, out)

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run pre-DP structural checks."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("precheck", help="Run pre-DP checks (compile + derive + sync + boundary + reference)")
    pre.add_argument("master", type=Path)
    pre.add_argument("session", type=Path)
    pre.add_argument("--output-dir", type=Path)

    final = sub.add_parser("final", help="Run post-DP final delivery checks")
    final.add_argument("master", type=Path)
    final.add_argument("session", type=Path)
    final.add_argument("--output-dir", type=Path)

    args = parser.parse_args()

    if args.command == "precheck":
        report = run_precheck(args.master, args.session, args.output_dir)
    else:
        report = run_final_checks(args.master, args.session, args.output_dir)

    for r in report.results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}")
        if not r.passed and r.output:
            for line in r.output.splitlines()[:10]:
                print(f"  {line}")

    if report.ok:
        print("All structural checks passed.")
        return 0
    else:
        print("Structural checks FAILED — block DP call until fixed.")
        return 1


if __name__ == "__main__":
    from cli_stdio import configure_utf8_stdio

    configure_utf8_stdio()
    raise SystemExit(main())
