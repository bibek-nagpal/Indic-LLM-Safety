# Phase A/B analysis

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
