# Pre-submission Status and Evidence Boundaries

## Completed and verified

- The 504-pair certified bank and 1,512 pair-model / 3,024-response target run remain frozen and unchanged.
- Phase A integrity and Phase B paired statistical outputs are the source of every main numerical claim.
- Phase C provides the prespecified judge-independent response-length signal.
- Phase D contains 1,944 valid GPT-5 Mini judgments, zero unresolved jobs, zero target-inference calls, and USD 3.67896645 committed under the USD 4.50 ceiling. Every integrity check passes.
- Phase E materials are prepared for two blinded annotators: 90 pair-model jobs, both languages, and 180 response items per annotator. Automated outcomes were not used for sample selection.
- The canonical manuscript is `paper/acl_latex.tex`; `paper/draft2_aug.tex` is only a compatibility wrapper. The compiled PDF has eight pages, resolved citations/references, no LaTeX errors, no overfull boxes, and no visually clipped content.

## Claims or quantities that cannot currently be verified

1. **Human agreement and adjudicated labels.** No labels have been returned, so there is no human accuracy, kappa, confusion matrix, or adjudicated result to report.
2. **Full generation funnel and certification selectivity.** The consolidated frozen attempt log has only six records (four retrieval failures and two audited candidates). It cannot recover the number or distribution of all generated and rejected candidates.
3. **Certification ablation.** No rejected-candidate ablation was run, and the incomplete historical funnel prevents a faithful retrospective reconstruction.
4. **Unusual-English out-of-distribution behavior.** This control has not been run and would require new target inference.
5. **Backend build identity beyond stored model slugs and timestamps.** Provider-routed model slugs, settings, request provenance, and dates are stored; an immutable provider-internal weight/build identifier was not exposed and is not claimed.
6. **Organic-traffic prevalence or universal multilingual behavior.** The design is a controlled synthetic probe, so those quantities are outside its estimand.

All bibliography entries and protocol-comparison claims in the V2 manuscript were checked against primary paper or proceedings records. No unverifiable numerical literature claim is used in the results.

## Highest-value remaining actions

1. **Collect the two human workbooks and run the frozen reconciliation analysis.** This is the highest scientific return with no model/API cost. Preserve raw annotator labels; store any later consensus/adjudication separately.
2. **If historical raw generation logs can be recovered, reconstruct the candidate funnel offline.** This would permit selectivity and failure-mode reporting without new inference. Do not infer missing records from the final bank.
3. **Consider the unusual-English control only after human validation.** It directly tests whether the observed effect is language/register-specific rather than generic perturbation sensitivity, but it requires a preregistered design and new paid target/judge calls.
4. **Do not prioritize a certification ablation unless the full candidate history is recovered or a new, explicitly approved replication is funded.** A partial post-hoc ablation would be less informative and could confuse the frozen study with a new experiment.
5. **Before public release, separate code/manifests/hashes from gated harmful prompts and responses.** Keep the research snapshot immutable and private while producing a sanitized release package.

## Final consistency command

Run `.\\.analysis-venv\\Scripts\\python.exe paper\\audit_paper_consistency.py`, followed by the repository test suite and a clean LaTeX compile. The audit fails if frozen counts, headline estimates, cross-judge accounting, human-protocol status, citation keys, or obsolete V1 claims diverge.
