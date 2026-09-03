"""Offline fault injection with fixed BENIGN fixture strings, not real U prompts.

All certification values below are synthetic control-flow fixtures, not scientific
judgments about their text. Sockets are blocked, including in HTTP adapter tests.
"""
import copy
import json
import socket
import sqlite3
from collections import Counter

import httpx
import pytest
from jsonschema import Draft202012Validator, ValidationError

from analysis.phase_g import strong_archaic_runtime as r
from analysis.phase_g.strong_archaic_preflight import inputs, offline_only, costs
from analysis.phase_g.strong_archaic_transport import SingleDispatchTransport


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket,"connect",offline_only)
    monkeypatch.setattr(socket,"create_connection",offline_only)
    monkeypatch.setattr(socket,"getaddrinfo",offline_only)


def cohort():
    rows = []
    for category in ("gambling","intoxication","sexual_violence","violence"):
        for strategy in ("RolePrompting","ScenarioNesting","SymbolicMasking"):
            text = f"BENIGN FIXTURE ONLY: arrange the library books. {len(rows)}"
            rows.append(dict(pair_id=f"fixture-{len(rows):02d}",source_E=text,source_E_sha256=r.digest(text),
                             metadata=dict(category=category,strategy=strategy,scenario=None,target_group=None,information_requested=None)))
    return rows


def config(rows=None, ceiling=1_000_000_000):
    rows = rows or cohort()
    return dict(hard_ceiling_nusd=ceiling,cohort_payload_hashes={"sanity":r.identifier(rows),"main_construction":r.identifier(rows)},
                stage_budgets_nusd=dict(sanity=ceiling,main_construction=0,target_inference=0,judging=0),
                roles={role:dict(model=model,temperature=.4 if role=="generation" else 0,max_tokens=4096,
                                 allowed_stages=["sanity","main_construction"],
                                 maximum_call_nusd=1000,request_parameters={"stream":False,
                                     "provider":{"order":["fixture-provider"],"only":["fixture-provider"],"allow_fallbacks":False,"require_parameters":True}})
                       for role,model in r.MODELS.items()})


def audit_fixture(item, strategy):
    # Populate the exact frozen schema, using benign placeholder representations.
    request = {k: "fixture" if v.get("type")=="string" else ["fixture"]
               for k,v in r.SCHEMAS["audit"]["properties"]["E_request"]["properties"].items()}
    structure = dict(layers=[],mappings=[],role=None)
    if strategy=="RolePrompting":
        structure["role"] = {k:"fixture" for k in ("persona","authority","addressee","operative_instruction")}
    elif strategy=="ScenarioNesting":
        structure["layers"] = [dict(identity=str(i),attribution="fixture",contained_request="fixture") for i in (1,2)]
    else:
        structure["mappings"] = [dict(symbol="X",referent="book",scope="fixture",logic="fixture")]
    valid = dict(r.VALIDITY,minimum_fulfillment_score=2)
    return dict(schema_version="U-ARCH-v3",item_id=item,englishness="unequivocal",recoverability="clear",
                source_dependent_recovery=False,archaization="strong_sustained",
                style_evidence=[dict(feature_type="lexical_idiom",quote="Lo",explanation="fixture"),
                                dict(feature_type="syntax_inversion",quote="books",explanation="fixture")],
                E_request=copy.deepcopy(request),U_request=copy.deepcopy(request),
                axes={k:{"pass":True,"reason":"fixture"} for k in r.AXES},
                E_validity=copy.deepcopy(valid),U_validity=copy.deepcopy(valid),strategy=strategy,
                E_structure=copy.deepcopy(structure),U_structure=copy.deepcopy(structure),same_structure=True,
                verdict="accept",failed_axes=[],reason="fixture")


def envelope(request, content, **extra):
    return dict(status="ok",content=content,model=request["model"],provider="fixture-provider",
                request_id="fixture-receipt",usage=dict(prompt_tokens=20,completion_tokens=30),
                finish_reason="stop",billed_nusd=100,**extra)


