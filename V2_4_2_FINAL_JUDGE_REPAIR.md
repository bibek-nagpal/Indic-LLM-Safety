# V2.4.2 final judge repair

This package contains the existing `revision_v2_targets_final` run at 1510/1512 and a verified judge fallback configuration.

The target responses are reused. Existing scores are reused. Only missing language judgments are attempted. The primary judge is Gemini 2.5 Flash; after strict retries fail, GPT-5 Mini is used as fallback. Fallback provenance is persisted in `scores.jsonl`.

Expected recovery: two missing judgments only (Nemotron EN for pair 3ac698ae8069513597b92b56; Qwen RH for pair 26ce5e75f47468b26e39495f).
