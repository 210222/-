"""Director vNext.1 E0 -> S1 -> K1 orchestration.

The injected provider is the future home of a real Director model/runtime.  It
cannot bypass the contracts below: this module validates its output before a
later blocking or execution phase can receive it.  It deliberately makes no
external model call and has no release capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .cache import ContentAddressedCache, content_address
from .capsules import RetrievalContext, retrieve_k1
from .contracts import (
    BlockingCommit,
    DecisionPacket,
    DirectorContractError,
    DirectorDecisionRecord,
    DecisionCandidate,
    EpisodeDirectionState,
    EpisodeRequest,
    KnowledgeCapsule,
    PhaseAResult,
    PhaseBResult,
    SceneInput,
    SceneVisualCurve,
)
from .capsules import retrieve_k2


class DirectorProvider(Protocol):
    """The minimal persistent-Director interface required for DDO-2."""

    def create_episode_direction(self, request: EpisodeRequest) -> EpisodeDirectionState:
        """Return E0 direction, without execution instructions."""

    def analyse_scene_phase_a(
        self, scene: SceneInput, episode_direction: EpisodeDirectionState
    ) -> PhaseAResult:
        """Return S1 diagnosis; B0/B1 answers are contractually invalid here."""

    def create_blocking_commit(
        self, scene: SceneInput, phase_a: PhaseAResult, k1_packet: DecisionPacket
    ) -> BlockingCommit:
        """Commit motivated spatial relations before K2 or camera choices."""

    def design_phase_b(
        self,
        scene: SceneInput,
        phase_a: PhaseAResult,
        blocking_commit: BlockingCommit,
        k1_packet: DecisionPacket,
        k2_packet: DecisionPacket,
    ) -> PhaseBResult:
        """Return explicit candidate and VEC choices after blocking/K2."""


@dataclass(frozen=True)
class PhaseAPlanningResult:
    """Auditable hand-off from E0/S1/K1 to the later BlockingCommit phase."""

    episode_direction: EpisodeDirectionState
    phase_a: PhaseAResult
    k1_packet: DecisionPacket
    episode_cache_key: str
    phase_a_cache_key: str


@dataclass(frozen=True)
class PhaseBPlanningResult:
    phase_a_result: PhaseAPlanningResult
    blocking_commit: BlockingCommit
    k2_packet: DecisionPacket
    phase_b: PhaseBResult


class DirectorAgent:
    """One persistent director identity, content-addressed by approved inputs."""

    def __init__(
        self,
        provider: DirectorProvider,
        *,
        director_id: str,
        catalog: Sequence[KnowledgeCapsule],
        cache: ContentAddressedCache | None = None,
    ) -> None:
        if not director_id.strip():
            raise DirectorContractError("director_id is required")
        self._provider = provider
        self._director_id = director_id
        self._catalog = tuple(catalog)
        self._cache = cache or ContentAddressedCache()

    @property
    def director_id(self) -> str:
        return self._director_id

    @property
    def cache(self) -> ContentAddressedCache:
        return self._cache

    def episode_direction(self, request: EpisodeRequest) -> tuple[EpisodeDirectionState, str]:
        key = content_address("director-vnext1/e0", request.cache_payload)
        cached = self._cache.get(key)
        if cached is not None:
            if not isinstance(cached, EpisodeDirectionState):
                raise DirectorContractError("E0 cache type is corrupted")
            return cached, key
        state = self._provider.create_episode_direction(request)
        if state.episode_id != request.episode_id:
            raise DirectorContractError("E0 output episode does not match its request")
        if state.director_id != self._director_id:
            raise DirectorContractError("E0 output changed the persistent Director identity")
        return self._cache.put(key, state), key

    def plan_phase_a(self, request: EpisodeRequest, scene: SceneInput) -> PhaseAPlanningResult:
        if request.episode_id != scene.episode_id:
            raise DirectorContractError("scene must be planned by its own episode direction")
        direction, episode_key = self.episode_direction(request)
        phase_key = content_address(
            "director-vnext1/s1",
            {"scene": scene.cache_payload, "episode_direction": direction},
        )
        cached = self._cache.get(phase_key)
        if cached is None:
            phase_a = self._provider.analyse_scene_phase_a(scene, direction)
            if phase_a.scene_intent.scene_id != scene.scene_id:
                raise DirectorContractError("S1 output scene does not match its request")
            cached = self._cache.put(phase_key, phase_a)
        if not isinstance(cached, PhaseAResult):
            raise DirectorContractError("S1 cache type is corrupted")
        k1_packet = retrieve_k1(
            packet_id=f"K1-{scene.scene_id}",
            problems=cached.problem_set,
            catalog=self._catalog,
            context=RetrievalContext(
                scene_tags=scene.scene_tags,
                approved_context=scene.approved_context,
                impact_level=scene.impact_level,
            ),
        )
        return PhaseAPlanningResult(
            episode_direction=direction,
            phase_a=cached,
            k1_packet=k1_packet,
            episode_cache_key=episode_key,
            phase_a_cache_key=phase_key,
        )

    def plan_phase_b(self, request: EpisodeRequest, scene: SceneInput) -> PhaseBPlanningResult:
        """Run B0 -> K2 -> B1; a VEC cannot be supplied before B0 validates."""

        phase_a_result = self.plan_phase_a(request, scene)
        blocking = self._provider.create_blocking_commit(
            scene, phase_a_result.phase_a, phase_a_result.k1_packet
        )
        if blocking.scene_id != scene.scene_id:
            raise DirectorContractError("BlockingCommit scene does not match its request")
        expected_phase_a = _phase_a_fingerprint(phase_a_result.phase_a)
        if blocking.phase_a_fingerprint != expected_phase_a:
            raise DirectorContractError("BlockingCommit must cite the exact Phase A result")
        k2_packet = retrieve_k2(
            packet_id=f"K2-{scene.scene_id}-{blocking.commit_id}",
            problems=phase_a_result.phase_a.problem_set,
            catalog=self._catalog,
            context=RetrievalContext(
                scene_tags=scene.scene_tags,
                approved_context=scene.approved_context,
                impact_level=scene.impact_level,
            ),
            blocking_commit_id=blocking.commit_id,
        )
        phase_b = self._provider.design_phase_b(
            scene, phase_a_result.phase_a, blocking, phase_a_result.k1_packet, k2_packet
        )
        return PhaseBPlanningResult(
            phase_a_result=phase_a_result,
            blocking_commit=blocking,
            k2_packet=k2_packet,
            phase_b=phase_b,
        )


def _phase_a_fingerprint(phase_a: PhaseAResult) -> str:
    """Keep Phase A binding deterministic without exposing private model reasoning."""

    return content_address(
        "director-vnext1/phase-a-contract",
        {"scene_intent": phase_a.scene_intent, "problem_set": phase_a.problem_set},
    )