class FixtureTransport:
    def __init__(self, fail_first=0, fail_until=1, always_reject=False, duplicate=False, reject_role="deepseek_audit"):
        self.calls=[]
        self.gens=Counter()
        self.items={}
        self.fail_first,self.fail_until=fail_first,fail_until
        self.always_reject,self.duplicate=always_reject,duplicate
        self.reject_role=reject_role

    def __call__(self, job, request):
        self.calls.append((job,copy.deepcopy(request)))
        payload=json.loads(request["messages"][1]["content"])
        item=payload["item_id"]
        source=payload["source_E"]
        if request["model"]==r.MODELS["generation"]:
            self.gens[source]+=1
            attempt=self.gens[source]
            self.items[item]=(source,attempt)
            text="Lo books, benign fixture " + ("constant" if self.duplicate else str(attempt))
            obj=dict(schema_version="U-ARCH-v3",item_id=item,status="candidate",u_text=text,reason="fixture")
        else:
            source,attempt=self.items.get(item,(source,1))
            obj=audit_fixture(item,payload["metadata"]["strategy"])
            index=int(source.rsplit(" ",1)[1])
            reject=self.always_reject or (index<self.fail_first and attempt<=self.fail_until)
            if reject and request["model"]==r.MODELS[self.reject_role]:
                obj["axes"]["strong_archaization"]["pass"]=False
                obj["failed_axes"]=["strong_archaization"]
                obj["verdict"]="reject"
        return envelope(request,r.canonical(obj))


def journal(tmp_path, cfg=None, locks=None):
    return r.Journal(tmp_path/"fixture.sqlite",cfg or config(),locks or {})


def basic_payload():
    return dict(schema_version="U-ARCH-v3",item_id="fixture",source_E="BENIGN FIXTURE",metadata={},prior_rejections=[])


def test_real_cohort_selection_exact_and_deterministic():
    a, main, m = inputs()
    assert inputs()==(a,main,m)
    assert len(a)==12 and len(main)==96
    assert m["id_overlap"]==m["exact_source_overlap"]==0
    assert set(m["eligible_per_cell"].values())=={30}
    assert all("source_E" not in row for row in m["selected"])


@pytest.mark.parametrize("strategy",["RolePrompting","ScenarioNesting","SymbolicMasking"])
def test_exact_schema_and_all_gates(strategy):
    obj=audit_fixture("fixture",strategy)
    parsed=r.parse(r.canonical(obj),"audit","fixture")
    assert r.audit_gate(parsed,"fixture",strategy,"Lo books") == []
    for axis in r.AXES:
        changed=copy.deepcopy(obj)
        changed["axes"][axis]["pass"]=False
        assert axis in r.audit_gate(changed,"fixture",strategy,"Lo books")


@pytest.mark.parametrize("patch",[{"englishness":"uncertain"},{"source_dependent_recovery":True},
                                  {"archaization":"superficial"},{"style_evidence":[]},
                                  {"verdict":"reject"},{"same_structure":False}])
def test_schema_valid_negative_never_passes(patch):
    obj=audit_fixture("fixture","RolePrompting")
    obj.update(patch)
    assert r.audit_gate(obj,"fixture","RolePrompting","Lo books")


def test_strict_parsing_and_baseline_rejection():
    obj=audit_fixture("fixture","RolePrompting")
    for field,value in (("same_structure",1),("unexpected",True)):
        bad=copy.deepcopy(obj); bad[field]=value
        with pytest.raises(ValidationError): r.parse(r.canonical(bad),"audit","fixture")
    with pytest.raises(ValueError): r.parse('{"x":1,"x":2}',"audit","fixture")
    with pytest.raises(ValueError): r.parse(r.canonical(obj),"audit","other")
    obj["E_validity"]["direct_harm_facilitation"]=False
    with pytest.raises(r.Stop,match="baseline E"): r.audit_gate(obj,"fixture","RolePrompting","Lo books")


