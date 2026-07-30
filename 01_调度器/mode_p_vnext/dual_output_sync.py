"""MODE:P vNext — Dual-Output Sync Checker (V5.8).

Verifies Storyboard and Video Prompt views derive from the same Master:
- Same shot count
- Consistent timing (tick-level)
- Same segment_id
- No field-level NL similarity used as source-binding proof

Spec references: LOOP §12.8-§12.9.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from mode_p_vnext.storyboard_projection import StoryboardView
from mode_p_vnext.video_projection import VideoPromptView


@dataclass
class DualOutputSyncResult:
    is_consistent: bool = True
    shot_count_violations: List[str] = field(default_factory=list)
    timing_violations: List[str] = field(default_factory=list)
    segment_id_violations: List[str] = field(default_factory=list)

    # Explicitly NO nl_similarity_score — source binding is structural


def check_dual_output_sync(
    storyboard: StoryboardView,
    video_prompt: VideoPromptView,
) -> DualOutputSyncResult:
    """Verify both views are structurally consistent with the same Master.

    Checks structural identity — NOT natural language similarity.
    """
    result = DualOutputSyncResult()

    # Segment ID must match
    if storyboard.segment_id != video_prompt.segment_id:
        result.segment_id_violations.append(
            f"Segment ID mismatch: SB={storyboard.segment_id} vs "
            f"VP={video_prompt.segment_id}"
        )

    # Shot count must match
    sb_count = len(storyboard.panels)
    vp_count = len(video_prompt.shot_descriptions)
    if sb_count != vp_count:
        result.shot_count_violations.append(
            f"Shot count mismatch: SB has {sb_count}, VP has {vp_count}"
        )

    # Timing must match at tick level for corresponding shots
    for i in range(min(sb_count, vp_count)):
        sb_shot = storyboard.panels[i]
        vp_shot = video_prompt.shot_descriptions[i]
        if sb_shot.get("start_tick") != vp_shot.get("start_tick") or \
           sb_shot.get("end_tick") != vp_shot.get("end_tick"):
            result.timing_violations.append(
                f"Timing mismatch at shot {i}: "
                f"SB [{sb_shot.get('start_tick')},{sb_shot.get('end_tick')}) vs "
                f"VP [{vp_shot.get('start_tick')},{vp_shot.get('end_tick')})"
            )

    result.is_consistent = (
        len(result.shot_count_violations) == 0
        and len(result.timing_violations) == 0
        and len(result.segment_id_violations) == 0
    )
    return result
