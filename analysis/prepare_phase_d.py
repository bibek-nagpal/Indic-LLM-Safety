"""Prepare hash-locked Phase D cross-judge jobs without making API calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from jailbreak_hermes import category_spec, judge

from analyze_phase_c import successful_trace_rows
from qc_final import (
    BANK_ID,
    EXPECTED_CATEGORIES,
    EXPECTED_MODELS,
    EXPECTED_STRATEGIES,
    RUN_ID,
    load_jsonl,
    run_qc,
    sha256_file,
)


GPT_JUDGE_MODEL = "openai/gpt-5-mini"
CLAUDE_JUDGE_MODEL = "anthropic/claude-sonnet-4.6"
SAMPLE_SEED = 20260829
SAMPLE_PER_CELL = 5
MAX_JUDGE_TOKENS = 2048

# Official list prices are re-verified immediately before paid execution.
PRICE_ASSUMPTIONS = {
    GPT_JUDGE_MODEL: {
        "input_usd_per_million_tokens": 0.25,
        "output_usd_per_million_tokens": 2.00,
        "expected_completion_tokens_per_job": 600,
        "pricing_verified_on": "2026-08-29",
        "pricing_source": "https://openrouter.ai/openai/gpt-5-mini/pricing",
        "pricing_note": "Conservative uncached-input estimate; repeated rubric prefixes may be cached.",
    },
    CLAUDE_JUDGE_MODEL: {
        "input_usd_per_million_tokens": 3.00,
        "output_usd_per_million_tokens": 15.00,
        "expected_completion_tokens_per_job": 500,
        "pricing_verified_on": "2026-08-29",
        "pricing_source": "https://openrouter.ai/anthropic/claude-sonnet-4.6/pricing",
        "pricing_note": "Conservative list-price estimate; no cache discount assumed.",
    },
}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return sha256_text(payload)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def estimate_message_tokens(messages: list[dict[str, str]]) -> int:
    """Offline planning proxy: UTF-8 bytes / 4 plus chat-envelope allowance."""
    content_bytes = sum(len(message["content"].encode("utf-8")) for message in messages)
    return math.ceil(content_bytes / 4) + 4 * len(messages) + 2


def upper_bound_message_tokens(messages: list[dict[str, str]]) -> int:
    """Pessimistic byte-level token ceiling plus a fixed protocol allowance."""
    content_bytes = sum(len(message["content"].encode("utf-8")) for message in messages)
    return content_bytes + 256


def sample_pair_model_jobs(
    traces: list[dict[str, Any]], *, seed: int, per_cell: int
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        key = (trace["model"], trace["category"], trace["strategy"])
        grouped[key].append(trace)

    expected_cells = {
        (model, category, strategy)
        for model in EXPECTED_MODELS
        for category in EXPECTED_CATEGORIES
        for strategy in EXPECTED_STRATEGIES
    }
    if set(grouped) != expected_cells:
        raise RuntimeError("sample cell grid does not match the expected 36 cells")

    selected = []
    for cell in sorted(expected_cells):
        candidates = grouped[cell]
        if len(candidates) != 42:
            raise RuntimeError(f"expected 42 jobs in cell {cell}, found {len(candidates)}")
        ranked = sorted(
            candidates,
            key=lambda row: sha256_text(
                f"{seed}\x1f{row['pair_id']}\x1f{row['model']}\x1f"
                f"{row['category']}\x1f{row['strategy']}"
            ),
        )
        for row in ranked[:per_cell]:
            copy = dict(row)
            copy["selection_rank_sha256"] = sha256_text(
                f"{seed}\x1f{row['pair_id']}\x1f{row['model']}\x1f"
                f"{row['category']}\x1f{row['strategy']}"
            )
            selected.append(copy)
    return sorted(selected, key=lambda row: (row["model"], row["category"], row["strategy"], row["pair_id"]))


def build_response_jobs(
    traces: list[dict[str, Any]],
    *,
    pair_lookup: dict[str, dict[str, Any]],
    judge_model: str,
) -> list[dict[str, Any]]:
    specs = {
        category: category_spec.load_by_id(category) for category in EXPECTED_CATEGORIES
    }
    rubric_sha = sha256_text(judge.JUDGE_SYSTEM)
    jobs = []
    for trace in traces:
        pair = pair_lookup[trace["pair_id"]]
        candidate = pair["candidate"]
        for language, trace_field, prompt_field in (
            ("en", "english", "english_prompt"),
            ("rh", "romanized_hindi", "romanized_hindi_prompt"),
        ):
            prompt = candidate[prompt_field]
            response = trace[trace_field]["content"]
            messages = judge.build_judge_messages(
                trace["category"],
                prompt,
                response,
                language=language,
                gate_questions=specs[trace["category"]].gate_questions,
            )
            prompt_sha = sha256_text(prompt)
            response_sha = sha256_text(response)
            message_sha = canonical_sha256(messages)
            identity = {
                "pair_id": trace["pair_id"],
                "target_model": trace["model"],
                "language": language,
                "judge_model": judge_model,
                "prompt_sha256": prompt_sha,
                "response_sha256": response_sha,
                "rubric_sha256": rubric_sha,
            }
            jobs.append(
                {
                    "schema_version": 1,
                    "job_id": canonical_sha256(identity)[:32],
                    **identity,
                    "category": trace["category"],
                    "strategy": trace["strategy"],
                    "judge_messages_sha256": message_sha,
                    "estimated_input_tokens_proxy": estimate_message_tokens(messages),
                    "input_token_upper_bound": upper_bound_message_tokens(messages),
                    "prompt_characters": len(prompt),
                    "response_characters": len(response),
                }
            )
    jobs.sort(key=lambda row: (row["pair_id"], row["target_model"], row["language"]))
    if len({row["job_id"] for row in jobs}) != len(jobs):
        raise RuntimeError("duplicate Phase D job IDs")
    return jobs


def build_plan(
    *,
    repo: Path,
    output_dir: Path,
    snapshot: Path,
    jobs_path: Path,
    jobs: list[dict[str, Any]],
    judge_model: str,
    scope: str,
    concurrency: int,
) -> dict[str, Any]:
    prices = PRICE_ASSUMPTIONS[judge_model]
    input_tokens = [row["estimated_input_tokens_proxy"] for row in jobs]
    input_upper_bounds = [row["input_token_upper_bound"] for row in jobs]
    expected_completion_tokens = int(prices["expected_completion_tokens_per_job"])
    total_input = sum(input_tokens)
    total_input_upper_bound = sum(input_upper_bounds)
    total_expected_output = len(jobs) * expected_completion_tokens
    total_max_output = len(jobs) * MAX_JUDGE_TOKENS
    expected_cost = (
        total_input * prices["input_usd_per_million_tokens"]
        + total_expected_output * prices["output_usd_per_million_tokens"]
    ) / 1_000_000
    max_input_output_cost_bound = (
        total_input_upper_bound * prices["input_usd_per_million_tokens"]
        + total_max_output * prices["output_usd_per_million_tokens"]
    ) / 1_000_000
    return {
        "schema_version": 1,
        "phase": "D",
        "scope": scope,
        "judge_model": judge_model,
        "jobs_manifest": str(jobs_path.relative_to(repo)).replace("\\", "/"),
        "jobs_manifest_sha256": sha256_file(jobs_path),
        "expected_jobs": len(jobs),
        "expected_pair_model_jobs": len(jobs) // 2,
        "languages_per_pair_model": 2,
        "input_snapshot": snapshot.name,
        "input_freeze_manifest_sha256": sha256_file(snapshot / "FREEZE_MANIFEST.json"),
        "input_bank_id": BANK_ID,
        "input_run_id": RUN_ID,
        "rubric_sha256": sha256_text(judge.JUDGE_SYSTEM),
        "temperature": 0.0,
        "max_judge_tokens": MAX_JUDGE_TOKENS,
        "strict_parse_retries": 2,
        "concurrency": concurrency,
        "output_dir": str(output_dir.relative_to(repo)).replace("\\", "/"),
        "resumable": True,
        "target_inference_calls": 0,
        "paid_judge_calls_required": True,
        "token_estimation": {
            "encoding": "offline planning proxy: ceil(UTF-8 bytes / 4) plus chat envelope",
            "total_input_token_proxy": total_input,
            "mean_input_tokens": statistics.fmean(input_tokens),
            "median_input_tokens": statistics.median(input_tokens),
            "p95_input_tokens": sorted(input_tokens)[int(0.95 * (len(input_tokens) - 1))],
            "max_input_tokens": max(input_tokens),
            "upper_bound_method": "UTF-8 content bytes plus 256 protocol tokens per request",
            "total_input_token_upper_bound": total_input_upper_bound,
            "expected_completion_tokens_per_job": expected_completion_tokens,
            "max_completion_tokens_per_job": MAX_JUDGE_TOKENS,
        },
        "price_assumption": prices,
        "cost_estimate_usd": {
            "expected_uncached": expected_cost,
            "pessimistic_no_retry_bound_uncached": max_input_output_cost_bound,
            "excludes_retries": True,
        },
        "retry_ceiling": {
            "parse_attempts_per_consistency_attempt": 3,
            "consistency_attempts_per_job": 3,
            "maximum_paid_scoring_calls_per_job": 9,
            "expected_paid_scoring_calls_per_job": 1,
        },
    }


def write_manifest(output_dir: Path, snapshot: Path) -> None:
    path = output_dir / "PREPARATION_MANIFEST.json"
    files = []
    for item in sorted(candidate for candidate in output_dir.rglob("*") if candidate.is_file()):
        if item == path:
            continue
        files.append(
            {
                "path": str(item.relative_to(output_dir)).replace("\\", "/"),
                "bytes": item.stat().st_size,
                "sha256": sha256_file(item),
            }
        )
    payload = {
        "schema_version": 1,
        "phase": "D preparation",
        "api_calls": 0,
        "input_snapshot": snapshot.name,
        "input_freeze_manifest_sha256": sha256_file(snapshot / "FREEZE_MANIFEST.json"),
        "preparation_script_sha256": sha256_file(Path(__file__).resolve()),
        "files": files,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--snapshot", type=Path, default=Path("frozen_final_2026_08_29"))
    parser.add_argument("--output", type=Path, default=Path("analysis/phase_d_preparation"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    snapshot = args.snapshot if args.snapshot.is_absolute() else repo / args.snapshot
    output_dir = args.output if args.output.is_absolute() else repo / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    qc = run_qc(snapshot)
    if qc["overall_status"] != "PASS":
        raise RuntimeError("Phase A QC failed; refusing Phase D preparation")

    pairs = load_jsonl(snapshot / "bank" / BANK_ID / "pairs.jsonl")
    pair_lookup = {row["pair_id"]: row for row in pairs}
    traces = successful_trace_rows(
        load_jsonl(snapshot / "run" / RUN_ID / "traces.jsonl")
    )
    if len(traces) != 1512:
        raise RuntimeError(f"expected 1512 successful traces, found {len(traces)}")

    selected_traces = sample_pair_model_jobs(
        traces, seed=SAMPLE_SEED, per_cell=SAMPLE_PER_CELL
    )
    sample_rows = [
        {
            "pair_id": row["pair_id"],
            "target_model": row["model"],
            "category": row["category"],
            "strategy": row["strategy"],
            "selection_seed": SAMPLE_SEED,
            "selection_rank_sha256": row["selection_rank_sha256"],
        }
        for row in selected_traces
    ]
    sample_frame = pd.DataFrame(sample_rows)
    sample_path = output_dir / "stratified_180_pair_model_sample.csv"
    sample_frame.to_csv(sample_path, index=False)

    gpt_jobs = build_response_jobs(
        traces,
        pair_lookup=pair_lookup,
        judge_model=GPT_JUDGE_MODEL,
    )
    claude_jobs = build_response_jobs(
        selected_traces,
        pair_lookup=pair_lookup,
        judge_model=CLAUDE_JUDGE_MODEL,
    )
    if len(gpt_jobs) != 3024 or len(claude_jobs) != 360:
        raise RuntimeError(
            f"unexpected Phase D job counts: GPT={len(gpt_jobs)}, Claude={len(claude_jobs)}"
        )

    gpt_jobs_path = output_dir / "gpt5mini_full_jobs.jsonl"
    claude_jobs_path = output_dir / "claude_sample_jobs.jsonl"
    write_jsonl(gpt_jobs_path, gpt_jobs)
    write_jsonl(claude_jobs_path, claude_jobs)

    gpt_plan = build_plan(
        repo=repo,
        output_dir=repo / "runs" / "cross_judge" / "gpt5mini_final",
        snapshot=snapshot,
        jobs_path=gpt_jobs_path,
        jobs=gpt_jobs,
        judge_model=GPT_JUDGE_MODEL,
        scope="full 3024-response independent re-judge",
        concurrency=8,
    )
    claude_plan = build_plan(
        repo=repo,
        output_dir=repo / "runs" / "cross_judge" / "claude_sonnet_4_6_sample",
        snapshot=snapshot,
        jobs_path=claude_jobs_path,
        jobs=claude_jobs,
        judge_model=CLAUDE_JUDGE_MODEL,
        scope="stratified 360-response independent-family sample",
        concurrency=4,
    )
    for filename, plan in (
        ("gpt5mini_full_plan.json", gpt_plan),
        ("claude_sample_plan.json", claude_plan),
    ):
        (output_dir / filename).write_text(
            json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    summary = [
        "# Phase D Paid-Call Preparation",
        "",
        "Preparation is complete and made zero API calls. Job manifests contain only IDs, "
        "hashes, metadata, lengths, and token estimates; prompts and target responses remain "
        "only in the frozen private snapshot.",
        "",
        "| Plan | Pair-model jobs | Response jobs | Input-token estimate | Expected uncached cost | Pessimistic no-retry bound |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, plan in (("GPT-5 Mini full", gpt_plan), ("Claude Sonnet sample", claude_plan)):
        summary.append(
            f"| {label} | {plan['expected_pair_model_jobs']} | {plan['expected_jobs']} | "
            f"{plan['token_estimation']['total_input_token_proxy']:,} | "
            f"${plan['cost_estimate_usd']['expected_uncached']:.2f} | "
            f"${plan['cost_estimate_usd']['pessimistic_no_retry_bound_uncached']:.2f} |"
        )
    summary.extend(
        [
            "",
            f"The shared validation sample uses seed {SAMPLE_SEED}, five pair-model jobs in "
            "each of 36 model×category×strategy cells, and both languages for every selected job.",
            "",
            "Prices and model availability must be re-verified immediately before execution. "
            "The runner requires an explicit paid-approval flag and defaults to validation-only.",
            "",
        ]
    )
    (output_dir / "preparation_summary.md").write_text("\n".join(summary), encoding="utf-8")
    write_manifest(output_dir, snapshot)
    print("Phase D preparation complete: 3024 GPT jobs + 360 Claude jobs; 0 API calls")


if __name__ == "__main__":
    main()
