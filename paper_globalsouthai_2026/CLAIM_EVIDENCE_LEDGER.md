# Corrected claim–evidence ledger

Point estimates are recomputed from frozen scores. Statistical intervals are taken from validated outputs, not newly sampled.

| Claim | Repository evidence | Correct interpretation |
|---|---|---|
| 504 pairs; 42 per 12 cells; 3,024 responses / 1,512 pair-model observations | frozen_final_2026_08_29 bank/run; analysis/qc_final.py | pair_id is the experimental unit |
| Qwen 65.9% EN /22.8% RH; gap43.1 [38.5,47.6];85 critical flips | analysis/results/main_results.csv; verify_headline.py | Scored assistance; 0–1 is not proof of refusal |
| GPT-OSS gap4.6 [1.4,7.7]; Nemotron−1.8 [−6.5,2.8] | Same validated main_results.csv | No replacement bootstrap digits |
| Robust Qwen-versus-rest; smaller contrast cluster-fragile | analysis/results/statistical_tests.json; analysis/sensitivity_results/cluster_sensitivity.csv | Not three statistically established regimes |
| Retained GEPA instruction equals seed;30/24 development results | prompts/optimized/gepa_20260826_135819/; scripts/verify_generator_artifact.py | Reflection attempted, no accepted evolved instruction |
| Deterministic filters → DeepSeek → Mini acceptance cascade | src/jailbreak_hermes/probe_bank.py; frozen bank audits | Dual pass for retained prompts, not unconditional independent rating |
| 272 short Nemotron RH zeros explicitly refuse | Frozen traces plus scores; analysis/verify_revision.py | Original regex missed curly apostrophes; length does not classify refusal |
| Second judge retains Qwen>OSS>Nemotron order | analysis/phase_d_results/judge_replacement_main_results.csv | 324 shared pairs/model; contrast magnitude/support changes |
| Human agreement74.7%; Mini79.6%, QWK.885 | unchanged analysis/human_a_results.json | 285 verified completed responses; conditional single-human comparison |
| Human Qwen gap53.1 on32 complete jobs | Same human result JSON | Directionally consistent, no tested human-minus-judge difference |
| B labels unavailable | Frozen Phase E template/output hashes, accepted independent audit | Blank template is not evidence of a returned workbook |
| Human bootstrap5000/seed20260904 | analysis/human_a_validation.py; unchanged results | Separate from Phase B10000/20260829 |
| Length ratio1.114; absolute rho≤.051,p≥.256 | analysis/sensitivity_results/prompt_length_null.json | Spearman association, not adjustment or absence-of-effect proof |
| Similarity gate versus clustering | near_duplicate_similarity.json; audit_sensitivity.py; construction code | SequenceMatcher within source bank; exact-only cross-bank; separate token Jaccard |
| Bowker/truncation | analysis/results/; analysis/sensitivity_results/truncation_sensitivity.csv | Transition-symmetry and completed-output sensitivity, not causal identification |
| Judge language labels | src/jailbreak_hermes/judge.py; frozen judge input format | Explicit en/rh labels and prompt text, not blinded |
| Participant warnings/right to stop | human_validation/ANNOTATOR_INSTRUCTIONS.md | Consent, compensation and ethics approval/exemption not established |
| Official template/checklist | build/official_2026.zip; SUBMISSION_RULES.md | Complete checklist retained after appendix; not charged to main pages |

See analysis/revision_verification.json (34 checks), NUMERICAL_AUDIT.md (30 checks), and REVISION_LOG.md for the full change mapping.
