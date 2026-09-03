# Phase G independent execution preflight — STOP before paid calls

Date: 2026-09-03. Reviewed clean starting HEAD
`5904ca735792e51327e57acfad21515bd92be3ee`, including the Phase G preparation
in `a14e774` and decision memo in `5904ca7` after dossier `f34074a`.

**Verdict: FAIL execution preflight. Frozen experimental integrity: PASS.**

The user authorized N=96 and at most USD 10.00, conditional on this preflight.
No provider/API calls, U generation, target inference, or response judging were
performed. Phase G spend and reservations remain USD 0.00. No execution run
manifest was created: the execution gate did not pass. Phase H was not started,
the manuscript was not edited, and no human labels were loaded.

## 1. What passes

- All **82 file hashes** across the final freeze, Phase B outputs, Phase C
  outputs, Phase D archive/results, and post-audit sensitivities match their
  respective manifests byte-for-byte. Of these, 14 are the original
  `FREEZE_MANIFEST.json` entries. That manifest alone does not cover Phase D;
  its separate manifests were also checked.
- Phase A QC passes all **28 checks**, written to a separate temporary output
  directory. The original 504-pair bank, 1,512 pair-model jobs and 3,024 scores
  were not changed or regenerated.
- Generator artifact verification passes all 17 checks, including the final
  instruction SHA, V2 loader eligibility, single-seed/no-evolution provenance,
  30 evaluations/24 all-constraint passes, and no target signal.
- Independent SHA-rank reconstruction reproduces all 96 selected IDs and
  their categories/strategies. There are exactly 8 in each of 12 cells. After
  the newline-only engineering correction below, both selection files reproduce
  byte-for-byte in a temporary directory without touching the originals.
- Alternating by hash rank within cells yields four archaic/over-formal and
  four telegraphic/clipped assignments in every cell. This is rederived from
  the specified rule; the prepared runner does not yet persist or use these
  assignments.
- All **576 existing E/R response-score keys** for the selected 96 pairs and
  three targets are present exactly once. Target slugs, temperature 0, empty
  system prompt, 4,096-token cap, Gemini judge ID and 2,048-token judge cap
  match the frozen run configuration. The intended new target/judge counts
  are 288/288, U only.
- Selection reads only bank identity/strata and manifest data; there is no
  Phase E label or target-outcome dependency. Existing scores were joined
  only in a separate verification step, after reproducing selection.
- `.env` exists, is ignored, and is not tracked. It was not opened or loaded.
  The established CLI uses `load_dotenv()` and the provider client reads the
  environment variable; the Phase G scaffold has no live credential/client
  integration yet. Live secret/logging safety therefore remains unvalidated.
- The algebra of the paired primary contrast is correct:
  `(E-R)-(E-U) = U-R` for the score-zero indicators. Pair-ID resampling,
  Qwen-only primary inference, two-sided exact McNemar, the frozen 0–3 rubric,
  E/R reuse and the English label for U are appropriate intended settings.
- The canonical manuscript consistency check passes. Manuscript and validated
  scientific outputs are unchanged. No stochastic published analysis was rerun.

## 2. Scientific blockers requiring a pre-outcome decision

### S1 — The manipulation gate is not operationally frozen

Sources: `analysis/phase_g/PREREGISTRATION.md` Sections 5.3 and 9;
`STATISTICAL_ANALYSIS_PLAN.md` Sections 6–8;
`EXECUTION_CHECKLIST.md` Stage 3; `config/phase_g.yaml`.

The preregistration names a “fixed public tokenizer” and “fixed English word
list” but specifies neither. No implementation pins their identities, versions
or hashes. The gate also does not settle whether it compares the median of
paired fragmentation differences or differences between marginal medians;
those are not generally equal. The descriptive 11.4% **character-length**
expansion is not a tokenizer-fragmentation margin. The only retained token
profile uses `chars/4 fallback`; that is a cost heuristic, not a usable
fragmentation measurement, and must not silently become the manipulation gate.

More importantly, Section 9 requires regenerating the U set with a
**strengthened instruction** if the gate fails, but supplies no strengthened
instruction, number of whole-set regeneration rounds, or rule for counting
those attempts against the four-attempt-per-pair ceiling. No exact initial
transformation prompt, English-to-English auditor prompt/schema or manipulation
implementation is committed either. The latter prompts can be engineered from
the semantic contract, but the gate-dependent change of U construction and
its stopping rule determine which prompts reach inference. They cannot be
silently chosen after seeing U candidates and described as the exact frozen
procedure.

The user's newer execution instruction resolves a separate conflict: if any
cell cannot be filled within its ceiling, stop. This overrides the older SAP
permission to analyze incomplete/unfilled cohorts. I have not relaxed either
the sample or the acceptance gate.

