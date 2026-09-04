# Citation audit

Every entry in `references.bib` was independently verified against ACL Anthology, DBLP,
PMLR, NeurIPS proceedings, arXiv or OpenReview. **No citation was invented; nothing
unverifiable is cited.**

| key | claim it supports | verification source | metadata | claim support | action |
|---|---|---|---|---|---|
| `wang2024xsafety` | multilingual safety benchmarks compare native scripts | aclanthology.org/2024.findings-acl.349 | corrected: title is "…of LLMs"; author "Lyu, Michael" | supports | metadata fixed |
| `deng2024multilingual` | non-English input degrades refusal | dblp ICLR 2024 | correct | supports | none |
| `yong2023lowresource` | low-resource translation degrades refusal | neurips.cc/virtual/2023/78913 | correct (SoLaR workshop) | supports | none |
| `shen2024languagebarrier` | multilingual safety degradation, mechanism-level | aclanthology.org/2024.findings-acl.156 | correct | supports | **added** |
| `yoo2025codeswitch` | code-switching is a distinct attack surface | aclanthology.org/2025.acl-long.657 | correct | supports | none |
| `j2024romansetu` | Romanized Indic text is rare in curated data | aclanthology.org/2024.acl-long.833 | casing corrected | supports | metadata fixed |
| `khanuja2020gluecos` | code-mixed South Asian text is pervasive | aclanthology.org/2020.acl-main.329 | correct | supports | **added** |
| `madhani2023aksharantar` | Romanized/transliterated Indic resources | aclanthology.org/2023.findings-emnlp.4 | correct | supports | **added** |
| `pattnayak2026indicjr` | judge-free South Asian jailbreak evaluation | aclanthology.org/2026.eacl-industry.50 | DOI + pages added | supports | metadata fixed |
| `banerjee2025attributional` | code-mixed perturbation attack surface | arxiv.org/abs/2505.14469 | correct, preprint | supports | none |
| `aswal2025haet` | phonetic perturbation attack surface | arxiv.org/abs/2505.14226 | correct (paper retitled across versions) | supports | none |
| `ning2025linguasafe` | multilingual safety benchmark | arxiv.org/abs/2508.12733 | correct, preprint | supports | none |
| `mazeika2024harmbench` | standard safety benchmarks are English-centric | proceedings.mlr.press/v235/mazeika24a | correct | supports | none |
| `chao2024jailbreakbench` | standard safety benchmarks are English-centric | NeurIPS 2024 D&B proceedings | URL corrected to proceedings | supports | metadata fixed |
| `souly2024strongreject` | scale should reward specificity, not engagement | NeurIPS 2024 D&B proceedings | URL corrected to proceedings | supports | metadata fixed; **now cited in text** |
| `zheng2023judging` | LLM-as-judge agreement profile | NeurIPS 2023 D&B proceedings | correct | supports | **added** |
| `wang2024unfair` | LLM judges are not reliable evaluators | aclanthology.org/2024.acl-long.511 | correct | supports | **added** |

## Corrections applied

1. **`khattab2024dspy` removed.** The previous bibliography paired the arXiv title
   ("…into Self-Improving Pipelines") with the ICLR 2024 venue, whose actual title is
   "…into State-of-the-Art Pipelines" — a genuine mis-attribution. The workshop paper does
   not need it, so it was dropped rather than carried with a corrected entry.
2. Five metadata corrections applied (see table).
3. Five verified works added: `shen2024languagebarrier`, `khanuja2020gluecos`,
   `madhani2023aksharantar`, `zheng2023judging`, `wang2024unfair`.
4. A stray `}` that would have broken BibTeX in the source bibliography was not carried
   into this manuscript's `references.bib`.

## Mechanical checks

- `bibtex main` runs with **no errors and no warnings**.
- **0** undefined citations in the final `.log`.
- **0** `[?]` markers in the compiled PDF.
- Every entry in `references.bib` is cited at least once (17 entries, 17 cited).
