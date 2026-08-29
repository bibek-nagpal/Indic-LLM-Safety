#!/usr/bin/env python3
"""Compare cross-auditor verdicts and nine-axis judgments on the same prompt set.

Example
-------
python scripts/analyze_cross_auditors.py ^
  --input "DeepSeek Flash=runs/cross_auditor/deepseek_v4_flash_full.jsonl" ^
  --input "DeepSeek Pro=runs/cross_auditor/deepseek_v4_pro_full.jsonl" ^
  --input "Claude Sonnet 4.6=runs/cross_auditor/claude_sonnet_4_6_full.jsonl" ^
  --output-dir runs/cross_auditor/comparison_50 ^
  --expected-items 50

You may add another model later by appending another --input:
  --input "GPT Mini=runs/cross_auditor/gpt_mini_full.jsonl"

The script:
  * uses Gemini from each record's original_equivalence as the baseline auditor;
  * keeps the last successful record for each ID and model;
  * compares every model pair only on IDs successfully available for both;
  * reports verdict agreement, Cohen's kappa, confusion counts, and nine-axis
    agreement/disagreement percentages;
  * does not make API calls and does not modify source JSONL files.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

AXES = (
    "same_harmful_intent",
    "same_scenario",
    "same_info_level_requested",
    "same_attack_strategy",
    "same_cultural_specificity",
    "same_target_group",
    "same_ambiguity_level",
    "language_fidelity",
    "strategy_faithfully_used",
)

BASELINE_LABEL = "Gemini 2.5 Flash"


def parse_input_spec(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            f"Invalid --input {spec!r}. Use LABEL=PATH."
        )
    label, raw_path = spec.split("=", 1)
    label = label.strip()
    path = Path(raw_path.strip())
    if not label:
        raise argparse.ArgumentTypeError("Model label cannot be empty.")
    if not raw_path.strip():
        raise argparse.ArgumentTypeError("Input path cannot be empty.")
    return label, path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Input JSONL not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
            if not isinstance(obj, dict):
                raise RuntimeError(f"Non-object JSON in {path}:{line_number}")
            obj["_source_line"] = line_number
            rows.append(obj)
    return rows


def successful_by_id(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Last successful record for each ID wins."""
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        rid = str(row.get("id") or "")
        if rid and not row.get("error"):
            out[rid] = row
    return out


