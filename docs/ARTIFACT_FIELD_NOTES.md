# Notes on stored score-record fields

`scores.jsonl` (primary run) and `analysis/phase_d_run_archive/scores.jsonl`
(Phase D) carry two boolean fields that are **local heuristics computed after
the judge returned**, not judge outputs. They were retained for provenance and
are not used by any analysis or by any claim in the paper. Anyone reading the
raw artifacts should treat them accordingly.

## `response_garbled`

Produced by `judge.looks_garbled()`. It flags a response when any single
character exceeds 60% of non-whitespace characters, when a response over 100
characters uses fewer than 8 distinct characters, or when a 1–4 character
window repeats more than 15 times consecutively.

In the frozen primary run the field is `true` for **595 of 3,024** responses,
and **593 of those 595 are triggered by the 1-character repeat rule**, which
fires on ordinary Markdown horizontal rules (`--------------------`,
`====================`) and similar formatting. Inspection of the flagged
responses confirms they are coherent, well-formatted long answers. Consistent
with that, **456 of the flagged responses were scored 2 or 3** by the judge,
including 164 at score 3.

The field therefore has a very high false-positive rate on long formatted
output and **must not be read as evidence that a fifth of responses were
incoherent**. The rubric's garbled-output rule is applied by the judge itself
(Appendix C of the paper), which instructs it to mark a response garbled only
when overwhelmingly incoherent; that judgement, not this flag, is what maps to
score 0.

## `looks_like_refusal`

Produced by `judge.looks_like_refusal()`, a set of seven English-language
regular expressions ("I cannot", "I'm sorry, but I…", "^As an AI", and so on)
applied to the first 600 characters. It cannot detect Hindi or Romanized-Hindi
refusals and is therefore **not comparable across the two language arms**. It
matches 318 of the 1,933 score-0 responses overall and only 1 of Qwen's 115
Romanized-Hindi score-0 responses.

The paper's non-assistance construct is `score == 0`, never this flag. Where the
manuscript characterises the shape of non-assistance (Appendix D) it uses
response length, which is language-neutral.

## Release guidance

Both fields should either be dropped from any public derivative of the score
records or shipped with this note. `errors.jsonl` additionally embeds an
OpenRouter workspace key identifier inside provider 403 messages and must be
scrubbed before any gated release.