**Required decision:** freeze the exact fragmentation statistic and resources,
and the bounded manipulation-failure procedure, including how its attempts
count. Either approve a precisely specified strengthening round under a fixed
total limit, or explicitly require stopping at manipulation failure. Neither
alternative has been activated. This is not a request to change N or add arms.

Tokenizer fragmentation is a surface proxy, not proof of equal distance from
all three models' unknown training distributions. A passing gate would support
an unusual-English control under that proxy, not a causal mechanism claim.
I have not claimed that the proposed U styles cannot pass: no U exists yet.

### S2 — The frozen interpretation table does not cover all possible intervals

Source: `PREREGISTRATION.md` Section 2, lines 86–91.

Literal application leaves each of these intervals with **no matching row**:

- `[-0.10, 0.75]`: contains 0 and 0.5, but not 1;
- `[0.25, 1.10]`: contains 0.5 and 1, but not 0;
- `[0, 0.5]` and `[0.5, 1]`: endpoint cases also fall through.

These are mathematical counterexamples, not experimental results. Furthermore,
the reproduction ratio divides by the E−R gap. Its policy for zero/sign-changing
bootstrap denominators or empty sensitivity subsets is unspecified. This is
particularly relevant to the small-effect descriptive models. Dropping such
draws, clipping ratios to [0,1], or assigning a substantive category by default
would each be an unregistered inferential choice.

**Required decision:** complete the pre-outcome rule. The conservative proposed
resolution is to label all otherwise unclassified intervals **inconclusive**,
and undefined/unstable ratios **not interpretable**, retain/report the direct
paired contrast, and never clip or discard problematic draws to obtain a
favorable category. This proposal is not an amendment to the frozen protocol
until approved; exact denominator handling still needs to be recorded.

The stated 0.913 power is for rejecting **Delta=0** under one simulated
U-generation model at rho=0.75. It is not demonstrated power for classifying
which side of **rho=0.50** the CI lies on. The simulation also assumes U cannot
differ where E and R agree. These are scenario assumptions, not a general
power guarantee. N=96 and the primary test are not changed by this audit.

## 3. Mechanical execution blockers, demonstrated offline

`runner.py` explicitly exits without executing even if both approval flags are
supplied (lines 250–254). It is a preparation scaffold, not a functioning
experiment. Its 13 preparation tests pass, but do not test the following
counterexamples. They are reproduced using **synthetic callbacks only** in
`analysis/phase_g/preflight_audit.py` and recorded in
`analysis/phase_g/preflight_20260903.json`.

| Fault | Reproduction | Consequence |
|---|---|---|
| Prior spending not restored | Two resumed segments each receive a fresh $1 guard; two $0.60 jobs both execute, totaling $1.20 | A per-process ceiling is not a total-run ceiling |
| Failed billed attempts absent from disk | A $0.20 parse failure followed by a $0.10 success leaves only $0.10 in the ledger, although memory recorded $0.30 | Restart undercounts spending/provenance |
| Reservation is an estimate, not a bound | Under a $0.10 ceiling, reserve $0.01 then receive a $0.20 success | Overspend is detected after billing; `settle()` raises before the successful payload is saved |
| Retry cap resets on restart | A job capped at three failed calls makes six across two restarts | No persistent per-job attempt ceiling |
| No durable in-flight marker | Simulated interruption after remote completion but before local persistence leads to a second remote completion on restart | Deterministic IDs alone do not prevent duplicate billing |

Additional source-level gaps: exceptions are assumed to cost zero even when
delivery/billing is ambiguous; `plan_jobs()` hashes pair/model/stage but not
the U prompt/configuration; generation attempts do not have distinct candidate
identities; the ledger is not tied to an immutable run/config/hash manifest;
no live remaining-work budget projection or single-writer lock exists.
Certification cascading, fail-closed U audits, generation retries, U-bank
freezing, manipulation enforcement, response judging and the SAP analysis
are not implemented. The standalone scaffold also does not load credentials.

Before activation, implement a durable request/reservation journal; reserve
verified maximum costs, retain all billable failures and ambiguous charges,
restore total commitments/attempts on resume, and persist raw successes before
further parsing or budget decisions. A remotely completed but locally unknown
request must be quarantined/reconciled, not automatically retried. Network
exactly-once billing cannot be guaranteed by a local job hash alone. Add
synthetic crash, restart, cost-overrun, stale-hash and repaired-parse tests.

These are repairable implementation issues. Because scientific blockers also
exist, I preserved the existing provider refusal guard rather than wiring an
experiment whose acceptance/interpretation rules are incomplete.

## 4. The cost model is not yet an execution-safe estimate

The committed $1.817 expected estimate is historical preparation, not a
verified current quote or a guarantee of 96 certified pairs:

