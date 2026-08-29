# V2.4.1 — narrow judge fallback

This patch does not regenerate prompts or target-model responses and does not alter existing judge scores.

- Primary response judge remains `google/gemini-2.5-flash`.
- `openai/gpt-5-mini` is used only when the primary judge still fails after its existing retry policy (e.g. provider `PROHIBITED_CONTENT`).
- Fallback provenance is written into each new score row (`fallback_used`, `judge_used`, `primary_judge_error`).
- Existing completed `(pair_id, model, language)` scores are reused unchanged.
- The run manifest records the fallback model and policy.

To complete the existing final run, copy the existing `runs/revision_v2_targets_final` folder into this project, preserve `.env`, and rerun the exact final command with the same run ID.
