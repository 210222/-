<!-- MODE_P_VNEXT_AUTHORITY: architecture-v3.1 -->

# MODE:P vNext — Architecture-v3.1 Isolated Workspace

This package is the isolated implementation workspace for the sole normative
architecture:

- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.1.md`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_CONSTRUCTION_V3_1.md`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_TASKS.json`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_STATE.json`

Run `python -m mode_p_vnext.release_control audit/status/next` from
`01_调度器`. Only the exact task returned by `next` may be claimed. v2.0-v2.3,
the old loop/implementation/progress files, R/DDO/CPL queues and
`director_vnext1` are `HISTORICAL_READ_ONLY`; v2.3 is rejected and v3.0 is
superseded by the v3.1 conflict repair. Neither grants v3.1 completion.

## Architecture boundaries

- Director is the sole visual designer. Fresh DP only emits bounded
  `RevisionRequest`; local code owns IDs, hashes, 24000-tick time, N+1
  boundaries, typed bindings and projection.
- One Shot is one initial generation unit. Every Shot is independent and no
  longer than the capability maximum (15 seconds for the default SD2.0
  profile); a Scene is not capped at 15 seconds.
- Source spans are provenance only. They never produce screen/audio timing.
- VEC compiles to one canonical `ProjectionAST`; Storyboard and Video derive
  from it before Gate 0, and Gate 0 passes its immutable bundle to Fresh DP.
- Text validation cannot claim visual acceptance. Real media and explicit
  hash-bound owner preview approval belong to A10.

## Isolation rules

- Do not import runtime modules from `01_调度器/mode_p` or
  `01_调度器/legacy_mode_p`.
- Do not read v4 knowledge indexes, caches, Sessions or delivery as vNext
  runtime input. v4 may be exercised only through registered black-box tests.
- Do not copy old compiler behavior or the 27K prompt as a hidden fallback.
- Do not load media binaries into Director/DP text context.
- Rebuild cannot enable Shadow, Pilot, Canary or Production, clear a kill
  switch, submit externally or change the real `/mode-p-pilot` entry.
- `production_entry=v4_unchanged` and
  `production_switch_authorized=false` remain invariant through A10.

A future production switch requires a separately scoped, authorized and
audited change with rollback; no A-task or feature flag can activate it.
