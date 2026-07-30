"""Dynamic Board Splitter — split a scene into N independent boards.

Supports dynamic board counts (not hardcoded to 3). Each board gets:
- ENTRY/EXIT boundary states
- Global + local time ranges
- Independent storyboard and video prompt

Never invents facts; every value traces to source contract.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BoardSpec:
    """Specification for one board in a multi-board scene."""
    board_index: int
    board_id: str  # e.g. "Board_A"
    global_time_start: float
    global_time_end: float
    local_duration: float
    entry_state_id: str
    exit_state_id: str
    shot_id: str
    plate_id: str
    characters_in_frame: List[str] = field(default_factory=list)
    required_props: List[str] = field(default_factory=list)
    dialog_ids: List[str] = field(default_factory=list)


@dataclass
class BoundarySpec:
    """Specification for one board-to-board boundary."""
    boundary_index: int
    boundary_id: str
    time_s: float
    boundary_type: str  # scene_entry | continuous | scene_exit
    from_board: Optional[str]
    to_board: Optional[str]
    entry_match_mode: str
    pixel_identical_required: bool
    camera_cut_allowed: bool
    upstream_laf: Optional[str]
    entry_composition: str = ""
    exit_composition: str = ""
    exit_hand_state: str = ""


@dataclass
class SplitResult:
    """Result of splitting a scene into N boards."""
    scene_id: str
    total_duration_s: float
    board_count: int
    boards: List[BoardSpec] = field(default_factory=list)
    boundaries: List[BoundarySpec] = field(default_factory=list)
    master_boundary_cells: int = 0  # N+1 boundary cells

    @property
    def boundary_cell_count(self) -> int:
        """Always N+1 boundary cells for N boards."""
        return self.board_count + 1 if self.board_count > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "total_duration_s": self.total_duration_s,
            "board_count": self.board_count,
            "boundary_cell_count": self.boundary_cell_count,
            "boards": [
                {
                    "board_index": b.board_index,
                    "board_id": b.board_id,
                    "global_time_start": b.global_time_start,
                    "global_time_end": b.global_time_end,
                    "local_duration": b.local_duration,
                    "entry_state_id": b.entry_state_id,
                    "exit_state_id": b.exit_state_id,
                    "shot_id": b.shot_id,
                    "plate_id": b.plate_id,
                    "characters_in_frame": b.characters_in_frame,
                    "required_props": b.required_props,
                    "dialog_ids": b.dialog_ids,
                }
                for b in self.boards
            ],
            "boundaries": [
                {
                    "boundary_index": bnd.boundary_index,
                    "boundary_id": bnd.boundary_id,
                    "time_s": bnd.time_s,
                    "boundary_type": bnd.boundary_type,
                    "from_board": bnd.from_board,
                    "to_board": bnd.to_board,
                    "entry_match_mode": bnd.entry_match_mode,
                    "pixel_identical_required": bnd.pixel_identical_required,
                    "camera_cut_allowed": bnd.camera_cut_allowed,
                    "upstream_laf": bnd.upstream_laf,
                }
                for bnd in self.boundaries
            ],
        }


class BoardSplitter:
    """Deterministic scene-to-board splitter.

    Rules:
    1. Each board <= 15 seconds
    2. Global timeline is continuous without gaps/overlaps
    3. N boards have N+1 boundary cells
    4. Board count is dynamic, not hardcoded
    """

    def __init__(self, max_board_duration_s: float = 15.0) -> None:
        if max_board_duration_s <= 0:
            raise ValueError("max_board_duration_s must be positive")
        if max_board_duration_s > 15.0:
            raise ValueError("max_board_duration_s must not exceed 15s per MODE:P spec")
        self.max_board_duration_s = max_board_duration_s

    def split(
        self,
        scene_id: str,
        total_duration_s: float,
        board_time_ranges: List[Tuple[float, float]],
        character_assignments: Optional[Dict[int, List[str]]] = None,
        prop_assignments: Optional[Dict[int, List[str]]] = None,
        dialog_assignments: Optional[Dict[int, List[str]]] = None,
    ) -> SplitResult:
        """Split a scene into boards based on pre-computed time ranges.

        Args:
            scene_id: Scene identifier
            total_duration_s: Total scene duration
            board_time_ranges: List of (start, end) in global seconds
            character_assignments: Per-board-index character list
            prop_assignments: Per-board-index prop list
            dialog_assignments: Per-board-index dialogue ID list
        """
        n = len(board_time_ranges)
        if n == 0:
            raise ValueError("Must have at least one board")

        result = SplitResult(
            scene_id=scene_id,
            total_duration_s=total_duration_s,
            board_count=n,
        )

        # Validate time ranges
        prev_end: Optional[float] = None
        for i, (start, end) in enumerate(board_time_ranges):
            if start >= end:
                raise ValueError(f"Board {i}: start ({start}) >= end ({end})")
            if end - start > self.max_board_duration_s:
                raise ValueError(
                    f"Board {i}: duration {end - start:.1f}s exceeds "
                    f"max {self.max_board_duration_s}s"
                )
            if prev_end is not None and abs(start - prev_end) > 0.01:
                raise ValueError(
                    f"Board {i}: start ({start}) does not match previous board end "
                    f"({prev_end}) — global timeline must be continuous"
                )
            prev_end = end

        # Create board specs
        board_ids = [f"Board_{chr(65 + i)}" for i in range(n)]  # A, B, C, ...
        if n > 26:
            board_ids = [f"Board_{i + 1:02d}" for i in range(n)]

        for i, (start, end) in enumerate(board_time_ranges):
            chars = (character_assignments or {}).get(i, [])
            props = (prop_assignments or {}).get(i, [])
            dialogs = (dialog_assignments or {}).get(i, [])

            result.boards.append(BoardSpec(
                board_index=i + 1,
                board_id=board_ids[i],
                global_time_start=start,
                global_time_end=end,
                local_duration=end - start,
                entry_state_id=f"S_{board_ids[i]}_entry",
                exit_state_id=f"S_{board_ids[i]}_exit",
                shot_id=f"#S{i + 1}",
                plate_id=f"CAM_{i + 1:02d}",
                characters_in_frame=chars,
                required_props=props,
                dialog_ids=dialogs,
            ))

        # Create N+1 boundary cells
        result.master_boundary_cells = n + 1

        # Scene entry boundary (B0)
        result.boundaries.append(BoundarySpec(
            boundary_index=0,
            boundary_id=f"B0",
            time_s=0.0,
            boundary_type="scene_entry",
            from_board=None,
            to_board=result.boards[0].board_id,
            entry_match_mode="scene_entry",
            pixel_identical_required=False,
            camera_cut_allowed=False,
            upstream_laf=None,
            entry_composition=f"{result.boards[0].board_id}_ENTRY",
        ))

        # Internal boundaries (B1 to B{N-1})
        for i in range(n - 1):
            left = result.boards[i]
            right = result.boards[i + 1]
            time_s = left.global_time_end

            result.boundaries.append(BoundarySpec(
                boundary_index=i + 1,
                boundary_id=f"B{i + 1}",
                time_s=time_s,
                boundary_type="continuous",
                from_board=left.board_id,
                to_board=right.board_id,
                entry_match_mode="continuous",
                pixel_identical_required=False,
                camera_cut_allowed=False,
                upstream_laf=f"LAF_{left.board_id.split('_')[-1]}" if "_" in left.board_id else f"LAF_{left.board_id}",
                entry_composition=f"{right.board_id}_ENTRY",
                exit_composition=f"{left.board_id}_EXIT",
            ))

        # Scene exit boundary (BN)
        result.boundaries.append(BoundarySpec(
            boundary_index=n,
            boundary_id=f"B{n}",
            time_s=total_duration_s,
            boundary_type="scene_exit",
            from_board=result.boards[-1].board_id,
            to_board=None,
            entry_match_mode="scene_exit",
            pixel_identical_required=False,
            camera_cut_allowed=False,
            upstream_laf=None,
            exit_composition=f"{result.boards[-1].board_id}_EXIT",
        ))

        return result

    def validate_split(self, result: SplitResult) -> List[str]:
        """Validate a split result. Returns list of issues (empty = OK)."""
        issues: List[str] = []

        # Check board count >= 1
        if result.board_count < 1:
            issues.append("Must have at least 1 board")
            return issues

        # Check N+1 boundary cells
        expected_bounds = result.board_count + 1
        if len(result.boundaries) != expected_bounds:
            issues.append(
                f"Expected {expected_bounds} boundaries for {result.board_count} "
                f"boards, got {len(result.boundaries)}"
            )

        # Check each board <= 15s
        for board in result.boards:
            if board.local_duration > self.max_board_duration_s:
                issues.append(
                    f"{board.board_id}: duration {board.local_duration:.2f}s "
                    f"exceeds max {self.max_board_duration_s}s"
                )
            if board.local_duration <= 0:
                issues.append(
                    f"{board.board_id}: duration {board.local_duration:.2f}s "
                    f"is not positive"
                )

        # Check global timeline continuous
        timeline: List[Tuple[float, float, str]] = [
            (b.global_time_start, b.global_time_end, b.board_id)
            for b in result.boards
        ]
        timeline.sort()

        for i in range(len(timeline) - 1):
            _, end, bid = timeline[i]
            start, _, next_bid = timeline[i + 1]
            if abs(end - start) > 0.01:
                issues.append(
                    f"Timeline gap: {bid} ends at {end}, {next_bid} starts at {start}"
                )

        # Check boundary times match board times
        for boundary in result.boundaries:
            if boundary.boundary_type == "scene_entry":
                if abs(boundary.time_s - 0.0) > 0.01:
                    issues.append(
                        f"Scene entry boundary at {boundary.time_s}s, expected 0.0s"
                    )
            elif boundary.boundary_type == "scene_exit":
                if abs(boundary.time_s - result.total_duration_s) > 0.01:
                    issues.append(
                        f"Scene exit boundary at {boundary.time_s}s, expected "
                        f"{result.total_duration_s}s"
                    )

        # Check board IDs unique and sequential
        seen_ids: set[str] = set()
        for board in result.boards:
            if board.board_id in seen_ids:
                issues.append(f"Duplicate board ID: {board.board_id}")
            seen_ids.add(board.board_id)

        return issues

    def generate_continuity_matrix(
        self, result: SplitResult
    ) -> Dict[str, Dict[str, Any]]:
        """Generate the 2xN boundary continuity matrix.

        Returns a dict mapping board_id -> {entry_state, exit_state} with
        continuity metadata for each board.
        """
        matrix: Dict[str, Dict[str, Any]] = {}
        for board in result.boards:
            entry_bound = next(
                (b for b in result.boundaries if b.to_board == board.board_id), None
            )
            exit_bound = next(
                (b for b in result.boundaries if b.from_board == board.board_id), None
            )

            matrix[board.board_id] = {
                "board_id": board.board_id,
                "time_range": [board.global_time_start, board.global_time_end],
                "local_duration": board.local_duration,
                "entry": {
                    "boundary_id": entry_bound.boundary_id if entry_bound else "SCENE_ENTRY",
                    "time_s": board.global_time_start,
                    "match_mode": entry_bound.entry_match_mode if entry_bound else "scene_entry",
                    "upstream_laf": entry_bound.upstream_laf if entry_bound else None,
                    "camera_cut_allowed": entry_bound.camera_cut_allowed if entry_bound else False,
                    "pixel_identical_required": entry_bound.pixel_identical_required if entry_bound else False,
                },
                "exit": {
                    "boundary_id": exit_bound.boundary_id if exit_bound else "SCENE_EXIT",
                    "time_s": board.global_time_end,
                    "match_mode": exit_bound.entry_match_mode if exit_bound else "scene_exit",
                    "scene_exit": exit_bound is None,
                },
            }
        return matrix

    def compute_fingerprint(self, result: SplitResult) -> str:
        """Compute a deterministic fingerprint of the split configuration."""
        raw = json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
