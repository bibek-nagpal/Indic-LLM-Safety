"""Deterministic OFFLINE selection/cost preflight; never generates U or calls APIs.

Run from repository root:
  .analysis-venv/Scripts/python.exe -B -m analysis.phase_g.strong_archaic_preflight --write
Outputs only identifiers, hashes, aggregate token/cost evidence and execution pins.
Existing output files must be byte-identical; no silent artifact replacement.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import math
import socket
import sys
from pathlib import Path

import yaml

from analysis.phase_g.strong_archaic_runtime import (ROOT, SPECS, MODELS, SCHEMAS, canonical,
                                                    digest, file_hash, identifier, messages, candidate_id)
from analysis.phase_g.preflight_audit import manifest_checks

BASE = ROOT / "analysis/phase_g"
BANK = ROOT / "frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/pairs.jsonl"
OUT = BASE / "u_arch_v3_preflight"
SEED = "phase-g-u-strong-archaic-sanity-v3|20260903"
CATEGORIES = ("gambling", "intoxication", "sexual_violence", "violence")
STRATEGIES = ("RolePrompting", "ScenarioNesting", "SymbolicMasking")


def offline_only(*args, **kwargs):
    raise RuntimeError("external access prohibited in this offline preflight")


def inputs():
    assert file_hash(BANK) == "fd13908cb1687a89b5256d54462dcba49e610ad21b2ff55ac53e4add7ff9fafa"
    assert file_hash(BASE/"selection_n96.csv") == "56f0961ea0762ea0c4873f4eb2c4c04f5d0b2e0c87d57f172255f07a014b7362"
    assert file_hash(BASE/"selection_n96_MANIFEST.json") == "aa066ec554c047af61ea11043c8b3deedccf51a8009b1e13ad67296cbbc2da2c"
    paths = [BASE / "selection_n120_MANIFEST.json",
             BASE / "u_control_development/DEVELOPMENT_COHORT_MANIFEST.json",
             BASE / "selection_n96_MANIFEST.json"]
    ladder, olddev, main = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    l_ids, d_ids, m_ids = set(ladder["selected_pair_ids"]), set(olddev["development_pair_ids"]), set(main["selected_pair_ids"])
    assert len(l_ids) == 120 and len(d_ids) == 24 and len(m_ids) == 96 and not l_ids & d_ids
    assert m_ids <= l_ids
    bank = {}
    for line in BANK.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        c = record["candidate"]
        # Whitelist source fields: no R, scores, targets, response lengths or notes.
        row = dict(pair_id=record["pair_id"], source_E=c["english_prompt"],
                   source_E_sha256=digest(c["english_prompt"]), metadata={
                       "category": c["category"], "strategy": c["strategy"],
                       "scenario": c.get("scenario"), "target_group": c.get("target_group"),
                       "information_requested": c.get("info_level_requested")})
        assert row["pair_id"] not in bank
        bank[row["pair_id"]] = row
    assert len(bank) == 504 and (l_ids | d_ids) <= bank.keys()
    cells = collections.defaultdict(list)
    for pid, row in bank.items():
        if pid in l_ids | d_ids: continue
        c, s = row["metadata"]["category"], row["metadata"]["strategy"]
        rank = digest("\x1f".join((SEED, pid, c, s)))
        cells[c, s].append((rank, pid))
    expected_cells = {(c, s) for c in CATEGORIES for s in STRATEGIES}
    assert cells.keys() == expected_cells
    sanity = [bank[sorted(cells[cell])[0][1]] for cell in sorted(cells)]
    s_ids = {r["pair_id"] for r in sanity}
    s_texts = {r["source_E"] for r in sanity}
    assert len(s_ids) == len(s_texts) == 12 and not s_ids & (l_ids | d_ids)
    assert not s_texts & {bank[p]["source_E"] for p in l_ids | d_ids}
    manifest = dict(version="U-ARCH-v3-sanity-amendment-1", parent_commit="b647e29d1ba456540b1594d110d8bb0f2f794901",
                    seed=SEED, bank_sha256=file_hash(BANK), n=12, candidates_generated=0,
                    per_cell=1, excluded_ladder_n=120, excluded_historical_development_n=24,
                    id_overlap=0, exact_source_overlap=0,
                    eligible_per_cell={"::".join(k): len(v) for k, v in sorted(cells.items())},
                    metadata_mapping={"information_requested": "candidate.info_level_requested (stored value, not inferred)"},
                    input_sha256={p.relative_to(ROOT).as_posix(): file_hash(p) for p in [BANK, *paths]},
                    selected=[dict(pair_id=r["pair_id"], **r["metadata"], source_E_sha256=r["source_E_sha256"],
                                   rank=digest("\x1f".join((SEED, r["pair_id"], r["metadata"]["category"], r["metadata"]["strategy"]))))
                              for r in sanity])
    # No source text or scenario metadata is exported to the public manifest.
    manifest["selected"] = [{k: r[k] for k in ("pair_id", "category", "strategy", "source_E_sha256", "rank")}
                             for r in manifest["selected"]]
    return sanity, [bank[p] for p in sorted(m_ids)], manifest


def cached_encodings():
    import tiktoken
    import tiktoken.load
    import tiktoken_ext.openai_public
    cached = Path(sys.prefix) / "Lib/site-packages/litellm/litellm_core_utils/tokenizers"
    evidence = {}
    def read_cached(url, expected_hash=None):
        path = cached / hashlib.sha1(url.encode()).hexdigest()
        blob = path.read_bytes()  # missing is a hard offline failure, never download
        assert hashlib.sha256(blob).hexdigest() == expected_hash
        evidence[path.name] = expected_hash
        return blob
    original = tiktoken.load.read_file_cached
    try:
        tiktoken.load.read_file_cached = read_cached
        tiktoken.load.read_file = offline_only
        # Constructors call the replaced reader even if the global registry is warm.
        enc = {name: tiktoken.Encoding(**getattr(tiktoken_ext.openai_public, name)())
               for name in ("cl100k_base", "o200k_base")}
    finally:
        tiktoken.load.read_file_cached = original
    return enc, evidence


def historical_prices():
    observations = collections.defaultdict(list)
    receipts = []
    for path in sorted((ROOT / "accounting").glob("api_calls_*.jsonl")):
        receipts.append({"path": path.relative_to(ROOT).as_posix(), "sha256": file_hash(path)})
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line: continue
            r = json.loads(line)
            u = r.get("usage_raw", {})
            d = u.get("cost_details", {})
            if u.get("prompt_tokens_details", {}).get("cached_tokens") or not r.get("prompt_tokens") or not r.get("completion_tokens"):
                continue
            if d.get("upstream_inference_prompt_cost") is None or d.get("upstream_inference_completions_cost") is None:
                continue
            observations[r["requested_model"]].append((
                round(d["upstream_inference_prompt_cost"] / r["prompt_tokens"] * 1e6, 7),
                round(d["upstream_inference_completions_cost"] / r["completion_tokens"] * 1e6, 7)))
    summary = {}
    for m, vals in observations.items():
        modal = collections.Counter(vals).most_common(1)[0]
        summary[m] = dict(n_uncached_receipts=len(vals), modal_rates=list(modal[0]), modal_n=modal[1],
                          min_rates=[min(v[i] for v in vals) for i in (0, 1)],
                          max_rates=[max(v[i] for v in vals) for i in (0, 1)])
    return summary, receipts


def judge_constant_module():
    # AST whitelist: read the exact pure builder/rubric without importing API client.
    tree = ast.parse((ROOT / "src/jailbreak_hermes/judge.py").read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if
             (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "JUDGE_SYSTEM" for t in n.targets))
             or (isinstance(n, ast.FunctionDef) and n.name == "build_judge_messages")]
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "frozen_judge_pure_builder", "exec"), namespace)
    return namespace


def costs(sanity, main):
    encs, assets = cached_encodings()
    prices, receipts = historical_prices()
    primary = encs["o200k_base"]
    count = lambda s: len(primary.encode_ordinary(s))
    # Wrapper margin is a PLANNING assumption, not an exact provider token bound.
    wrapper = 32
    profiles = {}
    role_inputs = {}
    for name, cohort in (("sanity", sanity), ("main", main)):
        profile = []
        for row in cohort:
            payload = dict(schema_version="U-ARCH-v3", item_id=candidate_id("sanity" if name=="sanity" else "main_construction",row,1), source_E=row["source_E"],
                           metadata=row["metadata"], prior_rejections=[])
            gen = messages("generation", payload)
            aud = dict(payload)
            del aud["prior_rejections"]
            aud["candidate_U"] = ""  # no U generated; future text represented ONLY as numeric tokens
            audit = messages("deepseek_audit", aud)
            profile.append({"pair_id": row["pair_id"], "source_tokens": count(row["source_E"]),
                            "generation_messages_o200k": sum(count(x["content"]) for x in gen),
                            "audit_empty_u_messages_o200k": sum(count(x["content"]) for x in audit),
                            "generation_messages_cl100k": sum(len(encs["cl100k_base"].encode_ordinary(x["content"])) for x in gen),
                            "audit_empty_u_messages_cl100k": sum(len(encs["cl100k_base"].encode_ordinary(x["content"])) for x in audit)})
        profiles[name] = profile
        avg = lambda key: sum(r[key] for r in profile) / len(profile)
        expected_u = math.ceil(1.5 * avg("source_tokens"))
        # Feedback at most 2 reports per failed candidate, 400 characters/reason;
        # expected scenario adds a 256-token allowance to EVERY generation call.
        # High envelope uses 8192 feedback tokens (six bounded reports + codes).
        role_inputs[name] = dict(
            generation_expected=math.ceil(avg("generation_messages_o200k"))+wrapper+256,
            generation_high=max(r["generation_messages_o200k"] for r in profile)+wrapper+8192+64,
            audit_expected=math.ceil(avg("audit_empty_u_messages_o200k"))+wrapper+expected_u,
            audit_high=max(r["audit_empty_u_messages_o200k"] for r in profile)+wrapper+8192+64,
            u_expected=expected_u, u_high=8192,
            generation_output_expected=min(4096, expected_u+256))
    rows = []
    def add(stage, role, expected_calls, high_calls, inp, high_inp, out, high_out, model):
        if model in prices:
            rate = prices[model]["modal_rates"]
            high_rate = prices[model]["max_rates"]
            evidence = "historical uncached billing; modal expected / observed max high; NOT current pricing"
        else:
            # Preserve documented old planning rates, explicitly not verified here.
            rate = {"qwen/qwen3-30b-a3b-instruct-2507": [.04815,.1931],
                    "openai/gpt-oss-20b": [.10,.50],
                    "nvidia/nemotron-3-nano-30b-a3b": [.05,.20]}[model]
            high_rate = rate
            evidence = "legacy locally recorded target rate; GPT-OSS is explicitly unverified"
        rows.append(dict(stage=stage, role=role, model=model, expected_calls=expected_calls, high_calls=high_calls,
                         expected_input_tokens_per_call=inp, high_input_tokens_per_call=high_inp,
                         expected_output_tokens_per_call=out, high_output_tokens_per_call=high_out,
                         expected_rates_usd_per_million=rate, high_rates_usd_per_million=high_rate,
                         price_evidence=evidence,
                         expected_input_cost=expected_calls*inp*rate[0]/1e6,
                         expected_output_cost=expected_calls*out*rate[1]/1e6,
                         high_input_cost=high_calls*high_inp*high_rate[0]/1e6,
                         high_output_cost=high_calls*high_out*high_rate[1]/1e6))
    for stage, n, maxgen in (("sanity",12,21), ("main",96,384)):
        v = role_inputs[stage]
        gen = n*5//4  # explicit 75% first / 25% second scenario, not a forecast
        audit = gen + math.ceil(.05*gen)  # one repair on 5% rounded UP of audits, separately for each role
        add(stage,"generation",gen,maxgen,v["generation_expected"],v["generation_high"],v["generation_output_expected"],4096,MODELS["generation"])
        for role in ("deepseek_audit","mini_audit"):
            add(stage,role,audit,maxgen*2,v["audit_expected"],v["audit_high"],3072,4096,MODELS[role])
    v = role_inputs["main"]
    for model in ("qwen/qwen3-30b-a3b-instruct-2507","openai/gpt-oss-20b","nvidia/nemotron-3-nano-30b-a3b"):
        add("targets",model,96+math.ceil(.05*96),288,v["u_expected"]+wrapper,v["u_high"]+wrapper,2048,4096,model)
    builder = judge_constant_module()["build_judge_messages"]
    judge_base = []
    for category in CATEGORIES:
        gates = yaml.safe_load((ROOT/f"configs/categories/{category}.yaml").read_text(encoding="utf-8"))["gate_questions"]
        judge_base.append(sum(count(m["content"]) for m in builder(category,"","",language="en",gate_questions=gates)))
    add("judging","gemini_judge",288+math.ceil(.05*288),864,
        math.ceil(sum(judge_base)/4)+wrapper+v["u_expected"]+2048,
        max(judge_base)+wrapper+v["u_high"]+8192,600,2048,MODELS["generation"])
    totals = {stage: {"expected": sum(r["expected_input_cost"]+r["expected_output_cost"] for r in rows if r["stage"]==stage),
                      "high": sum(r["high_input_cost"]+r["high_output_cost"] for r in rows if r["stage"]==stage)}
              for stage in ("sanity","main","targets","judging")}
    totals["full"] = {k:sum(x[k] for x in totals.values()) for k in ("expected","high")}
    # A sanity run that fails readiness can use all 48 gen +192 audit requests;
    # it MUST STOP, so this is NOT added to a completed full-phase scenario.
    failed_sanity_high = totals["sanity"]["high"]*48/21
    return dict(status="conditional planning estimates; no externally verified current price ceiling",
                tokenization="o200k_base proxy; cl100k sensitivity; not exact Gemini/DeepSeek/target token counts",
                tokenizer_asset_sha256=assets, source_profiles=profiles, input_envelopes=role_inputs,
                historical_price_summary=prices, price_receipt_hashes=receipts,
                assumptions=["75% first-generation / 25% second-generation success for expected scenario (not empirical)",
                             "5% extra format/known-retry calls rounded up per role; all are budgeted as fully billed",
                             "Expected audit output 3072 includes hidden reasoning; generation output 1.5xE +256; targets 2048; judge 600",
                             "High: 9 sanity first-pass +3 fourth-pass =21 generations; main all fourth-pass =384; two calls/auditor/candidate",
                             "High: three infrastructure attempts per target/judge job; never retry a valid target response or score",
                             "Future U and judge-response input envelope 8192 proxy tokens each; a stress assumption, NOT a provable cross-tokenizer bound",
                             "Exact first-attempt item IDs and source messages measured; high adds 64 tokens for other hexadecimal attempt IDs",
                             "High generation feedback allowance 8192 proxy tokens; feedback limited to 400 characters/report and six reports",
                             "No cache savings, provider discounts or batch savings credited",
                             "Hard ceiling is $10 globally, not permission or a guarantee of completing the high scenario"],
                rows=rows, totals=totals, failed_sanity_max_calls=240,
                failed_sanity_high_cost=failed_sanity_high, successful_sanity_high_calls=105,
                hard_ceiling_usd=10, api_calls_made=0)


def build():
    sanity, main, manifest = inputs()
    from jsonschema import Draft202012Validator
    for schema in SCHEMAS.values(): Draft202012Validator.check_schema(schema)
    assert len(SCHEMAS["audit"]["properties"]["axes"]["required"]) == 17
    frozen = manifest_checks()
    assert all(not r["mismatches"] for r in frozen)
    locks = {p.relative_to(ROOT).as_posix(): file_hash(p) for p in
             [*sorted(SPECS.glob("strong_archaic_v3*")), BANK,
              BASE/"selection_n96.csv", BASE/"selection_n96_MANIFEST.json",
              BASE/"selection_n120_MANIFEST.json",
              BASE/"config/phase_g.yaml", ROOT/"src/jailbreak_hermes/judge.py",
              BASE/"u_control_development/DEVELOPMENT_COHORT_MANIFEST.json",
              BASE/"strong_archaic_runtime.py", BASE/"strong_archaic_transport.py",
              BASE/"strong_archaic_preflight.py", BASE/"U_CONTROL_PROTOCOL_PROPOSED.md"]}
    locks.update({f"configs/categories/{c}.yaml":file_hash(ROOT/f"configs/categories/{c}.yaml") for c in CATEGORIES})
    plan = dict(version="U-ARCH-v3-sanity-amendment-1", live_enabled=False,
                hard_ceiling_nusd=10_000_000_000, current_paid_authorization_usd=0,
                cohort_payload_hashes={"sanity":identifier(sanity),"main_construction":identifier(main)},
                generation_attempts_per_pair=4, auditor_attempts_per_candidate=2,
                sanity_first_attempt_floor=9, sanity_all_certified=12,
                request_timeout_seconds=120, hidden_transport_retries=0, stream=False,
                auditor_policy="both independently for every mechanically valid new candidate",
                roles={role:dict(model=model,temperature=.4 if role=="generation" else 0,max_tokens=4096,
                                 maximum_call_nusd=None,
                                 request_parameters={"stream":False,"provider":{"allow_fallbacks":False,"require_parameters":True}})
                       for role,model in MODELS.items()},
                native_schema_mode="system schema plus strict local parsing; native structured mode not enabled",
                provider_route="UNVERIFIED; no live dispatch permitted",
                reasoning_configuration="UNVERIFIED compatibility and billable cap semantics; do not silently drop temperature",
                target_plan={"models":["qwen/qwen3-30b-a3b-instruct-2507","openai/gpt-oss-20b","nvidia/nemotron-3-nano-30b-a3b"],
                             "n_u_only_jobs":288,"temperature":0,"max_tokens":4096,"empty_system_prompt":True,
                             "attempts_per_job":3,"retry_valid_response":False,"controller_available":False},
                judge_plan={"model":"google/gemini-2.5-flash","n_u_only_jobs":288,"temperature":0,"max_tokens":2048,
                            "language":"en","attempts_per_job":3,"retry_valid_score":False,"cross_judge":False,
                            "rubric_builder_file_sha256":file_hash(ROOT/"src/jailbreak_hermes/judge.py"),"controller_available":False},
                locks=locks)
    cost = costs(sanity,main)
    blockers = ["Single-dispatch construction adapter is tested offline only; live provider compatibility is unverified. Legacy runner remains disabled/unsafe.",
                "Current provider route/prices, model availability, temperature support and reasoning/output-cap semantics require external verification, forbidden in this task.",
                "Verified per-call token/price upper bounds are missing; maximum_call_nusd is null and dispatch fails closed.",
                "Full high-cost completion exceeds $10; the existing ceiling stops work before exhaustion, not guarantees completion.",
                "Main preregistration/SAP still reference obsolete U design: prospectively reconcile before targets; not changed in this narrow amendment.",
                "No API approval: sanity NOT RUN. Main construction and targets require their later separate approvals."]
    report = dict(amendment_pre_outcome=True, sanity_rule_updated=True, sanity_cohort_valid=True,
                  schemas_valid=True, frozen_files_checked=sum(x["checked"] for x in frozen), frozen_mismatches=[],
                  no_u_generated=True, no_target_inference=True, api_calls=0,
                  external_calls=0, live_preflight="FAIL", blockers=blockers,
                  runtime_scope="construction controller plus single-dispatch HTTP adapter, offline-tested only; no target/judge execution controller",
                  cost_totals=cost["totals"], hard_budget_ceiling_usd=10,current_paid_authorization_usd=0)
    return {"SANITY_COHORT_MANIFEST.json":manifest,"EXECUTION_PLAN.json":plan,
            "COST_PREFLIGHT.json":cost,"PREFLIGHT.json":report}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true")
    args = parser.parse_args()
    socket.create_connection = offline_only
    socket.socket.connect = offline_only
    socket.getaddrinfo = offline_only
    outputs = build()
    if args.write:
        OUT.mkdir(parents=True,exist_ok=True)
        for name, value in outputs.items():
            path = OUT/name
            blob = (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
            if path.exists():
                if path.read_bytes()!=blob: raise SystemExit(f"Refusing to overwrite {name}; review/version the changed report")
            else:
                with path.open("xb") as f: f.write(blob)
    print(json.dumps(outputs["PREFLIGHT.json"],indent=2))
    # Return 1 for NOT ready, even though offline checks/serialization succeeded.
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
