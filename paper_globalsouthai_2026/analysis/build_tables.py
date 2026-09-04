#!/usr/bin/env python3
"""Emit LaTeX tables directly from the verified analysis JSON. No hand-typed numbers."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
MODELS = ["qwen/qwen3-30b-a3b-instruct-2507", "openai/gpt-oss-20b", "nvidia/nemotron-3-nano-30b-a3b"]
NAMES = ["Qwen3-30B-A3B", "GPT-OSS-20B", "Nemotron-3-Nano"]

head = json.loads((HERE / "headline_verification.json").read_text(encoding="utf-8"))
human = json.loads((HERE / "human_a_results.json").read_text(encoding="utf-8"))

rows = []
for m in MODELS:
    d = head["per_model"][m]
    rows.append(r"%s & %.1f & %.1f & $%+.1f$ & [%.1f, %.1f] & %d & %d \\" % (
        d["display"], d["en_nonassistance_pct"], d["rh_nonassistance_pct"], d["gap_pp"],
        d["gap_ci_pp"][0], d["gap_ci_pp"][1], d["forward_flips"], d["critical_forward"]))
(PAPER / "tables/main_results.tex").write_text(
    "\\begin{tabular}{lrrrrrr}\n\\toprule\n"
    "Model & EN (\\%) & RH (\\%) & Gap (pp) & 95\\% CI & Fwd.\\ flips & Crit.\\ flips \\\\\n"
    "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n",
    encoding="utf-8", newline="\n")

rows = []
for name in NAMES:
    d = human["human_rates"]["per_model"][name]
    rows.append(r"%s & %d & %.1f & %.1f & $%+.1f$ & [%.1f, %.1f] & $%+.1f$ \\" % (
        name, d["n_jobs"], d["human_en_nonassistance_pct"], d["human_rh_nonassistance_pct"],
        d["human_gap_pp"], d["human_gap_ci_pp"][0], d["human_gap_ci_pp"][1], d["gemini_gap_pp"]))
(PAPER / "tables/human_rates.tex").write_text(
    "\\begin{tabular}{lrrrrrr}\n\\toprule\n"
    "Model & Jobs & EN (\\%) & RH (\\%) & Human gap & 95\\% CI & Judge gap \\\\\n"
    "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n",
    encoding="utf-8", newline="\n")
print("wrote tables/main_results.tex and tables/human_rates.tex")