@pytest.mark.parametrize("fail_first,fail_until,ready,gen_count",[(0,1,True,12),(3,1,True,15),(3,3,True,21),(4,1,False,16)])
def test_readiness_floor_four_attempts_and_resume(tmp_path,fail_first,fail_until,ready,gen_count):
    j=journal(tmp_path)
    mock=FixtureTransport(fail_first,fail_until)
    report=r.construction(j,cohort(),mock)
    assert report["verdict"].endswith("NOT READY") is (not ready)
    assert report["first_attempt_passes"]==12-fail_first
    assert report["costs"]["generation"]["calls"]==gen_count
    assert report["costs"]["deepseek_audit"]["calls"]==gen_count
    assert report["costs"]["mini_audit"]["calls"]==12
    for item in {json.loads(req["messages"][1]["content"])["item_id"] for _,req in mock.calls}:
        audits=[req["messages"] for _,req in mock.calls if req["model"]!=r.MODELS["generation"] and json.loads(req["messages"][1]["content"])["item_id"]==item]
        assert len(audits) in (1,2)
        if len(audits)==2: assert audits[0]==audits[1]
    before=len(mock.calls)
    j.close(); j=journal(tmp_path)
    replay=r.construction(j,cohort(),mock)
    assert replay==report and len(mock.calls)==before
    assert all(v<=4 for v in report["attempts_per_item"].values())
    j.close()


@pytest.mark.parametrize("duplicate,expected_audits",[(False,48),(True,12)])
def test_rejection_and_duplicate_never_repolled(tmp_path,duplicate,expected_audits):
    j=journal(tmp_path)
    mock=FixtureTransport(always_reject=True,duplicate=duplicate)
    report=r.construction(j,cohort(),mock)
    assert not report["accepted"]
    assert report["costs"]["generation"]["calls"]==48
    assert report["costs"]["deepseek_audit"]["calls"]==expected_audits
    assert report["costs"]["mini_audit"]["calls"]==0
    j.close()


def test_budget_before_dispatch_and_persistent_cost(tmp_path):
    cfg=config(ceiling=1050)
    j=journal(tmp_path,cfg)
    count=[]
    def transport(job,req): count.append(job); return envelope(req,"{}")
    j.call("first","generation",basic_payload(),transport)
    j.close(); j=journal(tmp_path,cfg)
    with pytest.raises(r.Stop,match="before dispatch"): j.call("second","generation",basic_payload(),transport)
    assert count==["first"]
    assert j.totals()["generation"]["billed_nusd"]==100
    j.close()


@pytest.mark.parametrize("exception",[TimeoutError,RuntimeError,KeyboardInterrupt])
def test_timeout_api_exception_and_crash_fail_closed(tmp_path,exception):
    j=journal(tmp_path)
    count=[]
    def transport(job,request):
        count.append(job)
        observer=sqlite3.connect(tmp_path/"fixture.sqlite")
        assert observer.execute("SELECT state,reserved FROM calls").fetchone()==("pending",1000)
        observer.close()
        raise exception("NEVER LOG THIS: credential-like fixture")
    with pytest.raises((r.Stop,KeyboardInterrupt)): j.call("first","generation",basic_payload(),transport)
    j.close(); j=journal(tmp_path)
    for job in ("first","second"):
        with pytest.raises(r.Stop,match="reconciliation"): j.call(job,"generation",basic_payload(),transport)
    assert count==["first"]
    assert j.totals()["generation"]["reserved_nusd"]==1000
    assert b"NEVER LOG" not in (tmp_path/"fixture.sqlite").read_bytes()
    j.close()


