"""Granular dependency invalidation for MODE:P cached artifacts.

The invalidator consumes recorded dependency edges.  It does not infer scene
meaning, choose creative modes, or collapse unrelated bootstrap changes into a
full-episode redo.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from pipeline_telemetry import record_event


class InvalidationError(ValueError):
    """Raised when the dependency graph or a change event is incomplete."""


class ChangeKind(str, Enum):
    SCRIPT_SCENE = "script_scene"
    SCRIPT_FULL = "script_full"
    PROJECT_CONTINUITY = "project_continuity"
    VISUAL_DIRECTION = "visual_direction"
    KNOWLEDGE_CAPSULE = "knowledge_capsule"
    ASSET = "asset"
    MASTER_SHOT = "master_shot"
    VIEW_TEXT = "view_text"
    DIRECTOR_VERSION = "director_version"
    DP_VERSION = "dp_version"
    RETRIEVER_VERSION = "retriever_version"
    TEMPLATE_VERSION = "template_version"
    CHECKER_VERSION = "checker_version"
    SD2_CAPABILITY = "sd2_capability"


@dataclass(frozen=True)
class ShotConsumer:
    scene_id: str
    shot_id: str


@dataclass
class DependencyGraph:
    scene_order: list[str]
    batch_assignments: dict[str, int]
    boundary_dependents: dict[str, set[str]] = field(default_factory=dict)
    capsule_consumers: dict[str, set[str]] = field(default_factory=dict)
    asset_consumers: dict[str, list[ShotConsumer]] = field(default_factory=dict)
    capability_consumers: dict[str, set[str]] = field(default_factory=dict)
    shot_order: dict[str, list[str]] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.scene_order or len(self.scene_order) != len(set(self.scene_order)):
            raise InvalidationError("scene_order must contain unique scene IDs")
        scenes = set(self.scene_order)
        if set(self.batch_assignments) != scenes:
            raise InvalidationError("batch_assignments must cover every scene exactly")
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 1
               for value in self.batch_assignments.values()):
            raise InvalidationError("batch indices must be positive integers")
        for source, dependents in self.boundary_dependents.items():
            if source not in scenes or not dependents <= scenes:
                raise InvalidationError("boundary dependency references an unknown scene")
        for consumers in self.capsule_consumers.values():
            if not consumers <= scenes:
                raise InvalidationError("capsule dependency references an unknown scene")
        for consumers in self.capability_consumers.values():
            if not consumers <= scenes:
                raise InvalidationError("capability dependency references an unknown scene")
        for scene_id, shots in self.shot_order.items():
            if scene_id not in scenes or len(shots) != len(set(shots)):
                raise InvalidationError("shot_order is malformed")
        for consumers in self.asset_consumers.values():
            for consumer in consumers:
                if consumer.scene_id not in scenes:
                    raise InvalidationError("asset dependency references an unknown scene")
                if consumer.shot_id not in self.shot_order.get(consumer.scene_id, []):
                    raise InvalidationError("asset dependency references an unknown Shot ID")


@dataclass
class InvalidationReport:
    global_artifacts: set[str] = field(default_factory=set)
    scene_stages: dict[str, set[str]] = field(default_factory=dict)
    affected_shots: dict[str, set[str]] = field(default_factory=dict)
    affected_boundaries: set[tuple[str, str, str]] = field(default_factory=set)
    checker_names: set[str] = field(default_factory=set)
    affected_batches: set[int] = field(default_factory=set)
    reasons: list[str] = field(default_factory=list)

    @property
    def affected_scenes(self) -> set[str]:
        return set(self.scene_stages) | set(self.affected_shots)

    @property
    def is_empty(self) -> bool:
        return not (
            self.global_artifacts or self.scene_stages or self.affected_shots
            or self.affected_boundaries or self.checker_names
        )

    @property
    def must_revalidate_visual_bible(self) -> bool:
        return "visual_bible" in self.global_artifacts

    @property
    def must_revalidate_ledger(self) -> bool:
        return "continuity_ledger" in self.global_artifacts


@dataclass
class DependencySnapshot:
    schema_version: str
    script_sha256: str
    scene_sha256: dict[str, str]
    user_visual_direction_sha256: str
    project_continuity_sha256: str
    capsule_sha256: dict[str, str]
    asset_fingerprints: dict[str, str]
    capability_mode_sha256: dict[str, str]
    director_fingerprint: str
    dp_fingerprint: str
    retriever_fingerprint: str
    template_fingerprints: dict[str, str]
    checker_fingerprints: dict[str, str]


_FULL_DESIGN_STAGES = {
    "scene_context", "knowledge_context", "master", "views", "dp_review",
    "structural_checks", "boundary_check", "reference_check",
}
_POST_MASTER_STAGES = {"views", "dp_review", "structural_checks", "boundary_check", "reference_check"}


def _kind(raw: Any) -> ChangeKind:
    if isinstance(raw, ChangeKind):
        return raw
    try:
        return ChangeKind(raw)
    except (TypeError, ValueError) as exc:
        raise InvalidationError(f"unknown change kind: {raw!r}") from exc


def _require_scene(graph: DependencyGraph, raw: Any) -> str:
    if not isinstance(raw, str) or raw not in graph.scene_order:
        raise InvalidationError(f"unknown or missing scene_id: {raw!r}")
    return raw


def _scenes_from_event(
    graph: DependencyGraph, change: dict[str, Any], default: Iterable[str]
) -> set[str]:
    raw = change.get("affected_scenes")
    scenes = set(default) if raw is None else set(raw)
    if not scenes <= set(graph.scene_order):
        raise InvalidationError("affected_scenes contains an unknown scene")
    return scenes


def _invalidate_scene(report: InvalidationReport, scene_id: str, stages: Iterable[str]) -> None:
    report.scene_stages.setdefault(scene_id, set()).update(stages)


def _mark_shot(
    report: InvalidationReport,
    graph: DependencyGraph,
    scene_id: str,
    shot_id: str,
) -> None:
    shots = graph.shot_order.get(scene_id, [])
    if shot_id not in shots:
        raise InvalidationError(f"unknown Shot ID {shot_id!r} in {scene_id}")
    report.affected_shots.setdefault(scene_id, set()).add(shot_id)
    index = shots.index(shot_id)
    if index > 0:
        report.affected_boundaries.add((scene_id, shots[index - 1], shot_id))
    if index + 1 < len(shots):
        report.affected_boundaries.add((scene_id, shot_id, shots[index + 1]))


def _record_batches(report: InvalidationReport, graph: DependencyGraph) -> None:
    report.affected_batches = {
        graph.batch_assignments[scene_id] for scene_id in report.affected_scenes
    }


def compute_invalidation(
    changes: list[dict[str, Any]], graph: DependencyGraph
) -> InvalidationReport:
    """Compute the minimum recorded dependency scope for explicit changes."""
    graph.validate()
    if not isinstance(changes, list):
        raise InvalidationError("changes must be an array")
    report = InvalidationReport()
    all_scenes = set(graph.scene_order)

    for change in changes:
        if not isinstance(change, dict):
            raise InvalidationError("every change must be an object")
        kind = _kind(change.get("kind"))

        if kind == ChangeKind.SCRIPT_SCENE:
            scene = _require_scene(graph, change.get("scene_id"))
            report.global_artifacts.update({"script_facts", "continuity_ledger"})
            _invalidate_scene(report, scene, _FULL_DESIGN_STAGES)
            for dependent in graph.boundary_dependents.get(scene, set()):
                _invalidate_scene(
                    report, dependent,
                    {"scene_context", "master", "views", "dp_review", "boundary_check"},
                )
            report.reasons.append(f"script scene changed: {scene}")

        elif kind == ChangeKind.SCRIPT_FULL:
            report.global_artifacts.update({"script_facts", "visual_bible", "continuity_ledger"})
            for scene in all_scenes:
                _invalidate_scene(report, scene, _FULL_DESIGN_STAGES)
            report.reasons.append("full script changed")

        elif kind == ChangeKind.PROJECT_CONTINUITY:
            report.global_artifacts.update({"visual_bible", "continuity_ledger"})
            for scene in _scenes_from_event(graph, change, all_scenes):
                _invalidate_scene(report, scene, _FULL_DESIGN_STAGES)
            report.reasons.append("project continuity input changed")

        elif kind == ChangeKind.VISUAL_DIRECTION:
            report.global_artifacts.add("visual_bible")
            for scene in _scenes_from_event(graph, change, all_scenes):
                _invalidate_scene(
                    report, scene,
                    {"scene_context", "master", "views", "dp_review", "structural_checks"},
                )
            report.reasons.append("user visual direction changed")

        elif kind == ChangeKind.KNOWLEDGE_CAPSULE:
            capsule = change.get("capsule_path")
            if not isinstance(capsule, str) or capsule not in graph.capsule_consumers:
                raise InvalidationError("capsule change lacks recorded consumers")
            for scene in graph.capsule_consumers[capsule]:
                _invalidate_scene(
                    report, scene,
                    {"knowledge_context", "master", "views", "dp_review", "structural_checks"},
                )
            report.reasons.append(f"selected capsule changed: {capsule}")

        elif kind == ChangeKind.ASSET:
            asset_id = change.get("asset_id")
            if not isinstance(asset_id, str) or asset_id not in graph.asset_consumers:
                raise InvalidationError("asset change lacks recorded Shot consumers")
            for consumer in graph.asset_consumers[asset_id]:
                _mark_shot(report, graph, consumer.scene_id, consumer.shot_id)
                _invalidate_scene(
                    report, consumer.scene_id,
                    {"master", "views", "dp_review", "reference_check", "boundary_check"},
                )
            report.reasons.append(f"referenced asset changed: {asset_id}")

        elif kind == ChangeKind.MASTER_SHOT:
            scene = _require_scene(graph, change.get("scene_id"))
            shot = change.get("shot_id")
            if not isinstance(shot, str):
                raise InvalidationError("master_shot change requires shot_id")
            _mark_shot(report, graph, scene, shot)
            _invalidate_scene(report, scene, _POST_MASTER_STAGES)
            report.reasons.append(f"Master Shot changed: {shot}")

        elif kind == ChangeKind.VIEW_TEXT:
            scene = _require_scene(graph, change.get("scene_id"))
            view = change.get("view")
            if view not in {"storyboard", "video_prompt"}:
                raise InvalidationError("view_text change requires storyboard or video_prompt")
            _invalidate_scene(report, scene, {f"{view}_check", "dp_review"})
            report.reasons.append(f"derived view changed: {scene}/{view}")

        elif kind == ChangeKind.DIRECTOR_VERSION:
            for scene in all_scenes:
                _invalidate_scene(report, scene, {"master", *list(_POST_MASTER_STAGES)})
            report.reasons.append("Director instruction changed")

        elif kind == ChangeKind.DP_VERSION:
            for scene in all_scenes:
                _invalidate_scene(report, scene, {"dp_review"})
            report.reasons.append("DP instruction/model changed")

        elif kind == ChangeKind.RETRIEVER_VERSION:
            for scene in all_scenes:
                _invalidate_scene(
                    report, scene,
                    {"knowledge_context", "master", "views", "dp_review", "structural_checks"},
                )
            report.reasons.append("context retriever changed")

        elif kind == ChangeKind.TEMPLATE_VERSION:
            template = change.get("template")
            if template == "master":
                stages = {"master", *list(_POST_MASTER_STAGES)}
            elif template in {"storyboard", "video_prompt", "views"}:
                stages = {"views", "dp_review", "structural_checks"}
            else:
                raise InvalidationError("template_version requires a known template")
            for scene in all_scenes:
                _invalidate_scene(report, scene, stages)
            report.reasons.append(f"template changed: {template}")

        elif kind == ChangeKind.CHECKER_VERSION:
            checker = change.get("checker")
            if not isinstance(checker, str) or not checker:
                raise InvalidationError("checker_version requires checker")
            report.checker_names.add(checker)
            for scene in all_scenes:
                _invalidate_scene(report, scene, {f"check:{checker}"})
            report.reasons.append(f"checker implementation changed: {checker}")

        elif kind == ChangeKind.SD2_CAPABILITY:
            mode = change.get("mode")
            if not isinstance(mode, str) or mode not in graph.capability_consumers:
                raise InvalidationError("capability change lacks recorded mode consumers")
            for scene in graph.capability_consumers[mode]:
                _invalidate_scene(
                    report, scene,
                    {"master", "views", "dp_review", "structural_checks", "reference_check"},
                )
            report.reasons.append(f"SD2 capability changed: {mode}")

    _record_batches(report, graph)
    return report


def _changed_keys(previous: dict[str, str], current: dict[str, str]) -> set[str]:
    return {
        key for key in set(previous) | set(current)
        if previous.get(key) != current.get(key)
    }


def compare_snapshots(
    previous: DependencySnapshot,
    current: DependencySnapshot,
    graph: DependencyGraph,
) -> InvalidationReport:
    """Translate component-level fingerprint differences into change events."""
    if previous.schema_version != "1.0" or current.schema_version != "1.0":
        raise InvalidationError("unsupported dependency snapshot schema_version")
    changes: list[dict[str, Any]] = []
    changed_scenes = _changed_keys(previous.scene_sha256, current.scene_sha256)
    if changed_scenes:
        for scene in sorted(changed_scenes):
            changes.append({"kind": ChangeKind.SCRIPT_SCENE, "scene_id": scene})
    elif previous.script_sha256 != current.script_sha256:
        changes.append({"kind": ChangeKind.SCRIPT_FULL})
    if previous.user_visual_direction_sha256 != current.user_visual_direction_sha256:
        changes.append({"kind": ChangeKind.VISUAL_DIRECTION})
    if previous.project_continuity_sha256 != current.project_continuity_sha256:
        changes.append({"kind": ChangeKind.PROJECT_CONTINUITY})
    for capsule in sorted(_changed_keys(previous.capsule_sha256, current.capsule_sha256)):
        if capsule in graph.capsule_consumers:
            changes.append({"kind": ChangeKind.KNOWLEDGE_CAPSULE, "capsule_path": capsule})
    for asset in sorted(_changed_keys(previous.asset_fingerprints, current.asset_fingerprints)):
        if asset in graph.asset_consumers:
            changes.append({"kind": ChangeKind.ASSET, "asset_id": asset})
    for mode in sorted(_changed_keys(previous.capability_mode_sha256, current.capability_mode_sha256)):
        if mode in graph.capability_consumers:
            changes.append({"kind": ChangeKind.SD2_CAPABILITY, "mode": mode})
    if previous.director_fingerprint != current.director_fingerprint:
        changes.append({"kind": ChangeKind.DIRECTOR_VERSION})
    if previous.dp_fingerprint != current.dp_fingerprint:
        changes.append({"kind": ChangeKind.DP_VERSION})
    if previous.retriever_fingerprint != current.retriever_fingerprint:
        changes.append({"kind": ChangeKind.RETRIEVER_VERSION})
    for template in sorted(_changed_keys(previous.template_fingerprints, current.template_fingerprints)):
        changes.append({"kind": ChangeKind.TEMPLATE_VERSION, "template": template})
    for checker in sorted(_changed_keys(previous.checker_fingerprints, current.checker_fingerprints)):
        changes.append({"kind": ChangeKind.CHECKER_VERSION, "checker": checker})
    return compute_invalidation(changes, graph)


def _graph_from_json(data: dict[str, Any]) -> DependencyGraph:
    return DependencyGraph(
        scene_order=data["scene_order"],
        batch_assignments=data["batch_assignments"],
        boundary_dependents={key: set(value) for key, value in data.get("boundary_dependents", {}).items()},
        capsule_consumers={key: set(value) for key, value in data.get("capsule_consumers", {}).items()},
        asset_consumers={
            key: [ShotConsumer(**item) for item in value]
            for key, value in data.get("asset_consumers", {}).items()
        },
        capability_consumers={key: set(value) for key, value in data.get("capability_consumers", {}).items()},
        shot_order=data.get("shot_order", {}),
    )


def _report_json(report: InvalidationReport) -> dict[str, Any]:
    return {
        "global_artifacts": sorted(report.global_artifacts),
        "scene_stages": {key: sorted(value) for key, value in sorted(report.scene_stages.items())},
        "affected_shots": {key: sorted(value) for key, value in sorted(report.affected_shots.items())},
        "affected_boundaries": [list(item) for item in sorted(report.affected_boundaries)],
        "checker_names": sorted(report.checker_names),
        "affected_batches": sorted(report.affected_batches),
        "reasons": report.reasons,
    }


def telemetry_scope(report: InvalidationReport) -> list[str]:
    """Flatten the exact computed invalidation scope without reasons/content."""
    scope = [f"global/{item}" for item in sorted(report.global_artifacts)]
    for scene_id, stages in sorted(report.scene_stages.items()):
        scope.extend(f"scene/{scene_id}/{stage}" for stage in sorted(stages))
    for scene_id, shots in sorted(report.affected_shots.items()):
        scope.extend(f"shot/{scene_id}/{shot}" for shot in sorted(shots))
    scope.extend(
        f"boundary/{scene}/{left}/{right}"
        for scene, left, right in sorted(report.affected_boundaries)
    )
    scope.extend(f"checker/{name}" for name in sorted(report.checker_names))
    scope.extend(f"batch/{index}" for index in sorted(report.affected_batches))
    return sorted(scope)


def record_invalidation_telemetry(
    report: InvalidationReport, session_dir: Path
) -> None:
    record_event(
        session_dir,
        event_type="invalidation",
        stage="dependency_invalidation",
        invalidation_scope=telemetry_scope(report),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute MODE:P invalidation scope.")
    parser.add_argument("graph", type=Path)
    parser.add_argument("changes", type=Path)
    parser.add_argument("--telemetry-session", type=Path)
    args = parser.parse_args()
    try:
        graph = _graph_from_json(json.loads(args.graph.read_text(encoding="utf-8")))
        changes = json.loads(args.changes.read_text(encoding="utf-8"))
        report = compute_invalidation(changes, graph)
        if args.telemetry_session:
            record_invalidation_telemetry(report, args.telemetry_session)
        print(json.dumps(_report_json(report), ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, InvalidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
