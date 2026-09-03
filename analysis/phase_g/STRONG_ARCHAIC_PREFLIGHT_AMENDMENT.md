# U-ARCH-v3: pre-outcome sanity amendment and offline preflight

Date: 2026-09-03. Parent: `b647e29d1ba456540b1594d110d8bb0f2f794901`.
This record is prospective. **No sanity run, U generation, target inference,
judging, external request or paid API call was performed. Current authorization:
$0.** The accepted strong-archaic construct is not reopened.

## Amendment and preserved history

The old rule at `b647e29` required 12 first-generation successes with no semantic
regeneration. The amended rule mirrors the bounded production process:

- 12 distinct sources, exactly one/category x strategy cell;
- at most four generation requests per source, including failed/malformed ones;
- both independent auditors assess each mechanically valid new candidate,
  rather than the old primary-pass-only cascade;
- acceptance requires both auditors to pass every frozen hard gate; first pass wins;
- valid rejection is never repolled. A new generation is required; exact or
  whitespace-only duplicate text reuses its earlier rejection without re-auditing;
- no target outcomes, numeric optimization, researcher selection, family switch
  or extra pilot. Baseline-E invalidity or unresolved infrastructure stops the stage.

**GENERATION SPECIFICATION READY** iff all 12 certify within four attempts each,
at least 9 certify on attempt one, provenance is complete, and no unresolved
failure/protocol violation remains. Otherwise **GENERATION SPECIFICATION NOT
READY**. The 9/12 floor is retained: it is a prospective feasibility threshold,
not a powered statistical test or a population-rate guarantee.

All attempts, auditor rejection axes, first-pass numerator/12, attempts/item,
unfilled items, and per-role call/billed/reserved totals are retained. Actual
first-pass rate, attempts/item and rejection axes are **NOT OBSERVED / NOT RUN**
in this task; synthetic fixture results are not development results.

The three `specs/strong_archaic_v3_*` files (generation instruction, independent
17-axis audit instruction, output schemas) are byte-identical to the parent.
The original preregistration/SAP, legacy runner/config/cost JSON, 96/120 selections,
historical 24-source/five-family material, frozen E/R, published analyses and
manuscript are not rewritten. Only banners mark the old execution checklist and
cost-model prose as historical. Git history preserves the superseded rule.

## Cohort preflight

The existing seed `phase-g-u-strong-archaic-sanity-v3|20260903` and lowest-SHA-256
selection rule are applied without opportunity/length/outcome filtering.
Each cell has **30 eligible sources** after excluding the 120-pair ladder and
24 historical development IDs. Exactly 12 unique source IDs/texts are selected,
one/cell, with **zero ID or exact-E-text overlap** with either excluded cohort.

The [sanity manifest](u_arch_v3_preflight/SANITY_COHORT_MANIFEST.json) contains
IDs, ranks, cell labels and source/input hashes, not raw prompts or generated U.
The code reads only whitelisted E/source metadata for development. Stored
`candidate.info_level_requested` maps to payload `information_requested`;
absent metadata remains null. No R text, outcome, response length or score is
used for selection, construction messages or cost input profiling.

## Execution engineering and its limits

[Execution plan](u_arch_v3_preflight/EXECUTION_PLAN.json) records exact model IDs,
temperatures, output caps, retry limits, deterministic cohort/attempt identity,
source/spec/code locks, streaming disabled and no hidden transport retries.
Generation and both audit schemas are validated with Draft 2020-12 and strict
JSON parsing; wrong IDs, extra fields, Boolean/integer confusion, duplicate keys
and inconsistent accept reports cannot pass. Schema validity alone is never
certification. Grounded, nonoverlapping style evidence and strategy structure
checks supplement all 17 required Boolean gates.

The separate construction controller and single-dispatch HTTP adapter replace
none of the old artifacts and do not expose a live command in this checkpoint.
Their safety properties are tested with fixed benign fixtures/HTTP mocks:

