"""MODE:P vNext — filesystem staging, atomic commit, and recovery.

The original V6.2 object only toggled an in-memory ``committed`` boolean.  This
module keeps that small API for compatibility, while adding the real scene
filesystem transaction required by LOOP §21 and §23:

* artifacts are written under ``staging/<generation_id>``;
* a hash-bound manifest is validated before promotion;
* promotion to ``commits/<commit_id>`` is a same-volume atomic rename;
* ``current.json`` and ``delivery/current.json`` are atomically replaced;
* delivery versions are built off to the side, so readers never see a partial
  mirror;
* crash recovery either promotes one unambiguous complete candidate or marks
  an incomplete staging directory abandoned.  It never stitches partial files.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Tuple


MANIFEST_NAME = "COMMIT_MANIFEST.json"
CURRENT_POINTER_NAME = "current.json"
ABANDONED_NAME = "ABANDONED.json"


class TransactionError(Exception):
    """A filesystem transaction could not be safely completed."""


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalise_text(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")


def _safe_relative_path(raw: str) -> str:
    candidate = raw.replace("\\", "/")
    path = PurePosixPath(candidate)
    if (
        not candidate
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in path.parts)
        or any(":" in part for part in path.parts)
    ):
        raise TransactionError(f"unsafe artifact path: {raw!r}")
    if path.name in {MANIFEST_NAME, ABANDONED_NAME}:
        raise TransactionError(f"reserved artifact path: {raw!r}")
    return path.as_posix()


def _safe_component(raw: str, label: str) -> str:
    if (
        not raw
        or raw in {".", ".."}
        or "/" in raw
        or "\\" in raw
        or ":" in raw
        or raw.endswith((" ", "."))
        or any(ord(character) < 32 for character in raw)
    ):
        raise TransactionError(f"unsafe {label}: {raw!r}")
    return raw


def _resolve_within(root: Path, relative: str) -> Path:
    target = (root / Path(relative)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise TransactionError(
            f"path escapes transaction root: {relative!r}"
        ) from exc
    return target


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Write one file and atomically replace its destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        with temp_path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write_bytes(path, _canonical_json_bytes(value))


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TransactionError(f"invalid JSON file: {path}") from exc
    if not isinstance(value, dict):
        raise TransactionError(f"JSON object required: {path}")
    return value


def _append_event(scene_root: Path, event: Mapping[str, Any]) -> None:
    event_path = scene_root / "telemetry" / "transaction_events.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical_json_bytes(event)
    with event_path.open("ab") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _validate_artifact_set(
    directory: Path,
    manifest: Mapping[str, Any],
) -> List[str]:
    violations: List[str] = []
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return ["manifest has no artifacts"]

    declared_paths: set[str] = set()
    for record in artifacts:
        if not isinstance(record, dict):
            violations.append("artifact record is not an object")
            continue
        try:
            relative = _safe_relative_path(str(record.get("path", "")))
        except TransactionError as exc:
            violations.append(str(exc))
            continue
        if relative in declared_paths:
            violations.append(f"duplicate artifact path: {relative}")
            continue
        declared_paths.add(relative)
        artifact_path = _resolve_within(directory, relative)
        if not artifact_path.is_file() or artifact_path.is_symlink():
            violations.append(f"artifact missing or not regular: {relative}")
            continue
        expected_hash = str(record.get("sha256", ""))
        actual_hash = _sha256_file(artifact_path)
        if actual_hash != expected_hash:
            violations.append(
                f"artifact hash mismatch for {relative}: "
                f"{actual_hash} != {expected_hash}"
            )
        expected_size = record.get("size_bytes")
        if not isinstance(expected_size, int) or artifact_path.stat().st_size != expected_size:
            violations.append(f"artifact size mismatch for {relative}")

    actual_paths = {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file() and path.name not in {MANIFEST_NAME, ABANDONED_NAME}
    }
    if actual_paths != declared_paths:
        violations.append(
            f"artifact set mismatch: actual={sorted(actual_paths)!r}, "
            f"declared={sorted(declared_paths)!r}"
        )
    return violations


def _validate_candidate(
    directory: Path,
    expected_commit_id: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    manifest_path = directory / MANIFEST_NAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return None, [f"missing regular {MANIFEST_NAME}"]
    try:
        manifest = _read_json(manifest_path)
    except TransactionError as exc:
        return None, [str(exc)]
    violations: List[str] = []
    if manifest.get("status") != "PREPARED":
        violations.append("manifest status is not PREPARED")
    directory_commit_id = expected_commit_id or directory.name
    if manifest.get("commit_id") != directory_commit_id:
        violations.append(
            f"commit_id {manifest.get('commit_id')!r} != "
            f"expected {directory_commit_id!r}"
        )
    violations.extend(_validate_artifact_set(directory, manifest))
    return manifest, violations


def _validate_staging_candidate(
    directory: Path,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    manifest_path = directory / MANIFEST_NAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return None, [f"missing regular {MANIFEST_NAME}"]
    try:
        manifest = _read_json(manifest_path)
    except TransactionError as exc:
        return None, [str(exc)]
    commit_id = str(manifest.get("commit_id", ""))
    parsed, violations = _validate_candidate(directory, commit_id)
    if manifest.get("generation_id") != directory.name:
        violations.append(
            f"generation_id {manifest.get('generation_id')!r} != "
            f"staging directory {directory.name!r}"
        )
    return parsed, violations


def _build_delivery_version(scene_root: Path, commit_id: str) -> Path:
    commit_dir = scene_root / "commits" / commit_id
    version_root = scene_root / "delivery" / "versions"
    version_root.mkdir(parents=True, exist_ok=True)
    version_dir = version_root / commit_id
    if version_dir.exists():
        manifest, violations = _validate_candidate(version_dir)
        if manifest is None or violations:
            raise TransactionError(
                f"existing delivery version is invalid: {violations}"
            )
        return version_dir

    temp_dir = version_root / f".{commit_id}.{uuid.uuid4().hex}.staging"
    try:
        shutil.copytree(commit_dir, temp_dir)
        manifest, violations = _validate_candidate(temp_dir, commit_id)
        if manifest is None or violations:
            raise TransactionError(
                f"delivery version validation failed: {violations}"
            )
        os.replace(temp_dir, version_dir)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    return version_dir


def _pointer_payload(scene_root: Path, commit_id: str) -> Dict[str, Any]:
    manifest_path = scene_root / "commits" / commit_id / MANIFEST_NAME
    return {
        "commit_id": commit_id,
        "manifest_sha256": _sha256_file(manifest_path),
        "updated_at_epoch": time.time(),
    }


def _activate_commit(scene_root: Path, commit_id: str) -> None:
    """Make a fully validated commit current without exposing partial delivery."""
    commit_dir = scene_root / "commits" / commit_id
    manifest, violations = _validate_candidate(commit_dir)
    if manifest is None or violations:
        raise TransactionError(f"commit candidate invalid: {violations}")

    # Build the hidden immutable delivery version before changing pointers.
    _build_delivery_version(scene_root, commit_id)
    pointer = _pointer_payload(scene_root, commit_id)
    _atomic_write_json(scene_root / CURRENT_POINTER_NAME, pointer)
    _atomic_write_json(scene_root / "delivery" / CURRENT_POINTER_NAME, pointer)


@dataclass(frozen=True)
class RecoveryReport:
    """Deterministic result of one scene recovery pass."""

    current_commit_id: str = ""
    promoted_commit_ids: Tuple[str, ...] = ()
    abandoned_staging: Tuple[str, ...] = ()
    delivery_repaired: bool = False
    errors: Tuple[str, ...] = ()


@dataclass
class Transaction:
    """One in-memory or filesystem-backed scene transaction.

    Supplying ``scene_root`` enables the production filesystem behaviour.
    Omitting it preserves the small legacy in-memory API used by early callers.
    """

    tx_id: str
    segment_id: str
    scene_root: Optional[Path] = None
    generation_id: str = ""
    parent_commit_id: str = ""
    staging: Dict[str, str] = field(default_factory=dict)
    committed: bool = False
    failed: bool = False
    failure_reason: str = ""
    prepared: bool = False

    def __post_init__(self) -> None:
        if not self.tx_id or not self.segment_id:
            raise TransactionError("tx_id and segment_id are required")
        _safe_component(self.tx_id, "tx_id")
        if self.scene_root is not None:
            self.scene_root = Path(self.scene_root).resolve()
        if not self.generation_id:
            self.generation_id = self.tx_id
        _safe_component(self.generation_id, "generation_id")

    @property
    def staging_dir(self) -> Optional[Path]:
        if self.scene_root is None:
            return None
        return self.scene_root / "staging" / self.generation_id

    @property
    def commit_dir(self) -> Optional[Path]:
        if self.scene_root is None:
            return None
        return self.scene_root / "commits" / self.tx_id

    def stage(self, artifact_name: str, content: str) -> None:
        if self.failed:
            raise TransactionError(f"TX '{self.tx_id}' already failed")
        if self.committed:
            raise TransactionError(f"TX '{self.tx_id}' already committed")
        if self.prepared:
            raise TransactionError(f"TX '{self.tx_id}' is already prepared")
        relative = _safe_relative_path(artifact_name)
        normalised = _normalise_text(content)
        self.staging[relative] = normalised
        if self.scene_root is not None:
            staging_dir = self.staging_dir
            assert staging_dir is not None
            target = _resolve_within(staging_dir, relative)
            _atomic_write_bytes(target, normalised.encode("utf-8"))

    def validate(self) -> List[str]:
        violations: List[str] = []
        if not self.staging:
            violations.append("Staging area is empty — nothing to commit")
        for name, content in self.staging.items():
            if not content.strip():
                violations.append(f"Empty content in '{name}'")
            if self.scene_root is not None:
                staging_dir = self.staging_dir
                assert staging_dir is not None
                target = _resolve_within(staging_dir, name)
                if not target.is_file() or target.is_symlink():
                    violations.append(f"Staged file missing or not regular: '{name}'")
                elif _sha256_file(target) != _sha256_bytes(
                    content.encode("utf-8")
                ):
                    violations.append(f"Staged file differs from memory: '{name}'")
        return violations

    def prepare(
        self,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        if self.scene_root is None:
            violations = self.validate()
            if violations:
                raise TransactionError(
                    f"Validation failed for TX '{self.tx_id}': "
                    + "; ".join(violations)
                )
            self.prepared = True
            return {
                "commit_id": self.tx_id,
                "generation_id": self.generation_id,
                "segment_id": self.segment_id,
                "status": "PREPARED",
            }
        if self.failed or self.committed:
            raise TransactionError(
                f"TX '{self.tx_id}' cannot be prepared in its current state"
            )
        if self.prepared:
            staging_dir = self.staging_dir
            assert staging_dir is not None
            return _read_json(staging_dir / MANIFEST_NAME)

        violations = self.validate()
        if violations:
            raise TransactionError(
                f"Validation failed for TX '{self.tx_id}': "
                + "; ".join(violations)
            )

        staging_dir = self.staging_dir
        assert staging_dir is not None
        artifacts = []
        for relative in sorted(self.staging):
            path = _resolve_within(staging_dir, relative)
            artifacts.append(
                {
                    "path": relative,
                    "sha256": _sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
        manifest: Dict[str, Any] = {
            "schema_name": "mode_p_commit_manifest",
            "schema_version": "1.0.0",
            "status": "PREPARED",
            "commit_id": self.tx_id,
            "parent_commit_id": self.parent_commit_id,
            "generation_id": self.generation_id,
            "segment_id": self.segment_id,
            "created_at_epoch": time.time(),
            "artifacts": artifacts,
            "metadata": dict(metadata or {}),
        }
        _atomic_write_json(staging_dir / MANIFEST_NAME, manifest)
        parsed, final_violations = _validate_staging_candidate(staging_dir)
        if parsed is None or final_violations:
            raise TransactionError(
                f"Prepared staging failed final validation: {final_violations}"
            )
        self.prepared = True
        return manifest

    def commit(self) -> None:
        if self.failed:
            raise TransactionError(
                f"Cannot commit failed TX '{self.tx_id}': {self.failure_reason}"
            )
        if self.committed:
            raise TransactionError(f"TX '{self.tx_id}' already committed")
        if self.scene_root is None:
            violations = self.validate()
            if violations:
                raise TransactionError(
                    f"Validation failed for TX '{self.tx_id}': "
                    + "; ".join(violations)
                )
            self.committed = True
            return

        if not self.prepared:
            self.prepare()
        staging_dir = self.staging_dir
        commit_dir = self.commit_dir
        assert staging_dir is not None and commit_dir is not None
        current_id, current_errors = _load_valid_current(self.scene_root)
        if current_errors:
            raise TransactionError(
                "cannot commit over an invalid current pointer: "
                + "; ".join(current_errors)
            )
        if current_id != self.parent_commit_id:
            raise TransactionError(
                f"parent commit {self.parent_commit_id!r} does not match "
                f"current {current_id!r}"
            )
        commit_dir.parent.mkdir(parents=True, exist_ok=True)
        if commit_dir.exists():
            raise TransactionError(f"commit already exists: {self.tx_id}")

        try:
            os.replace(staging_dir, commit_dir)
            _activate_commit(self.scene_root, self.tx_id)
            _append_event(
                self.scene_root,
                {
                    "event": "COMMIT_ACTIVATED",
                    "commit_id": self.tx_id,
                    "generation_id": self.generation_id,
                    "segment_id": self.segment_id,
                    "at_epoch": time.time(),
                },
            )
        except Exception as exc:
            self.failed = True
            self.failure_reason = str(exc)
            if isinstance(exc, TransactionError):
                raise
            raise TransactionError(
                f"filesystem commit failed for '{self.tx_id}': {exc}"
            ) from exc
        self.committed = True

    def fail(self, reason: str) -> None:
        if self.committed:
            raise TransactionError(
                f"Cannot fail committed TX '{self.tx_id}'"
            )
        self.failed = True
        self.failure_reason = reason


def _load_valid_current(scene_root: Path) -> Tuple[str, List[str]]:
    pointer_path = scene_root / CURRENT_POINTER_NAME
    if not pointer_path.exists():
        return "", []
    try:
        pointer = _read_json(pointer_path)
    except TransactionError as exc:
        return "", [str(exc)]
    commit_id = str(pointer.get("commit_id", ""))
    if not commit_id:
        return "", ["current pointer has no commit_id"]
    commit_dir = scene_root / "commits" / commit_id
    manifest, violations = _validate_candidate(commit_dir)
    if manifest is None or violations:
        return "", [f"current commit invalid: {violations}"]
    expected_manifest_hash = str(pointer.get("manifest_sha256", ""))
    actual_manifest_hash = _sha256_file(commit_dir / MANIFEST_NAME)
    if expected_manifest_hash != actual_manifest_hash:
        return "", ["current pointer manifest hash mismatch"]
    return commit_id, []


def _abandon_staging(
    scene_root: Path,
    staging_dir: Path,
    reasons: List[str],
) -> str:
    abandoned_root = scene_root / "staging" / "abandoned"
    abandoned_root.mkdir(parents=True, exist_ok=True)
    target = abandoned_root / (
        f"{staging_dir.name}-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
    )
    os.replace(staging_dir, target)
    _atomic_write_json(
        target / ABANDONED_NAME,
        {
            "generation_id": staging_dir.name,
            "reasons": list(reasons),
            "abandoned_at_epoch": time.time(),
        },
    )
    return target.relative_to(scene_root).as_posix()


def recover_scene(scene_root: Path) -> RecoveryReport:
    """Recover one scene from the last valid commit and uncommitted staging.

    A complete candidate is promoted only when it is the single candidate whose
    parent matches the current commit.  Ambiguity is fail-closed.  Incomplete
    staging is moved to ``staging/abandoned`` with a diagnostic record.
    """

    root = Path(scene_root).resolve()
    for relative in (
        "staging",
        "commits",
        "delivery/versions",
        "telemetry",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)

    current_id, current_errors = _load_valid_current(root)
    errors = list(current_errors)
    promoted: List[str] = []
    abandoned: List[str] = []
    candidates: List[Tuple[str, Path, str]] = []

    staging_root = root / "staging"
    for path in sorted(staging_root.iterdir(), key=lambda item: item.name):
        if not path.is_dir() or path.name == "abandoned":
            continue
        manifest, violations = _validate_staging_candidate(path)
        if manifest is None or violations:
            abandoned.append(
                _abandon_staging(root, path, violations or ["invalid staging"])
            )
            continue
        parent = str(manifest.get("parent_commit_id", ""))
        if parent != current_id:
            abandoned.append(
                _abandon_staging(
                    root,
                    path,
                    [
                        f"parent_commit_id {parent!r} does not match "
                        f"current {current_id!r}"
                    ],
                )
            )
            continue
        candidates.append((str(manifest["commit_id"]), path, "staging"))

    commits_root = root / "commits"
    for path in sorted(commits_root.iterdir(), key=lambda item: item.name):
        if not path.is_dir() or path.name == current_id:
            continue
        manifest, violations = _validate_candidate(path)
        if manifest is None or violations:
            errors.append(f"invalid orphan commit {path.name}: {violations}")
            continue
        parent = str(manifest.get("parent_commit_id", ""))
        if parent == current_id:
            candidates.append((str(manifest["commit_id"]), path, "commit"))

    if current_errors:
        errors.append("recovery blocked because current pointer is invalid")
    elif len(candidates) > 1:
        errors.append(
            "ambiguous recovery candidates: "
            + ", ".join(sorted(candidate[0] for candidate in candidates))
        )
    elif len(candidates) == 1:
        commit_id, candidate_path, location = candidates[0]
        commit_dir = commits_root / commit_id
        if location == "staging":
            if commit_dir.exists():
                errors.append(f"commit destination already exists: {commit_id}")
            else:
                os.replace(candidate_path, commit_dir)
        if not errors:
            _activate_commit(root, commit_id)
            current_id = commit_id
            promoted.append(commit_id)

    delivery_repaired = False
    if current_id and not errors:
        expected_pointer = _pointer_payload(root, current_id)
        delivery_pointer_path = root / "delivery" / CURRENT_POINTER_NAME
        repair_needed = True
        if delivery_pointer_path.is_file():
            try:
                delivery_pointer = _read_json(delivery_pointer_path)
                repair_needed = (
                    delivery_pointer.get("commit_id") != current_id
                    or delivery_pointer.get("manifest_sha256")
                    != expected_pointer["manifest_sha256"]
                )
            except TransactionError:
                repair_needed = True
        if repair_needed:
            _build_delivery_version(root, current_id)
            _atomic_write_json(delivery_pointer_path, expected_pointer)
            delivery_repaired = True

    _append_event(
        root,
        {
            "event": "RECOVERY",
            "current_commit_id": current_id,
            "promoted_commit_ids": promoted,
            "abandoned_staging": abandoned,
            "errors": errors,
            "at_epoch": time.time(),
        },
    )
    return RecoveryReport(
        current_commit_id=current_id,
        promoted_commit_ids=tuple(promoted),
        abandoned_staging=tuple(abandoned),
        delivery_repaired=delivery_repaired,
        errors=tuple(errors),
    )
