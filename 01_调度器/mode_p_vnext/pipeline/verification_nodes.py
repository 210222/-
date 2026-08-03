"""v3.1 Gate/DP/media verification control nodes.

Persistent evidence types are imported from ``domain.evidence`` and are never
redeclared here.  Model/provider outputs remain non-authoritative Draft DTOs;
local deterministic code creates every canonical ID, digest, binding, and
status transition.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, fields as dataclass_fields

from mode_p_vnext.domain.artifact import (
    ArtifactKind,
    DomainValidationError,
    SourceRef,
    canonical_sha256,
    require_sha256,
)
from mode_p_vnext.domain.evidence import (
    DPReviewVerdict,
    DeterministicGateResult,
    FrameEvidence,
    FrameEvidencePlan,
    IndependentDPReviewResult,
    MediaEvidence,
    MediaRunRecord,
    OutcomeAttribution,
    OwnerApprovalDecision,
    OwnerApprovalRecord,
    ReviewPacket,
    RevisionFailureType,
    RevisionRequest,
    VisualVerificationResult,
)
from mode_p_vnext.domain.facts import FactRegistry, require_opaque_id
from mode_p_vnext.domain.ids import IdFactory
from mode_p_vnext.domain.projection import ProjectionAST
from mode_p_vnext.domain.vec import VisualExecutionContract
from mode_p_vnext.ports.media_renderer import MediaRenderOutput, MediaRenderRequest
from mode_p_vnext.ports.media_verifier import MediaVerificationOutput
from mode_p_vnext.services.deterministic_gates import validate_gate0_result
from mode_p_vnext.services.projection_compiler import StoryboardProjection, VideoProjection
from mode_p_vnext.services.revision_router import RevisionScope, validate_revision_request


TEXT_VALIDATED = "TEXT_VALIDATED"
VISUAL_EVIDENCED = "VISUAL_EVIDENCED"
OWNER_APPROVED = "OWNER_APPROVED"


class VerificationStatus(str, enum.Enum):
    TEXT_VALIDATED = TEXT_VALIDATED
    VISUAL_EVIDENCED = VISUAL_EVIDENCED
    OWNER_APPROVED = OWNER_APPROVED


class AttributionLayer(str, enum.Enum):
    ASSEMBLY = "ASSEMBLY"
    GATE0 = "GATE0"
    PROJECTION = "PROJECTION"
    DP = "DP"
    MEDIA_RENDER = "MEDIA_RENDER"
    MEDIA_VERIFY = "MEDIA_VERIFY"
    DIRECTOR = "DIRECTOR"


def _text_tuple(value: tuple[str, ...], field_name: str, *, required: bool) -> tuple[str, ...]:
    values = tuple(value)
    if (required and not values) or any(
        not isinstance(item, str) or not item.strip() for item in values
    ):
        raise DomainValidationError(f"{field_name} must contain non-empty text")
    if len(values) != len(set(values)):
        raise DomainValidationError(f"{field_name} must not contain duplicates")
    return values


def _attribution(
    *,
    layer: AttributionLayer,
    reason: str,
    supporting_evidence: tuple[str, ...],
    confidence: str = "high",
) -> OutcomeAttribution:
    return OutcomeAttribution(
        result_id=f"attr:{canonical_sha256((layer, reason, supporting_evidence))}",
        cause=f"{layer.value}|{reason}",
        confidence=confidence,
        supporting_evidence=supporting_evidence,
    )


def gate0_attribution(result: DeterministicGateResult) -> OutcomeAttribution:
    if type(result) is not DeterministicGateResult or result.passed:
        raise DomainValidationError("Gate 0 attribution requires a failed canonical result")
    return _attribution(
        layer=AttributionLayer.GATE0,
        reason=",".join(result.failed_check_ids),
        supporting_evidence=(result.result_id, *result.target_artifact_ids),
    )


def gate_result_source_ref(result: DeterministicGateResult) -> SourceRef:
    """Expose exactly the Gate result reference present in a ReviewPacket."""

    if type(result) is not DeterministicGateResult:
        raise DomainValidationError("result must be a canonical DeterministicGateResult")
    return SourceRef(source_id=result.result_id, digest=canonical_sha256(result))


def media_render_attribution(
    *, scene_id: str, renderer_version: str, reason: str
) -> OutcomeAttribution:
    return _attribution(
        layer=AttributionLayer.MEDIA_RENDER,
        reason=reason,
        supporting_evidence=(scene_id, renderer_version),
    )


def media_verify_attribution(
    *, scene_id: str, verifier_version: str, reason: str
) -> OutcomeAttribution:
    return _attribution(
        layer=AttributionLayer.MEDIA_VERIFY,
        reason=reason,
        supporting_evidence=(scene_id, verifier_version),
    )


def layer_of(attribution: OutcomeAttribution) -> AttributionLayer | None:
    head = attribution.cause.split("|", 1)[0].strip().upper()
    return next((item for item in AttributionLayer if item.value == head), None)


def ladder_status(
    *,
    text_ceiling: str,
    verification: VisualVerificationResult | None,
    approval: OwnerApprovalRecord | None,
) -> VerificationStatus:
    """Compute the strict text -> real-media -> explicit-owner ladder."""

    if text_ceiling != TEXT_VALIDATED:
        raise DomainValidationError(
            f"text pipeline claim ceiling must be {TEXT_VALIDATED}"
        )
    if verification is None:
        if approval is not None:
            raise DomainValidationError("approval cannot exist without visual verification")
        return VerificationStatus.TEXT_VALIDATED
    if type(verification) is not VisualVerificationResult or not verification.passed:
        raise DomainValidationError("VISUAL_EVIDENCED requires a passed canonical verification")
    if approval is None:
        return VerificationStatus.VISUAL_EVIDENCED
    if type(approval) is not OwnerApprovalRecord:
        raise DomainValidationError("approval must be a canonical OwnerApprovalRecord")
    if approval.decision is not OwnerApprovalDecision.APPROVED:
        raise DomainValidationError("owner decision is not APPROVED")
    if approval.visual_verification_artifact_id != verification.verification_id:
        raise DomainValidationError("owner approval does not bind the exact verification")
    return VerificationStatus.OWNER_APPROVED


def _local_id(
    factory: IdFactory,
    *,
    kind: ArtifactKind,
    episode_id: str,
    scene_id: str,
    stage: str,
    value: object,
    ordinal: int = 0,
) -> str:
    return factory.create(
        artifact_kind=kind,
        episode_id=episode_id,
        scene_id=scene_id,
        stage=stage,
        input_digest=canonical_sha256(value),
        ordinal=ordinal,
    )


def _require_factory(factory: IdFactory, program_version: str) -> None:
    if not isinstance(factory, IdFactory) or factory.program_version != program_version:
        raise DomainValidationError("IdFactory must match program_version")


def build_media_run_record(
    *,
    request: MediaRenderRequest,
    output: MediaRenderOutput,
    id_factory: IdFactory,
    episode_id: str,
    program_version: str,
) -> MediaRunRecord:
    """Turn a provider Draft into a locally identified canonical run record."""

    _require_factory(id_factory, program_version)
    if type(request) is not MediaRenderRequest or type(output) is not MediaRenderOutput:
        raise DomainValidationError("media run inputs must use exact port DTOs")
    request_digest = canonical_sha256(request)
    run_id = _local_id(
        id_factory,
        kind=ArtifactKind.MEDIA_RUN_RECORD,
        episode_id=episode_id,
        scene_id=request.scene_id,
        stage="media:run",
        value={"request": request, "output": output},
    )
    return MediaRunRecord(
        run_id=run_id,
        provider=output.provider,
        request_digest=request_digest,
        output_refs=output.output_refs,
    )


def build_media_evidence(
    *,
    plan: FrameEvidencePlan,
    media_run: MediaRunRecord,
    frames: tuple[FrameEvidence, ...],
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    program_version: str,
) -> MediaEvidence:
    _require_factory(id_factory, program_version)
    supplied_frames = tuple(frames)
    if not all(type(item) is FrameEvidence for item in supplied_frames):
        raise DomainValidationError("frame evidence must use exact FrameEvidence values")
    frame_by_index = {item.frame_index: item for item in supplied_frames}
    if (
        len(supplied_frames) != len(plan.frame_indices)
        or len(frame_by_index) != len(supplied_frames)
        or set(frame_by_index) != set(plan.frame_indices)
    ):
        raise DomainValidationError("frame evidence must cover the exact deterministic plan")
    frame_values = tuple(frame_by_index[index] for index in plan.frame_indices)
    if any(item.media_run_id != media_run.run_id for item in frame_values):
        raise DomainValidationError("frame evidence must bind the exact media run")
    evidence_id = _local_id(
        id_factory,
        kind=ArtifactKind.MEDIA_EVIDENCE,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="media:evidence",
        value={"plan": plan, "run": media_run, "frames": frame_values},
    )
    return MediaEvidence(
        evidence_id=evidence_id,
        frame_evidence_plan_artifact_id=plan.plan_id,
        media_run_artifact_id=media_run.run_id,
        media_run_id=media_run.run_id,
        frame_evidence=frame_values,
    )


def build_frame_evidence_plan(
    *,
    vec: VisualExecutionContract,
    checks: tuple[str, ...],
    frame_indices: tuple[int, ...],
    id_factory: IdFactory,
    program_version: str,
) -> FrameEvidencePlan:
    """Create the canonical frame plan and its ID under local authority."""

    _require_factory(id_factory, program_version)
    plan_value = {
        "vec_artifact_id": vec.contract_id,
        "checks": tuple(checks),
        "frame_indices": tuple(frame_indices),
    }
    plan_id = _local_id(
        id_factory,
        kind=ArtifactKind.FRAME_EVIDENCE_PLAN,
        episode_id=vec.episode_id,
        scene_id=vec.scene_id,
        stage="media:frame-plan",
        value=plan_value,
    )
    return FrameEvidencePlan(plan_id=plan_id, **plan_value)


def build_visual_verification(
    *,
    vec: VisualExecutionContract,
    plan: FrameEvidencePlan,
    media_run: MediaRunRecord,
    media_evidence: MediaEvidence,
    verifier_output: MediaVerificationOutput,
    id_factory: IdFactory,
    program_version: str,
) -> VisualVerificationResult:
    """Assemble a verifier Draft; no default or text-inferred pass exists."""

    _require_factory(id_factory, program_version)
    if type(verifier_output) is not MediaVerificationOutput:
        raise DomainValidationError("verifier_output must be an exact media verifier DTO")
    if plan.vec_artifact_id != vec.contract_id:
        raise DomainValidationError("frame plan does not bind the supplied VEC")
    expected_plan_id = _local_id(
        id_factory,
        kind=ArtifactKind.FRAME_EVIDENCE_PLAN,
        episode_id=vec.episode_id,
        scene_id=vec.scene_id,
        stage="media:frame-plan",
        value={
            "vec_artifact_id": vec.contract_id,
            "checks": tuple(plan.checks),
            "frame_indices": tuple(plan.frame_indices),
        },
    )
    if plan.plan_id != expected_plan_id:
        raise DomainValidationError("frame plan is not the canonical local plan")
    if media_evidence.media_run_id != media_run.run_id:
        raise DomainValidationError("media evidence does not bind the supplied media run")
    if media_evidence.frame_evidence_plan_artifact_id != plan.plan_id:
        raise DomainValidationError("media evidence does not bind the supplied frame plan")
    if media_evidence.media_run_artifact_id != media_run.run_id:
        raise DomainValidationError("media evidence does not bind the supplied media run artifact")
    expected_evidence_id = _local_id(
        id_factory,
        kind=ArtifactKind.MEDIA_EVIDENCE,
        episode_id=vec.episode_id,
        scene_id=vec.scene_id,
        stage="media:evidence",
        value={
            "plan": plan,
            "run": media_run,
            "frames": tuple(media_evidence.frame_evidence),
        },
    )
    if media_evidence.evidence_id != expected_evidence_id:
        raise DomainValidationError("media evidence is not the canonical local aggregate")
    if tuple(verifier_output.frames) != tuple(media_evidence.frame_evidence):
        raise DomainValidationError("verifier output must bind the canonical MediaEvidence frames")
    if not any(
        media_run.run_id in attribution.supporting_evidence
        for attribution in verifier_output.attributions
    ):
        raise DomainValidationError(
            "media verifier attribution must bind the exact media run"
        )
    verification_id = _local_id(
        id_factory,
        kind=ArtifactKind.VISUAL_VERIFICATION_RESULT,
        episode_id=vec.episode_id,
        scene_id=vec.scene_id,
        stage="media:visual-verification",
        value={
            "vec": vec.contract_id,
            "plan": plan,
            "media_run": media_run,
            "media_evidence": media_evidence,
            "verifier_output": verifier_output,
        },
    )
    return VisualVerificationResult(
        verification_id=verification_id,
        vec_artifact_id=vec.contract_id,
        media_run_id=media_run.run_id,
        passed=verifier_output.passed,
        frame_evidence=verifier_output.frames,
        attributions=verifier_output.attributions,
    )


def build_dp_review_packet(
    *,
    facts: FactRegistry,
    vec: VisualExecutionContract,
    ast: ProjectionAST,
    storyboard: StoryboardProjection,
    video: VideoProjection,
    gate0: DeterministicGateResult,
    episode_direction_artifact_id: str,
    scene_intent_artifact_id: str,
    id_factory: IdFactory,
    program_version: str,
) -> ReviewPacket:
    """Build the minimal, reference-only packet accepted by a fresh DP."""

    _require_factory(id_factory, program_version)
    if type(facts) is not FactRegistry or type(vec) is not VisualExecutionContract:
        raise DomainValidationError("facts and VEC must use exact canonical types")
    if type(ast) is not ProjectionAST or storyboard.ast is not ast or video.ast is not ast:
        raise DomainValidationError("both delivery views must consume the exact ProjectionAST")
    if type(gate0) is not DeterministicGateResult or not gate0.passed:
        raise DomainValidationError("fresh DP cannot start before a passed canonical Gate 0")
    validate_gate0_result(
        result=gate0,
        vec=vec,
        ast=ast,
        storyboard=storyboard,
        video=video,
        id_factory=id_factory,
        program_version=program_version,
    )
    require_opaque_id(episode_direction_artifact_id, "episode_direction_artifact_id")
    require_opaque_id(scene_intent_artifact_id, "scene_intent_artifact_id")
    fact_ids = {item.fact_id for item in facts.facts}
    fact_handles = {item.fact_handle for item in facts.facts}
    if fact_ids != set(vec.source_fact_ids) or fact_handles != set(vec.approved_fact_handles):
        raise DomainValidationError("ReviewPacket fact scope must equal the approved VEC scope")
    capability_digest = canonical_sha256(vec.capability_profile)
    if {
        storyboard.manifest.capability_profile_digest,
        video.manifest.capability_profile_digest,
    } != {capability_digest}:
        raise DomainValidationError("delivery manifests disagree with canonical capability")
    packet_value = {
        "fact_refs": tuple(sorted(fact_handles)),
        "episode_direction_artifact_id": episode_direction_artifact_id,
        "scene_intent_artifact_id": scene_intent_artifact_id,
        "vec_artifact_id": vec.contract_id,
        "projection_artifact_ids": (ast.projection_id,),
        "gate_result_refs": (gate0.result_id,),
        "capability_profile_digest": capability_digest,
    }
    packet_id = _local_id(
        id_factory,
        kind=ArtifactKind.REVIEW_PACKET,
        episode_id=vec.episode_id,
        scene_id=vec.scene_id,
        stage="dp:review-packet",
        value=packet_value,
    )
    return ReviewPacket(packet_id=packet_id, **packet_value)


@dataclass(frozen=True)
class FreshDPContext:
    """Local proof that only one ReviewPacket entered a new isolated session."""

    session_id: str
    review_packet_digest: str
    attempt_ordinal: int
    prior_history_refs: tuple[str, ...] = ()
    forbidden_input_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_opaque_id(self.session_id, "session_id")
        require_sha256(self.review_packet_digest, "review_packet_digest")
        if (
            isinstance(self.attempt_ordinal, bool)
            or not isinstance(self.attempt_ordinal, int)
            or self.attempt_ordinal < 0
        ):
            raise DomainValidationError("attempt_ordinal must be a non-negative integer")
        object.__setattr__(
            self,
            "prior_history_refs",
            _text_tuple(self.prior_history_refs, "prior_history_refs", required=False),
        )
        object.__setattr__(
            self,
            "forbidden_input_refs",
            _text_tuple(self.forbidden_input_refs, "forbidden_input_refs", required=False),
        )


class DPInputBlockedError(DomainValidationError):
    """DP_INPUT_BLOCKED: the proposed session is not fresh or packet-only."""


def start_fresh_dp_context(
    packet: ReviewPacket,
    *,
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    program_version: str,
    attempt_ordinal: int,
) -> FreshDPContext:
    if type(packet) is not ReviewPacket:
        raise DomainValidationError("packet must be the canonical ReviewPacket")
    _require_factory(id_factory, program_version)
    session_id = _local_id(
        id_factory,
        kind=ArtifactKind.DP_REVIEW_RESULT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="dp:fresh-session",
        value=packet,
        ordinal=attempt_ordinal,
    )
    return FreshDPContext(
        session_id=session_id,
        review_packet_digest=canonical_sha256(packet),
        attempt_ordinal=attempt_ordinal,
    )


@dataclass(frozen=True)
class RevisionRequestDraft:
    """The complete DP revision output surface; it contains no IDs or hashes."""

    target_artifact_id: str
    failure_type: RevisionFailureType
    fact_refs: tuple[str, ...]
    field_paths: tuple[str, ...]
    observed_issue: str
    requested_change: str
    evidence_ref_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("target_artifact_id", "observed_issue", "requested_change"):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name).strip():
                raise DomainValidationError(f"{field_name} must be non-empty")
        if not isinstance(self.failure_type, RevisionFailureType):
            raise DomainValidationError("failure_type must be a RevisionFailureType")
        for field_name in ("fact_refs", "field_paths", "evidence_ref_ids"):
            object.__setattr__(
                self,
                field_name,
                _text_tuple(getattr(self, field_name), field_name, required=True),
            )


@dataclass(frozen=True)
class DPReviewDraft:
    verdict: DPReviewVerdict
    finding_codes: tuple[str, ...]
    revision_requests: tuple[RevisionRequestDraft, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.verdict, DPReviewVerdict):
            raise DomainValidationError("verdict must be a DPReviewVerdict")
        findings = _text_tuple(
            self.finding_codes,
            "finding_codes",
            required=self.verdict is DPReviewVerdict.REVISION_REQUIRED,
        )
        requests = tuple(self.revision_requests)
        if not all(type(item) is RevisionRequestDraft for item in requests):
            raise DomainValidationError("revision_requests must contain RevisionRequestDraft")
        if self.verdict is DPReviewVerdict.APPROVED and (findings or requests):
            raise DomainValidationError("READY cannot carry findings or revisions")
        if self.verdict is DPReviewVerdict.REVISION_REQUIRED and not requests:
            raise DomainValidationError("REVISION_REQUIRED must carry a bounded request")
        object.__setattr__(self, "finding_codes", findings)
        object.__setattr__(self, "revision_requests", requests)


@dataclass(frozen=True)
class FreshDPReviewBundle:
    result: IndependentDPReviewResult
    revision_requests: tuple[RevisionRequest, ...]


def assemble_fresh_dp_review(
    *,
    packet: ReviewPacket,
    context: FreshDPContext,
    draft: DPReviewDraft,
    scopes: tuple[RevisionScope, ...],
    allowed_evidence_refs: tuple[SourceRef, ...],
    id_factory: IdFactory,
    episode_id: str,
    scene_id: str,
    program_version: str,
) -> FreshDPReviewBundle:
    """Create canonical DP artifacts or emit DP_INPUT_BLOCKED fail-closed."""

    _require_factory(id_factory, program_version)
    if type(packet) is not ReviewPacket or type(context) is not FreshDPContext:
        raise DomainValidationError("DP assembly requires exact packet and context types")
    if type(draft) is not DPReviewDraft:
        raise DomainValidationError("DP output must be the bounded DPReviewDraft")
    packet_value = {
        item.name: getattr(packet, item.name)
        for item in dataclass_fields(packet)
        if item.name != "packet_id"
    }
    expected_packet_id = _local_id(
        id_factory,
        kind=ArtifactKind.REVIEW_PACKET,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="dp:review-packet",
        value=packet_value,
    )
    expected_session_id = _local_id(
        id_factory,
        kind=ArtifactKind.DP_REVIEW_RESULT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="dp:fresh-session",
        value=packet,
        ordinal=context.attempt_ordinal,
    )
    if (
        packet.packet_id != expected_packet_id
        or context.session_id != expected_session_id
        or context.review_packet_digest != canonical_sha256(packet)
        or context.prior_history_refs
        or context.forbidden_input_refs
    ):
        raise DPInputBlockedError(
            "DP_INPUT_BLOCKED: independent session must contain only the current ReviewPacket"
        )
    refs_by_id = {item.source_id: item for item in allowed_evidence_refs}
    if len(refs_by_id) != len(allowed_evidence_refs):
        raise DomainValidationError("allowed evidence source IDs must be unique")
    if not set(refs_by_id).issubset(packet.gate_result_refs):
        raise DomainValidationError(
            "DP evidence inputs must be references already visible in its ReviewPacket"
        )
    packet_target_ids = {
        packet.episode_direction_artifact_id,
        packet.scene_intent_artifact_id,
        packet.vec_artifact_id,
        *packet.projection_artifact_ids,
    }
    scope_by_target = {item.target_artifact_id: item for item in scopes}
    if len(scope_by_target) != len(scopes):
        raise DomainValidationError("revision scopes must have unique targets")
    if not set(scope_by_target).issubset(packet_target_ids):
        raise DomainValidationError(
            "revision scope target must be explicitly visible in the ReviewPacket"
        )

    revisions: list[RevisionRequest] = []
    for ordinal, item in enumerate(draft.revision_requests):
        if not set(item.fact_refs).issubset(packet.fact_refs):
            raise DomainValidationError("DP revision references facts outside its packet")
        try:
            evidence_refs = tuple(refs_by_id[item_id] for item_id in item.evidence_ref_ids)
        except KeyError as exc:
            raise DomainValidationError("DP revision references unauthorized evidence") from exc
        request_value = {
            "target_artifact_id": item.target_artifact_id,
            "failure_type": item.failure_type,
            "fact_refs": item.fact_refs,
            "field_paths": item.field_paths,
            "observed_issue": item.observed_issue,
            "requested_change": item.requested_change,
            "evidence_refs": evidence_refs,
        }
        request_id = _local_id(
            id_factory,
            kind=ArtifactKind.REVISION_REQUEST,
            episode_id=episode_id,
            scene_id=scene_id,
            stage="dp:revision-request",
            value={"packet_id": packet.packet_id, **request_value},
            ordinal=ordinal,
        )
        request = RevisionRequest(request_id=request_id, **request_value)
        scope = scope_by_target.get(request.target_artifact_id)
        if scope is None:
            raise DomainValidationError("DP revision target is outside local authorization")
        validate_revision_request(
            request,
            scope=scope,
            allowed_fact_refs=packet.fact_refs,
        )
        revisions.append(request)

    independent_context_digest = canonical_sha256(
        {
            "session_id": context.session_id,
            "review_packet_digest": context.review_packet_digest,
            "allowed_input_surface": tuple(item.name for item in dataclass_fields(packet)),
            "prior_history_refs": (),
            "forbidden_input_refs": (),
        }
    )
    result_value = {
        "review_packet_artifact_id": packet.packet_id,
        "verdict": draft.verdict,
        "finding_codes": draft.finding_codes,
        "revision_request_artifact_ids": tuple(item.request_id for item in revisions),
        "independent_context_digest": independent_context_digest,
    }
    result_id = _local_id(
        id_factory,
        kind=ArtifactKind.DP_REVIEW_RESULT,
        episode_id=episode_id,
        scene_id=scene_id,
        stage="dp:review-result",
        value=result_value,
    )
    result = IndependentDPReviewResult(result_id=result_id, **result_value)
    return FreshDPReviewBundle(result=result, revision_requests=tuple(revisions))


__all__ = [
    "AttributionLayer",
    "DPInputBlockedError",
    "DPReviewDraft",
    "DPReviewVerdict",
    "DeterministicGateResult",
    "FrameEvidence",
    "FrameEvidencePlan",
    "FreshDPContext",
    "FreshDPReviewBundle",
    "IndependentDPReviewResult",
    "MediaEvidence",
    "MediaRunRecord",
    "OutcomeAttribution",
    "OwnerApprovalDecision",
    "OwnerApprovalRecord",
    "ReviewPacket",
    "RevisionFailureType",
    "RevisionRequest",
    "RevisionRequestDraft",
    "VerificationStatus",
    "VisualVerificationResult",
    "assemble_fresh_dp_review",
    "build_dp_review_packet",
    "build_media_evidence",
    "build_frame_evidence_plan",
    "build_media_run_record",
    "build_visual_verification",
    "gate0_attribution",
    "gate_result_source_ref",
    "ladder_status",
    "layer_of",
    "media_render_attribution",
    "media_verify_attribution",
    "start_fresh_dp_context",
]
