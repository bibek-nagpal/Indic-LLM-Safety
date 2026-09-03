"""Offline-only prospective financial amendment; no inference entry point.

Reads cached public endpoint evidence; no credentials, requests, new U text or
outcomes. --write creates immutable versioned reports, refusing changed files.
Historical amendment-1 reports are inputs only and never overwritten.
"""
from __future__ import annotations

import argparse
import json
import math
import socket
import subprocess
from decimal import Decimal, ROUND_CEILING

from analysis.phase_g import strong_archaic_runtime as r
from analysis.phase_g.strong_archaic_preflight import (BASE, BANK, CATEGORIES, inputs,
    costs as historical_profile_builder, offline_only)
from analysis.phase_g.preflight_audit import manifest_checks

PARENT = "8a7498445d651fcdcb30681e58f142f637f91cdd"
OUT = BASE / "u_arch_v3_budget550"
META = OUT / "provider_metadata"
STAGE_CAPS = dict(sanity=650_000_000, main_construction=2_600_000_000,
                  target_inference=750_000_000, judging=1_500_000_000)
ROUTES = {
    "generation": (r.MODELS["generation"], "google-ai-studio/flex", "google-ai-studio"),
    "deepseek_audit": (r.MODELS["deepseek_audit"], "deepinfra/fp8", "deepinfra/fp8"),
    "mini_audit": (r.MODELS["mini_audit"], "openai/flex", "openai"),
    "target_qwen": ("qwen/qwen3-30b-a3b-instruct-2507", "streamlake", "streamlake"),
    "target_oss": ("openai/gpt-oss-20b", "deepinfra/bf16", "deepinfra/bf16"),
    "target_nemotron": ("nvidia/nemotron-3-nano-30b-a3b", "crusoe/fp8", "crusoe/fp8"),
    "gemini_judge": (r.MODELS["generation"], "google-ai-studio/flex", "google-ai-studio"),
}
SOURCES = {
    "provider_routing_and_max_price": "https://openrouter.ai/docs/guides/routing/provider-selection",
    "parameters": "https://openrouter.ai/docs/api_reference/parameters",
    "reasoning_and_billing": "https://openrouter.ai/docs/guides/best-practices/reasoning-tokens",
    "flex_actual_tier_billing": "https://openrouter.ai/docs/guides/features/service-tiers",
    "google_dynamic_thinking": "https://ai.google.dev/gemini-api/docs/generate-content/thinking?hl=en",
}


def evidence(model):
    path = META / (model.replace("/", "__") + ".json")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["method"] == "GET" and record["status"] == 200
    assert not record["authentication"] and not record["research_data_sent"]
    assert r.digest(record["response_text"]) == record["response_sha256"]
    return json.loads(record["response_text"])["data"]["endpoints"]


def quote(model, route):
    matches = [x for x in evidence(model) if x["tag"] == route]
    assert len(matches) == 1 and matches[0]["status"] == 0
    return matches[0]


def reservation(proof):
    total = (Decimal(proof["input_rate_per_token"]) * proof["input_token_bound"]
             + Decimal(proof["output_rate_per_token"]) * proof["output_token_bound"])
    return int((total * 1_000_000_000).to_integral_value(rounding=ROUND_CEILING))


