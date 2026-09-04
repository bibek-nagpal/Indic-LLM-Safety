#!/usr/bin/env python3
"""Check every headline number that appears in the compiled PDF against verified sources."""
import json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
head = json.loads((HERE / "headline_verification.json").read_text(encoding="utf-8"))
human = json.loads((HERE / "human_a_results.json").read_text(encoding="utf-8"))
text = subprocess.run(["pdftotext", str(PAPER / "main.pdf"), "-"],
                      capture_output=True, text=True, check=True).stdout
flat = " ".join(text.split())

q = head["per_model"]["qwen/qwen3-30b-a3b-instruct-2507"]
g = head["per_model"]["openai/gpt-oss-20b"]
n = head["per_model"]["nvidia/nemotron-3-nano-30b-a3b"]
hg = human["agreement"]["human_vs_gemini"]
hr = human["human_rates"]["per_model"]

CHECKS = [
    ("bank size 504", "504", head["bank"]["n_pairs"] == 504),
    ("responses per model 1,008", "1,008", head["scores"]["n_response_judgments"] // 3 == 1008),
    ("total responses 3,024", "3,024", head["scores"]["n_response_judgments"] == 3024),
    ("pair-model observations 1,512", "1,512", head["scores"]["n_pair_model_observations"] == 1512),
    ("cells 12 x 42", "42 accepted", head["bank"]["n_cells"] == 12 and head["bank"]["per_cell"] == [42]),
    ("Qwen EN 65.9", "65.9", round(q["en_nonassistance_pct"], 1) == 65.9),
    ("Qwen RH 22.8", "22.8", round(q["rh_nonassistance_pct"], 1) == 22.8),
    ("Qwen gap +43.1", "43.1", round(q["gap_pp"], 1) == 43.1),
    ("Qwen CI [38.5, 47.6]", "[38.5, 47.6]", [round(x, 1) for x in q["gap_ci_pp"]] == [38.5, 47.6]),
    ("Qwen critical flips 85", "85 of 504", q["critical_forward"] == 85),
    ("Qwen critical pct 16.9", "16.9", round(100 * q["critical_forward"] / 504, 1) == 16.9),
    ("GPT-OSS gap +4.6", "4.6", round(g["gap_pp"], 1) == 4.6),
    ("Nemotron gap -1.8", "1.8", round(n["gap_pp"], 1) == -1.8),
    ("Nemotron fwd 65 rev 70", "(65 forward, 70 reverse)",
     n["forward_flips"] == 65 and n["reverse_flips"] == 70),
    ("human exact 74.7", "74.7", round(100 * hg["exact"], 1) == 74.7),
    ("human adjacent 94.0", "94.0", round(100 * hg["adjacent"], 1) == 94.0),
    ("human kappa 0.513", "0.513", round(hg["kappa"], 3) == 0.513),
    ("human qwk 0.825", "0.825", round(hg["kappa_quadratic"], 3) == 0.825),
    ("human CI [69.4, 79.9]", "[69.4, 79.9]",
     [round(100 * x, 1) for x in hg["exact_ci"]] == [69.4, 79.9]),
    ("human higher 58 lower 14", "on 58 items and lower on 14",
     hg["human_higher"] == 58 and hg["other_higher"] == 14),
    ("human n 285", "285", hg["n"] == 285),
    ("items returned 287", "287", human["completion"]["items_scored_including_unverifiable_stimuli"] == 287),
    ("unscored 73 of 360", "73 of 360", human["completion"]["items_unscored"] == 73),
    ("binary agreement 88.8", "88.8",
     round(100 * human["agreement"]["nonassistance_binary"]["exact"], 1) == 88.8),
    ("human Qwen gap +53.1", "53.1", round(hr["Qwen3-30B-A3B"]["human_gap_pp"], 1) == 53.1),
    ("fallback 2 of 3,024", "2 of 3,024", head["scores"]["fallback_judged_responses"] == 2),
]

rows, failures = [], []
for name, needle, source_ok in CHECKS:
    in_pdf = needle in flat
    ok = source_ok and in_pdf
    rows.append((name, needle, "PASS" if ok else "FAIL",
                 "source=%s pdf=%s" % (source_ok, in_pdf)))
    if not ok:
        failures.append(name)

# stale-number sweep: values from the older V1 experiment must not appear
# Phrases that would indicate a claim the evidence does not support.
# Phrases that would indicate a claim the evidence does not support. "two annotators" and
# "adjudication" are NOT listed: the paper now discloses that a two-annotator design was
# preregistered and that annotator B returned nothing, which is a required disclosure.
STALE = ["1,512 unique", "1512 unique prompt pairs", "Logical Appeal", "two human annotators",
         "inter-annotator agreement", "human consensus", "ground truth", "Phase G", "archaic"]
NEGATORS = ("no ", "not ", "never", "without", "makes no", "make no", "single annotator")


def affirmative_hits(phrases):
    """A phrase only counts as a defect if it is NOT inside a negated disclaimer."""
    low = flat.lower()
    found = []
    for phrase in phrases:
        start = 0
        while True:
            i = low.find(phrase.lower(), start)
            if i < 0:
                break
            window = low[max(0, i - 90):i]
            if not any(neg in window for neg in NEGATORS):
                found.append(phrase)
                break
            start = i + 1
    return found


stale_hits = affirmative_hits(STALE)
# Required disclaimers that MUST be present.
REQUIRED = ["single annotator", "make no inter-annotator", "not completed",
            "Annotator B returned a workbook containing no scores",
            "reflectively optimized", "cascade", "the same model",
            "no direct-request and no benign condition"]
missing_required = [s for s in REQUIRED if s.lower() not in flat.lower()]

out = ["# Numerical consistency audit", "",
       "Every headline number in the compiled PDF, checked against",
       "`analysis/headline_verification.json` and `analysis/human_a_results.json`,",
       "which are themselves recomputed from the frozen artifacts.", "",
       "| check | string required in PDF | status | detail |", "|---|---|---|---|"]
out += ["| %s | `%s` | %s | %s |" % r for r in rows]
out += ["", "## Stale / forbidden phrase sweep", ""]
out.append("Searched for: " + ", ".join("`%s`" % s for s in STALE))
out.append("")
out.append("**Result:** " + ("no hits" if not stale_hits else "HITS: " + ", ".join(stale_hits)))
out += ["", "## Required-disclaimer sweep", "",
        "Searched for: " + ", ".join("`%s`" % s for s in REQUIRED), "",
        "**Result:** " + ("all present" if not missing_required
                          else "MISSING: " + ", ".join(missing_required))]
out += ["", "## Verdict", "",
        "**%s** — %d/%d checks pass%s." % (
            "PASS" if not failures and not stale_hits and not missing_required else "FAIL",
            len(rows) - len(failures), len(rows),
            "" if not failures else "; failed: " + ", ".join(failures))]
(PAPER / "NUMERICAL_AUDIT.md").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join("%-4s %s" % (r[2], r[0]) for r in rows))
print("\nstale hits:", stale_hits or "none")
print("missing required disclaimers:", missing_required or "none")
ok = not failures and not stale_hits and not missing_required
print("VERDICT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
