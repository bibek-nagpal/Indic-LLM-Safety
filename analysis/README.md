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

The original full standard GPT-5 Mini and Claude preparations above are preserved for later use. Under the current $4.50 Phase D ceiling, Claude is deferred. OpenRouter's live Batch validator rejected both the base and `:batch` GPT-5 Mini identifiers before persistence, so the active design is now the shared-pair standard-price contingency. Rebuild the token-exact budget design with:

```powershell
.analysis-venv\Scripts\python.exe analysis\design_phase_d_budget.py
```

This hashes every exact reconstructed judge message, counts the actual frozen prompt/response text with GPT-5 Mini's tokenizer, and assumes no prompt-cache discount. The preserved Batch plan and active standard-price stratified plan live in `analysis/phase_d_budget_design/`. The standard plan selects the same pair IDs across target models so between-model gap comparisons remain paired.

Validate both plans locally with:

```powershell
.analysis-venv\Scripts\python.exe scripts\run_cross_judge_batch.py --plan analysis\phase_d_budget_design\gpt5mini_batch_full_plan.json
.analysis-venv\Scripts\python.exe scripts\run_cross_judge_standard_budget.py --plan analysis\phase_d_budget_design\gpt5mini_standard_fallback_plan.json
```

Validation does not load `.env` and makes zero API calls. The unavailable Batch plan refuses further paid access. A paid two-response standard smoke requires `--execute-paid-calls --max-jobs 2 --paid-approval-confirmed`; it must not be used without explicit user approval. The remaining standard subset is independently gated by `--full-run-approval-confirmed` and cannot run until the smoke verifies parsing, non-BYOK OpenRouter billing, and the expected standard price.

After the GPT-5 Mini standard subset is complete, generate the cross-judge agreement statistics, judge-replacement headline metrics, regime verdict, tables, and figures with:

```powershell
.analysis-venv\Scripts\python.exe analysis\analyze_phase_d.py
```

The analyzer fails closed unless every paid score row matches its hash-locked job plan and the Phase A frozen-input gate still passes. Its resampling unit is `pair_id`; publication-ready outputs are written to `analysis/phase_d_results/`.

If the deferred Claude plan is reinstated later, pass `--claude-scores`, `--sample`, and `--claude-plan`; the analyzer then adds the preserved three-judge stratified-sample comparisons without changing the full GPT analysis.
