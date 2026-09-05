# Final submission edit — 2026-09-05

This final pass preserves the scientific record below while replacing audit-like and defensive prose with direct claims, methods and limitations. It also checks the workshop manuscript against the current official GlobalSouthAI submission rules, NeurIPS 2026 style, Code of Ethics and Paper Checklist. The sole human audit is classified narrowly as work performed by an unpaid co-author within the research team: no external participants, crowdworkers or contractors were recruited, so checklist Questions 14--15 are marked not applicable. This classification is not a formal institutional exemption determination. No experiment, model call or frozen artifact changed.

Surgical follow-up from `24ae35fa0302ebef7d2d9ab5feec5045469dbe53`: the latest Human A workbook still contains three blank score cells (items 314, 319 and 320), so the completed human statistics remain unchanged. Table 1 now identifies the main interval as a pair-level percentile bootstrap, distinct from the near-duplicate cluster-bootstrap sensitivity analysis. Remaining unsupported or internal-process wording was removed. Checklist Question 12 remains No after partial license verification because the routed API-service and full software-asset terms are not comprehensively documented.

## Accepted independent-audit correction pass — 2026-09-04

Baseline candidate: `8eca4be99f7d1af62a48980690069c3bcb3bd1c0`, retained in Git history.
Follow-up: HUMAN_A_CLARIFICATION.md records the completed co-author audit, current denominators and author-reported participant facts. The correction-pass account below is historical; current reporting supersedes its earlier partial-workbook human numbers without changing the frozen experiment.
This pass changes only the separate GlobalSouthAI manuscript and workshop supporting files.
It supersedes the baseline's correction claims; it does not change experimental data.

## Disposition: 4/4 blocking, 5/5 major, 8/8 moderate reporting corrections, 2/2 minor

| ID | Evidence and implemented correction | Status |
|---|---|---|
| B1 | Persisted GEPA state retains one seed instruction, no accepted revision; 30 development evaluations / 24 accepts. Main §2 and Appendix A now describe this rather than claiming evolved guidance. Deterministic checks → DeepSeek → GPT-5 Mini cascade clarified. | Fixed |
| B2 | Exact frozen response inspection: all 272 short Nemotron RH zeros are explicit refusals; original ASCII regex misses curly apostrophes. §3 and Appendix C remove degeneration/comprehension interpretations. Regex values remain historical diagnostics, not semantic truth. | Fixed |
| B3 | Both judges order Qwen > GPT-OSS > Nemotron; shared-subset smaller contrast is +4.3 versus +11.7 pp, not reversed. §3–4 corrected. | Fixed |
| B4 | Official linked 2026 checklist explicitly requires inclusion, with no verified workshop waiver. All 16 questions, answers, justifications and guidelines now follow the appendix. | Fixed |
| M1 | Shared pipeline dependencies can have model-dependent effects. The bank controls target-specific prompt selection, not all measurement bias. | Fixed |
| M2 | Primary-source author repairs: Shanu Kumar, Parag Agrawal; Darpan Aswal, Siddharth D Jaiswal; Meng Lingyu added. | Fixed |
| M3 | Human results are exploratory single-co-author corroboration, not population confirmation or human ground truth. English scores 0–1 are not called refusal/near-refusal. | Fixed |
| M4 | Both EN and RH inputs use Latin script; language/lexical/syntactic realization varies, training frequency is unmeasured. No isolated script or register mechanism claimed. | Fixed |
| M5 | Removed unsupported population/default-input/first-of-kind claims. Explicitly positioned against CSRT, IndicJR, RomanSetu and Indi-RomCoM. Narrowed citation attachments and predictability claim. | Fixed |
| C1 | Validated GPT-OSS gap CI [1.4, 7.7], Nemotron [−6.5, 2.8]. Human comparisons were recomputed from the completed workbook with the frozen job-cluster method and seed. | Fixed |
| C2 | Prompt-length result is Spearman association, not conditioning/causal adjustment; mean paired ratio 1.114, correct rho/p bounds. | Fixed |
| C3 | Completed-workbook flow is explicit: 357 valid labels, three blank labels, three frozen-stimulus verification exclusions, 354 analyzed items and 174 complete jobs. | Fixed |
| C5 | Judges received prompt text and explicit en/rh labels; disclosed as unblinded. | Fixed |
| C6 | SequenceMatcher within-source-bank gate distinguished from exact-only cross-bank consolidation and separate token-Jaccard sensitivity. Five pairwise relationships, not five demonstrated gate violations. | Fixed |
| C7 | Exact model IDs, token limits, seeds, separate 5,000-resample human analysis and provider-resource limits disclosed. The co-author's voluntary, unpaid annotation role and safeguards are reported exactly; no recruited participants are implied and external artifact access is not invented. | Reporting fixed; external access remains unresolved |
| C8 | Official style restored; dblblindworkshop and required workshoptitle{GlobalSouthAI} set, no format overrides. Draft notice follows official behavior. | Fixed |
| P1 | Figure 1 now displays a literal percent sign, not a backslash. | Fixed |
| P2 | Relevant arXiv entries render identifiers, versions and URLs under plainnat. | Fixed |

Also removed the unprespecified cell sign-test attachment (retained descriptive 12/12 positive cells), clarified Bowker's hypothesis, and corrected fallback rounding wording.

## Validation performed

- 82/82 artifact hashes across six frozen manifests: PASS.
- Final-bank/run QC: 28/28 checks, read-only.
- Generator artifact verifier: 17/17 checks.
- Selected Phase D agreement/regime unit tests: 4 passed, 3 deselected.
- Workshop revision gate: 35/35 checks for the final completed-workbook candidate.
- PDF numerical/claim regression checks: 35/35, with no stale claims and all required disclosures present.
- Completed private workbook verified by SHA-256; workshop human result JSON regenerated with the fixed analysis seed.
- Clean isolated LaTeX → BibTeX → LaTeX → LaTeX build: no unresolved citations/references, overfull boxes or missing characters.
- All 15 pages visually inspected; main text 1–4, references 5–6, appendix 6–8, checklist 9–15.
- No inference/API calls, no new experiment and no Phase G continuation. Published automated bootstrap outputs were not redrawn; only the completed human audit was recomputed with its fixed seed.
- Public template and local compiler packages were downloaded; no research data were transmitted.

## Remaining author decisions

The PDF is a revised candidate, not a formal institutional ethics determination.
Authors must confirm the documented co-author classification and review the asset-license inventory before making submission declarations.
The checklist records that the audit was author-produced research work, not crowdsourcing or recruited human-subject participation. External reproducibility still requires an authorized anonymous artifact-access arrangement; none is represented as already established.
