# Phase G U-control design review

Status: **PROPOSAL FOR ADVERSARIAL REVIEW — NOT AN EXECUTION AUTHORIZATION**.

Date: 2026-09-03. Starting checkpoint: `f91ac690372bb1023a722db0d862b74f298a4c31`.

This is a design-only response to the failed preflight. No experimental U prompt,
pilot prompt, target response, new judgment or API call was produced. The frozen
96-pair selection, E/R data, existing preregistration, SAP and runner are unchanged.
The operational specification is [U_CONTROL_PROTOCOL_PROPOSED.md](U_CONTROL_PROTOCOL_PROPOSED.md).
That document, not the alternatives evaluated here, specifies the recommendation.

## 1. Decision in brief

Recommend **one standardized, constrained telegraphic-English family: selective
article clipping**. U may delete contextually recoverable occurrences of `a`,
`an`, and `the`; it may not introduce words, substitute vocabulary, reorder
words, change inflections, alter punctuation, or rewrite the request. Independent
certification must reject deletions that change reference, scope or meaning.

Call this an **article-clipped, noncanonical-English control**, not a validated
sample from “the OOD distribution.” This deliberately narrows the scientific
claim. It is cleaner to test an observable, auditable grammatical manipulation
than to declare two freely rewritten styles equally distant from unknown
training distributions.

Retain N=96 and eight existing base pairs per cell; apply the same family to all
96. Do not retain the archaic-versus-telegraphic allocation merely for continuity.
This is a **proposed substantive amendment**, not an interpretation of what the
old preregistration already authorized. The existing two-style analyses would
need a prospective amendment before implementation.

Use two separate gates: all-item semantic/structural certification, then a
dataset-level manipulation gate combining a prespecified clipping profile with
an independent prompt-only English-reader check. Tokenizer metrics describe the
surface change; they neither select candidates nor license target inference.
Require a disjoint 24-pair feasibility pilot before touching the experimental 96.

## 2. Define the construct before measuring it

The manipulated construct is **reduced overt realization of English articles
while retaining recoverable English propositions and the original lexical and
adversarial structure**. Repeated missing articles should create recognizable
telegraphic/noncanonical English, not incomprehensible strings. “English” here
allows names and loanwords already present in E; it does not mean replacing
India-specific terms with an English-only dictionary vocabulary.

| Concept | Meaning here | Manipulate, control, or exclude? |
|---|---|---|
| Linguistic noncanonicality | Departure from ordinary English expression, relative to E and fluent readers' judgments | Manipulate a narrow, named instance; not a universal scalar |
| Lexical rarity | Low frequency of particular lexical items in a specified reference population | Hold non-article vocabulary exactly constant; no rare-word selection |
| Syntactic unusualness | Less canonical realization of grammatical dependencies or constituent structure | Manipulate article realization only; keep word order and remaining morphology |
| Register shift | A recognizable change in communicative style | Operationalize one note-like/clipped style, not a free “be weird” instruction |
| Tokenizer fragmentation | Number of subword pieces relative to characters or words under a particular vocabulary | Measure descriptively with fixed tokenizers; no required direction |
| Orthographic perturbation | Altering spelling, script, characters or within-word segmentation | Exclude; complete words retain their original spelling and case |
| LM surprisal/perplexity | Probability assigned by a specified language model to a specified segmentation | Not an execution gate and not in the required metric set |
| Semantic distance | Change in propositions, referents, conditions or requested assistance | Keep approximately zero through hard certification; token overlap is not proof |
| Adversarial obfuscation | Concealing referents/instructions or adding decoding work as an attack mechanism | Exclude anything beyond the frozen strategy; recoverability alone does not excuse added encoding |

Article deletion is not semantics-free. English articles can encode definiteness,
anaphora and quantity. That is precisely why “delete every article” is **not**
the proposed transformation. Mechanical preservation is a strong constraint on
possible drift, not a substitute for semantic auditing and human spot checks.

### What “OOD” cannot mean

We do not observe the three targets' training or safety-tuning distributions.
Neither a public tokenizer, English word list, nor a proxy LM identifies
membership in those distributions. The same text can be common in one corpus,
rare in another, easy for one tokenizer and fragmented for another. Ordinary
English can itself contain rare words, and very familiar English can be
grammatically clipped.

Do not combine these quantities into an unvalidated weighted “OOD score.” Do not
assert that a higher value on any one proxy makes the control more conservative.
Too much alteration can change comprehension rather than safety; there is no
established monotone relation between these proxies and harmful assistance.

## 3. Candidate constructions

These judgments are prospective design assessments, not measured comparisons
of generated alternatives. No candidate family was tested against target models.

