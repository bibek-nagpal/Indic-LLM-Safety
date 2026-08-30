# Reviewer Action Matrix

Status reflects the canonical manuscript `paper/acl_latex.tex` and the frozen repository state on 2026-08-30.

| Requested action | Status | Resolution or evidence | Remaining boundary |
|---|---|---|---|
| Define the attack strategies precisely, especially role prompting | Addressed | Section 4.2 gives binding structural definitions for SymbolicMasking, ScenarioNesting, and RolePrompting; Appendix A restates the auditor contract. | No additional strategy is claimed or needed for the present design. |
| Clarify whether the bank is target-conditioned | Addressed | The generator objective is explicitly target-independent; the frozen manifest records no target model and no target signal during generation. | None for the frozen bank. |
| Explain GEPA scoring and weights | Addressed | Section 4.1 and Appendix B state the implemented 13-constraint binary objective with equal weight and natural-language feedback. Obsolete V1 equations were removed. | The objective optimizes validity, not attack success. |
| Specify auditor independence and hard gates | Addressed | Section 4.3 identifies the DeepSeek primary and GPT-5 Mini secondary auditors, their cascade, hard acceptance rule, schemas, and failure behavior. | Because the secondary auditor saw only primary passes, full inter-auditor agreement is not estimable. |
| Add human validation of model-based scores | Prepared; labels pending | Two blinded, independently ordered 180-item workbooks and a prespecified analysis pipeline are complete. Sampling is outcome-independent and balanced across model × category × strategy. | No human result is reported until both workbooks are returned. |
| Define semantic/direct refusal and flip outcomes before analysis | Addressed | Section 3 defines the ordinal score, refusal, refusal gap, forward/reverse flips, and critical flips before results. | None. |
| Use the pair, not individual responses, as the experimental unit | Addressed | Pair ID is explicit as the resampling and inference unit; bootstrap, exact paired tests, randomization, and clustered GEE preserve pairing. | None. |
| Strengthen reproducibility | Addressed | Frozen identifiers, SHA-256 hashes, model slugs, decoding settings, seeds, fallback provenance, analysis scripts, and a reproducibility manifest are included. | Raw harmful content should remain gated in any public release. |
| Add a judge-independent check | Addressed | Phase C uses only stored response lengths under prespecified thresholds and reproduces the three-model directional ordering. | Length is correctly treated as a coarse signal, not a semantic safety metric. |
| Replace or cross-check the Gemini response judge | Addressed within budget | All 1,944 responses in the outcome-independent shared subset were re-judged by GPT-5 Mini with the identical rubric; ordering is preserved, while absolute severity calibration changes. | This is not a complete re-judge of all 3,024 responses. |
| Position the work against current safety benchmarks | Addressed | Related work and Table 1 compare HarmBench, JailbreakBench, StrongREJECT, LinguaSafe, IndicJR, and IndicAlignProbe on pairing, equivalence, scoring, script, and intended use. | Comparisons are protocol-level, not empirical benchmark leaderboards. |
| Narrow the scope of the title and claims | Addressed | The manuscript consistently limits claims to three models, one English/Hinglish-RH setting, four harm categories, and the frozen synthetic probe distribution. | No universal multilingual or deployment-prevalence claim is made. |
| Add an unusual-English out-of-distribution control | Deferred | The manuscript marks this experiment as unrun. | Requires new target inference and scientific/budget approval. |
| Add a certification ablation or estimate selectivity | Not currently identifiable | The frozen consolidated attempt log contains only six records and cannot reconstruct the full candidate funnel. | Recover complete historical generation logs before attempting an offline analysis; otherwise a new experiment would be required. |
| Expand languages and target models | Future work | Explicitly stated as a limitation. | Consequential new experimental design and paid inference would be required. |

## Submission interpretation

The empirical Phase A--D claims are complete and reproducible. The manuscript is a submission-ready draft, but the planned human-validation result remains intentionally blank until two independent annotators return labels. The paper does not imply that a prepared protocol is completed evidence.
