"""Offline evidence audit of the preparation checkpoint, never an execution runner.

Reads frozen inputs without rewriting them; uses only synthetic callbacks for
ledger fault injection. No provider client, credentials, human labels, generation,
or stochastic published analysis is loaded. Writes a separate audit JSON report.
Exit 1 means the independently checked preparation is not ready for execution.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_checks():
    reports = []
    for relative in (
        "frozen_final_2026_08_29/FREEZE_MANIFEST.json",
        "analysis/results/ANALYSIS_MANIFEST.json",
        "analysis/phase_c_results/PHASE_C_MANIFEST.json",
        "analysis/phase_d_run_archive/RUN_ARCHIVE_MANIFEST.json",
        "analysis/phase_d_results/PHASE_D_MANIFEST.json",
        "analysis/sensitivity_results/SENSITIVITY_MANIFEST.json",
    ):
        path = ROOT / relative
        manifest = read_json(path)
        files = manifest.get("files")
        if files is None:
            files = [{"path": k, "sha256": v} for k, v in manifest["outputs"].items()]
        mismatch = [r["path"] for r in files if digest(path.parent / r["path"]) != r["sha256"]]
        reports.append({"manifest": relative, "checked": len(files), "mismatches": mismatch})
    return reports


def selection_check():
    select = load_module("phase_g_selection_audit", "analysis/phase_g/select_base_pairs.py")
    qc = load_module("phase_g_qc_audit", "analysis/qc_final.py")
    manifest_path = ROOT / "analysis/phase_g/selection_n96_MANIFEST.json"
    manifest = read_json(manifest_path)
    bank = qc.load_jsonl(select.BANK)
    bank_manifest = read_json(select.BANK_MANIFEST)
    cells = collections.defaultdict(list)
    for row in bank:
        c = row["candidate"]
        cells[c["category"], c["strategy"]].append(row["pair_id"])
    rows, assignment_counts = [], collections.Counter()
    for (category, strategy), ids in sorted(cells.items()):
        ranked = sorted(ids, key=lambda p: select.rank_key(p, category, strategy))[:8]
        for rank, pair_id in enumerate(ranked):
            rows.append(dict(pair_id=pair_id, category=category, strategy=strategy))
            assignment_counts[f"{category}::{strategy}::{rank % 2}"] += 1
    rows.sort(key=lambda r: r["pair_id"])
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=("pair_id", "category", "strategy"))
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = buf.getvalue().encode("utf-8")
    csv_path = manifest_path.parent / manifest["selection_csv"]
    expected = dict(manifest)
    expected.update(
        selected_pair_ids=[r["pair_id"] for r in rows],
        cell_counts={f"{c}::{s}": 8 for c, s in cells},
        frozen_bank_pairs_file_sha256=digest(select.BANK),
        frozen_bank_sha256=qc.bank_sha256(bank),
        selection_csv_sha256=hashlib.sha256(csv_bytes).hexdigest(),
    )
    # Frozen artifacts use LF for JSON and csv's CRLF for CSV.
    json_text = json.dumps(expected, indent=2, sort_keys=True) + "\n"
    expected_bytes = json_text.encode("utf-8")
    checks = {
        "n96_unique": len(rows) == len(set(r["pair_id"] for r in rows)) == 96,
        "12_cells_eight_each": len(cells) == 12 and set(expected["cell_counts"].values()) == {8},
        "selected_ids_match": expected["selected_pair_ids"] == manifest["selected_pair_ids"],
        "csv_reproduced_byte_identically": csv_bytes == csv_path.read_bytes(),
        "manifest_reproduced_byte_identically": expected_bytes == manifest_path.read_bytes(),
        "bank_hash_matches": expected["frozen_bank_sha256"] == bank_manifest["bank_sha256"] == select.EXPECTED_BANK_SHA256,
        "manifest_fields_match": expected == manifest,
        "rank_allocation_balanced": len(assignment_counts) == 24 and set(assignment_counts.values()) == {4},
    }
    return {"checks": checks, "sub_register_assignment_status": "rederived from rule, not persisted by prepared runner"}


def literal_interpretations(low, high):
    """Literal transcription of the four rows; deliberately supplies no default."""
    labels = []
    if high < 0.5:
        labels.append("register_specific_dominant")
    if low > 0.5:
        labels.append("generic_ood_dominant")
    if low <= 0.5 <= high and not low <= 0 <= high and not low <= 1 <= high:
        labels.append("mixed")
    if low <= 0 and high >= 1:
        labels.append("inconclusive")
    return labels


def reuse_mapping_check():
    """Separate from selection: join the frozen, already selected E/R scores."""
    manifest = read_json(ROOT / "analysis/phase_g/selection_n96_MANIFEST.json")
    config = load_module("phase_g_reuse_runner", "analysis/phase_g/runner.py").load_config(
        ROOT / "analysis/phase_g/config/phase_g.yaml")
    run_dir = ROOT / "frozen_final_2026_08_29/run/revision_v2_targets_final"
    frozen_config = read_json(run_dir / "run_manifest.json")
    scores = [json.loads(line) for line in (run_dir / "scores.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = set(manifest["selected_pair_ids"])
    rows = [r for r in scores if r["pair_id"] in selected]
    keys = [(r["pair_id"], r["model"], r["language"]) for r in rows]
    expected = {(p, m, language) for p in selected for m in config["target_models"] for language in ("en", "rh")}
    counts = {}
    for model in config["target_models"]:
        counts[model] = {language: sum(r["score"] == 0 for r in rows if r["model"] == model and r["language"] == language) for language in ("en", "rh")}
    return {"selected_response_score_keys": len(keys), "keys_unique_and_complete": len(keys) == len(set(keys)) == 576 and set(keys) == expected,
            "model_ids_match_frozen": set(config["target_models"]) == set(frozen_config["target_models"]),
            "target_settings_match_frozen": all(config[k] == frozen_config[k] for k in ("target_temperature", "max_target_tokens", "empty_target_system_prompt")),
            "judge_and_cap_match_frozen": config["primary_judge"] == frozen_config["judge_model"] and config["max_judge_tokens"] == frozen_config["max_judge_tokens"],
            "existing_non_assistance_counts_per_96": counts,
            "selection_uses_this_join": False}


def runner_faults(base):
    runner = load_module("phase_g_runner_audit", "analysis/phase_g/runner.py")

    def job(n):
        return {"stage": "generate_u", "job_id": runner.job_id(runner.Stage.GENERATE_U, pair_id=str(n))}

    result = {}
    ledger = runner.Ledger(base / "restart.jsonl").load()
    def good(_):
        return {"ok": True, "cost_usd": 0.6}
    runner.run_jobs([job(0)], good, ledger, runner.BudgetGuard(1), estimate_usd=0.6)
    runner.run_jobs([job(1)], good, runner.Ledger(ledger.path).load(), runner.BudgetGuard(1), estimate_usd=0.6)
    result["restart_spend"] = {"ceiling": 1, "persisted_total": sum(json.loads(l)["cost_usd"] for l in ledger.path.read_text().splitlines())}

    ledger = runner.Ledger(base / "failed_billing.jsonl").load()
    replies = iter([{"ok": False, "cost_usd": 0.2, "error": "synthetic parse error"}, {"ok": True, "cost_usd": 0.1}])
    guard = runner.BudgetGuard(1)
    runner.run_jobs([job(0)], lambda _: next(replies), ledger, guard, estimate_usd=0.2)
    result["billed_failure"] = {"in_memory_spent": guard.spent_usd, "persisted_spent": sum(json.loads(l)["cost_usd"] for l in ledger.path.read_text().splitlines())}

    ledger = runner.Ledger(base / "overrun.jsonl").load()
    guard = runner.BudgetGuard(0.1)
    try:
        runner.run_jobs([job(0)], lambda _: {"ok": True, "cost_usd": 0.2, "payload": "synthetic success"}, ledger, guard, estimate_usd=0.01)
    except runner.BudgetExceeded:
        pass
    result["under_reservation"] = {"ceiling": 0.1, "already_billed": guard.spent_usd, "successes_persisted": runner.Ledger(ledger.path).load().completed}

    ledger = runner.Ledger(base / "attempts.jsonl").load()
    attempts = []
    def fails(_):
        attempts.append(1)
        return {"ok": False, "cost_usd": 0}
    for _ in range(2):
        runner.run_jobs([job(0)], fails, runner.Ledger(ledger.path).load(), runner.BudgetGuard(1), retry_ceiling=3)
    result["retry_restart"] = {"ceiling": 3, "attempts": len(attempts)}

    ledger = runner.Ledger(base / "crash.jsonl").load()
    received = []
    def interrupted(_):
        received.append(1)  # synthetic provider completed work; result not saved
        raise KeyboardInterrupt("synthetic interruption")
    try:
        runner.run_jobs([job(0)], interrupted, ledger, runner.BudgetGuard(1), retry_ceiling=1)
    except KeyboardInterrupt:
        pass
    def resumed(_):
        received.append(1)
        return {"ok": True, "cost_usd": 0.1}
    runner.run_jobs([job(0)], resumed, runner.Ledger(ledger.path).load(), runner.BudgetGuard(1))
    result["crash_after_remote_completion"] = {"remote_completions": len(received), "completed_jobs": ledger.load().completed, "pending_marker_before_restart": False}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "analysis/phase_g/preflight_20260903.json")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="phase-g-audit-") as scratch:
        faults = runner_faults(Path(scratch))
    manifests = manifest_checks()
    selection = selection_check()
    cost = read_json(ROOT / "analysis/phase_g/cost_model.json")
    scenario = cost["scenarios"]["expected"]
    success = scenario["primary_pass"] * scenario["secondary_pass"]
    coverage = 1 - (1 - success) ** 4
    output = {
        "audit_kind": "offline_preflight_not_experimental_outcomes",
        "head_at_audit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "audited_scientific_input_hashes": {name: digest(ROOT / "analysis/phase_g" / name) for name in (
            "PREREGISTRATION.md", "STATISTICAL_ANALYSIS_PLAN.md", "config/phase_g.yaml",
            "selection_n96_MANIFEST.json", "selection_n96.csv", "runner.py", "cost_model.py", "cost_model.json", "design_power.py", "design_power.json")},
        "api_calls": 0,
        "api_cost_usd": 0,
        "manifests": manifests,
        "selection": selection,
        "reuse_mapping": reuse_mapping_check(),
        "synthetic_runner_faults": faults,
        "interpretation_counterexamples": [{"ci": [lo, hi], "matching_rows": literal_interpretations(lo, hi)} for lo, hi in [(-0.1, 0.75), (0.25, 1.1), (0, 0.5), (0.5, 1)]],
        "cost_funnel_internal_consistency": {
            "scenario_only_not_a_yield_prediction": True,
            "preregistered_n": 96,
            "generation_calls_expected_scenario": cost["designs"]["expected|N=96|dual=True|xjudge=False"]["calls"]["generation"],
            "pass_probability_per_attempt_if_independent": success,
            "expected_certifications_in_211_2_attempts_if_independent": 211.2 * success,
            "per_pair_success_with_four_attempts_if_independent": coverage,
            "expected_filled_of_96_if_independent": 96 * coverage,
            "probability_all_96_filled_if_independent": coverage ** 96,
        },
        "verdict": "FAIL_EXECUTION_PREFLIGHT",
        "scientific_decisions_required": [
            "Operationalize and freeze the manipulation gate and bounded strengthening procedure, including its interaction with the four-attempt cap.",
            "Complete the interpretation table and ratio-denominator policy before outcomes; do not select a rule from observed results.",
        ],
        "execution_status": "Not started; provider refusal guard deliberately preserved.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": output["verdict"], "manifest_files_checked": sum(m["checked"] for m in manifests), "manifest_mismatches": sum(len(m["mismatches"]) for m in manifests), "selection_checks": selection["checks"], "api_calls": 0, "output": str(args.output)}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
