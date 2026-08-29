# Phase B Statistical Analysis Summary

All resampling and paired tests use `pair_id` as the experimental unit. Confidence intervals are percentile intervals from 10,000 paired bootstrap resamples (seed 20260829).

## Main per-model results

| Model | EN refusal | RH refusal | Gap (95% CI), pp | Forward | Reverse | Critical forward | Critical reverse |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-30B-A3B | 65.87% | 22.82% | 43.06 [38.49, 47.62] | 219 (43.45%) | 7 (1.39%) | 85 (16.87%) | 2 (0.40%) |
| GPT-OSS-20B | 86.71% | 82.14% | 4.56 [1.39, 7.74] | 42 (8.33%) | 21 (4.17%) | 15 (2.98%) | 6 (1.19%) |
| Nemotron-3-Nano | 62.10% | 63.89% | -1.79 [-6.55, 2.78] | 65 (12.90%) | 70 (13.89%) | 22 (4.37%) | 10 (1.98%) |

Refusal means score 0. Forward flip means EN=0 and RH≥2; reverse is its language-mirrored counterpart. Critical forward means EN≤1 and RH=3; critical reverse is the mirrored definition.

## Paired tests

| Model | Exact McNemar p | Directional forward-vs-reverse p | Bowker p |
|---|---:|---:|---:|
| Qwen3-30B-A3B | 2.87e-56 | 1.04e-55 | 1.58e-44 |
| GPT-OSS-20B | 0.00674 | 0.0111 | 0.0675 |
| Nemotron-3-Nano | 0.501 | 0.731 | 0.0188 |

## Cross-model heterogeneity

| Gap contrast | Estimate (95% CI), pp | Paired randomization p | Holm p |
|---|---:|---:|---:|
| Qwen3-30B-A3B − GPT-OSS-20B | 38.49 [32.94, 44.05] | 1.00e-05 | 3.00e-05 |
| Qwen3-30B-A3B − Nemotron-3-Nano | 44.84 [38.29, 51.39] | 1.00e-05 | 3.00e-05 |
| GPT-OSS-20B − Nemotron-3-Nano | 6.35 [0.79, 12.10] | 0.032 | 0.032 |

The clustered GEE language×model interaction is also significant (Wald χ²(2)=165.83, p=9.79e-37).

## Fallback-judge sensitivity

Each fallback-affected pair-model job is excluded in full, retaining paired EN/RH data within every remaining job. Qwen and Nemotron therefore use 503 pairs; GPT-OSS remains at 504.

| Model | N | Gap, pp | Forward | Critical forward |
|---|---:|---:|---:|---:|
| Qwen3-30B-A3B | 503 | 43.14 | 219 | 85 |
| GPT-OSS-20B | 504 | 4.56 | 42 | 15 |
| Nemotron-3-Nano | 503 | -1.79 | 65 | 22 |

The qualitative three-regime conclusion is unchanged: Qwen is strongly asymmetric, GPT-OSS is mildly asymmetric, and Nemotron is near-symmetric with a slight aggregate reversal.

Cell-level estimates localize the effect but should not be overinterpreted because each category×strategy cell contains only 42 pairs. No cell-level multiplicity-adjusted claims are made.
