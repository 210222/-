---
description: Execute exactly one isolated MODE:P vNext engineering task from the architecture-v3.0 ReleaseLedger; never switch production.
argument-hint: [optional exact next A-task id]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

<!-- MODE_P_VNEXT_AUTHORITY: architecture-v3.0 -->

# MODE:P vNext Architecture-v3.0 Construction

Execute exactly one engineering round for `$ARGUMENTS` according to
`MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_CONSTRUCTION_V3.md`.

The sole architecture is
`MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0.md`.
The sole task registry and state are `MODE_P_VNEXT_RELEASE_TASKS.json` and
`MODE_P_VNEXT_RELEASE_STATE.json`. v2.0-v2.3 architecture documents and R,
DDO, CPL, V0-V10 queues are historical evidence only; v2.3 is rejected and
cannot select or complete work.

## Hard boundary

- Implement only the one A0-A10 task returned by `release_control next`.
- Modify only that task's `allowed_paths`; do not enter a second task.
- Architecture v3.0 outranks the construction plan and current code. On a gap,
  write failure evidence and fail the current task; never choose an old design.
- Models may make creative Draft choices but must not mint IDs, hashes, ticks,
  boundaries or machine bindings. Local code owns deterministic assembly.
- Do not invoke creative models or media tools unless the selected task
  explicitly registers that effect. A0-A7 cannot start external media.
- Do not run `/mode-p-pilot`, `/mode-p-accept`, or alter the active entry.
- Do not import v4 runtime modules, knowledge indexes, caches, Sessions,
  delivery or fallback behavior into vNext.
- Treat v4 only as a read-only black-box regression and rollback baseline.
- Text validation never authorizes media acceptance.
- Never call `record-owner-approval` for the user.
- A green A-task never authorizes production; `production_entry` remains
  `v4_unchanged` and `production_switch_authorized` remains false.

## Start — the sole ReleaseLedger is mandatory

1. From `01_调度器`, run `python -m mode_p_vnext.release_control audit`.
   Stop without implementation edits if it fails.
2. Run `python -m mode_p_vnext.release_control status` and
   `python -m mode_p_vnext.release_control next`.
3. `$ARGUMENTS`, when present, must equal the exact returned A-task. Reject all
   R, DDO, CPL and V task IDs.
4. Create one unique owner/run ID and claim with
   `release_control claim <task_id> --owner <run-id>`.
5. Retain the token. Read the one v3.0 document, the task's `spec_refs`, direct
   dependencies, `required_checks`, `verification_commands` and `allowed_paths`.
6. Never directly edit state, lock, completion lists, release gates or old
   queue status.

## Execute one round

1. A successful claim is the only valid `IN_PROGRESS` transition.
2. Establish a failing focused test or another mechanically reproducible
   observation before changing behavior.
3. Implement the smallest complete architecture-v3.0 behavior inside the
   claimed task's paths.
4. Run every registered verification command and relevant affected regression.
5. Write one `A<id>_*.json` Evidence containing `task_id`, all `changed_paths`,
   named check results, architecture input hash and diagnostic notes. The
   controller is the authority for `verification_results` and 产物哈希.
6. Complete only through
   `release_control complete ... --evidence ...`; it re-runs immutable
   `verification_commands`, validates scope/dependencies, and records hashes.
7. If architecture or execution fails, write failure evidence and call
   `release_control fail`; do not skip forward.
8. Commit and push only the completed task's exact files, then stop.

## Recovery

If state and lock disagree, run `release_control audit` and stop. Recover only
through `release_control recover`; without `--force` it refuses a live owner
PID. Reopen drifted completion only through `release_control invalidate`.
Architecture changes require all affected completions to be invalidated, the
single new authority document registered and `rebase-architecture` executed
before any new claim.

## Completion

For one completed task, report its Evidence, commit, pushed branch, and the next
A-task with `PRODUCTION_ENTRY: v4_unchanged`. Even after A10 report:

~~~text
ARCHITECTURE_V3_IMPLEMENTED
PRODUCTION_SWITCH: NOT_PERFORMED
NEXT_EXPLICIT_STEP: separate production-switch proposal
~~~

Do not start Shadow, media generation, or production switching automatically.
