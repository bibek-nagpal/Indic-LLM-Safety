# Audit verification scripts

Independent recomputation scripts written for the audit. **All are read-only, make zero API calls, and never write to the frozen artifacts.** Run from the repository root with a Python that has numpy, scipy, and pandas.

| script | purpose |
|---|---|
| `recompute_main.py` | Independent replication of every Phase A/B headline number from `frozen_final_2026_08_29/run/.../scores.jsonl`: integrity checks, refusal/non-assistance rates, gaps, flips, critical flips, exact McNemar, directional binomial, pair bootstrap CIs, cross-model contrasts. Writes `main_recompute.json`. |
| `bank_diversity.py` | Bank prompt diversity: uniqueness after NFKC/casefold/whitespace normalisation, EN/RH prompt-length asymmetry, code-switch depth proxy, within-cell Jaccard similarity, and the most-similar within-cell prompt pairs. |
| `cluster_bootstrap.py` | Cluster bootstrap of the per-model gap with pairs joined into connected components at several Jaccard thresholds. |
| `cluster_tests.py` | Cluster sign-flip randomisation tests and cluster-bootstrap CIs for the three cross-model gap contrasts. |
| `contrast_sensitivity.py` | Threshold sweep for the GPT-OSS − Nemotron contrast and the GPT-OSS gap under cluster-robust resampling. |
| `trace_audit.py` | Deduplicates the 1,649 trace rows to 1,512 (keep-last), reports `finish_reason` distributions and truncation asymmetry, response lengths, and reproduces the Phase C counts. Writes `deduped_response_rows.json`, consumed by the two scripts below. |
| `refusal_semantics.py` | Construct validity of "refusal" (length and refusal-regex profile of score-0 responses), truncation sensitivity of the headline estimates, and score-3 rates by truncation status. |
| `phase_c_confound.py` | Phase C confound test: length shapes restricted to pairs the judge scored 0 in both languages, plus per-language verbosity comparisons. |
| `phase_c_decomp.py` | Full decomposition of the Phase C shapes by judged outcome stratum. |
| `phase_d_recompute.py` | Schema inspection of the Phase D GPT-5 Mini score archive. |
| `phase_d_full.py` | Independent replication of all Phase D statistics: agreement, both kappas, score distributions, per-model×language agreement and bias, and the six judge-replacement headline rows with contrasts under each judge. |
| `equivalence_confound.py` | Association of the pair-level gap and forward flips with audited equivalence scores and RH/EN prompt-length ratio; auditor score distributions and their correlation. |

Run order: `trace_audit.py` before `refusal_semantics.py`, `phase_c_confound.py`, and `phase_c_decomp.py` (it writes the shared intermediate). All others are standalone.

`main_recompute.json` and `deduped_response_rows.json` are derived intermediates and can be regenerated at any time.
