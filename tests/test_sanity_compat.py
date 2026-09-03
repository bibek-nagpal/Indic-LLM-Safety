"""API compatibility and N12-only authority; no network, fixed benign fixtures."""
import copy
import json
import socket
import subprocess

import httpx
import pytest

from jsonschema import ValidationError

from analysis.phase_g import strong_archaic_runtime as r
from analysis.phase_g import sanity_compat as s
from analysis.phase_g import migrate_journal_scope as m
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
    expected["mini_audit"]["max_tokens"]=r.MAX_TOKENS["mini_audit"]
    assert plan["roles"]==expected
    assert plan["roles"]["mini_audit"]["maximum_call_nusd"]==previous["roles"]["mini_audit"]["maximum_call_nusd"]
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
        assert body["model"]=="openai/gpt-5-mini" and body["max_tokens"]==r.MAX_TOKENS["mini_audit"]
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
    monkeypatch.setattr(s,"git",lambda *args,**kwargs:b"not the committed preflight")
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


# --- Stage 1 committed-artifact verifier: real Git repositories, real commits ---
# Regression cover for the false failure in which a checkout that legitimately
# re-encoded line endings was reported as a modified frozen artifact.


def _git(root,*args,stdin=None):
    return subprocess.run(["git",*args],cwd=root,capture_output=True,check=True,input=stdin).stdout


@pytest.fixture
def committed_repo(tmp_path,monkeypatch):
    """A real repository whose checkout of a real commit carries CRLF endings."""
    root=tmp_path/"repo"; out=root/"out"; out.mkdir(parents=True)
    _git(tmp_path,"init","-q","-b","main","repo")
    for key,value in (("user.email","t@example.invalid"),("user.name","test"),("core.autocrlf","true")):
        _git(root,"config",key,value)
    (root/".gitignore").write_bytes(b"bank.jsonl\n")
    (root/".gitattributes").write_bytes(b"frozen.csv text eol=crlf\nout/*.json text eol=lf\ncode.py text eol=lf\n")
    (root/"frozen.csv").write_bytes(b"pair_id,rank\r\na,1\r\nb,2\r\n")
    (root/"code.py").write_bytes(b"VALUE = 1\n")
    (root/"bank.jsonl").write_bytes(b'{"pair_id": "x"}\n')
    plan={"authorized_stages":["sanity"],
          "locks":{name:r.file_hash(root/name) for name in ("frozen.csv","code.py","bank.jsonl")}}
    (out/"EXECUTION_PLAN.json").write_bytes((json.dumps(plan,indent=2,sort_keys=True)+"\n").encode())
    (out/"PREFLIGHT.json").write_bytes(b'{"status": "PASS"}\n')
    receipt={"status":"PASS","passed":165,"total":165,"failed":0,
             "execution_plan_sha256":r.file_hash(out/"EXECUTION_PLAN.json")}
    (out/"OFFLINE_VALIDATION.json").write_bytes((json.dumps(receipt,indent=2,sort_keys=True)+"\n").encode())
    _git(root,"add","-A"); _git(root,"commit","-qm","prospective amendment")
    monkeypatch.setattr(r,"ROOT",root); monkeypatch.setattr(s,"OUT",out); monkeypatch.setattr(s,"BANK",root/"bank.jsonl")
    return root,out,_git(root,"rev-parse","HEAD").decode().strip(),plan


def test_committed_checkout_line_ending_normalisation_is_not_a_mismatch(committed_repo):
    root,_,commit,plan=committed_repo
    raw=(root/"frozen.csv").read_bytes(); blob=_git(root,"show",commit+":frozen.csv")
    assert b"\r\n" in raw and b"\r\n" not in blob and raw!=blob
    assert not _git(root,"status","--porcelain").strip()
    assert r.file_hash(root/"frozen.csv")==plan["locks"]["frozen.csv"]
    s.verify_commit(commit,plan)


def test_committed_content_modification_still_fails(committed_repo):
    root,_,commit,plan=committed_repo
    (root/"frozen.csv").write_bytes(b"pair_id,rank\r\na,1\r\nb,2\r\nc,3\r\n")
    assert not s.committed_matches(commit,"frozen.csv",root/"frozen.csv")
    with pytest.raises(r.Stop,match="prospective committed input/code hash mismatch"):
        s.verify_commit(commit,plan)


