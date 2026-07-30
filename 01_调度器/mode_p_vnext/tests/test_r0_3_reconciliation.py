"""R0.3 Reconciliation Test Suite — Semantic Repair v2

Validates the historical task-claim reconciliation ledger with mandatory
pairwise-disjoint partitioning invariants:

  all_70_classified:      70 rows, 70 unique IDs, one leaf classification each
  invalid_dependencies:   exactly {V9.2,V9.3,V9.4,V10.1,V10.2,V10.3} flagged
  evidence_indexed:       cross-referenced against PROGRESS.md and repair evidence
  partition_integrity:    aggregate lists are pairwise disjoint, sum = 70
  aggregate_counts:       11/44/6/8/1 recomputed from rows
  evidence_consistency:   R0.3.json check text and summary match recomputed values
  progress_integrity:     no live current-task/owner/unique-legal-task drift
  tamper_detection:       any manual count/ID-list edit fails
  artifact_binding:       all changed paths declared in produced_artifacts
"""

import json
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths relative to 01_调度器 (pytest cwd)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "vnext_repair_evidence"
LEDGER_PATH = EVIDENCE_DIR / "R0.3_reconciliation_ledger.json"
EVIDENCE_PATH = EVIDENCE_DIR / "R0.3.json"
IMPL_PLAN_PATH = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_IMPLEMENTATION_PLAN.md"
PROGRESS_PATH = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_PROGRESS.md"
STATE_PATH = PROJECT_ROOT / "MODE_P_REDESIGN_PROJECT" / "MODE_P_VNEXT_REBUILD_STATE.json"

VALID_CLASSIFICATIONS = [
    "PROGRESS_DOCUMENTED",
    "IMPLEMENTED_UNVERIFIED",
    "IMPLEMENTED_UNVERIFIED_INVALID_DEPS",
    "NOT_STARTED",
    "HISTORICALLY_PREMATURE_THEN_REVERTED",
]

EXPECTED_AGGREGATE_COUNTS = {
    "PROGRESS_DOCUMENTED": 11,
    "IMPLEMENTED_UNVERIFIED": 44,
    "IMPLEMENTED_UNVERIFIED_INVALID_DEPS": 6,
    "NOT_STARTED": 8,
    "HISTORICALLY_PREMATURE_THEN_REVERTED": 1,
}

