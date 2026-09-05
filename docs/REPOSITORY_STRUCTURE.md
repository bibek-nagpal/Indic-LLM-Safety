# Repository structure and evidence boundaries

This document exists so that a reader can tell, without opening a directory,
what weight its contents carry. Three categories are used throughout:

- **Evidence** — load-bearing. A manuscript claim depends on it, its hashes are
  recorded in a manifest, and it must not be regenerated casually.
- **Tooling** — code, configuration and tests that produce or check evidence.
- **Non-evidentiary** — development records, superseded drafts, and incomplete
  work. Nothing here supports a claim.

---

## Top level

| Path | Category | What it is |
|---|---|---|
| `README.md` | — | Repository overview and headline result. |
| `CITATION.cff` | — | Citation metadata. Author names are withheld pending de-anonymisation. |
| `LICENSE` | — | MIT, covering the code in this repository. |
| `pyproject.toml`, `uv.lock` | Tooling | The `jailbreak-hermes` package (`jbh` CLI) and its pinned environment. |
| `.gitattributes` | Tooling | Byte-level line-ending pins. Several Phase G artifacts are hashed as raw bytes, so their EOLs are fixed here; do not relax these. |
| `.gitignore` | Tooling | The gated-release boundary. See "What is deliberately not tracked". |
| `.env.example` | Tooling | Template only. Real credentials never enter the repository. |
| `IndicAlignProbe_ResearchPaper.pdf`, `rebuttal.pdf` | Non-evidentiary | Historical V1 artifacts. |
| `README_REVISION_V2.md`, `V2_*.md`, `TARGET_INFERENCE_V2_4.md`, `JUDGE_FALLBACK_V2_4_1.md`, `PROJECT_HANDOFF_AND_PLAN.md` | Non-evidentiary | Development log for the V2 revision. Superseded by `docs/` and the manuscripts. |

## Evidence

| Path | What it holds |
|---|---|
| `frozen_final_2026_08_29/` | The immutable snapshot boundary: `FREEZE_MANIFEST.json` (bank id `revision_v2_3_1_final_504_dedup`, canonical bank SHA-256 `35bfbc1d…c2028ed`) and `CODE_VERSION.json`. The `bank/` and `run/` payloads are intentionally untracked. |
| `analysis/results/` | Phase B headline. `main_results.csv` is the source of truth for every EN/RH rate, gap and confidence interval quoted anywhere. |
| `analysis/phase_c_results/` | Judge-independent response-length analysis. Reads stored responses only. |
| `analysis/phase_d_results/`, `analysis/phase_d_run_archive/` | Cross-judge replication: 1,944 completed GPT-5 Mini judgments over 324 shared pair IDs × 3 models × 2 languages, with the immutable score/provenance/accounting archive. |
| `analysis/sensitivity_results/` | Post-audit robustness: near-duplicate clustering, truncation, prompt-length null, non-assistance length profile, per-cell agreement. |
| `analysis/phase_d_budget_design/`, `analysis/phase_d_preparation/` | Hash-locked job plans. Identifiers, hashes, lengths and cost metadata only — no prompt or response text. |
| `human_validation/` | Human validation of the automated judge: protocol, annotator instructions, `HUMAN_VALIDATION_MANIFEST.json`, and de-identified label analysis. Workbooks themselves are gated. |
| `accounting/` | Per-call API accounting ledgers (`api_calls_*.jsonl`) for every paid call the project ever made. |
| `prompts/optimized/gepa_20260826_135819/` | The single tracked generator-guidance artifact. Its `generator.txt` SHA-256 is the one recorded in the frozen bank manifest; `scripts/verify_generator_artifact.py` proves it was retained unchanged. The `_superseded_v1_*` sibling is historical. |

## Tooling

| Path | What it holds |
|---|---|
| `src/jailbreak_hermes/` | The harness: generator, equivalence certification, judge, flip detection, evidence gate, injection scan, CLI. |
| `configs/` | Category specifications (`violence`, `sexual_violence`, `intoxication`, `gambling`), model roster, run configuration. |
| `analysis/*.py` | Phase A–D analysis entry points. None makes an API call. `analysis/README.md` documents them. |
| `scripts/` | Snapshot creation, cross-judge runners, generator-artifact verification, shell drivers. |
| `tests/` | Offline test suite (`pytest`), including Phase C/D/G regression fixtures. |
| `docs/` | Status memos, executive summary, reviewer action matrix, artifact field notes, and this file. |
| `seeds/` | Empty by design. Optional manually-validated seed pairs are maintained in a separate access-controlled corpus. |
| `runs/`, `memory/`, `probe_banks/`, `output/` | Placeholder roots whose contents are runtime artifacts or gated material. |

## Non-evidentiary

| Path | Why |
|---|---|
| `analysis/phase_g/` | **Incomplete.** Preregistered, partially executed at sanity scale, never completed. Produced no production result and supports no claim. See `analysis/phase_g/README.md`. |
| `paper/` | The historical V1/ACL manuscript and its figures. Superseded. |
| `reviews/claude_independent_audit/` | An adversarial internal audit and its proposed patches. A record of scrutiny, not a source of results; the accepted corrections are already reflected in the evidence directories. |

## Manuscripts

| Path | What it is |
|---|---|
| `paper_globalsouthai_2026/` | The GlobalSouthAI @ NeurIPS 2026 workshop paper (4 main pages) and its full audit trail: claim–evidence ledger, numerical audit, citation audit, reviewer risk audit, revision log, submission rules and final checklist. Built from the tree tagged `globalsouthai-2026-submission`. |

The tag `globalsouthai-2026-submission` is frozen. Do not retarget it, and do
not modify the artifacts it references.

## What is deliberately not tracked

`.gitignore` is a release-policy document, not just build hygiene. The
following contain full research prompts, target responses, or credentials, and
are excluded on purpose:

- `probe_banks/*` — the certified prompt banks.
- `frozen_final_*/bank/`, `frozen_final_*/run/` — the frozen bank and run
  payloads. Their SHA-256 hashes remain tracked in `FREEZE_MANIFEST.json`, so
  the snapshot stays auditable without publishing the text.
- `human_validation/outputs/**/*.xlsx`, `/Human_*_annotations.xlsx` — annotation
  workbooks. Hashes are in `HUMAN_VALIDATION_MANIFEST.json`; de-identified
  identifier/score CSVs stay tracked.
- `historical_v1_evidence/` — read-only V1 source material that includes live
  credential files. Never commit this tree.
- `analysis/phase_g/u_arch_v3_private/` — Phase G construction journals with
  private source, U and audit text.
- `.env` and every credential pattern.

Because the hashes are tracked and the text is not, an outside reader can
verify that an artifact is the one that was analysed without being handed the
harmful material itself. Preserve that property in any future change.
