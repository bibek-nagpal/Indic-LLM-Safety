# Phase E human-validation package

This package contains an outcome-independent, blinded 180-response sample for two independent annotators. The same response items appear in independently randomized order in the Human A and Human B workbooks.

The sampling unit is a pair-model job. The design selects 90 jobs from the completed, outcome-independent Phase D shared-pair scope, retains both English and Romanized-Hindi responses, and assigns 2 or 3 jobs to every target-model × category × strategy cell. Selection occurs before automated scores are loaded. Pair IDs are disjoint across models within each category × strategy cell to maximize prompt diversity.

Annotators receive only their workbook and `ANNOTATOR_INSTRUCTIONS.pdf`. Do not give them the `private/` directory. The private files map each workbook's neutral item number to a stable reconciliation ID and then to frozen provenance and automated scores.

Rebuild the package:

```powershell
& .\.analysis-venv\Scripts\python.exe human_validation\prepare_human_validation.py
& '<bundled-node>' human_validation\build_annotation_workbooks.mjs
```

After both annotators return completed workbooks:

```powershell
uv run --group analysis python human_validation\analyze_returned_labels.py `
  --human-a human_validation\outputs\phase_e_human_validation\Human_A_annotations.xlsx `
  --human-b human_validation\outputs\phase_e_human_validation\Human_B_annotations.xlsx
```

The analyzer reports human-human exact and adjacent agreement, unweighted and quadratic-weighted Cohen's kappa, 4×4 confusion matrices, and each human's agreement with the frozen Gemini-primary and GPT-5 Mini scores. It does not fabricate consensus or adjudicated labels; disagreements remain explicitly unresolved until adjudication occurs.
