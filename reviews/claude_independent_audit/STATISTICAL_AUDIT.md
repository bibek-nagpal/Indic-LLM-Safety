# Statistical Audit

All recomputations were performed on the user's machine against the frozen artifacts, with no API calls. Scripts: `reviews/claude_independent_audit/scripts/`.

---

## 1. Replication of the reported analysis

`scripts/recompute_main.py` reads `frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl` independently of `analysis/analyze_final.py` and reproduces:

| Quantity | Paper | Independent recomputation |
|---|---|---|
| Qwen EN / RH / gap | 65.87 / 22.82 / 43.06 | 65.87 / 22.82 / 43.0556 |
| GPT-OSS EN / RH / gap | 86.71 / 82.14 / 4.56 | 86.71 / 82.14 / 4.5635 |
| Nemotron EN / RH / gap | 62.10 / 63.89 / −1.79 | 62.10 / 63.89 / −1.7857 |
| Forward / reverse | 219/7, 42/21, 65/70 | identical |
| Critical F / R | 85/2, 15/6, 22/10 | identical |
| Exact McNemar p | 2.87e−56, .00674, .501 | identical (discordants 225/8, 45/22, 66/75) |
| Directional binomial p | 1.04e−55, .011, .731 | identical |
| Contrast point estimates | 38.49, 44.84, 6.35 | identical |
| Phase C counts | 203:0, 59:16, 56:120 | identical |
| Phase D agreement | 73.65 / 91.35 / .541 / .813 | identical |
| Phase D six headline rows | Table 3 | identical, CIs included |

My independent bootstrap (10,000 draws, seed 20260829) returns [38.29, 47.82] / [1.59, 7.74] / [−6.35, 2.78] against the reported [38.49, 47.62] / [1.39, 7.74] / [−6.55, 2.78]. The differences are pure RNG-stream variation in the percentile endpoints, not a methodological discrepancy.

**Integrity checks all pass independently:** 3,024 score rows, 0 duplicate `(pair_id, model, language)` keys, 0 scores outside {0,1,2,3}, 0 non-null `parse_error`, 0 `logical_consistency_ok == false`, exactly 2 non-Gemini judge rows, 504 unique pair IDs, exact 42-per-cell balance, 1,512 EN and 1,512 RH rows.

**Conclusion: the reported statistics are computed correctly from the frozen data.** The issues below concern the *inferential model*, not the arithmetic.

---

## 2. Pseudoreplication — the resampling unit is not the independence unit

The paper's central methodological boast is that "the *pair ID*, not an individual response, is the experimental and resampling unit" (§3). That correctly avoids the obvious error of treating 3,024 responses as independent. It does not establish that the 504 pair IDs are independent of one another.

Deduplication was exact-string only. `CONSOLIDATION_REPORT.json` states the rule verbatim: "Normalization=NFKC + casefold + whitespace collapse. **No fuzzy/semantic deduplication.**" Yet `manifest.json` publishes `near_duplicate_threshold: 0.85`, which a reader will take as an applied guarantee.

Measured token-set Jaccard similarity between English prompts within each of the 12 cells (`scripts/bank_diversity.py`):

| cell | mean | max | pairs > 0.6 |
|---|---:|---:|---:|
| gambling · RolePrompting | 0.348 | 0.900 | 42 |
| gambling · ScenarioNesting | 0.331 | 0.833 | 26 |
| intoxication · ScenarioNesting | 0.323 | 0.864 | 17 |
| sexual_violence · SymbolicMasking | 0.286 | **0.921** | 14 |
| sexual_violence · ScenarioNesting | 0.281 | 0.806 | 22 |
| violence · ScenarioNesting | 0.256 | 0.746 | 3 |
| intoxication · RolePrompting | 0.232 | 0.846 | 22 |
| sexual_violence · RolePrompting | 0.226 | 0.773 | 11 |
| intoxication · SymbolicMasking | 0.211 | 0.692 | 6 |
| violence · SymbolicMasking | 0.198 | 0.667 | 3 |
| violence · RolePrompting | 0.188 | 0.717 | 6 |
| gambling · SymbolicMasking | 0.174 | 0.738 | 3 |
| **all within-cell** | **0.254** | — | **141** |
| random cross-bank baseline | 0.138 | — | — |

