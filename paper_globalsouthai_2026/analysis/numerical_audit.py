#!/usr/bin/env python3
"""Check every headline number that appears in the compiled PDF against verified sources."""
import json, re, subprocess, sys, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
head = json.loads((HERE / "headline_verification.json").read_text(encoding="utf-8"))
human = json.loads((HERE / "human_a_results.json").read_text(encoding="utf-8"))
pdf = PAPER / "main.pdf"
if shutil.which("pdftotext"):
    command = ["pdftotext", str(pdf), "-"]
elif sys.platform == "win32":
    command = ["wsl", "-d", "Ubuntu", "--exec", "pdftotext", "/mnt/" + pdf.drive[0].lower() + pdf.as_posix()[2:], "-"]
else:
    raise SystemExit("Install poppler-utils: pdftotext is required for the PDF text audit.")
text = subprocess.run(command,
                      capture_output=True, text=True, check=True).stdout
flat = " ".join(text.split())
flat = flat.replace("\u2212", "-")

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
    ("GPT-OSS validated CI", "[1.4, 7.7]", [round(x, 1) for x in g["gap_ci_pp"]] == [1.4, 7.7]),
    ("Nemotron validated CI", "[-6.5, 2.8]", [round(x, 1) for x in n["gap_ci_pp"]] == [-6.5, 2.8]),
    ("Nemotron gap -1.8", "1.8", round(n["gap_pp"], 1) == -1.8),
    ("Nemotron fwd 65 rev 70", "(65 forward, 70 reverse)",
     n["forward_flips"] == 65 and n["reverse_flips"] == 70),
    ("human exact 69.2", "69.2", round(100 * hg["exact"], 1) == 69.2),
    ("human adjacent 92.9", "92.9", round(100 * hg["adjacent"], 1) == 92.9),
    ("human kappa 0.485", "0.485", round(hg["kappa"], 3) == 0.485),
    ("human qwk 0.794", "0.794", round(hg["kappa_quadratic"], 3) == 0.794),
    ("human CI [63.8, 74.1]", "[63.8, 74.1]",
     [round(100 * x, 1) for x in hg["exact_ci"]] == [63.8, 74.1]),
    ("human higher 91 lower 18", "on 91 items and lower on 18",
     hg["human_higher"] == 91 and hg["other_higher"] == 18),
    ("human analyzed n 354", "354 analyzed items", hg["n"] == 354),
    ("human GPT5 exact rounding", "75.1%", round(100 * human["agreement"]["human_vs_gpt5mini"]["exact"], 1) == 75.1),
    ("human GPT5 adjacent rounding", "92.7%", round(100 * human["agreement"]["human_vs_gpt5mini"]["adjacent"], 1) == 92.7),
    ("human GPT5 kappa rounding", "0.589", round(human["agreement"]["human_vs_gpt5mini"]["kappa"], 3) == 0.589),
    ("human GPT5 QWK rounding", "0.851", round(human["agreement"]["human_vs_gpt5mini"]["kappa_quadratic"], 3) == 0.851),
    ("human GPT5 CI rounding", "[70.1, 79.9]", [round(100 * x, 1) for x in human["agreement"]["human_vs_gpt5mini"]["exact_ci"]] == [70.1, 79.9]),
    ("items with valid labels 357", "357 scored items", human["completion"]["items_with_valid_labels"] == 357),
    ("blank labels 3 of 360", "three labels are blank", human["completion"]["items_unscored"] == 3),
    ("complete jobs 174", "174 verified jobs", human["completion"]["jobs_with_both_languages_scored"] == 174),
    ("binary agreement 87.9", "87.9",
     round(100 * human["agreement"]["nonassistance_binary"]["exact"], 1) == 87.9),
    ("human Qwen gap +37.9", "37.9", round(hr["Qwen3-30B-A3B"]["human_gap_pp"], 1) == 37.9),
    ("same-pairs Qwen judge gap +36.2", "36.2", round(hr["Qwen3-30B-A3B"]["gemini_gap_pp"], 1) == 36.2),
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
# The sweep is a regression guard, not a substitute for semantic/visual review.
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
REQUIRED = ["single-co-author human audit",
            "final generation used the seed unchanged",
            "only pairs accepted by both were retained",
            "Gemini generated the prompts and also served as the primary response judge",
            "explicit EN/RH language label",
            "both prompt conditions use Latin script", "SequenceMatcher",
            "Cross-bank consolidation removed exact matches only", "does not adjust for prompt length",
            "no benign or direct-request control"]
REQUIRED += ["unpaid co-author", "without AI assistance", "knowingly and voluntarily undertook",
             "automated-judge scores", "aggregate experimental results",
             "357 contain valid scores", "three labels are blank",
             "Three labeled rows fail", "174 complete pair-model jobs",
             "No crowdsourcing or human-subject recruitment was conducted"]
missing_required = [s for s in REQUIRED if s.lower() not in flat.lower()]
FORBIDDEN = ["reflectively optimized", "cannot manufacture", "cannot produce a between-model",
             "more consistent with degenerate", "also reverses under judge", "ordering is not",
             "across script", "English refusal or near-refusal", "not missing at random",
             "hundreds of millions", "high-refusal", "occupy three different regimes",
             "79.7%", "0.886", "Annotator B labels", "two annotator", "second annotator",
             "independent human", "independent external", "73 unscored", "287 scores",
             "n = 285", "missingness is associated", "outcome-associated",
             "completion-conditional", "background sheet", "unestablished consent",
             "consent was unestablished", "For the Global South", "India-salient",
             "preregistered fallback", "register-sensitive evaluation", "per-model claims",
             "without claiming that work validates", "conjunctive cascade, not",
             "not independent validation or a test of equality",
             "No formal institutional ethics/IRB review or approval was obtained"]
stale_hits += [s for s in FORBIDDEN if s.lower() in flat.lower()]

out = ["# Numerical consistency audit", "",
       "Every headline number in the compiled PDF, checked against",
       "`analysis/headline_verification.json` and `analysis/human_a_results.json`.",
       "Point estimates are checked against frozen artifacts; confidence intervals are reused",
       "from validated Phase B and the completed Human A result JSON; only its fixed-seed",
       "job-cluster bootstrap was recomputed for the completed workbook.", "",
       "| check | string required in PDF | status | detail |", "|---|---|---|---|"]
out += ["| %s | `%s` | %s | %s |" % r for r in rows]
out += ["", "## Stale / forbidden phrase sweep", ""]
out.append("Searched the configured legacy-claim and forbidden-phrase regression list.")
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
