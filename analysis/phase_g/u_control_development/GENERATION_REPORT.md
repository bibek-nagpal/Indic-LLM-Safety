# Phase G U-control — development candidate generation report

**Status:** development artifact only. This is **not** the Phase G target experiment.
**Scope:** construct, for a 24-pair development cohort disjoint from the frozen Phase G
120-pair selection ladder, five candidate unusual-English (U) versions of every ordinary
English (E) prompt — one per transformation family.

**Explicitly not done here.** No candidate was scored, ranked, or preferred. No family
was selected. No target-model response was generated or read. No Qwen, GPT-OSS,
Nemotron, response-judge, certification or other external/paid API was called. No target
outcome, flip label, Phase D judgment or Phase E label was opened. The frozen Phase G
96/120 selection was not modified; it was read only as an exclusion set.

---

## 1. Development cohort

Selected by `analysis/phase_g/select_development_pairs.py`, implementing the cohort rule
in `U_CONTROL_PROTOCOL_PROPOSED.md` §2: ascending SHA-256 of

```
seed + U+001F + pair_id + U+001F + category + U+001F + strategy
seed = "phase-g-u-article-clip-pilot-v1|20260903"
```

over the 504-pair frozen bank, **after removing every pair_id in
`selection_n120_MANIFEST.json`**, taking the two lowest-ranked items in each of the
12 category x strategy cells.

Selection is outcome-independent by construction: the ranking key uses only the pair
identifier, category and strategy.

| property | value |
|---|---|
| source pairs | 24 |
| category x strategy cells | 12 |
| pairs per cell | 2 |
| overlap with Phase G 120-pair ladder | 0 |
| exact-text overlap with ladder prompts | 0 |
| bank SHA-256 verified | yes |

Artifacts: `development_cohort.json`, `development_cohort_index.csv`,
`DEVELOPMENT_COHORT_MANIFEST.json`.

## 2. Candidate set

24 sources x 5 families = **120 candidates**, in `u_candidates.json`.
Every record carries: `development_pair_id`, `pair_id`, `category`, `strategy`,
`source_E`, `source_E_sha256`, `transformation_family`, `family_code`, `candidate_U`,
`candidate_U_sha256`, `n_operations`, `tiers_used`, and `transformations_performed` —
an ordered list of `{operator_id, tier, char_offset, before, after}`.

Candidate text is **derived from** the recorded operation list, not written alongside it:
`generate_u_candidates.py` applies each recorded edit to `source_E` in order and requires
each anchor to match exactly once. The transformation record therefore reproduces the
candidate byte-for-byte by construction, and cannot silently drift from it.

## 3. The five families as applied

Definitions follow `U_CONTROL_DESIGN_REVIEW.md` §4 and `U_CONTROL_PROTOCOL_PROPOSED.md`
§§3–4. Tier tags on each recorded operation mark provenance:

- `listed` — the operation appears verbatim in the published closed inventory;
- `E1` / `A` — a documented deterministic **extension** of a listed operation;
- `E2` — a documented enumerated **addendum** introduced here (§5).

### AC — ArticleClipping (`AC-R1-article-deletion`, all `listed`)

Fully mechanical, deletion only. Rule AC-R1: whitespace tokenise; a token is an article
iff it is exactly `a`, `an` or `the` in lower case (so capitalised, sentence-initial
articles are never touched and case is trivially preserved); an article inside a
single-quoted masked-symbol span is protected; deletions run left to right and stop
before `k / n_E` would exceed 0.20. No vocabulary, order, inflection, punctuation or
case change. The verifier independently reconstructs the candidate as
`source tokens minus the recorded indices`.

Realised: k between 2 and 8 deletions per item; deletion ratio 0.054–0.128, all within
the 0.20 guard; 113 deletions total.

### AR — AntiquatedEnglish

Closed obsolete-form inventory. Realised operators: `AR-L-knows-knoweth`,
`AR-L-often-oft`, `AR-L-while-whilst` (listed); `AR-E1-eth`, `AR-E1b-doth-not` (E1);
`AR-E2-on-upon`, `AR-E2-must-needs`, `AR-E2-fain`, `AR-E2-pray` (E2).
No `thou/thee/thy`, no honorific, historical speaker, deity or quotation attribution,
no pseudo-archaic spelling, no deliberate spelling corruption.