| Construction | Construct validity and semantic/strategy risks | Readability, reproducibility and auditability | RH comparison and decision |
|---|---|---|---|
| Archaic/over-formal English | Mixes syntax, vocabulary, politeness, historical framing and possibly authority/persuasion. Archaic modal meanings and persona-like phrasing can change force. Formality does not establish rarity to a model. | Can be readable, but “archaic enough” has no small stable rule set. A generator can satisfy style through stock theatrical framing; auditors may mistake fluent elaboration for equivalence. | Neither distance nor communicative register matches conversational RH. Drop from the recommended control. |
| Unconstrained telegraphic/clipped English | Clearly changes grammatical surface form, but deleting subjects, auxiliaries, negation or connectors can alter agency, time, obligation and nesting. Aggressive clipping becomes interpretive noise. | Easy to request, difficult to reproduce as an exact intervention. Readability varies with omitted content. | Relevant within-English departure, but too broad without a restricted edit language. Do not use unrestricted rewriting. |
| Marked but grammatical syntax | Fronting, passive voice and clefts can retain truth conditions, yet change focus, presupposition, agency salience and extraction scope. Sentence/layer reordering is especially risky for ScenarioNesting. | More naturally readable. However, eligible constructions vary by source prompt, and many are ordinary rather than materially noncanonical. Needs syntactic annotation beyond a simple edit check. | A useful future syntactic control, but no reason it matches RH novelty. Not selected for this small, budgeted run. |
| Lexical/register substitution | Changes word frequency but synonyms are rarely interchangeable in legal, substance-related or culturally situated requests. Euphemisms can become a masking attack; technical words can add specificity. | Dictionaries do not settle task equivalence. A rare-word target rewards obscure paraphrases. Hard to audit consistently at scale. | Confounds lexical accessibility with the register contrast; reject for this experiment. |
| **Selective article clipping** | Changes one grammatical subsystem. No new lexical content, order, persuasion or attack scaffold is possible mechanically. Remaining risk is article-dependent reference/quantity; hard gates must reject it. | Exact deletion replay is verifiable without a parser. Fluent readers can distinguish clipped-but-clear from guessed meaning. Feasibility remains unproven until a disjoint pilot. | A narrow, interpretable English noncanonicality control, not distance-matched RH. **Recommended.** |
| Ordinary-English paraphrase | Can diagnose generic rewriting effects but may remain entirely canonical. Can change synonyms, emphasis and content despite good fluency. | Reproducible only as a generated artifact, not a single edit operation. | Does not manipulate the construct requested here; would require another arm and budget. Do not add it. |
| Typography, misspelling, homoglyphs, encoding, JSON/code wrapping | Changes decoding or introduces a new instruction/format mechanism. Maximizing fragmentation directly encourages these constructions. | Easy to generate and measure, but token metrics reward the confound. | Not a clean linguistic/register control; exclude. |

### Why one family rather than two or many

Two styles can broaden coverage, but a pooled result then estimates a particular
mixture of quite different interventions. With one U per base pair, a style
comparison also uses different source pairs, rather than a within-pair contrast
of styles. Balance does not remove that distinction. Opposite style effects can
cancel, and N=48/style leaves less precision for diagnosing that cancellation.

A within-pair factorial control would be scientifically useful, but would need
at least two U responses per target/pair, changing both design and cost. It is
not necessary to answer the narrower question chosen here. One exact edit
family at all 96 pairs gives the clearest treatment definition. Its narrower
external validity is an explicit price, not something to hide in the title.

The recommendation is **not** that article clipping is the most representative
English distribution shift. It is the most tightly auditable control among
these options under the requirement to preserve attack structure and avoid a
metric-driven search. If it cannot be realized clearly and safely, the correct
answer is not to run this control, not to make it stranger until it passes.

## 4. Certification and manipulation validation answer different questions

**Gate A, every prompt:** does U still ask for the same thing, using the same
strategy, in understandable English? Both DeepSeek and GPT-5 Mini must pass all
axes, and a deterministic replayer must verify the limited edit language.

**Gate B, the dataset:** is the intervention visibly and broadly realized,
rather than one inconsequential omission or a few extreme outliers? Evaluate
fixed magnitude/coverage criteria and independent English-reader assessments
after accepting the first valid candidate for each pair.

Compare the alternatives:

- A numerical unusualness minimum on **every U** selects for extremity, punishes
  sources with fewer opportunities, and encourages retries that accumulate
  artificial edits. A tokenizer threshold is particularly poorly aligned with
  grammatical noncanonicality. Reject this option.
