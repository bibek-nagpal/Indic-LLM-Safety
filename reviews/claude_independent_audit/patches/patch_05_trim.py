"""Manuscript patch 5/5: trim main text to restore page-limit slack.

Detail is not deleted; it moves to appendices that already carry it.
"""
from pathlib import Path

P = Path("paper/acl_latex.tex")
t = P.read_text(encoding="utf-8")
n = 0

def sub(old: str, new: str) -> None:
    global t, n
    assert old in t, f"NOT FOUND:\n{old[:200]}"
    assert t.count(old) == 1, f"AMBIGUOUS ({t.count(old)}x):\n{old[:120]}"
    t = t.replace(old, new)
    n += 1

# 1. Section 3 non-assistance note: tighten
sub(
 r"""We write $R$ as non-assistance rather than refusal because score 0 covers any response without domain-specific harmful content, including a verbose non-answer. The distinction is material and asymmetric: 61.1\% of \qwen's English score-0 responses are under 80 characters, whereas none of its 115 RH score-0 responses are and 99.1\% exceed 500 characters (Appendix~\ref{app:nonassistance}). We report the same quantity other work calls a refusal gap, under a name that matches what the rubric measures.""",
 r"""We say non-assistance rather than refusal because score 0 covers any response without domain-specific harmful content, including a verbose non-answer, and the difference is asymmetric: 61.1\% of \qwen's English score-0 responses are under 80 characters, against none of its 115 RH score-0 responses (Appendix~\ref{app:nonassistance}).""",
)

# 2. Section 4.3 dedup paragraph: tighten
sub(
 r"""Two deduplication stages apply. During generation, each candidate is screened against every accepted pair of the same strategy and rejected at a normalized sequence-similarity of 0.85 or above. Consolidation of the three source banks then removed exact duplicates after Unicode normalization, casefolding, and whitespace collapse, but applied no fuzzy matching \emph{across} banks; two gambling cells consequently fell to 41 pairs and were refilled with certified pairs before freezing. Residual similarity is low: across all 42{,}084 within-strategy pairs of the final bank the mean similarity under the generation-gate metric is 0.093 and five pairs remain at or above 0.85 (Appendix~\ref{app:clusters}).""",
 r"""Deduplication has two stages: a 0.85 normalized-similarity gate rejects near-duplicates during each bank build, and consolidation of the three source banks removes exact duplicates after Unicode normalization but applies no fuzzy matching across banks. Two gambling cells consequently fell to 41 pairs and were refilled with certified pairs before freezing. Residual similarity is low---mean 0.093 over all 42{,}084 within-strategy pairs, five at or above the gate (Appendix~\ref{app:clusters}).""",
)

# 3. Section 4.4: move truncation detail to the appendix
sub(
 r"""The judge message contains the prompt and an explicit language tag, so the judge is not blind to the condition it scores; the cross-judge study of Section~\ref{sec:crossjudge} replays the identical messages and preserves that cue. Responses reaching the token cap were scored as issued, and truncation is asymmetric for two targets (\qwen 0 English versus 22 RH, exact $p=4.8\times10^{-7}$; \nemo 77 versus 35, $p=1.7\times10^{-5}$; \gptoss 47 versus 55, n.s.). Dropping every pair-model job with a truncation on either side leaves gaps of 43.36, 4.73, and $-0.50$ pp, so the headline estimates are not driven by truncation (Appendix~\ref{app:clusters}).""",
 r"""The judge message contains the prompt and an explicit language tag, so the judge is not blind to the condition it scores, and the re-judge of Section~\ref{sec:crossjudge} replays identical messages and preserves that cue. Responses reaching the token cap were scored as issued; truncation is asymmetric for \qwen and \nemo, but dropping every truncated pair-model job leaves gaps of 43.36, 4.73, and $-0.50$ pp (Appendix~\ref{app:clusters}).""",
)

# 4. Section 5.1 sensitivity paragraph: tighten
sub(
 r"""We claim only what survives sensitivity analysis. The two \qwen contrasts hold at $p<10^{-4}$ under every resampling unit we tried. The \gptoss{}--\nemo contrast does not: its interval crosses zero once lexically similar prompts are grouped into a single resampling unit (Appendix~\ref{app:clusters}), and it is 4.32 pp (95\% CI $-3.09$--11.42) under the primary judge but 11.73 (3.70--19.14) under GPT-5 Mini on the shared cross-judge subset. The supported statement is that \qwen is robustly distinct from both other targets, while \gptoss and \nemo differ in point estimate and in the sign of the \nemo effect but are not reliably separated by this design.""",
 r"""We claim only what survives sensitivity analysis. Both \qwen contrasts hold at $p<10^{-4}$ under every resampling unit we tried. The \gptoss{}--\nemo contrast does not: its interval crosses zero once lexically similar prompts form one resampling unit (Appendix~\ref{app:clusters}), and on the shared cross-judge subset it is 4.32 pp ($-3.09$--11.42) under the primary judge but 11.73 (3.70--19.14) under GPT-5 Mini. The supported statement is that \qwen is robustly distinct from both other targets, while \gptoss and \nemo are not reliably separated by this design.""",
)

# 5. Section 5.2 cell-level paragraph: compress, detail already in appendix tables
sub(
 r"""Qwen's gap is positive in all 12 category-by-strategy cells, ranging from 7.14 to 76.19 pp. GPT-OSS is positive in 9 of 12 cells, with gaps from $-7.14$ to 11.90 pp. Nemotron is mixed across cells (5 positive), from $-26.19$ to 19.05 pp. Because each cell has 42 pairs, these values localize behavior but do not support independent cell-level claims.""",
 r"""Qwen's gap is positive in all 12 category-by-strategy cells (7.14 to 76.19 pp), GPT-OSS in 9 of 12 ($-7.14$ to 11.90), and Nemotron in 5 ($-26.19$ to 19.05). With 42 pairs per cell these localize behavior but support no independent cell-level claim.""",
)

