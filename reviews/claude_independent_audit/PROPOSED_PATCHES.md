# Proposed Manuscript Patches

**Not applied.** `paper/acl_latex.tex` is unchanged. Line numbers refer to the canonical manuscript at commit `31d5732`.

Every patch below is supported by evidence in this audit and requires **no new API calls and no new data**. Patches are grouped by priority. Space impact is noted, since the paper is at eight pages.

---

## P0 — Blocking. Do not submit without these.

### P0-1 · §4.1 (line 106–108) — remove the unsupported GEPA optimisation claim
*Evidence:* `METHODOLOGY_AUDIT.md` §3. The frozen GEPA state has one program candidate with `parent_program_for_candidate: [[None]]`, a null Pareto summary, one reflection call, 24 evaluations, $0.0302 spend, and only `iter_0_prog_0.json` outputs.

**Replace** (lines 106–108, from "We use \gepa within DSPy" through "The generator instruction is frozen before bank construction."):

> The generator is \texttt{google/gemini-2.5-flash}. It produces English/RH candidates from a harm-category and strategy specification under fixed construction invariants and a fixed supplementary guidance instruction. The guidance is authored by hand, is frozen before bank construction, and is target-independent by construction: it neither references nor is conditioned on any target model.
>
> We validate the guidance offline against a target-independent probe-validity metric: the fraction of 13 hard constraints satisfied (nine paired axes, RH not stronger than English, probe eligibility, correct harmful-category membership, and direct harmful facilitation with non-benign purpose). Over a 12-item development set the metric was evaluated on 30 candidates using the DSPy harness; every evaluation record carries \texttt{target\_model\_called=false}, and the procedure produced no accepted revision to the guidance. No target-model response, refusal, judge score, or flip outcome enters the metric or the instruction.

**Also:** remove `agrawal2026gepa` from the citation on line 106 (retain `khattab2024dspy` for the DSPy harness), and delete the `\gepa` macro from line 22 if it becomes unused. Update the contribution bullet at line 48 if it mentions optimisation.

### P0-2 · Appendix B (lines 253–259) — retitle and recast
**Change** the section title from `\section{GEPA Objective}` to `\section{Target-Independent Probe-Validity Metric}`.

**Replace** the closing sentence ("Natural-language feedback lists failed constraints… during generation.") with:

> The metric is a validation diagnostic, not an optimisation objective: no target-model response, refusal, judge score, or forward/critical flip enters $Q$, and the procedure produced no accepted revision to the generator guidance. The manifest records \texttt{gepa\_target\_signal\_used=false} and an empty target-model list during generation, and every development-set evaluation record carries \texttt{target\_model\_called=false}.

*Net space: neutral.*

