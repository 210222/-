# MODE:P vNext Architecture Redesign v2.3 Amendment

> Status: NORMATIVE AMENDMENT
>
> Base package: `MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0.md` +
> `MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.1_AMENDMENT.md` +
> `MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.2_AMENDMENT.md`
>
> Triggering evidence: `A5_ARCHITECTURE_GAP_001.json`
>
> Production boundary: this amendment does not authorize a production switch;
> `v4_unchanged` remains the sole production entry.

## 1. Purpose and authority

The A5 audit found that v2.0 section 5.4 requires local tick allocation from
duration weights, dialogue anchors, and a segment-length ceiling, while the
v2.2 frozen fact and time contracts define neither an audio timing coordinate
nor a segment ceiling. This is an architecture gap, not an implementation
choice. The gap must not be filled by source-text heuristics, model judgement,
or an undocumented duration constant.

This amendment supplies the missing contract. All v2.0--v2.2 rules remain in
force unless this document states otherwise. On conflict, v2.3 prevails.

## 2. ADR-025: deterministic local temporal binding

### 2.1 One bounded generation segment

For the current B1 contract, one scene produces exactly one local
`GenerationSegment`. Its hard duration is
`MAX_GENERATION_SEGMENT_TICKS = 360000` (15 seconds at the canonical 24000
ticks/second timebase). `MAX_SHOT_TICKS` is the same ceiling because every
shot must lie wholly inside that one segment.

The local `TimelineAllocator` MUST:

- reject an empty draft, non-positive weights, or a number of shots exceeding
  the available tick capacity;
- allocate exactly `MAX_GENERATION_SEGMENT_TICKS` positive integer ticks among
  the ordered B1 duration weights using deterministic largest-remainder
  allocation with source order as the final tie-breaker;
- emit adjacent half-open ranges covering `[0, MAX_GENERATION_SEGMENT_TICKS)`;
- reject, rather than silently split, a scene that needs multiple generation
  segments. Multi-segment creative structure needs a future typed B1 contract
  and architecture amendment.

This is a local execution capability bound, not a model-selected duration and
not a display-frame rate.

### 2.2 Typed dialogue anchor

`ScriptFact` gains `dialogue_anchor_ppm: int | None`, where PPM means parts
per million of the normalized scene source. The field is locally assembled;
the I0 model contract MUST NOT return it.

For a dialogue fact, `FactAssembler` MUST compute it from the source-supported
half-open span supplied by I0 and the exact normalized scene text used for
that request:

```text
dialogue_anchor_ppm = floor(
  ((source_start + source_end) / 2) * 1_000_000 / len(normalized_scene_source)
)
```

The result is clamped only by rejecting an invalid source span; it must be in
`[0, 1_000_000]`. `ScriptFact.validate_against_normalized_source()` MUST
recompute and verify this value. A dialogue fact requires a non-null anchor;
all non-dialogue facts must have `dialogue_anchor_ppm is None`.

`source_start`, `source_end`, `statement`, `subject_id`, and `spoken_text`
retain their v2.2 meaning. The anchor is a local, auditable projection of a
validated source location, not a model-authored timing opinion and not a
speech-duration estimate.

### 2.3 AudioEvent placement

`VECAssembler` MUST derive dialogue audio only from typed dialogue facts. It
MUST order dialogue facts by this stable key:

```text
(dialogue_anchor_ppm, source_ref.source_id, source_ref.digest,
 source_start, source_end, ordinal, fact_id)
```

For each ordered fact, the nominal target tick is:

```text
floor(dialogue_anchor_ppm * (segment_duration_ticks - 1) / 1_000_000)
```

The assembler schedules one positive binding-marker tick per event at the
greater of its target tick and the first unused local tick. If no local tick
remains, it MUST fail closed. The resulting interval is `[start_tick,
start_tick + 1)`. It records source binding and ordering only; adapters MUST
NOT reinterpret this marker as a measured voice-performance duration.

Each event still receives exactly one `VoiceRequirement` from the same
typed `subject_id`, and `spoken_text` is copied only from that fact. No
`fact_id`, statement, source filename, or free-text intent may be parsed for
category, speaker, text, or time.

## 3. ADR-026: binding boundary for B1 creative text

`reference_intents[]` and `audio_intents[]` in the current B1 Draft remain
creative, free-text notes. They are not typed entity or dialogue bindings and
MUST NOT be parsed or matched against facts.

The current VEC contract therefore derives scene-scoped
`ReferenceRequirement`s from every typed
`character | wardrobe | prop | setting | asset` fact and preserves their
source-fact mapping. It derives dialogue `AudioEvent`s directly from every
typed dialogue fact. These are the complete binding inputs available in the
current authoritative B1 shape.

The v2.2 rule that a visual design reference without a corresponding fact, or
a dialogue design without a unique dialogue fact, fails closed applies when a
future B1 revision introduces an explicit typed entity or dialogue selector.
Such a selector is not present in v2.3 and may not be improvised as a string
protocol. Until a later amendment defines it, a free-text B1 intent is never a
binding request and cannot silently create or select a fact.

## 4. Required construction effects

The architecture package is rebased to 2.3. Prior A0--A4 evidence is invalid
because the frozen domain, temporal assembly, and architecture-bundle hashes
changed. Revalidation must proceed from A0 in dependency order.

- A0 locks the four-document authority bundle and confirms v4 isolation.
- A1 adds and mechanically verifies the local dialogue-anchor contract.
- A4 confirms I0 still excludes the local anchor and that B1 free text is not
  a binding transport.
- A5 proves the bounded segment allocator, anchored deterministic audio
  placement, source binding, and the v2.2 typed semantic rules.
- A6--A10 remain subject to their existing v2.2 constraints and are not
  authorized to start before their dependencies re-complete.

No A task may claim media acceptance, owner approval, or production switching
under this amendment.
