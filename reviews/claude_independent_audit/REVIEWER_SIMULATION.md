# Reviewer Simulation

Three independent simulated reviews of `paper/acl_latex.tex` at commit `31d5732`, written as the reviewers would write them — each seeing only the manuscript plus the artifact repository, with no access to this audit. ACL-style scoring: Overall 1–5, Soundness 1–5, Excitement 1–5.

---

## Reviewer A — Skeptical NLP methodology reviewer

**Summary.** The paper builds a 504-pair English/Hinglish probe with per-item dual-model equivalence certification, runs it on three open models, and reports that the English-minus-Hinglish refusal gap is 43 pp for Qwen, 4.6 pp for GPT-OSS, and −1.8 pp for Nemotron. The methodological framing — matched pairs, frozen bank, pair as unit — is the right instinct for a question that is usually asked sloppily.

**Strengths.**
- The construct is well posed. Separating "does this attack set work?" from "does behaviour change when only register changes?" is a real distinction, and the paper states it crisply.
- Everything is defined before it is used: the 0–3 rubric, refusal, forward/reverse/critical flips. §3 is the cleanest part of the paper.
- The bank is frozen with a published SHA before any target call, and generation provenance records no target model. That is the correct discipline and it is rare.
- Scope restraint is genuine and repeated. The paper says explicitly that it does not estimate prevalence and does not claim universality. I want to reward that.
- Cross-model heterogeneity is the honest headline. A weaker paper would have buried Nemotron.

**Weaknesses.**
1. **I checked the artifact and the GEPA claim does not hold up.** §4.1 says GEPA optimises the generator guidance and Appendix B is devoted to the objective. The GEPA state in the repository contains one program candidate with no parent, a null Pareto summary, a single reflection call, and thirty dollars-of-a-cent of spend. Whatever produced the frozen instruction, it was not prompt evolution. And the instruction whose hash the bank manifest records is not in the repository at all — the committed GEPA directory holds a different, older prompt. This is the kind of thing that makes me distrust the rest of the method section, even though the rest of it checked out when I looked.
2. **"Refusal" is not what is being measured.** R = 1[s=0] is "no domain-specific harmful assistance." The authors' own data show that not one of Qwen's 115 Hinglish score-0 responses is short — 114 of 115 exceed 500 characters — while 61% of its English score-0s are terse. The headline number is a real and interesting asymmetry, but calling it a refusal gap misdescribes it.
3. **The judge is told which condition it is scoring.** `PROMPT LANGUAGE: en|rh` appears verbatim in every judge message. For an EN-vs-RH difference study, that is a design flaw, and the cross-judge replays the same messages, so it does not test for it.
4. **Two of the three "regimes" are not distinguishable.** The GPT-OSS − Nemotron contrast sits at Holm p = .032 on a single analysis, and on the paper's own cross-judge subset it is 4.32 pp with a CI spanning zero under Gemini. "Three distinct regimes" is doing more work than the interval supports.
5. **Prompt independence is assumed, not established.** The consolidation report says exact-string dedup only, yet the bank manifest advertises a 0.85 near-duplicate threshold. Within cells I can find English prompts sharing 90% of their tokens. The pair-level bootstrap treats these as independent draws.
6. Cell-level results at n=42 are correctly labelled descriptive; no complaint there.

**Questions.**
- What exactly did GEPA optimise, and where is the instruction whose SHA the manifest records?
- Why does the manifest advertise a near-duplicate threshold that the consolidation report says was not applied?
- Why does the judge see the language label, and what would change if it did not?
- What is the effective number of independent prompts?
- The consolidation report says 502 retained; the bank has 504. Where did the other two come from, and when?

**Scores.** Soundness 3 · Excitement 3 · **Overall 2.5 → reject, with a clear path to accept.** The empirical work is careful and the numbers I could check were exact. I cannot recommend acceptance while a Method section claim is contradicted by the authors' own artifact. Every one of my objections is fixable without new experiments, and I would look favourably on a resubmission.

---

## Reviewer B — Statistical / reproducibility reviewer

**Summary.** Paired analysis of 504 probes on three models, with pair-clustered bootstrap CIs, exact paired tests, sign randomisation with Holm, and a clustered GEE secondary model. A judge-free length check and a partial cross-judge re-judge are offered as robustness.