- Its expected scenario spends on 211.2 generation/primary-audit attempts and
  assumes 60% primary pass and 60% secondary pass. That implies 76.032 expected
  acceptances, not 96. `component_costs()` does not use `secondary_pass` to
  determine attempts needed to fill N.
- Under that scenario and **independent, identical attempts**, a four-attempt
  cap fills a pair with probability `1-0.64^4 = 0.83222784`: about 79.89 of 96
  pairs in expectation. The chance of filling all 96 would be about
  `2.20e-8`. This exposes internal scenario incompatibility; it is **not** an
  empirical prediction of English-to-English certification yield.
- The conservative cost scenario uses 4.38 generation calls per accepted pair,
  exceeding the four-attempt ceiling if every selected pair must complete.
- Gemini judging cost is proxied by historical GPT-5 Mini cost and called a
  “strict upper bound”; no mathematical bound is established by using another
  model's observed mean. Target output lengths use a `chars/4` heuristic.
- GPT-OSS's list price is explicitly unverified. The expected-high $3.39
  includes an extra cross-judge, which is **not authorized in this design**.
  The nominal 864-job no-retry plan also differs from the cost model's roughly
  1,158 expected all-stage calls once generation and retry overhead are added.

Current provider pricing was not fetched: the scientific gate failed before
any provider API request was necessary. Actual request-size/max-output bounds,
reasoning usage, current routing prices and a projected remaining-work stop
must be validated after the missing procedure is frozen and before payment.
No ceiling increase is requested, and no extra cross-judge is authorized.

## 5. Objective engineering fixes made in this gate

1. **Default pytest collection:** the original repository-wide command wandered
   into ignored historical V1 checkouts and temporary directories, producing
   duplicate-module imports, a legacy-module shadow and a permission error.
   Scoped normal discovery to `tests` and the active `src` tree in
   `pyproject.toml`. No historical evidence was edited or deleted.
2. **Selection byte reproducibility on Windows:** the selection CSV matched,
   but the original JSON writer used platform-dependent newlines, while the
   frozen manifest has LF bytes. Explicit LF output and narrowly scoped Git
   attributes now preserve the existing JSON-LF/CSV-CRLF serialization. A new
   regression test runs selection into a temporary directory and compares
   both outputs byte-for-byte against the frozen selection. No pair, seed,
   allocation, manifest content or selection hash changed.

The standalone audit and its JSON contain aggregate verification evidence and
synthetic failures, not U data, secrets, human labels or reproduced harmful
content. The preregistration, SAP, execution config, runner, manuscript and
all A–D/sensitivity outputs were left unchanged.

## 6. Commands and completion state

All commands are local/offline, from the repository root:

```powershell
.\.analysis-venv\Scripts\python.exe -m pytest -q
.\.analysis-venv\Scripts\python.exe analysis/phase_g/runner.py
.\.analysis-venv\Scripts\python.exe analysis/phase_g/preflight_audit.py
.\.analysis-venv\Scripts\python.exe analysis/qc_final.py --output tmp/phase_g_preflight_20260903/qc
.\.analysis-venv\Scripts\python.exe scripts/verify_generator_artifact.py
.\.analysis-venv\Scripts\python.exe paper/audit_paper_consistency.py
```

The audit intentionally exits 1 because the gate fails; this is not a crashed
experiment. The runner command above is its **dry run**, not a resume command.
After the mechanical fixes, the full active repository suite passes **79/79
tests**, including all 13 original Phase G tests and the new byte-reproduction
test. This does not certify the scaffold for paid execution: its uncovered
faults are separately demonstrated above. `git diff --check` also passes.

| Requested field | State |
|---|---|
| Preflight | **FAIL — stop before paid calls** |
| Certified U prompts | **0/96** |
| U target jobs | **0/288** |
| U judgments | **0/288** |
| Actual API cost / committed | **$0.00 / $0.00** |
| Remaining authorized maximum | **$10.00**, conditional on passing preflight |
| Qwen E/U/R results, gaps, primary CI/p | No Phase G result; U does not exist |
| GPT-OSS / Nemotron results | No Phase G result |
| Manipulation check | **NOT RUN**, not a measured failure |
| Phase G sensitivities/interpretation | **NOT RUN** |
| Frozen integrity | **PASS: 82/82 manifest file hashes** |
| Design deviations | None executed; no experimental data collected |

Next required action is approval of a narrow **pre-outcome clarification** for
S1/S2. Keep N=96, the 12-cell allocation, the two U forms, both auditors, the
U-only target arm, original rubric, Qwen estimand/test and $10 ceiling unchanged.
Then complete and adversarially test the implementation, freeze its execution
manifest, and repeat preflight before any paid call. Do not start Phase H or
rewrite the manuscript.
