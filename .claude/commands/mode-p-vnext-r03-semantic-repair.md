---
description: Reopen and repair only the R0.3 semantic evidence defect under the DeepSeek parent and read-only expert audit.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R0.3 Semantic Repair

This is a one-task corrective command. The parent Claude Code session is the
only writer and must be `deepseek-v4-pro`. The routed Agent remains read-only.
Do not continue to R1.1 in this command.

## Non-negotiable model gate

Before mutation, report the parent model. Use only a parent session explicitly
selected as `deepseek-v4-pro`. Invoke only
`mode-p-vnext-control-evidence-auditor`, in the foreground, and verify the Agent
result's actual `resolvedModel` is exactly `deepseek-v4-pro`. If either model
gate fails, stop without mutation and return `EXPERT_MODEL_MISMATCH`.

## Exact write boundary

The parent may semantically edit only:

- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R0.3_reconciliation_ledger.json`
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R0.3.json`
- `01_调度器/mode_p_vnext/tests/test_r0_3_reconciliation.py`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md`

The following control artifacts may change only through
`01_调度器/mode_p_vnext/rebuild_control.py`; never edit them directly:

- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD_STATE.json`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock`

Everything else is forbidden, including R0.1/R0.2 Evidence, the task registry,
the control program and its tests, `.claude/commands/mode-p-vnext-rebuild.md`,
R1.1 artifacts, v4, Sessions, knowledge sources, media, feature gates, Shadow,
Pilot, Canary, Production, and external model/generation calls.

## Preflight before invalidation

Read and record:

1. `rebuild_control audit`, `status`, and `next`;
2. R0.1 and R0.2 Evidence SHA-256 values and every bound artifact hash;
3. full workspace `git status --short`, plus an explicit existence check for
   `.claude/settings.local.json`;
4. the current R0.3 Evidence, ledger, test, and Progress contradictions.

Proceed only when audit is clean, R0.3 is completed, R1.1 has not been claimed
or completed, there is no current owner/token, `next_task` is R1.1, and the four
write paths have no unknown user edits. `.claude/settings.local.json` must be
absent because the sealed R0.2 regression rejects project-local machine
permissions; if permissions are needed, configure them outside the project
workspace. Otherwise stop with
`R03_REPAIR_PRECONDITION_BLOCKED` and do not invalidate.

## Controlled reopen

Use `rebuild_control invalidate R0.3` with a unique DeepSeek repair owner and a
reason that names the semantic evidence inconsistency. Immediately confirm that
R0.3 is again the legal next task. Claim exactly R0.3 through the control plane,
capture its owner token privately, and never expose the token in user-facing
output or give it to the Agent.

On any failure after claim, use `rebuild_control fail` with the same owner/token
and an Evidence file describing the failure. Do not manually release or edit
the lock. Do not claim R1.1.

## Read-only expert packet

Invoke exactly one `mode-p-vnext-control-evidence-auditor` after claim and again
after the candidate repair. Give it only R0.3 spec refs, the four semantic
paths, read-only state/task paths, the R0.1/R0.2 hash snapshot, and the mandatory
checks below. The Agent cannot write, run tests, own the token, or complete the
task. Treat `READY` as advisory.

## Mandatory repair invariants

Implement tests before changing evidence data. The tests must fail on the old
defect and then prove:

- exactly 70 rows and 70 unique IDs;
- exactly one leaf classification per row;
- aggregate classification lists are pairwise disjoint and partition all 70
  rows;
- aggregate counts are recomputed from rows and equal `11/44/6/8/1` for
  `PROGRESS_DOCUMENTED/IMPLEMENTED_UNVERIFIED/IMPLEMENTED_UNVERIFIED_INVALID_DEPS/NOT_STARTED/HISTORICALLY_PREMATURE_THEN_REVERTED`;
- invalid dependency IDs are exactly
  `V9.2,V9.3,V9.4,V10.1,V10.2,V10.3`;
- R0.3 Evidence check text and ledger summary match recomputed values;
- no count can pass by double-counting one set while omitting another;
- Progress contains no live current-task/owner/unique-legal-task duplicate that
  can drift from machine state; it points readers to `rebuild_control status`
  and `next` as the authority;
- `changed_paths` declares the ledger, test, and Progress view actually changed;
  `produced_artifacts` accurately describes outputs without claiming a circular
  self-hash for R0.3 Evidence;
- after completion, immutable changed paths are in control
  `artifact_hashes`, R0.3 Evidence is bound by the record-level Evidence hash,
  and Progress is explicitly described as a mutable, non-hash-bound control
  view under rebuild_control's `_MUTABLE_CONTROL_PATHS` policy;
- tampering any aggregate count, task ID list, Evidence count, or forbidden
  stale Progress statement makes the suite fail.

Do not weaken an assertion to fit existing data. Do not hand-author a second
count source when it can be computed from the task rows.

## Verification and completion

Run the authoritative R0.3 verification command from the task registry. Also
run `mode_p_vnext/tests/test_rebuild_control.py` and
`mode_p/test_active_entrypoints.py`; the latter must not be bypassed or reduced
to stored hashes. Then run the read-only expert post-review. Complete R0.3
through `rebuild_control` only when every suite passes, the expert returns
`READY`, and its actual resolved model is verified.

After completion, run `audit`, `status`, and `next`, then compare R0.1/R0.2
Evidence and artifact hashes with the preflight snapshot. Success requires:

- `completed_tasks` contains R0.1, R0.2, R0.3;
- `next_task` is R1.1 and no task is claimed;
- R0.1/R0.2 hashes are byte-for-byte unchanged;
- R0.3 artifact hashes bind the repaired ledger and test, its record-level hash
  binds Evidence, and the report truthfully marks Progress as mutable and not
  hash-bound;
- `.claude/settings.local.json` remains absent and the R0.2 active-entrypoint
  suite is green;
- production entry remains `v4_unchanged`;
- no file outside the exact write boundary changed because of this command.

Return a concise repair report with the exact tests, final R0.3 Evidence hash,
bound artifact hashes, verified Agent resolved model, and any remaining issue.
Never output `LOCAL_VNEXT_READY`.