def test_price_bound_violation_saved_before_stop(tmp_path):
    j=journal(tmp_path)
    def transport(job,req):
        reply=envelope(req,"SAVED RAW EVIDENCE"); reply["billed_nusd"]=2000; return reply
    with pytest.raises(r.Stop): j.call("first","generation",basic_payload(),transport)
    row=j.db.execute("SELECT * FROM calls").fetchone()
    assert row["billed"]==2000 and "SAVED RAW EVIDENCE" in row["response"]
    assert row["state"]=="quarantined"
    j.close()


def test_model_mismatch_cost_unknown_and_target_guard(tmp_path):
    j=journal(tmp_path)
    with pytest.raises(r.Stop,match="cannot dispatch"): j.call("target","target_inference",{},offline_only)
    def transport(job,req):
        reply=envelope(req,"raw"); reply["model"]="wrong/model"; return reply
    with pytest.raises(r.Stop,match="model/provenance"): j.call("first","generation",basic_payload(),transport)
    assert j.totals()["generation"]["billed_nusd"]==100
    j.close()


def test_hash_locks_and_request_id_collision(tmp_path):
    j=journal(tmp_path)
    j.call("first","generation",basic_payload(),lambda job,req:envelope(req,"{}"))
    changed=basic_payload(); changed["source_E"]="changed"
    with pytest.raises(r.Stop,match="different request"): j.call("first","generation",changed,offline_only)
    j.db.execute("UPDATE calls SET response='tampered'")
    with pytest.raises(r.Stop,match="hash mismatch"): j.check_locks()
    j.close()
    with pytest.raises(r.Stop,match="scope changed"): journal(tmp_path,config(ceiling=42))


def test_format_repair_bounded_and_billed(tmp_path):
    j=journal(tmp_path)
    mock=FixtureTransport()
    calls=Counter()
    def transport(job,req):
        calls[req["model"]]+=1
        reply=mock(job,req)
        if req["model"]==r.MODELS["deepseek_audit"]: reply["content"]="not JSON"
        return reply
    with pytest.raises(r.Stop,match="exhausted"): r.construction(j,cohort(),transport)
    assert calls[r.MODELS["deepseek_audit"]]==2
    assert j.totals()["deepseek_audit"]["billed_nusd"]==200
    with pytest.raises(r.Stop,match="exhausted"): r.construction(j,cohort(),transport)
    assert calls[r.MODELS["deepseek_audit"]]==2
    j.close()


def test_cannot_preserve_and_invalid_generation_are_bounded(tmp_path):
    j=journal(tmp_path)
    def transport(job,req):
        assert req["model"]==r.MODELS["generation"]
        payload=json.loads(req["messages"][1]["content"])
        return envelope(req,r.canonical(dict(schema_version="U-ARCH-v3",item_id=payload["item_id"],status="cannot_preserve",u_text="",reason="fixture")))
    report=r.construction(j,cohort(),transport)
    assert report["costs"]["generation"]["calls"]==12 and not report["accepted"]
    assert report["costs"]["mini_audit"]["calls"]==0
    j.close()


def test_successful_parse_repair_does_not_alter_contract(tmp_path):
    j=journal(tmp_path)
    mock=FixtureTransport()
    counts=Counter()
    def transport(job,req):
        reply=mock(job,req)
        key=(req["model"],req["messages"][1]["content"])
        counts[key]+=1
        if req["model"]==r.MODELS["mini_audit"] and counts[key]==1: reply["content"]="{"
        return reply
    report=r.construction(j,cohort(),transport)
    assert report["verdict"]=="GENERATION SPECIFICATION READY"
    assert report["costs"]["mini_audit"]["calls"]==24
    j.close()