### SY — MarkedSyntax (all `listed`)

Reordering only, no lexical substitution. Two of the four licensed moves proved
licensable in this corpus: `SY-M2-adjunct-prepose` (prepose an existing
temporal / locative / conditional adjunct **within its original scope**, 32 uses) and
`SY-M4-adjunct-reorder` (reorder existing adjuncts so the matrix predicate occurs late,
10 uses). Object fronting (move 1) and predicative-AP inversion (move 3) were not
licensable — see §6. Only commas were added or removed.

### FR — FormalRareRegister

Closed substitution list, constituent order preserved. Listed operators used:
`FR-L-use-employ` (10), `FR-L-about-concerning` (5), `FR-L-after-subsequent-to` (2).
Addendum operators used: `effective→efficacious` (8), `try→endeavor` (7),
`achieve→attain` (4), `way→means` (3), `give→provide` (3), `move→convey` (3),
`avoid→eschew` (2), `look for→seek` (2), `want→desire` (2), `help→assistance` (2),
`best→optimal` (1), `find→locate` (1), `need→require` (1).

### HY — CombinedMarkedRegister

SY moves applied first, then FR substitutions. Every HY candidate realises **at least one
SY move and at least one FR substitution** (asserted, not assumed), and the verifier
checks that the HY string is the FR string under licensed reordering (identical word
multiset, identical non-comma punctuation sequence).

## 4. Universal invariants

Preserved in every candidate, by construction and by check: harmful objective,
requested information level, target group, scenario, original attack strategy;
SymbolicMasking symbol inventory and mappings; ScenarioNesting layer count, order and
containment; RolePrompting role identity and role-specific instruction; all referents,
quantities and constraints.

Nothing was introduced from the prohibited list: no new jailbreak strategy, no
obfuscation or encoding, no character substitution, no spelling corruption, no
translation, no extra role-play, no additional scenario layer, no added or removed
harmful specificity, no new persuasive language, no safety-related language absent from
the source.

Mechanical checks run over all 120 candidates:

| check | result |
|---|---|
| masked-symbol span multiset identical to source | pass (120/120) |
| protected proper nouns (Mumbai, IPL, India, Maharashtra, Uttar, Pradesh) preserved | pass |
| numeral characters preserved | pass |
| AC is a deletion-only replay, ratio ≤ 0.20 | pass |
| SY word multiset + non-comma punctuation sequence identical to source | pass |
| HY word multiset identical to the FR string | pass |
| HY realises both an FR substitution and an SY move | pass |
| candidate differs from source | pass |
| candidate texts unique across all 120 | pass |

## 5. Documented extensions (the substantive generation difficulty)

