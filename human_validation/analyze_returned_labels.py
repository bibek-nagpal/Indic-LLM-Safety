"""Frozen Phase E analysis: returned human labels versus each other and the automated judges.

Prespecified on 2026-08-31, before any label exists. The resampling and cluster
unit is the pair-model job, because a job contributes two correlated response
items (English and Romanized Hindi).

Primary results use pre-adjudication labels exactly as returned. Adjudicated
results, if an adjudication file is supplied, are reported separately and are
always secondary. See ADJUDICATION_PROTOCOL.md.

Usage:
    python human_validation/analyze_returned_labels.py \
        --human-a .../Human_A_annotations.xlsx \
        --human-b .../Human_B_annotations.xlsx \
        [--adjudicated .../adjudication.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

SEED = 20260831
N_BOOT = 10_000
EXPECTED_ITEMS = 360
MODEL_NAMES = {
    "qwen/qwen3-30b-a3b-instruct-2507": "Qwen3-30B-A3B",
    "openai/gpt-oss-20b": "GPT-OSS-20B",
    "nvidia/nemotron-3-nano-30b-a3b": "Nemotron-3-Nano",
}
LANGUAGE_NAMES = {"en": "English", "rh": "Hinglish/RH"}


# --------------------------------------------------------------------------
# statistics


def confusion(left: Sequence[int], right: Sequence[int]) -> np.ndarray:
    matrix = np.zeros((4, 4), dtype=int)
    for a, b in zip(left, right, strict=True):
        matrix[int(a), int(b)] += 1
    return matrix


def _kappa_from_matrix(matrix: np.ndarray, weights: np.ndarray) -> float:
    total = matrix.sum()
    if total == 0:
        return float("nan")
    observed = matrix / total
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0))
    observed_disagreement = float((weights * observed).sum())
    expected_disagreement = float((weights * expected).sum())
    if expected_disagreement == 0:
        return 1.0
    return 1.0 - observed_disagreement / expected_disagreement


UNWEIGHTED = 1.0 - np.eye(4)
QUADRATIC = np.fromfunction(lambda i, j: ((i - j) / 3.0) ** 2, (4, 4))


def agreement_statistics(left: Sequence[int], right: Sequence[int]) -> dict[str, float]:
    a, b = np.asarray(left, dtype=int), np.asarray(right, dtype=int)
    if a.size == 0:
        return {
            "n": 0, "exact_agreement": float("nan"), "adjacent_agreement": float("nan"),
            "unweighted_kappa": float("nan"), "quadratic_weighted_kappa": float("nan"),
        }
    matrix = confusion(a, b)
    return {
        "n": int(a.size),
        "exact_agreement": float((a == b).mean()),
        "adjacent_agreement": float((np.abs(a - b) <= 1).mean()),
        "unweighted_kappa": _kappa_from_matrix(matrix, UNWEIGHTED),
        "quadratic_weighted_kappa": _kappa_from_matrix(matrix, QUADRATIC),
    }


def cluster_bootstrap_ci(
    values: Sequence[float],
    clusters: Sequence[str],
    statistic,
    rng: np.random.Generator,
    n_boot: int = N_BOOT,
) -> tuple[float, float]:
    """Percentile CI resampling whole pair-model jobs."""
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, cluster in enumerate(clusters):
        grouped[cluster].append(index)
    keys = sorted(grouped)
    if len(keys) < 2:
        return float("nan"), float("nan")
    index_lists = [np.asarray(grouped[key]) for key in keys]
    array = np.asarray(values, dtype=float)
    draws = rng.integers(0, len(keys), size=(n_boot, len(keys)))
    estimates = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        picked = np.concatenate([index_lists[i] for i in draws[b]])
        estimates[b] = statistic(array[picked])
    low, high = np.nanpercentile(estimates, [2.5, 97.5])
    return float(low), float(high)


def agreement_with_ci(
    left: Sequence[int],
    right: Sequence[int],
    clusters: Sequence[str],
    rng: np.random.Generator,
) -> dict[str, Any]:
    stats = agreement_statistics(left, right)
    if stats["n"] >= 2:
        a, b = np.asarray(left, dtype=int), np.asarray(right, dtype=int)
        exact_low, exact_high = cluster_bootstrap_ci(
            (a == b).astype(float), clusters, np.mean, rng
        )
        adj_low, adj_high = cluster_bootstrap_ci(
            (np.abs(a - b) <= 1).astype(float), clusters, np.mean, rng
        )
        stats["exact_agreement_ci"] = [exact_low, exact_high]
        stats["adjacent_agreement_ci"] = [adj_low, adj_high]
    return stats


def severity_metrics(reference: Sequence[int], predicted: Sequence[int]) -> dict[str, float]:
    """Treat score 3 as the positive class: how well does an automated judge
    recover the human 'fully actionable' label, and vice versa."""
    ref = np.asarray(reference, dtype=int) == 3
    pred = np.asarray(predicted, dtype=int) == 3
    true_positive = int((ref & pred).sum())
    false_positive = int((~ref & pred).sum())
    false_negative = int((ref & ~pred).sum())
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else float("nan")
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else float("nan")
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision == precision and recall == recall and (precision + recall) > 0
        else float("nan")
    )
    return {
        "n_human_score3": int(ref.sum()),
        "n_judge_score3": int(pred.sum()),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision_judge_vs_human": precision,
        "recall_judge_vs_human": recall,
        "f1": f1,
    }


# --------------------------------------------------------------------------
# I/O


def read_workbook_scores(path: Path) -> tuple[dict[int, int | None], dict[int, dict[str, bool]], dict[str, str]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("openpyxl is required; run `uv sync --group analysis`") from exc
    workbook = load_workbook(path, read_only=True, data_only=True)
    if "Annotation" not in workbook.sheetnames:
        raise ValueError(f"{path}: missing Annotation sheet")
    sheet = workbook["Annotation"]
    scores: dict[int, int | None] = {}
    flags: dict[int, dict[str, bool]] = {}
    for row in sheet.iter_rows(min_row=2, max_col=6, values_only=True):
        item, _prompt, _response, score, borderline, unreadable = (list(row) + [None] * 6)[:6]
        if item is None:
            continue
        item = int(item)
        truthy = lambda v: bool(v) and str(v).strip().lower() not in {"", "0", "false", "no"}
        flags[item] = {"borderline": truthy(borderline), "unreadable": truthy(unreadable)}
        if score is None or str(score).strip() == "":
            scores[item] = None
            continue
        if isinstance(score, bool) or int(score) != score or int(score) not in range(4):
            raise ValueError(f"{path}: item {item} has invalid score {score!r}")
        scores[item] = int(score)
    if set(scores) != set(range(1, EXPECTED_ITEMS + 1)):
        raise ValueError(f"{path}: expected items 1..{EXPECTED_ITEMS}, found {len(scores)}")

    metadata: dict[str, str] = {}
    if "Annotator" in workbook.sheetnames:
        for label, value in workbook["Annotator"].iter_rows(min_row=2, max_col=2, values_only=True):
            if label:
                metadata[str(label)] = "" if value is None else str(value)
    return scores, flags, metadata


def write_matrix(path: Path, matrix: np.ndarray, left: str, right: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([f"{left}\\{right}", 0, 1, 2, 3])
        for score, row in enumerate(matrix.tolist()):
            writer.writerow([score, *row])


# --------------------------------------------------------------------------
# main


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-a", type=Path, required=True)
    parser.add_argument("--human-b", type=Path, required=True)
    parser.add_argument(
        "--adjudicated",
        type=Path,
        default=None,
        help="optional CSV with columns reconciliation_id,adjudicated_score (secondary analysis only)",
    )
    parser.add_argument("--package-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-dir", type=Path, default=Path("human_validation/results"))
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    raw = {}
    flags = {}
    annotator_metadata = {}
    for name, path in (("Human A", args.human_a), ("Human B", args.human_b)):
        raw[name], flags[name], annotator_metadata[name] = read_workbook_scores(path.resolve())

    with (package_dir / "private/annotator_order_key.csv").open(encoding="utf-8") as handle:
        order_rows = list(csv.DictReader(handle))
    with (package_dir / "private/reconciliation_key.csv").open(encoding="utf-8") as handle:
        reconciliation = {row["reconciliation_id"]: row for row in csv.DictReader(handle)}

    labels: dict[str, dict[str, int | None]] = {"Human A": {}, "Human B": {}}
    item_flags: dict[str, dict[str, dict[str, bool]]] = {"Human A": {}, "Human B": {}}
    for row in order_rows:
        name = f"Human {row['annotator']}"
        rid = row["reconciliation_id"]
        item = int(row["item_number"])
        labels[name][rid] = raw[name][item]
        item_flags[name][rid] = flags[name][item]
    if set(labels["Human A"]) != set(labels["Human B"]):
        raise RuntimeError("annotator reconciliation grids differ")
    ids = sorted(labels["Human A"])
    if len(ids) != EXPECTED_ITEMS:
        raise RuntimeError(f"expected {EXPECTED_ITEMS} reconciled items, found {len(ids)}")

    # ---- missing / flagged data -----------------------------------------
    missing = {
        name: sorted(rid for rid in ids if labels[name][rid] is None) for name in labels
    }
    data_quality = {
        "items": len(ids),
        "unique_pair_model_jobs": len({reconciliation[rid]["pair_id"] for rid in ids}),
        "per_annotator": {
            name: {
                "unscored": len(missing[name]),
                "borderline_flagged": sum(1 for rid in ids if item_flags[name][rid]["borderline"]),
                "cannot_read_flagged": sum(1 for rid in ids if item_flags[name][rid]["unreadable"]),
                "cannot_read_by_language": dict(
                    Counter(
                        reconciliation[rid]["language"]
                        for rid in ids
                        if item_flags[name][rid]["unreadable"]
                    )
                ),
            }
            for name in labels
        },
        "language_background": annotator_metadata,
    }
    usable = [rid for rid in ids if labels["Human A"][rid] is not None and labels["Human B"][rid] is not None]
    data_quality["items_usable_for_human_human"] = len(usable)

    # ---- vectors ---------------------------------------------------------
    def vectors(subset: Sequence[str]) -> dict[str, list[int]]:
        return {
            "Human A": [labels["Human A"][rid] for rid in subset],
            "Human B": [labels["Human B"][rid] for rid in subset],
            "Primary pipeline": [int(reconciliation[rid]["gemini_score"]) for rid in subset],
            "GPT-5 Mini": [int(reconciliation[rid]["gpt5mini_score"]) for rid in subset],
        }

    def clusters_for(subset: Sequence[str]) -> list[str]:
        return [
            f"{reconciliation[rid]['pair_id']}|{reconciliation[rid]['target_model']}"
            for rid in subset
        ]

    PAIRINGS = (
        ("Human A", "Human B"),
        ("Human A", "Primary pipeline"),
        ("Human B", "Primary pipeline"),
        ("Human A", "GPT-5 Mini"),
        ("Human B", "GPT-5 Mini"),
    )

    def analyse(subset: Sequence[str]) -> dict[str, Any]:
        if not subset:
            return {}
        vecs = vectors(subset)
        cl = clusters_for(subset)
        return {
            f"{left} vs {right}": agreement_with_ci(vecs[left], vecs[right], cl, rng)
            for left, right in PAIRINGS
        }

    def subset_where(**criteria: str) -> list[str]:
        out = []
        for rid in usable:
            row = reconciliation[rid]
            if all(row[key] == value for key, value in criteria.items()):
                out.append(rid)
        return out

    results: dict[str, Any] = {
        "schema_version": 2,
        "analysis": "pre-adjudication (primary)",
        "cluster_unit": "pair-model job",
        "bootstrap_resamples": N_BOOT,
        "seed": SEED,
        "data_quality": data_quality,
        "overall": analyse(usable),
        "by_model": {
            MODEL_NAMES[model]: analyse(subset_where(target_model=model))
            for model in MODEL_NAMES
        },
        "by_language": {
            LANGUAGE_NAMES[language]: analyse(subset_where(language=language))
            for language in LANGUAGE_NAMES
        },
        "by_model_language": {
            f"{MODEL_NAMES[model]} \u00b7 {LANGUAGE_NAMES[language]}": analyse(
                subset_where(target_model=model, language=language)
            )
            for model in MODEL_NAMES
            for language in LANGUAGE_NAMES
        },
        "score_distributions": {
            name: dict(sorted(Counter(values).items()))
            for name, values in vectors(usable).items()
        },
    }

    # ---- human-derived non-assistance gaps -------------------------------
    gap_rows: dict[str, Any] = {}
    for model, display in MODEL_NAMES.items():
        entry: dict[str, Any] = {}
        for scorer in ("Human A", "Human B", "Primary pipeline", "GPT-5 Mini"):
            per_job: dict[str, dict[str, int]] = defaultdict(dict)
            for rid in usable:
                row = reconciliation[rid]
                if row["target_model"] != model:
                    continue
                value = (
                    labels[scorer][rid]
                    if scorer.startswith("Human")
                    else int(row["gemini_score" if scorer == "Primary pipeline" else "gpt5mini_score"])
                )
                per_job[row["pair_id"]][row["language"]] = value
            complete = [v for v in per_job.values() if "en" in v and "rh" in v]
            if len(complete) < 2:
                entry[scorer] = {"n_jobs": len(complete)}
                continue
            differences = np.asarray(
                [float(v["en"] == 0) - float(v["rh"] == 0) for v in complete]
            )
            keys = [str(i) for i in range(len(differences))]
            low, high = cluster_bootstrap_ci(differences, keys, np.mean, rng)
            entry[scorer] = {
                "n_jobs": len(complete),
                "non_assistance_gap_pp": round(100 * float(differences.mean()), 4),
                "ci_low_pp": round(100 * low, 4),
                "ci_high_pp": round(100 * high, 4),
            }
        gap_rows[display] = entry
    results["human_derived_non_assistance_gaps"] = gap_rows

    # ---- critical-severity agreement -------------------------------------
    vecs_all = vectors(usable)
    results["critical_severity"] = {
        f"{human} vs {judge}": severity_metrics(vecs_all[human], vecs_all[judge])
        for human in ("Human A", "Human B")
        for judge in ("Primary pipeline", "GPT-5 Mini")
    }
    results["critical_severity"]["Human A vs Human B"] = severity_metrics(
        vecs_all["Human A"], vecs_all["Human B"]
    )

    # ---- confusion matrices ---------------------------------------------
    matrices_dir = output_dir / "confusion_matrices"
    matrices_dir.mkdir(parents=True, exist_ok=True)
    slug = lambda s: s.lower().replace(" ", "_").replace("-", "")
    for left, right in PAIRINGS:
        write_matrix(
            matrices_dir / f"confusion_{slug(left)}_vs_{slug(right)}.csv",
            confusion(vecs_all[left], vecs_all[right]),
            left,
            right,
        )

    # ---- disagreement register ------------------------------------------
    disagreements = []
    for rid in usable:
        a, b = labels["Human A"][rid], labels["Human B"][rid]
        if a != b:
            disagreements.append(
                {
                    "reconciliation_id": rid,
                    "human_a_score": a,
                    "human_b_score": b,
                    "absolute_difference": abs(a - b),
                    "routed_to_adjudication": abs(a - b) >= 2,
                }
            )
    with (output_dir / "human_disagreements.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "reconciliation_id", "human_a_score", "human_b_score",
                "absolute_difference", "routed_to_adjudication",
            ),
        )
        writer.writeheader()
        writer.writerows(disagreements)
    results["disagreements"] = {
        "total": len(disagreements),
        "adjacent_only": sum(1 for d in disagreements if d["absolute_difference"] == 1),
        "routed_to_adjudication": sum(1 for d in disagreements if d["routed_to_adjudication"]),
    }

    # ---- secondary: adjudicated ------------------------------------------
    if args.adjudicated is not None:
        with args.adjudicated.resolve().open(encoding="utf-8") as handle:
            adjudicated = {
                row["reconciliation_id"]: int(row["adjudicated_score"])
                for row in csv.DictReader(handle)
            }
        required = {d["reconciliation_id"] for d in disagreements if d["routed_to_adjudication"]}
        if not required <= set(adjudicated):
            raise RuntimeError(
                f"adjudication file is missing {len(required - set(adjudicated))} routed items"
            )
        consensus = {
            rid: adjudicated.get(rid, labels["Human A"][rid])
            if rid in required
            else labels["Human A"][rid]
            for rid in usable
        }
        vecs = vectors(usable)
        vecs["Adjudicated human"] = [consensus[rid] for rid in usable]
        cl = clusters_for(usable)
        results["secondary_adjudicated"] = {
            "note": "secondary; pre-adjudication labels above remain primary",
            "adjudicated_items": len(required),
            "adjudicated_score_distribution": dict(
                sorted(Counter(adjudicated[rid] for rid in required).items())
            ),
            "comparisons": {
                f"Adjudicated human vs {judge}": agreement_with_ci(
                    vecs["Adjudicated human"], vecs[judge], cl, rng
                )
                for judge in ("Primary pipeline", "GPT-5 Mini")
            },
        }

    (output_dir / "human_validation_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, default=float), encoding="utf-8"
    )

    # ---- readable summary ------------------------------------------------
    def fmt(entry: dict[str, Any]) -> str:
        if not entry or entry.get("n", 0) == 0:
            return "| n/a | | | | |"
        ci = entry.get("exact_agreement_ci", [float("nan")] * 2)
        return (
            f"| {entry['n']} | {entry['exact_agreement']:.1%} "
            f"[{ci[0]:.1%}, {ci[1]:.1%}] | {entry['adjacent_agreement']:.1%} | "
            f"{entry['unweighted_kappa']:.3f} | {entry['quadratic_weighted_kappa']:.3f} |"
        )

    lines = [
        "# Phase E human-validation results (pre-adjudication, primary)",
        "",
        f"Items reconciled: **{len(ids)}** across **{data_quality['unique_pair_model_jobs']}** "
        f"pair-model jobs. Usable for human-human comparison: **{len(usable)}**.",
        "Confidence intervals are percentile intervals from "
        f"{N_BOOT:,} bootstrap resamples of pair-model jobs.",
        "",
        "## Overall",
        "",
        "| Comparison | n | Exact [95% CI] | Adjacent | Kappa | Quadratic kappa |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, entry in results["overall"].items():
        lines.append(f"| {key} " + fmt(entry))
    lines += ["", "## By target model and language", "",
              "| Stratum | Comparison | n | Exact [95% CI] | Adjacent | Kappa | Quadratic kappa |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for stratum, block in results["by_model_language"].items():
        for key, entry in block.items():
            lines.append(f"| {stratum} | {key} " + fmt(entry))
    lines += ["", "## Human-derived non-assistance gaps", "",
              "| Model | Scorer | Jobs | Gap pp [95% CI] |", "|---|---|---:|---:|"]
    for model, entry in results["human_derived_non_assistance_gaps"].items():
        for scorer, values in entry.items():
            if "non_assistance_gap_pp" in values:
                lines.append(
                    f"| {model} | {scorer} | {values['n_jobs']} | "
                    f"{values['non_assistance_gap_pp']:.2f} "
                    f"[{values['ci_low_pp']:.2f}, {values['ci_high_pp']:.2f}] |"
                )
    lines += ["", "## Critical severity (score 3 as the positive class)", "",
              "| Comparison | Human 3s | Judge 3s | Precision | Recall |", "|---|---:|---:|---:|---:|"]
    for key, values in results["critical_severity"].items():
        lines.append(
            f"| {key} | {values['n_human_score3']} | {values['n_judge_score3']} | "
            f"{values['precision_judge_vs_human']:.3f} | {values['recall_judge_vs_human']:.3f} |"
        )
    lines += [
        "",
        "## Data quality",
        "",
        f"- Unscored items: " + ", ".join(
            f"{name} {values['unscored']}" for name, values in data_quality["per_annotator"].items()
        ),
        "- Borderline flags: " + ", ".join(
            f"{name} {values['borderline_flagged']}" for name, values in data_quality["per_annotator"].items()
        ),
        "- Cannot-read flags: " + ", ".join(
            f"{name} {values['cannot_read_flagged']} {values['cannot_read_by_language']}"
            for name, values in data_quality["per_annotator"].items()
        ),
        f"- Human-human disagreements: {results['disagreements']['total']} "
        f"({results['disagreements']['adjacent_only']} adjacent, "
        f"{results['disagreements']['routed_to_adjudication']} routed to adjudication)",
        "",
        "Automated scores were joined only after the human labels were read and reconciled.",
    ]
    if "secondary_adjudicated" in results:
        lines += ["", "## Secondary: adjudicated labels", "",
                  f"Adjudicated items: {results['secondary_adjudicated']['adjudicated_items']}.",
                  "", "| Comparison | n | Exact [95% CI] | Adjacent | Kappa | Quadratic kappa |",
                  "|---|---:|---:|---:|---:|---:|"]
        for key, entry in results["secondary_adjudicated"]["comparisons"].items():
            lines.append(f"| {key} " + fmt(entry))
    (output_dir / "human_validation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "items": len(ids),
        "usable": len(usable),
        "jobs": data_quality["unique_pair_model_jobs"],
        "disagreements": results["disagreements"]["total"],
    }))


if __name__ == "__main__":
    main()
