"""Create a non-overwriting archival copy of the certified bank and target run."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_BANK_ID = "revision_v2_3_1_final_504_dedup"
DEFAULT_RUN_ID = "revision_v2_targets_final"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def copy_tree_exact(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(source)
    shutil.copytree(source, destination, copy_function=shutil.copy2)


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("frozen_final_2026_08_29"))
    parser.add_argument("--bank-id", default=DEFAULT_BANK_ID)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args()

    repo = args.repo.resolve()
    output = args.output if args.output.is_absolute() else repo / args.output
    if output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing frozen snapshot: {output}"
        )

    bank_source = repo / "probe_banks" / args.bank_id
    run_source = repo / "runs" / args.run_id
    bank_destination = output / "bank" / args.bank_id
    run_destination = output / "run" / args.run_id
    copy_tree_exact(bank_source, bank_destination)
    copy_tree_exact(run_source, run_destination)

    accounting_summary = json.loads(
        (run_source / "api_accounting_summary.json").read_text(encoding="utf-8")
    )
    accounting_relative = Path(accounting_summary["path"])
    accounting_source = repo / accounting_relative
    if not accounting_source.is_file():
        raise FileNotFoundError(accounting_source)
    accounting_destination = output / "run" / "accounting" / accounting_source.name
    accounting_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(accounting_source, accounting_destination)

    code_metadata = {
        "git_commit": git_value(repo, "rev-parse", "HEAD"),
        "git_tree": git_value(repo, "rev-parse", "HEAD^{tree}"),
        "git_commit_subject": git_value(repo, "log", "-1", "--format=%s"),
        "package_version": "0.1.0",
        "run_id": args.run_id,
        "bank_id": args.bank_id,
        "relevant_code_sha256": {
            str(path.relative_to(repo)).replace("\\", "/"): sha256_file(path)
            for path in sorted((repo / "src" / "jailbreak_hermes").glob("*.py"))
        },
        "configuration_sha256": {
            str(path.relative_to(repo)).replace("\\", "/"): sha256_file(path)
            for path in sorted((repo / "configs").rglob("*.yaml"))
        },
    }
    (output / "CODE_VERSION.json").write_text(
        json.dumps(code_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    bank_manifest = json.loads(
        (bank_destination / "manifest.json").read_text(encoding="utf-8")
    )
    run_manifest = json.loads(
        (run_destination / "run_manifest.json").read_text(encoding="utf-8")
    )
    file_rows = []
    for path in iter_files(output):
        relative = str(path.relative_to(output)).replace("\\", "/")
        file_rows.append(
            {"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        )
    freeze_manifest = {
        "schema_version": 1,
        "snapshot_id": output.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_git_commit": code_metadata["git_commit"],
        "bank_id": bank_manifest["bank_id"],
        "canonical_bank_sha256": bank_manifest["bank_sha256"],
        "run_id": run_manifest["run_id"],
        "source_paths": {
            "bank": f"probe_banks/{args.bank_id}",
            "run": f"runs/{args.run_id}",
            "accounting": str(accounting_relative).replace("\\", "/"),
        },
        "files": file_rows,
    }
    (output / "FREEZE_MANIFEST.json").write_text(
        json.dumps(freeze_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "README.md").write_text(
        "# Frozen final V2 snapshot\n\n"
        "This directory is a local, immutable archival copy of the certified 504-pair "
        "bank and the completed 1,512-job target run. The `bank/` and `run/` trees "
        "contain private harmful-research material and are intentionally ignored by Git. "
        "`FREEZE_MANIFEST.json` records byte-level hashes without reproducing prompts or "
        "responses. The creator refuses to overwrite an existing snapshot.\n",
        encoding="utf-8",
    )

    print(f"Created {output}")
    print(f"Archived files: {len(file_rows)}")
    print(f"Canonical bank hash: {bank_manifest['bank_sha256']}")


if __name__ == "__main__":
    main()
