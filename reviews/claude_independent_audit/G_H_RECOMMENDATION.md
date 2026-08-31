# Phase G and Phase H — Expected Value Assessment

Neither experiment was run, and nothing here proposes running one. This is an assessment of expected scientific value against cost and complexity, informed by what the audit found.

**Headline:** Phase G is the single highest-value remaining experiment and is **more** necessary than the current manuscript implies, because the audit found that the paper's only judge-free control is itself confounded. Phase H is low-value in its designed form and should stay deferred — but a *free, offline* fragment of it is recoverable and worth doing.

---

## Phase G — unusual-English out-of-distribution control

### Does it actually distinguish a Romanized-Hindi effect from generic distribution shift?

**Yes, and it is currently the only instrument in the project that can.** The argument is worth stating precisely because the answer is not obvious.

Reviewer 2's objection is that the Hinglish effect may be nothing but a distribution-shift effect: safety training generalises poorly off the English instruction-tuning manifold, and Hinglish is simply off-manifold. Every existing element of the paper is compatible with that reading:

- The **paired certification** controls intent, scenario, granularity, strategy, cultural specificity, target group, and ambiguity. It does **not** control distance from the training distribution — that is precisely what the manipulation changes, and it is what the alternative hypothesis names.
- The **model-heterogeneity result** is suggestive but not decisive. Qwen 43 pp / GPT-OSS 4.6 pp / Nemotron −1.8 pp shows the effect is model-dependent, which rules out a pure harness artifact. It does not rule out that Qwen is simply the most brittle to *any* off-distribution input.
- The **cross-judge re-judge** holds the responses fixed and swaps the scorer. It says nothing about what caused the responses.
- The **length signal** is judge-free but, as this audit established, largely reflects language-conditioned verbosity: 32% of Qwen's forward-shaped pairs and 48% of Nemotron's reverse-shaped pairs come from pairs the judge scored 0 in *both* languages. It cannot separate register from distribution shift either — and it now needs its own defence.

So the OOD alternative is currently unaddressed by construction. Phase G addresses it directly: hold the same 120 frozen base pairs, add a third arm that is distribution-shifted **within English**, and compute a difference-in-differences. If Qwen's unusual-English gap is ~5 pp against its 43 pp Hinglish gap, the register-specific claim is established. If it is ~35 pp, the paper's central interpretation must change — and that would still be a publishable, honest result.

### The audit raises the value of Phase G in a way the handoff did not anticipate

Two findings compound:

1. **Phase C is confounded.** The manuscript leans on the length check as its independence guarantee. Once the both-safe decomposition is reported (as it must be), the paper's judge-free evidence weakens, and the OOD control becomes the strongest remaining external validation.
2. **The judge is not blind to language** (`PROMPT LANGUAGE: en|rh` in every judge message). Phase G partially repairs this at no extra cost: the unusual-English arm is scored under `PROMPT LANGUAGE: en`, identical to the baseline arm. A large baseline-EN-vs-unusual-EN difference under an identical language tag, contrasted with the EN-vs-RH difference, gives a within-tag comparison that the current design cannot produce. Phase G should be designed to exploit this explicitly.

### Design assessment

The handoff's §G design (120 pairs, 10 per cell, fixed seed, two predeclared sub-registers, English-to-English certification with the same nine axes, dual DeepSeek + GPT-5 Mini acceptance, reuse of existing baseline English responses, 360 new target calls) is sound. Five refinements:

