"""Prepare the frozen, outcome-independent Phase E human-validation sample.

Design (v2, revised after the independent audit):

* the sampling unit is the pair-model job, not an isolated response;
* exactly 5 jobs are drawn from each of the 36 model x category x strategy
  cells, giving 180 jobs and 360 response items per annotator, or 11.9% of the
  1,512-job grid;
* within a category x strategy cell the sampled pair IDs are disjoint across
  target models, so 180 distinct prompts are covered;
* the two language items of a job are at least MIN_SEPARATION positions apart
  in both independently randomized annotator orders;
* selection reads identities and strata only. No automated score, flip status,
  or downstream result is loaded until after the sample is frozen, and scores
  are joined only into the private reconciliation key.

A separate familiarization set is drawn from Phase D pairs that are *not* in
the analysis sample. It is scored by both annotators before the main task so
that reading comprehension can be confirmed and rubric questions resolved on
non-sample material. No reference labels are distributed with it: handing
annotators automated scores as an answer key would train them toward the very
judges the study is meant to validate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SEED = 20260831
SCHEMA_VERSION = 2
JOBS_PER_CELL = 5
MIN_SEPARATION = 10
FAMILIARIZATION_ITEMS = 8
MODELS = (
    "qwen/qwen3-30b-a3b-instruct-2507",
    "openai/gpt-oss-20b",
    "nvidia/nemotron-3-nano-30b-a3b",
)
CATEGORIES = ("violence", "intoxication", "gambling", "sexual_violence")
STRATEGIES = ("SymbolicMasking", "ScenarioNesting", "RolePrompting")
LANGUAGES = (("en", "english"), ("rh", "romanized_hindi"))
EXPECTED_JOBS = len(MODELS) * len(CATEGORIES) * len(STRATEGIES) * JOBS_PER_CELL
EXPECTED_ITEMS = EXPECTED_JOBS * len(LANGUAGES)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(pair_id: str, model: str, language: str) -> str:
    raw = f"phase-e-v2|{pair_id}|{model}|{language}".encode()
    return "HV-" + hashlib.sha256(raw).hexdigest()[:16].upper()


def select_jobs(eligible: dict[tuple[str, str, str], list[str]]) -> list[dict[str, str]]:
    """Draw 5 jobs per model x category x strategy cell, 180 in total.

    Within each category x strategy cell the 15 sampled pair IDs are disjoint
    across the three target models, so every selected job carries a distinct
    prompt pair.
    """
    rng = random.Random(SEED)
    selected: list[dict[str, str]] = []
    for category in CATEGORIES:
        for strategy in STRATEGIES:
            shared = set(eligible[(MODELS[0], category, strategy)])
            for model in MODELS[1:]:
                shared &= set(eligible[(model, category, strategy)])
            needed = JOBS_PER_CELL * len(MODELS)
            if len(shared) < needed:
                raise RuntimeError(
                    f"{category}/{strategy}: need {needed} shared Phase D pair IDs, "
                    f"found {len(shared)}"
                )
            pool = sorted(shared)
            rng.shuffle(pool)
            for model_index, model in enumerate(MODELS):
                start = model_index * JOBS_PER_CELL
                for pair_id in pool[start : start + JOBS_PER_CELL]:
                    selected.append(
                        {
                            "pair_id": pair_id,
                            "target_model": model,
                            "category": category,
                            "strategy": strategy,
                        }
                    )
    if len(selected) != EXPECTED_JOBS:
        raise AssertionError(f"expected {EXPECTED_JOBS} jobs, found {len(selected)}")
    if len({row["pair_id"] for row in selected}) != EXPECTED_JOBS:
        raise AssertionError("selected pair IDs are not globally unique")
    counts = Counter((r["target_model"], r["category"], r["strategy"]) for r in selected)
    if set(counts.values()) != {JOBS_PER_CELL} or len(counts) != 36:
        raise AssertionError("cell allocation is not exactly 5 jobs in each of 36 cells")
    return selected


def randomize_with_separation(
    items: list[dict[str, Any]], rng: random.Random, min_separation: int
) -> list[dict[str, Any]]:
    """Shuffle items so a job's two language items are far apart.

    A plain shuffle leaves roughly nine adjacent-ish twins in 180 pairs, and
    adjacency invites the row-to-row comparison the protocol forbids. We
    shuffle, then repair violations by swapping, and assert the invariant.
    """
    order = list(items)
    rng.shuffle(order)

    def violations(seq: list[dict[str, Any]]) -> list[int]:
        last: dict[tuple[str, str], int] = {}
        bad: list[int] = []
        for position, item in enumerate(seq):
            key = (item["pair_id"], item["target_model"])
            if key in last and position - last[key] < min_separation:
                bad.append(position)
            last[key] = position
        return bad

    for _ in range(20_000):
        bad = violations(order)
        if not bad:
            return order
        position = bad[0]
        target = rng.randrange(len(order))
        order[position], order[target] = order[target], order[position]
    raise RuntimeError("could not satisfy the minimum-separation constraint")


def separation_stats(order: list[dict[str, Any]]) -> dict[str, int]:
    positions: dict[tuple[str, str], list[int]] = defaultdict(list)
    for position, item in enumerate(order):
        positions[(item["pair_id"], item["target_model"])].append(position)
    distances = [max(v) - min(v) for v in positions.values() if len(v) == 2]
    ordered = sorted(distances)
    return {
        "min": ordered[0],
        "median": ordered[len(ordered) // 2],
        "max": ordered[-1],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--build-dir", type=Path, default=Path("tmp/human_validation"))
    parser.add_argument("--output-dir", type=Path, default=Path("human_validation"))
    args = parser.parse_args()
    root = args.root.resolve()
    build_dir = (root / args.build_dir).resolve()
    output_dir = (root / args.output_dir).resolve()
    private_dir = output_dir / "private"
    build_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    jobs_path = root / "analysis/phase_d_run_archive/gpt5mini_standard_fallback_jobs.jsonl"
    traces_path = root / "frozen_final_2026_08_29/run/revision_v2_targets_final/traces.jsonl"
    primary_scores_path = root / "frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl"
    gpt_scores_path = root / "analysis/phase_d_run_archive/scores.jsonl"

    # ---- selection inputs: identities and strata, no judge outcomes --------
    phase_d_jobs = read_jsonl(jobs_path)
    eligible_sets: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    language_grid: Counter[tuple[str, str, str]] = Counter()
    for row in phase_d_jobs:
        eligible_sets[(row["target_model"], row["category"], row["strategy"])].add(row["pair_id"])
        language_grid[(row["pair_id"], row["target_model"], row["language"])] += 1
    eligible = {key: sorted(values) for key, values in eligible_sets.items()}
    for key in ((m, c, s) for m in MODELS for c in CATEGORIES for s in STRATEGIES):
        if len(eligible.get(key, [])) != 27:
            raise RuntimeError(f"incomplete eligible stratum {key}: {len(eligible.get(key, []))}")

    selected_jobs = select_jobs(eligible)
    selected_pair_ids = {row["pair_id"] for row in selected_jobs}

    # ---- text and automated outcomes load only after selection is frozen ---
    trace_map = {(r["pair_id"], r["model"]): r for r in read_jsonl(traces_path)}
    primary_map = {
        (r["pair_id"], r["model"], r["language"]): int(r["score"])
        for r in read_jsonl(primary_scores_path)
    }
    gpt_map = {
        (r["pair_id"], r["target_model"], r["language"]): int(r["score"])
        for r in read_jsonl(gpt_scores_path)
    }

    canonical_items: list[dict[str, Any]] = []
    reconciliation: list[dict[str, Any]] = []
    for job in selected_jobs:
        pair_id, model = job["pair_id"], job["target_model"]
        if (pair_id, model) not in trace_map:
            raise RuntimeError(f"missing frozen trace for {(pair_id, model)}")
        trace = trace_map[(pair_id, model)]
        for language, trace_side in LANGUAGES:
            if language_grid[(pair_id, model, language)] != 1:
                raise RuntimeError(f"invalid Phase D job multiplicity for {(pair_id, model, language)}")
            side = trace[trace_side]
            prompt, response = side["prompt"], side["content"]
            rid = stable_id(pair_id, model, language)
            canonical_items.append(
                {
                    "reconciliation_id": rid,
                    "pair_id": pair_id,
                    "target_model": model,
                    "harmful_prompt": prompt,
                    "target_response": response,
                }
            )
            reconciliation.append(
                {
                    "reconciliation_id": rid,
                    "pair_id": pair_id,
                    "target_model": model,
                    "category": job["category"],
                    "strategy": job["strategy"],
                    "language": language,
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
                    "finish_reason": side.get("finish_reason") or "",
                    "gemini_score": primary_map[(pair_id, model, language)],
                    "gpt5mini_score": gpt_map[(pair_id, model, language)],
                }
            )
    if len(canonical_items) != EXPECTED_ITEMS:
        raise AssertionError(f"expected {EXPECTED_ITEMS} response items, found {len(canonical_items)}")
    if len({r["reconciliation_id"] for r in canonical_items}) != EXPECTED_ITEMS:
        raise AssertionError("reconciliation IDs are not unique")

    # ---- familiarization set: outside the analysis sample ------------------
    # Chosen to span the rubric range and both languages. These items are never
    # analysed and no reference label is distributed with them, so using stored
    # scores to pick them cannot anchor annotators toward the automated judges.
    familiarization_rng = random.Random(SEED + 7)
    pool_by_level: dict[tuple[int, str], list[tuple[str, str, str]]] = defaultdict(list)
    for row in phase_d_jobs:
        pair_id, model, language = row["pair_id"], row["target_model"], row["language"]
        if pair_id in selected_pair_ids:
            continue
        pool_by_level[(primary_map[(pair_id, model, language)], language)].append(
            (pair_id, model, language)
        )
    familiarization: list[dict[str, Any]] = []
    for level in (0, 1, 2, 3):
        for language in ("en", "rh"):
            pool = sorted(pool_by_level.get((level, language), []))
            if not pool:
                continue
            pair_id, model, _ = familiarization_rng.choice(pool)
            side = dict(LANGUAGES)[language]
            block = trace_map[(pair_id, model)][side]
            familiarization.append(
                {
                    "pair_id": pair_id,
                    "target_model": model,
                    "language": language,
                    "harmful_prompt": block["prompt"],
                    "target_response": block["content"],
                }
            )
    familiarization_rng.shuffle(familiarization)
    familiarization = familiarization[:FAMILIARIZATION_ITEMS]
    if len({(f["pair_id"], f["target_model"], f["language"]) for f in familiarization}) != len(
        familiarization
    ):
        raise AssertionError("familiarization items are not unique")
    if selected_pair_ids & {f["pair_id"] for f in familiarization}:
        raise AssertionError("familiarization set overlaps the analysis sample")
    (build_dir / "familiarization.json").write_text(
        json.dumps(
            [
                {
                    "item_number": index,
                    "harmful_prompt": item["harmful_prompt"],
                    "target_response": item["target_response"],
                }
                for index, item in enumerate(familiarization, start=1)
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ---- independent randomization with a separation guarantee -------------
    annotator_maps: list[dict[str, Any]] = []
    separation: dict[str, dict[str, int]] = {}
    for annotator, offset in (("A", 101), ("B", 202)):
        ordered = randomize_with_separation(
            canonical_items, random.Random(SEED + offset), MIN_SEPARATION
        )
        separation[annotator] = separation_stats(ordered)
        payload = []
        for item_number, item in enumerate(ordered, start=1):
            payload.append(
                {
                    "item_number": item_number,
                    "harmful_prompt": item["harmful_prompt"],
                    "target_response": item["target_response"],
                }
            )
            annotator_maps.append(
                {
                    "annotator": annotator,
                    "item_number": item_number,
                    "reconciliation_id": item["reconciliation_id"],
                }
            )
        (build_dir / f"annotator_{annotator}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    shared_positions = sum(
        1
        for a, b in zip(
            [r for r in annotator_maps if r["annotator"] == "A"],
            [r for r in annotator_maps if r["annotator"] == "B"],
        )
        if a["reconciliation_id"] == b["reconciliation_id"]
    )

    reconciliation_path = private_dir / "reconciliation_key.csv"
    with reconciliation_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(reconciliation[0]))
        writer.writeheader()
        writer.writerows(reconciliation)
    order_path = private_dir / "annotator_order_key.csv"
    with order_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(annotator_maps[0]))
        writer.writeheader()
        writer.writerows(annotator_maps)

    stratum_counts = Counter(
        (r["target_model"], r["category"], r["strategy"]) for r in selected_jobs
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "design": "outcome-independent stratified sample of pair-model jobs; both languages retained",
        "selection_seed": SEED,
        "selected_pair_model_jobs": EXPECTED_JOBS,
        "response_items_per_annotator": EXPECTED_ITEMS,
        "unique_pair_ids": EXPECTED_JOBS,
        "coverage_fraction_of_pair_model_grid": round(EXPECTED_JOBS / 1512, 4),
        "annotators": 2,
        "same_items_for_both_annotators": True,
        "independent_row_randomization": True,
        "identical_item_positions_across_annotators": shared_positions,
        "min_positions_between_language_items_of_a_job": MIN_SEPARATION,
        "observed_separation_by_annotator": separation,
        "selection_used_automated_scores": False,
        "eligibility_scope": "completed outcome-independent Phase D shared-pair scope (27 jobs per model/category/strategy cell)",
        "allocation": f"exactly {JOBS_PER_CELL} pair-model jobs in each of the 36 model/category/strategy cells; both languages",
        "pair_ids_disjoint_across_models_within_category_strategy": True,
        "familiarization_items": len(familiarization),
        "familiarization_disjoint_from_analysis_sample": True,
        "familiarization_reference_labels_distributed": False,
        "cluster_unit_for_analysis": "pair-model job",
        "stratum_counts_pair_model_jobs": {
            "|".join(key): value for key, value in sorted(stratum_counts.items())
        },
        "source_hashes": {
            str(path.relative_to(root)).replace("\\", "/"): sha256_file(path)
            for path in (jobs_path, traces_path, primary_scores_path, gpt_scores_path)
        },
        "private_key_hashes": {
            str(reconciliation_path.relative_to(root)).replace("\\", "/"): sha256_file(reconciliation_path),
            str(order_path.relative_to(root)).replace("\\", "/"): sha256_file(order_path),
        },
    }
    (output_dir / "HUMAN_VALIDATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "selected_jobs": EXPECTED_JOBS,
                "items_per_annotator": EXPECTED_ITEMS,
                "coverage": manifest["coverage_fraction_of_pair_model_grid"],
                "separation": separation,
                "shared_positions": shared_positions,
                "familiarization_items": len(familiarization),
                "build_dir": str(build_dir),
            }
        )
    )


if __name__ == "__main__":
    main()
