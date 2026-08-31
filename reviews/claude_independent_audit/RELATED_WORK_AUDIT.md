# Related Work and Positioning Audit

Independent verification of `paper/references.bib` against primary sources, plus a search for directly relevant literature the manuscript omits.

**Bibliographic discipline:** every entry below that I recommend adding was located via web search and, where marked "verified", confirmed against the arXiv/ACL Anthology record. Entries marked "**verify before citing**" are ones where I saw the title in a search result but did not open the primary record; do not enter them into the `.bib` on my word alone.

---

## 1. Existing citations — verification

| Key | Status | Notes |
|---|---|---|
| `wang2024xsafety` | Consistent | XSafety, Findings of ACL 2024, ten languages. Characterisation in §2 is fair. |
| `deng2024multilingual` | Consistent | Deng et al., ICLR 2024. "larger vulnerabilities in lower-resource settings" is a fair summary. |
| `yoo2025codeswitch` | Consistent | Yoo, Yang & Lee, ACL 2025 Long Papers. Code-switching red-teaming. Correctly cited. |
| `j2024romansetu` | Consistent | RomanSetu, ACL 2024. The claim that "romanization materially changes tokenization and multilingual representations" matches the paper's thesis. |
| `ning2025linguasafe` | Consistent as an arXiv preprint (2508.12733). **Table 1 asserts "No RH track"** — I could not open the primary record within this audit (fetch blocked), so this cell is currently unverified. Either verify it directly or soften to "no Romanized-Indic track reported". A negative claim about another benchmark is exactly what a reviewer will check. |
| `pattnayak2026indicjr` | **Verified.** EACL 2026 Industry Track, also arXiv:2602.16832. 12 South Asian languages, 45,216 prompts, JSON/Free tracks, judge-free rule-based detector with human audit. The manuscript's row ("Language/script variants · No hard dual gate · Rule-based binary · JSR/orthography contrasts · Yes") is accurate. **But see §3.1 — the paper omits IndicJR's central finding, which cuts against its own.** |
| `mazeika2024harmbench` | Consistent. ICML 2024. "Binary classifier / Aggregate ASR / not paired / no romanization" is fair. |
| `chao2024jailbreakbench` | Consistent. NeurIPS 2024 D&B. Fair characterisation. |
| `souly2024strongreject` | Consistent. NeurIPS 2024 D&B. "Graded usefulness" and the over-statement critique are correctly represented. |
| `khattab2024dspy` | Consistent (ICLR 2024). |
| `agrawal2026gepa` | Bibliographically consistent (ICLR 2026, arXiv:2507.19457). **But the citation is methodologically unsupported** — see `METHODOLOGY_AUDIT.md` §3: no prompt evolution occurred. Citing GEPA for a component that produced a single seed candidate is the kind of thing a reviewer who knows the GEPA paper will notice. Remove or recast as "we use the DSPy/GEPA metric harness to evaluate, not to evolve". |

**No fabricated or malformed entry was found.** Volumes, page ranges, DOIs, and URLs are consistent with the anthology records.

---

## 2. The bibliography is too thin for an ACL Related Work

Eleven references, of which two are tooling (DSPy, GEPA). Nine substantive citations for a paper positioned against "multilingual jailbreak/safety benchmarks, Romanized/code-switched safety work" is below what an ACL committee expects, and — more importantly — the omissions are not peripheral. Two of them are direct novelty threats.

---

## 3. Missing work that materially affects the novelty claim

### 3.1 Banerjee et al., "Attributional Safety Failures in Large Language Models under Code-Mixed Perturbations" (arXiv:2505.14469v2, 30 Nov 2025) — **the most serious omission**
*Verified.* Authors: Somnath Banerjee, Pratyush Chatterjee, Shanu Kumar, Sayan Layek, Parag Agrawal, Rima Hazra, Animesh Mukherjee.

