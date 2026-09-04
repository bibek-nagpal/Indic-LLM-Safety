# Numerical consistency audit

Every headline number in the compiled PDF, checked against
`analysis/headline_verification.json` and `analysis/human_a_results.json`,
Point estimates are checked against frozen artifacts; confidence intervals are reused
from validated Phase B and the unchanged Human A result JSON, never redrawn.

| check | string required in PDF | status | detail |
|---|---|---|---|
| bank size 504 | `504` | PASS | source=True pdf=True |
| responses per model 1,008 | `1,008` | PASS | source=True pdf=True |
| total responses 3,024 | `3,024` | PASS | source=True pdf=True |
| pair-model observations 1,512 | `1,512` | PASS | source=True pdf=True |
| cells 12 x 42 | `42 accepted` | PASS | source=True pdf=True |
| Qwen EN 65.9 | `65.9` | PASS | source=True pdf=True |
| Qwen RH 22.8 | `22.8` | PASS | source=True pdf=True |
| Qwen gap +43.1 | `43.1` | PASS | source=True pdf=True |
| Qwen CI [38.5, 47.6] | `[38.5, 47.6]` | PASS | source=True pdf=True |
| Qwen critical flips 85 | `85 of 504` | PASS | source=True pdf=True |
| Qwen critical pct 16.9 | `16.9` | PASS | source=True pdf=True |
| GPT-OSS gap +4.6 | `4.6` | PASS | source=True pdf=True |
| GPT-OSS validated CI | `[1.4, 7.7]` | PASS | source=True pdf=True |
| Nemotron validated CI | `[-6.5, 2.8]` | PASS | source=True pdf=True |
| Nemotron gap -1.8 | `1.8` | PASS | source=True pdf=True |
| Nemotron fwd 65 rev 70 | `(65 forward, 70 reverse)` | PASS | source=True pdf=True |
| human exact 74.7 | `74.7` | PASS | source=True pdf=True |
| human adjacent 94.0 | `94.0` | PASS | source=True pdf=True |
| human kappa 0.513 | `0.513` | PASS | source=True pdf=True |
| human qwk 0.825 | `0.825` | PASS | source=True pdf=True |
| human CI [69.4, 79.9] | `[69.4, 79.9]` | PASS | source=True pdf=True |
| human higher 58 lower 14 | `on 58 items and lower on 14` | PASS | source=True pdf=True |
| human n 285 | `285` | PASS | source=True pdf=True |
| human GPT5 exact rounding | `79.6%` | PASS | source=True pdf=True |
| human GPT5 QWK rounding | `0.885` | PASS | source=True pdf=True |
| items returned 287 | `287` | PASS | source=True pdf=True |
| unscored 73 of 360 | `73 of 360` | PASS | source=True pdf=True |
| binary agreement 88.8 | `88.8` | PASS | source=True pdf=True |
| human Qwen gap +53.1 | `53.1` | PASS | source=True pdf=True |
| fallback 2 of 3,024 | `2 of 3,024` | PASS | source=True pdf=True |

## Stale / forbidden phrase sweep

Searched for: `1,512 unique`, `1512 unique prompt pairs`, `Logical Appeal`, `two human annotators`, `inter-annotator agreement`, `human consensus`, `ground truth`, `Phase G`, `archaic`

**Result:** no hits

## Required-disclaimer sweep

Searched for: `single annotator`, `make no inter-annotator`, `not completed`, `No usable Annotator B labels`, `retained the seed instruction unchanged`, `cascade`, `the same model`, `language was not blinded`, `both inputs use Latin script`, `completion-conditional`, `SequenceMatcher`, `Cross-bank consolidation removed exact matches only`, `no direct-request and no benign condition`, `not covariate adjustment`, `unpaid co-author`, `retrospective clarification`, `without AI assistance`, `73 unscored`, `No usable Annotator B labels`

**Result:** all present

## Verdict

**PASS** — 30/30 checks pass.
