"""Fail-closed release control for the isolated MODE:P vNext rebuild.

This module is deliberately a *rebuild-time control plane*, not a production
router.  It must never make vNext runnable from a repair task.  The real
``/mode-p-pilot`` entry remains v4 until a separately authorised release task
creates and validates an actual production integration.

Spec references: LOOP §27.1--§27.6.  R3.1 implements only the safety
preconditions: default-current routing, no activation in Rebuild, and a
read-only view of a rollback/kill-switch control record.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


class GateError(RuntimeError):
    """Raised whenever an activation or external submission is attempted."""


GATE_MODES = frozenset(
    {"shadow", "pilot", "canary", "production"}
)
CURRENT_MODE = "current"
REBUILD_PHASE = "rebuild"


@dataclass(frozen=True)
class GateStatus:
    """A deliberately small, auditable view of the effective rebuild state."""

    effective_mode: str
    phase: str
    vnext_invocation_allowed: bool
    external_submission_allowed: bool
    kill_switch_armed: bool
    reason_code: str


class FeatureGate:
    """Fail closed for every vNext gate while running a Rebuild task.

    There is intentionally no ``force`` flag, implicit promotion, or release
    path in this class.  A future, separately approved release integration
    must not reuse a repair-time object as an activation bypass.
    """

    def __init__(
        self,
        control_root: Optional[str | Path] = None,
        *,
        phase: str = REBUILD_PHASE,
    ) -> None:
        if phase != REBUILD_PHASE:
            raise GateError(
                "FeatureGate is rebuild-only; release activation is not "
                "implemented by MODE:P vNext R3.1"
            )
        self._phase = phase
        self._control_root = (
            Path(control_root).resolve() if control_root is not None else None
        )

    @property
    def shadow_enabled(self) -> bool:
        return False

    @property
    def pilot_enabled(self) -> bool:
        return False

    @property
    def canary_enabled(self) -> bool:
        return False

    @property
    def production_enabled(self) -> bool:
        return False

    @property
    def enabled_episodes(self) -> List[str]:
        """Compatibility view; Rebuild never has an enabled scope."""

        return []

    def _reject_activation(self, gate_name: str, scope: Iterable[str]) -> None:
        del scope  # Scope is never trusted as a substitute for approval.
        if gate_name not in GATE_MODES:
            raise GateError(f"Unknown vNext gate: {gate_name}")
        raise GateError(
            f"Cannot enable {gate_name} in Rebuild: all vNext gates are "
            "fail-closed until a separately approved release workflow exists"
        )

    def enable_shadow(self, episodes: Iterable[str]) -> None:
        self._reject_activation("shadow", episodes)

    def enable_pilot(self, episodes: Iterable[str]) -> None:
        self._reject_activation("pilot", episodes)

    def enable_canary(self, episodes: Iterable[str]) -> None:
        self._reject_activation("canary", episodes)

    def enable_production(self, episodes: Iterable[str]) -> None:
        self._reject_activation("production", episodes)

    def can_enable_in_rebuild(self, gate_name: str) -> bool:
        """Return false for every known *and unknown* request, fail closed."""

        del gate_name
        return False

    def status(self) -> GateStatus:
        """Report rebuild-safe state without trusting a vNext route record."""

        armed = False
        if self._control_root is not None:
            try:
                # Imported lazily to keep this small safety layer acyclic.
                from .rollback import RollbackController

                armed = RollbackController(self._control_root).read_state().kill_switch_armed
            except Exception:
                # A corrupt/missing control record must never enable vNext.
                armed = False
        return GateStatus(
            effective_mode=CURRENT_MODE,
            phase=self._phase,
            vnext_invocation_allowed=False,
            external_submission_allowed=False,
            kill_switch_armed=armed,
            reason_code=("KILL_SWITCH_ARMED" if armed else "REBUILD_FAIL_CLOSED"),
        )

    def assert_submission_allowed(self) -> None:
        """R3.1 never permits an external model or delivery submission."""

        raise GateError(
            "External submission is forbidden from the MODE:P vNext Rebuild "
            "control plane"
        )