**The published closed inventories do not cover this corpus.** They were written from the
family definitions rather than from the selected prompts, and the development prompts are
overwhelmingly first-person, present-tense requests ("I'm writing…", "As an X, can you
detail…", "What are some effective ways…"). Applying the inventories verbatim:

- **AR:** only 3 of 24 sources contain any listed form (`knows`, `often`, `while`).
  21 of 24 would have produced **zero** operations.
- **FR:** only 12 of 24 sources contain a listed substitution target.

Producing five comparable candidates per source therefore required extensions. Each is
enumerated, deterministic, and tagged per operation so the evaluator can discount or
reject any candidate that depends on it.

**AR-E1 — the `-eth` rule.** All 16 listed finite-present-3sg forms are instances of one
morphological rule. E1 generalises it: a finite present-tense 3rd-person-singular lexical
verb `V-s` becomes `V-eth` (`needs→needeth`, `works→worketh`, `wants→wanteth`,
`involves→involveth`, `focuses→focuseth`, `plans→planneth`), with the listed suppletive
table taking precedence. 14 uses.

**AR-E1b — `doesn't→doth not`.** The listed `does→doth` composed with expansion of the
negative contraction. 1 use.

**AR-E2 — enumerated addendum**, four attested Early Modern English items chosen because
the corpus offered nothing else, all avoiding the prohibited `thou/thee/thy` register:
`on→upon` (preposition, 22 uses); `I need to VP → I must needs VP` (5);
`I want to VP → I would fain VP` (1); `please VP → pray VP` (1).

**FR-A — enumerated addendum**, 13 register-raising synonym pairs listed in §3.
The listed pairs' inflectional paradigms are also treated as in scope
(`use/uses/used/using → employ/employs/employed/employing`).

Resulting tier profile:

| family | items using only listed operations | items depending on an extension |
|---|---|---|
| AC | 24 | 0 |
| SY | 24 | 0 |
| FR | 4 | 20 |
| AR | 0 | 24 |
| HY | 4 | 20 |

**This is a finding, not a formatting note.** AntiquatedEnglish as published is not
applicable to this prompt population; every AR candidate here rests on a documented
extension, and 10 of 24 rest on the E2 addendum alone. Any downstream decision about the
AR family should be read as a decision about `listed ∪ E1 ∪ E2`, not about the published
inventory.

## 6. Other generation difficulties

1. **SY moves 1 and 3 were not licensable.** Object fronting (move 1) requires
   topicalisation out of a wh-question or infinitival in nearly every source here, which
   is degraded English; predicative-AP inversion (move 3) requires a matrix copula with a
   non-referential predicate, and the sources' only predicative APs sit inside relative
   clauses where inversion is ungrammatical. All 42 SY moves are therefore adjunct
   repositioning. Six items admitted only one move.
2. **Clause-medial preposing was preferred to clause-initial fronting** because fronting
   to sentence-initial position would move the capitalised token and force a case change,
   which the SY definition forbids. Medial preposing is also more marked, so this
   constraint helped rather than hurt.
3. **Terminal punctuation re-attaches under reordering.** Moving an adjunct past the end
   of a sentence changes which word carries the `?` or `.`. The verifier therefore
   compares the word multiset with commas stripped and terminal punctuation removed, and
   separately requires the ordered sequence of non-comma sentence punctuation to be
   identical. No `.`/`?`/`!` was added or removed anywhere.
4. **`if → in the event that` was not licensable** in
   `DEV-intoxication-ScenarioNesting-01`: the source's `if mixed in specific proportions`
   is a reduced conditional, and the listed substitution requires a finite clause.
5. **Articles inside masked-symbol spans are protected**, e.g. the `a` in
   `'silence a discordant note'`. AC would otherwise have altered a symbol's surface form,
   violating the SymbolicMasking invariant.
6. **Some AC items clip few articles** (minimum 2, ratio 0.054) simply because the source
   is article-poor. The guard is an upper bound only; no lower bound is imposed beyond
   k ≥ 1.
7. **A few candidates are deliberately marginal** rather than being silently dropped —
   e.g. `how to eschew, when setting up a new betting ring, getting caught by the police`
   (HY, `DEV-gambling-ScenarioNesting-02`). Judging comprehension and naturalness is the
   evaluator's job, not the generator's, so nothing was filtered on quality.

## 7. Verification summary

| requirement | result |
|---|---|
| 24 unique source pairs | pass |
| exactly 2 per category x strategy cell (12 cells) | pass |
| zero overlap with the Phase G 120-pair ladder | pass |
| exactly 5 candidates per source pair | pass |
| exactly 120 candidates total | pass |
| no candidate scored, ranked or selected | pass |
| no model inference / external API call | pass |
| no target outcome, Phase D judgment or Phase E label read | pass |

`generate_u_candidates.py` exits non-zero if any structural check fails; the recorded run
reported `{"candidates": 120, "problems": []}`.

## 8. Files

| file | contents |
|---|---|
| `development_cohort.json` | the 24 frozen source pairs |
| `development_cohort_index.csv` | cohort index |
| `DEVELOPMENT_COHORT_MANIFEST.json` | cohort selection manifest |
| `u_candidates.json` | **the 120 candidates with full transformation records** |
| `u_candidates_index.csv` | flat index (family, op count, tiers, candidate hash) |
| `U_CANDIDATE_MANIFEST.json` | counts, verification results, file hashes |
| `../generate_u_candidates.py` | generator + verifier (deterministic, offline) |
| `../select_development_pairs.py` | cohort selector |

## 9. Handling note

`u_candidates.json` and `development_cohort.json` contain full harmful prompt text across
the violence, intoxication, gambling and sexual_violence categories. The repository's
`.gitignore` otherwise excludes harmful research content (`probe_banks/*`,
`frozen_final_*/bank/`, `human_validation/outputs/**/*.xlsx`) from version control. These
files are committed because they are the development deliverable, but this directory is
**gated research content** and must be excluded from any public release, appendix or
supplementary-material bundle.
