"""Engineering-only command line interface for MODE:P vNext.

The historical ``shadow`` command remains structural-only.  A8 adds one
separate ``text-shadow`` composition that invokes only the structured text
Director port and a fresh packet-only DP port; it never invokes v4, a renderer,
a verifier, a media adapter, or a production switch.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from . import __version__
from .adapters.model.claude_deepseek import ClaudeDeepSeekStructuredAdapter
from .adapters.storage.shadow_run import TextShadowStorage, TextShadowStorageError
from .canonical_serialization import canonical_json_dumps
from .domain.artifact import ArtifactEnvelope, ArtifactKind, DomainValidationError, canonical_sha256
from .domain.ids import IdFactory
from .domain.time import GenerationCapabilityProfile
from .pipeline.episode_nodes import EpisodeNodeError, run_episode_direction, run_scene_intent
from .pipeline.graph import NodeSpec, StateGraph
from .pipeline.ingest_nodes import IngestNodeError, compile_i0_prompts, normalize_raw_source, run_i0_ingest
from .pipeline.scene_nodes import (
    NativeFreshDPReviewer,
    SceneNodeError,
    run_blocking,
    run_dp_review,
    run_execution_design,
    run_gate0_artifact,
    run_k1_snapshot,
    run_k2_snapshot,
    run_projection,
    run_vec_assembly,
)
from .ports.structured_text import GenerationPolicy
from .prompts.compiler import PromptCompiler
from .runtime.session import RunSessionError
from .session_state import (
    InvalidStateTransition,
    PersistentSession,
    SessionStateError,
)
from .shadow_entry import ShadowConfig, ShadowError, run_shadow


def _emit(value: Mapping[str, Any], stream: Any | None = None) -> None:
    """Emit through the current process stream, including embedded CLI callers."""

    (sys.stdout if stream is None else stream).write(canonical_json_dumps(dict(value)) + "\n")


def _parse_hashes(items: Optional[Iterable[str]]) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for item in items or ():
        if "=" not in item:
            raise SessionStateError(
                "artifact hash must use NAME=64-character-sha256 syntax"
            )
        name, digest = item.split("=", 1)
        if not name or not digest:
            raise SessionStateError("artifact hash name and digest are required")
        parsed[name] = digest
    return parsed


def _snapshot_response(snapshot: Any) -> Dict[str, Any]:
    return {"status": "OK", "session": snapshot.to_dict()}


def _session_init(args: argparse.Namespace) -> Dict[str, Any]:
    session = PersistentSession.create(
        Path(args.session_dir),
        args.episode_id,
        args.scene_id or "",
        scope=args.scope,
        owner=args.actor,
        initial_state=args.initial_state,
        correlation_id=args.correlation_id,
        artifact_hashes=_parse_hashes(args.artifact_hash),
    )
    return _snapshot_response(session.status(owner=args.actor))


def _session_status(args: argparse.Namespace) -> Dict[str, Any]:
    session = PersistentSession.open(Path(args.session_dir), owner=args.actor)
    return _snapshot_response(session.status(owner=args.actor))


def _session_transition(args: argparse.Namespace) -> Dict[str, Any]:
    session = PersistentSession.open(Path(args.session_dir), owner=args.actor)
    snapshot = session.transition(
        args.to,
        actor=args.actor,
        reason_code=args.reason_code,
        input_commit_id=args.input_commit_id,
        output_commit_id=args.output_commit_id,
        correlation_id=args.correlation_id,
        artifact_hashes=_parse_hashes(args.artifact_hash)
        if args.artifact_hash
        else None,
    )
    return _snapshot_response(snapshot)


def _shadow(args: argparse.Namespace) -> Dict[str, Any]:
    result = run_shadow(
        ShadowConfig(
            episode_script_path=args.script,
            session_dir=args.session_dir,
            episode_id=args.episode_id or "",
            run_id=args.run_id or "",
        )
    )
    return {"status": "OK", "shadow": result.to_dict()}


# A8's program identity is intentionally independent from test program IDs and
# from the historical structural-shadow implementation above.
_A8_PROGRAM_VERSION = "mode-p-vnext-a8-v3.0"
_A8_NODE_ORDER = (
    "I0", "E0", "S1", "K1", "B0", "K2", "B1", "VEC", "Projection", "G0", "DP",
)


class A8TextShadowError(RuntimeError):
    """A raw-source text shadow could not prove its fail-closed boundary."""


def _a8_graph() -> StateGraph:
    """The complete A8 persistent graph, with one owner per output field."""

    return StateGraph(
        (
            NodeSpec(
                "I0", "a8-v3.0",
                {"normalized_source": ArtifactKind.NORMALIZED_SOURCE, "fact_registry": ArtifactKind.FACT_REGISTRY},
                input_fields=("raw_source",),
            ),
            NodeSpec(
                "E0", "a8-v3.0",
                {"episode_direction": ArtifactKind.EPISODE_DIRECTION_DRAFT},
                input_fields=("fact_registry",),
            ),
            NodeSpec(
                "S1", "a8-v3.0",
                {"scene_intent": ArtifactKind.SCENE_INTENT_DRAFT},
                input_fields=("fact_registry", "episode_direction"),
            ),
            NodeSpec(
                "K1", "a8-v3.0",
                {"k1_snapshot": ArtifactKind.KNOWLEDGE_SNAPSHOT},
                input_fields=("episode_direction", "scene_intent"),
            ),
            NodeSpec(
                "B0", "a8-v3.0",
                {"blocking_draft": ArtifactKind.BLOCKING_DRAFT, "blocking_commit": ArtifactKind.BLOCKING_COMMIT},
                input_fields=("scene_intent", "k1_snapshot"),
                uses_knowledge_snapshot=True,
            ),
            NodeSpec(
                "K2", "a8-v3.0",
                {"k2_snapshot": ArtifactKind.KNOWLEDGE_SNAPSHOT},
                input_fields=("scene_intent", "blocking_commit"),
            ),
            NodeSpec(
                "B1", "a8-v3.0",
                {"execution_design": ArtifactKind.EXECUTION_DESIGN_DRAFT},
                input_fields=("fact_registry", "scene_intent", "blocking_commit", "k2_snapshot"),
                uses_knowledge_snapshot=True,
                uses_capability_profile=True,
            ),
            NodeSpec(
                "VEC", "a8-v3.0",
                {"vec": ArtifactKind.VISUAL_EXECUTION_CONTRACT},
                input_fields=("fact_registry", "blocking_commit", "execution_design"),
                uses_capability_profile=True,
            ),
            NodeSpec(
                "Projection", "a8-v3.0",
                {"projection_ast": ArtifactKind.PROJECTION_AST, "projection_manifest": ArtifactKind.PROJECTION_MANIFEST},
                input_fields=("vec",),
                uses_capability_profile=True,
            ),
            NodeSpec(
                "G0", "a8-v3.0",
                {"gate0_result": ArtifactKind.GATE0_RESULT},
                input_fields=("vec", "projection_ast", "projection_manifest"),
                uses_capability_profile=True,
            ),
            NodeSpec(
                "DP", "a8-v3.0",
                {"review_packet": ArtifactKind.REVIEW_PACKET, "dp_review_result": ArtifactKind.DP_REVIEW_RESULT},
                input_fields=("fact_registry", "episode_direction", "scene_intent", "vec", "projection_ast", "gate0_result"),
                uses_capability_profile=True,
            ),
        )
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_text_shadow_provider(args: argparse.Namespace) -> Any:
    """Create the sole live creative-stage provider used by the public CLI."""

    return ClaudeDeepSeekStructuredAdapter(executable=args.claude_executable)


def build_text_shadow_dp_reviewer(args: argparse.Namespace) -> Any:
    """Create the separate fresh-session native DP reviewer for the public CLI."""

    return NativeFreshDPReviewer(
        executable=args.claude_executable,
        model=args.model,
        timeout_seconds=args.provider_timeout_seconds,
    )


def _artifact_digest(artifact: ArtifactEnvelope[Any]) -> str:
    if type(artifact) is not ArtifactEnvelope:
        raise A8TextShadowError("A8 graph outputs must be exact canonical ArtifactEnvelope instances")
    return canonical_sha256(artifact)


def _accept_a8_node(
    storage: TextShadowStorage,
    *,
    node_id: str,
    artifacts: Mapping[str, ArtifactEnvelope[Any]],
    input_digests: Mapping[str, str],
    knowledge_snapshot_digest: str | None = None,
    capability_profile_digest: str | None = None,
) -> bool:
    """Accept exactly one node, or prove it is already the same accepted node.

    A rehydrated value is checked against both the persistent state and the
    immutable artifact repository.  The function never calls a provider; that
    separation is what makes resume unable to recall accepted creative stages.
    """

    state = storage.session.state()
    accepted = state.accepted.get(node_id)
    if accepted is not None:
        if (
            dict(accepted.input_digests) != dict(input_digests)
            or accepted.knowledge_snapshot_digest != knowledge_snapshot_digest
            or accepted.capability_profile_digest != capability_profile_digest
        ):
            raise A8TextShadowError(f"accepted {node_id} node is bound to different current inputs")
        for field_name, artifact in artifacts.items():
            storage.assert_artifact(field_name, artifact)
        return False
    try:
        storage.session.runner(owner="a8-text-shadow").execute(
            node_id,
            artifacts=artifacts,
            input_digests=input_digests,
            base_state_sha256=canonical_sha256(state.to_dict()),
            knowledge_snapshot_digest=knowledge_snapshot_digest,
            capability_profile_digest=capability_profile_digest,
        )
    except Exception as exc:
        raise A8TextShadowError(f"cannot atomically accept {node_id}: {exc}") from exc
    for field_name, artifact in artifacts.items():
        storage.assert_artifact(field_name, artifact)
    return True


def _paused_response(storage: TextShadowStorage, *, stop_after: str) -> Dict[str, Any]:
    state = storage.session.state()
    return {
        "status": "PAUSED",
        "claim_ceiling": "TEXT_VALIDATED",
        "run_id": storage.session.run_id,
        "stop_after": stop_after,
        "accepted_nodes": list(state.accepted),
        "runnable_nodes": list(storage.session.graph.runnable_node_ids(state)),
        "external_media_started": False,
        "v4_write": False,
        "production_switch_authorized": False,
    }


def _stop_if_requested(storage: TextShadowStorage, args: argparse.Namespace, node_id: str) -> Dict[str, Any] | None:
    return _paused_response(storage, stop_after=node_id) if args.stop_after == node_id else None


def run_text_shadow(args: argparse.Namespace) -> Dict[str, Any]:
    """Run the A8 raw-source -> Projection text-only vertical through this CLI.

    The only runtime path starts with bytes from ``--source``.  It is not the
    historical ``shadow`` command and it never invokes v4, a renderer, a
    verifier, a media adapter, or a production switch.
    """

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.is_file() or source_path.is_symlink():
        raise A8TextShadowError("--source must name a regular raw-source file")
    try:
        raw_source = source_path.read_bytes()
    except OSError as exc:
        raise A8TextShadowError("cannot read raw source") from exc
    if not raw_source:
        raise A8TextShadowError("raw source must not be empty")
    if not isinstance(args.episode_id, str) or not args.episode_id.strip() or not isinstance(args.scene_id, str) or not args.scene_id.strip():
        raise A8TextShadowError("episode_id and scene_id are required")

    provisional_source_id = args.source_id or "raw-source"
    normalized = normalize_raw_source(
        raw_source=raw_source,
        source_id=provisional_source_id,
        episode_id=args.episode_id,
        scene_id=args.scene_id,
        encoding=args.encoding,
    )
    source_id = args.source_id or f"raw-source-{normalized.source_ref.digest[:16]}"
    if source_id != provisional_source_id:
        normalized = normalize_raw_source(
            raw_source=raw_source,
            source_id=source_id,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            encoding=args.encoding,
        )
    run_id = args.run_id or f"a8-{normalized.source_ref.digest[:24]}"
    provider = build_text_shadow_provider(args)
    reviewer = build_text_shadow_dp_reviewer(args)
    provider_id = str(getattr(provider, "provider_id", f"native_structured:{args.model}"))
    reviewer_id = str(getattr(reviewer, "reviewer_id", ""))
    if not reviewer_id:
        raise A8TextShadowError("fresh DP reviewer must expose a stable reviewer_id")
    run_root = Path(args.runs_root).expanduser().resolve()
    existing_run = (run_root / run_id).exists()
    graph = _a8_graph()
    storage = TextShadowStorage.create_or_open(
        runs_root=run_root,
        run_id=run_id,
        graph=graph,
        write_scope="a8-" + canonical_sha256({"episode_id": args.episode_id, "scene_id": args.scene_id})[:32],
        episode_id=args.episode_id,
        scene_id=args.scene_id,
        source_id=source_id,
        source_digest=normalized.source_ref.digest,
        program_version=_A8_PROGRAM_VERSION,
        provider_id=provider_id,
        dp_reviewer_id=reviewer_id,
        created_at_utc=None if existing_run else _utc_now(),
    )
    storage.assert_run_record()
    try:
        storage.session.resume_plan({"raw_source": normalized.source_ref.digest})
    except RunSessionError as exc:
        raise A8TextShadowError(f"raw source cannot resume this run: {exc}") from exc

    created_at_utc = str(storage.run_record["created_at_utc"])
    id_factory = IdFactory(program_version=_A8_PROGRAM_VERSION)
    policy = GenerationPolicy(requested_model=args.model)
    compiler = PromptCompiler()

    try:
        ingest = run_i0_ingest(
            raw_source=raw_source,
            source_id=source_id,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            encoding=args.encoding,
            provider=provider,
            policy=policy,
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
            storage=storage,
            compiler=compiler,
        )
        _accept_a8_node(
            storage,
            node_id="I0",
            artifacts={"normalized_source": ingest.normalized_source_artifact, "fact_registry": ingest.fact_registry_artifact},
            input_digests={"raw_source": normalized.source_ref.digest},
        )
        paused = _stop_if_requested(storage, args, "I0")
        if paused:
            return paused

        facts = ingest.fact_registry_artifact.payload
        e0 = run_episode_direction(
            facts=facts,
            fact_registry_artifact_id=ingest.fact_registry_artifact.artifact_id,
            episode_id=args.episode_id,
            provider=provider,
            policy=policy,
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
            storage=storage,
            compiler=compiler,
        )
        _accept_a8_node(
            storage,
            node_id="E0",
            artifacts={"episode_direction": e0.artifact},
            input_digests={"fact_registry": _artifact_digest(ingest.fact_registry_artifact)},
        )
        paused = _stop_if_requested(storage, args, "E0")
        if paused:
            return paused

        s1 = run_scene_intent(
            facts=facts,
            fact_registry_artifact_id=ingest.fact_registry_artifact.artifact_id,
            episode_direction=e0.artifact,
            scene_id=args.scene_id,
            provider=provider,
            policy=policy,
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
            storage=storage,
            compiler=compiler,
        )
        _accept_a8_node(
            storage,
            node_id="S1",
            artifacts={"scene_intent": s1.artifact},
            input_digests={
                "fact_registry": _artifact_digest(ingest.fact_registry_artifact),
                "episode_direction": _artifact_digest(e0.artifact),
            },
        )
        paused = _stop_if_requested(storage, args, "S1")
        if paused:
            return paused

        k1 = run_k1_snapshot(
            episode_direction=e0.artifact,
            scene_intent=s1.artifact,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            created_at_utc=created_at_utc,
        )
        _accept_a8_node(
            storage,
            node_id="K1",
            artifacts={"k1_snapshot": k1.snapshot_artifact},
            input_digests={"episode_direction": _artifact_digest(e0.artifact), "scene_intent": _artifact_digest(s1.artifact)},
        )
        paused = _stop_if_requested(storage, args, "K1")
        if paused:
            return paused

        b0 = run_blocking(
            facts=facts,
            scene_intent=s1.artifact,
            k1_snapshot=k1.snapshot_artifact,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            provider=provider,
            policy=policy,
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
            storage=storage,
            compiler=compiler,
        )
        _accept_a8_node(
            storage,
            node_id="B0",
            artifacts={"blocking_draft": b0.draft_artifact, "blocking_commit": b0.commit_artifact},
            input_digests={"scene_intent": _artifact_digest(s1.artifact), "k1_snapshot": _artifact_digest(k1.snapshot_artifact)},
            knowledge_snapshot_digest=k1.snapshot_artifact.canonical_payload_sha256,
        )
        paused = _stop_if_requested(storage, args, "B0")
        if paused:
            return paused

        k2 = run_k2_snapshot(
            scene_intent=s1.artifact,
            blocking_commit=b0.commit_artifact,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            created_at_utc=created_at_utc,
        )
        _accept_a8_node(
            storage,
            node_id="K2",
            artifacts={"k2_snapshot": k2.snapshot_artifact},
            input_digests={"scene_intent": _artifact_digest(s1.artifact), "blocking_commit": _artifact_digest(b0.commit_artifact)},
        )
        paused = _stop_if_requested(storage, args, "K2")
        if paused:
            return paused

        execution = run_execution_design(
            facts=facts,
            scene_intent=s1.artifact,
            blocking_commit=b0.commit_artifact,
            k2_snapshot=k2.snapshot_artifact,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            provider=provider,
            policy=policy,
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
            storage=storage,
            capability_profile=GenerationCapabilityProfile.sd20_default(),
            compiler=compiler,
        )
        capability_digest = canonical_sha256(execution.vec.capability_profile)
        _accept_a8_node(
            storage,
            node_id="B1",
            artifacts={"execution_design": execution.draft_artifact},
            input_digests={
                "fact_registry": _artifact_digest(ingest.fact_registry_artifact),
                "scene_intent": _artifact_digest(s1.artifact),
                "blocking_commit": _artifact_digest(b0.commit_artifact),
                "k2_snapshot": _artifact_digest(k2.snapshot_artifact),
            },
            knowledge_snapshot_digest=k2.snapshot_artifact.canonical_payload_sha256,
            capability_profile_digest=capability_digest,
        )
        paused = _stop_if_requested(storage, args, "B1")
        if paused:
            return paused

        vec = run_vec_assembly(
            facts=facts,
            execution=execution,
            blocking_commit=b0.commit_artifact,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
        )
        _accept_a8_node(
            storage,
            node_id="VEC",
            artifacts={"vec": vec.artifact},
            input_digests={
                "fact_registry": _artifact_digest(ingest.fact_registry_artifact),
                "blocking_commit": _artifact_digest(b0.commit_artifact),
                "execution_design": _artifact_digest(execution.draft_artifact),
            },
            capability_profile_digest=capability_digest,
        )
        paused = _stop_if_requested(storage, args, "VEC")
        if paused:
            return paused

        projections = run_projection(
            facts=facts,
            vec_artifact=vec.artifact,
            blocking_commit=b0.commit_artifact,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
        )
        _accept_a8_node(
            storage,
            node_id="Projection",
            artifacts={"projection_ast": projections.ast_artifact, "projection_manifest": projections.manifest_artifact},
            input_digests={"vec": _artifact_digest(vec.artifact)},
            capability_profile_digest=capability_digest,
        )
        paused = _stop_if_requested(storage, args, "Projection")
        if paused:
            return paused

        gate = run_gate0_artifact(
            facts=facts,
            vec_artifact=vec.artifact,
            projections=projections,
            compiled_prompts=(
                *compile_i0_prompts(ingest.i0_inputs, compiler=compiler),
                e0.compiled_prompt,
                s1.compiled_prompt,
                b0.compiled_prompt,
                execution.compiled_prompt,
            ),
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
        )
        _accept_a8_node(
            storage,
            node_id="G0",
            artifacts={"gate0_result": gate.artifact},
            input_digests={
                "vec": _artifact_digest(vec.artifact),
                "projection_ast": _artifact_digest(projections.ast_artifact),
                "projection_manifest": _artifact_digest(projections.manifest_artifact),
            },
            capability_profile_digest=capability_digest,
        )
        paused = _stop_if_requested(storage, args, "G0")
        if paused:
            return paused

        dp = run_dp_review(
            facts=facts,
            episode_direction=e0.artifact,
            scene_intent=s1.artifact,
            vec_artifact=vec.artifact,
            projections=projections,
            gate_artifact=gate.artifact,
            episode_id=args.episode_id,
            scene_id=args.scene_id,
            id_factory=id_factory,
            program_version=_A8_PROGRAM_VERSION,
            created_at_utc=created_at_utc,
            storage=storage,
            reviewer=reviewer,
        )
        _accept_a8_node(
            storage,
            node_id="DP",
            artifacts={"review_packet": dp.packet_artifact, "dp_review_result": dp.result_artifact},
            input_digests={
                "fact_registry": _artifact_digest(ingest.fact_registry_artifact),
                "episode_direction": _artifact_digest(e0.artifact),
                "scene_intent": _artifact_digest(s1.artifact),
                "vec": _artifact_digest(vec.artifact),
                "projection_ast": _artifact_digest(projections.ast_artifact),
                "gate0_result": _artifact_digest(gate.artifact),
            },
            capability_profile_digest=capability_digest,
        )
    except (IngestNodeError, EpisodeNodeError, SceneNodeError, TextShadowStorageError, DomainValidationError, ValueError) as exc:
        raise A8TextShadowError(str(exc)) from exc

    state = storage.session.state()
    if tuple(state.accepted) != _A8_NODE_ORDER:
        raise A8TextShadowError("A8 text shadow did not commit the complete frozen v3.0 graph")
    result = {
        "status": "TEXT_VALIDATED",
        "claim_ceiling": "TEXT_VALIDATED",
        "run_id": storage.session.run_id,
        "accepted_nodes": list(state.accepted),
        "fact_registry_artifact_id": ingest.fact_registry_artifact.artifact_id,
        "vec_artifact_id": vec.artifact.artifact_id,
        "projection_ast_artifact_id": projections.ast_artifact.artifact_id,
        "gate0_result_artifact_id": gate.artifact.artifact_id,
        "dp_review_result_artifact_id": dp.result_artifact.artifact_id,
        "dp_fresh_session_id": dp.context.session_id,
        "dp_audit_sha256": canonical_sha256(dp.audit),
        "runtime_state_sha256": canonical_sha256(state.to_dict()),
        "run_record_sha256": storage.run_record["record_sha256"],
        "external_media_started": False,
        "v4_write": False,
        "production_switch_authorized": False,
    }
    persisted = storage.write_result(result)
    return {**result, "result_record_sha256": persisted["record_sha256"], "reused_existing_run": existing_run}


def _text_shadow(args: argparse.Namespace) -> Dict[str, Any]:
    return {"status": "OK", "text_shadow": run_text_shadow(args)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m mode_p_vnext",
        description=(
            "MODE:P vNext engineering CLI.  Historical structural Shadow and "
            "one resumable raw-source-to-Projection text shadow; never production delivery."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    session = commands.add_parser("session", help="create, inspect, or explicitly transition a vNext session")
    session_commands = session.add_subparsers(dest="session_command", required=True)

    init = session_commands.add_parser("init", help="initialize an idempotent persistent session")
    init.add_argument("--session-dir", required=True)
    init.add_argument("--episode-id", required=True)
    init.add_argument("--scene-id", default="")
    init.add_argument("--scope", choices=("episode", "scene"), required=True)
    init.add_argument("--initial-state", default=None)
    init.add_argument("--actor", default="cli")
    init.add_argument("--correlation-id", default="cli-session-init")
    init.add_argument("--artifact-hash", action="append", default=[])
    init.set_defaults(handler=_session_init)

    status = session_commands.add_parser("status", help="read a persistent session's authoritative state")
    status.add_argument("--session-dir", required=True)
    status.add_argument("--actor", default="cli")
    status.set_defaults(handler=_session_status)

    transition = session_commands.add_parser("transition", help="append one explicit, audited session transition")
    transition.add_argument("--session-dir", required=True)
    transition.add_argument("--to", required=True)
    transition.add_argument("--reason-code", required=True)
    transition.add_argument("--actor", default="cli")
    transition.add_argument("--input-commit-id", default="")
    transition.add_argument("--output-commit-id", default="")
    transition.add_argument("--correlation-id", default="cli-session-transition")
    transition.add_argument("--artifact-hash", action="append", default=[])
    transition.set_defaults(handler=_session_transition)

    shadow = commands.add_parser("shadow", help="run an isolated vNext structural Shadow; never submits media")
    shadow.add_argument("--script", required=True)
    shadow.add_argument("--session-dir", required=True)
    shadow.add_argument("--episode-id", default="")
    shadow.add_argument("--run-id", default="")
    shadow.set_defaults(handler=_shadow)

    text_shadow = commands.add_parser(
        "text-shadow",
        help=(
            "the sole A8 raw-source-to-Projection CLI vertical; persists only "
            "TEXT_VALIDATED evidence and never starts media or v4"
        ),
    )
    text_shadow.add_argument("--source", required=True, help="regular raw UTF text source")
    text_shadow.add_argument("--runs-root", required=True, help="dedicated A8 run storage root")
    text_shadow.add_argument("--episode-id", required=True)
    text_shadow.add_argument("--scene-id", required=True)
    text_shadow.add_argument("--source-id", default="")
    text_shadow.add_argument("--run-id", default="")
    text_shadow.add_argument("--encoding", default="utf-8")
    text_shadow.add_argument("--model", default="deepseek-v4-pro")
    text_shadow.add_argument("--claude-executable", default="claude.exe")
    text_shadow.add_argument("--provider-timeout-seconds", type=int, default=600)
    text_shadow.add_argument("--stop-after", choices=_A8_NODE_ORDER, default=None)
    text_shadow.set_defaults(handler=_text_shadow)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        response = args.handler(args)
    except (
        SessionStateError,
        InvalidStateTransition,
        ShadowError,
        A8TextShadowError,
        TextShadowStorageError,
        RunSessionError,
        OSError,
        ValueError,
        RuntimeError,
    ) as exc:
        _emit(
            {
                "status": "ERROR",
                "error_type": type(exc).__name__,
                "message": str(exc),
            },
            stream=sys.stderr,
        )
        return 2
    _emit(response)
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry delegates here
    raise SystemExit(main())