def test_committed_single_field_edit_still_fails(committed_repo):
    root,_,commit,plan=committed_repo
    (root/"code.py").write_bytes(b"VALUE = 2\n")
    assert not s.committed_matches(commit,"code.py",root/"code.py")
    with pytest.raises(r.Stop,match="prospective committed input/code hash mismatch"):
        s.verify_commit(commit,plan)


def test_frozen_hash_mismatch_still_fails(committed_repo):
    root,_,commit,plan=committed_repo
    corrupted=copy.deepcopy(plan); corrupted["locks"]["frozen.csv"]="0"*64
    with pytest.raises(r.Stop,match="prospective committed input/code hash mismatch"):
        s.verify_commit(commit,corrupted)


def test_line_ending_only_rewrite_of_frozen_bytes_still_fails_the_raw_hash_gate(committed_repo):
    """Normalisation tolerance never becomes byte-level tolerance for frozen data."""
    root,_,commit,plan=committed_repo
    path=root/"frozen.csv"; path.write_bytes(path.read_bytes().replace(b"\r\n",b"\n"))
    assert s.committed_matches(commit,"frozen.csv",path)
    assert r.file_hash(path)!=plan["locks"]["frozen.csv"]
    with pytest.raises(r.Stop,match="prospective committed input/code hash mismatch"):
        s.verify_commit(commit,plan)


def test_untracked_bank_is_hash_checked_without_a_committed_blob(committed_repo):
    root,_,commit,plan=committed_repo
    assert not _git(root,"ls-files","bank.jsonl").strip()
    (root/"bank.jsonl").write_bytes(b'{"pair_id": "tampered"}\n')
    with pytest.raises(r.Stop,match="prospective committed input/code hash mismatch"):
        s.verify_commit(commit,plan)


def test_uncommitted_receipt_edit_still_fails(committed_repo):
    root,out,commit,plan=committed_repo
    (out/"PREFLIGHT.json").write_bytes(b'{"status": "PASS", "slipped_in": true}\n')
    with pytest.raises(r.Stop,match="must match prospective"):
        s.verify_commit(commit,plan)


def test_project_repository_checkout_normalisation_is_not_a_mismatch():
    """The exact files whose CRLF checkout produced the original Stage 1 failure."""
    names=["analysis/phase_g/selection_n96.csv","configs/categories/gambling.yaml",
           "configs/categories/intoxication.yaml","configs/categories/sexual_violence.yaml",
           "configs/categories/violence.yaml"]
    normalised=0
    for name in names:
        path=r.ROOT/name; raw=path.read_bytes(); blob=s.git("show",s.PARENT+":"+name)
        assert raw.replace(b"\r\n",b"\n")==blob.replace(b"\r\n",b"\n")
        assert s.committed_matches(s.PARENT,name,path)
        normalised+=raw!=blob
    assert normalised, "no checkout re-encoding present; regression would be vacuous"


def test_project_repository_tampered_frozen_bytes_are_rejected(tmp_path):
    name="configs/categories/violence.yaml"
    original=(r.ROOT/name).read_bytes()
    tampered=tmp_path/"violence.yaml"; tampered.write_bytes(original.replace(b"category",b"cathegory",1))
    assert tampered.read_bytes()!=original
    assert not s.committed_matches(s.PARENT,name,tampered)


# --- GPT-5 Mini completion-budget truncation, 2026-09-03 sanity run -------------
# The auditor returned HTTP 200 twice with finish_reason "length" at exactly the
# 4096-token cap; reasoning consumed 2368 and 2752 of it, leaving too few visible
# tokens for the 17-axis verdict, which costs 1734 for this payload. The stored
# provider evidence is redacted into tests/fixtures (the response text embeds the
# harmful source and the U candidate, so only measurements are committed).

EVIDENCE=json.loads((r.ROOT/"tests/fixtures/phase_g_mini_truncation_2026_09_03.json").read_text(encoding="utf-8"))


def truncated_audit(item, strategy, visible_tokens):
    """A complete verdict cut mid-string exactly as the provider truncation cut it."""
    complete=r.canonical(audit_fixture(item,strategy))
    cut=complete[:max(1,int(visible_tokens*4.28))]
    while cut.count('"')%2==0 or cut.endswith("\\"):
        cut=cut[:-1]
    return cut


