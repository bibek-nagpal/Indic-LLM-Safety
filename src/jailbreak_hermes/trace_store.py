"""TraceStore — per-run, append-only JSONL writer.

One directory per batch (`runs/run_<YYYYMMDD_HHMMSS>/`) with these
files:

  traces.jsonl              one line per attempt — full record
  candidates_redacted.jsonl one line per accepted candidate, redacted
  scores.jsonl              one line per (model, language) scoring
  flips.jsonl               one line per FlipRecord
  report.md                 the human-readable report

Records are dataclass-friendly: pass any dict-like object and we
write JSON.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from ._jsonable import to_jsonable


class TraceStore:
    def __init__(self, runs_root: str | Path = "runs", run_id: str | None = None):
        self.runs_root = Path(runs_root)
        self.run_id = run_id or time.strftime("run_%Y%m%d_%H%M%S")
        self.dir = self.runs_root / self.run_id
        self.dir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        return self.dir / name

    def append(self, name: str, record: Any) -> None:
        p = self.path(name)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(to_jsonable(record), ensure_ascii=False) + "\n")

    def write_text(self, name: str, text: str) -> Path:
        p = self.path(name)
        p.write_text(text, encoding="utf-8")
        return p

    def list_records(self, name: str) -> list[dict]:
        p = self.path(name)
        if not p.exists():
            return []
        out: list[dict] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out
