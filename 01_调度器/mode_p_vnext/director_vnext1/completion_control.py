"""Controller binding for the post-DDO completion-evidence queue."""

from __future__ import annotations

from pathlib import Path

from mode_p_vnext.rebuild_control import RebuildControl


COMPLETION_TASKS_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_COMPLETION_TASKS.json")
COMPLETION_STATE_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_COMPLETION_STATE.json")
COMPLETION_LOCK_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_COMPLETION.lock.json")


class CompletionControl(RebuildControl):
    """Keep completion evidence separate from the finished text-pipeline queue."""

    def __init__(self, project_root: Path):
        super().__init__(
            project_root,
            tasks_rel=COMPLETION_TASKS_REL,
            state_rel=COMPLETION_STATE_REL,
            lock_rel=COMPLETION_LOCK_REL,
        )

    @classmethod
    def default(cls) -> "CompletionControl":
        return cls(Path(__file__).resolve().parents[3])
