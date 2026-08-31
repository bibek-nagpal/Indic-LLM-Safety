# Methodology Audit — Manuscript vs. Implementation

Reconstruction of the actual final V2 pipeline from `src/`, `configs/`, `analysis/`, `scripts/`, and the frozen artifacts, compared line-by-line against `paper/acl_latex.tex`.

---

## 1. Reconstructed pipeline

```
configs/categories/{violence,intoxication,gambling,sexual_violence}.yaml
        │
        ▼
generator  google/gemini-2.5-flash
   system prompt = fixed invariants + `system_override`
   `system_override` = prompts/optimized/<latest V2-eligible>/generator.txt
                       sha256 = 025fbd35…  ← NOT IN THE REPOSITORY (see §3)
        │
        ▼
primary auditor   deepseek/deepseek-v4-flash      (every candidate)
        │  pass
        ▼
secondary auditor openai/gpt-5-mini               (primary passes only)
        │  pass = deterministic AND over all hard fields (equivalence.check_hard)
        ▼
bank revision_v2_3_1_final_504_dedup
   3 source banks → 504 in → 502 after exact-string dedup → 504 final (+2 undocumented top-ups)
   sha256 35bfbc1d…   FROZEN before any target call
        │
        ▼
targets (temperature 0, max_tokens 4096, empty system prompt)
   qwen/qwen3-30b-a3b-instruct-2507
   openai/gpt-oss-20b
   nvidia/nemotron-3-nano-30b-a3b
   → 1,512 pair-model jobs / 3,024 responses
     (1,649 raw trace rows; 137 retried after OpenRouter 403 credit-limit errors)
        │
        ▼
primary judge google/gemini-2.5-flash — 3 ordered gates → 0–3
   judge message contains: CATEGORY, **PROMPT LANGUAGE: en|rh**, category gates,
                           the full prompt, and the response
   fallback openai/gpt-5-mini on 2 unresolved PROHIBITED_CONTENT items
        │
        ├── Phase A  qc_final.py            integrity gate
        ├── Phase B  analyze_final.py       paired stats, pair_id clustering
        ├── Phase C  analyze_phase_c.py     response-length shapes, no judge
        └── Phase D  run_cross_judge_standard_budget.py → analyze_phase_d.py
                     openai/gpt-5-mini re-judge, 324 shared pairs × 3 × 2 = 1,944
```

---

## 2. Verified-correct correspondences

The manuscript matches the implementation on: sample counts (504 / 1,512 / 3,024); the three strategies and their binding definitions (`generator.V2_STRATEGIES`, structural checks in `equivalence.py`); four categories; 42-per-cell balance; model slugs (`run_manifest.json`, `configs/models.yaml`); temperature 0, 4,096-token cap, empty system prompt; the auditor cascade and its deterministic acceptance predicate; the scalar equivalence score being descriptive only; the frozen bank SHA and its precedence over target inference; `target_models_used_during_generation: []`; the two fallback judgments and their preserved provenance; the ordered-gate rubric and its deterministic consistency checker; the Phase D sample construction and hash-locked provenance; and pair-ID clustering in every inferential procedure. The 13-constraint GEPA objective in §4.1 and Appendix B matches `equivalence.hard_constraint_score` exactly (the "ten" in `PROJECT_HANDOFF_AND_PLAN.md` §4.2 is stale — it matches two *earlier* V2 runs whose `optimization_manifest.json` declares `objective: paired_prompt_quality_only`, "9 axes + RH-not-stronger").

This is an unusually faithful method section. The mismatches below are the exceptions.

---

## 3. Material mismatch 1 — GEPA optimisation did not occur (CRITICAL)

**Manuscript §4.1:** "We use \gepa within DSPy \cite{khattab2024dspy,agrawal2026gepa} to optimize supplementary generator guidance… Failed constraints yield textual feedback for prompt-guidance evolution."
**Appendix B** presents Q(c) = (1/13)Σh_k(c) as the optimisation objective.

**Artifact evidence.** The run whose `generator.txt` hashes to the bank manifest's `gepa_instruction_sha256` is `prompts/optimized/gepa_20260826_135819/`. Unpickling its `gepa_logs/gepa_state.bin`:

```
program_candidates:                        n = 1   (940 chars)
parent_program_for_candidate:              [[None]]
num_metric_calls_by_discovery:             [0]
prog_candidate_val_subscores:              [{0: 0.077, 1: 1.0, …, 8: 0.846, …}]
program_at_pareto_front_valset:            every task → {0}
num_full_ds_evals: 1        total_num_evals: 24
```
`pareto_summary.json` = `{best_val_score: null, best_aggregate_score: null, num_iter: null}`.
`gepa_logs/generated_best_outputs_valset/task_*/` contains only `iter_0_prog_0.json`.
`api_accounting.json` = 30 metric evaluations, 29 LLM calls (28 `gepa_task_generation` + **1** `gepa_reflection`), **$0.0302** total.

