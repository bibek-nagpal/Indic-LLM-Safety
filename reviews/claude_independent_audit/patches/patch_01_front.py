"""Manuscript patch 1/4: abstract, introduction, contributions, related work, Table 1."""
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

# ---- abstract -------------------------------------------------------------
sub(
 r"Paired analysis shows sharply different language effects: the English-minus-RH refusal gap is 43.06 percentage points (95\% CI 38.49--47.62) for \qwen, 4.56 (1.39--7.74) for \gptoss, and $-1.79$ ($-6.55$--2.78) for \nemo. A judge-independent response-length check reproduces the same directional ordering. On an outcome-independent 324-pair subset per model, a complete GPT-5 Mini re-judge preserves the ordering and nearly reproduces the Qwen and GPT-OSS gaps, while making Nemotron more reverse-asymmetric. Absolute critical-severity rates are more judge-sensitive than the model ordering. These results support a narrow conclusion: language-conditioned safety robustness is strongly model-dependent in this Hinglish/RH setting; they do not estimate unsafe-response prevalence in organic traffic.",
 r"Paired analysis shows sharply different language effects: the English-minus-RH \emph{non-assistance} gap---the difference in the rate of responses carrying no domain-specific harmful content---is 43.06 percentage points (95\% CI 38.49--47.62) for \qwen, 4.56 (1.39--7.74) for \gptoss, and $-1.79$ ($-6.55$--2.78) for \nemo. A judge-independent response-length check reproduces the same directional ordering, though it partly reflects language-conditioned verbosity rather than harmfulness alone. On an outcome-independent 324-pair subset per model, a complete GPT-5 Mini re-judge preserves the ordering and nearly reproduces the Qwen and GPT-OSS gaps, while making Nemotron more reverse-asymmetric. Absolute critical-severity rates are more judge-sensitive than the model ordering. \qwen is robustly distinct from both other targets under every sensitivity we ran; \gptoss and \nemo are not reliably separated from each other. These results support a narrow conclusion: language-conditioned safety robustness is strongly model-dependent in this Hinglish/RH setting; they do not estimate unsafe-response prevalence in organic traffic.",
)

# ---- introduction: soften the attribution-gap claim ------------------------
sub(
 r"The central measurement problem is attribution. If an English prompt and a non-English prompt differ in intent, specificity, scenario, ambiguity, or adversarial framing, different responses cannot be assigned to language alone. Aggregate attack-success benchmarks answer whether an attack set succeeds. They do not necessarily answer whether a language/register change alters behavior for an otherwise matched request.",
 r"The central measurement problem is attribution. If an English prompt and a non-English prompt differ in intent, specificity, scenario, ambiguity, or adversarial framing, different responses cannot be assigned to language alone. Aggregate attack-success benchmarks answer whether an attack set succeeds rather than whether a language/register change alters behavior for an otherwise matched request. Matched-pair code-mixed evaluations do address that question \cite{banerjee2025attributional}; what remains open is how far the matching itself can be audited, and whether the effect is a property of models or of the register.",
)

# ---- contributions --------------------------------------------------------
sub(
 r"    \item a target-independent, equivalence-certified paired probe for English versus Hinglish/RH safety robustness;",
 r"    \item a target-independent paired probe in which equivalence is certified \emph{per item} by two independent auditor families rather than imposed by a construction rule;",
)
sub(
 r"    \item judge-independent length corroboration and an independent GPT-5 Mini re-judge demonstrating that the three-regime ordering survives judge replacement, although exact severity rates do not.",
 r"    \item judge-independent length corroboration of the directional flips, and a GPT-5 Mini re-judge showing that the model ordering survives judge replacement although exact severity rates do not.",
)

# ---- related work: matched-pair and Hinglish prior work --------------------
sub(
 r"In South Asian settings, IndicJR evaluates 12 languages and explicitly studies native, romanized, and mixed orthographies with a judge-free protocol \cite{pattnayak2026indicjr}. RomanSetu further shows that romanization materially changes tokenization and multilingual representations, motivating explicit treatment of Romanized text rather than assuming it behaves like native script \cite{j2024romansetu}.",
 r"In South Asian settings, IndicJR evaluates 12 languages and explicitly studies native, romanized, and mixed orthographies with a judge-free protocol \cite{pattnayak2026indicjr}. RomanSetu further shows that romanization materially changes tokenization and multilingual representations, motivating explicit treatment of Romanized text rather than assuming it behaves like native script \cite{j2024romansetu}. Cross-lingual safety-transfer failure was established early by \citet{yong2023lowresource}.",
)
sub(
 r"""These resources establish that language and orthography matter. Our complementary goal is matched-pair attribution: we trade language breadth for per-pair certification and use the identical certified pair set across targets.""",
 r"""\paragraph{Matched-pair and Hinglish-specific work.}
Closest to our design, \citet{banerjee2025attributional} pair English queries with linguistically equivalent code-mixed counterparts built from a Matrix Language Frame construction across ten languages, and report attack success rising from roughly 9\% to 69\% under code-mixing, with native-speaker validation in six languages. \citet{aswal2025haet} red-team models using phonetically perturbed code-mixed Hinglish. We differ on three axes: the register is Latin-script Romanized Hinglish rather than native-script code-mixing; equivalence is certified per item by two auditor families rather than imposed by a construction rule; and the estimand is a graded, model-resolved severity difference rather than aggregate attack success.

These resources establish that language and orthography matter, but not that they matter in one direction. IndicJR reports that romanized and mixed inputs \emph{reduce} jailbreak success under its contract-bound track, whereas we observe a large RH degradation on one target and none on another. Our model-resolved result suggests one reconciliation---the sign of an orthography effect may itself be model-dependent, so estimates pooled over models can point either way---and differing scoring protocols (a rule-based binary detector versus a graded rubric) may contribute as well. Our complementary goal is auditable matched-pair attribution: we trade language breadth for per-pair certification and use the identical certified pair set across targets.""",
)

# ---- Table 1: add Banerjee row, sharpen LinguaSafe --------------------------
sub(
 r"LinguaSafe & Multilingual, not matched & Translation/refinement & Graded severity & Cross-language safety & No RH track & Safety benchmark \\",
 r"LinguaSafe & Multilingual, not matched & Translation/transcreation & Graded severity & Cross-language safety & No Hindi; no romanized track & Safety benchmark \\" "\n"
 r"\citet{banerjee2025attributional} & Yes: EN/code-mixed & Construction rule (MLF) & Binary ASR & Cross-language ASR shift & Native-script code-mixing & Diagnostic study \\",
)
sub(
 r"\caption{Positioning based on the published protocols of each resource. ``No hard dual gate'' does not imply poor translation quality; it distinguishes translation/transliteration construction from our per-pair, two-auditor acceptance predicate. ASR is attack success rate and JSR is jailbreak success rate.}",
 r"\caption{Positioning based on the published protocols of each resource. ``No hard dual gate'' does not imply poor translation quality; it distinguishes translation, transliteration, or rule-based construction from our per-pair, two-auditor acceptance predicate. ASR is attack success rate and JSR is jailbreak success rate.}",
)

P.write_text(t, encoding="utf-8")
print(f"patch 1: applied {n} substitutions")
