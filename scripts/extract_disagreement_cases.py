#!/usr/bin/env python3
"""Create blind and unblinded CSVs for cross-auditor disagreement cases."""
from __future__ import annotations
import argparse, csv, hashlib, json, zipfile
from collections import Counter
from pathlib import Path
from typing import Any

AXES=("same_harmful_intent","same_scenario","same_info_level_requested","same_attack_strategy","same_cultural_specificity","same_target_group","same_ambiguity_level","language_fidelity","strategy_faithfully_used")

def stable_id(trace_name:str,line_number:int,en:str,rh:str)->str:
    payload="\x1f".join((trace_name,str(line_number),en,rh)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:24]

def read_archive(zip_path:Path)->dict[str,dict[str,Any]]:
    out={}
    with zipfile.ZipFile(zip_path,"r") as zf:
        names=sorted(n for n in zf.namelist() if n.endswith("/traces.jsonl"))
        if not names: raise RuntimeError("No */traces.jsonl files found")
        for trace_name in names:
            run_name=trace_name.rsplit("/",2)[-2]
            raw=zf.read(trace_name).decode("utf-8",errors="strict")
            for line_number,line in enumerate(raw.splitlines(),1):
                if not line.strip(): continue
                event=json.loads(line)
                if event.get("event")!="candidate": continue
                cand=event.get("candidate"); old=event.get("equivalence")
                if not isinstance(cand,dict) or not isinstance(old,dict):
                    raise RuntimeError(f"Malformed candidate event at {trace_name}:{line_number}")
                en=cand.get("english_prompt"); rh=cand.get("romanized_hindi_prompt")
                if not isinstance(en,str) or not isinstance(rh,str):
                    raise RuntimeError(f"Non-string prompt at {trace_name}:{line_number}")
                rid=stable_id(trace_name,line_number,en,rh)
                out[rid]={"id":rid,"trace_name":trace_name,"trace_line":line_number,"run_name":run_name,"candidate":cand,"original_equivalence":old}
    return out

def read_cross(path:Path)->dict[str,dict[str,Any]]:
    out={}
    for i,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        row=json.loads(line)
        if row.get("error"): continue
        rid=str(row.get("id") or "")
        if not rid: raise RuntimeError(f"Missing id at {path}:{i}")
        if not isinstance(row.get("original_equivalence"),dict) or not isinstance(row.get("independent_equivalence"),dict):
            raise RuntimeError(f"Missing audit objects at {path}:{i}")
        out[rid]=row
    return out

def axis_equal(audit:dict[str,Any],axis:str)->Any:
    e=(audit.get("axes") or {}).get(axis)
    return e.get("equal","") if isinstance(e,dict) else ""

def axis_reason(audit:dict[str,Any],axis:str)->str:
    e=(audit.get("axes") or {}).get(axis)
    return str(e.get("reason","")) if isinstance(e,dict) else ""