def truncating_envelope(request, item, strategy, reasoning, budget):
    body=truncated_audit(item,strategy,budget-reasoning)
    return dict(status="ok",content=body,model=request["model"],provider="fixture-provider",
                request_id="fixture-receipt",finish_reason="length",billed_nusd=100,
                usage=dict(prompt_tokens=4137,completion_tokens=budget,
                           completion_tokens_details=dict(reasoning_tokens=reasoning)))


class TruncatingMiniTransport(FixtureTransport):
    """Generation and DeepSeek behave normally; Mini truncates at the completion cap."""
    def __call__(self, job, request):
        if request["model"]!=r.MODELS["mini_audit"]:
            return super().__call__(job,request)
        self.calls.append((job,copy.deepcopy(request)))
        payload=json.loads(request["messages"][1]["content"])
        return truncating_envelope(request,payload["item_id"],payload["metadata"]["strategy"],
                                   2368,r.MAX_TOKENS["mini_audit"])

    def dispatched(self, role):
        return sum(request["model"]==r.MODELS[role] for _,request in self.calls)


def test_recorded_evidence_shows_budget_exhaustion_not_a_schema_or_parser_defect():
    for observed in EVIDENCE["mini_responses"]:
        assert observed["http_status"]==200 and observed["status"]=="ok"
        assert observed["finish_reason"]=="length"
        assert observed["usage"]["completion_tokens"]==EVIDENCE["diagnosis"]["configured_mini_max_tokens_at_failure"]
        assert observed["usage"]["completion_tokens_details"]["reasoning_tokens"]>0
        assert observed["axes_fully_emitted"]<observed["axes_required"]
        assert observed["ends_inside_unterminated_string"] and observed["unclosed_braces"]>0
        assert "JSONDecodeError" in observed["json_parse_error"]
    reference=EVIDENCE["complete_reference"]
    assert reference["parses"] and reference["axes"]==17 and reference["finish_reason"]=="stop"
    # every truncated attempt had less visible budget than a complete verdict costs
    for observed in EVIDENCE["mini_responses"]:
        assert observed["visible_tokens"]<reference["completion_tokens"]
    assert reference["completion_tokens"]<r.MAX_TOKENS["mini_audit"], "corrected budget must fit a full verdict"


def test_truncated_stored_content_is_rejected_by_the_parser(tmp_path):
    item=r.candidate_id("sanity",cohort()[0],1)
    for observed in EVIDENCE["mini_responses"]:
        cut=truncated_audit(item,"RolePrompting",observed["visible_tokens"])
        with pytest.raises(ValueError):
            r.parse(cut,"audit",item)


def test_truncation_stops_without_burning_the_repair_allowance_or_recording_a_verdict(tmp_path):
    j=reporting_journal(tmp_path); rows=cohort()
    transport=TruncatingMiniTransport()
    with pytest.raises(r.Stop,match="truncated at the configured completion limit"):
        r.construction(j,rows,transport,stage="sanity")
    assert transport.dispatched("mini_audit")==1, "no futile identical repeat"
    assert transport.dispatched("generation")==1, "truncation consumes no extra generation attempt"
    assert transport.dispatched("deepseek_audit")==1
    events={x["id"] for x in j.db.execute("SELECT id FROM events")}
    item=r.candidate_id("sanity",rows[0],1)
    assert r.identifier(item,"mini_audit","truncated",1) in events
    assert r.identifier(item,"mini_audit","verdict") not in events, "truncation is never a verdict"
    assert r.identifier(item,"decision") not in events, "truncation is never a rejection"
    payload=json.loads(j.db.execute("SELECT payload FROM events WHERE id=?",
                                    (r.identifier(item,"mini_audit","truncated",1),)).fetchone()[0])
    assert payload["not_a_verdict"] is True
    j.close()


