<!-- MODE_P_VNEXT_AUTHORITY: architecture-v3.1 -->

# MODE:P vNext Architecture v3.1 construction protocol

> Active authority: `vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.1.md`.
>
> Sole controller: `python -m mode_p_vnext.release_control`.
>
> Production boundary: `production_entry=v4_unchanged`; `production_switch_authorized=false`; A0–A10 never authorize a production switch.

## 1. Authority and fail-closed rule

Construction follows only the v3.1 architecture SHA locked by `MODE_P_VNEXT_RELEASE_TASKS.json`, the active ReleaseLedger state, and this protocol. v3.0, v2.x, R, DDO, CPL, V0–V10, `director_vnext1`, old tests, prompt content, and existing implementation are historical or lower-level evidence. They cannot explain away a v3.1 requirement.

If architecture, plan, code, tests, Evidence, or active guidance disagree, record the conflict, fail-close the affected package, invalidate dependent completion where required, and repair the authoritative control plane before resuming. Never silently choose an old branch of a contradiction. A new architecture requires one complete successor, conflict Evidence, frozen SHA, active-guidance convergence, registry update, and ReleaseLedger rebase.

## 2. Continuous one-package execution loop

Run from `01_调度器`:

```text
python -m mode_p_vnext.release_control audit
python -m mode_p_vnext.release_control status
python -m mode_p_vnext.release_control next
```

Only proceed when `audit.ok=true`. Claim exactly the one returned A-task with a unique owner ID. Before changing behavior, read its architecture references, dependencies, allowed paths, required checks, registered verification, and current Evidence. Do not edit state, locks, completed lists, release gates, or task status directly.

For the claimed package:

1. Establish a reproducible failure or mechanical observation and map requirements, ownership, dependencies, failure modes, adversarial cases, and Evidence.
2. Implement the smallest complete change consistent with v3.1 only inside allowed paths.
3. Run every registered verification command and the affected cross-package/invariant regressions.
4. Write Evidence with task ID, all changed paths, required-check mapping, diagnostics, architecture hash, v4 boundary, and claim ceiling.
5. Complete through `release_control complete`; the controller re-runs registered verification and records authoritative hashes/results.
6. Stage only files belonging to that completion, commit, and push.
7. Automatically begin a new `audit -> status -> next` cycle. This is sequential continuation, not permission to claim or edit two packages at once.

## 3. Non-negotiable implementation boundaries

- Director alone creates visual design. Models return only Drafts, typed intents, candidates, and bounded RevisionRequests.
- Local deterministic code owns IDs, hashes, 24000 ticks, timeline placements, N+1 boundaries, typed binding, VEC, ProjectionAST, and delivery views.
- Source span is provenance/order only; never derive time from characters or spans.
- Each CinematicShot is one GenerationUnit and must fit its own capability limit; no Scene/Episode 15-second cap.
- `VEC -> ProjectionAST -> StoryboardProjection + VideoProjection -> Gate 0 -> Fresh DP` is the sole accepted order.
- Gate 0 validates the immutable ProjectionBundle; Gate failure does not call DP. DP returns only READY or a locally validated bounded RevisionRequest and never modifies ProjectionAST.
- `TEXT_VALIDATED` is not media or visual acceptance. A0–A9 do not run external media.
- v4 is read-only for regression/rollback comparison. Do not import v4 runtime behavior into vNext, change production entry, or set the production switch true.
- Never create A10 owner approval for the user.

## 4. Recovery, user-worktree isolation, and Git

User changes present before a claim are user-owned. Do not overwrite, delete, stage, commit, or use them as test fixtures. Use registered repository fixtures or temporary directories, not personal output paths.

For a stale/failed lock, use only `release_control recover`; for evidence drift, use `invalidate`; for a genuine architecture conflict, bind conflict Evidence and use `rebase-architecture`. Rebase keeps invalidated history and must not be simulated by direct JSON edits.

Ordinary test failures, dependency errors, path errors, ledger drift, Git non-fast-forward, merge conflict, or incomplete Evidence are repair work: diagnose, repair, verify, and continue. Ask the user only for an irreversible user-data operation, v4/production switch, paid/public external action, unavailable external credential/media without a local proof alternative, irreducible product-semantic fork, or user-only A10 approval.

## 5. Completion boundary

Each A package needs its own Evidence, controller completion, commit, and successful push. A10 may reach only `PRODUCTION_SWITCH_PROPOSAL_ELIGIBLE`; actual production switching is an independently authorized future project.
