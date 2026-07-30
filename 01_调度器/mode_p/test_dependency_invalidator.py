"""Tests for dependency-edge-based minimum invalidation."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from dependency_invalidator import (
    ChangeKind,
    DependencyGraph,
    DependencySnapshot,
    InvalidationError,
    ShotConsumer,
    compare_snapshots,
    compute_invalidation,
    record_invalidation_telemetry,
    telemetry_scope,
)
from pipeline_telemetry import summarize_events


class InvalidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = DependencyGraph(
            scene_order=["S-A", "S-B", "S-C", "S-D"],
            batch_assignments={"S-A": 1, "S-B": 1, "S-C": 2, "S-D": 2},
            boundary_dependents={"S-B": {"S-C"}},
            capsule_consumers={"capsules/dialogue.md": {"S-A", "S-C"}},
            asset_consumers={
                "rico-ref": [ShotConsumer("S-B", "S-B-2")],
            },
            capability_consumers={
                "first_last_frame": {"S-B"}, "omni_reference": {"S-C"},
            },
            shot_order={
                "S-A": ["S-A-1"],
                "S-B": ["S-B-1", "S-B-2", "S-B-3"],
                "S-C": ["S-C-1", "S-C-2"],
                "S-D": ["S-D-1"],
            },
        )

    def test_script_scene_uses_recorded_handoff_dependents_not_numeric_guess(self) -> None:
        report = compute_invalidation(
            [{"kind": ChangeKind.SCRIPT_SCENE, "scene_id": "S-B"}], self.graph
        )
        self.assertEqual(report.affected_scenes, {"S-B", "S-C"})
        self.assertNotIn("S-A", report.affected_scenes)
        self.assertEqual(report.affected_batches, {1, 2})
        self.assertTrue(report.must_revalidate_ledger)

    def test_capsule_change_only_invalidates_actual_consumers(self) -> None:
        report = compute_invalidation(
            [{"kind": "knowledge_capsule", "capsule_path": "capsules/dialogue.md"}],
            self.graph,
        )
        self.assertEqual(report.affected_scenes, {"S-A", "S-C"})
        self.assertNotIn("scene_context", report.scene_stages["S-A"])

    def test_asset_change_targets_recorded_shot_and_its_boundaries(self) -> None:
        report = compute_invalidation(
            [{"kind": "asset", "asset_id": "rico-ref"}], self.graph
        )
        self.assertEqual(report.affected_shots, {"S-B": {"S-B-2"}})
        self.assertEqual(report.affected_boundaries, {
            ("S-B", "S-B-1", "S-B-2"),
            ("S-B", "S-B-2", "S-B-3"),
        })
        self.assertEqual(report.affected_scenes, {"S-B"})

    def test_master_shot_preserves_master_but_invalidates_downstream(self) -> None:
        report = compute_invalidation(
            [{"kind": "master_shot", "scene_id": "S-C", "shot_id": "S-C-1"}],
            self.graph,
        )
        self.assertNotIn("master", report.scene_stages["S-C"])
        self.assertIn("views", report.scene_stages["S-C"])
        self.assertEqual(report.affected_boundaries, {("S-C", "S-C-1", "S-C-2")})

    def test_view_change_invalidates_dp_and_only_corresponding_view_check(self) -> None:
        report = compute_invalidation(
            [{"kind": "view_text", "scene_id": "S-D", "view": "storyboard"}],
            self.graph,
        )
        self.assertEqual(report.scene_stages["S-D"], {"storyboard_check", "dp_review"})

    def test_dp_and_checker_versions_do_not_destroy_design_cache(self) -> None:
        dp = compute_invalidation([{"kind": "dp_version"}], self.graph)
        self.assertTrue(all(stages == {"dp_review"} for stages in dp.scene_stages.values()))
        checker = compute_invalidation(
            [{"kind": "checker_version", "checker": "boundary_check.py"}], self.graph
        )
        self.assertEqual(checker.checker_names, {"boundary_check.py"})
        self.assertTrue(all(stages == {"check:boundary_check.py"} for stages in checker.scene_stages.values()))

    def test_capability_change_only_invalidates_scenes_using_that_mode(self) -> None:
        report = compute_invalidation(
            [{"kind": "sd2_capability", "mode": "omni_reference"}], self.graph
        )
        self.assertEqual(report.affected_scenes, {"S-C"})

    def test_unknown_consumers_fail_instead_of_falling_back_to_all_scenes(self) -> None:
        with self.assertRaises(InvalidationError):
            compute_invalidation(
                [{"kind": "knowledge_capsule", "capsule_path": "unknown.md"}], self.graph
            )
        with self.assertRaises(InvalidationError):
            compute_invalidation([{"kind": "asset", "asset_id": "unknown"}], self.graph)

    def test_full_script_change_invalidates_all_design_and_episode_artifacts(self) -> None:
        report = compute_invalidation([{"kind": "script_full"}], self.graph)
        self.assertEqual(report.affected_scenes, set(self.graph.scene_order))
        self.assertTrue(report.must_revalidate_visual_bible)
        self.assertTrue(report.must_revalidate_ledger)

    def test_empty_change_set_is_empty(self) -> None:
        self.assertTrue(compute_invalidation([], self.graph).is_empty)

    def test_exact_invalidation_scope_is_recorded_in_runtime_telemetry(self) -> None:
        report = compute_invalidation(
            [{"kind": "master_shot", "scene_id": "S-B", "shot_id": "S-B-2"}],
            self.graph,
        )
        with tempfile.TemporaryDirectory(prefix="invalidation_telemetry_") as tmp:
            session = Path(tmp)
            record_invalidation_telemetry(report, session)
            summary = summarize_events(session)
            self.assertEqual(summary["invalidation_scope"], telemetry_scope(report))
            self.assertIn("shot/S-B/S-B-2", summary["invalidation_scope"])
            self.assertIn("batch/1", summary["invalidation_scope"])


class SnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = DependencyGraph(
            scene_order=["S1", "S2"],
            batch_assignments={"S1": 1, "S2": 1},
            capsule_consumers={"dialogue": {"S1"}},
            asset_consumers={"ref": [ShotConsumer("S2", "S2-1")]},
            capability_consumers={"omni_reference": {"S2"}},
            shot_order={"S1": ["S1-1"], "S2": ["S2-1"]},
        )
        self.base = DependencySnapshot(
            schema_version="1.0", script_sha256="a", scene_sha256={"S1": "a", "S2": "b"},
            user_visual_direction_sha256="a", project_continuity_sha256="a",
            capsule_sha256={"dialogue": "a"}, asset_fingerprints={"ref": "a"},
            capability_mode_sha256={"omni_reference": "a"},
            director_fingerprint="a", dp_fingerprint="a", retriever_fingerprint="a",
            template_fingerprints={"views": "a"}, checker_fingerprints={"boundary.py": "a"},
        )

    def test_snapshot_comparison_preserves_component_identity(self) -> None:
        current = copy.deepcopy(self.base)
        current.capsule_sha256["dialogue"] = "b"
        current.dp_fingerprint = "b"
        report = compare_snapshots(self.base, current, self.graph)
        self.assertIn("master", report.scene_stages["S1"])
        self.assertEqual(report.scene_stages["S2"], {"dp_review"})

    def test_unconsumed_component_change_does_not_invalidate_scenes(self) -> None:
        current = copy.deepcopy(self.base)
        current.capsule_sha256["unused"] = "new"
        report = compare_snapshots(self.base, current, self.graph)
        self.assertTrue(report.is_empty)

    def test_changed_scene_hash_is_granular_even_when_full_script_hash_changes(self) -> None:
        current = copy.deepcopy(self.base)
        current.script_sha256 = "new"
        current.scene_sha256["S2"] = "new"
        report = compare_snapshots(self.base, current, self.graph)
        self.assertEqual(report.affected_scenes, {"S2"})


if __name__ == "__main__":
    unittest.main()
