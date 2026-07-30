---
description: Reopen R1.3 under the strengthened Codex-owned semantic-coverage gate after the fourth false-positive completion.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R1.3 Semantic-Coverage Repair

This is the only legal next repair command. The parent Claude Code session is
the sole writer and must resolve to `deepseek-v4-pro`. Reopen and repair exactly
R1.3, then stop. Never start R1.4.

## Why the reported 17/17 is rejected

The first Codex external gate passed, and no gate monkeypatch was found.
However, that gate proved only that 21 selected anchor spans existed. It did
not prove that the full Golden outputs were source-grounded or that one
Director timeline was projected to both outputs.

The strengthened external gate currently produces:

```text
16 passed, 11 failed
```

The eleven failures are authoritative:

1. the contract lacks `semantic_sources_sha256` and
   `semantic_derivations`;
2. storyboard/video views of a scene do not share one immutable canonical
   contract, and every pair fails production comparison;
3. most emitted semantics have no source span or declared deterministic
   derivation;
4. delimiter-concatenated fingerprints have a demonstrated collision;
5. the four Golden timelines are phase summaries instead of complete
   per-second state timelines;
6. audience and alley have no explicit instant nodes at internal cut
   boundaries;
7. rendered outputs omit or corrupt full Golden-format sentinel text;
8. required storyboard/video section sets are empty;
9. the semantic-source registry has no canonical authority hash;
10. changing semantic text while retaining the old source span is accepted;
11. worker tests still construct handwritten `_gb/_aud/_pa/_al` and
    `_gbv/_auv/_pav/_alv` substitutes.

Examples of invalid current bindings that must be removed:

- gun-barrel text meaning "not a vortex or illusion" is used as target style,
  lighting, arrow explanation and storyboard priority;
- "camera at the doorway" is used as handoff and transition;
- the storyboard style span starts in the middle of "13 frames" and misses the
  full black-and-white line-art declaration;
- required section sets are empty even though renderers claim complete
  delivery.

The previous R1.3 Evidence and Golden `READY` are therefore invalid.

## Strengthened immutable external authority

The following file is Codex-owned and read-only:

`MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_3_external_acceptance.py`

Its required SHA-256 is:

```text
de251e5dd97cc7b03b3ae27619f01e2587ce69efe23971a803e61d07fccc47cd
```

Before invalidating R1.3, verify the hash and reproduce exactly 16 passes and
11 failures. After every implementation edit and before completion, verify the
same hash. Never edit, copy, replace, skip, xfail, shadow, monkeypatch,
conditionally bypass or intercept imports for this gate. Any change is
`R13_GATE_TAMPERED`.

Do not reinterpret a gate assertion as a formatting trick. Implement the
production invariant that the assertion represents.

## Model and expert boundary

Invoke only `mode-p-vnext-golden-prompt-auditor`, read-only and in the
foreground, once before invalidation and once after repair. The parent must
verify actual `resolvedModel=deepseek-v4-pro` both times.

The expert must read:

- this command;
- the strengthened external gate;
- all eight exact R1.2 prompt fixtures and their manifest;
- `fixtures/r1_3/source_spans.json`;
- `fixtures/r1_3/golden_cases.py`;
- current R1.3 production files, worker tests and Evidence.

The pre-review must return `ISSUES` and name the eleven failure classes above.
A pre-review returning `READY` is invalid and must stop the run.

## Preflight and controller protocol

Require:

- control audit clean;
- R1.3 completed and R1.4 next;
- no current owner/token;
- `production_entry=v4_unchanged`;
- `.claude/settings.local.json` absent;
- all R0.1-R1.2 evidence/artifact hashes unchanged;
- all eight R1.2 fixture body hashes still match their pinned constants;
- strengthened gate hash matches the value above;
- strengthened gate reproduces 16 passes and 11 failures.

