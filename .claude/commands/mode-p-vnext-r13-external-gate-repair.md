---
description: Reopen R1.3 under a locked Codex-owned external acceptance gate after the third false-positive completion.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R1.3 Locked External-Gate Repair

This is the only legal next repair command. The parent Claude Code session is
the sole writer and must resolve to `deepseek-v4-pro`. Reopen and repair exactly
R1.3, then stop. Never start R1.4.

## Why the third completion is rejected

The reported `72 passed` is reproducible, but those tests remain self-authored
and do not establish R1.3 correctness:

- `test_v5_2_storyboard_renderer.py` still handwrites `_gb/_aud/_pa/_al`;
- `test_v5_4_video_renderer.py` still handwrites
  `_gbv/_auv/_pav/_alv`;
- neither test loads any of the eight exact R1.2 prompt fixtures;
- `fixtures/r1_3/` contains only `structural_signature.json`; there is no
  character-span registry or source-grounded Golden builder;
- Evidence lists no R1.3 source-span artifact while claiming exact grounding;
- the hand-authored alley substitutes `Pedro在窄巷中行走` for the exact
  `跑动追球` event;
- the production renderer modules still render directly without validation;
- a direct minimal storyboard renders 40 characters and a direct minimal
  video renders 20 characters instead of failing closed;
- an empty contract renders `## EMPTY (0s)` or a blank video;
- missing style provenance, unknown shot IDs, out-of-bounds nodes, duplicate
  phases, invalid node types and duplicate references all produce no specific
  validation violation;
- canonical segment bounds and authoritative shot IDs are still optional
  caller arguments rather than immutable contract authority;
- `video_only_nodes_allowed=(count > 0 or count == 0)` remains a tautology;
- fingerprinting remains delimiter concatenation and omits provenance for
  references, duties, legend, phases, audio, prohibitions and route markers.

Therefore the previous Golden `READY` and current R1.3 Evidence are invalid.

## Immutable external authority

The following test is owned by the independent Codex audit and is read-only to
this repair:

`MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_3_external_acceptance.py`

Before invalidating R1.3, hash it. After every edit and before completion,
verify its SHA-256 is unchanged. Do not edit, copy, replace, monkeypatch, skip,
xfail, conditionally bypass, intercept imports for, or weaken this file. Do not
create a same-named shadow file. Any change is immediate `R13_GATE_TAMPERED`.

The gate fixes the acceptance API:

- `fixtures/r1_3/source_spans.json` with its documented exact schema;
- `mode_p_vnext.fixtures.r1_3.golden_cases.build_golden_deliveries()`;
- frozen `storyboard_projection.SourceSpan`;
- canonical envelope fields on `DualOutputContract`;
- `temporal_kind` on every node;
- `semantic_sources` as unique `(semantic_path, SourceSpan)` pairs;
- fail-closed public functions in `storyboard_renderer.py` and
  `video_renderer.py`.

Do not negotiate or reinterpret this API. Implement it.

## Model and expert boundary

Invoke only `mode-p-vnext-golden-prompt-auditor`, read-only and in the
foreground, once before invalidation and once after repair. Verify the actual
`resolvedModel=deepseek-v4-pro` both times.

The expert must read:

- this command;
- the locked external acceptance gate;
- all eight exact R1.2 fixture JSON files;
- the R1.2 manifest;
- current R1.3 production files, worker tests and Evidence.

Pre-review must return `ISSUES`. A pre-review returning `READY` is invalid and
must stop the run.

## Preflight and controller protocol

Require:

- control audit clean;
- R1.3 completed and R1.4 next;
- no current owner/token;
- `production_entry=v4_unchanged`;
- `.claude/settings.local.json` absent;
- all R0.1-R1.2 evidence/artifact hashes unchanged;
- all eight R1.2 fixture body hashes equal the constants in the locked gate.

Run the locked gate before invalidation and record its real failures. Then use
the controller to invalidate exactly R1.3. The invalidation reason must name
the absent source spans, hand-authored substitutes, fail-open public
renderers, missing canonical envelope, missing provenance coverage and
structural validation gaps. Confirm R1.3 is next and claim exactly R1.3.

Never edit machine state, task graphs, locks or completion lists directly.

## Exact write boundary

The parent may edit only:

