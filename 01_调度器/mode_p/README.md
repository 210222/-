# MODE:P v4.0 Runtime

This directory contains the active deterministic runtime for the Director/DP
MODE:P pipeline. It is not the legacy single-scene controller.

## User Entry

Claude Code users run:

```text
/mode-p-pilot <episode-script-path>
```

The episode file is independently uploaded and outranks optional project
background. Project binding and episode ID are automatic; no project is a valid
standalone mode. The command owns script ingest, episode strategy, Director batch design,
Master compilation, view derivation, structural precheck, fresh DP review,
revision, final hash check, episode review, and atomic delivery.

Users do not run Python scripts, prepare Scene Context files, choose subagents,
or forward DP feedback.

## Runtime Roles

- **Orchestrator**: the current Claude Code task. It runs deterministic state
  and Agent routing but never authors creative files.
- **Director**: one persistent `mode-p-director` Agent per episode. It is
  resumed across every batch, revision, and Episode Review. It
  writes `DIRECTOR_MASTER.md` and owns camera, movement, composition,
  lighting, performance, transition, and reference-mode decisions.
- **DP**: a fresh `mode-p-dp` subagent for every review round. It checks
  observable spatial, continuity, cinematic, and SD2.0 execution risks.
- **Local runtime**: Python modules in this directory handle parsing, caching,
  hashing, compiling, deriving, prechecking, locking, telemetry, recovery, and
  atomic commits. They do not make creative design choices.

Production inherits the parent Claude Code task's selected model and records
every Agent tool's actual `resolvedModel`. It enforces a model match only when
the user explicitly requires one for that run. The separate fixed semantic
acceptance command `/mode-p-accept` requires `deepseek-v4-pro`.

## Canonical Flow

```text
BOOTSTRAP
  -> SCRIPT_PARSE
  -> DIRECTOR_BATCH
  -> MASTER_COMPILE
  -> VIEW_DERIVE
  -> STRUCTURAL_PRECHECK
  -> FRESH_DP_BATCH
  -> DIRECTOR_REVISE when needed
  -> FINAL_HASH_CHECK
  -> ATOMIC_BATCH_COMMIT
  -> EPISODE_REVIEW
  -> ATOMIC_DELIVERY
```

`DIRECTOR_MASTER.md` is the only design source. `SHOT_MANIFEST.json` is a
mechanical projection. `STORYBOARD.md` and `VIDEO_PROMPT.md` are derived views.

Final delivery contains only:

```text
delivery/STORYBOARD.md
delivery/VIDEO_PROMPT.md
```

## Important Modules

| Module | Purpose |
|---|---|
| `mode_p_pilot.py` | Independent-episode preparation and automatic project binding |
| `project_context.py` | Optional background registration and episode version binding |
| `asset_card_registry.py` | Text-only verified media evidence and context budgets |
| `batch_state_machine.py` | Batch stage progression and recovery |
| `director_session.py` | Episode-level Director identity/model binding |
| `session_lock.py` | Session lock, staging, commit, and recovery safety |
| `bootstrap_loader.py` | Local metadata preload without LLM calls |
| `context_retriever.py` | Core + 1-3 capsules + 0-3 validated experiences |
| `master_compiler.py` | Master to mechanical Shot Manifest |
| `view_deriver.py` | Master to Profile-adaptive Storyboard and Video Prompt |
| `structural_precheck.py` | DP-before deterministic checks, including full prompt preflight |
| `batch_dp.py` | Batch DP packet, response validation, final READY binding |
| `episode_review.py` | Minimal whole-episode review packet and result routing |
| `episode_delivery.py` | Atomic final two-file delivery |
| `render_evidence.py` | External real-render evidence and promotion safety |
| `knowledge_curator.py` | Non-runtime learning from external Jimeng results |
| `benchmark_harness.py` | Structural regression and real model-run evidence policy |
| `legacy_residue_check.py` | Active-entry residue scanner |

## Hard Invariants

- Runtime creative roles are only Director and fresh DP.
- Storyboard and Video Prompt must come from the same Master.
- Each Shot has one visual timeline: Video uses every node and Storyboard uses
  only Director-tagged `[SB]` nodes.
- N Shots have exactly N+1 shared Boundaries; a continuous handoff is authored
  once, not duplicated as two per-Shot states.
- Every Shot is an independent SD2.0 generation unit with `0 < duration <= 15s`.
- Every Shot declares one generation mode: pure prompt, first/last frames, or
  omni reference.
- No media binary enters a Director or DP context. Missing assets select
  `text_only`; referenced assets require current verified text cards.
- Reference assets must have stable asset IDs and explicit responsibilities.
- The same episode Director identity is required across batches and revisions.
- Final outputs must not contain Seko packaging, YAML agent protocol,
  TIME_SKELETON, Gate reports, PLAN files, old specialist agents, or rule-ID
  proof chains.

## Learning Boundary

MODE:P does not render. Phase 5 learning uses only external Jimeng SD2.0 render
results plus human observations. `validated` experience requires real render
cases, linked observations, at least two different scene IDs, human approval,
and a passed regression command.

## Verification

From the repository root, install the declared runtime and test dependencies
once after cloning or moving the project to another computer:

```powershell
python -m pip install -r requirements.txt
```

Then change to `01_调度器/mode_p` before running the commands below.

Focused examples:

```powershell
python -m pytest test_full_pilot_loop.py test_batch_dp.py -q
python -m pytest test_render_evidence.py test_knowledge_curator.py -q
python -m legacy_residue_check
```

Full suite:

```powershell
python -m pytest . -q
```

Current verified result:

```text
686 tests passed (`python -m unittest discover -q`, 2026-07-22; includes the vNext rebuild-entry isolation test)
```