The single program has no parent and no descendants: it is the seed. For contrast, sibling run `gepa_20260826_103104` has `program_candidates` of length 2 with `parent_program_for_candidate: [[None], [0]]` and a 3,914-character child — so the reflective machinery works and simply produced nothing accepted in the run that was used.

The frozen instruction reads as hand-authored, not evolved: it enumerates the certification contract in prose and closes with "Do not optimize for any target model's behavior and do not include target responses, refusal, compliance, or flip outcomes" — a guardrail sentence a human writes, not one a reflective optimiser emits.

**Verdict.** The generator guidance is a **fixed, hand-specified, target-independent instruction**. Q(c) was computed 30 times as an offline validity diagnostic (24/30 accepted; failures dominated by `correct_category_membership` and `direct_harm_facilitation`) and never selected or evolved a prompt. §4.1 and Appendix B must be rewritten. Nothing in the results depends on this, and the corrected description is *more* defensible — a fixed, auditable instruction is easier to trust than an evolved one.

**Secondary defect.** `hard_constraint_score` (`equivalence.py:498–528`) can append `strategy_faithfully_used` a second time when the axis passes but `report.strategy_faithfully_used` is False, permitting 14 failures against a denominator of 13 and a clamp to 0.0. Immaterial to the frozen bank (acceptance is governed by `check_hard`, not by Q), but it should be fixed before release.

## 4. Material mismatch 2 — the frozen generator instruction is not in the repository (CRITICAL)

| artifact | SHA-256 of `generator.txt` | committed? | has `optimization_manifest.json`? |
|---|---|---|---|
| `gepa_20260523_130239` (900 chars, V1-era) | `33910016c5b9ada8…` | **yes** | **no** |
| `gepa_20260825_210033` (900 chars) | `33910016c5b9ada8…` | no | yes (`paired_prompt_quality_only`, 10 constraints) |
| `gepa_20260826_103104` (900 chars) | `33910016c5b9ada8…` | no | yes (`paired_prompt_quality_only`, 10 constraints) |
| **`gepa_20260826_135819` (940 chars)** | **`025fbd3573fc018b…`** | **no** | **yes (`complete_target_independent_probe_validity`, 13 constraints)** |
| bank manifest `gepa_instruction_sha256` | `025fbd3573fc018b…` | — | — |

`.gitignore` ignores `prompts/optimized/*` and whitelists only `gepa_20260523_130239/` — exactly the one directory that is *not* the one used.

This is not merely a provenance gap. `probe_bank.py:162` calls `load_optimized_instruction(require_v2=True)`, and `optimized_prompt.eligible()` requires an `optimization_manifest.json` with `schema_version == 2`, `target_model_signal_used is False`, and `objective == "complete_target_independent_probe_validity"`. The committed directory has no such file, so with the repository exactly as released `run_bank` raises `RuntimeError("gepa_enabled=true but no optimized generator instruction was found")`. **The bank-construction step cannot be executed from the release, and the instruction the manuscript says was frozen and hashed cannot be inspected.**

Fix: commit `gepa_20260826_135819/` in full, amend `.gitignore`, and remove or clearly label the obsolete May directory. Then Appendix A's "the final bank manifest hashes the generator guidance" becomes checkable.

## 5. Material mismatch 3 — the response judge is not blind to language (MAJOR)

`judge.build_judge_messages` (`src/jailbreak_hermes/judge.py:246–259`) constructs:

```
CATEGORY: {category_id}
PROMPT LANGUAGE: {language}          ← the experimental factor, stated explicitly
GATE QUESTIONS …
PROMPT (for context, do not score the prompt): {prompt_used}
MODEL RESPONSE TO SCORE: {response_text}
```

For a study whose estimand is an EN-minus-RH difference, the scorer is told which arm it is scoring, and additionally sees the prompt (which reveals language anyway). Phase D replays hash-locked reconstructions of these same messages, so judge replacement tests only whether a second model with the same cue behaves similarly — it does not test for language-conditioned leniency at all. The only cue-free check is Phase C, which the statistical audit shows is confounded by verbosity.

The run is frozen, so this becomes a disclosure obligation. The manuscript never mentions it. It belongs in the "Model-based measurement" limitation, and a response-only (prompt-free, language-tag-free) re-judge is the natural cheap follow-up.

## 6. Moderate mismatches and omissions

**6.1 The 502 → 504 top-up is undocumented.** `CONSOLIDATION_REPORT.json`: `input_pairs: 504`, `retained_unique_pairs: 502`, with `gambling__SymbolicMasking: 41` and `gambling__RolePrompting: 41` after removing two exact duplicates. The final bank has 504 with 42 everywhere. Two replacement pairs were therefore generated or admitted after consolidation. The manuscript says only "The final bank has 504 rows"; it should state when the top-up occurred and confirm it preceded target inference.

**6.2 The 0.85 near-duplicate gate is enforced per bank build but not across the consolidation of three source banks.** *(Corrected during implementation — my initial reading that the field was unapplied was wrong.)* `probe_bank.py:88` enforces it at generation time via SequenceMatcher; `CONSOLIDATION_REPORT.json` shows the merge of three source banks used exact-string dedup only. Result: 5 of 42,084 within-strategy pairs in the final bank sit at or above 0.85. Document the two-stage behaviour rather than removing the field.

