# U-ARCH-v3 amendment 3: Mini API compatibility and N12-only authorization

Parent: `604c8c386d81fd89c497c46505a6db60a7c787ff`. This is a prospective,
pre-outcome API-compatibility amendment explicitly authorized by the user.
No Phase G U outcome had been observed when this amendment was prepared.

## Exact change

Omit the `temperature` field entirely from GPT-5 Mini auditor requests because
the pinned OpenRouter endpoint does not support it. Do not send null, zero or a
replacement sampling value. Mini uses its native sampling. Its model identity,
4096-token output cap, JSON-object format, reasoning settings (omitted, unchanged),
provider route and all instruction/schema bytes remain unchanged. This is not
a change to the scientific method, construct or certification criteria.
Gemini generation retains temperature 0.4 and DeepSeek auditing temperature 0.

All 17 hard axes, identical independent auditor inputs, primary-pass-only Mini
dispatch, four total generation attempts, first-certified-candidate stopping,
bounded format/known-unbilled repair, and prohibition on repolling valid rejects
remain unchanged. Source selection/seed/IDs and the strong-archaic instructions
are byte-identical. No instructions are revised after observing the run.

## Conditional authority and stop conditions

The user authorizes **only the frozen N=12 sanity check**, after all Stage 1
requirements pass and the amendment/preflight are committed. Sanity retains
exactly one source per category x strategy cell, disjoint from the frozen 120
ladder and previous 24 sources. READY still requires 12/12 dual certified within
four attempts, >=9 first-attempt dual passes, complete provenance and no unresolved
failure or protocol violation. Any incomplete technical run is NOT READY and
explicitly distinguished from a completed scientific readiness failure.

Sanity cap **$0.65**. Cumulative remaining Phase G ceiling **$5.50**. The other
stage caps ($2.60 construction, $0.75 targets, $1.50 judging) are preserved and
cannot be borrowed. They are not authorization to execute those stages. All
costs stay in the existing canonical phase-wide journal; no fresh budget/reset.

No main U construction, target inference, response judging, E/R rerun, replacement
source, extra pilot, alternate model/endpoint or post-result rule change is
authorized. If preflight fails, no paid call. If execution stops, preserve all
evidence and do not improvise a recovery or continue to another experiment.

## Execution/provenance

`sanity_compat.py` provides separate public-metadata, offline-preflight, and
sanity-execution modes. The first two cannot load credentials or run inference.
The execution mode requires a committed passing preflight/offline-test receipt
and verifies its code/input locks before loading the API key locally. Nothing
prints or commits the key. The only live adapter allows the same three generator/
auditor models and exact endpoint tags. No target/judge orchestration is imported.

The shared FULL-synchronous SQLite journal records intent/reservation before each
dispatch and the complete raw response/actual receipt before parsing. Replays use
completed calls; pending or quarantined delivery stops all dispatch. No hidden
transport retries or automatic reconciliation. Per-call reservations, stage caps,
provider/tier checks and billing-error behavior from amendment 2 are unchanged.

Public reports contain IDs/hashes, counts, rejection axes and accounting only;
source/U/audit text and raw response bodies stay in Git-ignored
`u_arch_v3_private/`. A summary is reconstructed from the durable journal even
when execution halts before a final scientific report. Unknown bills retain
reservations and are never described as actual charges. Token-cost estimates
are distinguished from provider-reported charges. No target outcomes enter this
process; final integrity verification is hashes only.

## Reproduction and scope

From the repository root, offline checks use:

```powershell
.\.analysis-venv\Scripts\python.exe -B -m analysis.phase_g.run_offline_tests
.\.analysis-venv\Scripts\python.exe -B -m analysis.phase_g.sanity_compat preflight
```

Only after the passing preflight and test receipt are committed:

```powershell
.\.analysis-venv\Scripts\python.exe -B -m analysis.phase_g.sanity_compat execute --amendment-commit COMMITTED_HASH
```

The exact run command/commit and final result are recorded in the versioned
`u_arch_v3_sanity_compat/` output directory. This document is pre-outcome and
will not be rewritten to accommodate the observed sanity result. Previous
preflight directories and the frozen bank/results remain unchanged.
