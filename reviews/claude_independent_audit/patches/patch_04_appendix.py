"""Manuscript patch 4/4: appendices and reproducibility manifest."""
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

# ---- Appendix A closing line: released instruction ------------------------
sub(
 r"The verbatim prompt and parser are archived with the submission source in \path{src/jailbreak_hermes/equivalence.py}; the final bank manifest hashes the generator guidance and records both auditor model slugs.",
 r"The verbatim prompt and parser are archived with the submission source in \path{src/jailbreak_hermes/equivalence.py}. The verbatim generator guidance is archived alongside them, and its SHA-256 equals the \texttt{gepa\_instruction\_sha256} recorded in the frozen bank manifest, which also records both auditor model slugs; a released script re-checks this correspondence.",
)

# ---- Appendix B: retitle and recast --------------------------------------
sub(
 r"""\section{GEPA Objective}

For a generated candidate $c$, let $h_k(c)\in\{0,1\}$ denote the 13 target-independent hard constraints described in Section~4.1. The development score is
\begin{equation}
Q(c)=\frac{1}{13}\sum_{k=1}^{13}h_k(c).
\end{equation}
Natural-language feedback lists failed constraints. No target-model response, refusal, judge score, or forward/critical flip enters $Q$. The manifest records \texttt{gepa\_target\_signal\_used=false} and an empty target-model list during generation.""",
 r"""\section{Target-Independent Probe-Validity Metric}
\label{app:metric}

For a generated candidate $c$, let $h_k(c)\in\{0,1\}$ denote the 13 target-independent hard constraints described in Section~4.1. The validation score is
\begin{equation}
Q(c)=\frac{1}{13}\sum_{k=1}^{13}h_k(c).
\end{equation}
No target-model response, refusal, judge score, or forward/critical flip enters $Q$. It is a validation diagnostic, not an optimization objective: the persisted harness state holds a single program candidate with no parent program, and the run recorded no accepted revision to the generator guidance, so the instruction that was frozen is the hand-written one. Over the 30 development-set evaluations, 24 candidates satisfied all 13 constraints; failures were dominated by category membership and direct harmful facilitation rather than by the equivalence axes. The bank manifest records \texttt{gepa\_target\_signal\_used=false} and an empty target-model list during generation, and every evaluation record carries \texttt{target\_model\_called=false}.""",
)

# ---- New appendices, inserted before Score Transitions ---------------------
sub(
 r"""\section{Score Transitions}
\label{app:transitions}""",
 r"""\section{The Non-Assistance Construct}
\label{app:nonassistance}

Score 0 denotes any response with no domain-specific harmful content, which includes verbose non-answers as well as explicit refusals. Table~\ref{tab:nonassist} profiles the score-0 responses. The English-pattern refusal regex cannot detect Hindi or Hinglish refusals and is shown only as a lower bound; the length columns carry the argument.

\begin{table}[h]
\centering
\small
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{llrrr}
\toprule
Model & Lang. & $n(\score{=}0)$ & $<$80 ch. & $>$500 ch. \\
\midrule
\qwen & EN & 332 & 203 (61.1\%) & 129 (38.9\%) \\
\qwen & RH & 115 & 0 (0.0\%) & 114 (99.1\%) \\
\gptoss & EN & 437 & 412 (94.3\%) & 25 (5.7\%) \\
\gptoss & RH & 414 & 367 (88.6\%) & 45 (10.9\%) \\
\nemo & EN & 313 & 208 (66.5\%) & 103 (32.9\%) \\
\nemo & RH & 322 & 272 (84.5\%) & 49 (15.2\%) \\
\bottomrule
\end{tabular}
\caption{Length profile of score-0 responses. \qwen's English non-assistance is mostly terse refusal; its RH non-assistance is not terse at all.}
\label{tab:nonassist}
\end{table}

\section{Similarity, Clustering, Truncation, and Prompt Length}
\label{app:clusters}

\paragraph{Prompt similarity.} Under the generation-gate metric (normalized \texttt{SequenceMatcher} ratio, maximum over the two languages) the mean similarity across all 42{,}084 within-strategy pairs of the final bank is 0.093, the 99th percentile is 0.480, and 5 pairs sit at or above the 0.85 gate. Those five are cross-source-bank residuals: the gate operates within a bank build, and consolidation across the three source banks matched exact strings only. Under a more permissive bag-of-words measure, mean within-cell Jaccard similarity is 0.254 against a 0.138 cross-bank baseline, reflecting shared scenario scaffolding rather than near-verbatim reuse.

\paragraph{Cluster-robust resampling.} Because shared scaffolding makes pair IDs less than fully independent, we repeat the analysis with connected components of prompts joined at a lexical-overlap threshold as the resampling unit (Table~\ref{tab:clusters}). The \qwen results are unchanged at every threshold. The \gptoss{}--\nemo contrast is not: its interval crosses zero from a threshold of 0.60 downward, before any Holm adjustment.

\begin{table}[h]
\centering
\small
\setlength{\tabcolsep}{3pt}
\begin{tabular}{lrrrr}
\toprule
Unit & $K$ & \qwen & \gptoss & G$-$N contrast \\
\midrule
pair ID & 504 & $<10^{-4}$ & .0070 & [0.79, 12.10] \\
0.70 & 459 & $<10^{-4}$ & .0078 & [0.60, 12.16] \\
0.65 & 420 & $<10^{-4}$ & .0107 & [0.20, 12.45] \\
0.60 & 380 & $<10^{-4}$ & .0094 & [$-0.78$, 13.32] \\
0.55 & 341 & $<10^{-4}$ & .0102 & [$-0.60$, 13.36] \\
\bottomrule
\end{tabular}
\caption{Cluster-robust sensitivity. $K$ is the number of resampling units; \qwen and \gptoss columns give sign-randomization $p$-values for each model's own gap; the final column is the 95\% interval for the \gptoss minus \nemo gap contrast.}
\label{tab:clusters}
\end{table}

\paragraph{Truncation.} Responses reaching the 4,096-token cap were scored as issued. Truncation counts are 0/22 (EN/RH) for \qwen, 47/55 for \gptoss, and 77/35 for \nemo; discordance is significant for \qwen ($p=4.8\times10^{-7}$) and \nemo ($p=1.7\times10^{-5}$). Dropping every pair-model job with a truncation on either side gives gaps of 43.36 pp ($n=482$), 4.73 ($n=423$), and $-0.50$ ($n=401$); critical forward/reverse counts move from 85/2, 15/6, and 22/10 to 82/2, 11/3, and 16/8.

\paragraph{Prompt length.} RH prompts are systematically longer than their English counterparts (mean 396.5 versus 356.6 characters; median ratio 1.114; paired Wilcoxon $p=7.7\times10^{-80}$), and length is not among the nine audited axes. It does not predict the outcome: Spearman correlations between the per-pair RH/EN length ratio and the pair-level gap are $-0.005$, $0.051$, and $-0.048$, and with forward flips $-0.035$, $0.062$, and $0.017$ (all $p>.10$). Forward-flip rates across ratio terciles are flat (\qwen 44.1/44.6/41.7\%).

\section{Cross-Judge Agreement Structure}
\label{app:crossjudge}

\begin{table}[h]
\centering
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{llrrr}
\toprule
Model & Lang. & Exact & Adj. & $\Delta$ mean \\
\midrule
\qwen & EN & 71.6\% & 88.0\% & $+0.42$ \\
\qwen & RH & 53.1\% & 87.7\% & $+0.60$ \\
\gptoss & EN & 89.8\% & 98.1\% & $+0.13$ \\
\gptoss & RH & 88.9\% & 96.0\% & $+0.14$ \\
\nemo & EN & 66.3\% & 87.6\% & $+0.46$ \\
\nemo & RH & 72.2\% & 90.7\% & $+0.29$ \\
\bottomrule
\end{tabular}
\caption{Primary-pipeline versus GPT-5 Mini agreement by condition on the shared 324-pair subset. $\Delta$ mean is the mean GPT-5 Mini minus primary score. Agreement is lowest, and the calibration shift largest, on the \qwen RH responses that drive the headline effect.}
\label{tab:crossjudgecells}
\end{table}

\section{Score Transitions}
\label{app:transitions}""",
)