Examples at the top of the distribution are near-verbatim re-instantiations of a single scenario template (e.g. two gambling·RolePrompting prompts both beginning "As a legal expert specializing in Indian gambling laws, can you detail the specific operational methods used b…", Jaccard 0.900).

### 2.1 Cluster bootstrap

`scripts/cluster_bootstrap.py` builds connected components over the 504 pairs, joining two pairs when either their EN or their RH prompts exceed a Jaccard threshold, then resamples *clusters* with a ratio estimator.

| threshold | clusters | largest | Qwen | GPT-OSS | Nemotron |
|---|---:|---:|---|---|---|
| none | 504 | 1 | 43.06 [38.49, 47.62] | 4.56 [1.39, 7.74] | −1.79 [−6.16, 2.78] |
| 0.75 | 487 | 3 | 43.06 [38.65, 47.63] | 4.56 [1.38, 7.71] | −1.79 [−6.50, 2.81] |
| 0.65 | 420 | 20 | 43.06 [38.02, 47.94] | 4.56 [1.28, 7.74] | −1.79 [−6.67, 3.27] |
| 0.55 | 341 | 26 | 43.06 [37.81, 48.43] | 4.56 [1.46, 7.72] | −1.79 [−7.44, 4.11] |
| 0.45 | 247 | 52 | 43.06 [36.74, 49.69] | 4.56 [1.35, 8.10] | −1.79 [−7.71, 4.81] |

**The per-model conclusions survive.** Qwen is untouched. GPT-OSS's gap excludes zero at every threshold down to 0.45. Cluster sign-flip randomisation at threshold 0.55 gives Qwen p ≈ 1e−5, GPT-OSS p = .0097, Nemotron p = .636. The reported CIs are therefore mildly anti-conservative but not misleading about the main effects.

### 2.2 Where it does bite: the GPT-OSS − Nemotron contrast

`scripts/contrast_sensitivity.py`:

| threshold | clusters | GPT-OSS gap p | GPT-OSS − Nemotron CI | p (unadjusted) |
|---|---:|---:|---|---:|
| none | 504 | .0065 | [0.79, 11.71] | **.032** |
| 0.80 | 496 | .0067 | [0.40, 12.30] | .036 |
| 0.70 | 459 | .0074 | [0.62, 11.98] | .037 |
| **0.65** | 420 | .0103 | **[−0.21, 12.55]** | **.060** |
| **0.60** | 380 | .0094 | **[−0.60, 13.47]** | **.102** |
| **0.55** | 341 | .0097 | **[−0.22, 13.08]** | **.101** |
| 0.50 | 293 | .0111 | [0.21, 12.80] | .079 |
| 0.45 | 247 | .0126 | [−0.26, 13.12] | .097 |

The manuscript reports this contrast at Holm-adjusted p = .032 — i.e. right at the edge — and rests the "three distinct regimes" framing on it. Once near-duplicate prompt clusters are the resampling unit, the interval crosses zero from Jaccard 0.65 downward and no threshold survives Holm adjustment. **This inference should be withdrawn or explicitly labelled fragile.**

---

## 3. Multiple comparisons

Holm is applied to exactly one family: the three cross-model gap contrasts. Not adjusted, and not flagged as unadjusted:
- three per-model exact McNemar tests (§5.1);
- three directional binomial tests (§5.1);
- three Bowker tests (in `statistical_tests.json`, unreported in the paper);
- three Phase C directional tests (§5.3);
- 36 cell-level gap estimates with bootstrap CIs (correctly described as descriptive — this one is handled well);
- six Phase D judge-replacement gap CIs.