def test_truncated_run_reports_no_attempt_consumed_and_no_auditor_rejection(tmp_path):
    j=reporting_journal(tmp_path); rows=cohort()
    try:
        r.construction(j,rows,TruncatingMiniTransport(),stage="sanity")
    except r.Stop as exc:
        stopped=str(exc)
    report=s.summarize(j,cohort(),None,stopped)
    assert report["rejections_by_axis"]=={"deepseek_audit":{},"mini_audit":{}}
    assert report["other_rejection_gate_codes"]=={"deepseek_audit":{},"mini_audit":{}}
    assert report["pairs_dual_certified"]==0 and report["sanity_result"].startswith("INCOMPLETE")
    assert all(kind["kind"]=="incomplete_output" for kind in report["failures"])
    j.close()


def test_complete_mini_audit_is_still_accepted_under_the_corrected_budget(tmp_path):
    j=reporting_journal(tmp_path); rows=cohort()
    completed=r.construction(j,rows,FixtureTransport(),stage="sanity")
    assert completed["verdict"] in ("GENERATION SPECIFICATION READY","GENERATION SPECIFICATION NOT READY")
    report=s.summarize(j,rows,None)
    assert report["pairs_dual_certified"]==12 and report["first_attempt_dual_passes"]==12
    j.close()


def test_missing_required_field_is_never_silently_accepted(tmp_path):
    item=r.candidate_id("sanity",cohort()[0],1)
    for field in ("axes","verdict","failed_axes","E_validity","strategy"):
        broken=audit_fixture(item,"RolePrompting"); del broken[field]
        with pytest.raises((ValidationError,KeyError,ValueError)):
            r.parse(r.canonical(broken),"audit",item)


def test_malformed_but_complete_output_still_uses_the_bounded_repair_path(tmp_path):
    """finish_reason 'stop' with unparseable text is a format repair, not a truncation."""
    class Malformed(FixtureTransport):
        def __init__(self): super().__init__(); self.mini=0
        def __call__(self, job, request):
            if request["model"]!=r.MODELS["mini_audit"]:
                return super().__call__(job,request)
            self.mini+=1
            return envelope(request,"not json at all")
    j=reporting_journal(tmp_path); rows=cohort()
    transport=Malformed()
    with pytest.raises(r.Stop,match="exhausted format"):
        r.construction(j,rows,transport,stage="sanity")
    assert transport.mini==2, "bounded repair allowance is still exactly two"
    j.close()


def test_seventeen_gates_and_rejection_behaviour_unchanged(tmp_path):
    assert len(r.AXES)==17
    item=r.candidate_id("sanity",cohort()[0],1)
    audit=audit_fixture(item,"RolePrompting")
    audit["axes"]["u_is_english"]={"pass":False,"reason":"fixture"}
    audit["failed_axes"]=["u_is_english"]; audit["verdict"]="reject"
    parsed=r.parse(r.canonical(audit),"audit",item)
    assert "u_is_english" in r.audit_gate(parsed,item,"RolePrompting","Lo, the books be counted.")


# --- reviewed re-scoping: resume without paying twice ---------------------------


class NoRedispatchTransport(FixtureTransport):
    """Fails loudly if any already-paid job identifier is dispatched a second time."""
    def __init__(self, already_paid):
        super().__init__(); self.already_paid=set(already_paid)
    def __call__(self, job, request):
        if job in self.already_paid:
            raise AssertionError("already-paid work was dispatched a second time: "+job[:16])
        return super().__call__(job,request)

    def dispatched(self, role):
        return sum(request["model"]==r.MODELS[role] for _,request in self.calls)


def interrupted_journal(tmp_path, monkeypatch):
    """Reproduce the real interruption: Mini truncated under the old 4096 budget."""
    def rated():
        cfg=config()
        for settings in cfg["roles"].values():
            settings.update(expected_rates_usd_per_million=[.1,.2],reservation_rates_usd_per_million=[.1,.2])
        return cfg
    monkeypatch.setitem(r.MAX_TOKENS,"mini_audit",4096)
    old=rated()
    j=r.Journal(tmp_path/"fixture.sqlite",old,{})
    rows=cohort()
    with pytest.raises(r.Stop,match="truncated at the configured completion limit"):
        r.construction(j,rows,TruncatingMiniTransport(),stage="sanity")
    spent=j.totals(); j.close()
    monkeypatch.setitem(r.MAX_TOKENS,"mini_audit",8192)
    return tmp_path/"fixture.sqlite",old,rated(),spent,rows


