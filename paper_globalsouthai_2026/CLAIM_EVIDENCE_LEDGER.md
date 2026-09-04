# Claim–evidence ledger

Every substantive claim in `main.tex`, its authoritative source, and how it was verified.
Headline quantities were **recomputed from the frozen artifacts**, not copied from prose:
`analysis/verify_headline.py` reads `frozen_final_2026_08_29/` directly and additionally
asserts that its own recomputation reproduces the committed frozen analysis exactly.

Verification artifacts: `analysis/headline_verification.json`, `analysis/human_a_results.json`,
`NUMERICAL_AUDIT.md`.

| # | Claim | Authoritative source | Raw/derived | Verification | Verified value | Manuscript |
|---|---|---|---|---|---|---|
| 1 | 504 unique certified pairs | `frozen.../bank/.../pairs.jsonl` | raw | recount + sha256 vs manifest | 504 unique `pair_id`; sha `35bfbc1d…dc2028ed` | §2, App. A |
| 2 | 4 categories × 3 framings × 42 | same | raw | cell counter | 12 cells, all exactly 42 | §2 |
| 3 | Both auditors accepted every retained pair | `pairs.jsonl` `primary_audit`/`secondary_audit` | raw | count `accepted` | 504/504 both | §2, App. A |
| 4 | Auditing was a **cascade**, not independent dual rating | bank `manifest.json` `auditor_cascade` | raw | field read verbatim | "DeepSeek primary on all candidates; GPT-5 Mini secondary only after primary pass" | §2, App. A |
| 5 | Generation was GEPA-optimized against the auditor objective | bank `manifest.json` | raw | `gepa_enabled=true`, `gepa_objective_required=complete_target_independent_probe_validity` | true | §2, App. A |
| 6 | No target signal in generation | bank `manifest.json` | raw | `gepa_target_signal_used=false`, `target_models_used_during_generation=[]` | confirmed | §2, App. A |
| 7 | Generator and primary judge are the same model | bank `manifest.json` + run `run_manifest.json` | raw | both = `google/gemini-2.5-flash` | confirmed | §2, App. A |
| 8 | 3,024 responses / 1,008 per model / 1,512 pair-model obs | `run/.../scores.jsonl` | raw | line count + index | 3,024 / 1,008 / 1,512 | §2, App. A |
| 9 | Qwen EN 65.9%, RH 22.8%, gap +43.1 pp [38.5, 47.6] | `scores.jsonl` | derived | recomputed; 10,000-resample cluster bootstrap | 65.8730 / 22.8175 / +43.0556 | Abstract, §3, Tab. 1 |
| 10 | Qwen 219 forward, 85 critical flips | `scores.jsonl` | derived | recomputed from definitions | 219 / 85 (16.9% of 504) | Abstract, §3, Tab. 1 |
| 11 | GPT-OSS gap +4.6 pp [1.6, 7.7] | `scores.jsonl` | derived | recomputed | +4.5635 | §3, Tab. 1 |
| 12 | Nemotron gap −1.8 pp [−6.4, 3.0] | `scores.jsonl` | derived | recomputed | −1.7857 | §3, Tab. 1 |
| 13 | Qwen gap positive in all 12 cells (+7.1 to +76.2) | `scores.jsonl` | derived | per-cell recomputation | 12/12 positive | §3 |
| 14 | Cross-model contrasts, Holm-adjusted | `analysis/results/statistical_tests.json` | derived | read frozen output | +38.49 [32.9,44.0]; +44.84 [38.3,51.4]; +6.35 [0.8,12.1] | §3 |
| 15 | GPT-OSS vs Nemotron not established under clustering | `analysis/sensitivity_results/cluster_sensitivity.csv` | derived | read frozen output | p 0.032 → 0.062 → 0.10 | §3, App. C |
| 16 | Cross-judge: 1,944 judgments, 73.7/91.4, κ .542, QWK .813 | `analysis/phase_d_results/agreement_overall.csv` | derived | read frozen output | exact match | §4 |
| 17 | Qwen gap stable under judge replacement | `phase_d_results/judge_replacement_main_results.csv` | derived | read frozen output | +42.59 vs +43.52 | §4 |
| 18 | GPT-5 Mini was also the secondary prompt auditor | bank `manifest.json` | raw | field read | confirmed | §4, App. A |
| 19 | Human A: n=285 of 360, exact 74.7%, adj 94.0%, κ .513, QWK .825 | `Human_A_annotations.xlsx` joined by reconciliation ID | derived | `analysis/human_a_validation.py`; join re-verified by re-hashing every delivered prompt+response | as stated | §4, App. B |
| 20 | Human higher on 58 / lower on 14 vs primary judge; reversed vs replacement (14/44) | same | derived | same script | as stated | §4, App. B |
| 21 | Human Qwen gap +53.1 pp [37.5, 71.9] on 32 jobs | same | derived | cluster bootstrap over jobs | as stated | §4, Tab. 2 |
| 22 | 73 items unscored, non-random (34% vs 72% score-0) | same | derived | same script | as stated | §4, App. B |
| 23 | Annotator B returned no scores | `human_validation/outputs/.../Human_B_annotations.xlsx` | raw | 360 rows, 0 scores filled | confirmed | App. B |
| 24 | Judge fallback on 2 of 3,024 | `scores.jsonl` `judge_model` + `JUDGE_FALLBACK_V2_4_1.md` | raw | count non-primary judge rows | 2 | §4, App. A |
| 25 | Non-assistance profile (Qwen RH zeros 99.1% >500 ch.) | `analysis/sensitivity_results/nonassistance_profile.csv` | derived | read frozen output | exact match | §3, App. C |
| 26 | Truncation sensitivity | `analysis/sensitivity_results/truncation_sensitivity.csv` | derived | read frozen output | 43.06→43.36; −1.79→−0.50 | §4, App. C |
| 27 | RH prompts 11.4% longer, ρ uncorrelated with gap | `analysis/sensitivity_results/prompt_length_null.json` | derived | read frozen output | \|ρ\| ≤ 0.05, p ≥ 0.26 | §4 |
| 28 | Decoding config (T=0, empty system prompt, 4096) | `run_manifest.json` | raw | field read | confirmed | §2, App. A |

## Claims deliberately NOT made

| Not claimed | Why |
|---|---|
| Two-human validation / inter-annotator agreement / adjudication / consensus ground truth | Only one annotator returned scores. The failed preregistered two-annotator design is disclosed in App. B. |
| The effect is caused by Romanized Hindi specifically | The register control was specified but **not completed**. Language, script, register and training frequency are confounded by design. Stated in the abstract and §5. |
| Any Phase G / unusual-English / strong-archaic result | That experiment is incomplete. It is excluded entirely; it is not cited even as partial evidence. |
| Generalization beyond three models | All generalizing sentences are scoped to "across these three models". |
| The judge is ground truth | The judge is described as a scorer; the human check is its only external anchor. |
| A refusal rate for ordinary harmful Romanized-Hindi requests | Every pair carries an adversarial framing; there is no direct-request or benign condition. Stated in §2. |
