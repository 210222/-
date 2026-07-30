---
description: Reopen R1.3 after false-positive completion and repair immutability, complete-output, Golden-archetype, provenance, and real tamper checks.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R1.3 Integrity Repair

The parent Claude Code session is the only writer and must resolve to
`deepseek-v4-pro`. The Golden expert is read-only. Reopen and repair exactly
R1.3, then stop. Do not start R1.4.

## Why the completed R1.3 must be reopened

The controller is clean and the registered suite is green, but the current
R1.3 evidence contains false-positive semantic claims:

1. `DualOutputContract` and `TimelineNode` are described as immutable but are
   mutable dataclasses containing mutable lists and dictionaries. Both
   projectors mutate the caller's contract and can alias the same object.
2. Direct `project_video_prompt(segment)` creates legacy
   `shot_descriptions` but creates no contract timeline nodes. The video
   renderer ignores `shot_descriptions`, so normal output can contain only a
   reference and the fabricated default style, with no shot timeline.
3. The minimal storyboard output silently omits references, shared anchors,
   required numbering, HOLD/handoff and prohibitions. The minimal video output
   silently omits numbering, arrow explanation, storyboard priority, shared
   lighting, timeline, audio, prohibitions/routing and transition.
4. Renderer defaults invent semantics. Examples include `按秒排列`,
   `不渲染色彩，只渲染光影与材质`, `紫色文字=镜头标签`,
   `真人实拍…8K`, and `画面同前`. These are not copied from a supplied source
   and some conflict with the exact Golden wording.
5. The advertised provenance is not enforced. Top-level semantic strings have
   no source IDs; supplied node display strings may omit provenance entirely.
6. `check_dual_output_sync` still checks only legacy shot count/ticks. Contract
   node IDs, phase IDs, anchors, boundaries, handoff and contract content are
   ignored. A contract tick can be changed while the checker returns
   `is_consistent=True`.
7. `test_tick_tampering_detected` does not call production validation; it only
   asserts two manually constructed values differ.
8. The four Golden archetypes in `structural_signature.json` are not projected
   and rendered by the tests. Tests mainly inspect the signature itself and one
   hand-authored gun-barrel-like contract.
9. Section-order tests do not check positions in rendered output. Counting nine
   or eleven records in the expected JSON is not proof that output follows
   LOOP §10.1/§11.1.
10. Reference-duty tests do not prove one-to-one coverage: two uploaded images
    are accepted alongside five generic duty categories.
11. `_derive_total_duration_s` rounds a half-second segment to integer `0s`.
    `_format_time_display` silently rounds arbitrary fractional ticks to one
    decimal.
12. The Evidence says schema work may be handled by R1.4, but R1.4's allowed
    paths do not include any schema or Master parser file.

These are correctness failures, not optional hardening.

## Model and expert gates

Invoke only `mode-p-vnext-golden-prompt-auditor`, in the foreground, before
invalidation and after all repairs. Verify the Agent tool's actual
`resolvedModel=deepseek-v4-pro` both times. The pre-review must assess the
specific twelve failures above; a prior generic `READY` is invalid evidence.

The expert remains read-only. Do not give it media binaries, the Codex JSONL,
full knowledge library, old v4 source, a control token or unrelated files.

## Immutable authorities

Use:

1. the eight verbatim R1.2 prompt fixtures and their pinned metadata;
2. `GOLDEN_SET_EVIDENCE_REPORT.md` sections 6-12;
3. `MODE_P_VNEXT_LOOP_SPEC.md` sections 10-11;
4. the controller's R1.3 task definition.

All eight exact prompt fixtures, `prompt_fixture_manifest.json`, R1.2 Evidence,
Golden registry/registration, media, knowledge sources and production
entrypoints are immutable.

## Preflight, invalidate and claim

Before edits require:

- control audit clean;
- R1.3 completed and R1.4 neither claimed nor completed;
- `next_task=R1.4`;
- no owner/token;
- `.claude/settings.local.json` absent;
- production entry `v4_unchanged`;
- all R0.1-R1.2 hashes and all nine exact R1.2 fixture/manifest hashes match
  their bound records;
- current R1.3 artifacts match the bound R1.3 record.

