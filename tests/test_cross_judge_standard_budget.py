from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_cross_judge_standard_budget import budget_commitment, parse_judgment


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
