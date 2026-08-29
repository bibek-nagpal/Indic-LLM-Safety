"""Experiment memory — long-lived, cross-run, redacted JSONL stores.

These files survive across runs and feed back into category lessons
and judge-disagreement audits. They explicitly DO NOT store raw
harmful procedures, slurs as reusable payloads, or full unredacted
prompt text.

Layout (intent doc, §4.I):

  memory/
    category_lessons.jsonl
    failed_mutations.jsonl
    successful_patterns_redacted.jsonl
    judge_disagreements.jsonl
    retrieval_sources.jsonl
    model_quirks.jsonl
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ._jsonable import to_jsonable

ALLOWED_STORES = {
    "category_lessons",
    "failed_mutations",
    "successful_patterns_redacted",
    "judge_disagreements",
    "retrieval_sources",
    "model_quirks",
}


class Memory:
    def __init__(self, root: str | Path = "memory"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, store: str, record: dict) -> None:
        if store not in ALLOWED_STORES:
            raise ValueError(f"unknown memory store {store!r}; allowed: {sorted(ALLOWED_STORES)}")
        record = dict(record)
        record.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
        p = self.root / f"{store}.jsonl"
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(to_jsonable(record), ensure_ascii=False) + "\n")

    def tail(self, store: str, n: int = 20) -> list[dict]:
        if store not in ALLOWED_STORES:
            raise ValueError(f"unknown memory store {store!r}")
        p = self.root / f"{store}.jsonl"
        if not p.exists():
            return []
        lines = p.read_text(encoding="utf-8").splitlines()[-n:]
        return [json.loads(line) for line in lines if line.strip()]


def redacted_pattern_record(
    *,
    category: str,
    strategy: str,
    model: str,
    en_score: int,
    rh_score: int,
    flip: bool,
    critical_flip: bool,
    equivalence_score: float,
    judge_rationale_summary: str,
    notes: str = "",
) -> dict:
    """Build a redacted summary safe to keep across runs.

    Note: by design this record does NOT contain the actual prompt text
    or the model output. Full text lives only in `runs/<run_id>/traces.jsonl`,
    which is gitignored.
    """
    return {
        "category": category,
        "strategy": strategy,
        "model": model,
        "en_score": en_score,
        "rh_score": rh_score,
        "flip": flip,
        "critical_flip": critical_flip,
        "equivalence_score": equivalence_score,
        "judge_rationale_summary": judge_rationale_summary[:400],
        "notes": notes,
    }
