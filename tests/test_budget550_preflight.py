"""Financial amendment fault injection: benign fixtures only, no live calls."""
import copy
import json
import socket

import httpx
import pytest

from analysis.phase_g import budget550_preflight as b
from analysis.phase_g import strong_archaic_runtime as r
from analysis.phase_g.strong_archaic_transport import SingleDispatchTransport
from test_strong_archaic_preflight import (config, cohort, journal, envelope,
    basic_payload, FixtureTransport, audit_fixture, offline_only)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket,"connect",offline_only)
    monkeypatch.setattr(socket,"create_connection",offline_only)
    monkeypatch.setattr(socket,"getaddrinfo",offline_only)


@pytest.fixture(scope="module")
def prepared():
    return b.build()


def test_live_quotes_cohort_and_sampling_blocker(prepared):
    plan=prepared["EXECUTION_PLAN.json"]
    assert plan["hard_ceiling_nusd"]==5_500_000_000==sum(plan["stage_budgets_nusd"].values())
    assert len(plan["inference_blockers"])==1 and "temperature" in plan["inference_blockers"][0]
    assert plan["roles"]["mini_audit"]["temperature"]==0  # NOT silently removed
    assert plan["roles"]["mini_audit"]["canonical_model"]=="openai/gpt-5-mini-2025-08-07"
    assert prepared["PREFLIGHT.json"]["frozen_files_checked"]==82
    assert prepared["PREFLIGHT.json"]["cohort_unchanged"]
    for role,settings in plan["roles"].items():
        assert b.reservation(settings["reservation_proof"])==settings["maximum_call_nusd"]
        assert settings["request_parameters"]["provider"]["allow_fallbacks"] is False
        assert settings["request_parameters"]["provider"]["only"]==[settings["endpoint_tag"]]
        assert settings["maximum_call_nusd"]<min(plan["stage_budgets_nusd"][s] for s in settings["allowed_stages"])


def test_new_costs_reconcile_without_inherited_prices(prepared):
    cost=prepared["COST_PREFLIGHT.json"]
    assert cost["expected_call_count"]==1011
    assert cost["totals"]["full"]["expected_cost_usd"]==pytest.approx(1.4398904811)
    assert cost["totals"]["full"]["standard_tier_expected_usd"]==pytest.approx(2.6358619811)
    assert cost["totals"]["full"]["hard_authorized_usd"]==5.5
    assert cost["full_protocol_output_caps_only_flex_usd"]>5.5
    assert not cost["full_completion_guaranteed_under_550"]
    for stage in r.STAGES:
        rows=[x for x in cost["rows"] if x["stage"]==stage]
        assert cost["totals"][stage]["expected_cost_usd"]==pytest.approx(sum(x["expected_input_cost_usd"]+x["expected_output_cost_usd"] for x in rows))


@pytest.mark.parametrize("kind",["cap_above","missing_stage","negative_stage","oversubscribed"])
def test_invalid_global_or_stage_budget_fails_closed(tmp_path,kind):
    cfg=config()
    if kind=="cap_above": cfg["hard_ceiling_nusd"]=5_500_000_001
    elif kind=="missing_stage": del cfg["stage_budgets_nusd"]["judging"]
    elif kind=="negative_stage": cfg["stage_budgets_nusd"]["judging"]=-1
    else: cfg["stage_budgets_nusd"]["judging"]=1
    with pytest.raises(r.Stop): journal(tmp_path,cfg)


