# Revised GlobalSouthAI submission candidate

Upload candidate: `C:\Prahlada\paper_globalsouthai_2026\main.pdf`.
This surgical pass starts from `24ae35fa0302ebef7d2d9ab5feec5045469dbe53`; the earlier independent-audit baseline `8eca4be99f7d1af62a48980690069c3bcb3bd1c0` remains preserved. See REVISION_LOG.md for the correction ledger.

| Property | Verified result |
|---|---|
| Main scientific paper | 4 pages |
| References | Begin page 5; extend into page 6 |
| Appendix | Pages 6–8, same PDF |
| Official checklist | All 16 items and guidelines, pages 9–15 |
| Total PDF | 15 pages |
| Format | Official NeurIPS 2026 style, dblblindworkshop, GlobalSouthAI workshop title parameter |
| Anonymity | Anonymous placeholder author block; empty author metadata; no identifying paths or repository links |
| Numerical checks | PASS; automated bootstrap outputs reused, completed human audit recomputed at its fixed seed |
| Frozen experimental data | Unchanged |
| Human audit | Completed workbook verified by hash; 354 analyzed items / 174 complete jobs |

The official checklist and excluded supplemental material explain the larger total page count; this is not a 16-page main paper.
Every page was rendered and visually inspected using the PDF workflow.
No margin, spacing, font-size or line-count override was used.

## Before upload

1. Confirm the documented human-audit classification: one unpaid co-author performed the rating as part of the research team after a sensitive-content warning; no external participants, crowdworkers or contractors were recruited. The checklist therefore marks the participant-specific Questions 14 and 15 as not applicable. This is not a formal institutional exemption determination.
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
The completed-workbook human analysis is deterministic apart from its fixed-seed job-cluster bootstrap. `human_a_results.json` records the authoritative workbook hash and verified result.
Only point estimates are recomputed by verify_headline.py; its intervals come from validated analysis/results/main_results.csv.
