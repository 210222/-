"""Approved, offline-normalized knowledge catalog for Director vNext.1.

The runtime entrypoint :func:`load_actual_catalog` returns bounded capsules and
does not open the source books.  Source files are read only by the explicit
offline verification function used during construction/audit.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Tuple

from .contracts import (
    CapsuleFieldProvenance,
    DirectorContractError,
    KnowledgeCapsule,
)


@dataclass(frozen=True)
class CatalogSource:
    source_id: str
    relative_path: str
    source_sha256: str
    bibliographic_locator: str
    authorization: str = "project_internal_approved"


ACTUAL_SOURCES: Tuple[CatalogSource, ...] = (
    CatalogSource(
        source_id="SRC-DIRECTOR-FRAMEWORK",
        relative_path="03_知识库/导演手册_视觉叙事决策框架.md",
        source_sha256="24cf80f1a42b3c9f1286ee729ce0390aa0b42c14b019462ba6514f2999bd9b9c",
        bibliographic_locator="卷一 §1-§5；卷五 §1-§3",
    ),
    CatalogSource(
        source_id="SRC-CAMERA-MOTION",
        relative_path="03_知识库/运镜思维_导演可用运动思维.md",
        source_sha256="ef42f79e93ef67398b512fd4d1fc0e5f8ff3fe9568f062139f7d2e6ed85361dd",
        bibliographic_locator="§一 原则一、原则四、原则五",
    ),
    CatalogSource(
        source_id="SRC-COMPOSITION",
        relative_path="03_知识库/04_构图思维_导演用.md",
        source_sha256="fe5b6c9b526fd1e842077329bf3bb27264ca334f0a4fb52e0c0b63ac7d09a952",
        bibliographic_locator="§一 原则一至五；§4.1；§4.3",
    ),
    CatalogSource(
        source_id="SRC-DIRECTOR-KB-V5",
        relative_path="03_知识库/03_导演知识库_v5.0.md",
        source_sha256="6e507a7d63c185a05f4dd8609745b0b1442691434baf856dbe130747cc26576b",
        bibliographic_locator="§0 GEN-05；§1 D-TRI-02、D-MOT-01 至 D-MOT-03",
    ),
)

_SOURCE_BY_ID: Mapping[str, CatalogSource] = {
    source.source_id: source for source in ACTUAL_SOURCES
}

_PROVENANCE_FIELDS = (
    "primary_type",
    "secondary_tags",
    "decision_level",
    "director_problem",
    "dramatic_function",
    "triggers",
    "contraindications",
    "required_context",
    "execution_rules",
    "expected_effect",
    "tradeoffs",
    "alternatives",
)


def _direct_provenance(locator: str) -> Tuple[CapsuleFieldProvenance, ...]:
    return tuple(
        CapsuleFieldProvenance(
            field_name=field_name,
            source_locator=locator,
            support_level="direct",
        )
        for field_name in _PROVENANCE_FIELDS
    )


def _capsule(
    *,
    capsule_id: str,
    source_id: str,
    line_locator: str,
    primary_type: str,
    tags: Tuple[str, ...],
    secondary_tags: Tuple[str, ...],
    decision_level: str,
    director_problem: str,
    dramatic_function: str,
    triggers: Tuple[str, ...],
    contraindications: Tuple[str, ...],
    required_context: Tuple[str, ...],
    execution_rules: Tuple[str, ...],
    expected_effect: str,
    tradeoffs: Tuple[str, ...],
    alternatives: Tuple[str, ...],
    allowed_uses: Tuple[str, ...],
    conflicting_capsule_ids: Tuple[str, ...] = (),
    anti_pattern_tags: Tuple[str, ...] = (),
) -> KnowledgeCapsule:
    source = _SOURCE_BY_ID[source_id]
    locator = f"{source.relative_path}:{line_locator}"
    return KnowledgeCapsule(
        capsule_id=capsule_id,
        source_locator=locator,
        source_sha256=source.source_sha256,
        source_authorization=source.authorization,
        primary_type=primary_type,
        tags=tags,
        secondary_tags=secondary_tags,
        decision_level=decision_level,
        director_problem=director_problem,
        dramatic_function=dramatic_function,
        triggers=triggers,
        contraindications=contraindications,
        required_context=required_context,
        execution_rules=execution_rules,
        expected_effect=expected_effect,
        tradeoffs=tradeoffs,
        alternatives=alternatives,
        confidence_level="high",
        review_status="approved",
        allowed_uses=allowed_uses,
        conflicting_capsule_ids=conflicting_capsule_ids,
        field_provenance=_direct_provenance(locator),
        anti_pattern_tags=anti_pattern_tags,
    )


ACTUAL_NORMALIZED_CAPSULES: Tuple[KnowledgeCapsule, ...] = (
    _capsule(
        capsule_id="K-DIR-NARRATIVE-FIRST-001",
        source_id="SRC-DIRECTOR-FRAMEWORK",
        line_locator="12-16",
        primary_type="dramatic",
        tags=("relationship", "power", "reveal", "departure", "tension"),
        secondary_tags=("attention", "information_change"),
        decision_level="scene",
        director_problem="What changes for the audience or character at this moment?",
        dramatic_function="make the scene change legible before choosing technique",
        triggers=("relationship", "power", "reveal", "departure", "tension"),
        contraindications=("pure_formatting",),
        required_context=(),
        execution_rules=(
            "state the dramatic change and attention target before any camera answer",
        ),
        expected_effect="technique follows a traceable narrative cause",
        tradeoffs=("may reject decorative coverage",),
        alternatives=("hold a clear static relation",),
        allowed_uses=("scene_intent",),
    ),
    _capsule(
        capsule_id="K-BLOCK-POWER-MAP-001",
        source_id="SRC-DIRECTOR-FRAMEWORK",
        line_locator="27-35",
        primary_type="blocking_performance",
        tags=("power", "blocking", "relationship", "departure"),
        secondary_tags=("screen_position", "depth"),
        decision_level="blocking",
        director_problem="How does spatial relation encode the current power state?",
        dramatic_function="make the power change visible through actor relation",
        triggers=("power", "blocking", "relationship", "departure"),
        contraindications=("location_unknown",),
        required_context=(),
        execution_rules=(
            "commit actor relation and attention direction before camera placement",
        ),
        expected_effect="blocking carries the power shift without explanatory prose",
        tradeoffs=("reduces arbitrary repositioning",),
        alternatives=("use performance timing while preserving positions",),
        allowed_uses=("blocking",),
    ),
    _capsule(
        capsule_id="K-CAM-MOTIVATED-MOTION-001",
        source_id="SRC-CAMERA-MOTION",
        line_locator="11-19,48-54",
        primary_type="camera_shot",
        tags=("motion", "reveal", "relationship_change", "character_action"),
        secondary_tags=("motivation", "follow"),
        decision_level="shot",
        director_problem="Does camera motion have an observable dramatic or actor cause?",
        dramatic_function="make camera motion respond to action, emotion, or discovery",
        triggers=("motion", "reveal", "relationship_change", "character_action"),
        contraindications=("static_information_exchange", "space_unverified"),
        required_context=("blocking_verified",),
        execution_rules=(
            "actor or information change motivates motion",
            "if removing motion does not weaken the scene, keep the camera fixed",
        ),
        expected_effect="movement reads as director intent rather than decoration",
        tradeoffs=("requires verified movement space",),
        alternatives=("fixed camera with actor-driven frame change",),
        allowed_uses=("camera_motion",),
        conflicting_capsule_ids=("K-CAM-STATIC-CLARITY-001",),
    ),
    _capsule(
        capsule_id="K-CAM-STATIC-CLARITY-001",
        source_id="SRC-CAMERA-MOTION",
        line_locator="17-19,76-86",
        primary_type="camera_shot",
        tags=("dialogue", "information_exchange", "static"),
        secondary_tags=("clarity", "restraint"),
        decision_level="shot",
        director_problem="Would camera motion dilute already-clear information?",
        dramatic_function="protect dialogue clarity through restraint",
        triggers=("dialogue", "information_exchange", "static"),
        contraindications=("relationship_change", "reveal"),
        required_context=("blocking_verified",),
        execution_rules=("use a fixed camera when change is carried by performance or words",),
        expected_effect="audience attention stays on the dramatic information",
        tradeoffs=("less overt visual energy",),
        alternatives=("one motivated slow push after the dramatic turn",),
        allowed_uses=("camera_motion",),
        conflicting_capsule_ids=("K-CAM-MOTIVATED-MOTION-001",),
    ),
    _capsule(
        capsule_id="K-COMP-SEQUENCE-001",
        source_id="SRC-COMPOSITION",
        line_locator="183-192",
        primary_type="camera_shot",
        tags=("composition", "motion", "reveal", "reframing"),
        secondary_tags=("start_frame", "end_frame", "attention"),
        decision_level="shot",
        director_problem="What complete start and end compositions express the shot change?",
        dramatic_function="treat movement as a time-based relation between compositions",
        triggers=("composition", "motion", "reveal", "reframing"),
        contraindications=("space_unverified",),
        required_context=("blocking_verified",),
        execution_rules=(
            "define complete start and end compositions before the camera path",
            "keep the attention center stable unless instability is the dramatic event",
        ),
        expected_effect="camera paths preserve readable composition and attention",
        tradeoffs=("limits impossible or decorative paths",),
        alternatives=("hard cut between two justified compositions",),
        allowed_uses=("composition_motion",),
    ),
    _capsule(
        capsule_id="K-EDIT-AXIS-GAZE-001",
        source_id="SRC-DIRECTOR-FRAMEWORK",
        line_locator="184-199",
        primary_type="editing_validation",
        tags=("dialogue", "gaze", "departure", "axis", "screen_direction"),
        secondary_tags=("continuity", "spatial_readability"),
        decision_level="validation",
        director_problem="Do adjacent shots preserve axis, gaze, and movement direction?",
        dramatic_function="keep spatial relations readable across a cut",
        triggers=("dialogue", "gaze", "departure", "axis", "screen_direction"),
        contraindications=("approved_axis_break",),
        required_context=("blocking_verified",),
        execution_rules=(
            "keep camera on the committed side of the relation axis",
            "match gaze and movement directions across adjacent shots",
        ),
        expected_effect="the audience understands who looks or moves toward whom",
        tradeoffs=("some attractive angles become unavailable",),
        alternatives=("re-establish the axis through actor repositioning or a bridge shot",),
        allowed_uses=("edit_validation",),
    ),
    _capsule(
        capsule_id="K-ANTI-UNMOTIVATED-TECHNIQUE-001",
        source_id="SRC-DIRECTOR-FRAMEWORK",
        line_locator="10-16,36-43",
        primary_type="camera_shot",
        tags=("motion", "composition", "dialogue", "reveal"),
        secondary_tags=("anti_pattern",),
        decision_level="validation",
        director_problem="Is a technique present only because it looks impressive?",
        dramatic_function="remove technique that does not change story comprehension",
        triggers=("motion", "composition", "dialogue", "reveal"),
        contraindications=("explicit_style_event",),
        required_context=("blocking_verified",),
        execution_rules=("reject camera or composition changes without a dramatic cause",),
        expected_effect="visual choices remain selective and legible",
        tradeoffs=("less decorative variety",),
        alternatives=("preserve the strongest justified visual decision",),
        allowed_uses=("review_only",),
        anti_pattern_tags=("unmotivated_technique",),
    ),
)


def validate_actual_catalog() -> None:
    """Validate provenance completeness without reading source documents."""

    source_hashes = {
        source.source_sha256 for source in ACTUAL_SOURCES
    }
    ids = [capsule.capsule_id for capsule in ACTUAL_NORMALIZED_CAPSULES]
    if len(ids) != len(set(ids)):
        raise DirectorContractError("actual knowledge catalog IDs must be unique")
    for capsule in ACTUAL_NORMALIZED_CAPSULES:
        if capsule.source_sha256 not in source_hashes:
            raise DirectorContractError(
                f"capsule {capsule.capsule_id} has no registered source snapshot"
            )
        if capsule.source_authorization != "project_internal_approved":
            raise DirectorContractError(
                f"capsule {capsule.capsule_id} source is not approved"
            )
        provenance = {
            item.field_name: item.support_level
            for item in capsule.field_provenance
        }
        missing = [
            field_name
            for field_name in _PROVENANCE_FIELDS
            if provenance.get(field_name) not in {"direct", "inferred", "unknown"}
        ]
        if missing:
            raise DirectorContractError(
                f"capsule {capsule.capsule_id} lacks provenance for {missing}"
            )


def load_actual_catalog() -> Tuple[KnowledgeCapsule, ...]:
    """Return only normalized cards; this function performs no source I/O."""

    validate_actual_catalog()
    return ACTUAL_NORMALIZED_CAPSULES


def verify_actual_source_snapshot(project_root: Path) -> Mapping[str, object]:
    """Offline audit of the local source files and the normalized snapshot."""

    results = []
    for source in ACTUAL_SOURCES:
        path = project_root / source.relative_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != source.source_sha256:
            raise DirectorContractError(
                f"knowledge source drift: {source.relative_path}"
            )
        results.append(
            {
                "source_id": source.source_id,
                "relative_path": source.relative_path,
                "source_sha256": actual_hash,
                "authorization": source.authorization,
                "bibliographic_locator": source.bibliographic_locator,
            }
        )
    snapshot_payload = {
        "sources": results,
        "capsule_fingerprints": [
            capsule.fingerprint for capsule in load_actual_catalog()
        ],
    }
    snapshot_sha256 = hashlib.sha256(
        json.dumps(
            snapshot_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        **snapshot_payload,
        "snapshot_sha256": snapshot_sha256,
        "runtime_full_sources_loaded": False,
    }


__all__ = [
    "ACTUAL_NORMALIZED_CAPSULES",
    "ACTUAL_SOURCES",
    "CatalogSource",
    "load_actual_catalog",
    "validate_actual_catalog",
    "verify_actual_source_snapshot",
]
