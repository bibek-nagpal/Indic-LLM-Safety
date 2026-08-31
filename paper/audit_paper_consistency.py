"""Fail-closed consistency checks for the canonical V2 manuscript.

This script intentionally reads only frozen manifests and validated analysis
outputs.  It never reads secrets, calls a model, or changes an experiment.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "acl_latex.tex"


def load_csv(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def close(actual: str | float, expected: float, tolerance: float = 5e-8) -> None:
    value = float(actual)
    assert abs(value - expected) <= tolerance, (value, expected)


def require(text: str, fragment: str) -> None:
    assert fragment in text, f"Missing manuscript evidence: {fragment!r}"


def main() -> None:
    manuscript = PAPER.read_text(encoding="utf-8")

    # Frozen experiment identity and immutable counts.
    freeze = load_json("frozen_final_2026_08_29/FREEZE_MANIFEST.json")
    assert freeze["bank_id"] == "revision_v2_3_1_final_504_dedup"
    assert freeze["canonical_bank_sha256"] == (
        "35bfbc1d09e78b77c24d62bbf41783cc9b297dd25f1bba3fe6062d53dc2028ed"
    )
    require(manuscript, "504 unique pairs")
    require(manuscript, "1,512 pair-model observations")
    require(manuscript, "3,024 responses")
    require(manuscript, freeze["bank_id"])
    require(manuscript, freeze["canonical_bank_sha256"])

    # Phase B headline estimates and paired flip counts.
    main_rows = {row["model_display"]: row for row in load_csv("analysis/results/main_results.csv")}
    expected_main = {
        "Qwen3-30B-A3B": (43.05555556, 38.49206349, 47.61904762, 219, 7, 85, 2),
        "GPT-OSS-20B": (4.563492063, 1.388888889, 7.738095238, 42, 21, 15, 6),
        "Nemotron-3-Nano": (-1.785714286, -6.547619048, 2.777777778, 65, 70, 22, 10),
    }
    for model, values in expected_main.items():
        row = main_rows[model]
        assert int(row["n_pairs"]) == 504
        close(row["refusal_gap_pp"], values[0])
        close(row["refusal_gap_ci_low_pp"], values[1])
        close(row["refusal_gap_ci_high_pp"], values[2])
        assert [int(row[key]) for key in (
            "forward_flip_count", "reverse_flip_count",
            "critical_forward_count", "critical_reverse_count",
        )] == list(values[3:])
    for fragment in (
        "43.06 percentage points", "38.49--47.62", "4.56", "1.39--7.74",
        "$-1.79$", "$-6.55$--2.78", "219 forward versus 7 reverse",
        "42 forward versus 21 reverse", "65 forward versus 70 reverse",
    ):
        require(manuscript, fragment)

    tests = load_json("analysis/results/statistical_tests.json")
    interaction = tests["gee"]["language_by_model_interaction_wald"]
    close(interaction["statistic"], 165.8295016522695)
    close(interaction["p_value"], 9.78546004081666e-37, 1e-48)
    require(manuscript, "$\\chi^2_2=165.83$")

    # Phase C judge-independent directional signal.
    length_rows = {
        row["model_display"]: row
        for row in load_csv("analysis/phase_c_results/length_results.csv")
    }
    assert {
        model: (int(row["forward_count"]), int(row["reverse_count"]))
        for model, row in length_rows.items()
    } == {
        "Qwen3-30B-A3B": (203, 0),
        "GPT-OSS-20B": (59, 16),
        "Nemotron-3-Nano": (56, 120),
    }
    require(manuscript, "Qwen has 203 forward-shaped and 0 reverse-shaped pairs")
    require(manuscript, "GPT-OSS 59 and 16, and Nemotron 56 and 120")

    # Phase D completion, accounting, agreement, and matched judge replacement.
    integrity = load_json("analysis/phase_d_results/integrity_report.json")
    assert integrity["overall_status"] == "PASS"
    assert integrity["valid_scores"] == 1944
    assert integrity["remaining_jobs"] == 0
    assert integrity["target_inference_calls"] == 0
    close(integrity["budget_committed_usd"], 3.67896645, 1e-12)
    assert all(integrity["checks"].values())
    require(manuscript, "1,944 response judgments")
    require(manuscript, "USD 3.67896645 under a USD 4.50 ceiling")

    agreement = {
        row["scope"]: row
        for row in load_csv("analysis/phase_d_results/agreement_overall.csv")
    }["gemini_only"]
    close(agreement["exact_agreement"], 0.736489964)
    close(agreement["adjacent_agreement"], 0.9135357694)
    close(agreement["unweighted_kappa"], 0.541291832)
    close(agreement["quadratic_weighted_kappa"], 0.8125875828)
    for fragment in ("73.65\\%", "91.35\\%", "$\\kappa=.541$", "$\\kappa=.813$"):
        require(manuscript, fragment)

    replacement_rows = load_csv("analysis/phase_d_results/judge_replacement_main_results.csv")
    replacement = {(r["judge"], r["model_display"]): r for r in replacement_rows}
    expected_gaps = {
        ("Gemini-primary pipeline", "Qwen3-30B-A3B"): 42.59259259,
        ("GPT-5 Mini", "Qwen3-30B-A3B"): 43.51851852,
        ("Gemini-primary pipeline", "GPT-OSS-20B"): 2.777777778,
        ("GPT-5 Mini", "GPT-OSS-20B"): 3.395061728,
        ("Gemini-primary pipeline", "Nemotron-3-Nano"): -1.543209877,
        ("GPT-5 Mini", "Nemotron-3-Nano"): -8.333333333,
    }
    for key, expected in expected_gaps.items():
        row = replacement[key]
        assert int(row["n_pairs"]) == 324
        close(row["refusal_gap_pp"], expected)

    # Phase E is a prepared protocol, never represented as a completed result.
    human = load_json("human_validation/HUMAN_VALIDATION_MANIFEST.json")
    assert human["schema_version"] == 2
    assert human["selection_used_automated_scores"] is False
    assert human["selected_pair_model_jobs"] == 180
    assert human["response_items_per_annotator"] == 360
    assert human["unique_pair_ids"] == 180
    assert human["annotators"] == 2
    assert human["same_items_for_both_annotators"] is True
    assert human["coverage_fraction_of_pair_model_grid"] == 0.119
    assert human["familiarization_disjoint_from_analysis_sample"] is True
    assert human["familiarization_reference_labels_distributed"] is False
    assert human["cluster_unit_for_analysis"] == "pair-model job"
    assert set(human["stratum_counts_pair_model_jobs"].values()) == {5}
    assert len(human["stratum_counts_pair_model_jobs"]) == 36
    minimum_separation = human["min_positions_between_language_items_of_a_job"]
    assert minimum_separation == 10
    for observed in human["observed_separation_by_annotator"].values():
        assert observed["min"] >= minimum_separation
    require(manuscript, "180 pair-model jobs")
    require(manuscript, "11.9\\% of the 1,512-job grid")
    require(manuscript, "360 response items per annotator")
    require(manuscript, "No human labels were available")

    # Obsolete V1 constructs must not re-enter the canonical manuscript.
    forbidden = (
        r"Logical\s*Appeal", r"LogicalAppeal", r"35\.9\\?%", r"152\s*:\s*0",
        r"1,512 certified pairs", r"target-conditioned prompt",
    )
    forbidden = forbidden + (
        r"three distinct regimes",
        r"optimize supplementary generator guidance",
        r"prompt-guidance evolution",
    )
    for pattern in forbidden:
        assert not re.search(pattern, manuscript, re.IGNORECASE), f"Obsolete claim: {pattern}"

    # The generator guidance is described as fixed and hand-specified, and the
    # released artifact is the one the frozen bank manifest hashed.
    require(manuscript, "The guidance is hand-specified")
    require(manuscript, "returned no accepted revision to the guidance")
    instruction = (
        ROOT / "prompts/optimized/gepa_20260826_135819/generator.txt"
    ).read_text(encoding="utf-8")
    instruction_sha256 = hashlib.sha256(instruction.encode("utf-8")).hexdigest()
    bank_manifest = load_json(
        "frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/manifest.json"
    )
    assert instruction_sha256 == bank_manifest["gepa_instruction_sha256"], instruction_sha256
    require(manuscript, instruction_sha256)
    optimization = load_json(
        "prompts/optimized/gepa_20260826_135819/optimization_manifest.json"
    )
    assert optimization["objective"] == "complete_target_independent_probe_validity"
    assert optimization["target_model_signal_used"] is False

    # Non-assistance terminology and the score-0 profile behind it.
    assert "refusal gap" not in manuscript
    require(manuscript, "non-assistance gap")
    profile = {
        (row["model"], row["language"]): row
        for row in load_csv("analysis/sensitivity_results/nonassistance_profile.csv")
    }
    qwen_en = profile[("Qwen3-30B-A3B", "English")]
    qwen_rh = profile[("Qwen3-30B-A3B", "Hinglish/RH")]
    close(qwen_en["under_80_pct"], 61.1, 5e-2)
    assert int(qwen_rh["n_score_zero"]) == 115 and int(qwen_rh["under_80_chars"]) == 0
    require(manuscript, "61.1\\% of \\qwen's English score-0 responses are under 80 characters")

    # Post-audit sensitivity analyses quoted in the manuscript.
    similarity = load_json("analysis/sensitivity_results/near_duplicate_similarity.json")
    assert similarity["n_pairs_compared"] == 42084
    close(similarity["mean"], 0.09348469955953735, 1e-9)
    assert similarity["counts_at_or_above"]["0.85"] == 5
    require(manuscript, "42{,}084 within-strategy pairs")
    require(manuscript, "five at or above the gate")
    require(manuscript, "5 pairs sit at or above the 0.85 gate")

    truncation = {
        row["model"]: row
        for row in load_csv("analysis/sensitivity_results/truncation_sensitivity.csv")
    }
    assert (int(truncation["Qwen3-30B-A3B"]["en_truncated"]),
            int(truncation["Qwen3-30B-A3B"]["rh_truncated"])) == (0, 22)
    close(truncation["Qwen3-30B-A3B"]["untruncated_gap_pp"], 43.361, 5e-4)
    close(truncation["GPT-OSS-20B"]["untruncated_gap_pp"], 4.7281, 5e-4)
    close(truncation["Nemotron-3-Nano"]["untruncated_gap_pp"], -0.4988, 5e-4)
    require(manuscript, "43.36, 4.73, and $-0.50$ pp")

    decomposition = {
        (row["model"], row["stratum"]): row
        for row in load_csv("analysis/sensitivity_results/phase_c_decomposition.csv")
    }
    both_safe = "both non-assisting (0/0)"
    assert int(decomposition[("Qwen3-30B-A3B", both_safe)]["forward_shaped"]) == 65
    assert int(decomposition[("Qwen3-30B-A3B", both_safe)]["reverse_shaped"]) == 0
    assert int(decomposition[("Nemotron-3-Nano", both_safe)]["reverse_shaped"]) == 58
    assert int(decomposition[("Qwen3-30B-A3B", "forward flip")]["forward_shaped"]) == 136
    require(manuscript, "65:0 for \\qwen, 22:2 for \\gptoss, 12:58 for \\nemo")

    cross_cells = {
        (row["model"], row["language"]): row
        for row in load_csv("analysis/sensitivity_results/cross_judge_agreement_by_cell.csv")
    }
    close(cross_cells[("Qwen3-30B-A3B", "Hinglish/RH")]["exact_agreement_pct"], 53.09, 5e-3)
    close(cross_cells[("GPT-OSS-20B", "English")]["exact_agreement_pct"], 89.81, 5e-3)
    require(manuscript, "53.1\\% for \\qwen English and RH")

    subset_contrasts = {
        (row["judge"], row["contrast"]): row
        for row in load_csv("analysis/sensitivity_results/cross_judge_subset_contrasts.csv")
    }
    gemini_contrast = subset_contrasts[
        ("Gemini-primary pipeline", "GPT-OSS-20B - Nemotron-3-Nano")
    ]
    close(gemini_contrast["estimate_pp"], 4.321, 5e-4)
    require(manuscript, "4.32 pp ($-2.78$--11.73)")

    bowker = load_json("analysis/results/statistical_tests.json")["per_model"]
    close(bowker["nvidia/nemotron-3-nano-30b-a3b"]["bowker"]["p_value"], 0.0188, 5e-5)
    close(bowker["qwen/qwen3-30b-a3b-instruct-2507"]["bowker"]["statistic"], 215.21, 5e-3)
    require(manuscript, "$p=.019$, nominal")

    # Every citation key resolves locally, and the compatibility source cannot diverge.
    cited: set[str] = set()
    for group in re.findall(r"\\cite\w*\{([^}]+)\}", manuscript):
        cited.update(key.strip() for key in group.split(","))
    bibliography = (ROOT / "paper" / "references.bib").read_text(encoding="utf-8")
    available = set(re.findall(r"@\w+\{\s*([^,\s]+)", bibliography))
    assert cited <= available, f"Missing bibliography keys: {sorted(cited - available)}"
    wrapper = (ROOT / "paper" / "draft2_aug.tex").read_text(encoding="utf-8")
    assert "\\input{acl_latex.tex}" in wrapper
    assert "\\documentclass" not in wrapper

    for figure in (
        "v2_model_refusal_gap.png", "v2_score_transition_matrices.png",
        "v2_length_directional_counts.png", "v2_judge_replacement_refusal_gaps.png",
    ):
        assert (ROOT / "paper" / "figures" / figure).is_file(), figure

    print("PASS: canonical manuscript matches frozen Phase A--E evidence and bibliography.")


if __name__ == "__main__":
    main()
