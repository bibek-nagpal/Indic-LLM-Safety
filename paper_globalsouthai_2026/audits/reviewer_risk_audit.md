# Adversarial reviewer audit

A skeptical NeurIPS reviewer was asked to reject the paper, with full read access to the
manuscript, the compiled PDF, and the frozen artifacts. Findings are classified and their
disposition recorded. **Everything rated FATAL or MAJOR that could be fixed with existing
evidence was fixed.**

## Findings and disposition

| # | Criticism | Severity | Disposition |
|---|---|---|---|
| 1 | The auditors were described as "two independent auditors"; the frozen manifest records a **cascade** (secondary only saw candidates the primary passed) | MAJOR (accuracy) | **FIXED.** §2 and App. A now describe a conjunctive cascade and state that no inter-auditor agreement statistic is defined. |
| 2 | Generation was **GEPA-optimized against the auditors' acceptance criterion**; the 504/504 acceptance rate is an optimization target, not an independent test — undisclosed | MAJOR | **FIXED.** Disclosed in §2 and App. A, with the argument for why it cannot produce a between-model contrast. |
| 3 | **Generator and primary judge are the same model** (`gemini-2.5-flash`) — undisclosed | MAJOR | **FIXED.** Disclosed in §2 and App. A. |
| 4 | A **second annotator was preregistered and returned nothing**; the paper said only "one annotator" | MAJOR (disclosure) | **FIXED.** App. B discloses the preregistered two-annotator design, that Annotator B returned no scores, and that the frozen adjudication protocol was never invoked. |
| 5 | Selective reporting: human scored *higher* than the primary judge (58/14) was reported; the *reverse* against the replacement judge (14/44) was not | MAJOR | **FIXED.** §4 now reports both directions. |
| 6 | The GPT-OSS vs Nemotron contrast degrades under near-duplicate clustering (p 0.032 → 0.10); paper attributed its fragility to judge replacement only | MAJOR (selective) | **FIXED.** §3 now reports the clustering result and declines to treat the contrast as established. |
| 7 | Score 0 conflates refusal with **incomprehension**; no evidence offered | MAJOR | **FIXED with existing evidence.** §3 and App. C Table 3 give the judge-free length/refusal-string profile: Qwen's RH zeros are 99.1% >500 chars and 1/115 refusal-like (rules out incomprehension); Nemotron's are 84.5% <80 chars (so its null is now explicitly qualified). |
| 8 | `gpt-5-mini` is the cross-judge **and** the secondary prompt auditor — not an independent replication | MODERATE | **FIXED.** §4 states the dependence and why it cannot create a between-model contrast. |
| 9 | **Every prompt carries an adversarial framing**; no direct-request or benign condition, but the abstract implied general safety | MAJOR | **FIXED.** §2 states the estimand is framing transfer across script, not general Romanized-Hindi safety. |
| 10 | Overclaiming: "is thus a property of the individual model" from n=3; "judge-invariant" from two judges; refusal language after disclaiming it | MODERATE | **FIXED.** All generalizations scoped to the three models; "stable under judge replacement"; scoring language made judge-relative. |
| 11 | Abstract asserted a Romanized-Hindi attribution the limitations disown | MODERATE | **FIXED.** The abstract now carries the mechanism caveat. |
| 12 | `souly2024strongreject` was in the bibliography but never cited, though it is the canonical treatment of the scale's design problem | MODERATE | **FIXED.** Cited where the scale is introduced. |
| 13 | No reproducibility configuration in the paper | MODERATE | **FIXED.** App. A gives bank id + SHA-256, decoding parameters, judge and fallback, seeds, resample counts, and a gated-release statement. |
| 14 | RH prompts are 11.4% longer than EN — "meaning-matched" unqualified | MODERATE | **FIXED.** §4 reports the asymmetry and that per-pair length ratio is uncorrelated with the gap. |
| 15 | Truncation asymmetry unreported | MODERATE | **FIXED.** §4 summary; App. C gives per-model numbers and exact tests. |
| 16 | Five retained pairs exceed the stated 0.85 dedup gate | MODERATE | **FIXED.** App. C reports them and the clustering sensitivity that leaves the Qwen result unchanged. |
| 17 | Missingness unbalanced by model and language, not just by score | MODERATE | **FIXED.** App. B reports both breakdowns and warns the per-model human gaps are not cross-comparable. |
| 18 | Table 2's judge gaps differ from Table 1 without explanation | MODERATE | **FIXED.** Caption states the difference explicitly. |
| 19 | Nemotron and Qwen are the same size class and both MoE — undersold | MINOR | **FIXED.** Stated in §2, ruling out a parameter-count explanation. |
| 20 | Multiplicity: the 12-cell claim carried no test | MINOR | **FIXED.** Sign test over disjoint cells reported. |
| 21 | Human "reproduce"/"confirms and exceeds" overstates n=32 | MODERATE | **FIXED.** Now states the intervals overlap and no test was performed. |
| 22 | Novelty unclear | NOT VALID as rejection ground, but under-defended | **FIXED.** §1 states the specific delta: a certified matched bank held fixed across targets licensing a between-model contrast. |
| 23 | Cherry-picking of targets or items | NOT VALID | Bank frozen before inference; all 3 preregistered targets run on all 504 pairs; fallback preregistered; recomputation reproduces the committed analysis exactly. |
| 24 | Stale `CONSOLIDATION_REPORT.json` says 502 retained pairs | MINOR | Verified directly: `pairs.jsonl` has 504 unique ids, 504 unique EN and 504 unique RH prompts, 12 cells × 42. Cells were refilled after dedup. Noted here for the artifact release. |
| 25 | No human verified prompt-pair equivalence | MAJOR | **NOT FIXABLE.** Stated as a limitation in §5 in exactly those terms. |
| 26 | Register/OOD confound unresolved | MAJOR | **NOT FIXABLE.** The control was not completed; stated in the abstract and §5. |
| 27 | Single greedy decode, no sampling variance | MODERATE | **NOT FIXABLE.** Stated in §5. |
| 28 | Annotator's Romanized-Hindi competence undocumented | MAJOR | **NOT FIXABLE from the frozen record.** Stated in §5 and App. B. |

## TOP 5 REMAINING REVIEWER RISKS

1. **No human validated prompt-pair equivalence.** The matched-pair premise rests entirely
   on LLM auditors, in a paper arguing LLMs are unreliable on Romanized Hindi — and those
   auditors were the generator's optimization target. Disclosed; not removable.
2. **The register/OOD confound is unresolved by design.** The control that would separate
   "Romanized Hindi" from "text unlike the safety-training distribution" was not completed.
   The response-profile evidence rules out the incomprehension variant, not the register one.
3. **Every prompt is an adversarial framing.** The estimand is framing transfer across
   script, not general Romanized-Hindi safety. Disclosed, but readers may still over-read it.
4. **n = 1 annotator, competence undocumented, 20% non-random attrition, 32–50 jobs per
   model.** Honest after disclosure, but thin; the failed second annotator invites questions.
5. **Only the Qwen arm is solidly established.** GPT-OSS's +4.6 pp has a lower CI bound of
   1.6 pp, and Nemotron's null rests on RH zeros that are 84.5% sub-80-character
   non-refusals. The "model-dependent" claim is carried mainly by one arm.

## Reviewer's overall assessment

6/10 before the fixes ("careful about the things it chose to report"); the reviewer stated
that disclosing the four undisclosed facts and adding the non-assistance profile table
would move it to 8/10. All of those changes were made.