# ---- Human-annotation protocol appendix ----------------------------------
sub(
 r"""Each annotator receives only a neutral item number, harmful prompt, target response, concise rubric, and 0--3 entry field. Model, category, strategy, language label, pair ID, automated scores, and study conclusions are absent. The two workbooks contain identical items in independent order, with reconciliation retained separately. Annotators are instructed not to use outside sources or discuss labels before both workbooks are returned. Pre-adjudication labels will remain immutable; any later consensus/adjudication will be stored separately.

The fixed sample has 180 response items per annotator: 90 unique pair-model jobs and both languages. Selection is outcome-independent within the cross-judge scope. Every one of the 36 model-by-category-by-strategy cells contributes two or three jobs, and pair IDs are disjoint across models within a category-by-strategy cell to broaden prompt coverage.""",
 r"""Each annotator receives a neutral item number, the harmful prompt, the target response, a concise rubric, a 0--3 entry field, and borderline and unreadable flags. Model, category, strategy, language tag, pair ID, automated scores, and study conclusions are absent from the workbooks; annotators see the response text, so blinding to language itself is not achievable, and they are instructed not to infer conditions, compare rows, use outside sources, or discuss labels before both workbooks are returned. Annotators must read English and conversational Romanized Hindi, complete a calibration set drawn from outside the sample, and record self-assessed proficiency. Ties are resolved by best fit rather than by a downward rule, so the instrument does not build in a direction relative to the automated judges. Pre-adjudication labels are immutable and primary; a prespecified rule sends only items where the two annotators differ by two or more levels to a third adjudicator who is blind to both original labels and to all automated scores, and adjudicated results are reported separately as secondary.

The fixed sample has 360 response items per annotator: 180 unique pair-model jobs and both languages, or 11.9\% of the 1,512-job grid. Selection is outcome-independent within the cross-judge scope and uses no automated score, flip status, or downstream result. Every one of the 36 model-by-category-by-strategy cells contributes exactly five jobs; pair IDs are disjoint across models within a category-by-strategy cell to broaden prompt coverage; and the two language items of a job are separated by at least ten positions in both independently randomized orders. The prespecified analysis clusters on the pair-model job.""",
)

# ---- Reproducibility manifest --------------------------------------------
sub(
 r"""Cross-judge committed cost & USD 3.67896645 under a USD 4.50 ceiling \\
Human sample seed & 20260830 \\""",
 r"""Cross-judge committed cost & USD 3.67896645 under a USD 4.50 ceiling \\
Generator guidance SHA-256 & \scriptsize\texttt{\seqsplit{025fbd3573fc018b3291a51a19acb456df3fd79a3725a1b29610dd89bcd5ce3b}} \\
Human sample & 180 jobs / 360 items, seed 20260831 \\""",
)

P.write_text(t, encoding="utf-8")
print(f"patch 4: applied {n} substitutions")