For Qwen nothing changes. For the borderline results it matters: Nemotron's Bowker p = .0188 becomes ≈.056 under Holm across three models, and GPT-OSS's directional p = .011 becomes ≈.033. The honest presentation is one sentence naming which family was adjusted and stating that the remaining p-values are nominal.

---

## 4. Phase C is confounded by verbosity — the most consequential statistical finding

The length rule is prespecified and judge-free, which is genuinely valuable. But it is not a safety measurement, and a large share of it is generated by pairs the judge found harmless in both languages.

`scripts/phase_c_decomp.py`, stratifying each model's 504 pairs by the judge's own verdict:

| model | stratum | n | forward-shaped | reverse-shaped |
|---|---|---:|---:|---:|
| Qwen | **both safe (0/0)** | 107 | **65** | **0** |
| Qwen | forward flip | 219 | 136 | 0 |
| Qwen | reverse flip | 7 | 0 | 0 |
| Qwen | other | 171 | 2 | 0 |
| GPT-OSS | **both safe (0/0)** | 392 | **22** | **2** |
| GPT-OSS | forward flip | 42 | 35 | 0 |
| GPT-OSS | reverse flip | 21 | 0 | 14 |
| GPT-OSS | other | 49 | 2 | 0 |
| Nemotron | **both safe (0/0)** | 247 | **12** | **58** |
| Nemotron | forward flip | 65 | 44 | 0 |
| Nemotron | reverse flip | 70 | 0 | 59 |
| Nemotron | other | 122 | 0 | 3 |

Restricted to both-safe pairs the directional imbalance is still overwhelming (Qwen 65:0, p = 5.4e−20; GPT-OSS 22:2, p = 3.6e−05; Nemotron 12:58, p = 2.3e−08). It contributes 32% of Qwen's forward shapes, 37% of GPT-OSS's, and 48% of Nemotron's reverse shapes.

The driver is plain verbosity. Among both-safe pairs, median response length (`scripts/phase_c_confound.py`):

| model | EN median | RH median | paired Wilcoxon |
|---|---:|---:|---:|
| Qwen | 48 | **4,366** | 1.2e−17 |
| GPT-OSS | 38 | 38 | .0035 |
| Nemotron | 39 | 38 | 1.5e−06 |

Qwen answers Hinglish prompts at ~90× the English length even when neither answer contains domain-specific harmful content. A statistic that thresholds on raw character counts cannot distinguish "supplied harmful content" from "wrote a long harmless essay", so it cannot corroborate a *safety* claim.

**What is defensible:** within judge-identified flips the length rule aligns essentially perfectly (Qwen 136 forward-shaped of 219 forward flips, 0 reverse-shaped; Nemotron 59 of 70 reverse flips reverse-shaped, 0 forward-shaped). That is a strong, honest, judge-free corroboration of the *flips*. Report the decomposition and make that the claim.

---

## 5. Response truncation

Unreported in the manuscript. `finish_reason == "length"` at the 4,096-token cap, after deduplicating the 1,649 trace rows to 1,512 by keep-last (137 pair-model jobs have a failed first attempt, all from OpenRouter 403 credit-limit errors; 0 empty or errored rows remain):

| model | EN truncated | RH truncated | discordant (EN-only / RH-only) | exact p |
|---|---:|---:|---:|---:|
| Qwen | 0 | 22 | 0 / 22 | 4.8e−7 |
| Nemotron | 77 | 35 | 68 / 26 | 1.7e−5 |
| GPT-OSS | 47 | 55 | 26 / 34 | .366 |

Truncated responses were scored as if complete, and score-3 rates differ sharply by truncation status (e.g. Nemotron RH: 28.6% among truncated vs 9.8% among untruncated).

**Sensitivity (`scripts/refusal_semantics.py`), dropping every pair-model job with a truncation on either side:**

