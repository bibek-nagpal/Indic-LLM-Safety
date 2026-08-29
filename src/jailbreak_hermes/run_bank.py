"""Revision V2 target sweep over one immutable frozen probe bank.

V2.4 adds safe resume semantics.  A (pair_id, model) target response is never
re-fired merely because judging was interrupted: successful raw target traces
are reused, missing language scores are judged independently, and completed
flips are skipped.  Reusing --run-id therefore resumes the same experiment.
"""
from __future__ import annotations

import asyncio
import dataclasses
import json
import time
from collections import defaultdict
from pathlib import Path

import httpx

from . import flip_detector, judge, model_registry, model_runner
from .generator import Candidate
from .probe_bank import validate_bank
from .trace_store import TraceStore
from .openrouter_client import write_accounting_summary


async def _to_thread(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)


def _key(row):
    return (row.get("pair_id"), row.get("model"))


def _load_state(store: TraceStore):
    """Return latest successful target traces, scores and flips for resume."""
    targets = {}
    for r in store.list_records("traces.jsonl"):
        if r.get("event") != "model_pair":
            continue
        en = r.get("english") or {}
        rh = r.get("romanized_hindi") or {}
        if not en.get("error") and not rh.get("error") and en.get("content") is not None and rh.get("content") is not None:
            targets[_key(r)] = r

    scores = {}
    for r in store.list_records("scores.jsonl"):
        lang = r.get("language")
        if lang in {"en", "rh"}:
            scores[(_key(r), lang)] = r

    flips = {}
    for r in store.list_records("flips.jsonl"):
        flips[_key(r)] = r
    return targets, scores, flips


def _jr_from_score(row: dict) -> judge.JudgeResult:
    fields = {f.name for f in dataclasses.fields(judge.JudgeResult)}
    return judge.JudgeResult(**{k: v for k, v in row.items() if k in fields})


async def _one(pair_record, model, reg, store, sem_target, sem_judge,
               http_client, gate_questions, targets, scores, flips):
    pid = pair_record["pair_id"]
    key = (pid, model)
    cand = Candidate(**pair_record["candidate"])

    if key in flips:
        return flips[key]

    # TARGET: reuse a successful raw response pair if it was already persisted.
    target_row = targets.get(key)
    if target_row is None:
        async with sem_target:
            pair = await model_runner.arun_pair(
                model,
                cand.english_prompt,
                cand.romanized_hindi_prompt,
                max_tokens=reg.max_target_tokens,
                temperature=reg.target_temperature,
                client=http_client,
            )
        target_row = {
            "event": "model_pair", "pair_id": pid, "model": model,
            "category": cand.category, "strategy": cand.strategy,
            "english": dataclasses.asdict(pair.english),
            "romanized_hindi": dataclasses.asdict(pair.romanized_hindi),
        }
        store.append("traces.jsonl", target_row)
        if pair.english.error or pair.romanized_hindi.error:
            store.append("errors.jsonl", {
                "pair_id": pid, "model": model, "stage": "target",
                "en_error": pair.english.error, "rh_error": pair.romanized_hindi.error,
            })
            return None
        targets[key] = target_row

    # JUDGE: score only languages that are still missing.  This means an
    # interruption between EN and RH judging does not cause duplicate judging.
    async def get_score(lang: str):
        skey = (key, lang)
        if skey in scores:
            return _jr_from_score(scores[skey])
        prompt = cand.english_prompt if lang == "en" else cand.romanized_hindi_prompt
        response = target_row["english"]["content"] if lang == "en" else target_row["romanized_hindi"]["content"]
        judge_used = reg.judge_model
        fallback_used = False
        primary_error = None
        async with sem_judge:
            try:
                jr = await _to_thread(
                    judge.score_response_strict, cand.category, prompt, response,
                    judge_model=reg.judge_model, language=lang,
                    max_tokens=reg.max_judge_tokens, gate_questions=gate_questions,
                )
            except Exception as exc:
                primary_error = str(exc)
                if not reg.fallback_judge_model:
                    raise
                judge_used = reg.fallback_judge_model
                fallback_used = True
                jr = await _to_thread(
                    judge.score_response_strict, cand.category, prompt, response,
                    judge_model=reg.fallback_judge_model, language=lang,
                    max_tokens=reg.max_judge_tokens, gate_questions=gate_questions,
                )
        row = {
            "pair_id": pid, "model": model, "language": lang,
            "category": cand.category, "strategy": cand.strategy,
            **dataclasses.asdict(jr),
            "primary_judge_model": reg.judge_model,
            "judge_used": judge_used,
            "fallback_used": fallback_used,
            "primary_judge_error": primary_error,
        }
        store.append("scores.jsonl", row)
        scores[skey] = row
        return jr

    en_jr, rh_jr = await asyncio.gather(get_score("en"), get_score("rh"))
    fr = flip_detector.detect(
        category=cand.category, strategy=cand.strategy, model=model,
        en_result=en_jr, rh_result=rh_jr,
    )
    rec = dataclasses.asdict(fr)
    rec["pair_id"] = pid
    store.append("flips.jsonl", rec)
    flips[key] = rec
    return rec


