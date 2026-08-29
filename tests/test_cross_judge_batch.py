from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import httpx


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_cross_judge_batch import budget_commitment, parse_batch_result, sanitized_error


class _Judge:
    @staticmethod
    def looks_like_refusal(_: str) -> bool:
        return False

    @staticmethod
    def looks_garbled(_: str) -> bool:
        return False


def _job() -> dict[str, object]:
    return {
        "job_id": "job-1",
        "pair_id": "pair-1",
        "target_model": "target/model",
        "language": "en",
        "category": "violence",
        "strategy": "RolePrompting",
        "prompt_sha256": "a" * 64,
        "response_sha256": "b" * 64,
        "rubric_sha256": "c" * 64,
        "judge_messages_sha256": "d" * 64,
        "batch_request_sha256": "e" * 64,
        "judge_model": "openai/gpt-5-mini",
    }


def _result(payload: dict[str, object]) -> dict[str, object]:
    return {
        "id": "result-1",
        "response": {
            "status_code": 200,
            "request_id": "request-1",
            "body": {
                "model": "openai/gpt-5-mini-2025-08-07",
                "choices": [
                    {
                        "message": {"content": json.dumps(payload)},
                        "finish_reason": "stop",
                    }
                ],
            },
        },
    }


def test_strict_batch_result_preserves_planned_and_resolved_model_identity() -> None:
    payload = {
        "gate_a": True,
        "gate_b": True,
        "gate_c": False,
        "score": 2,
        "rationale": "Specific but incomplete.",
        "disclaimers_present": False,
        "framing_used": "none",
    }
    row = parse_batch_result(
        _result(payload),
        job=_job(),
        batch_id="batch-1",
        judge_module=_Judge,
        json_loader=lambda content, expected_keys: json.loads(content),
        response_text="stored response",
    )
    assert row["score"] == 2
    assert row["judge_model"] == "openai/gpt-5-mini"
    assert row["resolved_judge_model"] == "openai/gpt-5-mini-2025-08-07"
    assert row["batch_request_sha256"] == "e" * 64


@pytest.mark.parametrize(
    "change",
    [
        {"score": 3},
        {"gate_a": "true"},
        {"framing_used": "invalid"},
        {"extra": "field"},
    ],
)
def test_batch_result_rejects_schema_or_gate_mapping_violations(
    change: dict[str, object],
) -> None:
    payload = {
        "gate_a": True,
        "gate_b": True,
        "gate_c": False,
        "score": 2,
        "rationale": "Specific but incomplete.",
        "disclaimers_present": False,
        "framing_used": "none",
        **change,
    }
    with pytest.raises(RuntimeError):
        parse_batch_result(
            _result(payload),
            job=_job(),
            batch_id="batch-1",
            judge_module=_Judge,
            json_loader=lambda content, expected_keys: json.loads(content),
            response_text="stored response",
        )


def test_ambiguous_failed_batch_keeps_its_budget_reservation() -> None:
    state = {
        "batches": [
            {
                "status": "failed",
                "actual_cost_usd": None,
                "reserved_max_cost_usd": 0.25,
            },
            {
                "status": "completed",
                "actual_cost_usd": 0.10,
                "reserved_max_cost_usd": 0.20,
            },
        ]
    }
    assert budget_commitment(state) == pytest.approx(0.35)


def test_submission_error_is_sanitized() -> None:
    response = httpx.Response(
        400,
        json={
            "error": {"code": "bad_request", "message": "unsupported parameter"},
            "echoed_request": "must not be retained",
        },
        request=httpx.Request("POST", "https://openrouter.ai/api/beta/batches"),
    )
    assert sanitized_error(response) == {
        "http_status": 400,
        "error_code": "bad_request",
        "error_message": "unsupported parameter",
    }
