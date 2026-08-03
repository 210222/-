"""A9 frozen holdout evaluation with explicit non-production boundaries.

This module intentionally evaluates only immutable references to a completed
text-shadow run.  It is not a second canonical domain model and never parses,
creates, modifies, or reprojects a VEC or ProjectionAST.  The local runtime
remains the authority for those artifacts.

The word ``quality`` in this module means an explicitly supplied,
hash-referenced *textual-contract* measurement.  It is never a visual or media
quality assertion.  A9 therefore cannot manufacture A10's frame evidence,
media acceptance, user approval, or a production-switch proposal.
"""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from mode_p_vnext.domain.artifact import canonical_sha256 as _runtime_canonical_sha256


ARCHITECTURE_DOCUMENT_PATH = (
    "MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/"
    "MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.1.md"
)
ARCHITECTURE_SHA256 = "d5616edc209dcaba3d82a1defe5e11187145399c30143bad6e4e685eb5c4c903"
TEXT_CLAIM_CEILING = "TEXT_VALIDATED"
QUALITY_SCOPE = "TEXTUAL_CONTRACT"
EVALUATOR_VERSION = "a9-v3.1"
EVALUATION_SCHEMA = "mode_p.vnext.a9.frozen-holdout-evaluation"
_A8_RUN_RECORD_SCHEMA = "mode_p_vnext_a8_text_shadow_run"
_A8_RESULT_RECORD_SCHEMA = "mode_p_vnext_a8_text_shadow_result"
_A8_RECORD_SCHEMA_VERSION = "3.0"
EXPECTED_TEXT_SHADOW_NODES = (
    "I0",
    "E0",
    "S1",
    "K1",
    "B0",
    "K2",
    "B1",
    "VEC",
    "Projection",
    "G0",
    "DP",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_QUALITY_MAX = 1000
_RUNTIME_WRITE_TERMINALS = frozenset(
    {
        "open",
        "write",
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rmdir",
        "touch",
        "replace",
        "rename",
        "truncate",
        "chmod",
        "chown",
        "remove",
        "rmtree",
        "copy",
        "copy2",
        "copytree",
        "move",
        "setattr",
        "delattr",
        "exec",
        "eval",
        "compile",
        "__import__",
    }
)
_RUNTIME_MUTATION_MODULES = frozenset(
    {
        "ctypes",
        "multiprocessing",
        "os",
        "shutil",
        "subprocess",
        "tempfile",
    }
)


class EvaluationError(RuntimeError):
    """Raised when an A9 input cannot be evaluated without ambiguity."""


class FrozenEvaluatorError(EvaluationError):
    """Raised when a supposedly frozen evaluator or authority has drifted."""


def _canonical_sha256(payload: Any) -> str:
    # Evaluation records use the already-canonical runtime hash function.  A9
    # does not introduce a competing canonical serialization authority.
    return _runtime_canonical_sha256(payload)


_FROZEN_TEXTUAL_QUALITY_CRITERIA = (
    "trace_lineage_integrity",
    "text_shadow_state_graph_conformance",
    "v3_authority_identity",
    "text_only_claim_boundary",
)
TEXTUAL_QUALITY_RUBRIC_SHA256 = _canonical_sha256(
    {
        "schema_name": "mode_p.vnext.a9.textual-contract-quality-rubric",
        "quality_scope": QUALITY_SCOPE,
        "criteria": list(_FROZEN_TEXTUAL_QUALITY_CRITERIA),
    }
)


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise EvaluationError(f"{field_name} must be a lowercase SHA-256")


def _require_case_id(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _CASE_ID_RE.fullmatch(value):
        raise EvaluationError(f"{field_name} must be a non-empty opaque evaluation ID")


def _require_nonnegative_int(value: int, field_name: str, *, maximum: int | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvaluationError(f"{field_name} must be a non-negative integer")
    if maximum is not None and value > maximum:
        raise EvaluationError(f"{field_name} must be <= {maximum}")


def _require_bool(value: bool, field_name: str) -> None:
    if type(value) is not bool:
        raise EvaluationError(f"{field_name} must be a bool")


def _repo_root() -> Path:
    # prompt_lab.py -> evaluation -> mode_p_vnext -> 01_调度器 -> repository root
    return Path(__file__).resolve().parents[3]


def authoritative_architecture_sha256() -> str:
    """Hash the sole v3.1 authority from the current repository, fail closed.

    This is deliberately a read-only check.  A9 cannot choose a replacement
    authority, repair it, or accept an architecture hash supplied by a caller.
    """

    repository = _repo_root().resolve()
    untrusted_path = repository / ARCHITECTURE_DOCUMENT_PATH
    if untrusted_path.is_symlink():
        raise FrozenEvaluatorError("the v3.1 architecture authority must not be a symlink")
    path = untrusted_path.resolve()
    if not path.is_relative_to(repository) or not path.is_file():
        raise FrozenEvaluatorError("the v3.1 architecture authority is unavailable or unsafe")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def evaluator_runtime_write_sites() -> tuple[str, ...]:
    """Return statically visible mutation sites in this evaluation package.

    A9 is intentionally a pure in-memory evaluator.  Its immutable report is
    returned to the caller; persistence is owned by the release/evidence layer,
    not by this evaluator.  Scanning the hash-bound local source makes a later
    attempt to add a runtime writer fail before a candidate is ranked.
    """

    package_root = Path(__file__).resolve().parent
    findings: list[str] = []
    for source_path in sorted(package_root.glob("*.py"), key=lambda item: item.name):
        try:
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        except (OSError, SyntaxError) as exc:
            raise FrozenEvaluatorError(f"cannot inspect evaluator source {source_path.name}: {exc}") from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in _RUNTIME_MUTATION_MODULES:
                        findings.append(f"{source_path.name}:{node.lineno}:import:{alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".", 1)[0] in _RUNTIME_MUTATION_MODULES:
                    findings.append(f"{source_path.name}:{node.lineno}:from:{node.module}")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            qualified = _call_name(node.func)
            terminal = qualified.rsplit(".", 1)[-1]
            # ``re.compile`` is required for strict identifier/hash validation;
            # only the unqualified built-in ``compile`` is a mutation escape.
            is_forbidden_builtin_compile = terminal == "compile" and qualified == "compile"
            is_other_forbidden_call = terminal in _RUNTIME_WRITE_TERMINALS and terminal != "compile"
            if is_forbidden_builtin_compile or is_other_forbidden_call:
                findings.append(f"{source_path.name}:{node.lineno}:{qualified}")
    return tuple(findings)


def evaluator_implementation_sha256() -> str:
    """Return the content digest of every Python source file in evaluation/."""

    package_root = Path(__file__).resolve().parent
    files: list[dict[str, str]] = []
    for source_path in sorted(package_root.glob("*.py"), key=lambda item: item.name):
        if not source_path.is_file() or source_path.is_symlink():
            raise FrozenEvaluatorError(f"unsafe evaluator source path: {source_path.name}")
        files.append(
            {
                "path": source_path.name,
                "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            }
        )
    if not files:
        raise FrozenEvaluatorError("frozen evaluator has no source files")
    return _canonical_sha256({"package": "mode_p_vnext.evaluation", "files": files})


@dataclass(frozen=True)
class GoldenCase:
    """A sealed Golden identity: never script text, prompt, answer, or VEC."""

    case_id: str
    normalized_source_sha256: str

    def __post_init__(self) -> None:
        _require_case_id(self.case_id, "golden case_id")
        _require_sha256(self.normalized_source_sha256, "golden normalized_source_sha256")

    def to_dict(self) -> dict[str, str]:
        return {
            "case_id": self.case_id,
            "normalized_source_sha256": self.normalized_source_sha256,
        }


@dataclass(frozen=True)
class HoldoutCase:
    """A sealed unseen-script identity fixed before candidate evaluation.

    Like ``GoldenCase``, this contains only an opaque ID and a NormalizedSource
    digest.  Raw script text remains outside both the evaluator policy and the
    Golden calibration set.
    """

    case_id: str
    normalized_source_sha256: str

    def __post_init__(self) -> None:
        _require_case_id(self.case_id, "holdout case_id")
        _require_sha256(self.normalized_source_sha256, "holdout normalized_source_sha256")

    def to_dict(self) -> dict[str, str]:
        return {
            "case_id": self.case_id,
            "normalized_source_sha256": self.normalized_source_sha256,
        }


@dataclass(frozen=True)
class TraceLineage:
    """Digest-only source → fact → draft → decision → VEC → Projection lineage.

    This is evaluation metadata, not a replacement artifact graph.  The
    canonical artifacts continue to live in the A1–A8 runtime stores.
    """

    normalized_source_sha256: str
    fact_registry_sha256: str
    draft_sha256: str
    decision_sha256: str
    vec_sha256: str
    projection_sha256: str
    output_sha256: str
    run_record_sha256: str

    def __post_init__(self) -> None:
        for field_name in (
            "normalized_source_sha256",
            "fact_registry_sha256",
            "draft_sha256",
            "decision_sha256",
            "vec_sha256",
            "projection_sha256",
            "output_sha256",
            "run_record_sha256",
        ):
            _require_sha256(getattr(self, field_name), field_name)

    def to_dict(self) -> dict[str, str]:
        return {
            "normalized_source_sha256": self.normalized_source_sha256,
            "fact_registry_sha256": self.fact_registry_sha256,
            "draft_sha256": self.draft_sha256,
            "decision_sha256": self.decision_sha256,
            "vec_sha256": self.vec_sha256,
            "projection_sha256": self.projection_sha256,
            "output_sha256": self.output_sha256,
            "run_record_sha256": self.run_record_sha256,
        }


@dataclass(frozen=True)
class RuntimeInvariantSnapshot:
    """Read-only evidence of the existing A8 text-shadow boundary."""

    authority_path: str
    authority_sha256: str
    accepted_nodes: tuple[str, ...]
    claim_ceiling: str
    external_media_started: bool
    v4_write: bool
    production_switch_authorized: bool
    visual_acceptance_claimed: bool
    owner_preview_approval_claimed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.authority_path, str) or not self.authority_path:
            raise EvaluationError("authority_path must be a non-empty path")
        _require_sha256(self.authority_sha256, "authority_sha256")
        if not isinstance(self.accepted_nodes, tuple) or not all(
            isinstance(node, str) and node for node in self.accepted_nodes
        ):
            raise EvaluationError("accepted_nodes must be a non-empty tuple of node IDs")
        if not isinstance(self.claim_ceiling, str) or not self.claim_ceiling:
            raise EvaluationError("claim_ceiling must be non-empty")
        for field_name in (
            "external_media_started",
            "v4_write",
            "production_switch_authorized",
            "visual_acceptance_claimed",
            "owner_preview_approval_claimed",
        ):
            _require_bool(getattr(self, field_name), field_name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_path": self.authority_path,
            "authority_sha256": self.authority_sha256,
            "accepted_nodes": list(self.accepted_nodes),
            "claim_ceiling": self.claim_ceiling,
            "external_media_started": self.external_media_started,
            "v4_write": self.v4_write,
            "production_switch_authorized": self.production_switch_authorized,
            "visual_acceptance_claimed": self.visual_acceptance_claimed,
            "owner_preview_approval_claimed": self.owner_preview_approval_claimed,
        }


@dataclass(frozen=True)
class EvaluationMetrics:
    """Hash-referenced, non-visual measurements for Pareto comparison.

    ``quality_score_milli`` is a frozen textual-contract measurement only.  It
    must not represent image, frame, media, or human visual acceptance.
    """

    quality_scope: str
    quality_score_milli: int
    quality_rubric_sha256: str
    quality_evidence_sha256: str
    measurement_evidence_sha256: str
    cost_units: int
    latency_ms: int
    complexity_units: int

    @staticmethod
    def bound_measurement_sha256(
        *,
        quality_scope: str,
        quality_score_milli: int,
        quality_rubric_sha256: str,
        quality_evidence_sha256: str,
        cost_units: int,
        latency_ms: int,
        complexity_units: int,
    ) -> str:
        """Bind every ranked value to its immutable measurement record."""

        return _canonical_sha256(
            {
                "schema_name": "mode_p.vnext.a9.measurement-record",
                "quality_scope": quality_scope,
                "quality_score_milli": quality_score_milli,
                "quality_rubric_sha256": quality_rubric_sha256,
                "quality_evidence_sha256": quality_evidence_sha256,
                "cost_units": cost_units,
                "latency_ms": latency_ms,
                "complexity_units": complexity_units,
            }
        )

    @classmethod
    def bind(
        cls,
        *,
        quality_scope: str,
        quality_score_milli: int,
        quality_rubric_sha256: str,
        quality_evidence_sha256: str,
        cost_units: int,
        latency_ms: int,
        complexity_units: int,
    ) -> "EvaluationMetrics":
        """Create metrics whose ranking inputs are cryptographically bound."""

        return cls(
            quality_scope=quality_scope,
            quality_score_milli=quality_score_milli,
            quality_rubric_sha256=quality_rubric_sha256,
            quality_evidence_sha256=quality_evidence_sha256,
            measurement_evidence_sha256=cls.bound_measurement_sha256(
                quality_scope=quality_scope,
                quality_score_milli=quality_score_milli,
                quality_rubric_sha256=quality_rubric_sha256,
                quality_evidence_sha256=quality_evidence_sha256,
                cost_units=cost_units,
                latency_ms=latency_ms,
                complexity_units=complexity_units,
            ),
            cost_units=cost_units,
            latency_ms=latency_ms,
            complexity_units=complexity_units,
        )

    def __post_init__(self) -> None:
        if self.quality_scope != QUALITY_SCOPE:
            raise EvaluationError(
                f"quality_scope must be {QUALITY_SCOPE!r}; visual/media scoring is prohibited in A9"
            )
        _require_nonnegative_int(
            self.quality_score_milli,
            "quality_score_milli",
            maximum=_QUALITY_MAX,
        )
        _require_sha256(self.quality_rubric_sha256, "quality_rubric_sha256")
        _require_sha256(self.quality_evidence_sha256, "quality_evidence_sha256")
        _require_sha256(self.measurement_evidence_sha256, "measurement_evidence_sha256")
        _require_nonnegative_int(self.cost_units, "cost_units")
        _require_nonnegative_int(self.latency_ms, "latency_ms")
        _require_nonnegative_int(self.complexity_units, "complexity_units")
        expected_measurement_digest = self.bound_measurement_sha256(
            quality_scope=self.quality_scope,
            quality_score_milli=self.quality_score_milli,
            quality_rubric_sha256=self.quality_rubric_sha256,
            quality_evidence_sha256=self.quality_evidence_sha256,
            cost_units=self.cost_units,
            latency_ms=self.latency_ms,
            complexity_units=self.complexity_units,
        )
        if self.measurement_evidence_sha256 != expected_measurement_digest:
            raise EvaluationError("measurement_evidence_sha256 is not bound to the ranked metric values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "quality_scope": self.quality_scope,
            "quality_score_milli": self.quality_score_milli,
            "quality_rubric_sha256": self.quality_rubric_sha256,
            "quality_evidence_sha256": self.quality_evidence_sha256,
            "measurement_evidence_sha256": self.measurement_evidence_sha256,
            "cost_units": self.cost_units,
            "latency_ms": self.latency_ms,
            "complexity_units": self.complexity_units,
        }


@dataclass(frozen=True)
class HoldoutCandidate:
    """One candidate evaluated against sealed Golden identities and A8 evidence."""

    candidate_id: str
    holdout_case_id: str
    lineage: TraceLineage
    invariants: RuntimeInvariantSnapshot
    metrics: EvaluationMetrics

    def __post_init__(self) -> None:
        _require_case_id(self.candidate_id, "candidate_id")
        _require_case_id(self.holdout_case_id, "holdout_case_id")
        if not isinstance(self.lineage, TraceLineage):
            raise EvaluationError("lineage must be TraceLineage")
        if not isinstance(self.invariants, RuntimeInvariantSnapshot):
            raise EvaluationError("invariants must be RuntimeInvariantSnapshot")
        if not isinstance(self.metrics, EvaluationMetrics):
            raise EvaluationError("metrics must be EvaluationMetrics")

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "holdout_case_id": self.holdout_case_id,
            "lineage": self.lineage.to_dict(),
            "invariants": self.invariants.to_dict(),
            "metrics": self.metrics.to_dict(),
        }


def _validated_a8_record(
    record: Mapping[str, Any],
    *,
    expected_schema: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise EvaluationError(f"{label} must be a mapping")
    copied = dict(record)
    record_sha256 = copied.pop("record_sha256", None)
    _require_sha256(record_sha256, f"{label} record_sha256")
    if copied.get("schema_name") != expected_schema or copied.get("schema_version") != _A8_RECORD_SCHEMA_VERSION:
        raise EvaluationError(f"{label} schema is not the frozen A8 schema")
    if _canonical_sha256(copied) != record_sha256:
        raise EvaluationError(f"{label} record_sha256 is invalid")
    return copied


def _validate_a8_run_record_binding(run_record: Mapping[str, Any], lineage: TraceLineage) -> dict[str, Any]:
    body = _validated_a8_record(
        run_record,
        expected_schema=_A8_RUN_RECORD_SCHEMA,
        label="A8 run record",
    )
    required_string_fields = (
        "run_id",
        "write_scope",
        "episode_id",
        "scene_id",
        "source_id",
        "program_version",
        "provider_id",
        "dp_reviewer_id",
        "created_at_utc",
    )
    for field_name in required_string_fields:
        value = body.get(field_name)
        if not isinstance(value, str) or not value:
            raise EvaluationError(f"A8 run record {field_name} must be non-empty")
    _require_sha256(body.get("source_digest"), "A8 run record source_digest")
    _require_sha256(body.get("graph_digest"), "A8 run record graph_digest")
    if body.get("source_digest") != lineage.normalized_source_sha256:
        raise EvaluationError("A8 run record source_digest is not bound to the candidate lineage")
    if body.get("claim_ceiling") != TEXT_CLAIM_CEILING:
        raise EvaluationError("A8 run record claim ceiling is not TEXT_VALIDATED")
    if body.get("external_media_started") is not False or body.get("v4_write") is not False:
        raise EvaluationError("A8 run record does not prove text-only v4-isolated execution")
    record_sha256 = run_record.get("record_sha256")
    if record_sha256 != lineage.run_record_sha256:
        raise EvaluationError("A8 run record digest is not bound to the candidate lineage")
    return body


def candidate_from_text_shadow_result(
    *,
    evaluator: "FrozenEvaluator",
    candidate_id: str,
    holdout_case_id: str,
    text_shadow_result: Mapping[str, Any],
    text_shadow_run_record: Mapping[str, Any],
    text_shadow_result_record: Mapping[str, Any],
    lineage: TraceLineage,
    metrics: EvaluationMetrics,
) -> HoldoutCandidate:
    """Bind an A9 candidate to an actual A8 ``text-shadow`` result record.

    The adapter intentionally reads only the result mapping produced by A8 and
    validates its terminal boundary.  It neither replays the pipeline nor
    reconstructs facts, decisions, VEC, or Projection.  The caller must supply
    the digest-only lineage that is independently stored by the canonical run.
    """

    if not isinstance(evaluator, FrozenEvaluator):
        raise EvaluationError("candidate_from_text_shadow_result requires FrozenEvaluator")
    evaluator.assert_integrity()
    if not isinstance(text_shadow_result, Mapping):
        raise EvaluationError("text_shadow_result must be a mapping")
    if not isinstance(lineage, TraceLineage):
        raise EvaluationError("lineage must be TraceLineage")
    if not isinstance(metrics, EvaluationMetrics):
        raise EvaluationError("metrics must be EvaluationMetrics")
    run_body = _validate_a8_run_record_binding(text_shadow_run_record, lineage)
    if text_shadow_result.get("status") != TEXT_CLAIM_CEILING:
        raise EvaluationError("A9 accepts only terminal TEXT_VALIDATED A8 results")
    if text_shadow_result.get("claim_ceiling") != TEXT_CLAIM_CEILING:
        raise EvaluationError("A8 result claim ceiling is not TEXT_VALIDATED")
    accepted_nodes = text_shadow_result.get("accepted_nodes")
    if not isinstance(accepted_nodes, list) or tuple(accepted_nodes) != evaluator.policy.expected_text_shadow_nodes:
        raise EvaluationError("A8 result has not accepted the complete frozen text-shadow graph")
    for field_name in (
        "external_media_started",
        "v4_write",
        "production_switch_authorized",
    ):
        if text_shadow_result.get(field_name) is not False:
            raise EvaluationError(f"A8 result does not prove {field_name}=false")
    run_record_sha256 = text_shadow_result.get("run_record_sha256")
    result_record_sha256 = text_shadow_result.get("result_record_sha256")
    _require_sha256(run_record_sha256, "A8 run_record_sha256")
    _require_sha256(result_record_sha256, "A8 result_record_sha256")
    if run_record_sha256 != lineage.run_record_sha256:
        raise EvaluationError("A8 run_record_sha256 is not bound to the candidate lineage")
    if result_record_sha256 != lineage.output_sha256:
        raise EvaluationError("A8 result_record_sha256 is not bound to the candidate output lineage")
    result_body = _validated_a8_record(
        text_shadow_result_record,
        expected_schema=_A8_RESULT_RECORD_SCHEMA,
        label="A8 result record",
    )
    if result_body.get("run_id") != run_body.get("run_id"):
        raise EvaluationError("A8 result record is not bound to the supplied run record")
    stored_result = result_body.get("result")
    if not isinstance(stored_result, Mapping):
        raise EvaluationError("A8 result record lacks a structured terminal result")
    returned_result = dict(text_shadow_result)
    returned_result.pop("result_record_sha256", None)
    returned_result.pop("reused_existing_run", None)
    if dict(stored_result) != returned_result:
        raise EvaluationError("A8 result record does not bind the supplied terminal result")
    if text_shadow_result_record.get("record_sha256") != lineage.output_sha256:
        raise EvaluationError("A8 result record digest is not bound to the candidate output lineage")
    return HoldoutCandidate(
        candidate_id=candidate_id,
        holdout_case_id=holdout_case_id,
        lineage=lineage,
        invariants=RuntimeInvariantSnapshot(
            authority_path=evaluator.policy.architecture_path,
            authority_sha256=evaluator.policy.architecture_sha256,
            accepted_nodes=evaluator.policy.expected_text_shadow_nodes,
            claim_ceiling=TEXT_CLAIM_CEILING,
            external_media_started=False,
            v4_write=False,
            production_switch_authorized=False,
            visual_acceptance_claimed=False,
            owner_preview_approval_claimed=False,
        ),
        metrics=metrics,
    )


@dataclass(frozen=True)
class FrozenEvaluationPolicy:
    """Hash-bound evaluator configuration that cannot learn from holdouts."""

    evaluator_id: str
    golden_cases: tuple[GoldenCase, ...]
    holdout_cases: tuple[HoldoutCase, ...]
    implementation_sha256: str
    architecture_path: str = ARCHITECTURE_DOCUMENT_PATH
    architecture_sha256: str = ARCHITECTURE_SHA256
    expected_text_shadow_nodes: tuple[str, ...] = EXPECTED_TEXT_SHADOW_NODES
    evaluator_version: str = EVALUATOR_VERSION
    runtime_mutation_policy: str = "FORBID"
    quality_scope: str = QUALITY_SCOPE
    quality_rubric_sha256: str = TEXTUAL_QUALITY_RUBRIC_SHA256
    frozen: bool = True

    def __post_init__(self) -> None:
        _require_case_id(self.evaluator_id, "evaluator_id")
        if not isinstance(self.golden_cases, tuple) or not self.golden_cases:
            raise EvaluationError("golden_cases must be a non-empty immutable tuple")
        if not all(isinstance(case, GoldenCase) for case in self.golden_cases):
            raise EvaluationError("golden_cases must contain GoldenCase values")
        if not isinstance(self.holdout_cases, tuple) or not self.holdout_cases:
            raise EvaluationError("holdout_cases must be a non-empty immutable tuple")
        if not all(isinstance(case, HoldoutCase) for case in self.holdout_cases):
            raise EvaluationError("holdout_cases must contain HoldoutCase values")
        golden_ids = [case.case_id for case in self.golden_cases]
        golden_sources = [case.normalized_source_sha256 for case in self.golden_cases]
        holdout_ids = [case.case_id for case in self.holdout_cases]
        holdout_sources = [case.normalized_source_sha256 for case in self.holdout_cases]
        if len(golden_ids) != len(set(golden_ids)):
            raise EvaluationError("golden case IDs must be unique")
        if len(golden_sources) != len(set(golden_sources)):
            raise EvaluationError("golden source digests must be unique")
        if len(holdout_ids) != len(set(holdout_ids)):
            raise EvaluationError("holdout case IDs must be unique")
        if len(holdout_sources) != len(set(holdout_sources)):
            raise EvaluationError("holdout source digests must be unique")
        if set(golden_ids) & set(holdout_ids):
            raise EvaluationError("Golden and holdout case IDs must remain disjoint")
        if set(golden_sources) & set(holdout_sources):
            raise EvaluationError("Golden and holdout source digests must remain disjoint")
        if self.golden_cases != tuple(sorted(self.golden_cases, key=lambda case: case.case_id)):
            raise EvaluationError("golden_cases must be in deterministic case-ID order")
        if self.holdout_cases != tuple(sorted(self.holdout_cases, key=lambda case: case.case_id)):
            raise EvaluationError("holdout_cases must be in deterministic case-ID order")
        _require_sha256(self.implementation_sha256, "implementation_sha256")
        if self.architecture_path != ARCHITECTURE_DOCUMENT_PATH:
            raise EvaluationError("A9 must use the sole v3.1 architecture path")
        if self.architecture_sha256 != ARCHITECTURE_SHA256:
            raise EvaluationError("A9 must use the sole v3.1 architecture SHA-256")
        if self.expected_text_shadow_nodes != EXPECTED_TEXT_SHADOW_NODES:
            raise EvaluationError("A9 may not replace the frozen A8 text-shadow graph expectation")
        if self.evaluator_version != EVALUATOR_VERSION:
            raise EvaluationError("unexpected evaluator version")
        if self.runtime_mutation_policy != "FORBID":
            raise EvaluationError("A9 evaluator runtime mutation must be forbidden")
        if self.quality_scope != QUALITY_SCOPE:
            raise EvaluationError("A9 quality scope must remain textual-contract only")
        if self.quality_rubric_sha256 != TEXTUAL_QUALITY_RUBRIC_SHA256:
            raise EvaluationError("A9 quality rubric must remain frozen and hash-bound")
        if self.frozen is not True:
            raise EvaluationError("A9 evaluator policy must be frozen")

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "mode_p.vnext.a9.frozen-evaluator-policy",
            "evaluator_id": self.evaluator_id,
            "golden_cases": [case.to_dict() for case in self.golden_cases],
            "holdout_cases": [case.to_dict() for case in self.holdout_cases],
            "implementation_sha256": self.implementation_sha256,
            "architecture_path": self.architecture_path,
            "architecture_sha256": self.architecture_sha256,
            "expected_text_shadow_nodes": list(self.expected_text_shadow_nodes),
            "evaluator_version": self.evaluator_version,
            "runtime_mutation_policy": self.runtime_mutation_policy,
            "quality_scope": self.quality_scope,
            "quality_rubric_sha256": self.quality_rubric_sha256,
            "frozen": self.frozen,
        }


@dataclass(frozen=True)
class FrozenEvaluatorIntegrity:
    """Read-only proof that the evaluator and sole authority have not drifted."""

    evaluator_fingerprint: str
    implementation_sha256: str
    architecture_path: str
    architecture_sha256: str
    quality_rubric_sha256: str
    runtime_write_sites: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluator_fingerprint": self.evaluator_fingerprint,
            "implementation_sha256": self.implementation_sha256,
            "architecture_path": self.architecture_path,
            "architecture_sha256": self.architecture_sha256,
            "quality_rubric_sha256": self.quality_rubric_sha256,
            "runtime_write_sites": list(self.runtime_write_sites),
        }


@dataclass(frozen=True)
class FrozenEvaluator:
    """Pure A9 evaluator; it returns reports and owns no mutable runtime state."""

    policy: FrozenEvaluationPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.policy, FrozenEvaluationPolicy):
            raise EvaluationError("FrozenEvaluator requires FrozenEvaluationPolicy")

    @property
    def fingerprint(self) -> str:
        return self.policy.fingerprint

    def assert_integrity(self) -> FrozenEvaluatorIntegrity:
        actual_architecture = authoritative_architecture_sha256()
        actual_implementation = evaluator_implementation_sha256()
        write_sites = evaluator_runtime_write_sites()
        issues: list[str] = []
        if actual_architecture != self.policy.architecture_sha256:
            issues.append("architecture_authority_sha256_drift")
        if actual_implementation != self.policy.implementation_sha256:
            issues.append("evaluator_implementation_sha256_drift")
        if write_sites:
            issues.append("runtime_write_site_detected")
        if issues:
            detail = ", ".join(issues)
            raise FrozenEvaluatorError(f"frozen evaluator integrity failed: {detail}")
        return FrozenEvaluatorIntegrity(
            evaluator_fingerprint=self.fingerprint,
            implementation_sha256=actual_implementation,
            architecture_path=self.policy.architecture_path,
            architecture_sha256=actual_architecture,
            quality_rubric_sha256=self.policy.quality_rubric_sha256,
            runtime_write_sites=write_sites,
        )


def freeze_evaluator(
    *,
    evaluator_id: str,
    golden_cases: Iterable[GoldenCase],
    holdout_cases: Iterable[HoldoutCase],
    expected_implementation_sha256: str | None = None,
) -> FrozenEvaluator:
    """Freeze an evaluator before holdout candidates are supplied.

    Only Golden/Holdout case identifiers and normalized-source digests are
    permitted in the policy.  The caller seals the holdout identities before
    submitting candidate results; raw text is not accepted or retained.  The
    function does not write any state, so evaluation cannot tune itself against
    an unseen script.
    """

    golden_tuple = tuple(sorted(tuple(golden_cases), key=lambda item: item.case_id))
    holdout_tuple = tuple(sorted(tuple(holdout_cases), key=lambda item: item.case_id))
    actual_implementation = evaluator_implementation_sha256()
    if expected_implementation_sha256 is not None:
        _require_sha256(expected_implementation_sha256, "expected_implementation_sha256")
        if expected_implementation_sha256 != actual_implementation:
            raise FrozenEvaluatorError("requested evaluator implementation digest does not match local source")
    policy = FrozenEvaluationPolicy(
        evaluator_id=evaluator_id,
        golden_cases=golden_tuple,
        holdout_cases=holdout_tuple,
        implementation_sha256=actual_implementation,
    )
    evaluator = FrozenEvaluator(policy=policy)
    evaluator.assert_integrity()
    return evaluator


@dataclass(frozen=True)
class CandidateEvaluation:
    """One auditable KEEP/DISCARD result; never a media approval."""

    candidate_id: str
    holdout_case_id: str
    disposition: str
    reasons: tuple[str, ...]
    pareto_dominated_by: tuple[str, ...]
    metrics: EvaluationMetrics
    lineage_sha256: str

    def __post_init__(self) -> None:
        _require_case_id(self.candidate_id, "candidate evaluation candidate_id")
        _require_case_id(self.holdout_case_id, "candidate evaluation holdout_case_id")
        if self.disposition not in {"KEEP", "DISCARD"}:
            raise EvaluationError("candidate disposition must be KEEP or DISCARD")
        if not isinstance(self.reasons, tuple) or not all(isinstance(reason, str) and reason for reason in self.reasons):
            raise EvaluationError("candidate reasons must be an immutable tuple of non-empty codes")
        if not isinstance(self.pareto_dominated_by, tuple) or not all(
            isinstance(candidate_id, str) and candidate_id for candidate_id in self.pareto_dominated_by
        ):
            raise EvaluationError("pareto_dominated_by must be an immutable tuple of IDs")
        if self.disposition == "KEEP" and (self.reasons or self.pareto_dominated_by):
            raise EvaluationError("kept candidate cannot have failure or domination reasons")
        if self.disposition == "DISCARD" and not (self.reasons or self.pareto_dominated_by):
            raise EvaluationError("discarded candidate needs a fail-closed reason")
        if not isinstance(self.metrics, EvaluationMetrics):
            raise EvaluationError("candidate evaluation metrics must be EvaluationMetrics")
        _require_sha256(self.lineage_sha256, "lineage_sha256")

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "holdout_case_id": self.holdout_case_id,
            "disposition": self.disposition,
            "reasons": list(self.reasons),
            "pareto_dominated_by": list(self.pareto_dominated_by),
            "metrics": self.metrics.to_dict(),
            "lineage_sha256": self.lineage_sha256,
        }


