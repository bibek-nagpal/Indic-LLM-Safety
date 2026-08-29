from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_cross_judge import load_existing_scores


def _job() -> dict[str, object]:
    return {
        "job_id": "job-1",
        "pair_id": "pair-1",
        "target_model": "target/model",
        "language": "en",
        "category": "category",
        "strategy": "strategy",
        "prompt_sha256": "a" * 64,
        "response_sha256": "b" * 64,
        "rubric_sha256": "c" * 64,
        "judge_messages_sha256": "d" * 64,
        "judge_model": "judge/model",
    }


def test_resume_accepts_only_a_valid_plan_bound_score(tmp_path: Path) -> None:
    job = _job()
    score = {
        **job,
        "score": 2,
        "logical_consistency_ok": True,
        "parse_error": None,
    }
    path = tmp_path / "scores.jsonl"
    path.write_text(json.dumps(score) + "\n", encoding="utf-8")
    loaded = load_existing_scores(path, {"job-1": job})
    assert loaded["job-1"]["score"] == 2


def test_resume_rejects_changed_identity_metadata(tmp_path: Path) -> None:
    job = _job()
    score = {
        **job,
        "language": "rh",
        "score": 2,
        "logical_consistency_ok": True,
        "parse_error": None,
    }
    path = tmp_path / "scores.jsonl"
    path.write_text(json.dumps(score) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="identity mismatch"):
        load_existing_scores(path, {"job-1": job})
