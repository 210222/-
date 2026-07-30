---
description: Execute exactly one isolated MODE:P vNext engineering task; never run creative agents or switch production.
argument-hint: [optional exact next repair task id]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# MODE:P vNext Engineering Rebuild

Execute exactly one engineering round for `$ARGUMENTS` according to:

`MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD_LOOP.md`

Current mandatory gate: if `MODE_P_VNEXT_REBUILD_STATE.json` says
`REPAIR_REQUIRED`, execute only `MODE_P_VNEXT_LOOP_REPAIR_PLAN.md` and
`MODE_P_VNEXT_REPAIR_TASKS.json`. Do not select any V0-V10 task.

## Hard boundary

- This command implements vNext code, tests and evidence only.
- Implementation code is confined to claimed paths under `01_调度器/mode_p_vnext/` plus explicitly listed repair-control documents.
- Do not invoke Agent, Task, Director, DP, image generation, video generation or model acceptance.
- Do not run `/mode-p-pilot`, `/mode-p-accept` or external render tools.
- Do not import v4 modules, knowledge indexes, caches, Sessions, delivery or fallback behavior into vNext.
- Treat v4 only as a read-only black-box regression and rollback baseline.
- Do not modify `01_调度器/legacy_mode_p/`, existing Sessions, delivery or Golden source media.
- Do not replace the active `mode_p` package or `/mode-p-pilot` entry.
- A local green build never authorizes Shadow, Pilot, Canary or Production.

## Start — deterministic control is mandatory

1. From `01_调度器`, run `python -m mode_p_vnext.rebuild_control audit`. Stop without edits if it fails.
2. Run `python -m mode_p_vnext.rebuild_control status` and `python -m mode_p_vnext.rebuild_control next`.
3. When repair state is active, `$ARGUMENTS` may only name the exact next eligible R task. Reject V task IDs.
4. Create one unique run ID for this invocation.
5. Claim through `python -m mode_p_vnext.rebuild_control claim <task_id> --owner <run-id>` and retain the returned token.
6. Read only that task's `spec_refs`, direct dependencies and allowed paths.
7. Never directly edit the machine state JSON, exclusive lock JSON, completion lists or task checkboxes.

## Execute one round

1. The successful control-plane claim is the only valid `IN_PROGRESS` transition.
2. Inspect current vNext files and relevant black-box contracts.
3. Add a failing focused test or a mechanically verifiable fixture.
4. Implement the smallest complete behavior only inside the claimed task's `allowed_paths`.
5. Run every `required_check` plus declared regression while developing.
6. Write one Evidence JSON under `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/` containing task_id, changed_paths and named check results. This is a summary, not authority to advance state.
7. Complete only through `rebuild_control complete ... --evidence ...`. It validates paths, dependencies and owner/token, executes the task registry's immutable `verification_commands`, and records `verification_results`, the Evidence hash and current `artifact_hashes`.
8. If work fails, write failure evidence and call `rebuild_control fail`; never manually release or advance state.
9. Stop after this one task.

## Recovery

If machine state and lock disagree, run `rebuild_control audit` and stop. Recover only through `rebuild_control recover`; without `--force` it refuses to recover a live owner PID. If a completed task's evidence or bound artifact becomes invalid, reopen it only through `rebuild_control invalidate <task_id> --owner <audit-run-id> --reason <reason>`. Never skip to a later task to avoid a failing prerequisite.

## Completion

The repair queue does not authorize Local Completion. When all R tasks pass, the controller changes state to `V_TASK_REVALIDATION_REQUIRED`; only then may the repaired controller migrate and revalidate V0-V10. When the later truthful Local Completion Audit passes, report exactly:

~~~text
LOCAL_VNEXT_READY
NEXT_EXPLICIT_STEP: isolated vnext shadow acceptance
PRODUCTION_ENTRY_UNCHANGED
~~~

Do not start Shadow automatically.
