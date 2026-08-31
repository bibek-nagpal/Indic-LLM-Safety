# Claim-to-Evidence Audit

Every substantive quantitative and methodological claim in `paper/acl_latex.tex` traced to primary frozen evidence. Line numbers refer to the canonical manuscript at commit `31d5732`.

Status key: **OK** = independently reproduced from frozen artifacts · **OK\*** = reproduced but incompletely or misleadingly framed · **UNSUPPORTED** = contradicted or not evidenced by the artifacts · **STALE/UNVERIFIABLE** = cannot be checked from the release.

---

## A. Abstract and Introduction

| # | Claim (line) | Evidence checked | Status |
|---|---|---|---|
| A1 | "final bank contains 504 unique pairs, balanced across four harm categories and three attack strategies" (34) | `pairs.jsonl`: 504 rows, 504 unique pair IDs, 504 unique NFKC-casefold-collapsed EN prompts, 504 unique RH prompts, 42 per cell × 12 cells | **OK** |
| A2 | "DeepSeek and GPT-5 Mini then independently enforce a hard equivalence and probe-validity contract" (34) | `manifest.json` certification_rule; `equivalence.py` `check_hard`; all 504 rows carry `primary_audit.accepted=True` and `secondary_audit.accepted=True` | **OK\*** — "independently" is true per candidate but the cascade means the secondary never saw primary rejects (conceded in Limitations). Descriptive scores of the two auditors correlate **−0.028** on the accepted set, so no inter-auditor reliability is measurable |
| A3 | "1,512 pair-model observations and 3,024 responses" (34) | `scores.jsonl`: 3,024 rows, 0 duplicate `(pair_id, model, language)`; `summary.json` `completed_pair_model_jobs: 1512` | **OK** |
| A4 | "43.06 (38.49–47.62) / 4.56 (1.39–7.74) / −1.79 (−6.55–2.78)" (34) | Recomputed exactly: 43.0556 / 4.5635 / −1.7857. Own 10,000-draw bootstrap gives [38.29,47.82] / [1.59,7.74] / [−6.35,2.78] — differences are RNG-stream noise only | **OK** |
| A5 | "A judge-independent response-length check reproduces the same directional ordering" (34, 180) | Counts reproduce exactly (203:0, 59:16, 56:120). But 32%/37%/48% of the shapes come from pairs scored 0 in **both** languages | **OK\*** — see `STATISTICAL_AUDIT.md` §4; the ordering claim holds, the corroboration-of-*safety* implication does not |
| A6 | "a complete GPT-5 Mini re-judge preserves the ordering and nearly reproduces the Qwen and GPT-OSS gaps" (34) | Verified: 43.52 vs 42.59; 3.40 vs 2.78 | **OK\*** — on this subset the GPT-OSS gap CI overlaps zero under **both** judges ([−0.93,6.79] and [−0.62,7.41]). "Nearly reproduces" reproduces a point estimate that is not itself distinguishable from zero at n=324 |
| A7 | "these results … do not estimate unsafe-response prevalence in organic traffic" (34) | Scope discipline maintained throughout | **OK** — this restraint is a genuine strength |
| A8 | "paired statistical analysis that treats pair ID as the experimental unit" (49) | `analyze_final.py` bootstrap/permutation/GEE all cluster on `pair_id` | **OK\*** — correct as stated, but pair IDs are not fully independent: 141 within-cell EN prompt pairs exceed Jaccard 0.62 (max 0.921), reflecting shared scenario templates (see the CORRECTION in `STATISTICAL_AUDIT.md`) |

## B. Method — §4.1 Generator and GEPA