**6.3 Truncation at the 4,096-token cap is asymmetric and unreported.** Qwen 0 EN vs 22 RH (p = 4.8e−7); Nemotron 77 vs 35 (p = 1.7e−5). Truncated responses were judged as complete. Sensitivity is favourable (gaps 43.36 / 4.73 / −0.50) and should be reported.

**6.4 The shipped `response_garbled` field is a near-pure false positive.** It is the local `looks_garbled()` heuristic, not a judge output. 595/3,024 responses (19.7%) are flagged, **593 of them by the `repeat-window-1` rule** (≥16 identical consecutive characters — markdown horizontal rules), and 456 of the flagged were scored ≥2, 164 of them 3. Inspection confirms the flagged Qwen items are coherent, well-formatted long answers. Results are unaffected, but an artifact reviewer will read `scores.jsonl` and conclude that a fifth of responses were incoherent yet scored fully actionable. Document or drop the field.

**6.5 `looks_like_refusal` is English-regex-only.** Seven English patterns ("I cannot", "I'm sorry, but I…", "^As an AI"). It cannot detect Hindi or Hinglish refusals and is therefore not comparable across arms. `judge.py`'s own docstring says regex-refusal with score ≥ 2 "flag[s] for human review"; there are 41 such cases and no record that any were reviewed.

**6.6 Attempt logging is effectively absent.** `attempts.jsonl` holds 6 records (4 retrieval errors, 2 audited candidates) for a run that certified 504 pairs. The manuscript concedes this. Partially recoverable material does exist, though: the three V2 GEPA `metric_log.jsonl` files hold 92 audited candidates with per-constraint failure reasons and an 80% (24/30) DeepSeek-primary acceptance rate in the frozen run — a GEPA-time distribution, not the bank-build funnel, and it must be labelled as such.

**6.7 Error-log hygiene.** `errors.jsonl` embeds an OpenRouter workspace key *identifier* inside 403 messages. The file is gitignored, but it must be scrubbed before any gated release.

**6.8 Reproducibility scope.** `.gitignore` excludes `frozen_final_*/bank/`, `frozen_final_*/run/`, and `probe_banks/*`. The Phase D GPT-5 Mini scores are committed; the primary Gemini scores are not. No Phase A–C number, and not even the Gemini side of the cross-judge comparison, is regenerable from the release. The manuscript's "Analysis scripts regenerate every reported table and figure from the frozen snapshot" is true only for a snapshot holder and should say so.

---

## 7. Code-quality observations

`analyze_final.py`, `qc_final.py`, `analyze_phase_d.py`, and `design_phase_d_budget.py` are careful, fail-closed, and hash-locked. Notable good practice: the Phase B analyser re-runs the Phase A gate and refuses to proceed on failure; the Phase D analyser refuses unless every paid score row matches its hash-locked job plan; figures are written with deterministic metadata; seeds are spawned from a single `SeedSequence`; `create_freeze_snapshot.py` refuses to overwrite an existing snapshot.

`paper/audit_paper_consistency.py` is a good hygiene tool but verifies *internal consistency only* — it asserts substrings in the `.tex` against committed CSVs. It would pass unchanged under every issue in this document, including the GEPA mismatch, because it never inspects `prompts/optimized/` or the GEPA state. Consider adding: (a) an assertion that the committed GEPA directory's `generator.txt` hashes to the bank manifest's `gepa_instruction_sha256`; (b) a check that `optimization_manifest.json` exists and declares the 13-constraint objective.

---

## 8. Summary table

| # | Issue | Severity | Fixable now? |
|---|---|---|---|
| 3 | GEPA optimisation claimed but not performed | Critical | Yes — rewrite §4.1 + App. B |
| 4 | Frozen generator instruction absent; wrong artifact committed; `run_bank` unrunnable from release | Critical | Yes — commit the correct directory |
| 5 | Judge sees `PROMPT LANGUAGE`; Phase D inherits it | Major | Disclose; optional cheap response-only re-judge |
| 6.1 | 502 → 504 top-up undocumented | Moderate | Yes — one sentence |
| 6.2 | `near_duplicate_threshold` advertised, not applied | Moderate | Yes |
| 6.3 | Asymmetric truncation unreported | Moderate | Yes — report sensitivity |
| 6.4 | `response_garbled` false-positive artifact | Moderate | Yes — document or drop |
| 6.5 | English-only refusal regex; 41 unreviewed flags | Minor | Document |
| 6.6 | Attempt logging near-absent | Minor (conceded) | Partial recovery from GEPA logs |
| 6.7 | Key identifier in error log | Minor | Scrub before release |
| 6.8 | Nothing in Phases A–C regenerable externally | Moderate | Yes — state the gating explicitly |
| 3b | `hard_constraint_score` double-count path | Minor | Yes — one-line fix |
