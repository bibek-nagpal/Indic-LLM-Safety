# Phase G cost model

> HISTORICAL MODEL — not a current U-ARCH-v3 cost estimate. The old $1.82 forecast
> does not price the present messages or retry bounds. Use
> [the strong-archaic preflight](STRONG_ARCHAIC_PREFLIGHT_AMENDMENT.md) and its
> machine-readable cost breakdown. No spending is authorized by either file.

All generation, certification and judging unit costs are **measured** from this
repository's own billing ledgers. Target unit prices are the only list-price
inputs, because the V2 target sweep's per-call usage was never persisted.

## Measured unit economics

| Component | Model | Calls observed | In/call | Out/call | USD/call |
|---|---|---:|---:|---:|---:|
| Pair generation | `google/gemini-2.5-flash` | 2,206 | 2,347 | 399 | $0.001408 |
| Primary certification | `deepseek/deepseek-v4-flash` | 2,234 | 1,810 | 2,256 | $0.000742 |
| Secondary certification | `openai/gpt-5-mini` | 1,192 | 1,734 | 2,762 | $0.005932 |
| Response judging | `openai/gpt-5-mini` | 2,054 | 1,983 | 652 | $0.001788 |

## Measured V2 bank-build funnel

- generation calls per accepted pair: **4.38**
- primary auditor pass rate: **53.4%**
- secondary auditor pass rate given a primary pass: **42.3%**
- overall acceptance: **22.6%** of audited candidates

This funnel is recovered from call counts in the accounting ledgers. It is the
closest thing the project has to the V2 certification selectivity that the frozen
six-record attempt log cannot supply.

## Target unit prices

| Target | Input $/M | Output $/M | Mean output tokens | Source |
|---|---:|---:|---:|---|
| `qwen/qwen3-30b-a3b-instruct-2507` | 0.04815 | 0.1931 | 690 | openrouter.ai model page (verified) |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.05 | 0.2 | 1,329 | openrouter.ai model page (verified) |
| `openai/gpt-oss-20b` | 0.1 | 0.5 | 488 | UNVERIFIED: page not retrievable; deliberately conservative upper bound, ~2x the two verified targets |

## Design costs -- expected funnel (2.2 generation calls per accepted pair, 60% primary pass, 60% secondary pass)

| N | Certification | Cross-judge | Gen | Primary | Secondary | Target | Judge | X-judge | **Total** |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 72 | dual | no | $0.22 | $0.12 | $0.56 | $0.05 | $0.41 | $0.00 | **$1.36** |
| 72 | DeepSeek only | no | $0.22 | $0.12 | $0.00 | $0.05 | $0.41 | $0.00 | **$0.80** |
| 72 | dual | yes | $0.22 | $0.12 | $0.56 | $0.05 | $0.41 | $0.41 | **$1.77** |
| 96 | dual | no | $0.30 | $0.16 | $0.75 | $0.07 | $0.54 | $0.00 | **$1.82** |
| 96 | DeepSeek only | no | $0.30 | $0.16 | $0.00 | $0.07 | $0.54 | $0.00 | **$1.07** |
| 96 | dual | yes | $0.30 | $0.16 | $0.75 | $0.07 | $0.54 | $0.54 | **$2.36** |
| 120 | dual | no | $0.37 | $0.20 | $0.94 | $0.08 | $0.68 | $0.00 | **$2.27** |
| 120 | DeepSeek only | no | $0.37 | $0.20 | $0.00 | $0.08 | $0.68 | $0.00 | **$1.33** |
| 120 | dual | yes | $0.37 | $0.20 | $0.94 | $0.08 | $0.68 | $0.68 | **$2.95** |

## Design costs -- conservative funnel (4.38 generation calls per accepted pair, 53% primary pass, 42% secondary pass)

| N | Certification | Cross-judge | Gen | Primary | Secondary | Target | Judge | X-judge | **Total** |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 72 | dual | no | $0.44 | $0.23 | $1.00 | $0.05 | $0.41 | $0.00 | **$2.14** |
| 72 | DeepSeek only | no | $0.44 | $0.23 | $0.00 | $0.05 | $0.41 | $0.00 | **$1.14** |
| 72 | dual | yes | $0.44 | $0.23 | $1.00 | $0.05 | $0.41 | $0.41 | **$2.54** |
| 96 | dual | no | $0.59 | $0.31 | $1.33 | $0.07 | $0.54 | $0.00 | **$2.85** |
| 96 | DeepSeek only | no | $0.59 | $0.31 | $0.00 | $0.07 | $0.54 | $0.00 | **$1.52** |
| 96 | dual | yes | $0.59 | $0.31 | $1.33 | $0.07 | $0.54 | $0.54 | **$3.39** |
| 120 | dual | no | $0.74 | $0.39 | $1.66 | $0.08 | $0.68 | $0.00 | **$3.56** |
| 120 | DeepSeek only | no | $0.74 | $0.39 | $0.00 | $0.08 | $0.68 | $0.00 | **$1.89** |
| 120 | dual | yes | $0.74 | $0.39 | $1.66 | $0.08 | $0.68 | $0.68 | **$4.24** |

## Recommended design

- **N = 96, dual certification, no additional GPT-5 Mini cross-judge**
- expected total: **$1.82**
- expected-high (conservative funnel *and* a GPT-5 Mini cross-judge): **$3.39**
- **hard spending ceiling: $10.00** -- roughly 3x expected-high, enforced by the
  runner's live cost accounting, which aborts before exceeding it

## Dominant cost

Secondary certification with GPT-5 Mini dominates every configuration. At $0.005932 per call it is 8.0x the DeepSeek per-call cost, and it accounted for $7.07 of the $11.84 spent building the
entire V2 bank. Target inference is negligible by comparison: the three open
targets together cost well under a dollar at every N considered.

Dropping to DeepSeek-only certification would save roughly $0.75 at N=96. The preregistration keeps dual certification anyway: the recovered V1
evidence shows single-auditor certification is exactly the failure mode that made
V1 unusable, and a few dollars is not worth reintroducing it.