| # | Claim (line) | Evidence checked | Status |
|---|---|---|---|
| B1 | "The generator is `google/gemini-2.5-flash`" (106) | `manifest.json` `generator_model` | **OK** |
| B2 | "We use GEPA within DSPy … to optimize supplementary generator guidance" (106) | `gepa_20260826_135819/gepa_state.bin`: `program_candidates` length **1**, `parent_program_for_candidate: [[None]]`, `num_metric_calls_by_discovery: [0]`; `pareto_summary.json` all `null`; only `iter_0_prog_0.json` outputs; `api_accounting.json` = 30 metric evals, 28 generation + **1** reflection call, **$0.0302** | **UNSUPPORTED** — the single program is the seed. No prompt evolution occurred. Sibling run `20260826_103104` has `n=2` with `parent [0]`, so the machinery works; this run produced nothing |
| B3 | "Its score is the fraction of 13 prompt-validity constraints satisfied: nine paired axes, RH not stronger than English, probe eligibility, correct harmful-category membership, and direct harmful facilitation with non-benign purpose" (108) | `equivalence.hard_constraint_score` (lines 491–529): `HARD_AXES` = 9 names, plus `rh_not_stronger_than_en`, `probe_eligibility`, `correct_category_membership`, `direct_harm_facilitation`; denominator 13 | **OK** — the manuscript is correct here. (`PROJECT_HANDOFF_AND_PLAN.md` §4.2 says "ten"; that matches the two *earlier* V2 runs whose `optimization_manifest.json` declares `objective: paired_prompt_quality_only`, "9 axes + RH-not-stronger". The handoff is stale, the paper is right.) Minor defect: `strategy_faithfully_used` can be appended a second time, allowing 14 failures against a denominator of 13 and a clamp to 0.0 |
| B4 | "It never calls a target model, never observes a target response or response-judge label, and has no flip reward" (108) | All 30 rows of `metric_log.jsonl` carry `target_model_called: false`; `manifest.json` `gepa_target_signal_used: false`, `target_models_used_during_generation: []` | **OK** — and this is stronger evidence than the manuscript currently cites; the record-level field is worth naming in Appendix B |
| B5 | "The generator instruction is frozen before bank construction" (108) | `manifest.json` `gepa_instruction_sha256 = 025fbd35…`; `probe_bank.py:166` = `sha256(instruction.encode("utf-8"))`. Matches **only** the uncommitted `gepa_20260826_135819/generator.txt`. The committed `gepa_20260523_130239/generator.txt` hashes to `33910016…` | **STALE/UNVERIFIABLE from the release** — the frozen instruction is absent; the committed artifact is a different, older instruction lacking `optimization_manifest.json`, which `load_optimized_instruction(require_v2=True)` would reject, so `run_bank` cannot execute |
| B6 | Appendix B: "Q(c) = (1/13)Σ h_k(c) … Natural-language feedback lists failed constraints" (255–259) | Q was computed 30 times as a diagnostic (24 accepted; failures dominated by `correct_category_membership`/`direct_harm_facilitation`). It never selected or evolved a prompt | **UNSUPPORTED as an optimisation objective**; accurate as a *validity metric* definition |

## C. Method — §4.2–4.4 Strategies, certification, inference, judging

