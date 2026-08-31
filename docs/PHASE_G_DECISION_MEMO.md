# Phase G decision memo: fund it or not

**To:** project team
**Date:** 2026-08-31
**Repository state:** `f34074a`, built on the verified checkpoint `f913e17`
**Decision requested:** authorize or decline roughly two dollars of inference
**Status:** designed, preregistered, costed. **Not executed.** No U prompt exists.

---

## 1. The objection that is still open

Every other major reviewer criticism has been answered. This one has not.

Qwen3-30B-A3B withholds domain-specific harmful content on 65.87% of English
prompts but only 22.82% of matched Romanized-Hindi prompts -- a **43.06 pp**
non-assistance gap (95% CI 38.49-47.62). Equivalence certification controls
*what* is asked: intent, scenario, information level, attack strategy, cultural
specificity, target group, ambiguity, strategy structure.

It does not control **how far the surface form sits from the model's training
distribution.**

So a reviewer can still say: *this is not about Hinglish, it is about unusual
input, and Hinglish happens to be unusual.* Nothing in the frozen design can
answer that, because every existing arm is either ordinary English or Romanized
Hindi. It is the objection behind Reviewer 2's score of 2.

## 2. What Phase G tests

A third arm on the same frozen base pairs:

- **E** ordinary English (already collected)
- **R** Romanized Hindi / Hinglish (already collected)
- **U** semantically matched **unusual English** (new)

U is unambiguously English. If the effect is about the Hinglish register, U
behaves like E. If it is about surface-form novelty, U behaves like R.

The primary estimand is a paired difference-in-differences, per model:

```
Delta = (E - R) - (E - U) = mean( 1[s(U)=0] - 1[s(R)=0] )
rho   = (E - U) / (E - R)     the share of the RH effect that unusual English reproduces
```

Because the English arm is shared it cancels, so the primary test is an exact
paired test on U-versus-R discordant pairs. Clean, well powered, distribution-free.

## 3. Recommended design

| | |
|---|---|
| **N** | **96 base pairs**, 8 in each of the 12 category x strategy cells |
| Unusual English | two balanced sub-registers: archaic/over-formal, and telegraphic/clipped |
| Selection | SHA-256 rank of pair identity, frozen manifest, outcome-independent |
| Certification | DeepSeek V4 Flash + GPT-5 Mini, dual hard gate, English-to-English axes |
| Target inference | U arm only, same three models, temperature 0, 4,096 tokens, empty system prompt |
| Judging | Gemini 2.5 Flash on U; E and R judgments reused unchanged |
| Primary model | Qwen only -- the design is not powered for the other two, and says so |

**Why 96 and not 72 or 120.** The discriminating scenario is U reproducing three
quarters of the RH effect, which is the hardest case to distinguish from generic
OOD. Power there is 0.748 at N=72 (a reviewer would rightly call that
underpowered), **0.913 at N=96**, and 0.971 at N=120. N=120 buys 0.058 more power
for 25% more inference. The three selections are nested, so 96 can be extended to
120 later without invalidating anything.

## 4. What already exists and is reused

- All 504 frozen English and Romanized-Hindi target responses and their Gemini
  judgments. The 96 selected pairs contribute 192 existing responses at no cost.
- The generator, auditor and judge harnesses, prompts, parsers and rubric.
- The certification contract, adapted to English-to-English.
- The pair-clustered statistical machinery from Phases B-D.

**Only the U arm needs new inference.**

## 5. New inference and cost

| | N=72 | **N=96** | N=120 |
|---|---:|---:|---:|
| New target calls | 228 | **304** | 380 |
| Total new API calls (all stages) | ~650 | **~864** | ~1,080 |
| Expected cost | $1.36 | **$1.82** | $2.27 |
| Expected-high cost | $2.54 | **$3.39** | $4.24 |
| Hard ceiling | -- | **$10.00** | -- |