| Check | Offline result / behavior |
|---|---|
| Durable before dispatch | SQLite `FULL` transaction saves exact request/hash, ID, role, timestamp and maximum reservation before transport invocation |
| Durable after response | Full response body, selected nonsecret headers, provider/model/request ID, usage and actual cost saved before parsing; no hidden reasoning substituted as JSON |
| Restart | Completed calls replay saved raw output; no new request for a completed call, valid rejection or exhausted repair job |
| Ambiguous timeout/crash | Pending/quarantined state retains reservation and blocks every further dispatch; no automatic zero-cost assumption or duplicate |
| Known billed error | Actual cost retained separately by role; generation consumes a slot; billed auditor infrastructure errors stop |
| Auditor format repair | Initial plus at most one identical-contract request; valid negatives are never format repairs |
| Unknown or excessive cost | Preserve evidence before stopping; unknown cost keeps reservation; excessive observed cost is recorded, not discarded |
| Budget | Integer nanodollars; persisted actual + pending reserve + next-call maximum must be <= $10 BEFORE dispatch |
| Concurrent/resumed controller | Atomic reservation and unresolved-call gate prevent another controller dispatching a duplicate |
| Main promotion | A recorded sanity READY and separate approval reference are necessary; same construction ledger/cost history retained |
| Target isolation | Construction controller and transport cannot enable target-model IDs; no target/outcome modules imported |
| Privacy | No `.env` reads; no authorization headers logged; future raw journals go to Git-ignored `u_arch_v3_private/` |

Both auditor payloads are identical; neither contains the other report or generator
reason. Bounded qualitative feedback contains failed-axis codes and at most 400
Unicode characters per report (up to six reports before attempt four). This is a
serialization/input-size bound, not a new scientific criterion.

There is **no exactly-once guarantee from OpenRouter** inferred from the client
job header. An ambiguous request may have completed remotely. It cannot be
reissued until externally evidenced reconciliation under review; no automatic
receipt-fetch/reconciliation operation is enabled here.

The legacy `runner.py` is still an intentionally disabled scaffold with known
faults. The new controller is tested offline, not represented as a tested live
experiment. Target/judge orchestration is still unavailable; future integration
must use a single phase-wide cost ledger including sanity/main expenses, not a
fresh $10 allowance. It must pass equivalent offline safeguards before targets.

## Cost recalculation: quantities and uncertainty

[Full cost breakdown](u_arch_v3_preflight/COST_PREFLIGHT.json) includes measured
per-source input profiles, role-specific input/output costs, retry counts,
tokenizer-asset hashes and local billing-evidence hashes. No old average charge
per call or old $1.82 forecast is reused as the new calculation.

The exact current system/schema strings and actual selected E/metadata are
assembled with the deterministic first-attempt IDs. Offline cached `o200k_base`
counts supply the planning token proxy; `cl100k_base` counts are also recorded.
These are **not exact Gemini, DeepSeek or target token counts**. U and responses
do not yet exist: their lengths are explicitly assumed, never presented as
measured generated text. Expected U is 1.5 times mean E token length (106 proxy
tokens); expected generator output adds 256 JSON/reason/other tokens. Expected
audit output is 3,072 tokens including reasoning; targets 2,048; judge 600.
Expected generation input includes an extra 256-token feedback allowance;
all requests include a 32-token planning wrapper margin.

Expected scenario: 75% first-generation and 25% second-generation successes,
with 5% extra audit/target/judge requests rounded up separately per role/model.
This is an explicit budgeting scenario, **not an empirically estimated success
probability**. All retry calls are priced as fully billed. No caching or batch
savings are assumed.

High scenario: all allowable generations, two auditor requests per candidate,
three target/judge requests per job, maximum output caps, 8,192-token future-U/
response input envelopes, 8,192 feedback tokens and 64 extra item-ID tokens.
The cross-tokenizer input envelopes are **stress assumptions, not rigorous
provider-certified upper bounds**. Valid completed target responses or scores
are never rerun; target retries concern infrastructure failures only.

| Stage | Expected requests | High requests | Expected input $ | Expected output $ | Expected total $ | High total $ |
|---|---:|---:|---:|---:|---:|---:|
| 12-source sanity | 47 | 105 | 0.0332 | 0.1256 | **0.1588** | **1.2045** |
| Construct/certify 96 U | 372 | 1,920 | 0.2622 | 0.9911 | **1.2533** | **22.0385** |
| 288 U-only target jobs | 303 | 864 | 0.0028 | 0.1847 | **0.1875** | **1.5229** |
| 288 Gemini judgment jobs | 303 | 864 | 0.2704 | 0.4545 | **0.7249** | **8.8843** |
| Full phase, including sanity | **1,025** | **3,753** | **0.5686** | **1.7560** | **2.3246** | **33.6501** |

Expected sanity splits into 15 generation, 16 DeepSeek and 16 Mini calls;
main splits into 120, 126 and 126 respectively. Expected sanity role costs
are $0.020694 / $0.023108 / $0.114992. Expected main role costs are
$0.165660 / $0.182027 / $0.905657. Each is independently reconciled in the JSON.

