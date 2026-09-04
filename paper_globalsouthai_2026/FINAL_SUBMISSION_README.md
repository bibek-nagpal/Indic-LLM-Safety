# Submit this

## The file

**Upload:** `C:\Prahlada\paper_globalsouthai_2026\main.pdf`

| Property | Value |
|---|---|
| Main content pages | **4** (references begin at the top of page 5) |
| Total PDF pages | **8** |
| References pages | 5–6 |
| Appendix pages | 6–8 (same PDF; no separate supplement) |
| Do references count toward the limit? | **No** — workshop FAQ: "up to 4 pages, excluding references and appendices" |
| Anonymity | **Anonymized.** Author block is the template's anonymous block; PDF metadata carries no author; no acknowledgments; no identifying strings found in the text |
| Template | NeurIPS 2026 (`neurips_2026.sty`, 2026-01-29) with the `dblblindworkshop` option |

## Where and when

- **Submission URL:** https://openreview.net/group?id=NeurIPS.cc%2F2026%2FWorkshop%2FGlobalSouthAI
- **Deadline:** 5 September 2026 **AoE** per the workshop site. A third-party tracker lists
  5 September 11:59 **UTC**. These differ by ~24 h. **Submit by 5 September 11:59 UTC** to be
  safe under either reading.
- Track: one unified track; this is the **short paper (≤4 pages)** format, not the 1-page abstract.
- Non-archival, so a concurrent submission elsewhere is permitted subject to that venue's rules.

## Manual actions required from you

1. **Open the OpenReview form and check its fields before pasting.** I could not reach
   OpenReview's API from this environment. In particular check whether the abstract field has
   a character limit (the paper's abstract is ~1,500 characters), and whether TL;DR, keywords
   or a subject-area selection are required.
2. **Enter title and abstract** into the form (copy from `main.tex`; do not re-type).
3. **Declare prior GlobalSouthAI/GlobalSouthML activity** if any co-author has had work
   accepted at GlobalSouthAI @ AAAI 2026, GlobalSouthML @ ICML 2026 or GlobalSouthAI @
   IJCAI-ECAI 2026 — the workshop asks for this at submission.
4. **Reviewer nomination:** authors with prior accepted papers may be asked to nominate an
   eligible co-author as a reviewer (form linked from the workshop's Submission page).
5. **Check whether the form asks for an ethics or LLM-use statement.** The workshop site does
   not require either; if the form does, the Method section already names every model used.
6. **Decide the artifact-release position.** The appendix says the bank would be released only
   under gated access. If you want to commit to a release, add the link at camera-ready — not now
   (it would break anonymity).
7. **Confirm the author list and affiliations** for the camera-ready version only.

## What I did not and could not do

- No paid or API calls were made. Every number comes from the frozen local artifacts.
- Phase G / the unusual-English control is **excluded entirely** — it is incomplete, and the
  paper explicitly states that the control was specified but not completed.
- The existing manuscript in `paper/` was not touched.

## Rebuilding

```
cd paper_globalsouthai_2026
python analysis/verify_headline.py        # recompute headline stats from frozen data
python analysis/human_a_validation.py     # recompute the human validation
python analysis/build_tables.py           # regenerate tables/*.tex from those JSONs
python analysis/build_figure.py           # regenerate figures/gap_by_model.pdf
pdflatex main && bibtex main && pdflatex main && pdflatex main
python analysis/numerical_audit.py        # verify every number in the PDF
```