@dataclass(frozen=True)
class EvaluationReport:
    """Immutable, text-only A9 report returned by the pure evaluator."""

    evaluator_integrity: FrozenEvaluatorIntegrity
    candidate_evaluations: tuple[CandidateEvaluation, ...]
    status: str
    claim_ceiling: str = TEXT_CLAIM_CEILING
    external_media_started: bool = False
    media_visual_acceptance: bool = False
    owner_preview_approval: bool = False
    production_switch_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.evaluator_integrity, FrozenEvaluatorIntegrity):
            raise EvaluationError("evaluator_integrity must be FrozenEvaluatorIntegrity")
        if not isinstance(self.candidate_evaluations, tuple) or not self.candidate_evaluations:
            raise EvaluationError("evaluation report needs at least one candidate result")
        if not all(isinstance(item, CandidateEvaluation) for item in self.candidate_evaluations):
            raise EvaluationError("evaluation report contains an invalid candidate result")
        if self.status not in {"TEXT_HOLDOUT_EVALUATED", "FAIL_CLOSED"}:
            raise EvaluationError("evaluation status must be TEXT_HOLDOUT_EVALUATED or FAIL_CLOSED")
        if self.claim_ceiling != TEXT_CLAIM_CEILING:
            raise EvaluationError("A9 report claim ceiling must remain TEXT_VALIDATED")
        for field_name in (
            "external_media_started",
            "media_visual_acceptance",
            "owner_preview_approval",
            "production_switch_authorized",
        ):
            _require_bool(getattr(self, field_name), field_name)
            if getattr(self, field_name):
                raise EvaluationError(f"A9 report cannot set {field_name}=true")
        kept = tuple(item for item in self.candidate_evaluations if item.disposition == "KEEP")
        if self.status == "TEXT_HOLDOUT_EVALUATED" and not kept:
            raise EvaluationError("successful textual holdout evaluation needs at least one kept candidate")
        if self.status == "FAIL_CLOSED" and kept:
            raise EvaluationError("fail-closed report cannot keep a candidate")

    @property
    def kept_candidate_ids(self) -> tuple[str, ...]:
        return tuple(item.candidate_id for item in self.candidate_evaluations if item.disposition == "KEEP")

    @property
    def digest(self) -> str:
        return _canonical_sha256(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": EVALUATION_SCHEMA,
            "schema_version": "1.0",
            "status": self.status,
            "claim_ceiling": self.claim_ceiling,
            "evaluator_integrity": self.evaluator_integrity.to_dict(),
            "candidate_evaluations": [item.to_dict() for item in self.candidate_evaluations],
            "kept_candidate_ids": list(self.kept_candidate_ids),
            "external_media_started": self.external_media_started,
            "media_visual_acceptance": self.media_visual_acceptance,
            "owner_preview_approval": self.owner_preview_approval,
            "production_switch_authorized": self.production_switch_authorized,
        }


