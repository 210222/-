---
description: Execute exactly one isolated MODE:P vNext engineering task from the architecture-v2.2 ReleaseLedger; never switch production.
argument-hint: [optional exact next A-task id]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# MODE:P vNext Architecture-v2.2 Construction

Execute exactly one engineering round for `$ARGUMENTS` according to:

`MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_CONSTRUCTION_V2.md`

The sole task registry is
`MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_TASKS.json`. The sole state is
`MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_RELEASE_STATE.json`. R, DDO, CPL, and V0-V10 files are historical evidence only and cannot select or complete work.

## Hard boundary

- Implement only the one A0-A10 task returned by `release_control next`.
- Modify only that task's `allowed_paths`.
- Do not invoke creative models or media tools unless the selected task
  explicitly registers that isolated verification and the user has authorized
  its external effect.
- Do not run `/mode-p-pilot`, `/mode-p-accept`, or change the active entry.
- Do not import v4 modules, knowledge indexes, caches, Sessions, delivery or fallback behavior into vNext.
- Treat v4 only as a read-only black-box regression and rollback baseline.
- Do not replace the active `mode_p` package or `/mode-p-pilot` entry.
- Text validation never authorizes media acceptance.
- Never call `record-owner-approval` for the user.
- A green A-task never authorizes production.

## Start — the sole ReleaseLedger is mandatory

1. From `01_调度器`, run `python -m mode_p_vnext.release_control audit`.
   Stop without edits if it fails.
2. Run `python -m mode_p_vnext.release_control status` and
   `python -m mode_p_vnext.release_control next`.
3. `$ARGUMENTS`, when present, must equal the exact returned A-task. Reject R,
   DDO, CPL, and V task IDs.
4. Create one unique run ID for this invocation.
5. Claim through
   `python -m mode_p_vnext.release_control claim <task_id> --owner <run-id>`
   and retain the returned token.
6. Read only that task's `spec_refs`, direct dependencies and allowed paths.
7. Never directly edit state, lock, completion lists, or legacy queue status.

## Execute one round

1. A successful ReleaseControl claim is the only valid `IN_PROGRESS` transition.
2. Inspect current vNext files and relevant black-box contracts.
3. Add a failing focused test or a mechanically verifiable fixture.
4. Implement the smallest complete behavior only inside the claimed task's `allowed_paths`.
5. Run every `required_check` plus declared regression while developing.
6. Write one `A<id>_*.json` Evidence under
   `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/`, containing task_id,
   changed_paths, and named check results.
7. Complete only through `release_control complete ... --evidence ...`. It
   validates scope and dependencies, executes immutable registry commands, and
   records Evidence, artifact, and locked-input hashes.
8. If work fails, write failure evidence and call `release_control fail`.
9. Stop after this one task.

## Recovery

If state and lock disagree, run `release_control audit` and stop. Recover only
through `release_control recover`; without `--force` it refuses a live owner
PID. Reopen drifted completed work only through `release_control invalidate`.
Never skip a dependency or revive an old queue to avoid a failing A-task.

## Completion

For one completed task, report its Evidence and next A-task with
`PRODUCTION_ENTRY: v4_unchanged`. Even after A10, report exactly:

~~~text
ARCHITECTURE_V2_IMPLEMENTED
PRODUCTION_SWITCH: NOT_PERFORMED
NEXT_EXPLICIT_STEP: separate production-switch proposal
~~~

Do not start Shadow, media generation, or production switching automatically.
