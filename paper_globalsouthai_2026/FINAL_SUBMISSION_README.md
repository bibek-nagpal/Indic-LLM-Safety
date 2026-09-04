# Revised GlobalSouthAI submission candidate

Upload candidate: `C:\Prahlada\paper_globalsouthai_2026\main.pdf`.
Baseline `8eca4be99f7d1af62a48980690069c3bcb3bd1c0` is preserved; see REVISION_LOG.md for the correction ledger.

| Property | Verified result |
|---|---|
| Main scientific paper | 4 pages |
| References | Begin page 5; extend into page 6 |
| Appendix | Pages 6–9, same PDF |
| Official checklist | All 16 items and guidelines, pages 10–16 |
| Total PDF | 16 pages |
| Format | Official NeurIPS 2026 style, dblblindworkshop, GlobalSouthAI workshop title parameter |
| Anonymity | Anonymous placeholder author block; empty author metadata; no identifying paths or repository links |
| Numerical checks | PASS; validated bootstrap outputs reused, not redrawn |
| Frozen data / Human A | Unchanged |

The official checklist and excluded supplemental material explain the larger total page count; this is not a 16-page main paper.
Every page was rendered and visually inspected using the PDF workflow.
No margin, spacing, font-size or line-count override was used.

## Before upload

1. Resolve/verify participant consent, compensation and institutional ethics-review facts. The records do not establish them; the checklist deliberately does not claim compliance or an exemption.
2. Review the disclosed license inventory and artifact-access limitations. No anonymous public release or gated service has been promised as already available.
3. Enter title, abstract, required keywords and author profiles in the OpenReview form; check the current form before final submission. PDF remains anonymous.
4. Confirm prior GlobalSouthAI/GlobalSouthML activity and nominate an eligible reviewer if the venue's conditional rule applies.
5. Confirm submission consent and CC BY 4.0 terms as authors. No submission, upload or license acceptance was performed by this revision.

Submission: https://openreview.net/group?id=NeurIPS.cc/2026/Workshop/GlobalSouthAI

The accepted independent audit recorded a nominal September 5 AoE deadline and OpenReview due time September 6, 2026, 11:58 UTC (17:28 IST), one minute earlier than the site's AoE conversion. Submit early; do not treat the later server expiry as an extension. No OpenReview API was queried during this revision.

## Local verification and rebuild

From repository root with the existing local Python environment:

```
python paper_globalsouthai_2026/analysis/verify_headline.py
python paper_globalsouthai_2026/analysis/build_tables.py
python paper_globalsouthai_2026/analysis/build_figure.py
python paper_globalsouthai_2026/analysis/build_submission.py
python paper_globalsouthai_2026/analysis/numerical_audit.py
python paper_globalsouthai_2026/analysis/verify_revision.py
```

Requirements: Python; matplotlib for the figure; pypdf for the revision gate; pdflatex, bibtex and pdftotext for the build/text checks.
On this Windows host the compiler is in Ubuntu WSL; use:

```
wsl -d Ubuntu --exec python3 /mnt/c/Prahlada/paper_globalsouthai_2026/analysis/build_submission.py
wsl -d Ubuntu --exec python3 /mnt/c/Prahlada/paper_globalsouthai_2026/analysis/numerical_audit.py
```

Use the bundled Windows Python for verify_revision.py (pypdf is installed there).
Set MPLCONFIGDIR to the repository's ignored .matplotlib-cache if needed.
The builder stages only source/tables/figures into a fresh ignored directory, runs all four compilation passes, rejects unresolved references or overflow, and copies the resulting PDF to main.pdf.
The existing human_a_validation.py is preserved for provenance; do **not** rerun it merely to redraw published bootstrap intervals. human_a_results.json is the verified baseline result.
Only point estimates are recomputed by verify_headline.py; its intervals come from validated analysis/results/main_results.csv.
