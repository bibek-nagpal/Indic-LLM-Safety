#!/usr/bin/env python3
"""Exact replay of archived candidate pairs through an independent auditor.

This script is intentionally a thin replay driver around the ORIGINAL
``jailbreak_hermes.equivalence.check`` implementation.  It does not reproduce
or reimplement the auditor prompt, prompt construction, JSON parsing,
axis-default behavior, temperature, or certification rule.

The experimental intervention is only the model passed as ``checker_model``.
The equivalence threshold is loaded from the original run configuration and
``max_tokens`` is loaded from the original model configuration.

Input
-----
The original ``v1_paper.zip`` containing per-batch ``traces.jsonl`` files.
Only records with ``event == \"candidate\"`` are replayed.  Prompt text is read
in memory but is never printed or written to the new output.

Output
------
A resumable JSONL file and a summary JSON under ``runs/cross_auditor`` by
default.  The source ZIP is opened read-only and is never modified.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import random
import statistics
import subprocess
import threading
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv

from jailbreak_hermes import equivalence, model_registry
from jailbreak_hermes.generator import Candidate
from jailbreak_hermes.run import RunConfig


SCHEMA_VERSION = 2
EXPECTED_TOTAL = 2001
EXPECTED_ACCEPTED = 1581
EXPECTED_REJECTED = 420
AXES = (
    "same_harmful_intent",
    "same_scenario",
    "same_info_level_requested",
    "same_attack_strategy",
    "same_cultural_specificity",
    "same_target_group",
    "same_ambiguity_level",
    "language_fidelity",
    "strategy_faithfully_used",
)
_WRITE_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Provenance and archive loading
# ---------------------------------------------------------------------------


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def stable_id(trace_name: str, line_number: int, en: str, rh: str) -> str:
    payload = "\x1f".join((trace_name, str(line_number), en, rh)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:24]


def pair_hash(en: str, rh: str) -> str:
    return hashlib.sha256("\x1f".join((en, rh)).encode("utf-8")).hexdigest()


def parse_target_model_from_run(run_name: str) -> str:
    """Grouping label only.  This value is never shown to the auditor."""
    lowered = run_name.lower()
    if "qwen3" in lowered:
        return "qwen/qwen3-30b-a3b-instruct-2507"
    if "gpt-oss" in lowered:
        return "openai/gpt-oss-20b"
    if "nemotron" in lowered:
        return "nvidia/nemotron-3-nano-30b-a3b"
    return "unknown"


def _validate_candidate_dict(cand: dict[str, Any], *, location: str) -> None:
    expected = {f.name for f in dataclasses.fields(Candidate)}
    actual = set(cand)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(
            f"Candidate schema mismatch at {location}: missing={missing}, extra={extra}. "
            "Refusing to guess or alter archived metadata."
        )


def candidate_from_archived(cand: dict[str, Any], *, location: str) -> Candidate:
    _validate_candidate_dict(cand, location=location)
    # Exact dataclass reconstruction: no normalization, translation, trimming,
    # metadata substitution, or prompt regeneration.
    return Candidate(**cand)


def read_candidates_from_zip(zip_path: str | Path) -> list[dict[str, Any]]:
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise FileNotFoundError(f"Data ZIP not found: {zip_path}")

    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path, mode="r") as zf:
        trace_names = sorted(n for n in zf.namelist() if n.endswith("/traces.jsonl"))
        if not trace_names:
            raise RuntimeError(f"No */traces.jsonl files found in {zip_path}")

        for trace_name in trace_names:
            run_name = trace_name.rsplit("/", 2)[-2]
            raw = zf.read(trace_name).decode("utf-8", errors="strict")
            for line_number, line in enumerate(raw.splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        f"Invalid JSON in {trace_name}:{line_number}: {exc}"
                    ) from exc
                if event.get("event") != "candidate":
                    continue
                if not isinstance(event.get("candidate"), dict):
                    raise RuntimeError(f"Missing candidate object at {trace_name}:{line_number}")
                if not isinstance(event.get("equivalence"), dict):
                    raise RuntimeError(
                        f"Missing original equivalence object at {trace_name}:{line_number}"
                    )

                cand_dict = event["candidate"]
                location = f"{trace_name}:{line_number}"
                _validate_candidate_dict(cand_dict, location=location)
                en = cand_dict["english_prompt"]
                rh = cand_dict["romanized_hindi_prompt"]
                if not isinstance(en, str) or not isinstance(rh, str):
                    raise RuntimeError(f"Prompt fields are not strings at {location}")

                rows.append(
                    {
                        "id": stable_id(trace_name, line_number, en, rh),
                        "pair_sha256": pair_hash(en, rh),
                        "trace_name": trace_name,
                        "trace_line": line_number,
                        "run_name": run_name,
                        "target_model_batch": parse_target_model_from_run(run_name),
                        "candidate": cand_dict,
                        "original_equivalence": event["equivalence"],
                    }
                )

    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        duplicates = [k for k, n in Counter(ids).items() if n > 1]
        raise RuntimeError(f"Duplicate replay IDs found: {duplicates[:10]}")
    return rows


def validate_expected_archive(rows: list[dict[str, Any]]) -> None:
    accepted = sum(bool(r["original_equivalence"].get("accepted")) for r in rows)
    rejected = len(rows) - accepted
    observed = (len(rows), accepted, rejected)
    expected = (EXPECTED_TOTAL, EXPECTED_ACCEPTED, EXPECTED_REJECTED)
    if observed != expected:
        raise RuntimeError(
            "Archive count check failed. "
            f"Observed total/accepted/rejected={observed}; expected={expected}. "
            "Use the exact original v1_paper.zip before making paid calls."
        )


# ---------------------------------------------------------------------------
# Configuration: load the exact knobs used by the original pipeline
# ---------------------------------------------------------------------------


def resolve_original_config(
    run_config_path: str | Path,
    models_config_override: str | Path | None,
) -> dict[str, Any]:
    run_path = Path(run_config_path)
    if not run_path.is_file():
        raise FileNotFoundError(f"Run config not found: {run_path}")

    run_cfg = RunConfig.from_yaml(run_path)
    models_path = Path(models_config_override or run_cfg.models_config)
    if not models_path.is_file():
        raise FileNotFoundError(f"Models config not found: {models_path}")
    reg = model_registry.load(models_path)

    return {
        "run_config_path": str(run_path),
        "models_config_path": str(models_path),
        "equivalence_threshold": float(run_cfg.equivalence_threshold),
        "max_tokens": int(reg.max_orchestrator_tokens),
        "temperature": 0.0,  # hard-coded inside equivalence.check
        "original_auditor_model": reg.equivalence_model,
        "system_prompt_sha256": sha256_text(equivalence.EQUIVALENCE_SYSTEM),
    }


def config_signature(
    *,
    source_archive_sha256: str,
    independent_model: str,
    resolved: dict[str, Any],
) -> str:
    controlled = {
        "schema_version": SCHEMA_VERSION,
        "source_archive_sha256": source_archive_sha256,
        "independent_model": independent_model,
        "equivalence_threshold": resolved["equivalence_threshold"],
        "max_tokens": resolved["max_tokens"],
        "temperature": resolved["temperature"],
        "system_prompt_sha256": resolved["system_prompt_sha256"],
        "implementation": "jailbreak_hermes.equivalence.check",
    }
    return sha256_text(json.dumps(controlled, sort_keys=True, separators=(",", ":")))


# ---------------------------------------------------------------------------
# Exact replay: call the original equivalence.check implementation directly
# ---------------------------------------------------------------------------


def evaluate_one(
    row: dict[str, Any],
    *,
    independent_model: str,
    resolved: dict[str, Any],
    source_archive_sha256: str,
    signature: str,
) -> dict[str, Any]:
    cand = candidate_from_archived(
        row["candidate"],
        location=f"{row['trace_name']}:{row['trace_line']}",
    )

    # This is the critical design choice: use the original implementation
    # directly.  It constructs the exact original user prompt, imports the
    # exact EQUIVALENCE_SYSTEM, calls at temperature 0.0, parses with the
    # original JSON extractor, applies the original axis defaults, and applies
    # the original certification predicate.  Only checker_model differs.
    report = equivalence.check(
        cand,
        checker_model=independent_model,
        accept_threshold=resolved["equivalence_threshold"],
        max_tokens=resolved["max_tokens"],
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "config_signature": signature,
        "id": row["id"],
        "pair_sha256": row["pair_sha256"],
        "trace_name": row["trace_name"],
        "trace_line": row["trace_line"],
        "run_name": row["run_name"],
        "target_model_batch": row["target_model_batch"],
        "category": cand.category,
        "strategy": cand.strategy,
        "original_equivalence": row["original_equivalence"],
        "independent_equivalence": dataclasses.asdict(report),
        "original_auditor_model": resolved["original_auditor_model"],
        "auditor_model_requested": independent_model,
        "equivalence_threshold": resolved["equivalence_threshold"],
        "temperature": resolved["temperature"],
        "max_tokens": resolved["max_tokens"],
        "system_prompt_sha256": resolved["system_prompt_sha256"],
        "source_archive_sha256": source_archive_sha256,
        "implementation": "jailbreak_hermes.equivalence.check",
    }


# ---------------------------------------------------------------------------
# Resumable JSONL I/O
# ---------------------------------------------------------------------------


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
    with _WRITE_LOCK:
        with path.open("a", encoding="utf-8") as f:
            f.write(text)
            f.flush()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
        if not isinstance(obj, dict):
            raise RuntimeError(f"Non-object JSON record in {path}:{line_number}")
        rows.append(obj)
    return rows


def validate_existing_output(rows: list[dict[str, Any]], signature: str, path: Path) -> None:
    for row in rows:
        if row.get("schema_version") != SCHEMA_VERSION:
            raise RuntimeError(
                f"{path} contains records from another script/schema. "
                "Use a new output filename or remove the old pilot output."
            )
        if row.get("config_signature") != signature:
            raise RuntimeError(
                f"{path} contains records produced with a different model, archive, "
                "prompt, threshold, or token setting. Refusing to mix experiments."
            )


def successful_rows_by_id(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Last successful record wins; errors remain retryable."""
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        rid = str(row.get("id") or "")
        if rid and not row.get("error"):
            out[rid] = row
    return out


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------


