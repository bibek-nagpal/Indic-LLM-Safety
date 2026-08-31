"""Render the V1->V2 dossier and executive summary to PDF.

Deterministic, offline, no network and no API calls. Requires pandoc with
xelatex, both present in the project toolchain.

    python docs/build_dossier_pdfs.py

Pandoc renders its own title block from the --metadata title/date, so the
leading H1 and the bold metadata lines are stripped from the PDF input to
avoid a duplicated heading. The Markdown sources keep them, because they are
read directly far more often than the PDFs are.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

HEADER = r"""
\usepackage{etoolbox}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{ragged2e}
\usepackage{microtype}
\PassOptionsToPackage{table}{xcolor}
\definecolor{navy}{HTML}{17365D}
\definecolor{rulegrey}{HTML}{AAB7C4}

% Wide Markdown tables: shrink and allow wrapping so nothing overflows.
\AtBeginEnvironment{longtable}{\footnotesize\setlength{\tabcolsep}{4pt}}
\let\oldtabular\tabular
\renewcommand{\tabular}{\footnotesize\oldtabular}
\setlength{\LTleft}{0pt}
\setlength{\LTright}{0pt}
\setlength{\emergencystretch}{3em}
\sloppy

\usepackage{titlesec}
\titleformat{\section}{\normalfont\Large\bfseries\color{navy}}{\thesection}{0.6em}{}
\titleformat{\subsection}{\normalfont\large\bfseries\color{navy}}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\normalfont\normalsize\bfseries\color{navy}}{\thesubsubsection}{0.6em}{}

\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\footnotesize\color{navy}Prahlada / IndicAlignProbe}
\fancyhead[R]{\footnotesize\color{navy}RUNNINGHEAD}
\fancyfoot[C]{\footnotesize\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{rulegrey}%
  \leaders\hrule height \headrulewidth\hfill}}
"""

DOCUMENTS = [
    {
        "source": DOCS / "PRAHLADA_V2_PROJECT_STATUS.md",
        "output": DOCS / "PRAHLADA_V2_PROJECT_STATUS.pdf",
        "title": "Prahlada / IndicAlignProbe: V1-to-V2 Project Status",
        "running_head": r"V1$\rightarrow$V2 Project Status",
        "toc": True,
    },
    {
        "source": DOCS / "PRAHLADA_V2_EXECUTIVE_SUMMARY.md",
        "output": DOCS / "PRAHLADA_V2_EXECUTIVE_SUMMARY.pdf",
        "title": "Prahlada / IndicAlignProbe: Executive Summary",
        "running_head": "Executive Summary",
        "toc": False,
    },
]

DATE = r"Verified repository state \texttt{f913e17} \quad 2026-08-31"


def strip_leading_title(text: str) -> str:
    """Drop the H1 and the bold metadata lines that follow it."""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].startswith("# "):
        start = 1
        while start < len(lines) and (
            lines[start].strip() == "" or lines[start].lstrip().startswith("**")
        ):
            if lines[start].strip() == "" and start + 1 < len(lines) \
               and not lines[start + 1].lstrip().startswith("**"):
                break
            start += 1
    return "\n".join(lines[start:]).lstrip("\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(doc: dict, header_path: Path) -> None:
    body = strip_leading_title(doc["source"].read_text(encoding="utf-8"))
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
        handle.write(body)
        staged = Path(handle.name)

    header = header_path.read_text(encoding="utf-8").replace("RUNNINGHEAD", doc["running_head"])
    with tempfile.NamedTemporaryFile("w", suffix=".tex", delete=False, encoding="utf-8") as handle:
        handle.write(header)
        header_file = Path(handle.name)

    command = [
        "pandoc", str(staged), "-o", str(doc["output"]),
        "--pdf-engine=xelatex",
        f"--include-in-header={header_file}",
        "-V", "geometry:a4paper,margin=2cm",
        "-V", "fontsize=10pt",
        "-V", "colorlinks=true", "-V", "linkcolor=navy", "-V", "urlcolor=navy",
        "-V", f"title={doc['title']}",
        "-V", f"date={DATE}",
    ]
    if doc["toc"]:
        command += ["--toc", "--toc-depth=2"]

    result = subprocess.run(command, capture_output=True, text=True)
    staged.unlink(missing_ok=True)
    header_file.unlink(missing_ok=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(f"pandoc failed for {doc['source'].name}")
    for line in result.stderr.splitlines():
        if "Missing character" in line:
            raise SystemExit(f"font gap in {doc['source'].name}: {line.strip()}")


def inspect(pdf: Path) -> dict:
    """Structural check: page count, blank pages, right-margin overflow."""
    bbox = subprocess.run(
        ["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True
    ).stdout
    pages = re.findall(r'<page width="([\d.]+)" height="[\d.]+">(.*?)</page>', bbox, re.S)
    blank, overflow = [], []
    for index, (width, body) in enumerate(pages, start=1):
        if not re.search(r"<word", body):
            blank.append(index)
        xs = [float(v) for v in re.findall(r'xMax="([\d.]+)"', body)]
        if xs and max(xs) > float(width) - 18:
            overflow.append((index, round(max(xs), 1)))
    return {"pages": len(pages), "blank": blank, "overflow": overflow}


def main() -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".tex", delete=False, encoding="utf-8") as handle:
        handle.write(HEADER)
        header_path = Path(handle.name)

    failures = 0
    for doc in DOCUMENTS:
        build(doc, header_path)
        report = inspect(doc["output"])
        status = "OK" if not report["blank"] and not report["overflow"] else "CHECK"
        if status != "OK":
            failures += 1
        print(
            f"[{status}] {doc['output'].relative_to(ROOT)}  "
            f"pages={report['pages']}  blank={report['blank'] or 'none'}  "
            f"overflow={report['overflow'] or 'none'}  sha256={sha256(doc['output'])[:16]}"
        )
    header_path.unlink(missing_ok=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
