"""Analyze completed Human A/B workbooks against each other and frozen judges."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np


def confusion(left: Iterable[int], right: Iterable[int]) -> np.ndarray:
    matrix = np.zeros((4, 4), dtype=int)
    for a, b in zip(left, right, strict=True):
        matrix[int(a), int(b)] += 1
    return matrix


def agreement(left: list[int], right: list[int]) -> dict[str, float | int]:
    if len(left) != len(right) or not left:
        raise ValueError("agreement vectors must be non-empty and equal length")
    a, b = np.asarray(left, dtype=int), np.asarray(right, dtype=int)
    matrix = confusion(a, b)
    total = int(matrix.sum())
    exact = float(np.trace(matrix) / total)
    adjacent = float(np.mean(np.abs(a - b) <= 1))
    row = matrix.sum(axis=1) / total
    col = matrix.sum(axis=0) / total
    expected_exact = float(np.dot(row, col))
    kappa = float((exact - expected_exact) / (1 - expected_exact)) if expected_exact < 1 else 1.0
    weights = np.fromfunction(lambda i, j: ((i - j) / 3.0) ** 2, (4, 4))
    observed_disagreement = float((weights * (matrix / total)).sum())
    expected = np.outer(row, col)
    expected_disagreement = float((weights * expected).sum())
    qwk = 1.0 - observed_disagreement / expected_disagreement if expected_disagreement else 1.0
    return {
        "n": total,
        "exact_agreement": exact,
        "adjacent_agreement": adjacent,
        "unweighted_kappa": kappa,
        "quadratic_weighted_kappa": qwk,
    }


def read_workbook_scores(path: Path) -> dict[int, int]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is required; run `uv sync --group analysis`") from exc
    workbook = load_workbook(path, read_only=True, data_only=True)
    if "Annotation" not in workbook.sheetnames:
        raise ValueError(f"{path}: missing Annotation sheet")
    sheet = workbook["Annotation"]
    scores: dict[int, int] = {}
    for item, _prompt, _response, score in sheet.iter_rows(min_row=2, max_col=4, values_only=True):
        if item is None:
            continue
        if score is None:
            raise ValueError(f"{path}: item {item} has no score")
        if isinstance(score, bool) or int(score) != score or int(score) not in range(4):
            raise ValueError(f"{path}: item {item} has invalid score {score!r}")
        scores[int(item)] = int(score)
    if len(scores) != 180 or set(scores) != set(range(1, 181)):
        raise ValueError(f"{path}: expected exactly items 1..180, found {len(scores)}")
    return scores


def write_matrix(path: Path, matrix: np.ndarray, left: str, right: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([f"{left}\\{right}", 0, 1, 2, 3])
        for score, row in enumerate(matrix.tolist()):
            writer.writerow([score, *row])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-a", type=Path, required=True)
    parser.add_argument("--human-b", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-dir", type=Path, default=Path("human_validation/results"))
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    human_scores = {
        "Human A": read_workbook_scores(args.human_a.resolve()),
        "Human B": read_workbook_scores(args.human_b.resolve()),
    }
    with (package_dir / "private/annotator_order_key.csv").open(encoding="utf-8") as handle:
        order_rows = list(csv.DictReader(handle))
    with (package_dir / "private/reconciliation_key.csv").open(encoding="utf-8") as handle:
        reconciliation = {row["reconciliation_id"]: row for row in csv.DictReader(handle)}

    labels: dict[str, dict[str, int]] = {"Human A": {}, "Human B": {}}
    for row in order_rows:
        name = f"Human {row['annotator']}"
        rid = row["reconciliation_id"]
        labels[name][rid] = human_scores[name][int(row["item_number"])]
    if set(labels["Human A"]) != set(labels["Human B"]) or len(labels["Human A"]) != 180:
        raise RuntimeError("annotator reconciliation grids differ")

    ids = sorted(labels["Human A"])
    comparisons: dict[str, dict[str, float | int]] = {}
    vectors: dict[str, list[int]] = {
        "Human A": [labels["Human A"][rid] for rid in ids],
        "Human B": [labels["Human B"][rid] for rid in ids],
        "Gemini": [int(reconciliation[rid]["gemini_score"]) for rid in ids],
        "GPT-5 Mini": [int(reconciliation[rid]["gpt5mini_score"]) for rid in ids],
    }
    pairs = (
        ("Human A", "Human B"),
        ("Human A", "Gemini"),
        ("Human A", "GPT-5 Mini"),
        ("Human B", "Gemini"),
        ("Human B", "GPT-5 Mini"),
    )
    for left, right in pairs:
        key = f"{left} vs {right}"
        comparisons[key] = agreement(vectors[left], vectors[right])
        write_matrix(output_dir / f"confusion_{left.lower().replace(' ', '_')}_vs_{right.lower().replace(' ', '_').replace('-', '')}.csv", confusion(vectors[left], vectors[right]), left, right)

    disagreements = []
    for rid in ids:
        if labels["Human A"][rid] != labels["Human B"][rid]:
            disagreements.append(
                {
                    "reconciliation_id": rid,
                    "human_a_score": labels["Human A"][rid],
                    "human_b_score": labels["Human B"][rid],
                }
            )
    with (output_dir / "human_disagreements.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("reconciliation_id", "human_a_score", "human_b_score"))
        writer.writeheader()
        writer.writerows(disagreements)

    result = {
        "schema_version": 1,
        "items": 180,
        "unresolved_human_human_disagreements": len(disagreements),
        "comparisons": comparisons,
        "score_distributions": {name: dict(sorted(Counter(values).items())) for name, values in vectors.items()},
    }
    (output_dir / "human_validation_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = ["# Human-validation results", "", f"Items scored by each annotator: **{len(ids)}**", "", "| Comparison | Exact | Adjacent | Unweighted kappa | Quadratic-weighted kappa |", "|---|---:|---:|---:|---:|"]
    for name, values in comparisons.items():
        lines.append(
            f"| {name} | {values['exact_agreement']:.2%} | {values['adjacent_agreement']:.2%} | "
            f"{values['unweighted_kappa']:.3f} | {values['quadratic_weighted_kappa']:.3f} |"
        )
    lines += ["", f"Unresolved Human A/B disagreements: **{len(disagreements)}**.", "", "Automated scores were joined only after human labels were read and reconciled."]
    (output_dir / "human_validation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"items": 180, "comparisons": len(comparisons), "disagreements": len(disagreements)}))


if __name__ == "__main__":
    main()
