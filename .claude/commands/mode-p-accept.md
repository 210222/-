---
description: Explicitly run the fixed MODE:P deepseek-v4-pro semantic acceptance once.
argument-hint: [new run id, for example run-002]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P Explicit Model Acceptance

Run exactly one acceptance attempt for $ARGUMENTS according to
MODE_P_REDESIGN_PROJECT/MODEL_ACCEPTANCE_PROTOCOL.md.

## Entry boundary

- This command must be invoked explicitly by the user.
- Never schedule it with /loop.
- Never modify activity code, tests, role contracts, templates, or knowledge to
  make the fixed case pass.
- The parent Claude Code session must be deepseek-v4-pro.
- The actual resolvedModel of Director and every DP must be deepseek-v4-pro.
- Do not launch `Explore`, `Plan`, `general-purpose`, or any helper Agent. The
  only permitted Agent calls are one `mode-p-director` identity (resumed when
  needed) and fresh `mode-p-dp` reviews. Read required files in the parent.
- This project is intentionally not a Git repository and uses
  `worktree.bgIsolation: none` for background Agent writes. Never call
  `EnterWorktree`, create a worktree, or change isolation during acceptance.
- Do not create Claude task-list objects (`TaskCreate`/`TaskUpdate`). Follow the
  numbered sequence below directly so orchestration does not consume attention.
- Do not inspect historical run directories or runtime implementation to infer
  the workflow. The complete operational sequence is specified below. Use a
  module's `--help` only when a listed command itself rejects its arguments.

## Preflight

1. Read SUPERVISION.lock, MODEL_ACCEPTANCE_STATUS.md, the protocol, and current
   local test evidence.
2. Stop when another writer or acceptance run is active.
3. Require a new unique run ID. Never reuse run-001 or any existing directory.
4. Verify the fixed input hash.
5. Prepare the run with model_acceptance_guard, then create the official episode
   scaffold with mode_p_pilot before any creative write.

## Director

Start exactly one mode-p-director Agent for all four scenes. Give it the fixed
input, run/session paths, active role contract, Master template, official pilot
manifests, and selected minimal knowledge paths.

Launch it with the custom Agent definition's `model: inherit`; do not pass
`deepseek-v4-pro` as an Agent-tool model option. The provenance guard, not the
Agent-tool enum, verifies the actual inherited `resolvedModel`.

Tell that one Director to write incrementally and only for the current pilot
stage: first `SCRIPT_FACTS.md`; after deterministic validation and skeleton
generation, the episode documents; then write one scene's `DIRECTOR_MASTER.md` per Write call.
A long or quiet generation is not evidence of failure. Never use TaskStop
merely because output has not appeared, never replace the Director,
and never launch a second Director for the same run. If the launched Director
actually fails or is interrupted, invalidate the run and stop; a new Director
requires a new run ID.

Immediately bind the launch through:

~~~powershell
python -m model_acceptance_guard bind-director --run-dir <run-dir> --agent-id <internal-agent-id>
~~~

Do not run precheck unless this exits zero. On failure, run model_acceptance_guard
invalidate with the exact reason and stop.

Every Director Write must pass the configured KB Guard Hook. A Hook error makes
the current acceptance run invalid even if Claude Code reports that the file was
written.

## Exact operational sequence

Run Python modules from `01_调度器/mode_p`. Use `py` when `python` is not on
PATH. Let `<episode>` be `<run-dir>/episode`, `<dp-dir>` be
`<episode>/dp_review`, and `<review-dir>` be `<episode>/episode_review`.

1. Before any Agent call:

~~~powershell
py -m model_acceptance_guard prepare --run-id <run-id> --owner claude-code
py -m mode_p_pilot <fixed-input> --session-dir <episode>
~~~

2. Confirm `PILOT_PREP_STATUS.json` says `awaiting_script_facts`. Launch the one
   `mode-p-director` to fill only the generated `SCRIPT_FACTS.md`. Bind that
   exact call with `model_acceptance_guard bind-director`, wait for a normal
   Agent completion, then run `mode_p_pilot` again. It validates facts and
   generates the exact Bible/Ledger skeletons. If the Director is interrupted,
   invalidate the run; do not replace it.

3. Confirm the pilot now says `awaiting_episode_documents`. Resume that same
   Director identity to fill only the generated `EPISODE_VISUAL_BIBLE.md` and
   `EPISODE_CONTINUITY_LEDGER.md` skeletons. Wait for normal completion and run
   `mode_p_pilot` again. Do not hand-create or replace either skeleton.

4. Confirm the pilot says `ready_for_scene_design`. Resume that same Director
   identity to write all four scene
   `DIRECTOR_MASTER.md` files. Do not launch a new Director. After normal
   completion, run for scene indices 1 through 4:

~~~powershell
py -m run_mode_p precheck <scene>/DIRECTOR_MASTER.md <scene> --batch 1 --total 1
~~~

   A deterministic precheck failure goes back to the same Director for a
   targeted fix, then reruns precheck for that scene.

5. Launch one fresh `mode-p-dp` only for `dp_adversarial_packet.md`. Wait for
   normal Agent completion, bind it under `adversarial-<n>`, export its exact
   transcript response, and run:

