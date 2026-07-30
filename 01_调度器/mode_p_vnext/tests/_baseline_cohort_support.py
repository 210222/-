"""Test-only support for the R3.2 v4 baseline cohort reconciliation.

The frozen V0.1 manifest remains immutable historical evidence.  This module
verifies that current pytest collection is fully explained by a reconstructed
generic candidate cohort plus the explicitly registered legacy EP35 suite; it
never upgrades the reconstructed candidate into a historical fact.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Set


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODE_P_DIR = PROJECT_ROOT / "01_调度器" / "mode_p"
LEDGER_PATH = (
    PROJECT_ROOT
    / "MODE_P_REDESIGN_PROJECT"
    / "vnext_repair_evidence"
    / "R3.2_BASELINE_COHORT_RECONCILIATION_001.json"
)


def load_ledger() -> dict[str, Any]:
    """Load the strict, versioned reconciliation ledger."""
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _ids_sha256(ids: Iterable[str]) -> str:
    canonical = "\n".join(sorted(ids)) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def collect_ids(*selection: str) -> Set[str]:
    """Collect v4 test node ids without creating pytest cache state."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--co",
            "-q",
            "-p",
            "no:cacheprovider",
            *selection,
        ],
        cwd=str(MODE_P_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "v4 collection failed: "
            f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    ids = {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("test_") and "::" in line
    }
    if not ids:
        raise AssertionError(f"could not parse test ids from collection output:\n{result.stdout}")
    return ids


def validate_registered_cohorts(
    ledger: dict[str, Any],
    all_ids: Set[str],
    legacy_ids: Set[str],
    generic_ids: Set[str],
) -> None:
    """Fail closed unless collection exactly matches the registered split."""
    assert ledger["status"] == "CURRENT_COLLECTION_RECONCILED_HISTORICAL_EXACT_SET_UNAVAILABLE"
    assert ledger["frozen_manifest"]["declared_test_count"] == 686
    assert ledger["frozen_manifest"]["historical_exact_collection_ids_available"] is False
    assert ledger["acceptance_contract"]["frozen_manifest_is_mutated"] is False

    cohorts = ledger["cohorts"]
    legacy = cohorts["legacy_ep35_s1_post_freeze"]
    generic = cohorts["reconstructed_generic_candidate"]
    relation = ledger["set_relation"]

    source = PROJECT_ROOT / legacy["source_path"]
    assert source.is_file(), f"registered legacy source is missing: {source}"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_hash == legacy["source_sha256"], "registered legacy source changed"

    assert len(all_ids) == ledger["current_collection"]["count"]
    assert _ids_sha256(all_ids) == ledger["current_collection"]["sorted_test_ids_sha256"]
    assert len(legacy_ids) == legacy["count"]
    assert _ids_sha256(legacy_ids) == legacy["sorted_test_ids_sha256"]
    assert len(generic_ids) == generic["count"]
    assert _ids_sha256(generic_ids) == generic["sorted_test_ids_sha256"]

    overlap = legacy_ids & generic_ids
    assert len(overlap) == relation["legacy_intersects_reconstructed_generic"], (
        f"registered cohorts overlap: {sorted(overlap)}"
    )
    union = legacy_ids | generic_ids
    assert len(union) == relation["legacy_union_reconstructed_generic_count"]
    assert union == all_ids, "current v4 collection contains an unregistered delta"
    assert relation["current_collection_equals_registered_union"] is True
    assert relation["unexplained_delta_count"] == 0


def assert_registered_v4_collection() -> None:
    """Collect all three cohorts and enforce their registered set relation."""
    ledger = load_ledger()
    all_ids = collect_ids()
    legacy_ids = collect_ids("test_ep35_s1_pipeline.py")
    generic_ids = collect_ids("--ignore=test_ep35_s1_pipeline.py")
    validate_registered_cohorts(ledger, all_ids, legacy_ids, generic_ids)
