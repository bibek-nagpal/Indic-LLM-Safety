# Frozen Final V2 Integrity Report

**Overall status:** PASS

- Snapshot: `frozen_final_2026_08_29`
- Bank: `revision_v2_3_1_final_504_dedup`
- Run: `revision_v2_targets_final`
- Canonical bank SHA-256: `35bfbc1d09e78b77c24d62bbf41783cc9b297dd25f1bba3fe6062d53dc2028ed`

## Counts

- Pairs: 504
- Raw Trace Rows Including Retries: 1649
- Successful Pair Model Jobs: 1512
- Scores: 3024
- Flips: 1512
- Historical Error Rows: 156
- Fallback Judgments: 2

## Checks

| Check | Status | Observed |
|---|---:|---|
| freeze_manifest_file_hashes | PASS | `0` |
| bank_row_count | PASS | `504` |
| bank_unique_pair_ids | PASS | `504` |
| pair_id_content_hashes | PASS | `504` |
| unique_normalized_english_prompts | PASS | `504` |
| unique_normalized_rh_prompts | PASS | `504` |
| balanced_category_strategy_cells | PASS | `{"violence::SymbolicMasking": 42, "violence::ScenarioNesting": 42, "violence::RolePrompting": 42, "intoxication::Symb...` |
| canonical_bank_sha256 | PASS | `"35bfbc1d09e78b77c24d62bbf41783cc9b297dd25f1bba3fe6062d53dc2028ed"` |
| dual_auditor_hard_acceptance | PASS | `504` |
| target_independent_generation_manifest | PASS | `{"gepa_target_signal_used": false, "target_models_used_during_generation": []}` |
| no_target_models_in_generation_provenance | PASS | `0` |
| immutable_run_settings | PASS | `"match"` |
| successful_pair_model_trace_coverage | PASS | `1512` |
| target_prompts_match_frozen_bank | PASS | `0` |
| target_trace_metadata_matches_bank | PASS | `0` |
| score_row_count | PASS | `3024` |
| unique_score_keys | PASS | `3024` |
| complete_score_key_grid | PASS | `3024` |
| score_range_and_nonmissing | PASS | `3024` |
| score_metadata_matches_bank | PASS | `0` |
| exact_two_documented_fallback_judgments | PASS | `2` |
| flip_row_count | PASS | `1512` |
| unique_flip_keys | PASS | `1512` |
| flip_records_match_scores_and_definitions | PASS | `0` |
| three_models_per_pair | PASS | `"504 pairs; counts=[3]"` |
| two_languages_per_pair_model_job | PASS | `"1512 jobs; counts=[2]"` |
| stored_summary_recomputed_exactly | PASS | `0` |
| completed_job_progress | PASS | `{"completed_pair_model_jobs": 1512, "expected_pair_model_jobs": 1512, "complete": true}` |

The historical error records are retained as append-only retry provenance. They do not represent missing final observations; every pair-model-language key has one valid final score.
