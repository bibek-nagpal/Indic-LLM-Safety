# GlobalSouthAI @ NeurIPS 2026 — authoritative submission rules

Retrieved 2026-09-04 by independent web verification. Every rule below carries its source.
**Do not rely on this file alone for the OpenReview form fields** — see OPEN ITEMS.

## Venue identity

| Item | Answer | Source |
|---|---|---|
| Name | GlobalSouthAI @ NeurIPS 2026 — "Rethinking AI for and from the Global South" | https://sites.google.com/view/globalsouthai-neurips26/home |
| Status | Branded on its own site as a **NeurIPS 2026 Affinity Event**; OpenReview venue id is `NeurIPS.cc/2026/Workshop/GlobalSouthAI` | site home; OpenReview |
| Archival | **Non-archival** | .../faq |
| Location / date | Sydney, Australia and Paris, France; December 2026 | site home |

## Hard submission rules

| Rule | Answer | Source |
|---|---|---|
| **Deadline** | **5 September 2026, AoE** | https://sites.google.com/view/globalsouthai-neurips26/dates |
| Notification | 20 September 2026 (AoE) | .../dates |
| Formats | One unified track; either a 1-page abstract **or** a short paper of **up to 4 pages** | .../faq, .../submission |
| **Page limit** | **4 pages of main content, excluding references and appendices** | .../faq ("up to 4 pages, excluding references and appendices") |
| Template | **NeurIPS 2026 official template** (`neurips_2026.sty`, dated 2026-01-29) | site home → https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip |
| Anonymity | **Double-blind; anonymize submissions** | .../submission |
| File format | PDF, via OpenReview | .../submission |
| Submission URL | https://openreview.net/group?id=NeurIPS.cc%2F2026%2FWorkshop%2FGlobalSouthAI | site home |
| Dual submission | Permitted (non-archival), subject to the other venue's policy | .../faq |
| Presentation | All accepted → poster; selected → contributed talk; subset → 3-minute thesis | .../awards |

## Style-file option

`neurips_2026.sty` declares `dblblindworkshop` (double-blind workshop review) alongside
`main`, `preprint`, `final`, `sglblindworkshop` and others. The workshop states a
double-blind policy but does **not** name the option. We use
`\usepackage[dblblindworkshop]{neurips_2026}`, which produces the anonymous author block and
submission line numbers. This is a reasoned inference, not a quoted rule.

## DISCREPANCIES (flagged, not silently resolved)

1. **Affinity Event vs Workshop.** The workshop's own site says "Affinity Event"; the
   OpenReview namespace says `Workshop`; it does not appear in the official list of NeurIPS
   2026 workshops. **Safest interpretation:** follow the workshop site (most authoritative
   about itself). No effect on manuscript preparation, but do not describe the paper as
   appearing at an "official NeurIPS 2026 workshop".
2. **Deadline timezone.** Workshop site: "September 5, 2026 (AoE)" = 6 Sept 11:59 UTC.
   A third-party aggregator (aiworkshoptracker.com) normalizes this to 5 Sept 11:59 UTC.
   **Safest interpretation:** treat **5 September 2026, 11:59 UTC** as the operative
   deadline. Submitting early costs nothing; being wrong costs the submission.

## OPEN ITEMS — could not be verified, require human action

| Item | Status |
|---|---|
| OpenReview form fields (abstract length cap, TL;DR, keywords, subject area) | **NOT VERIFIED.** OpenReview is JS-rendered and its API is blocked from this environment. **You must open the submission form and check.** |
| Ethics / responsible-research statement required? | **NOT STATED** anywhere on the workshop site. |
| AI/LLM-use disclosure required? | **NOT STATED** at workshop level. NeurIPS main-track policy asks that agent/LLM use be described in the experimental setup if it is an important or non-standard component; our Method already names every model used, which satisfies that standard if applied. |
| NeurIPS paper checklist required? | **NOT MENTIONED** by the workshop. `checklist.tex` ships in the template but the workshop never requires it. Given a 4-page limit it is almost certainly not expected. |
| Separate supplementary upload permitted / size limits | **NOT STATED.** Appendices are described only as excluded from the page count, implying same-PDF. We put the appendix in the same PDF. |
| Camera-ready deadline; attendance/registration requirement | **NOT STATED.** |

## Compliance of this submission

- 4 pages of main content; references begin on page 5; appendix follows. **Compliant.**
- `neurips_2026.sty` with `dblblindworkshop`; anonymous author block; line numbers present.
- Appendix in the same PDF; no separate supplement.
- No acknowledgments section (correct for anonymous submission per the template).
