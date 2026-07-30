---
description: Reopen R1.3 again to replace invented Golden archetypes and vacuous delivery/provenance checks with exact source-span-grounded contracts.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R1.3 Exact Golden Grounding Repair

The parent Claude Code session is the only writer and must resolve to
`deepseek-v4-pro`. The Golden expert is read-only. Reopen and repair exactly
R1.3, then stop. Do not start R1.4.

## Second post-completion audit result

The first integrity repair fixed primary contract mutability and the empty
direct-video timeline, but R1.3 is still not acceptable. The replacement
Evidence and tests contain new false-positive claims:

1. `validate_delivery_contract(DualOutputContract(), segment_id)` returns no
   violations. Empty and incomplete contracts pass.
2. `render_storyboard_checked(project_storyboard(segment))` and
   `render_video_prompt_checked(project_video_prompt(segment))` emit incomplete
   documents instead of failing closed.
3. Node display values without provenance pass validation.
4. "Unknown shot" validation compares node shot IDs with the set of shot IDs
   from those same nodes, so it can never detect an unknown shot.
5. Nodes outside the canonical segment interval pass because validation
   receives no segment interval.
6. Duplicate reference duties pass because validation collapses IDs to sets;
   this is not one-to-one validation.
7. Top-level provenance is omitted from `contract_fingerprint`; changing
   `source:A` to `source:B` leaves the fingerprint unchanged.
8. A one-tick positive time at 24000 ticks/second formats as `0s`.
9. `ProjectionComparison` is frozen only at the outer dataclass; its violation
   list remains mutable, and `video_only_nodes_allowed` is computed with
   `>= 0`, which is always true.
10. The "11th storyboard section" and "12th video section" are invented node
    count footers. LOOP §10.1/§11.1 contain no node-count footer.
11. The four hand-authored "Golden archetypes" are not the user's Golden data:
    - gun barrel changes seated Rico into Rico standing/walking at the door;
    - audience changes 12 seconds and 3s/8s cuts into 7 seconds and 2s/5s;
    - prep area changes Iuri's first entry from 5s to 2s;
    - alley changes Pedro's 13-second alley/helicopter/stationary-car sequence
      into Rico, helicopter POV and a moving car chase.
12. Video tests construct and render only the gun-barrel case, while Evidence
    claims all four storyboard/video archetype pairs were rendered.

These failures prove that green tests were obtained from model-authored
substitute stories rather than the exact high-weight fixtures.

## Model and expert gates

Invoke only `mode-p-vnext-golden-prompt-auditor`, in the foreground, once
before invalidation and once after repair. Verify actual
`resolvedModel=deepseek-v4-pro` both times.

The expert must read the exact eight R1.2 prompt fixtures, not summaries. It
must independently check the twelve failures above. A prior `READY` that did
not compare archetype facts with exact fixture text is invalid.

## Verbatim source gate

The only prompt authorities are the current eight R1.2 fixtures with these
prompt-body hashes:

| fixture | characters | prompt text SHA-256 |
|---|---:|---|
| gun_barrel_sb | 1703 | `ce4caf8504593b307d0835120e516f427f4d6ed0e41d2bf35395f95169496ea8` |
| gun_barrel_video | 2544 | `452f8fabc04e6e44b6e8f4d80919ea35b37bd8b765cc52bad94dfaa1a5095cce` |
| audience_sb | 2099 | `1cd5a30f019e97f6651771fa8155229c85c8c969eca0400d7da0db3bb2b02141` |
| audience_video | 2397 | `5fa1815ade3e507807f583c2d4556997bbe8e10538a4badeaaed4eb51bfb8787` |
| prep_area_sb | 1600 | `ed006256727083cba8e1b5ae065fe6e1e7671b02f033c8d4c738d49d3af1b057` |
| prep_area_video | 1811 | `36f45f042d3c3350a3e6a847e321eb9c0e3c9b2be9966a8154237af42d13a46c` |
| alley_sb | 3032 | `8e14b8f21da8a54116d2ff2fe5ef0ec9eab5c03a3d8c55ae28daa184aa766edb` |
| alley_video | 2932 | `a558b598e0718c3bbae1aa717c44f08b07c2939d2feedce5c775ad97fcdc52c9` |