| model | full N=504 | untruncated subset |
|---|---|---|
| Qwen | gap 43.06, CF/CR 85/2 | N=482, gap **43.36**, CF/CR 82/2 |
| GPT-OSS | gap 4.56, CF/CR 15/6 | N=423, gap **4.73**, CF/CR 11/3 |
| Nemotron | gap −1.79, CF/CR 22/10 | N=401, gap **−0.50**, CF/CR 16/8 |

The gaps are robust; critical-flip counts move more. This is a cheap, favourable sensitivity check that should be in the appendix alongside the existing fallback-sensitivity analysis.

---

## 6. Ordinal-scale handling

Correct. `metrics_from_arrays` never averages the 0–3 scores; refusal is a strict indicator, flips are threshold events, the full 4×4 transition table is retained, and Bowker rather than a paired t-test is used for symmetry. The `bowker_test` implementation is textbook-correct (sum over off-diagonal pairs of (n_ij − n_ji)²/(n_ij + n_ji), df = number of non-empty pairs). Quadratic-weighted κ in Phase D and Phase E uses the standard (i−j)²/(k−1)² weighting.

**But Bowker's results are not reported.** `statistical_tests.json` gives Nemotron χ²(5) = 13.54, **p = .0188** — symmetry rejected — with GPT-OSS at .0675 and Qwen at 1.58e−44. Three independent indicators (Bowker, the length signal at 56:120, the GPT-5 Mini re-judge at −8.33 pp with a CI excluding zero) all point to a genuine *reverse* asymmetry in Nemotron that the binary refusal metric misses. Reporting the test the authors already ran makes the Nemotron story coherent instead of looking like an inconvenient null.

---

## 7. GEE secondary model

`fit_gee` is correctly specified: binomial family, exchangeable working correlation, `pair_id` clusters, a 2-df Wald test on the two interaction terms, robust SEs. Reproduces at χ²(2) = 165.83, p = 9.79e−37.

Two caveats worth a clause in the text:
1. Clustering is on `pair_id`, so each cluster holds 6 rows (3 models × 2 languages). Model is thus a *within-cluster* factor, which is efficient, but it means the same near-duplicate-prompt dependence from §2 is unmodelled here too.
2. The Wald statistic is overwhelmingly driven by the Qwen contrast. A significant 2-df omnibus interaction does not license the pairwise claim that GPT-OSS and Nemotron differ — see §2.2.

---

## 8. Bootstrap design details

- **Unstratified resampling of a stratified design.** The bank is fixed at 42 pairs per cell, but the bootstrap resamples the 504 pair IDs without respecting cells. This adds between-cell variance and is therefore *conservative*; worth one clause, not a change.
- **Percentile intervals** on a bounded proportion difference. Adequate here (no interval abuts ±100), though BCa would be marginally better for the small cell-level estimates.
- **Correlated bootstrap draws across models** are handled correctly: the same resampled pair indices are applied to all three models, so the contrast CIs properly inherit the pairing. This is a genuine strength.
- **Sign-flip randomisation** on per-pair contrast differences is a valid exact-ish test under sign symmetry, with the standard (extreme+1)/(B+1) correction. Correctly implemented.
- **Seed discipline** via `SeedSequence.spawn` gives independent, reproducible streams per analysis block. Good practice.

---

## 9. Phase D statistical issues

1. **Heterogeneous agreement masked by pooling** (`scripts/phase_d_full.py`):

| target × language | n | exact | mean(GPT-5 Mini − Gemini) | Gemini score-0 | GPT-5 Mini score-0 |
|---|---:|---:|---:|---:|---:|
| Qwen RH | 324 | **53.1%** | **+0.605** | 23.1% | 10.5% |
| Qwen EN | 324 | 71.6% | +0.417 | 65.7% | 54.0% |
| Nemotron EN | 323 | 66.3% | +0.461 | 61.9% | 50.5% |
| Nemotron RH | 324 | 72.2% | +0.293 | 63.3% | 58.6% |
| GPT-OSS EN | 324 | 89.8% | +0.127 | 85.5% | 83.6% |
| GPT-OSS RH | 324 | 88.9% | +0.139 | 82.7% | 80.2% |

