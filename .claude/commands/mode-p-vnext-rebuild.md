---
description: Sequentially execute the current MODE:P vNext architecture-v3.1 ReleaseLedger package, verify it, commit/push it, then continue with the next single package; never switch production.
argument-hint: [optional exact next A-task id]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

<!-- MODE_P_VNEXT_AUTHORITY: architecture-v3.1 -->

# MODE:P vNext Architecture-v3.1 construction

The sole architecture is
`MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.1.md`.
The sole active construction protocol is
`MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_CONSTRUCTION_V3_1.md`; the sole registry
and state are `MODE_P_VNEXT_RELEASE_TASKS.json` and
`MODE_P_VNEXT_RELEASE_STATE.json`.

v3.0 is superseded by the recorded Projection/Gate-0/DP conflict repair.
v2.0–v2.2, v2.3, R, DDO, CPL, V0–V10, and `director_vnext1` are historical
evidence only; v2.3 is rejected. They cannot select, complete, or reinterpret
v3.1 work.

## Hard boundaries

- Use exactly one returned A0–A10 package at a time; modify only its allowed paths.
- v3.1 outranks the task plan, existing code, tests, prompts, and old Evidence.
  On drift, record evidence, fail-close/invalidate as required, and repair the
  authoritative control plane. Do not choose an old design silently.
- Director is the sole visual designer. Models may emit only Drafts, typed
  intents, candidates, and bounded RevisionRequests. Local code owns IDs,
  hashes, 24000 ticks, Boundary, typed binding, VEC, and ProjectionAST.
- The sole review order is `VEC -> ProjectionAST -> Storyboard/Video -> Gate 0
  -> Fresh DP`. Gate 0 failure never calls DP; DP cannot create or modify a
  ProjectionAST; text never claims visual acceptance.
- Do not invoke external media before A10, alter a v4 entrypoint, import v4
  runtime behavior into vNext, call `/mode-p-pilot` or `/mode-p-accept`, or
  enable a feature/production switch. `production_entry=v4_unchanged` and
  `production_switch_authorized=false` remain true.
- Never call `record-owner-approval` for the user.

## Sequential execution

From `01_调度器`, run:

```text
python -m mode_p_vnext.release_control audit
python -m mode_p_vnext.release_control status
python -m mode_p_vnext.release_control next
```

Proceed only with a clean audit. `$ARGUMENTS`, if supplied, must equal the
returned A-task. Claim it with a unique owner ID, retain its token, inspect its
requirements/ownership/dependencies/failure modes, then establish a focused
failure or mechanical observation before implementation.

```text
python -m mode_p_vnext.release_control claim <task_id> --owner <run-id>
python -m mode_p_vnext.release_control complete <task_id> --owner <run-id> --token <token> --evidence <A-task-evidence.json>
python -m mode_p_vnext.release_control fail <task_id> --owner <run-id> --token <token> --evidence <failure-evidence.json>
python -m mode_p_vnext.release_control recover
python -m mode_p_vnext.release_control invalidate <task_id> --owner <run-id> --reason <reason>
```

Implement the smallest complete v3.1 behavior within the claimed paths. Run all
registered verification and affected cross-package invariants. Write Evidence
with complete changed paths and diagnostics, then use `release_control complete`
so the controller re-runs the registered commands and records hashes. Stage only
the claimed package's files, commit, and push.

After a successful push, automatically repeat `audit -> status -> next` and
continue with the next one package. Sequential continuation does not authorize
claiming or editing two packages together.

## Recovery and user boundary

Use `recover` for stale locks, `invalidate` for drifted completion, and
`rebase-architecture --conflict-evidence ...` only after a complete successor
authority, all affected invalidations, and active-guidance/registry convergence.
Never edit state, locks, completion lists, or release gates directly.

Treat normal failures—tests, dependencies, paths, evidence, Git non-fast-forward
or ordinary conflicts—as self-service diagnosis/repair work. Preserve preexisting
user worktree changes and never stage them. Ask only for an irreversible
user-data action, v4/production switch, paid/public external action, unavailable
external credential/media with no valid local proof, irreducible semantic fork,
or user-only A10 approval.

Even after A10, report only:

```text
ARCHITECTURE_V31_IMPLEMENTED
PRODUCTION_SWITCH: NOT_PERFORMED
NEXT_EXPLICIT_STEP: separately authorized production-switch proposal
```