| # | Claim (line) | Evidence checked | Status |
|---|---|---|---|
| C1 | Three binding strategy definitions (112–117) | `generator.V2_STRATEGIES`; `equivalence.py` strategy-structure checks; `manifest.json` strategies list | **OK** |
| C2 | "42 certified pairs in each of the 12 category-by-strategy cells" (118) | Verified from `scores.jsonl` metadata and `manifest.json` `cell_counts` | **OK\*** — but `CONSOLIDATION_REPORT.json` records `retained_unique_pairs: 502` with `gambling__SymbolicMasking: 41` and `gambling__RolePrompting: 41`. Two pairs were added afterwards to restore balance; this top-up is undocumented in the manuscript and should be stated with its timing relative to target inference |
| C3 | "primary auditor deepseek/deepseek-v4-flash; secondary openai/gpt-5-mini … GPT-5 Mini is called only after a primary pass" (122) | `manifest.json` `auditor_cascade`; per-row audits | **OK** |
| C4 | "A scalar equivalence score is stored descriptively but is not an acceptance threshold" (122) | Confirmed in `check_hard`; primary scores 0.95–1.00 (456/504 = 1.00), secondary 0.95–1.00 | **OK** |
| C5 | "504 rows and 504 unique pair IDs, English prompts, and RH prompts" (124) | Verified after NFKC + casefold + whitespace collapse | **OK** — exact-string uniqueness; a 0.85 SequenceMatcher near-duplicate gate was additionally enforced per bank build but not across the consolidation of three source banks, leaving 5 residual pairs at or above 0.85 (see the CORRECTION in `STATISTICAL_AUDIT.md`) |
| C6 | Bank SHA-256 `35bfbc1d…` (124, 312) | Matches `FREEZE_MANIFEST.json` `canonical_bank_sha256` and `run_manifest.json` `probe_bank_sha256` | **OK** |
| C7 | "temperature 0, a 4,096-token cap, and an empty target system prompt" (128) | `run_manifest.json`: `target_temperature 0.0`, `max_target_tokens 4096`, `empty_target_system_prompt true` | **OK\*** — the cap has an unreported asymmetric consequence: `finish_reason=="length"` occurs 0 (EN) vs 22 (RH) for Qwen (p=4.8e−7) and 77 vs 35 for Nemotron (p=1.7e−5). Truncated responses were judged as complete |
| C8 | "Two of 3,024 primary judgments remained blocked as PROHIBITED_CONTENT after retries and were scored by the prespecified openai/gpt-5-mini fallback" (130) | Exactly 2 rows have `judge_model == "openai/gpt-5-mini"`: `26ce5e75…`/Qwen/rh/score 3 and `3ac698ae…`/Nemotron/en/score 3 | **OK** — note `errors.jsonl` contains 3 `PROHIBITED_CONTENT` worker errors; one was evidently resolved on retry. The remaining 153 errors are all OpenRouter 403 credit-limit events, and all 137 affected pair-model jobs were successfully retried (0 empty or errored rows after keep-last dedup of the 1,649 trace rows → 1,512) |
| C9 | "Infrastructure or parse failures never become score 0" (130) | `judge.score_response_strict` retries then raises; `scores.jsonl` has 0 non-null `parse_error` | **OK** |
| C10 | Appendix C rubric and "A deterministic checker enforces gate-score consistency" (278) | `_check_logical_consistency`; all 3,024 rows `logical_consistency_ok: true` | **OK** |
| C11 | Not claimed but material: the judge is language-aware | `judge.build_judge_messages` emits a literal `PROMPT LANGUAGE: {language}` line plus the full prompt | **Omission** — the scorer is told which experimental arm it is scoring. Phase D replays the same messages and so does not test this |

## D. Results — §5