Do not read the original Codex JSONL. Verify these exact bodies from the
already-bound fixtures. Never modify the eight files or their manifest.

## Exact Golden fact gate

At minimum preserve these source facts:

- **gun barrel:** 13 seconds; camera starts at the door; Rico is seated with
  his back to camera under the desk lamp; the attention path contracts from
  room/worktable to hand/tube opening to metal interior; final HOLD; metal
  machining texture is not a vortex or hallucination.
- **audience:** 12 seconds; one Generation Segment with WS, MCU and ECU internal
  shots; planned cuts around the 3s and 8s boundaries; Isabela and Joe in the
  first row; final phone/WhatsApp reveal.
- **prep area:** one continuous fixed-camera shot; Rico remains seated cleaning
  the competition pistol; Iuri first enters at 5s, passes without looking at
  Rico, Rico does not look up; no invented internal cut.
- **alley:** 13 seconds; Pedro, not Rico; handheld low-angle follow, tilt up,
  helicopter moves screen-right to screen-left, cut back to Pedro at the alley
  exit, then attention moves/pushes toward a stationary black car; no
  helicopter POV, no car tracking, no pursuit and no moving car.

Any conflicting test fixture is a P0 failure even if renderer structure is
green.

## Preflight, invalidate and claim

Require clean audit, R1.3 completed, R1.4 unclaimed/uncompleted,
`next_task=R1.4`, no owner/token, local settings absent and production
`v4_unchanged`. Verify all R0.1-R1.2 bound hashes and current R1.3 hashes.

Run the strengthened Golden expert and require `ISSUES`.

