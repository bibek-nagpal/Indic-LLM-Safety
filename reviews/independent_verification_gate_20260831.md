# Independent verification gate after Claude audit corrections

Verified against base `31d5732`, Claude-completed HEAD `aca00de`, and the
minor objective corrections made by this gate on 2026-08-31. No paid API call,
target inference, Phase G/H experiment, or stochastic replacement of published
analysis outputs was performed.

## Verdict

| Area | Verdict | Basis |
|---|---|---|
| Frozen-data integrity | **PASS** | The 14 freeze-manifest hashes match; the 504-pair bank, 1,512 pair-model target run, 3,024 responses/scores, Phase A/B outputs, Phase C outputs, and Phase D archive are unchanged. Phase A QC passes all 28 checks. |
| Methodology | **PASS WITH MINOR FIXES** | Claude's repaired generator artifact and V2 loader path are correct. This gate fixed one remaining abstract sentence that still implied generator optimization and narrowed one sentence that overclaimed Nemotron's reverse asymmetry. |
| Statistics | **PASS WITH MINOR FIXES** | Published analyses trace to frozen data and the eight sensitivity outputs reproduce exactly (after normalizing Windows line endings). Before human labels, this gate fixed pairwise missing-data handling, added job-clustered intervals for kappa and severity metrics, and removed Human-A privilege from the secondary adjudication path. |
| Manuscript | **PASS WITH MINOR FIXES** | Headline values, limitations, and sensitivity claims are accurate. This gate corrected two visible figure labels, two literature details, the GEPA abstract sentence, and an appendix/PDF layout defect. |
| Phase E readiness | **PASS WITH MINOR FIXES** | The v2 package is correctly sampled, blinded, blank, hash-locked, and safe to distribute. The obsolete 90-job workbooks remain on disk in a separately warned directory and must not be sent. |
| Reproducibility | **PASS WITH MINOR FIXES** | Hash locks, deterministic selection, private mappings, generator reproduction, and offline manuscript compilation work. This gate made the instruction PDF byte-reproducible and records binary Git attributes. Full raw-data regeneration still appropriately requires gated access to the harmful frozen snapshot. |

## Independent checks

### Frozen experimental core

- `git diff 31d5732..aca00de` does not modify the frozen bank/run or validated
  Phase A--D result directories.
- Every file in `frozen_final_2026_08_29/FREEZE_MANIFEST.json` exists and has
  the recorded SHA-256.
- `analysis/qc_final.py` passes 28/28 checks on a temporary output directory.
- `paper/audit_paper_consistency.py` passes after the gate fixes.
- The repository test suite passes: 65 tests.

### Generator artifact and GEPA description

- `scripts/verify_generator_artifact.py` passes all checks.
- `generator.txt` hashes to
  `025fbd3573fc018b3291a51a19acb456df3fd79a3725a1b29610dd89bcd5ce3b`,
  exactly the frozen bank manifest value.
- The required V2 loader returns that instruction with `require_v2=True`.
- The persisted state contains one seed candidate, no parent, no accepted
  revision, 30 metric evaluations, 24 all-constraint passes, and no target
  signal. The manuscript now consistently calls the instruction fixed and
  hand-specified and treats Q as a validation diagnostic.

### Terminology and scientific interpretation

- Non-assistance is consistently the operational construct in the title,
  abstract, definitions, headline tables, conclusions, and visible figure
  labels. Remaining uses of “refusal” describe actual refusal text, the refusal
  regex, or cited titles rather than renaming score 0.
- Phase C is described as a judge-independent length/behavior diagnostic,
  decomposed using the judge labels. It is not presented as independent
  evidence of harmfulness.
- Qwen-versus-rest is the robust heterogeneity result. GPT-OSS and Nemotron are
  explicitly not reliably separated; the nominal Bowker result, length signal,
  and GPT-5 Mini shift are described as consistent with reverse-asymmetric
  Nemotron behavior, not proof of a distinct regime.
- Cluster/near-duplicate, truncation, Bowker, prompt-length, and cross-judge
  sensitivity values agree with their committed outputs. The exact
  sensitivity run reproduced all eight output files byte-for-byte after LF
  normalization.