The 105 sanity high requests are conditional on being able to proceed:
9 first-attempt +3 fourth-attempt successes =21 generations, plus 42 calls per
auditor. An exhausted sanity run can instead reach **48 +96 +96 =240 calls**,
about **$2.7531** under the high assumptions, but necessarily fails readiness
and **stops before main**. Adding that failed pilot to a completed full-phase
scenario would violate the progression rule.

Historical uncached billing evidence (USD/million input / output tokens):

- Gemini Flash: **0.30 / 2.50**, 1,005 uncached receipts.
- GPT-5 Mini: **0.25 / 2.00**, 1,113 uncached receipts.
- DeepSeek V4 Flash: modal **0.14 / 0.28** (423 of 1,490 uncached receipts);
  observed maxima **0.44 / 1.32** used in the high scenario.
- Qwen **0.04815 / 0.1931**, Nemotron **0.05 / 0.20**: historical locally
  recorded rates; GPT-OSS **0.10 / 0.50** is an explicitly unverified legacy
  planning assumption, not a verified offer.

No current prices or provider availability were looked up. Neither the expected
estimate nor the high scenario is a guaranteed invoice. **$10 remains the hard
total phase ceiling; $33.65 is not authorized spend.** A costlier realized path
must stop at the ceiling, potentially leaving the phase incomplete. Even a
high scenario below a ceiling would not replace verified per-call reservations.

## Remaining live-preflight blockers

1. Current provider routing, exact model availability, parameter support (including
   temperature on Mini), reasoning settings and billable output-limit semantics
   require external verification, forbidden in this task. Model slugs are pinned;
   they do not guarantee an immutable upstream model snapshot.
2. Verified per-call input-token/price maxima are absent. The execution plan keeps
   every `maximum_call_nusd` **null**, so the controller fails before dispatch.
   Do not convert the proxy cost estimates into allegedly verified reservations.
3. The new adapter is HTTP-mock tested only. A future authorized, price-verified
   execution entry point and private journal require reviewed quote/settings locks.
4. Before targets, prospectively reconcile the older preregistration/SAP and
   complete/test target/judge integration. Neither can be silently inherited from
   the obsolete two-register/metric-regeneration design. No such rewrite occurs now.
5. No paid approval exists for this task. The actual sanity result is NOT RUN.
   Main construction and targets require the later separate approvals already
   specified; an expensive realization stops under the unchanged $10 cap.

## Reproduce the offline checks

From `C:\Prahlada` using the existing environment, with no package downloads:

```powershell
.\.analysis-venv\Scripts\python.exe -B -m analysis.phase_g.run_offline_tests
.\.analysis-venv\Scripts\python.exe -B -m analysis.phase_g.strong_archaic_preflight --write
git diff --check
```

The preflight command exits **1 intentionally** because live readiness is FAIL.
It computes only selection, hashes and cost tables. It refuses to overwrite
different existing preflight outputs; repeated identical execution verifies them.
The regression wrapper blocks external networking while permitting Windows
asyncio's internal loopback wakeup pipe. New construction tests block all sockets.
An initial overly broad all-socket regression guard blocked that OS mechanism;
the two unrelated async tests were rerun under this loopback-only wrapper, not
fixed by enabling external networking or changing scientific code.

**124 regression tests pass**, including 45 new offline preflight/controller/
transport tests. All 82 files in the existing freeze/analysis manifests and
10 legacy G input byte locks verify unchanged. All three accepted specs match
the parent Git blobs byte-for-byte. Git-canonical comparison confirms no changes
to the nine historical development files.

One pre-existing historical serialization issue is disclosed, not silently
rewritten: `u_control_development/u_candidates_index.csv` has CRLF in this
working tree (SHA-256 `b3d6b02eeb5a88b27ee9f1386093910635e973b05d88e30ffc5e368eeeffcab8`),
whereas its manifest and parent Git blob specify LF (SHA-256
`ce29cd966e05815e9e94549cbb2b6b86c4696b4fdbe3904880aa79984a05111a`).
Normalizing line endings reproduces the parent blob exactly; the file's write
time predates this task's new implementation. Its bytes are left untouched.
It is not a U-ARCH-v3 input. `.gitattributes` now records its manifest's intended
LF for future checkouts, while preserving CRLF for the development-cohort CSV
and local billing receipts whose byte hashes use CRLF. No normalization command
or historical regeneration was run. The new manifest and directly hash-locked
inputs have explicit checkout line-ending rules.

**Sanity rule updated: YES. Cohort valid: YES. Construction resumability and
cost ledger: PASS under offline tests. Frozen artifacts unchanged: YES.
Overall live preflight: FAIL (blocked as listed). Stop before any paid call.**
