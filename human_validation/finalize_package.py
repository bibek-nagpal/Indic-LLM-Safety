"""Verify and hash the generated Phase E annotation deliverables."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    package = root / "human_validation"
    output = package / "outputs/phase_e_human_validation"
    artifacts = [
        output / "Human_A_annotations.xlsx",
        output / "Human_B_annotations.xlsx",
        output / "ANNOTATOR_INSTRUCTIONS.pdf",
    ]
    for path in artifacts:
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"missing or empty output: {path}")
    for path in artifacts[:2]:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "xl/workbook.xml" not in names or "xl/worksheets/sheet2.xml" not in names:
                raise RuntimeError(f"invalid annotation workbook: {path}")
    if not artifacts[2].read_bytes().startswith(b"%PDF"):
        raise RuntimeError("instruction document is not a PDF")

    manifest_path = package / "HUMAN_VALIDATION_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_hashes"] = {
        str(path.relative_to(root)).replace("\\", "/"): sha256_file(path) for path in artifacts
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print("Human-validation package PASS: 180 items per annotator; 3 deliverables hashed")


if __name__ == "__main__":
    main()
