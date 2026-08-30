# Phase D Cross-Judge Robustness

## Cross-judge agreement

- Pure Gemini vs GPT-5 Mini (N=1,943) exact agreement: 73.65%
- Pure Gemini vs GPT-5 Mini adjacent agreement: 91.35%
- Pure Gemini vs GPT-5 Mini unweighted Cohen's kappa: 0.541
- Pure Gemini vs GPT-5 Mini quadratic-weighted kappa: 0.813
- Frozen primary pipeline vs GPT-5 Mini in the planned scope (N=1,944) exact agreement: 73.66%
- The planned scope contains 1 preserved GPT-5 Mini fallback score(s) in the primary pipeline; the pure comparison excludes them.

## Headline metrics under judge replacement

| Judge | Model | EN refusal | RH refusal | Gap (95% CI), pp | Forward/reverse | Critical forward/reverse |
|---|---|---:|---:|---:|---:|---:|
| Gemini-primary pipeline | Qwen3-30B-A3B | 65.74% | 23.15% | 42.59 [37.04, 48.46] | 141/5 | 53/2 |
| Gemini-primary pipeline | GPT-OSS-20B | 85.49% | 82.72% | 2.78 [-0.93, 6.79] | 24/15 | 10/5 |
| Gemini-primary pipeline | Nemotron-3-Nano | 61.73% | 63.27% | -1.54 [-7.41, 4.63] | 46/47 | 16/8 |
| GPT-5 Mini | Qwen3-30B-A3B | 54.01% | 10.49% | 43.52 [37.65, 49.38] | 146/7 | 102/0 |
| GPT-5 Mini | GPT-OSS-20B | 83.64% | 80.25% | 3.40 [-0.62, 7.41] | 27/16 | 21/14 |
| GPT-5 Mini | Nemotron-3-Nano | 50.31% | 58.64% | -8.33 [-14.81, -1.85] | 43/69 | 34/35 |

## Qualitative regime robustness

- GPT-5 Mini gap order: Qwen3-30B-A3B > GPT-OSS-20B > Nemotron-3-Nano
- Predeclared three-regime conclusion survives judge replacement: YES
