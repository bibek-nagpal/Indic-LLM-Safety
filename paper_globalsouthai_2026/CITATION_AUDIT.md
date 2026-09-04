# Corrected citation audit — 2026-09-04

The accepted independent audit checked primary sources, rather than treating bibliography entries as authority.
This revision applies those verified corrections and checks all 18 keys against the compiled bibliography.
No inference/API call was made during this correction pass.

## Verified author corrections

| Work | Correction | Primary source |
|---|---|---|
| Attributional Safety Failures | Shanu Kumar (not Avik Halder); Parag Agrawal (not Amruit) | https://arxiv.org/html/2505.14469v2 |
| Phonetic Perturbations Reveal Tokenizer-Rooted Safety Gaps | Darpan Aswal; Siddharth D Jaiswal | https://arxiv.org/html/2505.14226v5 |
| LinguaSafe | Added Meng Lingyu, encoded as Lingyu, Meng to reproduce the primary-source display order | https://arxiv.org/html/2508.12733v2 |

The phonetic-perturbation entry explicitly identifies v5 and distinguishes first posting in 2025 from revision in 2026.
plainnat ignores bare eprint metadata; relevant preprints now have rendered arXiv identifiers, versions and URLs.

## Directly relevant addition

[Indi-RomCoM](https://arxiv.org/abs/2606.30790v1), Avisha Das, Mihir Parmar, Mohana Ramnath and Pulkit Verma (2026), benchmarks Romanized Indic–English instruction following.
It improves positioning without claiming it is a matched jailbreak-certification study. CSRT and IndicJR are also contrasted explicitly, not merely cited in a list.
Broader additions were not made because they would add bibliography volume without materially sharpening this four-page contribution.

## Primary-source record for the retained references

| Key | Primary record |
|---|---|
| wang2024xsafety | https://aclanthology.org/2024.findings-acl.349/ |
| deng2024multilingual | ICLR 2024 / OpenReview, Multilingual Jailbreak Challenges in Large Language Models |
| yong2023lowresource | https://arxiv.org/abs/2310.02446 ; SoLaR 2023 |
| shen2024languagebarrier | https://aclanthology.org/2024.findings-acl.156/ |
| yoo2025codeswitch | https://aclanthology.org/2025.acl-long.657/ |
| j2024romansetu | https://aclanthology.org/2024.acl-long.833/ |
| khanuja2020gluecos | https://aclanthology.org/2020.acl-main.329/ |
| madhani2023aksharantar | https://aclanthology.org/2023.findings-emnlp.4/ |
| pattnayak2026indicjr | https://aclanthology.org/2026.eacl-industry.50/ |
| banerjee2025attributional | https://arxiv.org/abs/2505.14469v2 |
| aswal2025haet | https://arxiv.org/abs/2505.14226v5 |
| ning2025linguasafe | https://arxiv.org/abs/2508.12733v2 |
| das2026indiromcom | https://arxiv.org/abs/2606.30790v1 |
| mazeika2024harmbench | PMLR 235, pp.35181–35224 (2024) |
| chao2024jailbreakbench | NeurIPS 37 Datasets and Benchmarks (2024) |
| souly2024strongreject | NeurIPS 37 Datasets and Benchmarks (2024) |
| zheng2023judging | NeurIPS 36 Datasets and Benchmarks (2023) |
| wang2024unfair | https://aclanthology.org/2024.acl-long.511/ |

## Claim attachments corrected

- GLUECoS/Aksharantar motivate code-switching/transliteration resources, not an estimate of LLM-user population or default input share.
- RomanSetu concerns romanization and model capability; it does not validate our prompt-pair equivalence.
- StrongREJECT motivates assessing useful assistance, not validation of our exact rubric.
- MT-Bench/Fair Evaluators support concerns about LLM judging, not an allegedly expected ordinal-agreement profile.
- Removed unsupported first-of-kind and predictive-generalization assertions.
- All 18 entries are cited; no undefined citation key, duplicate key, uncited entry or BibTeX warning remains.
