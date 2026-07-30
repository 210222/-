"""Execution strategy derived from an authoritative batch manifest."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from batch_scheduler import BatchManifest, ScheduleError, schedule_batches


@dataclass
class StrategyReport:
    mode: str
    executable: bool
    total_scenes: int
    selected_scenes: list[int]
    total_batches: int
    baseline_director_calls: int | None
    baseline_dp_calls: int | None
    execution_batches: list[dict] = field(default_factory=list)
    shared_documents: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    manifest: BatchManifest | None = None

    @property
    def is_pilot(self) -> bool:
        return self.mode == "pilot"

    @property
    def is_long_form(self) -> bool:
        return self.mode == "multi_batch"


def plan_strategy(
    script_path: Path,
    ingest_json_path: Path,
    scene_indices: list[int] | None = None,
    max_scenes_per_batch: int | None = None,
    *,
    session_dir: Path | None = None,
    budget_profile_path: Path | None = None,
    capsules_by_scene: Mapping[int, list[Path]] | None = None,
    expected_shots_by_scene: Mapping[int, int] | None = None,
    user_visual_constraints: str = "",
) -> StrategyReport:
    """Create a call plan only when measured preparation inputs are complete."""
    # script_path is an explicit caller binding; the digest remains canonical.
    if not script_path.is_file():
        raise ScheduleError(f"script not found: {script_path}")
    manifest = schedule_batches(
        ingest_json_path,
        max_scenes_per_batch,
        scene_indices,
        session_dir=session_dir,
        budget_profile_path=budget_profile_path,
        capsules_by_scene=capsules_by_scene,
        expected_shots_by_scene=expected_shots_by_scene,
        user_visual_constraints=user_visual_constraints,
        include_lead_director_output=True,
    )
    selected_count = len(manifest.selected_scenes)
    if not manifest.authoritative:
        mode = "provisional"
    elif manifest.total_batches > 1:
        mode = "multi_batch"
    elif selected_count == 1:
        mode = "single_scene"
    elif 3 <= selected_count <= 5 and manifest.selected_scenes == list(
        range(1, manifest.total_scenes + 1)
    ):
        mode = "pilot"
    elif manifest.selected_scenes != list(range(1, manifest.total_scenes + 1)):
        mode = "local_scope"
    else:
        mode = "single_batch"

    execution_batches = [
        {
            "batch_index": batch.batch_index,
            "scene_indices": batch.scene_indices,
            "director_context_policy": (
                "one_persistent_episode_director" if manifest.total_batches == 1
                else "new_director_batch_with_shared_bible_and_committed_ledger"
            ),
            "dp_context_policy": "fresh_subagent_no_prior_dp_context",
            "fresh_dp_required": batch.fresh_dp_required,
            "prior_committed_ledger_required": batch.prior_committed_ledger_required,
            "estimated_input_tokens": batch.estimated_input_tokens,
            "estimated_output_tokens": batch.estimated_output_tokens,
        }
        for batch in manifest.batches
    ]
    executable = manifest.authoritative
    return StrategyReport(
        mode=mode,
        executable=executable,
        total_scenes=manifest.total_scenes,
        selected_scenes=manifest.selected_scenes,
        total_batches=manifest.total_batches,
        baseline_director_calls=manifest.total_batches if executable else None,
        baseline_dp_calls=manifest.total_batches if executable else None,
        execution_batches=execution_batches,
        shared_documents=manifest.shared_documents,
        blockers=[] if executable else list(manifest.provisional_reasons),
        manifest=manifest,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan MODE:P Director/DP calls.")
    parser.add_argument("script", type=Path)
    parser.add_argument("ingest_json", type=Path)
    parser.add_argument("--session-dir", type=Path)
    parser.add_argument("--budget-profile", type=Path)
    parser.add_argument("--scenes")
    parser.add_argument("--max-scenes", type=int)
    args = parser.parse_args()
    try:
        scenes = [int(item) for item in args.scenes.split(",")] if args.scenes else None
        report = plan_strategy(
            args.script, args.ingest_json, scenes, args.max_scenes,
            session_dir=args.session_dir,
            budget_profile_path=args.budget_profile,
        )
        print(json.dumps({
            "mode": report.mode,
            "executable": report.executable,
            "total_scenes": report.total_scenes,
            "selected_scenes": report.selected_scenes,
            "total_batches": report.total_batches,
            "baseline_director_calls": report.baseline_director_calls,
            "baseline_dp_calls": report.baseline_dp_calls,
            "execution_batches": report.execution_batches,
            "shared_documents": report.shared_documents,
            "blockers": report.blockers,
        }, ensure_ascii=False, indent=2))
        return 0 if report.executable else 2
    except (ScheduleError, OSError, ValueError) as exc:
        print(f"Strategy error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