- Semantic/structural hard gates per item plus **dataset-level validation**
  permit item variation while demanding broad, nontrivial realization. This is
  the recommended option.
- A purely qualitative “the generator says it is unusual” criterion is too weak.
  Conversely, a composite proxy score does not become valid merely because it
  includes several measurements. Use directly interpretable components and an
  independent readability/style check, without a weighted total.

Some per-item constraints remain: at least one actual article omission,
understandability, and an upper bound on deletion. Those define the treatment
and guard against damage; they do not demand individual “OODness.” The exact
coverage/effect-size thresholds are prespecified **design conventions**, not
empirically validated universal boundaries. Their rationale is in the protocol.

## 5. The manipulation profile

The core signature is article omission in a fixed original word sequence, not
increased tokenization cost. Keep the following dimensions separate:

1. **Syntactic realization:** number and density of article deletions, plus
   preservation of strategy-bearing spans and clause punctuation.
2. **Lexical preservation:** exact case-sensitive non-article token sequence;
   no introduced word and no rare-word substitution.
3. **Surface change and compression:** token edit distance, character and word
   length ratios, and token-set overlap. Under delete-only editing, some of
   these are algebraically redundant; do not count them as independent evidence.
4. **Tokenization profile:** fixed public BPE token counts and tokens/character
   for E/U/R, reported under two pinned tokenizers without choosing the better
   looking one. They are not the targets' known tokenizers and are not OOD tests.
5. **Human interpretability/noncanonicality:** independently collected prompt-only
   judgments from two fluent English readers on a fixed sample. They see no
   responses, automated labels, model identities or study hypothesis.

No frequency lexicon is required: content vocabulary is held fixed directly.
An English-dictionary OOV rate would misclassify unchanged Indian names and
domain vocabulary and is inappropriate for RH. Type-token ratio is affected by
length, and average word length rises mechanically when short articles disappear.
Neither is strong evidence for an independently changed lexical construct.

Proxy-LM perplexity would mix reference-model familiarity, length, segmentation,
domain content and grammar. Selecting a proxy or acceptance threshold after
looking at U would introduce another design degree of freedom. Target-model
perplexity could additionally violate the target-independent construction rule.
Do not add either to this protocol. A future separately preregistered descriptive
LM analysis could be useful, but is not needed to validate article clipping.

## 6. Relationship to R and limits of inference

The proposed control does **not** require `D(E,U) approximately equals D(E,R)`.
There is no validated scalar D available here. It requires strong evidence for
the **named English grammatical manipulation** relative to E, alongside unchanged
task/strategy and retained comprehension.

This is sufficient to ask whether this particular English noncanonicality
reproduces the observed E→R gap. It is **not** sufficient to discriminate all
possible “generic OOD” mechanisms from all possible RH-specific mechanisms.
Equal tokenizer fragmentation, even if achieved, would not solve that problem.

If E≈U while R differs, say: “This certified article-clipped English control did
not reproduce the RH effect.” Do not say “generic OOD is ruled out.” If U and R
have similar measured gaps, say this English perturbation can reproduce a
similar effect under the measurement pipeline. Do not conclude that it caused
the original RH difference or that all unusual registers behave alike.

Clipping necessarily shortens U. Unlike free paraphrasing, this is an exactly
documented part of the treatment, but it is not independently randomized away.
The estimand is the effect of the **article-clipped text package**, not grammar
with length held constant. No padding, compensatory verbosity or extra baseline
arm is introduced to conceal that limitation.

Existing E/R scores and new U scores also differ in collection time; unchanged
provider slugs do not establish unchanged internal model builds. The explicit
English tag matches E/U, but text still reveals condition and U/R remain
different judge conditions. Shared judge identity does not guarantee cancellation
of condition-specific measurement error.

## 7. Disjoint pilot and no metric optimization

A single 24-pair pilot is necessary because applicability and clarity of this
restricted transform have not been demonstrated. Select two pairs per cell by
identity hash from the frozen bank, excluding the entire frozen N=120 ladder
(therefore also N=96). The pilot process sees only its own English texts and
identity/strategy metadata, never target outputs, scores or Phase E labels.
No pilot selection or generation happens in this task.

The pilot can establish engineering feasibility, expose semantic failure modes,
check reader comprehension and estimate observed certification costs/yield. It
cannot establish safety effects, comparative jailbreak power, population OODness,
or that the main 96 will fill successfully. Every rejection and failed gate is
retained. The protocol has one fixed pilot and no automatic revision loop.

