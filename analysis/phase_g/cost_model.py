"""Phase G cost model for N = 72, 96, 120.

Every per-call figure for generation, certification and judging is *measured*
from this repository's own billing ledgers, not from list prices:

  accounting/*.jsonl            V2 bank construction (generation + certification)
  runs/cross_judge/.../standard_accounting.jsonl   Phase D response judging

Target-model unit prices are the only list-price inputs, because the target
sweep's per-call usage was never persisted. They are taken from the official
OpenRouter model pages and are flagged in the output.

Makes no API call. Writes analysis/phase_g/COST_MODEL.md and cost_model.json.
"""

from __future__ import annotations

import collections
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/phase_g"

# ---------------------------------------------------------------- measured

def measure_ledgers() -> dict:
    rows = []
    for path in sorted(glob.glob(str(ROOT / "accounting" / "*.jsonl"))):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    agg = collections.defaultdict(lambda: dict(n=0, pt=0, ct=0, cost=0.0))
    for r in rows:
        a = agg[(r.get("purpose"), r.get("resolved_model"))]
        a["n"] += 1
        a["pt"] += r.get("prompt_tokens") or 0
        a["ct"] += r.get("completion_tokens") or 0
        a["cost"] += r.get("cost_usd") or 0.0

    judge_path = ROOT / "runs/cross_judge/gpt5mini_standard_budget/standard_accounting.jsonl"
    judge = dict(n=0, pt=0, ct=0, cost=0.0)
    if judge_path.exists():
        with judge_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    r = json.loads(line)
                    judge["n"] += 1
                    judge["pt"] += r.get("prompt_tokens") or 0
                    judge["ct"] += r.get("completion_tokens") or 0
                    judge["cost"] += r.get("cost_usd") or 0.0

    def per_call(a):
        return dict(
            calls=a["n"],
            in_per_call=a["pt"] / a["n"],
            out_per_call=a["ct"] / a["n"],
            usd_per_call=a["cost"] / a["n"],
            total_usd=a["cost"],
        )

    gen = per_call(agg[("prompt_generation", "google/gemini-2.5-flash")])
    ds = per_call(agg[("equivalence_audit", "deepseek/deepseek-v4-flash")])
    gm = per_call(agg[("equivalence_audit", "openai/gpt-5-mini")])
    jm = per_call(judge)

    accepted = 504
    funnel = {
        "accepted_pairs": accepted,
        "generation_calls_per_accepted_pair": gen["calls"] / accepted,
        "primary_audits_per_accepted_pair": ds["calls"] / accepted,
        "secondary_audits_per_accepted_pair": gm["calls"] / accepted,
        "primary_pass_rate": gm["calls"] / ds["calls"],
        "secondary_pass_rate": accepted / gm["calls"],
        "overall_acceptance_rate": accepted / ds["calls"],
    }
    return {"generation": gen, "primary_audit": ds, "secondary_audit": gm,
            "response_judging_gpt5mini": jm, "v2_bank_funnel": funnel}


# ------------------------------------------------------- list-price inputs
# Official OpenRouter model pages, retrieved 2026-08-31.
TARGETS = {
    "qwen/qwen3-30b-a3b-instruct-2507": {
        "in_usd_per_m": 0.04815, "out_usd_per_m": 0.1931,
        "mean_out_tokens": 690, "price_source": "openrouter.ai model page (verified)",
    },
    "nvidia/nemotron-3-nano-30b-a3b": {
        "in_usd_per_m": 0.05, "out_usd_per_m": 0.20,
        "mean_out_tokens": 1329, "price_source": "openrouter.ai model page (verified)",
    },
    "openai/gpt-oss-20b": {
        "in_usd_per_m": 0.10, "out_usd_per_m": 0.50,
        "mean_out_tokens": 488,
        "price_source": "UNVERIFIED: page not retrievable; deliberately conservative "
                        "upper bound, ~2x the two verified targets",
    },
}
U_PROMPT_TOKENS = 107          # E arm measured at ~89; +20% headroom for U expansion
JUDGE_MAX_OUT = 2048           # max_judge_tokens from the frozen run manifest

# Funnel scenarios. "expected" assumes an English-to-English rewrite certifies
# more easily than de-novo EN/RH pair construction; "conservative" simply
# reuses the measured V2 bank-build funnel unchanged.
SCENARIOS = {
    "expected": {"gen_per_accepted": 2.2, "primary_pass": 0.60, "secondary_pass": 0.60},
    "conservative": {"gen_per_accepted": 4.38, "primary_pass": 0.534, "secondary_pass": 0.423},
}
RETRY_FACTOR = 2054 / 1944     # measured Phase D attempt-to-valid ratio


