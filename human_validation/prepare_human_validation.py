"""Prepare the frozen, outcome-independent Phase E human-validation sample.

The script selects pair-model jobs, not isolated responses.  Both language
responses for every selected job are retained.  It never reads an automated
score until after selection is complete; scores are joined only into the
private reconciliation key used by the post-annotation analysis.
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


SEED = 20260830
MODELS = (
    "qwen/qwen3-30b-a3b-instruct-2507",
    "openai/gpt-oss-20b",
    "nvidia/nemotron-3-nano-30b-a3b",
)
CATEGORIES = ("violence", "intoxication", "gambling", "sexual_violence")
STRATEGIES = ("SymbolicMasking", "ScenarioNesting", "RolePrompting")
LANGUAGES = (("en", "english"), ("rh", "romanized_hindi"))


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
    raw = f"phase-e-v1|{pair_id}|{model}|{language}".encode()
    return "HV-" + hashlib.sha256(raw).hexdigest()[:16].upper()


def select_jobs(eligible: dict[tuple[str, str, str], list[str]]) -> list[dict[str, str]]:
    """Select 90 disjoint pair-model jobs with 2/3 jobs in every cell.

    The checkerboard allocation gives every model six 3-job cells and six
    2-job cells.  Every model x strategy margin is exactly 10 jobs.  Within a
    category x strategy cell, sampled pair IDs are disjoint across models to
    maximize prompt diversity and reduce recognition effects.
    """
    rng = random.Random(SEED)
    selected: list[dict[str, str]] = []
    for category_index, category in enumerate(CATEGORIES):
        for strategy_index, strategy in enumerate(STRATEGIES):
            common = set(eligible[(MODELS[0], category, strategy)])
            for model in MODELS[1:]:
                common &= set(eligible[(model, category, strategy)])
            if len(common) != 27:
                raise RuntimeError(
                    f"expected 27 shared Phase D pair IDs in {category}/{strategy}, "
                    f"found {len(common)}"
                )
            pool = sorted(common)
            rng.shuffle(pool)
            cursor = 0
            for model_index, model in enumerate(MODELS):
                count = 3 if (model_index + category_index + strategy_index) % 2 == 0 else 2
                chosen = pool[cursor : cursor + count]
                cursor += count
                for pair_id in chosen:
                    selected.append(
                        {
                            "pair_id": pair_id,
                            "target_model": model,
                            "category": category,
                            "strategy": strategy,
                        }
                    )
    if len(selected) != 90:
        raise AssertionError(f"expected 90 selected jobs, found {len(selected)}")
    if len({row["pair_id"] for row in selected}) != 90:
        raise AssertionError("selected pair IDs are not globally unique")
    return selected


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

    # Selection inputs contain identities and strata but no judge outcomes.
    phase_d_jobs = read_jsonl(jobs_path)
    eligible_sets: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    language_grid: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in phase_d_jobs:
        key = (row["target_model"], row["category"], row["strategy"])
        eligible_sets[key].add(row["pair_id"])
        language_grid[(row["pair_id"], *key, row["language"])] += 1
    eligible = {key: sorted(values) for key, values in eligible_sets.items()}
    for key in ((m, c, s) for m in MODELS for c in CATEGORIES for s in STRATEGIES):
        if len(eligible.get(key, [])) != 27:
            raise RuntimeError(f"incomplete eligible stratum {key}: {len(eligible.get(key, []))}")

    selected_jobs = select_jobs(eligible)
    selected_keys = {(r["pair_id"], r["target_model"]) for r in selected_jobs}

    # Text and automated outcomes are loaded only after the selection is frozen.
    traces = read_jsonl(traces_path)
    trace_map = {(r["pair_id"], r["model"]): r for r in traces}
    primary_scores = read_jsonl(primary_scores_path)
    primary_map = {(r["pair_id"], r["model"], r["language"]): int(r["score"]) for r in primary_scores}
    gpt_scores = read_jsonl(gpt_scores_path)
    gpt_map = {(r["pair_id"], r["target_model"], r["language"]): int(r["score"]) for r in gpt_scores}

    canonical_items: list[dict[str, Any]] = []
    reconciliation: list[dict[str, Any]] = []
    for job in selected_jobs:
        pair_id, model = job["pair_id"], job["target_model"]
        if (pair_id, model) not in trace_map:
            raise RuntimeError(f"missing frozen trace for {(pair_id, model)}")
        trace = trace_map[(pair_id, model)]
        for language, trace_side in LANGUAGES:
            if language_grid[(pair_id, model, job["category"], job["strategy"], language)] != 1:
                raise RuntimeError(f"invalid Phase D job multiplicity for {(pair_id, model, language)}")
            side = trace[trace_side]
            prompt = side["prompt"]
            response = side["content"]
            rid = stable_id(pair_id, model, language)
            canonical_items.append(
                {
                    "reconciliation_id": rid,
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
                    "gemini_score": primary_map[(pair_id, model, language)],
                    "gpt5mini_score": gpt_map[(pair_id, model, language)],
                }
            )
    if len(canonical_items) != 180 or len({r["reconciliation_id"] for r in canonical_items}) != 180:
        raise AssertionError("human-validation response grid is not exactly 180 unique items")

    annotator_maps: list[dict[str, Any]] = []
    for annotator, offset in (("A", 101), ("B", 202)):
        ordered = list(canonical_items)
        random.Random(SEED + offset).shuffle(ordered)
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
        "schema_version": 1,
        "design": "outcome-independent stratified sample of pair-model jobs; both languages retained",
        "selection_seed": SEED,
        "selected_pair_model_jobs": 90,
        "response_items_per_annotator": 180,
        "unique_pair_ids": 90,
        "annotators": 2,
        "same_items_for_both_annotators": True,
        "independent_row_randomization": True,
        "selection_used_automated_scores": False,
        "eligibility_scope": "completed outcome-independent Phase D shared-pair scope (27 jobs per model/category/strategy cell)",
        "allocation": "2 or 3 pair-model jobs per model/category/strategy cell; both languages; six 3-job and six 2-job cells per model",
        "pair_ids_disjoint_across_models_within_category_strategy": True,
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
    print(json.dumps({"selected_jobs": 90, "items_per_annotator": 180, "build_dir": str(build_dir)}))


if __name__ == "__main__":
    main()
