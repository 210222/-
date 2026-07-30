"""Structural validation, leak scanning, and scoped invalidation for projections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Tuple

from .contracts import DirectorContractError, VisualExecutionContract
from .projection import StoryboardProjection, VideoProjection, _shot_node


class ProjectionValidationError(DirectorContractError):
    pass


_PROMPT_LEAKS = (
    ("hash", re.compile(r"\b[a-f0-9]{64}\b|sha[- ]?256", re.IGNORECASE)),
    ("global_time", re.compile(r"\bglobal\b|全局\s*\d", re.IGNORECASE)),
    ("state_summary", re.compile(r"状态摘要|status\s+summary", re.IGNORECASE)),
    ("internal_id", re.compile(r"\b(?:VEC|SEG|SH|DIALOGUE|DECISION)-[A-Z0-9-]+\b", re.IGNORECASE)),
    ("legacy_master", re.compile(r"@图片\d|主连续性板|master[_ ]continuity|director[_ ]master", re.IGNORECASE)),
    ("review_or_next", re.compile(r"审查结论|审核结论|下一段|next\s+segment|continue\s+to\s+next", re.IGNORECASE)),
    ("literary_aside", re.compile(r"戏剧反讽|thematic\s+irony|旁白注释", re.IGNORECASE)),
    ("negative_noun", re.compile(r"不要出现|不得出现|禁止出现|do\s+not\s+(?:show|include)|no\s+\w+", re.IGNORECASE)),
)


def assert_prompt_pure(prompt: str) -> None:
    if not prompt.strip():
        raise ProjectionValidationError("creative prompt cannot be empty")
    for name, pattern in _PROMPT_LEAKS:
        if pattern.search(prompt):
            raise ProjectionValidationError(f"creative prompt leaks forbidden {name}")


def assert_projection_homology(
    vec: VisualExecutionContract, storyboard: StoryboardProjection, video: VideoProjection
) -> None:
    """Compare fields/topology, never a natural-language similarity score."""

    expected = tuple(_shot_node(shot) for shot in vec.shots)
    if expected != tuple(storyboard.shot_nodes) or expected != tuple(video.shot_nodes):
        raise ProjectionValidationError("storyboard and video AST shot nodes are not homologous")
    if len(expected) != len(vec.shots):
        raise ProjectionValidationError("projection AST does not cover every VEC shot")
    for manifest in (storyboard.manifest, video.manifest):
        if manifest.contract_fingerprint != vec.fingerprint:
            raise ProjectionValidationError("projection manifest contract fingerprint mismatch")
        if manifest.blocking_commit_hashes != (vec.blocking_commit.fingerprint,):
            raise ProjectionValidationError("projection manifest BlockingCommit mismatch")
        if manifest.decision_ids != tuple(item.decision_id for item in vec.decisions):
            raise ProjectionValidationError("projection manifest decision chain mismatch")
    if storyboard.manifest.reference_binding_fingerprint != video.manifest.reference_binding_fingerprint:
        raise ProjectionValidationError("projection reference bindings differ")
    if storyboard.manifest.audio_binding_fingerprint != video.manifest.audio_binding_fingerprint:
        raise ProjectionValidationError("projection audio bindings differ")
    source_shots = {f"shot:{shot.shot_id}" for shot in vec.shots}
    panel_shots = {source for panel in storyboard.panels for source in panel.source_node_ids if source.startswith("shot:")}
    if not source_shots.issubset(panel_shots):
        raise ProjectionValidationError("storyboard omits a VEC shot source")
    vec_boundaries = {(item.from_shot_id, item.to_shot_id, item.mode, item.reason) for item in vec.boundaries}
    if set(video.boundary_nodes) != vec_boundaries:
        raise ProjectionValidationError("video boundary topology differs from VEC")
    assert_prompt_pure(storyboard.prompt_text)
    assert_prompt_pure(video.prompt_text)


def assert_no_repeated_dialogue(
    vec: VisualExecutionContract, completed_dialogue: Iterable[tuple[str, str]] = ()
) -> None:
    """A frozen/completed segment can prohibit a later repeated spoken line."""

    seen = {(character, " ".join(text.lower().split())) for character, text in completed_dialogue}
    for event in vec.dialogue_events:
        key = (event.character_id, " ".join(event.text.lower().split()))
        if key in seen:
            raise ProjectionValidationError("dialogue repeats a completed segment line")
        seen.add(key)


@dataclass(frozen=True)
class InvalidationResult:
    changed_node_ids: Tuple[str, ...]
    invalidated_node_ids: Tuple[str, ...]


class ProjectionDependencyIndex:
    """Maps a changed VEC/reference/adapter node to only its local descendants."""

    def __init__(self, edges: Mapping[str, Tuple[str, ...]]) -> None:
        self._edges = {key: tuple(value) for key, value in edges.items()}

    @classmethod
    def from_vec(cls, vec: VisualExecutionContract, *, adapter_version: str) -> "ProjectionDependencyIndex":
        edges: dict[str, Tuple[str, ...]] = {}
        for shot in vec.shots:
            shot_node = f"shot:{shot.shot_id}"
            edges[f"beat:{shot.blocking_beat_id}"] = tuple(set(edges.get(f"beat:{shot.blocking_beat_id}", ()) + (shot_node,)))
            edges[shot_node] = (f"storyboard:{shot.shot_id}", f"video:{shot.shot_id}")
        for boundary in vec.boundaries:
            boundary_node = f"boundary:{boundary.boundary_id}"
            edges[boundary_node] = (f"storyboard:{boundary.boundary_id}", f"video-boundary:{boundary.boundary_id}")
        edges[f"adapter:{adapter_version}"] = (f"adapter-payload:{adapter_version}",)
        return cls(edges)

    def invalidate(self, changed_node_ids: Sequence[str]) -> InvalidationResult:
        pending = list(changed_node_ids)
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            pending.extend(self._edges.get(current, ()))
        return InvalidationResult(tuple(changed_node_ids), tuple(sorted(visited)))
