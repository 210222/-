---
description: Run exactly one read-only DeepSeek vNext expert review without modifying files or advancing rebuild state.
argument-hint: <exact-current-R-task-id> [optional focused question]
allowed-tools: Read, Glob, Grep, Agent
---

# MODE:P vNext Read-only Expert Review

This command is advisory only. It must not claim, implement, test, write
Evidence, edit state, release locks, or call `rebuild_control complete`.

## Model gate

The parent Claude Code session must be `deepseek-v4-pro`. Every custom expert
uses `model: inherit`. After the Agent returns, verify the Agent tool's actual
`resolvedModel`; accept the review only when it is exactly
`deepseek-v4-pro`. Otherwise discard it and return:

```text
EXPERT_MODEL_MISMATCH
EXPECTED: deepseek-v4-pro
```

## Current-task gate

Read `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD_STATE.json` and
`MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REPAIR_TASKS.json`. `$ARGUMENTS` must
name either the machine state's `current_task` when status is `IN_PROGRESS`, or
its `next_task` otherwise. Reject any other task, V task, completed task, or
production operation.

## Expert routing

- R0.1, R0.2, R0.3 -> `mode-p-vnext-control-evidence-auditor`
- R1.1, R1.2, R1.3, R1.4 -> `mode-p-vnext-golden-prompt-auditor`
- R2.1, R2.2 -> `mode-p-vnext-runtime-systems-auditor`
- R2.3, R2.4 -> `mode-p-vnext-knowledge-safety-auditor`
- R3.1, R3.2 -> `mode-p-vnext-release-auditor`

Launch exactly one routed expert in the foreground. Never launch a creative
Director/DP, general-purpose helper, second reviewer, or background writer.

## Task packet

Give the expert only:

- exact task_id and title;
- task `spec_refs`, `required_checks`, and `verification_commands`;
- an explicit `allowed_read_paths` list limited to the task, direct dependency
  Evidence, and necessary cited specification sections;
- the focused question from `$ARGUMENTS`, if present;
- the expert's required output schema.

Do not give it the full LOOP, full knowledge library, unrelated tests, v4 source,
Sessions, media binaries, hidden reasoning, control token, or write paths merely
because they exist. Do not expose internal Agent IDs in the user-facing result.

Return the expert's structured review plus the verified resolved model. The
parent may later use `/mode-p-vnext-rebuild <task_id>` to implement findings,
but this review command never changes machine state.
