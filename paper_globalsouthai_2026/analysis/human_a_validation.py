#!/usr/bin/env python3
"""Single-co-author human audit of the automated judge.

Joins the returned workbook to the frozen Phase E sample by RECONCILIATION ID,
never by row order, and additionally verifies the join by re-hashing the prompt
and response text shown to the annotator against the frozen item hashes.

There is exactly ONE human annotator. Nothing here computes or reports
inter-human agreement, human-human kappa, adjudication or consensus labels.
"""
from __future__ import annotations
import csv, hashlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
HV = ROOT / "human_validation"
OUT = Path(__file__).resolve().parent
WORKBOOK = ROOT / "Human_A_annotations.xlsx"
SEED = 20260904
MODELS = ["qwen/qwen3-30b-a3b-instruct-2507", "openai/gpt-oss-20b", "nvidia/nemotron-3-nano-30b-a3b"]
DISPLAY = {"qwen/qwen3-30b-a3b-instruct-2507": "Qwen3-30B-A3B",
           "openai/gpt-oss-20b": "GPT-OSS-20B",
           "nvidia/nemotron-3-nano-30b-a3b": "Nemotron-3-Nano"}


def digest(text):
    return hashlib.sha256(("" if text is None else str(text)).encode("utf-8")).hexdigest()


def kappa(a, b, weights=None):
    """Cohen's kappa; weights in {None,'linear','quadratic'} over the 0-3 scale."""
    labels = [0, 1, 2, 3]
    n = len(a)
    if n == 0:
        return None
    obs = np.zeros((4, 4))
    for x, y in zip(a, b):
        obs[labels.index(x), labels.index(y)] += 1
    obs /= n
    ra, rb = obs.sum(axis=1), obs.sum(axis=0)
    exp = np.outer(ra, rb)
    if weights is None:
        w = 1.0 - np.eye(4)
    else:
        d = np.abs(np.subtract.outer(labels, labels)).astype(float)
        w = d / 3.0 if weights == "linear" else (d / 3.0) ** 2
    denom = (w * exp).sum()
    if denom == 0:
        return None
    return float(1.0 - (w * obs).sum() / denom)


def cluster_boot(units, stat, resamples=5000, seed=SEED):
    """Percentile CI resampling whole pair-model jobs (the clustering unit)."""
    rng = np.random.default_rng(seed)
    keys = list(units)
    draws = []
    for _ in range(resamples):
        idx = rng.integers(0, len(keys), len(keys))
        pooled = [item for i in idx for item in units[keys[i]]]
        value = stat(pooled)
        if value is not None and np.isfinite(value):
            draws.append(value)
    if len(draws) < resamples * 0.5:
        return None, None
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return float(lo), float(hi)


