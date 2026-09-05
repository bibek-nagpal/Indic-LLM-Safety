# Phase G — INCOMPLETE AND NON-EVIDENTIARY

**Phase G did not produce a production result. Nothing in this directory
supports any claim in any manuscript, and nothing here may be cited as a
finding.**

Read this before opening anything else in `analysis/phase_g/`. The directory
is large, densely instrumented and full of JSON that looks like results. It is
not results. It is the record of a control experiment that was designed, cost
modelled, preregistered, and then halted during its compatibility sanity check.

## What Phase G was for

The frozen V2 result is that Qwen3-30B-A3B withholds domain-specific harmful
content on 65.87% of English prompts but only 22.82% of matched
Romanized-Hindi prompts — a 43.06 pp non-assistance gap. Equivalence
certification controls *what* is asked. It does not control *how far the
surface form sits from the model's training distribution*.

That leaves two live explanations the frozen design cannot separate:

1. **Register-specific** — safety degrades because the request is in
   code-switched Romanized Hindi.
2. **Generic out-of-distribution** — safety degrades under *any* sufficiently
   unusual surface form, and Hinglish merely happens to be one.

Phase G proposed a third arm, `U`: an unusual-English control that is far from
the training distribution in surface form while remaining English and holding
semantic content fixed. Comparing EN / RH / U would have distinguished the
explanations.

**It never ran. The distinction remains unresolved, and the manuscripts state
it as an open limitation rather than settling it.**

## How far it actually got

| Stage | Outcome |
|---|---|
| Design, power and cost model | Complete. `design_power.py`, `cost_model.py`, `COST_MODEL.md`. |
| Preregistration | Complete and frozen *before* any U data existed. `PREREGISTRATION.md`, `STATISTICAL_ANALYSIS_PLAN.md`. |
| Development cohort (24 pairs, disjoint from any evaluated set) | Complete. 120 U candidates generated offline. `u_control_development/`. |
| Frozen selection manifests (n=72 / n=96 / n=120) | Complete. |
| Stage 1 preflight | PASS. `u_arch_v3_preflight/`, `u_arch_v3_budget550/`. |
| Compatibility sanity check (N=12 pairs) | **Halted.** `u_arch_v3_sanity_compat/SANITY_RESULT.json`. |
| Production run | **Never dispatched.** |
| Phase G outcome, statistic, table or figure | **Does not exist.** |

### What the halted sanity check recorded

From `u_arch_v3_sanity_compat/SANITY_RESULT.json`:

- `sanity_result`: `INCOMPLETE DUE TO EXECUTION OR BUDGET FAILURE`
- `readiness_verdict`: `GENERATION SPECIFICATION NOT READY`
- `stop_reason`: `auditor exhausted format/known-unbilled repair allowance`
- `pairs_dual_certified`: **2 of 12**; `unresolved_pairs`: 10
- `first_attempt_pass_rate`: 0.167
- `total_reported_cost_usd`: 0.0279
- `later_stage_calls`: 0 — **no target model was ever called in Phase G**
- `protocol_violations`: none; `provenance_complete`: true;
  `sanity_cap_respected`: true

Two dual-certified U items out of twelve is a specification that is not ready,
not a result. The generation specification would need revision and a fresh
sanity check before any production run could be authorised.

## What the JSON in here is, then

It is **process evidence**: preregistration, cost models, hash-locked execution
plans, provider metadata, journal scope records, stop reports, and superseded
snapshots kept so that each halt is auditable. Directories named
`superseded_*` are prior attempts retained deliberately — a
line-ending verifier bug, a GPT-5 Mini completion-budget truncation, and an
amendment-versioning change — none of which produced results either.

`u_arch_v3_private/` is untracked by design: it holds private source, U and
auditor text.

## Rules for anyone working here

- Do not report any number from this directory as a finding.
- Do not describe Phase G as "run", "attempted at scale", or "inconclusive
  evidence for" anything. It was halted before it could produce evidence.
- Do not treat the 2/12 sanity outcome as an observed rate for the population;
  `counts_are_not_observed_failure_rates` is recorded in the stop reports for
  exactly this reason.
- Do not retroactively edit the preregistration. It is dated and frozen
  precisely so that thresholds cannot be chosen to suit a result.
- Several files here are hashed as raw bytes. `.gitattributes` pins their line
  endings; do not relax those rules.
- Any resumption requires a fresh preregistered amendment, explicit written
  approval, and both runner flags `--execute-paid-calls
  --paid-approval-confirmed`.