def _summary(flips: list[dict]) -> dict:
    by_model = defaultdict(list)
    for f in flips:
        by_model[f["model"]].append(f)
    out = {}
    for model, rows in by_model.items():
        n = len(rows)
        en_refusal = sum(r["en_score"] == 0 for r in rows) / n if n else 0.0
        rh_refusal = sum(r["rh_score"] == 0 for r in rows) / n if n else 0.0
        out[model] = {
            "n": n,
            "en_refusal_rate": en_refusal,
            "rh_refusal_rate": rh_refusal,
            "refusal_gap_pp": 100.0 * (en_refusal - rh_refusal),
            "forward_flips": sum(bool(r["flip"]) for r in rows),
            "critical_flips": sum(bool(r["critical_flip"]) for r in rows),
        }
    return out


async def run_frozen_bank(config, bank_dir: str | Path, *, run_id: str | None = None,
                          limit_pairs: int | None = None,
                          target_models: list[str] | None = None) -> Path:
    validated = validate_bank(bank_dir, require_complete=True)
    manifest = validated["manifest"]
    all_records = validated["records"]
    records = all_records[:limit_pairs] if limit_pairs else all_records

    reg = model_registry.load(config.models_config)
    env_targets = model_registry.env_override_target_models()
    if target_models:
        reg = dataclasses.replace(reg, target_models=target_models)
    elif env_targets:
        reg = dataclasses.replace(reg, target_models=env_targets)

    run_id = run_id or time.strftime("revision_v2_run_%Y%m%d_%H%M%S")
    store = TraceStore(runs_root="runs", run_id=run_id)
    manifest_path = store.path("run_manifest.json")
    new_manifest = {
        "schema_version": 3,
        "run_id": run_id,
        "probe_bank_id": manifest["bank_id"],
        "probe_bank_sha256": validated["bank_sha256"],
        "bank_n_pairs": len(all_records),
        "selected_n_pairs": len(records),
        "smoke_limit_pairs": limit_pairs,
        "target_models": reg.target_models,
        "judge_model": reg.judge_model,
        "fallback_judge_model": reg.fallback_judge_model,
        "fallback_policy": "primary judge retries first; fallback only on unresolved primary judge failure",
        "same_frozen_bank_for_all_targets": True,
        "target_temperature": reg.target_temperature,
        "max_target_tokens": reg.max_target_tokens,
        "max_judge_tokens": reg.max_judge_tokens,
        "empty_target_system_prompt": True,
    }
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        immutable = ("probe_bank_sha256", "target_models", "judge_model", "target_temperature", "max_target_tokens")
        bad = [k for k in immutable if old.get(k) != new_manifest.get(k)]
        if bad:
            raise RuntimeError(
                f"Refusing unsafe resume of run_id={run_id}: experiment settings changed: {bad}. "
                "Use the original settings or a new --run-id."
            )
        # A smoke run may later be expanded to the full bank under the same id.
        old.update({
            "selected_n_pairs": len(records),
            "smoke_limit_pairs": limit_pairs,
            "fallback_judge_model": reg.fallback_judge_model,
            "fallback_policy": "primary judge retries first; fallback only on unresolved primary judge failure",
        })
        store.write_text("run_manifest.json", json.dumps(old, indent=2))
    else:
        store.write_text("run_manifest.json", json.dumps(new_manifest, indent=2))

    from . import category_spec
    gates = {cid: category_spec.load_by_id(cid).gate_questions for cid in manifest["categories"]}
    sem_target = asyncio.Semaphore(config.v3_concurrency)
    sem_judge = asyncio.Semaphore(config.v3_concurrency)
    targets, scores, flips_state = _load_state(store)
    print(f"judge fallback configured: {reg.fallback_judge_model or 'NONE'}", flush=True)

    selected_keys = {(r["pair_id"], m) for r in records for m in reg.target_models}
    pending = [(r, m) for r in records for m in reg.target_models if (r["pair_id"], m) not in flips_state]
    print(
        f"run-bank: {len(records)} pairs x {len(reg.target_models)} models = {len(selected_keys)} pair-model jobs; "
        f"already complete={len(selected_keys & set(flips_state))}, pending={len(pending)}",
        flush=True,
    )

    async with httpx.AsyncClient(timeout=180.0) as client:
        tasks = [
            _one(r, model, reg, store, sem_target, sem_judge, client,
                 gates[r["candidate"]["category"]], targets, scores, flips_state)
            for r, model in pending
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for (r, model), x in zip(pending, results):
        if isinstance(x, Exception):
            store.append("errors.jsonl", {
                "pair_id": r["pair_id"], "model": model,
                "stage": "worker", "error": repr(x),
            })

    # Summarize persisted completed observations, including work from earlier
    # invocations of this same run_id.
    _, _, final_flips = _load_state(store)
    selected_flips = [v for k, v in final_flips.items() if k in selected_keys]
    summary = _summary(selected_flips)
    summary["_progress"] = {
        "completed_pair_model_jobs": len(selected_flips),
        "expected_pair_model_jobs": len(selected_keys),
        "complete": len(selected_flips) == len(selected_keys),
    }
    store.write_text("summary.json", json.dumps(summary, indent=2))
    write_accounting_summary(store.dir / "api_accounting_summary.json")
    return store.dir
