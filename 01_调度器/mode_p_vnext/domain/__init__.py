"""Canonical, pure MODE:P vNext domain schemas (architecture v2.1)."""

from .artifact import (
    ArtifactEnvelope,
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    ValidationStatus,
)
from .blocking import (
    BlockingBeat,
    BlockingBeatDraft,
    BlockingCommit,
    BlockingDraft,
)
from .decisions import (
    DecisionBasis,
    DecisionDraft,
    DirectorDecision,
    VisualCurvePoint,
    VisualCurvePointDraft,
)
from .direction import EpisodeDirectionDraft, SceneIntentDraft
from .ids import IdFactory
from .knowledge import (
    KnowledgeCapsuleV2,
    KnowledgeDecisionEntry,
    KnowledgeDecisionView,
    KnowledgeSnapshot,
    KnowledgeStage,
)
from .projection import ProjectionAST, ProjectionManifest, ProjectionNode
from .time import (
    CanonicalTimeline,
    GenerationSegmentTimeline,
    TickRange,
    TimelinePlacement,
)
from .vec import (
    AudioEvent,
    ExecutionDesignDraft,
    GenerationSegment,
    ReferenceRequirement,
    ShotBoundary,
    ShotDesignDraft,
    StoryboardRole,
    VisualBeat,
    VisualBeatDraft,
    VisualBeatPhase,
    VisualExecutionContract,
    VisualShot,
    VoiceRequirement,
)

__all__ = (
    "ArtifactEnvelope",
    "ArtifactKind",
    "AudioEvent",
    "BlockingBeat",
    "BlockingBeatDraft",
    "BlockingCommit",
    "BlockingDraft",
    "CanonicalTimeline",
    "DecisionBasis",
    "DecisionDraft",
    "DirectorDecision",
    "DomainValidationError",
    "EpisodeDirectionDraft",
    "ExecutionDesignDraft",
    "GenerationSegment",
    "GenerationSegmentTimeline",
    "IdFactory",
    "KnowledgeCapsuleV2",
    "KnowledgeDecisionEntry",
    "KnowledgeDecisionView",
    "KnowledgeSnapshot",
    "KnowledgeStage",
    "ProjectionAST",
    "ProjectionManifest",
    "ProjectionNode",
    "ReferenceRequirement",
    "SceneIntentDraft",
    "ShotBoundary",
    "ShotDesignDraft",
    "SourceRef",
    "StoryboardRole",
    "TickRange",
    "TimelinePlacement",
    "ValidationStatus",
    "VisualBeat",
    "VisualBeatDraft",
    "VisualBeatPhase",
    "VisualCurvePoint",
    "VisualCurvePointDraft",
    "VisualExecutionContract",
    "VisualShot",
    "VoiceRequirement",
)
