# Architecture Decision: reject v2.3 and rebase MODE:P vNext to v3.0

## Decision

`MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.3_AMENDMENT.md` is
`REJECTED_BY_WHOLE_SYSTEM_AUDIT`. The only normative vNext architecture is now
`MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0.md`, SHA-256
`a8d58de8d9865d989f567b78d49c1c7de2251e061c7887b6fe2d8018797a830a`.

ReleaseLedger recorded A0 invalidation at `2026-08-01T12:25:30.132887+00:00`
and architecture rebase at `2026-08-01T12:32:34.040972+00:00`. All v3 work
must be revalidated from A0; v2 completion evidence grants no v3 completion.

## Evidence from the complete MODE:P project

| Question | Production/product evidence | v2.3 behavior | Decision |
|---|---|---|---|
| What does 15 seconds constrain? | `02_Agent/director_agent.md` and `LOOP_SPEC.md`: every Shot is an independent generation unit and each Shot is <=15s | one Scene is exactly one 15s GenerationSegment | Reject; capability applies per Shot |
| What does a source span mean? | source location and fact provenance | character midpoint became dialogue timing | Reject; provenance never produces screen/audio time |
| Who selects reference/audio use? | Director owns the visual plan and reference responsibility | assembler derived requirements from all typed scene facts | Reject; Director selects opaque handles via typed intents |
| Where is a requirement consumed? | production Shot contract carries explicit responsibility | generated requirements floated globally with empty Shot bindings | Reject; every requirement binds a Shot/VisualBeat |
| Who builds canonical facts? | local deterministic code owns identifiers and schema validation | FactAssembler was required but no pre-A5 package owned it | Move NormalizedSource and FactAssembler to A1 |
| Is the change a patch? | it changes domain, timing, provider, persistence and VEC | presented as an amendment | Treat as major single-baseline rearchitecture |

## Rejected alternatives

1. **Keep v2.3 and only fix its tests.** Rejected because tests would preserve
   the wrong scene-duration and source-timing semantics.
2. **Add a v2.4 amendment.** Rejected because another overlay would retain
   contradictory authority and make task ownership harder to audit.
3. **Return to v2.2.** Rejected because v2.2 still lacks legal FactAssembler,
   temporal capability and Shot/Beat binding contracts.
4. **Let A5 infer missing behavior.** Rejected because that would modify A1
   domain assumptions downstream and violate fail-close construction.

## Safety result

The rebase did not start Director, DP, Shadow or external media; did not change
the `/mode-p-pilot` production entry; and kept
`production_switch_authorized=false`.
