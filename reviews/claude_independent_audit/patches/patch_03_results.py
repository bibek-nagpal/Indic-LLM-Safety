"""Manuscript patch 3/4: results, cross-judge, human protocol, limitations, ethics."""
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

# ---- Table 2 headers / caption -------------------------------------------
sub(
 r"Model & EN refusal & RH refusal & Gap pp [95\% CI] & Forward & Reverse & Critical F & Critical R \\",
 r"Model & EN non-asst. & RH non-asst. & Gap pp [95\% CI] & Forward & Reverse & Critical F & Critical R \\",
)
sub(
 r"\caption{Primary results over 504 paired probes per model. Gap is English refusal minus RH refusal. Critical F/R denote critical forward/reverse flips.}",
 r"\caption{Primary results over 504 paired probes per model. Non-assistance is the rate of score-0 responses; the gap is English minus RH. Critical F/R denote critical forward/reverse flips.}",
)

# ---- 5.1 section heading + regime claim ----------------------------------
sub(
 r"\subsection{Model-dependent language asymmetry}",
 r"\subsection{Model-dependent language asymmetry}\label{sec:main}",
)
sub(
 r"Table~\ref{tab:main} shows three distinct regimes. \qwen has a large directional asymmetry:",
 r"Table~\ref{tab:main} shows a strongly graded pattern. \qwen has a large directional asymmetry:",
)
sub(
 r"""The language effect differs by model. Gap contrasts are 38.49 pp for Qwen minus GPT-OSS (95\% CI 32.94--44.05), 44.84 pp for Qwen minus Nemotron (38.29--51.39), and 6.35 pp for GPT-OSS minus Nemotron (0.79--12.10); Holm-adjusted randomization $p$-values are below $3.1\times10^{-5}$, below $3.1\times10^{-5}$, and $.032$. The clustered language-by-model interaction is also strong ($\chi^2_2=165.83$, $p=9.79\times10^{-37}$).""",
 r"""The language effect differs by model. Gap contrasts are 38.49 pp for Qwen minus GPT-OSS (95\% CI 32.94--44.05), 44.84 pp for Qwen minus Nemotron (38.29--51.39), and 6.35 pp for GPT-OSS minus Nemotron (0.79--12.10); Holm-adjusted randomization $p$-values are below $3.1\times10^{-5}$, below $3.1\times10^{-5}$, and $.032$. The clustered language-by-model interaction is also strong ($\chi^2_2=165.83$, $p=9.79\times10^{-37}$), but it is dominated by \qwen and does not by itself license a pairwise separation of the other two targets.

We claim only what survives sensitivity analysis. The two \qwen contrasts hold at $p<10^{-4}$ under every resampling unit we tried. The \gptoss{}--\nemo contrast does not: its interval crosses zero once lexically similar prompts are grouped into a single resampling unit (Appendix~\ref{app:clusters}), and it is 4.32 pp (95\% CI $-3.09$--11.42) under the primary judge but 11.73 (3.70--19.14) under GPT-5 Mini on the shared cross-judge subset. The supported statement is that \qwen is robustly distinct from both other targets, while \gptoss and \nemo differ in point estimate and in the sign of the \nemo effect but are not reliably separated by this design.""",
)

# ---- 5.2 Bowker -----------------------------------------------------------
sub(
 r"""The complete score-transition matrices (Appendix~\ref{app:transitions}) show why binary refusal alone is insufficient. Qwen has 85 transitions from English score 0 to RH score 3, versus two in the opposite direction. GPT-OSS and Nemotron have fewer critical transitions and substantially more bidirectional movement.""",
 r"""The complete score-transition matrices (Appendix~\ref{app:transitions}) show why the binary contrast alone is insufficient. Qwen has 85 transitions from English score 0 to RH score 3, versus two in the opposite direction. GPT-OSS and Nemotron have fewer critical transitions and substantially more bidirectional movement. Bowker's symmetry test rejects for \qwen ($\chi^2_5=215.21$, $p=1.6\times10^{-44}$) and for \nemo ($\chi^2_5=13.54$, $p=.019$, nominal) but not for \gptoss ($p=.068$). \nemo's rejection, its reverse-dominant length signal, and its more reverse-asymmetric GPT-5 Mini gap together indicate a genuine reverse asymmetry that the binary non-assistance contrast does not capture.""",
)