- `01_调度器/mode_p_vnext/storyboard_projection.py`
- `01_调度器/mode_p_vnext/storyboard_renderer.py`
- `01_调度器/mode_p_vnext/video_projection.py`
- `01_调度器/mode_p_vnext/video_renderer.py`
- `01_调度器/mode_p_vnext/tests/test_v5_1_storyboard_projection.py`
- `01_调度器/mode_p_vnext/tests/test_v5_2_storyboard_renderer.py`
- `01_调度器/mode_p_vnext/tests/test_v5_3_video_projection.py`
- `01_调度器/mode_p_vnext/tests/test_v5_4_video_renderer.py`
- `01_调度器/mode_p_vnext/tests/test_v5_8_dual_output_sync.py`
- R1.3-only files under `01_调度器/mode_p_vnext/fixtures/r1_3/`
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.3.json`

Everything else is read-only. In particular, never edit:

- the locked external gate;
- the eight R1.2 prompt fixtures or their manifest;
- V5.5-V5.7;
- schema, Master parser, capabilities, payload compiler/manifest;
- control files, task registry, LOOP documents, v4 or production entrypoints.

If this boundary cannot satisfy the locked gate, fail R1.3 with
`R13_SCOPE_BLOCKED`; do not widen scope.

## Required implementation

### Exact source registry

Create `fixtures/r1_3/source_spans.json` exactly as the locked gate specifies.
It must contain all eight closed fixture IDs. Every semantic field used by a
Golden delivery stores fixture filename, pinned body SHA-256, character
start/end, exact sliced text, exact-text SHA-256 and stable field ID.

Offsets are Python Unicode code-point offsets into `prompt_text`. Tests must
execute `prompt_text[start:end] == exact_text`. Do not copy a whole prompt body
into R1.3. Do not translate, summarize or synonym-rewrite a span.

### Source-grounded Golden deliveries

Create `fixtures/r1_3/golden_cases.py` and
`build_golden_deliveries()`. It returns exactly eight distinct public views:

`gun_barrel_sb`, `gun_barrel_video`, `audience_sb`, `audience_video`,
`prep_area_sb`, `prep_area_video`, `alley_sb`, `alley_video`.

All semantic strings in these views must come from verified `SourceSpan`
records or a deterministic derivation recorded beside the source span. It is
for regression tests only; runtime projectors and renderers must never load a
Golden fixture.

Preserve the exact anchors fixed by the external gate. In particular, alley
starts with Pedro running after/bouncing the old football, not merely walking.

### Canonical immutable envelope

Add the locked fields to `DualOutputContract` and `temporal_kind` to nodes.
Authority lives inside the contract:

- canonical start/end tick and ticks-per-second;
- authoritative shot IDs;
- required output kinds and section sets;
- verified semantic sources.

Renderers and validation must not depend on callers remembering optional
bounds or shot-ID arguments. Duration comes from the canonical interval, not
selected node min/max.

### Complete provenance

`SourceSpan` is a frozen value object. Verify fixture ID, prompt hash, offsets,
exact text, exact-text hash and field ID. Bind unique semantic paths for
references, duties, style, legend, anchors, numbering, every phase field,
every node field, audio, prohibitions, route marker, handoff and transition.

Reject absent, duplicate, orphan, unknown or altered source records. A free
string such as `source:Golden.fixture` is not provenance.

### Real fail-closed delivery

The public functions defined in `storyboard_renderer.py` and
`video_renderer.py` must themselves validate before emitting any byte. There
must be no raw public renderer with the same production name that bypasses
validation. Internal unchecked formatting helpers must be private.

Reject incomplete semantic-section sets instead of silently omitting them.
Do not invent missing content.

### Structural and temporal validation

Reject empty/mismatched identity, duplicate node/phase/reference/duty IDs,
missing/orphan duties, unknown shot IDs, out-of-bounds nodes, gaps or illegal
overlap, unresolved phases, invalid node/temporal types, interval-vs-instant
errors, placeholders, alternatives and all source/provenance failures.

Remove the self-referential shot-ID branch. Remove optional-authority behavior.
Remove the always-true `video_only_nodes_allowed` expression.

Use unambiguous canonical serialization for fingerprints. Include canonical
envelope, every semantic value, every source record and ordering. Production
comparison must detect tick, temporal-kind, node-order, text, source
hash/span, phase, anchor, handoff, duty and route tampering.

## Test protocol

Worker-owned tests must import the source registry and Golden builder; delete
all hand-authored `_gb/_aud/_pa/_al/_gbv/_auv/_pav/_alv` substitute stories.
Do not use self-comparison, length-only assertions or signature-only checks.

Run in this order:

1. locked external gate;
2. V5.1-V5.8;
3. R1.2 exact fixtures;
4. R1.1 baseline;
5. R0.1 control;
6. R0.2 entrypoints;
7. locked external gate again;
8. post-repair read-only Golden expert.

Every command must exit zero. No skip/xfail is allowed. Re-hash the locked gate
and all R1.2 fixtures after tests.

## Evidence and completion

Replacement R1.3 Evidence must bind:

- unchanged locked-gate SHA-256;
- source registry and Golden builder hashes;
- all eight prompt-body hashes;
- all eight rendered output hashes;
- named external negative-matrix tests;
- production and worker test results;
- pre-review `ISSUES` and post-review `READY`;
- retraction of every false claim from the prior Evidence.

The post-review may return `READY` only after independently reading the locked
gate and confirming the unchanged hash and zero exit status.

Complete R1.3 only through the controller. Final state must have clean audit,
R0.1-R1.2 hashes unchanged, R1.4 next, no owner/token, no local settings and
`production_entry=v4_unchanged`. Stop without starting R1.4 and never output
`LOCAL_VNEXT_READY`.
