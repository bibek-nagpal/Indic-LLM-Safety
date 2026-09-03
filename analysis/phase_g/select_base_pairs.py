"""Freeze the Phase G base-pair selection.

Deterministic and outcome-independent. Selection depends only on the frozen
bank identity (pair_id, category, strategy) and a fixed seed string, hashed
with SHA-256. It never reads a target score, flip, response length, Phase D
judgment, or Phase E human label, and the script does not open those files.

Balanced by construction: N/12 pairs from each of the 12 category x strategy
cells. N must therefore be divisible by 12.

    python analysis/phase_g/select_base_pairs.py --n 96
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/pairs.jsonl"
BANK_MANIFEST = ROOT / "frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/manifest.json"
OUT = ROOT / "analysis/phase_g"
SELECTION_SEED = "phase-g-unusual-english-control-v1|20260901"
EXPECTED_BANK_SHA256 = "35bfbc1d09e78b77c24d62bbf41783cc9b297dd25f1bba3fe6062d53dc2028ed"
CATEGORIES = ("violence", "intoxication", "gambling", "sexual_violence")
STRATEGIES = ("SymbolicMasking", "ScenarioNesting", "RolePrompting")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rank_key(pair_id: str, category: str, strategy: str) -> str:
    """Outcome-independent deterministic rank. Identity and seed only."""
    return hashlib.sha256(
        f"{SELECTION_SEED}\x1f{pair_id}\x1f{category}\x1f{strategy}".encode()
    ).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=96, help="total base pairs; must divide by 12")
    parser.add_argument("--out-prefix", default=None)
    args = parser.parse_args()
    if args.n % 12:
        raise SystemExit(f"--n must be divisible by 12 for a balanced design, got {args.n}")
    per_cell = args.n // 12

    manifest = json.loads(BANK_MANIFEST.read_text(encoding="utf-8"))
    if manifest["bank_sha256"] != EXPECTED_BANK_SHA256:
        raise SystemExit("frozen bank hash does not match the expected value")

    cells: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    n_rows = 0
    with BANK.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            candidate = row["candidate"]
            key = (candidate["category"], candidate["strategy"])
            cells[key].append((rank_key(row["pair_id"], *key), row["pair_id"]))
            n_rows += 1
    if n_rows != 504:
        raise SystemExit(f"expected 504 bank rows, found {n_rows}")
    expected_cells = {(c, s) for c in CATEGORIES for s in STRATEGIES}
    if set(cells) != expected_cells or any(len(v) != 42 for v in cells.values()):
        raise SystemExit("frozen bank is not the expected 12 x 42 grid")

    selected: list[dict[str, str]] = []
    for category in CATEGORIES:
        for strategy in STRATEGIES:
            ranked = sorted(cells[(category, strategy)])
            for _, pair_id in ranked[:per_cell]:
                selected.append(
                    {"pair_id": pair_id, "category": category, "strategy": strategy}
                )
    selected.sort(key=lambda row: row["pair_id"])
    if len(selected) != args.n or len({r["pair_id"] for r in selected}) != args.n:
        raise SystemExit("selection is not the expected size or contains duplicates")

    prefix = args.out_prefix or f"selection_n{args.n}"
    csv_path = OUT / f"{prefix}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("pair_id", "category", "strategy"))
        writer.writeheader()
        writer.writerows(selected)

    payload = {
        "schema_version": 1,
        "phase": "G",
        "purpose": "unusual-English out-of-distribution control",
        "n_base_pairs": args.n,
        "per_cell": per_cell,
        "selection_seed": SELECTION_SEED,
        "selection_rule": "SHA-256 rank of (seed, pair_id, category, strategy); "
                          "lowest per_cell ranks in each of 12 cells",
        "selection_is_outcome_independent": True,
        "inputs_read": ["frozen bank pairs.jsonl (identity fields only)", "frozen bank manifest.json"],
        "inputs_deliberately_not_read": [
            "target scores", "flips", "response lengths",
            "Phase D cross-judge scores", "Phase E human labels",
        ],
        "frozen_bank_id": manifest["bank_id"],
        "frozen_bank_sha256": manifest["bank_sha256"],
        "frozen_bank_pairs_file_sha256": sha256_file(BANK),
        "selection_csv": csv_path.name,
        "selection_csv_sha256": sha256_file(csv_path),
        "cell_counts": {f"{c}::{s}": per_cell for c in CATEGORIES for s in STRATEGIES},
        "selected_pair_ids": [r["pair_id"] for r in selected],
    }
    json_path = OUT / f"{prefix}_MANIFEST.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8", newline="\n")
    print(json.dumps({
        "n": args.n, "per_cell": per_cell,
        "selection_csv": str(csv_path.relative_to(ROOT)),
        "manifest": str(json_path.relative_to(ROOT)),
        "selection_sha256": payload["selection_csv_sha256"][:16],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