~~~powershell
py -m model_acceptance_guard export-dp-response --run-dir <run-dir> `
  --review-id adversarial-<n> --output <adversarial-response>
py -m dp_adversarial_check <run-dir>/DP_ADVERSARIAL_RESPONSE.md
~~~

6. Only after all scene prechecks and the adversarial gate pass, freeze the
   Bible/Ledger and create the production packet:

~~~powershell
py -m batch_dp prepare 1 <episode>/BATCH_MANIFEST.json <dp-dir> `
  --scene-session 1=<scene-001> --scene-session 2=<scene-002> `
  --scene-session 3=<scene-003> --scene-session 4=<scene-004> `
  --dp-model inherit
~~~

7. Launch one fresh `mode-p-dp` with `DP_PACKET.md`. Its final message must use
   only the packet response contract: on pass, exactly one `READY` line per
   scene, not per Shot; each detail is 18-240 characters, cites a current Shot,
   and names an observable review dimension. No preface, heading, summary, or
   postscript. Wait for normal Agent completion, bind it under
   `production-<n>`, then export the exact transcript response outside
   `<dp-dir>/DP_FEEDBACK.md` and submit that exact file once:

~~~powershell
py -m model_acceptance_guard export-dp-response --run-dir <run-dir> `
  --review-id production-<n> --output <production-response>
py -m batch_dp submit <dp-dir> <production-response> `
  --model-name <bound-model> --model-call-id <bound-call-id>
~~~

   Do not call `run_mode_p submit` for production READY lines. Confirm
   `<dp-dir>/DP_STATE.json` says `committed` before continuing.
   Never edit, shorten, merge, or reformat a DP response. If its exact response
   fails the contract, retain it as evidence and launch a new fresh DP under a
   new `production-<n>` ID.

8. Prepare Episode Review:

~~~powershell
py -m episode_review prepare <episode>/BATCH_MANIFEST.json `
  <episode>/EPISODE_VISUAL_BIBLE.md <episode>/EPISODE_CONTINUITY_LEDGER.md `
  <review-dir> --scene-session 1=<scene-001> --scene-session 2=<scene-002> `
  --scene-session 3=<scene-003> --scene-session 4=<scene-004>
~~~

   Resume the same Director identity only to write the review result. It may
   not edit Bible/Ledger or any committed scene. Submit and deliver:

~~~powershell
py -m episode_review submit <review-dir> <review-result>
py -m episode_delivery assemble <review-dir> <episode> `
  --scene-session 1=<scene-001> --scene-session 2=<scene-002> `
  --scene-session 3=<scene-003> --scene-session 4=<scene-004>
~~~

9. Write the required run evidence and semantic reviews, refresh the root
   state with `mode_p_pilot`, then call guard `complete` as specified in Finish.

## DP loop

Use official runtime commands for compile, derive, precheck, batch DP, final
check, commit, Episode Review, and delivery. Do not hand-advance RUN_STATE.
The production response must be submitted once through `batch_dp submit` for
the whole packet; never route its READY lines by calling `run_mode_p submit`
scene by scene.

Complete `EPISODE_VISUAL_BIBLE.md` and `EPISODE_CONTINUITY_LEDGER.md` before
creating the production DP packet. After the packet exists, both documents are
hash-bound and immutable for that review. If either must change, invalidate the
run; do not patch it after DP and continue to Episode Review.

Every review is a newly launched mode-p-dp Agent. Its assignment must include the
fixed input and run directory so provenance is bound. After the Agent returns,
save its final text verbatim and bind it before validating or submitting that
exact response:

~~~powershell
python -m model_acceptance_guard bind-dp --run-dir <run-dir> --review-id <round-id> --agent-id <internal-agent-id>
~~~

Route valid cited issues to the same persistent Director. Never resume a DP.
The guard hashes the DP Agent final text from the Claude transcript; a parent
task rewrite cannot be submitted as acceptance evidence.

Before the production DP, launch a separate fresh DP for the fixed
`dp_adversarial_packet.md`, bind it under a unique adversarial review ID, and
run `python -m dp_adversarial_check <response>`. It must identify all five
required categories. This acceptance-only call must never enter production
delivery, cache, or knowledge/experience promotion.

## Finish

Persist all evidence required by MODEL_ACCEPTANCE_PROTOCOL.md and verify both
delivery hashes. Keep the guard-created `provenance/` snapshots inside the run;
an external transcript path alone is not portable evidence. Then run exactly:

~~~powershell
python -m mode_p_pilot <fixed-input> --session-dir <run-dir>/episode
python -m model_acceptance_guard complete --run-dir <run-dir>
~~~

The first command refreshes the episode root state from official scene, review,
and delivery evidence. Only the second command may write
`MODEL_ACCEPTANCE_PASSED`; never edit `ACCEPTANCE_BOOTSTRAP.json` or
`MODEL_ACCEPTANCE_STATUS.md` directly. If it fails, do not claim success.
Preserve the run as invalid or blocked with the exact reason. Do not expose
internal Agent IDs in the user-facing response.
