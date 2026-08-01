# MODE:P vNext v3.0 construction-plan architecture audit

## Scope

This audit checks the complete A0–A10 task graph against every normative v3.0
boundary before implementation resumes. It is a design/control audit, not
evidence that A1–A10 implementation already exists.

## Findings and repairs

| Prior hidden mismatch | Root consequence | v3.0 task repair | Status |
|---|---|---|---|
| FactAssembler required by ingest but owned by no package before A5 | A4/A5 could not consume canonical facts legally | A1 owns `source_normalizer.py`, `fact_assembler.py`, fact domain and tests | Closed in task graph |
| 15-second constant scoped to a Scene pool | multi-shot scenes compressed/truncated | A1 owns capability types; A5 enforces the maximum for every Shot and proves Scene is not capped | Closed in architecture/task checks |
| dialogue anchor derived from source characters | provenance became invented screen timing | A1 defines typed phase intent; A5 maps it into the selected VisualBeat; source span excluded | Closed in architecture/task checks |
| reference/audio requirements derived globally | Director choice lost and requirements floated | A1 freezes typed binding intents; A4 transports them; A5 validates and binds them | Closed in ownership chain |
| Projection types redefined downstream | two delivery truth sources | A1 owns domain type; A6 only compiles canonical ProjectionAST and adapters | Closed in task graph |
| active docs said v2.2 while ledger said v2.3 | operators could follow a different authority than controller | A0 owns five active guidance surfaces and controller audits their registry marker | Closed by A0 implementation |
| architecture audit accepted document hashes but not active-entry convergence | stale guidance could still be claimed | `next` and `claim` fail on v3 authority/guidance drift | Closed by A0 implementation |
| broad tests depend on personal absolute paths | green/failing result not portable | A0 requires portable registered verification; later task tests must use repo fixtures/temp dirs or explicit external classification | Policy closed; affected legacy fixtures remain non-authoritative |
| old 27K prompt island remained discoverable | easy accidental return to monolithic prompt design | historical island remains read-only; A4 has hard B1 prompt/schema budgets and no hidden fallback | Closed by authority and A4 checks |

## Ownership stress test

The graph is strictly linear `A0 -> A1 -> ... -> A10`; path overlap audit is
mandatory. Cross-package contracts are frozen at their earliest legal owner:

- A1: persistent domain, ingest assembly, capability and intent types;
- A2: state and invalidation mechanics;
- A3: selected knowledge contract;
- A4: model transport only;
- A5: deterministic compilation only;
- A6: projection only;
- A7: review/media ports only;
- A8: composition through the real CLI, without redefining earlier types;
- A9: frozen evaluation, without runtime self-modification;
- A10: evidence and human gate, without production switching.

No later task may repair an earlier persistent contract. Discovery of such a
need is an architecture gap and must fail/invalidates downstream evidence.

## Adversarial pathway checks

- A free-text note that resembles a fact ID cannot create a binding.
- A fact ID prefix cannot reveal semantic type.
- A long Scene with several valid Shots is legal; each Shot is checked
  independently against the capability profile.
- Changing source formatting without fact semantic change preserves source
  provenance rules but never moves audio in time.
- A requirement with no Shot/Beat consumer fails Gate 0.
- A storyboard adapter cannot add an event absent from ProjectionAST.
- DP cannot claim media acceptance, and media acceptance cannot imply owner
  approval.
- Owner approval is hash-bound to current media evidence and still cannot set
  the production switch flag.
- Architecture or active-guidance drift blocks `next/claim` before worker edits.

## Audit conclusion

The v3.0 construction plan preserves the original Director/DP and dual-output
ideas while repairing ownership and data-flow gaps. It is internally suitable
to begin A0–A10 migration. This conclusion authorizes only A0 in the current
round and does not assert downstream implementation completion.
