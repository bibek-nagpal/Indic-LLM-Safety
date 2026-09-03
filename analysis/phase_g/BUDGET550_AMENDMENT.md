# U-ARCH-v3 amendment 2: bounded $5.50 execution design

2026-09-03; parent `8a7498445d651fcdcb30681e58f142f637f91cdd`.
Prospective engineering/financial amendment, not a new U construct or a result.
**No paid approval in this task. No sanity run, U generation, target inference
or judging.** Seven successful public unauthenticated metadata GETs were made;
only public model IDs were sent, never source prompts, outcomes or credentials.

This record supersedes amendment 1's both-auditors-on-rejected-candidates rule
and $10 ceiling. Its historical reports under `u_arch_v3_preflight/` remain
byte-for-byte intact. Current reports are in `u_arch_v3_budget550/`.

## Scientific strictness versus call inefficiency

All three accepted specification/schema files are unchanged. All 17 axes remain
mandatory in **one complete call per auditor**, not 17 calls. Semantic, harmful-
objective, requested-information and strategy equivalence, comprehensibility,
Englishness and strong sustained archaization remain hard requirements.

Auditing is now **sequential**: generate -> mechanical checks -> DeepSeek ->
GPT-5 Mini only if DeepSeek passes. Both auditors still certify every accepted
candidate. A primary rejection cannot be rescued by Mini, so its second call
was redundant for the acceptance decision. Each auditor sees the same E/U and
metadata, never the other's report or generator rationale. Missing secondary
reports are logged as NOT DISPATCHED, not fabricated as failures or agreements.
This permits dual certification, **not** unbiased unconditional inter-auditor
agreement estimates. Rejection summaries must state their different denominators.
Feedback now contains the first rejecting auditor's qualitative reasons only;
this changes the search path prospectively, not any acceptance gate.

Four generation requests per pair remain the absolute maximum. Acceptance stops
that pair. Valid auditor rejections never trigger repolling: a genuinely new
candidate is required. Duplicate/whitespace-equivalent candidates are not
re-audited. Each dispatched auditor has at most two requests, the second only
for malformed output or a proven-unbilled transient error. Format repairs are
fully budgeted as billed. Local BOM/whitespace/exact JSON-fence removal is free;
it does not fill fields, guess scores or change content. Deterministic 400/401/
403/404/405/422 responses stop immediately. Billed infrastructure failures and
ambiguous delivery stop; never assume an HTTP error is free or retry a timeout.

The generator/auditor 4096-token caps are retained. The detailed rubric requires
request/strategy representations, per-axis reasons and grounded style evidence;
no live length measurements justify lower limits yet. JSON-object response mode
and the existing concise structured contract reduce format waste without
dropping any field. Reasoning effort is not reduced/disabled; suppressing its
display would not avoid its bill. No input truncation or metric regeneration.
Prompt prefixes are stable and may receive automatic caching, but **zero cache
savings** enter either forecast or reservations. No explicit cache-writing calls.

The only target work budgeted is **96 U x3 models =288** jobs and 288 new Gemini
judgments. Frozen E/R results/scores are reused unchanged; no repeated target E/R,
second cross-judge experiment or new pilot is included.

## Sanity rule unchanged

N=12; exactly one per category x strategy cell, same seed and same selected IDs
as amendment 1, disjoint from both the 120 ladder and historical 24 sources.
READY iff all 12 certify within four requests each, >=9 pass on attempt one,
provenance is complete, and no unresolved failures/violations remain. Otherwise
NOT READY; a budget/infrastructure stop is additionally reported as incomplete,
not falsely interpreted as semantic failure. First-pass count/rate, attempts/item,
all rejection axes and role-specific calls/costs are reported.

The 9/12 floor remains reasonable as a prospective feasibility gate, **not a
powered estimate of population success** or a promise of budget feasibility.
Relaxing it would weaken the gate, whereas sequencing avoids a redundant call.
The separate financial gate may stop before four attempts; it never permits
accepting an uncertified item, shrinking N, or selecting the most convenient items.

