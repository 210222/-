"""EP35_S1 Scene Context Parser — deterministic scene/board/boundary extraction.

Reads the EP35_S1 scene fixture directory and produces structured data
suitable for pipeline consumption. Never invents facts; every field traces
to a source file or explicit contract.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CharacterState:
    entity_id: str
    clothing: str
    position: str
    orientation: str
    pose: str
    emotion: str
    hands: str
    presence: str  # "present" | "absent"
    props_carried: Dict[str, str] = field(default_factory=dict)


@dataclass
class PropState:
    prop_id: str
    state: str
    state_chain: List[str] = field(default_factory=list)


@dataclass
class LightingState:
    layers: Dict[str, str] = field(default_factory=dict)


@dataclass
class BoardEntry:
    board_id: str
    global_time_range: Tuple[float, float]
    local_time_range: Tuple[float, float]
    storyboard_path: Path
    video_prompt_path: Path
    entry_state: Dict[str, Any]
    exit_state: Dict[str, Any]
    character_states: Dict[str, CharacterState] = field(default_factory=dict)
    prop_states: Dict[str, PropState] = field(default_factory=dict)
    lighting: LightingState = field(default_factory=LightingState)
    camera_axis: str = ""
    spatial_anchor: str = ""


@dataclass
class BoundaryContract:
    boundary_id: str
    time_s: float
    boundary_type: str  # scene_entry | continuous | scene_exit
    from_board: Optional[str]
    to_board: Optional[str]
    entry_match_mode: str  # scene_entry | structured_state_match_with_camera_cut | exact_visual_frame_match | scene_exit
    pixel_identical_required: bool
    camera_cut_allowed: bool
    upstream_laf: Optional[str]
    states_equal: Optional[bool]
    composition: str = ""
    visual_prompt: str = ""
    hand_state: str = ""


@dataclass
class DialogueLine:
    dialogue_id: str
    speaker: str
    text: str
    valid_chars: int
    global_sec_start: float
    global_sec_end: float
    duration_s: float
    board: str


@dataclass
class SceneContext:
    scene_id: str
    location: str
    time_of_day: str
    total_duration_s: float
    board_count: int
    boards: List[BoardEntry] = field(default_factory=list)
    boundaries: List[BoundaryContract] = field(default_factory=list)
    dialogues: List[DialogueLine] = field(default_factory=list)
    characters: Dict[str, CharacterState] = field(default_factory=dict)
    props: Dict[str, PropState] = field(default_factory=dict)
    lighting: LightingState = field(default_factory=LightingState)
    source_sha256: str = ""


class EP35SceneParser:
    """Deterministic parser for EP35_S1 scene fixture directory."""

    def __init__(self, fixture_dir: Path) -> None:
        if not fixture_dir.is_dir():
            raise FileNotFoundError(f"Fixture directory not found: {fixture_dir}")
        self.fixture_dir = fixture_dir
        self._vcp: Optional[Dict[str, Any]] = None
        self._child_packets: Optional[List[Dict[str, Any]]] = None
        self._handoff_packets: Optional[List[Dict[str, Any]]] = None
        self._state_spine: Optional[List[Dict[str, Any]]] = None

    @property
    def vcp(self) -> Dict[str, Any]:
        if self._vcp is None:
            vcp_path = self.fixture_dir / "VCP.json"
            if not vcp_path.is_file():
                raise FileNotFoundError(f"VCP.json missing: {vcp_path}")
            self._vcp = json.loads(vcp_path.read_text(encoding="utf-8"))
        return self._vcp

    @property
    def child_packets(self) -> List[Dict[str, Any]]:
        if self._child_packets is None:
            path = self.fixture_dir / "CHILD_PACKETS.json"
            if not path.is_file():
                raise FileNotFoundError(f"CHILD_PACKETS.json missing: {path}")
            self._child_packets = json.loads(path.read_text(encoding="utf-8"))
        return self._child_packets

    @property
    def handoff_packets(self) -> List[Dict[str, Any]]:
        if self._handoff_packets is None:
            path = self.fixture_dir / "HANDOFF_PACKETS.json"
            if not path.is_file():
                raise FileNotFoundError(f"HANDOFF_PACKETS.json missing: {path}")
            self._handoff_packets = json.loads(path.read_text(encoding="utf-8"))
        return self._handoff_packets

    @property
    def state_spine(self) -> List[Dict[str, Any]]:
        if self._state_spine is None:
            path = self.fixture_dir / "STATE_SPINE.json"
            if not path.is_file():
                raise FileNotFoundError(f"STATE_SPINE.json missing: {path}")
            self._state_spine = json.loads(path.read_text(encoding="utf-8"))
        return self._state_spine

    def parse(self) -> SceneContext:
        """Parse the full scene context from the fixture directory."""
        vcp = self.vcp
        meta = vcp["META"]

        context = SceneContext(
            scene_id=meta["scene_id"],
            location=vcp["SCENE_META"]["location"],
            time_of_day=vcp["SCENE_META"]["time_of_day"],
            total_duration_s=meta["total_duration_s"],
            board_count=meta["board_count"],
        )

        self._parse_characters(context)
        self._parse_props(context)
        self._parse_lighting(context)
        self._parse_dialogues(context)
        self._parse_boards(context)
        self._parse_boundaries(context)

        # Compute source hash for integrity checks
        raw = json.dumps(vcp, ensure_ascii=False, sort_keys=True)
        context.source_sha256 = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return context

    def _parse_characters(self, context: SceneContext) -> None:
        master = self.vcp.get("MASTER_STATE", {}).get("characters", {})
        for char_id, char_data in master.items():
            context.characters[char_id] = CharacterState(
                entity_id=char_id,
                clothing=char_data.get("clothing", ""),
                position=char_data.get("position", ""),
                orientation=char_data.get("orientation", ""),
                pose=char_data.get("pose", ""),
                emotion=char_data.get("emotion", ""),
                hands=char_data.get("hands", ""),
                presence=char_data.get("presence", "present"),
                props_carried=char_data.get("props_carried", {}),
            )

    def _parse_props(self, context: SceneContext) -> None:
        scene_props = self.vcp.get("SCENE_META", {}).get("props", [])
        for prop in scene_props:
            context.props[prop["name"]] = PropState(
                prop_id=prop["name"],
                state=prop["initial_state"],
                state_chain=prop.get("state_chain", []),
            )

    def _parse_lighting(self, context: SceneContext) -> None:
        lighting = self.vcp.get("MASTER_STATE", {}).get("lighting", {})
        for layer in lighting.get("layers", []):
            context.lighting.layers[layer["id"]] = layer["value"]

    def _parse_dialogues(self, context: SceneContext) -> None:
        for d in self.vcp.get("DIALOGUE_SYNC", []):
            context.dialogues.append(DialogueLine(
                dialogue_id=d["id"],
                speaker=d["speaker"],
                text=d["text"],
                valid_chars=d["valid_chars"],
                global_sec_start=d["global_sec_start"],
                global_sec_end=d["global_sec_end"],
                duration_s=d["duration_s"],
                board=d.get("board", ""),
            ))

    def _parse_boards(self, context: SceneContext) -> None:
        for packet in self.child_packets:
            board_id = packet["board"]
            storyboard_file = packet.get("storyboard_prompt_file", "")
            video_file = packet.get("video_prompt_file", "")

            sb_path = self.fixture_dir / storyboard_file if storyboard_file else Path()
            vp_path = self.fixture_dir / video_file if video_file else Path()

            board = BoardEntry(
                board_id=board_id,
                global_time_range=(
                    float(packet["global_time_range"][0]),
                    float(packet["global_time_range"][1]),
                ),
                local_time_range=(
                    float(packet["local_time_range"][0]),
                    float(packet["local_time_range"][1]),
                ),
                storyboard_path=sb_path,
                video_prompt_path=vp_path,
                entry_state=packet.get("entry_state", {}),
                exit_state=packet.get("exit_state", {}),
            )

            # Attach character states
            for char_id, char_data in packet.get("entry_state", {}).get("characters", {}).items():
                board.character_states[char_id] = CharacterState(
                    entity_id=char_id,
                    clothing=char_data.get("clothing", ""),
                    position=char_data.get("position", ""),
                    orientation=char_data.get("orientation", ""),
                    pose=char_data.get("pose", ""),
                    emotion=char_data.get("emotion", ""),
                    hands=char_data.get("hands", ""),
                    presence=char_data.get("presence", "present"),
                    props_carried=char_data.get("props_carried", {}),
                )

            # Attach prop states
            for prop_id, prop_state in packet.get("entry_state", {}).get("props", {}).items():
                board.prop_states[prop_id] = PropState(
                    prop_id=prop_id,
                    state=prop_state,
                )

            # Attach lighting
            for lid, lval in packet.get("entry_state", {}).get("lighting", {}).items():
                board.lighting.layers[lid] = lval

            board.camera_axis = packet.get("entry_state", {}).get("camera_axis", "")
            board.spatial_anchor = packet.get("entry_state", {}).get("spatial", {}).get("anchor", "")

            context.boards.append(board)

    def _parse_boundaries(self, context: SceneContext) -> None:
        boundaries = self.vcp.get("BOARD_BOUNDARIES", [])
        handoffs = {h["handoff_id"]: h for h in self.handoff_packets}

        for b in boundaries:
            bid = b["boundary_id"]
            btype = b["type"]
            time_s = float(b["time_s"])

            # Map boundary to handoff for visual match policy
            handoff = None
            if btype == "continuous":
                if bid == "B02":
                    handoff = handoffs.get("Board_A_TO_Board_B", {})
                elif bid == "B03":
                    handoff = handoffs.get("Board_B_TO_Board_C", {})

            visual_policy = handoff.get("visual_match_policy", {}) if handoff else {}

            # Map boards
            from_board = None
            to_board = None
            if btype == "continuous":
                if bid == "B02":
                    from_board, to_board = "Board_A", "Board_B"
                elif bid == "B03":
                    from_board, to_board = "Board_B", "Board_C"
            elif btype == "scene_entry":
                to_board = "Board_A"
            elif btype == "scene_exit":
                from_board = "Board_C"

            # Find visual prompt from BOUNDARY_VISUALS
            bv = self.vcp.get("BOUNDARY_VISUALS", {})
            visual_prompt = ""
            composition = ""
            hand_state = ""
            if btype == "scene_entry" and "Board_A_ENTRY" in bv:
                visual_prompt = bv["Board_A_ENTRY"].get("visual_prompt", "")
                composition = bv["Board_A_ENTRY"].get("composition", "")
                hand_state = bv["Board_A_ENTRY"].get("hand_state", "")
            elif btype == "scene_exit" and "Board_C_EXIT" in bv:
                visual_prompt = bv["Board_C_EXIT"].get("visual_prompt", "")
                composition = bv["Board_C_EXIT"].get("composition", "")
                hand_state = bv["Board_C_EXIT"].get("hand_state", "")
            elif bid == "B02":
                if "Board_A_EXIT" in bv:
                    visual_prompt = bv["Board_A_EXIT"].get("visual_prompt", "")
                    composition = bv["Board_A_EXIT"].get("composition", "")
                    hand_state = bv["Board_A_EXIT"].get("hand_state", "")
            elif bid == "B03":
                if "Board_B_EXIT" in bv:
                    visual_prompt = bv["Board_B_EXIT"].get("visual_prompt", "")
                    composition = bv["Board_B_EXIT"].get("composition", "")
                    hand_state = bv["Board_B_EXIT"].get("hand_state", "")

            context.boundaries.append(BoundaryContract(
                boundary_id=bid,
                time_s=time_s,
                boundary_type=btype,
                from_board=from_board,
                to_board=to_board,
                entry_match_mode=visual_policy.get("match_mode", btype),
                pixel_identical_required=visual_policy.get("pixel_identical_required", False),
                camera_cut_allowed=visual_policy.get("camera_cut_allowed", False),
                upstream_laf=visual_policy.get("upstream_laf_id"),
                states_equal=b.get("states_equal"),
                composition=composition,
                visual_prompt=visual_prompt,
                hand_state=hand_state,
            ))

    def verify_continuity(self) -> List[str]:
        """Verify all boundary states are consistent. Returns list of issues (empty = OK)."""
        issues: List[str] = []
        context = self.parse()

        for boundary in context.boundaries:
            if boundary.boundary_type != "continuous":
                continue

            # Find the two boards connected by this boundary
            from_board = next(
                (b for b in context.boards if b.board_id == boundary.from_board), None
            )
            to_board = next(
                (b for b in context.boards if b.board_id == boundary.to_board), None
            )

            if not from_board or not to_board:
                issues.append(
                    f"Boundary {boundary.boundary_id}: cannot find connected boards"
                )
                continue

            # Check EXIT==ENTRY state equality
            if boundary.states_equal is False:
                issues.append(
                    f"Boundary {boundary.boundary_id}: "
                    f"{boundary.from_board}_EXIT != {boundary.to_board}_ENTRY"
                )

            # Verify per-character continuity: from_board EXIT must match to_board ENTRY
            from_exit = from_board.exit_state.get("characters", {})
            to_entry = to_board.entry_state.get("characters", {})

            for char_id, from_char in from_exit.items():
                to_char = to_entry.get(char_id)
                if to_char is None:
                    if from_char.get("presence") == "present":
                        issues.append(
                            f"Boundary {boundary.boundary_id}: "
                            f"Character {char_id} disappeared across boundary"
                        )
                    continue

                # Check key invariant fields
                for field in ("clothing", "position", "orientation", "pose"):
                    fv = from_char.get(field, "")
                    tv = to_char.get(field, "")
                    if fv != tv:
                        issues.append(
                            f"Boundary {boundary.boundary_id}: "
                            f"Character {char_id}.{field} changed: {fv!r} -> {tv!r}"
                        )

            # Check prop continuity at boundary
            from_exit_props = from_board.exit_state.get("props", {})
            to_entry_props = to_board.entry_state.get("props", {})
            for prop_id, from_state in from_exit_props.items():
                to_state = to_entry_props.get(prop_id)
                if to_state and from_state != to_state:
                    issues.append(
                        f"Boundary {boundary.boundary_id}: "
                        f"Prop {prop_id} state changed: {from_state!r} -> {to_state!r}"
                    )

        return issues

    def get_storyboard_cell_count(self, board_path: Path) -> int:
        """Count storyboard cells (panels) in a child storyboard file."""
        if not board_path.is_file():
            return 0
        text = board_path.read_text(encoding="utf-8")
        # Count 【格N】 markers
        cells = re.findall(r'【格(\d+)】', text)
        return len(cells) if cells else 0

    def get_video_beat_count(self, board_path: Path) -> int:
        """Count video timeline beats in a video prompt file."""
        if not board_path.is_file():
            return 0
        text = board_path.read_text(encoding="utf-8")
        beats = re.findall(r'【第[\d.]+-[\d.]+秒】', text)
        return len(beats)
