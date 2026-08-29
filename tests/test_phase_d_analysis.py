from __future__ import annotations

import math
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np


ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "analysis"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

from analyze_phase_d import agreement_metrics, confusion_matrix, regime_assessment, weighted_kappa
from qc_final import RUN_ID


REPO = Path(__file__).resolve().parents[1]


def _write_mock_scores(
    path: Path,
    jobs: list[dict[str, object]],
    score_lookup: dict[tuple[str, str, str], int],
) -> None:
    payload = []
    for job in jobs:
        key = (str(job["pair_id"]), str(job["target_model"]), str(job["language"]))
        payload.append(
            json.dumps(
                {
                    **job,
                    "score": score_lookup[key],
                    "logical_consistency_ok": True,
                    "parse_error": None,
                },
                sort_keys=True,
            )
        )
    path.write_text("\n".join(payload) + "\n", encoding="utf-8")


def test_confusion_matrix_orientation() -> None:
    reference = np.array([0, 0, 1, 2, 3])
    comparison = np.array([0, 1, 1, 3, 2])
    matrix = confusion_matrix(reference, comparison)
    assert matrix.sum() == 5
    assert matrix[0, 0] == 1
    assert matrix[0, 1] == 1
    assert matrix[2, 3] == 1
    assert matrix[3, 2] == 1


def test_perfect_agreement_metrics() -> None:
    scores = np.array([0, 1, 2, 3] * 5)
    metrics, matrix = agreement_metrics(scores, scores)
    assert metrics["exact_agreement"] == 1.0
    assert metrics["adjacent_agreement"] == 1.0
    assert metrics["unweighted_kappa"] == 1.0
    assert metrics["quadratic_weighted_kappa"] == 1.0
    assert weighted_kappa(matrix, quadratic=False) == 1.0


def test_adjacent_agreement_is_distinct_from_exact() -> None:
    left = np.array([0, 1, 2, 3])
    right = np.array([1, 2, 3, 2])
    metrics, _ = agreement_metrics(left, right)
    assert metrics["exact_agreement"] == 0.0
    assert metrics["adjacent_agreement"] == 1.0
    assert not math.isnan(metrics["quadratic_weighted_kappa"])


def test_predeclared_three_regime_assessment() -> None:
    import pandas as pd

    frame = pd.DataFrame(
        [
            {
                "model": "qwen/qwen3-30b-a3b-instruct-2507",
                "model_display": "Qwen3-30B-A3B",
                "en_refusal_rate": 0.66,
                "rh_refusal_rate": 0.23,
                "refusal_gap_pp": 43.0,
            },
            {
                "model": "openai/gpt-oss-20b",
                "model_display": "GPT-OSS-20B",
                "en_refusal_rate": 0.87,
                "rh_refusal_rate": 0.82,
                "refusal_gap_pp": 5.0,
            },
            {
                "model": "nvidia/nemotron-3-nano-30b-a3b",
                "model_display": "Nemotron-3-Nano",
                "en_refusal_rate": 0.62,
                "rh_refusal_rate": 0.64,
                "refusal_gap_pp": -2.0,
            },
        ]
    )
    result = regime_assessment(frame)
    assert result["ordering_matches"] is True
    assert result["all_regimes_match"] is True


