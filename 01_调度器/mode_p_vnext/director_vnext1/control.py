"""Controller binding for the independent vNext.1 Director construction queue."""

from __future__ import annotations

from pathlib import Path

from mode_p_vnext.rebuild_control import RebuildControl


DIRECTOR_TASKS_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_DIRECTOR_V1_1_TASKS.json")
DIRECTOR_STATE_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_DIRECTOR_V1_1_STATE.json")
DIRECTOR_LOCK_REL = Path("MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_DIRECTOR_V1_1.lock.json")


class DirectorDdoControl(RebuildControl):
    """Use the audited control-plane mechanics without reusing R0--R3 state."""

    def __init__(self, project_root: Path):
        super().__init__(
            project_root,
            tasks_rel=DIRECTOR_TASKS_REL,
            state_rel=DIRECTOR_STATE_REL,
            lock_rel=DIRECTOR_LOCK_REL,
        )

    @classmethod
    def default(cls) -> "DirectorDdoControl":
        return cls(Path(__file__).resolve().parents[3])
