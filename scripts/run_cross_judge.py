"""Validate or execute a hash-locked, resumable Phase D judge plan.

The default mode is validation-only and cannot make an API call. Paid execution
requires both ``--execute-paid-calls`` and ``--paid-approval-confirmed``.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return sha256_text(payload)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"non-object JSON at {path}:{line_number}")
            rows.append(row)
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def successful_trace_lookup(traces: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in traces:
        if row.get("event") != "model_pair":
            continue
        english = row.get("english") or {}
        rh = row.get("romanized_hindi") or {}
        if (
            not english.get("error")
            and not rh.get("error")
            and english.get("content") is not None
            and rh.get("content") is not None
        ):
            latest[(row["pair_id"], row["model"])] = row
    return latest


def git_commit(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def aggregate_accounting(accounting_dir: Path) -> dict[str, Any]:
    rows = []
    for path in sorted(accounting_dir.glob("api_calls_*.jsonl")):
        rows.extend(load_jsonl(path))
    by_model: dict[str, dict[str, Any]] = {}
    known_cost = 0.0
    for row in rows:
        model = row.get("requested_model", "unknown")
        bucket = by_model.setdefault(
            model,
            {
                "calls": 0,
                "successful": 0,
                "failed": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "known_cost_usd": 0.0,
            },
        )
        bucket["calls"] += 1
        bucket["successful"] += int(row.get("status") == "success")
        bucket["failed"] += int(row.get("status") != "success")
        bucket["prompt_tokens"] += int(row.get("prompt_tokens") or 0)
        bucket["completion_tokens"] += int(row.get("completion_tokens") or 0)
        if row.get("cost_usd") is not None:
            cost = float(row["cost_usd"])
            bucket["known_cost_usd"] += cost
            known_cost += cost
    return {
        "accounting_files": len(list(accounting_dir.glob("api_calls_*.jsonl"))),
        "calls": len(rows),
        "successful_calls": sum(row.get("status") == "success" for row in rows),
        "failed_calls": sum(row.get("status") != "success" for row in rows),
        "known_cost_usd": known_cost,
        "by_model": by_model,
    }


def load_existing_scores(
    path: Path, jobs_by_id: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows = load_jsonl(path)
    job_ids = [row.get("job_id") for row in rows]
    if len(job_ids) != len(set(job_ids)):
        raise RuntimeError("scores.jsonl contains duplicate job_id values")
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
        "judge_model",
    )
    for row in rows:
        job = jobs_by_id.get(row.get("job_id"))
        if job is None:
            raise RuntimeError("scores.jsonl contains a job outside this plan")
        changed = [field for field in identity_fields if row.get(field) != job.get(field)]
        if changed:
            raise RuntimeError(
                f"scores.jsonl identity mismatch for {row['job_id']}: {changed}"
            )
        score = row.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or score not in {0, 1, 2, 3}:
            raise RuntimeError(f"scores.jsonl has invalid score for {row['job_id']}")
        if row.get("logical_consistency_ok") is not True or row.get("parse_error") is not None:
            raise RuntimeError(f"scores.jsonl has an invalid judged result for {row['job_id']}")
    return {row["job_id"]: row for row in rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--execute-paid-calls", action="store_true")
    parser.add_argument("--paid-approval-confirmed", action="store_true")
    parser.add_argument("--max-jobs", type=int)
    parser.add_argument("--concurrency", type=int)
    args = parser.parse_args()

    repo = args.repo.resolve()
    plan_path = args.plan if args.plan.is_absolute() else repo / args.plan
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    jobs_path = repo / plan["jobs_manifest"]
    snapshot = repo / plan["input_snapshot"]
    output_dir = repo / plan["output_dir"]

    if sha256_file(jobs_path) != plan["jobs_manifest_sha256"]:
        raise RuntimeError("jobs manifest SHA-256 does not match plan")
    if sha256_file(snapshot / "FREEZE_MANIFEST.json") != plan["input_freeze_manifest_sha256"]:
        raise RuntimeError("input freeze manifest SHA-256 does not match plan")
    jobs = load_jsonl(jobs_path)
    if len(jobs) != plan["expected_jobs"]:
        raise RuntimeError(f"expected {plan['expected_jobs']} jobs, found {len(jobs)}")
    job_ids = [row["job_id"] for row in jobs]
    jobs_by_id = {row["job_id"]: row for row in jobs}
    if len(job_ids) != len(set(job_ids)):
        raise RuntimeError("jobs manifest contains duplicate job IDs")
    if any(row.get("judge_model") != plan["judge_model"] for row in jobs):
        raise RuntimeError("jobs manifest judge model does not match plan")

    os.environ["JBH_ACCOUNTING_ROOT"] = str(output_dir / "accounting")
    from jailbreak_hermes import category_spec, judge

    if sha256_text(judge.JUDGE_SYSTEM) != plan["rubric_sha256"]:
        raise RuntimeError("current judge rubric hash does not match the frozen plan")

    pairs = load_jsonl(snapshot / "bank" / plan["input_bank_id"] / "pairs.jsonl")
    pair_lookup = {row["pair_id"]: row for row in pairs}
    traces = successful_trace_lookup(
        load_jsonl(snapshot / "run" / plan["input_run_id"] / "traces.jsonl")
    )
    specs = {
        category: category_spec.load_by_id(category)
        for category in {row["category"] for row in jobs}
    }

    materialized: dict[str, dict[str, Any]] = {}
    for job in jobs:
        pair = pair_lookup.get(job["pair_id"])
        trace = traces.get((job["pair_id"], job["target_model"]))
        if pair is None or trace is None:
            raise RuntimeError(f"job {job['job_id']} cannot be resolved in frozen inputs")
        if job["language"] == "en":
            prompt = pair["candidate"]["english_prompt"]
            response = trace["english"]["content"]
        elif job["language"] == "rh":
            prompt = pair["candidate"]["romanized_hindi_prompt"]
            response = trace["romanized_hindi"]["content"]
        else:
            raise RuntimeError(f"unexpected language in job {job['job_id']}")
        if sha256_text(prompt) != job["prompt_sha256"]:
            raise RuntimeError(f"prompt hash mismatch for job {job['job_id']}")
        if sha256_text(response) != job["response_sha256"]:
            raise RuntimeError(f"response hash mismatch for job {job['job_id']}")
        messages = judge.build_judge_messages(
            job["category"],
            prompt,
            response,
            language=job["language"],
            gate_questions=specs[job["category"]].gate_questions,
        )
        if canonical_sha256(messages) != job["judge_messages_sha256"]:
            raise RuntimeError(f"judge-message hash mismatch for job {job['job_id']}")
        materialized[job["job_id"]] = {
            "job": job,
            "prompt": prompt,
            "response": response,
            "gate_questions": specs[job["category"]].gate_questions,
        }

    print(
        f"Validated plan: {plan['judge_model']} | {len(jobs)} response jobs | "
        f"target inference calls=0 | expected cost=${plan['cost_estimate_usd']['expected_uncached']:.2f}"
    )
    if not args.execute_paid_calls:
        print("Validation-only mode: 0 API calls")
        return
    if not args.paid_approval_confirmed:
        raise SystemExit(
            "Paid execution refused: add --paid-approval-confirmed only after explicit user approval"
        )
    if args.max_jobs is not None and args.max_jobs <= 0:
        raise ValueError("--max-jobs must be positive")
    concurrency = args.concurrency or int(plan["concurrency"])
    if concurrency < 1 or concurrency > 32:
        raise ValueError("concurrency must be between 1 and 32")

    load_dotenv(repo / ".env", override=False)
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY is unavailable; no calls made")

    output_dir.mkdir(parents=True, exist_ok=True)
    scores_path = output_dir / "scores.jsonl"
    errors_path = output_dir / "errors.jsonl"
    existing = load_existing_scores(scores_path, jobs_by_id)
    pending = [job for job in jobs if job["job_id"] not in existing]
    if args.max_jobs is not None:
        pending = pending[: args.max_jobs]

    run_manifest = {
        "schema_version": 1,
        "phase": "D",
        "plan": str(plan_path.relative_to(repo)).replace("\\", "/"),
        "plan_sha256": sha256_file(plan_path),
        "jobs_manifest_sha256": plan["jobs_manifest_sha256"],
        "judge_model": plan["judge_model"],
        "rubric_sha256": plan["rubric_sha256"],
        "temperature": plan["temperature"],
        "max_judge_tokens": plan["max_judge_tokens"],
        "strict_parse_retries": plan["strict_parse_retries"],
        "input_freeze_manifest_sha256": plan["input_freeze_manifest_sha256"],
        "target_inference_calls": 0,
        "paid_approval_confirmed": True,
        "git_commit_at_start": git_commit(repo),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = output_dir / "run_manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        immutable = (
            "plan_sha256",
            "jobs_manifest_sha256",
            "judge_model",
            "rubric_sha256",
            "temperature",
            "max_judge_tokens",
            "input_freeze_manifest_sha256",
        )
        changed = [key for key in immutable if old.get(key) != run_manifest.get(key)]
        if changed:
            raise RuntimeError(f"unsafe resume: immutable run settings changed: {changed}")
    else:
        manifest_path.write_text(
            json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def score_one(job: dict[str, Any]) -> dict[str, Any]:
        context = materialized[job["job_id"]]
        last_problem = "unknown"
        for consistency_try in range(3):
            result = judge.score_response_strict(
                job["category"],
                context["prompt"],
                context["response"],
                judge_model=plan["judge_model"],
                language=job["language"],
                max_tokens=int(plan["max_judge_tokens"]),
                gate_questions=context["gate_questions"],
                retries=int(plan["strict_parse_retries"]),
            )
            if result.score not in {0, 1, 2, 3}:
                last_problem = f"score outside 0-3: {result.score}"
                continue
            if not result.logical_consistency_ok:
                last_problem = "gate answers and score are logically inconsistent"
                continue
            row = {
                "schema_version": 1,
                "job_id": job["job_id"],
                "pair_id": job["pair_id"],
                "target_model": job["target_model"],
                "language": job["language"],
                "category": job["category"],
                "strategy": job["strategy"],
                "prompt_sha256": job["prompt_sha256"],
                "response_sha256": job["response_sha256"],
                "rubric_sha256": job["rubric_sha256"],
                "judge_messages_sha256": job["judge_messages_sha256"],
                "judge_model": plan["judge_model"],
                "temperature": plan["temperature"],
                "max_judge_tokens": plan["max_judge_tokens"],
                "consistency_attempt": consistency_try + 1,
                "scored_at_utc": datetime.now(timezone.utc).isoformat(),
                **dataclasses.asdict(result),
            }
            return row
        raise RuntimeError(last_problem)

    attempted = 0
    successful = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_job = {executor.submit(score_one, job): job for job in pending}
        for future in as_completed(future_to_job):
            job = future_to_job[future]
            attempted += 1
            try:
                row = future.result()
            except Exception as exc:  # noqa: BLE001
                append_jsonl(
                    errors_path,
                    {
                        "schema_version": 1,
                        "job_id": job["job_id"],
                        "pair_id": job["pair_id"],
                        "target_model": job["target_model"],
                        "language": job["language"],
                        "judge_model": plan["judge_model"],
                        "error": str(exc),
                        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                    },
                )
            else:
                append_jsonl(scores_path, row)
                existing[row["job_id"]] = row
                successful += 1
            if attempted % 25 == 0 or attempted == len(pending):
                print(
                    f"progress: attempted_this_process={attempted}/{len(pending)} "
                    f"successful_total={len(existing)}/{len(jobs)}",
                    flush=True,
                )

    accounting = aggregate_accounting(output_dir / "accounting")
    accounting_path = output_dir / "api_accounting_summary.json"
    accounting_path.write_text(
        json.dumps(accounting, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    accounting_complete = accounting["successful_calls"] >= len(existing)
    progress = {
        "expected_jobs": len(jobs),
        "successful_jobs": len(existing),
        "remaining_jobs": len(jobs) - len(existing),
        "attempted_this_process": attempted,
        "successful_this_process": successful,
        "complete": len(existing) == len(jobs),
        "accounting_complete_for_scores": accounting_complete,
        "known_cost_usd": accounting["known_cost_usd"],
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / "progress.json").write_text(
        json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if progress["complete"] and accounting_complete:
        completion = {
            "schema_version": 1,
            "phase": "D",
            "plan_sha256": sha256_file(plan_path),
            "jobs_manifest_sha256": plan["jobs_manifest_sha256"],
            "scores_sha256": sha256_file(scores_path),
            "errors_sha256": sha256_file(errors_path) if errors_path.exists() else None,
            "api_accounting_summary_sha256": sha256_file(accounting_path),
            "successful_jobs": len(existing),
            "successful_api_calls": accounting["successful_calls"],
            "failed_api_calls": accounting["failed_calls"],
            "known_cost_usd": accounting["known_cost_usd"],
            "target_inference_calls": 0,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        (output_dir / "completion_manifest.json").write_text(
            json.dumps(completion, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(progress, sort_keys=True))
    if not accounting_complete:
        raise RuntimeError(
            "accounting ledger has fewer successful calls than score rows; run not valid"
        )


if __name__ == "__main__":
    main()
