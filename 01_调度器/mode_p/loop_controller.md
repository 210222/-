# MODE:P Loop Controller

The controller orchestrates a director conversation. It does not design shots,
interpret the knowledge base, classify scene complexity, write audit reports, or
package a platform request.

## Inputs

- One `Scene Context` document following `scene_context.md`.
- Director kernel, selected scene capsule(s), and SD2.0 capsule.

## Loop

```text
1. Start `02_Agent/director_agent.md` in draft mode with Scene Context and selected knowledge.
2. Save the Director's two final-format documents as the current design.
3. Run `sd2_preflight.py` on VIDEO_PROMPT before spending a DP call.
4. If preflight finds hard errors, send only those errors to Director/fix and return to step 3.
5. Start `02_Agent/dp_agent.md` with Scene Context and the structurally valid design.
6. Only the exact readiness sentence below passes review: `No issues. The scene is spatially workable, visually continuous, and ready for final checks.`
7. If DP identifies design issues, start Director in revise mode, return to step 3, then use a fresh DP.
8. On DP confirmation, run final preflight once more and deliver the two documents.
```

## Revision discipline

- Pass the complete current design, but ask the Director to rewrite only cited shots and
  their directly affected neighbors.
- Do not regenerate a separate PLAN, storyboard skeleton, YAML, audit report, or render package.
- A deterministic preflight issue is a copy edit, not a new DP review unless it changes
  a camera, action, duration, composition, boundary, or reference decision.

## Delivery

```text
STORYBOARD_[script]_[scene].md
VIDEO_PROMPT_[script]_[scene].md
```

No other delivery file is required.

## Optional render feedback

After an actual SD2.0 canvas render, pass observable result notes or frames to the
Director only when there is a real deviation. The Director fixes the affected shot;
the DP is re-engaged only when the fix changes spatial or cinematic design.
