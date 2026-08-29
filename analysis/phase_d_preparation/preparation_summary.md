# Phase D Paid-Call Preparation

Preparation is complete and made zero API calls. Job manifests contain only IDs, hashes, metadata, lengths, and token estimates; prompts and target responses remain only in the frozen private snapshot.

| Plan | Pair-model jobs | Response jobs | Input-token estimate | Expected uncached cost | Pessimistic no-retry bound |
|---|---:|---:|---:|---:|---:|
| GPT-5 Mini full | 1512 | 3024 | 5,913,237 | $5.11 | $18.46 |
| Claude Sonnet sample | 180 | 360 | 753,148 | $4.96 | $20.33 |

The shared validation sample uses seed 20260829, five pair-model jobs in each of 36 model×category×strategy cells, and both languages for every selected job.

Prices and model availability must be re-verified immediately before execution. The runner requires an explicit paid-approval flag and defaults to validation-only.
