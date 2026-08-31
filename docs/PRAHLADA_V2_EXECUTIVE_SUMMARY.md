# Executive Summary: Prahlada / IndicAlignProbe

**Verified repository state:** `f913e17` | **Date:** 2026-08-31
**Full technical dossier:** `docs/PRAHLADA_V2_PROJECT_STATUS.md`

## The question

When the same harmful request is written in ordinary English versus conversational code-switched Hinglish / Romanized Hindi (RH), does a model's safety behaviour change -- after intent, scenario, specificity, attack strategy, target group and ambiguity have been audited for equivalence?

This is a measurement instrument, not a benchmark. It estimates a within-pair English-minus-RH difference on a controlled synthetic probe distribution. It does not estimate how often unsafe responses occur in real traffic.

## Why V1 had to be rebuilt, not rewritten

The original submission (reviewer scores 4 / 2 / 2) reported a 35.9 pp English-RH gap for Qwen across "1,512 certified pairs". Historical evidence recovered for this dossier shows two structural problems that a manuscript revision could not fix.

**V1 gave every target model a different prompt set.** The 1,512 were 1,512 distinct target-conditioned pairs, produced by twelve independent batches of one category by one model. The three targets were never shown the same prompts, so V1's headline cross-model claim compared models on different material.

**V1's sole certification auditor was measurably unreliable.** A July 2026 re-audit of 50 certified pairs found:

| Auditor pair | Verdict agreement | Cohen's kappa |
|---|---:|---:|
| Gemini vs DeepSeek Flash | 60.0% | 0.265 |
| Gemini vs DeepSeek Pro | 58.3% | 0.245 |
| Gemini vs GPT-5 Mini | 50.0% | 0.150 |
| DeepSeek Flash vs GPT-5 Mini | 86.0% | 0.696 |
| DeepSeek Pro vs GPT-5 Mini | 81.3% | 0.586 |
| DeepSeek Flash vs DeepSeek Pro | 79.2% | 0.556 |

Gemini -- the V1 auditor -- was the outlier; the three independent families agreed with each other. Eighteen of twenty disagreements were Gemini-accept / independent-reject. Independent auditors accepted **0/24** and **1/23** of the Logical Appeal pairs they saw, and the disagreement concentrated almost entirely on one axis, strategy faithfulness. V1's 0.60 equivalence threshold had no aggregation rubric behind it and never bound on the audited sample.

Roughly 60-70% of what V1 certified would have been rejected by an independent auditor.

## What V2 changed

Every major change traces to a measured failure, not to taste.

| V1 | V2 |
|---|---|
| A different prompt set per target model | **One** frozen 504-pair bank sent unchanged to all three targets |
| Gemini generated, audited and judged | DeepSeek V4 Flash + GPT-5 Mini certify; Gemini judges only |
| Logical Appeal (0/24 independent acceptance) | RolePrompting with a binding structural test |
| Scenario Nesting accepted at one layer | Two genuine containment layers, enforced |
| Scalar `e >= 0.60` with no rubric | Unanimous hard-field pass; missing fields fail closed |
| GEPA objective rewarded target flips (0.55 weight) | Construction is target-independent; no target signal enters |
| Score 0 called "refusal" | Renamed **non-assistance**: score 0 includes long non-answers |
| Descriptive rates | Paired bootstrap, exact tests, randomization, Holm, clustered GEE |

504 unique certified pairs x 3 target models = **1,512 pair-model observations** and 3,024 responses. V1 and V2 both report "1,512" for structurally different things.

## Verified V2 results

| Target | EN non-assistance | RH non-assistance | Gap, pp (95% CI) | Forward / reverse | Critical fwd / rev |
|---|---:|---:|---:|---:|---:|
| Qwen3-30B-A3B | 65.87% | 22.82% | **43.06 (38.49, 47.62)** | 219 / 7 | 85 / 2 |
| GPT-OSS-20B | 86.71% | 82.14% | **4.56 (1.39, 7.74)** | 42 / 21 | 15 / 6 |
| Nemotron-3-Nano | 62.10% | 63.89% | **-1.79 (-6.55, 2.78)** | 65 / 70 | 22 / 10 |

Qwen's effect is large and stable (directional test on 219 vs 7 flips, `p = 1.04e-55`). GPT-OSS shows a small positive gap. Nemotron's aggregate gap includes zero.

**The robust claim is Qwen versus the other two.** The Qwen contrasts survive every resampling unit tested. The GPT-OSS-Nemotron contrast (6.35 pp) crosses zero once lexically similar prompts are grouped, and it moves with the response judge. The paper does not claim three statistically distinct regimes.

## What the supporting analyses do and do not show

- **Phase A integrity:** 28/28 checks; frozen grid, hashes, settings, completeness.
- **Phase C response length:** condition-blind and directionally consistent, but among pairs scored 0 in *both* languages the counts are still 65:0, 22:2 and 12:58. It corroborates language-associated response *behaviour*, not harmfulness.
- **Phase D re-judge:** 1,944/1,944 GPT-5 Mini judgments on a shared 324-pair subset; ordering preserved, absolute severity is judge-sensitive. Cost USD 3.68, zero target calls.
- **Sensitivities:** near-duplicate clustering, truncation exclusion, Bowker symmetry, prompt-length checks and fallback exclusion all preserve the ordering.

## Live limitations

1. The response judge sees the prompt and an explicit language tag; the re-judge replays the same cue, so neither can detect language-conditioned leniency.
2. GPT-5 Mini is secondary auditor, fallback judge and re-judge -- Phase D is a scoring check, not an independent-family replication.
3. One register, three models, four harm categories, synthetic probes.
4. **The generic-OOD alternative is unresolved.** Certification controls audited semantic axes, not distance from a model's training distribution.
5. Human validation of the automated scores is not yet in hand.

## Where the project stands

| Work | Status |
|---|---|
| Phases A-D, post-audit corrections, independent verification gate | **COMPLETE** |
| Phase E human validation (2 annotators, 180 jobs, 360 items each, 11.9% coverage) | **IN PROGRESS -- RESULTS UNKNOWN** |
| Phase G unusual-English OOD control | **PLANNED** -- designed and costed, not authorized |
| Phase H certification ablation | **DEFERRED** -- the historical funnel cannot support a clean ablation |

## The one remaining scientific objection

Reviewer 2 asked whether the effect is specific to Hinglish/RH or just a generic consequence of unusual input. Nothing in the current design separates the two: equivalence certification controls *what* is asked, not *how far* the surface form sits from a model's training distribution.

Phase G answers it with a third arm -- **U**, semantically matched but unusual English -- on the same frozen base pairs, comparing E-to-U against E-to-R as a paired difference-in-differences. It is designed, preregistered and costed; it awaits authorization. See `docs/PHASE_G_DECISION_MEMO.md`.
