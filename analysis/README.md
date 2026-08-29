# Phase A-D analysis

This directory contains the reproducible integrity and paired-statistical analysis for the frozen final V2 experiment. It never calls a target model or an API.

From the repository root, create the archival snapshot once:

```powershell
.analysis-venv\Scripts\python.exe scripts\create_freeze_snapshot.py
```

Run the Phase A integrity gate:

```powershell
.analysis-venv\Scripts\python.exe analysis\qc_final.py
```

Run Phase B only after the gate passes:

```powershell
.analysis-venv\Scripts\python.exe analysis\analyze_final.py
```

The analyzer reruns the QC gate and fails closed if any check is not clean. All bootstrap resampling clusters on `pair_id` and retains every associated language/model observation. Generated outputs live in `analysis/results/`.

Run the judge-independent Phase C length analysis with:

```powershell
.analysis-venv\Scripts\python.exe analysis\analyze_phase_c.py
```

Phase C outputs live in `analysis/phase_c_results/`. It reads only stored target responses and makes no API calls.

Prepare the hash-locked Phase D manifests and stratified sample offline with:

```powershell
.analysis-venv\Scripts\python.exe analysis\prepare_phase_d.py
```

This recreates `analysis/phase_d_preparation/` deterministically. The manifests contain identifiers, hashes, lengths, and cost-planning metadata, but no prompt or response text. Validate both plans without loading `.env` or making an API call with:

```powershell
.analysis-venv\Scripts\python.exe scripts\run_cross_judge.py --plan analysis\phase_d_preparation\gpt5mini_full_plan.json
.analysis-venv\Scripts\python.exe scripts\run_cross_judge.py --plan analysis\phase_d_preparation\claude_sample_plan.json
```

Paid execution is permitted only after explicit user approval. It requires both `--execute-paid-calls` and `--paid-approval-confirmed`; `--max-jobs` supports a small smoke batch and resumable staged execution. These jobs re-score stored responses only and make zero target-inference calls. Raw scores, errors, provenance, and accounting remain under the ignored `runs/cross_judge/` directory.

After both plans are complete, generate the cross-judge agreement statistics, judge-replacement headline metrics, regime verdict, tables, and figures with:

```powershell
.analysis-venv\Scripts\python.exe analysis\analyze_phase_d.py
```

The analyzer fails closed unless every paid score row matches its hash-locked job plan and the Phase A frozen-input gate still passes. Its resampling unit is `pair_id`; publication-ready outputs are written to `analysis/phase_d_results/`.
