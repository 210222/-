# MODE:P v4.0 - Minimal-Context Director/DP Runtime

## User entry

The normal user command is:

```text
/mode-p-pilot <episode-script-path>
```

`/mode-p` is only a compatibility alias. The supplied file is the independently
uploaded current episode and is always the episode narrative authority. The user
does not provide project flags, scene ranges, session paths, Agent names, or
local commands.

When the user separately identifies a complete script as project background,
register it with the deterministic project-context tool. A later episode need
not be a substring of that background. One active project binds automatically;
no project runs standalone. Current-episode facts override conflicting project
background.

## Runtime roles

- The current Claude Code task is the orchestrator and must not author or repair
  creative Director files.
- One persistent `mode-p-director` subagent owns the entire episode and
  follows `02_Agent/director_agent.md`.
- Every review uses a new `mode-p-dp` subagent following
  `02_Agent/dp_agent.md`.
- Local programs handle deterministic state, retrieval, compilation, checks,
  caching, recovery, telemetry, and atomic commits. They never choose shots or
  aesthetics.

Never spawn one Director per scene or per batch. Every batch, revision, and
Episode Review resumes that same Director, while every DP is fresh. Production
inherits the model selected for the parent task and records every Agent tool's
actual `resolvedModel`; it enforces a model match only when the user explicitly
requires one for that run. Fixed `/mode-p-accept` alone requires
`deepseek-v4-pro`. If persistent Director resume is unavailable, stop as a
runtime blocker instead of making the orchestrator take over creative work.

## Canonical flow

```text
BOOTSTRAP -> SCRIPT_PARSE -> DIRECTOR_BATCH
          -> MASTER_COMPILE -> VIEW_DERIVE -> STRUCTURAL_PRECHECK
          -> FRESH_DP_BATCH -> DIRECTOR_REVISE (when needed)
          -> FINAL_HASH_CHECK -> ATOMIC_BATCH_COMMIT
          -> EPISODE_REVIEW -> ATOMIC_DELIVERY
```

Master is the sole design source. Director writes Master; local code derives
Profile-adaptive Storyboard and Video Prompt views plus the mechanical Manifest.
Each Shot has one visual timeline; Video projects all nodes and Storyboard only
the `[SB]` nodes. N Shots share exactly N+1 Boundary blocks.
Every Shot is independent and at most 15 seconds. Final delivery contains only
`STORYBOARD.md` and `VIDEO_PROMPT.md`.

Director and DP never read media binaries. Verified text asset cards are bound
to media hashes in `ASSET_CARD_INDEX.json`; no card means normal `text_only`
design, not a blocker. Director sees only relevant cards, Core, selected
capsules/experiences, episode evidence, continuity and the compact runtime
contract. DP sees only clean episode evidence, the two views, used capabilities
and used verified card evidence.

## Active sources

- `MODE_P_REDESIGN_PROJECT/LOOP_SPEC.md`: runtime authority.
- `.claude/commands/mode-p-pilot.md`: Claude Code execution contract.
- `.claude/agents/mode-p-director.md`, `.claude/agents/mode-p-dp.md`: valid
  custom-agent definitions with required frontmatter.
- `02_Agent/director_agent.md`, `02_Agent/dp_agent.md`: canonical role detail.
- `01_调度器/mode_p/`: deterministic runtime.
- `01_调度器/mode_p/knowledge/core/`: four fixed Core documents.
- `01_调度器/mode_p/knowledge/capsules/`: selectively loaded knowledge.
- `ASSET_INDEX.json`, `ASSET_CARD_INDEX.json`, and the current SD2.0 capability
  profile: local reference and platform evidence.

Never use `legacy_mode_p/`, old output reports, Seko packaging, specialist
design Agent chains, YAML Agent protocols, rule-ID audits, TIME_SKELETON, PLAN,
Gate reports, or fixed revision-round limits as active MODE:P behavior.

## Implementation work

### vNext architecture-v2.2 release gate

vNext engineering is governed only by the architecture-v2.2 ReleaseLedger:

- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0.md`
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.1_AMENDMENT.md`
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.2_AMENDMENT.md`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_TASKS.json`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_STATE.json`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_CONSTRUCTION_V2.md`
- `.claude/commands/mode-p-vnext-rebuild.md`

For `/mode-p-vnext-rebuild`, run `python -m mode_p_vnext.release_control
audit/status/next/claim/complete/fail/recover/invalidate` from `01_调度器`.
The model must not directly edit machine state, exclusive locks, completion
lists, release gates, or task checkboxes. R, DDO, CPL, and V0-V10 controllers
are historical/read-only task sources after the sole ledger exists. A10 media
acceptance and owner approval are separate hash-bound gates; the model must
never record owner approval for the user. Until a separately authorized
production-switch task succeeds, v4 remains the sole production path.

The following legacy instructions apply only `/mode-p-rebuild`, never
`/mode-p-vnext-rebuild`: obey `MODE_P_REDESIGN_PROJECT/IMPLEMENTATION_PLAN.md` and
`PROGRESS.md`, using `MODE_P_REDESIGN_PROJECT/CLAUDE_CODE_REBUILD_LOOP.md` as
the Claude Code rebuild protocol. A checked item requires executable evidence,
focused tests, and relevant regression tests. Documentation or placeholder tests
alone are not completion evidence. If `MODE_P_REDESIGN_PROJECT/SUPERVISION.lock`
exists, read it: continue only when it is explicitly released or its release
condition is already met; stop when another active supervisor owns edits.

`/mode-p-rebuild` is deterministic and never starts creative Agents. Fixed
real-model acceptance is a separate, explicit `/mode-p-accept <new-run-id>`
command and must never be scheduled by `/loop`.