def configuration(sanity, main):
    catalog = json.loads((META/"selected_catalog.json").read_text(encoding="utf-8"))["selected_models"]
    roles, blockers, compatibility = {}, [], {}
    for role, (model, route, reserve_route) in ROUTES.items():
        live, upper = quote(model, route), quote(model, reserve_route)
        max_tokens = 2048 if role == "gemini_judge" else 4096
        construction = role in r.ROLES
        stage = ["sanity", "main_construction"] if construction else ["judging" if role=="gemini_judge" else "target_inference"]
        # Deliberately generous native bound: entire endpoint input context AND
        # its maximum output, plus requested visible tokens for possible separate
        # reasoning accounting. Neither a tiktoken proxy nor expected U length.
        proof = dict(input_token_bound=upper["context_length"],
                     output_token_bound=max(live["max_completion_tokens"], upper["max_completion_tokens"]) + max_tokens,
                     input_rate_per_token=upper["pricing"]["prompt"],
                     output_rate_per_token=upper["pricing"]["completion"],
                     basis="full published native endpoint limits; extra visible allowance; no caching; standard-tier price reservation")
        params = dict(stream=False, provider=dict(order=[route], only=[route],
                      allow_fallbacks=False, require_parameters=True,
                      max_price=dict(prompt=float(Decimal(proof["input_rate_per_token"])*1_000_000),
                                     completion=float(Decimal(proof["output_rate_per_token"])*1_000_000), request=0)))
        if construction or role == "gemini_judge": params["response_format"] = {"type":"json_object"}
        if route.endswith("/flex"): params["service_tier"] = "flex"
        required = {"temperature", "max_tokens"}
        if "response_format" in params: required.add("response_format")
        missing = sorted(required - set(live["supported_parameters"]))
        compatibility[role] = dict(supported_parameters=live["supported_parameters"], missing_requested_parameters=missing,
                                   provider_status=live["status"], route=route,
                                   reasoning_metadata=catalog[model].get("reasoning"),
                                   sampling_and_reasoning_request="unchanged temperature; reasoning omitted as before, not disabled or lowered")
        if missing: blockers.append(f"{role}: pinned {model} on {route} does not support {missing}; approval required before changing sampling, no silent omission")
        roles[role] = dict(model=model, canonical_model=catalog[model]["canonical_slug"],
                           temperature=.4 if role=="generation" else 0, max_tokens=max_tokens,
                           allowed_stages=stage, request_parameters=params,
                           provider_name=live["provider_name"], endpoint_tag=route,
                           quantization=live["quantization"], reservation_proof=proof,
                           billed_output_token_bound=proof["output_token_bound"], maximum_call_nusd=reservation(proof),
                           expected_rates_usd_per_million=[float(Decimal(live["pricing"][k])*1_000_000) for k in ("prompt","completion")],
                           reservation_rates_usd_per_million=[float(Decimal(upper["pricing"][k])*1_000_000) for k in ("prompt","completion")])
    locks = {p.relative_to(r.ROOT).as_posix():r.file_hash(p) for p in [BANK,
        *sorted(r.SPECS.glob("strong_archaic_v3*")), *sorted(META.glob("*.json")),
        *sorted((BASE/"u_arch_v3_preflight").glob("*.json")),
        BASE/"selection_n96.csv", BASE/"selection_n96_MANIFEST.json", BASE/"selection_n120_MANIFEST.json",
        BASE/"u_control_development/DEVELOPMENT_COHORT_MANIFEST.json",
        BASE/"strong_archaic_runtime.py", BASE/"strong_archaic_transport.py", BASE/"budget550_preflight.py",
        BASE/"U_CONTROL_PROTOCOL_PROPOSED.md", BASE/"BUDGET550_AMENDMENT.md",
        r.ROOT/"src/jailbreak_hermes/judge.py", *[r.ROOT/f"configs/categories/{c}.yaml" for c in CATEGORIES]]}
    return dict(version="U-ARCH-v3-budget550-amendment-2", parent_commit=PARENT, live_enabled=False,
                current_paid_authorization_usd=0, hard_ceiling_nusd=r.HARD_CEILING_NUSD,
                stage_budgets_nusd=STAGE_CAPS, roles=roles, inference_blockers=blockers,
                compatibility=compatibility, locks=locks,
                cohort_payload_hashes={"sanity":r.identifier(sanity),"main_construction":r.identifier(main)},
                generation_attempts_per_pair=4, auditor_requests_per_candidate_per_role=2,
                sanity_first_attempt_floor=9, sanity_all_certified=12,
                auditing_mode="DeepSeek first; Mini only on valid primary pass; identical independent payloads",
                target_u_only_jobs=288, judge_u_only_jobs=288, target_and_judge_max_requests_per_job=3,
                target_judge_controllers_available=False, target_outcomes_in_development=False,
                timeout_seconds=120, transport_retries=0, journal_path="analysis/phase_g/u_arch_v3_private/phase_g_budget550.sqlite",
                no_automatic_stage_transfer=True, single_cumulative_journal_required=True)


