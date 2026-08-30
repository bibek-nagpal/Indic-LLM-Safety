from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_cross_judge_standard_budget import (
    budget_commitment,
    known_actual_cost,
    maximum_job_cost,
    next_token_cap,
    parse_judgment,
)


def _valid() -> dict[str, object]:
    return {
        "gate_a": True,
        "gate_b": True,
        "gate_c": False,
        "score": 2,
        "rationale": "Specific but incomplete.",
        "disclaimers_present": False,
        "framing_used": "none",
    }


def test_standard_strict_parser_accepts_exact_logical_schema() -> None:
    payload = _valid()
    parsed = parse_judgment(
        json.dumps(payload),
        json_loader=lambda content, expected_keys: json.loads(content),
    )
    assert parsed == payload


@pytest.mark.parametrize(
    "change",
    [
        {"score": 3},
        {"gate_a": "true"},
        {"framing_used": "invalid"},
        {"extra": "field"},
    ],
)
def test_standard_strict_parser_rejects_invalid_results(
    change: dict[str, object],
) -> None:
    with pytest.raises(RuntimeError):
        parse_judgment(
            json.dumps({**_valid(), **change}),
            json_loader=lambda content, expected_keys: json.loads(content),
        )


def test_standard_budget_keeps_ambiguous_reservations() -> None:
    state = {
        "attempts": [
            {"actual_cost_usd": None, "reserved_max_cost_usd": 0.01},
            {"actual_cost_usd": 0.02, "reserved_max_cost_usd": 0.03},
            {"actual_cost_usd": 0.0, "reserved_max_cost_usd": 0.04},
        ]
    }
    assert budget_commitment(state) == pytest.approx(0.03)
    assert known_actual_cost(state) == pytest.approx(0.02)


def test_reasoning_only_truncation_gets_one_larger_cap() -> None:
    plan = {
        "max_judge_tokens": 768,
        "continuation_max_judge_tokens": 1024,
        "truncation_repair_max_judge_tokens": 1280,
    }
    state = {
        "attempts": [
            {
                "job_id": "job",
                "status": "completed_parse_error",
                "max_tokens_used": 768,
                "truncation_repair_eligible": True,
                "usage": {
                    "completion_tokens": 768,
                    "completion_tokens_details": {"reasoning_tokens": 768},
                },
            }
        ]
    }
    assert next_token_cap("job", state, plan) == 1024
    state["attempts"][0]["max_tokens_used"] = 1024
    assert next_token_cap("job", state, plan) == 1280
    state["attempts"][0]["max_tokens_used"] = 1280
    with pytest.raises(RuntimeError):
        next_token_cap("job", state, plan)


def test_unattempted_continuation_uses_live_validated_cap() -> None:
    plan = {
        "max_judge_tokens": 768,
        "continuation_max_judge_tokens": 1024,
        "truncation_repair_max_judge_tokens": 1280,
    }
    assert next_token_cap("new-job", {"attempts": []}, plan) == 1024


def test_partial_json_truncation_is_repairable_from_token_evidence() -> None:
    plan = {
        "max_judge_tokens": 768,
        "continuation_max_judge_tokens": 1024,
        "truncation_repair_max_judge_tokens": 1280,
    }
    state = {
        "attempts": [
            {
                "job_id": "job",
                "status": "completed_parse_error",
                "max_tokens_used": 768,
                "truncation_repair_eligible": False,
                "usage": {
                    "completion_tokens": 768,
                    "completion_tokens_details": {"reasoning_tokens": 640},
                },
            }
        ]
    }
    assert next_token_cap("job", state, plan) == 1024


def test_repair_cost_uses_actual_cap() -> None:
    job = {"costed_input_tokens": 1000}
    plan = {
        "max_judge_tokens": 768,
        "pricing": {
            "input_usd_per_million_tokens": 0.25,
            "output_usd_per_million_tokens": 2.0,
        },
    }
    assert maximum_job_cost(job, plan, max_tokens=1024) == pytest.approx(0.002298)
