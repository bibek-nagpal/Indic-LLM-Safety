# Phase D Budget Redesign

The design generation is offline. Three Batch submission validations were rejected before persistence; no inference batch was created and the local ledger records $0. Claude remains fully prepared but deferred.

| Mode | Response jobs | Input cost | Expected output cost (600/job) | Expected total | Max total | Conservative retry allowance | Fits $4.50? |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-5 Mini standard, full | 3024 | $1.494 | $3.629 | $5.122 | $7.687 (1024/job) | $0 (over ceiling by $3.187) | NO |
| GPT-5 Mini Batch API, full | 3024 | $0.747 | $1.814 | $2.561 | $3.843 (1024/job) | $0.657 | YES |
| Standard fallback, 27/cell | 1944 | $0.959 | $2.333 | $3.292 | $4.940 (1024/job) | runtime hard guard | NO at theoretical max |

The full Batch design would reserve $0.657 below the hard $4.50 ceiling even if every response consumes the full 1024-token cap. At the single most expensive job's maximum cost, that reserve covers 393 whole-job retries.

However, live OpenRouter validation rejected both GPT-5 Mini Batch identifiers before persistence. The standard-price shared-pair contingency is therefore the active recommendation.

The standard-price contingency selects the same 27 pair IDs in each of the 12 category×strategy cells for all three target models, retaining both languages. This preserves pair-level between-model comparisons while reserving $0.50 for retries.

After live truncation evidence, remaining items use a 1024-token ceiling. If a response reaches that cap after internal reasoning and fails strict JSON parsing, the runner may retry only that item at 1280 tokens, with one final 2048-token escape hatch only after another documented length stop. The rubric, schema, prompt, model, and reasoning effort remain unchanged; all failed paid attempts count toward the $4.50 ceiling. The $0.50 reserve covers at least 54 such whole-job repairs even at the single most expensive input size.

A hash-locked deferred complement contains exactly the other 180 pair IDs (15 per category×strategy cell), with zero overlap and a 504-pair union. It costs approximately $1.830 at 600 output tokens/job or at most $2.746 before retries at the continuation cap. It cannot run without new explicit paid approval.

The strict JSON schema constrains only the response format already required by the frozen rubric. Reasoning effort is unchanged; prompt caching is automatic provider-side upside and contributes $0 to the budget case. The 1024-token Batch cap includes reasoning tokens and exceeds both historical local GPT-5 Mini response-judge completions (614 and 577 tokens).