def pareto_dominates(left: EvaluationMetrics, right: EvaluationMetrics) -> bool:
    """Return whether ``left`` is strictly no worse on all A9 objectives.

    Higher textual-contract quality is better; cost, latency, and complexity
    are minimized.  This is a ranking helper only and never changes a runtime
    configuration, a prompt, or a Director decision.
    """

    if not isinstance(left, EvaluationMetrics) or not isinstance(right, EvaluationMetrics):
        raise EvaluationError("pareto_dominates requires EvaluationMetrics values")
    no_worse = (
        left.quality_score_milli >= right.quality_score_milli
        and left.cost_units <= right.cost_units
        and left.latency_ms <= right.latency_ms
        and left.complexity_units <= right.complexity_units
    )
    strictly_better = (
        left.quality_score_milli > right.quality_score_milli
        or left.cost_units < right.cost_units
        or left.latency_ms < right.latency_ms
        or left.complexity_units < right.complexity_units
    )
    return no_worse and strictly_better


def _candidate_violations(policy: FrozenEvaluationPolicy, candidate: HoldoutCandidate) -> tuple[str, ...]:
    violations: list[str] = []
    golden_ids = {case.case_id for case in policy.golden_cases}
    golden_sources = {case.normalized_source_sha256 for case in policy.golden_cases}
    holdout_by_id = {case.case_id: case for case in policy.holdout_cases}
    if candidate.holdout_case_id in golden_ids:
        violations.append("GOLDEN_CASE_ID_OVERLAP")
    elif candidate.holdout_case_id not in holdout_by_id:
        violations.append("UNREGISTERED_HOLDOUT_CASE")
    elif (
        candidate.lineage.normalized_source_sha256
        != holdout_by_id[candidate.holdout_case_id].normalized_source_sha256
    ):
        violations.append("HOLDOUT_SOURCE_DIGEST_MISMATCH")
    if candidate.lineage.normalized_source_sha256 in golden_sources:
        violations.append("GOLDEN_SOURCE_DIGEST_OVERLAP")
    if candidate.invariants.authority_path != policy.architecture_path:
        violations.append("AUTHORITY_PATH_MISMATCH")
    if candidate.invariants.authority_sha256 != policy.architecture_sha256:
        violations.append("AUTHORITY_SHA256_MISMATCH")
    if candidate.invariants.accepted_nodes != policy.expected_text_shadow_nodes:
        violations.append("TEXT_SHADOW_STATE_GRAPH_MISMATCH")
    if candidate.invariants.claim_ceiling != TEXT_CLAIM_CEILING:
        violations.append("TEXT_CLAIM_CEILING_VIOLATION")
    if candidate.invariants.external_media_started:
        violations.append("EXTERNAL_MEDIA_STARTED")
    if candidate.invariants.v4_write:
        violations.append("V4_WRITE_DETECTED")
    if candidate.invariants.production_switch_authorized:
        violations.append("PRODUCTION_SWITCH_DETECTED")
    if candidate.invariants.visual_acceptance_claimed:
        violations.append("TEXT_ONLY_MEDIA_CLAIM")
    if candidate.invariants.owner_preview_approval_claimed:
        violations.append("OWNER_PREVIEW_APPROVAL_CLAIM")
    if candidate.metrics.quality_rubric_sha256 != policy.quality_rubric_sha256:
        violations.append("TEXTUAL_QUALITY_RUBRIC_MISMATCH")
    return tuple(violations)


