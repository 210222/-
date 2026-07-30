---
description: Continue the already-claimed R1.3 semantic-coverage repair from the verified 17-pass/10-fail checkpoint.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R1.3 Semantic-Coverage Continuation

Continue the existing R1.3 repair. This is not a new task, a new claim or a
request to change approach.

The parent Claude Code session remains the sole writer and must resolve to
`deepseek-v4-pro`. The full authority remains:

`/mode-p-vnext-r13-semantic-coverage-repair`

Read that command in full before editing. All of its write boundaries,
forbidden paths, Golden requirements, test order and final postconditions
remain mandatory.

## Verified continuation checkpoint

The independent Codex checkpoint is:

```text
control status: IN_PROGRESS
current_task: R1.3
current_owner: ds-r13-semantic-20260723
next_task: R1.3
production_entry: v4_unchanged
external gate: 19 passed, 8 failed
external gate SHA-256:
de251e5dd97cc7b03b3ae27619f01e2587ce69efe23971a803e61d07fccc47cd
```

Completed production work now includes the contract authority fields,
canonical fingerprinting, source-authority validation, shared scene
contracts, instant-boundary support, fail-closed renderers and removal of
handwritten worker substitutes. Do not revert it.

Codex corrected one contradiction in the external gate: a shared Master
contract is now counted through its projection. The gun contract must contain
14 total video states, of which 13 have `sb_node=True` for the storyboard.
The gate no longer requires one shared `contract.nodes` tuple to have two
different raw lengths.

Before editing, independently reproduce this exact state. If R1.3 is no longer
owned by `ds-r13-semantic-20260723`, the gate hash differs, or production entry
is not `v4_unchanged`, stop with `R13_CONTINUATION_STATE_MISMATCH`.

## Controller continuity

Do not run `invalidate`, `claim`, `recover`, `fail` or `complete` at the start.
The claim is already active. Continue using the lock token retained by the
parent session. Never print the token or write it to a file.

Do not release or complete the claim at an intermediate checkpoint. Only the
final all-green run may call `complete`.

If the current model/tool turn ends before all phases are complete, leave the
claim active and return:

```text
R13_CONTINUATION_CHECKPOINT
completed_phase: <A|B|C>
gate_result: <passed>/<27>
remaining_failures:
- <exact test id>
files_changed:
- <path>
next_action: continue the same R1.3 claim with this command
```

Response size or implementation breadth is not a blocker and is not a reason
to ask the user for a different approach. Work in the phases below.

## Remaining authoritative failures

Exactly these eight external tests currently fail:

1. `test_all_eight_valid_deliveries_render_through_public_modules`
2. `test_no_cross_scene_character_leakage`
3. `test_rendered_outputs_preserve_exact_success_facts`
4. `test_every_emitted_semantic_value_has_exact_source_binding`
5. `test_full_per_second_state_timeline_is_preserved`
6. `test_internal_cuts_are_zero_duration_at_boundaries`
7. `test_rendered_outputs_have_complete_golden_format_sentinels`
8. `test_required_section_sets_are_declared`

Do not fix only the assertions. Fix the production invariant and the real
Golden data each assertion represents.

The first, second, third, sixth and seventh failures currently cascade from
invalid Golden semantic mappings: for example, the creative
`style_declaration` value differs from its retained source span. Treat the
underlying mapping failure once; do not add renderer bypasses.

## Phase A — completed production authority

Phase A is already complete. Verify but do not redesign it:

1. Replace delimiter/newline fingerprinting with canonical JSON
   serialization.
2. Include the complete canonical envelope, required sections, ordered
   timeline and phases, every semantic value, every `SourceSpan` field,
   `semantic_sources_sha256` and every derivation in the fingerprint.
3. Recompute and validate `semantic_sources_sha256`; do not merely trust the
   value stored by the caller.
4. Add closed validation that an emitted semantic value equals its bound
   source text or the result of an explicitly allowed deterministic
   derivation.
5. Reject missing, duplicate, orphan and altered semantic paths, source
   fields, derivation rules and derivation inputs.
6. Enforce output-kind-specific required section sets.
7. Preserve fail-closed public renderer behavior.

Run the strengthened external gate once to reproduce 19/27, then continue
immediately to Phase B.

## Phase B — one contract and full Golden timelines

Rebuild `fixtures/r1_3/source_spans.json` and `golden_cases.py` from the eight
immutable R1.2 fixtures:

1. Construct one frozen canonical contract per scene.
2. Return storyboard and video views over the same scene contract.
3. Put the union timeline in that contract; storyboard selects `[SB]` nodes
   and video selects the full ordered timeline.
4. Preserve the authoritative projected state-node counts:
   - gun: storyboard 13, video 14;
   - audience: 12/12;
   - prep area: 10/10;
   - alley: 13/13.
5. Add explicit `at` cut nodes for audience 3s/8s and alley 5s/9s.
6. Expand source coverage to every emitted semantic category named by the
   main repair command. The current registry has 21 records and each shared
   scene contract uses only four; this is incomplete.
7. Correct semantically false span mappings. Never use an unrelated valid
   span merely to satisfy provenance.
8. Use deterministic derivations only for mechanical formatting; record
   closed rule names and exact input semantic paths.
9. Render all eight views and verify the complete Golden-format sentinel
   sequence and duration.
10. Add `prohibition_route` to `required_video_sections`; it is the only
    currently missing video section authority.
11. Add the gun video's explicit 13s terminal state as a video-only
    `panel`/`hold` state with `sb_node=False`. It must be a valid instant or
    otherwise valid terminal state inside the canonical 13s bounds, not an
    invented interval beyond the segment.

Do not hand-enter 100+ expanded `SourceSpan` records independently. Add an
R1.3-only deterministic registry generator under `fixtures/r1_3/`:

1. Load the eight immutable R1.2 fixture bodies read-only.
2. Consume a small declarative mapping of semantic path, fixture ID, exact
   source needle and occurrence index.
3. Locate Unicode code-point offsets and require exactly one selected
   occurrence.
4. Compute prompt and exact-text hashes mechanically.
5. Emit records in canonical sorted order.
6. Fail if a needle is absent, ambiguous without an occurrence index, or
   points to an unrelated semantic category.
7. Re-run the generator in tests and require byte-identical
   `source_spans.json`.

Where a current Golden value is a paraphrase, prefer changing it to the exact
fixture span. Use a declared allowed derivation only for mechanical display
formatting. Never expand the registry by binding an unrelated span merely
because its hash and offset validate.

Do not copy or edit R1.2 fixtures. Runtime projectors/renderers must not load
Golden fixture files.

After Phase B, run the strengthened gate again. Record the result. Do not
complete R1.3. Continue immediately to Phase C.

## Phase C — worker tests, full regression and Evidence

1. Confirm the already-completed removal of handwritten Golden builders from
   V5.2, V5.4 and equivalent R1.3 worker tests.
2. Confirm all positive Golden tests use `build_golden_deliveries()`.
3. Retain explicit synthetic contracts only for negative validation tests.
4. Add production-path tests for source/value/derivation tampering,
   fingerprint collision resistance, shared topology, cuts and required
   sections.
5. Run the complete test order from the main repair command.
6. Require all 27 external tests to pass twice with the locked hash unchanged.
7. Run the read-only Golden auditor and require `READY`.
8. Replace R1.3 Evidence with the required retractions and hashes.
9. Complete R1.3 through the controller using the retained token.

Stop after the final controller audit shows R1.4 next and no owner/token.
Never claim or start R1.4.
