"""Select the frozen 24-pair Phase G U-control development cohort.

Implements the cohort rule in U_CONTROL_PROTOCOL_PROPOSED.md section 2:

    rank ascending SHA-256 of  seed + U+001F + pair_id + U+001F + category
                               + U+001F + strategy
    seed = phase-g-u-article-clip-pilot-v1|20260903
    two per each of 12 category x strategy cells, drawn from the 504-pair bank,
    excluding every pair_id in selection_n120_MANIFEST.json

Outcome-independent: reads bank identity metadata only. It does not open target
scores, flips, response lengths, Phase D judgments or Phase E labels, and it
never mutates the frozen 96/120 selection.

    python analysis/phase_g/select_development_pairs.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/pairs.jsonl"
BANK_MANIFEST = ROOT / "frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/manifest.json"
LADDER = ROOT / "analysis/phase_g/selection_n120_MANIFEST.json"
OUT = ROOT / "analysis/phase_g/u_control_development"

SEED = "phase-g-u-article-clip-pilot-v1|20260903"
US = "\x1f"
PER_CELL = 2
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
    return hashlib.sha256(
        (SEED + US + pair_id + US + category + US + strategy).encode("utf-8")
    ).hexdigest()


def main() -> int:
    manifest = json.loads(BANK_MANIFEST.read_text(encoding="utf-8"))
    if manifest["bank_sha256"] != EXPECTED_BANK_SHA256:
        raise SystemExit("frozen bank hash mismatch")
    ladder = set(json.loads(LADDER.read_text(encoding="utf-8"))["selected_pair_ids"])
    if len(ladder) != 120:
        raise SystemExit(f"expected a 120-pair ladder, found {len(ladder)}")

    cells: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    rows = 0
    with BANK.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            candidate = record["candidate"]
            pair_id = record["pair_id"]
            rows += 1
            if pair_id in ladder:
                continue
            key = (candidate["category"], candidate["strategy"])
            cells[key].append(
                (rank_key(pair_id, *key), pair_id, candidate["english_prompt"])
            )
    if rows != 504:
        raise SystemExit(f"expected 504 bank rows, found {rows}")

    selected: list[dict[str, str]] = []
    for category in CATEGORIES:
        for strategy in STRATEGIES:
            pool = sorted(cells[(category, strategy)], key=lambda t: (t[0], t[1]))
            if len(pool) < PER_CELL:
                raise SystemExit(f"cell {category}/{strategy} has only {len(pool)} eligible pairs")
            for index, (_, pair_id, english) in enumerate(pool[:PER_CELL], start=1):
                selected.append({
                    "development_pair_id": f"DEV-{category}-{strategy}-{index:02d}",
                    "pair_id": pair_id,
                    "category": category,
                    "strategy": strategy,
                    "source_E": english,
                    "source_E_sha256": hashlib.sha256(english.encode("utf-8")).hexdigest(),
                })

    if len(selected) != 24:
        raise SystemExit(f"expected 24 development pairs, found {len(selected)}")
    ids = {row["pair_id"] for row in selected}
    if len(ids) != 24:
        raise SystemExit("development pair_ids are not unique")
    if ids & ladder:
        raise SystemExit("development cohort overlaps the frozen N=120 ladder")
    texts = {row["source_E"] for row in selected}
    if len(texts) != 24:
        raise SystemExit("development source texts are not exact-text disjoint")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "development_cohort.json").write_text(
        json.dumps(selected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    index_path = OUT / "development_cohort_index.csv"
    with index_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("development_pair_id", "pair_id", "category", "strategy", "source_E_sha256"),
        )
        writer.writeheader()
        for row in selected:
            writer.writerow({k: row[k] for k in writer.fieldnames})

    payload = {
        "schema_version": 1,
        "phase": "G",
        "cohort": "u_control_development",
        "purpose": "five-family U-control candidate generation (development only)",
        "selection_seed": SEED,
        "selection_rule": "ascending SHA-256 of seed+US+pair_id+US+category+US+strategy; "
                          "lowest 2 ranks per category x strategy cell; pair_id lexical tiebreak",
        "per_cell": PER_CELL,
        "n_development_pairs": len(selected),
        "excluded_cohorts": ["selection_n120_MANIFEST.json (complete Phase G ladder)"],
        "disjoint_from_n120_ladder": True,
        "selection_is_outcome_independent": True,
        "inputs_read": ["frozen bank pairs.jsonl", "frozen bank manifest.json",
                        "selection_n120_MANIFEST.json (identifiers only)"],
        "inputs_deliberately_not_read": ["target scores", "flips", "response lengths",
                                          "Phase D cross-judge scores", "Phase E human labels"],
        "frozen_bank_id": manifest["bank_id"],
        "frozen_bank_sha256": manifest["bank_sha256"],
        "frozen_bank_pairs_file_sha256": sha256_file(BANK),
        "cell_counts": {f"{c}::{s}": PER_CELL for c in CATEGORIES for s in STRATEGIES},
        "development_pair_ids": [row["pair_id"] for row in selected],
        "cohort_index_sha256": sha256_file(index_path),
    }
    (OUT / "DEVELOPMENT_COHORT_MANIFEST.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"n": len(selected), "cells": len(payload["cell_counts"]),
                      "overlap_with_ladder": 0,
                      "manifest": "analysis/phase_g/u_control_development/DEVELOPMENT_COHORT_MANIFEST.json"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