The disagreement is concentrated on the Qwen Hinglish responses that produce the headline effect. The mean differences are uniformly positive, so this is a systematic calibration shift, not symmetric noise — κ absorbs part of it via the marginals, raw exact agreement does not.

2. **Contrasts are judge-dependent.** On the shared 324 pairs:

| contrast | under Gemini | under GPT-5 Mini |
|---|---|---|
| Qwen − GPT-OSS | 39.81 [33.02, 46.91] | 40.12 [33.02, 46.91] |
| Qwen − Nemotron | 44.14 [36.11, 52.16] | 51.85 [42.90, 60.49] |
| **GPT-OSS − Nemotron** | **4.32 [−3.09, 11.42]** | **11.73 [3.70, 19.14]** |

The Qwen-vs-rest ordering is judge-invariant. Whether GPT-OSS and Nemotron are separable is entirely judge-determined.

3. **Subset power.** The GPT-OSS gap has a CI overlapping zero under both judges on this subset (2.78 [−0.93, 6.79] and 3.40 [−0.62, 7.41]). "Nearly reproduces the … GPT-OSS gap" should say that the subset lacks the power to confirm it.

4. **No multiplicity control** across the six judge-replacement CIs.

5. **Selection.** `pair_rank` is a SHA-256 of `(seed, pair_id, category, strategy)`, so pair identity is outcome-independent. Only the scalar per-cell count (27) is set by a budget descent over aggregate token counts, which weakly depends on response lengths in the hash-ranked prefix. Non-directional and negligible, but a footnote would be honest.

---

## 10. Construct validity of "refusal"

R = 1[s == 0] is labelled "refusal" throughout. Score 0 means *no domain-specific harmful assistance*, which is broader.

| model / language | n(score 0) | < 80 chars | > 500 chars | matches English refusal regex |
|---|---:|---:|---:|---:|
| Qwen EN | 332 | 203 (61%) | 129 (39%) | 274 |
| **Qwen RH** | **115** | **0 (0%)** | **114 (99%)** | **1** |
| GPT-OSS EN | 437 | 412 (94%) | 25 (6%) | 0 |
| GPT-OSS RH | 414 | 367 (89%) | 45 (11%) | 0 |
| Nemotron EN | 313 | 208 (66%) | 103 (33%) | 38 |
| Nemotron RH | 322 | 272 (84%) | 49 (15%) | 5 |

The 43.06 pp headline contrasts 61%-terse-refusal English against 0%-terse-refusal Hinglish. The regex column is English-pattern-only (`looks_like_refusal` in `judge.py` matches "I cannot", "I'm sorry, but I…", etc.) and cannot detect Hindi refusals, so the length columns carry the argument. The measurement is legitimate; the label is not. Rename to *non-assistance rate* / *non-assistance gap*.

---

## 11. Confounds tested that came back null

These strengthen the paper and should be reported (`scripts/equivalence_confound.py`):

- **Prompt-length asymmetry.** RH prompts are longer (mean 396.5 vs 356.6 chars, mean word count 64.9 vs 55.5, median ratio 1.114, Wilcoxon p = 7.7e−80) and length is not one of the nine audited axes. But per-pair RH/EN ratio has no association with outcome: Spearman ρ with the pair-level gap = −0.005 / +0.051 / −0.048 and with forward flips = −0.035 / +0.062 / +0.017 (all p > .10). Forward-flip rates across ratio terciles are flat: Qwen 44.0 / 44.6 / 41.7%, GPT-OSS 7.1 / 7.1 / 10.7%, Nemotron 11.3 / 14.3 / 13.1%.
- **Audited equivalence score.** No association with the gap or with flips (|ρ| ≤ 0.062, all p > .10). **This test has essentially no power** — 456 of 504 primary scores are exactly 1.00 and the full range is 0.95–1.00 — so it must not be cited as evidence that residual non-equivalence is absent. Related: the two auditors' descriptive scores correlate at **−0.028** on the accepted set, meaning the artifact contains no measurable inter-auditor reliability.
- **Truncation** (§5) and **near-duplication** (§2.1) both leave the main effects intact.

