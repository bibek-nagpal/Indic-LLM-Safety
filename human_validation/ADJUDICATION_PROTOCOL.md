# Phase E adjudication protocol (prespecified)

Fixed on 2026-08-31, **before** any human label exists. Frozen alongside the
sample so that no adjudication rule can be chosen after seeing results.

## 1. Primary analysis uses pre-adjudication labels

The reported human-validation results are computed from the two annotators'
independent labels exactly as returned. These labels are immutable: they are
never edited, re-scored, or replaced. Any adjudicated quantity is reported
separately and explicitly as secondary.

## 2. What is adjudicated

Only items where the two annotators differ by **two or more** scale levels
(|A − B| ≥ 2) are sent to adjudication. Adjacent disagreements (|A − B| = 1) are
left standing: on a four-point ordinal rubric they are ordinary measurement
noise, and resolving them selectively would manufacture agreement.

Items where either annotator ticked **Cannot read** are not adjudicated. They
are reported as missing data with their counts and are excluded pairwise from
agreement statistics.

## 3. Who adjudicates, and what they see

A third annotator, meeting the same language-competence requirement, resolves
the flagged items. The adjudicator sees the item's prompt, response, and rubric
and nothing else. In particular they do **not** see:

- either original annotator's label, or that the item was disagreed on beyond
  the fact that it was routed to them;
- any automated score from either judge;
- the model identity, language tag, pair ID, category, strategy, or any
  study conclusion.

The adjudicator scores the item afresh under the same rubric. The adjudicated
label for such an item is the adjudicator's score, not a negotiated consensus
and not the majority of three.

## 4. What is reported

- **Primary:** human A versus human B; each human versus the primary pipeline;
  each human versus the GPT-5 Mini re-judge. All from pre-adjudication labels.
- **Secondary, clearly marked:** the same statistics after substituting the
  adjudicator's score for each routed |A − B| ≥ 2 item in both annotator
  streams. Non-routed items retain their original A or B label; this avoids
  arbitrarily treating either annotator as the consensus source. We also report
  the count of adjudicated items and the distribution of adjudicated scores.

Both sets are produced by the same frozen script. If the primary and secondary
conclusions differ, both are reported and the difference is discussed.

## 5. No discussion-based consensus

Annotators do not meet to reconcile labels. Discussion of specific items is
permitted only on the familiarization set, before the main task begins, and
those items are never analysed.

## 6. Deviation

Any departure from this protocol must be recorded in writing, with its reason
and date, before the affected analysis is run, and reported in the paper.