Then use `rebuild_control.py` to invalidate exactly R1.3. The reason must name:
incomplete semantic coverage, separate per-output contracts, reduced
timelines, missing cut instants, empty required-section authority,
non-canonical fingerprinting, insufficient source-authority validation,
semantic rewrite acceptance and handwritten worker fixtures.

Confirm R1.3 becomes next and claim exactly R1.3. Never edit machine state,
task graphs, locks or completion lists directly.

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

- the strengthened external gate;
- the eight R1.2 prompt fixtures or their manifest;
- V5.5-V5.7;
- schema, Master parser, capabilities, payload compiler/manifest;
- controller, task registry, LOOP documents, v4 or production entrypoints.

If this boundary cannot satisfy the gate, fail R1.3 with
`R13_SCOPE_BLOCKED`; do not widen scope.

## Required production design

### 1. One Director contract per scene

Build exactly one frozen `DualOutputContract` for each of the four scenes.
The storyboard view and video view must reference/project that same canonical
contract, not independently reconstructed contracts.

The contract owns the union timeline and all shared semantics. Storyboard
selects the ordered `[SB]` nodes; video selects the complete ordered timeline.
All four pairs must be consistent through the production
`compare_projections()` path.

Do not prove synchronization merely by Python object identity. Tests must also
show that independently serialized/reloaded equivalent contracts compare
consistently and that semantic/topology tampering is detected.

### 2. Full Golden timelines

Replace phase-summary nodes with source-grounded per-second state nodes.
Required minimum state-node counts are:

| Scene view | Required state nodes |
|---|---:|
| gun_barrel storyboard | 13 |
| gun_barrel video | 14 |
| audience storyboard | 12 |
| audience video | 12 |
| prep_area storyboard | 10 |
| prep_area video | 10 |
| alley storyboard | 13 |
| alley video | 13 |

Preserve exact temporal meaning from the prompt fixtures. Add explicit
`temporal_kind="at"` nodes for:

- audience internal cuts at 3s and 8s;
- alley internal cuts at 5s and 9s.

An `at` node may have equal start/end ticks. An `interval` node must have
strictly positive duration. Do not create fake text or duplicate phase prose
to meet counts.

### 3. Complete source coverage

Every emitted semantic string must have a unique semantic path bound to a
verified `SourceSpan`, or to an explicit deterministic derivation whose rule
and input source paths are stored in the contract.

Coverage includes:

- reference tags and reference responsibilities;
- target style and visual style;
- complete arrow/annotation legend;
- shared visual anchors;
- numbering semantics;
- every phase label, shot/camera description and temporal range;
- every node description, shot label, framing, action, movement and hold;
- audio;
- prohibitions;
- handoff and transition;
- any output route marker.

A free provenance string is not a source. A summary, translation, synonym,
model-authored rewrite or unrelated source span is not exact grounding.

Creative semantic values must equal their bound span text. Only mechanical
values may be derived, and each derivation must use a closed rule such as
`prefix`, `join`, `tick_format` or `route_classification`, with explicit input
paths. No unrestricted "model inference" derivation is allowed.

### 4. Source authority and tamper rejection

Add `semantic_sources_sha256` to the immutable contract. Compute it with the
project's canonical JSON serializer over every ordered semantic path and every
`SourceSpan` field:

- fixture ID and filename;
- prompt-body SHA-256;
- start/end offsets;
- exact text;
- exact-text SHA-256;
- field ID.

Validation must reject:

- wrong prompt-body hash;
- shifted offsets even when length is unchanged;
- wrong field ID or fixture ID;
- slice mismatch;
- exact-text hash mismatch;
- missing, duplicate, orphan or unknown semantic paths;
- an altered semantic value paired with an unchanged old span;
- an altered derivation or derivation input.

Runtime production code must not load Golden fixture data. Fixture-authority
loading is confined to the R1.3 Golden builder/tests; production validation
works from immutable contract authority and canonical hashes.

### 5. Correct the registry and field mapping

Expand `source_spans.json` from selected anchors to full semantic coverage.
Every record must point to the semantically correct text.

Do not reuse:

