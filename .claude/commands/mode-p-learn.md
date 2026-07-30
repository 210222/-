# /mode-p-learn — Curate MODE:P experience from external render evidence

MODE:P does NOT render. This command ingests real Jimeng SD2.0 render
results and user observations, producing structured experience candidates
for the knowledge pipeline.

## Usage

```text
/mode-p-learn ingest <render-case-id>
/mode-p-learn curate
/mode-p-learn list [--status candidate|repeated|validated|rejected]
/mode-p-learn review <candidate-id>
/mode-p-learn export
```

## What it does

1. `ingest` — Reads a render case from `05_项目经验/render_cases/<id>/`
   (evidence.json + observations.json), synthesizes a candidate experience,
   and saves it to `05_项目经验/candidates/`.

2. `curate` — Reviews all candidates and suggests promotions based on
   evidence rules (>=2 independent evidence → repeated; no evidence → reject).

3. `list` — Lists candidates by status.

4. `review` — Shows full details of a specific candidate.

5. `export` — Exports validated knowledge as JSON for potential integration
   with `knowledge_index.json`.

## Rules

- No real render evidence → no candidate creation.
- Single observation stays in candidate; cannot enter validated.
- Knowledge updates are reversible; regression tests must pass.
- The Knowledge Curator does NOT call any rendering engine.

## Related

- `/mode-p-promote` — Human approval for validated experiences.
- `05_项目经验/` — Experience directory structure.
- `01_调度器/mode_p/knowledge_curator.py` — Implementation.
- `01_调度器/mode_p/render_evidence.py` — Evidence schema.
