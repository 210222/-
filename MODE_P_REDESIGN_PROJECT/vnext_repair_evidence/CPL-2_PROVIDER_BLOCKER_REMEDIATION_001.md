# CPL-2 DeepSeek Director Historical-Blocker Remediation

## Scope and current decision

This document records a controlled pause of the CPL-2 real-provider Shadow
validation.  It does not mark CPL-2 complete, does not change production v4,
and does not claim that any storyboard or video has been visually accepted.

The current provider uses the authenticated local Claude Code CLI with the
exact model `deepseek-v4-pro`, text only.  It supplies no image, video, or
local-file attachment to DeepSeek.  Therefore DeepSeek can validate text
contracts and Director decisions, but cannot validate mirror direction, hand
ownership, eye-line, wardrobe, prop orientation, or frame continuity in a
rendered result.

## Observed failures

| ID | Evidence | Root cause | Why the old behavior was insufficient |
| --- | --- | --- | --- |
| P-01 | `CPL-2_UNKNOWN_TEXT_SHADOW_005/FAILED_TEXT_SHADOW.json`: `beats[1]` had no `action_paths` | The Python `BlockingBeat` contract required a non-empty action path, while the CLI JSON Schema only said that the field was an array. | A response could satisfy JSON type shape and still be impossible to accept semantically; the failure was discovered only after a long model call. |
| P-02 | The same run recorded a B0 response rejected before decoding as non-strict JSON, then a corrected response rejected by P-01. | CLI presentation/model behavior can add wrappers or omit a semantically required field despite a text instruction. | “Please output JSON” and one generic repair message were not enough to make the required B0 causal structure salient. |
| P-03 | Run 005 took 1,031.5 seconds before it failed. Its recorded calls were E0 156,890 ms, S1 314,844 ms, B0 attempt 1 246,719 ms, B0 attempt 2 311,516 ms. | Maximum-effort model calls plus a large repeated packet and late semantic failures multiply wall time. These are transport usage measurements, not a claim about private model reasoning. | The old checkpoint wrote a hash and summary only; it could not reconstruct the accepted E0/S1 state to resume B0/B1. |

## Implemented corrective controls

### 1. Contract parity before model output

`strict_json_schema(BlockingCommit)` now applies `minItems: 1` to every B0
collection whose Python contract is non-empty:

- `BlockingCommit.beats` and `BlockingCommit.constraint_refs`;
- `BlockingBeat.character_states`, `BlockingBeat.action_paths`, and
  `BlockingBeat.constraint_refs`;
- `CharacterBlockingState.visible_body_parts`.

All string fields in the transport schema use `minLength: 1`.  This is a
transport-level early guard; Python dataclass validation remains the final
semantic authority.

### 2. Explicit B0 causal preflight and targeted repair

The B0 instruction now requires every `beats[i].action_paths` value to be a
non-empty list of causal strings:

`character: motivation -> physical action -> spatial/result state`

It prohibits empty arrays, placeholders, and camera/edit language.  The same
requirements appear in a structured stage checklist and in the one permitted
repair instruction.  The repair remains bounded to one additional response;
it does not loop indefinitely or retain raw model text.

### 3. Maximum reasoning without chain-of-thought storage

All Director stages now invoke Claude Code with `--effort max`.  The provider
asks the model to stress-test constraints, alternatives, causal paths, edge
cases, and risks privately.  Its allowed output is only the JSON contract and
the contract's short auditable reason/tradeoff/risk fields.  Complete private
reasoning is neither requested, logged, nor written to project artifacts.

### 4. Smaller knowledge payloads

B0 and B1 no longer serialize an entire `DecisionPacket` with normalization
and field-provenance internals.  They receive a bounded runtime projection:
selected capsule metadata, permitted execution guidance, applicability,
conflict status, and identifiers.  Source-document evidence stays offline.
This preserves the Director's ability to use the knowledge capsules while
removing fields that do not affect the current decision.

### 5. Actual recovery, not merely checkpoints

`CHECKPOINT_E0_S1.json` now stores the accepted E0 state, full structured S1
state, and deterministic K1 fingerprint.  A `resume=True` Shadow invocation:

1. restores only that accepted checkpoint;
2. reconstructs the typed Phase-A result;
3. re-runs deterministic K1 and verifies its fingerprint;
4. calls only the failed/later B0 and B1 stages;
5. merges old and new call records into the final evidence.

It refuses a missing, malformed, completed, scene-mismatched, director-
mismatched, or K1-mismatched checkpoint.  It never resumes a partial B0/B1
object as if it were approved.

## Verification performed

- Focused CPL-2 provider tests: `10 passed`.
- CPL-0, CPL-1, CPL-2, and DDO-0 through DDO-6 regression selection:
  `49 passed`.
- Tests include empty B0 action-path rejection, stage-specific repair text,
  transport-schema `minItems`, and recovery that performs only B0 then B1
  after an accepted E0/S1 checkpoint.

## Required next action (deliberately not run during this pause)

Create a new Shadow run after review of these controls.  It must begin from a
fresh E0/S1 checkpoint because historic run 005 predates the recoverable
checkpoint format.  If B0 fails, rerun the same run ID with `resume=True`;
the evidence must show no repeated E0/S1 provider calls.  CPL-2 may be marked
complete only if a fresh run accepts E0, S1, B0, and B1 in that order, retains
the `TEXT_VALIDATED` ceiling, and leaves production v4 unchanged.

## Explicit non-goals

- This change does not authorize media generation or a production entry
  switch.
- It does not make a text model a visual evaluator.
- It does not equate valid storyboard/video prompts with an accepted rendered
  video.  Those remain separate downstream evidence and human/visual review
  gates.
