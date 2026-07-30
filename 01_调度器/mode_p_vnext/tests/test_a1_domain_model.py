"""Mechanical acceptance tests for A1's canonical vNext domain boundary.

These tests deliberately describe the public schema that downstream A2--A10
must consume.  Legacy schemas remain outside this authority boundary.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path

import pytest

from mode_p_vnext.compat.legacy_checkpoint import read_legacy_b0_k2_checkpoint
from mode_p_vnext.domain.artifact import (
    ArtifactEnvelope,
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    ValidationStatus,
    canonical_sha256,
)
from mode_p_vnext.domain.blocking import BlockingBeatDraft, BlockingDraft
from mode_p_vnext.domain.direction import EpisodeDirectionDraft, SceneIntentDraft
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.time import (
    TICKS_PER_SECOND,
    CanonicalTimeline,
    GenerationSegmentTimeline,
    TickRange,
    TimelinePlacement,
)
from mode_p_vnext.domain.vec import ExecutionDesignDraft


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_ROOT = Path(__file__).resolve().parents[1] / "domain"


def _episode_direction() -> EpisodeDirectionDraft:
    return EpisodeDirectionDraft(
        dramatic_promise="The quiet decision changes the relationship.",
        audience_contract="The audience can follow cause and effect.",
        tension_curve=("arrival", "choice", "aftermath"),
        visual_principles=("hold on the decision",),
        continuity_priorities=("the letter remains in the left hand",),
        unresolved_questions=("Does the other character see the letter?",),
    )


def test_canonical_artifact_envelope_is_hash_bound_and_machine_assembled() -> None:
    direction = _episode_direction()
    source = SourceRef(source_id="script:episode-1", digest="a" * 64)
    artifact_id = IdFactory(program_version="vnext-2.1").create(
        artifact_kind=ArtifactKind.EPISODE_DIRECTION,
        episode_id="episode-1",
        scene_id=None,
        stage="A1",
        input_digest=canonical_sha256({"script": "episode-1"}),
        ordinal=1,
    )
    envelope = ArtifactEnvelope.create(
        artifact_id=artifact_id,
        artifact_kind=ArtifactKind.EPISODE_DIRECTION,
        schema_version="2.1",
        program_version="vnext-2.1",
        payload=direction,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
        validation_status=ValidationStatus.DRAFT,
        created_at="2026-07-30T00:00:00Z",
    )

    assert envelope.content_sha256 == ArtifactEnvelope.content_digest_for(
        artifact_kind=ArtifactKind.EPISODE_DIRECTION,
        schema_version="2.1",
        program_version="vnext-2.1",
        payload=direction,
        source_refs=(source,),
        dependency_digests={"script": source.digest},
    )
    assert envelope.artifact_id == artifact_id
    assert envelope.validation_status is ValidationStatus.DRAFT
    assert dataclasses.is_dataclass(envelope)
    assert envelope.__dataclass_params__.frozen
    with pytest.raises(TypeError):
        envelope.dependency_digests["script"] = "b" * 64

    with pytest.raises(DomainValidationError, match="content_sha256"):
        ArtifactEnvelope(
            artifact_id=artifact_id,
            artifact_kind=ArtifactKind.EPISODE_DIRECTION,
            schema_version="2.1",
            program_version="vnext-2.1",
            payload=direction,
            source_refs=(source,),
            dependency_digests={"script": source.digest},
            content_sha256="0" * 64,
            created_at="2026-07-30T00:00:00Z",
            validation_status=ValidationStatus.DRAFT,
        )


def test_id_factory_is_stable_and_drafts_cannot_carry_machine_authority() -> None:
    factory = IdFactory(program_version="vnext-2.1")
    kwargs = {
        "artifact_kind": ArtifactKind.SCENE_INTENT,
        "episode_id": "episode-1",
        "scene_id": "scene-2",
        "stage": "B0",
        "input_digest": "b" * 64,
        "ordinal": 3,
    }
    assert factory.create(**kwargs) == factory.create(**kwargs)
    assert factory.create(**kwargs) != factory.create(**{**kwargs, "ordinal": 4})

    draft_fields = {
        field.name
        for draft_type in (
            EpisodeDirectionDraft,
            SceneIntentDraft,
            BlockingBeatDraft,
            BlockingDraft,
            ExecutionDesignDraft,
        )
        for field in dataclasses.fields(draft_type)
    }
    forbidden_model_authority = {
        "artifact_id",
        "content_sha256",
        "dependency_digests",
        "start_tick",
        "end_tick",
        "timeline",
        "vec_id",
        "contract_id",
    }
    assert not (draft_fields & forbidden_model_authority)


def test_only_24000_tick_canonical_timebase_and_half_open_ranges_exist() -> None:
    assert TICKS_PER_SECOND == 24_000
    timeline = CanonicalTimeline()
    assert timeline.ticks_per_second == 24_000
    assert TickRange(10, 20).contains(10)
    assert not TickRange(10, 20).contains(20)
    assert TickRange(10, 20).duration_ticks == 10
    assert TimelinePlacement(scope_id="scene-1", interval=TickRange(100, 300)).interval.start_tick == 100
    assert GenerationSegmentTimeline(duration_ticks=120).interval == TickRange(0, 120)
    with pytest.raises(DomainValidationError):
        CanonicalTimeline(ticks_per_second=24)
    with pytest.raises(DomainValidationError):
        GenerationSegmentTimeline(start_tick=1, duration_ticks=120)


def test_domain_schema_is_frozen_and_has_one_declared_authority_per_type() -> None:
    module_names = (
        "artifact",
        "ids",
        "time",
        "facts",
        "direction",
        "knowledge",
        "blocking",
        "decisions",
        "vec",
        "projection",
        "evidence",
        "release",
    )
    declared_types: list[str] = []
    for module_name in module_names:
        module = importlib.import_module(f"mode_p_vnext.domain.{module_name}")
        assert module.DOMAIN_SCHEMA_VERSION == "2.1"
        authority = module.CANONICAL_DOMAIN_TYPES
        assert authority, module_name
        assert len(authority) == len(set(authority)), module_name
        declared_types.extend(authority)
    assert len(declared_types) == len(set(declared_types))

    for draft_type in (
        EpisodeDirectionDraft,
        SceneIntentDraft,
        BlockingBeatDraft,
        BlockingDraft,
        ExecutionDesignDraft,
    ):
        assert draft_type.__dataclass_params__.frozen
    for type_name in declared_types:
        for module_name in module_names:
            module = importlib.import_module(f"mode_p_vnext.domain.{module_name}")
            candidate = getattr(module, type_name, None)
            if candidate is not None and dataclasses.is_dataclass(candidate):
                assert candidate.__dataclass_params__.frozen, type_name


def test_domain_has_no_legacy_or_runtime_imports() -> None:
    allowed_stdlib_roots = {
        "__future__",
        "dataclasses",
        "datetime",
        "enum",
        "fractions",
        "hashlib",
        "json",
        "types",
        "typing",
    }
    violations: list[str] = []
    for source_path in DOMAIN_ROOT.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for imported in node.names:
                    root = imported.name.split(".", 1)[0]
                    if root not in allowed_stdlib_roots:
                        violations.append(f"{source_path.name}: import {imported.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                if node.module is None:
                    continue
                root = node.module.split(".", 1)[0]
                if root == "mode_p_vnext" and not node.module.startswith("mode_p_vnext.domain"):
                    violations.append(f"{source_path.name}: from {node.module}")
                elif root not in allowed_stdlib_roots and root != "mode_p_vnext":
                    violations.append(f"{source_path.name}: from {node.module}")
    assert not violations, "\n".join(violations)


def test_compat_is_one_way_and_never_imports_legacy_runtime_code() -> None:
    compat_root = Path(__file__).resolve().parents[1] / "compat"
    violations: list[str] = []
    for source_path in compat_root.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("mode_p_vnext."):
                if not node.module.startswith("mode_p_vnext.domain"):
                    violations.append(f"{source_path.name}: from {node.module}")
    assert not violations, "\n".join(violations)


def test_legacy_checkpoint_adapter_is_read_only_and_returns_canonical_blocking_draft() -> None:
    checkpoint = (
        REPOSITORY_ROOT
        / "MODE_P_REDESIGN_PROJECT"
        / "vnext_completion_runs"
        / "CPL-2_UNKNOWN_TEXT_SHADOW_016"
        / "CHECKPOINT_B0_K2.json"
    )
    envelope = read_legacy_b0_k2_checkpoint(checkpoint)

    assert isinstance(envelope, ArtifactEnvelope)
    assert envelope.artifact_kind is ArtifactKind.BLOCKING_DRAFT
    assert isinstance(envelope.payload, BlockingDraft)
    assert envelope.payload.beats
    assert envelope.validation_status is ValidationStatus.DRAFT
    assert all(ref.source_id.startswith("legacy-checkpoint:") for ref in envelope.source_refs)
    assert envelope.content_sha256 == ArtifactEnvelope.content_digest_for(
        artifact_kind=envelope.artifact_kind,
        schema_version=envelope.schema_version,
        program_version=envelope.program_version,
        payload=envelope.payload,
        source_refs=envelope.source_refs,
        dependency_digests=envelope.dependency_digests,
    )