def _lineage_sha256(candidate: HoldoutCandidate) -> str:
    return _canonical_sha256(candidate.lineage.to_dict())


def evaluate_holdout_candidates(
    evaluator: FrozenEvaluator,
    candidates: Iterable[HoldoutCandidate],
) -> EvaluationReport:
    """Evaluate unseen textual candidates against one frozen, read-only policy.

    A policy-integrity failure or an ambiguous candidate identity raises before
    any ranking occurs.  A candidate that violates v3.1 is represented as a
    traceable ``DISCARD``.  If no candidate can be kept, the report is
    explicitly ``FAIL_CLOSED`` rather than a passing substitute for A10.
    """

    if not isinstance(evaluator, FrozenEvaluator):
        raise EvaluationError("evaluate_holdout_candidates requires FrozenEvaluator")
    integrity = evaluator.assert_integrity()
    candidate_tuple = tuple(candidates)
    if not candidate_tuple:
        raise EvaluationError("holdout evaluation requires at least one candidate")
    if not all(isinstance(candidate, HoldoutCandidate) for candidate in candidate_tuple):
        raise EvaluationError("holdout evaluation received an invalid candidate")
    candidate_tuple = tuple(sorted(candidate_tuple, key=lambda item: item.candidate_id))
    candidate_ids = tuple(candidate.candidate_id for candidate in candidate_tuple)
    if len(candidate_ids) != len(set(candidate_ids)):
        raise EvaluationError("duplicate candidate IDs make the holdout comparison ambiguous")

    violations_by_candidate = {
        candidate.candidate_id: _candidate_violations(evaluator.policy, candidate)
        for candidate in candidate_tuple
    }
    valid_candidates = tuple(
        candidate
        for candidate in candidate_tuple
        if not violations_by_candidate[candidate.candidate_id]
    )
    dominators: dict[str, tuple[str, ...]] = {}
    for candidate in valid_candidates:
        dominated_by = tuple(
            other.candidate_id
            for other in valid_candidates
            if other.candidate_id != candidate.candidate_id
            and pareto_dominates(other.metrics, candidate.metrics)
        )
        dominators[candidate.candidate_id] = tuple(sorted(dominated_by))

    results: list[CandidateEvaluation] = []
    for candidate in candidate_tuple:
        violations = violations_by_candidate[candidate.candidate_id]
        dominated_by = dominators.get(candidate.candidate_id, ())
        if violations:
            result = CandidateEvaluation(
                candidate_id=candidate.candidate_id,
                holdout_case_id=candidate.holdout_case_id,
                disposition="DISCARD",
                reasons=violations,
                pareto_dominated_by=(),
                metrics=candidate.metrics,
                lineage_sha256=_lineage_sha256(candidate),
            )
        elif dominated_by:
            result = CandidateEvaluation(
                candidate_id=candidate.candidate_id,
                holdout_case_id=candidate.holdout_case_id,
                disposition="DISCARD",
                reasons=(),
                pareto_dominated_by=dominated_by,
                metrics=candidate.metrics,
                lineage_sha256=_lineage_sha256(candidate),
            )
        else:
            result = CandidateEvaluation(
                candidate_id=candidate.candidate_id,
                holdout_case_id=candidate.holdout_case_id,
                disposition="KEEP",
                reasons=(),
                pareto_dominated_by=(),
                metrics=candidate.metrics,
                lineage_sha256=_lineage_sha256(candidate),
            )
        results.append(result)

    result_tuple = tuple(results)
    status = "TEXT_HOLDOUT_EVALUATED" if any(
        item.disposition == "KEEP" for item in result_tuple
    ) else "FAIL_CLOSED"
    report = EvaluationReport(
        evaluator_integrity=integrity,
        candidate_evaluations=result_tuple,
        status=status,
    )
    assert_no_text_only_media_claim(report)
    return report


def assert_no_text_only_media_claim(report: EvaluationReport) -> None:
    """Refuse any attempt to elevate an A9 report into a visual/media claim."""

    if not isinstance(report, EvaluationReport):
        raise EvaluationError("report must be EvaluationReport")
    if (
        report.claim_ceiling != TEXT_CLAIM_CEILING
        or report.external_media_started
        or report.media_visual_acceptance
        or report.owner_preview_approval
        or report.production_switch_authorized
    ):
        raise EvaluationError("A9 text evaluation cannot claim media, visual acceptance, or production authority")
    for item in report.candidate_evaluations:
        if item.metrics.quality_scope != QUALITY_SCOPE:
            raise EvaluationError("A9 report contains a non-textual quality scope")