1. **Pre-register before generating variants.** Write down the transformation rules, the sub-register definitions, the certification predicate, the analysis (paired difference-in-differences with pair-clustered bootstrap), and the falsification criterion — e.g. "if the unusual-English gap exceeds 50% of the RH gap for Qwen, we report that the effect is not register-specific." Commit the file first. The audit found several places where post-hoc framing weakened otherwise good work; this experiment must not join them.
2. **Add a perplexity or tokenisation-cost anchor.** The weak point of any OOD control is that "unusual English" and "Hinglish" may not be equally unusual. Report a distribution-distance proxy — tokens per character under each target's tokeniser, or the token-count ratio to baseline English — for all three arms. Without it, a null Phase G invites the reply "your unusual English simply was not unusual enough." This is measurable offline before any target call and should gate execution: if the unusual-English arm is not at least as token-expansive as the RH arm (RH is +11.4% in characters over baseline English), regenerate the variants.
3. **Sample the 120 pairs from within the Phase D cross-judge scope** where possible, so the OOD control, the cross-judge, and the human validation share pairs and can be jointly analysed.
4. **Certify equal length, not just equal strength.** RH prompts run 11.4% longer than their English counterparts. The English-to-English variants should be held to a comparable expansion so the arms are matched on the one axis the original nine do not cover.
5. **Do not re-run baseline English.** Correct in the handoff; reuse the frozen responses. This halves cost and preserves the frozen-artifact discipline.

### Cost and complexity