def test_exact_550_cumulative_four_stage_boundary_and_restart(tmp_path):
    cfg=config(ceiling=5_500_000_000)
    cfg["stage_budgets_nusd"]=b.STAGE_CAPS.copy()
    for stage,cap in b.STAGE_CAPS.items():
        role="fixture_"+stage
        settings=copy.deepcopy(cfg["roles"]["generation"])
        settings.update(allowed_stages=[stage],maximum_call_nusd=cap)
        cfg["roles"][role]=settings
    seen=[]
    for stage,cap in b.STAGE_CAPS.items():
        j=journal(tmp_path,cfg)
        role="fixture_"+stage
        settings=cfg["roles"][role]
        req=dict(settings["request_parameters"],model=settings["model"],temperature=.4,max_tokens=4096,messages=[])
        def mock(job,request):
            seen.append(job)
            reply=envelope(request,"{}"); reply["billed_nusd"]=cap
            return reply
        j._dispatch_request(stage,role,stage,req,mock)
        assert j._dispatch_request(stage,role,stage,req,offline_only)["billed_nusd"]==cap
        j.close()
    j=journal(tmp_path,cfg)
    assert sum(x["billed_nusd"] for x in j.stage_totals().values())==5_500_000_000
    assert sum(x["billed_nusd"] for x in j.totals().values())==5_500_000_000
    with pytest.raises(r.Stop,match="hard budget stop before dispatch"):
        j.call("would_exceed","generation",basic_payload(),offline_only)
    assert len(seen)==4
    j.close()


def test_stage_reservation_protects_future_funds(tmp_path):
    cfg=config(ceiling=5_500_000_000)
    cfg["stage_budgets_nusd"]=b.STAGE_CAPS.copy()
    cfg["roles"]["generation"]["maximum_call_nusd"]=400_000_000
    j=journal(tmp_path,cfg)
    def mock(job,request):
        reply=envelope(request,"{}"); reply["billed_nusd"]=300_000_000
        return reply
    j.call("one","generation",basic_payload(),mock)
    with pytest.raises(r.Stop,match="stage budget stop before dispatch"):
        j.call("two","generation",basic_payload(),offline_only)
    assert j.stage_totals()["sanity"]["calls"]==1
    assert j.stage_totals()["target_inference"]["calls"]==0
    with pytest.raises(r.Stop,match="another stage"):
        j.call("divert","generation",basic_payload(),offline_only,stage="judging")
    j.close()


def test_canonical_journal_and_mutable_config_cannot_reset_cap(tmp_path):
    cfg=config()
    cfg["journal_path"]="analysis/phase_g/u_arch_v3_private/phase_g_budget550.sqlite"
    with pytest.raises(r.Stop,match="canonical cumulative"):
        journal(tmp_path,cfg)
    cfg=config()
    j=journal(tmp_path,cfg)
    cfg["hard_ceiling_nusd"]+=1
    with pytest.raises(r.Stop,match="scope changed"):
        j.call("mutation","generation",basic_payload(),offline_only)
    j.close()


def test_live_blocker_prevents_every_call(tmp_path):
    cfg=config(); cfg["inference_blockers"]=["unsupported temperature"]
    j=journal(tmp_path,cfg)
    with pytest.raises(r.Stop,match="preflight blockers"):
        j.call("blocked","generation",basic_payload(),offline_only)
    assert j.stage_totals()["sanity"]["calls"]==0
    j.close()


def test_offline_plan_and_omitted_hash_locks_block_dispatch(tmp_path):
    cfg=config(); cfg["live_enabled"]=False
    j=journal(tmp_path,cfg)
    with pytest.raises(r.Stop,match="offline-only"):
        j.call("blocked","generation",basic_payload(),offline_only)
    assert j.stage_totals()["sanity"]["calls"]==0
    j.close()
    cfg=config(); cfg["locks"]={"expected":"not-a-real-hash"}
    with pytest.raises(r.Stop,match="entire frozen lock set"):
        journal(tmp_path,cfg)


def test_reservation_price_proof_mismatch_before_dispatch(tmp_path):
    cfg=config(); settings=cfg["roles"]["generation"]
    settings["reservation_proof"]=dict(input_token_bound=10,output_token_bound=10,
        input_rate_per_token="0.00000005",output_rate_per_token="0.00000005")
    settings["billed_output_token_bound"]=10
    # Bound is exactly1000 but pinned price disagrees.
    settings["request_parameters"]["provider"]["max_price"]={"prompt":.05,"completion":.06,"request":0}
    j=journal(tmp_path,cfg)
    with pytest.raises(r.Stop,match="price ceiling mismatch"):
        j.call("badquote","generation",basic_payload(),offline_only)
    assert j.stage_totals()["sanity"]["calls"]==0
    j.close()


