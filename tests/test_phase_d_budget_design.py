from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DESIGN_DIR = REPO / "analysis" / "phase_d_budget_design"


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_full_batch_fits_but_full_standard_does_not() -> None:
    report = json.loads((DESIGN_DIR / "cost_analysis.json").read_text(encoding="utf-8"))
    assert report["jobs"] == 3024
    assert report["pair_model_jobs"] == 1512
    assert report["hard_budget_usd"] == 4.50
    assert report["standard"]["full_run_fits_hard_budget_at_maximum"] is False
    assert report["standard"]["maximum_1024_output_tokens_per_job"]["total_cost_usd"] > 4.50
    assert report["batch"]["full_run_fits_hard_budget_at_maximum"] is True
    assert report["batch"]["maximum_1024_output_tokens_per_job"]["total_cost_usd"] < 4.50
    assert report["batch"]["conservative_retry_allowance_usd"] > 0.65
    assert report["costing_assumptions"]["prompt_cache_savings_assumed_usd"] == 0.0
    assert report["active_recommendation"] == "standard_fallback_shared_pairs"
    assert report["batch_live_validation_available"] is False

    for mode in ("standard", "batch"):
        expected = report[mode]["expected_600_output_tokens_per_job"]
        assert abs(
            expected["input_cost_usd"]
            + expected["output_cost_usd"]
            - expected["total_cost_usd"]
        ) < 1e-12
    batch_plan = json.loads(
        (DESIGN_DIR / "gpt5mini_batch_full_plan.json").read_text(encoding="utf-8")
    )
    assert batch_plan["status"] == "unavailable_after_live_smoke_validation"


def test_full_jobs_are_complete_hash_only_identifiers() -> None:
    jobs = _jsonl(DESIGN_DIR / "gpt5mini_batch_full_jobs.jsonl")
    assert len(jobs) == 3024
    assert len({row["job_id"] for row in jobs}) == 3024
    assert len({(row["pair_id"], row["target_model"]) for row in jobs}) == 1512
    assert Counter(row["language"] for row in jobs) == {"en": 1512, "rh": 1512}
    forbidden = {"prompt", "response", "messages", "content", "rationale"}
    assert all(not (forbidden & set(row)) for row in jobs)
    assert all(len(str(row["batch_request_sha256"])) == 64 for row in jobs)


def test_standard_contingency_is_balanced_in_every_cell() -> None:
    jobs = _jsonl(DESIGN_DIR / "gpt5mini_standard_fallback_jobs.jsonl")
    pair_models = {
        (row["pair_id"], row["target_model"], row["category"], row["strategy"])
        for row in jobs
    }
    cells = Counter((model, category, strategy) for _, model, category, strategy in pair_models)
    assert len(jobs) == 1944
    assert len(pair_models) == 972
    assert len(cells) == 36
    assert set(cells.values()) == {27}
    pair_ids_by_model_cell: dict[tuple[str, str, str], set[object]] = {}
    for model, category, strategy in cells:
        pair_ids_by_model_cell[(model, category, strategy)] = {
            pair_id
            for pair_id, row_model, row_category, row_strategy in pair_models
            if (row_model, row_category, row_strategy) == (model, category, strategy)
        }
    for category, strategy in {(cell[1], cell[2]) for cell in cells}:
        selections = {
            frozenset(pair_ids_by_model_cell[(model, category, strategy)])
            for model in {cell[0] for cell in cells}
        }
        assert len(selections) == 1
    for pair_id, model, _, _ in pair_models:
        languages = {
            row["language"]
            for row in jobs
            if row["pair_id"] == pair_id and row["target_model"] == model
        }
        assert languages == {"en", "rh"}

    plan = json.loads(
        (DESIGN_DIR / "gpt5mini_standard_fallback_plan.json").read_text(encoding="utf-8")
    )
    assert plan["status"] == "recommended_after_batch_unavailable"
    assert plan["request_contract"]["response_format"]["json_schema"]["strict"] is True
    assert "temperature" not in plan["request_contract"]
    assert plan["request_contract"]["seed"] == 20260829
    assert plan["maximum_no_retry_cost_usd"] + plan["retry_reserve_usd"] < 4.50
    assert plan["max_judge_tokens"] == 768
    assert plan["truncation_repair_max_judge_tokens"] == 1024
    report = json.loads((DESIGN_DIR / "cost_analysis.json").read_text(encoding="utf-8"))
    repair = report["standard_fallback"]["adaptive_truncation_repair"]
    assert repair["rubric_or_reasoning_effort_change"] is False
    assert repair["conservative_whole_job_repairs_within_reserve"] >= 80


def test_deferred_complement_is_exactly_disjoint_and_complete() -> None:
    selected = _jsonl(DESIGN_DIR / "gpt5mini_standard_fallback_jobs.jsonl")
    complement = _jsonl(DESIGN_DIR / "gpt5mini_standard_complement_jobs.jsonl")
    selected_pairs = {row["pair_id"] for row in selected}
    complement_pairs = {row["pair_id"] for row in complement}
    assert len(selected_pairs) == 324
    assert len(complement_pairs) == 180
    assert selected_pairs.isdisjoint(complement_pairs)
    assert len(selected_pairs | complement_pairs) == 504
    assert len(complement) == 1080
    pair_models = {
        (row["pair_id"], row["target_model"], row["category"], row["strategy"])
        for row in complement
    }
    cells = Counter((model, category, strategy) for _, model, category, strategy in pair_models)
    assert len(pair_models) == 540
    assert len(cells) == 36
    assert set(cells.values()) == {15}
    for pair_id, model, _, _ in pair_models:
        assert {
            row["language"]
            for row in complement
            if row["pair_id"] == pair_id and row["target_model"] == model
        } == {"en", "rh"}

    plan = json.loads(
        (DESIGN_DIR / "gpt5mini_standard_complement_plan.json").read_text(encoding="utf-8")
    )
    assert plan["status"] == "deferred_until_additional_budget_approved"
    assert plan["requires_new_explicit_paid_approval"] is True
    assert plan["overlapping_pair_ids"] == 0
    assert plan["combined_pair_ids"] == 504
