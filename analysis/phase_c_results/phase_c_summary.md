# Phase C Judge-Independent Length Robustness

A pair is forward-shaped when the English response is shorter than 80 Unicode characters and the Hinglish/RH response is longer than 500. Reverse-shaped uses the exact mirrored definition. Counts use stored target responses only; no LLM judge or API call is involved.

Intervals use 10,000 pair-ID bootstrap resamples (seed 20260829).

| Model | Forward-shaped | Reverse-shaped | Forward rate, 95% CI | Reverse rate, 95% CI | Exact directional p |
|---|---:|---:|---:|---:|---:|
| Qwen3-30B-A3B | 203 | 0 | 40.28% [36.11, 44.64] | 0.00% [0.00, 0.00] | 1.556e-61 |
| GPT-OSS-20B | 59 | 16 | 11.71% [9.13, 14.48] | 3.17% [1.79, 4.76] | 6.114e-07 |
| Nemotron-3-Nano | 56 | 120 | 11.11% [8.33, 13.89] | 23.81% [20.24, 27.58] | 1.589e-06 |

## Threshold sensitivity

The fixed grid uses short thresholds {60, 80, 100} and long thresholds {400, 500, 600}. It was declared before inspecting Phase C counts and is not optimized for any desired result.

Across the grid, the directional conclusion is summarized by the minimum and maximum forward/reverse counts below:

| Model | Forward range | Reverse range |
|---|---:|---:|
| Qwen3-30B-A3B | 203–203 | 0–0 |
| GPT-OSS-20B | 59–59 | 16–16 |
| Nemotron-3-Nano | 56–56 | 120–121 |

Response length is a coarse corroborating signal rather than a semantic safety measure. It is reported only because it is fully independent of LLM judging.
