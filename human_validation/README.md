# Phase E human-validation package (v2)

An outcome-independent, blinded **360-response** sample for two independent
annotators. The same response items appear in independently randomized order in
the Human A and Human B workbooks.

The sampling unit is the pair-model job. The design draws **exactly 5 jobs from
each of the 36 target-model x category x strategy cells** — 180 jobs, **11.9%**
of the 1,512-job grid — from the completed, outcome-independent Phase D
shared-pair scope, and retains both the English and Romanized-Hindi response of
every job. Within a category x strategy cell the sampled pair IDs are disjoint
across models, so 180 distinct prompt pairs are covered. Selection reads
identities and strata only; automated scores, flip status, and downstream
results are never consulted, and scores are joined solely into the private
reconciliation key. The two language items of a job are at least 10 positions
apart in both workbook orders.

> The earlier 90-job / 180-item package is **obsolete** and must not be
> distributed. See `outputs/phase_e_human_validation/OBSOLETE_DO_NOT_DISTRIBUTE.md`.
> No labels were ever collected from it.

## What annotators receive

- `outputs/phase_e_v2_180jobs/Human_A_annotations.xlsx` or `Human_B_annotations.xlsx`
- `outputs/phase_e_v2_180jobs/Familiarization_set.xlsx` (8 items, completed first)
- `outputs/phase_e_v2_180jobs/ANNOTATOR_INSTRUCTIONS.pdf`

Send **copies**. Keep the hashed originals untouched so a returned workbook can
always be checked against the frozen item order. Do **not** give annotators the
`private/` directory: it maps each workbook's item number to a reconciliation ID
and thence to frozen provenance and automated scores.

Each workbook has three sheets: `Instructions`, `Annotator` (language
background and dates), and `Annotation` (item, prompt, response, score,
`Borderline`, `Cannot read`).

## Requirements and instrument design

Annotators must read English and conversational Romanized Hindi (Hinglish) in
Latin script, and record self-assessed proficiency. Three properties of the
instrument are deliberate:

- **Symmetric tie-breaking.** Annotators choose the best-fitting score and tick
  `Borderline`. The previous "choose the lowest score" rule would have built a
  systematic human-below-judge offset into the design, biting hardest on the
  Romanized-Hindi arm where uncertainty is highest.
- **An explicit `Cannot read` flag.** Unreadability is recorded as missing data
  rather than silently coded as 0.
- **A familiarization set with no answer key.** The 8 familiarization items come
  from Phase D pairs that are *not* in the analysis sample. Automated scores were
  used to span the rubric range when choosing them, but **no reference label is
  distributed**: handing annotators judge scores as gold would train them toward
  the very judges the study exists to validate. The set confirms reading
  comprehension and lets rubric questions be settled on non-sample material
  before the main task begins.

Blinding removes model, pair ID, category, strategy, language tag, automated
scores and conclusions. Annotators nevertheless read the response text, so
blinding to language itself is not achievable; the instructions ask them not to
infer conditions or compare rows.

Adjudication is fixed in advance in `ADJUDICATION_PROTOCOL.md`: only |A − B| ≥ 2
items are routed to a blinded third annotator, pre-adjudication labels are
primary and immutable, and adjudicated results are reported as secondary.

## Rebuild the package

```powershell
& .\.analysis-venv\Scripts\python.exe human_validation\prepare_human_validation.py
& .\.analysis-venv\Scripts\python.exe human_validation\build_annotation_workbooks.py
& .\.analysis-venv\Scripts\python.exe human_validation\build_instruction_pdf.py
& .\.analysis-venv\Scripts\python.exe human_validation\finalize_package.py
```

Everything is deterministic from `SEED = 20260831`. The workbook builder uses
`openpyxl`, so the package no longer depends on a Node toolchain.

## Analyze returned labels

```powershell
& .\.analysis-venv\Scripts\python.exe human_validation\analyze_returned_labels.py `
  --human-a human_validation\outputs\phase_e_v2_180jobs\Human_A_annotations.xlsx `
  --human-b human_validation\outputs\phase_e_v2_180jobs\Human_B_annotations.xlsx
```

The analysis is prespecified and frozen. It clusters on the pair-model job —
each job contributes two correlated items — and reports human-human and
human-versus-judge exact and adjacent agreement, unweighted and
quadratic-weighted Cohen's kappa, percentile confidence intervals from 10,000
job-level bootstrap resamples, 4x4 confusion matrices, breakdowns overall and by
model, language and model x language, human-derived non-assistance gaps per
model with clustered intervals, critical-severity (score-3) precision and
recall against each automated judge, and counts of borderline, unreadable and
unscored items. Missing labels are excluded pairwise, so one annotator's missing
item does not discard the other annotator's usable human-versus-judge comparison.
`Cannot read` must have a blank score and is treated as missing. The script
fabricates no consensus: disagreements are reported, and adjudicated labels enter
only via `--adjudicated` and only as a secondary result; routed scores are
substituted into both annotator streams while non-routed labels remain separate.

## Power

At 60 jobs per model the study is powered to validate judge accuracy, chiefly
on the Qwen regime. It is not powered to re-estimate the language gap for
GPT-OSS or Nemotron, and the manuscript says so.