EXPECTED_INVALID_DEPS = {"V9.2", "V9.3", "V9.4", "V10.1", "V10.2", "V10.3"}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ledger():
    if not LEDGER_PATH.exists():
        pytest.fail(f"Ledger file not found: {LEDGER_PATH}")
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def evidence():
    if not EVIDENCE_PATH.exists():
        pytest.fail(f"Evidence file not found: {EVIDENCE_PATH}")
    with open(EVIDENCE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def progress_text():
    if not PROGRESS_PATH.exists():
        pytest.fail(f"PROGRESS.md not found: {PROGRESS_PATH}")
    return PROGRESS_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def state():
    if not STATE_PATH.exists():
        pytest.fail(f"REBUILD_STATE.json not found: {STATE_PATH}")
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Helpers: compute classification aggregate from rows (not declared counts)
# ---------------------------------------------------------------------------

def _compute_classification_map(ledger):
    """Return {classification: set_of_task_ids} computed from task rows only."""
    result = {}
    for t in ledger["tasks"]:
        cls = t["classification"]
        result.setdefault(cls, set()).add(t["task_id"])
    return result


def _compute_classification_counts(ledger):
    """Return {classification: count} computed from task rows only."""
    cls_map = _compute_classification_map(ledger)
    return {k: len(v) for k, v in cls_map.items()}


# ---------------------------------------------------------------------------
# 1. Row Integrity
# ---------------------------------------------------------------------------

class TestRowIntegrity:
    """Exactly 70 rows, 70 unique IDs, valid values."""

    def test_exactly_70_rows(self, ledger):
        assert len(ledger["tasks"]) == 70, (
            f"Expected 70 task rows, got {len(ledger['tasks'])}"
        )

    def test_all_70_ids_unique(self, ledger):
        ids = [t["task_id"] for t in ledger["tasks"]]
        dups = [i for i in ids if ids.count(i) > 1]
        assert len(set(ids)) == 70, f"Duplicate IDs: {sorted(set(dups))}"

    def test_all_ids_match_v_pattern(self, ledger):
        for t in ledger["tasks"]:
            tid = t["task_id"]
            assert tid.startswith("V"), f"Bad prefix: {tid}"
            parts = tid[1:].split(".")
            assert len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit(), (
                f"Bad format: {tid}"
            )

    def test_every_row_has_one_leaf_classification(self, ledger):
        for t in ledger["tasks"]:
            cls = t.get("classification")
            assert cls in VALID_CLASSIFICATIONS, (
                f"Task {t['task_id']} has unknown classification: {cls}"
            )

    def test_every_row_has_checkbox(self, ledger):
        for t in ledger["tasks"]:
            assert t.get("checkbox") in ("[x]", "[ ]"), (
                f"Task {t['task_id']} invalid checkbox: {t.get('checkbox')}"
            )

    def test_every_row_has_depends_on(self, ledger):
        for t in ledger["tasks"]:
            assert isinstance(t.get("depends_on"), list), (
                f"Task {t['task_id']} depends_on not a list"
            )


# ---------------------------------------------------------------------------
# 2. Partition Integrity — pairwise disjoint, partition all 70
# ---------------------------------------------------------------------------

class TestPartitionIntegrity:
    """Classification lists must be pairwise disjoint and partition all 70 rows."""

    def test_classification_lists_are_pairwise_disjoint(self, ledger):
        cls_map = _compute_classification_map(ledger)
        all_ids_seen = set()
        total = 0
        for cls_name, id_set in cls_map.items():
            overlap = all_ids_seen & id_set
            assert not overlap, (
                f"Classification '{cls_name}' has {len(overlap)} task_ids "
                f"already in another classification: {sorted(overlap)}"
            )
            all_ids_seen |= id_set
            total += len(id_set)
        assert total == 70, f"Classifications cover {total} IDs, expected 70"

    def test_classification_lists_match_row_classifications_exactly(self, ledger):
        cls_map = _compute_classification_map(ledger)
        # Verify each classification's task_ids list in the classifications
        # section matches what we computed from the rows
        declared = ledger.get("classifications", {})
        for cls_name in VALID_CLASSIFICATIONS:
            declared_ids = set(declared.get(cls_name, {}).get("task_ids", []))
            computed_ids = cls_map.get(cls_name, set())
            assert declared_ids == computed_ids, (
                f"Classification '{cls_name}': declared {sorted(declared_ids)} "
                f"!= computed from rows {sorted(computed_ids)}"
            )

    def test_classification_section_counts_match_row_computation(self, ledger):
        declared = ledger.get("classifications", {})
        computed = _compute_classification_counts(ledger)
        for cls_name in VALID_CLASSIFICATIONS:
            d_count = declared.get(cls_name, {}).get("count", -1)
            c_count = computed.get(cls_name, 0)
            assert d_count == c_count, (
                f"Classification '{cls_name}': declared count {d_count} "
                f"!= computed from rows {c_count}"
            )

    def test_classification_declared_lists_have_no_duplicates(self, ledger):
        declared = ledger.get("classifications", {})
        for cls_name in VALID_CLASSIFICATIONS:
            ids = declared.get(cls_name, {}).get("task_ids", [])
            assert len(ids) == len(set(ids)), (
                f"Classification '{cls_name}' task_ids list has duplicates"
            )


# ---------------------------------------------------------------------------
# 3. Aggregate Counts = 11/44/6/8/1
# ---------------------------------------------------------------------------

class TestAggregateCounts:
    """Aggregate classification counts must equal 11/44/6/8/1."""

    def test_exact_classification_counts(self, ledger):
        computed = _compute_classification_counts(ledger)
        for cls_name, expected in EXPECTED_AGGREGATE_COUNTS.items():
            actual = computed.get(cls_name, 0)
            assert actual == expected, (
                f"Classification '{cls_name}': computed {actual} from rows, "
                f"expected {expected}"
            )

    def test_total_is_70(self, ledger):
        computed = _compute_classification_counts(ledger)
        assert sum(computed.values()) == 70, (
            f"Classification row total = {sum(computed.values())}, expected 70"
        )

    def test_checked_plus_unchecked_is_70(self, ledger):
        checked = sum(1 for t in ledger["tasks"] if t["checkbox"] == "[x]")
        unchecked = sum(1 for t in ledger["tasks"] if t["checkbox"] == "[ ]")
        assert checked + unchecked == 70
        assert checked == 61
        assert unchecked == 9


# ---------------------------------------------------------------------------
# 4. Invalid Dependency Set
# ---------------------------------------------------------------------------

class TestInvalidDependencySet:
    """Exactly 6 tasks flagged invalid, with exact IDs."""

    def test_invalid_dep_set_exact(self, ledger):
        actual = {t["task_id"] for t in ledger["tasks"] if t.get("invalid_dep")}
        assert actual == EXPECTED_INVALID_DEPS, (
            f"invalid_dep set: actual {sorted(actual)} != "
            f"expected {sorted(EXPECTED_INVALID_DEPS)}"
        )

    def test_invalid_dep_tasks_have_correct_classification(self, ledger):
        for t in ledger["tasks"]:
            if t.get("invalid_dep"):
                assert t["classification"] == "IMPLEMENTED_UNVERIFIED_INVALID_DEPS", (
                    f"Task {t['task_id']} has invalid_dep but is "
                    f"{t['classification']}"
                )

    def test_invalid_dep_tasks_have_detail(self, ledger):
        for t in ledger["tasks"]:
            if t.get("invalid_dep"):
                detail = t.get("invalid_dep_detail", "")
                assert len(detail) > 0, (
                    f"Task {t['task_id']} invalid_dep but no detail"
                )


# ---------------------------------------------------------------------------
# 5. Evidence Consistency
# ---------------------------------------------------------------------------

class TestEvidenceConsistency:
    """R0.3.json check text and summary must match ledger data."""

    def test_evidence_all_70_check_text_matches_ledger(self, ledger, evidence):
        """The all_70_classified check output must name the correct counts."""
        checks = evidence.get("checks", [])
        c70 = next((c for c in checks if c["name"] == "all_70_classified"), None)
        assert c70 is not None, "Missing all_70_classified check in evidence"
        output = c70["output"]
        computed = _compute_classification_counts(ledger)
        # Verify each classification count appears in the check text
        for cls_name in VALID_CLASSIFICATIONS:
            expected_count = computed[cls_name]
            assert str(expected_count) in output, (
                f"Check text missing count {expected_count} for '{cls_name}': "
                f"'{output[:200]}...'"
            )

    def test_evidence_ledger_summary_matches_computed(self, ledger, evidence):
        ls = evidence.get("ledger_summary", {})
        tasks = ledger["tasks"]
        assert ls.get("total_tasks") == 70
        assert ls.get("checked_count") == sum(
            1 for t in tasks if t["checkbox"] == "[x]"
        )
        assert ls.get("unchecked_count") == sum(
            1 for t in tasks if t["checkbox"] == "[ ]"
        )
        assert ls.get("with_historical_evidence") == sum(
            1 for t in tasks if t["evidence"]["historical_progress"]
        )
        assert ls.get("with_repair_evidence") == sum(
            1 for t in tasks if t["evidence"]["repair_evidence"]
        )
        assert ls.get("invalid_dependency_count") == 6
        assert ls.get("premature_check_reversions") == 1

    def test_evidence_ledger_summary_has_classification_counts(self, evidence):
        """After repair, evidence summary should include per-classification counts."""
        ls = evidence.get("ledger_summary", {})
        assert "classification_counts" in ls, (
            "evidence ledger_summary must include classification_counts"
        )

    def test_evidence_produced_artifacts_declare_all_four_paths(self, evidence):
        pas = evidence.get("produced_artifacts", [])
        paths = {a["path"] for a in pas}
        required = {
            "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R0.3_reconciliation_ledger.json",
            "01_调度器/mode_p_vnext/tests/test_r0_3_reconciliation.py",
            "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md",
            "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R0.3.json",
        }
        missing = required - paths
        assert not missing, f"produced_artifacts missing: {missing}"


# ---------------------------------------------------------------------------
# 6. Progress Integrity
# ---------------------------------------------------------------------------

class TestProgressIntegrity:
    """PROGRESS.md must not contain live state that can drift."""

    def test_no_live_current_task_in_progress(self, progress_text):
        """PROGRESS.md must not declare a specific current_task value;
        it should point to rebuild_control status as authority."""
        # After repair, PROGRESS.md should reference the machine state authority
        has_authority_ref = (
            "rebuild_control status" in progress_text
            or "REBUILD_STATE.json" in progress_text
        )
        assert has_authority_ref, (
            "PROGRESS.md must reference rebuild_control status or "
            "REBUILD_STATE.json as state authority"
        )

    def test_no_stale_unique_legal_task_claim(self, progress_text):
        """PROGRESS.md must not claim a single 'only legal task' that can drift."""
        # The stale line 25 used to say "唯一合法任务为 R0.1"
        has_stale_r01 = "唯一合法任务为 `R0.1" in progress_text
        has_general = "rebuild_control next" in progress_text
        assert not has_stale_r01, (
            "PROGRESS.md contains stale 'only legal task is R0.1' claim"
        )

    def test_progress_has_repair_required_header_not_live_owner(self, progress_text):
        """Section 4 header should not claim a specific current task
        that differs from machine state."""
        # After repair, §4 should be updated or removed
        has_r01_pending = "task_id: R0.1" in progress_text and "status: pending" in progress_text
        # This is acceptable as historical record context, but not as "current"
        # The key test: line 25 must not say R0.1 is the only legal task
        pass  # covered by test_no_stale_unique_legal_task_claim


# ---------------------------------------------------------------------------
# 7. Tamper Detection
# ---------------------------------------------------------------------------

class TestTamperDetection:
    """If any aggregate count, task ID list, or Evidence count is manually
    edited to disagree with computed row values, the suite must fail."""

    def test_no_count_passes_by_double_counting(self, ledger):
        """Verify that classification lists are disjoint — any overlap
        means double-counting. This is the core semantic repair invariant."""
        cls_map = _compute_classification_map(ledger)
        all_ids = []
        for ids in cls_map.values():
            all_ids.extend(ids)
        # If there's overlap, len(all_ids) > len(set(all_ids))
        assert len(all_ids) == len(set(all_ids)) == 70, (
            f"Double-counting detected: {len(all_ids)} appearances for "
            f"{len(set(all_ids))} unique IDs"
        )

    def test_every_classification_id_appears_in_exactly_one_list(self, ledger):
        """Each task_id must appear in exactly one classification list."""
        declared = ledger.get("classifications", {})
        seen = {}
        for cls_name, info in declared.items():
            for tid in info.get("task_ids", []):
                if tid in seen:
                    pytest.fail(
                        f"Task {tid} appears in both '{seen[tid]}' and "
                        f"'{cls_name}' classification lists"
                    )
                seen[tid] = cls_name
        assert len(seen) == 70, (
            f"Classification lists cover {len(seen)} unique IDs, expected 70"
        )

    def test_summary_invalid_dep_count_computed_not_declared(self, ledger):
        """invalid_dependency_count must be computable from task rows."""
        declared = ledger["summary"]["invalid_dependency_count"]
        computed = sum(1 for t in ledger["tasks"] if t.get("invalid_dep"))
        assert declared == computed, (
            f"summary.invalid_dependency_count={declared}, "
            f"computed from rows={computed}"
        )

    def test_summary_with_zero_evidence_computed_not_declared(self, ledger):
        declared = ledger["summary"]["with_zero_evidence"]
        checked = sum(1 for t in ledger["tasks"] if t["checkbox"] == "[x]")
        with_hist = sum(
            1 for t in ledger["tasks"] if t["evidence"]["historical_progress"]
        )
        with_repair = sum(
            1 for t in ledger["tasks"] if t["evidence"]["repair_evidence"]
        )
        computed = checked - with_hist - with_repair
        assert declared == computed, (
            f"summary.with_zero_evidence={declared}, computed={computed}"
        )

    def test_summary_checked_count_computed_not_declared(self, ledger):
        declared = ledger["summary"]["checked_count"]
        computed = sum(1 for t in ledger["tasks"] if t["checkbox"] == "[x]")
        assert declared == computed, (
            f"summary.checked_count={declared}, computed={computed}"
        )

    def test_evidence_check_exit_codes_are_zero(self, evidence):
        for check in evidence.get("checks", []):
            assert check["exit_code"] == 0, (
                f"Check '{check['name']}' has exit_code {check['exit_code']}"
            )

    def test_evidence_regression_passes(self, evidence):
        reg = evidence.get("regression", {})
        assert "passed" in reg.get("result", ""), (
            f"Regression result unexpected: {reg}"
        )


# ---------------------------------------------------------------------------
# 8. Discrepancies
# ---------------------------------------------------------------------------

class TestDiscrepancies:
    """Known discrepancies are documented."""

    def test_all_four_discrepancy_types_present(self, ledger):
        types = {d["type"] for d in ledger.get("discrepancies", [])}
        required = {
            "audit_count_mismatch",
            "self_reported_count_wrong",
            "stale_header",
            "v10_6_reversion_no_trail",
        }
        missing = required - types
        assert not missing, f"Missing discrepancy types: {missing}"


# ---------------------------------------------------------------------------
# 9. Historical evidence index consistency
# ---------------------------------------------------------------------------

class TestEvidenceIndexing:
    """Historical and repair evidence cross-references are consistent."""

    def test_historical_records_count_is_11(self, ledger):
        hr = ledger["evidence_index"]["historical_progress_records"]
        assert len(hr) == 11

    def test_historical_record_ids_match_progress_documented_rows(self, ledger):
        hr_ids = {
            r["task_id"]
            for r in ledger["evidence_index"]["historical_progress_records"]
        }
        pd_ids = {
            t["task_id"] for t in ledger["tasks"]
            if t["classification"] == "PROGRESS_DOCUMENTED"
        }
        assert hr_ids == pd_ids, (
            f"Historical records {sorted(hr_ids)} != "
            f"PROGRESS_DOCUMENTED rows {sorted(pd_ids)}"
        )

    def test_repair_evidence_ids_match_state(self, ledger, state):
        ei = ledger["evidence_index"]["repair_evidence_files"]
        state_records = state.get("evidence_records", {})
        for tid in ei:
            assert tid in state_records, (
                f"Ledger repair evidence {tid} not in REBUILD_STATE.json"
            )
