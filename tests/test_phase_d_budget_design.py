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

    for mode in ("standard", "batch"):
        expected = report[mode]["expected_600_output_tokens_per_job"]
        assert abs(
            expected["input_cost_usd"]
            + expected["output_cost_usd"]
            - expected["total_cost_usd"]
        ) < 1e-12


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
    for pair_id, model, _, _ in pair_models:
        languages = {
            row["language"]
            for row in jobs
            if row["pair_id"] == pair_id and row["target_model"] == model
        }
        assert languages == {"en", "rh"}
