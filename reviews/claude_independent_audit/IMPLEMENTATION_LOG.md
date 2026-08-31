# Implementation log — audit findings applied

Records what was applied from this audit on 2026-08-31, what was deliberately
not applied, and one correction to the audit itself.

## Correction to the audit

**M7 / near-duplicate threshold was partly wrong.** The audit reported that
`near_duplicate_threshold: 0.85` was "advertised but never applied". It *is*
applied: `probe_bank._near_duplicate` enforces it at generation time within each
bank build, using a normalized `SequenceMatcher` ratio. What consolidation across
the three source banks used was exact-string matching only, so cross-bank
near-duplicates were unscreened. Measured under the gate's own metric, mean
similarity across all 42,084 within-strategy pairs is 0.093 and five pairs sit at
or above 0.85. The manuscript now states this two-stage behaviour accurately.
The cluster-robust sensitivity stands, reframed as shared scenario scaffolding
rather than near-verbatim duplication. Full detail is appended to
`STATISTICAL_AUDIT.md`; `EXECUTIVE_REVIEW.md`, `METHODOLOGY_AUDIT.md` and
`CLAIM_EVIDENCE_AUDIT.md` were corrected in place.

## Applied

| Audit item | Where |
|---|---|
| C1 GEPA optimisation claim unsupported | §4.1 rewritten; Appendix B retitled "Target-Independent Probe-Validity Metric"; `agrawal2026gepa` citation removed |
| C2 wrong generator artifact tracked | `prompts/optimized/gepa_20260826_135819/` committed; V1 run renamed `_superseded_v1_…`; `.gitignore` fixed; `scripts/verify_generator_artifact.py` added |
| C3 Phase C confounded by verbosity | §5.3 decomposition; abstract qualified; Appendix E |
| M4 judge not blind to language | §4.4 and Limitations |
| M5 "refusal" misnomer | renamed *non-assistance* throughout, incl. title, tables and figure captions; Appendix D |
| M6 three-regime claim over-stated | §5.1 and Conclusion rewritten; Appendix E Table 5 |
| M7 prompt independence | §4.3 two-stage dedup; Appendix E; `analysis/audit_sensitivity.py` |
| M8 cross-judge not family-independent; pooled agreement | §5.4 and Limitations; Appendix F |
| M9 Phase E halved and under-specified | rebuilt at 180 jobs / 360 items; instrument and analysis corrected |
| Mod10 truncation, garbled flag, Bowker, reproducibility scope | §4.4 and Appendix E; `docs/ARTIFACT_FIELD_NOTES.md`; §5.2; §8 |
| Free robustness results | prompt-length null, truncation sensitivity, cluster sensitivity all reported |
| Related work | Banerjee et al. 2025, Aswal & Jaiswal 2025, Yong et al. 2023 added and verified against primary sources; IndicJR's opposite-direction finding engaged; Table 1 row added; LinguaSafe cell corrected after checking the primary source (12 languages, no Hindi, no romanized track) |

## Applied with a judgment call

- **Title.** Changed from "Language-Conditioned Refusal Asymmetry" to
  "…Safety Asymmetry", because leaving "Refusal" in the title contradicts the
  renamed construct. One edit reverts it if you disagree.
- **Workbooks untracked.** The annotation workbooks embed full harmful prompts
  and responses, which the repository's own policy keeps out of git. They stay
  on disk and are hashed in the manifest. Earlier revisions remain in git
  history; purging that is a separate deliberate decision.

## Not applied

- **Phase G, Phase H, any target inference, any paid API call.** Out of scope by
  instruction. Phase G remains the single recommended paid experiment.
- **Regenerating `analysis/results/`.** Re-running `analyze_final.py` would
  redraw the bootstrap and shift published CI digits with no scientific gain.
  The frozen Phase A–D outputs are untouched.
- **The 41 regex-refusal-versus-score-2 disagreements** flagged in `judge.py`'s
  docstring were not reviewed; they would need human reading of harmful content
  and are better folded into Phase E.
- **Purging `errors.jsonl`** of the OpenRouter workspace key identifier. The file
  is gitignored and untouched by this work; it must be scrubbed before any gated
  release. Recorded in `docs/ARTIFACT_FIELD_NOTES.md`.
- **`hard_constraint_score` double-count path** (`equivalence.py:498–528`) left
  as is: fixing it changes a frozen-era code path for no current benefit.
  Documented here instead.

## Outstanding manual step

`human_validation/outputs/phase_e_human_validation/` could not be deleted or
renamed because `Human_A_annotations.xlsx` was open in Excel. It carries
`OBSOLETE_DO_NOT_DISTRIBUTE.md`. Close Excel and remove the directory.