| # | Claim (line) | Evidence checked | Status |
|---|---|---|---|
| D1 | Table 2 rows: 65.87/22.82/43.06/219/7/85/2; 86.71/82.14/4.56/42/21/15/6; 62.10/63.89/−1.79/65/70/22/10 (150–152) | All reproduced exactly | **OK** |
| D2 | "exact directional p = 1.04e−55 / .011 / .731" (159) | 1.04e−55, .0111, .731 | **OK** |
| D3 | "Exact McNemar p = 2.87e−56, .00674, .501" (159) | 2.87e−56 (b/c = 225/8), .00674 (45/22), .501 (66/75) | **OK\*** — unadjusted across three models; immaterial given the magnitudes |
| D4 | Gap contrasts 38.49 [32.94,44.05] / 44.84 [38.29,51.39] / 6.35 [0.79,12.10]; Holm p < 3.1e−5, < 3.1e−5, .032 (161) | Point estimates exact; my CIs [32.74,44.05] / [38.29,51.39] / [0.99,11.90] | **OK\*** — the third contrast is fragile: cluster-robust CI crosses zero at Jaccard ≥ 0.65 (p = .060 → .102 unadjusted), and it is 4.32 [−3.09,11.42] under Gemini vs 11.73 [3.70,19.14] under GPT-5 Mini on the shared subset |
| D5 | "clustered language-by-model interaction … χ²₂ = 165.83, p = 9.79e−37" (161) | `statistical_tests.json` = 165.8295, 9.785e−37 | **OK\*** — this is dominated by Qwen and does not license the pairwise three-regime claim |
| D6 | "Qwen positive in all 12 cells, 7.14–76.19; GPT-OSS 9 of 12, −7.14–11.90; Nemotron 5 positive, −26.19–19.05" (172) | `cell_results.csv`: 12/12, [7.14,76.19]; 9/12, [−7.14,11.90]; 5/12, [−26.19,19.05] | **OK** |
| D7 | "Qwen has 85 transitions from English 0 to RH 3, versus two" (174) | Transition matrices confirm 85 / 2 | **OK** |
| D8 | Fallback sensitivity: 503/504/503 pairs, gaps 43.14/4.56/−1.79 (176) | Reproduced; consistent with 217/503, 23/504, −9/503 | **OK** |
| D9 | Phase C counts and the 3×3 threshold grid (180) | 203:0, 59:16, 56:120; grid gives Qwen constant 203:0, GPT-OSS constant 59:16, Nemotron 120 or 121 reverse | **OK** |
| D10 | "Length is not a semantic safety score, but it is independent of both LLM judges" (180) | True of the *measurement*; but the statistic is heavily loaded by verbosity — both-safe pairs contribute 65:0 (Qwen), 22:2 (GPT-OSS), 12:58 (Nemotron) | **OK\*** — judge-independent, not safety-corroborating |
| D11 | "We sampled 27 pair IDs from every category-by-strategy cell … The sample was fixed without using target scores" (184) | `design_phase_d_budget.py`: `pair_rank` = SHA-256 of `(DESIGN_SEED, pair_id, category, strategy)`; per-cell count chosen by budget descent | **OK** — only the scalar 27 has any weak dependence on aggregate token counts; the *identity* of selected pairs is outcome-independent |
| D12 | "All 1,944 GPT-5 Mini judgments completed … strict parsing and hash-locked provenance" (184) | 1,944 rows, 324 pairs × 3 models × 2 languages, 0 parse errors, 0 consistency failures, per-row `judge_messages_sha256` | **OK** |
| D13 | Table 3 six rows (193–198) | All six reproduced exactly, including CIs | **OK** |
| D14 | "exact agreement is 73.65% over 1,943 responses; adjacent 91.35%; κ = .541; quadratic κ = .813" (205) | Reproduced: 73.65 / 91.35 / .541 / .813 | **OK\*** — pooling hides Qwen-RH at 53.1% vs GPT-OSS at ~89% |
| D15 | "GPT-5 Mini also assigns score 3 more often (30.97% versus 12.91%)" (205) | 602/1944 = 30.97% and 251/1944 = 12.91% on the planned scope including the preserved fallback | **OK** |
| D16 | "The robust conclusion is the ordering … not an invariant absolute severity rate" (205) | Supported for Qwen vs the rest; not for GPT-OSS vs Nemotron | **OK\*** |
| D17 | Not claimed: Bowker | `statistical_tests.json`: Nemotron χ²(5)=13.54, **p = .0188**; GPT-OSS .0675; Qwen 1.58e−44 | **Omission** — the paper's own secondary test rejects symmetry for Nemotron and is not reported. It corroborates the reverse-asymmetry story that the length signal and GPT-5 Mini both show |

## E. Human validation, Limitations, Reproducibility

