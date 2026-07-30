# /mode-p-promote — Human approval for MODE:P experience promotion

Promotes an experience candidate to a higher status in the knowledge
pipeline. This command requires explicit human judgment; it cannot be
automated.

## Usage

```text
/mode-p-promote <candidate-id> repeated
/mode-p-promote <candidate-id> validated --approved-by <name> --regression-command "<command>" --regression-passed
/mode-p-promote <candidate-id> rejected --rejection-reason "<reason>"
/mode-p-promote <candidate-id> candidate
/mode-p-promote rollback <candidate-id>
```

## Status transitions

| From      | To          | Requires                        |
|-----------|-------------|---------------------------------|
| candidate | repeated    | ≥2 real render cases + observations |
| candidate | rejected    | Rejection reason documented     |
| repeated  | validated   | ≥2 scenes + human approval + regression OK |
| repeated  | rejected    | Rejection reason documented     |
| validated | rejected    | Regression evidence of failure  |
| rejected  | candidate   | New evidence submitted          |

## What it does

1. Loads the candidate from `05_项目经验/`.
2. Validates the transition is legal.
3. Validates referenced render cases, observation links, approval fields, and regression evidence.
4. Writes a rollback snapshot under `.promotion_history/`.
5. Moves the candidate file to the new status directory.
6. Records the promotion timestamp and approval record.

## Rules

- Single observation cannot enter validated.
- `repeated` and `validated` require at least two independent evidence IDs and
  two user observations.
- `validated` additionally requires those evidence IDs to come from at least
  two different `scene_id` values.
- Validated experiences must have regression test coverage.
- Validated promotion requires `--approved-by`, `--regression-command`, and
  `--regression-passed`.
- Referenced render cases must exist under `05_项目经验/render_cases/`, and
  referenced observations must exist in those cases.
- Render evidence with reference assets must record the asset content/version
  hash used for that render.
- Knowledge updates are reversible.
- Mode/promote does NOT call any rendering engine.

## Related

- `/mode-p-learn` — Knowledge Curator for ingest and curation.
- `05_项目经验/` — Experience directory structure.
- `01_调度器/mode_p/render_evidence.py` — Implementation.
