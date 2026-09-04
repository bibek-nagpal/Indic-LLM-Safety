# Completed co-author annotation record — 2026-09-05

This note records the completed workshop-specific human audit and the author-supplied participant facts used in the manuscript. The authoritative private workbook is `C:\Prahlada\Human_A_annotations.xlsx`, SHA-256 `535a59facb9f662e86d7c8f7063431fd7cee064f20b10e7dcda4f92c25bf8fbb`. The workbook is intentionally not tracked because it contains harmful prompts, target responses and private item mappings.

## Annotator facts

- The annotator was an unpaid co-author, comfortable reading English and conversational Romanized Hindi.
- They knowingly and voluntarily agreed to annotate after being informed that the material could be harmful or sensitive.
- They read the instructions, completed the familiarization examples and scored without AI assistance.
- They necessarily saw prompts and target responses, but were blinded to automated-judge scores and aggregate experimental results.
- No formal institutional ethics/IRB review or approval was obtained.

These facts support describing the exercise as an exploratory single-co-author audit. It is not external validation, human consensus or a substitute for language-model-only pair certification.

## Verified data flow

- Intended: 180 pair-model jobs / 360 response items, selected without reference to automated outcomes.
- Valid labels: 357; three labels are blank (item numbers 314, 319 and 320).
- Stimulus verification: Three labeled rows fail byte verification against the frozen source (prompt mismatches at item numbers 70 and 262; response mismatch at item number 273). They are excluded without repair.
- Analysis set: 354 verified scored items and 174 complete pair-model jobs.
- Analyzed-item breakdown: GPT-OSS 119, Nemotron 117, Qwen 118; gambling 88, intoxication 89, sexual violence 89, violence 88; RolePrompting 118, ScenarioNesting 117, SymbolicMasking 119; English 174, Romanized Hindi 180.
- Label validity: no nonblank malformed or out-of-range labels; no unreadable flags.

The exclusions affect only this human-audit analysis. They do not alter the frozen 504-pair bank, the 3,024 target responses, automated scores or validated headline results.

## Reproducibility

`analysis/human_a_validation.py` verifies item identity against the frozen selection manifest and source artifacts, excludes unverifiable stimuli, and computes agreement and paired-language summaries. Confidence intervals use 5,000 pair-model-job cluster-bootstrap resamples with seed 20260904. `analysis/human_a_results.json` records the input hash, validation checks, denominators, exclusions and outputs.

No public preregistration or other externally binding statement requiring a different human-annotation design was found in the repository. Historical internal planning files outside this workshop package are not evidence of a completed additional annotation.