def test_corrected_configuration_cannot_open_the_journal_until_it_is_migrated(tmp_path,monkeypatch):
    path,_,new,_,_=interrupted_journal(tmp_path,monkeypatch)
    with pytest.raises(r.Stop,match="journal configuration/hash scope changed"):
        r.Journal(path,new,{})


def test_migration_preserves_every_row_and_every_nanodollar(tmp_path,monkeypatch):
    path,_,new,spent,_=interrupted_journal(tmp_path,monkeypatch)
    dry=m.migrate(path,new,{},"unit test",apply=False)
    assert dry["applied"] is False and dry["scope_change_required"] is True and not dry["problems"]
    assert [x["role"] for x in dry["superseded"]]==["mini_audit"]
    assert {x["role"] for x in dry["replayable_without_payment"]}=={"generation","deepseek_audit"}
    applied=m.migrate(path,new,{},"unit test",apply=True)
    assert applied["applied"] is True
    ledger=("calls","billed_nusd","reserved_nusd")
    assert {k:applied["totals_after"][k] for k in ledger}=={k:applied["totals_before"][k] for k in ledger}, \
        "no row and no nanodollar removed"
    assert applied["totals_after"]["events"]==applied["totals_before"]["events"]+1, "only the migration record added"
    journal=r.Journal(path,new,{})
    assert journal.totals()["mini_audit"]["billed_nusd"]==spent["mini_audit"]["billed_nusd"]
    assert journal.totals()["generation"]["billed_nusd"]==spent["generation"]["billed_nusd"]
    events={x["id"] for x in journal.db.execute("SELECT id FROM events")}
    assert r.identifier("journal_scope_migration",applied["recorded_scope"],applied["new_scope"]) in events
    journal.close()


def test_resume_reuses_paid_generation_and_primary_audit_without_redispatch(tmp_path,monkeypatch):
    path,_,new,spent,rows=interrupted_journal(tmp_path,monkeypatch)
    m.migrate(path,new,{},"unit test",apply=True)
    journal=r.Journal(path,new,{})
    before={x["id"]:(x["role"],x["billed"],x["response_hash"],x["finished"])
            for x in journal.db.execute("SELECT * FROM calls")}
    paid=list(before)
    assert len(paid)==3
    transport=NoRedispatchTransport(paid)
    completed=r.construction(journal,rows,transport,stage="sanity")
    assert transport.dispatched("generation")==len(rows)-1, "the paid Gemini generation replayed from the journal"
    assert transport.dispatched("deepseek_audit")==len(rows)-1, "the paid DeepSeek pass replayed from the journal"
    assert transport.dispatched("mini_audit")==len(rows), "only the truncated auditor step is re-dispatched"
    after=journal.totals()
    assert after["generation"]["calls"]==spent["generation"]["calls"]+len(rows)-1
    kept={x["id"]:(x["role"],x["billed"],x["response_hash"],x["finished"])
          for x in journal.db.execute("SELECT * FROM calls") if x["id"] in before}
    assert kept==before, "already-paid receipts were altered or re-billed on resume"
    assert after["mini_audit"]["billed_nusd"]>spent["mini_audit"]["billed_nusd"], "superseded spend still counted"
    report=s.summarize(journal,rows,completed)
    assert report["pairs_dual_certified"]==12
    assert report["attempts_per_pair"][rows[0]["pair_id"]]==1, "resume consumed no extra generation attempt"
    journal.close()


def test_migration_refuses_an_unreconciled_or_tampered_journal(tmp_path,monkeypatch):
    path,_,new,_,_=interrupted_journal(tmp_path,monkeypatch)
    db=__import__("sqlite3").connect(path)
    db.execute("UPDATE calls SET state='pending' WHERE role='generation'"); db.commit(); db.close()
    with pytest.raises(r.Stop,match="migration refused"):
        m.migrate(path,new,{},"unit test",apply=True)


def test_migration_refuses_when_a_reservation_bound_changed(tmp_path,monkeypatch):
    path,_,new,_,_=interrupted_journal(tmp_path,monkeypatch)
    changed=copy.deepcopy(new); changed["roles"]["mini_audit"]["maximum_call_nusd"]=999
    with pytest.raises(r.Stop,match="reservation bound changed"):
        m.migrate(path,changed,{},"unit test",apply=True)
