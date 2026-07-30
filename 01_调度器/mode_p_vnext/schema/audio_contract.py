"""MODE:P vNext — Audio/Lipsync Contract (V2.6).

Structured dialogue attribution, lip visibility, off-screen dialogue,
audio bridges, and time-window constraints.

Spec references: LOOP §11.8; Omission P1-09.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from mode_p_vnext.schema.canonical_timeline import Tick


# ---------------------------------------------------------------------------
# DialogueLine
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DialogueLine:
    """A single line of dialogue with timing and visibility info."""

    line_id: str
    character_id: str
    text: str
    start_tick: Tick
    end_tick: Tick
    lip_visible: bool
    source: str = "on_screen"   # on_screen | offscreen | voice_over | internal


# ---------------------------------------------------------------------------
# AudioBridge
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AudioBridge:
    """Continuous sound that spans across shot/segment boundaries."""

    bridge_id: str
    sound_description: str
    from_tick: Tick
    to_tick: Tick
    crosses_segment_boundary: bool = False


# ---------------------------------------------------------------------------
# AudioContract
# ---------------------------------------------------------------------------

@dataclass
class AudioContract:
    """Complete audio plan for a segment."""

    segment_id: str
    dialogue_lines: List[DialogueLine] = field(default_factory=list)
    audio_bridges: List[AudioBridge] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def check_lipsync(
    dialogue_lines: Sequence[DialogueLine],
) -> List[str]:
    """Return warnings where on-screen dialogue has no visible lips."""
    warnings: List[str] = []
    for dl in dialogue_lines:
        if not dl.lip_visible and dl.source == "on_screen":
            warnings.append(
                f"Dialogue '{dl.line_id}' ({dl.character_id}: '{dl.text}') "
                f"is on_screen but lip_visible=False — verify camera can see lips"
            )
    return warnings


def check_dialogue_overlaps(
    dialogue_lines: Sequence[DialogueLine],
) -> List[str]:
    """Return conflicts where dialogue lines overlap in time."""
    conflicts: List[str] = []
    sorted_lines = sorted(dialogue_lines, key=lambda d: d.start_tick)
    for i in range(len(sorted_lines)):
        for j in range(i + 1, len(sorted_lines)):
            a = sorted_lines[i]
            b = sorted_lines[j]
            if a.end_tick > b.start_tick:  # overlap
                conflicts.append(
                    f"Dialogue overlap: '{a.line_id}' [{a.start_tick},{a.end_tick}) "
                    f"vs '{b.line_id}' [{b.start_tick},{b.end_tick})"
                )
            else:
                break  # sorted, no further overlaps possible
    return conflicts
