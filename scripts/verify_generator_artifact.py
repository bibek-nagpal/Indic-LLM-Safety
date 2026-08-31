"""Fail-closed verification of the frozen generator-guidance artifact.

Checks that the tracked generator instruction is byte-identical to the one whose
SHA-256 the frozen bank manifest recorded, and that the persisted harness state
supports the manuscript's description: a fixed, hand-specified instruction that
the target-independent probe-validity metric did not revise.

Reads only committed artifacts. Makes no API call and writes nothing.
"""

from __future__ import annotations

import hashlib
import io
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "prompts" / "optimized" / "gepa_20260826_135819"
EXPECTED_INSTRUCTION_SHA256 = (
    "025fbd3573fc018b3291a51a19acb456df3fd79a3725a1b29610dd89bcd5ce3b"
)
FROZEN_BANK_MANIFEST = (
    ROOT
    / "frozen_final_2026_08_29"
    / "bank"
    / "revision_v2_3_1_final_504_dedup"
    / "manifest.json"
)


class _Stub:
    def __init__(self, *args, **kwargs) -> None:  # noqa: D107
        pass


class _TolerantUnpickler(pickle.Unpickler):
    """Load the harness state without importing DSPy."""

    def find_class(self, module: str, name: str):  # noqa: D102
        try:
            return super().find_class(module, name)
        except Exception:  # noqa: BLE001
            return _Stub


def check(condition: bool, message: str, failures: list[str]) -> None:
    print(f"  [{'PASS' if condition else 'FAIL'}] {message}")
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    print("Generator-artifact verification")

    instruction_path = ARTIFACT / "generator.txt"
    check(instruction_path.exists(), "tracked generator.txt exists", failures)
    if not instruction_path.exists():
        return 1

    # Read as text so CRLF/LF checkouts hash identically, matching
    # probe_bank.build_bank, which hashes optimized_prompt.load_optimized_instruction().
    instruction = instruction_path.read_text(encoding="utf-8")
    digest = hashlib.sha256(instruction.encode("utf-8")).hexdigest()
    check(
        digest == EXPECTED_INSTRUCTION_SHA256,
        f"generator.txt SHA-256 == {EXPECTED_INSTRUCTION_SHA256} (got {digest})",
        failures,
    )

    if FROZEN_BANK_MANIFEST.exists():
        manifest = json.loads(FROZEN_BANK_MANIFEST.read_text(encoding="utf-8"))
        check(
            manifest.get("gepa_instruction_sha256") == digest,
            "frozen bank manifest gepa_instruction_sha256 matches the tracked instruction",
            failures,
        )
        check(
            manifest.get("gepa_target_signal_used") is False
            and manifest.get("target_models_used_during_generation") == [],
            "frozen bank manifest records no target-model signal during generation",
            failures,
        )
    else:
        print("  [SKIP] frozen bank manifest not present (gated snapshot); hash check only")

    optimization_manifest = json.loads(
        (ARTIFACT / "optimization_manifest.json").read_text(encoding="utf-8")
    )
    check(
        optimization_manifest.get("objective")
        == "complete_target_independent_probe_validity",
        "optimization_manifest declares the 13-constraint target-independent objective",
        failures,
    )
    check(
        optimization_manifest.get("target_model_signal_used") is False
        and optimization_manifest.get("judge_signal_used") is False,
        "optimization_manifest declares no target-model and no judge signal",
        failures,
    )

    records = [
        json.loads(line)
        for line in (ARTIFACT / "metric_log.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    check(len(records) > 0, f"metric_log.jsonl has records (n={len(records)})", failures)
    check(
        all(record.get("target_model_called") is False for record in records),
        "every development-set evaluation record has target_model_called == false",
        failures,
    )

    accepted = sum(1 for record in records if record.get("accepted") is True)
    check(
        (len(records), accepted) == (30, 24),
        f"development-set evaluations match the manuscript (30 evaluations, 24 accepted; got {len(records)}, {accepted})",
        failures,
    )
    accounting = json.loads((ARTIFACT / "api_accounting.json").read_text(encoding="utf-8"))
    check(
        abs(float(accounting["known_cost_usd"]) - 0.03017940) < 1e-8,
        f"validation cost matches the manuscript (USD 0.030; got {accounting['known_cost_usd']})",
        failures,
    )

    state = _TolerantUnpickler(
        io.BytesIO((ARTIFACT / "gepa_logs" / "gepa_state.bin").read_bytes())
    ).load()
    candidates = state.get("program_candidates", [])
    parents = state.get("parent_program_for_candidate", [])
    check(
        len(candidates) == 1,
        f"harness state holds exactly one program candidate (n={len(candidates)})",
        failures,
    )
    check(
        bool(parents) and all(parent is None for parent in parents[0]),
        "the single candidate is the seed (no parent program)",
        failures,
    )
    seed_text = candidates[0].get("generate", "") if candidates else ""
    check(
        seed_text.strip() == instruction.strip(),
        "the seed candidate text equals the tracked generator.txt",
        failures,
    )
    subscores = state.get("prog_candidate_val_subscores", [])
    check(
        bool(subscores) and len(subscores[0]) == 12,
        f"development set has 12 items (got {len(subscores[0]) if subscores else 0})",
        failures,
    )
    pareto = json.loads((ARTIFACT / "pareto_summary.json").read_text(encoding="utf-8"))
    check(
        all(pareto.get(key) is None for key in ("best_val_score", "best_aggregate_score", "num_iter")),
        "pareto summary records no accepted revision (all fields null)",
        failures,
    )

    superseded = ROOT / "prompts" / "optimized" / "_superseded_v1_gepa_20260523_130239"
    if superseded.exists():
        superseded_digest = hashlib.sha256(
            (superseded / "generator.txt").read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()
        check(
            superseded_digest != EXPECTED_INSTRUCTION_SHA256,
            "the superseded V1 artifact is distinct from the frozen instruction",
            failures,
        )
        check(
            not (superseded / "optimization_manifest.json").exists(),
            "the superseded V1 artifact is correctly ineligible (no optimization_manifest.json)",
            failures,
        )

    if failures:
        print(f"\nFAILED: {len(failures)} check(s)")
        return 1
    print("\nAll generator-artifact checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
