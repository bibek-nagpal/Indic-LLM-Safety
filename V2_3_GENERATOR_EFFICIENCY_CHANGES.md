# Revision V2.3 — generator-efficiency / resumability patch

Scientific certification is unchanged: DeepSeek V4 Flash remains the primary auditor and GPT-5 Mini remains the secondary auditor after primary pass. Existing certified pairs remain valid.

Changes:
- `bank_max_attempts_per_cell` raised from 180 to 1000.
- Attempt budget is now cumulative across resumptions; existing attempt history is counted before a cell resumes.
- Generator now uses strategy-specific constructive contracts for SymbolicMasking, ScenarioNesting, and RolePrompting.
- Generator JSON includes a language-neutral `construction` scaffold. Both EN and RH are rendered from the same underlying task/strategy structure.
- A free deterministic proposal-side precheck rejects candidates whose explicit construction scaffold cannot satisfy the requested strategy before either paid auditor is called.
- Generator failures now persist subtype diagnostics (`chat` vs `json_parse`, finish reason/content length when available) in `attempts.jsonl`.
- No extra LLM/API call was added per generation attempt. The changes are prompt/schema/local-validation changes only.

Deliberately NOT changed:
- auditor prompts or hard acceptance criteria;
- GEPA objective or target independence;
- target-model execution;
- the three-strategy experimental design;
- existing certified pairs in `revision_v2_final_504`.
