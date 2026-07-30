"""Immutable rollback manifests and a fail-closed vNext control record.

R3.1 does not switch the real MODE:P entrypoint.  It binds an already
prepared, read-only v4 rollback archive to vNext evidence, and writes one
atomic *vNext-only* control record for rollback drills and kill-switch drills.
No method in this module copies, deletes, or writes a v4 Session/delivery.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .canonical_serialization import canonical_json_dumps, stable_hash_file


class RollbackError(RuntimeError):
    """The requested rollback/kill-switch operation is unsafe or invalid."""


class ManifestIntegrityError(RollbackError):
    """A manifest, archive artifact, or retained evidence no longer verifies."""


class KillSwitchActive(RollbackError):
    """A second incident request tried to overwrite an armed kill switch."""


SCHEMA_MANIFEST = "mode_p_vnext_rollback_manifest"
SCHEMA_CONTROL = "mode_p_vnext_release_control"
SCHEMA_VERSION = "1.0.0"
CONTROL_FILENAME = "RELEASE_CONTROL.json"
MANIFEST_DIRECTORY = "rollback_manifests"
CURRENT_MODE = "current"
VNEXT_MODES = frozenset(
    {"vnext_shadow", "vnext_pilot", "vnext_canary", "vnext_production"}
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_dumps(dict(payload)).encode("utf-8")).hexdigest()


def _safe_relative(value: str | Path, *, label: str) -> str:
    text = str(value).replace("\\", "/")
    candidate = PurePath(text)
    if not text or candidate.is_absolute() or ":" in text:
        raise RollbackError(f"{label} must be a non-empty relative path")
    parts = candidate.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise RollbackError(f"{label} contains an unsafe relative path")
    return "/".join(parts)


def _safe_regular_file(root: Path, relative: str, *, label: str) -> Path:
    root = Path(root)
    if root.is_symlink():
        raise RollbackError(f"{label} root cannot be a symbolic link")
    resolved_root = root.resolve(strict=True)
    normalized = _safe_relative(relative, label=label)
    candidate = root
    for component in PurePath(normalized).parts:
        candidate = candidate / component
        if candidate.is_symlink():
            raise RollbackError(f"{label} cannot traverse a symbolic link")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise RollbackError(f"{label} escapes or is missing from its declared root") from exc
    if not resolved.is_file():
        raise RollbackError(f"{label} must name a regular file")
    return resolved


def _normalise_scope(value: Mapping[str, Sequence[str]]) -> Dict[str, list[str]]:
    if not isinstance(value, Mapping):
        raise RollbackError("affected scope must be an object")
    unexpected = set(value) - {"episode_ids", "scene_ids"}
    if unexpected:
        raise RollbackError(f"affected scope has unsupported keys: {sorted(unexpected)}")
    normalised: Dict[str, list[str]] = {}
    for key in ("episode_ids", "scene_ids"):
        raw = value.get(key, [])
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise RollbackError(f"{key} must be a list of identifiers")
        items = list(raw)
        if any(not isinstance(item, str) or not _SAFE_ID.fullmatch(item) for item in items):
            raise RollbackError(f"{key} contains an unsafe identifier")
        if len(set(items)) != len(items):
            raise RollbackError(f"{key} contains duplicate identifiers")
        normalised[key] = sorted(items)
    if not normalised["episode_ids"] and not normalised["scene_ids"]:
        raise RollbackError("affected scope cannot be empty")
    return normalised


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Publish a complete UTF-8 canonical record, or leave the old one intact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    data = canonical_json_dumps(dict(payload)).encode("utf-8")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class ArchiveArtifact:
    relative_path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ArchiveArtifact":
        try:
            relative_path = _safe_relative(value["relative_path"], label="archive artifact")
            sha256 = str(value["sha256"])
            size_bytes = int(value["size_bytes"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ManifestIntegrityError("invalid archive artifact") from exc
        if not re.fullmatch(r"[0-9a-f]{64}", sha256) or size_bytes < 0:
            raise ManifestIntegrityError("archive artifact integrity fields are invalid")
        return cls(relative_path=relative_path, sha256=sha256, size_bytes=size_bytes)


@dataclass(frozen=True)
class RollbackManifest:
    bundle_id: str
    created_at_utc: str
    entry_relative_path: str
    archive_artifacts: Tuple[ArchiveArtifact, ...]
    release_evidence_relative_path: str
    release_evidence_sha256: str
    retained_commit_ids: Tuple[str, ...]
    affected_scope: Dict[str, list[str]]
    integrity_sha256: str = ""

    def _unsigned_dict(self) -> Dict[str, Any]:
        return {
            "schema_name": SCHEMA_MANIFEST,
            "schema_version": SCHEMA_VERSION,
            "bundle_id": self.bundle_id,
            "created_at_utc": self.created_at_utc,
            "rollback_target": {
                "entry_id": "current_v4_archive",
                "entry_relative_path": self.entry_relative_path,
                "artifacts": [artifact.to_dict() for artifact in self.archive_artifacts],
            },
            "vnext_provenance": {
                "release_evidence_relative_path": self.release_evidence_relative_path,
                "release_evidence_sha256": self.release_evidence_sha256,
                "retained_commit_ids": list(self.retained_commit_ids),
            },
            "affected_scope": self.affected_scope,
        }

    def with_integrity(self) -> "RollbackManifest":
        return RollbackManifest(
            bundle_id=self.bundle_id,
            created_at_utc=self.created_at_utc,
            entry_relative_path=self.entry_relative_path,
            archive_artifacts=self.archive_artifacts,
            release_evidence_relative_path=self.release_evidence_relative_path,
            release_evidence_sha256=self.release_evidence_sha256,
            retained_commit_ids=self.retained_commit_ids,
            affected_scope=dict(self.affected_scope),
            integrity_sha256=_hash_payload(self._unsigned_dict()),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = self._unsigned_dict()
        payload["integrity_sha256"] = self.integrity_sha256
        return payload

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RollbackManifest":
        try:
            target = value["rollback_target"]
            provenance = value["vnext_provenance"]
            artifacts = tuple(ArchiveArtifact.from_dict(item) for item in target["artifacts"])
            manifest = cls(
                bundle_id=str(value["bundle_id"]),
                created_at_utc=str(value["created_at_utc"]),
                entry_relative_path=_safe_relative(target["entry_relative_path"], label="entry"),
                archive_artifacts=artifacts,
                release_evidence_relative_path=_safe_relative(
                    provenance["release_evidence_relative_path"], label="release evidence"
                ),
                release_evidence_sha256=str(provenance["release_evidence_sha256"]),
                retained_commit_ids=tuple(str(item) for item in provenance["retained_commit_ids"]),
                affected_scope=_normalise_scope(value["affected_scope"]),
                integrity_sha256=str(value["integrity_sha256"]),
            )
        except (KeyError, TypeError, ValueError, RollbackError) as exc:
            raise ManifestIntegrityError("invalid rollback manifest shape") from exc
        if value.get("schema_name") != SCHEMA_MANIFEST or value.get("schema_version") != SCHEMA_VERSION:
            raise ManifestIntegrityError("unsupported rollback manifest schema")
        if not _SAFE_ID.fullmatch(manifest.bundle_id):
            raise ManifestIntegrityError("unsafe rollback bundle identifier")
        if not manifest.archive_artifacts:
            raise ManifestIntegrityError("rollback manifest has no archive artifacts")
        paths = [artifact.relative_path for artifact in manifest.archive_artifacts]
        if len(paths) != len(set(paths)) or manifest.entry_relative_path not in paths:
            raise ManifestIntegrityError("rollback archive artifacts are incomplete or duplicate")
        if not re.fullmatch(r"[0-9a-f]{64}", manifest.release_evidence_sha256):
            raise ManifestIntegrityError("invalid release evidence hash")
        if not manifest.retained_commit_ids or any(
            not _SAFE_ID.fullmatch(item) for item in manifest.retained_commit_ids
        ):
            raise ManifestIntegrityError("retained commit identifiers are invalid")
        if len(set(manifest.retained_commit_ids)) != len(manifest.retained_commit_ids):
            raise ManifestIntegrityError("retained commit identifiers are duplicated")
        if manifest.integrity_sha256 != _hash_payload(manifest._unsigned_dict()):
            raise ManifestIntegrityError("rollback manifest integrity hash does not verify")
        return manifest

    def verify(self, *, archive_root: Path, vnext_root: Path) -> None:
        # Reparse through the public verifier so a constructed object cannot skip checks.
        RollbackManifest.from_dict(self.to_dict())
        for artifact in self.archive_artifacts:
            source = _safe_regular_file(archive_root, artifact.relative_path, label="archive artifact")
            if source.stat().st_size != artifact.size_bytes or stable_hash_file(source) != artifact.sha256:
                raise ManifestIntegrityError("archive artifact hash or size drifted")
        evidence = _safe_regular_file(vnext_root, self.release_evidence_relative_path, label="release evidence")
        if stable_hash_file(evidence) != self.release_evidence_sha256:
            raise ManifestIntegrityError("retained vNext release evidence hash drifted")


@dataclass(frozen=True)
class ReleaseControlState:
    generation: int
    active_mode: str
    active_entry_id: str
    rollback_manifest_relative_path: str
    rollback_manifest_sha256: str
    rollback_reason_code: str
    rollback_actor: str
    rolled_back_at_utc: str
    affected_scope: Dict[str, list[str]]
    kill_switch_armed: bool
    kill_reason_code: str
    armed_by: str
    armed_at_utc: str
    request_id: str
    integrity_sha256: str = ""

    @classmethod
    def current_default(cls) -> "ReleaseControlState":
        return cls(
            generation=0,
            active_mode=CURRENT_MODE,
            active_entry_id="current_v4_unchanged",
            rollback_manifest_relative_path="",
            rollback_manifest_sha256="",
            rollback_reason_code="",
            rollback_actor="",
            rolled_back_at_utc="",
            affected_scope={"episode_ids": [], "scene_ids": []},
            kill_switch_armed=False,
            kill_reason_code="",
            armed_by="",
            armed_at_utc="",
            request_id="",
        ).with_integrity()

    def _unsigned_dict(self) -> Dict[str, Any]:
        return {
            "schema_name": SCHEMA_CONTROL,
            "schema_version": SCHEMA_VERSION,
            "generation": self.generation,
            "active_mode": self.active_mode,
            "active_entry_id": self.active_entry_id,
            "rollback_manifest_relative_path": self.rollback_manifest_relative_path,
            "rollback_manifest_sha256": self.rollback_manifest_sha256,
            "rollback_reason_code": self.rollback_reason_code,
            "rollback_actor": self.rollback_actor,
            "rolled_back_at_utc": self.rolled_back_at_utc,
            "affected_scope": self.affected_scope,
            "kill_switch": {
                "armed": self.kill_switch_armed,
                "reason_code": self.kill_reason_code,
                "armed_by": self.armed_by,
                "armed_at_utc": self.armed_at_utc,
                "request_id": self.request_id,
            },
        }

    def with_integrity(self) -> "ReleaseControlState":
        return ReleaseControlState(
            generation=self.generation,
            active_mode=self.active_mode,
            active_entry_id=self.active_entry_id,
            rollback_manifest_relative_path=self.rollback_manifest_relative_path,
            rollback_manifest_sha256=self.rollback_manifest_sha256,
            rollback_reason_code=self.rollback_reason_code,
            rollback_actor=self.rollback_actor,
            rolled_back_at_utc=self.rolled_back_at_utc,
            affected_scope=dict(self.affected_scope),
            kill_switch_armed=self.kill_switch_armed,
            kill_reason_code=self.kill_reason_code,
            armed_by=self.armed_by,
            armed_at_utc=self.armed_at_utc,
            request_id=self.request_id,
            integrity_sha256=_hash_payload(self._unsigned_dict()),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = self._unsigned_dict()
        payload["integrity_sha256"] = self.integrity_sha256
        return payload

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ReleaseControlState":
        try:
            kill = value["kill_switch"]
            state = cls(
                generation=int(value["generation"]),
                active_mode=str(value["active_mode"]),
                active_entry_id=str(value["active_entry_id"]),
                rollback_manifest_relative_path=str(value["rollback_manifest_relative_path"]),
                rollback_manifest_sha256=str(value["rollback_manifest_sha256"]),
                rollback_reason_code=str(value["rollback_reason_code"]),
                rollback_actor=str(value["rollback_actor"]),
                rolled_back_at_utc=str(value["rolled_back_at_utc"]),
                affected_scope=_normalise_scope(value["affected_scope"])
                if isinstance(value["affected_scope"], Mapping)
                and (value["affected_scope"].get("episode_ids") or value["affected_scope"].get("scene_ids"))
                else {"episode_ids": [], "scene_ids": []},
                kill_switch_armed=bool(kill["armed"]),
                kill_reason_code=str(kill["reason_code"]),
                armed_by=str(kill["armed_by"]),
                armed_at_utc=str(kill["armed_at_utc"]),
                request_id=str(kill["request_id"]),
                integrity_sha256=str(value["integrity_sha256"]),
            )
        except (AttributeError, KeyError, TypeError, ValueError, RollbackError) as exc:
            raise ManifestIntegrityError("invalid release control state") from exc
        if value.get("schema_name") != SCHEMA_CONTROL or value.get("schema_version") != SCHEMA_VERSION:
            raise ManifestIntegrityError("unsupported release control schema")
        if state.generation < 0 or state.active_mode not in {CURRENT_MODE, *VNEXT_MODES}:
            raise ManifestIntegrityError("invalid active mode in release control state")
        if not _SAFE_ID.fullmatch(state.active_entry_id):
            raise ManifestIntegrityError("unsafe active entry identifier")
        if state.rollback_manifest_relative_path:
            _safe_relative(state.rollback_manifest_relative_path, label="rollback manifest")
        if state.rollback_manifest_sha256 and not re.fullmatch(r"[0-9a-f]{64}", state.rollback_manifest_sha256):
            raise ManifestIntegrityError("invalid rollback manifest hash")
        if state.integrity_sha256 != _hash_payload(state._unsigned_dict()):
            raise ManifestIntegrityError("release control integrity hash does not verify")
        return state


@dataclass(frozen=True)
class EffectiveEntry:
    mode: str
    entry_id: str
    vnext_invocation_allowed: bool
    kill_switch_armed: bool
    reason_code: str


class RollbackController:
    """Write only under a dedicated vNext control root; never a v4 session."""

    def __init__(self, control_root: str | Path) -> None:
        root = Path(control_root)
        if not str(root):
            raise RollbackError("control root is required")
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink():
            raise RollbackError("control root cannot be a symbolic link")
        self.control_root = root.resolve()

    @property
    def state_path(self) -> Path:
        return self.control_root / CONTROL_FILENAME

    @property
    def manifest_root(self) -> Path:
        return self.control_root / MANIFEST_DIRECTORY

    def _manifest_path(self, bundle_id: str) -> Path:
        return self.manifest_root / f"{bundle_id}.json"

    def _load_manifest_file(self, manifest_path: str | Path) -> Tuple[Path, RollbackManifest]:
        raw = Path(manifest_path)
        try:
            resolved = raw.resolve(strict=True)
            resolved.relative_to(self.manifest_root.resolve(strict=True))
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise RollbackError("manifest must be a file owned by this control root") from exc
        if resolved.is_symlink() or not resolved.is_file():
            raise RollbackError("manifest must be a regular control-root file")
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ManifestIntegrityError("rollback manifest is unreadable") from exc
        return resolved, RollbackManifest.from_dict(payload)

    def create_manifest(
        self,
        *,
        archive_root: str | Path,
        entry_relative_path: str | Path,
        archive_artifact_paths: Iterable[str | Path],
        vnext_root: str | Path,
        release_evidence_relative_path: str | Path,
        retained_commit_ids: Iterable[str],
        affected_scope: Mapping[str, Sequence[str]],
        bundle_id: Optional[str] = None,
    ) -> Path:
        archive_root_path = Path(archive_root)
        vnext_root_path = Path(vnext_root)
        entry = _safe_relative(entry_relative_path, label="entry")
        artifacts: list[ArchiveArtifact] = []
        seen: set[str] = set()
        for raw_path in archive_artifact_paths:
            relative = _safe_relative(raw_path, label="archive artifact")
            if relative in seen:
                raise RollbackError("archive artifact paths cannot be duplicated")
            source = _safe_regular_file(archive_root_path, relative, label="archive artifact")
            seen.add(relative)
            artifacts.append(
                ArchiveArtifact(
                    relative_path=relative,
                    sha256=stable_hash_file(source),
                    size_bytes=source.stat().st_size,
                )
            )
        if entry not in seen:
            raise RollbackError("rollback entry must be included in archive artifacts")
        evidence_relative = _safe_relative(release_evidence_relative_path, label="release evidence")
        evidence = _safe_regular_file(vnext_root_path, evidence_relative, label="release evidence")
        commits = tuple(str(item) for item in retained_commit_ids)
        if not commits or len(commits) != len(set(commits)) or any(
            not _SAFE_ID.fullmatch(item) for item in commits
        ):
            raise RollbackError("retained commit identifiers must be unique safe IDs")
        identifier = bundle_id or f"RB_{uuid.uuid4().hex}"
        if not _SAFE_ID.fullmatch(identifier):
            raise RollbackError("rollback bundle identifier is unsafe")
        manifest = RollbackManifest(
            bundle_id=identifier,
            created_at_utc=_utc_now(),
            entry_relative_path=entry,
            archive_artifacts=tuple(sorted(artifacts, key=lambda item: item.relative_path)),
            release_evidence_relative_path=evidence_relative,
            release_evidence_sha256=stable_hash_file(evidence),
            retained_commit_ids=tuple(sorted(commits)),
            affected_scope=_normalise_scope(affected_scope),
        ).with_integrity()
        # Verify before publishing: this reads sources only and never copies them.
        manifest.verify(archive_root=archive_root_path, vnext_root=vnext_root_path)
        path = self._manifest_path(identifier)
        if path.exists():
            raise RollbackError("rollback manifest bundle already exists")
        _atomic_write_json(path, manifest.to_dict())
        return path

    def verify_manifest(
        self,
        manifest_path: str | Path,
        *,
        archive_root: str | Path,
        vnext_root: str | Path,
    ) -> RollbackManifest:
        _, manifest = self._load_manifest_file(manifest_path)
        manifest.verify(archive_root=Path(archive_root), vnext_root=Path(vnext_root))
        return manifest

    def read_state(self) -> ReleaseControlState:
        """Return current on every missing, corrupt, or untrusted state record."""

        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            return ReleaseControlState.from_dict(payload)
        except (AttributeError, OSError, UnicodeDecodeError, json.JSONDecodeError, RollbackError):
            return ReleaseControlState.current_default()

    def _publish_state(self, state: ReleaseControlState) -> ReleaseControlState:
        verified = ReleaseControlState.from_dict(state.with_integrity().to_dict())
        _atomic_write_json(self.state_path, verified.to_dict())
        return verified

    def rollback_to_current(
        self,
        *,
        manifest_path: str | Path,
        archive_root: str | Path,
        vnext_root: str | Path,
        reason_code: str,
        affected_scope: Mapping[str, Sequence[str]],
        actor: str,
        request_id: str,
    ) -> ReleaseControlState:
        if not _SAFE_ID.fullmatch(reason_code) or not _SAFE_ID.fullmatch(actor) or not _SAFE_ID.fullmatch(request_id):
            raise RollbackError("rollback reason, actor, and request ID must be safe IDs")
        scope = _normalise_scope(affected_scope)
        manifest_file, manifest = self._load_manifest_file(manifest_path)
        manifest.verify(archive_root=Path(archive_root), vnext_root=Path(vnext_root))
        if scope != manifest.affected_scope:
            raise RollbackError("rollback scope must match the approved manifest scope")
        previous = self.read_state()
        if previous.kill_switch_armed:
            raise KillSwitchActive("kill switch is armed; no ordinary rollback can overwrite it")
        relative_manifest = manifest_file.relative_to(self.control_root).as_posix()
        next_state = ReleaseControlState(
            generation=previous.generation + 1,
            active_mode=CURRENT_MODE,
            active_entry_id="current_v4_unchanged",
            rollback_manifest_relative_path=relative_manifest,
            rollback_manifest_sha256=stable_hash_file(manifest_file),
            rollback_reason_code=reason_code,
            rollback_actor=actor,
            rolled_back_at_utc=_utc_now(),
            affected_scope=scope,
            kill_switch_armed=False,
            kill_reason_code="",
            armed_by="",
            armed_at_utc="",
            request_id=request_id,
        )
        return self._publish_state(next_state)

    def arm_kill_switch(
        self,
        *,
        manifest_path: str | Path,
        archive_root: str | Path,
        vnext_root: str | Path,
        reason_code: str,
        affected_scope: Mapping[str, Sequence[str]],
        actor: str,
        request_id: str,
    ) -> ReleaseControlState:
        previous = self.read_state()
        if previous.kill_switch_armed:
            if previous.request_id == request_id:
                return previous
            raise KillSwitchActive("kill switch already armed; original incident cannot be overwritten")
        if not _SAFE_ID.fullmatch(reason_code) or not _SAFE_ID.fullmatch(actor) or not _SAFE_ID.fullmatch(request_id):
            raise RollbackError("kill reason, actor, and request ID must be safe IDs")
        scope = _normalise_scope(affected_scope)
        manifest_file, manifest = self._load_manifest_file(manifest_path)
        manifest.verify(archive_root=Path(archive_root), vnext_root=Path(vnext_root))
        if scope != manifest.affected_scope:
            raise RollbackError("kill scope must match the approved manifest scope")
        relative_manifest = manifest_file.relative_to(self.control_root).as_posix()
        # One replacement records both the route-to-current and the incident
        # latch.  There is no intermediate state that could be mistaken for a
        # release permission by a future integration.
        armed = ReleaseControlState(
            generation=previous.generation + 1,
            active_mode=CURRENT_MODE,
            active_entry_id="current_v4_unchanged",
            rollback_manifest_relative_path=relative_manifest,
            rollback_manifest_sha256=stable_hash_file(manifest_file),
            rollback_reason_code=reason_code,
            rollback_actor=actor,
            rolled_back_at_utc=_utc_now(),
            affected_scope=scope,
            kill_switch_armed=True,
            kill_reason_code=reason_code,
            armed_by=actor,
            armed_at_utc=_utc_now(),
            request_id=request_id,
        )
        return self._publish_state(armed)

    def resolve_effective_entry(self) -> EffectiveEntry:
        """Resolve only a verified control record; missing/corrupt is current."""

        state = self.read_state()
        if state.kill_switch_armed:
            return EffectiveEntry(
                mode=CURRENT_MODE,
                entry_id="current_v4_unchanged",
                vnext_invocation_allowed=False,
                kill_switch_armed=True,
                reason_code="KILL_SWITCH_ARMED",
            )
        if state.active_mode in VNEXT_MODES:
            # This can only describe a future, separately authorised release
            # state. R3.1 itself provides no activation API.
            return EffectiveEntry(
                mode=state.active_mode,
                entry_id=state.active_entry_id,
                vnext_invocation_allowed=True,
                kill_switch_armed=False,
                reason_code="VERIFIED_RELEASE_CONTROL",
            )
        return EffectiveEntry(
            mode=CURRENT_MODE,
            entry_id="current_v4_unchanged",
            vnext_invocation_allowed=False,
            kill_switch_armed=False,
            reason_code="CURRENT_DEFAULT",
        )
