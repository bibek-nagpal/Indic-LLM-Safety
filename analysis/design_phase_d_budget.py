"""Design a cost-locked Phase D GPT-5 Mini plan without making API calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import tiktoken

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


GPT_MODEL = "openai/gpt-5-mini"
BATCH_MODEL = "openai/gpt-5-mini:batch"
TOKEN_ENCODING = "o200k_base"
DESIGN_SEED = 20260829
HARD_BUDGET_USD = 4.50
FALLBACK_RETRY_RESERVE_USD = 0.50
EXPECTED_OUTPUT_TOKENS = 600
MAX_OUTPUT_TOKENS = 1024
STANDARD_FALLBACK_MAX_OUTPUT_TOKENS = 768
STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS = 1024
STANDARD_REPAIR_MAX_OUTPUT_TOKENS = 1280
STANDARD_FINAL_REPAIR_MAX_OUTPUT_TOKENS = 2048
CHAT_TOKENS_PER_MESSAGE = 3
CHAT_PRIMING_TOKENS = 3

STANDARD_PRICING = {
    "input_usd_per_million_tokens": 0.25,
    "cached_input_usd_per_million_tokens": 0.025,
    "output_usd_per_million_tokens": 2.00,
    "source": "https://openrouter.ai/openai/gpt-5-mini/pricing",
}
BATCH_PRICING = {
    "input_usd_per_million_tokens": 0.125,
    "cached_input_usd_per_million_tokens": 0.0125,
    "output_usd_per_million_tokens": 1.00,
    "source": "https://openrouter.ai/openai/gpt-5-mini:batch",
    "execution_contract": "https://openrouter.ai/docs/batch-quickstart",
    "provider_tier": "OpenAI Flex",
}
PRICING_VERIFIED_ON = "2026-08-30"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def quantiles(values: list[int]) -> dict[str, float | int]:
    ordered = sorted(values)
    return {
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "p95": ordered[int(0.95 * (len(ordered) - 1))],
        "max": max(values),
        "total": sum(values),
    }


def cost(
    input_tokens: int,
    output_tokens: int,
    prices: dict[str, Any],
) -> dict[str, float]:
    input_cost = input_tokens * prices["input_usd_per_million_tokens"] / 1_000_000
    output_cost = output_tokens * prices["output_usd_per_million_tokens"] / 1_000_000
    return {
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": input_cost + output_cost,
    }


def pair_rank(row: dict[str, Any]) -> str:
    return sha256_text(
        f"{DESIGN_SEED}\x1f{row['pair_id']}\x1f{row['category']}\x1f{row['strategy']}"
    )


def fallback_subset(
    rows: list[dict[str, Any]],
    *,
    prices: dict[str, Any],
) -> tuple[int, list[dict[str, Any]], dict[str, float]]:
    by_pair_model: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    metadata: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["pair_id"], row["target_model"])
        by_pair_model[key].append(row)
        metadata[key] = row
    if any(len(group) != 2 for group in by_pair_model.values()):
        raise RuntimeError("fallback candidates are not complete EN/RH pair-model jobs")

    pair_metadata: dict[str, dict[str, Any]] = {}
    for row in metadata.values():
        previous = pair_metadata.setdefault(row["pair_id"], row)
        if (previous["category"], previous["strategy"]) != (
            row["category"],
            row["strategy"],
        ):
            raise RuntimeError("pair metadata changes across target models")
    cells: dict[tuple[str, str], list[str]] = defaultdict(list)
    for pair_id, row in pair_metadata.items():
        cells[(row["category"], row["strategy"])].append(pair_id)
    expected_cells = {
        (category, strategy)
        for category in EXPECTED_CATEGORIES
        for strategy in EXPECTED_STRATEGIES
    }
    if set(cells) != expected_cells or any(len(keys) != 42 for keys in cells.values()):
        raise RuntimeError("fallback candidate grid is not the expected 12×42 pair design")
    ranked_cells = {
        cell: sorted(keys, key=lambda pair_id: pair_rank(pair_metadata[pair_id]))
        for cell, keys in cells.items()
    }

    spend_limit = HARD_BUDGET_USD - FALLBACK_RETRY_RESERVE_USD
    for per_cell in range(42, 0, -1):
        selected_pair_ids = {
            pair_id for keys in ranked_cells.values() for pair_id in keys[:per_cell]
        }
        selected = [
            row
            for row in rows
            if row["pair_id"] in selected_pair_ids
        ]
        input_tokens = sum(row["costed_input_tokens"] for row in selected)
        maximum_output = len(selected) * STANDARD_FALLBACK_MAX_OUTPUT_TOKENS
        maximum_cost = cost(input_tokens, maximum_output, prices)
        if maximum_cost["total_cost_usd"] <= spend_limit:
            selected.sort(key=lambda row: (row["pair_id"], row["target_model"], row["language"]))
            return per_cell, selected, maximum_cost
    raise RuntimeError("even one job per cell cannot fit the standard-price fallback budget")


def write_manifest(output_dir: Path, snapshot: Path) -> None:
    manifest_path = output_dir / "BUDGET_DESIGN_MANIFEST.json"
    files = []
    for path in sorted(item for item in output_dir.rglob("*") if item.is_file()):
        if path == manifest_path:
            continue
        files.append(
            {
                "path": str(path.relative_to(output_dir)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    payload = {
        "schema_version": 1,
        "phase": "D budget redesign",
        "api_calls": 0,
        "hard_budget_usd": HARD_BUDGET_USD,
        "active_recommendation": "standard_fallback_shared_pairs",
        "batch_live_validation_available": False,
        "input_snapshot": snapshot.name,
        "input_freeze_manifest_sha256": sha256_file(snapshot / "FREEZE_MANIFEST.json"),
        "design_script_sha256": sha256_file(Path(__file__).resolve()),
        "files": files,
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--snapshot", type=Path, default=Path("frozen_final_2026_08_29"))
    parser.add_argument("--output", type=Path, default=Path("analysis/phase_d_budget_design"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    snapshot = args.snapshot if args.snapshot.is_absolute() else repo / args.snapshot
    output_dir = args.output if args.output.is_absolute() else repo / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    if run_qc(snapshot)["overall_status"] != "PASS":
        raise RuntimeError("Phase A QC failed; refusing Phase D budget design")

    old_jobs_path = repo / "analysis" / "phase_d_preparation" / "gpt5mini_full_jobs.jsonl"
    old_plan_path = repo / "analysis" / "phase_d_preparation" / "gpt5mini_full_plan.json"
    deferred_claude_path = repo / "analysis" / "phase_d_preparation" / "claude_sample_plan.json"
    old_jobs = load_jsonl(old_jobs_path)
    old_by_id = {row["job_id"]: row for row in old_jobs}
    pairs = load_jsonl(snapshot / "bank" / BANK_ID / "pairs.jsonl")
    pair_lookup = {row["pair_id"]: row for row in pairs}
    traces = successful_trace_rows(load_jsonl(snapshot / "run" / RUN_ID / "traces.jsonl"))
    trace_lookup = {(row["pair_id"], row["model"]): row for row in traces}
    specs = {
        category: category_spec.load_by_id(category) for category in EXPECTED_CATEGORIES
    }
    encoding = tiktoken.get_encoding(TOKEN_ENCODING)
    schema_tokens = len(
        encoding.encode(
            json.dumps(
                judge.JUDGE_RESPONSE_FORMAT,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    )
    chat_overhead = 2 * CHAT_TOKENS_PER_MESSAGE + CHAT_PRIMING_TOKENS
    request_contract = {
        "endpoint": "/v1/chat/completions",
        "model": BATCH_MODEL,
        "temperature": 0.0,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "include_reasoning": True,
        "response_format": judge.JUDGE_RESPONSE_FORMAT,
        "provider": {"require_parameters": True},
    }
    standard_request_contract = {
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "model": GPT_MODEL,
        # GPT-5 Mini is a mandatory-reasoning model and its live OpenRouter
        # metadata does not advertise temperature. Requiring temperature=0
        # excludes every endpoint, so use its supported deterministic seed
        # parameter while preserving the exact rubric and structured schema.
        "seed": DESIGN_SEED,
        "max_tokens": STANDARD_FALLBACK_MAX_OUTPUT_TOKENS,
        "include_reasoning": True,
        "response_format": judge.JUDGE_RESPONSE_FORMAT,
        "provider": {"require_parameters": True},
    }

    rows = []
    messages_by_job_id: dict[str, list[dict[str, str]]] = {}
    for old in old_jobs:
        pair = pair_lookup[old["pair_id"]]
        trace = trace_lookup[(old["pair_id"], old["target_model"])]
        if old["language"] == "en":
            prompt = pair["candidate"]["english_prompt"]
            response = trace["english"]["content"]
        else:
            prompt = pair["candidate"]["romanized_hindi_prompt"]
            response = trace["romanized_hindi"]["content"]
        messages = judge.build_judge_messages(
            old["category"],
            prompt,
            response,
            language=old["language"],
            gate_questions=specs[old["category"]].gate_questions,
        )
        if canonical_sha256(messages) != old["judge_messages_sha256"]:
            raise RuntimeError(f"judge message drift for {old['job_id']}")
        system_tokens = len(encoding.encode(messages[0]["content"]))
        user_tokens = len(encoding.encode(messages[1]["content"]))
        message_content_tokens = system_tokens + user_tokens
        estimated_chat_tokens = message_content_tokens + chat_overhead
        costed_input_tokens = estimated_chat_tokens + schema_tokens
        body = {
            "messages": messages,
            **{key: value for key, value in request_contract.items() if key not in {"endpoint", "model"}},
        }
        row = {
            **old,
            "token_encoding": TOKEN_ENCODING,
            "stored_prompt_tokens": len(encoding.encode(prompt)),
            "stored_response_tokens": len(encoding.encode(response)),
            "judge_system_tokens": system_tokens,
            "judge_user_message_tokens": user_tokens,
            "judge_message_content_tokens": message_content_tokens,
            "estimated_chat_protocol_tokens": estimated_chat_tokens,
            "structured_output_schema_tokens_conservative": schema_tokens,
            "costed_input_tokens": costed_input_tokens,
            "batch_request_sha256": canonical_sha256(body),
        }
        if old_by_id[row["job_id"]]["response_sha256"] != row["response_sha256"]:
            raise RuntimeError("old job identity mismatch")
        rows.append(row)
        messages_by_job_id[row["job_id"]] = messages
    if len(rows) != 3024:
        raise RuntimeError(f"expected 3024 full cross-judge rows, found {len(rows)}")

    jobs_path = output_dir / "gpt5mini_batch_full_jobs.jsonl"
    write_jsonl(jobs_path, rows)
    total_input = sum(row["costed_input_tokens"] for row in rows)
    expected_output = len(rows) * EXPECTED_OUTPUT_TOKENS
    maximum_output = len(rows) * MAX_OUTPUT_TOKENS
    standard_expected = cost(total_input, expected_output, STANDARD_PRICING)
    standard_maximum = cost(total_input, maximum_output, STANDARD_PRICING)
    batch_expected = cost(total_input, expected_output, BATCH_PRICING)
    batch_maximum = cost(total_input, maximum_output, BATCH_PRICING)
    standard_maximum_margin = HARD_BUDGET_USD - standard_maximum["total_cost_usd"]
    batch_retry_reserve = HARD_BUDGET_USD - batch_maximum["total_cost_usd"]
    maximum_single_retry_cost = max(
        cost(row["costed_input_tokens"], MAX_OUTPUT_TOKENS, BATCH_PRICING)["total_cost_usd"]
        for row in rows
    )
    conservative_retry_jobs = math.floor(batch_retry_reserve / maximum_single_retry_cost)

    per_cell, fallback_rows, fallback_maximum = fallback_subset(
        rows, prices=STANDARD_PRICING
    )
    fallback_pair_ids = {row["pair_id"] for row in fallback_rows}
    complement_rows = [row for row in rows if row["pair_id"] not in fallback_pair_ids]
    complement_pair_ids = {row["pair_id"] for row in complement_rows}
    all_pair_ids = {row["pair_id"] for row in rows}
    if fallback_pair_ids & complement_pair_ids:
        raise RuntimeError("standard fallback and future complement overlap")
    if fallback_pair_ids | complement_pair_ids != all_pair_ids:
        raise RuntimeError("standard fallback and future complement do not cover the bank")
    if len(fallback_pair_ids) != 324 or len(complement_pair_ids) != 180:
        raise RuntimeError("unexpected standard fallback/complement pair counts")

    def as_standard_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            **{key: value for key, value in row.items() if key != "batch_request_sha256"},
            "standard_request_sha256": canonical_sha256(
                {
                    "messages": messages_by_job_id[row["job_id"]],
                    **{
                        key: value
                        for key, value in standard_request_contract.items()
                        if key != "endpoint"
                    },
                }
            ),
        }

    fallback_rows = [as_standard_row(row) for row in fallback_rows]
    complement_rows = [as_standard_row(row) for row in complement_rows]
    complement_rows.sort(
        key=lambda row: (row["pair_id"], row["target_model"], row["language"])
    )
    fallback_path = output_dir / "gpt5mini_standard_fallback_jobs.jsonl"
    write_jsonl(fallback_path, fallback_rows)
    complement_path = output_dir / "gpt5mini_standard_complement_jobs.jsonl"
    write_jsonl(complement_path, complement_rows)
    fallback_input = sum(row["costed_input_tokens"] for row in fallback_rows)
    fallback_expected = cost(
        fallback_input,
        len(fallback_rows) * EXPECTED_OUTPUT_TOKENS,
        STANDARD_PRICING,
    )
    fallback_continuation_maximum = cost(
        fallback_input,
        len(fallback_rows) * STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS,
        STANDARD_PRICING,
    )
    maximum_truncated_attempt_plus_repair = max(
        cost(
            2 * row["costed_input_tokens"],
            STANDARD_REPAIR_MAX_OUTPUT_TOKENS
            + STANDARD_FINAL_REPAIR_MAX_OUTPUT_TOKENS,
            STANDARD_PRICING,
        )["total_cost_usd"]
        for row in fallback_rows
    )
    conservative_repair_jobs = math.floor(
        FALLBACK_RETRY_RESERVE_USD / maximum_truncated_attempt_plus_repair
    )
    complement_input = sum(row["costed_input_tokens"] for row in complement_rows)
    complement_expected = cost(
        complement_input,
        len(complement_rows) * EXPECTED_OUTPUT_TOKENS,
        STANDARD_PRICING,
    )
    complement_maximum = cost(
        complement_input,
        len(complement_rows) * STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS,
        STANDARD_PRICING,
    )

    empirical = {
        "response_judging_calls": 2,
        "completion_tokens": [614, 577],
        "reasoning_tokens": [448, 448],
        "mean_completion_tokens": 595.5,
        "basis": "existing local OpenRouter accounting; no new calls",
    }
    token_statistics = {
        "stored_prompt_tokens": quantiles([row["stored_prompt_tokens"] for row in rows]),
        "stored_response_tokens": quantiles([row["stored_response_tokens"] for row in rows]),
        "judge_message_content_tokens": quantiles(
            [row["judge_message_content_tokens"] for row in rows]
        ),
        "costed_input_tokens": quantiles([row["costed_input_tokens"] for row in rows]),
        "judge_system_tokens_per_job": rows[0]["judge_system_tokens"],
        "chat_protocol_tokens_per_job": chat_overhead,
        "structured_output_schema_tokens_per_job_conservative": schema_tokens,
    }
    cost_report = {
        "schema_version": 1,
        "api_calls": 0,
        "jobs": len(rows),
        "pair_model_jobs": len(rows) // 2,
        "hard_budget_usd": HARD_BUDGET_USD,
        "active_recommendation": "standard_fallback_shared_pairs",
        "batch_live_validation_available": False,
        "pricing_verified_on": PRICING_VERIFIED_ON,
        "token_encoding": TOKEN_ENCODING,
        "token_statistics": token_statistics,
        "output_token_basis": empirical,
        "standard": {
            "prices": STANDARD_PRICING,
            "expected_600_output_tokens_per_job": standard_expected,
            f"maximum_{MAX_OUTPUT_TOKENS}_output_tokens_per_job": standard_maximum,
            "full_run_fits_hard_budget_at_maximum": standard_maximum["total_cost_usd"]
            <= HARD_BUDGET_USD,
            "margin_after_maximum_outputs_usd": standard_maximum_margin,
            "conservative_retry_allowance_usd": max(0.0, standard_maximum_margin),
        },
        "batch": {
            "prices": BATCH_PRICING,
            "expected_600_output_tokens_per_job": batch_expected,
            f"maximum_{MAX_OUTPUT_TOKENS}_output_tokens_per_job": batch_maximum,
            "full_run_fits_hard_budget_at_maximum": batch_maximum["total_cost_usd"]
            <= HARD_BUDGET_USD,
            "retry_reserve_after_maximum_outputs_usd": batch_retry_reserve,
            "conservative_retry_allowance_usd": batch_retry_reserve,
            "maximum_single_job_retry_cost_usd": maximum_single_retry_cost,
            "conservative_whole_job_retries_within_reserve": conservative_retry_jobs,
        },
        "standard_fallback": {
            "selection_seed": DESIGN_SEED,
            "same_pair_ids_across_target_models": True,
            "pair_model_jobs_per_model_category_strategy_cell": per_cell,
            "pair_model_jobs": len(fallback_rows) // 2,
            "response_jobs": len(fallback_rows),
            "expected_600_output_tokens_per_job": fallback_expected,
            f"maximum_{STANDARD_FALLBACK_MAX_OUTPUT_TOKENS}_output_tokens_per_job": fallback_maximum,
            f"continuation_maximum_{STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS}_output_tokens_per_job": fallback_continuation_maximum,
            "max_output_tokens_per_job": STANDARD_FALLBACK_MAX_OUTPUT_TOKENS,
            "continuation_max_output_tokens_per_job": STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS,
            "reserved_for_retries_usd": FALLBACK_RETRY_RESERVE_USD,
            "adaptive_truncation_repair": {
                "base_max_output_tokens": STANDARD_FALLBACK_MAX_OUTPUT_TOKENS,
                "continuation_max_output_tokens": STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS,
                "repair_max_output_tokens": STANDARD_REPAIR_MAX_OUTPUT_TOKENS,
                "final_repair_max_output_tokens": STANDARD_FINAL_REPAIR_MAX_OUTPUT_TOKENS,
                "eligibility": "strict parse failure after completion reached the cap with reasoning tokens",
                "maximum_single_failed_attempt_plus_repair_cost_usd": maximum_truncated_attempt_plus_repair,
                "conservative_whole_job_repairs_within_reserve": conservative_repair_jobs,
                "rubric_or_reasoning_effort_change": False,
            },
        },
        "standard_complement_after_top_up": {
            "selection_rule": "exact set complement of the active 324-pair selection",
            "selected_pair_ids": len(fallback_pair_ids),
            "complement_pair_ids": len(complement_pair_ids),
            "overlapping_pair_ids": 0,
            "union_pair_ids": len(fallback_pair_ids | complement_pair_ids),
            "pair_model_jobs": len(complement_rows) // 2,
            "response_jobs": len(complement_rows),
            "expected_600_output_tokens_per_job": complement_expected,
            f"maximum_{STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS}_output_tokens_per_job": complement_maximum,
            "max_output_tokens_per_job": STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS,
            "requires_new_explicit_paid_approval": True,
        },
        "costing_assumptions": {
            "actual_stored_text_tokenized": True,
            "judge_messages_exactly_reconstructed_and_hash_checked": True,
            "chat_protocol_tokens_per_job_conservative": chat_overhead,
            "structured_output_schema_counted_as_input_per_job_conservative": True,
            "reasoning_tokens_included_in_output_budget": True,
            "prompt_cache_savings_assumed_usd": 0.0,
            "retry_allowance_definition": (
                "Budget remaining after every planned job consumes its full output cap; "
                "active and ambiguously failed requests retain their maximum reservation."
            ),
        },
    }
    report_path = output_dir / "cost_analysis.json"
    report_path.write_text(
        json.dumps(cost_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    batch_plan = {
        "schema_version": 1,
        "phase": "D1 budget-constrained full independent re-judge",
        "execution_mode": "openrouter_asynchronous_batch_api",
        "submission_endpoint": "https://openrouter.ai/api/beta/batches",
        "request_endpoint": "/v1/chat/completions",
        "judge_model": GPT_MODEL,
        "batch_model": BATCH_MODEL,
        "use_colon_batch_slug": True,
        "colon_batch_slug_investigation": (
            "The live Batch API validator requires the :batch model variant for GPT-5 Mini; "
            "a base-slug smoke submission was rejected with HTTP 400 before persistence."
        ),
        "jobs_manifest": str(jobs_path.relative_to(repo)).replace("\\", "/"),
        "jobs_manifest_sha256": sha256_file(jobs_path),
        "expected_jobs": len(rows),
        "expected_pair_model_jobs": len(rows) // 2,
        "input_snapshot": snapshot.name,
        "input_freeze_manifest_sha256": sha256_file(snapshot / "FREEZE_MANIFEST.json"),
        "input_bank_id": BANK_ID,
        "input_run_id": RUN_ID,
        "rubric_sha256": sha256_text(judge.JUDGE_SYSTEM),
        "response_format_sha256": canonical_sha256(judge.JUDGE_RESPONSE_FORMAT),
        "request_contract": request_contract,
        "request_contract_sha256": canonical_sha256(request_contract),
        "hard_budget_usd": HARD_BUDGET_USD,
        "cost_analysis": str(report_path.relative_to(repo)).replace("\\", "/"),
        "cost_analysis_sha256": sha256_file(report_path),
        "pricing": BATCH_PRICING,
        "pricing_verified_on": PRICING_VERIFIED_ON,
        "maximum_no_retry_cost_usd": batch_maximum["total_cost_usd"],
        "retry_reserve_usd": batch_retry_reserve,
        "smoke_test_jobs": 2,
        "target_inference_calls": 0,
        "output_dir": "runs/cross_judge/gpt5mini_batch_budget",
        "deferred_claude_plan": str(deferred_claude_path.relative_to(repo)).replace("\\", "/"),
        "deferred_claude_plan_sha256": sha256_file(deferred_claude_path),
        "supersedes_for_current_budget": str(old_plan_path.relative_to(repo)).replace("\\", "/"),
        "superseded_plan_preserved": True,
        "status": "unavailable_after_live_smoke_validation",
        "availability_evidence": (
            "OpenRouter returned HTTP 400 before persistence for both the base and :batch "
            "model identifiers; no inference batch was created and the local ledger records $0."
        ),
    }
    (output_dir / "gpt5mini_batch_full_plan.json").write_text(
        json.dumps(batch_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    fallback_plan = {
        "schema_version": 1,
        "phase": "D1 standard-price contingency",
        "execution_mode": "synchronous_resumable",
        "judge_model": GPT_MODEL,
        "request_contract": standard_request_contract,
        "request_contract_sha256": canonical_sha256(standard_request_contract),
        "jobs_manifest": str(fallback_path.relative_to(repo)).replace("\\", "/"),
        "jobs_manifest_sha256": sha256_file(fallback_path),
        "expected_jobs": len(fallback_rows),
        "expected_pair_model_jobs": len(fallback_rows) // 2,
        "pair_model_jobs_per_cell": per_cell,
        "selection_seed": DESIGN_SEED,
        "selection_independent_of_target_scores": True,
        "same_pair_ids_across_target_models": True,
        "input_snapshot": snapshot.name,
        "input_freeze_manifest_sha256": sha256_file(snapshot / "FREEZE_MANIFEST.json"),
        "input_bank_id": BANK_ID,
        "input_run_id": RUN_ID,
        "rubric_sha256": sha256_text(judge.JUDGE_SYSTEM),
        "hard_budget_usd": HARD_BUDGET_USD,
        "retry_reserve_usd": FALLBACK_RETRY_RESERVE_USD,
        "maximum_no_retry_cost_usd": fallback_maximum["total_cost_usd"],
        "pricing": STANDARD_PRICING,
        "max_judge_tokens": STANDARD_FALLBACK_MAX_OUTPUT_TOKENS,
        "continuation_max_judge_tokens": STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS,
        "truncation_repair_max_judge_tokens": STANDARD_REPAIR_MAX_OUTPUT_TOKENS,
        "final_truncation_repair_max_judge_tokens": STANDARD_FINAL_REPAIR_MAX_OUTPUT_TOKENS,
        "truncation_repair_policy": (
            "Retry only when strict parsing fails after the response reaches the output cap "
            "with reasoning tokens; preserve the prompt, rubric, schema, model, and "
            "reasoning effort. Every failed paid attempt remains in total budget accounting."
        ),
        "budget_enforcement": (
            "Before every request, known actual spend plus all ambiguous reservations plus "
            "the next request's maximum reservation must not exceed the hard ceiling."
        ),
        "response_format_sha256": canonical_sha256(judge.JUDGE_RESPONSE_FORMAT),
        "cost_analysis": str(report_path.relative_to(repo)).replace("\\", "/"),
        "cost_analysis_sha256": sha256_file(report_path),
        "expected_cost_usd": fallback_expected["total_cost_usd"],
        "smoke_test_jobs": 2,
        "output_dir": "runs/cross_judge/gpt5mini_standard_budget",
        "target_inference_calls": 0,
        "status": "recommended_after_batch_unavailable",
    }
    (output_dir / "gpt5mini_standard_fallback_plan.json").write_text(
        json.dumps(fallback_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    complement_plan = {
        "schema_version": 1,
        "phase": "D1 deferred exact-complement completion",
        "execution_mode": "synchronous_resumable",
        "judge_model": GPT_MODEL,
        "request_contract": standard_request_contract,
        "request_contract_sha256": canonical_sha256(standard_request_contract),
        "jobs_manifest": str(complement_path.relative_to(repo)).replace("\\", "/"),
        "jobs_manifest_sha256": sha256_file(complement_path),
        "expected_jobs": len(complement_rows),
        "expected_pair_model_jobs": len(complement_rows) // 2,
        "expected_pair_ids": len(complement_pair_ids),
        "pair_model_jobs_per_cell": 42 - per_cell,
        "selection_rule": "all frozen pair IDs absent from the active 324-pair selection",
        "selected_pair_ids_manifest": str(fallback_path.relative_to(repo)).replace("\\", "/"),
        "selected_pair_ids_manifest_sha256": sha256_file(fallback_path),
        "overlapping_pair_ids": 0,
        "combined_pair_ids": len(fallback_pair_ids | complement_pair_ids),
        "same_pair_ids_across_target_models": True,
        "input_snapshot": snapshot.name,
        "input_freeze_manifest_sha256": sha256_file(snapshot / "FREEZE_MANIFEST.json"),
        "input_bank_id": BANK_ID,
        "input_run_id": RUN_ID,
        "rubric_sha256": sha256_text(judge.JUDGE_SYSTEM),
        "pricing": STANDARD_PRICING,
        "max_judge_tokens": STANDARD_FALLBACK_MAX_OUTPUT_TOKENS,
        "continuation_max_judge_tokens": STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS,
        "truncation_repair_max_judge_tokens": STANDARD_REPAIR_MAX_OUTPUT_TOKENS,
        "final_truncation_repair_max_judge_tokens": STANDARD_FINAL_REPAIR_MAX_OUTPUT_TOKENS,
        "response_format_sha256": canonical_sha256(judge.JUDGE_RESPONSE_FORMAT),
        "cost_analysis": str(report_path.relative_to(repo)).replace("\\", "/"),
        "cost_analysis_sha256": sha256_file(report_path),
        "expected_incremental_cost_usd": complement_expected["total_cost_usd"],
        "maximum_incremental_no_retry_cost_usd": complement_maximum["total_cost_usd"],
        "output_dir": "runs/cross_judge/gpt5mini_standard_complement",
        "target_inference_calls": 0,
        "requires_new_explicit_paid_approval": True,
        "status": "deferred_until_additional_budget_approved",
    }
    (output_dir / "gpt5mini_standard_complement_plan.json").write_text(
        json.dumps(complement_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary = [
        "# Phase D Budget Redesign",
        "",
        "The design generation is offline. Three Batch submission validations were rejected "
        "before persistence; no inference batch was created and the local ledger records $0. "
        "Claude remains fully prepared but deferred.",
        "",
        f"| Mode | Response jobs | Input cost | Expected output cost (600/job) | Expected total | Max total | Conservative retry allowance | Fits $4.50? |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| GPT-5 Mini standard, full | {len(rows)} | ${standard_expected['input_cost_usd']:.3f} | "
        f"${standard_expected['output_cost_usd']:.3f} | ${standard_expected['total_cost_usd']:.3f} | "
        f"${standard_maximum['total_cost_usd']:.3f} ({MAX_OUTPUT_TOKENS}/job) | $0 (over ceiling by "
        f"${-standard_maximum_margin:.3f}) | NO |",
        f"| GPT-5 Mini Batch API, full | {len(rows)} | ${batch_expected['input_cost_usd']:.3f} | "
        f"${batch_expected['output_cost_usd']:.3f} | ${batch_expected['total_cost_usd']:.3f} | "
        f"${batch_maximum['total_cost_usd']:.3f} ({MAX_OUTPUT_TOKENS}/job) | "
        f"${batch_retry_reserve:.3f} | YES |",
        f"| Standard fallback, {per_cell}/cell | {len(fallback_rows)} | "
        f"${fallback_expected['input_cost_usd']:.3f} | ${fallback_expected['output_cost_usd']:.3f} | "
        f"${fallback_expected['total_cost_usd']:.3f} | ${fallback_continuation_maximum['total_cost_usd']:.3f} "
        f"({STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS}/job) | runtime hard guard | NO at theoretical max |",
        "",
        f"The full Batch design would reserve ${batch_retry_reserve:.3f} below the hard "
        f"$4.50 ceiling even if every response consumes the full {MAX_OUTPUT_TOKENS}-token cap. "
        f"At the single most expensive job's maximum cost, that reserve covers "
        f"{conservative_retry_jobs} whole-job retries.",
        "",
        "However, live OpenRouter validation rejected both GPT-5 Mini Batch identifiers before "
        "persistence. The standard-price shared-pair contingency is therefore the active recommendation.",
        "",
        f"The standard-price contingency selects the same {per_cell} pair IDs in each of the "
        "12 category×strategy cells for all three target models, retaining both languages. "
        "This preserves pair-level between-model comparisons while reserving $0.50 for retries.",
        "",
        f"After live truncation evidence, remaining items use a {STANDARD_CONTINUATION_MAX_OUTPUT_TOKENS}-token "
        f"ceiling. If a response reaches that cap after internal reasoning and fails strict JSON "
        f"parsing, the runner may retry only that item at {STANDARD_REPAIR_MAX_OUTPUT_TOKENS} tokens, "
        f"with one final {STANDARD_FINAL_REPAIR_MAX_OUTPUT_TOKENS}-token escape hatch only after another "
        f"documented length stop. "
        f"The rubric, schema, prompt, model, and reasoning "
        f"effort remain unchanged; all failed paid attempts count toward the $4.50 ceiling. The "
        f"$0.50 reserve covers at least {conservative_repair_jobs} such whole-job repairs even at "
        "the single most expensive input size.",
        "",
        f"A hash-locked deferred complement contains exactly the other {len(complement_pair_ids)} "
        f"pair IDs ({42 - per_cell} per category×strategy cell), with zero overlap and a "
        f"{len(fallback_pair_ids | complement_pair_ids)}-pair union. It costs approximately "
        f"${complement_expected['total_cost_usd']:.3f} at 600 output tokens/job or at most "
        f"${complement_maximum['total_cost_usd']:.3f} before retries at the continuation cap. It cannot "
        "run without new explicit paid approval.",
        "",
        "The strict JSON schema constrains only the response format already required by the frozen rubric. "
        "Reasoning effort is unchanged; prompt caching is automatic provider-side upside and contributes "
        f"$0 to the budget case. The {MAX_OUTPUT_TOKENS}-token Batch cap includes reasoning tokens and "
        "exceeds both historical "
        "local GPT-5 Mini response-judge completions (614 and 577 tokens).",
        "",
    ]
    (output_dir / "budget_design_summary.md").write_text(
        "\n".join(summary), encoding="utf-8"
    )
    write_manifest(output_dir, snapshot)
    print(
        f"Phase D budget design complete: full batch max=${batch_maximum['total_cost_usd']:.3f}; "
        f"standard fallback={len(fallback_rows)} responses; 0 API calls"
    )


if __name__ == "__main__":
    main()