def component_costs(n: int, m: dict, scenario: dict, dual_certification: bool,
                    gpt5_cross_judge: bool) -> dict:
    accepted = n
    gen_calls = accepted * scenario["gen_per_accepted"]
    primary_calls = gen_calls
    secondary_calls = primary_calls * scenario["primary_pass"] if dual_certification else 0.0

    gen_cost = gen_calls * m["generation"]["usd_per_call"]
    primary_cost = primary_calls * m["primary_audit"]["usd_per_call"]
    secondary_cost = secondary_calls * m["secondary_audit"]["usd_per_call"]

    target_calls = accepted * len(TARGETS)
    target_cost = 0.0
    per_target = {}
    for slug, spec in TARGETS.items():
        calls = accepted * RETRY_FACTOR
        cost = calls * (
            U_PROMPT_TOKENS * spec["in_usd_per_m"] / 1e6
            + spec["mean_out_tokens"] * spec["out_usd_per_m"] / 1e6
        )
        per_target[slug] = {"calls": round(calls, 1), "usd": round(cost, 5)}
        target_cost += cost

    judge_calls = accepted * len(TARGETS) * RETRY_FACTOR
    # Gemini is the primary judge. Its usage was never reported by the provider,
    # so it is priced at the measured GPT-5 Mini judging rate: a strict upper bound.
    judge_cost = judge_calls * m["response_judging_gpt5mini"]["usd_per_call"]
    cross_judge_cost = judge_calls * m["response_judging_gpt5mini"]["usd_per_call"] if gpt5_cross_judge else 0.0

    total = gen_cost + primary_cost + secondary_cost + target_cost + judge_cost + cross_judge_cost
    return {
        "n_base_pairs": n,
        "dual_certification": dual_certification,
        "gpt5_cross_judge": gpt5_cross_judge,
        "calls": {
            "generation": round(gen_calls, 1),
            "primary_audit": round(primary_calls, 1),
            "secondary_audit": round(secondary_calls, 1),
            "target_inference": round(target_calls * RETRY_FACTOR, 1),
            "response_judging": round(judge_calls, 1),
            "cross_judging": round(judge_calls, 1) if gpt5_cross_judge else 0,
        },
        "usd": {
            "generation": round(gen_cost, 4),
            "primary_audit": round(primary_cost, 4),
            "secondary_audit": round(secondary_cost, 4),
            "target_inference": round(target_cost, 4),
            "response_judging": round(judge_cost, 4),
            "cross_judging": round(cross_judge_cost, 4),
        },
        "per_target": per_target,
        "total_usd": round(total, 4),
    }