Invalidate exactly R1.3 with a reason naming incomplete-contract acceptance,
unenforced provenance, tautological shot validation, missing bounds/duplicate
duty checks, incomplete fingerprint, zero-time formatting, invented node-count
footers, fabricated archetype facts and missing three video archetypes. Confirm
R1.3 becomes next, then claim exactly R1.3.

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
- R1.3-only files below `01_调度器/mode_p_vnext/fixtures/r1_3/`
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.3.json`

V5.5-V5.7 are read-only regressions. Everything else is forbidden, including
the exact R1.2 fixtures/manifest, schema, Master parser, capability/payload
code, `dual_output_sync.py`, control registry, old v4 and production.

## Required source-grounding structure

New R1.3 Golden-case data must be machine-verifiable against an exact R1.2
body. Every extracted semantic value must store:

- fixture filename;
- pinned prompt-body SHA-256;
- character start/end offsets;
- exact extracted text;
- SHA-256 of the extracted UTF-8 text;
- stable source field ID.

Tests must prove `prompt_text[start:end] == exact_extracted_text` and both
hashes match. A paraphrase, translation, renamed person, altered time, inferred
camera viewpoint or model-generated replacement must fail.

Derived formatting values such as tick integers and normalized IDs may exist
only beside the exact source span and must record the deterministic derivation
rule. Do not put the full prompt body into a new fixture.

## Required contract and validation repair

### Complete canonical envelope

The immutable contract must carry or receive for validation:

- canonical segment start/end ticks and ticks-per-second;
- authoritative shot IDs;
- temporal node kind: `at` for an instant/cut or `interval` for duration/HOLD;
- required output kind and required semantic-section set;
- source-grounded values and provenance for all semantic fields.

Do not infer canonical segment duration from selected node min/max.

### Provenance by construction

Use a frozen sourced-value type or an equivalently non-bypassable structure.
Provenance is required for:

- references and each reference duty;
- style and annotation legend;
- anchors and numbering;
- every phase field;
- every node display value;
- audio;
- prohibitions and route marker;
- handoff and transition.

Validation must reject display/provenance key mismatch, empty provenance,
unknown source IDs and changed source text/hash. Fingerprint all semantic values
and all provenance fields.

### Real delivery fail-closed

The primary public `render_storyboard()` and `render_video_prompt()` entrypoints
must validate and fail closed. A caller must not be able to bypass delivery
validation by avoiding a `*_checked()` wrapper.

Storyboard validation must require all applicable LOOP §10.1 semantic items.
Video validation must require all LOOP §11.1 semantic items, including
one-to-one reference duties, arrow legend, priority, style, lighting, full
timeline, audio, targeted prohibitions/route and transition.

Do not require content that is genuinely absent by inventing text. Instead
block delivery until Director input supplies it.

### Structural validation

Reject:

- empty contract/nodes;
- empty or mismatched segment ID;
- duplicate node/phase/reference/duty IDs;
- missing or duplicate duties;
- orphan duties;
- unknown shot IDs;
- nodes outside the canonical segment;
- invalid/overlapping temporal ownership;
- interval used where an instant cut is required;
- unresolved phases;
- invalid node types;
- incomplete provenance;
- placeholders and unadjudicated alternatives.

### Exact time formatting

Positive tick values must never display as `0s`. Use a declared deterministic
precision policy or exact rational representation for sub-precision ticks.
Preserve `at` versus `[start,end)` semantics and incoming ownership.

### Canonical fingerprint/comparison

Use unambiguous canonical serialization, preferably the existing
`canonical_json_dumps`, rather than delimiter-concatenated strings. Include the
canonical envelope, every semantic value, every provenance record and ordering.

Make comparison result collections immutable. Remove tautologies such as
`count >= 0`. Explicitly detect node/text/provenance/phase/anchor/handoff/
reference-duty tampering.

## Renderer format correction

LOOP §10.1 lists 11 ordered semantic items, not 11 Markdown headings.
LOOP §11.1 lists 12 ordered semantic items, not 12 Markdown headings.

Remove:

- `*N 个故事板节点*`
- `*N 个时间线节点*`

Panel metadata and color annotations belong inside panel descriptions.
Internal-shot/movement-phase separators organize the full video timeline.
Do not add artificial footer sections to reach a numeric count.

The resulting external format must remain close to the eight exact successful
prompts, including `@` references, phase separators, per-time states, `@音轨`,
`@禁止` and `@转场`.

## Required tests

Add failing tests before implementation.

### Negative delivery matrix

Call the primary renderer and assert rejection for every individual missing
section/provenance category. Explicitly test empty contract, direct minimal
segment, bad shot ID, out-of-bounds node, duplicate phase/node/reference/duty,
missing duty, orphan duty, missing source span and altered source hash.

### Exact four-pair grounding

For each of gun barrel, audience, prep area and alley:

- load the exact storyboard and video prompt fixture;
- verify pinned body hash;
- verify every structured source span;
- build a distinct storyboard and video delivery;
- project and render both;
- assert actual source timing, people, actions, topology, HOLD/cut behavior and
  final attention target;
- assert the pair shares the intended topology without cross-scene leakage.

All eight outputs must be exercised. A single gun video plus four storyboard
substitutes is a failure.

### Explicit anti-invention tests

Assert:

- gun barrel does not make Rico walk in from the door;
- audience is not shortened to 7 seconds or cut at 2s/5s;
- prep Iuri does not enter at 2s;
- alley uses Pedro and contains no Rico, helicopter POV, tracking car, pursuit
  or moving car.

### Fingerprint/tamper matrix

Call production comparison after independently changing tick, temporal kind,
node order, display text, provenance source/hash/span, phase, anchor, handoff,
reference duty and route marker. Each must fail. Untampered independently built
projections must pass.

### Time and renderer tests

- 0.5s remains `0.5s`;
- one positive tick never becomes `0s`;
- duration comes from canonical segment bounds;
- node-count footers are absent;
- actual semantic order is checked in output without relying on `.find`
  returning `-1` (assert presence before ordering).

No skipped/xfail tests, manual invented story substitutes, output
self-comparison or signature-only validation.

## Verification and Evidence

Run the complete V5.1-V5.8 suite plus R1.2, R1.1, R0.1 and R0.2 regressions.
Run focused reproductions for every negative validation case and all eight
source-grounded outputs. Run the Golden expert post-review and require `READY`.

Replacement Evidence must:

- retract the invented archetype facts and false all-four-video claim;
- bind every source-span fixture and implementation/test artifact;
- report eight rendered exact-source cases;
- name negative validation and tamper test nodes;
- record source prompt hashes unchanged;
- record D3 and D6-D7 as unassigned control-graph gaps, never R1.4 work.

Complete only through the controller. Require audit clean, R0.1-R1.2 hashes
unchanged, no owner/token, `next_task=R1.4`, local settings absent and
production `v4_unchanged`. Never output `LOCAL_VNEXT_READY`.