Why it matters: this paper already does the core thing IndicAlignProbe claims as its contribution.
- **Matched paired prompts**: original English queries paired with linguistically equivalent code-mixed versions, constructed via the Matrix Language Frame model at a controlled 60:40 matrix-to-embedded ratio.
- Ten languages **including Hindi**.
- ASR rises from ~9% monolingual English to ~69% code-mixed, exceeding 90% for Hindi and Arabic.
- **Human validation across six languages, Fleiss κ = 0.76–0.81** — precisely the validation IndicAlignProbe does not yet have.
- Plus a mechanistic account (attribution mass migrating off safety-critical tokens) and a mitigation.

The Introduction currently asserts that aggregate ASR benchmarks "do not necessarily answer whether a language/register change alters behavior for an otherwise matched request." A reviewer holding this citation will reply that a matched-pair code-mixed study with human validation already answered it, at ten languages.

**What survives as genuine differentiation** — and what the paper must argue explicitly rather than by omission:
1. **Latin-script Romanized Hinglish**, not native-script code-mixing (Banerjee et al. use Devanagari for Hindi). Given RomanSetu's tokenisation argument, this is a real and defensible distinction.
2. **Per-pair dual-LLM certification** with a deterministic acceptance predicate over nine axes, versus rule-based MLF construction. Equivalence is *audited per item*, not assumed by construction.
3. **Graded 0–3 severity** rather than binary ASR.
4. **Cross-model heterogeneity as the headline** — Banerjee et al. report a broadly consistent collapse; IndicAlignProbe's central result is that the effect is strongly model-dependent (43 / 4.6 / −1.8 pp). This is arguably the paper's strongest and least contested contribution and deserves more weight in the framing.

### 3.2 Aswal & Jaiswal, "'Haet Bhasha aur Diskrimineshun': Phonetic Perturbations in Code-Mixed Hinglish to Red-Team LLMs" (arXiv:2505.14226v3) — **most on-topic omission**
*Verified.* Darpan Aswal (Université Paris-Saclay), Siddharth D Jaiswal (IIT Kharagpur). Code-mixed Hinglish red-teaming with deliberate phonetic misspelling of sensitive tokens; 99% average ASR on text (ChatGPT-4o-mini, Llama-3-8B-Instruct, Gemma-1.1-7b-it, Mistral-7B-Instruct-v0.3) and 78% on image generation.

This is *the* prior Hinglish red-teaming paper. A paper titled "…Refusal Asymmetry in Hinglish" that does not cite it will read as an incomplete literature search to any multilingual-safety reviewer. It is also a useful contrast for the paper's own framing: Aswal & Jaiswal maximise attack success by *adding* orthographic perturbation, whereas IndicAlignProbe deliberately holds everything but register constant. That contrast is a positioning asset, not a threat.

### 3.3 Yong, Menghini & Bach, "Low-Resource Languages Jailbreak GPT-4" (arXiv:2310.02446)
*Verified by search; venue is a NeurIPS 2023 workshop (SoLaR) — confirm the exact venue string before citing.* This is the canonical origin point for the cross-lingual safety-transfer literature and is standardly cited in every paper in this space. Its absence is conspicuous.

### 3.4 IndicJR's actual finding contradicts the paper's, and is not engaged
The manuscript cites IndicJR only for scope. IndicJR's abstract reports: "Orthography matters: **romanized or mixed inputs reduce JSR** under JSON, with correlations to romanization share and tokenization (approx 0.28 to 0.32)." That is, in IndicJR's setting romanization *reduced* jailbreak success — the opposite direction from IndicAlignProbe's Qwen result.

This is not a problem for the paper; it is an opportunity, and it is exactly what the paper's model-heterogeneity finding is positioned to explain. But leaving it unmentioned while citing the paper looks like selective reading. Add two sentences noting the divergence and offering the model-dependence result plus the differing scoring protocol (rule-based binary detector vs. graded LLM rubric) as candidate explanations.

