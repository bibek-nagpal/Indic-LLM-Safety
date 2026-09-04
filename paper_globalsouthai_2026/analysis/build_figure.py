#!/usr/bin/env python3
"""One compact figure: EN vs RH non-assistance by model, from verified analysis output."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
head = json.loads((HERE / "headline_verification.json").read_text(encoding="utf-8"))
MODELS = ["qwen/qwen3-30b-a3b-instruct-2507", "openai/gpt-oss-20b", "nvidia/nemotron-3-nano-30b-a3b"]

names, en, rh, gaps, lo, hi = [], [], [], [], [], []
for m in MODELS:
    d = head["per_model"][m]
    names.append(d["display"]); en.append(d["en_nonassistance_pct"]); rh.append(d["rh_nonassistance_pct"])
    gaps.append(d["gap_pp"]); lo.append(d["gap_pp"] - d["gap_ci_pp"][0]); hi.append(d["gap_ci_pp"][1] - d["gap_pp"])

fig, ax = plt.subplots(figsize=(5.4, 2.05))
y = range(len(names))
for i, (a, b) in enumerate(zip(en, rh)):
    ax.plot([b, a], [i, i], color="#9aa0a6", lw=1.4, zorder=1, solid_capstyle="round")
ax.scatter(en, list(y), s=46, color="#1f4e79", zorder=3, label="English")
ax.scatter(rh, list(y), s=46, color="#c1440e", zorder=3, marker="D", label="Romanized Hindi")
for i, g in enumerate(gaps):
    x = max(en[i], rh[i]) + 3
    ax.annotate("%+.1f pp" % g, (x, i), va="center", fontsize=8.5, color="#202124")
ax.set_yticks(list(y)); ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel("Non-assistance rate (score $=$ 0), \\% of 504 matched pairs", fontsize=9)
ax.set_xlim(0, 108); ax.set_ylim(-0.6, len(names) - 0.4)
ax.tick_params(axis="x", labelsize=8.5)
ax.grid(axis="x", color="#e8eaed", lw=0.7)
ax.set_axisbelow(True)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color("#9aa0a6")
ax.legend(frameon=False, fontsize=8.5, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2,
          handletextpad=0.3, columnspacing=1.2)
fig.tight_layout(pad=0.3)
(HERE.parent / "figures").mkdir(exist_ok=True)
fig.savefig(HERE.parent / "figures/gap_by_model.pdf", bbox_inches="tight")
print("wrote figures/gap_by_model.pdf")
