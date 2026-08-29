# Phase D Budget Redesign

No API calls were made. Claude remains fully prepared but deferred.

| Mode | Response jobs | Input cost | Expected output cost (600/job) | Expected total | Max total | Conservative retry allowance | Fits $4.50? |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-5 Mini standard, full | 3024 | $1.494 | $3.629 | $5.122 | $7.687 (1024/job) | $0 (over ceiling by $3.187) | NO |
| GPT-5 Mini Batch API, full | 3024 | $0.747 | $1.814 | $2.561 | $3.843 (1024/job) | $0.657 | YES |
| Standard fallback, 27/cell | 1944 | $0.959 | $2.333 | $3.292 | $3.945 (768/job) | $0.500 | YES |

The recommended full Batch API design reserves $0.657 below the hard $4.50 ceiling even if every response consumes the full 1024-token cap. At the single most expensive job's maximum cost, that reserve covers 393 whole-job retries.

The standard-price contingency selects the same 27 pair IDs in each of the 12 category×strategy cells for all three target models, retaining both languages. This preserves pair-level between-model comparisons while reserving $0.50 for retries.

The strict JSON schema constrains only the response format already required by the frozen rubric. Reasoning effort is unchanged; prompt caching is automatic provider-side upside and contributes $0 to the budget case. The 1024-token Batch cap includes reasoning tokens and exceeds both historical local GPT-5 Mini response-judge completions (614 and 577 tokens).
