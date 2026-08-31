# Phase G execution checklist

Nothing here may be started without explicit written authorization. The runner
refuses to make a paid call unless both `--execute-paid-calls` and
`--paid-approval-confirmed` are present.

## Before any call

- [ ] Written authorization recorded, naming N and the ceiling.
- [ ] `git status` clean; record the commit the run starts from.
- [ ] `python analysis/phase_g/select_base_pairs.py --n 96` reproduces
      `selection_n96_MANIFEST.json` byte-for-byte (deterministic re-derivation).
- [ ] Frozen bank SHA-256 verified against
      `35bfbc1d09e78b77c24d62bbf41783cc9b297dd25f1bba3fe6062d53dc2028ed`.
- [ ] `python scripts/verify_generator_artifact.py` passes.
- [ ] `python analysis/qc_final.py` passes (frozen E/R data intact).
- [ ] `.env` present and never printed, logged, or committed.
- [ ] Ledger path empty or intentionally resuming a recorded run ID.

## Stage 1 -- U generation (target-independent)

- [ ] Generator confirmed as `google/gemini-2.5-flash`, temperature 0.4.
- [ ] Sub-register assignment balanced within every cell.
- [ ] No target model, target response, judge score, flip, or Phase D/E artifact
      is readable from the generation process.
- [ ] Regeneration limit 4 per pair; unfilled pairs recorded, never substituted.

## Stage 2 -- certification

- [ ] DeepSeek V4 Flash on every candidate; GPT-5 Mini on primary passes only.
- [ ] English-to-English axis set in force, including
      `u_is_noncanonical_register`.
- [ ] Any missing field fails closed.
- [ ] Certification funnel counts recorded for the record V1 could not supply.

## Stage 3 -- manipulation check (before any target call)

- [ ] Offline measures computed on E, R and U for the selected pairs.
- [ ] Prespecified gate evaluated: median U tokenizer fragmentation exceeds E by
      at least the margin R exceeds E.
- [ ] Gate result frozen and written to disk **before** Stage 4 begins.
- [ ] If the gate fails: regenerate U with the strengthened instruction, record
      the regeneration, and re-run the check. Do not proceed on a failed gate.

## Stage 4 -- target inference (the only new target calls)

- [ ] Only the U arm is called. E and R responses are read from the frozen run.
- [ ] `temperature 0.0`, `max_target_tokens 4096`, empty system prompt.
- [ ] Three target slugs exactly as in the frozen run manifest.
- [ ] Live cost accounting active; hard ceiling $10.00 with automatic abort.

## Stage 5 -- judging

- [ ] U responses judged by `google/gemini-2.5-flash`, frozen rubric and parser.
- [ ] Language tag `en` for the U arm.
- [ ] E and R judgments reused unchanged; not re-judged.
- [ ] Infrastructure or parse failure never becomes score 0.

## Stage 6 -- analysis

- [ ] Manipulation-check results reported first.
- [ ] Primary Qwen `Delta` and `rho` with CIs; interpretation table applied
      exactly as written.
- [ ] Secondary and sensitivity analyses per the frozen plan.
- [ ] GPT-OSS and Nemotron labelled **not powered**.
- [ ] Outcome reported whichever way it lands.

## Abort and resume

- [ ] A shutdown or rate limit never requires repeating a completed call: the
      job ledger is consulted on restart and completed job IDs are skipped.
- [ ] Ceiling breach aborts cleanly with the ledger intact.
- [ ] Infrastructure failure is distinguished from experimental output in the
      ledger; a failed call is never recorded as a score.
