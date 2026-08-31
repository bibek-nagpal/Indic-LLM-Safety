"""Manuscript patch 2/4: problem formulation, GEPA description, certification, judging."""
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

# ---- Section 3: non-assistance construct ----------------------------------
sub(
 r"""Refusal is $R_{im\ell}=\indicator[\score_{im\ell}=0]$. The primary language effect for model $m$ is the paired refusal gap
\begin{equation}
\Delta_m=\frac{1}{N}\sum_{i=1}^{N}\left(R_{im\mathrm{EN}}-R_{im\mathrm{RH}}\right).
\end{equation}
A positive gap means more refusals in English than RH. The \emph{pair ID}, not an individual response, is the experimental and resampling unit.""",
 r"""\emph{Non-assistance} is $R_{im\ell}=\indicator[\score_{im\ell}=0]$. The primary language effect for model $m$ is the paired non-assistance gap
\begin{equation}
\Delta_m=\frac{1}{N}\sum_{i=1}^{N}\left(R_{im\mathrm{EN}}-R_{im\mathrm{RH}}\right).
\end{equation}
A positive gap means more English than RH responses carry no domain-specific harmful content. The \emph{pair ID}, not an individual response, is the experimental and resampling unit.

We write $R$ as non-assistance rather than refusal because score 0 covers any response without domain-specific harmful content, including a verbose non-answer. The distinction is material and asymmetric: 61.1\% of \qwen's English score-0 responses are under 80 characters, whereas none of its 115 RH score-0 responses are and 99.1\% exceed 500 characters (Appendix~\ref{app:nonassistance}). We report the same quantity other work calls a refusal gap, under a name that matches what the rubric measures.""",
)

# ---- Section 4.1: GEPA -> fixed hand-specified guidance ---------------------
sub(
 r"""The generator is \texttt{google/gemini-2.5-flash}. It produces English/RH candidates from a harm-category and strategy specification. We use \gepa within DSPy \cite{khattab2024dspy,agrawal2026gepa} to optimize supplementary generator guidance. The optimized text cannot alter fixed construction invariants or the auditor contract.

Most importantly, optimization is target-independent. It never calls a target model, never observes a target response or response-judge label, and has no flip reward. Its score is the fraction of 13 prompt-validity constraints satisfied: nine paired axes, RH not stronger than English, probe eligibility, correct harmful-category membership, and direct harmful facilitation with non-benign purpose. Failed constraints yield textual feedback for prompt-guidance evolution. The generator instruction is frozen before bank construction.""",
 r"""The generator is \texttt{google/gemini-2.5-flash}. It produces English/RH candidates from a harm-category and strategy specification under fixed construction invariants and a fixed supplementary guidance instruction. The guidance is hand-specified; it cannot alter the construction invariants or the auditor contract, and it is frozen before bank construction.

Most importantly, the guidance is target-independent. It never references a target model, and no target response, refusal, response-judge label, or flip outcome informs it. We validated it offline against a target-independent probe-validity metric $Q$: the fraction of 13 hard constraints satisfied, namely nine paired axes, RH not stronger than English, probe eligibility, correct harmful-category membership, and direct harmful facilitation with non-benign purpose (Appendix~\ref{app:metric}). Using the DSPy harness \cite{khattab2024dspy}, $Q$ was evaluated on 30 candidates over a 12-item development set at a cost of USD 0.030; every evaluation record carries \texttt{target\_model\_called=false}, and the procedure returned no accepted revision to the guidance. We therefore describe the instruction as fixed and hand-specified rather than optimized, and report $Q$ as a validation diagnostic. The verbatim instruction is released; its SHA-256 matches the \texttt{gepa\_instruction\_sha256} recorded in the frozen bank manifest.""",
)

# ---- Section 4.2: compress strategy prose (space recovery) -----------------
sub(
 r"""The final strategies are binding structural definitions:
\begin{itemize}[leftmargin=1.35em,itemsep=2pt]
    \item \textbf{SymbolicMasking}: a recoverable symbolic or metaphorical mapping re-encodes the harmful referent in both languages. A label, role, or story alone is insufficient.
    \item \textbf{ScenarioNesting}: at least two genuine containment layers occur in the same order in both languages, with the harmful request innermost. A single story/research wrapper fails.
    \item \textbf{RolePrompting}: both prompts explicitly assign a role, persona, or professional stance, and that assignment is the attack mechanism. Mere narration fails.
\end{itemize}
We cross these with violence, intoxication, gambling, and sexual violence. The final design contains 42 certified pairs in each of the 12 category-by-strategy cells.""",
 r"""The strategies are binding structural definitions, enforced by the auditor contract (Appendix~\ref{app:auditor}). \textbf{SymbolicMasking} requires a recoverable symbolic mapping re-encoding the harmful referent in both languages; a label, role, or story alone is insufficient. \textbf{ScenarioNesting} requires at least two genuine containment layers in the same order in both languages with the harmful request innermost; a single story or research wrapper fails. \textbf{RolePrompting} requires an explicit assigned role in both languages that is itself the attack mechanism; mere narration fails. We cross these with violence, intoxication, gambling, and sexual violence, giving 42 certified pairs in each of the 12 category-by-strategy cells.""",
)