def build_rows(archive,cross):
    missing=sorted(set(cross)-set(archive))
    if missing: raise RuntimeError(f"{len(missing)} IDs missing from archive; examples={missing[:5]}")
    rows=[]
    for rid,cross_row in cross.items():
        a=archive[rid]; cand=a["candidate"]; old=cross_row["original_equivalence"]; new=cross_row["independent_equivalence"]
        oa=bool(old.get("accepted")); na=bool(new.get("accepted"))
        if oa==na: continue
        direction="Gemini accept -> independent reject" if oa and not na else "Gemini reject -> independent accept"
        row={
            "review_order":0,"id":rid,"category":cand.get("category",""),"strategy":cand.get("strategy",""),"scenario":cand.get("scenario",""),"info_level_requested":cand.get("info_level_requested",""),"target_group":cand.get("target_group",""),"english_prompt":cand.get("english_prompt",""),"romanized_hindi_prompt":cand.get("romanized_hindi_prompt",""),
            "human_certification":"","human_rh_stronger_than_en":"","human_language_fidelity_ok":"","human_strategy_faithfully_used":"","human_primary_failure_axis":"","human_confidence_1_to_5":"","human_reasoning":"",
            "disagreement_direction":direction,"gemini_accepted":oa,"independent_accepted":na,"gemini_score":old.get("score",""),"independent_score":new.get("score",""),"gemini_rh_stronger_than_en":old.get("rh_stronger_than_en",""),"independent_rh_stronger_than_en":new.get("rh_stronger_than_en",""),"gemini_language_fidelity_ok":old.get("language_fidelity_ok",""),"independent_language_fidelity_ok":new.get("language_fidelity_ok",""),"gemini_strategy_faithfully_used":old.get("strategy_faithfully_used",""),"independent_strategy_faithfully_used":new.get("strategy_faithfully_used",""),"gemini_verdict_reason":old.get("verdict_reason",""),"independent_verdict_reason":new.get("verdict_reason",""),"run_name":a["run_name"],"trace_name":a["trace_name"],"trace_line":a["trace_line"]}
        for axis in AXES:
            row[f"gemini_{axis}"]=axis_equal(old,axis); row[f"independent_{axis}"]=axis_equal(new,axis); row[f"gemini_{axis}_reason"]=axis_reason(old,axis); row[f"independent_{axis}_reason"]=axis_reason(new,axis)
        rows.append(row)
    rows.sort(key=lambda r:(str(r["strategy"]),str(r["category"]),str(r["id"])))
    for i,r in enumerate(rows,1): r["review_order"]=i
    return rows

def write_csv(path:Path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-zip",required=True)
    ap.add_argument("--cross-audit-jsonl",required=True)
    ap.add_argument("--output-dir",default="runs/cross_auditor/manual_review")
    args=ap.parse_args()
    zp=Path(args.data_zip); jp=Path(args.cross_audit_jsonl); out=Path(args.output_dir)
    archive=read_archive(zp); cross=read_cross(jp); rows=build_rows(archive,cross)
    blind=["review_order","id","category","strategy","scenario","info_level_requested","target_group","english_prompt","romanized_hindi_prompt","human_certification","human_rh_stronger_than_en","human_language_fidelity_ok","human_strategy_faithfully_used","human_primary_failure_axis","human_confidence_1_to_5","human_reasoning"]
    unblind=blind+["disagreement_direction","gemini_accepted","independent_accepted","gemini_score","independent_score","gemini_rh_stronger_than_en","independent_rh_stronger_than_en","gemini_language_fidelity_ok","independent_language_fidelity_ok","gemini_strategy_faithfully_used","independent_strategy_faithfully_used","gemini_verdict_reason","independent_verdict_reason"]
    for axis in AXES: unblind += [f"gemini_{axis}",f"independent_{axis}",f"gemini_{axis}_reason",f"independent_{axis}_reason"]
    unblind += ["run_name","trace_name","trace_line"]
    bp=out/"disagreement_cases_blind.csv"; up=out/"disagreement_cases_unblinded.csv"; sp=out/"disagreement_cases_summary.json"
    write_csv(bp,rows,blind); write_csv(up,rows,unblind)
    summary={"cross_audit_successful_records":len(cross),"disagreement_count":len(rows),"agreement_count":len(cross)-len(rows),"disagreement_by_direction":dict(Counter(r["disagreement_direction"] for r in rows)),"disagreement_by_strategy":dict(Counter(str(r["strategy"]) for r in rows)),"disagreement_by_category":dict(Counter(str(r["category"]) for r in rows)),"files":{"blind":str(bp),"unblinded":str(up)}}
    sp.write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Cross-audit successful records: {len(cross)}"); print(f"Disagreement cases: {len(rows)}"); print(f"Wrote: {bp}"); print(f"Wrote: {up}"); print(f"Wrote: {sp}")
    return 0
if __name__=="__main__": raise SystemExit(main())
