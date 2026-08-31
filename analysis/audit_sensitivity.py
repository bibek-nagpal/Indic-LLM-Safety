"""Phase B/C/D sensitivity analyses added after the independent audit.

Reads only the frozen snapshot and the committed Phase D archive. Makes no API
call and never writes to a frozen artifact. Outputs feed the manuscript
appendices on prompt-similarity clustering, response truncation, response
length, the non-assistance construct, and cross-judge agreement structure.

Usage (from the repository root):
    python analysis/audit_sensitivity.py
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import itertools
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import binomtest, spearmanr, wilcoxon

BANK_ID = "revision_v2_3_1_final_504_dedup"
RUN_ID = "revision_v2_targets_final"
MODELS = (
    "qwen/qwen3-30b-a3b-instruct-2507",
    "openai/gpt-oss-20b",
    "nvidia/nemotron-3-nano-30b-a3b",
)
MODEL_NAMES = {
    MODELS[0]: "Qwen3-30B-A3B",
    MODELS[1]: "GPT-OSS-20B",
    MODELS[2]: "Nemotron-3-Nano",
}
CONTRASTS = ((0, 1), (0, 2), (1, 2))
JACCARD_THRESHOLDS = (0.80, 0.70, 0.65, 0.60, 0.55, 0.50)
SHORT_CHARS = 80
LONG_CHARS = 500
SEED = 20260829
N_BOOT = 10_000
N_PERM = 100_000


# --------------------------------------------------------------------------
# loading


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dedupe_traces(traces: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    """Keep the last trace per (pair_id, model): retries follow failed attempts."""
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for trace in traces:
        latest[(trace["pair_id"], trace["model"])] = trace
    return latest


# --------------------------------------------------------------------------
# prompt similarity


def normalise_for_gate(text: str) -> str:
    """Exactly probe_bank._norm_for_similarity."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def token_set(text: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z']+", text.casefold()))


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = len(left | right)
    return len(left & right) / union if union else 0.0


def native_gate_statistics(bank: list[dict[str, Any]]) -> dict[str, Any]:
    """Duplication measured with the metric the generation-time gate uses."""
    rows = []
    for record in bank:
        candidate = record["candidate"]
        rows.append(
            {
                "pair_id": record["pair_id"],
                "category": candidate["category"],
                "strategy": candidate["strategy"],
                "en": normalise_for_gate(candidate["english_prompt"]),
                "rh": normalise_for_gate(candidate["romanized_hindi_prompt"]),
            }
        )
    by_strategy: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        by_strategy[row["strategy"]].append(row)

    similarities: list[float] = []
    residual: list[dict[str, Any]] = []
    for strategy, group in by_strategy.items():
        for left, right in itertools.combinations(group, 2):
            similarity = max(
                SequenceMatcher(None, left["en"], right["en"]).ratio(),
                SequenceMatcher(None, left["rh"], right["rh"]).ratio(),
            )
            similarities.append(similarity)
            if similarity >= 0.85:
                residual.append(
                    {
                        "similarity": similarity,
                        "strategy": strategy,
                        "left_pair_id": left["pair_id"],
                        "right_pair_id": right["pair_id"],
                        "left_category": left["category"],
                        "right_category": right["category"],
                    }
                )
    values = np.asarray(similarities)
    residual.sort(key=lambda item: -item["similarity"])
    return {
        "metric": "difflib.SequenceMatcher ratio on probe_bank-normalised text, max(EN, RH)",
        "scope": "all within-strategy pairs of the final bank",
        "gate_threshold": 0.85,
        "gate_scope_at_generation": "within a single bank build, within strategy",
        "n_pairs_compared": int(values.size),
        "mean": float(values.mean()),
        "p99": float(np.percentile(values, 99)),
        "max": float(values.max()),
        "counts_at_or_above": {
            f"{threshold:.2f}": int((values >= threshold).sum())
            for threshold in (0.90, 0.85, 0.80, 0.75, 0.70)
        },
        "residual_pairs_at_or_above_gate": residual,
    }


