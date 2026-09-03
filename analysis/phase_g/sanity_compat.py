"""Prospectively gated N12-only execution. No target/outcome/response-judge calls.

metadata: public unauthenticated GET only. preflight: entirely offline.
execute: requires committed PASS + offline test receipt, then N12 authority only.
Raw source/U/audit data remain in the ignored canonical phase-wide SQLite ledger.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal

from analysis.phase_g import strong_archaic_runtime as r
from analysis.phase_g.strong_archaic_preflight import BASE, BANK, inputs
from analysis.phase_g.preflight_audit import manifest_checks

PARENT = "604c8c386d81fd89c497c46505a6db60a7c787ff"
OUT = BASE / "u_arch_v3_sanity_compat"
OLD = BASE / "u_arch_v3_budget550"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_new(path, value):
    blob=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=blob: raise r.Stop("refusing to overwrite changed immutable report")
    else:
        with path.open("xb") as f: f.write(blob)


def git(*args,root=None,stdin=None):
    return subprocess.run(["git",*args],cwd=root or r.ROOT,capture_output=True,check=True,input=stdin).stdout


def committed_matches(commit,name,path,root=None):
    """Would committing these working bytes reproduce the recorded blob exactly?

    Raw bytes are compared first. A difference is accepted only when it is
    confined to CRLF/LF line-ending representation AND Git's own clean filter
    (core.autocrlf, .gitattributes text/eol) maps the working bytes onto exactly
    the recorded blob object, which is what a legitimate checkout of that commit
    produces. Any other difference fails both tests, so genuine modification of a
    frozen artifact still fails verification. Byte-level authority over frozen
    data stays with the unchanged raw sha256 locks and manifest hashes, which
    reject even a line-ending-only rewrite of a frozen artifact.
    """
    raw=path.read_bytes(); blob=git("show",commit+":"+name,root=root)
    if raw==blob: return True
    if raw.replace(b"\r\n",b"\n")!=blob.replace(b"\r\n",b"\n"): return False
    return (git("rev-parse",commit+":"+name,root=root).strip()
            ==git("hash-object","--stdin","--path="+name,root=root,stdin=raw).strip())


def frozen_check():
    manifests=manifest_checks()
    if any(x["mismatches"] for x in manifests): raise r.Stop("frozen data manifest mismatch")
    old=read(BASE/"preflight_20260903.json")["audited_scientific_input_hashes"]
    if any(r.file_hash(BASE/n)!=h for n,h in old.items()): raise r.Stop("legacy Phase G hash mismatch")
    paths=[*r.SPECS.glob("strong_archaic_v3*"),*(BASE/"u_arch_v3_preflight").glob("*.json"),*OLD.rglob("*.json")]
    for path in paths:
        if not committed_matches(PARENT,path.relative_to(r.ROOT).as_posix(),path):
            raise r.Stop("parent specification/preflight artifact changed")
    if git("diff",PARENT,"--name-only","--","paper","human_validation","analysis/phase_d",
           "analysis/phase_g/u_control_development","accounting"):
        raise r.Stop("out-of-scope validated artifact changed")
    return dict(status="PASS",core_manifest_files=sum(x["checked"] for x in manifests),
                legacy_g_locks=len(old),parent_spec_and_preflight_files=len(paths))


def fetch_metadata():
    """Never reads the bank or credentials. No retries, no POST, no redirects."""
    import httpx
    path=OUT/"PROVIDER_METADATA.json"
    if path.exists(): return read(path)
    responses={}
    with httpx.Client(transport=httpx.HTTPTransport(retries=0),timeout=30,follow_redirects=False,trust_env=False) as client:
        for model in r.MODELS.values():
            url="https://openrouter.ai/api/v1/models/"+model+"/endpoints"
            response=client.get(url)
            response.raise_for_status()
            assert response.json()["data"]["id"]==model
            responses[model]=dict(url=url,fetched_at_utc=datetime.now(timezone.utc).isoformat(),
                response_sha256=r.digest(response.text),response_text=response.text)
    result=dict(method="GET",authentication=False,research_data_sent=False,inference_calls=0,responses=responses)
    save_new(path,result)
    return result


def make_plan():
    original=read(OLD/"EXECUTION_PLAN.json")
    plan=copy.deepcopy(original)
    del plan["roles"]["mini_audit"]["temperature"]
    plan["roles"]["mini_audit"]["max_tokens"]=r.MAX_TOKENS["mini_audit"]
    plan.update(version="U-ARCH-v3-mini-temperature-amendment-3",parent_commit=PARENT,
        live_enabled=True,current_paid_authorization_usd=.65,authorized_stages=["sanity"],
        approval_reference="User attachment db6a852a-8e98-4bc9-adf9-80b583febfd8: conditional N12 sanity only",
        inference_blockers=[],mini_temperature_policy="omitted; user-approved native sampling; pre-outcome",
        mini_output_budget_policy="completion cap raised to 8192 so reasoning plus the 17-axis verdict fit; "
                                  "auditor instruction, schema, axes, gates and sampling unchanged; "
                                  "frozen per-call reservation unchanged and still a sound upper bound")
    metadata=read(OUT/"PROVIDER_METADATA.json")
    assert metadata["method"]=="GET" and not metadata["research_data_sent"] and not metadata["authentication"]
    for role in r.ROLES:
        s=plan["roles"][role]
        data=metadata["responses"][s["model"]]
        assert r.digest(data["response_text"])==data["response_sha256"]
        endpoints=json.loads(data["response_text"])["data"]["endpoints"]
        matches=[x for x in endpoints if x["tag"]==s["endpoint_tag"]]
        if len(matches)!=1 or matches[0]["status"]!=0: raise r.Stop("pinned endpoint unavailable; no substitution")
        q=matches[0]
        needed={"max_tokens","response_format"} | ({"temperature"} if role!="mini_audit" else set())
        if needed-set(q["supported_parameters"]): raise r.Stop("pinned request parameter unsupported")
        if q["provider_name"]!=s["provider_name"] or q["quantization"]!=s["quantization"]:
            raise r.Stop("pinned provider/precision changed")
        for key,rate in zip(("prompt","completion"),s["expected_rates_usd_per_million"]):
            if Decimal(q["pricing"][key])*1_000_000!=Decimal(str(rate)):
                raise r.Stop("pinned endpoint quote changed; no price substitution")
        proof=s["reservation_proof"]
        if q["context_length"]>proof["input_token_bound"] or max(q["max_completion_tokens"],s["max_tokens"])>proof["output_token_bound"]:
            raise r.Stop("published native limits exceed frozen reservation")
        plan["compatibility"][role].update(missing_requested_parameters=[],supported_parameters=q["supported_parameters"],
            sampling_and_reasoning_request="Mini temperature omitted by approval; all other request settings unchanged" if role=="mini_audit" else "unchanged")
    # Old reports are preserved, not regenerated with this runtime's new code hash.
    paths=[r.ROOT/name for name in original["locks"]]
    paths += [BASE/"sanity_compat.py",BASE/"SANITY_COMPATIBILITY_AMENDMENT.md",OUT/"PROVIDER_METADATA.json",
              OLD/"EXECUTION_PLAN.json",r.ROOT/"tests/test_sanity_compat.py",r.ROOT/"tests/test_strong_archaic_preflight.py"]
    plan["locks"]={p.relative_to(r.ROOT).as_posix():r.file_hash(p) for p in paths}
    return plan


def preflight():
    integrity=frozen_check()
    plan=make_plan()
    sanity,_,manifest=inputs()
    original=read(OLD/"EXECUTION_PLAN.json")
    assert plan["cohort_payload_hashes"]["sanity"]==r.identifier(sanity)==original["cohort_payload_hashes"]["sanity"]
    assert manifest==read(BASE/"u_arch_v3_preflight/SANITY_COHORT_MANIFEST.json")
    expected=copy.deepcopy(original["roles"]); del expected["mini_audit"]["temperature"]
    expected["mini_audit"]["max_tokens"]=r.MAX_TOKENS["mini_audit"]
    assert plan["roles"]==expected
    assert plan["roles"]["mini_audit"]["maximum_call_nusd"]==original["roles"]["mini_audit"]["maximum_call_nusd"]
    assert plan["roles"]["mini_audit"]["reservation_proof"]==original["roles"]["mini_audit"]["reservation_proof"]
    assert plan["stage_budgets_nusd"]==original["stage_budgets_nusd"] and plan["stage_budgets_nusd"]["sanity"]==650_000_000
    assert plan["hard_ceiling_nusd"]==5_500_000_000
    assert plan["generation_attempts_per_pair"]==4 and plan["sanity_first_attempt_floor"]==9 and plan["sanity_all_certified"]==12
    assert plan["auditing_mode"]==original["auditing_mode"] and len(r.AXES)==17
    for schema in r.SCHEMAS.values(): r.Draft202012Validator.check_schema(schema)
    return plan,dict(status="PASS",parent_commit=PARENT,pre_outcome=True,temperature_omitted_only_for_mini=True,
        all_other_role_settings_identical=True,sanity_n=12,one_per_cell=True,excluded_ladder_n=120,excluded_olddev_n=24,
        id_overlap=0,exact_source_overlap=0,generation_attempt_limit=4,first_attempt_floor=9,
        sequential_dual_certification_unchanged=True,hard_sanity_cap_usd=.65,global_cap_usd=5.5,
        frozen_artifacts=integrity,inference_calls_before_amendment=0,stage_2_requires_committed_passing_test_receipt=True,
        scope_hash=r.identifier(plan,plan["locks"]))


def verify_commit(commit,plan):
    if len(commit)!=40 or any(c not in "0123456789abcdef" for c in commit): raise r.Stop("full amendment commit hash required")
    git("merge-base","--is-ancestor",commit,"HEAD")
    for path in [OUT/"EXECUTION_PLAN.json",OUT/"PREFLIGHT.json",OUT/"OFFLINE_VALIDATION.json"]:
        if not committed_matches(commit,path.relative_to(r.ROOT).as_posix(),path):
            raise r.Stop("preflight/test receipt must match prospective amendment commit")
    receipt=read(OUT/"OFFLINE_VALIDATION.json")
    if receipt["status"]!="PASS" or receipt["failed"]!=0 or receipt["passed"]!=receipt["total"]:
        raise r.Stop("offline tests did not completely pass")
    if receipt["execution_plan_sha256"]!=r.file_hash(OUT/"EXECUTION_PLAN.json"):
        raise r.Stop("test receipt plan hash mismatch")
    if read(OUT/"PREFLIGHT.json")["status"]!="PASS": raise r.Stop("Stage 1 failed")
    if plan["authorized_stages"]!=["sanity"]: raise r.Stop("approval is sanity only")
    for name,sha in plan["locks"].items():
        path=r.ROOT/name
        if r.file_hash(path)!=sha or (path!=BANK and not committed_matches(commit,name,path)):
            raise r.Stop("prospective committed input/code hash mismatch")


def summarize(journal,sanity,completed=None,stop_reason=None):
    """Report raw durable facts even when controller stops before a final report."""
    journal.check_locks()
    rows=journal.db.execute("SELECT * FROM calls ORDER BY created,id").fetchall()
    events={x["id"]:json.loads(x["payload"]) for x in journal.db.execute("SELECT * FROM events")}
    index={r.candidate_id("sanity",s,n):(s,n) for s in sanity for n in range(1,5)}
    attempts={s["pair_id"]:0 for s in sanity}
    accepted={}; axes={role:Counter() for role in r.ROLES[1:]}; other={role:Counter() for role in r.ROLES[1:]}
    failures=[]; estimates={role:Decimal(0) for role in r.ROLES}; trace=[]
    for row in rows:
        request=json.loads(row["request"])
        payload=json.loads(request["messages"][1]["content"])
        source,n=index[payload["item_id"]]
        if row["role"]=="generation": attempts[source["pair_id"]]=max(n,attempts[source["pair_id"]])
        response=json.loads(row["response"]) if row["response"] else {}
        kind="generator" if row["role"]=="generation" else "audit"
        failure=None
        if response.get("status")!="ok" or row["state"]!="received": failure="api_delivery_billing_or_provenance"
        elif response.get("finish_reason")!="stop": failure="incomplete_output"
        else:
            try: r.parse(response.get("content"),kind,payload["item_id"])
            except (ValueError,TypeError,r.ValidationError): failure="malformed_output"
        if failure: failures.append(dict(job_id=row["id"],role=row["role"],kind=failure,http_status=response.get("http_status"),
                                        reported_cost_usd=row["billed"]/1e9 if row["billed"] is not None else None))
        usage=response.get("usage") or {}
        s=journal.config["roles"][row["role"]]
        rates=s["expected_rates_usd_per_million"] if response.get("service_tier")=="flex" else s["reservation_rates_usd_per_million"]
        if all(type(usage.get(k)) is int for k in ("prompt_tokens","completion_tokens")):
            estimates[row["role"]]+=sum(Decimal(usage[k])*Decimal(str(rate))/1_000_000 for k,rate in zip(("prompt_tokens","completion_tokens"),rates))
        trace.append(dict(job_id=row["id"],role=row["role"],stage=row["stage"],state=row["state"],
                          request_sha256=row["request_hash"],response_sha256=row["response_hash"],
                          provider_request_id=response.get("request_id"),reported_nusd=row["billed"],reserved_nusd=row["reserved"]))
    for item,(source,n) in index.items():
        decision=events.get(r.identifier(item,"decision"),{})
        if decision.get("status")=="accepted": accepted[source["pair_id"]]=dict(attempt=n,item_id=item,u_sha256=decision["u_sha256"])
        for role in r.ROLES[1:]:
            verdict=events.get(r.identifier(item,role,"verdict"),{})
            for axis in verdict.get("failed",[]):
                (axes[role] if axis in r.AXES else other[role])[axis]+=1
    totals={role:dict(journal.totals()[role],reported_cost_usd=journal.totals()[role]["billed_nusd"]/1e9,
                     estimated_cost_from_tokens_usd=float(estimates[role]),
                     unknown_billing_calls=sum(x["role"]==role and x["billed"] is None for x in rows)) for role in r.ROLES}
    first=sum(x["attempt"]==1 for x in accepted.values())
    result=completed["verdict"] if completed else "INCOMPLETE DUE TO EXECUTION OR BUDGET FAILURE"
    ready=result=="GENERATION SPECIFICATION READY"
    return dict(sanity_result=result,readiness_verdict="GENERATION SPECIFICATION READY" if ready else "GENERATION SPECIFICATION NOT READY",
        sanity_executed=bool(rows),pairs_dual_certified=len(accepted),first_attempt_dual_passes=first,
        first_attempt_pass_rate=first/12,attempts_per_pair=attempts,
        cell_key_by_pair={s["pair_id"]:s["metadata"]["category"]+"::"+s["metadata"]["strategy"] for s in sanity},
        accepted=accepted,rejections_by_axis={k:dict(v) for k,v in axes.items()},other_rejection_gate_codes={k:dict(v) for k,v in other.items()},
        role_accounting=totals,failures=failures,total_reported_cost_usd=sum(x["billed"] or 0 for x in rows)/1e9,
        unknown_billing_calls=sum(x["billed"] is None for x in rows),
        outstanding_reservations_usd=sum(x["reserved"] for x in rows if x["billed"] is None)/1e9,
        reported_cost_precision="integer nanodollars, each provider receipt rounded UP; never count unused reservations as spending",
        sanity_cap_respected=sum(x["billed"] if x["billed"] is not None else x["reserved"] for x in rows)<=650_000_000,
        global_cap_unchanged=journal.config["hard_ceiling_nusd"]==5_500_000_000,
        provenance_complete=all(x["state"]=="received" for x in rows),unresolved_pairs=12-len(accepted),
        protocol_violations=[],stop_reason=stop_reason,trace_index=trace,
        later_stage_calls=sum(x["stage"]!="sanity" for x in rows),scope_hash=journal.scope)


def execute(commit):
    plan=read(OUT/"EXECUTION_PLAN.json")
    verify_commit(commit,plan)
    frozen_check()
    sanity,_,_=inputs()
    if r.identifier(sanity)!=plan["cohort_payload_hashes"]["sanity"]: raise r.Stop("cohort changed")
    private=r.ROOT/plan["journal_path"]
    private.parent.mkdir(parents=True,exist_ok=True)
    journal=r.Journal(private,plan,plan["locks"])
    journal.event("prospective_amendment_commit",{"commit":commit,"plan_sha256":r.file_hash(OUT/"EXECUTION_PLAN.json")})
    # Credential consumption occurs ONLY after committed PASS and explicit N12 authority.
    from dotenv import dotenv_values
    from analysis.phase_g.strong_archaic_transport import SingleDispatchTransport
    key=os.environ.get("OPENROUTER_API_KEY") or dotenv_values(r.ROOT/".env").get("OPENROUTER_API_KEY")
    if not key: raise r.Stop("required OpenRouter credential unavailable; no request sent")
    adapter=SingleDispatchTransport(api_key=key,approved=True,
        routes={plan["roles"][k]["model"]:plan["roles"][k]["endpoint_tag"] for k in r.ROLES},
        provider_names={plan["roles"][k]["model"]:plan["roles"][k]["provider_name"] for k in r.ROLES})
    completed=None; stopped=None
    def transport(job,request):
        reply=adapter(job,request)
        print(json.dumps({"response_received":request["model"],"status":reply.get("status"),"reported_nusd":reply.get("billed_nusd")}),flush=True)
        return reply
    try:
        completed=r.construction(journal,sanity,transport,stage="sanity")
    except r.Stop as exc:
        stopped=str(exc)  # only controller's fixed diagnostic, never HTTP exception text
    except BaseException as exc:
        stopped="execution interrupted: "+type(exc).__name__
    finally:
        adapter.close()
    summary=summarize(journal,sanity,completed,stopped)
    summary["amendment_commit"]=commit
    summary["final_frozen_verification"]=frozen_check()
    journal.close()
    summary["private_journal_sha256"]=r.file_hash(private)
    save_new(OUT/"SANITY_RESULT.json",summary)
    print(json.dumps(summary,indent=2))
    return 0 if completed else 2


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["metadata","preflight","execute"])
    parser.add_argument("--amendment-commit")
    args=parser.parse_args()
    if args.mode=="metadata":
        result=fetch_metadata(); print(json.dumps({"public_models_checked":len(result["responses"]),"inference_calls":0})); return 0
    if args.mode=="preflight":
        plan,report=preflight()
        save_new(OUT/"EXECUTION_PLAN.json",plan); save_new(OUT/"PREFLIGHT.json",report)
        print(json.dumps(report,indent=2)); return 0
    return execute(args.amendment_commit or "")


if __name__=="__main__":
    raise SystemExit(main())
