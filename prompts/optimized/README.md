# Generator-guidance program artifacts

The final V2 probe bank was built with a **fixed, hand-specified supplementary
generator instruction**. `probe_bank.build_bank` loads it through
`optimized_prompt.load_optimized_instruction(require_v2=True)`, hashes it, and
records the hash in the bank manifest as `gepa_instruction_sha256`.

## Authoritative artifact

`gepa_20260826_135819/` is the artifact used for the frozen bank
`revision_v2_3_1_final_504_dedup`.

| file | role |
|---|---|
| `generator.txt` | the verbatim supplementary instruction; SHA-256 `025fbd3573fc018b3291a51a19acb456df3fd79a3725a1b29610dd89bcd5ce3b`, which is exactly the `gepa_instruction_sha256` recorded in the frozen bank manifest |
| `optimization_manifest.json` | declares `objective: complete_target_independent_probe_validity`, the 13 hard constraints, `target_model_signal_used: false`, `judge_signal_used: false` |
| `metric_log.jsonl` | one record per development-set evaluation (30 records); every record carries `target_model_called: false` |
| `api_accounting.json` | 30 metric evaluations, 29 provider calls, USD 0.03017940 total |
| `gepa_logs/gepa_state.bin` | DSPy/GEPA harness state |
| `pareto_summary.json`, `program.json` | harness bookkeeping |

## What the harness did, and did not, do

The DSPy/GEPA harness was used to **evaluate** the instruction against the
target-independent 13-constraint probe-validity metric described in the paper's
Appendix B. It did **not** produce an evolved instruction. The persisted state
records a single program candidate whose `parent_program_for_candidate` is
`[None]` — that is, the seed instruction — with `pareto_summary.json` reporting
`best_val_score`, `best_aggregate_score` and `num_iter` all null, and only
`iter_0_prog_0.json` outputs under `gepa_logs/generated_best_outputs_valset/`.

The instruction that was frozen and used is therefore the hand-written one, and
the manuscript describes it as such. `scripts/verify_generator_artifact.py`
re-checks the hash and these properties.

## Superseded artifact

`_superseded_v1_gepa_20260523_130239/` is a May-2026 exploratory run from the V1
pipeline. Its `generator.txt` is a **different** 900-character instruction
(SHA-256 `33910016c5b9ada87b79894bc9081128269bc647f8578c5e6741390aae9b81ef`) that
was **not** used for the frozen bank, and it carries no
`optimization_manifest.json`, so `load_optimized_instruction(require_v2=True)`
correctly refuses it. It is retained for history only. Its directory name
deliberately does not match the `gepa_*` glob, so it can never be selected.

Two further exploratory V2 runs (`gepa_20260825_210033`, `gepa_20260826_103104`)
exist in the local working tree and are intentionally untracked: they used an
earlier 10-constraint objective (`paired_prompt_quality_only`) and did not
produce the frozen instruction.