- "not a vortex or illusion" as style, lighting, priority or legend;
- "camera at the doorway" as handoff or transition;
- a partial `"13 frames"` substring as the storyboard style;
- a title substring as numbering semantics.

The storyboard style must include the complete line-art/black-and-white
declaration from the storyboard fixture. Handoff, transition, audio,
prohibition and route values must use their own source or an allowed
deterministic derivation.

### 6. Required section authority

Populate and validate non-empty `required_storyboard_sections` and
`required_video_sections`. They must reflect the actual Golden delivery
contracts and be output-kind specific.

Public renderers must fail closed when a required section is absent, empty,
unresolved or unsourced. They must not silently omit a section and must not
invent a default.

### 7. Canonical collision-resistant fingerprint

Replace newline/delimiter concatenation with unambiguous canonical JSON
serialization. Reuse `canonical_json_dumps` if its current API is suitable.
The fingerprint must cover:

- every contract envelope field;
- required section sets;
- every timeline/phase field and order;
- every emitted semantic value;
- every `SourceSpan` field and semantic path;
- `semantic_sources_sha256`;
- every derivation rule and input path.

The demonstrated `("x\nref:y",)` versus `("x", "y")` collision must no
longer collide. Production comparison must reject changes to topology,
temporal kind, ticks, text, source authority, derivations, duties, anchors,
audio, prohibitions, handoff, transition and route.

### 8. Real worker tests

Delete handwritten Golden builders from:

- `test_v5_2_storyboard_renderer.py`;
- `test_v5_4_video_renderer.py`;
- any equivalent R1.3 worker test.

All Golden format tests must import
`mode_p_vnext.fixtures.r1_3.golden_cases.build_golden_deliveries()` and render
the eight real source-grounded views. Tests may add deliberately invalid
contracts only for negative cases.

Do not satisfy section/order checks using counts, footers, sentinels,
self-comparison or duplicated expected constants.

### 9. Evidence correction

Replace R1.3 Evidence and explicitly retract the earlier false claims that:

- 21 anchor spans represented complete fixture-body grounding;
- separate storyboard/video contracts constituted one dual-output timeline;
- phase summaries constituted full per-second Golden timelines;
- the existing fingerprint covered complete provenance;
- handwritten worker data represented the eight exact Golden views.

Evidence must bind the strengthened gate hash, full registry hash, Golden
builder hash, semantic-source authority hashes, all eight rendered output
hashes, named negative tests, full test outputs and both expert reviews.

## Test and completion protocol

Run in this order:

1. strengthened external gate — all 27 tests must pass;
2. V5.1-V5.8;
3. R1.2 exact fixtures;
4. R1.1 baseline;
5. R0.1 control;
6. R0.2 entrypoints;
7. strengthened external gate again — all 27 tests must pass;
8. post-repair read-only Golden expert — must return `READY`.

No skip, xfail, expected failure, monkeypatch of the gate, import interception
or warning-only result is allowed. Re-hash the gate and all R1.2 fixtures after
tests.

Complete R1.3 only through the controller. Final state must show:

- clean control audit;
- completed tasks R0.1 through R1.3;
- R1.4 next;
- no owner/token;
- all R0.1-R1.2 hashes unchanged;
- no `.claude/settings.local.json`;
- `production_entry=v4_unchanged`;
- strengthened gate hash unchanged.

Stop without claiming or starting R1.4. Never output `LOCAL_VNEXT_READY`.

## Persistence rule

This repair may span multiple Claude Code turns. Implementation breadth or
response-size limits do not justify changing approach, weakening the gate,
failing the task or asking the user whether to continue.

While R1.3 remains actively claimed, resume with:

```text
/mode-p-vnext-r13-semantic-coverage-continue
```

Keep the same owner and retained token. Do not invalidate, re-claim, recover,
fail or complete at an intermediate checkpoint. If a turn ends before all 27
external tests pass, leave the claim active and emit the structured
`R13_CONTINUATION_CHECKPOINT` required by the continuation command.
