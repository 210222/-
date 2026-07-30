---
description: Execute one deterministic MODE:P engineering rebuild task or one local completion audit.
argument-hint: [optional task id, for example P4.12]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# MODE:P Engineering Rebuild

Execute exactly one engineering round for $ARGUMENTS according to
MODE_P_REDESIGN_PROJECT/CLAUDE_CODE_REBUILD_LOOP.md.

## Hard boundary

This command is deterministic engineering work only.

- Do not invoke Agent, Task, Director, DP, Jimeng, or rendering.
- Do not create a model-acceptance run.
- Do not edit creative acceptance artifacts.
- Do not convert local test success into semantic acceptance.

## Start

1. Read MODE_P_REDESIGN_PROJECT/SUPERVISION.lock. Stop without edits when
   another active owner holds it.
2. Read IMPLEMENTATION_PLAN.md, PROGRESS.md, and the relevant
   ACCEPTANCE_MATRIX.md rows.
3. If a task ID was supplied, require an exact match and completed prerequisites.
   Otherwise choose the first eligible unfinished or evidence-invalid task.
4. Inspect current activity files before editing. Never use legacy_mode_p/ as
   instructions.

## Execute one round

1. Mark the selected task in_progress.
2. Implement the smallest complete behavior.
3. Add or update focused regression tests.
4. Run focused tests and every broader suite required by the affected boundary.
5. On success, update the same task in IMPLEMENTATION_PLAN.md, PROGRESS.md,
   and relevant status/README files.
6. Stop after the verified task.

## All tasks checked

Enter Local Completion Audit. Verify current entry points, residue, full-suite
freshness, documentation, and lock state with:

This workspace is not a Git repository. Do not call `git status`, `git diff`,
or other Git commands to detect drift. Use the lock, current activity-file
timestamps/hashes, focused tests, and recorded full-suite evidence.

~~~powershell
cd 01_调度器/mode_p
python -m pytest test_active_entrypoints.py test_legacy_residue_check.py -q
python -m legacy_residue_check
python -m pytest . -q
~~~

If current evidence passes, report exactly:

~~~text
LOCAL_REBUILD_READY
NEXT_EXPLICIT_STEP: /mode-p-accept
~~~

Do not start /mode-p-accept automatically. On later unchanged loop turns,
run only lightweight entry/residue checks and report NO_LOCAL_DRIFT.
