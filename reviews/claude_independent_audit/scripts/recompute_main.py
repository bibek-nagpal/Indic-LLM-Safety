import json, collections, math, itertools
import numpy as np
from scipy import stats

ROOT='frozen_final_2026_08_29'
S=[json.loads(l) for l in open(f'{ROOT}/run/revision_v2_targets_final/scores.jsonl',encoding='utf-8')]
print('rows',len(S))
# integrity
keys=collections.Counter((r['pair_id'],r['model'],r['language']) for r in S)
print('dup keys', sum(1 for k,v in keys.items() if v>1))
print('scores outside 0-3', sum(1 for r in S if r['score'] not in (0,1,2,3)))
print('judge models', collections.Counter(r['judge_model'] for r in S))
print('parse_error non-null', sum(1 for r in S if r.get('parse_error')))
print('logical_consistency_ok False', sum(1 for r in S if not r.get('logical_consistency_ok')))
print('languages', collections.Counter(r['language'] for r in S))
fb=[r for r in S if r['judge_model']!='google/gemini-2.5-flash']
print('FALLBACK rows:', len(fb))
for r in fb: print('   ', r['pair_id'], r['model'], r['language'], r['score'], r['judge_model'])

D={}
for r in S: D[(r['pair_id'],r['model'],r['language'])]=r
pairs=sorted(set(r['pair_id'] for r in S))
models=sorted(set(r['model'] for r in S))
print('n pairs',len(pairs),'models',models)
meta={r['pair_id']:(r['category'],r['strategy']) for r in S}
cells=collections.Counter(meta.values())
print('cell counts', dict(cells))

def arr(m):
    en=np.array([D[(p,m,'en')]['score'] for p in pairs])
    rh=np.array([D[(p,m,'rh')]['score'] for p in pairs])
    return en,rh

res={}
for m in models:
    en,rh=arr(m)
    Ren=(en==0).astype(int); Rrh=(rh==0).astype(int)
    fwd=int(((en==0)&(rh>=2)).sum()); rev=int(((rh==0)&(en>=2)).sum())
    cf=int(((en<=1)&(rh==3)).sum()); cr=int(((rh<=1)&(en==3)).sum())
    gap=(Ren.mean()-Rrh.mean())*100
    b=int(((Ren==1)&(Rrh==0)).sum()); c=int(((Ren==0)&(Rrh==1)).sum())
    mcn=stats.binomtest(b,b+c,0.5).pvalue
    dirp=stats.binomtest(fwd,fwd+rev,0.5).pvalue
    res[m]=dict(en=Ren.mean()*100,rh=Rrh.mean()*100,gap=gap,fwd=fwd,rev=rev,cf=cf,cr=cr,
                mcnemar_b=b,mcnemar_c=c,mcnemar_p=mcn,dir_p=dirp)
    print(f'{m}: EN {Ren.mean()*100:.2f} RH {Rrh.mean()*100:.2f} gap {gap:.2f} fwd {fwd} rev {rev} CF {cf} CR {cr} mcnemar b/c {b}/{c} p={mcn:.3g} dir_p={dirp:.3g}')

# bootstrap
rng=np.random.default_rng(20260829)
n=len(pairs)
G={m:[] for m in models}
A={m:arr(m) for m in models}
idxs=rng.integers(0,n,size=(10000,n))
for m in models:
    en,rh=A[m]; Ren=(en==0).astype(float); Rrh=(rh==0).astype(float)
    d=Ren-Rrh
    G[m]=d[idxs].mean(axis=1)*100
for m in models:
    lo,hi=np.percentile(G[m],[2.5,97.5])
    print(f'BOOT {m}: gap {res[m]["gap"]:.2f} CI [{lo:.2f},{hi:.2f}]')
contr=[('qwen/qwen3-30b-a3b-instruct-2507','openai/gpt-oss-20b'),
       ('qwen/qwen3-30b-a3b-instruct-2507','nvidia/nemotron-3-nano-30b-a3b'),
       ('openai/gpt-oss-20b','nvidia/nemotron-3-nano-30b-a3b')]
for a,b in contr:
    d=G[a]-G[b]; lo,hi=np.percentile(d,[2.5,97.5])
    print(f'CONTRAST {a.split("/")[1]} - {b.split("/")[1]}: {res[a]["gap"]-res[b]["gap"]:.2f} CI [{lo:.2f},{hi:.2f}]')
json.dump({k:{kk:(float(vv) if isinstance(vv,(int,float,np.floating)) else vv) for kk,vv in v.items()} for k,v in res.items()}, open('reviews/claude_independent_audit/scripts/main_recompute.json','w'), indent=1)
