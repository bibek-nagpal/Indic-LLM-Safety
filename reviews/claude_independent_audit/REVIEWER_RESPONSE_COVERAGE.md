# Reviewer-Response Coverage Audit

Independent re-adjudication of `docs/REVIEWER_ACTION_MATRIX.md` against the manuscript and the primary repository evidence. The matrix's own status is in the second column; my verdict is in the third. Disagreements are flagged.

Original reviewer scores: R1 = 4, R2 = 2, R3 = 2.

| # | Requested action | Matrix status | **My verdict** | Basis |
|---|---|---|---|---|
| 1 | Define the attack strategies precisely, especially role prompting | Addressed | **Resolved** | §4.2 gives binding structural definitions enforced by `equivalence.py` strategy-structure checks; Appendix A restates the contract. `Logical Appeal` is fully purged. Agreed. |
| 2 | Clarify whether the bank is target-conditioned | Addressed | **Resolved, and under-evidenced** | `target_models_used_during_generation: []`, `gepa_target_signal_used: false`, and — stronger than the paper cites — all 30 development-set records carry `target_model_called: false`. The paper should cite the record-level field. |
| 3 | Explain GEPA scoring and weights | Addressed | **NOT RESOLVED — regressed** | The obsolete weighted objective was correctly removed, but the replacement description is also unsupported. The frozen GEPA state has one program candidate with no parent, a null Pareto summary, one reflection call, 24 evaluations, $0.0302 spend. No optimisation occurred. The matrix records this as closed; it is the most falsifiable claim in the paper. See `METHODOLOGY_AUDIT.md` §3. |
| 4 | Specify auditor independence and hard gates | Addressed | **Resolved, with a correct caveat** | §4.3 and Appendix A are accurate and the cascade limitation is conceded. Worth adding: the two auditors' descriptive scores correlate at −0.028 on the accepted set, so no inter-auditor reliability is estimable at all. |
| 5 | Add human validation of the LLM judge, enlarged to ~10% | Prepared; labels pending | **PARTIALLY PREPARED — commitment reduced without disclosure** | R1 asked for ~10%; `PROJECT_HANDOFF_AND_PLAN.md` §E1 and §14 promise 180 pair-model jobs / 360 responses (11.9%). Delivered: 90 jobs / 180 responses = **5.95%**. The matrix, README, manifest, and §5.5 all foreground "180 response items," which is true and simultaneously the framing under which a halved study reads as the promised one. See `PHASE_E_AUDIT.md` E-1. |
| 6 | Define semantic/direct refusal and flip outcomes before analysis | Addressed | **Resolved in structure, flawed in labelling** | §3 defines everything before use — genuinely good. But "refusal" is the wrong name for 1[s=0]: none of Qwen's 115 RH score-0 responses is short and 114 exceed 500 characters. The reviewer asked for definitional clarity and got a precise definition under a misleading name. |
| 7 | Use the pair, not individual responses, as the experimental unit | Addressed | **Resolved as asked; incomplete as needed** | Pair-ID clustering is correctly implemented everywhere. But pairs are not independent: exact-string dedup only, 141 within-cell prompt pairs above Jaccard 0.62, max 0.921. The reviewer's specific request is met; the underlying independence assumption is not established. |
| 8 | Strengthen reproducibility | Addressed | **PARTIALLY RESOLVED** | Hashes, seeds, slugs, settings, provenance, and scripts are all present and of high quality. But `.gitignore` excludes the bank, the target run, and all probe banks, and the committed GEPA directory is the wrong one — so `run_bank` cannot execute from the release and no Phase A–C number is externally regenerable. A reproducibility-minded reviewer will try and fail. |
| 9 | Add a judge-independent check | Addressed | **PARTIALLY RESOLVED** | Phase C is genuinely judge-free and prespecified. But 32%/37%/48% of the directional shapes come from pairs the judge scored 0 in both languages, so it substantially measures verbosity. It is judge-independent; it is not independent evidence of a safety difference. See `STATISTICAL_AUDIT.md` §4. |
| 10 | Replace or cross-check the Gemini response judge | Addressed within budget | **PARTIALLY RESOLVED** | 1,944 responses were completely re-judged with hash-locked provenance — real work, honestly bounded. Two gaps: GPT-5 Mini was also the secondary certification auditor and the fallback primary judge, so it is not family-independent of the bank; and the judge message carries `PROMPT LANGUAGE: en|rh`, which the replay reproduces, so the cross-judge cannot detect language-conditioned leniency. R3's correlated-error concern is reduced, not retired. |
| 11 | Position the work against current safety benchmarks | Addressed | **NOT RESOLVED** | Table 1 is well built, but the bibliography has eleven entries (two of them tooling) and omits the two closest works: Banerjee et al. 2025 (matched English/code-mixed pairs, ten languages, human-validated) and Aswal & Jaiswal 2025 (Hinglish red-teaming), plus Yong et al. 2023. IndicJR is cited but its finding — that romanization *reduces* JSR — is not engaged. See `RELATED_WORK_AUDIT.md`. |
| 12 | Narrow the scope of the title and claims | Addressed | **Resolved** | Consistently disciplined: one register, three models, four categories, synthetic distribution, no prevalence claim. The best-executed item in the matrix. One residual over-reach — "three distinct regimes" — is inferential rather than scope-related (see #15). |
| 13 | Add an unusual-English OOD control | Deferred | **Correctly deferred, and now more necessary** | Honestly marked unrun. The audit raises its value: with Phase C confounded and the judge non-blind, this is the only remaining instrument that separates register from distribution shift. See `G_H_RECOMMENDATION.md`. |
| 14 | Add a certification ablation or estimate selectivity | Not currently identifiable | **Correct on the ablation; over-pessimistic on selectivity** | The six-record `attempts.jsonl` genuinely cannot reconstruct the funnel. But the three uncommitted V2 GEPA `metric_log.jsonl` files hold 92 audited candidates with per-constraint failure reasons and an 80% primary-acceptance rate under the frozen objective — a labelled, partial selectivity statement is available at zero cost. |
| 15 | *(not in the matrix)* R2's "is this just generic OOD transfer?" | — | **STILL EXPOSED** | The matrix folds this into row 13, but it is the objection that drove R2's score of 2. Nothing in the current manuscript answers it: certification controls the nine audited axes, not distance from the training distribution. Model heterogeneity is suggestive, not decisive. |
| 16 | *(not in the matrix)* R3's correlated-error concern across pipeline stages | — | **PARTIALLY EXPOSED** | Generation is Gemini, primary judging is Gemini; auditing is DeepSeek + GPT-5 Mini; the cross-judge is GPT-5 Mini. The revision breaks the single-family pipeline but substitutes an auditor/judge overlap. A genuinely uninvolved family (the deferred Claude judge) would close it. |
| 17 | Expand languages and target models | Future work | **Correctly deferred** | Explicit in Limitations. Agreed; breadth is not what this paper needs. |

---

## Summary

| Verdict | Count | Rows |
|---|---:|---|
| Genuinely resolved | 5 | 1, 2, 4, 6\*, 12 |
| Partially resolved | 5 | 5, 7, 8, 9, 10 |
| Not resolved | 2 | 3, 11 |
| Correctly deferred | 3 | 13, 14\*, 17 |
| Still exposed, untracked | 2 | 15, 16 |

\* Row 6 is resolved structurally but mislabelled; row 14 is correct on the ablation and over-pessimistic on selectivity.

**The matrix is over-optimistic.** It records eleven rows as "Addressed"; on the evidence, five of those are partial and two (GEPA explanation, benchmark positioning) are not addressed at all. The matrix is also silent on two objections that drove the low scores — R2's OOD alternative and R3's residual family overlap — folding them into adjacent rows rather than tracking them.

**Recommended matrix revisions before resubmission:**
1. Row 3 → "Superseded description; requires correction" until P0-1/P0-2 land.
2. Row 5 → state the 5.95% coverage explicitly and either restore the promised size or record the reduction and its reason.
3. Row 8 → "Addressed for a snapshot holder; release is gated" and note the GEPA artifact fix.
4. Row 9 → "Addressed; corroborates directional flips, partly reflects verbosity."
5. Row 10 → "Addressed within budget; cross-judge shares a family with the secondary auditor and inherits the language cue."
6. Row 11 → "Not yet addressed; bibliography requires three additions and a direction-of-effect discussion."
7. Add explicit rows for the OOD alternative (#15) and the residual auditor/judge overlap (#16), each with its own boundary statement.

**On resubmission dynamics:** R1 (score 4) is largely satisfied on rows 1, 2, 4, 6, 12 and will care most about row 5's halved human study. R3 (score 2) will re-raise row 10's family overlap and row 11's positioning. R2 (score 2) is the hardest: their central objection (#15) is untouched, and only Phase G can move it. The free fixes in `PROPOSED_PATCHES.md` should move R1 and R3; R2 realistically requires the OOD control.
