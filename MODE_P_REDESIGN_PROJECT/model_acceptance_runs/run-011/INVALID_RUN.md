# Invalid MODE:P Acceptance Run

invalidated_at: 2026-07-18T19:47:02.854141+00:00
run_id: run-011
reason: episode_review prepare rejects all four committed Masters ('Master lacks a scene-level summary'): the Directors Masters omit the template numbered container headings (## 2. 共享 Boundary etc.); master_compiler and the full structural precheck accepted that layout, but the review excerpt extractor requires the ## 1. section to be terminated by a literal ## 2. heading. The scenes are hash-bound at batch_commit; run_mode_p precheck only accepts director_batch/structural_precheck, no CLI reopens a committed 1-batch scene, and the episode-review REVISE reopen path is unreachable because prepare itself fails. Reaching Episode Review would require bypassing the official state machine, so the run cannot complete. Provenance is intact and preserved: Director and all six fresh DPs resolvedModel deepseek-v4-pro; adversarial gate passed on adversarial-4; production DP production-2 READY committed scenes 1-4. Template/precheck section-layout gap is an engineering finding for /mode-p-rebuild, not repairable inside an acceptance run.

This run is retained for diagnosis only. Its Director output, precheck, DP review, Episode Review, and delivery must not be promoted as acceptance evidence.