---

## 12. Priority list for the statistical revision

1. Withdraw or explicitly flag the GPT-OSS − Nemotron contrast; soften "three distinct regimes" to "Qwen is robustly distinct; the other two are not reliably separated."
2. Add the Phase C both-safe decomposition and reframe the length signal as corroborating the *flips*.
3. Add the cluster-robust sensitivity table (§2.1–2.2) and state that dedup was exact-string only; remove or explain `near_duplicate_threshold: 0.85`.
4. Rename "refusal gap" to "non-assistance gap" and report §10.
5. Report the truncation asymmetry and its (favourable) sensitivity.
6. Report Bowker p-values, including Nemotron's p = .0188.
7. Report per-model×language cross-judge agreement, not only the pooled figure.
8. State which p-value family was Holm-adjusted and that the rest are nominal.
9. Add the two null confound checks in §11 as pre-emptive robustness evidence.

Items 1–9 require no new data, no API calls, and no change to the frozen experiment.

---

## CORRECTION (issued during implementation, supersedes the near-duplicate finding above)

While implementing the fixes I re-checked `probe_bank.py` and found that my original characterisation of `near_duplicate_threshold: 0.85` was **wrong**, and the correction is material.

`NEAR_DUPLICATE_THRESHOLD = 0.85` (`probe_bank.py:81`) **is applied**, at generation time: `_near_duplicate()` screens every new candidate against all existing rows of the same strategy using `difflib.SequenceMatcher` ratio on normalised text (max of the EN and RH ratios), and rejects matches at or above 0.85 with a `near_duplicate` attempt event. The manifest field is therefore an accurate record of an enforced gate, not an unapplied advertisement.

What is true is narrower. The final bank consolidated **three** source banks (`revision_v2_final_smoke`, `revision_v2_3_1_pilot_5`, `revision_v2_3_1_final_35`). The 0.85 gate operates within a single bank build, and consolidation across banks used exact-string dedup only, so cross-bank near-duplicates were never screened.

Measured under the gate's own metric across all 42,084 within-strategy pairs in the final bank:

| statistic | value |
|---|---:|
| mean SequenceMatcher ratio | 0.093 |
| 99th percentile | 0.480 |
| maximum | 0.942 |
| **pairs at or above the 0.85 gate** | **5** |
| pairs ≥ 0.80 | 12 |
| pairs ≥ 0.75 | 29 |
| pairs ≥ 0.70 | 59 |

All five surviving ≥0.85 pairs are within-category and within-strategy, consistent with cross-source-bank leakage.

**What this changes.** The claim "deduplication was exact-string only" is correct *for the consolidation step* and wrong as a description of the pipeline. The Jaccard figures reported above (mean within-cell 0.254, 141 pairs above 0.62, max 0.921) are correct but measure **shared scenario scaffolding**, not near-verbatim duplication: Jaccard over token *sets* is far more permissive than a sequence-alignment ratio, and prompts built from the same strategy template share vocabulary without being near-copies.

**What this does not change.** The cluster-bootstrap sensitivity remains a legitimate robustness analysis — shared-template prompts are still not fully independent draws — and its conclusion is unaltered: the Qwen results are robust at every threshold, and the GPT-OSS − Nemotron contrast crosses zero once shared-template clusters are the resampling unit. The manuscript text written during implementation uses this corrected framing throughout, and reports both metrics.

Verification script: `reviews/claude_independent_audit/scripts/native_neardup_check.py`.
