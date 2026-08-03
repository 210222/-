"""Deterministic v3.1 time allocation for local GenerationUnits.

The director may select only a :class:`DurationIntent`.  The approved local
``GenerationCapabilityProfile`` maps that intent to ticks.  This module never
accepts model-authored weights, raw ticks, source spans, or a scene-wide 15 s
cap.  The generation cap applies independently to each GenerationUnit.
"""

from __future__ import annotations

from mode_p_vnext.domain.artifact import DomainValidationError
from mode_p_vnext.domain.time import (
    DurationIntent,
    GenerationCapabilityProfile,
    GenerationUnitTimeline,
    SceneTimeline,
    TickRange,
    TimelinePlacement,
)


def allocate_shot_timelines(
    *,
    scene_id: str,
    generation_unit_ids: tuple[str, ...],
    duration_intents: tuple[DurationIntent, ...],
    capability_profile: GenerationCapabilityProfile,
) -> tuple[SceneTimeline, tuple[GenerationUnitTimeline, ...]]:
    """Allocate adjacent scene placements from local capability policy.

    The returned ``GenerationUnitTimeline`` values always use unit-local time
    starting at zero.  ``SceneTimeline`` is a separate placement coordinate
    system, constructed solely by this deterministic allocator.
    """

    unit_ids = tuple(generation_unit_ids)
    intents = tuple(duration_intents)
    if not isinstance(scene_id, str) or not scene_id.strip():
        raise DomainValidationError("scene_id must be non-empty")
    if not unit_ids:
        raise DomainValidationError("at least one GenerationUnit is required")
    if len(unit_ids) != len(intents):
        raise DomainValidationError("generation_unit_ids and duration_intents must align")
    if any(not isinstance(unit_id, str) or not unit_id.strip() for unit_id in unit_ids):
        raise DomainValidationError("generation_unit_ids must contain non-empty local IDs")
    if len(unit_ids) != len(set(unit_ids)):
        raise DomainValidationError("generation_unit_ids must be unique")
    if not isinstance(capability_profile, GenerationCapabilityProfile):
        raise DomainValidationError("capability_profile must be canonical")

    unit_timelines: list[GenerationUnitTimeline] = []
    placements: list[TimelinePlacement] = []
    cursor = 0
    for unit_id, intent in zip(unit_ids, intents):
        option = capability_profile.option_for(intent)
        timeline = GenerationUnitTimeline(
            duration_ticks=option.target_ticks,
            capability_profile_id=capability_profile.profile_id,
            capability_profile_version=capability_profile.profile_version,
            max_generation_ticks=capability_profile.max_generation_ticks,
        )
        unit_timelines.append(timeline)
        placement = TimelinePlacement(
            scope_id=unit_id,
            parent_scope_id=scene_id,
            interval=TickRange(cursor, cursor + timeline.duration_ticks),
        )
        placements.append(placement)
        cursor = placement.interval.end_tick

    return (
        SceneTimeline(
            scene_id=scene_id,
            interval=TickRange(0, cursor),
            generation_unit_placements=tuple(placements),
        ),
        tuple(unit_timelines),
    )
