---
description: Repair R1.3 dual-output projections and renderers against the four exact Golden prompt pairs without changing Master schema or negative-routing code.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R1.3 Dual-output Format Repair

The parent Claude Code session is the only writer and must resolve to
`deepseek-v4-pro`. The Golden expert is read-only. Execute exactly R1.3 and
stop after R1.3; do not start R1.4.

## Governing result of the pre-review

The R1.3 pre-review correctly found that the current storyboard/video
projections and renderers are flat generic documents rather than the user's
successful Golden format. Its findings must be split by the machine task
boundary:

- **R1.3 defects:** D1, D2, D4, D5, D9, D10, D11, D12, D13 and D14.
- **Outside R1.3:** D3 schema expansion and D6-D7 capability/payload routing.
- **False dependency alarm:** D8. `canonical_serialization.py` exists; verify
  its imported APIs read-only, but do not edit it.

Never expand R1.3 merely because an auditor mentioned another file. In
particular, do not edit `schema/generation_segment.py`, `master_parser.py`,
`schema/boundary.py`, `capability_adapter.py`, `payload_compiler.py`,
`payload_manifest.py`, `dual_output_sync.py`, the repair task registry, the
control plane, old v4, or production entrypoints.

D6-D7 are not declared fixed by R1.3. Their existing V5.5-V5.7 tests are
read-only regression tests in this run: do not weaken, rewrite, skip, delete or
turn them into proxies for the four R1.3 required checks. Record the scope gap
truthfully in R1.3 Evidence. If an R1.3 required check genuinely cannot pass
without an out-of-scope edit, stop with `R13_SCOPE_BLOCKED`; never work around
the controller.

## Sources and priority

Use, in order:

1. The eight exact prompt fixtures and pinned R1.2 metadata.
2. `GOLDEN_SET_EVIDENCE_REPORT.md` sections 6-12.
3. `MODE_P_VNEXT_LOOP_SPEC.md` sections 10-11.

Old v4 output and generic Markdown conventions are not format authorities.
Do not read media binaries, the Codex session JSONL, the full knowledge
library, or unrelated LOOP sections.

The exact R1.2 fixtures are immutable inputs:

- `gun_barrel_sb_prompt.json`
- `gun_barrel_video_prompt.json`
- `audience_sb_prompt.json`
- `audience_video_prompt.json`
- `prep_area_sb_prompt.json`
- `prep_area_video_prompt.json`
- `alley_sb_prompt.json`
- `alley_video_prompt.json`
- `prompt_fixture_manifest.json`

Before claiming, verify their current file hashes against the manifest and
their `prompt_text` lengths/SHA-256 against the pinned R1.2 values. R1.3 must
not change a code point, metadata field, filename or manifest hash. New R1.3
fixtures, if needed, go only under a distinct `fixtures/r1_3/` directory.

## Model and expert gates

Invoke only `mode-p-vnext-golden-prompt-auditor`, in the foreground, once
before implementation and once after all tests pass. Verify the Agent tool's
actual `resolvedModel=deepseek-v4-pro` on both calls. A textual self-claim is
not sufficient.

The expert remains read-only and receives only R1.3 paths, the eight exact
fixture texts, R1.2 Evidence, LOOP sections 10-11, Evidence Report sections
6-12, and the required output schema. It must not receive a control token or
write paths.

## Exact write boundary

After a successful R1.3 claim, the parent may edit only:

