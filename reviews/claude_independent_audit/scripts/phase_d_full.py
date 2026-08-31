import json, collections, itertools
import numpy as np
from scipy import stats
G=[json.loads(l) for l in open('analysis/phase_d_run_archive/scores.jsonl',encoding='utf-8')]
S=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl',encoding='utf-8')]
P={(r['pair_id'],r['model'],r['language']):r for r in S}
GD={(r['pair_id'],r['target_model'],r['language']):r for r in G}
print('unique gpt keys',len(GD))
pids=sorted({r['pair_id'] for r in G}); print('unique cross-judge pairs',len(pids))
M=['qwen/qwen3-30b-a3b-instruct-2507','openai/gpt-oss-20b','nvidia/nemotron-3-nano-30b-a3b']
meta={r['pair_id']:(r['category'],r['strategy']) for r in G}
print('cells', collections.Counter(meta.values()))
print('pairs per model', collections.Counter(r['target_model'] for r in G))
print('parse errors', sum(1 for r in G if r['parse_error']), 'consistency false', sum(1 for r in G if not r['logical_consistency_ok']))
# agreement
a=[];b=[]
for k,r in GD.items():
    pr=P[k]
    if pr['judge_model']!='google/gemini-2.5-flash': continue
    a.append(pr['score']); b.append(r['score'])
a=np.array(a);b=np.array(b)
print(f'\nPure-Gemini vs GPT5mini N={len(a)} exact={100*(a==b).mean():.2f}% adjacent={100*(abs(a-b)<=1).mean():.2f}%')
def kappa(x,y,w=None):
    n=len(x); cats=[0,1,2,3]
    O=np.zeros((4,4)); 
    for i,j in zip(x,y): O[i,j]+=1
    O/=n
    px=O.sum(1); py=O.sum(0); E=np.outer(px,py)
    if w is None:
        W=1-np.eye(4)
    else:
        W=np.array([[ (i-j)**2/9 for j in cats] for i in cats])
    return 1-(W*O).sum()/(W*E).sum()
print(f'unweighted kappa={kappa(a,b):.3f} quadratic-weighted kappa={kappa(a,b,"q"):.3f}')
print('\nGemini score dist', collections.Counter(a.tolist()))
print('GPT5m  score dist', collections.Counter(b.tolist()))
print(f'score3 rate: gemini {100*(a==3).mean():.2f}%  gpt5mini {100*(b==3).mean():.2f}%')
print(f'score0 rate: gemini {100*(a==0).mean():.2f}%  gpt5mini {100*(b==0).mean():.2f}%')
# per model/language agreement + directional bias
print('\nper model x language: mean(gpt - gemini) and exact agreement')
for m in M:
    for lg in ('en','rh'):
        x=[];y=[]
        for p in pids:
            k=(p,m,lg)
            if k in GD and P[k]['judge_model']=='google/gemini-2.5-flash':
                x.append(P[k]['score']); y.append(GD[k]['score'])
        x=np.array(x);y=np.array(y)
        print(f'  {m.split("/")[1][:22]:22s} {lg}  n={len(x):3d} exact={100*(x==y).mean():5.1f}%  mean diff={np.mean(y-x):+.3f}  gemini0={100*(x==0).mean():5.1f}% gpt0={100*(y==0).mean():5.1f}%')
# headline under each judge on subset
print('\nHeadline on 324-pair subset')
def gaps(getter):
    out={}
    for m in M:
        en=np.array([getter(p,m,'en') for p in pids]); rh=np.array([getter(p,m,'rh') for p in pids])
        out[m]=((en==0).astype(float)-(rh==0).astype(float))
    return out
gg=gaps(lambda p,m,l:P[(p,m,l)]['score'])
g5=gaps(lambda p,m,l:GD[(p,m,l)]['score'])
rng=np.random.default_rng(20260829); n=len(pids); idx=rng.integers(0,n,size=(10000,n))
for name,g in (('Gemini',gg),('GPT5m',g5)):
    for m in M:
        v=g[m]; bs=v[idx].mean(axis=1)*100; lo,hi=np.percentile(bs,[2.5,97.5])
        print(f'  {name:7s} {m.split("/")[1][:22]:22s} gap={v.mean()*100:7.2f} [{lo:6.2f},{hi:6.2f}]')
    for i,j in [(0,1),(0,2),(1,2)]:
        d=(g[M[i]]-g[M[j]]); bs=d[idx].mean(axis=1)*100; lo,hi=np.percentile(bs,[2.5,97.5])
        print(f'  {name:7s} CONTRAST {M[i].split("/")[1][:10]}-{M[j].split("/")[1][:10]}: {d.mean()*100:7.2f} [{lo:6.2f},{hi:6.2f}]')
