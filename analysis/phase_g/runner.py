"""Phase G runner scaffolding: resumable, idempotent, checkpointed, budget-limited.

**This module never makes a paid call unless both --execute-paid-calls and
--paid-approval-confirmed are supplied.** Without them it validates the plan,
prints what it would do, and exits. No Phase G experiment has been executed.

Design constraints, from the historical record: earlier phases were interrupted
by provider rate limits, credit exhaustion and machine shutdown. A restart must
never repeat a completed call.

Guarantees
----------
deterministic job IDs   a job's identity is a hash of its semantic content, so
                        the same job always maps to the same ledger key
completed-job ledger    append-only JSONL; a completed job is skipped on restart
idempotence             re-running after any interruption converges to the same
                        artifact set without duplicate billing
retry ceiling           per-job attempt cap; exhausted jobs are recorded as
                        infrastructure failures, never as experimental outcomes
failure separation      an infra failure is never written as a score
live cost accounting    every billed call is appended before the next is issued
hard budget stop        the run aborts cleanly before exceeding the ceiling
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "analysis/phase_g/config/phase_g.yaml"


class Stage(str, Enum):
    GENERATE_U = "generate_u"
    CERTIFY_PRIMARY = "certify_primary"
    CERTIFY_SECONDARY = "certify_secondary"
    TARGET_INFERENCE = "target_inference"
    JUDGE_U = "judge_u"


class Outcome(str, Enum):
    COMPLETED = "completed"
    INFRA_FAILURE = "infra_failure"      # never an experimental result
    REFUSED_BY_GATE = "refused_by_gate"  # a real experimental outcome
    SKIPPED_LEDGER = "skipped_ledger"


def job_id(stage: Stage, **parts: str) -> str:
    """Deterministic, content-addressed job identity.

    Depends only on semantic content, never on wall-clock time, ordering or
    attempt number, so an interrupted run maps its retries onto the same key.
    """
    payload = "|".join(f"{k}={parts[k]}" for k in sorted(parts))
    return hashlib.sha256(f"phase-g|{stage.value}|{payload}".encode()).hexdigest()[:32]


@dataclass
class BudgetGuard:
    """Live cost accounting with a hard stop."""

    ceiling_usd: float
    spent_usd: float = 0.0
    committed_usd: float = 0.0

    def would_exceed(self, estimated_usd: float) -> bool:
        return self.spent_usd + self.committed_usd + estimated_usd > self.ceiling_usd

    def reserve(self, estimated_usd: float) -> None:
        if self.would_exceed(estimated_usd):
            raise BudgetExceeded(
                f"reserving ${estimated_usd:.4f} would exceed the ${self.ceiling_usd:.2f} "
                f"ceiling (spent ${self.spent_usd:.4f}, committed ${self.committed_usd:.4f})"
            )
        self.committed_usd += estimated_usd

    def settle(self, estimated_usd: float, actual_usd: float) -> None:
        self.committed_usd = max(0.0, self.committed_usd - estimated_usd)
        self.spent_usd += actual_usd
        if self.spent_usd > self.ceiling_usd:
            raise BudgetExceeded(
                f"actual spend ${self.spent_usd:.4f} exceeded the ${self.ceiling_usd:.2f} ceiling"
            )


class BudgetExceeded(RuntimeError):
    """Raised to abort cleanly with the ledger intact."""


@dataclass
class Ledger:
    """Append-only completed-job ledger. Written before the next call is issued."""

    path: Path
    _done: dict[str, dict[str, Any]] = field(default_factory=dict)

    def load(self) -> "Ledger":
        self._done.clear()
        if self.path.exists():
            with self.path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("outcome") in (Outcome.COMPLETED.value, Outcome.REFUSED_BY_GATE.value):
                        self._done[row["job_id"]] = row
        return self

    def is_done(self, key: str) -> bool:
        return key in self._done

    def get(self, key: str) -> dict[str, Any] | None:
        return self._done.get(key)

    def record(self, row: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        if row.get("outcome") in (Outcome.COMPLETED.value, Outcome.REFUSED_BY_GATE.value):
            self._done[row["job_id"]] = row

    @property
    def completed(self) -> int:
        return len(self._done)


def run_jobs(
    jobs: Iterable[dict[str, Any]],
    execute: Callable[[dict[str, Any]], dict[str, Any]],
    ledger: Ledger,
    budget: BudgetGuard,
    *,
    retry_ceiling: int = 3,
    estimate_usd: float = 0.006,
) -> dict[str, int]:
    """Execute jobs idempotently under a hard budget.

    `execute` returns {"ok": bool, "cost_usd": float, "payload": ...}. It is
    called at most `retry_ceiling` times per job. A job that never succeeds is
    recorded as an infrastructure failure and is explicitly not a result.
    """
    counts = {o.value: 0 for o in Outcome}
    for job in jobs:
        key = job["job_id"]
        if ledger.is_done(key):
            counts[Outcome.SKIPPED_LEDGER.value] += 1
            continue

        last_error: str | None = None
        for attempt in range(1, retry_ceiling + 1):
            budget.reserve(estimate_usd)
            try:
                result = execute(job)
            except BudgetExceeded:
                raise
            except Exception as exc:  # noqa: BLE001
                budget.settle(estimate_usd, 0.0)
                last_error = f"{type(exc).__name__}: {exc}"
                continue
            budget.settle(estimate_usd, float(result.get("cost_usd", 0.0)))
            if result.get("ok"):
                outcome = result.get("outcome", Outcome.COMPLETED.value)
                ledger.record({
                    "job_id": key, "stage": job["stage"], "attempt": attempt,
                    "outcome": outcome, "cost_usd": result.get("cost_usd", 0.0),
                    "payload": result.get("payload"),
                })
                counts[outcome] += 1
                break
            last_error = str(result.get("error", "unspecified failure"))
        else:
            ledger.record({
                "job_id": key, "stage": job["stage"], "attempt": retry_ceiling,
                "outcome": Outcome.INFRA_FAILURE.value, "cost_usd": 0.0,
                "error": last_error,
            })
            counts[Outcome.INFRA_FAILURE.value] += 1
    return counts


def load_config(path: Path) -> dict[str, Any]:
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def plan_jobs(config: dict[str, Any], selection: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Enumerate every job the run would issue. Pure; makes no call."""
    jobs: list[dict[str, Any]] = []
    for row in selection:
        pid = row["pair_id"]
        jobs.append({"stage": Stage.GENERATE_U.value, "pair_id": pid,
                     "job_id": job_id(Stage.GENERATE_U, pair_id=pid)})
        jobs.append({"stage": Stage.CERTIFY_PRIMARY.value, "pair_id": pid,
                     "job_id": job_id(Stage.CERTIFY_PRIMARY, pair_id=pid)})
        jobs.append({"stage": Stage.CERTIFY_SECONDARY.value, "pair_id": pid,
                     "job_id": job_id(Stage.CERTIFY_SECONDARY, pair_id=pid)})
        for model in config["target_models"]:
            jobs.append({"stage": Stage.TARGET_INFERENCE.value, "pair_id": pid, "model": model,
                         "job_id": job_id(Stage.TARGET_INFERENCE, pair_id=pid, model=model)})
            jobs.append({"stage": Stage.JUDGE_U.value, "pair_id": pid, "model": model,
                         "job_id": job_id(Stage.JUDGE_U, pair_id=pid, model=model)})
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase G runner (preparation only by default)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--ledger", type=Path, default=ROOT / "runs/phase_g/ledger.jsonl")
    parser.add_argument("--execute-paid-calls", action="store_true")
    parser.add_argument("--paid-approval-confirmed", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    manifest = json.loads((ROOT / config["selection_manifest"]).read_text(encoding="utf-8"))
    selection = [{"pair_id": p} for p in manifest["selected_pair_ids"]]
    jobs = plan_jobs(config, selection)

    by_stage: dict[str, int] = {}
    for job in jobs:
        by_stage[job["stage"]] = by_stage.get(job["stage"], 0) + 1

    ledger = Ledger(args.ledger).load()
    print(json.dumps({
        "phase": "G",
        "status": config["status"],
        "n_base_pairs": config["n_base_pairs"],
        "planned_jobs": len(jobs),
        "jobs_by_stage": by_stage,
        "unique_job_ids": len({j["job_id"] for j in jobs}),
        "already_completed_in_ledger": ledger.completed,
        "expected_cost_usd": config["expected_cost_usd"],
        "hard_ceiling_usd": config["hard_ceiling_usd"],
    }, indent=2))

    if not (args.execute_paid_calls and args.paid_approval_confirmed):
        print("\nPREPARATION ONLY. Both --execute-paid-calls and "
              "--paid-approval-confirmed are required to issue any billed call.")
        print("No Phase G experiment has been executed.")
        return 0

    raise SystemExit(
        "Refusing to execute: Phase G stage implementations are intentionally not "
        "wired to a provider client in this preparation commit. Executing the "
        "preregistered experiment requires a separate, explicitly authorized change."
    )


if __name__ == "__main__":
    raise SystemExit(main())