def template_clusters(
    pair_ids: list[str],
    english: dict[str, frozenset[str]],
    romanized: dict[str, frozenset[str]],
    threshold: float,
) -> list[list[str]]:
    """Connected components joined by lexical overlap in either language."""
    parent = {pair_id: pair_id for pair_id in pair_ids}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for left, right in itertools.combinations(pair_ids, 2):
        if (
            jaccard(english[left], english[right]) >= threshold
            or jaccard(romanized[left], romanized[right]) >= threshold
        ):
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parent[right_root] = left_root

    groups: dict[str, list[str]] = collections.defaultdict(list)
    for pair_id in pair_ids:
        groups[find(pair_id)].append(pair_id)
    return list(groups.values())


def cluster_bootstrap(
    gaps: dict[str, np.ndarray],
    groups: list[np.ndarray],
    rng: np.random.Generator,
    n_boot: int,
) -> dict[str, np.ndarray]:
    """Ratio-estimator bootstrap resampling whole clusters."""
    n_clusters = len(groups)
    sizes = np.asarray([len(group) for group in groups], dtype=float)
    draws = rng.integers(0, n_clusters, size=(n_boot, n_clusters))
    denominator = sizes[draws].sum(axis=1)
    out = {}
    for model, values in gaps.items():
        sums = np.asarray([values[group].sum() for group in groups])
        out[model] = 100.0 * sums[draws].sum(axis=1) / denominator
    return out


def cluster_sign_flip_p(
    values: np.ndarray, groups: list[np.ndarray], rng: np.random.Generator, n_perm: int
) -> float:
    cluster_sums = np.asarray([values[group].sum() for group in groups])
    observed = abs(values.mean())
    n = values.size
    extreme = 0
    completed = 0
    while completed < n_perm:
        batch = min(5000, n_perm - completed)
        signs = rng.choice(np.array([-1.0, 1.0]), size=(batch, len(groups)))
        extreme += int(np.sum(np.abs(signs @ cluster_sums / n) >= observed))
        completed += batch
    return (extreme + 1) / (n_perm + 1)