- `01_调度器/mode_p_vnext/storyboard_projection.py`
- `01_调度器/mode_p_vnext/storyboard_renderer.py`
- `01_调度器/mode_p_vnext/video_projection.py`
- `01_调度器/mode_p_vnext/video_renderer.py`
- `01_调度器/mode_p_vnext/tests/test_v5_1_storyboard_projection.py`
- `01_调度器/mode_p_vnext/tests/test_v5_2_storyboard_renderer.py`
- `01_调度器/mode_p_vnext/tests/test_v5_3_video_projection.py`
- `01_调度器/mode_p_vnext/tests/test_v5_4_video_renderer.py`
- `01_调度器/mode_p_vnext/tests/test_v5_8_dual_output_sync.py`
- new files below `01_调度器/mode_p_vnext/fixtures/r1_3/`
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.3.json`

Although the registry glob could match all `test_v5_*.py`, treat
`test_v5_5_capability_adapter.py`, `test_v5_6_payload_compiler.py` and
`test_v5_7_payload_manifest.py` as read-only regressions. State and lock
changes occur only through `rebuild_control.py`.

Everything else is forbidden, including the eight exact fixtures, R1.2
Evidence, schemas, parsers, Golden registry, media, knowledge sources,
`.claude/settings.local.json`, and production gates.

## Architectural boundary

There is one Director design and one visual timeline. Do not create separate
creative storyboard and video plans.

Because R1.3 cannot change the Master schema, implement a single immutable
**dual-output projection contract** inside an allowed projection module and
reuse that same type from both projectors. It is an output-side carrier, not a
second Director:

- references and their responsibilities;
- target style and stability statements;
- annotation legend;
- shared visual anchors;
- numbered camera phases;
- ordered timeline/panel nodes with stable IDs, ticks, phase ID, node type,
  `[SB]` membership, shot binding and exact display strings;
- explicit HOLD and internal-boundary display records;
- audio nodes;
- targeted prohibitions and their human routing marker;
- final handoff/transition.

Every semantic display string must be copied verbatim from a supplied source
field and retain a stable `source_field_id` or equivalent provenance. The
projection layer may derive only deterministic display facts such as seconds,
ordering, numbering glyphs and section delimiters. It must not summarize,
translate, replace synonyms, drop parentheses, invent transition language or
create a second set of shot semantics.

Keep backward compatibility required by V5.5-V5.8:

- `project_video_prompt(segment)` must still be callable without optional
  presentation data.
- `VideoPromptView.reference_images`, `shot_descriptions`, `audio_track`,
  `forbidden` and `transitions` remain available.
- `StoryboardView.panels` remains available.
- Shot IDs and tick intervals used by `dual_output_sync.py` remain identical
  in both views.

The backward-compatible default must still render the complete ordered
document skeleton from segment fields. Do not emit placeholders such as
`TODO`, `N/A`, `待补充` or fabricated Golden content.

If a feature requires a Master/schema field that does not exist, accept it
only through the shared dual-output projection contract with provenance and
fail closed when required provenance is absent. Do not dynamically attach
attributes to `GenerationSegment`, hide JSON blobs in `narrative_summary` or
`fact_bindings`, hard-code the four scene texts, or make a renderer read Golden
fixtures at runtime.

## Storyboard output contract

The renderer must deterministically emit this semantic order:

1. scene title and derived duration;
2. `@人物`, `@场景`, `@道具` references;
3. black-and-white line-art style declaration;
4. annotation color legend;
5. shared visual anchors;
6. numbering meanings;
7. phase-separated panel descriptions;
8. each panel's time, shot size, focal length and camera motion;
9. red/blue/green/orange annotations where supplied;
10. final HOLD and handoff;
11. storyboard-specific prohibitions.

Content-image instructions remain black and white; colors apply only to
director annotations. Preserve `[start,end)` timing semantics internally.
Render integral seconds without `.0`; render non-integral values
deterministically without false frame precision. Panel count is independent of
duration. Preserve interval panels, repeated HOLD panels, first-appearance
delay, both sides of an internal cut, and start/path/landing nodes.

Storyboard projection selects only nodes explicitly marked `[SB]`; it never
assumes every Cinematic Shot equals one panel.

## Human video-prompt output contract

The renderer must deterministically emit this semantic order:

1. `@上传参考图`;
2. one explicit responsibility for every reference;
3. numbering meanings;
4. storyboard-arrow explanation;
5. storyboard-reference priority;
6. live-action or target style;
7. shared lighting and stability requirements;
8. internal-shot and movement-phase separators;
9. the complete ordered timeline, including non-`[SB]` nodes;
10. `@音轨`;
11. `@禁止`, with a human-readable negative-route marker;
12. `@转场`.

The human document always preserves auditable targeted prohibitions. It must
not claim that every prohibition is submitted to the model; Render Payload
routing is outside R1.3. Emit exactly one preferred execution, never A/B
variants.

Reference duties stay separate: storyboard controls composition/camera/person
placement/movement/internal cuts/landing; character controls identity and
wardrobe; scene controls space/material/light; prop controls geometry/scale/
orientation/operation; audio controls dialogue/tone/rhythm/environment.

## Test-first Golden structure contract

Replace weak flat-format assertions before implementation. The new tests must
fail on the current renderers and cover all four required checks without
self-comparison.

### `storyboard_full_template`

- assert all 11 sections exist once and in fixed order;
- assert phase grouping, per-node timing, focal/shot/motion labels, annotations,
  HOLD and handoff;
- assert no mechanical one-panel-per-second or one-panel-per-shot assumption;
- assert integer time display and half-open tick ownership.

### `video_full_template`

- assert all 12 sections exist once and in fixed order;
- assert each reference has exactly one declared duty;
- assert numbered phases, arrow legend, priority, full timeline, audio,
  targeted prohibitions, route marker and transition;
- assert one preferred execution and no variants.

### `golden_structure_match`

Use an independently authored structural signature fixture under
`fixtures/r1_3/`; do not compute expected values from candidate output.
Exercise four archetypes:

- **gun barrel:** one attention-contraction chain, numbered phase path,
  start/process/landing, final HOLD, and physical anti-vortex correction;
- **audience:** one Generation Segment with three internal shots, hard cuts at
  the supplied boundaries, and WS -> MCU -> ECU information-scale progression;
- **prep area:** one continuous fixed-camera shot, delayed Iuri entry, explicit
  brief pause, and no invented internal cut;
- **alley:** locked event/direction/landing nodes plus an OPTIMIZABLE connection
  record; the prompt retains the preferred plan without offering alternatives.

The signature may describe structure, IDs, section order, counts and required
sentinel strings. It must not duplicate or reconstruct all eight prompt bodies.

### `no_semantic_rewrite`

- inject punctuation, parentheses, distances, color temperatures, correction
  phrases and unique Unicode sentinels into source fields;
- prove both projections and renderers preserve them byte-for-byte;
- prove storyboard `[SB]` node IDs are an ordered subset of video node IDs;
- prove shared shot IDs, phase IDs, anchors, ticks, boundary types and handoff
  IDs agree;
- prove tampering one source binding or tick is detected;
- prove renderer output does not come from the Golden fixture files.

Do not satisfy tests by searching only for generic words such as `镜头`, by
comparing output with itself, by snapshotting the current wrong output, by
lowering assertions, or by adding skipped/xfail tests.

## Control flow

1. Run `rebuild_control audit`, `status` and `next`; require clean audit,
   `next_task=R1.3`, no current owner/token and no project-local settings.
2. Record R0.1-R1.2 Evidence/artifact hashes and all immutable R1.2 fixture
   hashes.
3. Run the scoped Golden pre-review and verify the resolved model.
4. Claim exactly R1.3 with a unique owner and retain the token privately.
5. Add failing focused tests and the independent R1.3 structural signature.
6. Implement only the four allowed production modules.
7. Run the complete registry suite, including unchanged V5.5-V5.7 regressions.
8. Run focused tests for immutability of all eight R1.2 fixtures and manifest.
9. Run the scoped Golden post-review and require `READY`.
10. Write R1.3 Evidence and complete only through the controller.

On any failure after claim, write failure evidence when possible and call
`rebuild_control fail`; never edit state or release the lock manually.

## Evidence and postconditions

R1.3 Evidence must bind every changed implementation/test/new fixture and
report:

- the four named required checks and their concrete test nodes;
- all test/subtest counts;
- immutable R1.2 fixture and manifest hashes before/after;
- exact source-to-output preservation sentinels;
- four-archetype structural coverage;
- verified pre/post expert model and post-review verdict;
- `out_of_scope_findings` for D3 and D6-D7 without claiming them fixed;
- D8 verification result;
- production entry unchanged.

Complete only when audit is clean, R0.1-R1.2 hashes are unchanged, all four
required checks pass, V5.1-V5.8 pass, the Golden expert says `READY`, no
owner/token remains, `next_task=R1.4`, `.claude/settings.local.json` is absent,
and production remains `v4_unchanged`.

Never output `LOCAL_VNEXT_READY`.
