import json, collections
import numpy as np
from scipy import stats
rows=json.load(open('reviews/claude_independent_audit/scripts/deduped_response_rows.json'))
S=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl',encoding='utf-8')]
SR={(r['pair_id'],r['model'],r['language']):r for r in S}
M=sorted({r['model'] for r in rows})
print('=== Is score==0 actually "refusal"? ===')
for m in M:
    for lg in ('en','rh'):
        sub=[r for r in rows if r['model']==m and r['lang']==lg and r['score']==0]
        short=sum(1 for r in sub if r['n']<80); long=sum(1 for r in sub if r['n']>500)
        lk=sum(1 for r in sub if SR[(r['pid'],r['model'],lg)]['looks_like_refusal'])
        gb=sum(1 for r in sub if SR[(r['pid'],r['model'],lg)]['response_garbled'])
        print(f'{m.split("/")[1][:22]:22s} {lg} n0={len(sub):3d}  <80ch {short:3d} ({100*short/max(1,len(sub)):.0f}%)  >500ch {long:3d} ({100*long/max(1,len(sub)):.0f}%)  looks_like_refusal {lk:3d}  garbled {gb}')
print('\n=== looks_like_refusal vs score (all 3024) ===')
ct=collections.Counter((r['score'],r['looks_like_refusal']) for r in S)
print(dict(sorted(ct.items())))
print('\n=== garbled flag by model/lang ===')
g=collections.Counter((r['model'].split("/")[1][:20],r['language']) for r in S if r['response_garbled'])
print(dict(g))
print('\n=== TRUNCATION SENSITIVITY: drop pair-model jobs with any finish_reason==length ===')
D={(r['pid'],r['model'],r['lang']):r for r in rows}
pids=sorted({r['pid'] for r in rows})
for m in M:
    keep=[p for p in pids if D[(p,m,'en')]['fin']!='length' and D[(p,m,'rh')]['fin']!='length']
    en=np.array([D[(p,m,'en')]['score'] for p in keep]); rh=np.array([D[(p,m,'rh')]['score'] for p in keep])
    ena=np.array([D[(p,m,'en')]['score'] for p in pids]); rha=np.array([D[(p,m,'rh')]['score'] for p in pids])
    gap=((en==0).mean()-(rh==0).mean())*100; gapa=((ena==0).mean()-(rha==0).mean())*100
    cf=int(((en<=1)&(rh==3)).sum()); cr=int(((rh<=1)&(en==3)).sum())
    cfa=int(((ena<=1)&(rha==3)).sum()); cra=int(((rha<=1)&(ena==3)).sum())
    print(f'{m.split("/")[1][:22]:22s} full N=504 gap={gapa:6.2f} CF/CR={cfa}/{cra} | untruncated N={len(keep)} gap={gap:6.2f} CF/CR={cf}/{cr}')
print('\n=== score3 rate by truncation status ===')
for m in M:
    for lg in ('en','rh'):
        sub=[r for r in rows if r['model']==m and r['lang']==lg]
        t=[r for r in sub if r['fin']=='length']; u=[r for r in sub if r['fin']!='length']
        f3=lambda a: 100*sum(1 for r in a if r['score']==3)/max(1,len(a))
        print(f'{m.split("/")[1][:22]:22s} {lg} trunc n={len(t):3d} score3={f3(t):5.1f}%  | untrunc n={len(u):3d} score3={f3(u):5.1f}%')
