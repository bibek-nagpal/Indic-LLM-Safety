# Pre-submission Status and Evidence Boundaries

## Completed and verified

- The 504-pair certified bank and 1,512 pair-model / 3,024-response target run remain frozen and unchanged.
- Phase A integrity and Phase B paired statistical outputs are the source of every main numerical claim.
- Phase C provides the prespecified judge-independent response-length signal.
- Phase D contains 1,944 valid GPT-5 Mini judgments, zero unresolved jobs, zero target-inference calls, and USD 3.67896645 committed under the USD 4.50 ceiling. Every integrity check passes.
- Phase E materials are prepared for two blinded annotators at the requested scale: **180 pair-model jobs, both languages, 360 response items per annotator (11.9% of the 1,512-job grid)**, exactly 5 jobs in each of the 36 model x category x strategy cells. Automated outcomes were not used for sample selection. The earlier 90-job / 180-item package is marked obsolete and was never labelled.
- Post-audit sensitivity analyses are committed under `analysis/sensitivity_results/` and regenerate from `analysis/audit_sensitivity.py`: prompt-similarity and cluster-robust resampling, response truncation, prompt-length null, the Phase C stratified decomposition, the score-0 length profile, and per-condition cross-judge agreement.
- The generator instruction whose SHA-256 the frozen bank manifest records is now tracked, and `scripts/verify_generator_artifact.py` re-checks the correspondence.
- The canonical manuscript is `paper/acl_latex.tex`; `paper/draft2_aug.tex` is only a compatibility wrapper. The compiled PDF has eight pages, resolved citations/references, no LaTeX errors, no overfull boxes, and no visually clipped content.

## Corrections made after the independent audit (2026-08-31)

1. **The GEPA description was wrong and is fixed.** The persisted harness state for the run that produced the frozen instruction holds a single seed program with no parent, a null Pareto summary, and one reflection call at USD 0.030. No prompt evolution occurred. Section 4.1 and Appendix B now describe a fixed, hand-specified, target-independent instruction validated against a 13-constraint metric.
2. **The wrong generator artifact was tracked.** The committed directory held a May-2026 V1-era instruction hashing to `33910016...`, not the `025fbd35...` the bank manifest records, and lacked the `optimization_manifest.json` that `load_optimized_instruction(require_v2=True)` requires, so `run_bank` could not execute from a clean checkout. The correct artifact is now tracked.
3. **"Refusal" was the wrong name for the score-0 construct** and is renamed *non-assistance* throughout. None of Qwen's 115 Romanized-Hindi score-0 responses is under 80 characters; 99.1% exceed 500.
4. **Phase C was presented as independent evidence of harm.** It is judge-independent but partly reflects verbosity: 65:0, 22:2 and 12:58 of the directional shapes arise among pairs scored 0 in both languages. Section 5.3 now decomposes it.
5. **The "three distinct regimes" claim was withdrawn.** The GPT-OSS-Nemotron contrast crosses zero under cluster-robust resampling and is judge-dependent. Qwen is robustly distinct; the other two are not reliably separated.
6. **Phase E was rebuilt** from 90 jobs (5.95%) to 180 jobs (11.9%) with a corrected instrument.

## Claims or quantities that cannot currently be verified

1. **Human agreement and adjudicated labels.** No labels have been returned, so there is no human accuracy, kappa, confusion matrix, or adjudicated result to report.
2. **Full generation funnel and certification selectivity.** The consolidated frozen attempt log has only six records (four retrieval failures and two audited candidates). It cannot recover the number or distribution of all generated and rejected candidates.
3. **Certification ablation.** No rejected-candidate ablation was run, and the incomplete historical funnel prevents a faithful retrospective reconstruction.
4. **Unusual-English out-of-distribution behavior.** This control has not been run and would require new target inference.
5. **Backend build identity beyond stored model slugs and timestamps.** Provider-routed model slugs, settings, request provenance, and dates are stored; an immutable provider-internal weight/build identifier was not exposed and is not claimed.
6. **Organic-traffic prevalence or universal multilingual behavior.** The design is a controlled synthetic probe, so those quantities are outside its estimand.

All bibliography entries and protocol-comparison claims in the V2 manuscript were checked against primary paper or proceedings records. No unverifiable numerical literature claim is used in the results.

## Highest-value remaining actions

1. **Collect the two human workbooks and run the frozen reconciliation analysis.** This is the highest scientific return with no model/API cost. Distribute copies from `human_validation/outputs/phase_e_v2_180jobs/`, never the originals, and never the `private/` directory. Pre-adjudication labels are primary and immutable; adjudication follows `human_validation/ADJUDICATION_PROTOCOL.md`.
2. **If historical raw generation logs can be recovered, reconstruct the candidate funnel offline.** This would permit selectivity and failure-mode reporting without new inference. Do not infer missing records from the final bank.
3. **Consider the unusual-English control only after human validation.** It directly tests whether the observed effect is language/register-specific rather than generic perturbation sensitivity, but it requires a preregistered design and new paid target/judge calls.
4. **Do not prioritize a certification ablation unless the full candidate history is recovered or a new, explicitly approved replication is funded.** A partial post-hoc ablation would be less informative and could confuse the frozen study with a new experiment.
5. **Before public release, separate code/manifests/hashes from gated harmful prompts and responses.** Keep the research snapshot immutable and private while producing a sanitized release package.

## Final consistency command

Run `.\\.analysis-venv\\Scripts\\python.exe paper\\audit_paper_consistency.py` and `.\\.analysis-venv\\Scripts\\python.exe scripts\\verify_generator_artifact.py`, followed by the repository test suite and a clean LaTeX compile. The consistency audit fails if frozen counts, headline estimates, cross-judge accounting, the post-audit sensitivity outputs, the generator-instruction hash, the non-assistance terminology, the Phase E protocol status, citation keys, or obsolete V1 and withdrawn claims diverge.
