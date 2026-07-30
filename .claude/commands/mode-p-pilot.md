---
description: Direct one uploaded episode script through a minimal-context Director, fresh DP reviews, and atomic two-file delivery.
argument-hint: <episode-script-path>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P Production Director Loop v4.0

Run the episode script in `$ARGUMENTS` through complete MODE:P delivery. The
user supplies only the current episode script. Do not ask for a project name,
episode ID, scene range, Agent name, or local command.

## Role and model boundary

The current Claude Code task is the orchestrator, never Director or DP.

- Start exactly one persistent `mode-p-director` Agent for the episode.
- Resume that same Agent ID for every scheduled batch, every revision, and
  Episode Review. A batch boundary must never create a second Director.
- Resume that same Director; do not replace it with a new Agent after a batch,
  revision, context compaction, or Episode Review handoff.
- Start one new `mode-p-dp` Agent for every review; never resume a DP.
- Custom Agents inherit the parent-selected model. Record every actual
  `resolvedModel`; enforce a match only when the user explicitly required one.
- Do not create camera, movement, composition, lighting, transition, asset,
  verifier, or packaging Agents.

## Automatic project resolution

1. Resolve the episode path from `$ARGUMENTS`.
2. Run the local project resolver. If exactly one active project exists, bind it
   automatically. If none exists, run standalone. Ask only when multiple
   projects are genuinely ambiguous.
3. Infer the episode ID from an explicit script header, otherwise from the file
   stem. Bind the run to the episode content hash so a changed script becomes a
   new version.
4. The current episode script is the episode narrative authority. Project
   background contributes only non-conflicting context.

When the user separately says that a complete script should become project
background, register it with the deterministic project-context tool. That
natural-language action is not a second user-facing MODE:P command and must not
start an Agent.

## Bootstrap and recovery

1. Read only the operational sections needed from `LOOP_SPEC.md`; never send
   the full Loop spec to a creative Agent.
2. Run Bootstrap and recovery before any model call.
3. Run `mode_p_pilot.py` on the entire current episode. User-facing scene-range
   selection is not part of production v4.0.
4. Read local state files to determine the next stage. Never infer state from
   filenames or chat memory.
5. Use only content/version-bound cache entries.

Follow `PILOT_PREP_STATUS.json` literally during episode preparation:

- `awaiting_script_facts`: launch the persistent Director to fill only the
  generated `SCRIPT_FACTS.md`, then rerun `mode_p_pilot`.
- `awaiting_episode_documents`: resume that same Director to fill only the
  exact generated `EPISODE_VISUAL_BIBLE.md` and
  `EPISODE_CONTINUITY_LEDGER.md` skeletons, then rerun `mode_p_pilot`.
- `ready_for_scene_design`: begin scene Master design with that same Director.

Never ask one call to invent facts, Bible, and Ledger before the deterministic
stage between them has validated facts and generated the next skeletons.

The orchestrator executes local modules from `01_调度器/mode_p`. The normal
sequence uses these concrete commands with state-derived paths; the user never
runs them:

```text
python -m project_context resolve <episode-script-path>
python -m mode_p_pilot <episode-script-path>
python -m director_session bind <episode-session> --agent-id <director-agent-id> --model-name <resolvedModel>
python -m director_session resume <episode-session> --agent-id <same-director-agent-id> --model-name <same-resolvedModel> --event-id <unique-stage-id>
python -m asset_card_registry match <batch-creative-brief> --budget 6000 --output <director-card-packet>
python -m run_mode_p precheck <DIRECTOR_MASTER.md> <scene-session>
python -m batch_dp prepare <batch-index> <BATCH_MANIFEST.json> <dp-review-dir> --scene-session <INDEX=PATH> [...]
python -m batch_dp submit <dp-review-dir> <fresh-dp-feedback> --model-name <resolvedModel> --model-call-id <call-id> --model-elapsed <seconds>
python -m episode_delivery assemble <episode-review-session> <episode-session> --scene-session <INDEX=PATH> [...]
```

When the user identifies a complete script as background, execute
`python -m project_context register <background-script-path>` before the next
episode run. Use `--replace` only after the user explicitly replaces the active
background.

## Strong reasoning model discipline

This contract is sufficient for a reasoning-capable inherited model such as the
user-selected DeepSeek V4 Pro. Do not add generic chain-of-thought requests or
send the whole project for "more context." Give the Director one explicit
creative assignment, authorized paths, output paths, and the current stage.
Require it to deliberate privately, write the complete authorized files, and
return only a short completion note. `effort: max` for Director and
`effort: high` for DP are host hints; correctness must come from the role
contracts and deterministic checks, not from assuming the hint is supported.