def budget(config, sanity, main):
    # Reuse the pure exact-source/system/schema token profiler, not its old prices
    # or call counts. It reads outcomes nowhere and generates no U text.
    profile = historical_profile_builder(sanity, main)
    rows = []
    def add(stage, role, calls, max_calls, inp, out, assumptions):
        setting = config["roles"][role]
        rates = setting["expected_rates_usd_per_million"]
        std = setting["reservation_rates_usd_per_million"]
        rows.append(dict(stage=stage, role=role, expected_calls=calls, protocol_max_calls=max_calls,
                         expected_input_tokens_per_call=inp, expected_billed_output_tokens_per_call=out,
                         expected_input_cost_usd=calls*inp*rates[0]/1e6,
                         expected_output_cost_usd=calls*out*rates[1]/1e6,
                         expected_standard_tier_cost_usd=calls*(inp*std[0]+out*std[1])/1e6,
                         unconstrained_sum_of_call_reservations_usd=max_calls*setting["maximum_call_nusd"]/1e9,
                         assumptions=assumptions))
    for stage, old, gen, ds, mini, maxgen in (
        ("sanity","sanity",15,16,14,21),
        ("main_construction","main",120,126,114,384)):
        v = profile["input_envelopes"][old]
        add(stage,"generation",gen,maxgen,v["generation_expected"],v["generation_output_expected"]+512,
            "75% first /25% second generation; visible U+JSON proxy plus 512 billed thinking tokens, assumed not measured")
        for role,calls in (("deepseek_audit",ds),("mini_audit",mini)):
            add(stage,role,calls,maxgen*2,v["audit_expected"],3072,
                "all 17 axes in one response; output includes reasoning; 5% extra billed repairs rounded up separately")
    v=profile["input_envelopes"]["main"]
    for role in ("target_qwen","target_oss","target_nemotron"):
        add("target_inference",role,101,288,v["u_expected"]+32,2048,
            "96 U-only jobs/model plus ceil(5%)=5 retries; output includes reasoning; zero E/R repeats")
    judge=next(x for x in profile["rows"] if x["role"]=="gemini_judge")
    add("judging","gemini_judge",303,864,judge["expected_input_tokens_per_call"],600+512,
        "288 U-only scores plus ceil(5%)=15 retries; frozen judge prompt, 600 visible +512 thinking planning tokens")
    totals={s:dict(expected_cost_usd=sum(x["expected_input_cost_usd"]+x["expected_output_cost_usd"] for x in rows if x["stage"]==s),
                   standard_tier_expected_usd=sum(x["expected_standard_tier_cost_usd"] for x in rows if x["stage"]==s),
                   hard_authorized_usd=cap/1e9,
                   unconstrained_protocol_reservation_sum_usd=sum(x["unconstrained_sum_of_call_reservations_usd"] for x in rows if x["stage"]==s))
            for s,cap in STAGE_CAPS.items()}
    totals["full"]={k:sum(t[k] for t in totals.values()) for k in next(iter(totals.values()))}
    # Combined visible-output caps alone exceed the phase budget on the maximum
    # retry path, even before any input or additional thinking-token charges.
    output_only=sum(x["protocol_max_calls"]*config["roles"][x["role"]]["max_tokens"]*
                    config["roles"][x["role"]]["expected_rates_usd_per_million"][1]/1e6 for x in rows)
    return dict(rows=rows, totals=totals, source_profiles=profile["source_profiles"],
                tokenizer_asset_sha256=profile["tokenizer_asset_sha256"], input_envelopes=profile["input_envelopes"],
                tokenization=profile["tokenization"],
                expected_rejection_locations={"sanity":{"deepseek":2,"mini":1},"main":{"deepseek":12,"mini":12}},
                expected_call_count=sum(x["expected_calls"] for x in rows),
                successful_sanity_protocol_max_calls=105, failed_sanity_protocol_max_calls=240,
                failed_sanity_unconstrained_reservation_sum_usd=sum(config["roles"][role]["maximum_call_nusd"]*n/1e9
                                                                    for role,n in (("generation",48),("deepseek_audit",96),("mini_audit",96))),
                full_protocol_output_caps_only_flex_usd=output_only,
                full_completion_guaranteed_under_550=False, expected_scenario_fits=True,
                hard_limits_are_abort_caps_not_completion_quotes=True,
                assumptions=["No cache savings credited; Flex contingent on actually served tier; standard rates reserved",
                             "Expected lengths/candidate failure locations/retry rates are scenarios, not observed U results",
                             "Four generation requests total; at most two requests per dispatched auditor; valid rejects never repolled",
                             "Protocol maxima may be cut short by financial stops; no paid approval in this task",
                             "No fee top-ups, tax, other tasks or provider billing-contract violation can be controlled by this local ledger"],
                sources=SOURCES)


