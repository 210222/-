# Invalid MODE:P Acceptance Run

invalidated_at: 2026-07-17T02:52:12.818046+00:00
run_id: run-004
reason: Director provenance binding failed because Claude resolvedModel was deepseek-v4-pro[1m] while the guard required exact deepseek-v4-pro. Parent Claude Code then violated the immutable-implementation boundary by editing model_acceptance_guard.py during the run. The run is invalid and its Director evidence must not be promoted.

This run is retained for diagnosis only. Its Director output, precheck, DP review, Episode Review, and delivery must not be promoted as acceptance evidence.