# 6. Section 5.3 decomposition: tighten
sub(
 r"""This signal is judge-independent but not judge-equivalent, and we decompose it by the judge's own verdict rather than presenting it as a second measure of harm. The shapes concentrate in judge-identified flips---136 of \qwen's 219 forward flips are forward-shaped with none reverse-shaped, and 59 of \nemo's 70 reverse flips are reverse-shaped with none forward-shaped---but a substantial share arises among pairs scored 0 in \emph{both} languages: 65:0 for \qwen, 22:2 for \gptoss, and 12:58 for \nemo. Among those pairs \qwen's median response is 48 characters in English and 4,366 in RH. Response length therefore corroborates a language-conditioned change in response \emph{behavior}, of which the flip component is the safety-relevant part; it is not an independent measure of harmfulness.""",
 r"""This signal is judge-independent but not judge-equivalent, so we decompose it by the judge's own verdict rather than treat it as a second measure of harm. The shapes concentrate in judge-identified flips---136 of \qwen's 219 forward flips are forward-shaped with none reverse-shaped; 59 of \nemo's 70 reverse flips are reverse-shaped---but a substantial share arises among pairs scored 0 in \emph{both} languages: 65:0 for \qwen, 22:2 for \gptoss, 12:58 for \nemo, where \qwen's median response is 48 characters in English and 4,366 in RH. Length therefore corroborates a language-conditioned change in response \emph{behavior}, of which the flip component is the safety-relevant part; it is not an independent measure of harmfulness.""",
)

# 7. Section 5.5 human protocol: compress; Appendix G carries the detail
sub(
 r"""We prepared an outcome-independent sample of 180 pair-model jobs---11.9\% of the 1,512-job grid---drawn from the completed cross-judge scope, retaining both languages for 360 response items per annotator. Every one of the 36 model-by-category-by-strategy cells contributes exactly five jobs. The same items are independently randomized for two annotators, with the two languages of a job at least ten positions apart in both orders, and are blinded to model, pair ID, language tag, automated scores, flips, and conclusions; annotators nevertheless see the response text, so blinding to language itself is not achievable. Annotators must read English and conversational Romanized Hindi, record their proficiency, and flag borderline or unreadable items; they choose the best-fitting score rather than the lowest defensible one. Adjudication rules are fixed in advance and pre-adjudication labels are primary. The prespecified analysis treats the pair-model job as the cluster unit and reports agreement, both $\kappa$ variants, cluster-bootstrap intervals, confusion matrices, per-model and per-language breakdowns, human-derived non-assistance gaps, and critical-severity agreement. At 30 jobs per model the study is powered to validate judge accuracy, chiefly on the \qwen regime, rather than to re-estimate the language gap. No human labels were available at submission-draft time, so we report no human result.""",
 r"""We prepared an outcome-independent sample of 180 pair-model jobs---11.9\% of the 1,512-job grid, five from each of the 36 model-by-category-by-strategy cells---retaining both languages for 360 response items per annotator. The same items are independently randomized for two annotators and blinded to model, pair ID, language tag, automated scores, flips, and conclusions; annotators see the response text, so blinding to language itself is not achievable. They must read English and conversational Romanized Hindi, flag borderline and unreadable items, and choose the best-fitting rather than the lowest defensible score. Adjudication is prespecified and pre-adjudication labels are primary. The frozen analysis clusters on the pair-model job and reports agreement, both $\kappa$ variants, cluster-bootstrap intervals, confusion matrices, per-model and per-language breakdowns, human-derived non-assistance gaps, and critical-severity agreement (Appendix~\ref{app:human}). At 60 jobs per model it is powered to validate judge accuracy, chiefly on the \qwen regime, rather than to re-estimate the language gap. No human labels were available at submission-draft time, so we report no human result.""",
)

# 8. Limitations: tighten the model-based-measurement paragraph
sub(
 r"""Prompt equivalence and response severity are LLM-assessed. Two auditor families, hard logical checks, a second response judge, and a judge-free length signal reduce correlated-error concerns but do not eliminate them, and two overlaps remain. GPT-5 Mini is both the secondary certification auditor and the re-judge, so no fully uninvolved family scores the responses. The judge also sees the prompt and an explicit language tag, so it is not blind to the condition; because the re-judge replays those messages, judge replacement cannot detect language-conditioned leniency, and the coarse length signal is the only condition-blind measurement. The auditor cascade further means the secondary auditor did not see primary rejects, and on the accepted set the two auditors' descriptive equivalence scores are range-restricted, so no inter-auditor reliability coefficient is estimable. The pending two-human study is therefore important.""",
 r"""Prompt equivalence and response severity are LLM-assessed, and two overlaps remain. GPT-5 Mini is both the secondary certification auditor and the re-judge, so no fully uninvolved family scores the responses. The judge sees the prompt and an explicit language tag, and the re-judge replays those messages, so judge replacement cannot detect language-conditioned leniency; the coarse length signal is the only condition-blind measurement. The cascade also means the secondary auditor never saw primary rejects, and the auditors' descriptive scores are range-restricted on the accepted set, so no inter-auditor reliability coefficient is estimable. The pending two-human study is therefore important.""",
)

# label the human-annotation appendix
sub(
 r"\section{Human-Annotation Protocol}",
 r"\section{Human-Annotation Protocol}\label{app:human}",
)

P.write_text(t, encoding="utf-8")
print(f"patch 5: applied {n} substitutions")