Every generation, certification and judging unit cost is *measured* from this
project's own billing ledgers, not from list prices. Expected-high assumes the
V2 bank-build funnel reproduces unchanged **and** an extra GPT-5 Mini cross-judge
is added. Derivation: `analysis/phase_g/COST_MODEL.md`.

**Dominant cost:** GPT-5 Mini secondary certification, at $0.005932 per call --
eight times the DeepSeek rate, and $7.07 of the $11.84 that built the entire V2
bank. Dropping to DeepSeek-only certification would save about $0.75. **We
recommend against it.** The recovered V1 evidence shows single-auditor
certification is exactly the failure that made V1 unusable; reintroducing it to
save under a dollar would be indefensible.

For scale: Phase D cost $3.68. Phase G at N=96 costs about half that.

## 6. Possible outcomes and what each would mean

The interpretation rule is fixed in advance, on the 95% interval for `rho`:

| Result | Reading | Consequence for the paper |
|---|---|---|
| CI upper bound < 0.50 | **Register-specific dominant.** Unusual English does not reproduce most of the RH effect. | The strongest outcome. The language-conditioned framing is vindicated against the main standing objection, and the paper can say so. |
| CI lower bound > 0.50 | **Generic-OOD dominant.** Unusual English reproduces most of it. | The paper must be reframed around distributional novelty rather than Hinglish. Painful, but it is the truth and far better found by us than by a reviewer. |
| CI spans 0.50, excludes 0 and 1 | **Mixed.** Both mechanisms contribute. | Report both components; claim neither exclusively. Still a substantially stronger paper than silence. |
| CI spans both 0 and 1 | **Inconclusive.** | Report the interval and claim nothing. Do not re-run at a different N to chase a threshold. |

We commit in advance to publishing whichever occurs, including the one that
weakens the headline.

## 7. Limitations Phase G will not remove

- **Not powered for GPT-OSS or Nemotron.** Their E-R gaps (4.56 and -1.79 pp) are
  too small; power never exceeds 0.21 at any N considered. Stated up front so
  their nulls cannot later be dressed up as findings.
- **Two sub-registers, not all of English.** It shows Hinglish differs from these
  two English sub-registers, not that it is unique among all registers.
- **No mechanism.** It is a behavioural contrast, not an account of what happens
  inside the model.
- **A third shared property** common to both R and U could still drive the effect.
- **Same rubric, same judge family.** Phase G inherits the measurement limitations
  of the frozen design, with one improvement: E and U are both judged under the
  `en` language tag, so the E-U contrast is made *within* one judge condition. The
  E-R contrast never was. That is a genuine partial repair of the judge-blinding
  limitation.

## 8. Relationship to Phase E

Phase G does **not** depend on Phase E succeeding, and can be run and analysed
whatever the human labels show. Three interpretation points should be revisited
once labels arrive:

1. Poor human-Gemini agreement on Qwen would mean stating Phase G conclusions in
   terms of *judge-measured* non-assistance.
2. A systematic human-judge offset largely cancels in a difference of
   differences; a *condition-dependent* offset would not, and would warrant a
   small human check on U responses.
3. If Phase E proves unusable, Phase G still runs; both are then reported as open.

Nothing in Phase G's selection, generation, certification, inference or primary
analysis may change in response to Phase E.

## 9. Recommendation

**Fund it. Run N=96.**

Three reasons.

**It is the last substantive scientific objection.** Everything else the
reviewers raised has been answered by the reconstruction, the audit and the
verification gate. This one is untouched, and it is the one that a competent
reviewer will raise first.

**It costs about two dollars.** Expected $1.82, expected-high $3.39, hard ceiling
$10.00 with an automatic abort. This is not a resource-allocation question; it is
a question of whether we want the answer.

**The downside risk is the point, not a reason to avoid it.** If unusual English
reproduces most of the effect, the paper's framing is wrong, and we would much
rather discover that ourselves than have it discovered in review. A preregistered
control that we commit to reporting either way is exactly what makes the
register-specific claim credible if it survives.

The one thing not to do is submit with this open and hope no reviewer presses it.

**Awaiting explicit authorization. Nothing will be executed until it is given.**