# ---- 5.3 Phase C decomposition -------------------------------------------
sub(
 r"""We prespecify a coarse directional check from stored response text only: ``forward-shaped'' means English response length below 80 Unicode characters and RH length above 500; reverse-shaped mirrors the rule. Qwen has 203 forward-shaped and 0 reverse-shaped pairs, GPT-OSS 59 and 16, and Nemotron 56 and 120. Exact directional $p$-values are $1.56\times10^{-61}$, $6.11\times10^{-7}$, and $1.59\times10^{-6}$. A fixed $3\times3$ threshold grid (short 60/80/100; long 400/500/600) leaves Qwen at 203:0 and GPT-OSS at 59:16; Nemotron varies only from 120 to 121 reverse-shaped cases. Length is not a semantic safety score, but it is independent of both LLM judges.""",
 r"""We prespecify a coarse directional check from stored response text only: ``forward-shaped'' means English response length below 80 Unicode characters and RH length above 500; reverse-shaped mirrors the rule. Qwen has 203 forward-shaped and 0 reverse-shaped pairs, GPT-OSS 59 and 16, and Nemotron 56 and 120. Exact directional $p$-values are $1.56\times10^{-61}$, $6.11\times10^{-7}$, and $1.59\times10^{-6}$. A fixed $3\times3$ threshold grid (short 60/80/100; long 400/500/600) leaves Qwen at 203:0 and GPT-OSS at 59:16; Nemotron varies only from 120 to 121 reverse-shaped cases.

This signal is judge-independent but not judge-equivalent, and we decompose it by the judge's own verdict rather than presenting it as a second measure of harm. The shapes concentrate in judge-identified flips---136 of \qwen's 219 forward flips are forward-shaped with none reverse-shaped, and 59 of \nemo's 70 reverse flips are reverse-shaped with none forward-shaped---but a substantial share arises among pairs scored 0 in \emph{both} languages: 65:0 for \qwen, 22:2 for \gptoss, and 12:58 for \nemo. Among those pairs \qwen's median response is 48 characters in English and 4,366 in RH. Response length therefore corroborates a language-conditioned change in response \emph{behavior}, of which the flip component is the safety-relevant part; it is not an independent measure of harmfulness.""",
)

