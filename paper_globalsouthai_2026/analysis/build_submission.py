"""Clean, isolated LaTeX build; no stale aux/bbl files or network operations.

Requires pdflatex and bibtex in PATH. Windows users can run this with Python in WSL.
The generated staging directory is retained for inspection under ignored build/.
"""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile

paper = Path(__file__).resolve().parents[1]
build_root = paper / "build"
build_root.mkdir(exist_ok=True)
stage = Path(tempfile.mkdtemp(prefix="submission_clean_", dir=build_root))
for name in ("main.tex", "references.bib", "neurips_2026.sty", "checklist.tex"):
    shutil.copy2(paper / name, stage / name)
for name in ("tables", "figures"):
    shutil.copytree(paper / name, stage / name)
commands = [
    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
    ["bibtex", "main"],
    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
]
for i, command in enumerate(commands, 1):
    proc = subprocess.run(command, cwd=stage, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stage / f"pass_{i}.txt").write_bytes(proc.stdout)
    if proc.returncode:
        raise RuntimeError(f"Build failed; inspect {stage / f'pass_{i}.txt'}")
log = (stage / "main.log").read_text(errors="replace")
for problem in ("undefined", "Rerun to get", "Overfull", "Missing character"):
    if problem in log:
        raise RuntimeError(f"Unresolved {problem!r}; inspect {stage / 'main.log'}")
bib_log = (stage / "main.blg").read_text(errors="replace")
if "Warning--" in bib_log:
    raise RuntimeError(f"Bibliography warning; inspect {stage / 'main.blg'}")
shutil.copy2(stage / "main.pdf", paper / "main.pdf")
(build_root / "latest_build.json").write_text(json.dumps({"stage": stage.name,
    "commands": commands, "status": "PASS"}, indent=2) + "\n")
print(f"PASS: clean build at {stage.name}; main.pdf updated")