def errors_from_rows(label: str, path: Path, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("error"):
            out.append(
                {
                    "model": label,
                    "source_file": str(path),
                    "source_line": row.get("_source_line", ""),
                    "id": row.get("id", ""),
                    "error": row.get("error", ""),
                }
            )
    return out


def get_axis(audit: Any, axis: str) -> bool | None:
    if not isinstance(audit, dict):
        return None
    axes = audit.get("axes")
    if not isinstance(axes, dict):
        return None
    entry = axes.get(axis)
    if not isinstance(entry, dict) or "equal" not in entry:
        return None
    return bool(entry["equal"])


def get_verdict(audit: Any) -> bool | None:
    if not isinstance(audit, dict) or "accepted" not in audit:
        return None
    return bool(audit["accepted"])


def safe_div(num: float, den: float) -> float | None:
    return num / den if den else None


def kappa_binary(a: list[int], b: list[int]) -> float | None:
    if not a or len(a) != len(b):
        return None
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa = sum(a) / n
    pb = sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if math.isclose(1 - pe, 0.0):
        return None
    return (po - pe) / (1 - pe)


def pair_names(labels: list[str]) -> Iterable[tuple[str, str]]:
    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            yield left, right


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fmt_float(value: float | None) -> str | float:
    return "" if value is None else value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        metavar="LABEL=PATH",
        help="Cross-auditor JSONL. Repeat once per model.",
    )
    parser.add_argument(
        "--output-dir",
        default="runs/cross_auditor/comparison",
        help="Directory for generated analysis files.",
    )
    parser.add_argument(
        "--expected-items",
        type=int,
        default=50,
        help="Expected successful IDs per model for coverage warnings.",
    )
    args = parser.parse_args()

    parsed_inputs = [parse_input_spec(spec) for spec in args.input]
    labels = [label for label, _ in parsed_inputs]
    if len(labels) != len(set(labels)):
        duplicates = [x for x, n in Counter(labels).items() if n > 1]
        raise SystemExit(f"Duplicate model labels: {duplicates}")
    if BASELINE_LABEL in labels:
        raise SystemExit(
            f"Do not use reserved label {BASELINE_LABEL!r}; Gemini is loaded from original_equivalence."
        )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # model_records[label][id] = row
    model_records: dict[str, dict[str, dict[str, Any]]] = {}
    source_paths: dict[str, Path] = {}
    all_error_rows: list[dict[str, Any]] = []

    for label, path in parsed_inputs:
        raw_rows = read_jsonl(path)
        model_records[label] = successful_by_id(raw_rows)
        source_paths[label] = path
        all_error_rows.extend(errors_from_rows(label, path, raw_rows))

    # Build baseline Gemini records from all successful model rows.
    # Verify that duplicate versions of the same ID agree.
    gemini_by_id: dict[str, dict[str, Any]] = {}
    metadata_by_id: dict[str, dict[str, Any]] = {}
    provenance_conflicts: list[str] = []

    for label in labels:
        for rid, row in model_records[label].items():
            old = row.get("original_equivalence")
            if not isinstance(old, dict):
                raise RuntimeError(f"{label} id={rid} lacks original_equivalence")
            if rid in gemini_by_id:
                old_verdict = get_verdict(gemini_by_id[rid])
                new_verdict = get_verdict(old)
                if old_verdict != new_verdict:
                    provenance_conflicts.append(rid)
            else:
                gemini_by_id[rid] = old

            metadata_by_id.setdefault(
                rid,
                {
                    "id": rid,
                    "category": row.get("category", ""),
                    "strategy": row.get("strategy", ""),
                    "run_name": row.get("run_name", ""),
                    "target_model_batch": row.get("target_model_batch", ""),
                    "trace_name": row.get("trace_name", ""),
                    "trace_line": row.get("trace_line", ""),
                },
            )

    if provenance_conflicts:
        raise RuntimeError(
            "Gemini verdict conflicts across model files for IDs: "
            + ", ".join(provenance_conflicts[:10])
        )

    # Pseudo-record map for baseline. Each value stores only an audit object.
    audits: dict[str, dict[str, dict[str, Any]]] = {
        BASELINE_LABEL: {rid: {"audit": audit} for rid, audit in gemini_by_id.items()}
    }
    for label in labels:
        audits[label] = {
            rid: {"audit": row["independent_equivalence"]}
            for rid, row in model_records[label].items()
            if isinstance(row.get("independent_equivalence"), dict)
        }

    ordered_labels = [BASELINE_LABEL] + labels
    all_ids = sorted(set().union(*(set(records) for records in audits.values())))

    # ------------------------------------------------------------------
    # Master verdict table: one row per ID, one verdict column per model.
    # ------------------------------------------------------------------
    master_rows: list[dict[str, Any]] = []
    for rid in all_ids:
        row = dict(metadata_by_id.get(rid, {"id": rid}))
        for label in ordered_labels:
            record = audits[label].get(rid)
            verdict = get_verdict(record["audit"]) if record else None
            row[label] = (
                "Accept" if verdict is True else "Reject" if verdict is False else ""
            )
        master_rows.append(row)

    master_fields = [
        "id",
        "category",
        "strategy",
        "run_name",
        "target_model_batch",
        "trace_name",
        "trace_line",
        *ordered_labels,
    ]
    write_csv(out_dir / "master_verdict_table.csv", master_fields, master_rows)

    # ------------------------------------------------------------------
    # Coverage report.
    # ------------------------------------------------------------------
    coverage_rows: list[dict[str, Any]] = []
    for label in ordered_labels:
        n = len(audits[label])
        coverage_rows.append(
            {
                "model": label,
                "successful_unique": n,
                "expected_items": args.expected_items,
                "missing_from_expected": max(args.expected_items - n, 0),
                "coverage_percent": safe_div(n * 100, args.expected_items),
                "source_file": (
                    "original_equivalence embedded in cross-audit rows"
                    if label == BASELINE_LABEL
                    else str(source_paths[label])
                ),
            }
        )
    write_csv(
        out_dir / "model_coverage.csv",
        [
            "model",
            "successful_unique",
            "expected_items",
            "missing_from_expected",
            "coverage_percent",
            "source_file",
        ],
        coverage_rows,
    )

    write_csv(
        out_dir / "error_attempts.csv",
        ["model", "source_file", "source_line", "id", "error"],
        all_error_rows,
    )

    # ------------------------------------------------------------------
    # Pairwise verdict comparisons.
    # ------------------------------------------------------------------
    verdict_rows: list[dict[str, Any]] = []
    confusion_rows: list[dict[str, Any]] = []
    verdict_disagreements: list[dict[str, Any]] = []

    agreement_matrix: dict[str, dict[str, Any]] = {
        label: {other: "" for other in ordered_labels} for label in ordered_labels
    }
    kappa_matrix: dict[str, dict[str, Any]] = {
        label: {other: "" for other in ordered_labels} for label in ordered_labels
    }

    for label in ordered_labels:
        agreement_matrix[label][label] = 1.0
        kappa_matrix[label][label] = 1.0

    for left, right in pair_names(ordered_labels):
        common_ids = sorted(set(audits[left]) & set(audits[right]))
        pairs: list[tuple[str, bool, bool]] = []
        for rid in common_ids:
            lv = get_verdict(audits[left][rid]["audit"])
            rv = get_verdict(audits[right][rid]["audit"])
            if lv is not None and rv is not None:
                pairs.append((rid, lv, rv))

        y_left = [int(lv) for _, lv, _ in pairs]
        y_right = [int(rv) for _, _, rv in pairs]
        n = len(pairs)
        agree_n = sum(lv == rv for _, lv, rv in pairs)
        left_accept_right_reject = sum(lv and not rv for _, lv, rv in pairs)
        left_reject_right_accept = sum((not lv) and rv for _, lv, rv in pairs)
        both_reject = sum((not lv) and (not rv) for _, lv, rv in pairs)
        both_accept = sum(lv and rv for _, lv, rv in pairs)
        agreement = safe_div(agree_n, n)
        kappa = kappa_binary(y_left, y_right)

        verdict_rows.append(
            {
                "model_a": left,
                "model_b": right,
                "n_compared": n,
                "agreement_count": agree_n,
                "disagreement_count": n - agree_n,
                "agreement_percent": None if agreement is None else agreement * 100,
                "cohen_kappa": fmt_float(kappa),
                "model_a_acceptance_percent": (
                    None if not n else 100 * sum(y_left) / n
                ),
                "model_b_acceptance_percent": (
                    None if not n else 100 * sum(y_right) / n
                ),
            }
        )
        confusion_rows.append(
            {
                "model_a": left,
                "model_b": right,
                "n_compared": n,
                "both_reject": both_reject,
                "a_reject_b_accept": left_reject_right_accept,
                "a_accept_b_reject": left_accept_right_reject,
                "both_accept": both_accept,
            }
        )

        agreement_matrix[left][right] = agreement_matrix[right][left] = (
            "" if agreement is None else agreement
        )
        kappa_matrix[left][right] = kappa_matrix[right][left] = (
            "" if kappa is None else kappa
        )

        for rid, lv, rv in pairs:
            if lv != rv:
                meta = metadata_by_id.get(rid, {})
                verdict_disagreements.append(
                    {
                        "model_a": left,
                        "model_b": right,
                        "id": rid,
                        "category": meta.get("category", ""),
                        "strategy": meta.get("strategy", ""),
                        "model_a_verdict": "Accept" if lv else "Reject",
                        "model_b_verdict": "Accept" if rv else "Reject",
                    }
                )

    write_csv(
        out_dir / "pairwise_verdict_agreement.csv",
        [
            "model_a",
            "model_b",
            "n_compared",
            "agreement_count",
            "disagreement_count",
            "agreement_percent",
            "cohen_kappa",
            "model_a_acceptance_percent",
            "model_b_acceptance_percent",
        ],
        verdict_rows,
    )
    write_csv(
        out_dir / "pairwise_confusion_counts.csv",
        [
            "model_a",
            "model_b",
            "n_compared",
            "both_reject",
            "a_reject_b_accept",
            "a_accept_b_reject",
            "both_accept",
        ],
        confusion_rows,
    )
    write_csv(
        out_dir / "pairwise_verdict_disagreements.csv",
        [
            "model_a",
            "model_b",
            "id",
            "category",
            "strategy",
            "model_a_verdict",
            "model_b_verdict",
        ],
        verdict_disagreements,
    )

    matrix_fields = ["model", *ordered_labels]
    write_csv(
        out_dir / "verdict_agreement_matrix.csv",
        matrix_fields,
        [
            {"model": label, **agreement_matrix[label]}
            for label in ordered_labels
        ],
    )
    write_csv(
        out_dir / "verdict_kappa_matrix.csv",
        matrix_fields,
        [
            {"model": label, **kappa_matrix[label]}
            for label in ordered_labels
        ],
    )

    # ------------------------------------------------------------------
    # Nine-axis pairwise agreement/disagreement.
    # ------------------------------------------------------------------
    axis_rows: list[dict[str, Any]] = []
    axis_case_disagreements: list[dict[str, Any]] = []

    for left, right in pair_names(ordered_labels):
        common_ids = sorted(set(audits[left]) & set(audits[right]))
        for axis in AXES:
            compared: list[tuple[str, bool, bool]] = []
            missing_left = 0
            missing_right = 0
            for rid in common_ids:
                lv = get_axis(audits[left][rid]["audit"], axis)
                rv = get_axis(audits[right][rid]["audit"], axis)
                if lv is None:
                    missing_left += 1
                if rv is None:
                    missing_right += 1
                if lv is not None and rv is not None:
                    compared.append((rid, lv, rv))

            n = len(compared)
            agree_n = sum(lv == rv for _, lv, rv in compared)
            disagree_n = n - agree_n
            y_left = [int(lv) for _, lv, _ in compared]
            y_right = [int(rv) for _, _, rv in compared]
            axis_kappa = kappa_binary(y_left, y_right)

            axis_rows.append(
                {
                    "model_a": left,
                    "model_b": right,
                    "axis": axis,
                    "n_compared": n,
                    "agreement_count": agree_n,
                    "disagreement_count": disagree_n,
                    "agreement_percent": None if not n else 100 * agree_n / n,
                    "disagreement_percent": None if not n else 100 * disagree_n / n,
                    "cohen_kappa": fmt_float(axis_kappa),
                    "model_a_true_percent": (
                        None if not n else 100 * sum(y_left) / n
                    ),
                    "model_b_true_percent": (
                        None if not n else 100 * sum(y_right) / n
                    ),
                    "missing_model_a": missing_left,
                    "missing_model_b": missing_right,
                }
            )

            for rid, lv, rv in compared:
                if lv != rv:
                    meta = metadata_by_id.get(rid, {})
                    axis_case_disagreements.append(
                        {
                            "model_a": left,
                            "model_b": right,
                            "axis": axis,
                            "id": rid,
                            "category": meta.get("category", ""),
                            "strategy": meta.get("strategy", ""),
                            "model_a_value": lv,
                            "model_b_value": rv,
                        }
                    )

    write_csv(
        out_dir / "pairwise_dimension_agreement.csv",
        [
            "model_a",
            "model_b",
            "axis",
            "n_compared",
            "agreement_count",
            "disagreement_count",
            "agreement_percent",
            "disagreement_percent",
            "cohen_kappa",
            "model_a_true_percent",
            "model_b_true_percent",
            "missing_model_a",
            "missing_model_b",
        ],
        axis_rows,
    )
    write_csv(
        out_dir / "pairwise_dimension_disagreement_cases.csv",
        [
            "model_a",
            "model_b",
            "axis",
            "id",
            "category",
            "strategy",
            "model_a_value",
            "model_b_value",
        ],
        axis_case_disagreements,
    )

    # ------------------------------------------------------------------
    # Compact JSON summary.
    # ------------------------------------------------------------------
    summary = {
        "models": ordered_labels,
        "expected_items": args.expected_items,
        "coverage": coverage_rows,
        "error_attempt_count": len(all_error_rows),
        "master_id_count": len(all_ids),
        "outputs": {
            "master_verdict_table": str(out_dir / "master_verdict_table.csv"),
            "model_coverage": str(out_dir / "model_coverage.csv"),
            "errors": str(out_dir / "error_attempts.csv"),
            "pairwise_verdict_agreement": str(out_dir / "pairwise_verdict_agreement.csv"),
            "verdict_agreement_matrix": str(out_dir / "verdict_agreement_matrix.csv"),
            "verdict_kappa_matrix": str(out_dir / "verdict_kappa_matrix.csv"),
            "pairwise_confusion_counts": str(out_dir / "pairwise_confusion_counts.csv"),
            "pairwise_verdict_disagreements": str(out_dir / "pairwise_verdict_disagreements.csv"),
            "pairwise_dimension_agreement": str(out_dir / "pairwise_dimension_agreement.csv"),
            "pairwise_dimension_disagreement_cases": str(
                out_dir / "pairwise_dimension_disagreement_cases.csv"
            ),
        },
    }
    (out_dir / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Models compared: {', '.join(ordered_labels)}")
    print(f"Unique IDs across all successful records: {len(all_ids)}")
    for row in coverage_rows:
        print(
            f"  {row['model']}: {row['successful_unique']}/"
            f"{row['expected_items']} successful"
        )
    print(f"Recorded error attempts: {len(all_error_rows)}")
    print(f"Wrote analysis to: {out_dir}")
    for name, path in summary["outputs"].items():
        print(f"  {name}: {path}")
    print(f"  summary: {out_dir / 'analysis_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
