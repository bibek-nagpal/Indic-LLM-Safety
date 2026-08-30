"""Archive and integrity-check the completed Phase D standard cross-judge run."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from qc_final import load_jsonl, sha256_file


ARCHIVE_FILES = (
    "scores.jsonl",
    "standard_state.json",
    "standard_accounting.jsonl",
    "errors.jsonl",
    "smoke_verification.json",
    "progress.json",
    "completion_manifest.json",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def logical_consistency(row: dict[str, Any]) -> bool:
    expected = 0 if not row["gate_a"] else 1 if not row["gate_b"] else 2 if not row["gate_c"] else 3
    return row["score"] == expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("runs/cross_judge/gpt5mini_standard_budget"),
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path("analysis/phase_d_budget_design/gpt5mini_standard_fallback_plan.json"),
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("analysis/phase_d_run_archive"),
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("analysis/phase_d_results"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    run_dir = args.run_dir if args.run_dir.is_absolute() else repo / args.run_dir
    plan_path = args.plan if args.plan.is_absolute() else repo / args.plan
    archive = args.archive if args.archive.is_absolute() else repo / args.archive
    results = args.results if args.results.is_absolute() else repo / args.results
    plan = load_json(plan_path)
    jobs_path = repo / plan["jobs_manifest"]
    completion = load_json(run_dir / "completion_manifest.json")
    state = load_json(run_dir / "standard_state.json")
    scores = load_jsonl(run_dir / "scores.jsonl")
    jobs = load_jsonl(jobs_path)
    accounting = load_jsonl(run_dir / "standard_accounting.jsonl")
    errors = load_jsonl(run_dir / "errors.jsonl")

    checks: dict[str, bool] = {}
    checks["plan_jobs_hash"] = sha256_file(jobs_path) == plan["jobs_manifest_sha256"]
    checks["completion_plan_hash"] = sha256_file(plan_path) == completion["plan_sha256"]
    checks["completion_jobs_hash"] = sha256_file(jobs_path) == completion["jobs_manifest_sha256"]
    for filename, key in (
        ("scores.jsonl", "scores_sha256"),
        ("standard_state.json", "state_sha256"),
        ("standard_accounting.jsonl", "accounting_sha256"),
    ):
        checks[f"completion_{filename}_hash"] = sha256_file(run_dir / filename) == completion[key]

    jobs_by_id = {row["job_id"]: row for row in jobs}
    score_ids = [row.get("job_id") for row in scores]
    checks["expected_job_count"] = len(jobs) == int(plan["expected_jobs"]) == 1944
    checks["score_count"] = len(scores) == 1944
    checks["unique_score_ids"] = len(score_ids) == len(set(score_ids))
    checks["score_grid_exact"] = set(score_ids) == set(jobs_by_id)
    identity_fields = (
        "pair_id",
        "target_model",
        "language",
        "category",
        "strategy",
        "prompt_sha256",
        "response_sha256",
        "rubric_sha256",
        "judge_messages_sha256",
        "standard_request_sha256",
        "judge_model",
    )
    checks["score_identity_hashes"] = all(
        all(row.get(field) == jobs_by_id[row["job_id"]].get(field) for field in identity_fields)
        for row in scores
    )
    checks["score_schema_and_logic"] = all(
        type(row.get("score")) is int
        and row["score"] in {0, 1, 2, 3}
        and row.get("logical_consistency_ok") is True
        and row.get("parse_error") is None
        and logical_consistency(row)
        for row in scores
    )

    attempts = state["attempts"]
    attempt_ids = [row.get("attempt_id") for row in attempts]
    checks["unique_attempt_ids"] = len(attempt_ids) == len(set(attempt_ids))
    checks["no_active_submissions"] = not any(row.get("status") == "submitting" for row in attempts)
    checks["all_error_jobs_resolved"] = all(row.get("job_id") in set(score_ids) for row in errors)
    checks["target_inference_calls_zero"] = completion.get("target_inference_calls") == 0

    known_actual = sum(
        float(row["actual_cost_usd"])
        for row in attempts
        if row.get("actual_cost_usd") is not None
    )
    ambiguous_reserved = sum(
        float(row["reserved_max_cost_usd"])
        for row in attempts
        if row.get("actual_cost_usd") is None
    )
    committed = known_actual + ambiguous_reserved
    accounting_cost = sum(float(row.get("cost_usd") or 0.0) for row in accounting)
    checks["known_cost_matches_completion"] = abs(
        known_actual - float(completion["known_actual_cost_usd"])
    ) < 1e-10
    checks["commitment_matches_completion"] = abs(
        committed - float(completion["budget_committed_usd"])
    ) < 1e-10
    checks["accounting_reconciles_known_cost"] = abs(accounting_cost - known_actual) < 1e-10
    checks["hard_budget_respected"] = committed <= float(plan["hard_budget_usd"])
    checks["completion_count"] = completion.get("successful_jobs") == 1944

    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"Phase D integrity failed: {failed}")

    archive.mkdir(parents=True, exist_ok=True)
    for filename in ARCHIVE_FILES:
        shutil.copy2(run_dir / filename, archive / filename)
    shutil.copy2(plan_path, archive / plan_path.name)
    shutil.copy2(jobs_path, archive / jobs_path.name)

    status_counts = Counter(str(row.get("status")) for row in attempts)
    error_job_ids = {row.get("job_id") for row in errors}
    report = {
        "schema_version": 1,
        "overall_status": "PASS",
        "checks": checks,
        "planned_jobs": len(jobs),
        "valid_scores": len(scores),
        "remaining_jobs": len(jobs) - len(scores),
        "attempts": len(attempts),
        "attempt_status_counts": dict(sorted(status_counts.items())),
        "error_records": len(errors),
        "error_jobs": len(error_job_ids),
        "error_jobs_without_final_score": len(error_job_ids - set(score_ids)),
        "known_actual_cost_usd": known_actual,
        "ambiguous_reserved_cost_usd": ambiguous_reserved,
        "budget_committed_usd": committed,
        "hard_budget_usd": float(plan["hard_budget_usd"]),
        "budget_remaining_usd": float(plan["hard_budget_usd"]) - committed,
        "target_inference_calls": 0,
        "scores_sha256": sha256_file(run_dir / "scores.jsonl"),
        "plan_sha256": sha256_file(plan_path),
        "jobs_manifest_sha256": sha256_file(jobs_path),
    }
    results.mkdir(parents=True, exist_ok=True)
    (results / "integrity_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown = [
        "# Phase D Integrity Report",
        "",
        "**Overall status: PASS**",
        "",
        f"- Planned and valid judgments: {len(scores):,}/{len(jobs):,}",
        f"- Remaining or unresolved score jobs: {len(jobs) - len(scores)}",
        f"- Total attempts: {len(attempts):,}",
        f"- Error records: {len(errors):,}; error jobs without a final valid score: 0",
        f"- Known billed cost: ${known_actual:.8f}",
        f"- Ambiguous reserved cost: ${ambiguous_reserved:.8f}",
        f"- Total committed: ${committed:.8f} of ${float(plan['hard_budget_usd']):.2f}",
        "- Target-model inference calls: 0",
        "- Score, plan, job-manifest, state, and accounting hashes: verified",
        "",
        "Attempt status counts:",
        "",
    ]
    markdown.extend(f"- `{name}`: {count}" for name, count in sorted(status_counts.items()))
    (results / "integrity_report.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")

    archive_manifest_path = archive / "RUN_ARCHIVE_MANIFEST.json"
    archive_files = []
    for path in sorted(item for item in archive.iterdir() if item.is_file()):
        if path == archive_manifest_path:
            continue
        archive_files.append(
            {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        )
    archive_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "phase": "D1 completed GPT-5 Mini cross-judge subset",
                "finalizer_script_sha256": sha256_file(Path(__file__).resolve()),
                "integrity_report_sha256": sha256_file(results / "integrity_report.json"),
                "files": archive_files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Phase D integrity PASS: {len(scores)}/{len(jobs)} scores; "
        f"committed=${committed:.8f}"
    )


if __name__ == "__main__":
    main()