**Strengths.**
- The statistical toolkit is the right one and is implemented correctly. I read `analyze_final.py`; the Bowker implementation, the Holm step-down, the sign-flip randomisation with the (extreme+1)/(B+1) correction, and the seed-spawning discipline are all textbook.
- Crucially, the bootstrap applies the *same* resampled pair indices across models, so the between-model contrast CIs properly inherit the pairing. Many papers get this wrong.
- The ordinal rubric is never averaged. Refusal is an indicator, flips are threshold events, the full 4×4 table is retained, Bowker is used rather than a t-test. Exactly right.
- The fallback-sensitivity analysis (dropping the two fallback-judged jobs in full, preserving pairing) is a model of how to do a provenance check.
- Fail-closed gating — the Phase B analyser re-runs the Phase A QC and refuses to proceed — is good engineering.
- I reproduced the point estimates from the committed CSVs and they are internally consistent to the last decimal.

**Weaknesses.**
1. **I could not reproduce anything from the repository.** `.gitignore` excludes `frozen_final_*/bank/`, `frozen_final_*/run/`, and `probe_banks/*`. The Phase D GPT-5 Mini scores are committed but the primary Gemini scores are not, so even the cross-judge comparison is not recomputable. The paper says "Analysis scripts regenerate every reported table and figure from the frozen snapshot," which is true only for someone who already has the snapshot. Given the content, gating is legitimate — but then say so, and say what a non-gated reader can and cannot verify.
2. **Multiplicity is applied to one family of three and nowhere else.** Three McNemar tests, three directional binomials, three Bowker tests, three Phase C tests, and six Phase D CIs are all unadjusted and unflagged. For Qwen it is irrelevant; for the borderline results it is not.
3. **The independence assumption is not defended.** Pair ID is the resampling unit, which is correct as far as it goes, but nothing establishes that the 504 pairs are independent. Deduplication was exact-string only. I would want a sensitivity analysis at the prompt-cluster level.
4. **The length check is presented as independent evidence but is not diagnostic.** It thresholds on raw character counts. Nothing in §5.3 rules out that the models are simply more verbose in Hinglish irrespective of content. Without a decomposition by judged outcome, I cannot tell how much of 203:0 is safety and how much is style.
5. **Truncation is not addressed.** With a 4,096-token cap and models that respond at very different lengths by language, I would expect a report of `finish_reason == length` by arm and a sensitivity analysis. Neither appears.
6. **Bowker p-values are computed and not reported.** The results file is in the repository. Reporting a test only in prose as "secondary" while its numbers exist is not good practice.
7. **A judge-agreement statistic pooled across conditions with obviously heterogeneous difficulty** (73.65%, κ=.541) tells me less than a breakdown would.
8. Percentile rather than BCa intervals for the small cell-level estimates; minor.

**Questions.**
- Can you release a synthetic or hash-only derivative sufficient to re-run Phases B–D end to end?
- What is the effective sample size after accounting for prompt similarity?
- What fraction of responses hit the token cap, by model and language, and what happens to the estimates when those jobs are dropped?
- Please report all Bowker statistics and state which p-value family was Holm-adjusted.
- What is the length-shape count restricted to pairs where the judge found harmful content?

**Scores.** Soundness 3 · Excitement 3 · **Overall 3 → borderline, leaning accept if the sensitivity analyses are added.** The analysis I can see is competent and honest. My concerns are about what is *not* shown rather than about errors in what is. None of them requires new data.

---

## Reviewer C — Multilingual / safety researcher

**Summary.** A controlled English/Romanized-Hindi paired probe, certified per item by two model families, evaluated on three open models with a graded severity rubric. Headline: the language effect is strongly model-dependent.

**Strengths.**
- **Romanized Hinglish is genuinely under-served**, and treating it as its own register rather than as noisy Hindi is the right call. The RomanSetu motivation is apt.
- **Per-item equivalence certification is a real methodological advance** over translate-then-evaluate. Nine named axes plus strategy structure plus a per-language validity check, with a deterministic acceptance predicate and fail-closed behaviour on missing fields, is stronger than anything in the benchmarks I know.
- **Graded 0–3 severity with prespecified critical-flip definitions** is the right response to StrongREJECT's critique of binary evaluators.
- **The heterogeneity finding is the most valuable thing here.** The same frozen 504 probes producing 43 pp on Qwen and nothing on Nemotron is a genuinely useful result for the field, and it is the natural reconciliation of contradictory prior reports. I would like this to be the paper's headline rather than its consolation.
- Ethical handling — no attack text in the main paper, gated-release recommendation, annotator warning — is appropriate.

