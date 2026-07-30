"""Isolated, non-production vNext Shadow execution.

R2.2 supplies a real filesystem run and a comparison envelope while the
creative Director runtime is still intentionally unavailable.  The result is
therefore honest about its scope: it records that no external model or v4
generation chain was invoked rather than manufacturing a Master or a render.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .atomic_commit import Transaction, TransactionError, recover_scene
from .canonical_serialization import canonical_json_dumps, stable_hash_file
from .contamination_scanner import ContaminationError, check_vnext_write_safe


class ShadowError(Exception):
    """Raised for unsafe, non-isolated, or invalid Shadow requests."""


SHADOW_MANIFEST_NAME = "SHADOW_MANIFEST.json"
SHADOW_SCHEMA_NAME = "mode_p_vnext_shadow_manifest"
SHADOW_SCHEMA_VERSION = "1.0.0"


def _safe_component(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise ShadowError(f"{label} must be a string")
    value = value.strip()
    if not value:
        raise ShadowError(f"{label} is required")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise ShadowError(f"{label} contains unsupported path characters")
    return value


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        temporary.write_bytes(canonical_json_dumps(dict(value)).encode("utf-8"))
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ShadowError(f"cannot parse Shadow manifest: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ShadowError("Shadow manifest must be a JSON object")
    return parsed


def _ensure_vnext_write_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if root == root.anchor or root.name in {"", ".", ".."}:
        raise ShadowError("session_dir must be a dedicated vNext directory")
    try:
        check_vnext_write_safe(root)
    except ContaminationError as exc:
        raise ShadowError(str(exc)) from exc
    if root.exists() and root.is_symlink():
        raise ShadowError("session_dir must not be a symlink")
    project_root = Path(__file__).resolve().parents[2]
    source_roots = (project_root, project_root / "01_调度器", Path(__file__).resolve().parent)
    if any(root == source_root.resolve() for source_root in source_roots):
        raise ShadowError("session_dir must not be a project or source directory")
    package_root = Path(__file__).resolve().parent
    try:
        root.relative_to(package_root)
    except ValueError:
        pass
    else:
        raise ShadowError("session_dir must not be inside the vNext source package")
    return root


@dataclass(frozen=True)
class ShadowConfig:
    """Inputs for one isolated Shadow structural run.

    The old boolean fields remain public for compatibility, but any attempt to
    turn one on is rejected rather than treated as advisory documentation.
    """

    episode_script_path: str
    session_dir: str
    mode: str = "shadow_only"
    episode_id: str = ""
    run_id: str = ""
    isolated_session: bool = True
    use_v4_cache: bool = False
    use_v4_generation_chain: bool = False
    writes_to_v4_delivery: bool = False
    external_submission: bool = False
    comparison_baseline: Mapping[str, Any] = field(default_factory=dict)

    @property
    def affects_production(self) -> bool:
        return False


@dataclass(frozen=True)
class ShadowResult:
    run_id: str
    run_root: str = ""
    manifest_path: str = ""
    source_script_sha256: str = ""
    vnext_output: Dict[str, Any] = field(default_factory=dict)
    comparison_ready: bool = False
    production_ready: bool = False
    external_submission: bool = False
    reused_existing_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_root": self.run_root,
            "manifest_path": self.manifest_path,
            "source_script_sha256": self.source_script_sha256,
            "vnext_output": dict(self.vnext_output),
            "comparison_ready": self.comparison_ready,
            "production_ready": self.production_ready,
            "external_submission": self.external_submission,
            "reused_existing_run": self.reused_existing_run,
        }


def _validate_config(config: ShadowConfig) -> None:
    if config.mode != "shadow_only":
        raise ShadowError("only mode='shadow_only' is permitted during rebuild")
    if not config.isolated_session:
        raise ShadowError("Shadow requires an isolated session")
    if config.use_v4_cache or config.use_v4_generation_chain or config.writes_to_v4_delivery:
        raise ShadowError("Shadow may not use v4 cache, generation, or delivery")
    if config.external_submission:
        raise ShadowError("Shadow may not submit to an external platform")
    if not isinstance(config.comparison_baseline, Mapping):
        raise ShadowError("comparison_baseline must be a mapping")


def _comparison(config: ShadowConfig) -> Dict[str, Any]:
    baseline = dict(config.comparison_baseline)
    # R2.2 intentionally has no Director or v4 imports.  These four artifacts
    # make the missing creative phase explicit and reserve a stable comparison
    # schema for later Shadow work instead of emitting a misleading success.
    return {
        "schema_name": "mode_p_vnext_shadow_comparison",
        "schema_version": "1.0.0",
        "baseline_supplied_by_caller": bool(baseline),
        "categories": {
            "master": {
                "vnext_status": "NOT_GENERATED_R2_2",
                "baseline": baseline.get("master", "NOT_PROVIDED"),
                "comparable": False,
            },
            "format": {
                "vnext_status": "STRUCTURAL_SCHEMA_ONLY",
                "baseline": baseline.get("format", "NOT_PROVIDED"),
                "comparable": False,
            },
            "budget": {
                "vnext_status": "NO_MODEL_CALLS",
                "baseline": baseline.get("budget", "NOT_PROVIDED"),
                "comparable": False,
            },
            "checks": {
                "vnext_status": "ISOLATION_AND_MANIFEST_ONLY",
                "baseline": baseline.get("checks", "NOT_PROVIDED"),
                "comparable": False,
            },
        },
    }


def _result_from_manifest(manifest: Mapping[str, Any], manifest_path: Path, *, reused: bool) -> ShadowResult:
    output = dict(manifest.get("vnext_output", {}))
    return ShadowResult(
        run_id=str(manifest["run_id"]),
        run_root=str(manifest_path.parent),
        manifest_path=str(manifest_path),
        source_script_sha256=str(manifest["source_script"]["sha256"]),
        vnext_output=output,
        comparison_ready=bool(manifest.get("comparison_ready", False)),
        production_ready=False,
        external_submission=False,
        reused_existing_run=reused,
    )


def run_shadow(config: ShadowConfig) -> ShadowResult:
    """Create or reuse one isolated structural Shadow run.

    The same source hash and deterministic default run ID are idempotent.  A
    different source cannot overwrite that run; callers must select a new ID.
    Every write stays below ``session_dir/shadow_runs`` and is guarded by the
    completed R2.1 atomic transaction implementation.
    """

    _validate_config(config)
    script_path = Path(config.episode_script_path).expanduser().resolve()
    if not script_path.is_file() or script_path.is_symlink():
        raise ShadowError("episode_script_path must be a regular existing file")
    try:
        script_text = script_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ShadowError(f"cannot read UTF-8 episode script: {exc}") from exc
    if not script_text.strip():
        raise ShadowError("episode script must not be empty")

    source_hash = stable_hash_file(script_path)
    run_id = config.run_id or f"shadow-{source_hash[:16]}"
    run_id = _safe_component(run_id, "run_id")
    root = _ensure_vnext_write_root(Path(config.session_dir))
    runs_root = root / "shadow_runs"
    run_root = (runs_root / run_id).resolve()
    try:
        run_root.relative_to(runs_root.resolve())
    except ValueError as exc:
        raise ShadowError("Shadow run path escapes its isolated session directory") from exc
    _ensure_vnext_write_root(run_root)
    manifest_path = run_root / SHADOW_MANIFEST_NAME

    if manifest_path.exists():
        manifest = _read_json(manifest_path)
        if manifest.get("schema_name") != SHADOW_SCHEMA_NAME:
            raise ShadowError("existing Shadow manifest has an unsupported schema")
        if manifest.get("run_id") != run_id:
            raise ShadowError("existing Shadow manifest run_id mismatch")
        if manifest.get("source_script", {}).get("sha256") != source_hash:
            raise ShadowError("run_id already belongs to a different source script")
        return _result_from_manifest(manifest, manifest_path, reused=True)

    if run_root.exists() and any(run_root.iterdir()):
        # R2.1 recovery may promote a complete commit after a process crash.
        # Do not delete an unknown/incomplete directory: it is evidence.
        recovery = recover_scene(run_root)
        if recovery.errors:
            raise ShadowError("existing Shadow run is incomplete or ambiguous")
        raise ShadowError("existing Shadow run lacks its manifest; refusing overwrite")

    run_root.mkdir(parents=True, exist_ok=True)
    comparison = _comparison(config)
    output = {
        "status": "STRUCTURAL_SHADOW_COMPLETE",
        "creative_generation_performed": False,
        "external_submission": False,
        "message": "R2.2 created only isolated runtime and comparison artifacts.",
    }
    comparison_text = canonical_json_dumps(comparison)
    output_text = canonical_json_dumps(output)
    commit_id = f"shadow-commit-{source_hash[:16]}"
    try:
        transaction = Transaction(
            tx_id=commit_id,
            segment_id=run_id,
            scene_root=run_root,
            generation_id=f"generation-{source_hash[:16]}",
            parent_commit_id="",
        )
        transaction.stage("SHADOW_OUTPUT.json", output_text)
        transaction.stage("comparison/MASTER_FORMAT_BUDGET_CHECKS.json", comparison_text)
        prepared = transaction.prepare(
            metadata={
                "run_kind": "vnext_shadow",
                "run_id": run_id,
                "mode": config.mode,
                "episode_id": config.episode_id,
                "source_script_sha256": source_hash,
                "external_submission": False,
                "writes_to_v4_delivery": False,
                "creative_generation_performed": False,
            }
        )
        transaction.commit()
    except TransactionError as exc:
        raise ShadowError(f"atomic Shadow transaction failed: {exc}") from exc

    commit_manifest_path = run_root / "commits" / commit_id / "COMMIT_MANIFEST.json"
    if not commit_manifest_path.is_file():
        raise ShadowError("atomic Shadow commit did not produce COMMIT_MANIFEST.json")
    manifest = {
        "schema_name": SHADOW_SCHEMA_NAME,
        "schema_version": SHADOW_SCHEMA_VERSION,
        "status": "COMPLETED",
        "run_id": run_id,
        "mode": "shadow_only",
        "episode_id": config.episode_id,
        "source_script": {
            "sha256": source_hash,
            "size_bytes": script_path.stat().st_size,
            "filename": script_path.name,
        },
        "isolation": {
            "isolated_session": True,
            "uses_v4_cache": False,
            "uses_v4_generation_chain": False,
            "writes_to_v4_delivery": False,
            "external_submission": False,
        },
        "atomic_commit": {
            "commit_id": commit_id,
            "commit_manifest_path": str(commit_manifest_path.relative_to(run_root)),
            "commit_manifest_sha256": stable_hash_file(commit_manifest_path),
            "artifact_count": len(prepared["artifacts"]),
        },
        "comparison_ready": True,
        # The comparison artifact is committed immutably with the Shadow run;
        # a root-level manifest must reference that actual commit path rather
        # than a convenient-but-nonexistent working-directory alias.
        "comparison_path": (
            f"commits/{commit_id}/comparison/MASTER_FORMAT_BUDGET_CHECKS.json"
        ),
        "vnext_output": output,
        "production_ready": False,
    }
    _atomic_write(manifest_path, manifest)
    return _result_from_manifest(manifest, manifest_path, reused=False)