def test_complete_phase_d_analysis_with_score_only_mock_outputs(tmp_path: Path) -> None:
    snapshot = REPO / "frozen_final_2026_08_29"
    primary_path = snapshot / "run" / RUN_ID / "scores.jsonl"
    sample_path = REPO / "analysis" / "phase_d_preparation" / "stratified_180_pair_model_sample.csv"
    primary = [json.loads(line) for line in primary_path.read_text(encoding="utf-8").splitlines()]
    score_lookup = {
        (row["pair_id"], row["model"], row["language"]): row["score"] for row in primary
    }
    with sample_path.open("r", encoding="utf-8", newline="") as stream:
        sample_pairs = {
            (row["pair_id"], row["target_model"]) for row in csv.DictReader(stream)
        }

    gpt_path = tmp_path / "gpt_scores.jsonl"
    claude_path = tmp_path / "claude_scores.jsonl"
    gpt_jobs = [
        json.loads(line)
        for line in (REPO / "analysis" / "phase_d_preparation" / "gpt5mini_full_jobs.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    claude_jobs = [
        json.loads(line)
        for line in (REPO / "analysis" / "phase_d_preparation" / "claude_sample_jobs.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert {
        (row["pair_id"], row["target_model"]) for row in claude_jobs
    } == sample_pairs
    _write_mock_scores(gpt_path, gpt_jobs, score_lookup)
    _write_mock_scores(claude_path, claude_jobs, score_lookup)
    output = tmp_path / "results"
    subprocess.run(
        [
            sys.executable,
            str(REPO / "analysis" / "analyze_phase_d.py"),
            "--snapshot",
            str(snapshot),
            "--gpt-scores",
            str(gpt_path),
            "--gpt-plan",
            str(REPO / "analysis" / "phase_d_preparation" / "gpt5mini_full_plan.json"),
            "--claude-scores",
            str(claude_path),
            "--sample",
            str(sample_path),
            "--output",
            str(output),
            "--bootstrap-resamples",
            "100",
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )

    with (output / "agreement_overall.csv").open("r", encoding="utf-8", newline="") as stream:
        agreement = list(csv.DictReader(stream))
    assert len(agreement) == 5
    assert all(float(row["exact_agreement"]) == 1.0 for row in agreement)
    assert all(float(row["quadratic_weighted_kappa"]) == 1.0 for row in agreement)
    pure = next(row for row in agreement if row["scope"] == "gemini_only")
    assert int(pure["n"]) == 3022

    regimes = json.loads((output / "regime_robustness.json").read_text(encoding="utf-8"))
    assert regimes["qualitative_three_regime_survives_judge_replacement"] is True

    manifest = json.loads((output / "PHASE_D_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["phase"] == "D"
    assert len(manifest["files"]) >= 10
    for record in manifest["files"]:
        artifact = output / record["path"]
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        assert digest == record["sha256"]


def test_complete_phase_d_gpt_only_batch_analysis(tmp_path: Path) -> None:
    snapshot = REPO / "frozen_final_2026_08_29"
    primary_path = snapshot / "run" / RUN_ID / "scores.jsonl"
    primary = [json.loads(line) for line in primary_path.read_text(encoding="utf-8").splitlines()]
    score_lookup = {
        (row["pair_id"], row["model"], row["language"]): row["score"] for row in primary
    }
    jobs_path = REPO / "analysis" / "phase_d_budget_design" / "gpt5mini_batch_full_jobs.jsonl"
    plan_path = REPO / "analysis" / "phase_d_budget_design" / "gpt5mini_batch_full_plan.json"
    jobs = [json.loads(line) for line in jobs_path.read_text(encoding="utf-8").splitlines()]
    gpt_path = tmp_path / "gpt_batch_scores.jsonl"
    _write_mock_scores(gpt_path, jobs, score_lookup)
    output = tmp_path / "gpt_only_results"
    subprocess.run(
        [
            sys.executable,
            str(REPO / "analysis" / "analyze_phase_d.py"),
            "--snapshot",
            str(snapshot),
            "--gpt-scores",
            str(gpt_path),
            "--gpt-plan",
            str(plan_path),
            "--output",
            str(output),
            "--bootstrap-resamples",
            "20",
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )

    with (output / "agreement_overall.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        agreement = list(csv.DictReader(stream))
    assert len(agreement) == 2
    assert agreement[0]["comparison"] == "Primary pipeline vs GPT-5 Mini"
    assert agreement[1]["comparison"] == "Gemini-only vs GPT-5 Mini"
    summary = (output / "phase_d_summary.md").read_text(encoding="utf-8")
    assert "Stratified three-judge sample" not in summary