New target calls: 120 × 3 models = 360 responses, plus 360 primary judge calls and optionally 360 cross-judge calls. Phase D judged 1,944 stored responses with GPT-5 Mini for $3.68 (~$0.0019 per judgment), and the three target models are small open models. Variant generation plus dual certification for 120 pairs is comparable to a small bank build (the frozen bank's per-candidate audit cost was on the order of cents).

**Realistic estimate: USD 5–15 all in**, with the dominant risk being certification yield — if the English-to-English equivalence gate rejects heavily, more generation rounds are needed. Budget for 2–3× the nominal candidate count.

Wall-clock: 1–2 days including preregistration. Complexity: moderate. It reuses the existing generator, auditor, target-runner, and judge code paths with a new category of transformation; no new infrastructure.

### Risk

The chief risk is **researcher degrees of freedom in defining "unusual English."** A transformation chosen (even unconsciously) to be mild produces a small unusual-English gap and a flattering conclusion. The handoff already says "Do not design the transformation to force the desired result" — preregistration plus the tokenisation anchor in (2) is how that instruction becomes enforceable.

Secondary risk: a null or ambiguous result. This is acceptable. A well-designed Phase G that finds a substantial unusual-English gap is a *better* paper than one that never asked, because it converts an unaddressed reviewer objection into a measured quantity.

### Verdict

**Run it — after Phase E, and only with a committed preregistration.** It converts the paper's most serious conceptual objection from unanswerable into answered, it partially compensates for the two validity findings above, and it costs on the order of ten dollars.

---

## Phase H — certification ablation

### Is it feasible from the existing logs?

**No.** `PRESUBMISSION_STATUS.md` is correct that the frozen `attempts.jsonl` holds only six records (four retrieval errors, two audited candidates) for a run that certified 504 pairs. The handoff's §H1 assumes "60 rejected candidate pairs, 5 per cell, stratified across major rejection causes, with complete EN/RH text and clear audit provenance." That material does not exist.

The audit found one partial recovery the presubmission status missed, which changes the picture at the margin but not the conclusion.

### What *is* recoverable, for free

The three uncommitted V2-era GEPA directories contain `metric_log.jsonl` files holding **92 audited candidates** with per-constraint failure reasons:

| run | records | acceptance | failure modes |
|---|---:|---|---|
| `gepa_20260825_210033` | 27 | scores 0.9–1.0 | 5 near-misses |
| `gepa_20260826_103104` | 35 | 29 perfect, 1 at 0.0 | mixed |
| `gepa_20260826_135819` (frozen objective) | 30 | **24/30 accepted (80%)** | 3× `correct_category_membership` + `direct_harm_facilitation`; 1× `direct_harm_facilitation`; 2× total failure |

This supports a short, honest **descriptive selectivity paragraph**: under the frozen 13-constraint objective, the DeepSeek primary auditor accepted 80% of generated candidates in offline evaluation, with rejections dominated by category-membership and direct-facilitation failures rather than equivalence-axis failures.

Three caveats that must be stated if it is used: (i) this is the GEPA-time distribution, not the bank-build funnel; (ii) it reflects primary-auditor acceptance only, not the full cascade; (iii) n = 30 for the frozen objective. Labelled that way, it is a legitimate partial answer to "how selective is the gate?" at zero cost. Do **not** present it as a certification ablation.

### Would a *new* certification ablation be worth commissioning?

Marginal, for three reasons.

1. **Weakest reviewer demand.** Reviewer 2 raised it alongside the OOD control, and the OOD control answers the deeper objection. No reviewer made it a condition.
2. **The result is close to a foregone conclusion.** Uncertified pairs will show noisier, larger, less model-specific gaps. That is what "the gate does something" predicts, and a reader will grant it without an experiment. It demonstrates a design principle rather than testing a hypothesis that could plausibly fail.
3. **It contaminates the frozen study.** 360 new target responses on deliberately-uncertified prompts create a second, differently-constructed dataset that must be kept rigorously separate from the frozen bank. `PRESUBMISSION_STATUS.md` §4 is right that a partial post-hoc ablation "could confuse the frozen study with a new experiment." That risk is real and is not worth the payoff.

One version *would* be worth doing, if resources were abundant: an **inter-auditor agreement study** on primary rejects. The cascade means GPT-5 Mini never saw DeepSeek's rejections, and the audit found that the two auditors' descriptive equivalence scores correlate at **−0.028** on the accepted set (range restriction explains most of it, but the artifact contains no measurable inter-auditor reliability at all). Sampling ~100 primary rejects, re-auditing them with GPT-5 Mini, and combining with ~100 accepted pairs would yield a real acceptance-agreement κ — the handoff's §F3. That requires **no target inference**, costs a few dollars in auditor calls, and directly retires the limitation the paper currently concedes in §7. It is a better use of the same budget than Phase H, though it depends on the rejects having been retained (the six-record `attempts.jsonl` suggests they were not, which would make even this infeasible without regeneration).

### Verdict

**Do not run Phase H.** Keep it as future work, exactly as the manuscript already does. Do the free offline selectivity paragraph from the GEPA metric logs, clearly labelled. If auditor budget becomes available, spend it on the §F3 inter-auditor agreement study instead — it addresses a limitation the paper actually concedes.

---

## Ranking by expected improvement per unit cost

| Rank | Action | Cost | Expected improvement | Reviewer addressed |
|---|---|---|---|---|
| **1** | Fix the GEPA description + commit the correct generator artifact | ~0 | **Very high** — removes a falsifiable Method claim | A (methodology) |
| **2** | Offline reanalyses: Phase C decomposition, cluster-robust sensitivity, truncation sensitivity, Bowker, per-cell cross-judge agreement, prompt-length null | ~0 (compute only) | **Very high** — retires most of Reviewer B's asks | B (statistics) |
| **3** | Bring related work current; narrow the novelty claim | ~0 | **High** — retires Reviewer C's strongest objection | C (multilingual) |
| **4** | Fix Phase E (competence criterion, symmetric tie-break, restored size, extended analysis script) then collect labels | ~0 API; annotator time | **High** — the only direct evidence on judge validity for Hinglish | A, C |
| **5** | **Phase G**, preregistered, with a tokenisation anchor | ~USD 5–15 | **High** — the only instrument that separates register from distribution shift | C, and Reviewer 2 of the original round |
| 6 | §F3 inter-auditor agreement on primary rejects (if rejects survive) | ~USD 2–5 | Moderate — retires a conceded limitation | A |
| 7 | Response-only re-judge (no prompt, no language tag) on a subsample | ~USD 2–4 | Moderate — the only way to test judge language-blindness | A |
| 8 | Offline selectivity paragraph from GEPA metric logs | 0 | Low–moderate, correctly labelled | A |
| **—** | **Phase H certification ablation** | ~USD 5–10 + contamination risk | **Low** — confirms the expected; risks confusing two datasets | none decisive |

Items 1–4 are free and should precede any paid experiment. Item 5 is the only paid experiment worth authorising, and only after 1–4 and with a preregistration committed first. Items 6–7 are attractive optional additions in the same budget band as 5. Item H should remain unrun.
