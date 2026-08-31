"""Phase G design calculations: precision and power for N = 72, 96, 120.

Uses only frozen E (English) and R (Romanized Hindi) outcomes. No U outcome is
assumed to exist; U is explored across prespecified hypothetical scenarios.
No API call is made.

Primary estimand, per target model m, on the selected pair subset S:

    d_i^{ER} = 1[s(E_i)=0] - 1[s(R_i)=0]      existing RH effect
    d_i^{EU} = 1[s(E_i)=0] - 1[s(U_i)=0]      new unusual-English effect
    Delta_m  = mean_i d_i^{ER} - mean_i d_i^{EU}
             = mean_i ( 1[s(U_i)=0] - 1[s(R_i)=0] )

The difference-in-differences collapses to a paired U-vs-R contrast on the same
pairs, because the shared English arm cancels. Delta is therefore estimated by
an exact paired (McNemar) analysis on discordant pairs, which is what the power
calculation below models.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
SCORES = ROOT / "frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl"
MODELS = (
    "qwen/qwen3-30b-a3b-instruct-2507",
    "openai/gpt-oss-20b",
    "nvidia/nemotron-3-nano-30b-a3b",
)
NAMES = {MODELS[0]: "Qwen3-30B-A3B", MODELS[1]: "GPT-OSS-20B", MODELS[2]: "Nemotron-3-Nano"}
CANDIDATE_N = (72, 96, 120)
N_SIM = 20_000
SEED = 20260901
ALPHA = 0.05


def _build_exact_reject_table(max_n: int, alpha: float) -> np.ndarray:
    """Lookup of the exact two-sided sign-test decision for every (n, b).

    Vectorises the power simulation: scipy's binomtest is called once per
    (n_discordant, successes) cell instead of once per simulated dataset.
    """
    table = np.zeros((max_n + 1, max_n + 1), dtype=bool)
    for n in range(1, max_n + 1):
        for b in range(n + 1):
            table[n, b] = stats.binomtest(b, n, 0.5).pvalue < alpha
    return table


_EXACT_REJECT = _build_exact_reject_table(max(CANDIDATE_N), ALPHA)


def load() -> tuple[list[str], dict]:
    rows = [json.loads(line) for line in SCORES.open(encoding="utf-8") if line.strip()]
    table = {(r["pair_id"], r["model"], r["language"]): r["score"] for r in rows}
    pairs = sorted({r["pair_id"] for r in rows})
    return pairs, table


def joint(pairs, table, model):
    """Observed per-pair (non-assistance under E, non-assistance under R)."""
    e = np.array([table[(p, model, "en")] == 0 for p in pairs], dtype=int)
    r = np.array([table[(p, model, "rh")] == 0 for p in pairs], dtype=int)
    return e, r


def simulate(e, r, n, rho, rng, n_sim=N_SIM):
    """Power of the exact paired test of Delta = 0 for a given scenario.

    rho is the fraction of the observed E->R effect that the unusual-English
    arm is assumed to reproduce. U is generated pair-wise: where E and R differ,
    U takes R's value with probability rho and E's value otherwise; where E and
    R agree, U takes that shared value. This preserves the observed marginals
    and the pairing, and encodes the scenario as a single interpretable knob.
    """
    idx = rng.integers(0, len(e), size=(n_sim, n))
    e_s, r_s = e[idx], r[idx]
    follow = rng.random((n_sim, n)) < rho
    u_s = np.where(e_s == r_s, e_s, np.where(follow, r_s, e_s))

    b = np.sum((u_s == 1) & (r_s == 0), axis=1)   # U non-assisting, R assisting
    c = np.sum((u_s == 0) & (r_s == 1), axis=1)   # the reverse
    n_disc = b + c
    reject = _EXACT_REJECT[n_disc, b]
    delta = (u_s.mean(axis=1) - r_s.mean(axis=1)) * 100
    half = 1.96 * np.std(delta, ddof=1)
    return {
        "power": float(reject.mean()),
        "mean_delta_pp": float(delta.mean()),
        "ci_halfwidth_pp": float(half / np.sqrt(1)),  # delta already an n-sample mean
        "se_pp": float(np.std(delta, ddof=1)),
        "mean_discordant": float(n_disc.mean()),
    }


def main() -> None:
    pairs, table = load()
    rng = np.random.default_rng(SEED)
    report = {"seed": SEED, "n_sim": N_SIM, "alpha": ALPHA, "models": {}}

    print("Observed frozen E/R structure on all 504 pairs\n")
    print(f"{'model':18s} {'E non-asst':>11} {'R non-asst':>11} {'gap pp':>8} {'discordant':>11}")
    for m in MODELS:
        e, r = joint(pairs, table, m)
        disc = int(np.sum(e != r))
        print(f"{NAMES[m]:18s} {e.mean():11.4f} {r.mean():11.4f} "
              f"{100*(e.mean()-r.mean()):8.2f} {disc:11d}")

    print("\nScenario power for the primary paired U-vs-R test\n")
    print("rho = share of the observed E->R effect that unusual English reproduces")
    print("  rho=0.00  U behaves exactly like ordinary English  -> register-specific")
    print("  rho=0.50  U reproduces half the effect             -> mixed")
    print("  rho=1.00  U behaves exactly like RH                -> generic OOD\n")

    for m in MODELS:
        e, r = joint(pairs, table, m)
        report["models"][NAMES[m]] = {
            "en_non_assistance": float(e.mean()),
            "rh_non_assistance": float(r.mean()),
            "observed_gap_pp": float(100 * (e.mean() - r.mean())),
            "scenarios": {},
        }
        print(f"--- {NAMES[m]} (observed E-R gap {100*(e.mean()-r.mean()):.2f} pp) ---")
        print(f"{'N':>5} {'rho':>6} {'E[Delta] pp':>12} {'SE pp':>7} "
              f"{'95% CI halfwidth':>17} {'power':>7} {'E[discordant]':>14}")
        for n in CANDIDATE_N:
            for rho in (0.0, 0.25, 0.5, 0.75, 1.0):
                res = simulate(e, r, n, rho, rng)
                report["models"][NAMES[m]]["scenarios"][f"N={n},rho={rho}"] = res
                print(f"{n:5d} {rho:6.2f} {res['mean_delta_pp']:12.2f} {res['se_pp']:7.2f} "
                      f"{1.96*res['se_pp']:17.2f} {res['power']:7.3f} {res['mean_discordant']:14.1f}")
        print()

    out = ROOT / "analysis/phase_g/design_power.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