def main() -> None:
    m = measure_ledgers()
    report = {"measured_unit_economics": m, "target_prices": TARGETS,
              "retry_factor": RETRY_FACTOR, "scenarios": SCENARIOS, "designs": {}}

    lines = ["# Phase G cost model", "",
             "All generation, certification and judging unit costs are **measured** from this",
             "repository's own billing ledgers. Target unit prices are the only list-price",
             "inputs, because the V2 target sweep's per-call usage was never persisted.", "",
             "## Measured unit economics", "",
             "| Component | Model | Calls observed | In/call | Out/call | USD/call |",
             "|---|---|---:|---:|---:|---:|"]
    for label, key, model in [
        ("Pair generation", "generation", "google/gemini-2.5-flash"),
        ("Primary certification", "primary_audit", "deepseek/deepseek-v4-flash"),
        ("Secondary certification", "secondary_audit", "openai/gpt-5-mini"),
        ("Response judging", "response_judging_gpt5mini", "openai/gpt-5-mini"),
    ]:
        c = m[key]
        lines.append(f"| {label} | `{model}` | {c['calls']:,} | {c['in_per_call']:,.0f} | "
                     f"{c['out_per_call']:,.0f} | ${c['usd_per_call']:.6f} |")

    f = m["v2_bank_funnel"]
    lines += ["", "## Measured V2 bank-build funnel", "",
              f"- generation calls per accepted pair: **{f['generation_calls_per_accepted_pair']:.2f}**",
              f"- primary auditor pass rate: **{f['primary_pass_rate']:.1%}**",
              f"- secondary auditor pass rate given a primary pass: **{f['secondary_pass_rate']:.1%}**",
              f"- overall acceptance: **{f['overall_acceptance_rate']:.1%}** of audited candidates",
              "",
              "This funnel is recovered from call counts in the accounting ledgers. It is the",
              "closest thing the project has to the V2 certification selectivity that the frozen",
              "six-record attempt log cannot supply.", "",
              "## Target unit prices", "",
              "| Target | Input $/M | Output $/M | Mean output tokens | Source |",
              "|---|---:|---:|---:|---|"]
    for slug, spec in TARGETS.items():
        lines.append(f"| `{slug}` | {spec['in_usd_per_m']} | {spec['out_usd_per_m']} | "
                     f"{spec['mean_out_tokens']:,} | {spec['price_source']} |")

    for scenario_name, scenario in SCENARIOS.items():
        lines += ["", f"## Design costs -- {scenario_name} funnel "
                      f"({scenario['gen_per_accepted']} generation calls per accepted pair, "
                      f"{scenario['primary_pass']:.0%} primary pass, "
                      f"{scenario['secondary_pass']:.0%} secondary pass)", "",
                  "| N | Certification | Cross-judge | Gen | Primary | Secondary | Target | Judge | X-judge | **Total** |",
                  "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for n in (72, 96, 120):
            for dual, xj, label in [(True, False, "dual"), (False, False, "DeepSeek only"),
                                    (True, True, "dual")]:
                row = component_costs(n, m, scenario, dual, xj)
                report["designs"][f"{scenario_name}|N={n}|dual={dual}|xjudge={xj}"] = row
                u = row["usd"]
                lines.append(
                    f"| {n} | {label} | {'yes' if xj else 'no'} | ${u['generation']:.2f} | "
                    f"${u['primary_audit']:.2f} | ${u['secondary_audit']:.2f} | "
                    f"${u['target_inference']:.2f} | ${u['response_judging']:.2f} | "
                    f"${u['cross_judging']:.2f} | **${row['total_usd']:.2f}** |")

    rec = component_costs(96, m, SCENARIOS["expected"], True, False)
    high = component_costs(96, m, SCENARIOS["conservative"], True, True)
    lines += ["", "## Recommended design", "",
              f"- **N = 96, dual certification, no additional GPT-5 Mini cross-judge**",
              f"- expected total: **${rec['total_usd']:.2f}**",
              f"- expected-high (conservative funnel *and* a GPT-5 Mini cross-judge): "
              f"**${high['total_usd']:.2f}**",
              f"- **hard spending ceiling: $10.00** -- roughly 3x expected-high, enforced by the",
              "  runner's live cost accounting, which aborts before exceeding it",
              "",
              "## Dominant cost", "",
              "Secondary certification with GPT-5 Mini dominates every configuration. At "
              f"${m['secondary_audit']['usd_per_call']:.6f} per call it is "
              f"{m['secondary_audit']['usd_per_call']/m['primary_audit']['usd_per_call']:.1f}x the "
              "DeepSeek per-call cost, and it accounted for $7.07 of the $11.84 spent building the",
              "entire V2 bank. Target inference is negligible by comparison: the three open",
              "targets together cost well under a dollar at every N considered.", "",
              "Dropping to DeepSeek-only certification would save roughly "
              f"${component_costs(96, m, SCENARIOS['expected'], True, False)['usd']['secondary_audit']:.2f} "
              "at N=96. The preregistration keeps dual certification anyway: the recovered V1",
              "evidence shows single-auditor certification is exactly the failure mode that made",
              "V1 unusable, and a few dollars is not worth reintroducing it.",
              ]

    (OUT / "COST_MODEL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "cost_model.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")
    print(f"expected N=96 dual, no x-judge : ${rec['total_usd']:.2f}")
    print(f"expected-high N=96 dual + x-judge, conservative funnel: ${high['total_usd']:.2f}")
    for n in (72, 96, 120):
        r = component_costs(n, m, SCENARIOS["expected"], True, False)
        h = component_costs(n, m, SCENARIOS["conservative"], True, True)
        print(f"  N={n:3d}  expected ${r['total_usd']:6.2f}   expected-high ${h['total_usd']:6.2f}"
              f"   new target calls {r['calls']['target_inference']:.0f}")
    print("wrote analysis/phase_g/COST_MODEL.md and cost_model.json")


if __name__ == "__main__":
    main()
