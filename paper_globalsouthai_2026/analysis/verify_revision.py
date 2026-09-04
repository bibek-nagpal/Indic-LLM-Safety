"""Offline revision gate; never dispatches inference or resamples published analyses.

Run with Python plus pypdf. Writes only the workshop verification report.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import re
import subprocess
from pypdf import PdfReader

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
BASE = "de160ee925ad2e3a6c1e4248526bc09404137959"
checks = []


def check(name, condition, detail=None):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


manifests = [
    "frozen_final_2026_08_29/FREEZE_MANIFEST.json",
    "analysis/results/ANALYSIS_MANIFEST.json",
    "analysis/phase_c_results/PHASE_C_MANIFEST.json",
    "analysis/phase_d_run_archive/RUN_ARCHIVE_MANIFEST.json",
    "analysis/phase_d_results/PHASE_D_MANIFEST.json",
    "analysis/sensitivity_results/SENSITIVITY_MANIFEST.json",
]
entry_count = 0
for rel in manifests:
    path = ROOT / rel
    manifest = read_json(path)
    entries = manifest.get("files") or [
        {"path": k, "sha256": v} for k, v in manifest["outputs"].items()]
    bad = [e["path"] for e in entries if sha(path.parent / e["path"]) != e["sha256"]]
    entry_count += len(entries)
    check(rel, not bad, {"entries": len(entries), "mismatches": bad})
check("82 frozen manifest entries", entry_count == 82)
completed_workbook_sha = "535a59facb9f662e86d7c8f7063431fd7cee064f20b10e7dcda4f92c25bf8fbb"
check("Completed Human A workbook identified", sha(ROOT / "Human_A_annotations.xlsx") ==
      completed_workbook_sha)
human_path = PAPER / "analysis/human_a_results.json"
human_results = read_json(human_path)
check("Human result provenance matches completed workbook",
      human_results["provenance"]["workbook_sha256"] == completed_workbook_sha)
check("Completed Human A analysis status", human_results["status"] == "PASS")

head = read_json(PAPER / "analysis/headline_verification.json")
with (ROOT / "analysis/results/main_results.csv").open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
        current = head["per_model"][row["model"]]
        check(row["model"] + " CI provenance", current["gap_ci_pp"] ==
              [float(row["refusal_gap_ci_low_pp"]), float(row["refusal_gap_ci_high_pp"])])
check("Point-estimate recomputation", head["status"] == "PASS")

run = ROOT / "frozen_final_2026_08_29/run/revision_v2_targets_final"
scores = [json.loads(s) for s in (run / "scores.jsonl").read_text(encoding="utf-8").splitlines()]
score = {(s["model"], s["pair_id"], s["language"]): s["score"] for s in scores}
responses = {}
for line in (run / "traces.jsonl").read_text(encoding="utf-8").splitlines():
    t = json.loads(line)
    for key, lang in [("english", "en"), ("romanized_hindi", "rh")]:
        item = t.get(key, {})
        if item.get("content") and not item.get("error"):
            responses[(t["model"], t["pair_id"], lang)] = item["content"]
short_zeros = defaultdict(list)
for k, s in score.items():
    response = responses[k]
    if s == 0 and len(response) < 80:
        short_zeros[(k[0], k[2])].append(response)
expected = {("nvidia/nemotron-3-nano-30b-a3b", "rh"): 272,
            ("nvidia/nemotron-3-nano-30b-a3b", "en"): 208,
            ("openai/gpt-oss-20b", "en"): 412,
            ("openai/gpt-oss-20b", "rh"): 367}
for k, n in expected.items():
    vals = short_zeros[k]
    normalized = {v.replace("\u2019", "'").strip() for v in vals}
    check("Explicit short refusal " + str(k), len(vals) == n and
          normalized == {"I'm sorry, but I can't help with that."}, {"count": len(vals)})
with (ROOT / "analysis/phase_d_results/judge_replacement_main_results.csv").open(encoding="utf-8") as f:
    by_judge = defaultdict(list)
    for r in csv.DictReader(f):
        by_judge[r["judge"]].append((float(r["refusal_gap_pp"]), r["model_display"]))
for judge, values in by_judge.items():
    check("Cross-judge ordering: " + judge, [n for _, n in sorted(values, reverse=True)] ==
          ["Qwen3-30B-A3B", "GPT-OSS-20B", "Nemotron-3-Nano"])

source = (PAPER / "main.tex").read_text(encoding="utf-8")
bib = (PAPER / "references.bib").read_text(encoding="utf-8")
cited = {key.strip() for group in re.findall(r"\\cite\w*\{([^}]+)\}", source) for key in group.split(",")}
keys = re.findall(r"@\w+\{([^,]+),", bib)
check("All cited keys defined once", cited <= set(keys) and len(keys) == len(set(keys)), {"cited": len(cited)})
check("All bibliography entries cited", set(keys) == cited)
check("Verified bibliography author repairs", all(s in bib for s in
      ["Kumar, Shanu", "Agrawal, Parag", "Aswal, Darpan", "Jaiswal, Siddharth D", "Lingyu, Meng"]))
check("Official anonymous workshop option and title", "[dblblindworkshop]" in source and
      "\\workshoptitle{GlobalSouthAI}" in source)
check("No layout overrides", not re.search(r"\\(?:vspace|hspace|geometry|newgeometry|linespread|fontsize|enlargethispage|addtolength|setlength)\b", source))
# Derived from the official archive identified in SUBMISSION_RULES.md, not from
# the candidate: these checks must work even when the ignored download is absent.
style = (PAPER / "neurips_2026.sty").read_text(encoding="utf-8").strip()
check("Official style restored (newline-normalized)", hashlib.sha256(style.encode()).hexdigest() ==
      "4991ddfd7fef1656ca236d70f10be15d4b77f6baef19c4f916035c59d8be33cc")
checklist = (PAPER / "checklist.tex").read_text(encoding="utf-8")
check("16 answered checklist items, no TODO", len(re.findall(r"Answer: \\answer(?:Yes|No|NA)\{\}", checklist)) == 16
      and "answerTODO" not in checklist and "justificationTODO" not in checklist)
skeleton = checklist[checklist.index(r"\begin{enumerate}"):]
skeleton = re.sub(r"^\s*\\item\[\] (?:Answer|Justification):[^\n]*", "", skeleton, flags=re.M)
check("Official checklist questions and guidelines retained", hashlib.sha256(" ".join(skeleton.split()).encode()).hexdigest() ==
      "b26d17746abe289d714097a8149f8387e5f234ea63a2ead26b5c2624447e6fd1")

pdf = PdfReader(PAPER / "main.pdf")
pages = [p.extract_text() for p in pdf.pages]
reference_page = next((i + 1 for i, t in enumerate(pages) if re.search(r"^References\s*\d*\s*$", t, re.M)), None)
check("Main paper at most four pages", reference_page is not None and reference_page <= 5,
      {"references_begin_page": reference_page, "total_pages": len(pages)})
check("US Letter pages", all(abs(float(p.mediabox.width) - 612) < 1 and abs(float(p.mediabox.height) - 792) < 1 for p in pdf.pages))
full = " ".join(pages)
check("PDF checklist included", "NeurIPS Paper Checklist" in full)
check("PDF author metadata anonymous", (pdf.metadata.author or "") in ("", "Anonymous Author(s)"))
check("No identifying local paths in PDF", not re.search(r"C:\\|\bPrahlada\b|\bDELL\b|github\.com/", full, re.I))
check("Figure percent escape repaired", "\\%" not in (PAPER / "analysis/build_figure.py").read_text(encoding="utf-8"))
changed = subprocess.check_output(["git", "-c", "core.safecrlf=false", "diff", "--name-only", BASE], cwd=ROOT, text=True).splitlines()
check("Tracked changes restricted to workshop", all(p.startswith("paper_globalsouthai_2026/") for p in changed), changed)

report = {"baseline": BASE, "status": "PASS" if all(c["pass"] for c in checks) else "FAIL",
          "frozen_entries": entry_count, "pdf_sha256": sha(PAPER / "main.pdf"),
          "pdf_pages": len(pages), "references_begin_page": reference_page, "checks": checks}
(PAPER / "analysis/revision_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
for c in checks:
    print(("PASS" if c["pass"] else "FAIL"), c["name"])
print(report["status"], len(checks), "checks")
raise SystemExit(0 if report["status"] == "PASS" else 1)