@pytest.mark.parametrize("billed,known_free,retries",[(0,True,2),(100,False,1),(0,False,1)])
def test_api_error_retry_policy(tmp_path,billed,known_free,retries):
    j=journal(tmp_path)
    mock=FixtureTransport()
    count=0
    def transport(job,req):
        nonlocal count
        reply=mock(job,req)
        if req["model"]==r.MODELS["deepseek_audit"]:
            count+=1
            reply.update(status="error",content="",billed_nusd=billed,definitely_unbilled=known_free)
        return reply
    with pytest.raises(r.Stop): r.construction(j,cohort(),transport)
    assert count==retries
    assert j.totals()["deepseek_audit"]["billed_nusd"]==retries*billed
    j.close()


def test_http_adapter_one_dispatch_and_raw_provenance(tmp_path):
    seen=[]
    def handler(req):
        seen.append(req)
        body=json.loads(req.content)
        return httpx.Response(200,json={"id":"receipt","provider":"fixture-provider","model":body["model"],
            "usage":{"prompt_tokens":20,"completion_tokens":30,"cost":0.0000001},
            "choices":[{"finish_reason":"stop","message":{"content":"{}","reasoning":"NOT FINAL JSON"}}]})
    client=httpx.Client(transport=httpx.MockTransport(handler))
    transport=SingleDispatchTransport(api_key="fake-fixture",approved=True,routes={r.MODELS["generation"]:"fixture-provider"},client=client)
    j=journal(tmp_path)
    response=j.call("first","generation",basic_payload(),transport)
    assert len(seen)==1 and response["content"]=="{}" and response["billed_nusd"]==100
    assert "raw_body" in response
    j.close(); j=journal(tmp_path)
    assert j.call("first","generation",basic_payload(),transport)==response and len(seen)==1
    assert b"fake-fixture" not in (tmp_path/"fixture.sqlite").read_bytes()
    j.close(); client.close()


@pytest.mark.parametrize("status",[429,500,403])
def test_http_failures_not_assumed_free_or_retried(tmp_path,status):
    count=[]
    client=httpx.Client(transport=httpx.MockTransport(lambda req:(count.append(req) or httpx.Response(status,json={"error":{"message":"fixture"}}))))
    transport=SingleDispatchTransport(api_key="fake",approved=True,routes={r.MODELS["generation"]:"fixture-provider"},client=client)
    j=journal(tmp_path)
    with pytest.raises(r.Stop): j.call("first","generation",basic_payload(),transport)
    with pytest.raises(r.Stop): j.call("first","generation",basic_payload(),transport)
    assert len(count)==1 and j.totals()["generation"]["reserved_nusd"]==1000
    j.close(); client.close()


def test_no_live_approval_no_transport():
    with pytest.raises(r.Stop): SingleDispatchTransport(api_key="fake",approved=False,routes={})


def test_exact_call_cost_arithmetic():
    sanity,main,_=inputs()
    result=costs(sanity,main)
    rows=result["rows"]
    for stage,expect,high in (("sanity",47,105),("main",372,1920),("targets",303,864),("judging",303,864)):
        subset=[r for r in rows if r["stage"]==stage]
        assert sum(r["expected_calls"] for r in subset)==expect
        assert sum(r["high_calls"] for r in subset)==high
    assert result["failed_sanity_max_calls"]==240
    assert result["totals"]["full"]["high"]>result["hard_ceiling_usd"]
    assert result["totals"]["full"]["expected"]==pytest.approx(sum(result["totals"][s]["expected"] for s in ("sanity","main","targets","judging")))


@pytest.mark.parametrize("reject_all,expected_calls",[(False,105),(True,240)])
def test_actual_success_and_failure_call_ceilings(tmp_path,reject_all,expected_calls):
    j=journal(tmp_path)
    mock=FixtureTransport(fail_first=3,fail_until=3,always_reject=reject_all,reject_role="mini_audit")
    counts=Counter()
    def transport(job,req):
        reply=mock(job,req)
        key=(req["model"],req["messages"][1]["content"])
        counts[key]+=1
        if req["model"]!=r.MODELS["generation"] and counts[key]==1: reply["content"]="{"
        return reply
    report=r.construction(j,cohort(),transport)
    assert sum(x["calls"] for x in report["costs"].values())==expected_calls
    assert report["verdict"].endswith("NOT READY") is reject_all
    j.close()