# ---- 5.4 cross-judge ------------------------------------------------------
sub(
 r"\subsection{Independent GPT-5 Mini re-judge}",
 r"\subsection{GPT-5 Mini re-judge}\label{sec:crossjudge}",
)
sub(
 r"""Budget constraints permitted a complete re-judge of an outcome-independent shared subset rather than all 3,024 responses.""",
 r"""GPT-5 Mini is a second response judge, not an uninvolved pipeline family: it also served as the secondary certification auditor for every accepted pair and as the fallback primary judge for the two blocked items. It therefore tests judge-scoring robustness, and does not retire the concern that generation, certification, and judging share model families. Budget constraints permitted a complete re-judge of an outcome-independent shared subset rather than all 3,024 responses.""",
)
sub(
 r"""Pure Gemini versus GPT-5 Mini exact agreement is 73.65\% over 1,943 responses; adjacent agreement is 91.35\%, unweighted Cohen's $\kappa=.541$, and quadratic-weighted $\kappa=.813$. The Qwen and GPT-OSS gaps change by only 0.93 and 0.62 pp. Nemotron becomes more reverse-asymmetric under GPT-5 Mini. GPT-5 Mini also assigns score 3 more often (30.97\% versus 12.91\% in the primary pipeline), so exact critical-severity rates are judge-sensitive. The robust conclusion is the ordering---Qwen strongly asymmetric, GPT-OSS mildly asymmetric, Nemotron near-symmetric or reverse-asymmetric---not an invariant absolute severity rate.""",
 r"""Pure Gemini versus GPT-5 Mini exact agreement is 73.65\% over 1,943 responses; adjacent agreement is 91.35\%, unweighted Cohen's $\kappa=.541$, and quadratic-weighted $\kappa=.813$. The Qwen and GPT-OSS gaps change by only 0.93 and 0.62 pp. Nemotron becomes more reverse-asymmetric under GPT-5 Mini. GPT-5 Mini also assigns score 3 more often (30.97\% versus 12.91\% in the primary pipeline), so exact critical-severity rates are judge-sensitive.

That pooled agreement figure conceals where the judges disagree. Exact agreement is 89.8\% and 88.9\% for \gptoss English and RH but 71.6\% and 53.1\% for \qwen English and RH, and 66.3\% and 72.2\% for \nemo (Appendix~\ref{app:crossjudge}). The judges therefore agree least on the \qwen RH responses that produce the largest effect, and GPT-5 Mini scores higher in every condition (mean difference $+0.13$ to $+0.60$), which is a calibration shift rather than symmetric noise. On this subset the \gptoss gap interval includes zero under both judges, so the subset reproduces that point estimate without confirming the effect. The robust conclusion is the ordering---Qwen strongly asymmetric, GPT-OSS mildly asymmetric, Nemotron near-symmetric or reverse-asymmetric---not an invariant absolute severity rate.""",
)
sub(
 r"\caption{Judge replacement on the same 324 pairs per model. ``Gemini pipeline'' includes one preserved GPT-5 Mini fallback judgment; pure Gemini agreement calculations exclude it.}",
 r"\caption{Judge replacement on the same 324 pairs per model. Gap is the English-minus-RH non-assistance difference. ``Gemini pipeline'' includes one preserved GPT-5 Mini fallback judgment; pure Gemini agreement calculations exclude it.}",
)
sub(
 r"Judge & Model & EN refusal & RH refusal & Gap pp [95\% CI] & Forward / reverse \\",
 r"Judge & Model & EN non-asst. & RH non-asst. & Gap pp [95\% CI] & Forward / reverse \\",
)

# ---- 5.5 human protocol ---------------------------------------------------
sub(
 r"""We prepared an outcome-independent sample of 90 pair-model jobs from the completed cross-judge scope, retaining both languages for 180 response items per annotator. Every model-by-category-by-strategy cell contributes two or three jobs; each model has six cells of each size. The same items are independently randomized for two annotators and are blinded to model, pair ID, language label, automated scores, flips, and conclusions. Annotators use the unchanged 0--3 rubric. The analysis script will report exact and adjacent agreement, unweighted and quadratic-weighted $\kappa$, $4\times4$ confusion matrices, and agreement of each human with both automated judges. No human labels were available at submission-draft time, so we report no human result.""",
 r"""We prepared an outcome-independent sample of 180 pair-model jobs---11.9\% of the 1,512-job grid---drawn from the completed cross-judge scope, retaining both languages for 360 response items per annotator. Every one of the 36 model-by-category-by-strategy cells contributes exactly five jobs. The same items are independently randomized for two annotators, with the two languages of a job at least ten positions apart in both orders, and are blinded to model, pair ID, language tag, automated scores, flips, and conclusions; annotators nevertheless see the response text, so blinding to language itself is not achievable. Annotators must read English and conversational Romanized Hindi, record their proficiency, and flag borderline or unreadable items; they choose the best-fitting score rather than the lowest defensible one. Adjudication rules are fixed in advance and pre-adjudication labels are primary. The prespecified analysis treats the pair-model job as the cluster unit and reports agreement, both $\kappa$ variants, cluster-bootstrap intervals, confusion matrices, per-model and per-language breakdowns, human-derived non-assistance gaps, and critical-severity agreement. At 30 jobs per model the study is powered to validate judge accuracy, chiefly on the \qwen regime, rather than to re-estimate the language gap. No human labels were available at submission-draft time, so we report no human result.""",
)

