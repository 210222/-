---
description: Reopen R1.2 and replace reconstructed summaries with eight verbatim user prompt fixtures under pinned hashes.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# MODE:P vNext R1.2 Exact Prompt Repair

The parent Claude Code session is the only writer and must be
`deepseek-v4-pro`. The Golden expert remains read-only. This command repairs
only R1.2; do not start R1.3.

## Model and source gates

Invoke only `mode-p-vnext-golden-prompt-auditor`, in the foreground, before and
after repair. Verify actual `resolvedModel=deepseek-v4-pro` every time.

The sole verbatim source is the existing Codex user-message JSONL:

`C:/Users/JT/.codex/sessions/2026/07/22/rollout-2026-07-22T08-59-14-019f8755-685c-7fe1-b712-5db7b5960a77.jsonl`

It is an actively appended file, so do not pin or require a whole-file hash.
Read it once by streaming JSONL; never load the 266MB file into model context.
Select only `type=response_item`, `payload.type=message`,
`payload.role=user`, and the first `input_text` content block for each pinned
event below. If the text contains the literal ASCII separator
`## My request for Codex:\n`, the prompt body is every code point after its
first occurrence; otherwise the entire first input-text block is the body.
Do not call `strip`, normalize newlines, join image blocks, or decode/re-encode
through a lossy console.

## Pinned verbatim bodies

| fixture stem | JSONL line | characters | UTF-8 SHA-256 |
|---|---:|---:|---|
| gun_barrel_sb | 275 | 1703 | `ce4caf8504593b307d0835120e516f427f4d6ed0e41d2bf35395f95169496ea8` |
| gun_barrel_video | 293 | 2544 | `452f8fabc04e6e44b6e8f4d80919ea35b37bd8b765cc52bad94dfaa1a5095cce` |
| audience_sb | 360 | 2099 | `1cd5a30f019e97f6651771fa8155229c85c8c969eca0400d7da0db3bb2b02141` |
| audience_video | 381 | 2397 | `5fa1815ade3e507807f583c2d4556997bbe8e10538a4badeaaed4eb51bfb8787` |
| prep_area_sb | 404 | 1600 | `ed006256727083cba8e1b5ae065fe6e1e7671b02f033c8d4c738d49d3af1b057` |
| prep_area_video | 425 | 1811 | `36f45f042d3c3350a3e6a847e321eb9c0e3c9b2be9966a8154237af42d13a46c` |
| alley_sb | 440 | 3032 | `8e14b8f21da8a54116d2ff2fe5ef0ec9eab5c03a3d8c55ae28daa184aa766edb` |
| alley_video | 458 | 2932 | `a558b598e0718c3bbae1aa717c44f08b07c2939d2feedce5c775ad97fcdc52c9` |

If any line/event/length/hash is unavailable or mismatched, stop before
invalidation with `R12_VERBATIM_SOURCE_BLOCKED`. Never substitute Evidence
Report prose, old v4 output, or model reconstruction.

## Exact write boundary

The parent may edit only:

- the eight `01_调度器/mode_p_vnext/fixtures/*_prompt.json` files;
- `01_调度器/mode_p_vnext/fixtures/prompt_fixture_manifest.json`;
- `01_调度器/mode_p_vnext/golden_fixture_registry.py`;
- `01_调度器/mode_p_vnext/golden_registration.py`;
- `01_调度器/mode_p_vnext/tests/test_v0_5_golden_fixtures.py`;
- `01_调度器/mode_p_vnext/tests/test_v8_1_golden_registration.py`;
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.2.json`.

State and lock changes occur only through `rebuild_control.py`. Everything
else is forbidden, including the source JSONL, R0/R1.1 files and Evidence,
R1.3 renderers/tests, media, old v4 output, knowledge sources, production gates,
and `.claude/settings.local.json`.

## Preflight and reopen

Require control audit clean, R1.2 completed, R1.3 unclaimed/uncompleted,
`next_task=R1.3`, no owner/token, project-local settings absent, and no unknown
edits in the exact write boundary. Record all R0.1-R1.1 Evidence and artifact
hashes. Stream-extract all eight bodies into memory or an OS temporary location,
verify the table, then discard temporary data after fixture writes.

Invalidate exactly R1.2 with a reason naming reconstructed summary prompts,
confirm R1.2 becomes next, and claim exactly R1.2 with a unique owner. Keep the
token private. On failure after claim, use control `fail`; do not manually edit
state or release locks.

## Test-first exactness contract

Before replacing fixtures, add tests that fail against the current summaries:

- exact fixture set is four storyboard/video pairs;
- each loaded `prompt_text` character count and UTF-8 SHA-256 equals the pinned
  table;
- source metadata contains `source_kind=codex_user_message`, JSONL line,
  `source_body_length`, `source_body_sha256`, and
  `source_fidelity=verbatim`;
- `integrity_note`, Evidence, and registration contain no `Reconstructed`,
  `reconstructed`, `summary`, or `created from descriptions` claim;
- changing one code point, trimming final newlines, normalizing blank lines, or
  replacing a full prompt with a >100-character summary fails;
- the fixture manifest hashes all eight final JSON files;
- prep-area remains one continuous fixed camera design with timing/behavior
  deviation; alley/prep section references remain correct;
- user statements and `INFERENCE` audit classifications stay separate.

Do not assert exactness by comparing a value with itself or with a hash computed
from the candidate fixture at test runtime. The expected prompt-body hashes and
lengths are fixed independent constants.

## Verification and completion

Run the authoritative R1.2 suite, R1.1 baseline suite, rebuild-control suite,
and R0.2 active-entrypoint suite. Run the Golden expert post-review. Complete
only when all pass and the verified expert returns `READY`.

Postconditions: audit clean; R0.1-R1.1 hashes unchanged; R1.2 artifact hashes
bind every fixture, fixture manifest, registry, registration, and both tests;
no owner/token; `next_task=R1.3`; `.claude/settings.local.json` absent; production
entry `v4_unchanged`. Evidence must report the eight pinned source-body hashes,
lengths, extraction rule, and `verbatim` status. Never output
`LOCAL_VNEXT_READY`.