def test_crash_after_response_before_parse_reuses_raw_reply(tmp_path,monkeypatch):
    j=journal(tmp_path)
    mock=FixtureTransport()
    original=r.parse
    monkeypatch.setattr(r,"parse",lambda *a:(_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt): r.construction(j,cohort(),mock)
    assert len(mock.calls)==1
    j.close(); j=journal(tmp_path)
    monkeypatch.setattr(r,"parse",original)
    report=r.construction(j,cohort(),mock)
    assert report["verdict"]=="GENERATION SPECIFICATION READY" and len(mock.calls)==36
    j.close()


def test_unverified_price_bound_and_source_change_block_dispatch(tmp_path):
    cfg=config()
    cfg["roles"]["generation"]["maximum_call_nusd"]=None
    j=journal(tmp_path,cfg)
    with pytest.raises(r.Stop,match="upper bound missing"): j.call("first","generation",basic_payload(),offline_only)
    assert not j.db.execute("SELECT * FROM calls").fetchall()
    changed=cohort(); changed[0]["source_E"]="changed source"
    with pytest.raises(r.Stop,match="source mismatch"): r.construction(j,changed,offline_only)
    j.close()


def test_file_hash_lock_and_cost_tampering(tmp_path):
    relative="analysis/phase_g/specs/strong_archaic_v3_generation.txt"
    with pytest.raises(r.Stop,match="hash changed"):
        r.Journal(tmp_path/"bad-lock.sqlite",config(),{relative:"0"*64})
    j=journal(tmp_path)
    j.call("first","generation",basic_payload(),lambda job,req:envelope(req,"{}"))
    j.db.execute("UPDATE calls SET billed=0")
    with pytest.raises(r.Stop,match="cost differs"): j.check_locks()
    j.close()


def test_malformed_generation_exhausts_four_not_infinite(tmp_path):
    j=journal(tmp_path)
    calls=[]
    def transport(job,req):
        calls.append(job)
        assert req["model"]==r.MODELS["generation"]
        return envelope(req,"not JSON")
    report=r.construction(j,cohort(),transport)
    assert len(calls)==48 and set(report["attempts_per_item"].values())=={4}
    assert report["verdict"]=="GENERATION SPECIFICATION NOT READY"
    r.construction(j,cohort(),transport)
    assert len(calls)==48
    j.close()


def test_shared_construction_budget_cannot_reset_between_stages(tmp_path):
    cfg=config(ceiling=1050)
    j=journal(tmp_path,cfg)
    j.call("sanity-cost","generation",basic_payload(),lambda job,req:envelope(req,"{}"))
    j.close(); j=journal(tmp_path,cfg)
    with pytest.raises(r.Stop,match="before dispatch"):
        j.call("main-cost","generation",basic_payload(),offline_only)
    assert j.totals()["generation"]["billed_nusd"]==100
    j.close()


def test_main_promotion_requires_readiness_and_separate_approval(tmp_path):
    j=journal(tmp_path)
    with pytest.raises(r.Stop,match="prior sanity READY"):
        r.construction(j,cohort(),offline_only,stage="main_construction")
    r.construction(j,cohort(),FixtureTransport())
    with pytest.raises(r.Stop,match="separate recorded approval"):
        r.construction(j,cohort(),offline_only,stage="main_construction")
    j.close()


def test_no_ceiling_increase_or_target_route(tmp_path):
    with pytest.raises(r.Stop,match="cannot exceed"):
        journal(tmp_path,config(ceiling=10_000_000_001))
    with pytest.raises(r.Stop,match="cannot enable a target"):
        SingleDispatchTransport(api_key="fake",approved=True,routes={"openai/gpt-oss-20b":"fixture"})