def test_two_controllers_see_pending_reservation_before_network(tmp_path):
    j=journal(tmp_path); other=journal(tmp_path)
    def mock(job,request):
        with pytest.raises(r.Stop,match="reconciliation"):
            other.call("same","generation",basic_payload(),offline_only)
        with pytest.raises(r.Stop,match="reconciliation"):
            other.call("different","generation",basic_payload(),offline_only)
        return envelope(request,"{}")
    j.call("same","generation",basic_payload(),mock)
    other.call("same","generation",basic_payload(),offline_only)
    assert other.stage_totals()["sanity"]["calls"]==1
    j.close(); other.close()


def test_local_json_wrapper_recovery_costs_no_api_retry(tmp_path):
    j=journal(tmp_path); fixture=FixtureTransport()
    def mock(job,request):
        reply=fixture(job,request)
        reply["content"]="\ufeff  ```json\n"+reply["content"]+"\n```  "
        return reply
    report=r.construction(j,cohort(),mock)
    assert len(fixture.calls)==36 and report["first_attempt_passes"]==12
    with pytest.raises(TypeError): r.parse(None,"audit","fixture")
    j.close()


@pytest.mark.parametrize("role",["generation","deepseek_audit"])
@pytest.mark.parametrize("status",[400,401,403,404,422])
def test_deterministic_errors_never_retried_even_proven_free(tmp_path,role,status):
    j=journal(tmp_path); fixture=FixtureTransport(); seen=[]
    def mock(job,request):
        reply=fixture(job,request)
        if request["model"]==r.MODELS[role]:
            seen.append(job)
            reply.update(status="error",http_status=status,billed_nusd=0,definitely_unbilled=True)
        return reply
    with pytest.raises(r.Stop,match="deterministic"):
        r.construction(j,cohort(),mock)
    with pytest.raises(r.Stop,match="deterministic"):
        r.construction(j,cohort(),mock)
    assert len(seen)==1
    j.close()


@pytest.mark.parametrize("tier",["flex","default",None])
def test_flex_display_name_and_unexpected_tier_accounting(tmp_path,tier):
    cfg=config(); settings=cfg["roles"]["generation"]
    provider=settings["request_parameters"]["provider"]
    provider.update(order=["google-ai-studio/flex"],only=["google-ai-studio/flex"])
    settings["request_parameters"]["service_tier"]="flex"
    seen=[]
    def handler(req):
        seen.append(req)
        return httpx.Response(200,json=dict(id="receipt",provider="Google AI Studio",service_tier=tier,
            model=r.MODELS["generation"],usage=dict(prompt_tokens=20,completion_tokens=30,cost=.0000001),
            choices=[dict(finish_reason="stop",message=dict(content="{}"))]))
    client=httpx.Client(transport=httpx.MockTransport(handler))
    transport=SingleDispatchTransport(api_key="fake",approved=True,routes={r.MODELS["generation"]:"google-ai-studio/flex"},
        provider_names={r.MODELS["generation"]:"Google AI Studio"},client=client)
    j=journal(tmp_path,cfg)
    if tier=="flex":
        assert j.call("one","generation",basic_payload(),transport)["service_tier"]=="flex"
    else:
        with pytest.raises(r.Stop): j.call("one","generation",basic_payload(),transport)
        with pytest.raises(r.Stop): j.call("again","generation",basic_payload(),transport)
    assert len(seen)==1 and j.totals()["generation"]["billed_nusd"]==100
    j.close(); client.close()


def test_primary_rejection_missing_secondary_is_not_agreement(tmp_path):
    j=journal(tmp_path); fixture=FixtureTransport(fail_first=3)
    report=r.construction(j,cohort(),fixture)
    skipped=[json.loads(x[0]) for x in j.db.execute("SELECT payload FROM events") if "not_a_mini_verdict" in x[0]]
    assert len(skipped)==3 and all(x["not_a_mini_verdict"] for x in skipped)
    assert len(report["accepted"])==12
    for accepted in report["accepted"].values():
        for role in ("deepseek_audit","mini_audit"):
            verdict=j.db.execute("SELECT payload FROM events WHERE id=?",(r.identifier(accepted["item_id"],role,"verdict"),)).fetchone()
            assert json.loads(verdict[0])["failed"]==[]
    j.close()