### P0-3 · Repository, referenced from Appendix A (line 251)
Commit `prompts/optimized/gepa_20260826_135819/` in full — `generator.txt` (SHA-256 `025fbd35…`, matching the bank manifest's `gepa_instruction_sha256`), `optimization_manifest.json`, `metric_log.jsonl`, `api_accounting.json`, `gepa_logs/`. Amend `.gitignore`, which currently whitelists only the obsolete `gepa_20260523_130239/`. Remove that directory or move it under a clearly labelled `historical/` path.

Then **append to line 251**, after "the final bank manifest hashes the generator guidance and records both auditor model slugs":

> The verbatim guidance instruction is archived alongside the parser, and its SHA-256 matches the value recorded in the bank manifest.

*Rationale:* without this, `probe_bank.py` cannot even execute from the release — `load_optimized_instruction(require_v2=True)` rejects the committed directory for lacking `optimization_manifest.json`.

### P0-4 · Global — rename the headline construct
*Evidence:* `STATISTICAL_AUDIT.md` §10. Not one of Qwen's 115 Hinglish score-0 responses is under 80 characters; 114 of 115 exceed 500.

Replace "refusal gap" with **"non-assistance gap"** and "refusal rate" with **"non-assistance rate"** throughout (abstract line 34; §3 lines 94–98; Table 2 headers line 148 and caption line 155; §5.1; Table 3 line 191; figures). Keep the symbol $R$ and the definition $R=\indicator[s=0]$.

**Add after line 98** (after "The *pair ID*, not an individual response, is the experimental and resampling unit."):

> We write $R$ as \emph{non-assistance} rather than refusal because score 0 covers any response without domain-specific harmful content, including verbose non-answers. The distinction is material and asymmetric: 61\% of \qwen's English score-0 responses are under 80 characters, whereas none of its 115 RH score-0 responses are, and 114 exceed 500 characters (Appendix~\ref{app:nonassistance}).

**Add** a short appendix `\label{app:nonassistance}` with the six-row table from `STATISTICAL_AUDIT.md` §10.

*Net space: +4 lines main text, +1 short appendix table.*

### P0-5 · §5.3 (line 178–180) — decompose the length signal
*Evidence:* `STATISTICAL_AUDIT.md` §4. Both-safe pairs contribute 65:0 (Qwen), 22:2 (GPT-OSS), 12:58 (Nemotron).

**Append after line 180** ("…but it is independent of both LLM judges."):

> This signal is judge-independent but not judge-equivalent. Decomposing by the primary judge's own verdict, the shapes concentrate in judge-identified flips (\qwen: 136 of 219 forward flips are forward-shaped, none reverse-shaped; \nemo: 59 of 70 reverse flips are reverse-shaped) but a substantial share arises among pairs scored 0 in \emph{both} languages: 65:0 for \qwen, 22:2 for \gptoss, and 12:58 for \nemo. Among those judged-safe pairs \qwen's median response length is 48 characters in English and 4{,}366 in RH. Response length therefore corroborates a language-conditioned change in \emph{response behaviour}, of which the flip component is the safety-relevant part; it is not an independent measure of harmfulness.

**Also amend the abstract, line 34.** Replace "A judge-independent response-length check reproduces the same directional ordering." with:

> A judge-independent response-length check reproduces the same directional ordering, though it partly reflects language-conditioned verbosity rather than harmfulness alone.

*Net space: +6 lines. Recover from P2-2.*

---

## P1 — Strongly recommended. These convert two likely rejects into supporters.

### P1-1 · §5.1 (line 161) and abstract — soften the three-regime claim
*Evidence:* `STATISTICAL_AUDIT.md` §2.2 and §9.2. The GPT-OSS − Nemotron contrast crosses zero under prompt-cluster resampling at Jaccard ≥ 0.65 (p = .060 → .102 unadjusted) and is 4.32 [−3.09, 11.42] under Gemini vs 11.73 [3.70, 19.14] under GPT-5 Mini on the shared subset.

**Append after line 161:**

> The \qwen contrasts are robust to every sensitivity we ran. The \gptoss{}--\nemo contrast is not: its interval crosses zero when near-duplicate prompt clusters rather than pair IDs are resampled (Appendix~\ref{app:clusters}), and it is 4.32 pp (95\% CI $-3.09$--11.42) under the primary judge but 11.73 (3.70--19.14) under GPT-5 Mini on the shared cross-judge subset. We therefore claim only that \qwen is robustly distinct from both other models; \gptoss and \nemo differ in point estimate and in the sign of the \nemo effect, but are not reliably separated by this design.

**Line 159:** change "Table~\ref{tab:main} shows three distinct regimes." to "Table~\ref{tab:main} shows a strongly graded pattern."
**Line 233 (Conclusion):** keep the descriptive sentence but drop any implication that all three are pairwise distinguishable.

### P1-2 · New appendix — prompt-similarity and cluster-robust sensitivity
*Evidence:* `STATISTICAL_AUDIT.md` §2.

Add `\label{app:clusters}` containing: (a) the statement that deduplication was exact-string after NFKC + casefold + whitespace collapse, with no fuzzy or semantic deduplication; (b) mean within-cell English-prompt Jaccard 0.254 against a 0.138 random cross-bank baseline, with 141 within-cell pairs above 0.62 and a maximum of 0.921; (c) the five-row cluster-bootstrap table; (d) the eight-row contrast-sensitivity table.

**Also:** remove or explain `near_duplicate_threshold: 0.85` in `probe_banks/.../manifest.json`. It is advertised and was never applied; a reviewer inspecting the manifest will read it as a guarantee.

### P1-3 · §4.4 / §5 — report the truncation asymmetry
*Evidence:* `STATISTICAL_AUDIT.md` §5.

**Append to §4.4 after line 130:**

> Responses reaching the 4{,}096-token cap were scored as issued. Truncation is asymmetric for two targets (\qwen: 0 English versus 22 RH, exact $p=4.8\times10^{-7}$; \nemo: 77 versus 35, $p=1.7\times10^{-5}$; \gptoss: 47 versus 55, n.s.). Dropping every pair-model job with a truncation on either side leaves gaps of 43.36, 4.73, and $-0.50$ pp, so the headline estimates are not driven by truncation; critical-flip counts are more sensitive (\nemo 22/10 becomes 16/8).

### P1-4 · §5.4 (line 205) — report per-condition cross-judge agreement
*Evidence:* `STATISTICAL_AUDIT.md` §9.1.

**Append after line 205:**

> Agreement is strongly heterogeneous across conditions: 89.8\% and 88.9\% for \gptoss English and RH, 71.6\% and 53.1\% for \qwen English and RH, and 66.3\% and 72.2\% for \nemo. The judges therefore agree least on the \qwen RH responses that produce the largest effect, and GPT-5 Mini scores higher in every condition (mean difference $+0.13$ to $+0.61$), indicating a calibration shift rather than symmetric noise. On this subset the \gptoss gap interval includes zero under both judges, so the subset confirms the point estimate without confirming the effect.

### P1-5 · §2 Related Work (lines 57–63) and Table 1 — bring the literature current
*Evidence:* `RELATED_WORK_AUDIT.md` §3.

**Insert into the first paragraph, after the IndicJR sentence at line 58:**

> Closest to our design, \citet{banerjee2025attributional} construct matched English and code-mixed prompt pairs across ten languages using a Matrix Language Frame construction and report attack-success rates rising from roughly 9\% to 69\% under code-mixing, with human validation in six languages. \citet{aswal2025haet} red-team LLMs with phonetically perturbed code-mixed Hinglish. Our design differs in three ways: we study Latin-script Romanized Hinglish rather than native-script code-mixing; equivalence is certified per item by two independent auditor families rather than imposed by a construction rule; and our estimand is a graded, model-resolved severity difference rather than aggregate attack success. Earlier cross-lingual work established the base phenomenon \citep{yong2023lowresource}.

**Insert after the paragraph at line 60:**

> These results do not agree on direction. IndicJR reports that romanized and mixed inputs \emph{reduce} jailbreak success under its contract-bound track, whereas we observe a large RH degradation for one target and none for another. Our model-resolved result suggests one reconciliation: the sign of the orthography effect may be model-dependent, so aggregate estimates pooled over models can point either way. Differences in scoring protocol---a rule-based binary detector versus a graded LLM rubric---may contribute as well.

**Table 1 (lines 65–83):** add a row for \citet{banerjee2025attributional} (Paired language: Yes, multilingual; Per-pair equivalence: construction rule, not per-item audited; Response score: binary ASR; Estimand: cross-language ASR shift; Romanized or mixed: native-script code-mixing; Intended use: diagnostic study). Consider adding a "Human validation" column. **Verify the LinguaSafe "No RH track" cell against the primary source or soften it to "no Romanized-Indic track reported"** — it is currently an unverified negative claim about another team's resource.

**`references.bib`:** add Banerjee et al. (arXiv:2505.14469), Aswal & Jaiswal (arXiv:2505.14226), Yong et al. (arXiv:2310.02446). Confirm the Yong et al. venue string against the primary record before entering it.

**§1 (line 41):** soften "Aggregate attack-success benchmarks answer whether an attack set succeeds. They do not necessarily answer whether a language/register change alters behavior for an otherwise matched request." to acknowledge that matched-pair code-mixed work exists and that the contribution is per-item certified equivalence plus model-resolved heterogeneity.

*Net space: +12 lines and one table row. This is the largest space cost in the patch set; see P2-2 for recovery.*

### P1-6 · §7 Limitations (line 219–220) — disclose the non-blind judge
**Append to the "Model-based measurement" paragraph:**

> The response judge receives the prompt and an explicit language tag, so it is not blind to the condition it scores; the cross-judge replays the same messages and therefore does not test for language-conditioned leniency. The judge-free length signal is the only condition-blind measurement in the design, and it is coarse.

### P1-7 · §5.5 and Appendix G — state Phase E coverage and blinding honestly
*Evidence:* `PHASE_E_AUDIT.md` E-1, E-5, E-6.

**Line 209**, after "We prepared an outcome-independent sample of 90 pair-model jobs":
> ---5.95\% of the 1{,}512 pair-model grid---

**Append to line 209:**
> At 30 jobs per model the study is powered to validate judge accuracy, chiefly on the \qwen regime; it is not powered to produce a human estimate of the language gap for \gptoss or \nemo.

**Appendix G (line 300), amend** "Model, category, strategy, language label, pair ID, automated scores, and study conclusions are absent." to:
> Model, category, strategy, language label, pair ID, automated scores, and study conclusions are absent from the workbooks. Annotators nonetheless see the response text, so blinding to language is not achievable; they are instructed not to infer conditions or compare rows.

---

## P2 — Recommended. Cheap credibility gains.

### P2-1 · §5.2 or §5.1 — report Bowker
*Evidence:* `STATISTICAL_AUDIT.md` §6. The paper computes these and reports none.

**Append to line 174:**
> Bowker's symmetry test rejects for \qwen ($\chi^2_5=215.2$, $p=1.6\times10^{-44}$) and for \nemo ($\chi^2_5=13.5$, $p=.019$; nominal, not adjusted across models), but not for \gptoss ($p=.068$). \nemo's rejection, its reverse-dominant length signal, and its more reverse-asymmetric GPT-5 Mini gap together indicate a genuine reverse asymmetry that the binary non-assistance contrast does not capture.

### P2-2 · §4.2 and §4.3 — recover space
Lines 112–117 restate the three strategy definitions that Appendix A (line 243) then restates again. Compress the main-text version to one sentence per strategy and cross-reference the appendix. Similarly, lines 122 and 243–251 overlap substantially on the auditor contract. **This recovers roughly 10–12 lines**, enough to absorb P0-5 and P1-5.

### P2-3 · §6 (line 227) — state the reproducibility boundary
**Replace** "Analysis scripts regenerate every reported table and figure from the frozen snapshot." with:

> Analysis scripts regenerate every reported table and figure from the frozen snapshot. Because the snapshot contains harmful prompts and responses, it is not part of the public release; the release carries code, manifests, hashes, seeds, and aggregate outputs, and full regeneration requires gated access to the snapshot.

### P2-4 · §4.3 (line 124) — document the 502→504 top-up
*Evidence:* `METHODOLOGY_AUDIT.md` §6.1.

**Append to line 124:**
> Consolidation of three source banks removed two exact duplicates, leaving 502 unique pairs with two gambling cells at 41; two additional certified pairs were generated to restore exact 42-per-cell balance before the bank was frozen and before any target call.

Verify the timing claim against the generation records before inserting it. **Do not insert it if the timing cannot be established** — an unverifiable ordering claim about target-independence is worse than the current silence.

### P2-5 · Appendix A (line 251) — note the inter-auditor limitation quantitatively
**Append:**
> Because acceptance is a cascade, the secondary auditor never saw primary rejects, and the descriptive equivalence scores of the two auditors are range-restricted on the accepted set (primary: 456 of 504 exactly 1.00). No inter-auditor reliability coefficient is estimable from the frozen bank.

### P2-6 · Repository hygiene, referenced from §6
- Document or remove the `response_garbled` field in `scores.jsonl`. It is the local `looks_garbled()` heuristic, not a judge output; 593 of its 595 triggers come from the `repeat-window-1` rule firing on markdown horizontal rules, and 456 flagged responses were scored $\geq 2$. As shipped it will be misread as evidence that a fifth of responses were incoherent.
- Note that `looks_like_refusal` uses English-only regexes and is not comparable across arms.
- Scrub the OpenRouter workspace key identifier from `errors.jsonl` before any gated release.
- Consider extending `paper/audit_paper_consistency.py` to assert that the committed generator instruction hashes to the bank manifest's `gepa_instruction_sha256`. The current audit passes under every issue in this report because it never inspects `prompts/optimized/`.

---

## P3 — Optional writing and presentation improvements

1. **§3 lacks a worked example.** The handoff's own §11 rewrite plan asks for "an intuitive worked pair before notation," and it was not implemented. Two short redacted prompt fragments (an English/RH pair, harmful specifics elided) would make §3 far more concrete. Cost: 4 lines. High value for a reader meeting the design cold.
2. **The abstract front-loads machinery over finding.** Four sentences on construction precede the result. Consider leading with model-dependence, which `REVIEWER_SIMULATION.md` shows is what reviewers find exciting.
3. **Terminology drift.** "Hinglish/RH", "Romanized Hindi", "RH", and "code-switched Hinglish" all appear. Fix one expansion at first use and use "RH" thereafter.
4. **"Controlled attribution" (line 43) is never defined.** One clause distinguishing it from causal identification would help, since the paper leans on the phrase to justify not claiming causality.
5. **Appendix D and E are two figures with almost no text.** Add one sentence of reading guidance to each.
6. **Table 3's caption footnote about the preserved fallback judgment** is easy to miss and explains the 1,943 vs 1,944 discrepancy. Promote it into the body text at line 205.
7. **The contribution bullets (46–51)** claim "judge-independent length corroboration"; after P0-5 this should read "judge-independent length corroboration of the directional flips."

---

## Space budget

| Patch | Δ lines |
|---|---:|
| P0-1, P0-2 | ~0 |
| P0-4 | +4 main, +1 appendix table |
| P0-5 | +6 |
| P1-1 | +7 |
| P1-2 | appendix only |
| P1-3 | +5 |
| P1-4 | +6 |
| P1-5 | +12, +1 table row |
| P1-6, P1-7 | +6 |
| P2-1 | +4 |
| P2-2 | **−10 to −12** |
| P2-3, P2-4, P2-5 | +6 |
| **Net main text** | **≈ +40 lines** |

Roughly one page of main-text growth against a hard eight-page limit. Recoverable by executing P2-2 in full, moving the cell-level localisation discussion (§5.2, lines 170–176) to the appendix and keeping two sentences in the body, and tightening §4.3, which currently restates the auditor contract that Appendix A gives in full. If space remains tight, P1-3 and P2-1 can move wholly to the appendix with one-clause pointers from the body; P0-1, P0-4, P0-5, P1-1, and P1-5 cannot.

---

## Suggested execution order

1. **P0-3** (commit the correct artifact) — do this first; it is a repository change and unblocks verification of P0-1.
2. **P0-1, P0-2** (GEPA description).
3. **P0-4** (terminology) — a global rename, so do it before other edits touch the same lines.
4. **P0-5, P1-1, P1-2** (the analysis-honesty cluster).
5. **P1-3, P1-4, P2-1** (add the computed-but-unreported results).
6. **P1-5** (related work) — the largest single edit; do it once, with the `.bib` verification.
7. **P1-6, P1-7, P2-3, P2-4, P2-5** (disclosures).
8. **P2-2** (space recovery) — last, once the final length is known.
9. **P2-6** (repository hygiene) — independent of the manuscript; can proceed in parallel.
10. **P3** — only if space and time remain.

Awaiting your approval before any of these is applied. Nothing in this document has been written to `paper/acl_latex.tex`.
