---
description: Reopen and repair only the R1.1 missing-media semantic evidence defect under a DeepSeek parent and read-only Golden audit.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R1.1 Missing-media Repair

This command repairs a completed R1.1 whose Golden-media test silently
continues when a file is absent. The parent Claude Code session is the only
writer and must be `deepseek-v4-pro`; the Golden expert remains read-only. Do
not start R1.2 in this command.

## Model gate

Use only a parent explicitly selected as `deepseek-v4-pro`. Invoke exactly one
`mode-p-vnext-golden-prompt-auditor` in the foreground before editing and once
after the candidate repair. Verify each Agent result's actual `resolvedModel`
is exactly `deepseek-v4-pro`; otherwise stop without accepting its result.

## Exact write boundary

The parent may semantically edit only:

- `MODE_P_REDESIGN_PROJECT/vnext_baseline/V0.1_FREEZE_MANIFEST.json`
- `01_调度器/mode_p_vnext/tests/test_v0_1_baseline.py`
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.1.json`

Machine state and lock changes are allowed only through
`01_调度器/mode_p_vnext/rebuild_control.py`; never edit them directly.

Everything else is forbidden: R0 artifacts/Evidence, R0.3 ledger, task
registry, control code/tests, R1.2 files, Golden prompt fixtures, source media,
v4, knowledge sources, Sessions, Shadow/Pilot/Canary/Production, external model
or generation calls, and `.claude/settings.local.json`.

## Preflight and controlled reopen

Before mutation:

1. run control `audit`, `status`, and `next`;
2. record every R0.1-R0.3 Evidence and artifact hash;
3. record the current R1.1 Evidence and artifact hashes;
4. run the current R1.1 suite and R0.2 active-entrypoint suite;
5. inspect full workspace status and require `.claude/settings.local.json` to
   be absent;
6. identify the exact `if not fpath.exists(): continue` media bypass.

Proceed only when R1.1 is completed, R1.2 is neither claimed nor completed,
there is no current owner/token, and `next_task` is R1.2. Invalidate exactly
R1.1 through the control plane with a reason naming the silent missing-media
bypass. Confirm R1.1 becomes next, claim exactly R1.1 with a unique owner, and
keep the token private. On failure after claim, use control `fail`; never edit
or manually release the lock.

## Test-first repair contract

Write failing tests before manifest/evidence changes. Implement a deterministic
validator or equivalent behavior that proves:

- `authority_files` contains exactly 13 entries with real matching hashes;
- each Golden media entry has explicit `status` in `available|missing`;
- an `available` entry requires an existing file plus matching SHA-256 and byte
  count; a missing file raises/fails and cannot be skipped;
- a `missing` entry requires `path` and non-empty `missing_reason`, is surfaced
  in a structured validation result, and never masquerades as verified media;
- a temporary nonexistent path marked `available` fails;
- the same controlled fixture marked `missing` produces an explicit missing
  record, not a silent pass;
- all eight current manifest media entries are accounted for exactly once;
- removing status, corrupting a hash, changing bytes, or reintroducing
  `continue` behavior fails the suite.

Do not read or transform image/video/audio content. Existence, file size, and
streamed SHA-256 are sufficient. Do not relocate or modify source media.

Update R1.1 Evidence so `missing_media_not_silent` cites the media behavior
tests and reports available/missing counts. It must not cite authority-file
failure as a substitute. Declare only the three exact write paths.

## Verification and completion

Run:

- the authoritative R1.1 suite from the task registry;
- `mode_p_vnext/tests/test_rebuild_control.py`;
- `mode_p/test_active_entrypoints.py`;
- the read-only Golden expert post-review.

Complete R1.1 only when all suites pass, the expert returns `READY`, and its
actual resolved model is verified. Then require control audit clean,
`completed_tasks` through R1.1, `next_task=R1.2`, no owner/token, unchanged
R0.1-R0.3 hashes, `.claude/settings.local.json` absent, and
`production_entry=v4_unchanged`.

Return exact test/subtest counts, available/missing media counts, final R1.1
Evidence hash, bound artifact hashes, verified Agent model, and remaining
issues. Never output `LOCAL_VNEXT_READY`.
