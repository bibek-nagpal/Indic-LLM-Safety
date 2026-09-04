# Numerical consistency audit

Every headline number in the compiled PDF, checked against
`analysis/headline_verification.json` and `analysis/human_a_results.json`.
Point estimates are checked against frozen artifacts; confidence intervals are reused
from validated Phase B and the completed Human A result JSON; only its fixed-seed
job-cluster bootstrap was recomputed for the completed workbook.

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
| human exact 69.2 | `69.2` | PASS | source=True pdf=True |
| human adjacent 92.9 | `92.9` | PASS | source=True pdf=True |
| human kappa 0.485 | `0.485` | PASS | source=True pdf=True |
| human qwk 0.794 | `0.794` | PASS | source=True pdf=True |
| human CI [63.8, 74.1] | `[63.8, 74.1]` | PASS | source=True pdf=True |
| human higher 91 lower 18 | `on 91 items and lower on 18` | PASS | source=True pdf=True |
| human analyzed n 354 | `354 analyzed items` | PASS | source=True pdf=True |
| human GPT5 exact rounding | `75.1%` | PASS | source=True pdf=True |
| human GPT5 adjacent rounding | `92.7%` | PASS | source=True pdf=True |
| human GPT5 kappa rounding | `0.589` | PASS | source=True pdf=True |
| human GPT5 QWK rounding | `0.851` | PASS | source=True pdf=True |
| human GPT5 CI rounding | `[70.1, 79.9]` | PASS | source=True pdf=True |
| items with valid labels 357 | `357 scored items` | PASS | source=True pdf=True |
| blank labels 3 of 360 | `Three of 360 labels are blank` | PASS | source=True pdf=True |
| complete jobs 174 | `174 verified jobs` | PASS | source=True pdf=True |
| binary agreement 87.9 | `87.9` | PASS | source=True pdf=True |
| human Qwen gap +37.9 | `37.9` | PASS | source=True pdf=True |
| same-pairs Qwen judge gap +36.2 | `36.2` | PASS | source=True pdf=True |
| fallback 2 of 3,024 | `2 of 3,024` | PASS | source=True pdf=True |

## Stale / forbidden phrase sweep

Searched the configured legacy-claim and forbidden-phrase regression list.

**Result:** no hits

## Required-disclaimer sweep

Searched for: `single co-author`, `make no inter-annotator`, `not completed`, `retained the seed instruction unchanged`, `cascade`, `the same model`, `language was not blinded`, `both inputs use Latin script`, `SequenceMatcher`, `Cross-bank consolidation removed exact matches only`, `no direct-request and no benign condition`, `not covariate adjustment`, `unpaid co-author`, `without AI assistance`, `voluntarily agreed`, `automated-judge scores`, `aggregate experimental results`, `357 contain valid scores`, `three labels are blank`, `Three labeled rows fail`, `174 complete pair-model jobs`, `No formal institutional ethics/IRB review or approval was obtained.`

**Result:** all present

## Verdict

**PASS** — 35/35 checks pass.