## Director packet

Launch the episode Director once, then resume it with a compact assignment for
the current batch or revision containing
only:

- The exact current episode script/excerpts with line numbers.
- Non-conflicting project background and committed continuity snapshot, when
  present.
- Current `PROJECT_VISUAL_BIBLE.md` when bound and
  `EPISODE_VISUAL_BIBLE.md` for this episode.
- Current `PROJECT_CONTINUITY_LEDGER.md` when bound and compact
  `EPISODE_CONTINUITY_LEDGER.md` state.
- Four Core files plus the compact list of candidate capsule filenames. The
  persistent Director chooses and reads 0-3 capsule files for the batch; the
  orchestrator only validates the chosen paths/count/hashes and must not infer
  scene type or choose a capsule through keyword scoring.
- Only the selected 0-3 validated experiences.
- A compact SD2.0 capability brief.
- Only relevant verified text asset-card sections. Never pass media binaries.
- `02_Agent/director_agent.md`,
  `01_调度器/mode_p/director_runtime_contract.md`, and exact Master output
  paths.

Immediately bind the first launch with `director_session bind`. After every
subsequent Agent resume, record the returned same Agent ID with
`director_session resume`. A binding mismatch blocks the run; never hide it by
starting a replacement Director. This check enforces identity continuity only
and does not impose a model-name allowlist.

Do not give the Director `LOOP_SPEC.md`, BATCH_MANIFEST, SCENE_SESSIONS,
Manifest JSON, cache data, telemetry, hashes, tests, runtime source code,
the full knowledge index, unselected capsule contents, unselected asset cards,
or old reports.

The Director owns the complete visual strategy and writes only authorized
Visual Bible, continuity/asset-requirement updates, and `DIRECTOR_MASTER.md`.
It never writes Storyboard, Video Prompt, or Manifest directly.

Without verified assets, the Director designs from the episode script,
non-conflicting project facts, Visual Bible, and knowledge. It uses
`text_only`, records reference assets as none, and may declare future asset
slots. Missing images are not a blocker.

## Compile and Profile derivation

For every Master, use local deterministic programs to:

1. Compile the mechanical Shot Manifest.
2. Derive Storyboard and Video Prompt from the same Master visual timeline:
   Video uses every node and Storyboard uses only Director-tagged `[SB]` nodes.
3. Apply the selected scene-expression Profile to output organization.
4. Apply `event_nodes`, `second_nodes`, or `half_second_nodes` exactly as the
   Director selected.
5. Apply `text_only`, `first_last_frame`, or `omni_reference` presentation
   without inventing design.
6. Check source ranges, IDs, `0 < duration <= 15s`, the single visual timeline,
   shared Boundaries,
   capabilities, asset-card binding, hashes, and prohibited residue.
7. Commit a complete working tree atomically.

A design/semantic structural failure returns to the same Director. A purely
mechanical failure is repaired locally without changing creative content.

## Fresh DP loop

Prepare one DP review for the current batch. On a cache miss, launch exactly one
new `mode-p-dp` Agent with only the model-visible paths in `DP_PACKET.md`:

- Relevant episode script excerpts.
- Compact committed continuity.
- Current Storyboard and Video Prompt.
- Compact capabilities actually used.
- Compact verified asset-card evidence actually used.

Do not give DP the Master, Manifest, knowledge files, Agent definitions,
parser/checker source, hashes, cache data, Director reasoning, prior DP feedback,
or media binaries. Runtime provenance may hash those files in JSON but must not
list them in the model-visible Markdown packet.

Record the actual DP model/call metadata on submit. Scene-specific READY evidence
advances. Issues go
only to cited Shots and genuinely affected neighboring boundaries in the same
Director. Re-derive, precheck, and launch a new DP.

There is no fixed round count. Stop only for a real unresolved input, a repeated
identical issue against an unchanged Master, or an explicit runtime blocker.

## Episode review and delivery

After all batches commit, resume the same episode Director with the compact Episode
Review packet. A revision repeats only affected scenes through fresh DP.

Only current Episode Review PASS may atomically deliver:

```text
delivery/STORYBOARD.md
delivery/VIDEO_PROMPT.md
```

Report absolute delivery paths, episode version, processed scene count, actual
Director/DP calls, cache hits, elapsed time, selected Profiles, asset mode
(`text_only` when none), and blockers. Do not deliver internal project memory,
Master, Manifest, asset requirements, DP feedback, telemetry, audit reports,
YAML, PLAN, TIME_SKELETON, Gate output, Seko syntax, or render packaging.
