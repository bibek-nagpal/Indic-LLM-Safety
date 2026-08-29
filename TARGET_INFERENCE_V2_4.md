# Target inference V2.4

This patch does **not** change the frozen prompt bank, target model list, judge rubric, or generation settings.
It hardens only execution of `run-bank`.

## Changes

- `--run-id` is now a true resumable experiment identifier.
- Successful raw target responses are reused after interruption; they are not re-fired just because judging was interrupted.
- EN and RH judge scores resume independently.
- Completed `(pair_id, target_model)` observations are skipped.
- Resume refuses to proceed if the frozen-bank hash or core inference settings changed.
- `--limit-pairs N` enables a cheap smoke test on the first N frozen pairs.
- `--models` optionally restricts target IDs for diagnostics.
- The run manifest records bank hash, model IDs, temperature and token limits.
- Summary progress is computed from all persisted completed observations, not only the latest invocation.

## Recommended smoke test

Run 2 frozen pairs across all three targets under a stable run id:

`uv run jbh run-bank probe_banks/revision_v2_3_1_final_504_dedup --config configs/run.yaml --run-id revision_v2_targets_smoke --limit-pairs 2`

After inspection, use a **new** run id for the full experiment rather than mixing smoke and final outputs.