**Weaknesses.**
1. **The related work is not current, and two omissions bear directly on novelty.** Banerjee et al. (2025) already build matched English/code-mixed pairs across ten languages including Hindi, with human validation at Fleiss κ = 0.76–0.81 and a mechanistic account. Aswal & Jaiswal (2025) is the existing Hinglish red-teaming paper. Neither is cited. Yong et al. (2023), the origin of this whole line, is also absent. Eleven references, two of them tooling, is thin.
2. **The paper cites IndicJR but not IndicJR's finding.** IndicJR reports that romanized and mixed inputs *reduce* jailbreak success rate — the opposite direction. That is a gift to this paper: model dependence explains it. Not engaging with it reads as selective.
3. **The scope of "Hinglish" is asserted, not characterised.** One register, produced by one generator model, audited by two others. There is no native-speaker validation that the Romanized Hindi is natural, no register or dialect analysis, no measure of code-switch depth. For a paper whose entire independent variable is a language register, this is the gap I feel most. The generator instruction reportedly asks for WhatsApp-style Hinglish; whether it delivered it is unverified.
4. **No human validation yet.** This is honestly disclosed, and I respect that the authors report no result rather than a weak one. But it means the central measurement rests on LLM judges throughout, and the one judge-free check is a length heuristic. For Romanized Hindi specifically, where I would expect automated judges to be least reliable, this matters more than it would in English.
5. **The "independent" cross-judge is GPT-5 Mini, which was also the secondary certification auditor for every pair in the bank.** So the model that decided which pairs were valid also re-scored the responses. That is not the independence the correlated-error concern called for.
6. **Only 12.9% vs 30.9% score-3 rates between judges** is a large calibration divergence, and it lands on exactly the "critical" category the paper uses for its most serious claims. The paper acknowledges this; I want it acknowledged harder.
7. Four harm categories and three strategies is narrow, though honestly stated as such.

**Questions.**
- Was the Romanized Hindi validated by native speakers? What is the code-switching ratio, and does it vary across categories or strategies?
- How much of the effect is the *Hinglish register* versus generic out-of-distribution input? The unusual-English control described in the limitations is the experiment I most want to see.
- Why is the model that certified the bank also the independent judge?
- How do you reconcile your direction of effect with IndicJR's?
- Would the ordering hold on instruction-tuned models with explicit multilingual safety training?

**Scores.** Soundness 3 · Excitement 4 · **Overall 3 → weak accept, conditional.** The instrument is good and the heterogeneity result is worth publishing. But the related work must be brought current, the novelty claim narrowed accordingly, and either the human validation or the OOD control delivered. Excitement is above average because I think the model-dependence finding will be cited; soundness is held down by the single-register, LLM-judged, no-human-validation chain.

---

## Consensus view

| | A (methodology) | B (statistics) | C (multilingual safety) |
|---|---|---|---|
| Soundness | 3 | 3 | 3 |
| Excitement | 3 | 3 | 4 |
| **Overall** | **2.5 reject** | **3 borderline** | **3 weak accept** |

**Where all three converge:**
- The Qwen result is large, well controlled, and believable. Nobody attacks it.
- The scope discipline and the decision to report no human result are noticed and credited by all three.
- The GEPA discrepancy (A), the reproducibility gating (B), and the missing related work (C) are three different reviewers finding three different symptoms of the same underlying problem: **the paper's supporting apparatus has not been audited as carefully as its core measurement.**
- Nobody asks for a new experiment as a *condition* of acceptance. Every blocking objection is a documentation, framing, or offline-analysis fix.

**Predicted outcome as submitted:** scores of roughly 2.5 / 3 / 3 — below the bar at a top-tier main conference, plausibly above it at a strong workshop or Findings.

**Predicted outcome after the free fixes** (correct the GEPA description, commit the real generator artifact, rename the refusal construct, decompose Phase C, soften the three-regime claim, add the cluster and truncation sensitivities, bring the related work current, report Bowker and per-cell agreement): Reviewer A moves to 3.5 (their objections are all addressed), B to 3.5–4 (their asks are exactly these analyses), C stays at 3 pending human validation or the OOD control. **That is an accept-range paper.**

The single highest-leverage action is the smallest: fixing the GEPA description and committing the correct artifact. It is what turns Reviewer A from a reject into a supporter, and it costs a paragraph and a `.gitignore` line.
