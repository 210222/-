"""Core, non-creative contracts for Director vNext.1 knowledge decisions.

The objects in this file carry provenance and bounded choices.  They do not
produce camera plans or prompts; that remains a later Director phase.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Literal, Mapping, Sequence, Tuple


class DirectorContractError(ValueError):
    """Raised when a vNext.1 contract would be ambiguous or unsafe."""


PRIMARY_CAPSULE_TYPES = frozenset(
    {
        "dramatic",
        "blocking_performance",
        "camera_shot",
        "editing_validation",
        "anti_pattern",
    }
)
CONFIDENCE_LEVELS = frozenset({"high", "medium", "low"})
REVIEW_STATUSES = frozenset({"approved", "draft", "rejected"})
SOURCE_AUTHORIZATION_STATUSES = frozenset(
    {"project_internal_approved", "restricted", "unknown"}
)
DECISION_LEVELS = frozenset(
    {"episode", "scene", "blocking", "shot", "edit", "validation"}
)
PROVENANCE_SUPPORT_LEVELS = frozenset({"direct", "inferred", "unknown"})
CONFLICT_PRIORITY_SOURCES = frozenset(
    {
        "user_or_project_fact",
        "approved_asset_fact",
        "episode_or_scene_intent",
        "target_capability_evidence",
        "verified_generation_evidence",
        "knowledge_confidence",
        "aesthetic_preference",
    }
)
K1_TYPES = frozenset({"dramatic", "blocking_performance"})
K2_TYPES = frozenset({"blocking_performance", "camera_shot", "editing_validation"})


def _canonical_hash(value: Mapping[str, object]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_identifier(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise DirectorContractError(f"{field_name} is required")


def _require_sha256(value: str, field_name: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise DirectorContractError(f"{field_name} must be a lowercase SHA-256")


# Phase A is deliberately a dramatic diagnosis, rather than a disguised shot
# list.  Keep this check narrow and explicit: it rejects execution vocabulary,
# but does not prohibit normal scene, character, or blocking questions.
_PHASE_A_EXECUTION_PATTERN = re.compile(
    r"(?:镜头|运镜|景别|焦段|机位|剪辑|硬切|转场|推拉摇移|"
    r"\bcamera\b|\blens\b|\bfocal\b|\bshot\b|\bcut\b|\bedit\b|"
    r"\bdolly\b|\bpan\b|\btilt\b|\bzoom\b|\bframe\b)",
    re.IGNORECASE,
)


def assert_phase_a_text_is_non_execution(value: str, field_name: str) -> None:
    """Reject a Phase-A answer that pre-answers B0/B1 execution decisions."""

    _require_identifier(value, field_name)
    if _PHASE_A_EXECUTION_PATTERN.search(value):
        raise DirectorContractError(
            f"{field_name} contains camera/edit execution language; Phase A may only diagnose intent"
        )


@dataclass(frozen=True)
class EpisodeRequest:
    """The stable E0 input.  It has no scene-level execution instructions."""

    episode_id: str
    episode_premise: str
    approved_story_facts: Tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.episode_id, "episode_id")
        _require_identifier(self.episode_premise, "episode_premise")

    @property
    def cache_payload(self) -> Mapping[str, object]:
        return {
            "episode_id": self.episode_id,
            "episode_premise": self.episode_premise,
            "approved_story_facts": self.approved_story_facts,
        }


@dataclass(frozen=True)
class SceneInput:
    """The stable S1 input, scoped to approved script and continuity facts."""

    scene_id: str
    episode_id: str
    script_excerpt: str
    scene_context: str
    character_state: Tuple[str, ...]
    scene_tags: Tuple[str, ...]
    approved_context: Tuple[str, ...]
    impact_level: str = "normal"

    def __post_init__(self) -> None:
        _require_identifier(self.scene_id, "scene_id")
        _require_identifier(self.episode_id, "episode_id")
        _require_identifier(self.script_excerpt, "script_excerpt")
        _require_identifier(self.scene_context, "scene_context")
        if self.impact_level not in {"normal", "high"}:
            raise DirectorContractError("SceneInput impact_level must be normal or high")

    @property
    def cache_payload(self) -> Mapping[str, object]:
        return {
            "scene_id": self.scene_id,
            "episode_id": self.episode_id,
            "script_excerpt": self.script_excerpt,
            "scene_context": self.scene_context,
            "character_state": self.character_state,
            "scene_tags": self.scene_tags,
            "approved_context": self.approved_context,
            "impact_level": self.impact_level,
        }


@dataclass(frozen=True)
class EpisodeDirectionState:
    """Persistent E0 direction shared by every scene in one episode.

    These fields define what the episode is trying to make legible.  They may
    not specify a camera, edit, lens, or any other downstream execution answer.
    """

    episode_id: str
    director_id: str
    thematic_axis: str
    character_arc: Tuple[str, ...]
    information_priorities: Tuple[str, ...]
    visual_development_goal: str

    def __post_init__(self) -> None:
        _require_identifier(self.episode_id, "episode_id")
        _require_identifier(self.director_id, "director_id")
        for field_name, value in (
            ("thematic_axis", self.thematic_axis),
            ("visual_development_goal", self.visual_development_goal),
        ):
            assert_phase_a_text_is_non_execution(value, field_name)
        for field_name, values in (
            ("character_arc", self.character_arc),
            ("information_priorities", self.information_priorities),
        ):
            if not values:
                raise DirectorContractError(f"{field_name} requires at least one approved priority")
            for item in values:
                assert_phase_a_text_is_non_execution(item, field_name)


@dataclass(frozen=True)
class SceneIntentBeat:
    """A fact-linked dramatic beat, deliberately without a shot prescription."""

    beat_id: str
    fact_refs: Tuple[str, ...]
    dramatic_function: str

    def __post_init__(self) -> None:
        _require_identifier(self.beat_id, "beat_id")
        if not self.fact_refs:
            raise DirectorContractError("SceneIntentBeat requires at least one fact reference")
        assert_phase_a_text_is_non_execution(self.dramatic_function, "SceneIntentBeat.dramatic_function")


@dataclass(frozen=True)
class SceneIntentContract:
    """The complete S1 diagnosis before spatial blocking is committed."""

    scene_id: str
    scene_priority: str
    dramatic_turn: str
    relationship_state: str
    performance_question: str
    information_goal: str
    scene_objective: str
    dramatic_action: str
    entry_state: str
    exit_state: str
    power_curve: str
    character_actions: Tuple[str, ...]
    beats: Tuple[SceneIntentBeat, ...]
    attention_trajectory: str
    audience_knowledge_delta: str
    character_knowledge_delta: str
    risk_flags: Tuple[str, ...]
    must_preserve: Tuple[str, ...]
    avoid_list: Tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.scene_id, "scene_id")
        for field_name, value in (
            ("scene_priority", self.scene_priority),
            ("dramatic_turn", self.dramatic_turn),
            ("relationship_state", self.relationship_state),
            ("performance_question", self.performance_question),
            ("information_goal", self.information_goal),
            ("scene_objective", self.scene_objective),
            ("dramatic_action", self.dramatic_action),
            ("entry_state", self.entry_state),
            ("exit_state", self.exit_state),
            ("power_curve", self.power_curve),
            ("attention_trajectory", self.attention_trajectory),
            ("audience_knowledge_delta", self.audience_knowledge_delta),
            ("character_knowledge_delta", self.character_knowledge_delta),
        ):
            assert_phase_a_text_is_non_execution(value, field_name)
        for field_name, values in (
            ("character_actions", self.character_actions),
            ("risk_flags", self.risk_flags),
            ("must_preserve", self.must_preserve),
            ("avoid_list", self.avoid_list),
        ):
            if not values:
                raise DirectorContractError(f"{field_name} requires at least one approved statement")
            for item in values:
                assert_phase_a_text_is_non_execution(item, field_name)
        if not self.beats:
            raise DirectorContractError("SceneIntentContract requires fact-linked beats")
        beat_ids = [beat.beat_id for beat in self.beats]
        if len(beat_ids) != len(set(beat_ids)):
            raise DirectorContractError("SceneIntentContract beat IDs must be unique")


@dataclass(frozen=True)
class PhaseAResult:
    """Output of S1: intent and questions only, never a VEC or shot plan."""

    scene_intent: SceneIntentContract
    problem_set: "DirectorProblemSet"

    def __post_init__(self) -> None:
        if self.scene_intent.scene_id != self.problem_set.scene_id:
            raise DirectorContractError("PhaseAResult scene intent and problem set must use the same scene")
        for problem in self.problem_set.problems:
            assert_phase_a_text_is_non_execution(problem.domain, "DirectorProblem.domain")
            assert_phase_a_text_is_non_execution(problem.question, "DirectorProblem.question")


@dataclass(frozen=True)
class DirectorProblem:
    """A question to be judged, not a camera or edit prescription."""

    problem_id: str
    domain: str
    question: str
    tags: Tuple[str, ...] = ()
    priority: str = "normal"

    def __post_init__(self) -> None:
        _require_identifier(self.problem_id, "problem_id")
        _require_identifier(self.domain, "domain")
        _require_identifier(self.question, "question")
        if self.priority not in {"normal", "high"}:
            raise DirectorContractError("DirectorProblem priority must be normal or high")


@dataclass(frozen=True)
class DirectorProblemSet:
    scene_id: str
    problems: Tuple[DirectorProblem, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.scene_id, "scene_id")
        if not self.problems:
            raise DirectorContractError("DirectorProblemSet requires at least one problem")
        ids = [problem.problem_id for problem in self.problems]
        if len(ids) != len(set(ids)):
            raise DirectorContractError("DirectorProblemSet problem IDs must be unique")


@dataclass(frozen=True)
class CapsuleFieldProvenance:
    """Field-level evidence from an offline-normalized source.

    ``unknown`` is deliberately a first-class value.  It prevents a normalizer
    from silently turning an interpretation into an attributed source fact.
    """

    field_name: str
    source_locator: str
    support_level: str

    def __post_init__(self) -> None:
        _require_identifier(self.field_name, "field_name")
        _require_identifier(self.source_locator, "source_locator")
        if self.support_level not in PROVENANCE_SUPPORT_LEVELS:
            raise DirectorContractError("unsupported field provenance level")


@dataclass(frozen=True)
class KnowledgeCapsule:
    """One approved, offline-normalized knowledge unit.

    ``source_locator`` is provenance only.  Full source documents never enter
    this runtime structure.
    """

    capsule_id: str
    source_locator: str
    source_sha256: str
    primary_type: str
    tags: Tuple[str, ...]
    director_problem: str
    dramatic_function: str
    triggers: Tuple[str, ...]
    contraindications: Tuple[str, ...]
    required_context: Tuple[str, ...]
    execution_rules: Tuple[str, ...]
    expected_effect: str
    tradeoffs: Tuple[str, ...]
    alternatives: Tuple[str, ...]
    confidence_level: str
    review_status: str
    allowed_uses: Tuple[str, ...]
    conflicting_capsule_ids: Tuple[str, ...] = ()
    inference_required: bool = False
    inference_prompts: Tuple[str, ...] = ()
    parent_capsule_id: str = ""
    secondary_tags: Tuple[str, ...] = ()
    decision_level: str = "scene"
    source_authorization: str = "project_internal_approved"
    related_capsule_ids: Tuple[str, ...] = ()
    field_provenance: Tuple[CapsuleFieldProvenance, ...] = ()
    inference_fields: Tuple[str, ...] = ()
    anti_pattern_tags: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_identifier(self.capsule_id, "capsule_id")
        _require_identifier(self.source_locator, "source_locator")
        _require_sha256(self.source_sha256, "source_sha256")
        if self.primary_type not in PRIMARY_CAPSULE_TYPES:
            raise DirectorContractError(f"unsupported capsule type: {self.primary_type}")
        if self.confidence_level not in CONFIDENCE_LEVELS:
            raise DirectorContractError("unsupported capsule confidence")
        if self.review_status not in REVIEW_STATUSES:
            raise DirectorContractError("unsupported capsule review status")
        if self.source_authorization not in SOURCE_AUTHORIZATION_STATUSES:
            raise DirectorContractError("unsupported capsule source authorization")
        if self.decision_level not in DECISION_LEVELS:
            raise DirectorContractError("unsupported capsule decision level")
        if not self.director_problem or not self.dramatic_function:
            raise DirectorContractError("capsule must state a director problem and dramatic function")
        if not self.triggers:
            raise DirectorContractError("capsule must state at least one trigger")
        if not self.allowed_uses:
            raise DirectorContractError("capsule must declare allowed uses")
        if self.inference_required and not self.inference_prompts:
            raise DirectorContractError("inference-required capsule needs bounded inference prompts")
        provenance_fields = [item.field_name for item in self.field_provenance]
        if len(provenance_fields) != len(set(provenance_fields)):
            raise DirectorContractError("capsule field provenance entries must be unique")
        unknown_fields = {
            item.field_name
            for item in self.field_provenance
            if item.support_level == "unknown"
        }
        if not set(self.inference_fields).issubset(set(provenance_fields)):
            raise DirectorContractError("inference_fields must have field provenance entries")
        if unknown_fields and not set(self.allowed_uses).issubset(
            {"advisory", "review_only"}
        ):
            raise DirectorContractError(
                "unknown source fields downgrade capsule uses to advisory or review_only"
            )

    @property
    def fingerprint(self) -> str:
        return _canonical_hash(
            {
                "capsule_id": self.capsule_id,
                "source_sha256": self.source_sha256,
                "primary_type": self.primary_type,
                "tags": self.tags,
                "secondary_tags": self.secondary_tags,
                "decision_level": self.decision_level,
                "triggers": self.triggers,
                "contraindications": self.contraindications,
                "execution_rules": self.execution_rules,
                "source_authorization": self.source_authorization,
                "field_provenance": [
                    asdict(item) for item in self.field_provenance
                ],
                "inference_fields": self.inference_fields,
                "confidence_level": self.confidence_level,
                "review_status": self.review_status,
            }
        )

    def runtime_metadata(self) -> Mapping[str, object]:
        """Provide only bounded, approved fields to runtime consumers."""

        return {
            "capsule_id": self.capsule_id,
            "source_locator": self.source_locator,
            "source_sha256": self.source_sha256,
            "source_authorization": self.source_authorization,
            "parent_capsule_id": self.parent_capsule_id,
            "primary_type": self.primary_type,
            "tags": self.tags,
            "secondary_tags": self.secondary_tags,
            "decision_level": self.decision_level,
            "director_problem": self.director_problem,
            "dramatic_function": self.dramatic_function,
            "triggers": self.triggers,
            "contraindications": self.contraindications,
            "required_context": self.required_context,
            "execution_rules": self.execution_rules,
            "expected_effect": self.expected_effect,
            "tradeoffs": self.tradeoffs,
            "alternatives": self.alternatives,
            "confidence_level": self.confidence_level,
            "allowed_uses": self.allowed_uses,
            "related_capsule_ids": self.related_capsule_ids,
            "field_provenance": tuple(
                asdict(item) for item in self.field_provenance
            ),
            "inference_fields": self.inference_fields,
            "anti_pattern_tags": self.anti_pattern_tags,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class CapsuleApplicabilityRecord:
    """Auditable application of one capsule to a single decision field."""

    capsule_id: str
    stage: str
    problem_ids: Tuple[str, ...]
    trigger_evidence: Tuple[str, ...]
    contraindication_check: str
    confidence_level: str
    allowed_use: str
    influenced_fields: Tuple[str, ...]
    rejected: bool = False
    rejection_reason: str = ""

    def __post_init__(self) -> None:
        if self.stage not in {"K1", "K2"}:
            raise DirectorContractError("capsule application stage must be K1 or K2")
        _require_identifier(self.capsule_id, "capsule_id")
        if not self.problem_ids:
            raise DirectorContractError("capsule application must cite a problem")
        if not self.trigger_evidence:
            raise DirectorContractError("capsule application must include trigger evidence")
        if self.confidence_level not in CONFIDENCE_LEVELS:
            raise DirectorContractError("capsule application confidence is invalid")
        _require_identifier(self.allowed_use, "allowed_use")
        if self.rejected and not self.rejection_reason:
            raise DirectorContractError("rejected capsule must record a reason")


@dataclass(frozen=True)
class ConflictDecisionRecord:
    """A Director-authored adjudication; retrieval may expose but never choose."""

    record_id: str
    scene_id: str
    stage: str
    conflict_capsule_ids: Tuple[str, ...]
    selected_capsule_ids: Tuple[str, ...]
    excluded_capsule_ids: Tuple[str, ...]
    priority_source: str
    director_id: str
    selection_reason: str
    exclusion_reason: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("record_id", self.record_id),
            ("scene_id", self.scene_id),
            ("director_id", self.director_id),
            ("selection_reason", self.selection_reason),
            ("exclusion_reason", self.exclusion_reason),
        ):
            _require_identifier(value, field_name)
        if self.stage not in {"K1", "K2"}:
            raise DirectorContractError("conflict decision stage must be K1 or K2")
        if self.priority_source not in CONFLICT_PRIORITY_SOURCES:
            raise DirectorContractError("unsupported conflict priority source")
        conflict_ids = set(self.conflict_capsule_ids)
        selected_ids = set(self.selected_capsule_ids)
        excluded_ids = set(self.excluded_capsule_ids)
        if len(conflict_ids) < 2:
            raise DirectorContractError("conflict decision requires at least two capsules")
        if not selected_ids or not excluded_ids:
            raise DirectorContractError("conflict decision must select and exclude explicitly")
        if selected_ids & excluded_ids:
            raise DirectorContractError("a capsule cannot be both selected and excluded")
        if selected_ids | excluded_ids != conflict_ids:
            raise DirectorContractError(
                "conflict decision must account for every conflicting capsule"
            )


@dataclass(frozen=True)
class DecisionPacket:
    """Small, stage-specific knowledge packet; never a hidden camera template."""

    packet_id: str
    scene_id: str
    stage: str
    primary_capsules: Tuple[KnowledgeCapsule, ...]
    application_records: Tuple[CapsuleApplicabilityRecord, ...]
    conflict_capsule: KnowledgeCapsule | None = None
    anti_pattern_capsule: KnowledgeCapsule | None = None
    conflict_decision: ConflictDecisionRecord | None = None
    blocking_commit_id: str = ""
    no_match: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.packet_id, "packet_id")
        _require_identifier(self.scene_id, "scene_id")
        if self.stage not in {"K1", "K2"}:
            raise DirectorContractError("DecisionPacket stage must be K1 or K2")
        if len(self.primary_capsules) > 3:
            raise DirectorContractError("DecisionPacket may contain at most three primary capsules")
        if self.stage == "K1" and self.blocking_commit_id:
            raise DirectorContractError("K1 packet must not depend on a BlockingCommit")
        if self.stage == "K2" and not self.blocking_commit_id:
            raise DirectorContractError("K2 packet requires a BlockingCommit ID")
        allowed_types = K1_TYPES if self.stage == "K1" else K2_TYPES
        for capsule in self.primary_capsules:
            if capsule.primary_type not in allowed_types:
                raise DirectorContractError(
                    f"{self.stage} cannot carry {capsule.primary_type} capsule {capsule.capsule_id}"
                )
        if self.conflict_capsule and self.conflict_capsule.capsule_id in {
            capsule.capsule_id for capsule in self.primary_capsules
        }:
            raise DirectorContractError("conflict capsule must not duplicate a primary capsule")
        if self.anti_pattern_capsule and not (
            self.anti_pattern_capsule.primary_type == "anti_pattern"
            or self.anti_pattern_capsule.anti_pattern_tags
        ):
            raise DirectorContractError("anti-pattern slot requires an anti-pattern marker")
        if self.no_match and (self.primary_capsules or self.conflict_capsule or self.anti_pattern_capsule):
            raise DirectorContractError("no-match packet cannot include capsules")
        if self.conflict_decision:
            if not self.conflict_capsule:
                raise DirectorContractError("conflict decision requires an exposed conflict capsule")
            if (
                self.conflict_decision.scene_id != self.scene_id
                or self.conflict_decision.stage != self.stage
            ):
                raise DirectorContractError("conflict decision scope must match its packet")
            exposed_ids = {
                self.conflict_capsule.capsule_id,
                *(capsule.capsule_id for capsule in self.primary_capsules),
            }
            if not set(self.conflict_decision.conflict_capsule_ids).issubset(
                exposed_ids
            ):
                raise DirectorContractError(
                    "conflict decision references a capsule absent from the packet"
                )
        primary_ids = {capsule.capsule_id for capsule in self.primary_capsules}
        record_ids = {record.capsule_id for record in self.application_records if not record.rejected}
        if primary_ids != record_ids:
            raise DirectorContractError("every selected primary capsule needs exactly one application record")

    @property
    def fingerprint(self) -> str:
        return _canonical_hash(
            {
                "packet_id": self.packet_id,
                "scene_id": self.scene_id,
                "stage": self.stage,
                "capsules": [capsule.fingerprint for capsule in self.primary_capsules],
                "conflict": self.conflict_capsule.fingerprint if self.conflict_capsule else "",
                "anti": self.anti_pattern_capsule.fingerprint if self.anti_pattern_capsule else "",
                "conflict_decision": (
                    asdict(self.conflict_decision)
                    if self.conflict_decision
                    else {}
                ),
                "blocking_commit_id": self.blocking_commit_id,
                "no_match": self.no_match,
            }
        )


# DDO-3 begins the execution-bearing layer.  These contracts are purposely
# more concrete than Phase A, and are only constructible after a BlockingCommit
# has fixed the motivated spatial relationship.
SCREEN_POSITIONS = frozenset({"screen_left", "screen_center", "screen_right", "offscreen"})
HOLDER_HANDS = frozenset({"left", "right", "both", "none"})
TRANSITION_MODES = frozenset({"hard_cut", "continuous", "match_cut", "dissolve"})
REFERENCE_BINDING_ROLES = frozenset(
    {
        "character_identity", "wardrobe", "blocking_layout", "prop_geometry",
        "scene_layout", "composition_motion",
    }
)
REFERENCE_BINDING_SCOPES = frozenset({"character", "prop", "scene", "segment", "shot"})
REJECTION_CODES = frozenset(
    {
        "BREAKS_BLOCKING",
        "REVEALS_HIDDEN_INFORMATION",
        "REPEATS_PATTERN",
        "EXCEEDS_TARGET_CAPABILITY",
        "WRONG_PACE",
        "CONFLICTS_WITH_APPROVED_FACTS",
    }
)


def _require_tick_interval(start_tick: int, end_tick: int, field_name: str) -> None:
    if not isinstance(start_tick, int) or not isinstance(end_tick, int):
        raise DirectorContractError(f"{field_name} ticks must be integers")
    if start_tick < 0 or end_tick <= start_tick:
        raise DirectorContractError(f"{field_name} must be a positive [start,end) interval")


@dataclass(frozen=True)
class CharacterBlockingState:
    character_id: str
    world_position: str
    screen_position: str
    body_facing: str
    head_facing: str
    gaze_target: str
    movement_vector: str
    visible_body_parts: Tuple[str, ...]
    wardrobe_state_id: str

    def __post_init__(self) -> None:
        _require_identifier(self.character_id, "character_id")
        if self.screen_position not in SCREEN_POSITIONS:
            raise DirectorContractError("character screen_position is invalid")
        for field_name, value in (
            ("world_position", self.world_position),
            ("body_facing", self.body_facing),
            ("head_facing", self.head_facing),
            ("gaze_target", self.gaze_target),
            ("movement_vector", self.movement_vector),
            ("wardrobe_state_id", self.wardrobe_state_id),
        ):
            _require_identifier(value, field_name)
        if not self.visible_body_parts:
            raise DirectorContractError("character visible_body_parts is required")


@dataclass(frozen=True)
class PropBlockingState:
    prop_state_id: str
    prop_id: str
    holder_character_id: str
    holder_hand: str
    grip: str
    visible_surface: str
    front_vector: str
    screen_plane_normal: str
    target_facing: str
    open_closed_state: str
    continuity_owner: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("prop_state_id", self.prop_state_id),
            ("prop_id", self.prop_id),
            ("holder_character_id", self.holder_character_id),
            ("grip", self.grip),
            ("visible_surface", self.visible_surface),
            ("front_vector", self.front_vector),
            ("screen_plane_normal", self.screen_plane_normal),
            ("target_facing", self.target_facing),
            ("open_closed_state", self.open_closed_state),
            ("continuity_owner", self.continuity_owner),
        ):
            _require_identifier(value, field_name)
        if self.holder_hand not in HOLDER_HANDS:
            raise DirectorContractError("prop holder_hand is invalid")
        if self.holder_hand == "none" and self.holder_character_id != "none":
            raise DirectorContractError("unheld prop must use holder_character_id='none'")


@dataclass(frozen=True)
class BlockingBeat:
    beat_id: str
    dramatic_function: str
    character_states: Tuple[CharacterBlockingState, ...]
    prop_states: Tuple[PropBlockingState, ...]
    action_paths: Tuple[str, ...]
    space_control: str
    entry_state_id: str
    exit_state_id: str
    dramatic_reason: str
    constraint_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("beat_id", self.beat_id),
            ("dramatic_function", self.dramatic_function),
            ("space_control", self.space_control),
            ("entry_state_id", self.entry_state_id),
            ("exit_state_id", self.exit_state_id),
            ("dramatic_reason", self.dramatic_reason),
        ):
            _require_identifier(value, field_name)
        if not self.character_states:
            raise DirectorContractError("BlockingBeat requires at least one character state")
        character_ids = [state.character_id for state in self.character_states]
        prop_state_ids = [state.prop_state_id for state in self.prop_states]
        if len(character_ids) != len(set(character_ids)):
            raise DirectorContractError("BlockingBeat character IDs must be unique")
        if len(prop_state_ids) != len(set(prop_state_ids)):
            raise DirectorContractError("BlockingBeat prop state IDs must be unique")
        known_characters = set(character_ids) | {"none"}
        if any(prop.holder_character_id not in known_characters for prop in self.prop_states):
            raise DirectorContractError("prop holder must be present in the same BlockingBeat")
        if not self.action_paths:
            raise DirectorContractError("BlockingBeat requires motivated action paths")
        if not self.constraint_refs:
            raise DirectorContractError("BlockingBeat requires fact or user constraint references")


@dataclass(frozen=True)
class BlockingCommit:
    """Immutable spatial state required before any camera decision enters VEC."""

    commit_id: str
    scene_id: str
    phase_a_fingerprint: str
    beats: Tuple[BlockingBeat, ...]
    entry_state_id: str
    exit_state_id: str
    dramatic_reason: str
    constraint_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("commit_id", self.commit_id),
            ("scene_id", self.scene_id),
            ("phase_a_fingerprint", self.phase_a_fingerprint),
            ("entry_state_id", self.entry_state_id),
            ("exit_state_id", self.exit_state_id),
            ("dramatic_reason", self.dramatic_reason),
        ):
            _require_identifier(value, field_name)
        if not self.beats or not self.constraint_refs:
            raise DirectorContractError("BlockingCommit requires beats and constraint references")
        beat_ids = [beat.beat_id for beat in self.beats]
        if len(beat_ids) != len(set(beat_ids)):
            raise DirectorContractError("BlockingCommit beat IDs must be unique")

    @property
    def fingerprint(self) -> str:
        return _canonical_hash(asdict(self))


@dataclass(frozen=True)
class VisualCurvePoint:
    beat_id: str
    attention_change: str
    information_release: str
    spatial_pressure: str
    visual_density: str
    restraint_or_emphasis: str
    permitted_transition_intent: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("beat_id", self.beat_id),
            ("attention_change", self.attention_change),
            ("information_release", self.information_release),
            ("spatial_pressure", self.spatial_pressure),
            ("visual_density", self.visual_density),
            ("restraint_or_emphasis", self.restraint_or_emphasis),
            ("permitted_transition_intent", self.permitted_transition_intent),
        ):
            _require_identifier(value, field_name)


@dataclass(frozen=True)
class SceneVisualCurve:
    scene_id: str
    blocking_commit_fingerprint: str
    points: Tuple[VisualCurvePoint, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.scene_id, "scene_id")
        _require_identifier(self.blocking_commit_fingerprint, "blocking_commit_fingerprint")
        if not self.points:
            raise DirectorContractError("SceneVisualCurve requires at least one beat point")
        ids = [point.beat_id for point in self.points]
        if len(ids) != len(set(ids)):
            raise DirectorContractError("SceneVisualCurve beat points must be unique")


@dataclass(frozen=True)
class DecisionCandidate:
    option_id: str
    decision_id: str
    decision_kind: str
    proposal_signature: str
    short_summary: str
    evidence_refs: Tuple[str, ...]
    benefit_summary: str
    tradeoff_summary: str
    capability_risk: str
    freedom_corridor: Tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("option_id", self.option_id),
            ("decision_id", self.decision_id),
            ("decision_kind", self.decision_kind),
            ("proposal_signature", self.proposal_signature),
            ("short_summary", self.short_summary),
            ("benefit_summary", self.benefit_summary),
            ("tradeoff_summary", self.tradeoff_summary),
            ("capability_risk", self.capability_risk),
        ):
            _require_identifier(value, field_name)
        if not self.evidence_refs or not self.freedom_corridor:
            raise DirectorContractError("candidate requires evidence and a freedom corridor")


@dataclass(frozen=True)
class RejectedOption:
    option_id: str
    rejection_code: str
    rejection_reason: str

    def __post_init__(self) -> None:
        _require_identifier(self.option_id, "option_id")
        _require_identifier(self.rejection_reason, "rejection_reason")
        if self.rejection_code not in REJECTION_CODES:
            raise DirectorContractError("rejected option must use an approved rejection code")


@dataclass(frozen=True)
class DirectorDecisionRecord:
    decision_id: str
    scope: str
    decision_kind: str
    problem_ids: Tuple[str, ...]
    blocking_commit_fingerprint: str
    selected_option_id: str
    constraint_locked: bool
    selected_capsule_ids: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    decision_summary: str
    tradeoff_summary: str
    rejected_options: Tuple[RejectedOption, ...]
    risk_flags: Tuple[str, ...]
    freedom_corridor: Tuple[str, ...]
    influenced_vec_field_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("decision_id", self.decision_id),
            ("scope", self.scope),
            ("decision_kind", self.decision_kind),
            ("blocking_commit_fingerprint", self.blocking_commit_fingerprint),
            ("selected_option_id", self.selected_option_id),
            ("decision_summary", self.decision_summary),
            ("tradeoff_summary", self.tradeoff_summary),
        ):
            _require_identifier(value, field_name)
        if not self.problem_ids or not self.evidence_refs or not self.freedom_corridor:
            raise DirectorContractError("decision requires problems, evidence, and a freedom corridor")
        if len(self.rejected_options) > 2:
            raise DirectorContractError("a decision may record at most two rejected alternatives")
        rejected_ids = [item.option_id for item in self.rejected_options]
        if self.selected_option_id in rejected_ids or len(rejected_ids) != len(set(rejected_ids)):
            raise DirectorContractError("selected and rejected options must be distinct")


@dataclass(frozen=True)
class GenerationSegment:
    segment_id: str
    start_tick: int
    end_tick: int
    shot_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.segment_id, "segment_id")
        _require_tick_interval(self.start_tick, self.end_tick, "GenerationSegment")
        if self.start_tick != 0:
            raise DirectorContractError("GenerationSegment must use a local timeline beginning at tick 0")
        if not self.shot_ids or len(self.shot_ids) != len(set(self.shot_ids)):
            raise DirectorContractError("GenerationSegment requires unique shot IDs")


@dataclass(frozen=True)
class VisualShot:
    shot_id: str
    segment_id: str
    start_tick: int
    end_tick: int
    dramatic_function: str
    attention_target: str
    information_action: str
    blocking_beat_id: str
    axis_id: str
    camera_side: str
    screen_order: Tuple[str, ...]
    shot_size: str
    focal_intent: str
    camera_pose: str
    camera_motion: str
    composition: str
    lighting: str
    performance: str
    gaze_targets: Tuple[str, ...]
    prop_state_ids: Tuple[str, ...]
    dialogue_event_ids: Tuple[str, ...]
    start_state_id: str
    end_state_id: str
    cut_in_reason: str
    cut_out_reason: str
    selected_capsule_ids: Tuple[str, ...]
    freedom_corridor: Tuple[str, ...]
    decision_id: str
    # This is a non-creative safety invariant. B1 may never opt out of it;
    # omission still materializes the safe local default.
    mirror_flip_forbidden: Literal[True] = True

    def __post_init__(self) -> None:
        for field_name, value in (
            ("shot_id", self.shot_id),
            ("segment_id", self.segment_id),
            ("dramatic_function", self.dramatic_function),
            ("attention_target", self.attention_target),
            ("information_action", self.information_action),
            ("blocking_beat_id", self.blocking_beat_id),
            ("axis_id", self.axis_id),
            ("camera_side", self.camera_side),
            ("shot_size", self.shot_size),
            ("focal_intent", self.focal_intent),
            ("camera_pose", self.camera_pose),
            ("camera_motion", self.camera_motion),
            ("composition", self.composition),
            ("lighting", self.lighting),
            ("performance", self.performance),
            ("start_state_id", self.start_state_id),
            ("end_state_id", self.end_state_id),
            ("cut_in_reason", self.cut_in_reason),
            ("cut_out_reason", self.cut_out_reason),
            ("decision_id", self.decision_id),
        ):
            _require_identifier(value, field_name)
        _require_tick_interval(self.start_tick, self.end_tick, "VisualShot")
        if not self.screen_order or not self.gaze_targets or not self.freedom_corridor:
            raise DirectorContractError("VisualShot requires screen order, gaze targets, and freedom corridor")
        if not self.mirror_flip_forbidden:
            raise DirectorContractError("VisualShot must explicitly forbid mirror flipping")


@dataclass(frozen=True)
class InternalBoundary:
    boundary_id: str
    segment_id: str
    from_shot_id: str
    to_shot_id: str
    mode: str
    reason: str
    decision_id: str
    evidence_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("boundary_id", self.boundary_id),
            ("segment_id", self.segment_id),
            ("from_shot_id", self.from_shot_id),
            ("to_shot_id", self.to_shot_id),
            ("reason", self.reason),
            ("decision_id", self.decision_id),
        ):
            _require_identifier(value, field_name)
        if self.mode not in TRANSITION_MODES:
            raise DirectorContractError("boundary transition mode is invalid")
        if not self.evidence_refs:
            raise DirectorContractError("boundary requires decision evidence")


@dataclass(frozen=True)
class DialogueEvent:
    event_id: str
    segment_id: str
    character_id: str
    voice_asset_id: str
    start_tick: int
    end_tick: int
    text: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("event_id", self.event_id),
            ("segment_id", self.segment_id),
            ("character_id", self.character_id),
            ("voice_asset_id", self.voice_asset_id),
            ("text", self.text),
        ):
            _require_identifier(value, field_name)
        _require_tick_interval(self.start_tick, self.end_tick, "DialogueEvent")


@dataclass(frozen=True)
class ReferenceBindingRequirement:
    """A VEC-owned asset responsibility, independent of platform upload order."""

    requirement_id: str
    role: str
    scope_kind: str
    scope_id: str
    minimum_priority: int

    def __post_init__(self) -> None:
        for field_name, value in (
            ("requirement_id", self.requirement_id),
            ("scope_id", self.scope_id),
        ):
            _require_identifier(value, field_name)
        if self.role not in REFERENCE_BINDING_ROLES:
            raise DirectorContractError("VEC reference requirement role is invalid")
        if self.scope_kind not in REFERENCE_BINDING_SCOPES:
            raise DirectorContractError("VEC reference requirement scope is invalid")
        if not isinstance(self.minimum_priority, int) or self.minimum_priority < 1:
            raise DirectorContractError("VEC reference requirement priority must be positive")


@dataclass(frozen=True)
class VisualExecutionDraft:
    """B1-only execution output, deliberately excluding an accepted B0 copy.

    The text model receives B0 as read-only input.  It must not re-author or
    repeat it in B1.  Local materialization below injects the exact accepted
    BlockingCommit into the final VEC, where all cross-stage invariants remain
    fail-closed.
    """

    contract_id: str
    schema_version: str
    scene_id: str
    source_fact_hashes: Tuple[str, ...]
    phase_a_fingerprint: str
    visual_curve: SceneVisualCurve
    decisions: Tuple[DirectorDecisionRecord, ...]
    segments: Tuple[GenerationSegment, ...]
    shots: Tuple[VisualShot, ...]
    boundaries: Tuple[InternalBoundary, ...]
    dialogue_events: Tuple[DialogueEvent, ...]
    reference_binding_requirements: Tuple[ReferenceBindingRequirement, ...]
    final_handoff: str


@dataclass(frozen=True)
class VisualExecutionContract:
    """The local, machine-readable creative source for both projections."""

    contract_id: str
    schema_version: str
    scene_id: str
    source_fact_hashes: Tuple[str, ...]
    phase_a_fingerprint: str
    blocking_commit: BlockingCommit
    visual_curve: SceneVisualCurve
    decisions: Tuple[DirectorDecisionRecord, ...]
    segments: Tuple[GenerationSegment, ...]
    shots: Tuple[VisualShot, ...]
    boundaries: Tuple[InternalBoundary, ...]
    dialogue_events: Tuple[DialogueEvent, ...]
    reference_binding_requirements: Tuple[ReferenceBindingRequirement, ...]
    final_handoff: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("contract_id", self.contract_id),
            ("schema_version", self.schema_version),
            ("scene_id", self.scene_id),
            ("phase_a_fingerprint", self.phase_a_fingerprint),
            ("final_handoff", self.final_handoff),
        ):
            _require_identifier(value, field_name)
        if self.scene_id != self.blocking_commit.scene_id:
            raise DirectorContractError("VEC scene must match its BlockingCommit")
        if self.phase_a_fingerprint != self.blocking_commit.phase_a_fingerprint:
            raise DirectorContractError("VEC must bind the same Phase A fingerprint as BlockingCommit")
        if self.visual_curve.scene_id != self.scene_id:
            raise DirectorContractError("VEC visual curve scene mismatch")
        if self.visual_curve.blocking_commit_fingerprint != self.blocking_commit.fingerprint:
            raise DirectorContractError("visual curve must cite the verified BlockingCommit")
        if not self.source_fact_hashes:
            raise DirectorContractError("VEC requires source fact hashes")
        for value in self.source_fact_hashes:
            _require_sha256(value, "source_fact_hash")
        if not self.decisions or not self.segments or not self.shots:
            raise DirectorContractError("VEC requires decisions, local segments, and shots")
        commit_hash = self.blocking_commit.fingerprint
        if any(record.blocking_commit_fingerprint != commit_hash for record in self.decisions):
            raise DirectorContractError("camera/execution decision precedes or mismatches BlockingCommit")
        beat_ids = {beat.beat_id for beat in self.blocking_commit.beats}
        curve_ids = {point.beat_id for point in self.visual_curve.points}
        if not curve_ids.issubset(beat_ids):
            raise DirectorContractError("visual curve references an unknown blocking beat")
        decision_ids = [record.decision_id for record in self.decisions]
        shot_ids = [shot.shot_id for shot in self.shots]
        segment_ids = [segment.segment_id for segment in self.segments]
        dialogue_ids = [event.event_id for event in self.dialogue_events]
        if any(len(values) != len(set(values)) for values in (decision_ids, shot_ids, segment_ids, dialogue_ids)):
            raise DirectorContractError("VEC IDs must be unique within their type")
        decision_set = set(decision_ids)
        segment_map = {segment.segment_id: segment for segment in self.segments}
        shot_map = {shot.shot_id: shot for shot in self.shots}
        prop_state_ids = {
            prop.prop_state_id for beat in self.blocking_commit.beats for prop in beat.prop_states
        }
        character_ids = {
            state.character_id for beat in self.blocking_commit.beats for state in beat.character_states
        }
        prop_ids = {
            prop.prop_id for beat in self.blocking_commit.beats for prop in beat.prop_states
        }
        requirement_ids = [item.requirement_id for item in self.reference_binding_requirements]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise DirectorContractError("VEC reference requirement IDs must be unique")
        requirement_pairs = {
            (item.role, item.scope_kind, item.scope_id) for item in self.reference_binding_requirements
        }
        for character_id in character_ids:
            for role in ("character_identity", "wardrobe"):
                if (role, "character", character_id) not in requirement_pairs:
                    raise DirectorContractError("VEC must require character identity and wardrobe bindings")
        for prop_id in prop_ids:
            if ("prop_geometry", "prop", prop_id) not in requirement_pairs:
                raise DirectorContractError("VEC must require prop geometry bindings")
        if ("scene_layout", "scene", self.scene_id) not in requirement_pairs:
            raise DirectorContractError("VEC must require a scene layout binding")
        for shot in self.shots:
            if shot.blocking_beat_id not in beat_ids or shot.decision_id not in decision_set:
                raise DirectorContractError("shot must cite a BlockingCommit beat and decision")
            if shot.segment_id not in segment_map:
                raise DirectorContractError("shot must belong to a declared local segment")
            segment = segment_map[shot.segment_id]
            if not (segment.start_tick <= shot.start_tick < shot.end_tick <= segment.end_tick):
                raise DirectorContractError("shot tick interval must stay inside its local segment")
            if not set(shot.prop_state_ids).issubset(prop_state_ids):
                raise DirectorContractError("shot references a prop state absent from BlockingCommit")
            if not set(shot.dialogue_event_ids).issubset(set(dialogue_ids)):
                raise DirectorContractError("shot references unknown dialogue events")
        if {shot_id for segment in self.segments for shot_id in segment.shot_ids} != set(shot_ids):
            raise DirectorContractError("segments must cover each VEC shot exactly once")
        if any(
            shot_id not in shot_map or shot_map[shot_id].segment_id != segment.segment_id
            for segment in self.segments for shot_id in segment.shot_ids
        ):
            raise DirectorContractError("segment shot list disagrees with shot ownership")
        for event in self.dialogue_events:
            if event.segment_id not in segment_map:
                raise DirectorContractError("dialogue event must belong to a local segment")
            segment = segment_map[event.segment_id]
            if not (segment.start_tick <= event.start_tick < event.end_tick <= segment.end_tick):
                raise DirectorContractError("dialogue event must stay inside its local segment")
        boundary_ids = [boundary.boundary_id for boundary in self.boundaries]
        if len(boundary_ids) != len(set(boundary_ids)):
            raise DirectorContractError("VEC boundary IDs must be unique")
        for boundary in self.boundaries:
            if boundary.decision_id not in decision_set:
                raise DirectorContractError("boundary must cite a decision")
            if boundary.from_shot_id not in shot_map or boundary.to_shot_id not in shot_map:
                raise DirectorContractError("boundary must connect declared shots")
            first, second = shot_map[boundary.from_shot_id], shot_map[boundary.to_shot_id]
            if first.segment_id != boundary.segment_id or second.segment_id != boundary.segment_id:
                raise DirectorContractError("internal boundary cannot cross local segments")
            if first.end_tick != second.start_tick:
                raise DirectorContractError("internal boundary must connect adjacent shot intervals")

    @property
    def fingerprint(self) -> str:
        return _canonical_hash(asdict(self))


@dataclass(frozen=True)
class PhaseBResult:
    """Locally materialized B1 result after validated K2 and B0."""

    blocking_commit: BlockingCommit
    visual_curve: SceneVisualCurve
    candidates: Tuple[DecisionCandidate, ...]
    decisions: Tuple[DirectorDecisionRecord, ...]
    visual_execution_contract: VisualExecutionContract

    def __post_init__(self) -> None:
        vec = self.visual_execution_contract
        if vec.blocking_commit.fingerprint != self.blocking_commit.fingerprint:
            raise DirectorContractError("Phase B VEC must bind its returned BlockingCommit")
        if vec.visual_curve != self.visual_curve or vec.decisions != self.decisions:
            raise DirectorContractError("Phase B VEC must use the exact selected curve and decisions")
        candidate_map = {candidate.option_id: candidate for candidate in self.candidates}
        if len(candidate_map) != len(self.candidates):
            raise DirectorContractError("candidate option IDs must be unique")
        decision_map = {decision.decision_id: decision for decision in self.decisions}
        for decision in self.decisions:
            selected = candidate_map.get(decision.selected_option_id)
            if selected is None or selected.decision_id != decision.decision_id:
                raise DirectorContractError("each decision must select a candidate in its own scope")
            signatures = {selected.proposal_signature}
            for rejected in decision.rejected_options:
                candidate = candidate_map.get(rejected.option_id)
                if candidate is None or candidate.decision_id != decision.decision_id:
                    raise DirectorContractError("rejected option must be a real candidate in the same decision")
                if candidate.proposal_signature in signatures:
                    raise DirectorContractError("rejected alternatives must be genuinely distinct")
                signatures.add(candidate.proposal_signature)


@dataclass(frozen=True)
class PhaseBExecutionDraft:
    """The exact B1 text-model contract, without duplicate BlockingCommit data."""

    visual_curve: SceneVisualCurve
    candidates: Tuple[DecisionCandidate, ...]
    decisions: Tuple[DirectorDecisionRecord, ...]
    visual_execution_draft: VisualExecutionDraft


def materialize_phase_b_result(
    *,
    blocking_commit: BlockingCommit,
    execution_draft: PhaseBExecutionDraft,
) -> PhaseBResult:
    """Inject accepted B0 locally and validate the complete final VEC.

    This is the only permitted B1-to-VEC boundary.  A model cannot substitute,
    mirror, or mutate B0 while producing camera/execution decisions.
    """

    draft = execution_draft.visual_execution_draft
    vec = VisualExecutionContract(
        contract_id=draft.contract_id,
        schema_version=draft.schema_version,
        scene_id=draft.scene_id,
        source_fact_hashes=draft.source_fact_hashes,
        phase_a_fingerprint=draft.phase_a_fingerprint,
        blocking_commit=blocking_commit,
        visual_curve=draft.visual_curve,
        decisions=draft.decisions,
        segments=draft.segments,
        shots=draft.shots,
        boundaries=draft.boundaries,
        dialogue_events=draft.dialogue_events,
        reference_binding_requirements=draft.reference_binding_requirements,
        final_handoff=draft.final_handoff,
    )
    return PhaseBResult(
        blocking_commit=blocking_commit,
        visual_curve=execution_draft.visual_curve,
        candidates=execution_draft.candidates,
        decisions=execution_draft.decisions,
        visual_execution_contract=vec,
    )