## Verified provider evidence and compatibility blocker

Public endpoint/catalog snapshots record retrieval time, URL, raw/selected
response hashes, exact model and canonical IDs, endpoint tags, prices, status,
parameter support, reasoning metadata and precision. Route pins and server-side
max_price caps prevent an automatic switch to a dearer provider. All fees are
USD per million input/output tokens; service tiers are not different model IDs.

| Role/model | Proposed pinned route | Expected input/output rates | Standard reservation rates |
|---|---|---:|---:|
| `google/gemini-2.5-flash` generator/judge | `google-ai-studio/flex` | 0.15 /1.25 | 0.30 /2.50 |
| `deepseek/deepseek-v4-flash` auditor | `deepinfra/fp8` | 0.09 /0.18 | same |
| `openai/gpt-5-mini` auditor | `openai/flex` | 0.125 /1.00 | 0.25 /2.00 |
| `qwen/qwen3-30b-a3b-instruct-2507` target | `streamlake` | 0.04815 /0.19305 | same; quote includes discount |
| `openai/gpt-oss-20b` target | `deepinfra/bf16` | 0.03 /0.14 | same |
| `nvidia/nemotron-3-nano-30b-a3b` target | `crusoe/fp8` | 0.05 /0.20 | same |

Target routes are budget preparation only, not enabled execution. No lower-
precision FP4 endpoint or new model identity is selected to save money. Models
and catalog canonical versions are pinned; aliases cannot guarantee an immutable
upstream snapshot. Recheck public availability before later authorization.

**BLOCKER:** every available Mini endpoint omits `temperature` from supported
parameters, whereas the frozen request contains `temperature=0`. With strict
parameter support this cannot route. No silent parameter dropping or fallback
is allowed. The appropriate compatibility amendment is to omit unsupported
temperature and accept Mini's native sampling; **it has NOT been implemented**
because the prior instruction requires approval for a consequential inference-
parameter correction. The model, rubric and gates need not change. Current live
sanity preflight is FAIL, and the execution plan blocks every dispatch.

Flex is requested explicitly with `service_tier=flex`, an exact endpoint route,
no provider fallback, and standard-tier price reservations. OpenRouter bills the
actual served tier; unexpected/absent Flex confirmation is saved with its actual
cost and quarantined, not repeatedly retried at standard price. Flex trades
latency/availability for cost, not a weaker rubric/model. The unchanged 120-second
timeout can therefore yield a fail-closed interruption; no timeout-resubmit loop.