- The five final-bank pairs at or above the 0.85 generation threshold all
  cross source-bank boundaries. The code enforces fuzzy matching within each
  bank build; consolidation used normalized exact matching only. Claude's
  correction of its original audit statement is correct.

### Literature verification

- Banerjee et al. use a Matrix-Language-Frame-inspired 60:40 construction
  across ten languages; the 9.46% to 69.08% increase is specifically Phi-4B,
  and their manual response-label check is on Hindi and Bengali. The manuscript
  was corrected accordingly.
- The current arXiv title for Aswal and Jaiswal (v5) is *Phonetic Perturbations
  Reveal Tokenizer-Rooted Safety Gaps in LLMs*; the bibliography was updated.
- LinguaSafe's translated/transcreated/native inputs and four severity levels,
  IndicJR's 12-language judge-free design and romanized/mixed JSON-track
  result, RomanSetu's token-fertility/representation claims, and Yong et al.'s
  low-resource cross-lingual jailbreak finding are supported by the cited
  primary papers.

### Judge limitations

- The manuscript discloses that the judge message contains an explicit
  language tag and that judge replacement preserves it.
- It also discloses that GPT-5 Mini served as secondary certification auditor,
  two-item fallback judge, and cross-judge scorer; the re-judge is therefore a
  scoring-robustness check, not a fully independent pipeline family.

### Phase E package

- Exactly 180 pair-model jobs and 360 response items per annotator: 5 jobs in
  every one of 36 model/category/strategy cells and 11.9% of the 1,512-job
  grid.
- Selection uses seed `20260831`, reads identities/strata before scores, and is
  outcome-independent. Pair IDs are disjoint across models within cells.
- Human A and B contain the identical 360 underlying items, in independently
  randomized orders; only one item shares the same position. The minimum twin
  separation is 11 positions for each annotator, exceeding the required 10.
- Artifact-tool inspection confirms the expected three sheets, correct headers,
  360 rows, blank score/flag fields, no formula errors, and prompt/response
  hashes matching the private order and reconciliation mappings.
- No model ID, pair ID, category, strategy, language tag, automated score, flip
  label, or conclusion is shipped in either workbook. Language itself cannot
  be hidden because annotators see the text, which is disclosed.
- The 8-item familiarization set is outside the analysis sample and ships no
  answer key. Automated scores were used only to span its rubric range, not to
  select the analysis sample.
- The current annotator guide is a visually checked one-page PDF and rebuilds
  byte-identically. The package finalizer passes and all four deliverable hashes
  match the manifest.
- Primary analysis keeps pre-adjudication labels, excludes unreadable/missing
  data pairwise, clusters every interval on pair-model job, reports human-human
  and each-human-versus-each-judge agreement, both kappas, confusion matrices,
  model/language strata, non-assistance gaps, and critical severity. Secondary
  adjudication replaces only routed scores in both separate human streams.

### Compiled manuscript

- `paper/acl_latex.tex` is canonical; `draft2_aug.tex` is only a wrapper.
- Tectonic 0.17.0 compiles the manuscript offline after caching the one missing
  standard Computer Modern font resource. There are no undefined citations or
  cross-references.
- The final PDF has 11 pages. Main content, including the conclusion, fits in
  the ACL long-paper 8-page content limit; appendices and references follow.
  All pages were rendered and visually inspected. The earlier nearly blank
  last page was removed without changing scientific content.
- Phase E is explicitly results-pending. Phase G/H controls appear only as
  unfinished limitations; no speculative result is presented as evidence.

## Distribution decision and remaining actions

The files in `human_validation/outputs/phase_e_v2_180jobs/` are safe to send as
copies to the two annotators, together with the familiarization workbook and
current instruction PDF. Send Human A only the A workbook and Human B only the
B workbook. Do not distribute `human_validation/private/`.

Before sending, quarantine or remove the obsolete workbooks still present in
`human_validation/outputs/phase_e_human_validation/` (after closing any program
that has them open), or package only the exact v2 directory. Preserve a private
backup of the two hashed master workbooks and mappings. Record annotator
eligibility/proficiency and dates, collect both files independently, verify
their item/order hashes on return, then run the frozen pre-adjudication analysis
before any routed adjudication. Complete and report Phase E before deciding on
Phase G. Do not start Phase G/H or any paid experiment without the separately
required approval and preregistration.
