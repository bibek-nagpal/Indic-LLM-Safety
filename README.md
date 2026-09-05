# IndicAlignProbe — English vs Romanized-Hindi safety asymmetry

A private research repository for a paired evaluation of open-weight language
model safety behaviour across two surface forms of the *same* request: English
and Romanized Hindi (Hinglish).

The construct measured throughout is **non-assistance**: a score of `0` on a
0–3 information-assistance scale. It is deliberately *not* called "refusal",
because a model can decline to assist without producing a refusal utterance,
and can produce a refusal utterance while still assisting.

> **This repository is private and stays private.** The prompt bank, the frozen
> run, and the annotation workbooks contain full research prompts and target
> responses. Those paths are ignored or gated by `.gitignore`; only manifests,
> hashes, identifiers and derived statistics are tracked. Do not make the
> repository public and do not commit the gated material.

## Headline result (frozen, V2)

504 certified EN/RH pairs (4 categories × 3 strategies × 42), bank
`revision_v2_3_1_final_504_dedup`, three target models, 1,008 responses per
model. Judged by `google/gemini-2.5-flash`, with a preregistered narrow
fallback to `openai/gpt-5-mini` on 2 of 3,024 responses.

| Model | EN non-assistance | RH non-assistance | Gap (pp) | 95% CI | Forward flips | Critical |
|---|---|---|---|---|---|---|
| Qwen3-30B-A3B | 65.87% | 22.82% | **+43.06** | [38.49, 47.62] | 219 | 85 |
| GPT-OSS-20B | 86.71% | 82.14% | +4.56 | [1.39, 7.74] | 42 | 15 |
| Nemotron-3-Nano | 62.10% | 63.89% | −1.79 | [−6.55, 2.78] | 65 | 22 |

The asymmetry is **model-dependent**, not universal. Source of truth:
`analysis/results/main_results.csv`. Bootstrap resampling clusters on
`pair_id`.

## Evidence boundaries

Not every directory in this repository carries the same evidential weight.
Read `docs/REPOSITORY_STRUCTURE.md` before citing anything from it. In short:

- **Load-bearing evidence** — `frozen_final_2026_08_29/` (manifest),
  `analysis/results/`, `analysis/phase_c_results/`, `analysis/phase_d_results/`,
  `analysis/phase_d_run_archive/`, `analysis/sensitivity_results/`,
  `human_validation/`, `accounting/`.
- **Incomplete and non-evidentiary** — `analysis/phase_g/`. Phase G was
  preregistered and never completed; it produced **no** production result and
  supports **no** claim in any manuscript. See `analysis/phase_g/README.md`.
- **Historical, superseded** — `paper/`, `README_REVISION_V2.md` and the other
  `V2_*` / `TARGET_INFERENCE_*` / `JUDGE_FALLBACK_*` notes at the repository
  root. Retained as a development record, not as current claims.

## Reproducing the analysis

Every analysis entry point reads committed artifacts only and makes zero API
calls. Paid execution is separately gated and is never invoked by these
commands.

```powershell
.analysis-venv\Scripts\python.exe scripts\create_freeze_snapshot.py   # once
.analysis-venv\Scripts\python.exe analysis\qc_final.py                # Phase A gate
.analysis-venv\Scripts\python.exe analysis\analyze_final.py           # Phase B headline
```

`analysis/README.md` documents the full Phase A–D and sensitivity pipeline,
including the judge-independent length analysis and the cross-judge
replication.

## The submission tag

`globalsouthai-2026-submission` marks the exact tree from which the
GlobalSouthAI @ NeurIPS 2026 workshop paper was built. It is frozen: do not
retarget it, and do not alter the artifacts it references. Sources for that
manuscript live in `paper_globalsouthai_2026/`.

## Layout

See `docs/REPOSITORY_STRUCTURE.md`.

## License

MIT — see `LICENSE`. The license covers the code in this repository. It does
not grant access to the gated prompt bank, target responses, or annotation
workbooks, which are released separately on request.