References: [provider routing/price caps](https://openrouter.ai/docs/guides/routing/provider-selection),
[service tiers](https://openrouter.ai/docs/guides/features/service-tiers),
[request parameters](https://openrouter.ai/docs/api_reference/parameters),
[reasoning billing/defaults](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens),
[Google thinking](https://ai.google.dev/gemini-api/docs/generate-content/thinking?hl=en).
Exact pricing/support evidence is in the seven local metadata snapshots.

## Cost interpretation and protected stage budgets

See `u_arch_v3_budget550/COST_PREFLIGHT.json` for separately calculated input and
output costs by role, exact current source/system/schema token profiles, assumed
future lengths, retry counts and standard-tier sensitivity. Expected is a
transparent scenario, not a measured probability or maximum invoice:

- sanity: 15 generation +16 DeepSeek +14 Mini =45 requests;
- main: 120 generation +126 DeepSeek +114 Mini =360 requests;
- targets: 101/model =303 including 5% rounded-up retries;
- judging: 303 including 5% rounded-up retries.

The generation scenario is 75% first-pass/25% second-pass. Primary rejects are
assumed to account for 2 of 3 sanity retries and 12 of 24 main retries. This
allocation is not observed. Expected audit output is 3072 billed tokens including
reasoning. Generator output uses 1.5xE +256 visible/JSON tokens plus a 512-token
thinking allowance; target output 2048 total; judge 600 visible +512 thinking.
Google's actual dynamic thinking is unmeasured and may be much greater. Input
profiles use offline o200k with cl100k sensitivity, **not native token bounds**.

| Stage | Expected Flex | Standard-tier sensitivity | Enforced hard-authorized ceiling |
|---|---:|---:|---:|
| Sanity N12 | $0.0851 | $0.1554 | $0.65 |
| Construction/certification N96 | $0.6863 | $1.2557 | $2.60 |
| U-only targets | $0.1120 | $0.1120 | $0.75 |
| U-only judging | $0.5564 | $1.1128 | $1.50 |
| Cumulative Phase G | **$1.4399** | **$2.6359** | **$5.50** |

No stage may borrow from another automatically. Unspent caps are not billed.
The ~$0.50 account reserve remains outside this ledger. Hard stage maxima mean
**abort limits, not guaranteed prices for completing that stage**. A successfully
ready sanity may reach 105 calls; a failed one 240; sequential auditing does not
reduce the worst case in which the primary always passes and the secondary
rejects. These call maxima and four-generation bounds remain, but affordability
can stop sooner. Full worst-case completion is **not guaranteed** within $5.50.
The JSON reports an uncapped, deliberately loose sum of reservations, and the
maximum-path output-cap cost alone, to demonstrate why these are different.
That output-only path costs $8.8292 at the quoted Flex prices before input or
additional thinking charges. It is not authorized. The much looser sum of
full-context reservations in JSON is a mathematical upper bound, not a realistic
forecast: each actual small request releases most of that conservative reserve.
Per-call reservation: generator $0.4886503, DeepSeek $0.1069056, Mini $0.364192,
Qwen $0.013131533, GPT-OSS $0.02102056, Nemotron $0.0611122, judge $0.4835303.
The sanity cap includes room for its expected cost plus its largest final-call
reservation; the controller may still stop well below the cap on an expensive path.

## Enforced accounting and reproducibility

One canonical private SQLite journal covers all four stages. Integer nanodollars,
FULL synchronous transactions and a write lock persist each role/stage/request/
hash/maximum reservation before dispatch. A request is refused if global actual
bills +pending reservations +next reservation exceed $5.50 **or** its stage cap.
All role costs reconcile to stage and global totals, including malformed replies,
errors and interrupted delivery. Completed calls replay raw saved responses;
pending/quarantined calls stop every controller. Changing configuration, request
bytes, role/stage, locks or journal path cannot reset the cap. No hidden retries.

Per-call reservations deliberately use full published native context bounds and
endpoint output maxima plus an extra requested-visible allowance, priced at
standard tier even when Flex is requested. This is loose, but avoids claiming
cross-tokenizer proxies prove a hard bound or assuming hidden reasoning is free.
Reservations are released to actual billed amounts only on a complete receipt.
No tools, search, plugins, images, explicit cache writes or per-request charges
are allowed. Server price caps are pinned in each request and reconciled with
the reservation proof. Unexpected prices/usage/tier/model/provider or missing
costs preserve evidence and stop; unknown charges retain their entire reserve.
No local controller can undo a provider billing-contract violation or control
other account users, credit-purchase fees or external spending; it guarantees
**authorized dispatch** within bounds, not the provider's billing machinery.

The financial kernel is shared with future target/judge adapters; those execution
controllers are not yet implemented/enabled. Before targets the older obsolete
preregistration/SAP must be prospectively reconciled, and both adapters must pass
the same offline safeguards using this same journal, not new budgets.

Reproduce without network or inference:

```powershell
.\.analysis-venv\Scripts\python.exe -B -m analysis.phase_g.run_offline_tests
.\.analysis-venv\Scripts\python.exe -B -m analysis.phase_g.budget550_preflight --write
git diff --check
```

Preflight exits 1 intentionally while the Mini compatibility blocker remains.
Reports are write-once and deterministic; changed reports require a reviewed
new version. The public fetcher is separate and not invoked by these commands.
Frozen data, published analyses, historical development and manuscript remain
unchanged. Current validation details are in `u_arch_v3_budget550/VALIDATION.json`.
