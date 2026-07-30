"""Budget-measured Director batch scheduler for MODE:P.

Batch boundaries are computed from recorded context and output budgets.  Scene
count alone is never a complexity judgment.  Missing preparation documents
produce a provisional manifest that cannot authorize an LLM call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from script_facts_tool import FactsError, load_digest


_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parents[1]
_DEFAULT_PROFILE = _MODULE_DIR / "model_budget_profile.json"
_SHARED_DOCUMENTS = (
    "SCRIPT_STRUCTURE.json",
    "SCRIPT_FACTS.md",
    "EPISODE_VISUAL_BIBLE.md",
    "EPISODE_CONTINUITY_LEDGER.md",
)
_CORE_FILES = tuple(sorted((_MODULE_DIR / "knowledge" / "core").glob("*.md")))
_INSTRUCTION_FILES = (
    _PROJECT_ROOT / "CLAUDE.md",
    _PROJECT_ROOT / ".claude" / "agents" / "mode-p-director.md",
    _PROJECT_ROOT / "02_Agent" / "director_agent.md",
    _MODULE_DIR / "director_master_template.md",
)


class ScheduleError(ValueError):
    """Raised when measured inputs cannot produce a safe schedule."""


@dataclass(frozen=True)
class BudgetProfile:
    schema_version: str
    profile_id: str
    source: str
    context_window_tokens: int
    reserved_system_tool_tokens: int
    reserved_output_tokens: int
    max_output_tokens_per_call: int
    safety_margin_ratio: float
    missing_document_reserve_tokens: int
    token_estimator_version: str

    @property
    def safety_margin_tokens(self) -> int:
        return math.ceil(self.context_window_tokens * self.safety_margin_ratio)

    @property
    def input_budget(self) -> int:
        return (
            self.context_window_tokens
            - self.reserved_system_tool_tokens
            - self.reserved_output_tokens
            - self.safety_margin_tokens
        )

    @property
    def output_budget(self) -> int:
        return min(self.reserved_output_tokens, self.max_output_tokens_per_call)


@dataclass(frozen=True)
class TextMeasurement:
    label: str
    character_count: int
    estimated_tokens: int
    content_sha256: str
    source: str


@dataclass
class SceneMeasurement:
    scene_index: int
    source_characters: int
    source_tokens: int
    estimated_shots: int
    shot_estimate_basis: str
    estimated_output_tokens: int
    capsules: list[str]
    capsule_characters: int
    capsule_tokens: int
    source_measurement: str


@dataclass
class BatchSpec:
    batch_index: int
    label: str
    scene_indices: list[int]
    shared_input_characters: int
    scene_input_characters: int
    capsule_input_characters: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    input_headroom_tokens: int
    output_headroom_tokens: int
    estimated_shots: int
    loaded_capsules: list[str]
    shared_documents: list[str]
    prior_committed_ledger_required: bool
    fresh_dp_required: bool = True
    same_episode_director_required: bool = True


@dataclass
class BatchManifest:
    schema_version: str
    script_source_hash: str
    mode: str
    director_scope: str
    director_resume_required: bool
    authoritative: bool
    provisional_reasons: list[str]
    total_scenes: int
    selected_scenes: list[int]
    total_batches: int
    budget_profile: dict[str, Any]
    estimator_version: str
    shared_measurements: list[TextMeasurement]
    scene_measurements: list[SceneMeasurement]
    batches: list[BatchSpec]
    shared_documents: list[str]
    split_reasons: list[str]
    warning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_budget_profile(path: Path = _DEFAULT_PROFILE) -> BudgetProfile:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScheduleError(f"cannot read model budget profile: {exc}") from exc
    expected = {
        "schema_version", "profile_id", "source", "context_window_tokens",
        "reserved_system_tool_tokens", "reserved_output_tokens",
        "max_output_tokens_per_call", "safety_margin_ratio",
        "missing_document_reserve_tokens", "token_estimator_version",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise ScheduleError("model budget profile fields do not match schema")
    if data["schema_version"] != "1.0" or data["source"] not in {"user_config", "runtime_detected"}:
        raise ScheduleError("unsupported model budget profile")
    integer_fields = (
        "context_window_tokens", "reserved_system_tool_tokens",
        "reserved_output_tokens", "max_output_tokens_per_call",
        "missing_document_reserve_tokens",
    )
    for name in integer_fields:
        value = data[name]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ScheduleError(f"budget profile {name} must be a positive integer")
    ratio = data["safety_margin_ratio"]
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not 0 < ratio < 0.5:
        raise ScheduleError("safety_margin_ratio must be between 0 and 0.5")
    for name in ("profile_id", "token_estimator_version"):
        if not isinstance(data[name], str) or not data[name]:
            raise ScheduleError(f"budget profile {name} cannot be empty")
    profile = BudgetProfile(**data)
    if profile.input_budget <= 0 or profile.output_budget <= 0:
        raise ScheduleError("budget reserves leave no usable model capacity")
    return profile


def estimate_tokens(text: str, estimator_version: str = "unicode_conservative_v1") -> int:
    """Conservative language-aware estimate used only for capacity planning."""
    if estimator_version != "unicode_conservative_v1":
        raise ScheduleError(f"unsupported token estimator: {estimator_version}")
    if not isinstance(text, str):
        raise ScheduleError("token estimator input must be text")
    cjk = ascii_alnum = ascii_punct = whitespace = other = 0
    for char in text:
        code = ord(char)
        if char.isspace():
            whitespace += 1
        elif (
            0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF
            or 0x3040 <= code <= 0x30FF or 0xAC00 <= code <= 0xD7AF
        ):
            cjk += 1
        elif code < 128 and char.isalnum():
            ascii_alnum += 1
        elif code < 128:
            ascii_punct += 1
        else:
            other += 1
    estimate = (
        cjk * 1.25 + ascii_alnum / 3.2 + ascii_punct / 2.0
        + whitespace / 8.0 + other * 1.5
    )
    return max(1, math.ceil(estimate) + 8)


def _measurement(label: str, text: str, source: str, profile: BudgetProfile) -> TextMeasurement:
    return TextMeasurement(
        label=label,
        character_count=len(text),
        estimated_tokens=estimate_tokens(text, profile.token_estimator_version),
        content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source=source,
    )


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ScheduleError(f"cannot read {label}: {exc}") from exc


def _scene_sources(
    digest: dict[str, Any], profile: BudgetProfile
) -> tuple[dict[int, tuple[str, str]], list[str]]:
    source_path = Path(digest["file_path"])
    provisional: list[str] = []
    if source_path.is_file():
        try:
            # Match script_ingest's universal-newline and BOM normalization.
            text = source_path.read_text(encoding=digest["encoding"]).lstrip("\ufeff")
        except (OSError, UnicodeError, LookupError) as exc:
            raise ScheduleError(f"cannot decode script source: {exc}") from exc
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != digest["source_content_hash"]:
            raise ScheduleError("script source changed after SCRIPT_STRUCTURE was created")
        lines = text.splitlines()
        result: dict[int, tuple[str, str]] = {}
        for scene in digest["scenes"]:
            start, end = scene["start_line"], scene["end_line"]
            result[scene["index"]] = ("\n".join(lines[start - 1:end]), "script_content")
        return result, provisional

    provisional.append("script source file unavailable; scene sizes use line-span reserve")
    result = {}
    for scene in digest["scenes"]:
        line_count = max(1, scene["end_line"] - scene["start_line"] + 1)
        result[scene["index"]] = ("X" * (line_count * 96), "line_span_reserve")
    return result, provisional


def _shared_measurements(
    ingest_path: Path,
    session_dir: Path,
    user_constraints: str,
    profile: BudgetProfile,
) -> tuple[list[TextMeasurement], list[str]]:
    measurements: list[TextMeasurement] = []
    provisional: list[str] = []
    seen: set[Path] = set()
    required_paths = [ingest_path]
    required_paths.extend(session_dir / name for name in _SHARED_DOCUMENTS[1:])
    required_paths.extend(_CORE_FILES)
    required_paths.extend(_INSTRUCTION_FILES)
    for path in required_paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if path.is_file():
            text = _read_text(path, path.name)
            measurements.append(_measurement(path.name, text, path.as_posix(), profile))
        else:
            provisional.append(f"missing shared input: {path.name}")
            reserve_text = "X" * (profile.missing_document_reserve_tokens * 3)
            measurements.append(_measurement(
                path.name, reserve_text, "provisional_missing_document_reserve", profile
            ))
    measurements.append(_measurement(
        "USER_VISUAL_CONSTRAINTS", user_constraints, "caller_input", profile
    ))
    return measurements, provisional


def _capsule_measurements(
    capsules_by_scene: Mapping[int, list[Path]], profile: BudgetProfile
) -> tuple[dict[str, TextMeasurement], dict[int, list[str]]]:
    measured: dict[str, TextMeasurement] = {}
    per_scene: dict[int, list[str]] = {}
    for scene, paths in capsules_by_scene.items():
        labels: list[str] = []
        for path in paths:
            path = Path(path)
            label = path.resolve().as_posix()
            if label not in measured:
                measured[label] = _measurement(
                    label, _read_text(path, f"capsule {path.name}"), label, profile
                )
            labels.append(label)
        if len(labels) != len(set(labels)):
            raise ScheduleError(f"scene {scene} contains duplicate capsule paths")
        per_scene[scene] = labels
    return measured, per_scene


def _estimate_shots(scene_text: str, explicit: int | None) -> tuple[int, str]:
    if explicit is not None:
        if isinstance(explicit, bool) or not isinstance(explicit, int) or explicit < 1:
            raise ScheduleError("expected Shot counts must be positive integers")
        return explicit, "caller_estimate"
    nonempty = [line for line in scene_text.splitlines() if line.strip()]
    return max(1, math.ceil(len(nonempty) / 3)), "nonempty_line_capacity_estimate_v1"


def _scene_output_tokens(source_tokens: int, expected_shots: int) -> int:
    # Versioned capacity formula for Master-authored creative text.  Views are
    # local projections and therefore do not consume Director output tokens.
    return math.ceil(900 + source_tokens * 2.5 + expected_shots * 520)


def schedule_batches(
    ingest_json_path: Path,
    max_scenes_per_batch: int | None = None,
    scene_indices: list[int] | None = None,
    *,
    session_dir: Path | None = None,
    budget_profile_path: Path | None = None,
    capsules_by_scene: Mapping[int, list[Path]] | None = None,
    expected_shots_by_scene: Mapping[int, int] | None = None,
    user_visual_constraints: str = "",
    include_lead_director_output: bool = False,
) -> BatchManifest:
    """Measure real inputs and greedily pack ordered scenes within both budgets."""
    try:
        digest = load_digest(ingest_json_path)
    except FactsError as exc:
        raise ScheduleError(str(exc)) from exc
    profile = load_budget_profile(budget_profile_path or _DEFAULT_PROFILE)
    if max_scenes_per_batch is not None and (
        isinstance(max_scenes_per_batch, bool)
        or not isinstance(max_scenes_per_batch, int) or max_scenes_per_batch < 1
    ):
        raise ScheduleError("max_scenes_per_batch must be a positive explicit limit")
    available = [scene["index"] for scene in digest["scenes"]]
    selected = available if scene_indices is None else list(scene_indices)
    if not selected or selected != sorted(set(selected)):
        raise ScheduleError("selected scene indices must be unique, non-empty, and ascending")
    unknown = sorted(set(selected) - set(available))
    if unknown:
        raise ScheduleError(f"selected scenes are outside the episode: {unknown}")

    session = (session_dir or ingest_json_path.parent).resolve()
    sources, provisional = _scene_sources(digest, profile)
    shared, missing = _shared_measurements(
        ingest_json_path, session, user_visual_constraints, profile
    )
    provisional.extend(missing)
    capsule_map = capsules_by_scene or {}
    if any(scene not in available for scene in capsule_map):
        raise ScheduleError("capsules_by_scene references an unknown scene")
    capsules, scene_capsules = _capsule_measurements(capsule_map, profile)
    expected = expected_shots_by_scene or {}
    if any(scene not in available for scene in expected):
        raise ScheduleError("expected_shots_by_scene references an unknown scene")

    scene_measurements: dict[int, SceneMeasurement] = {}
    for scene in selected:
        text, source_method = sources[scene]
        source_tokens = estimate_tokens(text, profile.token_estimator_version)
        shots, basis = _estimate_shots(text, expected.get(scene))
        labels = sorted(scene_capsules.get(scene, []))
        scene_measurements[scene] = SceneMeasurement(
            scene_index=scene,
            source_characters=len(text),
            source_tokens=source_tokens,
            estimated_shots=shots,
            shot_estimate_basis=basis,
            estimated_output_tokens=_scene_output_tokens(source_tokens, shots),
            capsules=labels,
            capsule_characters=sum(capsules[label].character_count for label in labels),
            capsule_tokens=sum(capsules[label].estimated_tokens for label in labels),
            source_measurement=source_method,
        )

    shared_tokens = sum(item.estimated_tokens for item in shared)
    shared_characters = sum(item.character_count for item in shared)
    full_script_tokens = sum(item.source_tokens for item in scene_measurements.values())
    lead_output = (
        math.ceil(1200 + full_script_tokens * 1.5 + len(available) * 650)
        if include_lead_director_output else 0
    )

    def measure_group(group: list[int], first_batch: bool) -> tuple[int, int, int, int, list[str]]:
        labels = sorted({label for scene in group for label in scene_measurements[scene].capsules})
        capsule_tokens = sum(capsules[label].estimated_tokens for label in labels)
        capsule_chars = sum(capsules[label].character_count for label in labels)
        input_tokens = shared_tokens + capsule_tokens + sum(
            scene_measurements[scene].source_tokens for scene in group
        )
        output_tokens = sum(
            scene_measurements[scene].estimated_output_tokens for scene in group
        ) + (lead_output if first_batch else 0)
        return input_tokens, output_tokens, capsule_tokens, capsule_chars, labels

    groups: list[list[int]] = []
    current: list[int] = []
    split_reasons: list[str] = []
    for scene in selected:
        candidate = current + [scene]
        first_batch = not groups
        input_tokens, output_tokens, _, _, _ = measure_group(candidate, first_batch)
        scene_limit_hit = (
            max_scenes_per_batch is not None and len(candidate) > max_scenes_per_batch
        )
        input_hit = input_tokens > profile.input_budget
        output_hit = output_tokens > profile.output_budget
        if current and (scene_limit_hit or input_hit or output_hit):
            if scene_limit_hit:
                split_reasons.append(f"explicit scene limit before scene {scene}")
            if input_hit:
                split_reasons.append(f"input budget before scene {scene}")
            if output_hit:
                split_reasons.append(f"output budget before scene {scene}")
            groups.append(current)
            current = [scene]
            input_tokens, output_tokens, _, _, _ = measure_group(current, False)
        else:
            current = candidate
        if input_tokens > profile.input_budget or output_tokens > profile.output_budget:
            raise ScheduleError(
                f"scene {scene} cannot fit one Director call: input {input_tokens}/"
                f"{profile.input_budget}, output {output_tokens}/{profile.output_budget}"
            )
    groups.append(current)

    batches: list[BatchSpec] = []
    for index, group in enumerate(groups, 1):
        input_tokens, output_tokens, _, capsule_chars, labels = measure_group(group, index == 1)
        batches.append(BatchSpec(
            batch_index=index,
            label=_batch_label(group),
            scene_indices=group,
            shared_input_characters=shared_characters,
            scene_input_characters=sum(scene_measurements[s].source_characters for s in group),
            capsule_input_characters=capsule_chars,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            input_headroom_tokens=profile.input_budget - input_tokens,
            output_headroom_tokens=profile.output_budget - output_tokens,
            estimated_shots=sum(scene_measurements[s].estimated_shots for s in group),
            loaded_capsules=labels,
            shared_documents=list(_SHARED_DOCUMENTS),
            prior_committed_ledger_required=index > 1,
        ))
    authoritative = not provisional
    warning_parts: list[str] = []
    if not authoritative:
        warning_parts.append("PROVISIONAL: missing inputs use explicit reserves; do not call Director")
    if len(batches) > 1:
        warning_parts.append(
            "Resume the same episode Director; each batch reloads Visual Bible and the latest committed Ledger"
        )
    return BatchManifest(
        schema_version="1.1",
        script_source_hash=digest["source_content_hash"],
        mode="single_batch" if len(batches) == 1 else "multi_batch",
        director_scope="episode",
        director_resume_required=True,
        authoritative=authoritative,
        provisional_reasons=provisional,
        total_scenes=digest["scene_count"],
        selected_scenes=selected,
        total_batches=len(batches),
        budget_profile={
            **asdict(profile),
            "safety_margin_tokens": profile.safety_margin_tokens,
            "detected_input_budget": profile.input_budget,
            "detected_output_budget": profile.output_budget,
        },
        estimator_version=profile.token_estimator_version,
        shared_measurements=shared,
        scene_measurements=[scene_measurements[index] for index in selected],
        batches=batches,
        shared_documents=list(_SHARED_DOCUMENTS),
        split_reasons=split_reasons,
        warning="; ".join(warning_parts),
    )


def _batch_label(indices: list[int]) -> str:
    if len(indices) == 1:
        return f"Scene {indices[0]}"
    if indices == list(range(indices[0], indices[-1] + 1)):
        return f"Scenes {indices[0]}-{indices[-1]}"
    return "Scenes " + ",".join(str(index) for index in indices)


def main() -> int:
    parser = argparse.ArgumentParser(description="Schedule budget-measured Director batches.")
    parser.add_argument("ingest_json", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--session-dir", type=Path)
    parser.add_argument("--budget-profile", type=Path)
    parser.add_argument("--max-scenes-per-batch", type=int)
    parser.add_argument("--scenes")
    args = parser.parse_args()
    try:
        scenes = None
        if args.scenes:
            scenes = [int(item) for item in re.split(r"\s*,\s*", args.scenes) if item]
        manifest = schedule_batches(
            args.ingest_json,
            args.max_scenes_per_batch,
            scenes,
            session_dir=args.session_dir,
            budget_profile_path=args.budget_profile,
        )
        payload = json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        return 0
    except (ScheduleError, OSError, ValueError) as exc:
        print(f"Batch schedule error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