### 3.5 Lower-priority additions (**verify before citing**)
- **Indi-RomCoM: Code-Mixed Benchmark for Evaluating LLMs on Romanized Indic-English Instructions** (arXiv:2606.30790). Directly relevant to Romanized Indic evaluation; I have title only.
- **Multilingual Blending: LLM Safety Alignment Evaluation with Language Mixture** (arXiv:2407.07342). Language-mixture safety; title only.
- **MLingualFC: Evaluating Jailbreak Vulnerabilities in Multilingual Vision-Language Models** (arXiv:2606.07706; also ACL Anthology 2026.mellm-1.22). Peripheral (vision-language) but shows the venue's current interest.

---

## 4. Table 1 assessment

The positioning table is a good idea, well constructed, and the caption's disclaimer ("'No hard dual gate' does not imply poor translation quality") is exactly the right defensive move. Three problems:

1. **The comparison set is now incomplete.** With Banerjee et al. omitted, the "Paired language: Yes" column is uniquely IndicAlignProbe's — which is the table's whole rhetorical payload, and it is no longer true. Banerjee et al. must be a row, with "Per-pair equivalence: MLF construction, not per-item audited" as the honest differentiator.
2. **The LinguaSafe "No RH track" cell is an unverified negative claim** about another team's resource. Verify or soften.
3. **Consider a "Human validation" column.** It is the dimension on which the paper is currently weakest (Phase E pending) and on which Banerjee et al. are strong. Including it is more credible than omitting it, and it makes the pending Phase E study read as a planned commitment rather than a gap.

---

## 5. Novelty verdict

**The novelty claim as currently written is over-broad; the underlying contribution is real but narrower.**

Not defensible as stated: that matched-pair, equivalence-controlled attribution for language-conditioned safety is new (Banerjee et al. 2025), or that Hinglish red-teaming is unexplored (Aswal & Jaiswal 2025).

Defensible, and what the paper should lead with:
- **Per-item certified equivalence** with a two-family deterministic acceptance predicate over nine axes and strategy structure — genuinely stronger than construction-by-rule or translation-plus-refinement, and the paper's real methodological contribution.
- **Romanized Latin-script Hinglish specifically**, with RomanSetu's tokenisation argument as the motivation for treating it separately from native-script code-mixing.
- **Graded 0–3 severity with explicit forward/critical flip definitions**, prespecified before analysis.
- **Model-dependent regimes as the headline finding.** This is the paper's most defensible and least-anticipated result: the same 504 frozen probes produce a 43 pp gap on one model and none on another. It is also the natural explanation for why IndicJR and Banerjee et al. report different directions. Lead with it.

Recommended reframing: the contribution is *a measurement instrument with per-item certified equivalence, and the finding that language-conditioned safety robustness is strongly model-dependent* — not the discovery that code-switching degrades safety, which is established.

---

## 6. Required actions

1. **Must add** (novelty-critical): Banerjee et al. 2025 (2505.14469); Aswal & Jaiswal 2025 (2505.14226); Yong et al. 2023 (2310.02446).
2. **Must engage**: IndicJR's romanization-reduces-JSR finding (§3.4).
3. **Must verify or soften**: the LinguaSafe "No RH track" cell.
4. **Must fix**: the `agrawal2026gepa` citation, which asserts a method component the artifacts do not support.
5. **Should add**: a Banerjee et al. row and a human-validation column to Table 1.
6. **Should reframe**: novelty around per-item certification + model heterogeneity, not around matched-pair attribution per se.

Sources consulted:
- [IndicJR (ACL Anthology)](https://aclanthology.org/2026.eacl-industry.50/) · [arXiv:2602.16832](https://arxiv.org/abs/2602.16832)
- [Attributional Safety Failures under Code-Mixed Perturbations (arXiv:2505.14469)](https://arxiv.org/html/2505.14469)
- ["Haet Bhasha aur Diskrimineshun" (arXiv:2505.14226)](https://arxiv.org/html/2505.14226v3)
- [Low-Resource Languages Jailbreak GPT-4 (arXiv:2310.02446)](https://arxiv.org/abs/2310.02446)
- [Indi-RomCoM (arXiv:2606.30790)](https://arxiv.org/html/2606.30790)
- [Multilingual Blending (arXiv:2407.07342)](https://arxiv.org/html/2407.07342v1)
