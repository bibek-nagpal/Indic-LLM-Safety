# Manuscript source

`acl_latex.tex` is the canonical current manuscript. `draft2_aug.tex` is a compatibility wrapper that inputs the canonical source, so the two filenames cannot silently diverge.

The repository uses the ACL style files stored in this directory and BibTeX references from `references.bib`. A reproducible local build with Tectonic 0.17.0 is:

```powershell
Set-Location C:\Prahlada\paper
..\tmp\tectonic\tectonic.exe -C -k --keep-logs -o build acl_latex.tex
```

`-C` makes the verified final build offline by using only already-cached TeX resources. The `build/` directory and ordinary LaTeX intermediates are ignored by Git. The reviewed deliverable is copied to `output/pdf/IndicAlignProbe_revision_v2.pdf`.

Before release, run the evidence audit from the repository root:

```powershell
.\.analysis-venv\Scripts\python.exe paper\audit_paper_consistency.py
```