# --------------------------------------------------------------------------
# main


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=Path("frozen_final_2026_08_29"))
    parser.add_argument(
        "--gpt-scores",
        type=Path,
        default=Path("analysis/phase_d_run_archive/scores.jsonl"),
    )
    parser.add_argument("--output", type=Path, default=Path("analysis/sensitivity_results"))
    parser.add_argument("--bootstrap-resamples", type=int, default=N_BOOT)
    parser.add_argument("--permutations", type=int, default=N_PERM)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    snapshot = args.snapshot.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    bank_path = snapshot / "bank" / BANK_ID / "pairs.jsonl"
    scores_path = snapshot / "run" / RUN_ID / "scores.jsonl"
    traces_path = snapshot / "run" / RUN_ID / "traces.jsonl"
    for path in (bank_path, scores_path, traces_path, args.gpt_scores):
        if not path.exists():
            raise SystemExit(f"required input missing: {path}")

    bank = load_jsonl(bank_path)
    scores = load_jsonl(scores_path)
    traces = dedupe_traces(load_jsonl(traces_path))
    gpt_scores = load_jsonl(args.gpt_scores)

    if len(bank) != 504 or len(scores) != 3024 or len(traces) != 1512:
        raise SystemExit(
            f"unexpected frozen input sizes: bank={len(bank)} scores={len(scores)} jobs={len(traces)}"
        )

    pair_ids = sorted(record["pair_id"] for record in bank)
    index = {pair_id: position for position, pair_id in enumerate(pair_ids)}
    candidate = {record["pair_id"]: record["candidate"] for record in bank}
    score = {
        (row["pair_id"], row["model"], row["language"]): row for row in scores
    }

    response = {}
    for (pair_id, model), trace in traces.items():
        for language, key in (("en", "english"), ("rh", "romanized_hindi")):
            block = trace[key]
            response[(pair_id, model, language)] = {
                "chars": len(block["content"] or ""),
                "finish_reason": block["finish_reason"],
            }

    seed_sequence = np.random.SeedSequence(args.seed)
    child_seeds = iter(seed_sequence.spawn(16))

    manifest_inputs = {
        "bank_pairs_sha256": sha256_file(bank_path),
        "run_scores_sha256": sha256_file(scores_path),
        "run_traces_sha256": sha256_file(traces_path),
        "phase_d_scores_sha256": sha256_file(args.gpt_scores),
    }

    # ---------------------------------------------------------------- (1)
    gate_stats = native_gate_statistics(bank)
    english_tokens_all = {
        record["pair_id"]: token_set(record["candidate"]["english_prompt"]) for record in bank
    }
    cells: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for record in bank:
        cells[(record["candidate"]["category"], record["candidate"]["strategy"])].append(
            record["pair_id"]
        )
    within_cell = [
        jaccard(english_tokens_all[left], english_tokens_all[right])
        for members in cells.values()
        for left, right in itertools.combinations(members, 2)
    ]
    baseline_rng = np.random.default_rng(next(child_seeds))
    ordered = sorted(english_tokens_all)
    baseline = [
        jaccard(
            english_tokens_all[ordered[int(i)]],
            english_tokens_all[ordered[int(j)]],
        )
        for i, j in baseline_rng.integers(0, len(ordered), size=(5000, 2))
    ]
    gate_stats["bag_of_words_jaccard"] = {
        "note": "token-set Jaccard over English prompts; a permissive proxy for shared scaffolding",
        "within_cell_mean": round(float(np.mean(within_cell)), 4),
        "within_cell_pairs": len(within_cell),
        "within_cell_above_0_62": int(sum(1 for v in within_cell if v > 0.62)),
        "within_cell_max": round(float(np.max(within_cell)), 4),
        "random_cross_bank_mean": round(float(np.mean(baseline)), 4),
    }
    (output_dir / "near_duplicate_similarity.json").write_text(
        json.dumps(gate_stats, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # ---------------------------------------------------------------- (2)
    english_tokens = {
        pair_id: token_set(candidate[pair_id]["english_prompt"]) for pair_id in pair_ids
    }
    romanized_tokens = {
        pair_id: token_set(candidate[pair_id]["romanized_hindi_prompt"])
        for pair_id in pair_ids
    }
    gaps = {
        model: np.asarray(
            [
                float(score[(pair_id, model, "en")]["score"] == 0)
                - float(score[(pair_id, model, "rh")]["score"] == 0)
                for pair_id in pair_ids
            ]
        )
        for model in MODELS
    }

    cluster_rows = []
    for threshold in (None, *JACCARD_THRESHOLDS):
        if threshold is None:
            clusters = [[pair_id] for pair_id in pair_ids]
        else:
            clusters = template_clusters(pair_ids, english_tokens, romanized_tokens, threshold)
        groups = [np.asarray([index[pair_id] for pair_id in cluster]) for cluster in clusters]
        boot = cluster_bootstrap(
            gaps, groups, np.random.default_rng(next(child_seeds)), args.bootstrap_resamples
        )
        permutation_rng = np.random.default_rng(next(child_seeds))
        row: dict[str, Any] = {
            "jaccard_threshold": "none (pair ID)" if threshold is None else f"{threshold:.2f}",
            "n_units": len(clusters),
            "largest_unit": max(len(cluster) for cluster in clusters),
        }
        for model in MODELS:
            low, high = np.percentile(boot[model], [2.5, 97.5])
            name = MODEL_NAMES[model]
            row[f"{name} gap pp"] = round(100 * float(gaps[model].mean()), 4)
            row[f"{name} ci_low"] = round(float(low), 4)
            row[f"{name} ci_high"] = round(float(high), 4)
            row[f"{name} p"] = cluster_sign_flip_p(
                gaps[model], groups, permutation_rng, args.permutations
            )
        for left, right in CONTRASTS:
            label = f"{MODEL_NAMES[MODELS[left]]}-{MODEL_NAMES[MODELS[right]]}"
            difference = boot[MODELS[left]] - boot[MODELS[right]]
            low, high = np.percentile(difference, [2.5, 97.5])
            row[f"{label} pp"] = round(
                100 * float(gaps[MODELS[left]].mean() - gaps[MODELS[right]].mean()), 4
            )
            row[f"{label} ci_low"] = round(float(low), 4)
            row[f"{label} ci_high"] = round(float(high), 4)
            row[f"{label} p"] = cluster_sign_flip_p(
                gaps[MODELS[left]] - gaps[MODELS[right]],
                groups,
                permutation_rng,
                args.permutations,
            )
        cluster_rows.append(row)
    cluster_frame = pd.DataFrame(cluster_rows)
    cluster_frame.to_csv(output_dir / "cluster_sensitivity.csv", index=False)

    # ---------------------------------------------------------------- (3)
    truncation_rows = []
    for model in MODELS:
        english_truncated = {
            pair_id: response[(pair_id, model, "en")]["finish_reason"] == "length"
            for pair_id in pair_ids
        }
        romanized_truncated = {
            pair_id: response[(pair_id, model, "rh")]["finish_reason"] == "length"
            for pair_id in pair_ids
        }
        en_only = sum(
            1 for pair_id in pair_ids if english_truncated[pair_id] and not romanized_truncated[pair_id]
        )
        rh_only = sum(
            1 for pair_id in pair_ids if romanized_truncated[pair_id] and not english_truncated[pair_id]
        )
        discordant = en_only + rh_only
        kept = [
            pair_id
            for pair_id in pair_ids
            if not english_truncated[pair_id] and not romanized_truncated[pair_id]
        ]
        english = np.asarray([score[(p, model, "en")]["score"] for p in kept])
        romanized = np.asarray([score[(p, model, "rh")]["score"] for p in kept])
        full_en = np.asarray([score[(p, model, "en")]["score"] for p in pair_ids])
        full_rh = np.asarray([score[(p, model, "rh")]["score"] for p in pair_ids])
        truncation_rows.append(
            {
                "model": MODEL_NAMES[model],
                "en_truncated": sum(english_truncated.values()),
                "rh_truncated": sum(romanized_truncated.values()),
                "discordant_en_only": en_only,
                "discordant_rh_only": rh_only,
                "discordance_exact_p": float(binomtest(en_only, discordant, 0.5).pvalue)
                if discordant
                else 1.0,
                "full_n": len(pair_ids),
                "full_gap_pp": round(100 * float((full_en == 0).mean() - (full_rh == 0).mean()), 4),
                "full_critical_forward": int(((full_en <= 1) & (full_rh == 3)).sum()),
                "full_critical_reverse": int(((full_rh <= 1) & (full_en == 3)).sum()),
                "untruncated_n": len(kept),
                "untruncated_gap_pp": round(
                    100 * float((english == 0).mean() - (romanized == 0).mean()), 4
                ),
                "untruncated_critical_forward": int(((english <= 1) & (romanized == 3)).sum()),
                "untruncated_critical_reverse": int(((romanized <= 1) & (english == 3)).sum()),
            }
        )
    pd.DataFrame(truncation_rows).to_csv(output_dir / "truncation_sensitivity.csv", index=False)

    # ---------------------------------------------------------------- (4)
    english_chars = np.asarray([len(candidate[p]["english_prompt"]) for p in pair_ids], dtype=float)
    romanized_chars = np.asarray(
        [len(candidate[p]["romanized_hindi_prompt"]) for p in pair_ids], dtype=float
    )
    ratio = romanized_chars / english_chars
    prompt_rows = []
    for model in MODELS:
        forward = np.asarray(
            [
                float(
                    score[(p, model, "en")]["score"] == 0
                    and score[(p, model, "rh")]["score"] >= 2
                )
                for p in pair_ids
            ]
        )
        gap_rho, gap_p = spearmanr(ratio, gaps[model])
        flip_rho, flip_p = spearmanr(ratio, forward)
        terciles = np.digitize(ratio, np.quantile(ratio, [1 / 3, 2 / 3]))
        prompt_rows.append(
            {
                "model": MODEL_NAMES[model],
                "spearman_rho_gap": round(float(gap_rho), 4),
                "spearman_p_gap": round(float(gap_p), 4),
                "spearman_rho_forward_flip": round(float(flip_rho), 4),
                "spearman_p_forward_flip": round(float(flip_p), 4),
                "forward_flip_pct_tercile1": round(100 * float(forward[terciles == 0].mean()), 2),
                "forward_flip_pct_tercile2": round(100 * float(forward[terciles == 1].mean()), 2),
                "forward_flip_pct_tercile3": round(100 * float(forward[terciles == 2].mean()), 2),
            }
        )
    prompt_length = {
        "en_chars_mean": round(float(english_chars.mean()), 2),
        "rh_chars_mean": round(float(romanized_chars.mean()), 2),
        "en_chars_median": float(np.median(english_chars)),
        "rh_chars_median": float(np.median(romanized_chars)),
        "rh_over_en_ratio_mean": round(float(ratio.mean()), 4),
        "rh_over_en_ratio_median": round(float(np.median(ratio)), 4),
        "paired_wilcoxon_p": float(wilcoxon(english_chars, romanized_chars).pvalue),
        "tercile_cutpoints": [round(float(v), 4) for v in np.quantile(ratio, [1 / 3, 2 / 3])],
        "per_model": prompt_rows,
    }
    (output_dir / "prompt_length_null.json").write_text(
        json.dumps(prompt_length, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # ---------------------------------------------------------------- (5)
    def stratum(pair_id: str, model: str) -> str:
        english_score = score[(pair_id, model, "en")]["score"]
        romanized_score = score[(pair_id, model, "rh")]["score"]
        if english_score == 0 and romanized_score == 0:
            return "both non-assisting (0/0)"
        if english_score == 0 and romanized_score >= 2:
            return "forward flip"
        if romanized_score == 0 and english_score >= 2:
            return "reverse flip"
        return "other"

    decomposition_rows = []
    for model in MODELS:
        for name in ("both non-assisting (0/0)", "forward flip", "reverse flip", "other"):
            subset = [p for p in pair_ids if stratum(p, model) == name]
            forward_shaped = sum(
                1
                for p in subset
                if response[(p, model, "en")]["chars"] < SHORT_CHARS
                and response[(p, model, "rh")]["chars"] > LONG_CHARS
            )
            reverse_shaped = sum(
                1
                for p in subset
                if response[(p, model, "rh")]["chars"] < SHORT_CHARS
                and response[(p, model, "en")]["chars"] > LONG_CHARS
            )
            english_lengths = np.asarray([response[(p, model, "en")]["chars"] for p in subset])
            romanized_lengths = np.asarray([response[(p, model, "rh")]["chars"] for p in subset])
            decomposition_rows.append(
                {
                    "model": MODEL_NAMES[model],
                    "stratum": name,
                    "n_pairs": len(subset),
                    "forward_shaped": forward_shaped,
                    "reverse_shaped": reverse_shaped,
                    "en_median_chars": float(np.median(english_lengths)) if subset else 0.0,
                    "rh_median_chars": float(np.median(romanized_lengths)) if subset else 0.0,
                    "directional_exact_p": float(
                        binomtest(forward_shaped, forward_shaped + reverse_shaped, 0.5).pvalue
                    )
                    if forward_shaped + reverse_shaped
                    else 1.0,
                }
            )
    pd.DataFrame(decomposition_rows).to_csv(
        output_dir / "phase_c_decomposition.csv", index=False
    )

    # ---------------------------------------------------------------- (6)
    profile_rows = []
    for model in MODELS:
        for language in ("en", "rh"):
            zeros = [p for p in pair_ids if score[(p, model, language)]["score"] == 0]
            short = sum(1 for p in zeros if response[(p, model, language)]["chars"] < SHORT_CHARS)
            long = sum(1 for p in zeros if response[(p, model, language)]["chars"] > LONG_CHARS)
            regex = sum(
                1 for p in zeros if score[(p, model, language)].get("looks_like_refusal")
            )
            profile_rows.append(
                {
                    "model": MODEL_NAMES[model],
                    "language": "English" if language == "en" else "Hinglish/RH",
                    "n_score_zero": len(zeros),
                    "under_80_chars": short,
                    "under_80_pct": round(100 * short / len(zeros), 1) if zeros else 0.0,
                    "over_500_chars": long,
                    "over_500_pct": round(100 * long / len(zeros), 1) if zeros else 0.0,
                    "matches_english_refusal_regex": regex,
                }
            )
    pd.DataFrame(profile_rows).to_csv(output_dir / "nonassistance_profile.csv", index=False)

    # ---------------------------------------------------------------- (7)
    gpt = {(row["pair_id"], row["target_model"], row["language"]): row for row in gpt_scores}
    cross_pair_ids = sorted({row["pair_id"] for row in gpt_scores})
    agreement_rows = []
    for model in MODELS:
        for language in ("en", "rh"):
            primary, replacement = [], []
            for pair_id in cross_pair_ids:
                key = (pair_id, model, language)
                if key in gpt and score[key]["judge_model"] == "google/gemini-2.5-flash":
                    primary.append(score[key]["score"])
                    replacement.append(gpt[key]["score"])
            primary_array = np.asarray(primary)
            replacement_array = np.asarray(replacement)
            agreement_rows.append(
                {
                    "model": MODEL_NAMES[model],
                    "language": "English" if language == "en" else "Hinglish/RH",
                    "n": int(primary_array.size),
                    "exact_agreement_pct": round(
                        100 * float((primary_array == replacement_array).mean()), 2
                    ),
                    "adjacent_agreement_pct": round(
                        100 * float((np.abs(primary_array - replacement_array) <= 1).mean()), 2
                    ),
                    "mean_replacement_minus_primary": round(
                        float((replacement_array - primary_array).mean()), 4
                    ),
                    "primary_score0_pct": round(100 * float((primary_array == 0).mean()), 2),
                    "replacement_score0_pct": round(
                        100 * float((replacement_array == 0).mean()), 2
                    ),
                    "primary_score3_pct": round(100 * float((primary_array == 3).mean()), 2),
                    "replacement_score3_pct": round(
                        100 * float((replacement_array == 3).mean()), 2
                    ),
                }
            )
    pd.DataFrame(agreement_rows).to_csv(
        output_dir / "cross_judge_agreement_by_cell.csv", index=False
    )

    # ---------------------------------------------------------------- (8)
    subset_rng = np.random.default_rng(next(child_seeds))
    subset_draws = subset_rng.integers(
        0, len(cross_pair_ids), size=(args.bootstrap_resamples, len(cross_pair_ids))
    )
    contrast_rows = []
    for judge_label, getter in (
        ("Gemini-primary pipeline", lambda key: score[key]["score"]),
        ("GPT-5 Mini", lambda key: gpt[key]["score"]),
    ):
        subset_gaps = {
            model: np.asarray(
                [
                    float(getter((p, model, "en")) == 0) - float(getter((p, model, "rh")) == 0)
                    for p in cross_pair_ids
                ]
            )
            for model in MODELS
        }
        for left, right in CONTRASTS:
            difference = subset_gaps[MODELS[left]] - subset_gaps[MODELS[right]]
            boot = 100.0 * difference[subset_draws].mean(axis=1)
            low, high = np.percentile(boot, [2.5, 97.5])
            contrast_rows.append(
                {
                    "judge": judge_label,
                    "contrast": f"{MODEL_NAMES[MODELS[left]]} - {MODEL_NAMES[MODELS[right]]}",
                    "n_pairs": len(cross_pair_ids),
                    "estimate_pp": round(100 * float(difference.mean()), 4),
                    "ci_low_pp": round(float(low), 4),
                    "ci_high_pp": round(float(high), 4),
                }
            )
    pd.DataFrame(contrast_rows).to_csv(
        output_dir / "cross_judge_subset_contrasts.csv", index=False
    )

    # ---------------------------------------------------------------- manifest
    payload = {
        "schema_version": 1,
        "seed": args.seed,
        "bootstrap_resamples": args.bootstrap_resamples,
        "permutations": args.permutations,
        "short_chars": SHORT_CHARS,
        "long_chars": LONG_CHARS,
        "inputs": manifest_inputs,
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "outputs": {},
    }
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file() and p.name != "SENSITIVITY_MANIFEST.json"):
        payload["outputs"][str(path.relative_to(output_dir)).replace("\\", "/")] = sha256_file(path)
    (output_dir / "SENSITIVITY_MANIFEST.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(f"wrote {len(payload['outputs'])} sensitivity outputs to {output_dir}")
    print(cluster_frame.to_string(index=False))


if __name__ == "__main__":
    main()
