"""Phase G preparation tests. Synthetic fixtures only; no network, no API call."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Register before exec: @dataclass resolves annotations via sys.modules.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = _load("phase_g_runner", "analysis/phase_g/runner.py")


# ---------------------------------------------------------------- job identity

def test_job_ids_are_deterministic_and_content_addressed():
    a = runner.job_id(runner.Stage.TARGET_INFERENCE, pair_id="abc", model="m1")
    b = runner.job_id(runner.Stage.TARGET_INFERENCE, model="m1", pair_id="abc")
    assert a == b, "job identity must not depend on keyword ordering"
    assert a != runner.job_id(runner.Stage.TARGET_INFERENCE, pair_id="abc", model="m2")
    assert a != runner.job_id(runner.Stage.JUDGE_U, pair_id="abc", model="m1")


def test_planned_jobs_are_unique_and_correctly_sized():
    config = runner.load_config(ROOT / "analysis/phase_g/config/phase_g.yaml")
    manifest = json.loads((ROOT / config["selection_manifest"]).read_text(encoding="utf-8"))
    selection = [{"pair_id": p} for p in manifest["selected_pair_ids"]]
    jobs = runner.plan_jobs(config, selection)
    n = config["n_base_pairs"]
    models = len(config["target_models"])
    assert len(jobs) == n * 3 + n * models * 2
    assert len({j["job_id"] for j in jobs}) == len(jobs)


# ---------------------------------------------------------------- budget guard

def test_budget_guard_blocks_before_exceeding_ceiling():
    guard = runner.BudgetGuard(ceiling_usd=1.0)
    guard.reserve(0.6)
    guard.settle(0.6, 0.6)
    with pytest.raises(runner.BudgetExceeded):
        guard.reserve(0.5)
    assert guard.spent_usd == pytest.approx(0.6)


def test_budget_guard_releases_reservation_on_failure():
    guard = runner.BudgetGuard(ceiling_usd=1.0)
    guard.reserve(0.4)
    guard.settle(0.4, 0.0)          # call failed, nothing billed
    assert guard.committed_usd == pytest.approx(0.0)
    assert guard.spent_usd == pytest.approx(0.0)


# ---------------------------------------------------------------- idempotence

def _jobs(n: int) -> list[dict]:
    return [
        {"stage": runner.Stage.GENERATE_U.value, "pair_id": f"p{i}",
         "job_id": runner.job_id(runner.Stage.GENERATE_U, pair_id=f"p{i}")}
        for i in range(n)
    ]


def test_completed_jobs_are_skipped_after_restart(tmp_path):
    ledger = runner.Ledger(tmp_path / "ledger.jsonl").load()
    guard = runner.BudgetGuard(ceiling_usd=10.0)
    calls: list[str] = []

    def execute(job):
        calls.append(job["job_id"])
        return {"ok": True, "cost_usd": 0.001, "payload": {"pair_id": job["pair_id"]}}

    first = runner.run_jobs(_jobs(5), execute, ledger, guard)
    assert first[runner.Outcome.COMPLETED.value] == 5
    assert len(calls) == 5

    # Simulate a restart: fresh ledger object over the same file, fresh budget.
    resumed = runner.Ledger(tmp_path / "ledger.jsonl").load()
    second = runner.run_jobs(_jobs(5), execute, resumed, runner.BudgetGuard(ceiling_usd=10.0))
    assert second[runner.Outcome.SKIPPED_LEDGER.value] == 5
    assert len(calls) == 5, "a restart must not re-issue completed calls"


def test_partial_run_resumes_without_duplicate_billing(tmp_path):
    ledger = runner.Ledger(tmp_path / "ledger.jsonl").load()
    guard = runner.BudgetGuard(ceiling_usd=0.0035)   # room for three calls only
    issued: list[str] = []

    def execute(job):
        issued.append(job["job_id"])
        return {"ok": True, "cost_usd": 0.001}

    with pytest.raises(runner.BudgetExceeded):
        runner.run_jobs(_jobs(10), execute, ledger, guard, estimate_usd=0.001)
    done_first = len(issued)
    assert 0 < done_first < 10

    resumed = runner.Ledger(tmp_path / "ledger.jsonl").load()
    runner.run_jobs(_jobs(10), execute, resumed, runner.BudgetGuard(ceiling_usd=10.0),
                    estimate_usd=0.001)
    assert len(issued) == 10, "every job runs exactly once across the interruption"


# ------------------------------------------------- infra failure vs experiment

def test_infra_failure_is_not_recorded_as_a_result(tmp_path):
    ledger = runner.Ledger(tmp_path / "ledger.jsonl").load()

    def always_fails(job):
        raise ConnectionError("provider 429")

    counts = runner.run_jobs(_jobs(2), always_fails, ledger,
                             runner.BudgetGuard(ceiling_usd=10.0), retry_ceiling=3)
    assert counts[runner.Outcome.INFRA_FAILURE.value] == 2
    rows = [json.loads(l) for l in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert all(r["outcome"] == runner.Outcome.INFRA_FAILURE.value for r in rows)
    assert all("payload" not in r for r in rows), "a failed call must carry no result"
    # Infra failures are not 'done', so a later run retries them.
    assert runner.Ledger(tmp_path / "ledger.jsonl").load().completed == 0


def test_gate_refusal_is_a_real_outcome_and_is_not_retried(tmp_path):
    ledger = runner.Ledger(tmp_path / "ledger.jsonl").load()
    attempts: list[str] = []

    def refused(job):
        attempts.append(job["job_id"])
        return {"ok": True, "cost_usd": 0.001,
                "outcome": runner.Outcome.REFUSED_BY_GATE.value, "payload": {"reason": "axis"}}

    counts = runner.run_jobs(_jobs(3), refused, ledger, runner.BudgetGuard(ceiling_usd=10.0))
    assert counts[runner.Outcome.REFUSED_BY_GATE.value] == 3
    resumed = runner.Ledger(tmp_path / "ledger.jsonl").load()
    runner.run_jobs(_jobs(3), refused, resumed, runner.BudgetGuard(ceiling_usd=10.0))
    assert len(attempts) == 3, "a certified refusal is a result and must not be re-issued"


def test_retry_ceiling_is_respected(tmp_path):
    ledger = runner.Ledger(tmp_path / "ledger.jsonl").load()
    attempts: list[str] = []

    def flaky(job):
        attempts.append(job["job_id"])
        return {"ok": False, "error": "timeout"}

    runner.run_jobs(_jobs(1), flaky, ledger, runner.BudgetGuard(ceiling_usd=10.0),
                    retry_ceiling=3)
    assert len(attempts) == 3


# ---------------------------------------------------------------- selection

def test_selection_is_deterministic_balanced_and_nested():
    manifests = {}
    for n in (72, 96, 120):
        path = ROOT / f"analysis/phase_g/selection_n{n}_MANIFEST.json"
        manifests[n] = json.loads(path.read_text(encoding="utf-8"))
        assert manifests[n]["n_base_pairs"] == n
        assert manifests[n]["selection_is_outcome_independent"] is True
        assert len(manifests[n]["selected_pair_ids"]) == n
        assert len(set(manifests[n]["selected_pair_ids"])) == n
        assert set(manifests[n]["cell_counts"].values()) == {n // 12}
        assert len(manifests[n]["cell_counts"]) == 12
    a, b, c = (set(manifests[n]["selected_pair_ids"]) for n in (72, 96, 120))
    assert a < b < c, "selections must nest so the design can be extended"


def test_selection_never_reads_outcome_fields():
    source = (ROOT / "analysis/phase_g/select_base_pairs.py").read_text(encoding="utf-8")
    for forbidden in ("scores.jsonl", "flips.jsonl", "phase_d_run_archive",
                      "human_validation", "reconciliation_key"):
        assert forbidden not in source, f"selection must not reference {forbidden}"


def test_selection_reproduces_frozen_bytes_without_overwriting_them(tmp_path, monkeypatch):
    select = _load("phase_g_selection_reproduction", "analysis/phase_g/select_base_pairs.py")
    if not select.BANK.exists():
        pytest.skip("byte reproduction requires the gated frozen bank")
    monkeypatch.setattr(select, "ROOT", tmp_path)
    monkeypatch.setattr(select, "OUT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["select_base_pairs.py", "--n", "96"])
    assert select.main() == 0
    for suffix in (".csv", "_MANIFEST.json"):
        filename = f"selection_n96{suffix}"
        assert (tmp_path / filename).read_bytes() == (ROOT / "analysis/phase_g" / filename).read_bytes()


# ---------------------------------------------------------------- guard rails

def test_runner_refuses_to_execute_without_both_approval_flags():
    source = (ROOT / "analysis/phase_g/runner.py").read_text(encoding="utf-8")
    assert "--execute-paid-calls" in source and "--paid-approval-confirmed" in source
    assert "Refusing to execute" in source


def test_config_declares_not_executed_and_a_ceiling():
    config = runner.load_config(ROOT / "analysis/phase_g/config/phase_g.yaml")
    assert config["status"] == "PREREGISTERED_NOT_EXECUTED"
    assert config["hard_ceiling_usd"] >= config["expected_high_cost_usd"]
    assert config["abort_on_ceiling"] is True
    assert config["arms"]["E"] == "reuse_frozen" and config["arms"]["R"] == "reuse_frozen"
    assert config["arms"]["U"] == "new"