# ---- Limitations ----------------------------------------------------------
sub(
 r"""Prompt equivalence and response severity are LLM-assessed. Two independent auditor families, hard logical checks, one independent judge family, and a judge-free length signal reduce correlated-error concerns but do not eliminate them. The pending two-human study is therefore important. The auditor cascade also means the secondary auditor did not see primary rejects, so the final bank cannot support a full inter-auditor agreement estimate.""",
 r"""Prompt equivalence and response severity are LLM-assessed. Two auditor families, hard logical checks, a second response judge, and a judge-free length signal reduce correlated-error concerns but do not eliminate them, and two overlaps remain. GPT-5 Mini is both the secondary certification auditor and the re-judge, so no fully uninvolved family scores the responses. The judge also sees the prompt and an explicit language tag, so it is not blind to the condition; because the re-judge replays those messages, judge replacement cannot detect language-conditioned leniency, and the coarse length signal is the only condition-blind measurement. The auditor cascade further means the secondary auditor did not see primary rejects, and on the accepted set the two auditors' descriptive equivalence scores are range-restricted, so no inter-auditor reliability coefficient is estimable. The pending two-human study is therefore important.""",
)
sub(
 r"""We have not run an unusual-English out-of-distribution control or a certification ablation on rejected candidates. Such experiments would require new target inference and are not represented as completed evidence. The frozen snapshot also does not preserve enough complete generation-attempt logs to reconstruct the full candidate funnel or certification selectivity rates.""",
 r"""We have not run an unusual-English out-of-distribution control or a certification ablation on rejected candidates. Such experiments would require new target inference and are not represented as completed evidence. Without the former we cannot separate a register-specific effect from generic sensitivity to off-distribution input; certification controls the nine audited axes, not distance from a target's training distribution. The frozen snapshot also does not preserve enough complete generation-attempt logs to reconstruct the full candidate funnel or certification selectivity rates.""",
)

# ---- Ethics / reproducibility --------------------------------------------
sub(
 r"""The probe bank and target responses contain harmful requests and model outputs. Public release should therefore separate code, manifests, hashes, and aggregate results from gated research access to raw content. The frozen snapshot records the bank/run IDs, model slugs, request settings, score provenance, two fallback cases, and SHA-256 hashes. Analysis scripts regenerate every reported table and figure from the frozen snapshot. No target response was regenerated for the cross-judge study.""",
 r"""The probe bank and target responses contain harmful requests and model outputs. Public release therefore separates code, manifests, hashes, seeds, and aggregate results from gated research access to raw content. The frozen snapshot records the bank/run IDs, model slugs, request settings, score provenance, two fallback cases, and SHA-256 hashes, and the released generator instruction hashes to the value the bank manifest records. Analysis scripts regenerate every reported table and figure from the frozen snapshot; because the snapshot holds harmful prompts and responses it is not itself public, so full regeneration requires gated access. No target response was regenerated for the cross-judge study.""",
)

# ---- Conclusion -----------------------------------------------------------
sub(
 r"""On the final frozen bank, the answer depends strongly on the target: Qwen shows a large English/RH asymmetry, GPT-OSS a small one, and Nemotron none or a reverse effect. Judge replacement preserves that ordering while changing absolute severity calibration.""",
 r"""On the final frozen bank, the answer depends strongly on the target: Qwen shows a large English/RH asymmetry and is robustly distinct from both other targets, while GPT-OSS and Nemotron show a small effect and a null-or-reverse effect that this design does not reliably separate. Judge replacement preserves that ordering while changing absolute severity calibration.""",
)

P.write_text(t, encoding="utf-8")
print(f"patch 3: applied {n} substitutions")