def stratified_sample(
    rows: list[dict[str, Any]],
    *,
    per_group: int,
    seed: int,
) -> list[dict[str, Any]]:
    if per_group <= 0:
        return list(rows)
    rng = random.Random(seed)
    groups: dict[tuple[str, str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        cand = row["candidate"]
        groups[
            (
                row["run_name"],
                str(cand.get("strategy")),
                bool(row["original_equivalence"].get("accepted")),
            )
        ].append(row)

    chosen: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = list(groups[key])
        rng.shuffle(group)
        chosen.extend(group[:per_group])
    rng.shuffle(chosen)
    return chosen


# ---------------------------------------------------------------------------
# Agreement statistics
# ---------------------------------------------------------------------------


def safe_div(num: float, den: float) -> float | None:
    return num / den if den else None


def kappa_binary(y_true: list[int], y_pred: list[int]) -> float | None:
    if not y_true or len(y_true) != len(y_pred):
        return None
    n = len(y_true)
    po = sum(a == b for a, b in zip(y_true, y_pred)) / n
    p_t1 = sum(y_true) / n
    p_p1 = sum(y_pred) / n
    pe = p_t1 * p_p1 + (1.0 - p_t1) * (1.0 - p_p1)
    if math.isclose(1.0 - pe, 0.0):
        return None
    return (po - pe) / (1.0 - pe)


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (denx * deny) if denx and deny else None


def axis_value(axes: Any, name: str) -> bool | None:
    if not isinstance(axes, dict):
        return None
    entry = axes.get(name)
    if isinstance(entry, dict) and "equal" in entry:
        return bool(entry["equal"])
    return None


def equivalence_pair(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    old = row.get("original_equivalence")
    new = row.get("independent_equivalence")
    if not isinstance(old, dict) or not isinstance(new, dict):
        raise RuntimeError(f"Malformed successful output row id={row.get('id')}")
    return old, new


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}

    old_new = [equivalence_pair(r) for r in rows]
    y0 = [int(bool(old.get("accepted"))) for old, _ in old_new]
    y1 = [int(bool(new.get("accepted"))) for _, new in old_new]
    tn = sum(a == 0 and b == 0 for a, b in zip(y0, y1))
    fp = sum(a == 0 and b == 1 for a, b in zip(y0, y1))
    fn = sum(a == 1 and b == 0 for a, b in zip(y0, y1))
    tp = sum(a == 1 and b == 1 for a, b in zip(y0, y1))
    old_scores = [float(old.get("score", 0.0)) for old, _ in old_new]
    new_scores = [float(new.get("score", 0.0)) for _, new in old_new]

    return {
        "n": len(rows),
        "agreement": (tp + tn) / len(rows),
        "cohen_kappa": kappa_binary(y0, y1),
        "confusion_matrix_orientation": {
            "rows": "original Gemini decision",
            "columns": "independent auditor decision",
            "positive": "accepted/certified",
        },
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "original_acceptance_rate": sum(y0) / len(rows),
        "independent_acceptance_rate": sum(y1) / len(rows),
        "gemini_accepted_confirmation_rate": safe_div(tp, tp + fn),
        "gemini_rejected_confirmation_rate": safe_div(tn, tn + fp),
        "score_mae": statistics.fmean(abs(a - b) for a, b in zip(old_scores, new_scores)),
        "score_pearson": pearson(old_scores, new_scores),
    }


def summarize_axis(rows: list[dict[str, Any]], axis: str) -> dict[str, Any]:
    pairs: list[tuple[bool, bool]] = []
    missing_old = 0
    missing_new = 0
    for row in rows:
        old, new = equivalence_pair(row)
        a = axis_value(old.get("axes"), axis)
        b = axis_value(new.get("axes"), axis)
        if a is None:
            missing_old += 1
        if b is None:
            missing_new += 1
        if a is not None and b is not None:
            pairs.append((a, b))

    y0 = [int(a) for a, _ in pairs]
    y1 = [int(b) for _, b in pairs]
    tn = sum(a == 0 and b == 0 for a, b in zip(y0, y1))
    fp = sum(a == 0 and b == 1 for a, b in zip(y0, y1))
    fn = sum(a == 1 and b == 0 for a, b in zip(y0, y1))
    tp = sum(a == 1 and b == 1 for a, b in zip(y0, y1))
    return {
        "n_compared": len(pairs),
        "missing_original": missing_old,
        "missing_independent": missing_new,
        "agreement": safe_div(tp + tn, len(pairs)),
        "cohen_kappa": kappa_binary(y0, y1),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "original_equal_rate": safe_div(sum(y0), len(y0)),
        "independent_equal_rate": safe_div(sum(y1), len(y1)),
    }


def grouped_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = sorted({str(r.get(field)) for r in rows})
    return {
        value: summarize_group([r for r in rows if str(r.get(field)) == value])
        for value in values
    }


def summarize(
    output_path: Path,
    summary_path: Path,
    *,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    raw_rows = read_jsonl(output_path)
    success_by_id = successful_rows_by_id(raw_rows)
    rows = list(success_by_id.values())
    error_rows = [r for r in raw_rows if r.get("error")]

    original_by_strategy_and_verdict: dict[str, dict[str, int]] = {}
    for strategy in sorted({str(r.get("strategy")) for r in rows}):
        selected = [r for r in rows if str(r.get("strategy")) == strategy]
        original_by_strategy_and_verdict[strategy] = {
            "accepted": sum(
                bool(equivalence_pair(r)[0].get("accepted")) for r in selected
            ),
            "rejected": sum(
                not bool(equivalence_pair(r)[0].get("accepted")) for r in selected
            ),
        }

    summary: dict[str, Any] = {
        "metadata": metadata,
        "records": {
            "successful_unique": len(rows),
            "error_attempts": len(error_rows),
            "error_types": dict(
                Counter(str(r.get("error", "unknown")).split(":", 1)[0] for r in error_rows)
            ),
        },
        "overall": summarize_group(rows),
        "by_strategy": grouped_summary(rows, "strategy"),
        "by_category": grouped_summary(rows, "category"),
        "by_target_model_batch": grouped_summary(rows, "target_model_batch"),
        "by_original_run": grouped_summary(rows, "run_name"),
        "axis_agreement": {axis: summarize_axis(rows, axis) for axis in AXES},
        "original_verdict_counts_by_strategy": original_by_strategy_and_verdict,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def default_output_for_model(model: str) -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in model).strip("_")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return Path("runs/cross_auditor") / f"{safe}.jsonl"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-zip", required=True, help="Path to the exact original v1_paper.zip")
    ap.add_argument(
        "--model",
        default="anthropic/claude-sonnet-4.6",
        help="Independent auditor model. This is the intended experimental change.",
    )
    ap.add_argument(
        "--run-config",
        default="configs/run.yaml",
        help="Original run config; supplies the equivalence threshold.",
    )
    ap.add_argument(
        "--models-config",
        default=None,
        help="Optional original model config path; defaults to models_config in run.yaml.",
    )
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument(
        "--per-group",
        type=int,
        default=0,
        help="Pilot sampler: N per (original run, strategy, original verdict); 0 = all.",
    )
    ap.add_argument("--max-items", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20260710)
    ap.add_argument(
        "--original-verdict",
        choices=("both", "accepted", "rejected"),
        default="both",
    )
    ap.add_argument(
        "--output",
        default=None,
        help="Output JSONL. Default: runs/cross_auditor/<sanitized-model>.jsonl",
    )
    ap.add_argument("--dry-run", action="store_true", help="Validate and select only; no API calls.")
    return ap


def main() -> int:
    load_dotenv()
    args = build_parser().parse_args()

    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")
    if args.per_group < 0 or args.max_items < 0:
        raise SystemExit("--per-group and --max-items must be >= 0")

    data_zip = Path(args.data_zip)
    archive_sha = sha256_file(data_zip)
    resolved = resolve_original_config(args.run_config, args.models_config)

    if args.model == resolved["original_auditor_model"]:
        raise SystemExit(
            "Independent model equals the original auditor model. "
            "Choose a different model family for the cross-auditor check."
        )

    signature = config_signature(
        source_archive_sha256=archive_sha,
        independent_model=args.model,
        resolved=resolved,
    )

    all_rows = read_candidates_from_zip(data_zip)
    validate_expected_archive(all_rows)

    rows = all_rows
    if args.original_verdict != "both":
        wanted = args.original_verdict == "accepted"
        rows = [
            r
            for r in rows
            if bool(r["original_equivalence"].get("accepted")) == wanted
        ]
    rows = stratified_sample(rows, per_group=args.per_group, seed=args.seed)
    if args.max_items > 0:
        rows = rows[: args.max_items]

    by_old = Counter(bool(r["original_equivalence"].get("accepted")) for r in rows)
    print("Exact implementation: jailbreak_hermes.equivalence.check")
    print(f"Original auditor model: {resolved['original_auditor_model']}")
    print(f"Independent auditor model: {args.model}")
    print(f"Threshold from {resolved['run_config_path']}: {resolved['equivalence_threshold']}")
    print(f"Max tokens from {resolved['models_config_path']}: {resolved['max_tokens']}")
    print(f"Temperature: {resolved['temperature']} (hard-coded by original check())")
    print(f"System prompt SHA-256: {resolved['system_prompt_sha256']}")
    print(f"Source ZIP SHA-256: {archive_sha}")
    print(
        f"Archive verified: total={len(all_rows)}, "
        f"accepted={EXPECTED_ACCEPTED}, rejected={EXPECTED_REJECTED}"
    )
    print(
        f"Selected {len(rows)} candidate pairs: "
        f"accepted={by_old[True]}, rejected={by_old[False]}"
    )
    print("Prompt text will not be printed or written to the replay output.")

    if args.dry_run:
        print("Dry run complete: no API calls were made.")
        return 0

    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY is not available from the environment/.env")

    output_path = Path(args.output) if args.output else default_output_for_model(args.model)
    summary_path = output_path.with_suffix(".summary.json")
    existing = read_jsonl(output_path)
    validate_existing_output(existing, signature, output_path)
    done = successful_rows_by_id(existing)
    selected_ids = {r["id"] for r in rows}
    pending = [r for r in rows if r["id"] not in done]
    selected_done = len(selected_ids & set(done))
    print(
        f"Output: {output_path}\n"
        f"Already complete in this selection: {selected_done}; "
        f"pending: {len(pending)}; workers={args.workers}"
    )

    def task(row: dict[str, Any]) -> dict[str, Any]:
        try:
            return evaluate_one(
                row,
                independent_model=args.model,
                resolved=resolved,
                source_archive_sha256=archive_sha,
                signature=signature,
            )
        except Exception as exc:  # retain error records; reruns retry them
            cand = row["candidate"]
            return {
                "schema_version": SCHEMA_VERSION,
                "config_signature": signature,
                "id": row["id"],
                "pair_sha256": row["pair_sha256"],
                "trace_name": row["trace_name"],
                "trace_line": row["trace_line"],
                "run_name": row["run_name"],
                "target_model_batch": row["target_model_batch"],
                "category": cand.get("category"),
                "strategy": cand.get("strategy"),
                "original_auditor_model": resolved["original_auditor_model"],
                "auditor_model_requested": args.model,
                "equivalence_threshold": resolved["equivalence_threshold"],
                "temperature": resolved["temperature"],
                "max_tokens": resolved["max_tokens"],
                "system_prompt_sha256": resolved["system_prompt_sha256"],
                "source_archive_sha256": archive_sha,
                "implementation": "jailbreak_hermes.equivalence.check",
                "error": f"{type(exc).__name__}: {exc}",
            }

    if args.workers == 1:
        for idx, row in enumerate(pending, start=1):
            append_jsonl(output_path, task(row))
            if idx % 10 == 0 or idx == len(pending):
                print(f"Completed {idx}/{len(pending)}")
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(task, row): row["id"] for row in pending}
            for idx, future in enumerate(as_completed(futures), start=1):
                append_jsonl(output_path, future.result())
                if idx % 10 == 0 or idx == len(pending):
                    print(f"Completed {idx}/{len(pending)}")

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "config_signature": signature,
        "source_archive": str(data_zip),
        "source_archive_sha256": archive_sha,
        "source_archive_expected_counts": {
            "total": EXPECTED_TOTAL,
            "accepted": EXPECTED_ACCEPTED,
            "rejected": EXPECTED_REJECTED,
        },
        "repository_git_commit": git_commit(),
        "implementation": "jailbreak_hermes.equivalence.check",
        "original_auditor_model": resolved["original_auditor_model"],
        "independent_auditor_model": args.model,
        "run_config_path": resolved["run_config_path"],
        "models_config_path": resolved["models_config_path"],
        "equivalence_threshold": resolved["equivalence_threshold"],
        "temperature": resolved["temperature"],
        "max_tokens": resolved["max_tokens"],
        "system_prompt_sha256": resolved["system_prompt_sha256"],
        "selection": {
            "original_verdict": args.original_verdict,
            "per_group": args.per_group,
            "max_items": args.max_items,
            "seed": args.seed,
        },
    }
    summary = summarize(output_path, summary_path, metadata=metadata)
    print(json.dumps(summary["overall"], indent=2, ensure_ascii=False))
    print(f"Wrote: {output_path}")
    print(f"Wrote: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