Run the strengthened Golden pre-review and require `ISSUES`.

Invalidate exactly R1.3 through `rebuild_control invalidate` with a reason
naming mutable/aliased contract, empty default video timeline, optional
required sections, fabricated defaults, unenforced provenance, vacuous
archetype/order checks and non-production tamper test. Confirm R1.3 becomes the
exact next task, then claim exactly R1.3 with a unique owner. Keep the token
private.

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
- new or corrected R1.3-only files below
  `01_调度器/mode_p_vnext/fixtures/r1_3/`
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.3.json`

State and lock changes occur only through `rebuild_control.py`.

Do not edit `dual_output_sync.py`; it is not in the machine task's allowed
paths. Implement the Golden contract fingerprint and comparison API inside an
allowed projection module and make V5.8 exercise that production API. Keep the
legacy checker as a backward-compatibility regression only.

Treat V5.5-V5.7 implementations and tests as read-only regressions. Do not
touch schema, Master parser, capability/payload modules, control/task registry,
R1.2 files, old v4, or production.

## Required implementation

### 1. Real immutability

Use frozen value objects and immutable nested collections:

- replace lists with tuples in immutable contracts;
- replace free-form phase dictionaries with a frozen typed phase value;
- copy and freeze display/provenance mappings on construction;
- reject mutation after construction;
- never mutate a supplied contract in either projector;
- avoid storyboard/video view aliasing as the proof of synchronization.

Two projections may contain equal immutable values, but correctness must be
established by canonical identity/fingerprint, not Python object identity.

### 2. One deterministic contract builder

Create one shared deterministic builder used by both projectors. Direct
`project_storyboard(segment)` and `project_video_prompt(segment)` must derive
the same shot-bound timeline node IDs and ticks.

The video renderer must never ignore an available canonical timeline in favor
of an empty contract. A segment containing shots must produce timeline nodes
in both projections.

Do not dynamically attach attributes, hide JSON in summary fields, read Golden
fixtures at runtime, or maintain two creative timelines.

### 3. Validation and fail-closed delivery

Validate before rendering:

- contract segment ID matches the canonical segment ID;
- node IDs are unique and ordered;
- intervals are valid and inside the segment;
- phase IDs resolve to defined phases;
- shot-bound visual nodes reference real shot IDs;
- boundary/HOLD/instant forms are structurally valid;
- required display values have non-empty source-field provenance;
- all delivery references have exactly one matching responsibility;
- required human-output semantic sections are present;
- no unadjudicated branch or placeholder exists.

Projection may produce a partial internal view for payload compatibility, but a
human delivery renderer must fail with a typed contract error rather than emit
an incomplete "successful" prompt.

### 4. No invented defaults

Remove semantic defaults that are not deterministic formatting. Do not invent:

- storyboard style, panel cadence or aspect ratio;
- annotation colors/meanings;
- live-action/8K quality;
- lighting/stability;
- HOLD descriptions;
- prohibitions or transitions.

Formatting punctuation, ordered headings, numbering glyphs and seconds derived
from integer ticks are allowed. All creative/visual text must be supplied with
provenance and copied exactly.

### 5. Exact timing

Preserve integer ticks as authority:

- integral seconds render without `.0`;
- non-integral seconds do not collapse to zero or silently round to one decimal;
- interval, instant/cut and HOLD displays remain distinct;
- duration derives from the canonical segment interval, not only the selected
  node min/max;
- boundary tick belongs to the incoming shot.

Use deterministic decimal/rational formatting with an explicit precision
policy. Do not make frame-number claims when FPS is unknown.

### 6. Complete Golden document

Storyboard output must contain the 11 ordered semantic items from LOOP §10.1.
Video output must contain the 12 ordered semantic items from LOOP §11.1.
Several items may share a visible block only when their order and independent
presence are mechanically verifiable; do not relabel a 9/11-item signature as
the full 11/12 contract.

Storyboard `[SB]` nodes are an ordered subset of the full video timeline.
Internal shot/movement phase boundaries and per-node timeline content must be
independently represented. Preserve final HOLD/handoff, audio, targeted
prohibitions and human route marker.

### 7. Production contract fingerprint

Implement canonical serialization/fingerprinting of all output-relevant
contract data inside an allowed projection module, including:

- segment ID;
- references and one-to-one duties;
- style/legend/anchors;
- phases;
- every node ID, shot ID, phase ID, type, `[SB]` flag, ticks, display text and
  provenance;
- audio;
- prohibitions and route marker;
- handoff/transition.

Expose a production comparison function for StoryboardView and
VideoPromptView. It must confirm:

- shared semantic contract fingerprints agree;
- storyboard node IDs are the correct ordered `[SB]` subset;
- all shared node fields agree;
- deliberate video-only nodes are allowed;
- changed tick/text/provenance/phase/anchor/handoff/reference duty is detected.

Tests must call this function. A bare `assertNotEqual` between two test objects
is not tamper detection.

## Required tests

Add failing tests before implementation.

### Complete-output tests

- direct video projection of a non-empty segment has non-empty timeline nodes;
- renderer either emits all required sections or raises the typed incomplete
  contract error;
- minimal internal calls cannot masquerade as deliverable documents;
- required section presence and actual output positions prove 11/12 semantic
  ordering;
- storyboard time/focal/shot/motion data and video full timeline are present;
- no fabricated fallback wording appears.

### Immutability/provenance tests

- assignment to contract, phase, node and nested mappings fails;
- caller-owned mutable inputs cannot change an existing contract;
- projections do not mutate their input contract;
- missing/unknown provenance blocks delivery;
- exact parentheses, temperatures, distances, correction phrases, Unicode and
  punctuation survive projection/rendering byte-for-byte.

### Four real archetype tests

Create independently authored R1.3 structured inputs for all four archetypes,
using exact prompt fixtures only as immutable source evidence. For each of gun
barrel, audience, prep area and alley:

- construct/project both outputs;
- render both outputs;
- assert ordered structural signature on the actual output;
- assert phase/shot topology, HOLD/first appearance/internal cut/optimized
  connection facts appropriate to that archetype;
- assert exact scene sentinels sourced from its prompt;
- assert no cross-scene sentinel leakage.

Do not merely load/count `structural_signature.json`. Do not make four aliases
of one gun-barrel contract.

### Real tamper tests

Start with two valid projections, create a new tampered immutable contract, and
call the production fingerprint/comparison API. Independently tamper tick,
node order, phase ID, text, provenance, anchor, handoff and reference duty; each
must fail for the correct reason. Untampered storyboard/video projections must
pass without relying on shared object identity.

### Reference responsibility tests

Use stable reference IDs. Every uploaded reference ID must map to exactly one
duty record for that same ID. Missing, duplicate, orphan and generic
category-only duties must block delivery.

No skipped/xfail tests, output-self-comparison, signature-self-validation,
generic-word-only checks or runtime Golden fixture reads are allowed.

## Verification and evidence

Run:

- complete V5.1-V5.8 registry suite;
- R1.2 exact Golden suite;
- R1.1 baseline suite;
- R0.1 control suite;
- R0.2 active-entrypoint suite;
- focused reproduction proving the previous empty video output, mutable alias
  and ignored contract tamper now fail/pass correctly.

Run the strengthened Golden expert post-review and require `READY`.

The replacement R1.3 Evidence must bind all artifacts and report concrete test
node IDs for:

- `storyboard_full_template`;
- `video_full_template`;
- `golden_structure_match`;
- `no_semantic_rewrite`;
- immutable nested values;
- direct video timeline;
- delivery fail-closed behavior;
- four actual archetype render pairs;
- one-to-one reference duties;
- production fingerprint tamper matrix;
- exact fractional duration behavior.

It must explicitly retract the previous 9/11 full-template claim and the
vacuous tamper/archetype claims. It must not say R1.4 can modify schema.
Record D3 and D6-D7 as unassigned control-graph gaps that must be resolved
before final local completion; do not claim them fixed.

Complete R1.3 only through the controller. Postconditions: audit clean,
R0.1-R1.2 hashes unchanged, no owner/token, `next_task=R1.4`, project-local
settings absent, production `v4_unchanged`. Never output
`LOCAL_VNEXT_READY`.