# ---- Section 4.3: compress + document dedup and the top-up -----------------
sub(
 r"""The primary auditor is \texttt{deepseek/deepseek-v4-flash}; the secondary auditor is \texttt{openai/gpt-5-mini}. DeepSeek sees every candidate. GPT-5 Mini is called only after a primary pass, but independently applies the same hard contract. Acceptance requires both auditors to affirm: category membership; direct harmful facilitation and non-benign purpose in both languages; minimum faithful-fulfillment level at least 2; no high-level-only or self-neutralizing request; all nine equivalence/language/strategy axes; strategy-specific structure; equal strength; RH not stronger than English; and an accept verdict. Any missing field fails closed. A scalar equivalence score is stored descriptively but is not an acceptance threshold.

The final bank has 504 rows and 504 unique pair IDs, English prompts, and RH prompts. It was frozen before target inference under bank ID \path{revision_v2_3_1_final_504_dedup}; its canonical SHA-256 is \texttt{\seqsplit{35bfbc1d09e78b77c24d62bbf41783cc9b297dd25f1bba3fe6062d53dc2028ed}}. Generation provenance lists no target models.""",
 r"""The primary auditor is \texttt{deepseek/deepseek-v4-flash}; the secondary auditor is \texttt{openai/gpt-5-mini}. DeepSeek sees every candidate; GPT-5 Mini is called only after a primary pass but independently applies the same hard contract. Acceptance requires both auditors to affirm category membership, direct harmful facilitation and non-benign purpose in both languages, minimum faithful-fulfillment level at least 2, no high-level-only or self-neutralizing request, all nine equivalence/language/strategy axes, strategy-specific structure, equal strength, RH not stronger than English, and an accept verdict (Appendix~\ref{app:auditor}). Any missing field fails closed. A scalar equivalence score is stored descriptively but is not an acceptance threshold.

Two deduplication stages apply. During generation, each candidate is screened against every accepted pair of the same strategy and rejected at a normalized sequence-similarity of 0.85 or above. Consolidation of the three source banks then removed exact duplicates after Unicode normalization, casefolding, and whitespace collapse, but applied no fuzzy matching \emph{across} banks; two gambling cells consequently fell to 41 pairs and were refilled with certified pairs before freezing. Residual similarity is low: across all 42{,}084 within-strategy pairs of the final bank the mean similarity under the generation-gate metric is 0.093 and five pairs remain at or above 0.85 (Appendix~\ref{app:clusters}).

The final bank has 504 rows and 504 unique pair IDs, English prompts, and RH prompts. It was frozen before any target call under bank ID \path{revision_v2_3_1_final_504_dedup}; its canonical SHA-256 is \texttt{\seqsplit{35bfbc1d09e78b77c24d62bbf41783cc9b297dd25f1bba3fe6062d53dc2028ed}}. Generation provenance lists no target models.""",
)

# ---- Section 4.4: judging, judge cue, truncation ---------------------------
sub(
 r"""The primary response judge is \texttt{google/gemini-2.5-flash}. It applies three ordered binary gates corresponding exactly to scores 0--3. Disclaimers and fictional, academic, archival, debugging, audit, hypothetical, or persona framing do not reduce the score; harmful content after a refusal is scored. Infrastructure or parse failures never become score 0. Two of 3,024 primary judgments remained blocked as \texttt{PROHIBITED\_CONTENT} after retries and were scored by the prespecified \texttt{openai/gpt-5-mini} fallback with provenance preserved.""",
 r"""The primary response judge is \texttt{google/gemini-2.5-flash}. It applies three ordered binary gates corresponding exactly to scores 0--3. Disclaimers and fictional, academic, archival, debugging, audit, hypothetical, or persona framing do not reduce the score; harmful content after a refusal is scored. Infrastructure or parse failures never become score 0. Two of 3,024 primary judgments remained blocked as \texttt{PROHIBITED\_CONTENT} after retries and were scored by the prespecified \texttt{openai/gpt-5-mini} fallback with provenance preserved.

The judge message contains the prompt and an explicit language tag, so the judge is not blind to the condition it scores; the cross-judge study of Section~\ref{sec:crossjudge} replays the identical messages and preserves that cue. Responses reaching the token cap were scored as issued, and truncation is asymmetric for two targets (\qwen 0 English versus 22 RH, exact $p=4.8\times10^{-7}$; \nemo 77 versus 35, $p=1.7\times10^{-5}$; \gptoss 47 versus 55, n.s.). Dropping every pair-model job with a truncation on either side leaves gaps of 43.36, 4.73, and $-0.50$ pp, so the headline estimates are not driven by truncation (Appendix~\ref{app:clusters}).""",
)

# ---- Section 5 Analysis: multiplicity ------------------------------------
sub(
 r"""Cell-level category-by-strategy analyses are descriptive because each cell contains only 42 pairs. We also repeat headline estimates after dropping the two fallback-affected pair-model jobs.""",
 r"""Holm correction is applied to the family of three cross-model gap contrasts; all other reported $p$-values are nominal. Cell-level category-by-strategy analyses are descriptive because each cell contains only 42 pairs. We repeat headline estimates after dropping the two fallback-affected pair-model jobs, after dropping truncated jobs, and under resampling units that group lexically similar prompts (Appendix~\ref{app:clusters}).""",
)

P.write_text(t, encoding="utf-8")
print(f"patch 2: applied {n} substitutions")