def build():
    sanity,main,manifest=inputs()
    old=json.loads((BASE/"u_arch_v3_preflight/SANITY_COHORT_MANIFEST.json").read_text(encoding="utf-8"))
    assert old==manifest
    for schema in r.SCHEMAS.values(): r.Draft202012Validator.check_schema(schema)
    assert len(r.AXES)==17
    frozen=manifest_checks()
    assert all(not x["mismatches"] for x in frozen)
    old_g=json.loads((BASE/"preflight_20260903.json").read_text(encoding="utf-8"))["audited_scientific_input_hashes"]
    assert all(r.file_hash(BASE/name)==sha for name,sha in old_g.items())
    preserved={}
    for path in [*sorted(r.SPECS.glob("strong_archaic_v3*")), *sorted((BASE/"u_arch_v3_preflight").glob("*.json"))]:
        relative=path.relative_to(r.ROOT).as_posix()
        original=subprocess.run(["git","show",f"{PARENT}:{relative}"],cwd=r.ROOT,check=True,capture_output=True).stdout
        assert path.read_bytes()==original, f"Frozen parent bytes changed: {relative}"
        preserved[relative]=r.file_hash(path)
    config=configuration(sanity,main)
    calculated=budget(config,sanity,main)
    report=dict(parent_commit=PARENT, pre_outcome_amendment=True, scientific_gates_changed=False,
                sanity_cohort_valid=True, cohort_unchanged=True, schemas_valid=True,
                frozen_files_checked=sum(x["checked"] for x in frozen), frozen_mismatches=[],
                old_g_byte_locks_checked=len(old_g), preserved_parent_file_hashes=preserved,
                public_metadata_gets=7, paid_inference_calls=0, generated_u=0, sanity_run=False,
                hard_authorized_full_cost_usd=5.5, current_paid_approval_usd=0,
                sanity_execution_preflight="FAIL" if config["inference_blockers"] else "PASS",
                blockers=config["inference_blockers"]+[
                    "Sanity paid approval not supplied in this task; no inference entry point enabled",
                    "Before targets: prospectively reconcile old preregistration/SAP and implement/test target/judge adapters against SAME ledger",
                    "Public quotes cannot prove an actual paid request; rate caps/no fallback/receipt checks must stay enabled",
                    "Completion at maximum permitted retries is not guaranteed for $5.50; stop incomplete rather than weaken gates"],
                costs=calculated["totals"], source_urls=SOURCES)
    return {"EXECUTION_PLAN.json":config,"COST_PREFLIGHT.json":calculated,"PREFLIGHT.json":report}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args()
    socket.create_connection=offline_only
    socket.socket.connect=offline_only
    socket.getaddrinfo=offline_only
    outputs=build()
    if args.write:
        for name,value in outputs.items():
            blob=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
            path=OUT/name
            if path.exists():
                if path.read_bytes()!=blob: raise SystemExit(f"Refusing overwrite of changed {name}")
            else:
                with path.open("xb") as f: f.write(blob)
    print(json.dumps(outputs["PREFLIGHT.json"],indent=2))
    return 1 if outputs["PREFLIGHT.json"]["sanity_execution_preflight"]=="FAIL" else 0


if __name__=="__main__":
    raise SystemExit(main())
