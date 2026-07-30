# Scene Context Contract

This factual artifact is prepared before visual design. For an existing context
it may be supplied directly; for a script-first command the Director may create
it during a fact-extraction phase. In either case it must not add visual design,
unsupported story interpretation, rules, or new events.

## Required input

```markdown
# [Scene name] - Scene Context

## Script
[Dialogue and action from the source script.]

## Spatial facts
- Room or exterior boundaries, depth, doors, windows, furniture, obstacles.
- Available camera placement areas and actor movement areas.
- Existing practical light sources and their physical direction.
- Facts inferred from a reference must be labelled as inferred.

## Characters
- [Name]: stable visible identity, wardrobe, and current state.

## Continuity at entry
- Character positions, held props, wardrobe state, unresolved movement.

## References
- Describe only what each reference establishes: identity, layout, color, or prop.

## User intent
- Optional visual preference, reference films, or deliberate constraints.
```

## Rules

1. Preserve source facts. Do not invent a window, door, light, object, or room.
2. Keep facts once. Do not copy the same spatial paragraph into separate files.
3. A missing physical fact remains unknown; it is not silently completed.
4. The Director may make a creative inference only when it does not contradict a fact.
5. This file is input context, not a delivery artifact.
