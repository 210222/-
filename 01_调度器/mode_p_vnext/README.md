# MODE:P vNext — Isolated Rewrite Workspace

This directory is reserved for the MODE:P vNext implementation governed by:

- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_LOOP_SPEC.md`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD_LOOP.md`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md`
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md`

Current state: isolated rebuild infrastructure. No vNext production runtime,
production entry switch, external generation submission, or visual-media
acceptance authority exists yet. v4 remains the sole production entry.

## Isolation rules

- Do not import modules from `01_调度器/mode_p` or `01_调度器/legacy_mode_p`.
- Do not read v4 knowledge indexes, caches, Sessions or delivery as runtime input.
- v4 may be exercised only through black-box regression commands recorded by the plan.
- Do not copy old compiler behavior as a hidden fallback.
- Golden source media remains external evidence; text runtime code does not load media binaries.
- All implementation work enters through `/mode-p-vnext-rebuild` one task at a time.
- Rebuild is fail-closed: it cannot enable Shadow, Pilot, Canary, or
  Production. It also cannot clear a kill switch or submit to an external
  generation platform.
- `rollback.py` is a vNext-only, tested control-plane drill. It binds a
  pre-existing read-only v4 rollback archive to retained vNext evidence; it
  does not change the real `/mode-p-pilot` entry, a v4 Session, or a delivery.
- The operations runbook is
  `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_OPERATIONS.md`.

A future release may be designed only after the rebuild queue, Golden and
recovery gates, real-media acceptance, and explicit user approval have all
completed. That future release must be a separately scoped, audited change;
it must not reuse a Rebuild flag as an activation shortcut.