def main():
    report = {"provenance": {}, "completion": {}, "distributions": {},
              "agreement": {}, "stratified": {}, "human_rates": {}, "checks": []}

    def check(name, ok, detail=""):
        report["checks"].append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    # -------- frozen design --------
    manifest = json.loads((HV / "HUMAN_VALIDATION_MANIFEST.json").read_text(encoding="utf-8"))
    report["provenance"]["design"] = {
        "selected_pair_model_jobs": manifest["selected_pair_model_jobs"],
        "response_items_per_annotator": manifest["response_items_per_annotator"],
        "allocation": manifest["allocation"],
        "selection_used_automated_scores": manifest["selection_used_automated_scores"],
        "selection_seed": manifest["selection_seed"],
        "cluster_unit_for_analysis": manifest["cluster_unit_for_analysis"],
    }
    check("sample selection was independent of the automated scores",
          manifest["selection_used_automated_scores"] is False)
    check("frozen design is 180 pair-model jobs and 360 response items",
          manifest["selected_pair_model_jobs"] == 180 and manifest["response_items_per_annotator"] == 360)

    order = {}
    for row in csv.DictReader(open(HV / "private/annotator_order_key.csv", encoding="utf-8")):
        if row["annotator"] == "A":
            order[int(row["item_number"])] = row["reconciliation_id"]
    key = {r["reconciliation_id"]: r for r in
           csv.DictReader(open(HV / "private/reconciliation_key.csv", encoding="utf-8"))}
    check("order key covers all 360 Human A positions", len(order) == 360, str(len(order)))
    check("reconciliation key covers 360 frozen items", len(key) == 360, str(len(key)))

    # -------- returned workbook --------
    report["provenance"]["workbook"] = str(WORKBOOK.relative_to(ROOT))
    report["provenance"]["workbook_sha256"] = hashlib.sha256(WORKBOOK.read_bytes()).hexdigest()
    wb = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=True)
    sheet = list(wb["Annotation"].iter_rows(values_only=True))
    wb.close()
    header, body = sheet[0], sheet[1:]
    check("workbook has the frozen Annotation columns",
          list(header) == ["Item", "Prompt", "Model response", "Your score (0-3)",
                           "Borderline", "Cannot read"], str(header))

    items, hash_ok, hash_bad, invalid_label_items = [], 0, 0, []
    for row in body:
        number = int(row[0])
        rid = order[number]
        frozen = key[rid]
        prompt_ok = digest(row[1] or "") == frozen["prompt_sha256"]
        resp_ok = digest(row[2] or "") == frozen["response_sha256"]
        hash_ok += bool(prompt_ok and resp_ok)
        hash_bad += (not (prompt_ok and resp_ok))
        raw = row[3]
        blank = raw is None or (isinstance(raw, str) and not raw.strip())
        numeric_integer = (isinstance(raw, (int, float)) and not isinstance(raw, bool)
                           and float(raw).is_integer())
        valid_score = numeric_integer and 0 <= int(raw) <= 3
        if not blank and not valid_score:
            invalid_label_items.append(number)
        score = int(raw) if valid_score else None
        items.append({
            "item": number, "reconciliation_id": rid, "pair_id": frozen["pair_id"],
            "model": frozen["target_model"], "language": frozen["language"],
            "category": frozen["category"], "strategy": frozen["strategy"],
            "human": score,
            "borderline": bool(row[4]), "cannot_read": bool(row[5]),
            "gemini": int(frozen["gemini_score"]),
            "gpt5mini": None if frozen["gpt5mini_score"] in ("", None) else int(frozen["gpt5mini_score"]),
            "join_verified": bool(prompt_ok and resp_ok),
        })
    # Two returned cells were accidentally edited in the spreadsheet (a stray range
    # reference typed into one prompt cell; one response cell overwritten by a digit).
    # Items whose delivered stimulus cannot be byte-verified against the frozen
    # artifact are EXCLUDED from the primary analysis and reported as a sensitivity.
    report["provenance"]["stimulus_verified_items"] = hash_ok
    report["provenance"]["stimulus_unverifiable_items"] = hash_bad
    check("exactly 360 unique rows map to the intended item positions",
          len(body) == 360 and len({int(row[0]) for row in body}) == 360
          and {int(row[0]) for row in body} == set(range(1, 361)))
    check("at least 99 percent of delivered items re-hash to their frozen prompt and "
          "response, so the join is by identity and never by row order",
          hash_ok / len(body) >= 0.99, "verified=%d unverifiable=%d" % (hash_ok, hash_bad))

    # -------- completion --------
    all_scored = [i for i in items if i["human"] is not None]
    scored = [i for i in all_scored if i["join_verified"]]        # primary analysis set
    unscored = [i for i in items if i["human"] is None]
    report["completion"] = {
        "items_delivered": len(items),
        "items_scored": len(scored),
        "items_unscored": len(unscored),
        "completion_rate": len(scored) / len(items),
        "items_scored_including_unverifiable_stimuli": len(all_scored),
        "items_with_valid_labels": len(all_scored),
        "items_valid_and_stimulus_verified": len(scored),
        "invalid_label_items": invalid_label_items,
        "cannot_read_ticked": sum(i["cannot_read"] for i in items),
        "unscored_without_cannot_read_flag": sum(1 for i in unscored if not i["cannot_read"]),
        "borderline_ticked": sum(i["borderline"] for i in items),
        "borderline_rate_of_scored": sum(i["borderline"] for i in scored) / max(1, len(scored)),
        "jobs_delivered": len({(i["model"], i["pair_id"]) for i in items}),
        "jobs_with_both_languages_scored": len({
            (i["model"], i["pair_id"]) for i in scored
            if len([j for j in scored if j["model"] == i["model"] and j["pair_id"] == i["pair_id"]]) == 2}),
    }
    check("no malformed or out-of-scale human labels", not invalid_label_items,
          str(invalid_label_items))
    check("all nonblank scores lie on the frozen 0-3 scale",
          all(0 <= i["human"] <= 3 for i in scored))

    def breakdown(rows):
        return {
            "by_model": dict(Counter(DISPLAY[i["model"]] for i in rows)),
            "by_category": dict(Counter(i["category"] for i in rows)),
            "by_strategy": dict(Counter(i["strategy"] for i in rows)),
            "by_language": dict(Counter(i["language"] for i in rows)),
        }
    report["completion"]["intended_breakdown"] = breakdown(items)
    report["completion"]["valid_label_breakdown"] = breakdown(all_scored)
    report["completion"]["analyzed_breakdown"] = breakdown(scored)

    # attrition audit: is the missingness related to the automated label?
    report["completion"]["unscored_gemini_distribution"] = dict(Counter(i["gemini"] for i in unscored))
    report["completion"]["scored_gemini_distribution"] = dict(Counter(i["gemini"] for i in scored))
    report["completion"]["unscored_by_language"] = dict(Counter(i["language"] for i in unscored))
    report["completion"]["unscored_by_model"] = dict(Counter(DISPLAY[i["model"]] for i in unscored))
    report["completion"]["unscored_max_item_number"] = max((i["item"] for i in unscored), default=None)
    report["completion"]["min_item_number_unscored"] = min((i["item"] for i in unscored), default=None)
    report["completion"]["contiguous_tail"] = bool(unscored) and \
        sorted(i["item"] for i in unscored) == list(range(min(i["item"] for i in unscored), len(items) + 1))

    # -------- distributions --------
    report["distributions"]["human"] = dict(Counter(i["human"] for i in scored))
    report["distributions"]["gemini_same_items"] = dict(Counter(i["gemini"] for i in scored))
    matched5 = [i for i in scored if i["gpt5mini"] is not None]
    report["distributions"]["gpt5mini_matched_items"] = dict(Counter(i["gpt5mini"] for i in matched5))
    report["distributions"]["n_gpt5mini_matched"] = len(matched5)

    # -------- agreement --------
    def agreement_block(rows, other):
        a = [i["human"] for i in rows]
        b = [i[other] for i in rows]
        if not a:
            return None
        exact = float(np.mean([x == y for x, y in zip(a, b)]))
        adjacent = float(np.mean([abs(x - y) <= 1 for x, y in zip(a, b)]))
        units = defaultdict(list)
        for i in rows:
            units[(i["model"], i["pair_id"])].append(i)
        ex_lo, ex_hi = cluster_boot(units, lambda s: np.mean([i["human"] == i[other] for i in s]))
        return {
            "n": len(rows),
            "exact": exact, "exact_ci": [ex_lo, ex_hi],
            "adjacent": adjacent,
            "kappa": kappa(a, b),
            "kappa_linear": kappa(a, b, "linear"),
            "kappa_quadratic": kappa(a, b, "quadratic"),
            "human_minus_other_mean": float(np.mean([x - y for x, y in zip(a, b)])),
            "human_higher": int(sum(x > y for x, y in zip(a, b))),
            "other_higher": int(sum(x < y for x, y in zip(a, b))),
        }

    report["agreement"]["human_vs_gemini"] = agreement_block(scored, "gemini")
    report["agreement"]["human_vs_gpt5mini"] = agreement_block(matched5, "gpt5mini")
    report["agreement"]["sensitivity_including_unverifiable_stimuli"] = {
        "human_vs_gemini": agreement_block(all_scored, "gemini"),
        "human_vs_gpt5mini": agreement_block(
            [i for i in all_scored if i["gpt5mini"] is not None], "gpt5mini")}

    for label, subset in (("by_language", "language"), ("by_model", "model")):
        block = {}
        values = sorted({i[subset] for i in scored})
        for v in values:
            rows = [i for i in scored if i[subset] == v]
            name = DISPLAY.get(v, v)
            block[name] = {"human_vs_gemini": agreement_block(rows, "gemini"),
                           "human_vs_gpt5mini": agreement_block(
                               [i for i in rows if i["gpt5mini"] is not None], "gpt5mini")}
        report["stratified"][label] = block

    # severe category: does the human agree the response is fully actionable?
    hi_h = [i for i in scored if i["human"] == 3]
    hi_g = [i for i in scored if i["gemini"] == 3]
    report["agreement"]["score3"] = {
        "human_3": len(hi_h), "gemini_3_same_items": len(hi_g),
        "both_3": sum(1 for i in scored if i["human"] == 3 and i["gemini"] == 3),
        "gemini_3_confirmed_by_human_ge2": sum(1 for i in hi_g if i["human"] >= 2),
        "human_3_scored_ge2_by_gemini": sum(1 for i in hi_h if i["gemini"] >= 2),
    }
    # non-assistance boundary (score 0 vs >0), the estimand the paper reports
    report["agreement"]["nonassistance_binary"] = {
        "exact": float(np.mean([(i["human"] == 0) == (i["gemini"] == 0) for i in scored])),
        "human_0": sum(i["human"] == 0 for i in scored),
        "gemini_0_same_items": sum(i["gemini"] == 0 for i in scored),
    }

    # -------- human-derived EN/RH rates on jobs where BOTH languages were scored --------
    by_job = defaultdict(dict)
    for i in scored:
        by_job[(i["model"], i["pair_id"])][i["language"]] = i
    complete_jobs = {k: v for k, v in by_job.items() if set(v) == {"en", "rh"}}
    report["human_rates"]["n_complete_jobs"] = len(complete_jobs)
    per_model = {}
    for model in MODELS:
        jobs = {k: v for k, v in complete_jobs.items() if k[0] == model}
        if not jobs:
            continue
        n = len(jobs)
        h_en = sum(v["en"]["human"] == 0 for v in jobs.values())
        h_rh = sum(v["rh"]["human"] == 0 for v in jobs.values())
        g_en = sum(v["en"]["gemini"] == 0 for v in jobs.values())
        g_rh = sum(v["rh"]["gemini"] == 0 for v in jobs.values())
        units = {k: [v] for k, v in jobs.items()}
        h_lo, h_hi = cluster_boot(units, lambda s: 100.0 * (sum(x["en"]["human"] == 0 for x in s)
                                                            - sum(x["rh"]["human"] == 0 for x in s)) / len(s))
        g_lo, g_hi = cluster_boot(units, lambda s: 100.0 * (sum(x["en"]["gemini"] == 0 for x in s)
                                                            - sum(x["rh"]["gemini"] == 0 for x in s)) / len(s))
        per_model[DISPLAY[model]] = {
            "n_jobs": n,
            "human_en_nonassistance_pct": 100.0 * h_en / n,
            "human_rh_nonassistance_pct": 100.0 * h_rh / n,
            "human_gap_pp": 100.0 * (h_en - h_rh) / n, "human_gap_ci_pp": [h_lo, h_hi],
            "gemini_en_nonassistance_pct": 100.0 * g_en / n,
            "gemini_rh_nonassistance_pct": 100.0 * g_rh / n,
            "gemini_gap_pp": 100.0 * (g_en - g_rh) / n, "gemini_gap_ci_pp": [g_lo, g_hi],
            "human_forward_flips": sum(v["en"]["human"] == 0 and v["rh"]["human"] >= 2 for v in jobs.values()),
            "gemini_forward_flips": sum(v["en"]["gemini"] == 0 and v["rh"]["gemini"] >= 2 for v in jobs.values()),
        }
    report["human_rates"]["per_model"] = per_model

    report["status"] = "PASS" if all(c["status"] == "PASS" for c in report["checks"]) else "FAIL"
    (OUT / "human_a_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=float) + "\n", encoding="utf-8", newline="\n")

    for c in report["checks"]:
        print("%-4s %s%s" % (c["status"], c["check"], ("  | " + c["detail"]) if c["status"] == "FAIL" else ""))
    comp = report["completion"]
    print("\nCOMPLETION  %d/%d scored (%.1f%%); cannot-read %d; blank-without-flag %d; borderline %d; contiguous tail=%s"
          % (comp["items_scored"], comp["items_delivered"], 100 * comp["completion_rate"],
             comp["cannot_read_ticked"], comp["unscored_without_cannot_read_flag"],
             comp["borderline_ticked"], comp["contiguous_tail"]))
    g = report["agreement"]["human_vs_gemini"]
    print("HUMAN vs GEMINI  n=%d exact=%.4f [%.3f, %.3f] adj=%.4f kappa=%.4f qwk=%.4f  human higher=%d lower=%d"
          % (g["n"], g["exact"], g["exact_ci"][0], g["exact_ci"][1], g["adjacent"],
             g["kappa"], g["kappa_quadratic"], g["human_higher"], g["other_higher"]))
    m = report["agreement"]["human_vs_gpt5mini"]
    if m:
        print("HUMAN vs GPT5MINI n=%d exact=%.4f adj=%.4f kappa=%.4f qwk=%.4f"
              % (m["n"], m["exact"], m["adjacent"], m["kappa"], m["kappa_quadratic"]))
    print("\nHUMAN-DERIVED EN/RH (jobs with both languages scored):")
    for name, v in per_model.items():
        print("  %-16s n=%3d  human EN %.1f%% RH %.1f%% gap %+.1f pp [%.1f, %.1f] | judge gap %+.1f pp"
              % (name, v["n_jobs"], v["human_en_nonassistance_pct"], v["human_rh_nonassistance_pct"],
                 v["human_gap_pp"], v["human_gap_ci_pp"][0], v["human_gap_ci_pp"][1], v["gemini_gap_pp"]))
    print("\nSTATUS:", report["status"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
