# Final submission checklist

Verified programmatically against the compiled `main.pdf` on a clean rebuild.

## Hard requirements

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Main content ≤ 4 pages | **PASS** | Main text ends on p4; `References` heading is the first content on p5 (`pdftotext -f 5`) |
| 2 | References excluded from limit | **PASS (per rules)** | Workshop FAQ: "up to 4 pages, excluding references and appendices" |
| 3 | Appendix excluded from limit | **PASS (per rules)** | same source; appendix is in the same PDF, after references |
| 4 | NeurIPS 2026 template | **PASS** | `neurips_2026.sty` (ProvidesPackage 2026-01-29), option `dblblindworkshop` |
| 5 | Double-blind / anonymized | **PASS** | Author block reads "Anonymous Author(s) / Affiliation / Address / email"; no acknowledgments section |
| 6 | No identifying strings anywhere in PDF | **PASS** | grep for author name, institution, repo host, emails, local paths → 0 hits |
| 7 | PDF metadata carries no author | **PASS** | `pdfinfo`: Author, Title, Subject, Keywords all empty |
| 8 | Submission line numbers present | **PASS** | 32 line numbers on p1 (submission mode, `final`/`preprint` omitted) |
| 9 | Compiles clean from scratch | **PASS** | 0 errors, 0 undefined refs, 0 overfull boxes on clean rebuild |
| 10 | No `[?]` citations | **PASS** | 0 occurrences |
| 11 | No TODO/FIXME/placeholders | **PASS** | 0 occurrences |
| 12 | All fonts embedded | **PASS** | `pdffonts`: every font `emb = yes` |
| 13 | Every bib entry cited; every citation resolves | **PASS** | 17 entries, 17 cited, 0 uncited, 0 unresolved |
| 14 | Every citation verified to exist | **PASS** | `CITATION_AUDIT.md` — all 17 verified against primary sources |
| 15 | All headline numbers reproduce from frozen data | **PASS** | `NUMERICAL_AUDIT.md` — 26/26 checks pass |
| 16 | No forbidden claim (two-human, consensus, ground truth, Phase G) | **PASS** | automated phrase sweep in `NUMERICAL_AUDIT.md`, negation-aware |
| 17 | Required disclosures present | **PASS** | single annotator, annotator B returned nothing, cascade, GEPA optimization, generator = judge, control not completed, no direct-request condition |
| 18 | Frozen artifacts unmodified | **PASS** | `git status` clean for `frozen_final_2026_08_29/`, `analysis/results/`, `human_validation/`, `paper/` |
| 19 | No paid/API calls made | **PASS** | all analysis reads local frozen files; no network call issued |
| 20 | Tables/figures derived programmatically | **PASS** | `analysis/build_tables.py`, `analysis/build_figure.py` read the verified JSON; no hand-typed numbers |

## Visual inspection (all 8 pages)

- p1 title, anonymous block, abstract, §1 — no overlap, figure-free, legible.
- p2 §1 end, §2 Method — no overflow.
- p3 Table 1 + Figure 1 + §3 — table and figure legible at 100%; figure labels ≥ 8.5 pt.
- p4 Table 2 + §4 + §5 — ends mid-page; main content complete.
- p5–6 References.
- p6–8 Appendix A/B/C incl. Table 3.
- No clipped text, no overlapping objects, no colored debug boxes, no broken equations,
  no missing glyphs (0 missing-character warnings in the log).

## Not verifiable from here — requires the submitter

- OpenReview form fields (abstract character cap, TL;DR, keywords, subject area).
- Whether the workshop wants any ethics / LLM-use declaration on the form.