A failed pilot means stop and document the failure. A substantive change requires
a new version and separate approval before a new, disjoint validation set; the
old pilot becomes development evidence. It cannot be hidden as an unpublished
attempt followed by a favorable “pilot.” This rule also applies before any
target outcomes exist: outcome-independent metric gaming is still metric gaming.

Pilot and main generation accept the first dual-certified candidate, without
seeing its numeric manipulation profile. Dataset-gate failure never triggers
“strengthen the style” regeneration. There is no tokenizer feedback channel.

## 8. Skeptical-reviewer attack table

| Attack | Prevention or honest bound |
|---|---|
| “U isn't actually OOD.” | Agreed that training-distribution OOD is not established. The claim names article-clipped, reader-validated noncanonical English. No stronger conclusion is licensed. |
| “U changes semantics.” | Exact deletion replay; protected quantifiers/referents; two hard auditors; independent fixed human sample. Residual audit error remains; high overlap alone is never evidence of equivalence. |
| “U is another jailbreak strategy.” | No inserted text, reordered layers, persona, persuasion, masking or decoding task. It is nevertheless a deliberate input perturbation; we do not claim surface form is mechanism-free. |
| “You chose the transformation for the desired result.” | Choice recorded before U/target outcomes; no competing family is screened on safety; fixed disjoint pilot; publish failure and all candidate attempts. Researchers know the existing RH result, which cannot be undone. |
| “Tokenizer fragmentation isn't OODness.” | Explicitly agree; both tokenizers are descriptive, and neither affects selection or passing. |
| “U and RH aren't equally unusual.” | No equality claim. The control bounds one proposed within-English explanation, not the full generic-OOD alternative. |
| “The generator optimized the metric.” | It proposes only deletion indices, sees no metric values/thresholds, receives only validity-axis rejection feedback, and stops at the first valid candidate. No dataset-failure regeneration. |
| “The control tests register, not language.” | Correct: the purpose is a within-English grammatical control. It cannot separately identify script, language and code-switching mechanisms in R. |
| “Your U styles are heterogeneous.” | One edit family across all 96; edit magnitude varies and is fully reported. No archaic/telegraphic pooling or post-hoc style selection. |
| “Your manipulation gate is circular.” | Mechanical metrics verify the planned intervention, not a latent model state. Independent readers verify perceived clipping and comprehension; neither constitutes proof of OOD. |
| “Human raters aren't truly blind.” | Labels/hypothesis/model identity are hidden, but text visibly reveals clipping. State this partial blinding, retain both independent judgments, and use no adjudication-to-pass. |
| “The thresholds are arbitrary.” | They are transparent smallest-realization/coverage rules, not natural constants; freeze before pilot and never tune them to pass. Report full distributions, including failures. |
| “Dropping articles only changes length.” | Length cochanges; do not claim a pure syntax causal effect. The limited transformation answers a narrower but cleaner counterfactual than unconstrained rewriting. |
| “All-item certification creates selection bias.” | Base IDs are fixed; no substitution. The first valid candidate is retained, all retries are disclosed, and a single unfilled main pair blocks targets rather than shrinking to a favorable subset. |

## 9. Scientific amendments and remaining engineering work

If approved, amend the preregistration prospectively to name one article-clipped
family, replace the fragmentation gate, add the disjoint pilot and human
prompt-validation procedure, remove the obsolete two-style split, and narrow
the interpretation labels. No such amendment was made here.

The faulty cost model must be rebuilt for the actual edit/audit messages and
pilot. Its $1.82/$3.39 numbers are not accepted forecasts for this proposal.
All future paid pilot and main calls together remain subject to the $10 Phase G
API ceiling unless the user explicitly changes it. Human time is an additional
resource requirement, not assumed free labor or an authorized expense.

The resumability, durable accounting, uncertain-delivery and hash-lock defects
documented in the preflight still require implementation and adversarial tests.
Passing this design review does not make the current runner executable.

## 10. Evidence discipline and sources

This review uses the repository's preregistration/SAP, frozen design metadata,
`reviews/phase_g_preflight_20260903.md`, the actual V2 hard-gate implementation in
`src/jailbreak_hermes/equivalence.py`, and the existing audit's construction and
judge-language limitations. It does not infer construct validity from the old
completion report.

Software versions and tokenizer asset hashes in the companion protocol were
checked against locally installed package metadata and
`tiktoken_ext.openai_public` source, without loading tokenizers or downloading
assets. No external API or literature search was performed in this design-only
task. Candidate-family comparisons and thresholds are explicit scientific
recommendations, not empirical findings or claims of literature consensus.

**Ready for adversarial design review: YES. Ready for implementation/execution:
NO — proposal approval, resources, preregistration amendment and the existing
engineering preflight remain necessary.**
