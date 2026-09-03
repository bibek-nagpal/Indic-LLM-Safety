"""API compatibility and N12-only authority; no network, fixed benign fixtures."""
import copy
import json
import socket

import httpx
import pytest

from analysis.phase_g import strong_archaic_runtime as r
from analysis.phase_g import sanity_compat as s
from analysis.phase_g.strong_archaic_transport import SingleDispatchTransport
from test_strong_archaic_preflight import (config,cohort,journal,FixtureTransport,
                                         envelope,basic_payload,offline_only,audit_fixture)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket,"connect",offline_only)
    monkeypatch.setattr(socket,"create_connection",offline_only)
    monkeypatch.setattr(socket,"getaddrinfo",offline_only)


def reporting_journal(tmp_path):
    cfg=config()
    for settings in cfg["roles"].values():
        settings.update(expected_rates_usd_per_million=[.1,.2],reservation_rates_usd_per_million=[.1,.2])
    return journal(tmp_path,cfg)


def test_real_preflight_sole_parameter_change_and_all_caps():
    plan,report=s.preflight()
    previous=s.read(s.OLD/"EXECUTION_PLAN.json")
    expected=copy.deepcopy(previous["roles"]); del expected["mini_audit"]["temperature"]
    assert plan["roles"]==expected
    assert plan["authorized_stages"]==["sanity"]
    assert plan["hard_ceiling_nusd"]==5_500_000_000
    assert plan["stage_budgets_nusd"]["sanity"]==650_000_000
    assert report["status"]=="PASS" and report["sanity_n"]==12
    assert report["id_overlap"]==report["exact_source_overlap"]==0
    assert report["frozen_artifacts"]["core_manifest_files"]==82
    assert "temperature" not in r.fixed_parameters(plan["roles"]["mini_audit"])
    assert r.fixed_parameters(plan["roles"]["generation"])["temperature"]==.4
    assert r.fixed_parameters(plan["roles"]["deepseek_audit"])["temperature"]==0


def test_mini_wire_request_omits_temperature_entirely(tmp_path):
    seen=[]
    def handler(req):
        body=json.loads(req.content); seen.append(body)
        assert "temperature" not in body
        assert body["model"]=="openai/gpt-5-mini" and body["max_tokens"]==4096
        payload=json.loads(body["messages"][1]["content"])
        return httpx.Response(200,json=dict(id="fixture",provider="fixture-provider",model=body["model"],
            usage=dict(prompt_tokens=20,completion_tokens=30,cost=.0000001),
            choices=[dict(finish_reason="stop",message=dict(content=r.canonical(audit_fixture(payload["item_id"],"RolePrompting"))))]))
    client=httpx.Client(transport=httpx.MockTransport(handler))
    adapter=SingleDispatchTransport(api_key="fake",approved=True,routes={r.MODELS["mini_audit"]:"fixture-provider"},client=client)
    j=journal(tmp_path)
    j.call("mini","mini_audit",basic_payload(),adapter)
    j.close(); j=journal(tmp_path)
    j.call("mini","mini_audit",basic_payload(),offline_only)
    assert len(seen)==1
    j.close(); client.close()


@pytest.mark.parametrize("value",[0,None,1])
def test_mini_reintroduced_temperature_rejected_before_dispatch(tmp_path,value):
    cfg=config(); cfg["roles"]["mini_audit"]["temperature"]=value
    j=journal(tmp_path,cfg)
    with pytest.raises(r.Stop,match="sampling settings"):
        j.call("bad","mini_audit",basic_payload(),offline_only)
    assert j.totals()["mini_audit"]["calls"]==0
    j.close()


@pytest.mark.parametrize("stage",["main_construction","target_inference","judging"])
def test_sanity_authority_cannot_pay_for_later_stages(tmp_path,stage):
    cfg=config(); cfg["authorized_stages"]=["sanity"]
    j=journal(tmp_path,cfg)
    settings=cfg["roles"]["generation"]
    request=dict(r.fixed_parameters(settings),messages=[])
    with pytest.raises(r.Stop,match="not authorized"):
        j._dispatch_request("no", "generation",stage,request,offline_only)
    j.close()


def test_complete_summary_dual_acceptance_costs_and_resume(tmp_path):
    j=reporting_journal(tmp_path); transport=FixtureTransport(fail_first=3)
    completed=r.construction(j,cohort(),transport)
    report=s.summarize(j,cohort(),completed)
    assert report["pairs_dual_certified"]==12 and report["first_attempt_dual_passes"]==9
    assert report["sanity_result"]=="GENERATION SPECIFICATION READY"
    assert report["rejections_by_axis"]["deepseek_audit"]=={"strong_archaization":3}
    assert report["rejections_by_axis"]["mini_audit"]=={}
    assert report["role_accounting"]["generation"]["calls"]==15
    assert report["role_accounting"]["mini_audit"]["calls"]==12
    assert report["total_reported_cost_usd"]==pytest.approx(42*100/1e9)
    assert report["outstanding_reservations_usd"]==0 and not report["protocol_violations"]
    r.construction(j,cohort(),offline_only)
    assert s.summarize(j,cohort(),completed)==report
    j.close()


def test_incomplete_summary_does_not_count_unknown_reservation_as_spend(tmp_path):
    j=reporting_journal(tmp_path)
    def timeout(job,req): raise TimeoutError("do not log")
    with pytest.raises(r.Stop): r.construction(j,cohort(),timeout)
    report=s.summarize(j,cohort(),stop_reason="unknown delivery")
    assert report["sanity_result"]=="INCOMPLETE DUE TO EXECUTION OR BUDGET FAILURE"
    assert report["total_reported_cost_usd"]==0
    assert report["outstanding_reservations_usd"]==.000001
    assert report["unknown_billing_calls"]==1 and report["pairs_dual_certified"]==0
    assert sorted(report["attempts_per_pair"].values())==[0]*11+[1]
    assert report["failures"][0]["reported_cost_usd"] is None
    j.close()


def test_failed_readiness_stays_failed_even_with_twelve_certified(tmp_path):
    j=reporting_journal(tmp_path)
    completed=r.construction(j,cohort(),FixtureTransport(fail_first=4))
    report=s.summarize(j,cohort(),completed)
    assert report["pairs_dual_certified"]==12 and report["first_attempt_dual_passes"]==8
    assert report["sanity_result"]=="GENERATION SPECIFICATION NOT READY"
    j.close()


def test_changed_or_uncommitted_preflight_cannot_load_credentials(monkeypatch):
    monkeypatch.setattr(s,"git",lambda *args:b"not the committed preflight")
    with pytest.raises(r.Stop,match="must match prospective"):
        s.verify_commit("0"*40,s.make_plan())


def test_no_hidden_model_or_endpoint_substitution(monkeypatch):
    original=s.read
    def changed(path):
        data=original(path)
        if path.name=="PROVIDER_METADATA.json":
            entry=data["responses"][r.MODELS["mini_audit"]]
            raw=json.loads(entry["response_text"])
            raw["data"]["endpoints"]=[x for x in raw["data"]["endpoints"] if x["tag"]!="openai/flex"]
            entry["response_text"]=r.canonical(raw); entry["response_sha256"]=r.digest(entry["response_text"])
        return data
    monkeypatch.setattr(s,"read",changed)
    with pytest.raises(r.Stop,match="endpoint unavailable"):
        s.make_plan()