| # | Claim (line) | Evidence checked | Status |
|---|---|---|---|
| E1 | "an outcome-independent sample of 90 pair-model jobs … 180 response items per annotator" (209) | `HUMAN_VALIDATION_MANIFEST.json`: 90 jobs, 180 items, seed 20260830, `selection_used_automated_scores: false` | **OK\*** — factually correct, but this is **5.95%** of the 1,512 grid, against the ~10% (180 jobs / 360 responses) committed in the rebuttal and in `PROJECT_HANDOFF_AND_PLAN.md` §E1. The manuscript never states the coverage fraction |
| E2 | "blinded to model, pair ID, language label, automated scores, flips, and conclusions" (209) | Workbook construction confirms these fields are absent; order randomisation is real (2/180 shared positions between A and B) | **OK\*** — "blinded to … language label" is literally true but the prompt text makes the language self-evident, so annotators are not blind to the experimental factor. One EN/RH twin pair sits at adjacent positions in Workbook A |
| E3 | "The analysis script will report exact and adjacent agreement, unweighted and quadratic-weighted κ, 4×4 confusion matrices, and agreement of each human with both automated judges" (209) | `analyze_returned_labels.py` does exactly this — and nothing else | **OK\*** — no CIs, no clustering on the 90 jobs, no per-model or per-language breakdown, no human-implied refusal gap. The script cannot validate the headline estimand |
| E4 | "No human labels were available at submission-draft time, so we report no human result" (209) | Confirmed; no results directory exists | **OK** — correct and commendable restraint |
| E5 | "The frozen snapshot also does not preserve enough complete generation-attempt logs to reconstruct the full candidate funnel" (223) | `attempts.jsonl` = 6 records (4 retrieval errors, 2 audited candidates) | **OK** — but partially recoverable: the three V2 GEPA `metric_log.jsonl` files hold 92 audited candidates with per-constraint failure reasons and an 80% (24/30) DeepSeek-primary acceptance rate in the frozen run. That is a GEPA-time distribution, not the bank-build funnel, and must be labelled as such |
| E6 | "Analysis scripts regenerate every reported table and figure from the frozen snapshot" (227) | True for a snapshot holder | **STALE/UNVERIFIABLE externally** — `.gitignore` excludes `frozen_final_*/bank/`, `frozen_final_*/run/`, and `probe_banks/*`. No Phase A–C number, and not even the Gemini side of the Phase D comparison, is regenerable from the release |
| E7 | "Two independent auditor families, hard logical checks, one independent judge family … reduce correlated-error concerns" (220) | GPT-5 Mini is secondary auditor, fallback primary judge, and cross-judge | **OK\*** — "independent judge family" overstates it; the cross-judge family gatekept the bank |
| E8 | Reproducibility manifest values: bootstrap seed 20260829 / 10,000 draws; cross-judge score SHA `783769c5…`; cost $3.67896645; human seed 20260830 (315–319) | All match `analyze_final.py` defaults, `HUMAN_VALIDATION_MANIFEST.json` source hash, and the Phase D integrity report | **OK** |

---

## F. Stale-V1 sweep

The handoff's §13 checklist items were verified against the manuscript text: no occurrence of "Logical Appeal", "0.60", "1512 pairs"/"1,512 unique", "35.9", "152:0", or the obsolete weighted Equation 4. **The V1 purge is complete.** The residual staleness is in the *documentation*, not the paper: `PROJECT_HANDOFF_AND_PLAN.md` §4.2 still says ten GEPA constraints (superseded by the 13-constraint frozen run) and describes a GEPA optimisation that the artifacts show did not occur.

## G. Summary count

- 8 claims **UNSUPPORTED** or **STALE/UNVERIFIABLE**: B2, B5, B6 (GEPA), E6 (reproducibility), plus omissions C11 (non-blind judge), D17 (Bowker), and the undocumented 502→504 top-up (C2).
- 16 claims **OK\*** — reproduced but framed more strongly, or more narrowly, than the evidence supports.
- All remaining numeric claims **OK**, reproduced to the last decimal.

No fabricated number was found anywhere in the manuscript. The problems are of description and framing, not of arithmetic.
