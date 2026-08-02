"""R3.2 tests for the controlled v4 collection-baseline reconciliation."""

from __future__ import annotations

import copy

import pytest

from mode_p_vnext.tests._baseline_cohort_support import (
    LEDGER_PATH,
    PROJECT_ROOT,
    SOURCE_HASH_MODE,
    assert_registered_v4_collection,
    cohort_source_sha256,
    collect_ids,
    load_ledger,
    validate_registered_cohorts,
)


def test_reconciliation_ledger_is_present_and_is_not_a_baseline_rewrite():
    ledger = load_ledger()
    assert LEDGER_PATH.is_file()
    assert ledger["frozen_manifest"]["declared_test_count"] == 686
    assert ledger["acceptance_contract"]["current_total_may_be_called_historical_v0_1_baseline"] is False
    assert ledger["acceptance_contract"]["current_generic_candidate_may_be_called_historical_v0_1_exact_ids"] is False
    assert ledger["acceptance_contract"]["legacy_suite_may_be_used_as_vnext_director_design_authority"] is False


def test_registered_current_collection_has_no_unexplained_delta():
    assert_registered_v4_collection()


def test_registered_legacy_source_has_expected_hash():
    ledger = load_ledger()
    legacy = ledger["cohorts"]["legacy_ep35_s1_post_freeze"]
    source = PROJECT_ROOT / legacy["source_path"]
    assert legacy["source_hash_mode"] == SOURCE_HASH_MODE
    assert cohort_source_sha256(source) == legacy["source_sha256"]
    assert legacy["design_source_for_vnext"] is False
    assert "master_continuity_board" in legacy["legacy_contracts_not_permitted_in_vnext"]


def test_overlap_or_unregistered_member_fails_closed():
    ledger = load_ledger()
    all_ids = collect_ids()
    legacy_ids = collect_ids("test_ep35_s1_pipeline.py")
    generic_ids = collect_ids("--ignore=test_ep35_s1_pipeline.py")

    tampered = copy.deepcopy(ledger)
    tampered["set_relation"]["legacy_intersects_reconstructed_generic"] = 1
    with pytest.raises(AssertionError):
        validate_registered_cohorts(tampered, all_ids, legacy_ids, generic_ids)

    tampered = copy.deepcopy(ledger)
    tampered["current_collection"]["count"] = len(all_ids) - 1
    with pytest.raises(AssertionError):
        validate_registered_cohorts(tampered, all_ids, legacy_ids, generic_ids)
